"""Post-validation business rules for v2 cluster emissions.

The JSON schema enforces structural correctness (required fields, enums,
conditional ``allOf`` rules). This layer enforces what the schema can't:

1. **evidence_tier == max(reference_citations[].tier)** — the schema's
   allOf rules promote evidence_tier to the maximum, but redundant
   verification catches schema-bypass paths and surfaces the discrepancy
   with a precise error message.

2. **element.baton_index resolves to baton.elements[].e_index** — specialists
   cannot invent ``e47`` when the baton has 30 elements. The schema can't
   express cross-document referential integrity, so we check at this layer.

3. **evidence_anchors[].reference resolves to a baton element (type=dom) or a
   section screenshot (type=visual)** — same structural-integrity rule
   applied to anchors.

Phase L additions (2026-04-29) — determinism rules:

4. **surface in cluster vocabulary** — surface field must be in the cluster's
   closed ``surface_vocabulary`` ∪ ``baton.sections[].slug`` ∪ ``{'other'}``.
   ``surface: 'other'`` requires a non-empty ``surface_note``.

5. **baton precedence (verbatim anchor heuristic)** — if a finding's prose
   verbatim-quotes element text, the cited ``baton_index`` should match the
   element with that text. Soft check; only fires on obvious mismatches.

6. **within-emission uniqueness** — no two findings within the emission share
   the same ``(surface, baton_index, verdict)`` tuple. ``baton_index='absent'``
   relaxes to bounce only if title-token Jaccard ≥ 0.7 AND ``(surface, verdict)``
   matches (protects legitimate distinct-but-missing things on same surface).

7. **finding count band** — ``findings[]`` count must be within the cluster's
   ``target_finding_count: <min>-<max>`` band when ``status='complete'``.

Failure path matches schema-validation failures (Phase E plan §6):
- First failure: lead constructs retry prompt embedding the rule violation
  and re-dispatches once.
- Second failure: cluster-emission marked ``status: partial``, lead logs in
  ``agent-behavior-log.md``, audit continues with whatever the specialist
  did emit.

Authored 2026-04-27 as Phase E.6 deliverable. Phase L additions 2026-04-29.
See:
- docs/plans/2026-04-27-feat-ecp-v2-redesign-plan.md Phase E
- docs/plans/2026-04-29-feat-phase-l-specialist-tightening-plan.md Phase L
- scripts/assembly/json_parser.py (sibling: schema validation)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import NamedTuple

from .models import EVIDENCE_TIER_RANK


_SCREENSHOT_PATTERN = re.compile(r"^section-[0-9]+(-mobile)?\.jpg$")
_ABSOLUTE_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)
_E_INDEX_PATTERN = re.compile(r"^e[0-9]+$")

# Phase L constants
_ABSENT_FINDING_JACCARD_THRESHOLD: float = 0.7
_MAX_VIOLATIONS_IN_RETRY_PROMPT: int = 24
# Verbatim-quoted strings in finding prose: 2-80 chars, plain or curly quotes
_VERBATIM_QUOTE_PATTERN = re.compile(r'["“”]([^"“”]{2,80})["“”]')
# Stopwords removed before computing title Jaccard
_TITLE_STOPWORDS = frozenset({
    "a", "an", "the", "of", "for", "to", "in", "on", "at", "with",
    "and", "or", "is", "are", "be", "by", "no", "not",
})


class FindingBand(NamedTuple):
    """Min-max band for findings[] count when status='complete'.

    Parsed from a cluster contract's ``target_finding_count: <min>-<max>``
    YAML field. Use ``FindingBand.parse('3-5')`` to construct from spec.
    """

    min_count: int
    max_count: int

    @classmethod
    def parse(cls, spec: str) -> "FindingBand":
        """Parse '<min>-<max>' string like '3-5' into a FindingBand."""
        lo, _, hi = spec.partition("-")
        return cls(int(lo), int(hi))


@dataclass(frozen=True)
class BusinessRuleViolation(Exception):
    """One business rule violation. Frozen for safe pass-through to retry-prompt construction."""

    rule: str
    finding_path: str  # e.g., "findings[2]" or "(emission)"
    field: str  # e.g., "element.baton_index"
    actual: str  # the offending value
    expected: str  # what was expected
    message: str  # human-readable

    def __str__(self) -> str:
        return f"{self.finding_path}.{self.field}: {self.message}"


def validate_business_rules(
    emission: dict,
    *,
    baton: dict | None = None,
    desktop_baton: dict | None = None,
    mobile_baton: dict | None = None,
    cluster_vocab: set[str] | None = None,
    target_band: FindingBand | None = None,
    anchor_candidates_sidecar: dict | None = None,
) -> list[BusinessRuleViolation]:
    """Run all post-validation business rules.

    Returns a list of BusinessRuleViolation. Empty list = pass.

    Baton resolution sources (in priority order):
    - ``baton`` (single baton): used when emission.device matches the baton
    - ``desktop_baton`` + ``mobile_baton``: used when emission is ethics
      (cluster='ethics', device='page'); element.baton_index can resolve
      against either device's baton

    If no baton is provided, baton-resolution checks are skipped (the rule
    can't be evaluated without the source-of-truth document).

    Phase L parameters:
    - ``cluster_vocab``: closed list of abstract surfaces this cluster
      audits (from contracts/specialists/{cluster}.md surface_vocabulary).
      If provided, the runtime checks ``surface`` is in
      ``cluster_vocab ∪ baton.sections[].slug ∪ {'other'}``.
    - ``target_band``: FindingBand from the cluster's
      ``target_finding_count``. If provided AND ``status='complete'``,
      ``findings[]`` count must be within band.

    Phase 4b parameter:
    - ``anchor_candidates_sidecar``: when provided (anchor-candidates-{device}.json
      payload), FAIL/PARTIAL findings whose ``element.baton_index`` is a real
      ``eN`` MUST cite a baton element that appears in the sidecar's
      ``candidate_to_e_index`` values, unless the finding sets
      ``intentional_outside_registry=true`` with a non-empty reason.
      When None (no sidecar for the device), the check is skipped — legacy
      engagements pass through. See contracts/specialist-prompt-v2.md
      'Anchor candidates' section.

    Phase L hard-assert: emissions reaching this function MUST have a
    ``schema_version`` field. v1 markdown emissions should not pass through
    here.
    """
    if "schema_version" not in emission:
        raise ValueError(
            "Phase L validators are v2-only; emission missing schema_version. "
            "v1 markdown emissions must not pass through validate_business_rules."
        )

    violations: list[BusinessRuleViolation] = []

    # Phase L: skipped emissions short-circuit all checks
    if emission.get("status") == "skipped":
        return violations

    findings = emission.get("findings", [])

    # Build the union of baton e_indexes for resolution checks
    baton_indexes: set[str] = set()
    if baton is not None:
        baton_indexes |= _e_indexes(baton)
    if desktop_baton is not None:
        baton_indexes |= _e_indexes(desktop_baton)
    if mobile_baton is not None:
        baton_indexes |= _e_indexes(mobile_baton)
    have_baton = bool(baton_indexes)

    # Phase L: build effective vocabulary
    effective_vocab: set[str] | None = None
    if cluster_vocab is not None:
        effective_vocab = set(cluster_vocab)
        effective_vocab.add("other")
        effective_vocab |= _baton_sections(baton, desktop_baton, mobile_baton)

    # Phase 4b — registry membership check is gated on sidecar presence.
    # When sidecar is None (legacy engagement), the check is silently
    # skipped; FAIL/PARTIAL findings can cite any baton element. When the
    # sidecar exists, the registry is the contract.
    registry_e_indexes: set[str] | None = None
    if isinstance(anchor_candidates_sidecar, dict):
        c2e = anchor_candidates_sidecar.get("candidate_to_e_index") or {}
        if isinstance(c2e, dict):
            registry_e_indexes = {
                v for v in c2e.values()
                if isinstance(v, str) and v.startswith("e") and v[1:].isdigit()
            }

    # Per-finding checks
    for i, f in enumerate(findings):
        path = f"findings[{i}]"
        violations.extend(_check_evidence_tier(f, path))
        if have_baton:
            violations.extend(_check_baton_index(f, path, baton_indexes))
            violations.extend(_check_anchor_resolution(f, path, baton_indexes))
            violations.extend(
                _check_baton_precedence(f, path, baton, desktop_baton, mobile_baton)
            )
            # Phase M (2026-05-01): catch precise-but-wrong selector hallucinations
            # by cross-checking the finding's claimed element metadata against the
            # actual baton element at the cited e_index. Closes the awdmods.com
            # 2026-05-01 e15-hallucination class.
            violations.extend(
                _check_element_text_match(f, path, baton, desktop_baton, mobile_baton)
            )
            violations.extend(
                _check_evidence_anchor_consistency(f, path, baton, desktop_baton, mobile_baton)
            )
        if effective_vocab is not None:
            violations.extend(_check_surface_in_vocabulary(f, path, effective_vocab))
        if registry_e_indexes is not None:
            violations.extend(
                _check_baton_index_in_candidate_registry(
                    f, path, registry_e_indexes, anchor_candidates_sidecar,
                )
            )

    # Emission-scoped checks (Phase L)
    violations.extend(_check_within_emission_unique_anchors(emission))
    if target_band is not None and emission.get("status") == "complete":
        violations.extend(_check_finding_count_in_band(emission, target_band))

    # Baton-scoped checks (Phase M, 2026-05-01) — disjoint-sections invariant.
    # JSON Schema cannot compare adjacent array items, so we lint here.
    for b in (baton, desktop_baton, mobile_baton):
        if b is not None:
            violations.extend(_check_baton_sections_disjoint(b))

    return violations


def _e_indexes(baton: dict) -> set[str]:
    """Extract the set of e_index values from a baton."""
    return {el.get("e_index", "") for el in (baton.get("elements") or []) if el.get("e_index")}


def _baton_sections(*batons: dict | None) -> set[str]:
    """Extract the union of sections[].slug values from any non-None baton(s)."""
    out: set[str] = set()
    for b in batons:
        if b is None:
            continue
        for sec in b.get("sections") or []:
            slug = sec.get("slug")
            if slug:
                out.add(slug)
    return out


def _check_evidence_tier(finding: dict, path: str) -> list[BusinessRuleViolation]:
    """Rule: evidence_tier == max(reference_citations[].tier)."""
    cites = finding.get("reference_citations") or []
    declared = finding.get("evidence_tier", "")
    if not cites:
        # No citations — only valid for PASS findings; the schema enforces
        # citation requirement for FAIL/PARTIAL via allOf, so we don't
        # double-check here.
        return []
    top_rank = max(EVIDENCE_TIER_RANK.get(c.get("tier", ""), 0) for c in cites)
    expected = next((tier for tier, rank in EVIDENCE_TIER_RANK.items() if rank == top_rank), "")
    if expected and declared and expected != declared:
        return [
            BusinessRuleViolation(
                rule="evidence_tier_matches_max_citation_tier",
                finding_path=path,
                field="evidence_tier",
                actual=declared,
                expected=expected,
                message=(
                    f"declared evidence_tier={declared!r} disagrees with "
                    f"max(reference_citations[].tier)={expected!r}"
                ),
            )
        ]
    return []


def _check_baton_index_in_candidate_registry(
    finding: dict,
    path: str,
    registry_e_indexes: set[str],
    sidecar: dict | None,
) -> list[BusinessRuleViolation]:
    """Phase 4b (2026-05-18) — FAIL/PARTIAL findings whose element.baton_index
    is a real ``eN`` MUST cite a baton element that appears in the
    anchor-candidates sidecar's ``candidate_to_e_index`` values, unless
    the finding opts out via ``intentional_outside_registry=true`` with
    a non-empty reason.

    Exempt:
    - PASS findings (no actionable hotspot — registry isn't load-bearing)
    - findings with ``baton_index = "absent"`` (no element to register)
    - findings with empty ``baton_index`` (schema validation catches separately)
    - findings with ``intentional_outside_registry: true`` AND non-empty
      ``intentional_outside_registry_reason``

    On violation, the message includes a sample of candidate_id ↔ eN
    mappings so the specialist can pick the right candidate_id on retry.
    """
    verdict = (finding.get("verdict") or "").upper()
    if verdict not in {"FAIL", "PARTIAL"}:
        return []

    element = finding.get("element") or {}
    bi = element.get("baton_index", "")
    if not bi or bi == "absent":
        return []
    if not _E_INDEX_PATTERN.match(bi):
        # Format violation is caught by _check_baton_index; don't double-report.
        return []
    if bi in registry_e_indexes:
        return []

    # Not in registry — check for opt-out
    if finding.get("intentional_outside_registry") is True:
        reason = (finding.get("intentional_outside_registry_reason") or "").strip()
        if reason:
            return []  # legitimate opt-out
        return [
            BusinessRuleViolation(
                rule="intentional_outside_registry_reason_required",
                finding_path=path,
                field="intentional_outside_registry_reason",
                actual="",
                expected="non-empty string",
                message=(
                    "intentional_outside_registry=true but "
                    "intentional_outside_registry_reason is empty. "
                    "Every opt-out from the candidate registry MUST carry "
                    "a human-readable justification for ranker tuning."
                ),
            )
        ]

    # Build a sample suggestion for the retry prompt
    sample_pairs: list[str] = []
    c2e = (sidecar or {}).get("candidate_to_e_index") or {}
    if isinstance(c2e, dict):
        for cid, e_index in list(c2e.items())[:5]:
            sample_pairs.append(f"{cid} -> {e_index}")
    suggestion = (
        "; ".join(sample_pairs) if sample_pairs else "(registry empty?)"
    )

    return [
        BusinessRuleViolation(
            rule="baton_index_in_candidate_registry",
            finding_path=path,
            field="element.baton_index",
            actual=bi,
            expected=f"one of registry baton_indexes ({len(registry_e_indexes)} total)",
            message=(
                f"baton_index={bi!r} is not in the anchor-candidates "
                f"registry. Either cite a candidate_id via "
                f"visual_evidence.observed_anchor.candidate_id "
                f"(sample: {suggestion}) OR opt out with "
                f"intentional_outside_registry: true plus a "
                f"non-empty intentional_outside_registry_reason "
                f"explaining why this element belongs outside the registry."
            ),
        )
    ]


def _check_baton_index(
    finding: dict, path: str, baton_indexes: set[str]
) -> list[BusinessRuleViolation]:
    """Rule: element.baton_index resolves to baton.elements[].e_index (or 'absent')."""
    element = finding.get("element") or {}
    bi = element.get("baton_index", "")
    if not bi:
        return []  # Schema requires baton_index; if missing, schema validation already caught it
    if bi == "absent":
        return []  # Reserved sentinel — legitimate
    if not _E_INDEX_PATTERN.match(bi):
        return [
            BusinessRuleViolation(
                rule="baton_index_format",
                finding_path=path,
                field="element.baton_index",
                actual=bi,
                expected="e<int> or absent",
                message=f"baton_index={bi!r} does not match pattern ^e[0-9]+$",
            )
        ]
    if bi not in baton_indexes:
        return [
            BusinessRuleViolation(
                rule="baton_index_resolves",
                finding_path=path,
                field="element.baton_index",
                actual=bi,
                expected=f"one of baton.elements[].e_index ({len(baton_indexes)} elements)",
                message=(
                    f"baton_index={bi!r} not found in baton.elements[]; "
                    f"baton has {len(baton_indexes)} indexed elements"
                ),
            )
        ]
    return []


# Role aliases tolerated when matching finding.element.role against baton role.
# Specialists frequently emit implicit-role variants; these are semantically equivalent.
_ROLE_ALIASES: dict[str, frozenset[str]] = {
    "banner": frozenset({"banner", "header"}),
    "header": frozenset({"banner", "header"}),
    "contentinfo": frozenset({"contentinfo", "footer"}),
    "footer": frozenset({"contentinfo", "footer"}),
    "navigation": frozenset({"navigation", "nav"}),
    "nav": frozenset({"navigation", "nav"}),
    "image": frozenset({"image", "img"}),
    "img": frozenset({"image", "img"}),
    "link": frozenset({"link", "a"}),
    "a": frozenset({"link", "a"}),
    "button": frozenset({"button"}),
    "heading": frozenset({"heading", "h1", "h2", "h3", "h4", "h5", "h6"}),
    "form": frozenset({"form"}),
}


def _normalize_text_for_compare(s: str) -> str:
    """Whitespace+case+punctuation normalize for cross-document text matching.

    DOM text often has extra/missing whitespace from minified templates ('PerformanceIntakesExhaust')
    while specialist findings naturally split the words ('Performance Intakes Exhaust'). We strip ALL
    whitespace and most punctuation so the substring check is robust to either formatting.
    """
    if not isinstance(s, str):
        return ""
    # Lowercase, then keep only alphanumerics — drops whitespace, newlines, and punctuation
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def _baton_element_by_index(
    baton_index: str,
    baton: dict | None,
    desktop_baton: dict | None,
    mobile_baton: dict | None,
) -> dict | None:
    """Find a baton element by e_index across one or more batons. None if not found."""
    for b in (baton, desktop_baton, mobile_baton):
        if b is None:
            continue
        for el in b.get("elements") or []:
            if el.get("e_index") == baton_index:
                return el
    return None


def _find_e_indexes_containing_text(
    needle: str,
    baton: dict | None,
    desktop_baton: dict | None,
    mobile_baton: dict | None,
    *,
    limit: int = 3,
) -> list[str]:
    """Return up to ``limit`` baton e_indexes whose text_content/accessible_name contains ``needle``.

    Used to power 'did you mean eN?' suggestions when a finding's claimed
    element text doesn't match its cited e_index.
    """
    needle_norm = _normalize_text_for_compare(needle)
    if not needle_norm:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for b in (baton, desktop_baton, mobile_baton):
        if b is None:
            continue
        for el in b.get("elements") or []:
            idx = el.get("e_index")
            if not idx or idx in seen:
                continue
            haystack = " ".join(
                _normalize_text_for_compare(el.get(f, "") or "")
                for f in ("text_content", "accessible_name")
            )
            if needle_norm in haystack:
                seen.add(idx)
                out.append(idx)
                if len(out) >= limit:
                    return out
    return out


def _check_element_text_match(
    finding: dict,
    path: str,
    baton: dict | None,
    desktop_baton: dict | None,
    mobile_baton: dict | None,
) -> list[BusinessRuleViolation]:
    """Rule: when finding cites a real e_index, finding.element.text_content / role / tag MUST
    agree with the actual baton element at that index.

    Catches the *precise-but-wrong* class of selector hallucination — where the cited e_index
    exists but the specialist's claimed element metadata doesn't describe what's actually at
    that index. Without this rule, schema validation passes (the index exists) and the renderer
    places hotspots correctly per the data — but on the wrong element semantically.

    Documented failure case: awdmods.com 2026-05-01 run, mobile findings ``pricing F-26``
    and ``visual-cta F-44`` both cited e15 with text 'div.announcement-bar' / 'div.hero__inner';
    actual mobile e15 was a <header role='banner'> containing 'Shop All / Shop by Category'.
    """
    element = finding.get("element") or {}
    bi = element.get("baton_index", "")
    if not bi or bi == "absent":
        return []
    if not _E_INDEX_PATTERN.match(bi):
        return []  # Format issue handled by _check_baton_index
    actual = _baton_element_by_index(bi, baton, desktop_baton, mobile_baton)
    if actual is None:
        return []  # Index doesn't resolve at all; _check_baton_index reports that
    out: list[BusinessRuleViolation] = []

    # Text-content check: claimed text must be a substring of the baton's
    # actual text_content OR accessible_name (whitespace+case normalized).
    claimed_text = element.get("text_content", "") or ""
    if claimed_text:
        claimed_norm = _normalize_text_for_compare(claimed_text)
        actual_text_norm = _normalize_text_for_compare(actual.get("text_content", "") or "")
        actual_name_norm = _normalize_text_for_compare(actual.get("accessible_name", "") or "")
        if claimed_norm and claimed_norm not in actual_text_norm and claimed_norm not in actual_name_norm:
            # Reverse-search: which baton e_indexes DO contain the claimed text?
            suggestions = _find_e_indexes_containing_text(
                claimed_text, baton, desktop_baton, mobile_baton, limit=3
            )
            if suggestions:
                hint = f" Claimed text appears at: {', '.join(suggestions)}."
            else:
                hint = (
                    " No baton element contains the claimed text — either fix the text claim "
                    "or use baton_index='absent' with proposed_anchor."
                )
            actual_preview = (actual.get("text_content") or actual.get("accessible_name") or "")[:60]
            out.append(
                BusinessRuleViolation(
                    rule="element_text_matches_baton",
                    finding_path=path,
                    field="element.text_content",
                    actual=claimed_text[:80],
                    expected=f"substring of baton[{bi}].text_content/accessible_name ({actual_preview!r})",
                    message=(
                        f"element.text_content={claimed_text[:60]!r} does not match baton[{bi}] "
                        f"(actual: {actual_preview!r})." + hint
                    ),
                )
            )

    # Role check (with alias tolerance): claimed role should match baton's role
    # under the alias map (banner ↔ header, link ↔ a, etc.).
    claimed_role = (element.get("role") or "").strip().lower()
    actual_role = (actual.get("role") or "").strip().lower()
    if claimed_role and actual_role and claimed_role != actual_role:
        aliases = _ROLE_ALIASES.get(claimed_role, frozenset({claimed_role}))
        if actual_role not in aliases:
            out.append(
                BusinessRuleViolation(
                    rule="element_role_matches_baton",
                    finding_path=path,
                    field="element.role",
                    actual=claimed_role,
                    expected=f"baton[{bi}].role ({actual_role!r}) or alias",
                    message=(
                        f"element.role={claimed_role!r} disagrees with baton[{bi}].role={actual_role!r}. "
                        f"Alias map for {claimed_role!r}: {sorted(aliases)}."
                    ),
                )
            )

    # Tag check (optional field): if specialist provided element.tag, it must match baton.
    claimed_tag = (element.get("tag") or "").strip().lower()
    actual_tag = (actual.get("tag") or "").strip().lower()
    if claimed_tag and actual_tag and claimed_tag != actual_tag:
        out.append(
            BusinessRuleViolation(
                rule="element_tag_matches_baton",
                finding_path=path,
                field="element.tag",
                actual=claimed_tag,
                expected=f"baton[{bi}].tag ({actual_tag!r})",
                message=(
                    f"element.tag={claimed_tag!r} disagrees with baton[{bi}].tag={actual_tag!r}. "
                    "Either fix the cited e_index or remove the tag claim."
                ),
            )
        )

    return out


def _check_evidence_anchor_consistency(
    finding: dict,
    path: str,
    baton: dict | None,
    desktop_baton: dict | None,
    mobile_baton: dict | None,
) -> list[BusinessRuleViolation]:
    """Rule: when both element.baton_index and an evidence_anchors[type='dom'].reference are
    real e_indexes, they SHOULD point at the same element OR the finding must justify the
    divergence (e.g., proposed_anchor explains why a different anchor target is used).

    Catches the copy-paste class where element.baton_index was hand-edited but evidence_anchors
    was left unchanged (or vice-versa). Soft check — emits only when both are concrete e_indexes
    AND they disagree AND no proposed_anchor explains the split.
    """
    element = finding.get("element") or {}
    bi = element.get("baton_index", "")
    if not bi or bi == "absent" or not _E_INDEX_PATTERN.match(bi):
        return []
    if bi not in {idx for b in (baton, desktop_baton, mobile_baton) if b for idx in _e_indexes(b)}:
        return []  # Unresolved index handled elsewhere
    has_proposed_anchor = bool(finding.get("proposed_anchor"))
    out: list[BusinessRuleViolation] = []
    for j, a in enumerate(finding.get("evidence_anchors") or []):
        if a.get("type") != "dom":
            continue
        ref = a.get("reference", "")
        if not _E_INDEX_PATTERN.match(ref):
            continue  # Free-form selector; can't compare
        if ref != bi and not has_proposed_anchor:
            out.append(
                BusinessRuleViolation(
                    rule="anchor_consistent_with_element",
                    finding_path=path,
                    field=f"evidence_anchors[{j}].reference",
                    actual=ref,
                    expected=f"{bi} (matching element.baton_index) or set proposed_anchor",
                    message=(
                        f"evidence_anchors[{j}].reference={ref!r} disagrees with "
                        f"element.baton_index={bi!r} and no proposed_anchor explains the split. "
                        "Either align the anchor to the element, or use proposed_anchor to "
                        "justify a different anchor target."
                    ),
                )
            )
    return out


def _check_anchor_resolution(
    finding: dict, path: str, baton_indexes: set[str]
) -> list[BusinessRuleViolation]:
    """Rule: evidence_anchors[].reference resolves to baton element or screenshot."""
    out: list[BusinessRuleViolation] = []
    for j, a in enumerate(finding.get("evidence_anchors") or []):
        apath = f"{path}.evidence_anchors[{j}]"
        ref = a.get("reference", "")
        atype = a.get("type", "")
        if not ref:
            continue  # schema requires reference; missing is a schema-level issue
        if atype == "dom":
            # Allowed: e<int> in baton, OR a CSS selector / DOM path (free-form)
            if _E_INDEX_PATTERN.match(ref):
                if ref not in baton_indexes:
                    out.append(
                        BusinessRuleViolation(
                            rule="anchor_baton_resolves",
                            finding_path=path,
                            field=f"evidence_anchors[{j}].reference",
                            actual=ref,
                            expected=f"one of baton.elements[].e_index",
                            message=(
                                f"DOM anchor reference={ref!r} not found in baton.elements[]"
                            ),
                        )
                    )
            # Else: free-form DOM path (CSS selector, XPath) — accepted; can't
            # validate without parsing the actual DOM tree.
        elif atype == "visual":
            if not _SCREENSHOT_PATTERN.match(ref):
                out.append(
                    BusinessRuleViolation(
                        rule="anchor_screenshot_pattern",
                        finding_path=path,
                        field=f"evidence_anchors[{j}].reference",
                        actual=ref,
                        expected="section-N.jpg or section-N-mobile.jpg",
                        message=(
                            f"visual anchor reference={ref!r} does not match "
                            f"^section-[0-9]+(-mobile)?\\.jpg$"
                        ),
                    )
                )
        elif atype == "both":
            # Per schema, 'both' anchors should still resolve — typically as
            # an e<int> with cross-modal context. Apply the dom rule.
            if _E_INDEX_PATTERN.match(ref) and ref not in baton_indexes:
                out.append(
                    BusinessRuleViolation(
                        rule="anchor_baton_resolves",
                        finding_path=path,
                        field=f"evidence_anchors[{j}].reference",
                        actual=ref,
                        expected="one of baton.elements[].e_index",
                        message=(
                            f"BOTH-type anchor reference={ref!r} (looks like e<int>) "
                            f"not found in baton.elements[]"
                        ),
                    )
                )
            elif _SCREENSHOT_PATTERN.match(ref):
                pass  # screenshot reference — valid for "both"
            elif not _E_INDEX_PATTERN.match(ref) and not _SCREENSHOT_PATTERN.match(ref):
                # Free-form dom path with type='both' — accepted; uncheckable
                pass
    return out


# ---------------------------------------------------------------------------
# Phase L checks
# ---------------------------------------------------------------------------


def _check_surface_in_vocabulary(
    finding: dict, path: str, effective_vocab: set[str]
) -> list[BusinessRuleViolation]:
    """Surface MUST be in (cluster_vocab ∪ baton.sections[].slug ∪ {'other'}).

    'other' surface requires a non-empty ``surface_note``.
    """
    surface = finding.get("surface", "")
    if not surface:
        return []  # schema requires it; missing is a schema-level issue

    if surface not in effective_vocab:
        # Show a sample of the vocab in the error to make the fix obvious
        sample = ", ".join(sorted(effective_vocab)[:8])
        more = "" if len(effective_vocab) <= 8 else f", ... ({len(effective_vocab)} total)"
        return [
            BusinessRuleViolation(
                rule="surface_in_vocabulary",
                finding_path=path,
                field="surface",
                actual=surface,
                expected=f"one of: {sample}{more}",
                message=(
                    f"surface={surface!r} is not in the cluster's allowed vocabulary, "
                    f"baton sections, or the literal 'other'. Pick from the cluster's "
                    f"surface_vocabulary, a baton section slug, or use 'other' with a "
                    f"non-empty surface_note explaining the gap."
                ),
            )
        ]

    if surface == "other":
        note = (finding.get("surface_note") or "").strip()
        if not note:
            return [
                BusinessRuleViolation(
                    rule="surface_other_requires_note",
                    finding_path=path,
                    field="surface_note",
                    actual="<empty>",
                    expected="non-empty string ≤ 240 chars",
                    message=(
                        "surface='other' requires a non-empty surface_note. "
                        "Briefly explain what concept the cluster vocabulary "
                        "should grow to cover so the operator can tune."
                    ),
                )
            ]
    return []


def _check_baton_precedence(
    finding: dict,
    path: str,
    baton: dict | None,
    desktop_baton: dict | None,
    mobile_baton: dict | None,
) -> list[BusinessRuleViolation]:
    """Heuristic: if finding's prose verbatim-quotes element text, baton_index should match.

    Looks for quoted strings in observation/recommendation; finds baton elements
    whose ``text_content`` contains the quoted string; if the cited element doesn't
    match any quoted phrase BUT another element does, flag.

    Soft check — fires only on obvious mismatches. The full precedence rule
    (verbatim anchor > absence anchor > lowest e_index tie-break) is enforced
    primarily through the prompt; this validator catches the egregious cases.
    """
    bi = (finding.get("element") or {}).get("baton_index", "")
    if not bi or bi == "absent":
        return []

    obs = finding.get("observation", "") or ""
    rec = finding.get("recommendation", "") or ""
    prose = f"{obs}\n{rec}"

    quotes = _VERBATIM_QUOTE_PATTERN.findall(prose)
    if not quotes:
        return []

    elements: list[dict] = []
    for b in (baton, desktop_baton, mobile_baton):
        if b is not None:
            elements.extend(b.get("elements") or [])
    if not elements:
        return []

    by_e_index = {el.get("e_index"): el for el in elements if el.get("e_index")}
    cited = by_e_index.get(bi) or {}
    cited_text = (cited.get("text_content") or "").lower()

    # If any quoted phrase matches the cited element's text, we're good.
    for q in quotes:
        ql = q.lower().strip()
        if ql and ql in cited_text:
            return []

    # No quote matched the cited element. Find any element where some quote does match.
    for q in quotes:
        ql = q.lower().strip()
        if not ql:
            continue
        for el in elements:
            tc = (el.get("text_content") or "").lower()
            if ql in tc and el.get("e_index") != bi:
                return [
                    BusinessRuleViolation(
                        rule="baton_precedence_verbatim_anchor",
                        finding_path=path,
                        field="element.baton_index",
                        actual=bi,
                        expected=el.get("e_index", ""),
                        message=(
                            f"Finding prose verbatim-quotes {q!r}, which matches "
                            f"text_content of baton element {el.get('e_index')!r} — "
                            f"but finding cites {bi!r} instead. Anchor at the "
                            f"verbatim-named element per the baton precedence rule."
                        ),
                    )
                ]

    # No clear match either way — accept (heuristic can't decide).
    return []


def _check_within_emission_unique_anchors(
    emission: dict,
) -> list[BusinessRuleViolation]:
    """Within-emission uniqueness: no duplicate (surface, baton_index, verdict) tuples.

    For ``baton_index='absent'``, relax to: bounce only if title-token Jaccard ≥
    ``_ABSENT_FINDING_JACCARD_THRESHOLD`` (0.7) AND ``(surface, verdict)`` matches.
    Protects legitimate distinct-but-missing things on the same surface (e.g.,
    no JSON-LD vs no OG image vs no GTIN — all ``(meta-tag, absent, FAIL)`` but
    conceptually distinct, low Jaccard between titles).
    """
    findings = emission.get("findings", [])
    violations: list[BusinessRuleViolation] = []

    by_tuple: dict[tuple[str, str, str], list[tuple[int, dict]]] = {}
    for i, f in enumerate(findings):
        key = (
            f.get("surface", ""),
            (f.get("element") or {}).get("baton_index", ""),
            f.get("verdict", ""),
        )
        by_tuple.setdefault(key, []).append((i, f))

    for (surface, bi, verdict), group in by_tuple.items():
        if len(group) < 2:
            continue

        if bi == "absent":
            # Pairwise Jaccard check; flag only on similar titles
            for ai, (i_a, f_a) in enumerate(group):
                for i_b, f_b in group[ai + 1 :]:
                    j = _title_jaccard(f_a.get("title", ""), f_b.get("title", ""))
                    if j >= _ABSENT_FINDING_JACCARD_THRESHOLD:
                        violations.append(
                            BusinessRuleViolation(
                                rule="within_emission_unique_anchors_absent",
                                finding_path=f"findings[{i_a}]",
                                field="(surface, baton_index='absent', verdict)",
                                actual=(
                                    f"({surface}, absent, {verdict}); "
                                    f"title Jaccard {j:.2f} with findings[{i_b}]"
                                ),
                                expected="distinct titles (Jaccard < 0.7) OR merged finding",
                                message=(
                                    f"Two 'absent' findings share (surface={surface}, "
                                    f"verdict={verdict}) AND have title-token Jaccard "
                                    f"{j:.2f} ≥ 0.7 — likely duplicates. Merge them, "
                                    f"or differentiate the titles enough to drop similarity."
                                ),
                            )
                        )
        else:
            # Strict: any duplicate is a violation
            i_a, _ = group[0]
            i_b, _ = group[1]
            violations.append(
                BusinessRuleViolation(
                    rule="within_emission_unique_anchors",
                    finding_path=f"findings[{i_a}]",
                    field="(surface, baton_index, verdict)",
                    actual=f"({surface}, {bi}, {verdict}); duplicate of findings[{i_b}]",
                    expected="unique tuple within emission",
                    message=(
                        f"findings[{i_a}] and findings[{i_b}] share the same "
                        f"(surface={surface}, baton_index={bi}, verdict={verdict}) "
                        f"tuple. Merge them into one finding before emitting."
                    ),
                )
            )

    return violations


def _title_jaccard(a: str, b: str) -> float:
    """Token-set Jaccard similarity on lowercase title tokens, stopwords removed."""
    tokens_a = {t for t in re.findall(r"\w+", a.lower()) if t not in _TITLE_STOPWORDS}
    tokens_b = {t for t in re.findall(r"\w+", b.lower()) if t not in _TITLE_STOPWORDS}
    union = tokens_a | tokens_b
    if not union:
        return 0.0
    return len(tokens_a & tokens_b) / len(union)


def _check_finding_count_in_band(
    emission: dict, band: FindingBand
) -> list[BusinessRuleViolation]:
    """findings[] count must be within band when status='complete'."""
    findings = emission.get("findings", [])
    n = len(findings)
    if n < band.min_count or n > band.max_count:
        if n > band.max_count:
            fix = f"Trim to {band.max_count} or fewer findings."
        else:
            fix = (
                f"Either add findings to reach {band.min_count}, or use "
                f"status='skipped' with skip_reason if the page genuinely "
                f"doesn't yield {band.min_count}+ findings for this cluster."
            )
        return [
            BusinessRuleViolation(
                rule="finding_count_in_band",
                finding_path="(emission)",
                field="findings",
                actual=f"{n} findings",
                expected=f"{band.min_count}-{band.max_count}",
                message=(
                    f"Cluster's target_finding_count band is "
                    f"{band.min_count}-{band.max_count}, but emission has {n}. {fix}"
                ),
            )
        ]
    return []


# ---------------------------------------------------------------------------
# Retry-prompt construction
# ---------------------------------------------------------------------------


def build_retry_prompt(
    cluster: str,
    device: str,
    violations: list[BusinessRuleViolation],
) -> str:
    """Construct a retry prompt the lead embeds when business rules failed.

    Phase L: rewrites preamble to be category-agnostic (covers structural
    integrity rules + determinism rules); sorts violations deterministically
    by (finding_path, field, rule) for cache-friendly retry prompts.
    """
    sorted_violations = sorted(
        violations,
        key=lambda v: (v.finding_path, v.field, v.rule),
    )

    lines = [
        f"Your previous emission for cluster={cluster!r} device={device!r} passed schema validation",
        "but failed validation across structural integrity rules and determinism rules.",
        "Structural rules check cross-document references (citations, baton elements,",
        "screenshot anchors). Determinism rules constrain surface labels, baton choice,",
        "verdict thresholds, within-emission uniqueness, and finding count.",
        "",
        "Violations:",
    ]
    for v in sorted_violations[:_MAX_VIOLATIONS_IN_RETRY_PROMPT]:
        lines.append(f"- {v}")
    if len(sorted_violations) > _MAX_VIOLATIONS_IN_RETRY_PROMPT:
        lines.append(
            f"- ... and {len(sorted_violations) - _MAX_VIOLATIONS_IN_RETRY_PROMPT} more"
        )
    lines += [
        "",
        "Re-emit a single JSON object validating against schema/cluster-emission-v1.json.",
        "Address each violation by either correcting the field value or removing the finding.",
        "If you cannot ground a finding to a real baton element or section screenshot, do not",
        "emit it — an unresolvable anchor is worse than a missing finding.",
        "No prose, no markdown fences, no preamble.",
    ]
    return "\n".join(lines)


def _check_baton_sections_disjoint(baton: dict) -> list[BusinessRuleViolation]:
    """Rule (Phase M, 2026-05-01): baton.sections[] MUST be disjoint by scroll_y range.

    For all adjacent pairs sorted by scroll_y_top: section[i].scroll_y_bottom <
    section[i+1].scroll_y_top, UNLESS section[i+1].overlap_reason is set
    (intentional overlap escape hatch).

    JSON Schema cannot compare across array items, so we enforce here. Closes
    Codex P2: baton-v1.json description claims disjoint-sections invariant, but
    schema-level validation cannot enforce it. Without this lint, malformed
    batons (last-section ranges that overlap with the previous section, or
    capture-artifact overlaps) pass validation silently.

    Catches the awdmods.com 2026-05-01 desktop baton: section[0] y=0-1080,
    section[1] y=900-1980 — 180px overlap, no overlap_reason set.
    """
    out: list[BusinessRuleViolation] = []
    sections = baton.get("sections") or []
    if not sections:
        return out
    # Sort by scroll_y_top so reasoning works even if the acquirer wrote sections
    # out of order (rare but possible with multi-pass capture).
    indexed = list(enumerate(sections))
    indexed.sort(key=lambda pair: pair[1].get("scroll_y_top", 0))
    for k in range(len(indexed) - 1):
        i, sec_a = indexed[k]
        j, sec_b = indexed[k + 1]
        bot_a = sec_a.get("scroll_y_bottom")
        top_b = sec_b.get("scroll_y_top")
        if bot_a is None or top_b is None:
            continue
        try:
            if int(bot_a) < int(top_b):
                continue  # Disjoint — pass.
        except (TypeError, ValueError):
            continue
        if sec_b.get("overlap_reason"):
            continue  # Documented intentional overlap — pass.
        out.append(
            BusinessRuleViolation(
                rule="baton_sections_disjoint",
                finding_path="(baton)",
                field=f"sections[{j}].scroll_y_top",
                actual=str(top_b),
                expected=f"> sections[{i}].scroll_y_bottom ({bot_a})",
                message=(
                    f"baton.sections[{i}].scroll_y_bottom={bot_a} overlaps with "
                    f"baton.sections[{j}].scroll_y_top={top_b}. Sections must be disjoint by "
                    f"scroll_y range (Phase M invariant). Either fix the acquirer's section "
                    f"detection to emit non-overlapping ranges (preferred), or set "
                    f"sections[{j}].overlap_reason to document an intentional overlap. "
                    f"Without this fix, proposed_anchor placements with kind='section' + "
                    f"placement='section-bottom-overlay' on section[{i}] will land inside "
                    f"section[{j}]'s screenshot."
                ),
            )
        )
    return out


__all__ = [
    "BusinessRuleViolation",
    "FindingBand",
    "build_retry_prompt",
    "validate_business_rules",
]
