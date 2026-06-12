from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.v2_html_builder import _apply_review_state_to_slide_markers  # noqa: E402


def _review_finding(f_ref: str) -> dict:
    return {
        "f_ref": f_ref,
        "status": "approved",
        "callout_position": {"x_pct": 12, "y_pct": 12, "w_pct": 24, "h_pct": 8},
        "callout_color": "#facc15",
    }


def _finding(f_ref: str, index: int = 1) -> dict:
    return {
        "f_ref": f_ref,
        "index": index,
        "cluster_index": index,
        "priority": "high",
    }


def test_hidden_review_state_markers_emit_no_v2_marker():
    review_state = {
        "slides": [{"slide_id": "slide-1"}],
        "findings": [
            _review_finding("hero F-01"),
            _review_finding("hero F-02"),
        ],
        "markers": [
            {
                "marker_id": "hero-F-01-manual",
                "f_ref": "hero F-01",
                "slide_id": "slide-1",
                "shape": "point",
                "hidden": True,
                "severity": "high",
            },
            {
                "marker_id": "hero-F-02-manual",
                "f_ref": "hero F-02",
                "slide_id": "slide-1",
                "shape": "rect",
                "x_pct": 10,
                "y_pct": 20,
                "w_pct": 30,
                "h_pct": 10,
                "severity": "medium",
            },
        ],
    }

    patched = _apply_review_state_to_slide_markers(
        {},
        review_state,
        [_finding("hero F-01", 1), _finding("hero F-02", 2)],
    )

    rendered_refs = {marker["f_ref"] for marker in patched.get(0, [])}
    assert "hero F-01" not in rendered_refs
    assert "hero F-02" in rendered_refs


def test_coordless_review_state_markers_emit_no_v2_marker():
    review_state = {
        "slides": [{"slide_id": "slide-1"}],
        "findings": [_review_finding("hero F-01")],
        "markers": [
            {
                "marker_id": "hero-F-01-manual",
                "f_ref": "hero F-01",
                "slide_id": "slide-1",
                "shape": "point",
                "severity": "high",
            },
        ],
    }

    patched = _apply_review_state_to_slide_markers(
        {},
        review_state,
        [_finding("hero F-01", 1)],
    )

    rendered_refs = {marker["f_ref"] for marker in patched.get(0, [])}
    assert "hero F-01" not in rendered_refs


def test_approved_deliberate_blank_review_state_stays_blank_in_v2_render():
    review_finding = _review_finding("hero F-01")
    review_finding["hotspot_confidence"] = "needs-manual-marker"
    review_state = {
        "slides": [{"slide_id": "slide-1"}],
        "findings": [review_finding],
        "markers": [
            {
                "marker_id": "hero-F-01-manual",
                "f_ref": "hero F-01",
                "slide_id": "slide-1",
                "shape": "point",
                "severity": "high",
            },
        ],
    }

    patched = _apply_review_state_to_slide_markers(
        {},
        review_state,
        [_finding("hero F-01", 1)],
    )

    rendered_refs = {marker["f_ref"] for marker in patched.get(0, [])}
    assert "hero F-01" not in rendered_refs


def test_point_review_state_marker_uses_cx_cy_geometry():
    review_state = {
        "slides": [{"slide_id": "slide-1"}],
        "findings": [_review_finding("hero F-01")],
        "markers": [
            {
                "marker_id": "hero-F-01-manual",
                "f_ref": "hero F-01",
                "slide_id": "slide-1",
                "shape": "point",
                "cx_pct": 17.25,
                "cy_pct": 61.5,
                "severity": "high",
            },
        ],
    }

    patched = _apply_review_state_to_slide_markers(
        {},
        review_state,
        [_finding("hero F-01", 1)],
    )

    marker = patched[0][0]
    assert marker["x_pct"] == 17.25
    assert marker["y_pct"] == 61.5


def test_ellipse_review_state_marker_uses_center_radius_geometry():
    review_state = {
        "slides": [{"slide_id": "slide-1"}],
        "findings": [_review_finding("hero F-01")],
        "markers": [
            {
                "marker_id": "hero-F-01-manual",
                "f_ref": "hero F-01",
                "slide_id": "slide-1",
                "shape": "ellipse",
                "cx": 45,
                "cy": 30,
                "rx": 12,
                "ry": 8,
                "severity": "high",
            },
        ],
    }

    patched = _apply_review_state_to_slide_markers(
        {},
        review_state,
        [_finding("hero F-01", 1)],
    )

    marker = patched[0][0]
    assert marker["x_pct"] == 45
    assert marker["y_pct"] == 30
    assert marker["zone"] == {
        "left_pct": 33,
        "top_pct": 22,
        "w_pct": 24,
        "h_pct": 16,
    }
