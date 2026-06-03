"""Negative tests: report rendering tolerates malformed anchor/viewport input.

Covers adversarial-review findings 18, 26, 27:
- html_builder._process_screenshots: baton viewport used as a dict when a
  malformed baton sends "viewport": null.
- v2_html_builder._build_evidence_anchors_html: int(scroll_y) and
  escape_html(viewport) crashed on operator-supplied string scroll_y / numeric
  viewport (operator-override anchors aren't schema-validated).
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.html_builder import _process_screenshots  # noqa: E402
from report.v2_html_builder import _build_evidence_anchors_html  # noqa: E402


class TestEvidenceAnchorsHtml(unittest.TestCase):
    def test_string_scroll_y_and_numeric_viewport(self):
        finding = {"evidence_anchors": [
            {"type": "visual", "reference": "section-1.jpg",
             "scroll_y": "abc", "viewport": 5}]}
        self.assertIsInstance(_build_evidence_anchors_html(finding), str)

    def test_both_type_non_integer_scroll_y(self):
        finding = {"evidence_anchors": [
            {"type": "both", "reference": "e5", "scroll_y": "40.5"}]}
        self.assertIsInstance(_build_evidence_anchors_html(finding), str)


class TestProcessScreenshotsNullViewport(unittest.TestCase):
    def test_null_viewport_does_not_crash(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        baton = {"viewport": None, "screenshots": []}
        result = _process_screenshots(Path(tmp.name), baton, {})
        self.assertIsInstance(result, dict)


if __name__ == "__main__":
    unittest.main()
