"""Regression: _strip_svg_innards is single-pass (correctness + no O(n^2) DoS).

Adversarial review 2026-07-08 #21. The old implementation replaced one <svg>
subtree then re-scanned the whole mutated string from the start, up to 5000
times, each pass re-lowercasing the full HTML — O(n_svg x len(html)), tens of GB
of scanning on a hostile multi-MB page with thousands of <svg>. It also
mis-handled multiple top-level svgs (its own self-closing stub swallowed the
rescan, so only the first svg was stripped). The single-pass rewrite fixes both.

Run:
    python -m pytest tests/test_strip_svg_innards.py
    python -m unittest tests.test_strip_svg_innards
"""
from __future__ import annotations

import importlib.util
import time
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "ecp_acquire_dom_under_test", _REPO / "scripts" / "ecp_acquire_dom.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
strip = _mod._strip_svg_innards


class StripSvgInnards(unittest.TestCase):
    def test_single_svg_stubbed(self):
        self.assertEqual(
            strip('<div><svg><path d="M0"/></svg></div>'),
            '<div><svg aria-label="svg"/></div>',
        )

    def test_multiple_top_level_svgs_all_stubbed(self):
        # The pre-fix bug: only the first svg was stripped.
        self.assertEqual(
            strip('<div><svg><path/></svg>A<svg><g/></svg>B</div>'),
            '<div><svg aria-label="svg"/>A<svg aria-label="svg"/>B</div>',
        )

    def test_nested_svg_collapses_to_one_stub(self):
        self.assertEqual(strip('<svg><svg><path/></svg></svg>'), '<svg aria-label="svg"/>')

    def test_self_closing_icon_kept_and_later_svg_stripped(self):
        self.assertEqual(
            strip('<svg viewBox="0 0 1 1"/>X<svg><path/></svg>'),
            '<svg viewBox="0 0 1 1"/>X<svg aria-label="svg"/>',
        )

    def test_aria_label_preserved(self):
        self.assertEqual(strip('<svg aria-label="Cart"><path/></svg>'), '<svg aria-label="Cart"/>')

    def test_no_svg_unchanged(self):
        self.assertEqual(strip("<div>hi</div>"), "<div>hi</div>")

    def test_unbalanced_svg_leaves_remainder_verbatim(self):
        # No closing tag -> keep the rest as-is (do not hang or drop content).
        self.assertEqual(strip('<div>ok</div><svg><path/>'), '<div>ok</div><svg><path/>')

    def test_large_input_is_linear_not_quadratic(self):
        # 3000 svgs plus a 500 KB tail. The O(n_svg x len(html)) version would
        # do billions of char scans; the single-pass version is milliseconds.
        big = "<div>" + ("<svg><path d='x'/></svg>" * 3000) + ("x" * 500_000) + "</div>"
        start = time.perf_counter()
        result = strip(big)
        elapsed = time.perf_counter() - start
        self.assertEqual(result.count('aria-label="svg"'), 3000)
        self.assertLess(elapsed, 5.0, f"strip took {elapsed:.2f}s — likely regressed to O(n^2)")


if __name__ == "__main__":
    unittest.main()
