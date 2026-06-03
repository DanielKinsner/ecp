"""Contract test for the acquirer element-selector allowlist (Root Cause #1 fix).

The element-extraction JS runs in a live headless browser, so the real proof is a
live re-audit + the visual-QA gate. This test locks the selector contract so a
future edit can't silently re-drop the hero controls the diagnosis identified
(YMM dropdowns / submit buttons / promo bars / gallery thumbnails / aria-named).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

import acquire_url  # noqa: E402


class TestElementSelectors(unittest.TestCase):
    def test_includes_targeted_control_selectors(self):
        js = acquire_url._build_elements_js("example.com")
        for sel in ("'select'", '[role="combobox"]', '[role="listbox"]',
                    'input[type="submit"]', 'input[type="button"]',
                    '[class*="dropdown"]', '[class*="gallery"]', '[class*="thumb"]',
                    '[class*="announce"]', '[class*="promo"]', '[aria-label]'):
            self.assertIn(sel, js, msg=f"missing selector: {sel}")

    def test_per_selector_cap_raised(self):
        self.assertIn("slice(0, 10)", acquire_url._build_elements_js("example.com"))

    def test_contamination_guard_and_hostname_intact(self):
        js = acquire_url._build_elements_js("example.com")
        self.assertIn("__contamination_detected", js)       # guard preserved
        self.assertIn('"example.com"', js)                  # hostname inlined as JSON literal


if __name__ == "__main__":
    unittest.main()
