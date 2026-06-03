"""Negative tests: review-state rendering/validation tolerate malformed input.

Covers adversarial-review findings 13, 14, 15 (bare float() on effect
opacity/feather crashes on non-numeric strings) and finding 16's tightening
(validate_review_state's reference check crashed on a non-dict finding/marker
in a hand-edited review-state file).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.review_state import (  # noqa: E402
    _render_effects,
    _render_spotlight,
    validate_review_state,
)


class TestEffectFloatCoercion(unittest.TestCase):
    def test_render_effects_non_numeric_strings(self):
        rs = {"slide_edits": [{"slide_id": "s1", "effects": [
            {"type": "blur", "mode": "inside", "feather_pct": "abc",
             "rect": {"x_pct": 10, "y_pct": 10, "w_pct": 20, "h_pct": 20}},
            {"type": "dim", "opacity": "xyz",
             "rect": {"x_pct": 0, "y_pct": 0, "w_pct": 50, "h_pct": 50}},
        ]}]}
        # Pre-fix: float("abc")/float("xyz") raise ValueError.
        html = _render_effects(rs, "s1")
        self.assertIsInstance(html, str)

    def test_render_spotlight_non_numeric_opacity(self):
        edit = {"effects": [{"type": "dim", "opacity": "not-a-number"}]}
        html = _render_spotlight("s1", [], [], edit)
        self.assertIsInstance(html, str)


class TestValidateReferencesNonDict(unittest.TestCase):
    def test_non_dict_finding_does_not_crash(self):
        rs = {"findings": [123], "markers": [], "slides": []}
        self.assertIsInstance(validate_review_state(rs), list)

    def test_non_dict_marker_does_not_crash(self):
        rs = {"findings": [], "markers": ["x"], "slides": []}
        self.assertIsInstance(validate_review_state(rs), list)


if __name__ == "__main__":
    unittest.main()
