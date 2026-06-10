"""G4 (product.md §4.2) — below the auto-place confidence threshold, the
hotspot is left BLANK for manual placement instead of auto-placing a guess.

Before 2026-05-26 the last-resort "banner" strategy pinned an unplaceable
finding at a top-of-page indicator (an auto-placed guess). The spec is
explicit: "a wrong hotspot costs more than a missing one; a blank is neutral.
Below threshold -> leave it blank. Never auto-place a guess." This regression
locks in the blank-and-queue behavior:

- auto_map_markers_v2 emits match_method="unplaced" with fallback_position=None
  (no position) for a finding with no usable placement signal.
- compute_marker_positions_v2 renders NO marker for it (truly blank).
- review_state surfaces it in the editor's "Place manually" queue
  (hotspot_confidence="needs-manual-marker") with a hidden, coord-less marker
  that the final-report renderer draws as nothing.
- The Phase-3 visual-evidence footprint stays page_level/low (same as the old
  banner), so this fix doesn't silently change the priority-path gate.

Phase-0 rulings A1+A2 (product.md §4.2 v1.2, 2026-06-10) extend the same
blank-and-queue treatment to all absence findings AND every sub-exact-tier
placement method: the renderer ONLY auto-places exact-tier matches
(e_index_lookup against a real on-slide baton element, or operator overrides).
``TestAbsentWithProposedAnchorStillBlank`` and ``TestSubExactTierBlanks``
guard that wider rule.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.v2_markers import auto_map_markers_v2, compute_marker_positions_v2  # noqa: E402
from report.visual_evidence import derive_visual_evidence  # noqa: E402
from assembly.review_state import (  # noqa: E402
    _hotspot_confidence,
    _marker_from_ai,
    _render_marker_svg,
    _unplaced_marker,
)


def _baton():
    """One real element on slide 0; a second slide so geometry is non-trivial."""
    return {
        "device": "laptop",
        "viewport": {"width": 1440, "height": 900},
        "screenshots": [
            {"path": "s1.jpg", "scrollY": 0, "naturalWidth": 1440, "naturalHeight": 900},
            {"path": "s2.jpg", "scrollY": 900, "naturalWidth": 1440, "naturalHeight": 900},
        ],
        "sections": [
            {"slug": "hero", "scroll_y_top": 0, "scroll_y_bottom": 899, "screenshot_ref": "s1.jpg"},
            {"slug": "footer", "scroll_y_top": 900, "scroll_y_bottom": 1799, "screenshot_ref": "s2.jpg"},
        ],
        "elements": [
            {"e_index": "e0", "rect": {"x": 40, "y": 100, "width": 300, "height": 60}},
        ],
    }


def _unplaceable_finding(index=1):
    """Absent finding with no proposed_anchor and no surface -> falls to Strategy 4."""
    return {
        "index": index,
        "f_ref": "trust-credibility/F-09",
        "baton_index": "absent",
        "priority": "HIGH",
        # deliberately no proposed_anchor, no surface/section
    }


class TestUnplacedMapping(unittest.TestCase):
    def test_strategy4_emits_no_position(self):
        mappings = auto_map_markers_v2([_unplaceable_finding()], _baton())
        self.assertEqual(len(mappings), 1)
        m = mappings[0]
        self.assertEqual(m["match_method"], "unplaced")
        self.assertIsNone(m["fallback_position"], "unplaced must carry NO position (blank)")
        self.assertIsNone(m["baton_element_index"])
        self.assertEqual(m["fallback_role"], "absent_unplaced")

    def test_no_marker_is_rendered_for_unplaced(self):
        findings = [_unplaceable_finding()]
        mappings = auto_map_markers_v2(findings, _baton())
        slide_markers = compute_marker_positions_v2(mappings, _baton())
        # The unplaced f_ref must not appear as a rendered marker on any slide.
        all_refs = {
            mk.get("f_ref")
            for markers in slide_markers.values()
            for mk in markers
        }
        self.assertNotIn("trust-credibility/F-09", all_refs)

    def test_visual_evidence_footprint_matches_old_banner(self):
        # page_level/low preserves the prior banner Phase-3 gate behavior.
        ve = derive_visual_evidence(match_method="unplaced")
        self.assertEqual(ve["type"], "page_level")
        self.assertEqual(ve["confidence"], "low")


class TestUnplacedReviewState(unittest.TestCase):
    def test_confidence_queues_for_manual_placement(self):
        self.assertEqual(_hotspot_confidence("unplaced"), "needs-manual-marker")

    def test_unplaced_marker_is_blank_and_hidden(self):
        marker = _unplaced_marker(
            "marker-x", "trust-credibility/F-09", "laptop-section-1", "high", None
        )
        self.assertTrue(marker["hidden"])
        self.assertEqual(marker["shape"], "point")
        self.assertEqual(marker["source"], "manual")
        for coord in ("cx_pct", "cy_pct", "x_pct", "y_pct", "w_pct", "h_pct"):
            self.assertNotIn(coord, marker, f"blank marker must not carry {coord}")

    def test_hidden_marker_renders_nothing(self):
        marker = _unplaced_marker(
            "marker-x", "trust-credibility/F-09", "laptop-section-1", "high", None
        )
        self.assertEqual(_render_marker_svg(marker, {"f_ref": "trust-credibility/F-09"}), "")

    def test_placed_finding_still_renders(self):
        # Guard against over-broadening: a normal e_index finding is unaffected.
        baton = _baton()
        findings = [{
            "index": 2,
            "f_ref": "visual-cta/F-01",
            "baton_index": "e0",
            "priority": "HIGH",
        }]
        mappings = auto_map_markers_v2(findings, baton)
        self.assertEqual(mappings[0]["match_method"], "e_index_lookup")
        slide_markers = compute_marker_positions_v2(mappings, baton)
        all_refs = {
            mk.get("f_ref")
            for markers in slide_markers.values()
            for mk in markers
        }
        self.assertIn("visual-cta/F-01", all_refs)


class TestAbsentWithProposedAnchorStillBlank(unittest.TestCase):
    """Phase-0 ruling A1 (product.md:144) — absences are ALWAYS blank, even
    when the specialist authored a precise ``proposed_anchor`` hint. The
    hint flows through to the editor as a manual-placement suggestion
    (review_state surfaces it on ``finding.raw.proposed_anchor``), but the
    renderer NEVER auto-pins from it."""

    def _absent_finding_with_hint(self, kind: str, **anchor_extras):
        """An absent finding carrying a typed proposed_anchor that pre-v1.2
        would have auto-placed."""
        anchor = {"kind": kind, "viewport": "laptop", "reason": "operator hint"}
        anchor.update(anchor_extras)
        return {
            "index": 1,
            "f_ref": "trust/F-09",
            "baton_index": "absent",
            "priority": "HIGH",
            "proposed_anchor": anchor,
        }

    def test_absent_with_element_kind_anchor_unplaced(self):
        # kind=element + a real on-slide e_index would have placed pre-v1.2;
        # now it MUST unplace because the finding is an absence.
        f = self._absent_finding_with_hint(
            "element",
            element_baton_index="e0",
            placement="before-element",
        )
        mappings = auto_map_markers_v2([f], _baton())
        self.assertEqual(mappings[0]["match_method"], "unplaced")
        self.assertIsNone(mappings[0]["fallback_position"])
        # No marker is drawn anywhere.
        slide_markers = compute_marker_positions_v2(mappings, _baton())
        rendered = {
            mk.get("f_ref")
            for markers in slide_markers.values()
            for mk in markers
        }
        self.assertNotIn("trust/F-09", rendered)

    def test_absent_with_section_kind_anchor_unplaced(self):
        # The exact case product.md:144 names ("no sticky CTA"-style absence).
        f = self._absent_finding_with_hint(
            "section",
            section_index=0,
            placement="section-bottom-overlay",
        )
        mappings = auto_map_markers_v2([f], _baton())
        self.assertEqual(mappings[0]["match_method"], "unplaced")
        self.assertIsNone(mappings[0]["fallback_position"])

    def test_absent_with_viewport_kind_anchor_unplaced(self):
        f = self._absent_finding_with_hint(
            "viewport",
            viewport_trigger="after_primary_cta_offscreen",
            placement="viewport-bottom-sticky",
        )
        mappings = auto_map_markers_v2([f], _baton())
        self.assertEqual(mappings[0]["match_method"], "unplaced")
        self.assertIsNone(mappings[0]["fallback_position"])


class TestExactTierGate(unittest.TestCase):
    """Phase-0 ruling A2 (product.md:147-151) — only exact-tier methods
    auto-place; every sub-exact strategy falls through to unplaced. With
    Strategies 2/3 pruned, the practical surface is: a non-absent finding
    whose ONLY signal is the now-removed section_centroid / proposed_anchor
    path no longer renders anywhere."""

    def test_finding_with_only_surface_signal_unplaces(self):
        """A finding that pre-prune would have hit Strategy 3
        (section_centroid via surface-string match) — non-absent, no real
        e_index, surface matches a section slug — must now unplace. Before
        the prune this would have rendered at the section centroid; now the
        only auto-placement path is Strategy 1 (real on-slide e_index)."""
        finding = {
            "index": 1,
            "f_ref": "trust/F-99",
            # No baton_index (or an invalid one) so Strategy 1 doesn't fire.
            "baton_index": "e999",  # out-of-range
            "priority": "HIGH",
            "surface": "hero",  # would have matched section slug pre-prune
        }
        mappings = auto_map_markers_v2([finding], _baton())
        self.assertEqual(mappings[0]["match_method"], "unplaced")
        self.assertIsNone(mappings[0]["fallback_position"])

    def test_strong_placement_methods_set_matches_visual_evidence(self):
        """The v2_html_builder ``_STRONG_PLACEMENT_METHODS`` set must equal
        the set of match_methods that visual_evidence classifies as
        (exact_element, high) — that is the operational definition of
        "exact-tier" the spec calls for."""
        from report.v2_html_builder import _STRONG_PLACEMENT_METHODS
        from report.visual_evidence import _MATCH_METHOD_TO_TYPE
        exact_high = {
            mm for mm, (t, c) in _MATCH_METHOD_TO_TYPE.items()
            if (t, c) == ("exact_element", "high")
        }
        self.assertEqual(
            _STRONG_PLACEMENT_METHODS,
            frozenset(exact_high),
            "v2_html_builder._STRONG_PLACEMENT_METHODS must contain exactly "
            "the match_methods that visual_evidence classifies as exact-tier. "
            "Drift here means the placement-QA summary and the visual-evidence "
            "taxonomy disagree about what counts as a confident placement.",
        )


class TestOperatorOverrideStillPlaces(unittest.TestCase):
    """The operator-override path (--markers file in v2_html_builder) MUST
    keep working — operator placement is exact-tier by definition (a human
    looked at the screenshot and clicked). merge_markers tags the entry
    ``match_method="operator_override"`` which renders just like
    e_index_lookup."""

    def test_operator_override_is_strong_placement(self):
        from report.v2_html_builder import _STRONG_PLACEMENT_METHODS
        self.assertIn("operator_override", _STRONG_PLACEMENT_METHODS)

    def test_operator_override_confidence_is_exact(self):
        # review_state surfaces operator-placed markers as exact-selector,
        # NOT needs-manual-marker — the operator already placed it.
        self.assertEqual(_hotspot_confidence("operator_override"), "exact-selector")

    def test_operator_override_renders(self):
        # End-to-end: merge_markers + compute_marker_positions_v2 produce a
        # rendered marker for an operator override entry.
        from report.v2_markers import merge_markers
        baton = _baton()
        auto = auto_map_markers_v2([_unplaceable_finding()], baton)
        # Operator override carries x_pct/y_pct directly.
        op_override = [{
            "f_ref": "trust-credibility/F-09",
            "finding_index": 1,
            "slide": 0,
            "fallback_position": {"x_pct": 35.0, "y_pct": 42.0},
            "severity": "high",
        }]
        merged = merge_markers(auto, op_override)
        # The merge tags the resulting entry as operator_override.
        self.assertEqual(merged[0]["match_method"], "operator_override")
        # And the renderer draws it.
        slide_markers = compute_marker_positions_v2(merged, baton)
        rendered = {
            mk.get("f_ref")
            for markers in slide_markers.values()
            for mk in markers
        }
        self.assertIn("trust-credibility/F-09", rendered)


if __name__ == "__main__":
    unittest.main()
