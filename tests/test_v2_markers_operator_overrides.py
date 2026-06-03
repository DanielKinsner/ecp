"""Negative tests: compute_marker_positions_v2 tolerates operator override entries.

Operator --markers override entries are merged verbatim with no per-entry schema
validation. Covers adversarial-review findings 19, 20, 21:
- 19: mapping["finding_index"] KeyError when an operator entry omits it.
- 20: slide < len(screenshots) TypeError when slide is a string.
- 21: nat_w * fallback_pos["x_pct"] crash when x_pct/y_pct are missing,
  non-numeric, or fallback_position is not a dict.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.v2_markers import compute_marker_positions_v2  # noqa: E402

_BATON = {
    "elements": [],
    "viewport": {"width": 1440, "height": 900},
    "screenshots": [{"naturalWidth": 1000, "naturalHeight": 2000}],
}


class TestOperatorOverrideSafety(unittest.TestCase):
    def test_override_without_finding_index(self):
        mm = [{"slide": 0, "f_ref": "visual-cta F-01",
               "fallback_position": {"x_pct": 50, "y_pct": 50}}]
        self.assertIsInstance(compute_marker_positions_v2(mm, _BATON), dict)

    def test_string_slide_is_coerced(self):
        mm = [{"slide": "0", "finding_index": 1,
               "fallback_position": {"x_pct": 50, "y_pct": 50}}]
        self.assertIsInstance(compute_marker_positions_v2(mm, _BATON), dict)

    def test_fallback_position_string_and_missing_pct(self):
        mm = [{"slide": 0, "finding_index": 1, "fallback_position": {"x_pct": "50"}}]
        self.assertIsInstance(compute_marker_positions_v2(mm, _BATON), dict)

    def test_fallback_position_non_dict(self):
        mm = [{"slide": 0, "finding_index": 1, "fallback_position": "bad"}]
        self.assertIsInstance(compute_marker_positions_v2(mm, _BATON), dict)


if __name__ == "__main__":
    unittest.main()
