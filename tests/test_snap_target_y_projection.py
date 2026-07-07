"""Regression: editor snap-to-element Y must match the renderer's Y.

Root cause (found 2026-07-07): review_state._build_snap_targets normalized a
snap target's y/h by the SECTION height (scroll_y_bottom - scroll_y_top), but
the section screenshot is a VIEWPORT-height capture and the marker layer
overlays the full image (.slide-stage img{width:100%;height:auto};
.marker-layer{inset:0}). compute_marker_positions_v2 normalizes by viewport
height and is correct. So for every section whose height != viewport height
(essentially all of them: e.g. 899 vs 1080), a snapped or placement-repaired
marker landed low by (1 - section_h/viewport_h) of the image.

This pins the invariant: the snap target and the auto-placed marker for the
SAME element resolve to the SAME y_pct. It fails on the section_h denominator
and passes on the viewport_h denominator.
"""
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.review_state import _element_snap_pct  # noqa: E402
from report.v2_markers import auto_map_markers_v2, compute_marker_positions_v2  # noqa: E402


# viewport 1440x900, but the section is only 700 tall (section_h != viewport_h) —
# this is the condition that exposed the bug.
_VIEWPORT_W = 1440.0
_VIEWPORT_H = 900.0
_SECTION_TOP = 0.0


def _baton(el_rect):
    return {
        "device": "laptop",
        "viewport": {"width": int(_VIEWPORT_W), "height": int(_VIEWPORT_H)},
        "screenshots": [
            {"path": "s1.jpg", "scrollY": 0, "naturalWidth": 1440, "naturalHeight": 900},
        ],
        "sections": [
            {"slug": "hero", "scroll_y_top": 0, "scroll_y_bottom": 700,
             "screenshot_ref": "s1.jpg"},
        ],
        "elements": [{"e_index": "e0", "rect": el_rect}],
    }


class TestSnapTargetYProjection(unittest.TestCase):
    def test_snap_y_matches_renderer_y(self):
        # Element mid-section: y=350 of a 900-tall viewport image.
        rect = {"x": 120, "y": 350, "width": 240, "height": 44}
        baton = _baton(rect)

        # Renderer's Y for the same element.
        mappings = auto_map_markers_v2(
            [{"index": 0, "f_ref": "visual-cta/F-01", "baton_index": "e0", "priority": "HIGH"}],
            baton,
        )
        slide_markers = compute_marker_positions_v2(mappings, baton)
        marker = next(m for marks in slide_markers.values() for m in marks)
        renderer_top_pct = marker["zone"]["top_pct"]

        # Snap target's Y for the same element.
        _x, snap_y_pct, _w, _h = _element_snap_pct(
            rect["x"], rect["y"], rect["width"], rect["height"],
            _SECTION_TOP, _VIEWPORT_W, _VIEWPORT_H,
        )

        # Editor snap and rendered report must agree (was 350/700=50% vs
        # 350/900=38.9% before the fix).
        self.assertAlmostEqual(snap_y_pct, renderer_top_pct, delta=0.2)

    def test_snap_y_uses_viewport_not_section_height(self):
        # Direct check on the denominator: y=450 -> 50% of viewport 900,
        # NOT 64.3% of section 700.
        _x, y_pct, _w, _h = _element_snap_pct(
            100, 450, 200, 40, _SECTION_TOP, _VIEWPORT_W, _VIEWPORT_H,
        )
        self.assertAlmostEqual(y_pct, 50.0, delta=0.01)


class TestPlacementYAcrossSections(unittest.TestCase):
    """End-to-end placement-Y invariant for section_h != viewport_h.

    The suite's other placement fixtures use one-viewport sections
    (section_h == viewport_h), which makes section_h- and viewport_h-normalized
    Y identical and hides the whole coordinate-space bug class (see
    docs / the 2026-07-07 snap-Y fix). This drives the REAL renderer across two
    sections — one shorter than the viewport, one equal — and pins that the
    rendered marker Y equals the element's true position in its viewport-height
    section image, and that the editor snap target agrees.
    """

    _VW, _VH = 1440.0, 900.0

    def _two_section_baton(self):
        return {
            "device": "laptop",
            "viewport": {"width": int(self._VW), "height": int(self._VH)},
            "screenshots": [
                {"path": "s1.jpg", "scrollY": 0, "naturalWidth": 1440, "naturalHeight": 900},
                {"path": "s2.jpg", "scrollY": 700, "naturalWidth": 1440, "naturalHeight": 900},
            ],
            "sections": [
                {"slug": "hero", "scroll_y_top": 0, "scroll_y_bottom": 700,  # 700 != 900
                 "screenshot_ref": "s1.jpg"},
                {"slug": "mid", "scroll_y_top": 700, "scroll_y_bottom": 1600,
                 "screenshot_ref": "s2.jpg"},
            ],
            # e0 near the bottom of the short first section; e1 in the second.
            "elements": [
                {"e_index": "e0", "rect": {"x": 100, "y": 600, "width": 200, "height": 40}},
                {"e_index": "e1", "rect": {"x": 100, "y": 1000, "width": 200, "height": 40}},
            ],
        }

    def _renderer_top_pct(self, baton, f_ref, baton_index):
        mappings = auto_map_markers_v2(
            [{"index": 0, "f_ref": f_ref, "baton_index": baton_index, "priority": "HIGH"}],
            baton,
        )
        slide_markers = compute_marker_positions_v2(mappings, baton)
        marker = next(m for marks in slide_markers.values() for m in marks)
        return marker["zone"]["top_pct"]

    def test_bottom_of_short_section_not_pushed_down(self):
        baton = self._two_section_baton()
        # e0: absolute y=600 in a viewport-height (900) image captured at scrollY 0.
        expected = (600 - 0) / self._VH * 100  # 66.7%, NOT 600/700 = 85.7%
        renderer = self._renderer_top_pct(baton, "visual-cta/F-01", "e0")
        _x, snap_y, _w, _h = _element_snap_pct(100, 600, 200, 40, 0.0, self._VW, self._VH)
        self.assertAlmostEqual(renderer, expected, delta=0.2)
        self.assertAlmostEqual(snap_y, expected, delta=0.2)

    def test_second_section_uses_its_screenshot_scroll(self):
        baton = self._two_section_baton()
        # e1: absolute y=1000, image captured at scrollY 700 -> (1000-700)/900.
        expected = (1000 - 700) / self._VH * 100  # 33.3%
        renderer = self._renderer_top_pct(baton, "pricing/F-02", "e1")
        _x, snap_y, _w, _h = _element_snap_pct(100, 1000, 200, 40, 700.0, self._VW, self._VH)
        self.assertAlmostEqual(renderer, expected, delta=0.2)
        self.assertAlmostEqual(snap_y, expected, delta=0.2)


if __name__ == "__main__":
    unittest.main()
