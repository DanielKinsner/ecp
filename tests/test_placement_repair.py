"""Tests for the placement-repair decision core (decide_match)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.placement_repair import decide_match, _overlap, _query_tokens  # noqa: E402


def _t(label, e):
    return {"label": label, "e_index": e, "slide_id": "desktop-section-1",
            "x_pct": 10, "y_pct": 10, "w_pct": 20, "h_pct": 10}


class TestOverlap(unittest.TestCase):
    def test_overlap_ignores_stopwords(self):
        self.assertGreater(_overlap("Add to Cart", {"add", "cart"}), 0.6)
        self.assertEqual(_overlap("", {"add"}), 0.0)


class TestDecideMatch(unittest.TestCase):
    def test_confident_unambiguous_reanchor(self):
        d = decide_match({"add", "cart", "button"}, [_t("Add to Cart", "e1"), _t("Footer links", "e2")])
        self.assertEqual(d["action"], "re-anchor")
        self.assertEqual(d["best"]["e_index"], "e1")
        self.assertIn("UNVERIFIED", d["reason"])

    def test_ambiguous_is_flagged(self):
        d = decide_match({"add", "cart"}, [_t("Add to Cart", "e1"), _t("Add to Cart", "e2")])
        self.assertEqual(d["action"], "flag")
        self.assertIn("ambiguous", d["reason"])

    def test_weak_match_flagged(self):
        d = decide_match({"pre", "order", "price", "badge"}, [_t("Regular price", "e1")])
        self.assertEqual(d["action"], "flag")
        self.assertIn("too weak", d["reason"])

    def test_no_overlap_flags_acquirer_gap(self):
        d = decide_match({"installment", "shoppay"}, [_t("Add to Cart", "e1"), _t("image", "e2")])
        self.assertEqual(d["action"], "flag")
        self.assertIn("NOT captured", d["reason"])

    def test_empty_query_flags_no_text(self):
        d = decide_match(set(), [_t("Add to Cart", "e1")])
        self.assertEqual(d["action"], "flag")
        self.assertIn("no anchorable element text", d["reason"])


class TestQueryTokens(unittest.TestCase):
    def test_pulls_from_finding_and_marker(self):
        finding = {"finding_title": "Add to Cart Button Low Contrast"}
        marker = {"visual_evidence": {"observed_anchor": {"text_quote": "Add to Cart"}}}
        toks = _query_tokens(finding, marker)
        self.assertIn("cart", toks)
        self.assertNotIn("low", toks)  # stopword


if __name__ == "__main__":
    unittest.main()
