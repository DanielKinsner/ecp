"""Visual evidence quality gates (Phase 3 — 2026-05-18).

The Phase 2 visual evidence taxonomy makes the visual representation contract
explicit per finding (see ``scripts/report/visual_evidence.py``). Phase 3
adds gates that check whether the resulting rendered report actually meets a
quality bar — not just "did every hotspot get placed somewhere" (the
pre-Phase-3 metric) but "is each hotspot's visual evidence defensible."

Gates exposed:

- ``check_giant_exact_rectangles`` — exact_element hotspots whose rect
  exceeds the configured width/height percent of the viewport. Solid
  exact-element rects covering >85% width or >70% height almost always mean
  the specialist anchored against a parent container (full header, full
  drawer) instead of a specific child element. The awdmods 2026-05-18 mobile
  run had 12 such mappings.

- ``check_proxy_overload`` — proportion of findings whose visual_evidence
  type is in the "non-exact" set (proxy_element, generated_expected_zone,
  section_absence, page_level). A proxy-heavy report visually reads as
  approximate; >40% is the warning threshold.

- ``check_priority_path_needs_review`` — Priority Path stories and
  ADJACENT/BLOCK ethics findings shipping with confidence=needs_review are
  rejected. Operators MUST place those markers in editor.html before
  shipping a client-facing report.

- ``compute_visual_evidence_summary`` — counts by (type, confidence) tuple
  for the trace-log summary table.

These are PURE functions: pass in the list of markers (or review_state
findings) and the optional config, get back a CanaryResult-shaped dict.

See ``docs/ecp/2026-05-18-report-accuracy-and-hotspot-remediation-plan.md``
Phase 3 acceptance criteria + threshold table.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, TypedDict

# Reuse the same CanaryResult shape so the trace-log writer can emit these
# alongside the Phase I canaries without a separate schema.
class CanaryResult(TypedDict):
    name: str
    passed: bool
    summary: str
    detail: dict


# ---------------------------------------------------------------------------
# Thresholds (Phase 3 first-pass — tune from real-run data)
# ---------------------------------------------------------------------------

DEFAULT_GIANT_WIDTH_PCT = 85.0
"""Exact-element rect wider than this fails the giant-rectangle gate."""

DEFAULT_GIANT_HEIGHT_PCT = 70.0
"""Exact-element rect taller than this fails the giant-rectangle gate."""

DEFAULT_PROXY_OVERLOAD_RATIO = 0.40
"""When >40% of findings are non-exact, the report visually reads as approximate."""

NON_EXACT_TYPES = frozenset({
    "proxy_element",
    "generated_expected_zone",
    "section_absence",
    "page_level",
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ve(finding_or_marker: dict) -> dict | None:
    """Return the finding/marker's ``visual_evidence`` dict if present, else
    None. Tolerates both review-state findings (visual_evidence at top
    level) and marker mappings (same shape)."""
    ve = finding_or_marker.get("visual_evidence")
    return ve if isinstance(ve, dict) else None


def _zone(marker: dict) -> dict | None:
    """Return a (w_pct, h_pct) zone dict regardless of marker shape.

    Supports two shapes:
    - Nested ``zone`` dict ``{left_pct, top_pct, w_pct, h_pct}`` — produced
      by ``compute_marker_positions_v2`` for element-pinned markers.
    - Top-level ``x_pct/y_pct/w_pct/h_pct`` — produced by ``_marker_from_ai``
      in ``scripts/assembly/review_state.py`` (the real review-state shape).

    Returns None for point markers (no w_pct/h_pct) so the gate skips them
    without reporting them as exact rectangles. Phase 3 hardening fix
    (2026-05-18) — Codex review note 2 on commit 3e502e2.
    """
    zone = marker.get("zone")
    if isinstance(zone, dict) and ("w_pct" in zone or "h_pct" in zone):
        return zone
    # Top-level shape (review-state markers from _marker_from_ai)
    if "w_pct" in marker and "h_pct" in marker:
        # Only return a synthetic zone when the marker is a rect (not point).
        # Point markers have shape="point" and no w_pct/h_pct; we still guard.
        try:
            w = float(marker.get("w_pct") or 0)
            h = float(marker.get("h_pct") or 0)
        except (TypeError, ValueError):
            return None
        if w <= 0 and h <= 0:
            return None
        return {
            "left_pct": float(marker.get("x_pct") or 0),
            "top_pct": float(marker.get("y_pct") or 0),
            "w_pct": w,
            "h_pct": h,
        }
    return None


# ---------------------------------------------------------------------------
# Gate 1 — giant exact rectangles
# ---------------------------------------------------------------------------


def check_giant_exact_rectangles(
    markers: Iterable[dict],
    *,
    max_width_pct: float = DEFAULT_GIANT_WIDTH_PCT,
    max_height_pct: float = DEFAULT_GIANT_HEIGHT_PCT,
) -> CanaryResult:
    """Fail when an exact_element hotspot covers a giant slice of the viewport.

    Exact-element typing claims "this finding is about THIS specific element."
    If the resulting rectangle covers most of the viewport, the specialist
    anchored against a parent container (header, drawer, body) instead of a
    real subject element. Visually meaningless — the customer can't tell what
    the finding is about.

    Pass criteria: every exact_element marker's zone has width <= max_width_pct
    AND height <= max_height_pct.

    Markers without ``visual_evidence`` (legacy) or without a ``zone``
    rectangle (point markers) are skipped — they're either pre-Phase-2 or
    don't have a rectangle to measure.
    """
    violations: list[dict] = []
    exact_count = 0
    for m in markers:
        ve = _ve(m)
        if not ve or ve.get("type") != "exact_element":
            continue
        zone = _zone(m)
        if not zone:
            continue
        exact_count += 1
        w = float(zone.get("w_pct", 0) or 0)
        h = float(zone.get("h_pct", 0) or 0)
        if w > max_width_pct or h > max_height_pct:
            violations.append({
                "f_ref": m.get("f_ref"),
                "finding_index": m.get("finding_index"),
                "w_pct": round(w, 1),
                "h_pct": round(h, 1),
                "slide": m.get("slide"),
            })

    passed = not violations
    summary = (
        f"giant_exact_rectangles: {len(violations)} of {exact_count} exact-element "
        f"markers exceed {max_width_pct:.0f}%w/{max_height_pct:.0f}%h → "
        f"{'PASS' if passed else 'FAIL'}"
    )
    return {
        "name": "visual_evidence_giant_exact_rectangles",
        "passed": passed,
        "summary": summary,
        "detail": {
            "exact_count": exact_count,
            "violation_count": len(violations),
            "violations": violations,
            "max_width_pct": max_width_pct,
            "max_height_pct": max_height_pct,
        },
    }


# ---------------------------------------------------------------------------
# Gate 2 — proxy / generated / section / page-level overload
# ---------------------------------------------------------------------------


def check_proxy_overload(
    findings: Iterable[dict],
    *,
    max_ratio: float = DEFAULT_PROXY_OVERLOAD_RATIO,
) -> CanaryResult:
    """Warn when more than ``max_ratio`` of findings render as non-exact
    visual evidence. A report dominated by proxies and generated overlays
    visually reads as approximate even when the underlying findings are
    rigorous.

    Pass criteria: ratio of non-exact visual_evidence types <= max_ratio.
    Findings without visual_evidence are skipped (not counted in either the
    numerator or denominator) — legacy emissions don't participate.
    """
    typed = [f for f in findings if _ve(f) is not None]
    if not typed:
        return {
            "name": "visual_evidence_proxy_overload",
            "passed": True,
            "summary": "proxy_overload: no findings with visual_evidence; skipped",
            "detail": {"typed_count": 0, "non_exact_count": 0, "ratio": 0.0, "max_ratio": max_ratio},
        }
    non_exact = [f for f in typed if _ve(f).get("type") in NON_EXACT_TYPES]
    ratio = len(non_exact) / len(typed)
    passed = ratio <= max_ratio
    summary = (
        f"proxy_overload: {len(non_exact)}/{len(typed)} non-exact "
        f"({ratio:.0%} vs {max_ratio:.0%} threshold) → "
        f"{'PASS' if passed else 'WARN'}"
    )
    by_type: dict[str, int] = {}
    for f in typed:
        t = _ve(f).get("type", "?")
        by_type[t] = by_type.get(t, 0) + 1
    return {
        "name": "visual_evidence_proxy_overload",
        "passed": passed,
        "summary": summary,
        "detail": {
            "typed_count": len(typed),
            "non_exact_count": len(non_exact),
            "ratio": round(ratio, 3),
            "max_ratio": max_ratio,
            "by_type": dict(sorted(by_type.items())),
        },
    }


# ---------------------------------------------------------------------------
# Gate 3 — Priority Path / ethics shipping needs_review
# ---------------------------------------------------------------------------


def check_priority_path_needs_review(
    findings: Iterable[dict],
    *,
    priority_path_refs: Iterable[str] = (),
) -> CanaryResult:
    """Fail when Priority Path stories or ADJACENT/BLOCK ethics findings
    ship with confidence=needs_review.

    These are the highest-visibility surfaces in the report; an uncertain
    visual placement on either undermines customer trust. Operators MUST
    pick the marker location in editor.html before the report ships.

    Args:
        findings: iterable of finding dicts (review-state entries or
            similar) with ``visual_evidence``, ``f_ref`` or
            ``canonical_ref``, and optionally ``ethics_state``.
        priority_path_refs: iterable of f_refs that appear in any
            Priority Path story. Caller passes this from
            synthesizer-emission-v1.json's priority_path[].f_refs union.
    """
    priority_set = set(priority_path_refs)
    violations: list[dict] = []
    for f in findings:
        ve = _ve(f)
        if not ve or ve.get("confidence") != "needs_review":
            continue
        f_ref = f.get("f_ref") or f.get("canonical_ref") or ""
        is_priority = f_ref in priority_set
        is_ethics_actionable = (
            f.get("cluster") == "ethics"
            and f.get("ethics_state") in {"BLOCK", "ADJACENT"}
        ) or (
            isinstance(f_ref, str) and f_ref.startswith("ethics")
            and f.get("verdict") in {"FAIL", "PARTIAL"}
        )
        if is_priority or is_ethics_actionable:
            violations.append({
                "f_ref": f_ref,
                "is_priority": is_priority,
                "is_ethics_actionable": is_ethics_actionable,
                "ve_type": ve.get("type"),
            })

    passed = not violations
    summary = (
        f"priority_path_needs_review: {len(violations)} high-visibility "
        f"finding(s) shipping with confidence=needs_review → "
        f"{'PASS' if passed else 'FAIL'}"
    )
    return {
        "name": "visual_evidence_priority_path_needs_review",
        "passed": passed,
        "summary": summary,
        "detail": {
            "violation_count": len(violations),
            "violations": violations,
            "priority_refs_checked": len(priority_set),
        },
    }


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------


def compute_visual_evidence_summary(findings: Iterable[dict]) -> dict[str, dict[str, int]]:
    """Return a nested {type: {confidence: count}} table for the trace log.

    Output shape:
        {
          "exact_element":        {"high": 13, "medium": 0, ...},
          "proxy_element":        {"high": 0,  "medium": 10, ...},
          "generated_expected_zone": {...},
          ...
          "_total": {"high": N, "medium": N, ...}
        }
    """
    from scripts.report.visual_evidence import ALL_CONFIDENCES, ALL_TYPES  # local import

    table: dict[str, dict[str, int]] = {
        t: {c: 0 for c in ALL_CONFIDENCES} for t in ALL_TYPES
    }
    totals: dict[str, int] = {c: 0 for c in ALL_CONFIDENCES}
    for f in findings:
        ve = _ve(f)
        if not ve:
            continue
        t = ve.get("type")
        c = ve.get("confidence")
        if t in table and c in totals:
            table[t][c] += 1
            totals[c] += 1
    table["_total"] = totals
    return table


def render_summary_table(summary: dict[str, dict[str, int]]) -> str:
    """Render the summary dict as a human-readable block for audit-trace.log."""
    lines: list[str] = ["# VISUAL EVIDENCE QUALITY (Phase 3 — informational):"]
    header = f"#   {'type':<28} {'high':>6} {'medium':>8} {'low':>6} {'needs_review':>14}"
    lines.append(header)
    for type_name, counts in summary.items():
        if type_name == "_total":
            continue
        lines.append(
            f"#   {type_name:<28} "
            f"{counts.get('high', 0):>6} "
            f"{counts.get('medium', 0):>8} "
            f"{counts.get('low', 0):>6} "
            f"{counts.get('needs_review', 0):>14}"
        )
    if "_total" in summary:
        t = summary["_total"]
        lines.append(
            f"#   {'TOTAL':<28} "
            f"{t.get('high', 0):>6} "
            f"{t.get('medium', 0):>8} "
            f"{t.get('low', 0):>6} "
            f"{t.get('needs_review', 0):>14}"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Convenience: run all Phase 3 gates against a review-state file
# ---------------------------------------------------------------------------


def run_visual_quality_gates(
    review_state_path: Path,
    synthesizer_emission_path: Path | None = None,
    *,
    max_width_pct: float = DEFAULT_GIANT_WIDTH_PCT,
    max_height_pct: float = DEFAULT_GIANT_HEIGHT_PCT,
    max_proxy_ratio: float = DEFAULT_PROXY_OVERLOAD_RATIO,
) -> dict:
    """Run all Phase 3 gates against an engagement's review-state output.

    Args:
        review_state_path: path to ``review-state-{device}.json``. Used as
            the source for findings list and (via embedded ``markers``)
            for hotspot zones if present.
        synthesizer_emission_path: optional path to
            ``synthesizer-emission-v1.json``. When provided, the Priority
            Path refs are extracted to feed
            ``check_priority_path_needs_review``.

    Returns: same dict shape as ``run_all_canaries`` in canary_checks.py
    so the audit lead can write them into the same SUBSTANTIVE CANARIES
    block of audit-trace.log.
    """
    state = json.loads(review_state_path.read_text(encoding="utf-8"))
    findings = state.get("findings") or []
    # Markers carry zone rectangles + visual_evidence; review state lifts
    # markers into `markers` key when present.
    markers = state.get("markers") or []

    priority_refs: list[str] = []
    if synthesizer_emission_path is not None and synthesizer_emission_path.exists():
        try:
            synth = json.loads(synthesizer_emission_path.read_text(encoding="utf-8"))
            for story in synth.get("priority_path", []):
                priority_refs.extend(story.get("f_refs") or [])
        except (OSError, json.JSONDecodeError):
            pass

    r1 = check_giant_exact_rectangles(
        markers, max_width_pct=max_width_pct, max_height_pct=max_height_pct,
    )
    r2 = check_proxy_overload(findings, max_ratio=max_proxy_ratio)
    r3 = check_priority_path_needs_review(findings, priority_path_refs=priority_refs)
    summary = compute_visual_evidence_summary(findings)

    results = [r1, r2, r3]
    all_passed = all(r["passed"] for r in results)
    return {
        "review_state_path": str(review_state_path),
        "all_passed": all_passed,
        "results": results,
        "summary_line": "; ".join(r["summary"] for r in results),
        "summary_table": summary,
        "summary_table_rendered": render_summary_table(summary),
    }


__all__ = [
    "CanaryResult",
    "DEFAULT_GIANT_HEIGHT_PCT",
    "DEFAULT_GIANT_WIDTH_PCT",
    "DEFAULT_PROXY_OVERLOAD_RATIO",
    "NON_EXACT_TYPES",
    "check_giant_exact_rectangles",
    "check_priority_path_needs_review",
    "check_proxy_overload",
    "compute_visual_evidence_summary",
    "render_summary_table",
    "run_visual_quality_gates",
]
