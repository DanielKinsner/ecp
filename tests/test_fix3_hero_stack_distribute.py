"""Diagnosis Fix #3 — distribute + flag the hero "absent-finding" stack.

emission_autofix injects an identical (kind=section, section_index=0,
section-bottom-overlay) proposed_anchor into every absent finding that lacks
one, so N hero concerns collapse onto a single pixel (~y=90% of section 0).
The 2026-06-02 diagnosis observed 10 mobile hero findings stacked there.

The chosen fix (operator decision 2026-06-03): spread the colliding markers UP
the section band by ordinal so each is individually visible, and relabel them
``section_stacked_manual`` so review_state flags the finding
``hotspot_confidence="needs-manual-marker"`` (editor "Place manually" queue) —
while still rendering each marker at its distributed position. No pin claims
section-match confidence on a pixel it didn't earn; nothing disappears.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.v2_markers import (  # noqa: E402
    SECTION_STACKED_MANUAL,
    auto_map_markers_v2,
    compute_marker_positions_v2,
)
from report.visual_evidence import derive_visual_evidence  # noqa: E402
from assembly.review_state import _hotspot_confidence, _marker_source  # noqa: E402


def _baton():
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


def _absent_section_finding(index: int, f_ref: str):
    """Absent finding carrying the auto-injected section-0 bottom-overlay anchor."""
    return {
        "index": index,
        "f_ref": f_ref,
        "baton_index": "absent",
        "priority": "HIGH",
        "proposed_anchor": {
            "kind": "section",
            "section_index": 0,
            "placement": "section-bottom-overlay",
            "viewport": "laptop",
            "reason": "auto-injected",
        },
    }


class TestStackIsDistributed(unittest.TestCase):
    def _stack(self, n=4):
        findings = [_absent_section_finding(i + 1, f"hero/F-{i+1:02d}") for i in range(n)]
        return auto_map_markers_v2(findings, _baton())

    def test_all_relabeled_for_manual(self):
        mappings = self._stack(4)
        self.assertTrue(all(m["match_method"] == SECTION_STACKED_MANUAL for m in mappings))

    def test_positions_no_longer_collide(self):
        mappings = self._stack(4)
        ys = [round(m["fallback_position"]["y_pct"], 2) for m in mappings]
        self.assertEqual(len(set(ys)), len(ys), f"markers still stacked: {ys}")
        # Spread spans the band: bottom-anchored near the original ~90%, top at the floor.
        self.assertGreater(max(ys), 80.0)
        self.assertLessEqual(min(ys), 16.0)

    def test_markers_still_render(self):
        # Unlike Strategy-4 unplaced, distributed markers keep a position and DO render.
        findings = [_absent_section_finding(i + 1, f"hero/F-{i+1:02d}") for i in range(4)]
        baton = _baton()
        mappings = auto_map_markers_v2(findings, baton)
        rendered = {
            mk.get("f_ref")
            for markers in compute_marker_positions_v2(mappings, baton).values()
            for mk in markers
        }
        for i in range(4):
            self.assertIn(f"hero/F-{i+1:02d}", rendered)

    def test_deterministic_order(self):
        # Same input twice -> identical y assignment (stable for re-audits).
        a = [m["fallback_position"]["y_pct"] for m in self._stack(4)]
        b = [m["fallback_position"]["y_pct"] for m in self._stack(4)]
        self.assertEqual(a, b)


class TestThinHeroDoesNotRecollapse(unittest.TestCase):
    """Adversarial review 2026-06-03 §1 Fix#3 [MEDIUM]: when the resolved y_pct
    sits at/below the distribute floor (a thin hero captured short relative to
    the viewport), bottom collapsed onto top and every marker re-stacked at the
    floor. The min-span guard must keep them distinct."""

    def _thin_stack(self, n, y_pct):
        from report.v2_markers import _distribute_stacked_section_markers
        mappings = [
            {
                "f_ref": f"hero/F-{i+1:02d}",
                "burn_number": i + 1,
                "slide": 0,
                "match_method": "proposed_anchor_section",
                "fallback_position": {"x_pct": 50.0, "y_pct": float(y_pct)},
            }
            for i in range(n)
        ]
        _distribute_stacked_section_markers(mappings)
        return mappings

    def test_thin_hero_y_pct_below_floor_does_not_restack(self):
        for y_pct in (0.0, 5.0, 10.0, 14.9):
            mappings = self._thin_stack(4, y_pct)
            ys = [round(m["fallback_position"]["y_pct"], 3) for m in mappings]
            self.assertEqual(len(set(ys)), len(ys),
                f"thin hero y_pct={y_pct} re-stacked all markers: {ys}")
            self.assertTrue(all(0.0 <= y <= 100.0 for y in ys), ys)
            self.assertTrue(all(m["match_method"] == SECTION_STACKED_MANUAL for m in mappings))

    def test_thin_hero_band_spans_minimum(self):
        from report.v2_markers import _STACK_DISTRIBUTE_MIN_SPAN_PCT
        ys = [m["fallback_position"]["y_pct"] for m in self._thin_stack(4, 10.0)]
        self.assertGreaterEqual(max(ys) - min(ys), _STACK_DISTRIBUTE_MIN_SPAN_PCT - 0.001)


class TestNonStackUntouched(unittest.TestCase):
    def test_single_section_finding_not_relabeled(self):
        mappings = auto_map_markers_v2([_absent_section_finding(1, "hero/F-01")], _baton())
        self.assertEqual(mappings[0]["match_method"], "proposed_anchor_section")

    def test_normal_element_finding_unaffected(self):
        findings = [{"index": 9, "f_ref": "cta/F-01", "baton_index": "e0", "priority": "HIGH"}]
        mappings = auto_map_markers_v2(findings, _baton())
        self.assertEqual(mappings[0]["match_method"], "e_index_lookup")


class TestReviewStateMapping(unittest.TestCase):
    def test_confidence_is_needs_manual(self):
        self.assertEqual(_hotspot_confidence(SECTION_STACKED_MANUAL), "needs-manual-marker")

    def test_source_preserves_section_provenance(self):
        # Must be a valid marker `source` enum value (schema/review-state-v1.json).
        self.assertEqual(_marker_source(SECTION_STACKED_MANUAL), "proposed_anchor_section")

    def test_visual_evidence_is_section_absence_low(self):
        ve = derive_visual_evidence(match_method=SECTION_STACKED_MANUAL)
        self.assertEqual((ve["type"], ve["confidence"]), ("section_absence", "low"))


if __name__ == "__main__":
    unittest.main()
