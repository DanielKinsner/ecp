"""Source guard: the v2 report carries the §3 ISN'T-list disclaimer (G9, 2026-05-29).

product.md §3 declares the audit is NOT a measurement/testing tool, NOT a compliance
certification, and NOT legal advice. The rendered report footer must carry an
informational disclaimer so the client-facing deliverable honors that boundary.
This guard fails if the footer disclaimer (or its style hook) is removed.
"""
from __future__ import annotations

import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_HTML = (_REPO / "scripts" / "report" / "templates" / "html_structure.py").read_text(encoding="utf-8")
_CSS = (_REPO / "scripts" / "report" / "templates" / "css.py").read_text(encoding="utf-8")


class TestReportDisclaimer(unittest.TestCase):
    def test_footer_disclaimer_text_present(self):
        self.assertIn("bottom-disclaimer", _HTML)
        self.assertIn("not a measurement or testing service", _HTML)
        self.assertIn("not a compliance certification", _HTML)
        self.assertIn("not legal advice", _HTML)

    def test_disclaimer_style_hook_present(self):
        self.assertIn(".bottom-disclaimer", _CSS)


if __name__ == "__main__":
    unittest.main()
