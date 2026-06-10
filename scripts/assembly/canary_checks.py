"""Phase I substantive canary checks (2026-04-28).

Three load-bearing canaries the audit lead runs at audit completion (after
``<phase_synthesize_v2>`` and before transitioning ``meta.json`` to
``phase: complete``):

1. **ethics_findings_have_source_urls** — every ethics finding with
   ``ethics_state`` in ``{BLOCK, ADJACENT}`` carries a ``source_url`` AND
   that URL does NOT contain the audited domain (preventing self-cite
   filler that the v1 reconciliation gate already catches at the
   reconciliation step; this canary surfaces a regression).

2. **element_index_match_rate** — at least 80 percent of ``**ELEMENT:**``
   lines in ``audit-{device}.md`` cite a baton element index (e.g.,
   ``at e23``). Effectively 100 percent post-Phase A on v2 (specialists
   emit baton_index directly), but the canary catches regression if a
   future change causes specialists to revert to fuzzy CSS selectors.

3. **cross_device_ethics_diff** — the count of actionable ethics findings
   (BLOCK + ADJACENT) that render into ``audit-desktop.md`` differs by
   at most 1 from the count that renders into ``audit-mobile.md``.
   Catches the case where the ethics subagent's emission rendered
   asymmetrically across the two device documents.

Phase 6 (2026-06-10) — ethics/legal enforcement batch (C18 + H2 + H3):

4. **ethics_findings_hedge_law_on_adjacent** (C18) — any ADJACENT finding
   whose ``observation`` / ``recommendation`` / ``why_this_matters`` cites
   a law / regulation without hedge phrasing fails. Enforces product.md
   §4.1 — misquoted / over-applied law is the highest-bar violation.

5. **ethics_source_url_against_registry** (H2) — every BLOCK / ADJACENT
   ``source_url`` must appear in the Source Registry parsed AT RUNTIME
   from ``references/ethics-gate.md``; URLs in the Vacated Rules tracker
   fail with a distinct message.

6. **recommendations_no_dark_patterns** (H3) — every finding's
   ``recommendation`` text plus every synth ``priority_path[].narrative``
   is scanned for dark-pattern-recommending shapes ("add a countdown
   timer", "pre-check the …"). Removal recommendations ("remove the fake
   countdown") are allowed. Closes the product.md §8 guardrail (ECP must
   never recommend a dark pattern even if instructed to).

These are PURE FUNCTIONS that read engagement artifacts and return
structured result dicts. The lead invokes them at audit completion, writes
the results to ``audit-trace.log``, and writes ``lead-reflection.md`` with
any non-passing canaries documented.

Authored Phase I (2026-04-28). Phase 6 ethics/legal batch added 2026-06-10.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlparse

from .reflection_state import REFLECTION_STATE_COMPLETE, VALID_REFLECTION_STATES


# Canonical pattern for a baton element index reference in an ELEMENT line.
# Matches "at e0", "at e23", "at e9999"; case-sensitive; word-boundary anchored
# to avoid matching "at e2 (y=" inside a longer phrase that happens to start
# with "at" followed by something that's not the e-prefixed index.
_ELEMENT_INDEX_RE = re.compile(r"\bat\s+e\d+\b")

# Canonical pattern for an ELEMENT line in the structured-fields format
# (see contracts/synthesizer-v2.md "Per-finding rendering format" spec).
_ELEMENT_LINE_RE = re.compile(r"^\*\*ELEMENT:\*\*\s*(.+?)\s*$", re.MULTILINE)

# An "off-baton" line denotes a finding about an element that does not
# need a baton_index reference. Two cases:
#
# 1. ABSENT — the page lacks the element entirely; the finding is about
#    its absence. Synthesizer phrasing varies across runs:
#    "(absent — proposed location: ...)" OR
#    "absent — proposed location: ..." (no parens).
# 2. ON-PAGE BUT NOT IN BATON — the element exists in the DOM but the
#    acquirer's baton doesn't capture it (the baton is a curated subset,
#    not a full DOM dump). Specialist describes by tag/role/text instead.
#    Synthesizer phrasing: "(absent from baton)", "(not in baton)",
#    "(no baton entry)", "(absent from baton element index)".
#
# Both cases are off-baton-by-design and excluded from the denominator;
# the canary measures "of present-AND-baton-indexed-claimable findings,
# what fraction actually cite ``at eN``?" It does NOT penalize the
# acquirer's curated baton coverage.
#
# Phase K (2026-04-29) refinement: the leading-absent pattern's opening
# paren is now optional. The Phase J D2 fixture wrapped absent in parens
# but Phase K dispatch runs surfaced synth output where "absent — proposed
# location" appears without parens. The canary's intent is to detect the
# absence phrasing regardless of parenthesization.
_ELEMENT_ABSENT_RE = re.compile(
    r"(?:^|\s)\(?absent[\s—\-:)]"
    r"|\babsent\s+from\s+baton\b"
    r"|\bnot\s+in\s+baton\b"
    r"|\bno\s+baton\s+(?:entry|index)\b",
    re.IGNORECASE,
)

# Canonical pattern for a finding heading in audit-{device}.md.
# Matches "### {cluster} F-NN — Title" or "#### {cluster} F-NN — Title".
_FINDING_HEADING_RE = re.compile(
    r"^#{3,4}\s+([a-z][\w-]*)\s+F-(\d{2})(?:\s+[—\-]\s+(.*?))?\s*$",
    re.MULTILINE | re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Result shapes
# ---------------------------------------------------------------------------


class CanaryResult(TypedDict):
    """Common shape for canary results."""

    name: str
    passed: bool
    summary: str
    detail: dict


# ---------------------------------------------------------------------------
# Canary 1 — ethics_findings_have_source_urls
# ---------------------------------------------------------------------------


def check_ethics_findings_have_source_urls(
    ethics_findings_path: Path,
    audited_domain: str | None = None,
) -> CanaryResult:
    """Verify BLOCK/ADJACENT ethics findings have valid source_url.

    Pass criteria:
    - Every finding with ``ethics_state`` in ``{BLOCK, ADJACENT}`` has a
      non-empty ``source_url`` field.
    - The ``source_url`` does NOT contain the audited domain (to prevent
      self-cite filler — a finding citing the page being audited is not
      a regulation/research source).

    CLEAR ethics findings are NOT required to have ``source_url`` (the
    finding is informational; no regulation reference needed). Findings
    without ``ethics_state`` (i.e., non-ethics findings somehow in this
    file) are skipped with a note in detail.

    Args:
        ethics_findings_path: path to ethics-findings.json. If the file
            doesn't exist, the canary returns a SOFT failure (passed=False,
            summary explains the missing file). The lead should treat
            this as a separate "ethics didn't run" assertion failure.
        audited_domain: domain of the page being audited (e.g., "slingmods.com").
            Used to detect self-cite filler. If None or empty, the
            self-cite check is skipped (only the non-empty source_url
            check runs).

    Returns:
        CanaryResult with detail keys:
            - 'total_actionable': count of BLOCK + ADJACENT findings
            - 'missing_source_url': list of {f_ref, ethics_state, title}
              for findings missing source_url
            - 'self_cite_filler': list of {f_ref, ethics_state, source_url}
              for findings whose source_url contains the audited domain
            - 'clear_count': count of CLEAR findings (informational)
    """
    if not ethics_findings_path.exists():
        return CanaryResult(
            name="ethics_findings_have_source_urls",
            passed=False,
            summary=f"ethics-findings.json not found at {ethics_findings_path}",
            detail={"file_missing": True},
        )

    try:
        data = json.loads(ethics_findings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return CanaryResult(
            name="ethics_findings_have_source_urls",
            passed=False,
            summary=f"ethics-findings.json unreadable: {exc}",
            detail={"parse_error": str(exc)},
        )

    if not isinstance(data, dict):
        return CanaryResult(
            name="ethics_findings_have_source_urls",
            passed=False,
            summary="ethics-findings.json root is not a JSON object",
            detail={"root_type": type(data).__name__},
        )
    findings = data.get("findings")
    if not isinstance(findings, list):
        findings = []
    audited_host = _domain_of(audited_domain) if audited_domain else None

    actionable_findings = []
    missing_source_url: list[dict] = []
    self_cite_filler: list[dict] = []
    clear_count = 0

    for f in findings:
        if not isinstance(f, dict):
            continue
        state = (f.get("ethics_state") or "").upper()
        if state in {"BLOCK", "ADJACENT"}:
            actionable_findings.append(f)
            local_id = f.get("local_id")
            try:
                f_ref = f"ethics F-{int(local_id):02d}"
            except (TypeError, ValueError):
                f_ref = "ethics F-??"
            source_url = (f.get("source_url") or "").strip()

            if not source_url:
                missing_source_url.append({
                    "f_ref": f_ref,
                    "ethics_state": state,
                    "title": f.get("title", "")[:80],
                })
                continue

            if audited_host:
                src_host = _domain_of(source_url)
                if src_host and (src_host == audited_host or src_host.endswith("." + audited_host)):
                    self_cite_filler.append({
                        "f_ref": f_ref,
                        "ethics_state": state,
                        "source_url": source_url,
                    })
        elif state == "CLEAR":
            clear_count += 1

    passed = not (missing_source_url or self_cite_filler)
    if passed:
        summary = (
            f"{len(actionable_findings)} actionable ethics finding(s) all carry "
            f"valid non-self-cite source_url ({clear_count} CLEAR findings skipped)"
        )
    else:
        parts = []
        if missing_source_url:
            parts.append(f"{len(missing_source_url)} missing source_url")
        if self_cite_filler:
            parts.append(f"{len(self_cite_filler)} self-cite filler")
        summary = (
            f"{len(actionable_findings)} actionable ethics finding(s); "
            f"{', '.join(parts)}"
        )

    return CanaryResult(
        name="ethics_findings_have_source_urls",
        passed=passed,
        summary=summary,
        detail={
            "total_actionable": len(actionable_findings),
            "missing_source_url": missing_source_url,
            "self_cite_filler": self_cite_filler,
            "clear_count": clear_count,
        },
    )


def _domain_of(url_or_host: str) -> str:
    """Return the canonical lowercased host from a URL or host string.

    Strips ``www.`` prefix and any trailing slashes. Returns empty string
    on a malformed input rather than raising — the caller treats empty as
    "skip the check".
    """
    if not url_or_host:
        return ""
    s = url_or_host.strip().lower()
    if "://" in s:
        try:
            host = urlparse(s).netloc
        except ValueError:
            return ""
    else:
        host = s.split("/")[0]
    if host.startswith("www."):
        host = host[4:]
    return host


# ---------------------------------------------------------------------------
# Canary 2 — element_index_match_rate
# ---------------------------------------------------------------------------


def check_element_index_match_rate(
    audit_paths: list[Path],
    threshold: float = 0.8,
) -> CanaryResult:
    """Verify ELEMENT lines cite baton element indices at the threshold rate.

    Counts ``**ELEMENT:**`` lines across all provided audit markdown files.
    Lines for ABSENT elements (``(absent — proposed location: ...)``) are
    excluded from the denominator: those findings correctly do NOT carry
    a baton_index because the element doesn't exist on the page. The
    canary measures "of findings that cite a present element, what
    fraction use baton_index e<N>?" Pass if matched / present_total >=
    threshold.

    Phase A locked specialists emitting ``baton_index`` directly for
    present-element findings; effectively 100 percent on v2. The canary
    fires when a future change regresses specialists to fuzzy CSS
    selectors instead.

    Args:
        audit_paths: list of audit-{device}.md paths to scan. Typically
            ``[engagement_dir / "audit-desktop.md", engagement_dir / "audit-mobile.md"]``.
            Missing files are tolerated (their counts are zero); a fully-empty
            input list returns a SOFT failure.
        threshold: pass criterion. Default 0.8 (80 percent).

    Returns:
        CanaryResult with detail keys:
            - 'total_elements': total ELEMENT lines across all files
            - 'present_elements': total minus absent-element lines
              (the denominator the rate is computed against)
            - 'matched': present_elements lines that contain ``at eN``
            - 'absent': total ELEMENT lines that mark element as absent
            - 'rate': matched / present_elements (0.0 if no present elements)
            - 'threshold': the threshold the check ran against
            - 'per_file': list of {path, total, present, matched, absent, rate}
    """
    if not audit_paths:
        return CanaryResult(
            name="element_index_match_rate",
            passed=False,
            summary="No audit paths provided",
            detail={"empty_input": True, "threshold": threshold},
        )

    per_file: list[dict] = []
    grand_total = 0
    grand_matched = 0
    grand_absent = 0

    for path in audit_paths:
        if not path.exists():
            per_file.append({
                "path": str(path),
                "exists": False,
                "total": 0,
                "present": 0,
                "matched": 0,
                "absent": 0,
                "rate": 0.0,
            })
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            per_file.append({
                "path": str(path),
                "exists": True,
                "read_error": str(exc),
                "total": 0,
                "present": 0,
                "matched": 0,
                "absent": 0,
                "rate": 0.0,
            })
            continue

        elements = _ELEMENT_LINE_RE.findall(text)
        total = len(elements)
        absent = sum(1 for line in elements if _ELEMENT_ABSENT_RE.search(line))
        present = total - absent
        # G20 (2026-05-27): matched must count from PRESENT lines only.
        # Pre-fix, matched scanned the whole element list — but absent
        # findings often phrase their `proposed_anchor` prose as
        # `(absent — proposed location: ... at e3)`, so the `at eN`
        # token appears on lines the denominator (`present`) excludes.
        # Result: `matched / present` could exceed 1.0. Live evidence:
        # `docs/ecp/2026-05-27-625832a6` lead-reflection reported
        # `element_index_match_rate=1.23`, an impossible value for a
        # rate, because three absent-finding `at eN` mentions were
        # counted into the numerator but not the denominator.
        matched = sum(
            1 for line in elements
            if _ELEMENT_INDEX_RE.search(line) and not _ELEMENT_ABSENT_RE.search(line)
        )
        rate = matched / present if present else 0.0
        per_file.append({
            "path": str(path),
            "exists": True,
            "total": total,
            "present": present,
            "matched": matched,
            "absent": absent,
            "rate": rate,
        })
        grand_total += total
        grand_matched += matched
        grand_absent += absent

    grand_present = grand_total - grand_absent
    overall_rate = grand_matched / grand_present if grand_present else 0.0
    passed = overall_rate >= threshold and grand_present > 0
    summary = (
        f"element_index_match_rate={overall_rate:.3f} "
        f"({grand_matched}/{grand_present} present-element findings "
        f"cite baton index; {grand_absent} absent excluded) "
        f"vs threshold {threshold:.2f} -> {'PASS' if passed else 'FAIL'}"
    )

    return CanaryResult(
        name="element_index_match_rate",
        passed=passed,
        summary=summary,
        detail={
            "total_elements": grand_total,
            "present_elements": grand_present,
            "matched": grand_matched,
            "absent": grand_absent,
            "rate": overall_rate,
            "threshold": threshold,
            "per_file": per_file,
        },
    )


# ---------------------------------------------------------------------------
# Canary 3 — cross_device_ethics_diff
# ---------------------------------------------------------------------------


def check_cross_device_ethics_diff(
    desktop_audit_path: Path,
    mobile_audit_path: Path,
    max_diff: int = 1,
) -> CanaryResult:
    """Verify desktop and mobile audits surface the same ethics findings.

    v2 ethics is a single page-scope emission (one ethics-findings.json,
    no per-device variants). The synthesizer renders the actionable ethics
    findings (BLOCK / ADJACENT — CLEAR are filtered) into both
    ``audit-desktop.md`` and ``audit-mobile.md``. This canary asserts that
    rendering parity holds — the two device audits surface the same set
    of ethics findings within the ``max_diff`` tolerance.

    Pass criterion: ``abs(desktop_count - mobile_count) <= max_diff``.

    Args:
        desktop_audit_path: path to audit-desktop.md.
        mobile_audit_path: path to audit-mobile.md.
        max_diff: maximum allowed difference. Default 1 (one finding
            asymmetry tolerated for edge cases like a finding rendered
            into one device's section due to per-device evidence
            framing).

    Returns:
        CanaryResult with detail keys:
            - 'desktop_count': count of ``### ethics F-NN`` headings
            - 'mobile_count': count of ``### ethics F-NN`` headings
            - 'diff': abs(desktop_count - mobile_count)
            - 'max_diff': the threshold the check ran against
            - 'desktop_refs': list of f_refs found
            - 'mobile_refs': list of f_refs found
            - 'asymmetric_refs': refs in one but not the other
    """
    desktop_refs = _ethics_refs_in(desktop_audit_path)
    mobile_refs = _ethics_refs_in(mobile_audit_path)

    desktop_count = len(desktop_refs)
    mobile_count = len(mobile_refs)
    diff = abs(desktop_count - mobile_count)

    desktop_only = sorted(set(desktop_refs) - set(mobile_refs))
    mobile_only = sorted(set(mobile_refs) - set(desktop_refs))
    asymmetric_refs = []
    for ref in desktop_only:
        asymmetric_refs.append({"ref": ref, "in": "desktop_only"})
    for ref in mobile_only:
        asymmetric_refs.append({"ref": ref, "in": "mobile_only"})

    passed = diff <= max_diff
    summary = (
        f"ethics findings: desktop={desktop_count}, mobile={mobile_count}, "
        f"diff={diff} vs max_diff={max_diff} -> {'PASS' if passed else 'FAIL'}"
    )

    return CanaryResult(
        name="cross_device_ethics_diff",
        passed=passed,
        summary=summary,
        detail={
            "desktop_count": desktop_count,
            "mobile_count": mobile_count,
            "diff": diff,
            "max_diff": max_diff,
            "desktop_refs": sorted(desktop_refs),
            "mobile_refs": sorted(mobile_refs),
            "asymmetric_refs": asymmetric_refs,
        },
    )


def check_priority_path_count_parity(
    synthesizer_emission_path: Path,
    engagement_dir: Path,
) -> CanaryResult:
    """Phase 6 (2026-05-18) — Codex Q2/Q3/Q4: assert renderer Priority Path
    card count matches the synth's priority_path[] count on every device.

    Pre-Phase-6, the renderer's ``load_v2_priority_path`` silently dropped
    stories whose underlying refs all resolved on the OTHER device. The
    awdmods 2026-05-18 desktop run showed 4 cards in HTML vs 5 stories in
    audit-desktop.md — same engagement, two surfaces, divergent priority
    counts visible to the customer. Phase 6 made the loader retain those
    stories as faded "applies elsewhere" cards so the counts agree.

    This canary pins the contract: synth count == loader count for both
    desktop and mobile, when the loader path can run.

    Pass criterion: per-device loader count equals synth count, OR the
    loader couldn't run (no audit-{device}.md, no canonical refs)
    in which case the check is informational.
    """
    if not synthesizer_emission_path.exists():
        return CanaryResult(
            name="priority_path_count_parity",
            passed=True,
            summary="priority_path_count_parity: skipped (no synth emission)",
            detail={"reason": "synthesizer-emission-v1.json not present"},
        )
    try:
        synth = json.loads(synthesizer_emission_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return CanaryResult(
            name="priority_path_count_parity",
            passed=False,
            summary=f"priority_path_count_parity: FAIL — synth unreadable: {e}",
            detail={"error": str(e)},
        )
    synth_count = len(synth.get("priority_path") or [])

    # Try to run the loader against each device's audit/baton. Lazy import
    # so canary_checks doesn't pull the renderer module unless this check
    # actually runs.
    import sys as _sys
    repo_root = Path(__file__).resolve().parent.parent.parent
    if str(repo_root / "scripts") not in _sys.path:
        _sys.path.insert(0, str(repo_root / "scripts"))

    per_device: dict[str, dict] = {}
    overall_pass = True
    for device in ("desktop", "mobile"):
        audit_md = engagement_dir / f"audit-{device}.md"
        if not audit_md.exists():
            per_device[device] = {"skipped": True, "reason": f"no audit-{device}.md"}
            continue
        try:
            from report.v2_loader import (
                _engagement_cluster_emission_paths,
                _engagement_ethics_findings_path,
                build_canonical_view,
                load_v2_findings,
                load_v2_priority_path,
            )
            actionable_refs = {f["f_ref"] for f in load_v2_findings(engagement_dir, device)}
            _, aliases, _drops = build_canonical_view(
                _engagement_cluster_emission_paths(engagement_dir),
                _engagement_ethics_findings_path(engagement_dir),
            )
            stories = load_v2_priority_path(
                engagement_dir, actionable_refs=actionable_refs,
                ref_aliases=aliases, device=device,
            )
            loader_count = len(stories)
            per_device[device] = {
                "synth_count": synth_count,
                "loader_count": loader_count,
                "matches": loader_count == synth_count,
            }
            if loader_count != synth_count:
                overall_pass = False
        except Exception as e:  # pragma: no cover — defensive
            per_device[device] = {"error": str(e)}
            overall_pass = False

    summaries: list[str] = []
    for dev, info in per_device.items():
        if info.get("skipped"):
            summaries.append(f"{dev}=skip")
        elif info.get("error"):
            summaries.append(f"{dev}=error")
        else:
            mark = "OK" if info["matches"] else "DIVERGE"
            summaries.append(f"{dev}={info['loader_count']}/{synth_count} {mark}")

    return CanaryResult(
        name="priority_path_count_parity",
        passed=overall_pass,
        summary=(
            f"priority_path_count_parity: synth={synth_count} stories; "
            + ", ".join(summaries)
            + f" -> {'PASS' if overall_pass else 'FAIL'}"
        ),
        detail={"synth_count": synth_count, "per_device": per_device},
    )


def _ethics_refs_in(audit_path: Path) -> list[str]:
    """Return list of ethics f_refs (ethics F-NN) referenced as headings."""
    if not audit_path.exists():
        return []
    try:
        text = audit_path.read_text(encoding="utf-8")
    except OSError:
        return []
    refs: list[str] = []
    for m in _FINDING_HEADING_RE.finditer(text):
        cluster = m.group(1).lower()
        idx = int(m.group(2))
        if cluster == "ethics":
            refs.append(f"ethics F-{idx:02d}")
    return refs


# ---------------------------------------------------------------------------
# Canary 5 — clusters_represented (G16, 2026-05-27)
# ---------------------------------------------------------------------------


def check_clusters_represented(
    engagement_dir: Path,
) -> CanaryResult:
    """G16: every requested CRO cluster must have at least one canonical f_ref.

    Catches the silent-drop failure mode where ``build_canonical_view`` 's
    pre-G16 bare ``except Exception: continue`` swallowed schema-invalid
    cluster emissions wholesale. Run ``docs/ecp/2026-05-27-52f53a53`` lost
    6 of 12 cluster files (trust-credibility and content-seo entirely,
    plus the desktop halves of performance-ux and product-media) and the
    operator received an audit billed as "comprehensive (6 clusters)"
    that in fact rendered findings from only 2 CRO clusters on desktop —
    with all other canaries still reporting PASS. Exactly the §0
    untraceable-misleading failure mode the trust contract forbids.

    Pass criteria:
    - Every cluster in ``meta.json["clusters_used"]`` (with ``ethics``
      excluded — it's page-scope, not CRO) appears at least once in
      ``canonical-f-refs.json["valid_refs"]``.
    - ``canonical-frefs-dropped.json["dropped_count"] == 0`` (or the
      file is absent, e.g. for pre-G16 legacy engagement fixtures).

    Either condition failing fails the canary. The drops-file check
    matters as well as the missing-cluster check because a partial-drop
    that still leaves ≥1 finding per cluster surviving (e.g. one device
    of a cluster fails but the other passes) would slip past a pure
    cluster-presence check — but every drop is itself a trust violation
    that the operator must address before phase advance.

    Returns ``CanaryResult`` with detail keys:
        - ``expected_clusters``: sorted list from ``meta.json``
          (minus ``ethics``).
        - ``represented_clusters``: sorted list parsed from
          ``canonical-f-refs.json`` valid_refs (minus ``ethics``).
        - ``missing_clusters``: sorted ``expected - represented``.
        - ``dropped_count``: int from ``canonical-frefs-dropped.json``,
          0 if file absent.
        - ``dropped``: the per-emission drop records, if any.
    """
    meta_path = engagement_dir / "meta.json"
    canonical_path = engagement_dir / "canonical-f-refs.json"
    dropped_path = engagement_dir / "canonical-frefs-dropped.json"

    if not meta_path.exists() or not canonical_path.exists():
        # Pre-canonical-stage engagement (e.g., a test fixture that stops
        # before lead_prep runs). Skip with a PASS verdict so this canary
        # doesn't false-positive on partial fixtures.
        return CanaryResult(
            name="clusters_represented",
            passed=True,
            summary="clusters_represented: skipped (meta.json or canonical-f-refs.json absent)",
            detail={"reason": "pre-canonical-stage engagement"},
        )

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        canon = json.loads(canonical_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return CanaryResult(
            name="clusters_represented",
            passed=False,
            summary=f"clusters_represented: FAIL -- unreadable artifacts: {e}",
            detail={"error": str(e)},
        )

    clusters_used = meta.get("clusters_used")
    expected = (set(clusters_used) if isinstance(clusters_used, list) else set()) - {"ethics"}
    valid_refs = canon.get("valid_refs") or []
    represented = {
        ref.split(" F-", 1)[0]
        for ref in valid_refs
        if isinstance(ref, str) and " F-" in ref
    } - {"ethics"}
    missing = expected - represented

    dropped: list[dict] = []
    dropped_count = 0
    if dropped_path.exists():
        try:
            dropped_doc = json.loads(dropped_path.read_text(encoding="utf-8"))
            dropped = list(dropped_doc.get("dropped") or [])
            raw_count = dropped_doc.get("dropped_count")
            dropped_count = int(raw_count) if raw_count is not None else len(dropped)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            # Corrupted drops file: treat as zero drops here but the file
            # itself becoming unreadable is a separate operator concern;
            # don't conflate with the cluster-coverage signal.
            pass

    passed = not missing and dropped_count == 0
    if missing and dropped_count:
        summary = (
            f"clusters_represented: FAIL -- {len(missing)} cluster(s) missing "
            f"({sorted(missing)}) AND {dropped_count} emission(s) dropped"
        )
    elif missing:
        summary = (
            f"clusters_represented: FAIL -- {len(missing)} requested CRO "
            f"cluster(s) have zero canonical f_refs: {sorted(missing)}"
        )
    elif dropped_count:
        summary = (
            f"clusters_represented: FAIL -- {dropped_count} emission(s) dropped "
            f"by canonical view (see canonical-frefs-dropped.json)"
        )
    else:
        summary = (
            f"clusters_represented: PASS ({len(represented)}/{len(expected)} "
            f"requested CRO clusters represented; 0 emissions dropped)"
        )

    return CanaryResult(
        name="clusters_represented",
        passed=passed,
        summary=summary,
        detail={
            "expected_clusters": sorted(expected),
            "represented_clusters": sorted(represented),
            "missing_clusters": sorted(missing),
            "dropped_count": dropped_count,
            "dropped": dropped,
        },
    )


# ---------------------------------------------------------------------------
# Canary 6 — trace_counters_reconcile_with_artifacts (G22+G24, 2026-05-28)
# ---------------------------------------------------------------------------


# Trace-counter line patterns. The lead writes these as
# ``key: <int>`` (one per line) per ``contracts/trace-assertion-canary.md``.
# We tolerate optional whitespace and a leading ``#`` (some legacy headers
# wrote counters under a ``# Counters`` section with ``#`` prefixes on
# subsequent lines — accept both shapes).
# The integer is anchored by a trailing word boundary, then anything may follow
# (whitespace, a ``(wave2 6+6)`` parenthetical, or the contract template's
# ``← v2: ...`` arrow comment). The earlier form required the int at end-of-line,
# so any annotated counter — including the contract's own template lines — was
# silently skipped and defaulted to 0, producing a FALSE reconcile failure. The
# strong leading anchor (``^\s*#?\s*`` + an alpha/underscore key) plus first-match
# ``setdefault`` keep event-log prose from being mistaken for a counter.
_TRACE_COUNTER_RE = re.compile(
    r"^\s*#?\s*([a-z_][a-z0-9_]*)\s*:\s*(\d+)\b.*$",
    re.IGNORECASE | re.MULTILINE,
)


# Counter aliases per ``contracts/dispatch-contract.md`` §"Backwards
# compatibility": v1 audits emit `team_spawned_acquirers` /
# `team_spawned_auditors`; v2 audits emit `subagent_spawned_acquirers` /
# `subagent_spawned_specialists` (Phase H.2; `team_spawned_specialists` / `team_spawned_auditors` retained as aliases). The reconciliation canary accepts any
# naming as evidence the role ran — checking the role's actual spawn
# count against observed artifact count, not the specific counter name.
_ACQUIRER_COUNTERS = ("subagent_spawned_acquirers", "team_spawned_acquirers")
_SPECIALIST_COUNTERS = ("subagent_spawned_specialists", "team_spawned_specialists", "team_spawned_auditors")
_ETHICS_COUNTERS = ("subagent_spawned_ethics",)
_SYNTHESIZER_COUNTERS = ("subagent_spawned_synthesizer",)
_CLUSTER_FILES_COUNTERS = ("cluster_files_written",)


def _parse_trace_counters(trace_text: str) -> dict[str, int]:
    """Extract ``counter_name -> int`` pairs from ``audit-trace.log`` text.

    The trace mixes counters, event-log lines, and free prose. Only lines
    that match the canonical ``key: <int>`` shape are extracted; everything
    else is ignored. Keys are lowercased for comparison (the contract uses
    lowercase but operator-edited files sometimes drift).
    """
    counters: dict[str, int] = {}
    for match in _TRACE_COUNTER_RE.finditer(trace_text):
        key = match.group(1).lower()
        try:
            value = int(match.group(2))
        except ValueError:
            continue
        # First match wins — the trace-assertion-canary contract says the
        # header counters appear first and the event log overwrites
        # specific lines in-place, but if a duplicate slips in we keep
        # the earlier (header) value to preserve the assertion intent.
        counters.setdefault(key, value)
    return counters


def _max_alias_value(counters: dict[str, int], aliases: tuple[str, ...]) -> int:
    """Return the max value across counter-name aliases. A role can be
    counted by either an old or new counter name; the larger of the two
    is the strongest claim the lead made about how many of that role ran.
    Missing counters contribute 0 (the conservative interpretation)."""
    return max((counters.get(name, 0) for name in aliases), default=0)


def check_trace_counters_reconcile_with_artifacts(
    engagement_dir: Path,
) -> CanaryResult:
    """G22+G24: reconcile ``audit-trace.log`` counters against observable
    artifact presence on disk.

    The ``contracts/dispatch-contract.md`` rule says the lead MUST
    increment the relevant counter after every successful dispatch
    (Agent for teammates, Task for subagents). The structural-assertion
    self-check in ``contracts/trace-assertion-canary.md`` is supposed
    to surface violations at audit completion. Engagement
    ``docs/ecp/2026-05-28-e4050c0e`` proved that gate is non-functional:
    all four spawn counters read 0 while 12 specialist emissions + 1
    ethics + 1 synth + 2 acquirers were observably on disk.

    This canary closes the loop by walking the filesystem and asserting
    ``counter >= observed_artifact_count`` for each role. A FAIL means
    the trace and reality have diverged — either the lead silently ran
    work without recording it (the actual 2026-05-28 case) or files
    landed without a recorded dispatch (a different drift class). Both
    are §0 untraceable-misleading failure modes; both demand operator
    attention before the audit is trustable.

    Pass criteria — for each role:
    - **Acquirers:** ``max(_ACQUIRER_COUNTERS) >= observed_baton_count``
      where ``observed_baton_count = #{baton.json, baton-mobile.json}``
      present on disk.
    - **Specialists:** ``max(_SPECIALIST_COUNTERS) >= observed_specialist_emission_count``
      where the observed count counts ``cluster-{cluster}-{device}.json``
      files (excluding ``cluster-context-*``) for clusters in
      ``meta.json["clusters_used"]`` × devices in
      ``meta.json["devices_scanned"]``.
    - **Ethics:** ``max(_ETHICS_COUNTERS) >= 1`` IFF
      ``ethics-findings.json`` exists and is non-empty.
    - **Synthesizer:** ``max(_SYNTHESIZER_COUNTERS) >= 1`` IFF
      ``synthesizer-emission-v1.json`` exists and is non-empty.
    - **cluster_files_written:** ``>= observed_specialist_emission_count``
      (separate counter the contract names; tracks files written, not
      dispatches that may have failed to write).

    Returns ``CanaryResult`` with detail keys per role: ``counter`` (the
    max alias value the lead recorded), ``observed`` (the artifact count
    on disk), ``reconciled`` (bool), and a ``violations`` list naming
    every role where ``counter < observed``.
    """
    trace_path = engagement_dir / "audit-trace.log"
    meta_path = engagement_dir / "meta.json"

    if not trace_path.exists() or not meta_path.exists():
        # Pre-trace-stage engagement (test fixture or aborted early). Skip
        # cleanly so this canary doesn't false-positive on partial setups.
        return CanaryResult(
            name="trace_counters_reconcile_with_artifacts",
            passed=True,
            summary=(
                "trace_counters_reconcile_with_artifacts: skipped "
                "(audit-trace.log or meta.json absent)"
            ),
            detail={"reason": "pre-trace-stage engagement"},
        )

    try:
        trace_text = trace_path.read_text(encoding="utf-8")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return CanaryResult(
            name="trace_counters_reconcile_with_artifacts",
            passed=False,
            summary=(
                f"trace_counters_reconcile_with_artifacts: FAIL -- "
                f"unreadable artifacts: {e}"
            ),
            detail={"error": str(e)},
        )

    counters = _parse_trace_counters(trace_text)

    # --- Observe artifact presence ---
    # Acquirers: count present batons (per-device).
    baton_files = [
        engagement_dir / "baton.json",
        engagement_dir / "baton-mobile.json",
    ]
    observed_acquirers = sum(
        1 for p in baton_files if p.exists() and p.stat().st_size > 0
    )

    # Specialists: count cluster-{cluster}-{device}.json files, excluding
    # cluster-context-* (those are DOM-slice inputs, not specialist
    # emissions). Restrict to (cluster, device) pairs that were actually
    # requested per meta.json so an unrelated stray emission doesn't
    # inflate the observation.
    _clusters_used = meta.get("clusters_used")
    requested_clusters = (
        [c for c in _clusters_used if c != "ethics"]
        if isinstance(_clusters_used, list) else []
    )
    _devices_scanned = meta.get("devices_scanned")
    requested_devices = _devices_scanned if isinstance(_devices_scanned, list) else []
    observed_specialists = 0
    for cluster in requested_clusters:
        for device in requested_devices:
            emission = engagement_dir / f"cluster-{cluster}-{device}.json"
            if emission.exists() and emission.stat().st_size > 0:
                observed_specialists += 1

    # Ethics + synth: presence-or-absence (counted as 0 or 1).
    ethics_path = engagement_dir / "ethics-findings.json"
    observed_ethics = 1 if ethics_path.exists() and ethics_path.stat().st_size > 0 else 0
    synth_path = engagement_dir / "synthesizer-emission-v1.json"
    observed_synth = 1 if synth_path.exists() and synth_path.stat().st_size > 0 else 0

    # --- Compare against trace counters ---
    role_checks = [
        ("acquirers", _max_alias_value(counters, _ACQUIRER_COUNTERS), observed_acquirers),
        ("specialists", _max_alias_value(counters, _SPECIALIST_COUNTERS), observed_specialists),
        ("ethics", _max_alias_value(counters, _ETHICS_COUNTERS), observed_ethics),
        ("synthesizer", _max_alias_value(counters, _SYNTHESIZER_COUNTERS), observed_synth),
        ("cluster_files_written", _max_alias_value(counters, _CLUSTER_FILES_COUNTERS), observed_specialists),
    ]

    role_detail: list[dict] = []
    violations: list[str] = []
    for role, counter_value, observed in role_checks:
        reconciled = counter_value >= observed
        role_detail.append({
            "role": role,
            "counter": counter_value,
            "observed": observed,
            "reconciled": reconciled,
        })
        if not reconciled:
            violations.append(
                f"{role} counter={counter_value} < observed={observed}"
            )

    passed = not violations
    if passed:
        summary = (
            f"trace_counters_reconcile_with_artifacts: PASS "
            f"(acquirers={role_detail[0]['counter']}/{role_detail[0]['observed']}, "
            f"specialists={role_detail[1]['counter']}/{role_detail[1]['observed']}, "
            f"ethics={role_detail[2]['counter']}/{role_detail[2]['observed']}, "
            f"synthesizer={role_detail[3]['counter']}/{role_detail[3]['observed']})"
        )
    else:
        summary = (
            f"trace_counters_reconcile_with_artifacts: FAIL -- "
            f"{len(violations)} role(s) under-counted in audit-trace.log: "
            f"{'; '.join(violations)}"
        )

    return CanaryResult(
        name="trace_counters_reconcile_with_artifacts",
        passed=passed,
        summary=summary,
        detail={
            "roles": role_detail,
            "violations": violations,
            "counters_parsed": counters,
        },
    )


def check_lead_reflection_not_stale(engagement_dir: Path) -> CanaryResult:
    """G23 follow-up (2026-05-29): flag a stale lead-reflection narrative.

    When an engagement is marked complete (``phase: complete`` OR
    ``engagement_status: complete``) but the lead never flipped
    ``reflection_state`` from ``draft`` to ``complete`` (the
    ``--mark-reflection-complete`` attestation), ``lead-reflection.md`` is
    stale relative to the finished pipeline. That is the
    ``docs/ecp/2026-05-28-e4050c0e`` failure class: a reflection written at
    specialist-phase time describing a "we failed" state that the pipeline
    then completed cleanly past, never refreshed.

    Back-compat (mirrors ``test_g23_reflection_state_gate``): an ABSENT
    ``reflection_state`` field is a pre-G23 engagement and is NOT flagged —
    only an *explicitly* ``draft`` field on a completed engagement. This keeps
    pre-G23 / Phase-J fixtures (``phase: complete`` with no ``reflection_state``)
    green. G23 built the draft->complete state machine; this canary is the
    consumer-side gate that surfaces leads who skipped the attestation.
    """
    name = "lead_reflection_not_stale"
    meta_path = engagement_dir / "meta.json"
    if not meta_path.exists():
        return CanaryResult(
            name=name,
            passed=True,
            summary=f"{name}: skipped (meta.json absent)",
            detail={"reason": "no meta.json"},
        )
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return CanaryResult(
            name=name,
            passed=False,
            summary=f"{name}: FAIL -- unreadable meta.json: {e}",
            detail={"error": str(e)},
        )

    phase = meta.get("phase")
    engagement_status = meta.get("engagement_status")
    is_complete = phase == "complete" or engagement_status == "complete"
    reflection_raw = meta.get("reflection_state")
    # Only enforce on engagements that EXPLICITLY track reflection_state. An
    # absent field is pre-G23 back-compat: read_reflection_state defaults it to
    # "draft", but that default must not be read as a skipped attestation.
    tracks_reflection = reflection_raw in VALID_REFLECTION_STATES

    detail = {
        "phase": phase,
        "engagement_status": engagement_status,
        "reflection_state": reflection_raw,
        "complete": is_complete,
    }

    if is_complete and tracks_reflection and reflection_raw != REFLECTION_STATE_COMPLETE:
        signal = "phase" if phase == "complete" else "engagement_status"
        return CanaryResult(
            name=name,
            passed=False,
            summary=(
                f"{name}: FAIL -- {signal}=complete but "
                f"reflection_state={reflection_raw!r}: the lead skipped the "
                f"--mark-reflection-complete attestation, so lead-reflection.md "
                f"may be stale relative to the finished pipeline (G23)"
            ),
            detail={**detail, "complete_signal": signal},
        )

    if is_complete and reflection_raw == REFLECTION_STATE_COMPLETE:
        summary = f"{name}: PASS (engagement complete, reflection_state=complete)"
    elif is_complete:
        summary = (
            f"{name}: PASS (engagement complete; reflection_state field absent "
            f"— pre-G23 back-compat, not enforced)"
        )
    else:
        summary = f"{name}: PASS (engagement not yet complete; reflection_state not required)"
    return CanaryResult(name=name, passed=True, summary=summary, detail=detail)


def check_lead_reflection_well_formed(engagement_dir: Path) -> CanaryResult:
    """G25 follow-up (2026-05-29): the lead's reflection must look like the lead wrote it.

    `lead-reflection.md` is a lead-owned artifact (`contracts/lead-discipline.md`).
    In `docs/ecp/2026-05-28-e4050c0e` a `specialist-content-seo-desktop` subagent
    wrote it instead — a file-ownership violation. The pipeline has no
    write-attribution, so this canary is a structural PROXY: when the file is
    present it MUST conform to the lead's required format — the canonical
    `# Lead Reflection — engagement <id>` header plus the `**Pipeline:**` and
    `**Phase reached:**` metadata markers. A specialist's content dump won't carry
    those, so a malformed reflection flags the most likely signature of a non-lead
    author (or a lead writing off-format). Presence itself is a separate soft-gate;
    this canary fires only when the file exists, and skips pre-format engagements
    cleanly (absent file → PASS).
    """
    name = "lead_reflection_well_formed"
    path = engagement_dir / "lead-reflection.md"
    if not path.exists():
        return CanaryResult(
            name=name,
            passed=True,
            summary=f"{name}: skipped (lead-reflection.md absent)",
            detail={"reason": "no lead-reflection.md"},
        )
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return CanaryResult(
            name=name,
            passed=False,
            summary=f"{name}: FAIL -- unreadable lead-reflection.md: {e}",
            detail={"error": str(e)},
        )

    missing: list[str] = []
    if not re.search(r"(?m)^#\s+Lead Reflection\b.*\bengagement\b", text):
        missing.append("'# Lead Reflection — engagement <id>' header")
    if "**Pipeline:**" not in text:
        missing.append("'**Pipeline:**' marker")
    if "**Phase reached:**" not in text:
        missing.append("'**Phase reached:**' marker")

    if missing:
        return CanaryResult(
            name=name,
            passed=False,
            summary=(
                f"{name}: FAIL -- lead-reflection.md is not in the lead's required "
                f"format (missing {', '.join(missing)}); a lead-owned file may have "
                f"been written by a non-lead — see contracts/lead-discipline.md"
            ),
            detail={"missing": missing},
        )
    return CanaryResult(
        name=name,
        passed=True,
        summary=f"{name}: PASS (lead-reflection.md conforms to the lead format)",
        detail={"missing": []},
    )


# ---------------------------------------------------------------------------
# Phase 6 ethics/legal batch (2026-06-10) — C18, H2, H3.
#
# Three canaries that close the ethics-side guardrails product.md §4.1 and
# §8 already specified but had no enforcement surface for. The vocabulary
# (law names, vacated rules, dark-pattern phrasings) is parsed AT RUNTIME
# from ``references/ethics-gate.md`` — no hardcoded copy that can drift.
# ---------------------------------------------------------------------------


# Canonical hedge tokens. Any one of these near a law citation satisfies
# the ADJACENT hedge contract (contracts/ethics-subagent-v2.md voice rule).
# Case-insensitive, word-boundary anchored.
_HEDGE_TOKENS = (
    "may implicate",
    "may potentially",
    "appears to",
    "borderline",
    "consult",
    "verify",
    # "current" / "currently" — operator language for probational
    # compliance ("not a current violation", "doesn't currently"); the
    # awdmods 2026-05-02 fixture uses this phrasing and it's a real,
    # acceptable hedge.
    "currently",
    "not a current",
    "not currently",
    # "adjacency" — the ethics-gate's own ADJACENT-state vocabulary;
    # when an operator uses it they're explicitly framing the citation
    # as non-violating.
    "adjacency",
    # Operator-voice future-conditional framing — the slingmods fixture
    # uses ("could mislead", "removes this exposure", "one complaint away
    # from"). These hedge the citation by framing it as a forward-looking
    # risk rather than a current violation.
    "could",
    "complaint away",
    "exposure",
    "this exposure",
    # "per-se" — "not a per-se violation" is the lawyerly framing the
    # slingmods fixture uses to acknowledge the rule without claiming a
    # current violation.
    "per-se",
    "not a per-se",
    # plain "may" is intentionally last and matched with word-boundaries
    # so it doesn't false-match inside larger tokens.
    "may",
)
_HEDGE_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(t) for t in _HEDGE_TOKENS) + r")\b",
    re.IGNORECASE,
)

# Generic regulation/law-name patterns. Matches things like:
#   FTC, FTC Act § 5, FTC § 5, GDPR, CCPA/CPRA, EU DSA, CAN-SPAM, TCPA,
#   16 CFR § 465.2, Directive 2002/58/EC, ROSCA, EAA, Lanham Act § 43(a),
#   ePrivacy, COPPA, ADA Title III, SB-478, SB-1001, etc.
# These are tokens commonly used by the ethics-gate; combined with the
# Source-Registry-derived name list (built at canary runtime) below, this
# catches both the explicit list and "law-shaped" prose patterns.
_GENERIC_LAW_PATTERNS = (
    re.compile(r"\b\d+\s*CFR\b", re.IGNORECASE),
    re.compile(r"\bU\.?S\.?C\.?\b", re.IGNORECASE),
    re.compile(r"\bDirective\s+\d", re.IGNORECASE),
    re.compile(r"\bRegulation\s+\(EU\)\b", re.IGNORECASE),
    re.compile(r"§\s*\d"),  # section marker followed by a digit
    re.compile(r"\bArt(?:icle|\.)\s*\d", re.IGNORECASE),
    re.compile(r"\bSB[\s\-]?\d{2,4}\b", re.IGNORECASE),
    re.compile(r"\bAB[\s\-]?\d{2,4}\b", re.IGNORECASE),
)


def _ethics_gate_path() -> Path:
    """Locate references/ethics-gate.md from the repo root."""
    return Path(__file__).resolve().parent.parent.parent / "references" / "ethics-gate.md"


def _read_ethics_gate_text() -> str:
    """Read references/ethics-gate.md, or return '' if unreadable."""
    p = _ethics_gate_path()
    if not p.exists():
        return ""
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""


# Source Registry row format inside <source_registry>:
#   "| <name> | <citation> | <https-url> |"
# We extract just the URLs (column 3 / 2 depending on table). Robust to
# rows that don't follow the strict 3-column shape by scanning for any
# http(s) URL inside the <source_registry> block.
_REGISTRY_URL_RE = re.compile(r"https?://[^\s)\]|]+", re.IGNORECASE)


def _parse_source_registry(gate_text: str) -> set[str]:
    """Return the set of Source Registry URLs (normalized, no trailing /)."""
    m = re.search(r"<source_registry>(.*?)</source_registry>", gate_text, re.DOTALL)
    if not m:
        return set()
    block = m.group(1)
    urls = {_normalize_url(u) for u in _REGISTRY_URL_RE.findall(block)}
    return {u for u in urls if u}


def _parse_vacated_urls(gate_text: str) -> set[str]:
    """Return URLs flagged 'VACATED' or 'SET ASIDE' in the tracker table.

    The Vacated Rules Tracker table sits above <source_registry>; each row
    starts with "| <Rule name>" and contains VACATED or SET ASIDE in the
    Status column. We collect Source Registry URLs that map to those rules
    by name (substring match against the Source Registry rows).
    """
    # Section between "Vacated / Rescinded Rules Tracker" and the next
    # "### " heading — bounded so we don't catch unrelated VACATED mentions.
    tracker_m = re.search(
        r"### Vacated.*?Rules Tracker(.*?)(?=^###\s)",
        gate_text,
        re.DOTALL | re.MULTILINE,
    )
    if not tracker_m:
        return set()
    tracker = tracker_m.group(1)
    vacated_names: list[str] = []
    for line in tracker.splitlines():
        if "VACATED" in line.upper() or "SET ASIDE" in line.upper():
            cells = [c.strip() for c in line.split("|") if c.strip()]
            if cells:
                # First cell is the rule name. Strip the parenthetical /
                # bracketed status notes for robust substring matching.
                name = re.sub(r"\(.*?\)|\[.*?\]", "", cells[0]).strip()
                if name:
                    vacated_names.append(name)
    if not vacated_names:
        return set()

    # Now scan the Source Registry table rows. A registry row whose
    # name-column matches one of the vacated names contributes its URL.
    vacated_urls: set[str] = set()
    reg_block_m = re.search(
        r"<source_registry>(.*?)</source_registry>", gate_text, re.DOTALL
    )
    if not reg_block_m:
        return vacated_urls
    for row in reg_block_m.group(1).splitlines():
        if "|" not in row:
            continue
        cells = [c.strip() for c in row.split("|") if c.strip()]
        if len(cells) < 2:
            continue
        name_cell = cells[0]
        # The Source Registry's vacated entries are explicitly marked in
        # the name column (e.g. "FTC Click-to-Cancel (VACATED ...)").
        # We also cross-reference the tracker's names for robustness.
        is_vacated_inline = "VACATED" in name_cell.upper() or "SET ASIDE" in name_cell.upper()
        is_tracker_match = any(
            _name_overlap(name_cell, vn) for vn in vacated_names
        )
        if not (is_vacated_inline or is_tracker_match):
            continue
        for url in _REGISTRY_URL_RE.findall(row):
            n = _normalize_url(url)
            if n:
                vacated_urls.add(n)
    return vacated_urls


def _name_overlap(a: str, b: str) -> bool:
    """Cheap fuzzy match — share a 4+ char alphabetic token (case-insensitive).

    Used only for vacated-rule cross-reference; an explicit hit on the
    Source Registry's inline "VACATED" marker is the primary path.
    """
    toks_a = {t.lower() for t in re.findall(r"[A-Za-z]{4,}", a)}
    toks_b = {t.lower() for t in re.findall(r"[A-Za-z]{4,}", b)}
    # Generic words that would over-match
    toks_a -= {"rule", "rules", "act", "the", "and", "for"}
    toks_b -= {"rule", "rules", "act", "the", "and", "for"}
    return bool(toks_a & toks_b)


def _normalize_url(url: str) -> str:
    """Lowercase + strip a single trailing slash, preserving query strings."""
    if not url:
        return ""
    s = url.strip().lower()
    if s.endswith("/") and not s.endswith("://"):
        s = s[:-1]
    return s


def _parse_law_name_list(gate_text: str) -> list[str]:
    """Build the list of regulation/law names from the Source Registry name column.

    The names column is the FIRST cell of each Source Registry table row.
    We collect them as case-insensitive substring tokens for the hedge-lint
    detector. Includes both the headline name (e.g. "FTC Fake Reviews Rule")
    and any registry-style alias visible in the row prose.
    """
    names: list[str] = []
    m = re.search(r"<source_registry>(.*?)</source_registry>", gate_text, re.DOTALL)
    if not m:
        return names
    for row in m.group(1).splitlines():
        if "|" not in row:
            continue
        # Skip header separators and headings
        if set(row.strip().replace("|", "").strip()) <= set("- "):
            continue
        cells = [c.strip() for c in row.split("|") if c.strip()]
        if not cells:
            continue
        first = cells[0]
        # Skip table-header rows (Markdown convention: "Regulation").
        if first.lower() in {"regulation", "policy"}:
            continue
        # Strip the parenthetical status notes ("(VACATED ...)") for
        # detection purposes — the name itself is still the citation.
        clean = re.sub(r"\(.*?\)", "", first).strip()
        if clean:
            names.append(clean)
    return names


def _has_law_citation(text: str, law_names: list[str]) -> str | None:
    """Return the matched law-name/pattern when ``text`` cites a regulation.

    Combines the runtime-built ``law_names`` (from the Source Registry) with
    the generic law-shape patterns. Returns the matched token (for the
    canary's detail field) or None when no citation is found.
    """
    if not text:
        return None
    low = text.lower()
    for name in law_names:
        if not name:
            continue
        # Use lowercase substring containment for the registry-derived
        # multi-word names; word-boundary regex would miss em-dash or
        # punctuation-adjacent occurrences in real prose.
        if name.lower() in low:
            return name
    for pat in _GENERIC_LAW_PATTERNS:
        m = pat.search(text)
        if m:
            return m.group(0)
    # Common bare acronyms that appear in cited form but may not match a
    # generic pattern. Listed here rather than per-registry-row so they
    # catch prose like "GDPR Art 6" even when only "GDPR" is the cite.
    for acronym in ("FTC", "GDPR", "CCPA", "CPRA", "DSA", "EAA", "ROSCA",
                    "CAN-SPAM", "TCPA", "COPPA", "ADA", "TILA", "BNPL"):
        if re.search(rf"\b{re.escape(acronym)}\b", text):
            return acronym
    return None


# ---------------------------------------------------------------------------
# Canary 8 (C18) — ethics_findings_hedge_law_on_adjacent
# ---------------------------------------------------------------------------


def check_ethics_findings_hedge_law_on_adjacent(
    ethics_findings_path: Path,
) -> CanaryResult:
    """Verify ADJACENT ethics findings hedge any law/regulation citation.

    product.md §4.1 calls misquoted / over-applied law the highest-bar
    violation. contracts/ethics-subagent-v2.md's ADJACENT carve-out
    requires any ADJACENT finding citing a law in its ``observation`` /
    ``recommendation`` / ``why_this_matters`` to hedge with one of the
    canonical tokens ("may implicate", "may", "appears to", "verify",
    "borderline", "consult"). BLOCK findings are unaffected — they SHOULD
    be direct.

    The vocabulary is parsed AT RUNTIME from
    ``references/ethics-gate.md`` — no hardcoded copy that can drift
    against the gate's Source Registry.

    Pass criteria: every ADJACENT finding either cites no law in its prose
    OR hedges that citation. Returns the per-finding violations in detail.
    """
    name = "ethics_findings_hedge_law_on_adjacent"
    if not ethics_findings_path.exists():
        return CanaryResult(
            name=name,
            passed=True,
            summary=f"{name}: skipped (ethics-findings.json absent)",
            detail={"reason": "no ethics-findings.json"},
        )
    try:
        data = json.loads(ethics_findings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return CanaryResult(
            name=name,
            passed=False,
            summary=f"{name}: FAIL -- unreadable ethics-findings.json: {e}",
            detail={"error": str(e)},
        )
    findings = data.get("findings") if isinstance(data, dict) else None
    if not isinstance(findings, list):
        return CanaryResult(
            name=name,
            passed=True,
            summary=f"{name}: skipped (no findings array)",
            detail={"reason": "no findings list"},
        )

    gate_text = _read_ethics_gate_text()
    law_names = _parse_law_name_list(gate_text)

    unhedged: list[dict] = []
    adjacent_total = 0
    for f in findings:
        if not isinstance(f, dict):
            continue
        if (f.get("ethics_state") or "").upper() != "ADJACENT":
            continue
        adjacent_total += 1
        for field in ("observation", "recommendation", "why_this_matters"):
            text = f.get(field) or ""
            cite = _has_law_citation(text, law_names)
            if cite and not _HEDGE_RE.search(text):
                local_id = f.get("local_id")
                try:
                    f_ref = f"ethics F-{int(local_id):02d}"
                except (TypeError, ValueError):
                    f_ref = "ethics F-??"
                unhedged.append({
                    "f_ref": f_ref,
                    "field": field,
                    "law_cited": cite,
                    "excerpt": text[:160],
                })
                # One violation per finding is enough to log; don't spam.
                break

    passed = not unhedged
    if passed:
        summary = (
            f"{name}: PASS ({adjacent_total} ADJACENT finding(s) "
            f"hedge any law citation per product.md §4.1)"
        )
    else:
        summary = (
            f"{name}: FAIL -- {len(unhedged)} ADJACENT finding(s) cite a "
            f"law without hedging (product.md §4.1 highest-bar violation): "
            + ", ".join(f"{u['f_ref']}[{u['field']}]" for u in unhedged)
        )
    return CanaryResult(
        name=name,
        passed=passed,
        summary=summary,
        detail={
            "adjacent_total": adjacent_total,
            "unhedged": unhedged,
            "law_name_list_size": len(law_names),
        },
    )


# ---------------------------------------------------------------------------
# Canary 9 (H2) — ethics_source_url_against_registry
# ---------------------------------------------------------------------------


def check_ethics_source_url_against_registry(
    ethics_findings_path: Path,
) -> CanaryResult:
    """Verify every BLOCK/ADJACENT source_url is in the Source Registry.

    The schema validates URL format only. Pre-Phase-6, nothing prevented
    citing one of the three vacated rules the library itself tracks as
    "do not cite as live authority" — or an invented URL. This canary
    parses the Source Registry + Vacated Rules tracker AT RUNTIME from
    ``references/ethics-gate.md`` (so a gate edit is honored without a
    code change) and:

    - A source_url not present in the Source Registry FAILS
      ("URL not in Source Registry").
    - A source_url matching a vacated-rule URL FAILS with a distinct
      message ("URL cites a VACATED rule — use the underlying statute").
    """
    name = "ethics_source_url_against_registry"
    if not ethics_findings_path.exists():
        return CanaryResult(
            name=name,
            passed=True,
            summary=f"{name}: skipped (ethics-findings.json absent)",
            detail={"reason": "no ethics-findings.json"},
        )
    try:
        data = json.loads(ethics_findings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return CanaryResult(
            name=name,
            passed=False,
            summary=f"{name}: FAIL -- unreadable ethics-findings.json: {e}",
            detail={"error": str(e)},
        )
    findings = data.get("findings") if isinstance(data, dict) else None
    if not isinstance(findings, list):
        return CanaryResult(
            name=name,
            passed=True,
            summary=f"{name}: skipped (no findings array)",
            detail={"reason": "no findings list"},
        )

    gate_text = _read_ethics_gate_text()
    registry_urls = _parse_source_registry(gate_text)
    vacated_urls = _parse_vacated_urls(gate_text)
    # Defensive: if the gate is unreadable or unparseable, skip with a
    # documented note rather than failing every audit on infra drift.
    if not registry_urls:
        return CanaryResult(
            name=name,
            passed=True,
            summary=(
                f"{name}: skipped (could not parse Source Registry from "
                f"references/ethics-gate.md — verify the file is present "
                f"and contains <source_registry>...</source_registry>)"
            ),
            detail={"reason": "no registry URLs parsed"},
        )

    not_in_registry: list[dict] = []
    vacated_hits: list[dict] = []
    total_actionable = 0
    for f in findings:
        if not isinstance(f, dict):
            continue
        state = (f.get("ethics_state") or "").upper()
        if state not in {"BLOCK", "ADJACENT"}:
            continue
        total_actionable += 1
        url = (f.get("source_url") or "").strip()
        if not url:
            # Source-url presence is the older canary's domain — skip here
            # to avoid double-reporting the same violation class.
            continue
        norm = _normalize_url(url)
        local_id = f.get("local_id")
        try:
            f_ref = f"ethics F-{int(local_id):02d}"
        except (TypeError, ValueError):
            f_ref = "ethics F-??"
        if norm in vacated_urls:
            vacated_hits.append({
                "f_ref": f_ref,
                "ethics_state": state,
                "source_url": url,
            })
        elif norm not in registry_urls:
            not_in_registry.append({
                "f_ref": f_ref,
                "ethics_state": state,
                "source_url": url,
            })

    passed = not (not_in_registry or vacated_hits)
    if passed:
        summary = (
            f"{name}: PASS ({total_actionable} actionable ethics "
            f"finding(s) all cite Source Registry URLs; "
            f"0 vacated-rule citations)"
        )
    else:
        parts: list[str] = []
        if vacated_hits:
            parts.append(
                f"{len(vacated_hits)} URL(s) cite a VACATED rule — "
                f"use the underlying statute"
            )
        if not_in_registry:
            parts.append(
                f"{len(not_in_registry)} URL(s) not in Source Registry"
            )
        summary = f"{name}: FAIL -- " + "; ".join(parts)
    return CanaryResult(
        name=name,
        passed=passed,
        summary=summary,
        detail={
            "total_actionable": total_actionable,
            "registry_url_count": len(registry_urls),
            "vacated_url_count": len(vacated_urls),
            "not_in_registry": not_in_registry,
            "vacated_hits": vacated_hits,
        },
    )


# ---------------------------------------------------------------------------
# Canary 10 (H3) — recommendations_no_dark_patterns
# ---------------------------------------------------------------------------


# Recommendation-voice verbs that mean "do this" (the pattern that fires
# the canary). Word-boundary anchored so we don't false-match "added"
# inside "added to the cart". The combined "add a countdown timer" shape
# is built by joining these against the dark-pattern terms.
_RECOMMEND_VERBS = (
    "add", "adding", "implement", "introduce", "create", "use", "enable",
    "build", "include", "show", "display", "set", "hide", "hiding",
    "pre-check", "precheck", "force", "trick",
)
_REMOVE_VERBS = (
    "remove", "delete", "drop", "strip", "kill", "eliminate", "avoid",
    "disable", "stop", "don't", "never", "replace", "fix",
    "uncheck",
)
# Plain-prose denial phrases that survive `\b` boundaries on the multi-word
# forms ("do not" vs "does not"). Word-boundary regex on "do not" doesn't
# catch "does not"; precompile a small set of denial regexes that do.
_REMOVE_PHRASE_RES = (
    re.compile(r"\bdo(?:es)?\s+not\b", re.IGNORECASE),
    re.compile(r"\bdid\s+not\b", re.IGNORECASE),
    re.compile(r"\bno\s+longer\b", re.IGNORECASE),
    # "display the count WITHOUT filtering out negative reviews" — the
    # dark-pattern term is the object of an exclusion, not a recommendation.
    re.compile(r"\bwithout\b", re.IGNORECASE),
)

# Dark-pattern term vocabulary. The ethics-gate's BLOCK rules name these
# explicitly (Part 1.1 urgency/scarcity, 1.2 pricing, 1.3 reviews, 1.4
# choice architecture, 1.5 subscription, 4.4 unsubscribe). We keep the
# curated list small + targeted to recommendation-shaped prose; full
# ethics adjudication lives in the subagent, not the lint.
# The non-greedy ``(?:\s+\w+){0,3}`` chunk lets the dark-pattern term
# tolerate a small number of intervening adjectives ("Hide the
# convenience fee", "Pre-check the newsletter opt-in box") without
# matching across whole sentences. Bounded at 3 words to keep the
# false-positive surface tight.
_DARK_PATTERN_TERMS = (
    r"countdown\s+timer(?:\s+that\s+resets)?",
    r"resetting\s+countdown",
    r"fake\s+(?:countdown|urgency|scarcity|review|stock|inventory)",
    r"fabricated\s+(?:countdown|urgency|scarcity|review)",
    r"(?:false|fake)\s+scarcity",
    r"only\s+\d+\s+left",  # "Only 3 left"
    r"people\s+viewing\s+counter",
    r"hidden\s+fee",
    r"hide(?:\s+\w+){0,3}\s+(?:fee|cost|charge|shipping|total|price)",
    r"drip[\s\-]?pricing",
    r"pre[\s\-]?check(?:ed)?(?:\s+\w+){0,4}\s+(?:opt[\s\-]?in|subscription|add[\s\-]?on|box(?:es)?|checkbox)",
    r"pre[\s\-]?check(?:ed)?\s+box(?:es)?",
    r"confirm[\s\-]?shaming",
    r"forced\s+continuity",
    r"auto[\s\-]?renew(?:al)?\s+without",
    r"negative\s+option",
    r"fake\s+review",
    r"review\s+gating",
    r"suppress(?:ing)?\s+(?:negative\s+)?review",
    r"filter(?:ing)?\s+out\s+(?:negative\s+)?review",
    r"phantom\s+social\s+proof",
    r"dark\s+pattern",
)
_DARK_PATTERN_RE = re.compile(
    r"|".join(_DARK_PATTERN_TERMS),
    re.IGNORECASE,
)
_RECOMMEND_VERB_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(v) for v in _RECOMMEND_VERBS) + r")\b",
    re.IGNORECASE,
)
_REMOVE_VERB_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(v) for v in _REMOVE_VERBS) + r")\b",
    re.IGNORECASE,
)


def _sentence_recommends_dark_pattern(sentence: str) -> str | None:
    """Return the matched dark-pattern phrase iff sentence is an add-shaped recommendation.

    A sentence FIRES iff:
      - It contains a recommend-voice verb (add/implement/show/hide/
        pre-check/...) — either as a free token OR as the verb-shape
        baked into the dark-pattern phrase itself (e.g. "Pre-check the
        opt-in" already encodes the verb), AND
      - It contains a dark-pattern term, AND
      - It does NOT contain a remove-voice verb (so "remove the fake
        countdown timer" passes), AND
      - It does NOT contain a denial phrase ("does not use a fabricated
        countdown" passes — describes absence, doesn't recommend).

    Returns the matched pattern text for the canary detail, or None.
    """
    if not sentence:
        return None
    dp_match = _DARK_PATTERN_RE.search(sentence)
    if not dp_match:
        return None
    # If a remove-verb or denial phrase is present anywhere in the same
    # sentence, treat as a removal/description. Sentences are short
    # enough that proximity checks across the whole sentence are reliable
    # for false-positive control without window heuristics.
    if _REMOVE_VERB_RE.search(sentence):
        return None
    if any(p.search(sentence) for p in _REMOVE_PHRASE_RES):
        return None
    if not _RECOMMEND_VERB_RE.search(sentence):
        return None
    return dp_match.group(0)


def _split_sentences(text: str) -> list[str]:
    """Cheap sentence splitter. Prose-only, no nested punctuation handling."""
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def _iter_recommendation_texts(engagement_dir: Path):
    """Yield (label, text) over every recommendation-bearing artifact.

    Sources:
      - every cluster-*.json findings[].recommendation
      - ethics-findings.json findings[].recommendation
      - synthesizer-emission-v1.json priority_path[].narrative
    """
    # Cluster + ethics findings.
    for path in sorted(engagement_dir.glob("cluster-*-*.json")):
        if "cluster-context" in path.name:
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for f in doc.get("findings") or []:
            if not isinstance(f, dict):
                continue
            rec = f.get("recommendation") or ""
            label = (
                f"{doc.get('cluster', path.stem)} "
                f"F-{f.get('local_id', '??')} {path.name}"
            )
            if rec:
                yield (label, rec)
    ethics_path = engagement_dir / "ethics-findings.json"
    if ethics_path.exists():
        try:
            doc = json.loads(ethics_path.read_text(encoding="utf-8"))
            for f in doc.get("findings") or []:
                if not isinstance(f, dict):
                    continue
                rec = f.get("recommendation") or ""
                label = f"ethics F-{f.get('local_id', '??')} ethics-findings.json"
                if rec:
                    yield (label, rec)
        except (OSError, json.JSONDecodeError):
            pass
    # Synth priority_path narratives.
    synth_path = engagement_dir / "synthesizer-emission-v1.json"
    if synth_path.exists():
        try:
            doc = json.loads(synth_path.read_text(encoding="utf-8"))
            for i, story in enumerate(doc.get("priority_path") or []):
                if not isinstance(story, dict):
                    continue
                text = story.get("narrative") or ""
                if text:
                    yield (
                        f"priority_path[{i}] {story.get('mode', 'unknown')}",
                        text,
                    )
        except (OSError, json.JSONDecodeError):
            pass


def check_recommendations_no_dark_patterns(
    engagement_dir: Path,
) -> CanaryResult:
    """product.md §8 — ECP MUST NEVER recommend a dark pattern.

    Scans every finding ``recommendation`` plus every synthesizer
    Priority Path story narrative for dark-pattern-recommending sentence
    shapes (add a countdown timer, pre-check the opt-in, hide the fee).
    Removal recommendations ("remove the fake countdown timer") pass.

    Vocabulary is the small curated regex set documented in
    ``_DARK_PATTERN_TERMS``, derived from the ethics-gate.md BLOCK
    detector vocabulary (Part 1.1/1.2/1.3/1.4/1.5). Adding/adjusting a
    pattern is a single-source change here, with the rationale documented
    inline so future operators can trace which BLOCK rule it implements.

    Pass criteria: zero sentences across all scanned artifacts that fire
    a dark-pattern-recommending shape. Each violation is returned in
    detail with the source label, matched pattern, and excerpt so the
    operator can locate and fix it.
    """
    name = "recommendations_no_dark_patterns"
    if not engagement_dir.exists():
        return CanaryResult(
            name=name,
            passed=True,
            summary=f"{name}: skipped (engagement dir absent)",
            detail={"reason": "no engagement dir"},
        )

    violations: list[dict] = []
    scanned = 0
    for label, text in _iter_recommendation_texts(engagement_dir):
        scanned += 1
        for sentence in _split_sentences(text):
            matched = _sentence_recommends_dark_pattern(sentence)
            if matched:
                violations.append({
                    "source": label,
                    "matched_pattern": matched,
                    "excerpt": sentence[:200],
                })

    passed = not violations
    if passed:
        summary = (
            f"{name}: PASS ({scanned} recommendation/narrative source(s) "
            f"scanned; no dark-pattern-recommending shapes detected)"
        )
    else:
        summary = (
            f"{name}: FAIL -- {len(violations)} dark-pattern-recommending "
            f"shape(s) found (product.md §8 violation): "
            + ", ".join(
                f"{v['source']} matched {v['matched_pattern']!r}"
                for v in violations[:3]
            )
            + ("…" if len(violations) > 3 else "")
        )
    return CanaryResult(
        name=name,
        passed=passed,
        summary=summary,
        detail={
            "sources_scanned": scanned,
            "violations": violations,
        },
    )


# ---------------------------------------------------------------------------
# Top-level — run all canaries against an engagement directory
# ---------------------------------------------------------------------------


def run_all_canaries(
    engagement_dir: Path,
    audited_domain: str | None = None,
    element_threshold: float = 0.8,
    ethics_max_diff: int = 1,
    ethics_findings_path: Path | None = None,
    include_visual_quality: bool = True,
) -> dict:
    """Run all substantive canaries against an engagement.

    Convenience entry point for the audit lead at audit completion.
    Resolves canonical paths from ``engagement_dir`` and invokes the
    individual canary helpers.

    Args:
        engagement_dir: path to ``docs/ecp/{engagement_id}/``.
        audited_domain: extracted from meta.json or baton.json by the
            caller; passed to the ethics source_url canary.
        element_threshold: passed to element_index_match_rate (default 0.8).
        ethics_max_diff: passed to cross_device_ethics_diff (default 1).
        ethics_findings_path: optional override. If None, looks at
            ``engagement_dir / "ethics-findings.json"`` and falls back to
            ``.phase-b-tmp/ethics-findings.json`` (the slingmods fixture's
            mixed-location pattern).
        include_visual_quality: when True (default as of Phase 3
            hardening 2026-05-18), also runs the Phase 3 visual evidence
            quality gates from ``visual_quality.py`` against
            ``review-state-{device}.json`` files and appends their
            results + summary_table to the returned dict. When no
            review-state files exist, the visual quality block is empty
            and ``results`` is unchanged from the Phase I baseline —
            engagements that haven't reached the render stage skip
            cleanly. Set to False to explicitly suppress the gates
            (e.g., from determinism tests that snapshot pre-Phase-3
            baselines).

    Returns:
        Dict with keys:
            - 'engagement_dir': str path
            - 'all_passed': bool — every canary passed (including visual
              quality when include_visual_quality=True)
            - 'results': list of CanaryResult dicts in order
              (ethics_findings_have_source_urls, element_index_match_rate,
              cross_device_ethics_diff, then Phase 3 visual quality gates
              when include_visual_quality=True)
            - 'summary': one-line human-readable summary
            - 'visual_quality': only present when include_visual_quality=True;
              dict with per-device run_visual_quality_gates output + a
              merged summary_table across devices for the trace log.
    """
    if ethics_findings_path is None:
        primary = engagement_dir / "ethics-findings.json"
        if primary.exists():
            ethics_findings_path = primary
        else:
            phase_b_tmp = engagement_dir.parent.parent.parent / ".phase-b-tmp" / "ethics-findings.json"
            if phase_b_tmp.exists():
                ethics_findings_path = phase_b_tmp
            else:
                ethics_findings_path = primary  # report the canonical missing path

    desktop_audit = engagement_dir / "audit-desktop.md"
    mobile_audit = engagement_dir / "audit-mobile.md"

    r1 = check_ethics_findings_have_source_urls(
        ethics_findings_path, audited_domain=audited_domain
    )
    r2 = check_element_index_match_rate(
        [desktop_audit, mobile_audit], threshold=element_threshold
    )
    r3 = check_cross_device_ethics_diff(
        desktop_audit, mobile_audit, max_diff=ethics_max_diff
    )
    # Phase 6 (2026-05-18) — Codex Q2/Q3/Q4 cross-device Priority Path
    # parity. Catches the desktop-markdown-shows-5-but-desktop-HTML-shows-4
    # class. Soft canary like the other three.
    r4 = check_priority_path_count_parity(
        engagement_dir / "synthesizer-emission-v1.json", engagement_dir,
    )
    # G16 (2026-05-27) — cluster-coverage parity. Catches engagements
    # where build_canonical_view silently swallowed schema-invalid cluster
    # emissions (the failure that left Run 2026-05-27-52f53a53 with 2 of
    # 6 CRO clusters rendered on desktop while every other canary passed).
    r5 = check_clusters_represented(engagement_dir)
    # G22+G24 (2026-05-28) — reconcile audit-trace.log counters with
    # observable artifact presence on disk. Closes the structural-
    # assertion enforcement gap that left docs/ecp/2026-05-28-e4050c0e
    # reading all spawn counters at 0 despite 12 specialists + 1 ethics
    # + 1 synth + 2 acquirers landing as artifacts.
    r6 = check_trace_counters_reconcile_with_artifacts(engagement_dir)
    # G23-followup (2026-05-29) — consumer-side staleness gate: if the
    # engagement is marked complete (phase or engagement_status) but the lead
    # never flipped reflection_state to complete, lead-reflection.md is stale
    # relative to the finished pipeline (the docs/ecp/2026-05-28-e4050c0e
    # premature-reflection class). Skips pre-G23 engagements (absent field).
    r7 = check_lead_reflection_not_stale(engagement_dir)
    # G25-followup (2026-05-29) — file-ownership proxy: lead-reflection.md, when
    # present, must conform to the lead's required format. Catches the
    # docs/ecp/2026-05-28-e4050c0e class where a specialist wrote the lead's file.
    r8 = check_lead_reflection_well_formed(engagement_dir)
    # Phase 6 (2026-06-10) — ethics/legal enforcement batch:
    #   C18: ADJACENT findings citing a law MUST hedge (product.md §4.1)
    #   H2:  BLOCK/ADJACENT source_url MUST be in the Source Registry and
    #        MUST NOT be a vacated-rule URL (references/ethics-gate.md)
    #   H3:  no recommendation may RECOMMEND a dark pattern (product.md §8)
    r9 = check_ethics_findings_hedge_law_on_adjacent(ethics_findings_path)
    r10 = check_ethics_source_url_against_registry(ethics_findings_path)
    r11 = check_recommendations_no_dark_patterns(engagement_dir)

    results = [r1, r2, r3, r4, r5, r6, r7, r8, r9, r10, r11]

    visual_quality_block: dict | None = None
    if include_visual_quality:
        # Phase 3 (2026-05-18) — visual evidence quality gates. Run against
        # each device's review-state if present; aggregate results +
        # summary_table for the trace writer. Import deferred so callers
        # that don't opt in don't pay the import cost.
        from .visual_quality import (
            compute_visual_evidence_summary,
            render_summary_table,
            run_visual_quality_gates,
        )

        synth_path = engagement_dir / "synthesizer-emission-v1.json"
        per_device: dict[str, dict] = {}
        combined_findings: list[dict] = []
        for review_path in sorted(engagement_dir.glob("review-state-*.json")):
            # Skip backup files (review-state-desktop.backup.json etc.)
            if ".backup" in review_path.stem:
                continue
            try:
                gates = run_visual_quality_gates(
                    review_path,
                    synth_path if synth_path.exists() else None,
                )
            except (OSError, json.JSONDecodeError):
                continue
            per_device[review_path.stem] = gates
            results.extend(gates["results"])
            try:
                state = json.loads(review_path.read_text(encoding="utf-8"))
                combined_findings.extend(state.get("findings") or [])
            except (OSError, json.JSONDecodeError):
                continue

        merged_summary = compute_visual_evidence_summary(combined_findings)
        visual_quality_block = {
            "per_device": per_device,
            "merged_summary_table": merged_summary,
            "merged_summary_rendered": render_summary_table(merged_summary),
        }

    all_passed = all(r["passed"] for r in results)
    summary = "; ".join(r["summary"] for r in results)

    out: dict = {
        "engagement_dir": str(engagement_dir),
        "all_passed": all_passed,
        "results": results,
        "summary": summary,
    }
    if visual_quality_block is not None:
        out["visual_quality"] = visual_quality_block
    return out


def main(argv: list[str] | None = None) -> int:
    """CLI entry point — runs all canaries against an engagement and prints."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engagement", required=True, type=Path)
    parser.add_argument("--audited-domain", default=None, type=str)
    parser.add_argument("--element-threshold", default=0.8, type=float)
    parser.add_argument("--ethics-max-diff", default=1, type=int)
    parser.add_argument(
        "--no-visual-quality",
        action="store_true",
        help=(
            "Skip the Phase 3 visual evidence quality gates. By default "
            "(Phase 3 hardening 2026-05-18) these run against every "
            "review-state-{device}.json present in the engagement dir and "
            "append their CanaryResult dicts to the output. Pass this "
            "flag to suppress them — useful for v1 engagements without "
            "review-state or for determinism baselines."
        ),
    )
    parser.add_argument(
        "--exit-on-fail",
        action="store_true",
        help="Return non-zero exit code if any canary fails",
    )
    args = parser.parse_args(argv)

    out = run_all_canaries(
        args.engagement,
        audited_domain=args.audited_domain,
        element_threshold=args.element_threshold,
        ethics_max_diff=args.ethics_max_diff,
        include_visual_quality=not args.no_visual_quality,
    )

    print(json.dumps(out, indent=2))

    if args.exit_on_fail and not out["all_passed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
