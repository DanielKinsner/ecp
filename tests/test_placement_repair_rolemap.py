"""Role-map re-anchoring in placement_repair (2026-07-21).

The repair tool's lexical matcher scores ~0.0 whenever the finding title
describes a PROBLEM ("Star Rating Touch Target Too Small") while the element
label is the element's TEXT ("4.7 out of 5 stars"). The anchor-candidates
sidecar already classifies elements into semantic roles (reviews-widget,
price-block, ...), so when the lexical path fails, a single unambiguous
same-slide candidate of the finding's inferred role is a trustworthy
re-anchor target.

Precision-first rules locked here:
- an explicit observed_anchor.candidate_id prefix is the strongest intent
- keyword inference is vetoed by false-friend guard tokens
  (the 2026-07-08 handoff trap: "Title Tag" SEO finding must NOT grab
  product-title)
- multi-role inference, multiple same-slide candidates, off-slide-only
  candidates, and the marker's CURRENT anchor all refuse to re-anchor
- no sidecar -> behavior identical to the pure lexical path
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

import assembly.review_state as _rs_mod  # noqa: E402
from assembly.anchor_candidates import SidecarLoadError  # noqa: E402
from report.placement_repair import (  # noqa: E402
    decide_match, infer_roles, repair,
)


def _t(label, e, slide="desktop-section-1"):
    return {"label": label, "e_index": e, "slide_id": slide,
            "x_pct": 10, "y_pct": 10, "w_pct": 20, "h_pct": 10}


class TestInferRoles(unittest.TestCase):
    def test_candidate_id_prefix_is_strongest_intent(self):
        marker = {"visual_evidence": {"observed_anchor": {"candidate_id": "reviews-widget-3"}}}
        self.assertEqual(infer_roles({"finding_title": "Anything At All"}, marker),
                         {"reviews-widget"})

    def test_candidate_id_with_unknown_prefix_ignored(self):
        marker = {"visual_evidence": {"observed_anchor": {"candidate_id": "made-up-role-1"}}}
        self.assertEqual(infer_roles({"finding_title": "Anything At All"}, marker), set())

    def test_keyword_inference_reviews(self):
        f = {"finding_title": "Star Rating Touch Target Is 12px CSS"}
        self.assertEqual(infer_roles(f, {}), {"reviews-widget"})

    def test_keyword_inference_price(self):
        f = {"finding_title": "No MSRP Anchor on $135.99 Floor Mat Price"}
        self.assertEqual(infer_roles(f, {}), {"price-block"})

    def test_title_tag_false_friend_guard(self):
        # The handoff's named trap: an SEO <title>-tag finding must NOT be
        # routed to the visible product-title heading.
        for title in ("Title Tag Missing Primary Keyword",
                      "Meta Title Exceeds 60 Characters",
                      "Page Title Duplicates Homepage"):
            self.assertEqual(infer_roles({"finding_title": title}, {}), set(), title)

    def test_genuine_product_title_finding_still_inferred(self):
        f = {"finding_title": "Product Title Hidden Below the Fold"}
        self.assertEqual(infer_roles(f, {}), {"product-title"})

    def test_multi_role_returned_as_is(self):
        # "payment" -> trust-strip AND "footer" -> footer-region: ambiguous by
        # design; decide_match refuses on len != 1.
        f = {"finding_title": "Payment Icons Buried in Footer"}
        self.assertEqual(infer_roles(f, {}), {"trust-strip", "footer-region"})

    def test_intent_ignores_observed_anchor_text_quote(self):
        # The anchor quote is element text (possibly from a WRONG anchor) —
        # it must not leak into role intent.
        marker = {"visual_evidence": {"observed_anchor": {"text_quote": "$4,399.00 price"}}}
        self.assertEqual(infer_roles({"finding_title": "Slow Hero Carousel"}, marker), set())

    def test_title_override_wins(self):
        f = {"finding_title": "Search Box Broken", "finding_title_override": "Slow Hero Carousel"}
        self.assertEqual(infer_roles(f, {}), set())


class TestDecideMatchRolePath(unittest.TestCase):
    """Role fallback inside the pure decision core."""

    def setUp(self):
        self.targets = [_t("4.7 out of 5 stars", "e10"), _t("Add to Cart", "e43")]
        self.e_to_roles = {"e10": {"reviews-widget"}, "e43": {"primary-cta"}}

    def test_lexical_failure_rescued_by_unique_role_candidate(self):
        d = decide_match({"star", "rating", "touch", "target"}, self.targets,
                         "desktop-section-1", desired_roles={"reviews-widget"},
                         e_to_roles=self.e_to_roles)
        self.assertEqual(d["action"], "re-anchor")
        self.assertEqual(d["best"]["e_index"], "e10")
        self.assertIn("role", d["reason"])
        self.assertIn("UNVERIFIED", d["reason"])

    def test_lexical_success_wins_over_role_path(self):
        d = decide_match({"add", "cart"}, self.targets, "desktop-section-1",
                         desired_roles={"reviews-widget"}, e_to_roles=self.e_to_roles)
        self.assertEqual(d["action"], "re-anchor")
        self.assertEqual(d["best"]["e_index"], "e43")  # lexical winner, not role

    def test_two_same_slide_role_candidates_refuse(self):
        targets = self.targets + [_t("5.0 / 5.0 (2 reviews)", "e24")]
        e_to_roles = dict(self.e_to_roles, e24={"reviews-widget"})
        d = decide_match({"star", "rating"}, targets, "desktop-section-1",
                         desired_roles={"reviews-widget"}, e_to_roles=e_to_roles)
        self.assertEqual(d["action"], "flag")

    def test_role_candidate_on_other_slide_refuses(self):
        targets = [_t("4.7 out of 5 stars", "e10", slide="desktop-section-9"),
                   _t("Add to Cart", "e43")]
        d = decide_match({"star", "rating"}, targets, "desktop-section-1",
                         desired_roles={"reviews-widget"}, e_to_roles=self.e_to_roles)
        self.assertEqual(d["action"], "flag")

    def test_multi_role_intent_refuses(self):
        d = decide_match({"payment", "footer"}, self.targets, "desktop-section-1",
                         desired_roles={"trust-strip", "footer-region"},
                         e_to_roles=self.e_to_roles)
        self.assertEqual(d["action"], "flag")

    def test_current_anchor_excluded_from_role_rescue(self):
        # The visual gate said the marker is WRONG where it is; re-asserting the
        # same element via its role would be a no-op repair that claims success.
        d = decide_match({"star", "rating"}, self.targets, "desktop-section-1",
                         desired_roles={"reviews-widget"}, e_to_roles=self.e_to_roles,
                         current_e_index="e10")
        self.assertEqual(d["action"], "flag")

    def test_no_role_args_behaves_lexically(self):
        d = decide_match({"star", "rating"}, self.targets, "desktop-section-1")
        self.assertEqual(d["action"], "flag")


class TestRepairIntegrationRoleMap(unittest.TestCase):
    def setUp(self):
        self._orig = _rs_mod._build_snap_targets
        _rs_mod._build_snap_targets = lambda eng, root, dev: {
            "desktop-section-1": [
                {"e_index": "e10", "label": "4.7 out of 5 stars",
                 "x_pct": 40, "y_pct": 50, "w_pct": 15, "h_pct": 8},
            ]
        }
        self.addCleanup(lambda: setattr(_rs_mod, "_build_snap_targets", self._orig))
        self.eng = Path(tempfile.mkdtemp(prefix="ecp-repair-role-"))
        rs = {
            "findings": [
                {"f_ref": "trust-credibility F-76",
                 "finding_title": "Review Summary Lacks Full Star Distribution",
                 "hotspot_confidence": "exact-selector"},
            ],
            "markers": [
                {"f_ref": "trust-credibility F-76", "marker_id": "m1",
                 "slide_id": "desktop-section-1", "shape": "rect",
                 "source": "proposed_anchor_section",
                 "x_pct": 1, "y_pct": 1, "w_pct": 5, "h_pct": 5},
            ],
        }
        (self.eng / "review-state-desktop.json").write_text(
            json.dumps(rs, indent=2), encoding="utf-8")

    def _write_sidecar(self):
        sidecar = {
            "candidates_by_role": {
                "reviews-widget": [{"candidate_id": "reviews-widget-1", "e_index": "e10"}],
            },
            "candidate_to_e_index": {"reviews-widget-1": "e10"},
        }
        (self.eng / "anchor-candidates-desktop.json").write_text(
            json.dumps(sidecar), encoding="utf-8")

    def test_role_rescue_end_to_end(self):
        self._write_sidecar()
        res = repair(self.eng, "desktop", ["trust-credibility F-76"], _REPO)
        self.assertEqual(res["re_anchored"], 1)
        repaired = json.loads(
            (self.eng / "review-state-desktop.repaired.json").read_text(encoding="utf-8"))
        m = repaired["markers"][0]
        self.assertEqual(m["snapped_baton_index"], "e10")
        self.assertEqual(m["x_pct"], 40)
        self.assertEqual(m["repair_status"], "re_anchored_unverified")
        # fail-safe confidence unchanged from the lexical path's contract
        self.assertEqual(repaired["findings"][0]["hotspot_confidence"], "section-match")
        # provenance is auditable in the log
        self.assertEqual(res["log"][0]["action"], "re-anchored")
        self.assertEqual(res["log"][0].get("via"), "role-map")

    def test_no_sidecar_keeps_pure_lexical_behavior(self):
        res = repair(self.eng, "desktop", ["trust-credibility F-76"], _REPO)
        self.assertEqual(res["re_anchored"], 0)
        self.assertEqual(res["flagged"], 1)

    def test_broken_sidecar_fails_loud(self):
        (self.eng / "anchor-candidates-desktop.json").write_text(
            "{not json", encoding="utf-8")
        with self.assertRaises(SidecarLoadError):
            repair(self.eng, "desktop", ["trust-credibility F-76"], _REPO)

    def test_lexical_reanchor_logs_lexical_provenance(self):
        self._write_sidecar()
        rs = json.loads((self.eng / "review-state-desktop.json").read_text(encoding="utf-8"))
        rs["findings"][0]["finding_title"] = "4.7 out of 5 stars widget"
        (self.eng / "review-state-desktop.json").write_text(json.dumps(rs), encoding="utf-8")
        res = repair(self.eng, "desktop", ["trust-credibility F-76"], _REPO)
        self.assertEqual(res["re_anchored"], 1)
        self.assertEqual(res["log"][0].get("via"), "lexical")


if __name__ == "__main__":
    unittest.main()
