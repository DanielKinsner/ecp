"""Guard: re-anchoring a point marker must convert it to a rect.

Regression for the repo-wide-review D1 finding (2026-06-18). placement_repair's
re-anchor wrote x_pct/y_pct/w_pct/h_pct (a box) but left shape='point'. The
first-class hotspot editor (product.md §4.2) renders any non-rect/ellipse/poly
shape from cx_pct/cy_pct (default 50,50) — tools/editor/editor.js:1676 — so a
re-anchored point marker ignored the new box and kept the old/center position:
the "fix" had no visual effect for the operator. The repair now sets
shape='rect' and drops the stale cx_pct/cy_pct so both the editor and the report
render the re-anchored box.

Run:
    python -m pytest tests/test_placement_repair_point_to_rect.py
    python -m unittest tests.test_placement_repair_point_to_rect
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts"))

from report import placement_repair  # noqa: E402
from assembly import review_state as _review_state  # noqa: E402


class ReAnchorPointBecomesRect(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.eng = Path(self._tmp.name)
        self.device = "desktop"
        # A misplaced POINT marker: center in cx/cy, no box keys.
        review_state = {
            "schema_version": "review-state-v1",
            "findings": [{"f_ref": "F-01", "title": "No MSRP anchor on price block",
                          "hotspot_confidence": "exact"}],
            "markers": [{
                "marker_id": "m1", "f_ref": "F-01", "slide_id": "slide-0",
                "shape": "point", "cx_pct": 12.0, "cy_pct": 90.0, "source": "manual",
            }],
        }
        (self.eng / f"review-state-{self.device}.json").write_text(
            json.dumps(review_state), encoding="utf-8")

        # Force a re-anchor decision so we don't need real snap targets.
        self._orig_decide = placement_repair.decide_match
        self._orig_targets = _review_state._build_snap_targets
        _review_state._build_snap_targets = lambda *a, **k: {}
        placement_repair.decide_match = lambda *a, **k: {
            "action": "re-anchor",
            "best": {"slide_id": "slide-2", "x_pct": 40.0, "y_pct": 30.0,
                     "w_pct": 18.0, "h_pct": 9.0, "e_index": 7, "label": "price block"},
            "score": 0.91, "reason": "exact e-index match",
        }

    def tearDown(self):
        placement_repair.decide_match = self._orig_decide
        _review_state._build_snap_targets = self._orig_targets
        self._tmp.cleanup()

    def test_point_marker_is_converted_to_rect_with_new_box(self):
        result = placement_repair.repair(self.eng, self.device, ["F-01"], plugin_root=self.eng)
        self.assertEqual(result["re_anchored"], 1)

        rs = json.loads((self.eng / f"review-state-{self.device}.repaired.json").read_text(encoding="utf-8"))
        marker = next(m for m in rs["markers"] if m["f_ref"] == "F-01")

        # shape flipped to rect so the editor's rect branch consumes the new box
        self.assertEqual(marker["shape"], "rect")
        # new box written
        self.assertEqual(marker["x_pct"], 40.0)
        self.assertEqual(marker["y_pct"], 30.0)
        self.assertEqual(marker["w_pct"], 18.0)
        # stale center geometry removed so no renderer falls back to (12,90)/(50,50)
        self.assertNotIn("cx_pct", marker)
        self.assertNotIn("cy_pct", marker)


if __name__ == "__main__":
    unittest.main()
