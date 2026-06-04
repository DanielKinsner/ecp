"""Tests for the capture-coverage verification tool."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.capture_coverage import classify, coverage, compare_coverage  # noqa: E402


def _write_baton(eng: Path, fname: str, device: str, elements: list) -> None:
    (eng / fname).write_text(
        json.dumps({"device": device, "elements": elements}), encoding="utf-8"
    )


class TestClassify(unittest.TestCase):
    def test_buckets(self):
        self.assertIn("dropdown", classify({"tag": "select"}))
        self.assertIn("dropdown", classify({"selector": '[class*="dropdown"]'}))
        self.assertIn("submit_input", classify({"tag": "input", "selector": 'input[type="submit"]'}))
        self.assertIn("gallery", classify({"selector": '[class*="gallery"]'}))
        self.assertIn("promo", classify({"selector": '[class*="announce"]'}))
        self.assertIn("aria_named", classify({"selector": "[aria-label]"}))
        self.assertEqual(classify({"tag": "div"}), set())


class TestCoverage(unittest.TestCase):
    def test_counts(self):
        eng = Path(tempfile.mkdtemp(prefix="ecp-cov-"))
        (eng / "baton.json").write_text(json.dumps({"elements": [
            {"tag": "select"},
            {"tag": "input", "selector": 'input[type="submit"]'},
            {"tag": "div"},
        ]}), encoding="utf-8")
        cov = coverage(eng, "baton.json")
        self.assertEqual(cov["total"], 3)
        self.assertEqual(cov["controls"]["dropdown"], 1)
        self.assertEqual(cov["controls"]["submit_input"], 1)

    def test_missing_baton_returns_none(self):
        self.assertIsNone(coverage(Path(tempfile.mkdtemp()), "baton.json"))

    def test_coverage_reports_device(self):
        eng = Path(tempfile.mkdtemp(prefix="ecp-cov-"))
        _write_baton(eng, "baton-mobile.json", "mobile", [{"tag": "select"}])
        cov = coverage(eng, "baton-mobile.json")
        self.assertEqual(cov["device"], "mobile")


class TestCompareCoverage(unittest.TestCase):
    def test_compare_covers_both_devices(self):
        """compare must report a delta for BOTH desktop and mobile, not just
        batons[0] (the desktop-blind bug, adversarial review §1 P0-2)."""
        before = Path(tempfile.mkdtemp(prefix="ecp-before-"))
        after = Path(tempfile.mkdtemp(prefix="ecp-after-"))
        # before: no dropdowns captured on either device
        _write_baton(before, "baton.json", "desktop", [{"tag": "div"}])
        _write_baton(before, "baton-mobile.json", "mobile", [{"tag": "div"}])
        # after: dropdown now captured on BOTH devices (RC#1 fix landed)
        _write_baton(after, "baton.json", "desktop", [{"tag": "select"}])
        _write_baton(after, "baton-mobile.json", "mobile", [{"tag": "select"}])

        cmp = compare_coverage(before, after)
        devices = {d["device"]: d for d in cmp["devices"]}
        self.assertIn("desktop", devices)
        self.assertIn("mobile", devices, "compare must surface the mobile delta")
        # mobile dropdown went 0 -> 1 (this is the half the old tool could not see)
        self.assertEqual(devices["mobile"]["delta"]["dropdown"], (0, 1))
        self.assertEqual(devices["desktop"]["delta"]["dropdown"], (0, 1))
        self.assertEqual(cmp["warnings"], [])

    def test_compare_does_not_mislabel_mobile_as_desktop(self):
        """When the desktop baton is absent, the mobile baton must be labeled
        mobile (not desktop) and a warning must be emitted (review §1 P0-2)."""
        before = Path(tempfile.mkdtemp(prefix="ecp-before-"))
        after = Path(tempfile.mkdtemp(prefix="ecp-after-"))
        _write_baton(before, "baton-mobile.json", "mobile", [{"tag": "div"}])
        _write_baton(after, "baton-mobile.json", "mobile", [{"tag": "select"}])

        cmp = compare_coverage(before, after)
        devices = {d["device"]: d for d in cmp["devices"]}
        self.assertIn("mobile", devices)
        self.assertNotIn("desktop", devices,
            "absent desktop baton must NOT be mislabeled as a desktop delta")
        self.assertTrue(any("desktop" in w.lower() for w in cmp["warnings"]),
            "missing desktop baton should produce a warning")


if __name__ == "__main__":
    unittest.main()
