"""Tests for the stage-attribution diagnostic (scripts/diagnose_engagement.py).

Covers the pure attribution logic + a live end-to-end run against the committed
awdmods engagement fixture (which is the documented failure case: a black-hero
capture failure + stacked/weak-anchor/predicate-mismatch placements). If this
suite passes, the tool will run on the operator's machine.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

import diagnose_engagement as dx  # noqa: E402


class TestLG4StacksSkipHiddenMarkers(unittest.TestCase):
    """LG4 Part 1 (2026-06-12 live gate): _stacks_and_dupes coerced a
    coord-less marker's (None, None) to (0, 0) via ``a.get("x_pct", 0) or 0``,
    so every hidden absence marker (12 desktop / 15 mobile in the repro) piled
    onto (0, 0) and was counted as a STACK. That inflated the live-gate
    'STACKED 10-11 / DUPLICATE 3-4 per device' signal — absences are not
    rendered, so they must not count toward placement stacks.
    """

    def test_hidden_and_coordless_markers_are_not_stacked(self):
        markers = [
            {"f_ref": f"ethics/F-{i:02d}", "slide_id": "desktop-section-1",
             "hidden": True, "x_pct": None, "y_pct": None}
            for i in range(12)
        ] + [
            {"f_ref": "pricing/F-01", "slide_id": "desktop-section-1", "x_pct": 30, "y_pct": 40},
            {"f_ref": "pricing/F-02", "slide_id": "desktop-section-1", "x_pct": 70, "y_pct": 80},
        ]
        stacked, duped = dx._stacks_and_dupes(markers)
        self.assertEqual(stacked, set())
        self.assertEqual(duped, set())

    def test_real_same_element_overlap_still_flagged(self):
        # Two placed markers at the same pixel are a genuine overlap — keep
        # flagging those (the fix only excludes hidden/coord-less markers).
        markers = [
            {"f_ref": "a/F-1", "slide_id": "desktop-section-1", "x_pct": 12.0, "y_pct": 13.0},
            {"f_ref": "b/F-2", "slide_id": "desktop-section-1", "x_pct": 12.0, "y_pct": 13.0},
            {"f_ref": "c/F-3", "slide_id": "desktop-section-1", "x_pct": 12.1, "y_pct": 13.1},
        ]
        stacked, duped = dx._stacks_and_dupes(markers)
        self.assertEqual(stacked, {"a/F-1", "b/F-2", "c/F-3"})
        self.assertTrue({"a/F-1", "b/F-2"} <= duped)


class TestLG6PredicateRegexLockstep(unittest.TestCase):
    """LG6: the runtime business rule (business_rules._check_predicate_mismatch)
    ports the operator diagnostic's OVER/UNDER/PRICE regexes. They MUST stay
    identical — drift means a finding the diagnostic flags as PREDICATE_MISMATCH
    could escape the lead's runtime bounce, which is the gap LG6 closes.
    """

    def test_predicate_regexes_match_between_modules(self):
        from assembly.business_rules import (
            _PREDICATE_OVER,
            _PREDICATE_PRICE,
            _PREDICATE_UNDER,
        )

        self.assertEqual(_PREDICATE_OVER.pattern, dx._OVER.pattern)
        self.assertEqual(_PREDICATE_UNDER.pattern, dx._UNDER.pattern)
        self.assertEqual(_PREDICATE_PRICE.pattern, dx._PRICE.pattern)


class TestPredicateMismatch(unittest.TestCase):
    def test_over_threshold_anchored_to_cheaper_element_flags(self):
        msg = dx._predicate_mismatch(
            "No Installment Pricing On Items Over $1,000", "From $135.99")
        self.assertIsNotNone(msg)
        self.assertIn("1,000", msg)
        self.assertIn("135", msg)

    def test_over_threshold_anchored_to_qualifying_element_is_fine(self):
        self.assertIsNone(
            dx._predicate_mismatch("Items Over $1,000 lack installments", "$1,766.00"))

    def test_no_predicate_no_flag(self):
        self.assertIsNone(dx._predicate_mismatch("Hero has no headline", "From $135.99"))

    def test_under_threshold(self):
        msg = dx._predicate_mismatch("Cheap items under $50 hidden", "$1,766.00")
        self.assertIsNotNone(msg)


class TestAttribute(unittest.TestCase):
    def _f(self, **kw):
        base = {"finding_title": "", "observation": "", "finding_body": ""}
        base.update(kw)
        return base

    def test_capture_suspect_wins_for_blank_region_finding(self):
        f = self._f(finding_title="Hero Band Is Empty Black Space With No Supporting Media")
        m = {"shape": "point", "source": "proposed_anchor_element",
             "visual_evidence": {"type": "generated_expected_zone", "confidence": "low"}}
        label, _ = dx.attribute(f, m, None, capture_suspect=True, stacked=False, duped=False)
        self.assertEqual(label, "CAPTURE_SUSPECT")

    def test_predicate_mismatch_attribution(self):
        f = self._f(finding_title="No Installment Pricing On Items Over $1,000")
        m = {"shape": "rect", "source": "e_index_lookup",
             "visual_evidence": {"type": "exact_element", "confidence": "high"}}
        anchor = {"text_content": "From $135.99"}
        label, _ = dx.attribute(f, m, anchor, capture_suspect=False, stacked=False, duped=False)
        self.assertEqual(label, "PREDICATE_MISMATCH")

    def test_point_for_region(self):
        f = self._f(finding_title="Empty Black Band Wastes the Entire Above-Fold Zone")
        m = {"shape": "point", "source": "e_index_lookup",
             "visual_evidence": {"type": "exact_element", "confidence": "high"}}
        label, _ = dx.attribute(f, m, {"text_content": "Select Year"},
                                capture_suspect=False, stacked=False, duped=False)
        self.assertEqual(label, "POINT_FOR_REGION")

    def test_weak_anchor(self):
        f = self._f(finding_title="Homepage has no aggregate trust block")
        m = {"shape": "point", "source": "proposed_anchor_section",
             "visual_evidence": {"type": "generated_expected_zone", "confidence": "low"}}
        label, _ = dx.attribute(f, m, None, capture_suspect=False, stacked=False, duped=False)
        self.assertEqual(label, "WEAK_ANCHOR")

    def test_exact_element_high_conf_is_ok(self):
        f = self._f(finding_title="CTA contrast is low on the Find Parts button")
        m = {"shape": "rect", "source": "e_index_lookup", "snapped_baton_index": 117,
             "visual_evidence": {"type": "exact_element", "confidence": "high"}}
        label, _ = dx.attribute(f, m, {"text_content": "Find parts"},
                                capture_suspect=False, stacked=False, duped=False)
        self.assertEqual(label, "OK")


class TestStacksAndDupes(unittest.TestCase):
    def test_identical_position_is_duplicate(self):
        markers = [
            {"f_ref": "a F-1", "slide_id": "s1", "x_pct": 10, "y_pct": 10},
            {"f_ref": "b F-2", "slide_id": "s1", "x_pct": 10, "y_pct": 10},
        ]
        stacked, duped = dx._stacks_and_dupes(markers)
        self.assertEqual(duped, {"a F-1", "b F-2"})

    def test_cluster_within_radius_is_stacked(self):
        markers = [
            {"f_ref": f"x F-{i}", "slide_id": "s1", "x_pct": 50 + i * 0.5, "y_pct": 50}
            for i in range(4)
        ]
        stacked, _ = dx._stacks_and_dupes(markers)
        self.assertTrue(stacked)

    def test_spread_markers_not_stacked(self):
        markers = [
            {"f_ref": "a F-1", "slide_id": "s1", "x_pct": 5, "y_pct": 5},
            {"f_ref": "b F-2", "slide_id": "s1", "x_pct": 80, "y_pct": 80},
        ]
        stacked, duped = dx._stacks_and_dupes(markers)
        self.assertEqual(stacked, set())
        self.assertEqual(duped, set())


class TestEndToEndOnAwdmodsFixture(unittest.TestCase):
    """The committed awdmods engagement is the documented failure case."""

    ENG = _REPO / "docs" / "ecp" / "2026-06-08-8e46b1c8"

    def test_desktop_flags_capture_failure_and_defects(self):
        if not (self.ENG / "review-state-desktop.json").exists():
            self.skipTest("awdmods engagement fixture not present")
        dev = dx.diagnose_device(self.ENG, "desktop", make_crops=False)
        self.assertIsNotNone(dev)
        # The hero capture failed: scroll-trigger DOM + flat above-fold => suspect.
        self.assertTrue(dev["capture"]["capture_suspect"])
        self.assertGreater(dev["capture"]["dom_scroll_trigger"], 0)
        # It must attribute the known defect classes (not silently pass).
        self.assertIn("CAPTURE_SUSPECT", dev["counts"])
        verdict, reasons = dx._verdict(dev)
        self.assertIn("DO NOT SHIP", verdict)
        self.assertTrue(reasons)


if __name__ == "__main__":
    unittest.main()
