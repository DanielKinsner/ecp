"""Phase-4 acquisition-truth fixes: C11, C12, C13, C16, hc-C3.

The live capture path is not covered by the test suite (needs agent-browser),
so each fix surfaces pure helpers / JS-string contracts that exercise here.
Mirrors the pattern established by tests/test_acquire_capture_truth.py.

C11 — force-removal records: scripts/ecp_acquire_overlays.force_remove_blocking_overlays
      now returns per-overlay records (selector identity, type, dismissal
      method). scripts/baton_v1_to_v2.py threads them into the v2 baton's
      capture_state.overlays_detected[] with synthesized e_index entries
      so the renderer's "DOM edited during capture" caveat can fire.

C12 — semantic overlay dismissal: scripts/ecp_acquire_overlays._DISMISS_ROUND
      must apply close-semantics (aria-label close/dismiss, ×/✕ glyphs,
      .close classes, "no thanks" text) on EVERY round, and must NEVER
      click a button whose text matches subscribe/sign-up/submit/accept.
      Pre-fix the first phase clicked the first `[role="dialog"] button`
      it found — in a newsletter popup that's "Subscribe".

C13 — URL-pinned variant selection: scripts/ecp_configurator parses
      ?variant=/?sku=/?variant_id= from the audit URL and selects that
      variant on every device (variant_source="url-pinned"). With no URL
      variant, first-available runs and the resolved id is recorded
      (variant_source="first-available") so cross-device drift is
      detectable downstream.

C16 — capture-then-cap: scripts/acquire_url._build_elements_js raises the
      per-selector cap to a sanity bound (100) and the global cap to 200
      (workflows/acquire.md §638), so a 36-product-card grid survives.

hc-C3 — true-height probe: scripts/acquire_url adds _probe_doc_height; the
      v1 baton carries true_max_scroll_px; scripts/baton_v1_to_v2 prefers
      the probed value with a sec_bottom safety floor so the converter
      can never shrink page_height below already-captured content.

Run:
    python -m pytest tests/test_acquire_capture_truth_phase4.py
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

import acquire_url  # noqa: E402
import baton_v1_to_v2 as conv  # noqa: E402
import ecp_acquire_overlays as ovl  # noqa: E402
import ecp_configurator as cfg  # noqa: E402

_EID = "2026-06-10-3e7bd452"
_CAPTURED = "2026-06-10T15:19:55.000Z"

_MINIMAL_DOM = "<!doctype html><html><head><title>x</title></head><body></body></html>"


def _v1_baton(**over: object) -> dict:
    base: dict = {
        "engagement_id": _EID,
        "device": "desktop",
        "dpr": 1,
        "viewport": {"width": 1920, "height": 1080, "dpr": 1},
        "screenshots": [{"index": 1, "label": "Above", "scrollY": 0, "path": "section-1.jpg"}],
        "sections": [{"label": "Above", "scrollY": 0, "height": 900, "clusters": ["visual-cta"], "screenshot_index": 1}],
        "elements": [{"selector": "h1", "tag": "h1", "text": "Hi", "class": "",
                      "x": 0, "y": 0, "width": 100, "height": 30, "visible": True}],
        "url": "https://example.com/p",
        "url_final": "https://example.com/p",
        "title": "x",
        "structured_data": [],
        "pre_hydration_warning": False,
    }
    base.update(over)
    return base


# ---------------------------------------------------------------------------
# C11 — force-removal record threading
# ---------------------------------------------------------------------------


class TestC11ForceRemovalJsReturnsRecords(unittest.TestCase):
    """The JS payload itself must build per-overlay records (selector identity,
    type, dismissal method). String-contract level — the live behavior is
    verified by the live audit + visual QA gate."""

    def test_js_returns_records_list_not_count_only(self):
        js = ovl._FORCE_REMOVE
        # the new payload returns {removed, records}
        self.assertIn("records", js)
        self.assertIn("records: records", js)

    def test_js_records_dismissal_method_per_overlay(self):
        js = ovl._FORCE_REMOVE
        self.assertIn("'js-remove'", js)
        self.assertIn("'js-style-display-none'", js)

    def test_js_classifies_overlay_type_from_classes(self):
        js = ovl._FORCE_REMOVE
        # The typing function names the schema enum members.
        self.assertIn("'cookie-consent'", js)
        self.assertIn("'newsletter-modal'", js)
        # Bulk-class signals drive routing.
        self.assertIn("omnisend", js)
        self.assertIn("klaviyo", js)


class TestC11ConverterFiresCaveat(unittest.TestCase):
    """v1.overlays records -> v2.capture_state.overlays_detected with valid
    e_index. Empty case stays empty. Schema-valid in both branches."""

    def test_empty_overlay_record_yields_empty_overlays_detected(self):
        v1 = _v1_baton()  # no `overlays` key
        v2 = conv.convert_baton(v1, _MINIMAL_DOM, device="desktop",
                                engagement_id=_EID, captured_at=_CAPTURED)
        self.assertEqual(v2["capture_state"]["overlays_detected"], [])

    def test_force_removed_overlay_lands_in_overlays_detected(self):
        v1 = _v1_baton(overlays=[
            {"tag": "div", "id": "newsletter-popup",
             "class": "omnisend-popup overlay",
             "coverage_pct": 75, "type": "newsletter-modal",
             "method": "js-style-display-none"},
        ])
        v2 = conv.convert_baton(v1, _MINIMAL_DOM, device="desktop",
                                engagement_id=_EID, captured_at=_CAPTURED)
        ods = v2["capture_state"]["overlays_detected"]
        self.assertEqual(len(ods), 1)
        self.assertEqual(ods[0]["type"], "newsletter-modal")
        self.assertTrue(ods[0]["dismissed"])
        self.assertRegex(ods[0]["e_index"], r"^e[0-9]+$")
        # The synthesized element entry MUST exist in elements[] so the
        # schema's overlay e_index reference is resolvable.
        eidxs = {e["e_index"] for e in v2["elements"]}
        self.assertIn(ods[0]["e_index"], eidxs)

    def test_multiple_overlays_each_get_unique_e_index(self):
        v1 = _v1_baton(overlays=[
            {"tag": "div", "id": "cookie", "class": "consent",
             "type": "cookie-consent", "method": "js-remove"},
            {"tag": "div", "id": "newsletter", "class": "omnisend",
             "type": "newsletter-modal", "method": "js-style-display-none"},
        ])
        v2 = conv.convert_baton(v1, _MINIMAL_DOM, device="desktop",
                                engagement_id=_EID, captured_at=_CAPTURED)
        ods = v2["capture_state"]["overlays_detected"]
        self.assertEqual(len(ods), 2)
        self.assertNotEqual(ods[0]["e_index"], ods[1]["e_index"])

    def test_reveal_summary_records_synthetic_overlay(self):
        v1 = _v1_baton(reveal_summary={"reveal_els": 7, "lazy_imgs": 3})
        v2 = conv.convert_baton(v1, _MINIMAL_DOM, device="desktop",
                                engagement_id=_EID, captured_at=_CAPTURED)
        ods = v2["capture_state"]["overlays_detected"]
        # One synthetic "other" overlay records the DOM-edit caveat.
        self.assertEqual(len(ods), 1)
        self.assertEqual(ods[0]["type"], "other")

    def test_reveal_summary_with_zero_does_NOT_record(self):
        # A non-reveal page must not get a spurious caveat overlay.
        v1 = _v1_baton(reveal_summary={"reveal_els": 0, "lazy_imgs": 5})
        v2 = conv.convert_baton(v1, _MINIMAL_DOM, device="desktop",
                                engagement_id=_EID, captured_at=_CAPTURED)
        self.assertEqual(v2["capture_state"]["overlays_detected"], [])

    def test_schema_valid_in_both_branches(self):
        # The converter calls _validate(); if it didn't throw, the v2 baton
        # passed schema/baton-v1.json. Re-invoke both branches.
        v1_empty = _v1_baton()
        conv.convert_baton(v1_empty, _MINIMAL_DOM, device="desktop",
                           engagement_id=_EID, captured_at=_CAPTURED)
        v1_full = _v1_baton(overlays=[
            {"tag": "div", "id": "x", "class": "omnisend",
             "type": "newsletter-modal", "method": "js-style-display-none"},
        ], reveal_summary={"reveal_els": 2})
        conv.convert_baton(v1_full, _MINIMAL_DOM, device="desktop",
                           engagement_id=_EID, captured_at=_CAPTURED)


# ---------------------------------------------------------------------------
# C12 — semantic overlay dismissal
# ---------------------------------------------------------------------------


class TestC12SemanticDismiss(unittest.TestCase):
    """The dismiss JS must use semantic close-targeting on EVERY round and
    must NEVER click a Subscribe / sign-up / submit button."""

    def setUp(self):
        self.js = ovl._DISMISS_ROUND

    def test_subscribe_blocklist_present(self):
        # The block pattern must include the canonical newsletter copy.
        self.assertIn("subscribe", self.js.lower())
        self.assertIn("sign", self.js.lower())  # "sign up" / "sign in"
        # The pattern must look like a regex that vetoes a click — search
        # for the BLOCK_TXT regex hint.
        self.assertIn("BLOCK_TXT", self.js)

    def test_safeToClick_gate_runs_before_every_click(self):
        # The semantic safety helper must exist and gate clicks.
        self.assertIn("safeToClick", self.js)
        # All click sites must run it.
        # Count `safeToClick(` calls; each phase should call it at least once.
        self.assertGreaterEqual(self.js.count("safeToClick("), 4)

    def test_close_semantic_selector_set_present(self):
        # The acquire.md ~222-228 enumeration: aria-label close/dismiss,
        # .close class, × / ✕ glyphs, "no thanks" text.
        self.assertIn('aria-label*="close"', self.js)
        self.assertIn('aria-label*="dismiss"', self.js)
        self.assertIn(".close", self.js)
        # Glyph + "no thanks" text gating.
        self.assertIn("no thanks", self.js.lower())
        # Glyphs in CLOSE_TXT — check for at least one × variant.
        self.assertTrue("×" in self.js or "✕" in self.js or "x" in self.js.lower())

    def test_close_semantics_win_over_blocklist(self):
        # "Continue without accepting" is a DECLINE even though bare
        # "continue" is a BLOCK_TXT token — close semantics must short-circuit
        # safeToClick to true before the block-list runs.
        self.assertIn("isCloseSemantic", self.js)
        self.assertIn("continue without", self.js.lower())
        # Priority order inside safeToClick: the close check must appear
        # before the BLOCK_TXT test.
        body = self.js[self.js.index("function safeToClick"):]
        self.assertLess(
            body.index("isCloseSemantic"), body.index("BLOCK_TXT"),
            "close-semantic short-circuit must run before the block-list veto",
        )

    def test_blind_container_button_click_is_removed(self):
        # The pre-fix did `el.click()` on a bare `[role="dialog"] button`
        # match. That unconditional click site must be GONE.
        self.assertNotIn("'[role=\"dialog\"] button'", self.js)
        self.assertNotIn("'.modal button'", self.js)
        # The newsletter-container shortcut is also gone.
        self.assertNotIn("'[class*=\"omnisend\"] button'", self.js)

    def test_close_semantics_apply_on_every_round(self):
        # The contract: close-semantics on EVERY round, not just as a final
        # fallback. The single `_DISMISS_ROUND` payload (called per round
        # by dismiss_overlays) must include close-set handling BEFORE any
        # container-button traversal.
        close_phase_idx = self.js.find("close-semantic")
        container_phase_idx = self.js.find("CONTAINERS")
        self.assertGreater(close_phase_idx, 0, "close-semantic phase missing")
        self.assertGreater(container_phase_idx, close_phase_idx,
                           "close-semantic phase must run before container scan")

    def test_accept_button_for_cookie_banner_still_works(self):
        # The fix must not break the cookie-consent accept-button flow —
        # ACCEPT_TXT pattern + the explicit onetrust/osano selectors stay.
        self.assertIn("ACCEPT_TXT", self.js)
        self.assertIn("onetrust", self.js.lower())
        self.assertIn("osano", self.js.lower())


# ---------------------------------------------------------------------------
# C13 — URL-pinned variant selection
# ---------------------------------------------------------------------------


class TestC13ExtractTargetVariant(unittest.TestCase):
    def test_variant_query_param_extracted(self):
        self.assertEqual(
            cfg.extract_target_variant_from_url("https://x.com/p?variant=12345"),
            "12345",
        )

    def test_sku_query_param_extracted(self):
        self.assertEqual(
            cfg.extract_target_variant_from_url("https://x.com/p?sku=ABC-100"),
            "ABC-100",
        )

    def test_variant_id_camel_and_underscore(self):
        self.assertEqual(
            cfg.extract_target_variant_from_url("https://x.com/p?variantId=999"), "999")
        self.assertEqual(
            cfg.extract_target_variant_from_url("https://x.com/p?variant_id=999"), "999")
        self.assertEqual(
            cfg.extract_target_variant_from_url("https://x.com/p?selected_variant=42"), "42")

    def test_no_variant_param_returns_none(self):
        self.assertIsNone(cfg.extract_target_variant_from_url("https://x.com/p"))
        self.assertIsNone(cfg.extract_target_variant_from_url("https://x.com/p?utm_source=x"))

    def test_invalid_url_returns_none(self):
        self.assertIsNone(cfg.extract_target_variant_from_url(""))
        self.assertIsNone(cfg.extract_target_variant_from_url(None))  # type: ignore[arg-type]

    def test_injection_attempt_rejected(self):
        # A URL parameter containing JS-injection-shaped characters is rejected.
        self.assertIsNone(
            cfg.extract_target_variant_from_url("https://x.com/p?variant=\";alert(1);//"))


class TestC13ApplyUrlPinnedJs(unittest.TestCase):
    def test_built_js_targets_specific_variant_id(self):
        js = cfg._build_apply_url_pinned_js("12345")
        # The id is inlined as a JS string literal, used in 3 selectors +
        # ShopifyAnalytics scan.
        self.assertIn('"12345"', js)
        self.assertIn("data-variant-id", js)
        self.assertIn('input[name="id"]', js)
        self.assertIn("ShopifyAnalytics", js)

    def test_built_js_reports_url_pinned_flag(self):
        js = cfg._build_apply_url_pinned_js("12345")
        self.assertIn("url_pinned", js)
        self.assertIn("target_variant_id", js)

    def test_built_js_falls_back_to_first_available_on_miss(self):
        # If the variant can't be located on the page, the JS must still
        # produce a usable configured-state by selecting first-available
        # so the screenshot pass doesn't silently fail.
        js = cfg._build_apply_url_pinned_js("99999")
        self.assertIn("required", js)  # the first-available fallback path
        self.assertIn("selectedIndex", js)

    def test_variant_index_swatch_click_is_not_reported_as_url_pinned(self):
        js = cfg._build_apply_url_pinned_js("12345")
        self.assertIn("heuristic_variant_index", js)
        self.assertNotIn("swatches[vi].click(); found = true", js)


class TestC13FirstAvailableResolvedVariantJs(unittest.TestCase):
    def test_selected_variant_id_precedes_product_first_variant_fallback(self):
        js = cfg._APPLY_FIRST_AVAILABLE_JS
        self.assertIn("selectedVariantId", js)
        self.assertLess(js.index("selectedVariantId"), js.index("variants[0]"))

    def test_resolved_variant_source_is_reported(self):
        js = cfg._APPLY_FIRST_AVAILABLE_JS
        self.assertIn("resolved_variant_source", js)
        self.assertIn("shopify-selectedVariantId", js)
        self.assertIn("shopify-product-first-variant", js)

    def test_product_first_variant_is_labeled_last_resort(self):
        js = cfg._APPLY_FIRST_AVAILABLE_JS
        self.assertLess(js.index("selected-option-value"), js.index("shopify-product-first-variant"))
        self.assertIn("last resort", js)


class TestC13RecordsVariantSource(unittest.TestCase):
    """try_configured_state_capture wires variant_source / variant_id into
    the configured_state dict via a fake eval + fake shot pair.
    """

    def _fake_eval_factory(self, *, detect_match=True, url_pinned=True,
                           resolved_id=None):
        calls: list[str] = []

        def fake_ev(src: str):
            calls.append(src)
            if "selects.filter" in src and "ctaDisabled" in src:
                return {"requiredCount": 2, "ctaDisabled": True, "match": detect_match}
            if "url_pinned" in src:
                return {"url_pinned": url_pinned, "target_variant_id": "12345"}
            if "resolved_variant_id" in src:
                return {
                    "ok": True,
                    "n": 2,
                    "resolved_variant_id": resolved_id,
                    "resolved_variant_source": "shopify-selectedVariantId",
                }
            if "ctaText" in src:
                return {"ctaText": "Add to cart", "ctaEnabled": True, "price": "$99"}
            return {}

        return fake_ev, calls

    def _fake_shot(self, tmp_path):
        # Returns a path + dummy metadata; write 200 bytes so the size check passes.
        def shot(out_path, quality):
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(b"x" * 200)
            return out_path, "deadbeef", None, ".jpg"
        return shot

    def test_url_pinned_path_records_url_pinned_source(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            eng = Path(tmp)
            ev, _calls = self._fake_eval_factory(url_pinned=True)
            shot = self._fake_shot(eng)
            res = cfg.try_configured_state_capture(
                ev=ev, scroll_to_y=lambda y: y, eng_dir=eng,
                shot_jpeg=shot, file_prefix="",
                target_url="https://example.com/p?variant=12345",
            )
            self.assertIsNotNone(res)
            assert res is not None  # for type checker
            self.assertEqual(res["variant_source"], "url-pinned")
            self.assertEqual(res["variant_id"], "12345")

    def test_first_available_path_records_resolved_id(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            eng = Path(tmp)
            ev, _calls = self._fake_eval_factory(resolved_id="555")
            shot = self._fake_shot(eng)
            res = cfg.try_configured_state_capture(
                ev=ev, scroll_to_y=lambda y: y, eng_dir=eng,
                shot_jpeg=shot, file_prefix="",
                target_url="https://example.com/p",
            )
            self.assertIsNotNone(res)
            assert res is not None
            self.assertEqual(res["variant_source"], "first-available")
            self.assertEqual(res["variant_id"], "555")
            self.assertEqual(res["variant_resolution_source"], "shopify-selectedVariantId")

    def test_url_present_but_variant_uncatchable_falls_back(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            eng = Path(tmp)
            ev, _calls = self._fake_eval_factory(url_pinned=False)
            shot = self._fake_shot(eng)
            res = cfg.try_configured_state_capture(
                ev=ev, scroll_to_y=lambda y: y, eng_dir=eng,
                shot_jpeg=shot, file_prefix="",
                target_url="https://example.com/p?variant=99999",
            )
            self.assertIsNotNone(res)
            assert res is not None
            # The JS reported url_pinned=false (variant not on page); the
            # python side must honestly record first-available.
            self.assertEqual(res["variant_source"], "first-available")


# ---------------------------------------------------------------------------
# C16 — capture-then-cap (per-selector cap + global cap)
# ---------------------------------------------------------------------------


class TestC16CaptureThenCap(unittest.TestCase):
    def test_per_selector_sanity_cap_is_100(self):
        # The selector slice is the sanity bound (not the truncation).
        self.assertIn("slice(0, 100)", acquire_url._build_elements_js("example.com"))

    def test_per_selector_old_truncation_removed(self):
        # The pre-fix `slice(0, 10)` is gone (the C16 root cause).
        js = acquire_url._build_elements_js("example.com")
        self.assertNotIn("slice(0, 10).map", js)
        self.assertNotIn("slice(0, 10);", js)

    def test_30_same_selector_elements_all_survive_under_cap(self):
        # Below the 200-global cap: all 30 elements survive _dedupe_elements_phys.
        rows = []
        for i in range(30):
            rows.append({"selector": "[class*='product-card']", "tag": "div",
                         "x": 10 + i * 5, "y": 100 + i * 10, "width": 200, "height": 100,
                         "visible": True})
        out = acquire_url._dedupe_elements_phys(rows, cap=200)
        self.assertEqual(len(out), 30)

    def test_global_cap_truncates_at_200(self):
        rows = []
        for i in range(250):  # over-cap input
            rows.append({"selector": f"sel-{i}", "tag": "div",
                         "x": i, "y": i, "width": 10, "height": 10, "visible": True})
        out = acquire_url._dedupe_elements_phys(rows, cap=200)
        self.assertEqual(len(out), 200)

    def test_global_cap_default_is_200_in_acquirer(self):
        # The acquirer's runtime call must use 200, not 140.
        import inspect
        src = inspect.getsource(acquire_url._run_one_device)
        self.assertIn("cap=200", src)
        self.assertNotIn("cap=140", src)


# ---------------------------------------------------------------------------
# hc-C3 — true-height probe
# ---------------------------------------------------------------------------


class TestHcC3TrueHeightProbe(unittest.TestCase):
    def test_probe_js_scrolls_to_end_and_loops(self):
        js = acquire_url._DOC_HEIGHT_PROBE_JS
        self.assertIn("scrollTo", js)
        self.assertIn("scrollHeight", js)
        # The loop must converge on stability.
        self.assertIn("stable", js)

    def test_probe_js_restores_prior_scroll(self):
        js = acquire_url._DOC_HEIGHT_PROBE_JS
        # Saves prev, then restores it at the end.
        self.assertIn("prev", js)
        # The probe returns true_max_scroll_px so the baton can be pinned.
        self.assertIn("true_max_scroll_px", js)

    def test_probe_helper_returns_dict_on_eval_failure(self):
        def boom(_src):
            raise RuntimeError("eval failed")

        out = acquire_url._probe_doc_height(boom)
        self.assertEqual(out, {})

    def test_probe_helper_returns_dict_on_non_dict_response(self):
        out = acquire_url._probe_doc_height(lambda _src: "not a dict")
        self.assertEqual(out, {})

    def test_probe_helper_passes_through_dict(self):
        out = acquire_url._probe_doc_height(
            lambda _src: {"true_max_scroll_px": 12345, "doc_h": 13456, "rounds": 4})
        self.assertEqual(out["true_max_scroll_px"], 12345)


class TestHcC3ConverterPrefersProbe(unittest.TestCase):
    """The converter prefers the probed height when present; falls back to
    el_bottom otherwise; never shrinks below sec_bottom."""

    def test_positive_probe_value_is_preferred(self):
        # Probed value 5000 beats el_bottom (~30) and sec_bottom (~900).
        v1 = _v1_baton(true_max_scroll_px=5000)
        v2 = conv.convert_baton(v1, _MINIMAL_DOM, device="desktop",
                                engagement_id=_EID, captured_at=_CAPTURED)
        self.assertEqual(v2["capture_state"]["page_height_px"], 5000)

    def test_absent_probe_falls_back_to_el_bottom(self):
        # No true_max_scroll_px -> el_bottom path; sec_bottom 900 wins here.
        v1 = _v1_baton()
        v2 = conv.convert_baton(v1, _MINIMAL_DOM, device="desktop",
                                engagement_id=_EID, captured_at=_CAPTURED)
        # sec_bottom = 0+900 = 900; el_bottom = 30; vh = 1080 -> 1080 wins.
        self.assertEqual(v2["capture_state"]["page_height_px"], 1080)

    def test_zero_probe_treated_as_absent(self):
        v1 = _v1_baton(true_max_scroll_px=0)
        v2 = conv.convert_baton(v1, _MINIMAL_DOM, device="desktop",
                                engagement_id=_EID, captured_at=_CAPTURED)
        # Same as the no-probe case.
        self.assertEqual(v2["capture_state"]["page_height_px"], 1080)

    def test_probe_never_shrinks_below_sec_bottom(self):
        # A probe value that's smaller than the captured section coverage
        # is overridden by sec_bottom (the safety floor).
        v1 = _v1_baton(
            true_max_scroll_px=200,
            sections=[{"label": "tall", "scrollY": 0, "height": 4500,
                       "clusters": ["visual-cta"], "screenshot_index": 1}],
        )
        v2 = conv.convert_baton(v1, _MINIMAL_DOM, device="desktop",
                                engagement_id=_EID, captured_at=_CAPTURED)
        # sec_bottom = 0 + 4500 = 4500 (the safety floor).
        self.assertGreaterEqual(v2["capture_state"]["page_height_px"], 4500)

    def test_probe_does_not_break_schema(self):
        # Schema-valid in the probe-supplied path.
        v1 = _v1_baton(true_max_scroll_px=9999)
        # If schema validation fails, convert_baton raises.
        conv.convert_baton(v1, _MINIMAL_DOM, device="desktop",
                           engagement_id=_EID, captured_at=_CAPTURED)


class TestC11PlaceholdersNotSpecialistVisible(unittest.TestCase):
    """Synthesized overlay placeholders (is_offscreen=True, rect 0,0,1,1) must
    never reach specialists as anchorable visible evidence — dom_preprocess
    excludes is_offscreen elements from every cluster context (review defect
    fix: a placeholder at y=0 overlapped every top section and could be
    anchored, yielding a 1px hotspot at the screenshot origin)."""

    def test_offscreen_elements_excluded_from_cluster_context(self):
        import json
        import tempfile
        from dom_preprocess import preprocess_device

        eng = Path(tempfile.mkdtemp(prefix="ecp-c11-"))
        (eng / "dom.html").write_text(_MINIMAL_DOM, encoding="utf-8")
        baton = {
            "engagement_id": _EID,
            "viewport": {"width": 1440, "height": 900, "dpr": 1},
            "screenshots": [],
            "sections": [{"label": "hero", "slug": "hero", "scrollY": 0,
                          "height": 900, "clusters": ["visual-cta"],
                          "screenshot_index": 1}],
            "elements": [
                {"e_index": "e1", "role": "button", "selector": ".cta",
                 "rect": {"x": 10, "y": 100, "width": 200, "height": 50}},
                {"e_index": "e2", "role": "dialog", "selector": "[data-overlay]",
                 "is_offscreen": True,
                 "rect": {"x": 0, "y": 0, "width": 1, "height": 1}},
            ],
        }
        (eng / "baton.json").write_text(json.dumps(baton), encoding="utf-8")
        preprocess_device(eng, "desktop", ["visual-cta"])
        ctx_path = eng / "cluster-context-visual-cta-desktop.json"
        self.assertTrue(ctx_path.exists())
        ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
        indexes = {el.get("e_index") for el in ctx.get("elements", [])}
        self.assertIn("e1", indexes)
        self.assertNotIn("e2", indexes, "is_offscreen element leaked into cluster context")

    def test_reveal_pass_placeholder_is_synthesized_offscreen(self):
        v1 = _v1_baton(reveal_summary={"reveal_els": 2})
        v2 = conv.convert_baton(v1, _MINIMAL_DOM, device="desktop",
                                engagement_id=_EID, captured_at=_CAPTURED)
        placeholder = next(
            el for el in v2["elements"]
            if str(el.get("accessible_name", "")).startswith("scroll-trigger reveal pass")
        )
        self.assertTrue(placeholder["is_offscreen"])


if __name__ == "__main__":
    unittest.main()
