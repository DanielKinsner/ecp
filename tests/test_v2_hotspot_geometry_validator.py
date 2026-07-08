from __future__ import annotations

import sys
import unittest
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.geometry_validator import (  # noqa: E402
    backfill_screenshots_from_sections,
    element_rect_raw,
    validate_v2_hotspot_geometry,
    viewport_dpr,
)
import report.geometry_validator as geometry_validator  # noqa: E402
from report.geometry import infer_element_coord_scale  # noqa: E402
from report.v2_markers import auto_map_markers_v2, compute_marker_positions_v2  # noqa: E402


class TestHotspotGeometryValidator(unittest.TestCase):
    def test_viewport_dpr_prefers_actual(self):
        self.assertEqual(
            viewport_dpr({"dpr_actual": 3, "dpr": 2, "dpr_requested": 1}),
            3,
        )

    def test_element_rect_raw_accepts_v2_rect(self):
        self.assertEqual(
            element_rect_raw({"rect": {"x": 3, "y": 6, "width": 9, "height": 12}}),
            {"x": 3.0, "y": 6.0, "width": 9.0, "height": 12.0},
        )

    def test_backfills_screenshots_from_sections(self):
        baton = {
            "viewport": {"width": 390, "height": 844},
            "sections": [{"screenshot_ref": "section-1.jpg", "scroll_y_top": 400}],
        }
        backfill_screenshots_from_sections(baton)
        self.assertEqual(baton["screenshots"][0]["path"], "section-1.jpg")
        self.assertEqual(baton["screenshots"][0]["scrollY"], 400)

    def test_detects_dpr_scale_mismatch(self):
        baton = {
            "device": "mobile",
            "viewport": {"width": 390, "height": 844, "dpr_actual": 3},
            "screenshots": [
                {"path": "s1.jpg", "scrollY": 0, "naturalWidth": 390, "naturalHeight": 844},
                {"path": "s2.jpg", "scrollY": 900, "naturalWidth": 390, "naturalHeight": 844},
            ],
            "sections": [
                {"scroll_y_top": 0, "scroll_y_bottom": 899},
                {"scroll_y_top": 900, "scroll_y_bottom": 1799},
            ],
            "elements": [
                {"rect": {"x": 45, "y": 3072, "width": 300, "height": 120}},
            ],
        }
        mappings = [{
            "f_ref": "visual-cta F-31",
            "finding_index": 1,
            "baton_element_index": 0,
            "slide": 1,
            "match_method": "e_index_lookup",
        }]
        slide_markers = {
            1: [{
                "f_ref": "visual-cta F-31",
                "match_method": "e_index_lookup",
                "x_pct": 100.0,
            }]
        }
        original_infer = geometry_validator._infer_element_coord_scale
        geometry_validator._infer_element_coord_scale = lambda *_args, **_kwargs: 1.0
        try:
            result = validate_v2_hotspot_geometry(baton, [{"f_ref": "visual-cta F-31"}], mappings, slide_markers)
        finally:
            geometry_validator._infer_element_coord_scale = original_infer
        self.assertFalse(result["passed"])
        codes = {failure["code"] for failure in result["failures"]}
        self.assertIn("dpr_scale_mismatch", codes)
        self.assertIn("right_edge_clamp_rate", codes)

    def test_mobile_regression_fixture_expected_slides(self):
        fixture = _REPO / "tests" / "fixtures" / "hotspot_geometry_mobile"
        baton = json.loads((fixture / "baton-mobile.json").read_text(encoding="utf-8"))
        expected = json.loads((fixture / "expected-hotspot-slides.json").read_text(encoding="utf-8"))
        backfill_screenshots_from_sections(baton)
        findings = [
            {
                "index": i,
                "f_ref": row["f_ref"],
                "baton_index": row["baton_index"],
                "priority": "MEDIUM",
            }
            for i, row in enumerate(expected, start=1)
        ]

        scale = infer_element_coord_scale(
            baton["elements"],
            baton["screenshots"],
            baton["viewport"],
            viewport_dpr(baton["viewport"]),
            baton["sections"],
        )
        self.assertEqual(scale, 3)

        mappings = auto_map_markers_v2(findings, baton)
        by_ref = {mapping["f_ref"]: mapping for mapping in mappings}
        for row in expected:
            self.assertEqual(
                by_ref[row["f_ref"]]["slide"] + 1,
                row["expected_slide"],
                row["f_ref"],
            )

        slide_markers = compute_marker_positions_v2(mappings, baton)
        result = validate_v2_hotspot_geometry(baton, findings, mappings, slide_markers)
        self.assertTrue(result["passed"], result)

    def test_horizontal_dpr_baton_does_not_false_fail_slide_match(self):
        """Adversarial review 2026-07-08 #6: on a baton whose physical-pixel
        coords are detected via HORIZONTAL extent (vertical fits the CSS
        envelope), the full renderer scale is DPR but the old Y-only
        _likely_expected_scale returned 1.0 — so the validator computed every
        e_index marker's expected slide at the wrong scale and false-FAILed the
        slide-match gate. The validator must now use the renderer's scale."""
        from report.geometry_validator import _likely_expected_scale

        baton = {
            "device": "mobile",
            "viewport": {"width": 390, "height": 844, "dpr_actual": 3},
            "screenshots": [
                {"path": "s1.jpg", "scrollY": 0, "naturalWidth": 1170, "naturalHeight": 2532},
                {"path": "s2.jpg", "scrollY": 844, "naturalWidth": 1170, "naturalHeight": 2532},
            ],
            "sections": [
                {"screenshot_ref": "s1.jpg", "scroll_y_top": 0, "scroll_y_bottom": 844},
                {"screenshot_ref": "s2.jpg", "scroll_y_top": 844, "scroll_y_bottom": 1688},
            ],
            # Physical-pixel element: horizontal extent overflows viewport*1.75
            # while vertical (940 raw) fits the 1688 CSS envelope.
            "elements": [{"e_index": "e0", "rect": {"x": 800, "y": 900, "width": 100, "height": 40}}],
        }
        rects = [element_rect_raw(baton["elements"][0])]
        csvh = geometry_validator._css_envelope_height(
            baton["screenshots"], baton["sections"], baton["viewport"])
        dpr = viewport_dpr(baton["viewport"])
        full_scale = infer_element_coord_scale(
            baton["elements"], baton["screenshots"], baton["viewport"], dpr, baton["sections"])
        # Precondition: this baton is genuinely the horizontal-DPR divergence case.
        self.assertEqual(full_scale, 3, "renderer scale should be DPR (horizontal detection)")
        self.assertEqual(_likely_expected_scale(rects, csvh, dpr), 1.0,
                         "the old Y-only heuristic disagrees — this is the regression case")

        findings = [{"index": 1, "f_ref": "pricing F-01", "baton_index": "e0", "priority": "MEDIUM"}]
        mappings = auto_map_markers_v2(findings, baton)
        slide_markers = compute_marker_positions_v2(mappings, baton)
        result = validate_v2_hotspot_geometry(baton, findings, mappings, slide_markers)

        self.assertEqual(result["summary"]["e_index_slide_match_rate"], 1.0)
        codes = {f["code"] for f in result["failures"]}
        self.assertNotIn("e_index_slide_mismatch_rate", codes,
                         "validator expected slide must use the renderer's scale, not Y-only")


if __name__ == "__main__":
    unittest.main()
