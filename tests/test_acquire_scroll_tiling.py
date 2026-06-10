"""Contract test for mobile screenshot tiling (Root Cause #2 fix).

The pre-fix planner hard-clamped every device to 6 viewport shots and then spread
them evenly across ``max_scroll``. On a tall mobile PDP (390x844) that produced
~700px dead zones *between* the captured windows, so elements in the gaps had no
section image to anchor a hotspot to. The fix lets mobile tile contiguously up to
``MAX_SCREENSHOTS_MOBILE``. These tests lock the no-gap contract so a future edit
can't silently re-introduce the cliff.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

import acquire_url  # noqa: E402
from acquire_url import (  # noqa: E402
    MAX_SCREENSHOTS_DESKTOP,
    MAX_SCREENSHOTS_MOBILE,
    _device_screenshot_cap,
    _plan_scroll_ys,
)


# iPhone 14 viewport (matches acquire_url.device_profile("mobile"))
MOBILE_H = 844
DESKTOP_H = 1080


def _max_gap(ys: list[int], inner_h: int) -> int:
    """Largest uncaptured vertical span between consecutive viewport windows."""
    if len(ys) < 2:
        return 0
    return max(b - (a + inner_h) for a, b in zip(ys, ys[1:]))


class TestDeviceCap(unittest.TestCase):
    def test_mobile_cap_exceeds_desktop(self):
        self.assertGreater(MAX_SCREENSHOTS_MOBILE, MAX_SCREENSHOTS_DESKTOP)
        self.assertEqual(_device_screenshot_cap("mobile"), MAX_SCREENSHOTS_MOBILE)
        self.assertEqual(_device_screenshot_cap("desktop"), MAX_SCREENSHOTS_DESKTOP)
        self.assertEqual(_device_screenshot_cap("laptop"), MAX_SCREENSHOTS_DESKTOP)


class TestContiguousTiling(unittest.TestCase):
    def test_tall_mobile_page_has_no_gaps(self):
        # ~8.6k-px PDP, the exact shape from the 2026-06-02 diagnosis.
        doc_h = 8622
        ys = _plan_scroll_ys(
            max_scroll=doc_h - MOBILE_H, inner_h=MOBILE_H, doc_h=doc_h,
            max_shots=MAX_SCREENSHOTS_MOBILE,
        )
        # Contiguous: no dead zone between adjacent viewports.
        self.assertLessEqual(_max_gap(ys, MOBILE_H), 0)
        # And it actually reaches the bottom of the page.
        self.assertGreaterEqual(ys[-1] + MOBILE_H, doc_h - 1)

    def test_pre_fix_cap_would_have_left_gaps(self):
        # Regression witness: the OLD cap of 6 on the same page leaves big gaps.
        doc_h = 8622
        ys6 = _plan_scroll_ys(
            max_scroll=doc_h - MOBILE_H, inner_h=MOBILE_H, doc_h=doc_h, max_shots=6,
        )
        self.assertGreater(_max_gap(ys6, MOBILE_H), 300)

    def test_short_mobile_page_does_not_overshoot(self):
        # A short page must not waste shots — fewer than the cap.
        doc_h = 2000
        ys = _plan_scroll_ys(
            max_scroll=doc_h - MOBILE_H, inner_h=MOBILE_H, doc_h=doc_h,
            max_shots=MAX_SCREENSHOTS_MOBILE,
        )
        self.assertLess(len(ys), MAX_SCREENSHOTS_MOBILE)
        self.assertLessEqual(_max_gap(ys, MOBILE_H), 0)

    def test_desktop_typical_page_contiguous_within_cap(self):
        doc_h = 6000
        ys = _plan_scroll_ys(
            max_scroll=doc_h - DESKTOP_H, inner_h=DESKTOP_H, doc_h=doc_h,
            max_shots=MAX_SCREENSHOTS_DESKTOP,
        )
        self.assertLessEqual(len(ys), MAX_SCREENSHOTS_DESKTOP)
        self.assertLessEqual(_max_gap(ys, DESKTOP_H), 0)

    def test_single_viewport_page(self):
        ys = _plan_scroll_ys(max_scroll=0, inner_h=MOBILE_H, doc_h=600, max_shots=12)
        self.assertEqual(ys, [0])


class TestCapBoundRegime(unittest.TestCase):
    """W3: very tall pages past the per-device cap fall into the cap-binding
    regime documented in ``_plan_scroll_ys``'s docstring.

    The contiguity contract holds only when the page fits inside the cap.
    Past that, the planner evenly spaces ``max_shots`` shots across
    ``[0, max_scroll]`` and the spacing between consecutive tiles
    **exceeds the viewport height** — there are uncaptured vertical bands
    between tiles. That is the documented behavior, not a bug; this test
    pins it so a future "fix" that silently re-introduces the cliff (or
    silently raises the cap) fails loudly.
    """

    def test_very_tall_mobile_page_hits_cap_and_spacing_exceeds_viewport(self):
        # 30k-px page far exceeds 12 mobile viewports (~10.1k px), so the
        # planner is forced into the cap-binding regime regardless of overlap.
        doc_h = 30000
        ys = _plan_scroll_ys(
            max_scroll=doc_h - MOBILE_H,
            inner_h=MOBILE_H,
            doc_h=doc_h,
            max_shots=MAX_SCREENSHOTS_MOBILE,
        )
        # The cap binds — we get exactly MAX_SCREENSHOTS_MOBILE tiles, not more.
        self.assertEqual(len(ys), MAX_SCREENSHOTS_MOBILE)
        # Spacing between consecutive ys exceeds the viewport height — i.e.,
        # there are uncaptured bands between every adjacent tile.
        spacings = [b - a for a, b in zip(ys, ys[1:])]
        self.assertTrue(
            all(s > MOBILE_H for s in spacings),
            f"cap-binding regime must have every gap > viewport height; got spacings={spacings}",
        )
        # Therefore _max_gap (spacing minus inner_h) is strictly positive.
        self.assertGreater(_max_gap(ys, MOBILE_H), 0)

    def test_very_tall_desktop_page_hits_cap_and_spacing_exceeds_viewport(self):
        # Same regime on desktop with its smaller cap of 6.
        doc_h = 30000
        ys = _plan_scroll_ys(
            max_scroll=doc_h - DESKTOP_H,
            inner_h=DESKTOP_H,
            doc_h=doc_h,
            max_shots=MAX_SCREENSHOTS_DESKTOP,
        )
        self.assertEqual(len(ys), MAX_SCREENSHOTS_DESKTOP)
        spacings = [b - a for a, b in zip(ys, ys[1:])]
        self.assertTrue(
            all(s > DESKTOP_H for s in spacings),
            f"cap-binding regime must have every gap > viewport height; got spacings={spacings}",
        )
        self.assertGreater(_max_gap(ys, DESKTOP_H), 0)


class TestCliDefault(unittest.TestCase):
    def test_default_is_auto_sentinel(self):
        # 0 = auto per-device cap; parsed without an explicit value.
        p = acquire_url.build_arg_parser() if hasattr(acquire_url, "build_arg_parser") else None
        if p is None:
            self.skipTest("no standalone arg-parser factory")
        ns = p.parse_args(["--url", "https://example.com"])
        self.assertEqual(ns.max_screenshots, 0)


if __name__ == "__main__":
    unittest.main()
