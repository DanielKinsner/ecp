"""LG4 Part 2 (2026-06-12 live gate) — fan out callouts for findings stacked on
the SAME element.

Multiple findings can legitimately cite one baton element (e.g. ethics F-27 +
F-66 both on e20). Their hotspot RECTS are identical and correct, but the
editor drew every callout at the same default offset (`x+8, y-8`), so the
numbered callouts overlapped pixel-for-pixel. `_default_callout_position` now
takes a stack index and steps each subsequent same-element callout sideways —
the marker rect is untouched (exact-tier preserved per §4.2). The report is
unaffected (it shows only the selected hotspot); this is an editor-view fix.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly import review_state as rs  # noqa: E402


class TestLG4CalloutDeStack(unittest.TestCase):
    def test_callout_fans_out_for_same_element_stack(self):
        marker = {"cx_pct": 30.0, "cy_pct": 40.0, "snapped_baton_index": "e5"}
        p0 = rs._default_callout_position(marker, 0)
        p1 = rs._default_callout_position(marker, 1)
        p2 = rs._default_callout_position(marker, 2)
        xs = [p0["x_pct"], p1["x_pct"], p2["x_pct"]]
        self.assertEqual(len(set(xs)), 3, f"callouts must fan out, got {xs}")
        self.assertLess(p0["x_pct"], p1["x_pct"])
        self.assertLess(p1["x_pct"], p2["x_pct"])
        # only the horizontal offset changes; vertical/size/anchor are stable
        self.assertEqual(p0["y_pct"], p2["y_pct"])
        self.assertEqual(p0["w_pct"], p2["w_pct"])
        self.assertEqual(p0["h_pct"], p2["h_pct"])
        self.assertEqual(p0["anchor"], p2["anchor"])

    def test_callout_x_stays_clamped(self):
        # A far-right element keeps the callout on-slide even when fanned out.
        marker = {"cx_pct": 72.0, "cy_pct": 40.0}
        for i in range(6):
            self.assertLessEqual(rs._default_callout_position(marker, i)["x_pct"], 74)

    def test_default_callout_backward_compatible(self):
        marker = {"cx_pct": 30.0, "cy_pct": 40.0}
        self.assertEqual(
            rs._default_callout_position(marker), rs._default_callout_position(marker, 0)
        )


if __name__ == "__main__":
    unittest.main()
