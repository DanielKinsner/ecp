"""Tests for the capture-coverage verification tool."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.capture_coverage import classify, coverage  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
