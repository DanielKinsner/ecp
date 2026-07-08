"""The giant-exact-rectangle predicate — 'wide AND tall', not 'wide OR tall'.

An exact_element hotspot is only a misleading parent-container box when it is
BOTH very wide AND very tall (a real header / drawer / body / modal). A full-
width but SHORT strip (nav bar, footer, CTA row, price strip) is a PRECISE
anchor, not a container, so it must stay exact. Before this rule the down-rank
and the giant_exact_rectangles gate fired on width OR height, which demoted
~80% of full-width strips to approximate dashed proxies even though they were
already anchored to the correct element. product.md §10 (2026-07-08).
"""
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.visual_quality import (  # noqa: E402
    DEFAULT_GIANT_HEIGHT_PCT,
    DEFAULT_GIANT_WIDTH_PCT,
    is_giant_exact_rect,
)


class IsGiantExactRectTest(unittest.TestCase):
    def test_full_width_short_strip_is_not_giant(self):
        # 100%w / 4%h — a nav bar / footer / CTA row / price strip.
        self.assertFalse(is_giant_exact_rect(100.0, 4.0))

    def test_tall_narrow_column_is_not_giant(self):
        self.assertFalse(is_giant_exact_rect(20.0, 85.0))

    def test_bulky_container_is_giant(self):
        # Both dimensions large = a real parent container.
        self.assertTrue(is_giant_exact_rect(95.0, 80.0))

    def test_must_exceed_both_thresholds(self):
        self.assertTrue(
            is_giant_exact_rect(DEFAULT_GIANT_WIDTH_PCT + 1, DEFAULT_GIANT_HEIGHT_PCT + 1)
        )
        # Over width but not height -> not giant (this is the strip case).
        self.assertFalse(
            is_giant_exact_rect(DEFAULT_GIANT_WIDTH_PCT + 1, DEFAULT_GIANT_HEIGHT_PCT)
        )
        # Over height but not width -> not giant (tall column).
        self.assertFalse(
            is_giant_exact_rect(DEFAULT_GIANT_WIDTH_PCT, DEFAULT_GIANT_HEIGHT_PCT + 1)
        )

    def test_boundary_equal_is_not_giant(self):
        self.assertFalse(
            is_giant_exact_rect(DEFAULT_GIANT_WIDTH_PCT, DEFAULT_GIANT_HEIGHT_PCT)
        )

    def test_custom_thresholds_respected(self):
        self.assertTrue(is_giant_exact_rect(60, 60, max_width_pct=50, max_height_pct=50))
        self.assertFalse(is_giant_exact_rect(60, 40, max_width_pct=50, max_height_pct=50))


if __name__ == "__main__":
    unittest.main()
