"""Tests for the Tier-0 placement-confidence analyzer."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.placement_audit import analyze_device, score_marker, _find_stacks  # noqa: E402


def _m(**kw):
    base = {"f_ref": "x F-01", "slide_id": "desktop-section-1",
            "x_pct": 10, "y_pct": 10, "w_pct": 20, "h_pct": 15,
            "source": "e_index_lookup", "snapped_baton_index": 5,
            "visual_evidence": {"type": "exact_element", "confidence": "high"}}
    base.update(kw)
    return base


class TestScoreMarker(unittest.TestCase):
    def test_strong_marker_has_no_reasons(self):
        self.assertEqual(score_marker(_m()), [])

    def test_section_fallback_flagged(self):
        r = score_marker(_m(source="proposed_anchor_section", snapped_baton_index=None,
                            visual_evidence={"type": "section_absence", "confidence": "low"}))
        self.assertTrue(any("section-fallback" in x for x in r))

    def test_oversized_flagged(self):
        r = score_marker(_m(w_pct=90, h_pct=75))
        self.assertTrue(any("oversized width" in x for x in r))
        self.assertTrue(any("oversized height" in x for x in r))

    def test_proxy_low_confidence_flagged(self):
        r = score_marker(_m(visual_evidence={"type": "proxy_element", "confidence": "low"}))
        self.assertIn("low confidence", r)
        self.assertTrue(any("non-exact" in x for x in r))


class TestStacks(unittest.TestCase):
    def test_three_on_one_pixel_is_a_stack(self):
        ms = [_m(f_ref=f"c F-{i}", x_pct=50.0, y_pct=77.7) for i in range(3)]
        stacks = _find_stacks(ms)
        self.assertEqual(len(stacks), 1)
        self.assertEqual(len(next(iter(stacks.values()))), 3)

    def test_two_on_one_pixel_is_not_a_stack(self):
        ms = [_m(f_ref=f"c F-{i}", x_pct=50.0, y_pct=77.7) for i in range(2)]
        self.assertEqual(_find_stacks(ms), {})


class TestAnalyzeDevice(unittest.TestCase):
    def test_end_to_end_on_temp_review_state(self):
        eng = Path(tempfile.mkdtemp(prefix="ecp-pa-"))
        rs = {"findings": [{}, {}, {}], "markers": [
            _m(f_ref="a F-1"),                                  # strong
            _m(f_ref="b F-2", x_pct=50, y_pct=80),             # stacked
            _m(f_ref="c F-3", x_pct=50, y_pct=80),             # stacked
            _m(f_ref="d F-4", x_pct=50, y_pct=80),             # stacked
        ]}
        (eng / "review-state-desktop.json").write_text(json.dumps(rs), encoding="utf-8")
        r = analyze_device(eng, "desktop")
        self.assertEqual(r["strong"], 1)
        self.assertEqual(r["weak"], 3)
        self.assertEqual(len(r["stacks"]), 1)


if __name__ == "__main__":
    unittest.main()
