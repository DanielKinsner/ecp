"""C1 step 1 — the placement seam is testable in isolation.

Before this seam, "does this finding auto-place or blank?" (product.md §4.2)
could only be exercised by running auto_map_markers_v2 over a whole baton and
reading match_method strings back out. decide_placement makes the decision a
pure function of (finding, PlacementContext) that returns a typed
``Placed | Blank`` — so each outcome (and WHY a blank blanked) is asserted
directly on the return value.
"""
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.placement import (  # noqa: E402
    Blank,
    Placed,
    PlacementContext,
    REASON_ABSENT,
    REASON_NO_GEOMETRY,
    REASON_OFFSLIDE,
    REASON_UNRESOLVED_BATON_INDEX,
    decide_placement,
)


def _baton(elements):
    return {
        "device": "laptop",
        "viewport": {"width": 1440, "height": 900},
        "screenshots": [
            {"path": "s1.jpg", "scrollY": 0, "naturalWidth": 1440, "naturalHeight": 900},
        ],
        "sections": [
            {"slug": "hero", "scroll_y_top": 0, "scroll_y_bottom": 899, "screenshot_ref": "s1.jpg"},
        ],
        "elements": elements,
    }


def _finding(baton_index, index=0, f_ref="visual-cta/F-01", priority="HIGH"):
    f = {"index": index, "f_ref": f_ref, "priority": priority}
    if baton_index is not None:
        f["baton_index"] = baton_index
    return f


class TestDecidePlacement(unittest.TestCase):
    def test_on_slide_element_is_placed(self):
        ctx = PlacementContext.from_baton(
            _baton([{"e_index": "e0", "rect": {"x": 40, "y": 100, "width": 300, "height": 60}}])
        )
        result = decide_placement(_finding("e0"), ctx)
        self.assertIsInstance(result, Placed)
        self.assertEqual(result.baton_element_index, 0)
        self.assertEqual(result.slide, 0)
        self.assertEqual(result.f_ref, "visual-cta/F-01")
        self.assertEqual(result.severity, "high")  # priority lowercased
        self.assertEqual(result.scope, "device")  # default

    def test_absent_baton_index_is_blank(self):
        ctx = PlacementContext.from_baton(_baton([{"e_index": "e0", "rect": {"x": 0, "y": 0, "width": 1, "height": 1}}]))
        result = decide_placement(_finding("absent"), ctx)
        self.assertIsInstance(result, Blank)
        self.assertEqual(result.reason, REASON_ABSENT)

    def test_missing_baton_index_is_blank_absent(self):
        ctx = PlacementContext.from_baton(_baton([{"e_index": "e0", "rect": {"x": 0, "y": 0, "width": 1, "height": 1}}]))
        result = decide_placement(_finding(None), ctx)
        self.assertIsInstance(result, Blank)
        self.assertEqual(result.reason, REASON_ABSENT)

    def test_out_of_range_index_is_unresolved(self):
        ctx = PlacementContext.from_baton(
            _baton([{"e_index": "e0", "rect": {"x": 40, "y": 100, "width": 300, "height": 60}}])
        )
        result = decide_placement(_finding("e9"), ctx)
        self.assertIsInstance(result, Blank)
        self.assertEqual(result.reason, REASON_UNRESOLVED_BATON_INDEX)

    def test_element_without_geometry_is_blank(self):
        # No rect at all -> no usable y or height -> never pin on an arbitrary slide.
        ctx = PlacementContext.from_baton(_baton([{"e_index": "e0"}]))
        result = decide_placement(_finding("e0"), ctx)
        self.assertIsInstance(result, Blank)
        self.assertEqual(result.reason, REASON_NO_GEOMETRY)

    def test_offslide_element_is_blank(self):
        # Element far below the single captured screenshot's viewport band.
        ctx = PlacementContext.from_baton(
            _baton([{"e_index": "e0", "rect": {"x": 40, "y": 5000, "width": 300, "height": 50}}])
        )
        result = decide_placement(_finding("e0"), ctx)
        self.assertIsInstance(result, Blank)
        self.assertEqual(result.reason, REASON_OFFSLIDE)


if __name__ == "__main__":
    unittest.main()
