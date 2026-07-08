"""Guard: the ethics-source same-domain integrity check must strip the "www."
PREFIX, not an arbitrary leading run of {w, .} characters.

Regression for adversarial review 2026-07-08 #19. _resolve_citations cleared an
ethics finding's SOURCE_URL when it pointed back at the audited store (same
domain). Both sides normalized the netloc with ``.lstrip("www.")``, which strips
ANY leading run of the characters w/. — so "www.wine.com" -> "ine.com" — and can
collapse two DISTINCT domains onto the same suffix, falsely clearing a
legitimately-different ethics source. The fix strips only the literal "www."
prefix.

Run:
    python -m pytest tests/test_html_builder_ethics_source_domain.py
    python -m unittest tests.test_html_builder_ethics_source_domain
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts"))

from report.html_builder import _resolve_citations  # noqa: E402


class EthicsSourceDomainPrefixStrip(unittest.TestCase):
    def _finding(self, source_url, state="ADJACENT"):
        return {"index": 1, "ethics_state": state, "source_url": source_url}

    def test_different_domain_not_falsely_cleared(self):
        # "wow.com" and "ow.com" are DIFFERENT domains. The old lstrip("www.")
        # turned "wow.com" -> "ow.com", matching the source and wrongly clearing
        # a legitimate ethics citation. The prefix-only strip keeps them distinct.
        findings = [self._finding("https://ow.com/ftc-regulation")]
        _resolve_citations(findings, str(_REPO), page_url="https://wow.com/product")
        self.assertEqual(
            findings[0]["source_url"], "https://ow.com/ftc-regulation",
            "A genuinely different-domain ethics source must NOT be cleared.",
        )

    def test_www_vs_apex_same_domain_still_cleared(self):
        # The real feature must be preserved: an ethics source pointing back at
        # the audited store (www vs apex is the same site) is still cleared.
        findings = [self._finding("https://www.store.com/checkout", state="BLOCK")]
        _resolve_citations(findings, str(_REPO), page_url="https://store.com/product")
        self.assertIsNone(
            findings[0]["source_url"],
            "An ethics source on the audited domain must still be cleared.",
        )


if __name__ == "__main__":
    unittest.main()
