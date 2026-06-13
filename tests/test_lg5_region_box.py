"""LG5 (2026-06-12 live gate) — a small, exactly-resolved element rendered as a
single POINT instead of a BOX.

compute_marker_positions_v2 only emitted a rectangle ``zone`` when BOTH
rect_w_pct >= 2.0 AND rect_h_pct >= 2.0. The ethics F-66 strikethrough price
(e166 = 56x21 px in a 1920x1080 viewport -> 2.92%w x 1.94%h) passed the width
gate but failed the height gate, so zone fell to None and the renderer drew a
point over a region — the POINT_FOR_REGION the live gate flagged.

The fix expands any sub-minimum dimension of an exactly-resolved element up to
the minimum visible size (centered), so the region renders as a box. It must
NOT change the marker's center, and a normal-sized element's zone is unchanged.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.v2_markers import (  # noqa: E402
    MIN_VISIBLE_ZONE_PCT,
    auto_map_markers_v2,
    compute_marker_positions_v2,
)


def _baton(elements):
    return {
        "device": "desktop",
        "viewport": {"width": 1920, "height": 1080},
        "screenshots": [
            {"path": "s1.jpg", "scrollY": 0, "naturalWidth": 1920, "naturalHeight": 1080},
        ],
        "sections": [
            {"slug": "hero", "scroll_y_top": 0, "scroll_y_bottom": 1079, "screenshot_ref": "s1.jpg"},
        ],
        "elements": elements,
    }


def _finding(index, f_ref):
    return {"index": index, "f_ref": f_ref, "baton_index": f"e{index}", "priority": "HIGH"}


def _markers(slide_markers):
    return [mk for marks in slide_markers.values() for mk in marks]


class TestLG5RegionBox(unittest.TestCase):
    def test_small_exact_element_renders_as_box(self):
        # 56x21 of 1920x1080 -> 2.92%w (>=2.0) x 1.94%h (<2.0): the F-66 shape.
        baton = _baton([{"e_index": "e0", "rect": {"x": 900, "y": 400, "width": 56, "height": 21}}])
        mappings = auto_map_markers_v2([_finding(0, "ethics/F-66")], baton)
        marker = _markers(compute_marker_positions_v2(mappings, baton))[0]
        zone = marker["zone"]
        self.assertIsNotNone(
            zone, "LG5: a small exactly-resolved element must render as a box, not a point"
        )
        # The thin dimension is expanded up to the minimum visible size...
        self.assertGreaterEqual(round(zone["h_pct"], 4), MIN_VISIBLE_ZONE_PCT)
        # ...the already-wide dimension is left as-is (not shrunk/expanded).
        self.assertAlmostEqual(zone["w_pct"], 56 / 1920 * 100, places=3)
        # ...and the box covers the element: the marker point lies inside it.
        self.assertLessEqual(zone["left_pct"], marker["x_pct"])
        self.assertGreaterEqual(zone["left_pct"] + zone["w_pct"], marker["x_pct"])
        self.assertLessEqual(zone["top_pct"], marker["y_pct"])
        self.assertGreaterEqual(zone["top_pct"] + zone["h_pct"], marker["y_pct"])

    def test_normal_element_zone_unchanged(self):
        # 300x60 -> ~15.6%w x ~5.6%h: both above the floor, emitted verbatim.
        baton = _baton([{"e_index": "e0", "rect": {"x": 100, "y": 200, "width": 300, "height": 60}}])
        mappings = auto_map_markers_v2([_finding(0, "visual-cta/F-01")], baton)
        marker = _markers(compute_marker_positions_v2(mappings, baton))[0]
        zone = marker["zone"]
        self.assertIsNotNone(zone)
        self.assertAlmostEqual(zone["w_pct"], 300 / 1920 * 100, places=3)
        self.assertAlmostEqual(zone["h_pct"], 60 / 1080 * 100, places=3)


if __name__ == "__main__":
    unittest.main()
