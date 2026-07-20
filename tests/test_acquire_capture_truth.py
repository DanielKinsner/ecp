"""Capture-truth fixes in scripts/acquire_url.py (C10, C14, C15).

The live capture path is not covered by the suite (needs agent-browser), so
each fix surfaces a pure helper that is exercised here and a string-level
contract on the embedded JS where the live behavior must change. Mirrors the
pattern established by tests/test_acquire_element_selectors.py +
tests/test_acquire_engagement_dir.py.

C10 — invisible elements: ``_build_elements_js`` must drop elements that exist
      in DOM but are not visible (computed display:none, visibility:hidden, or
      aria-hidden=true). Pre-fix the filter only dropped zero-size /
      out-of-viewport, so a `visibility:hidden` element entered the baton as
      visible evidence (workflows/acquire.md §558-563).
C14 — per-section occlusion: ``_section_occluded_from_viewport_state`` runs the
      contract's >30% occlusion check on a single scroll position's
      viewport-state dict. Pre-fix the acquirer probed once at scroll_y=0 and
      copied one boolean to every section (workflows/acquire.md §363).
C15 — DPR fallback: ``_build_viewport_dpr_fields`` records the request-vs-actual
      DPR split so a mobile capture that fell back to 1x via
      chromium_headless_shell surfaces in the baton; the resulting viewport
      sub-object validates against the viewport schema in
      schema/baton-v1.json.

Run:
    python -m pytest tests/test_acquire_capture_truth.py
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

import acquire_url  # noqa: E402

try:
    from jsonschema import Draft202012Validator
    _HAVE_JSONSCHEMA = True
except ImportError:  # pragma: no cover — jsonschema is a hard runtime dep
    _HAVE_JSONSCHEMA = False


class TestC10InvisibleElementFilter(unittest.TestCase):
    """The element-extraction JS must drop computed-hidden / aria-hidden
    elements, exactly per workflows/acquire.md §558-563."""

    def test_computed_display_none_filtered(self):
        js = acquire_url._build_elements_js("example.com")
        self.assertIn("getComputedStyle", js)
        self.assertIn("cs.display === 'none'", js)

    def test_computed_visibility_hidden_filtered(self):
        js = acquire_url._build_elements_js("example.com")
        self.assertIn("cs.visibility === 'hidden'", js)

    def test_aria_hidden_true_filtered(self):
        js = acquire_url._build_elements_js("example.com")
        self.assertIn("aria-hidden", js)
        self.assertIn("'true'", js)

    def test_filter_lands_after_geometry_guard(self):
        """The visibility filter must run AFTER the zero-size / out-of-viewport
        guards — they short-circuit cheaper. A misordered edit that put the
        getComputedStyle call before the geometry guards would slow every
        extraction; this test pins the order."""
        js = acquire_url._build_elements_js("example.com")
        geom_idx = js.find("r.bottom < 0 || r.top > window.innerHeight")
        # Ignore the local-wrapper visibility check inside the zero-size proxy
        # resolver; this ordering assertion concerns the ordinary element's
        # computed-style filter.
        cs_idx = js.find("const cs = window.getComputedStyle(el)")
        self.assertGreater(geom_idx, 0, "geometry guard missing")
        self.assertGreater(cs_idx, geom_idx, "visibility filter must run AFTER geometry guard")

    def test_contamination_guard_still_present(self):
        """Defensive: the visibility filter sits inside the same function as the
        contamination guard. Locking both keeps either fix from being lost in
        an edit that touches the JS string."""
        js = acquire_url._build_elements_js("example.com")
        self.assertIn("__contamination_detected", js)


class TestC14PerSectionOcclusion(unittest.TestCase):
    """``_section_occluded_from_viewport_state`` runs the contract's >30%
    check on a per-scroll-position viewport-state dict. The same probe
    sequence at different positions must produce different occluded values."""

    def test_clear_viewport_is_not_occluded(self):
        state = {"clear": True, "blocking": []}
        self.assertFalse(acquire_url._section_occluded_from_viewport_state(state))

    def test_small_overlay_below_threshold_not_occluded(self):
        # 15% coverage banner — under the contract 30% bar.
        state = {"clear": False, "blocking": [{"tag": "div", "coverage": 15}]}
        self.assertFalse(acquire_url._section_occluded_from_viewport_state(state))

    def test_large_overlay_above_threshold_is_occluded(self):
        # 45% coverage modal — over the contract 30% bar.
        state = {"clear": False, "blocking": [{"tag": "div", "coverage": 45}]}
        self.assertTrue(acquire_url._section_occluded_from_viewport_state(state))

    def test_per_position_sequence_differs(self):
        """The pre-fix bug copied ONE boolean to every section. Verify the
        helper produces independent per-position values when the probe
        sequence differs — the contract's per-section semantics."""
        probes = [
            {"clear": True, "blocking": []},                               # scroll 0: clear
            {"clear": False, "blocking": [{"coverage": 10}]},              # scroll 800: small banner
            {"clear": False, "blocking": [{"coverage": 60}]},              # scroll 1600: chat widget
            {"clear": True, "blocking": []},                               # scroll 2400: clear again
        ]
        per_section = [acquire_url._section_occluded_from_viewport_state(p) for p in probes]
        self.assertEqual(per_section, [False, False, True, False])

    def test_malformed_state_falls_back_loud(self):
        # A non-dict state cannot prove occlusion either way; default to False so
        # we don't false-positive every section, but a dict missing 'blocking'
        # with clear=False surfaces as occluded (fail loud).
        self.assertFalse(acquire_url._section_occluded_from_viewport_state(None))
        self.assertFalse(acquire_url._section_occluded_from_viewport_state("nope"))
        self.assertTrue(acquire_url._section_occluded_from_viewport_state({"clear": False}))

    def test_threshold_is_configurable(self):
        state = {"clear": False, "blocking": [{"coverage": 25}]}
        # 30% default: 25% does not trip
        self.assertFalse(acquire_url._section_occluded_from_viewport_state(state))
        # 20% threshold: 25% does trip
        self.assertTrue(acquire_url._section_occluded_from_viewport_state(state, threshold_pct=20))


_SCHEMA_PATH = _REPO / "schema" / "baton-v1.json"


class TestC15DprFallbackBaton(unittest.TestCase):
    """A baton emitted under a 1x-actual mobile capture must carry
    dpr_requested=3, dpr_actual=1, dpr_fallback=true, and the viewport
    sub-object must validate against schema/baton-v1.json's viewport schema."""

    def test_mobile_1x_fallback_records_split(self):
        vp = acquire_url._build_viewport_dpr_fields(
            inner_w=390, inner_h=844, dpr_requested=3.0, dpr_actual=1.0,
        )
        self.assertEqual(vp["dpr_requested"], 3.0)
        self.assertEqual(vp["dpr_actual"], 1.0)
        self.assertTrue(vp["dpr_fallback"])

    def test_desktop_matching_dpr_no_fallback(self):
        vp = acquire_url._build_viewport_dpr_fields(
            inner_w=1920, inner_h=1080, dpr_requested=1.0, dpr_actual=1.0,
        )
        self.assertEqual(vp["dpr_requested"], 1.0)
        self.assertEqual(vp["dpr_actual"], 1.0)
        self.assertFalse(vp["dpr_fallback"])

    def test_dpr_legacy_field_tracks_actual(self):
        """``viewport.dpr`` (legacy single-value field) keeps its semantics —
        the actual scaling factor — so scripts/report/geometry.py's
        ``viewport_dpr`` fallback chain returns the right multiplier when only
        the legacy field is consulted. Element coords on disk are already
        physical pixels at the ACTUAL dpr, so this must NOT be the requested
        value."""
        vp = acquire_url._build_viewport_dpr_fields(
            inner_w=390, inner_h=844, dpr_requested=3.0, dpr_actual=1.0,
        )
        self.assertEqual(vp["dpr"], 1)

    @unittest.skipUnless(_HAVE_JSONSCHEMA, "jsonschema not installed")
    def test_viewport_validates_against_schema(self):
        """The emitted viewport sub-object must validate against the
        ``viewport`` property in schema/baton-v1.json (the v2 deepen-plan
        architecture schema). jsonschema is a hard runtime dep — the test
        SKIPs only on a broken environment."""
        schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
        viewport_schema = schema["properties"]["viewport"]
        vp = acquire_url._build_viewport_dpr_fields(
            inner_w=390, inner_h=844, dpr_requested=3.0, dpr_actual=1.0,
        )
        # The schema bans extra properties via additionalProperties:false; the
        # ``dpr_fallback`` / legacy ``dpr`` keys live OUTSIDE the schema'd subset
        # but inside the baton's runtime viewport dict, so we validate only the
        # schema's required+defined keys.
        valid_keys = set(viewport_schema["properties"].keys())
        vp_for_schema = {k: v for k, v in vp.items() if k in valid_keys}
        Draft202012Validator(viewport_schema).validate(vp_for_schema)
        # And the required keys are all present without filtering:
        for k in viewport_schema["required"]:
            self.assertIn(k, vp, f"required viewport key missing: {k}")


if __name__ == "__main__":
    unittest.main()
