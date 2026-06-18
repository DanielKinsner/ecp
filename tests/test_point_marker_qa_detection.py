"""Guard: point markers must be visible to the placement-QA tools.

Regression for the repo-wide-review D1 finding (2026-06-18). Rect/box markers
store their position in x_pct/y_pct (top-left); POINT markers store it in
cx_pct/cy_pct (center). Both QA tools (scripts/report/placement_audit.py and
scripts/diagnose_engagement.py) read x_pct/y_pct only, so a point hotspot's
coordinates resolved to None/0 and the marker silently escaped stack/duplicate
detection and cropped to the (0,0) corner. The fix resolves the center via a
cx_pct/cy_pct fallback (_marker_xy / _marker_center).

Run:
    python -m pytest tests/test_point_marker_qa_detection.py
    python -m unittest tests.test_point_marker_qa_detection
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts"))

from report.placement_audit import _find_stacks, _marker_xy  # noqa: E402
import diagnose_engagement  # noqa: E402


def _point(fref: str, cx: float, cy: float, slide: str = "s1") -> dict:
    """A point marker as written by the editor / placement: center in cx/cy, no box."""
    return {"f_ref": fref, "shape": "point", "cx_pct": cx, "cy_pct": cy, "slide_id": slide}


def _rect(fref: str, x: float, y: float, slide: str = "s1") -> dict:
    return {"f_ref": fref, "shape": "rect", "x_pct": x, "y_pct": y,
            "w_pct": 10, "h_pct": 8, "slide_id": slide}


class MarkerCenterResolution(unittest.TestCase):
    def test_point_marker_resolves_to_center(self):
        self.assertEqual(_marker_xy(_point("f1", 40, 60)), (40, 60))
        self.assertEqual(diagnose_engagement._marker_center(_point("f1", 40, 60)), (40, 60))

    def test_rect_marker_resolves_to_top_left(self):
        self.assertEqual(_marker_xy(_rect("f1", 12, 34)), (12, 34))
        self.assertEqual(diagnose_engagement._marker_center(_rect("f1", 12, 34)), (12, 34))

    def test_coordless_marker_stays_none(self):
        m = {"f_ref": "f1", "shape": "point", "slide_id": "s1"}
        self.assertEqual(_marker_xy(m), (None, None))
        self.assertEqual(diagnose_engagement._marker_center(m), (None, None))


class PointMarkersDetectedByPlacementAudit(unittest.TestCase):
    def test_three_stacked_point_markers_form_a_stack(self):
        markers = [_point(f"f{i}", 50.0, 50.0) for i in range(3)]
        stacks = _find_stacks(markers)
        # Pre-fix: x_pct is None -> every point skipped -> {} (no stack detected).
        self.assertEqual(len(stacks), 1, "three co-located point markers must form one stack")
        self.assertEqual(sorted(next(iter(stacks.values()))), ["f0", "f1", "f2"])

    def test_rect_markers_still_stack(self):
        markers = [_rect(f"r{i}", 20.0, 20.0) for i in range(3)]
        self.assertEqual(len(_find_stacks(markers)), 1)


class PointMarkersDetectedByDiagnose(unittest.TestCase):
    def test_three_co_located_point_markers_are_stacked_and_duped(self):
        markers = [_point(f"f{i}", 50.0, 50.0) for i in range(3)]
        stacked, duped = diagnose_engagement._stacks_and_dupes(markers)
        # STACK_MIN=2, STACK_RADIUS_PCT=6 -> all three are within radius of >=2 others.
        self.assertEqual(stacked, {"f0", "f1", "f2"})
        # exact-coincidence (<=0.5%) with a different f_ref -> duplicates.
        self.assertEqual(duped, {"f0", "f1", "f2"})

    def test_hidden_point_marker_still_excluded(self):
        markers = [_point(f"f{i}", 50.0, 50.0) for i in range(3)]
        markers[0]["hidden"] = True
        stacked, _ = diagnose_engagement._stacks_and_dupes(markers)
        self.assertNotIn("f0", stacked)


if __name__ == "__main__":
    unittest.main()
