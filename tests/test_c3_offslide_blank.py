"""C3 (product.md §4.2) — off-slide elements render NO marker.

Pre-fix (2026-05-02 mitigation): when an e_index lookup found a real element
whose geometry sat OUTSIDE every captured screenshot's viewport band, the
resolver still emitted a mapping (``match_method="e_index_lookup_offslide"``)
pointing at the nearest slide with the full element geometry. The renderer
then clamped that rect onto the wrong slide — a hard product.md §4.2
violation (wrong-page placement is worse than blank).

Post-fix (2026-06-10): the off-slide case falls through to Strategy 4 just
like the no-signal case, emitting ``match_method="unplaced"`` with no
fallback_position, and review_state queues the finding for manual placement
with a blank, hidden marker. Same representation as the G4 blank-below-
confidence path (see tests/test_g4_blank_below_confidence.py).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.v2_markers import auto_map_markers_v2, compute_marker_positions_v2  # noqa: E402
from assembly.review_state import _hotspot_confidence  # noqa: E402


def _baton_with_gap():
    """Two captured slides with a GAP between them: slide 0 covers y=[0,900),
    slide 1 covers y=[2000,2900). An element at y=1200 lies in the un-captured
    gap and matches no slide's viewport band.
    """
    return {
        "device": "laptop",
        "viewport": {"width": 1440, "height": 900},
        "screenshots": [
            {"path": "s1.jpg", "scrollY": 0, "naturalWidth": 1440, "naturalHeight": 900},
            {"path": "s2.jpg", "scrollY": 2000, "naturalWidth": 1440, "naturalHeight": 900},
        ],
        "sections": [
            {"slug": "hero", "scroll_y_top": 0, "scroll_y_bottom": 899, "screenshot_ref": "s1.jpg"},
            {"slug": "footer", "scroll_y_top": 2000, "scroll_y_bottom": 2899, "screenshot_ref": "s2.jpg"},
        ],
        "elements": [
            # e0 is between the two captured viewport bands (off-slide).
            {"e_index": "e0", "rect": {"x": 40, "y": 1200, "width": 300, "height": 60}},
            # e1 is squarely inside slide 0 — control.
            {"e_index": "e1", "rect": {"x": 40, "y": 100, "width": 300, "height": 60}},
        ],
    }


def _finding(index, f_ref, baton_index):
    return {
        "index": index,
        "f_ref": f_ref,
        "baton_index": baton_index,
        "priority": "HIGH",
    }


class TestOffSlideBlank(unittest.TestCase):
    def test_offslide_element_yields_unplaced_mapping(self):
        # Off-slide e_index must NOT emit a positioned mapping — it falls
        # through to Strategy 4 ("unplaced") with no fallback_position.
        mappings = auto_map_markers_v2([_finding(1, "trust/F-01", "e0")], _baton_with_gap())
        self.assertEqual(len(mappings), 1)
        m = mappings[0]
        self.assertEqual(m["match_method"], "unplaced")
        self.assertIsNone(m["fallback_position"])
        self.assertIsNone(m["baton_element_index"])
        self.assertEqual(m["fallback_role"], "absent_unplaced")

    def test_offslide_match_method_never_emitted(self):
        # The legacy "e_index_lookup_offslide" string must not appear.
        mappings = auto_map_markers_v2([_finding(1, "trust/F-01", "e0")], _baton_with_gap())
        methods = {m.get("match_method") for m in mappings}
        self.assertNotIn("e_index_lookup_offslide", methods)

    def test_no_marker_is_rendered_on_any_slide(self):
        # Renderer must draw nothing for the off-slide finding — not on the
        # nearest slide, not anywhere.
        findings = [_finding(1, "trust/F-01", "e0")]
        mappings = auto_map_markers_v2(findings, _baton_with_gap())
        slide_markers = compute_marker_positions_v2(mappings, _baton_with_gap())
        all_refs = {
            mk.get("f_ref")
            for markers in slide_markers.values()
            for mk in markers
        }
        self.assertNotIn("trust/F-01", all_refs)

    def test_on_slide_element_still_renders(self):
        # Guard against over-broadening: a normal on-slide element is unaffected.
        baton = _baton_with_gap()
        findings = [_finding(2, "cta/F-02", "e1")]
        mappings = auto_map_markers_v2(findings, baton)
        self.assertEqual(mappings[0]["match_method"], "e_index_lookup")
        slide_markers = compute_marker_positions_v2(mappings, baton)
        all_refs = {
            mk.get("f_ref")
            for markers in slide_markers.values()
            for mk in markers
        }
        self.assertIn("cta/F-02", all_refs)

    def test_confidence_queues_for_manual_placement(self):
        # The unplaced match_method maps to the manual-marker queue
        # confidence label (matches G4 blank-below-confidence behavior).
        mappings = auto_map_markers_v2([_finding(1, "trust/F-01", "e0")], _baton_with_gap())
        self.assertEqual(
            _hotspot_confidence(mappings[0]["match_method"]),
            "needs-manual-marker",
        )

    def test_capture_limited_section_never_auto_places_hotspot(self):
        for flag, value in (
            ("occluded", True),
            ("scroll_failed", True),
            ("overlay_dismissed", False),
        ):
            with self.subTest(flag=flag):
                baton = _baton_with_gap()
                baton["sections"][0][flag] = value
                mappings = auto_map_markers_v2(
                    [_finding(2, "cta/F-02", "e1")], baton
                )
                self.assertEqual(mappings[0]["match_method"], "unplaced")
                self.assertEqual(mappings[0]["fallback_role"], "capture_limited")
                rendered = compute_marker_positions_v2(mappings, baton)
                self.assertFalse(any(rendered.values()))

    def test_explicit_false_occlusion_does_not_block_hotspot(self):
        baton = _baton_with_gap()
        baton["sections"][0].update({
            "occluded": False,
            "scroll_failed": False,
            "overlay_dismissed": True,
        })
        mapping = auto_map_markers_v2(
            [_finding(2, "cta/F-02", "e1")], baton
        )[0]
        self.assertEqual(mapping["match_method"], "e_index_lookup")


if __name__ == "__main__":
    unittest.main()
