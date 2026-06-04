"""Fix#4 fold-in: the v2 renderer's own Tier-0 placement-QA summary.

The renderer reports "0 unplaced" when every finding got *some* coordinate, which
says nothing about whether the hotspot landed on the right element. _placement_qa
surfaces (a) weak (non-element-anchored) placements and (b) >=STACK_MIN-on-a-pixel
stacks, deterministically, so the operator gets the signal without remembering to
run the standalone placement_audit.py (adversarial review 2026-06-03 §1 P1-5).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.v2_html_builder import _placement_qa, _STRONG_PLACEMENT_METHODS  # noqa: E402
from report.placement_audit import STACK_MIN  # noqa: E402


def _marker(f_ref, x, y):
    return {"f_ref": f_ref, "x_pct": x, "y_pct": y}


class TestPlacementQaWeak(unittest.TestCase):
    def test_strong_methods_are_not_weak(self):
        mappings = [{"match_method": m} for m in sorted(_STRONG_PLACEMENT_METHODS)]
        self.assertEqual(_placement_qa(mappings, {})["weak"], 0)

    def test_unplaced_not_counted_as_weak(self):
        # unplaced is reported on its own line, not as a weak *placement*.
        self.assertEqual(_placement_qa([{"match_method": "unplaced"}], {})["weak"], 0)

    def test_fallback_methods_are_weak(self):
        mappings = [
            {"match_method": "e_index_lookup"},          # strong
            {"match_method": "section_centroid"},        # weak
            {"match_method": "proposed_anchor_section"}, # weak
            {"match_method": "proposed_anchor_viewport"},# weak
            {"match_method": "section_stacked_manual"},  # weak (Fix#3 method)
            {"match_method": "banner"},                  # weak
        ]
        self.assertEqual(_placement_qa(mappings, {})["weak"], 5)


class TestPlacementQaStacks(unittest.TestCase):
    def test_three_distinct_on_a_pixel_is_a_stack(self):
        slide_markers = {0: [
            _marker("a/F-01", 50.0, 90.0),
            _marker("a/F-02", 50.04, 90.02),  # rounds to (50.0, 90.0)
            _marker("a/F-03", 49.96, 89.98),
        ]}
        qa = _placement_qa([], slide_markers)
        self.assertEqual(len(qa["stacks"]), 1)
        self.assertEqual(qa["stacks"][0]["count"], STACK_MIN)
        self.assertEqual(qa["stacks"][0]["f_refs"], ["a/F-01", "a/F-02", "a/F-03"])

    def test_two_on_a_pixel_is_not_a_stack(self):
        slide_markers = {0: [_marker("a/F-01", 10.0, 10.0), _marker("a/F-02", 10.0, 10.0)]}
        self.assertEqual(_placement_qa([], slide_markers)["stacks"], [])

    def test_same_fref_twice_does_not_inflate_a_stack(self):
        # AI-twin / duplicate f_ref on the same pixel is one distinct finding.
        slide_markers = {0: [_marker("a/F-01", 5.0, 5.0)] * STACK_MIN}
        self.assertEqual(_placement_qa([], slide_markers)["stacks"], [])

    def test_distinct_slides_do_not_merge(self):
        slide_markers = {
            0: [_marker("a/F-01", 50.0, 50.0), _marker("a/F-02", 50.0, 50.0)],
            1: [_marker("a/F-03", 50.0, 50.0)],
        }
        self.assertEqual(_placement_qa([], slide_markers)["stacks"], [])

    def test_deterministic_output(self):
        slide_markers = {0: [_marker(f"a/F-{i:02d}", 50.0, 50.0) for i in range(STACK_MIN)]}
        a = _placement_qa([], slide_markers)
        b = _placement_qa([], slide_markers)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
