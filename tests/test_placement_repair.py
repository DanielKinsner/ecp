"""Tests for the placement-repair decision core (decide_match)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

import json  # noqa: E402
import tempfile  # noqa: E402

import assembly.review_state as _rs_mod  # noqa: E402
from report.placement_repair import decide_match, _overlap, _query_tokens, repair, finalize  # noqa: E402


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

    def test_off_slide_match_flagged_not_reanchored(self):
        # the only match is on a different slide than the marker -> flag (manual move)
        d = decide_match({"add", "cart"}, [_t("Add to Cart", "e1")], current_slide="desktop-section-9")
        self.assertEqual(d["action"], "flag")
        self.assertIn("different slide", d["reason"])

    def test_same_slide_match_reanchors(self):
        d = decide_match({"add", "cart"}, [_t("Add to Cart", "e1")], current_slide="desktop-section-1")
        self.assertEqual(d["action"], "re-anchor")


class TestQueryTokens(unittest.TestCase):
    def test_pulls_from_finding_and_marker(self):
        finding = {"finding_title": "Add to Cart Button Low Contrast"}
        marker = {"visual_evidence": {"observed_anchor": {"text_quote": "Add to Cart"}}}
        toks = _query_tokens(finding, marker)
        self.assertIn("cart", toks)
        self.assertNotIn("low", toks)  # stopword

    def test_prefers_finding_title_override(self):
        finding = {"finding_title": "Stale Wrong Subject", "finding_title_override": "Add to Cart Button"}
        toks = _query_tokens(finding, {})
        self.assertIn("cart", toks)
        self.assertNotIn("stale", toks)


class TestRepairIntegration(unittest.TestCase):
    """Locks the editor contract + file/log shapes the JS reads back (finding [6])."""

    def setUp(self):
        self._orig = _rs_mod._build_snap_targets
        _rs_mod._build_snap_targets = lambda eng, root, dev: {
            "desktop-section-1": [
                {"e_index": "e9", "label": "Add to Cart", "x_pct": 40, "y_pct": 50, "w_pct": 15, "h_pct": 8},
            ]
        }
        self.addCleanup(lambda: setattr(_rs_mod, "_build_snap_targets", self._orig))
        self.eng = Path(tempfile.mkdtemp(prefix="ecp-repair-int-"))
        self.rs = {
            "findings": [
                {"f_ref": "visual-cta F-01", "finding_title": "Add to Cart Button Low Contrast",
                 "hotspot_confidence": "exact-selector"},
                {"f_ref": "pricing F-02", "finding_title": "Pre-Order Badge Elapsed Date",
                 "hotspot_confidence": "exact-selector"},
            ],
            "markers": [
                {"f_ref": "visual-cta F-01", "marker_id": "m1", "slide_id": "desktop-section-1",
                 "shape": "rect", "source": "proposed_anchor_section",
                 "x_pct": 1, "y_pct": 1, "w_pct": 5, "h_pct": 5},
                {"f_ref": "pricing F-02", "marker_id": "m2", "slide_id": "desktop-section-1",
                 "shape": "rect", "source": "proposed_anchor_section",
                 "x_pct": 1, "y_pct": 1, "w_pct": 5, "h_pct": 5},
            ],
        }
        self.orig_path = self.eng / "review-state-desktop.json"
        self.orig_path.write_text(json.dumps(self.rs, indent=2), encoding="utf-8")
        self.orig_bytes = self.orig_path.read_bytes()

    def test_repair_sets_editor_contract_and_is_nondestructive(self):
        res = repair(self.eng, "desktop", ["visual-cta F-01", "pricing F-02"], _REPO)
        self.assertEqual(res["re_anchored"], 1)
        self.assertEqual(res["flagged"], 1)

        repaired = json.loads((self.eng / "review-state-desktop.repaired.json").read_text(encoding="utf-8"))
        rm = {m["f_ref"]: m for m in repaired["markers"]}
        rf = {f["f_ref"]: f for f in repaired["findings"]}

        # re-anchored marker: valid source enum + new e_index bbox
        self.assertEqual(rm["visual-cta F-01"]["source"], "e_index_lookup")
        self.assertEqual(rm["visual-cta F-01"]["snapped_baton_index"], "e9")
        self.assertEqual(rm["visual-cta F-01"]["x_pct"], 40)
        # finding-level confidence drives the editor: unverified re-anchor = check placement
        self.assertEqual(rf["visual-cta F-01"]["hotspot_confidence"], "section-match")
        # flagged finding enters the "Place manually" worklist
        self.assertEqual(rf["pricing F-02"]["hotspot_confidence"], "needs-manual-marker")

        # original file untouched
        self.assertEqual(self.orig_path.read_bytes(), self.orig_bytes)

        # log/action shapes the JS reads back
        actions = {e["f_ref"]: e["action"] for e in res["log"]}
        self.assertEqual(actions["visual-cta F-01"], "re-anchored")
        self.assertEqual(actions["pricing F-02"], "flagged")

    def test_duplicate_misplaced_processed_once(self):
        res = repair(self.eng, "desktop", ["pricing F-02", "pricing F-02"], _REPO)
        self.assertEqual(res["flagged"], 1)  # not 2

    def test_non_dict_root_raises(self):
        (self.eng / "review-state-desktop.json").write_text("[1, 2, 3]", encoding="utf-8")
        with self.assertRaises(ValueError):
            repair(self.eng, "desktop", ["pricing F-02"], _REPO)


class TestFinalize(unittest.TestCase):
    def test_applies_verdicts_to_repaired_file(self):
        eng = Path(tempfile.mkdtemp(prefix="ecp-finalize-"))
        rs = {"findings": [
            {"f_ref": "a F-1", "hotspot_confidence": "section-match"},
            {"f_ref": "b F-2", "hotspot_confidence": "section-match"},
        ], "markers": []}
        (eng / "review-state-desktop.repaired.json").write_text(json.dumps(rs), encoding="utf-8")
        res = finalize(eng, "desktop", ["a F-1"], ["b F-2"])
        rf = {f["f_ref"]: f for f in
              json.loads((eng / "review-state-desktop.repaired.json").read_text(encoding="utf-8"))["findings"]}
        self.assertEqual(rf["a F-1"]["hotspot_confidence"], "exact-selector")       # confirmed
        self.assertEqual(rf["b F-2"]["hotspot_confidence"], "needs-manual-marker")  # reverted/no-verdict
        self.assertEqual((res["confirmed"], res["reverted"]), (1, 1))


if __name__ == "__main__":
    unittest.main()
