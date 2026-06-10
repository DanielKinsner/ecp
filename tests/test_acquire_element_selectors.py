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
        # C16: per-selector cap is the sanity bound (100), NOT a real truncation.
        # The contract is capture-then-cap — the global cap (200, applied by
        # _dedupe_elements_phys) is the only intentional truncation point. A
        # bare slice(0, 10) here regresses the 36-product-card case.
        js = acquire_url._build_elements_js("example.com")
        self.assertIn("slice(0, 100)", js)
        # Use a closed-delimiter form so "slice(0, 100)" doesn't false-match.
        self.assertNotIn("slice(0, 10).map", js)
        self.assertNotIn("slice(0, 10);", js)

    def test_zero_sized_form_controls_are_kept(self):
        """RC#1(a): a zero-sized native <select>/<input>/<button> must NOT be
        dropped by the per-element size guard — it must resolve to a sized
        ancestor rect instead. Locks the source-level fix; the behavioral proof
        (real chromium) lives in tests/acquire-element-capture-smoke.mjs.
        """
        js = acquire_url._build_elements_js("example.com")
        self.assertIn("isFormControl", js,
            "form-control exception to the zero-size drop is missing")
        # the bare unconditional zero-size drop must be gone
        self.assertNotIn("if (r.width === 0 || r.height === 0) return null;", js,
            "unconditional zero-size drop still present — form controls re-dropped")
        # ancestor-rect resolution must be wired
        self.assertIn("getBoundingClientRect", js)
        self.assertIn("parentElement", js)

    def test_contamination_guard_and_hostname_intact(self):
        js = acquire_url._build_elements_js("example.com")
        self.assertIn("__contamination_detected", js)       # guard preserved
        self.assertIn('"example.com"', js)                  # hostname inlined as JSON literal


if __name__ == "__main__":
    unittest.main()
