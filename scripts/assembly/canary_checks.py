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

These are PURE FUNCTIONS that read engagement artifacts and return
structured result dicts. The lead invokes them at audit completion, writes
the results to ``audit-trace.log``, and writes ``lead-reflection.md`` with
any non-passing canaries documented.

Authored Phase I (2026-04-28).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlparse


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

    findings = data.get("findings") or []
    audited_host = _domain_of(audited_domain) if audited_domain else None

    actionable_findings = []
    missing_source_url: list[dict] = []
    self_cite_filler: list[dict] = []
    clear_count = 0

    for f in findings:
        state = (f.get("ethics_state") or "").upper()
        if state in {"BLOCK", "ADJACENT"}:
            actionable_findings.append(f)
            local_id = f.get("local_id")
            f_ref = f"ethics F-{local_id:02d}" if local_id else "ethics F-??"
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
        matched = sum(1 for line in elements if _ELEMENT_INDEX_RE.search(line))
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
            _, aliases = build_canonical_view(
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

    results = [r1, r2, r3, r4]

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
