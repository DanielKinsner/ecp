"""Data model for the ECP Audit Assembly package.

v2 migration (Phase E, 2026-04-27):

- ``Finding`` is now ``frozen=True``. All mutations use ``dataclasses.replace()``
  to produce a new instance — eliminates the in-place writes at the v1
  ``dedup.py:_absorb_losers`` site (the original ``winner.merged_from.append(ref)``
  + ``winner.ethics_state = "ADJACENT"`` pattern). Frozen-dataclass merging is
  the deterministic-Python invariant Phase E builds: same inputs → byte-identical
  outputs across runs because no shared mutable state can drift.

- v2 fields added with defaults so the v1 ``parser.py`` constructor calls keep
  working without modification (per Kieran's rule: no new code touches
  ``parser.py`` after Phase E):

    - ``scope: str`` ("page" | "device", default "device")
    - ``change_type: str`` ("copy" | "css" | "html-attr" | "component" | "feature", default "")
    - ``change_scope: str`` ("single-file" | "component" | "cross-cutting", default "")
    - ``evidence_anchors: tuple[EvidenceAnchor, ...]`` (default empty tuple — tuple
      not list so the frozen dataclass is fully immutable; ``replace()`` rebuilds)
    - ``confidence: float | None`` (default None; specialist self-rated 0.0-1.0)
    - ``baton_index: str`` (default ""; "e<int>" or "absent")
    - ``surface: str`` (default ""; baton section slug or surface taxonomy)

- ``EvidenceAnchor`` is the new typed structure for ``evidence_anchors[]``.
  Frozen, hashable, total-ordered for stable sort.

- ``EVIDENCE_TIER_RANK`` is the canonical Bronze/Silver/Gold ordering used by
  the dedup tie-breaker and Priority Path Severity-mode sort. Bronze=1,
  Silver=2, Gold=3 — higher is stronger.

See docs/plans/2026-04-27-feat-ecp-v2-redesign-plan.md Phase E.2a.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

PRIORITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}

EVIDENCE_TIER_RANK = {"Bronze": 1, "Silver": 2, "Gold": 3}
EVIDENCE_TIER_BY_RANK = {v: k for k, v in EVIDENCE_TIER_RANK.items()}


@dataclass(frozen=True)
class EvidenceAnchor:
    """One concrete tie-point for a finding (DOM element or screenshot region).

    Frozen so the parent ``Finding`` is fully immutable. Tuples are used in
    place of lists in the parent so the whole graph supports
    ``dataclasses.replace()`` without needing custom copy semantics.
    """

    type: str  # "dom" | "visual" | "both"
    reference: str  # e<int> for dom, section-N(-mobile)?.jpg for visual
    scroll_y: int | None = None  # required for visual-position findings
    viewport: str = ""  # "desktop" | "mobile" — defaults to finding.device
    context: str = ""  # optional human-readable context

    def sort_key(self) -> tuple:
        """Stable total ordering for deterministic iteration."""
        return (
            self.type,
            self.reference,
            self.scroll_y if self.scroll_y is not None else -1,
            self.viewport,
        )


@dataclass(frozen=True)
class ProposedAnchor:
    """Placement hint for absent findings (architectural fix B, 2026-04-30).

    Discriminated union on ``kind``. The schema's oneOf rejects cross-variant
    fields at validation time; the empty-string / None defaults here let the
    Finding dataclass carry every variant without needing per-variant subclasses.
    Frozen for the same reason as ``EvidenceAnchor`` — the parent ``Finding``
    must remain fully immutable.

    Does NOT participate in finding identity / dedup. Identity stays
    surface-based (see scripts/assembly/business_rules.py and pipeline.py).
    Renderer reads this to decide WHERE to pin a hotspot when the underlying
    element does not exist on the page; everything upstream just rides along.
    """

    kind: str  # "element" | "section" | "viewport"
    placement: str  # constrained per kind by schema oneOf
    viewport: str  # "mobile" | "desktop" — no "both" in v1
    element_baton_index: str = ""  # set iff kind="element"
    section_index: int | None = None  # set iff kind="section"
    viewport_trigger: str = ""  # set iff kind="viewport"
    reason: str = ""  # operator-tooltip prose ONLY; renderer must NOT parse


@dataclass(frozen=True)
class Finding:
    """A single finding parsed from either a v1 cluster file or v2 emission.

    Frozen — see module docstring. v2 fields default so v1 ``parser.py``
    keeps working unchanged. v2 ``json_parser.py`` populates them from the
    cluster-emission JSON.
    """

    cluster: str
    device: str
    local_index: int  # 1-based within cluster file
    verdict: str  # FAIL or PARTIAL (v1) / FAIL | PARTIAL | PASS (v2)
    section: str
    element: str
    element_normalized: str
    source: str  # VISUAL/CODE/BOTH
    priority: str  # CRITICAL/HIGH/MEDIUM/LOW
    priority_rank: int  # 0-3 per PRIORITY_ORDER
    observation: str
    recommendation: str
    reference: str
    title: str = ""
    why_matters: str = ""
    citation: str = ""
    tier: str = ""  # Gold | Silver | Bronze
    synthesis_hint: str = ""
    ethics_state: str = ""  # BLOCK/ADJACENT/CLEAR/empty
    source_url: str = ""
    raw_block: str = ""  # original code-fenced text (v1) — empty for v2
    merged_from: tuple[str, ...] = ()  # tuple not list so frozen replace() works
    display_index: int = 0  # 1-based; assigned by pipeline.assign_display_indices
    # ----- v2 fields (default-empty so v1 callers keep working) -----
    scope: str = "device"  # "page" | "device" — v1 always "device"
    change_type: str = ""  # copy | css | html-attr | component | feature
    change_scope: str = ""  # single-file | component | cross-cutting
    evidence_anchors: Tuple[EvidenceAnchor, ...] = ()
    confidence: float | None = None  # specialist self-rating 0.0-1.0
    baton_index: str = ""  # "e<int>" or "absent" — v2 hotspot resolution key
    surface: str = ""  # v2 surface slug
    proposed_anchor: ProposedAnchor | None = None  # placement hint for absent findings (fix B)
    # Phase 2 visual evidence taxonomy + Phase 4a anchor candidates
    # (added 2026-05-18). Producer-authored visual_evidence — when set
    # by the specialist — survives the parse pipeline so downstream
    # consumers (marker pipeline, review-state, renderer) can honor it.
    # Pre-Phase-4a-hardening, the field was lost during json_parser →
    # FinalizedFindings.build → loader_dict because Finding didn't carry
    # it. Stored as an arbitrary dict to keep the dataclass simple;
    # schema validation happens at the json_parser entry, not on this
    # field.
    visual_evidence: dict | None = None

    @staticmethod
    def normalize_element(element: str) -> str:
        """Normalize an element selector for v1 dedup comparison.

        v2 dedup uses ``baton_index`` as the structural identity key and
        does not need ``element_normalized``. This helper stays for v1
        ``parser.py`` compatibility per Kieran's no-touch rule.

        - Removes parenthetical descriptions: ``div.rating (five hollow stars)`` -> ``div.rating``
        - Lowercases and strips whitespace
        - Removes trailing pseudo-selectors (``:hover``, ``::before``)
        """
        normalized = re.sub(r"\s*\([^)]*\)", "", element)
        normalized = normalized.strip().lower()
        normalized = re.sub(r":{1,2}[a-z-]+$", "", normalized)
        return normalized.strip()


@dataclass(frozen=True)
class PassFinding:
    """Represents a v1 PASS finding.

    Frozen for symmetry with Finding. v2 PASS findings are full
    ``Finding`` instances with ``verdict='PASS'`` — this class stays
    only for v1 ``parser.py`` compatibility.
    """

    cluster: str
    text: str


@dataclass
class DedupeResult:
    """Output of the dedup engine.

    Mutable container — fields are populated incrementally by the dedup
    layers. The ``Finding`` instances inside are frozen, so re-assignment
    of the list fields (``kept = [...]``) is the mutation pattern, not
    in-place edits to the findings themselves.
    """

    kept: List[Finding] = field(default_factory=list)
    auto_merged: List[dict] = field(default_factory=list)
    fuzzy_candidates: List[dict] = field(default_factory=list)
    ethics_findings: List[Finding] = field(default_factory=list)
    pass_findings: List[PassFinding] = field(default_factory=list)
    synthesis_groups: Dict[str, List[Finding]] = field(default_factory=dict)

    def all_actionable(self) -> List[Finding]:
        """Return the union of buckets every downstream renderable consumer needs.

        ``kept`` holds non-ethics findings that survived dedup.
        ``ethics_findings`` holds BLOCK/ADJACENT ethics findings (CLEAR ethics
        land in ``kept`` as PASS findings instead).

        Both buckets must feed into ``FinalizedFindings.build`` for any
        consumer that produces canonical f_refs, renderable refs, or HTML
        output. Forgetting ``ethics_findings`` silently drops ADJACENT/BLOCK
        ethics from canonical-refs while the renderer still includes them,
        causing namespace drift across markdown/HTML surfaces. See the
        2026-05-18-5ff7a91f engagement post-mortem (docs/ecp/
        2026-05-18-5ff7a91f-fixed/CLAUDE-FIXED-VS-ORIGINAL-DIFF.md) for the
        documented failure case this helper exists to prevent.

        Consumers that intentionally need a different subset (e.g. the dedup
        engine's internal scoring layer that wants only ``kept``) should call
        ``deduped.kept`` directly with an explanatory comment; the cross-
        consumer parity test in ``tests/test_dedup_consumer_parity.py`` will
        catch new consumers that drift from the union.
        """
        return list(self.kept) + list(self.ethics_findings)
