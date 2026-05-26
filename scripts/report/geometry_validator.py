"""Pre-render geometry validation for v2 hotspot placement.

The validator is intentionally independent from the final overlay renderer:
it checks whether the current marker output is internally consistent with the
baton's viewport, screenshot, section, and element coordinate spaces before an
HTML report is written.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:  # Support both `python -m report.geometry_validator` and direct script use.
    from .geometry import slide_for_css_y
    from .markers import _infer_element_coord_scale
    from .v2_loader import load_v2_engagement
    from .v2_markers import (
        _slide_for_y,
        auto_map_markers_v2,
        compute_marker_positions_v2,
        merge_markers,
    )
except ImportError:  # pragma: no cover - exercised by manual direct invocation.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from report.geometry import slide_for_css_y
    from report.markers import _infer_element_coord_scale
    from report.v2_loader import load_v2_engagement
    from report.v2_markers import (
        _slide_for_y,
        auto_map_markers_v2,
        compute_marker_positions_v2,
        merge_markers,
    )


def viewport_dpr(viewport: dict[str, Any]) -> float:
    """Return the effective DPR for legacy and v2 viewport shapes."""
    raw = (
        viewport.get("dpr_actual")
        or viewport.get("dpr")
        or viewport.get("dpr_requested")
        or 1
    )
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 1.0
    return value if value > 0 else 1.0


def element_rect_raw(element: dict[str, Any]) -> dict[str, float] | None:
    """Return raw element geometry from v2 rect or legacy flat fields."""
    rect = element.get("rect") if isinstance(element.get("rect"), dict) else element
    try:
        return {
            "x": float(rect.get("x", 0) or 0),
            "y": float(rect.get("y", 0) or 0),
            "width": float(rect.get("width", 0) or 0),
            "height": float(rect.get("height", 0) or 0),
        }
    except (AttributeError, TypeError, ValueError):
        return None


def backfill_screenshots_from_sections(baton: dict[str, Any]) -> None:
    """Populate v1-style screenshots[] from v2 sections[] when absent.

    This mirrors the current renderer setup so the validator checks the same
    marker inputs that the report renderer is about to consume.
    """
    if baton.get("screenshots") or not baton.get("sections"):
        return
    viewport = baton.get("viewport") or {}
    screenshots: list[dict[str, Any]] = []
    for section in baton.get("sections") or []:
        ref = section.get("screenshot_ref")
        if not ref:
            continue
        screenshots.append({
            "path": ref,
            "scrollY": section.get("scroll_y_top", section.get("scrollY", 0)) or 0,
            "naturalWidth": viewport.get("width", 1),
            "naturalHeight": viewport.get("height", 1),
        })
    if screenshots:
        baton["screenshots"] = screenshots


def _css_envelope_height(
    screenshots: list[Any],
    sections: list[Any],
    viewport: dict[str, Any],
) -> float:
    try:
        viewport_h = float(viewport.get("height") or 0)
    except (TypeError, ValueError):
        viewport_h = 0.0

    max_bottom = viewport_h
    for screenshot in screenshots:
        if not isinstance(screenshot, dict):
            continue
        try:
            max_bottom = max(max_bottom, float(screenshot.get("scrollY", 0) or 0) + viewport_h)
        except (TypeError, ValueError):
            continue
    for section in sections:
        if not isinstance(section, dict):
            continue
        for key in ("scroll_y_bottom", "scrollY"):
            try:
                max_bottom = max(max_bottom, float(section.get(key, 0) or 0))
            except (TypeError, ValueError):
                pass
    return max_bottom


def _likely_expected_scale(
    rects: list[dict[str, float]],
    css_envelope_h: float,
    dpr: float,
) -> float:
    if dpr <= 1 or css_envelope_h <= 0 or not rects:
        return 1.0
    raw_y_max = max(r["y"] + max(0.0, r["height"]) for r in rects)
    return dpr if raw_y_max > css_envelope_h * 1.25 else 1.0


def _marker_by_ref(slide_markers: dict[Any, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for slide, markers in slide_markers.items():
        for marker in markers or []:
            ref = marker.get("f_ref")
            if not ref:
                continue
            enriched = dict(marker)
            enriched["_slide"] = slide
            out[str(ref)] = enriched
    return out


def validate_v2_hotspot_geometry(
    baton: dict[str, Any],
    findings: list[dict[str, Any]],
    marker_mappings: list[dict[str, Any]],
    slide_markers: dict[Any, list[dict[str, Any]]],
    *,
    max_x_clamp_rate: float = 0.30,
    min_e_index_section_match_rate: float = 0.80,
) -> dict[str, Any]:
    """Validate v2 marker geometry and return a structured result."""
    elements = baton.get("elements") or []
    screenshots = baton.get("screenshots") or []
    sections = baton.get("sections") or []
    viewport = baton.get("viewport") or {}
    dpr = viewport_dpr(viewport)
    try:
        inferred_scale = float(_infer_element_coord_scale(elements, screenshots, viewport, dpr))
    except (TypeError, ValueError):
        inferred_scale = 1.0

    rects = [rect for el in elements if (rect := element_rect_raw(el)) is not None]
    css_envelope_h = _css_envelope_height(screenshots, sections, viewport)
    raw_y_max = max((r["y"] + max(0.0, r["height"]) for r in rects), default=0.0)
    expected_scale = _likely_expected_scale(rects, css_envelope_h, dpr)

    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    if dpr > 1 and inferred_scale == 1.0 and raw_y_max > css_envelope_h * 1.25:
        failures.append({
            "code": "dpr_scale_mismatch",
            "message": (
                "DPR-scaled element rects look like physical pixels, but "
                "element_coord_scale inferred CSS passthrough."
            ),
            "detail": {
                "dpr": dpr,
                "inferred_scale": inferred_scale,
                "expected_scale": expected_scale,
                "raw_y_max": raw_y_max,
                "css_envelope_h": css_envelope_h,
            },
        })

    marker_lookup = _marker_by_ref(slide_markers)
    e_index_mappings = [
        m for m in marker_mappings
        if str(m.get("match_method") or "").startswith("e_index")
        and isinstance(m.get("baton_element_index"), int)
    ]

    clamped_refs: list[dict[str, Any]] = []
    for mapping in e_index_mappings:
        marker = marker_lookup.get(str(mapping.get("f_ref")))
        if not marker:
            continue
        try:
            x_pct = float(marker.get("x_pct", 0) or 0)
        except (TypeError, ValueError):
            continue
        if x_pct > 95.0:
            clamped_refs.append({
                "f_ref": mapping.get("f_ref"),
                "slide": int(mapping.get("slide", 0) or 0) + 1,
                "x_pct": round(x_pct, 2),
            })

    clamp_denominator = len(e_index_mappings)
    clamp_rate = len(clamped_refs) / clamp_denominator if clamp_denominator else 0.0
    if clamp_denominator and clamp_rate > max_x_clamp_rate:
        failures.append({
            "code": "right_edge_clamp_rate",
            "message": "Too many e_index hotspots are clamped near the right edge.",
            "detail": {
                "clamped": len(clamped_refs),
                "total": clamp_denominator,
                "rate": round(clamp_rate, 4),
                "threshold": max_x_clamp_rate,
                "examples": clamped_refs[:8],
            },
        })

    try:
        viewport_h = float(viewport.get("height") or 0)
    except (TypeError, ValueError):
        viewport_h = 0.0
    slide_mismatches: list[dict[str, Any]] = []
    slide_matches = 0
    slide_total = 0
    scale_for_expected = expected_scale or 1.0
    for mapping in e_index_mappings:
        elem_idx = mapping.get("baton_element_index")
        if not isinstance(elem_idx, int) or elem_idx < 0 or elem_idx >= len(elements):
            continue
        rect = element_rect_raw(elements[elem_idx])
        if not rect:
            continue
        center_y_css = (rect["y"] + max(0.0, rect["height"]) / 2.0) / scale_for_expected
        expected_slide = slide_for_css_y(center_y_css, viewport_h, screenshots, sections)
        try:
            actual_slide = int(mapping.get("slide", 0) or 0)
        except (TypeError, ValueError):
            actual_slide = 0
        slide_total += 1
        if actual_slide == expected_slide:
            slide_matches += 1
        else:
            slide_mismatches.append({
                "f_ref": mapping.get("f_ref"),
                "element": f"e{elem_idx}",
                "actual_slide": actual_slide + 1,
                "expected_slide": expected_slide + 1,
                "raw_y": round(rect["y"], 2),
                "css_y": round(rect["y"] / scale_for_expected, 2),
            })

    slide_match_rate = slide_matches / slide_total if slide_total else 1.0
    if slide_total and slide_match_rate < min_e_index_section_match_rate:
        failures.append({
            "code": "e_index_slide_mismatch_rate",
            "message": (
                "Too many e_index hotspots land on a different slide than "
                "their CSS-normalized target rect."
            ),
            "detail": {
                "matched": slide_matches,
                "total": slide_total,
                "rate": round(slide_match_rate, 4),
                "threshold": min_e_index_section_match_rate,
                "examples": slide_mismatches[:8],
            },
        })

    if not e_index_mappings:
        warnings.append({
            "code": "no_e_index_markers",
            "message": "No e_index markers were available for geometry validation.",
        })

    return {
        "passed": not failures,
        "summary": {
            "device": baton.get("device"),
            "dpr": dpr,
            "inferred_scale": inferred_scale,
            "expected_scale": expected_scale,
            "raw_y_max": raw_y_max,
            "css_envelope_h": css_envelope_h,
            "e_index_markers": len(e_index_mappings),
            "right_edge_clamp_rate": round(clamp_rate, 4),
            "e_index_slide_match_rate": round(slide_match_rate, 4),
            "findings": len(findings),
        },
        "failures": failures,
        "warnings": warnings,
    }


def format_validation_report(result: dict[str, Any], *, engagement: Path | None = None, device: str | None = None) -> str:
    """Format a geometry validation result for CLI/stderr output."""
    status = "PASSED" if result.get("passed") else "FAILED"
    lines = [f"Hotspot geometry validation {status}"]
    if engagement is not None:
        lines.append(f"engagement: {engagement}")
    if device:
        lines.append(f"device: {device}")

    summary = result.get("summary") or {}
    if summary:
        lines.append("summary:")
        for key in (
            "dpr",
            "inferred_scale",
            "expected_scale",
            "raw_y_max",
            "css_envelope_h",
            "e_index_markers",
            "right_edge_clamp_rate",
            "e_index_slide_match_rate",
            "findings",
        ):
            if key in summary:
                lines.append(f"  {key}: {summary[key]}")

    for failure in result.get("failures") or []:
        lines.append(f"FAIL {failure.get('code')}: {failure.get('message')}")
        detail = failure.get("detail") or {}
        for key, value in detail.items():
            if key == "examples" and isinstance(value, list):
                lines.append("  examples:")
                for example in value:
                    lines.append(f"    - {json.dumps(example, sort_keys=True)}")
            else:
                lines.append(f"  {key}: {value}")

    for warning in result.get("warnings") or []:
        lines.append(f"WARN {warning.get('code')}: {warning.get('message')}")

    return "\n".join(lines)


def validate_engagement_geometry(
    engagement_dir: Path,
    device: str,
    plugin_root: Path,
    *,
    audit_file: str | None = None,
    baton_file: str | None = None,
) -> dict[str, Any]:
    """Load a v2 engagement, compute current markers, and validate them."""
    inputs = load_v2_engagement(
        engagement_dir,
        device,
        plugin_root,
        audit_file=audit_file,
        baton_file=baton_file,
    )
    baton = inputs["baton"]
    backfill_screenshots_from_sections(baton)
    mappings = auto_map_markers_v2(inputs["findings"], baton)
    merged = merge_markers(mappings, None)
    slide_markers = compute_marker_positions_v2(merged, baton)
    return validate_v2_hotspot_geometry(baton, inputs["findings"], merged, slide_markers)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate v2 hotspot geometry before report render")
    parser.add_argument("--engagement", required=True, help="Path to engagement directory")
    parser.add_argument("--device", required=True, choices=["mobile", "desktop", "laptop"])
    parser.add_argument("--plugin-root", default=".", help="Path to plugin root")
    parser.add_argument("--audit", default=None, help="Audit filename override")
    parser.add_argument("--baton", default=None, help="Baton filename override")
    args = parser.parse_args(argv)

    engagement = Path(args.engagement).resolve()
    plugin_root = Path(args.plugin_root).resolve()
    result = validate_engagement_geometry(
        engagement,
        args.device,
        plugin_root,
        audit_file=args.audit,
        baton_file=args.baton,
    )
    stream = sys.stdout if result.get("passed") else sys.stderr
    print(format_validation_report(result, engagement=engagement, device=args.device), file=stream)
    return 0 if result.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
