"""Anchor candidate registry (Phase 4a — 2026-05-18).

Tests covering:
- Role classifier rules per role (positive + negative cases)
- Ranker determinism and factor inputs
- Candidate ID format and ordering stability
- Expected-overlay template registry coverage
- Sidecar writer end-to-end against a baton fixture
- Schema accepts the new candidate_id field on visual_evidence.observed_anchor

See ``docs/ecp/2026-05-18-report-accuracy-and-hotspot-remediation-plan.md``
Phase 4 acceptance criteria.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from assembly.anchor_candidates import (
    EXPECTED_OVERLAY_TEMPLATES,
    build_anchor_candidates_sidecar,
    build_candidates,
)


def _el(
    *,
    e_index: str = "e0",
    tag: str = "div",
    role: str = "",
    accessible_name: str = "",
    text_content: str = "",
    class_: str = "",
    rect: dict | None = None,
    is_above_fold: bool = False,
    is_sticky: bool = False,
) -> dict:
    return {
        "e_index": e_index,
        "tag": tag,
        "role": role or tag,
        "accessible_name": accessible_name,
        "text_content": text_content,
        "class": class_,
        "rect": rect or {"x": 0, "y": 0, "width": 200, "height": 50},
        "is_above_fold": is_above_fold,
        "is_sticky": is_sticky,
    }


def _baton(elements: list[dict], *, device: str = "desktop") -> dict:
    return {
        "schema_version": 1,
        "engagement_id": "2026-05-18-deadbeef",
        "device": device,
        "url": "https://example.test",
        "captured_at": "2026-05-18T00:00:00.000Z",
        "viewport": {"width": 1920, "height": 1080, "dpr_requested": 1, "dpr_actual": 1},
        "capture_state": {"hydration": "post-hydration", "overlays_detected": [], "page_height_px": 3000},
        "elements": elements,
        "sections": [],
        "page_head": {},
    }


# ---------------------------------------------------------------------------
# Role classifier tests
# ---------------------------------------------------------------------------


class TestClassifierPrimaryCTA:
    def test_button_with_add_to_cart_text(self):
        baton = _baton([_el(e_index="e0", tag="button", accessible_name="Add to Cart")])
        c = build_candidates(baton)
        assert "primary-cta" in c
        assert c["primary-cta"][0]["e_index"] == "e0"

    def test_button_with_select_color_text_wins_over_variant_selector(self):
        """Phase 4a regression — 'Select Color' on a PDP is the gated
        primary CTA, not a variant swatch. Test pins the classifier
        ordering: primary-cta beats variant-selector."""
        baton = _baton([_el(e_index="e0", tag="button", accessible_name="Select Color")])
        c = build_candidates(baton)
        assert "primary-cta" in c
        assert "variant-selector" not in c
        assert c["primary-cta"][0]["e_index"] == "e0"

    def test_non_button_with_cta_text_not_classified(self):
        # Plain div with "buy now" text shouldn't fire — interactivity matters
        baton = _baton([_el(e_index="e0", tag="div", text_content="Buy now")])
        c = build_candidates(baton)
        assert "primary-cta" not in c


class TestClassifierPriceBlock:
    def test_currency_in_text_fires(self):
        baton = _baton([_el(e_index="e0", text_content="$399.50")])
        c = build_candidates(baton)
        assert "price-block" in c

    def test_strikethrough_compare_at_fires(self):
        baton = _baton([_el(e_index="e0", accessible_name="Sale $399.50 Regular $470.00")])
        c = build_candidates(baton)
        assert "price-block" in c

    def test_no_currency_no_fire(self):
        baton = _baton([_el(e_index="e0", text_content="Free shipping over orders")])
        c = build_candidates(baton)
        assert "price-block" not in c


class TestClassifierProductTitle:
    def test_h1_is_product_title(self):
        baton = _baton([_el(e_index="e0", tag="h1", accessible_name="Premium Headphones")])
        c = build_candidates(baton)
        assert "product-title" in c

    def test_h2_above_fold_is_product_title(self):
        baton = _baton([_el(e_index="e0", tag="h2", accessible_name="Premium Headphones", is_above_fold=True)])
        c = build_candidates(baton)
        assert "product-title" in c

    def test_generic_section_label_demotes_to_subheading(self):
        baton = _baton([_el(e_index="e0", tag="h2", accessible_name="Specifications")])
        c = build_candidates(baton)
        assert "product-title" not in c
        assert "subheading" in c


class TestClassifierVariantSelector:
    def test_select_dropdown_with_size_text(self):
        baton = _baton([_el(e_index="e0", tag="select", accessible_name="Size: Small/Medium/Large")])
        c = build_candidates(baton)
        assert "variant-selector" in c

    def test_button_with_color_text_only_no_select_keyword(self):
        # "Color: Red" on a button — variant selector
        baton = _baton([_el(e_index="e0", tag="button", accessible_name="Color: Red")])
        c = build_candidates(baton)
        assert "variant-selector" in c


class TestClassifierTrustStrip:
    def test_payment_logos_text(self):
        baton = _baton([_el(e_index="e0", text_content="Visa Mastercard PayPal Apple Pay")])
        c = build_candidates(baton)
        assert "trust-strip" in c

    def test_guarantee_text(self):
        baton = _baton([_el(e_index="e0", text_content="30-day money back guarantee")])
        c = build_candidates(baton)
        assert "trust-strip" in c

    def test_free_shipping_with_dollar_threshold_classifies_as_trust_not_price(self):
        """Phase 4a hardening regression — pre-fix the currency check fired
        before the trust-token check, so 'Free shipping on orders over $75'
        was classified as price-block. Codex 2026-05-18 review of 84622b0.
        """
        baton = _baton([_el(
            e_index="e0",
            text_content="Free shipping on orders over $75",
        )])
        c = build_candidates(baton)
        assert "trust-strip" in c, "Trust copy should be classified as trust-strip"
        assert "price-block" not in c, (
            "Trust copy containing a dollar amount must NOT be swallowed "
            "by price-block. The classifier ordering should give trust "
            "tokens precedence over the currency-pattern test."
        )
        assert c["trust-strip"][0]["e_index"] == "e0"

    def test_bnpl_marker_with_savings_amount_classifies_as_trust(self):
        """BNPL providers (Klarna, Afterpay, Affirm) frequently quote a
        savings or installment dollar amount. Must classify as trust-strip,
        not price-block."""
        baton = _baton([_el(
            e_index="e0",
            text_content="Pay in 4 installments of $19.99 with Klarna",
        )])
        c = build_candidates(baton)
        assert "trust-strip" in c
        assert "price-block" not in c

    def test_guarantee_with_dollar_purchase_threshold_classifies_as_trust(self):
        """Guarantee copy that mentions a minimum purchase amount must
        still classify as trust-strip."""
        baton = _baton([_el(
            e_index="e0",
            text_content="Money back guarantee within 30 days on purchases of $50+",
        )])
        c = build_candidates(baton)
        assert "trust-strip" in c
        assert "price-block" not in c

    def test_actual_price_block_still_classifies_correctly_after_reorder(self):
        """Sanity: reordering trust-before-price must not break the
        common case where a plain $399.50 IS the price block."""
        baton = _baton([_el(
            e_index="e0",
            text_content="$399.50",
        )])
        c = build_candidates(baton)
        assert "price-block" in c
        assert "trust-strip" not in c

    def test_price_block_with_compare_at_still_classifies_correctly(self):
        baton = _baton([_el(
            e_index="e0",
            accessible_name="Sale price $399.50 Regular price $470.00",
        )])
        c = build_candidates(baton)
        assert "price-block" in c
        assert "trust-strip" not in c


class TestClassifierFooterAndNavigation:
    def test_footer_role(self):
        baton = _baton([_el(e_index="e0", tag="footer", role="contentinfo", accessible_name="Site footer")])
        c = build_candidates(baton)
        assert "footer-region" in c

    def test_navigation_role(self):
        baton = _baton([_el(e_index="e0", tag="nav", role="navigation", accessible_name="Main nav")])
        c = build_candidates(baton)
        assert "navigation" in c


class TestClassifierSearch:
    def test_search_role_form(self):
        baton = _baton([_el(e_index="e0", tag="form", role="search", accessible_name="Search our store")])
        c = build_candidates(baton)
        assert "search" in c

    def test_search_input(self):
        baton = _baton([_el(e_index="e0", tag="input", text_content="search query")])
        c = build_candidates(baton)
        assert "search" in c


class TestClassifierGalleryImage:
    def test_img_tag(self):
        baton = _baton([_el(e_index="e0", tag="img", role="image", accessible_name="Product photo")])
        c = build_candidates(baton)
        assert "gallery-image" in c


class TestClassifierReviewsWidget:
    def test_review_text(self):
        baton = _baton([_el(e_index="e0", text_content="4.5 stars based on 127 reviews")])
        c = build_candidates(baton)
        assert "reviews-widget" in c


# ---------------------------------------------------------------------------
# Ranker tests
# ---------------------------------------------------------------------------


class TestRanker:
    def test_above_fold_outranks_below_fold(self):
        baton = _baton([
            _el(e_index="e0", tag="h1", accessible_name="Title A", is_above_fold=False),
            _el(e_index="e1", tag="h1", accessible_name="Title B", is_above_fold=True),
        ])
        c = build_candidates(baton)
        # Above-fold (e1) should rank higher than below-fold (e0)
        titles = c["product-title"]
        assert titles[0]["e_index"] == "e1"
        assert titles[1]["e_index"] == "e0"

    def test_small_rect_outranks_giant_rect(self):
        baton = _baton([
            _el(e_index="e0", tag="button", accessible_name="Add to cart",
                rect={"x": 0, "y": 0, "width": 1800, "height": 800}),
            _el(e_index="e1", tag="button", accessible_name="Add to cart",
                rect={"x": 0, "y": 0, "width": 200, "height": 40}),
        ])
        c = build_candidates(baton)
        # Specific button (e1) should outrank giant container (e0)
        assert c["primary-cta"][0]["e_index"] == "e1"

    def test_named_outranks_anonymous(self):
        baton = _baton([
            _el(e_index="e0", tag="img", accessible_name=""),
            _el(e_index="e1", tag="img", accessible_name="Hero product photo"),
        ])
        c = build_candidates(baton)
        assert c["gallery-image"][0]["e_index"] == "e1"

    def test_rank_score_is_deterministic(self):
        baton = _baton([
            _el(e_index="e0", tag="button", accessible_name="Add to cart", is_above_fold=True),
        ])
        a = build_candidates(baton)
        b = build_candidates(baton)
        assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)

    def test_rank_factors_exposed(self):
        baton = _baton([_el(e_index="e0", tag="button", accessible_name="Add to cart")])
        c = build_candidates(baton)
        factors = c["primary-cta"][0]["rank_factors"]
        for key in (
            "classification_confidence", "above_fold", "has_accessible_name",
            "rect_size_specificity", "text_richness",
        ):
            assert key in factors


# ---------------------------------------------------------------------------
# Candidate ID format and stability
# ---------------------------------------------------------------------------


class TestCandidateIds:
    def test_id_format_is_role_dash_number(self):
        baton = _baton([_el(e_index="e0", tag="h1", accessible_name="Title")])
        c = build_candidates(baton)
        cid = c["product-title"][0]["candidate_id"]
        assert cid == "product-title-1"

    def test_ids_are_1_based_within_role(self):
        baton = _baton([
            _el(e_index=f"e{i}", tag="img", role="image", accessible_name=f"Image {i}")
            for i in range(3)
        ])
        c = build_candidates(baton)
        ids = [x["candidate_id"] for x in c["gallery-image"]]
        assert set(ids) == {"gallery-image-1", "gallery-image-2", "gallery-image-3"}

    def test_ids_stable_across_runs(self):
        baton = _baton([
            _el(e_index="e0", tag="h1", accessible_name="Product A"),
            _el(e_index="e1", tag="button", accessible_name="Add to cart"),
        ])
        a = build_candidates(baton)
        b = build_candidates(baton)
        for role in a:
            assert [x["candidate_id"] for x in a[role]] == [x["candidate_id"] for x in b[role]]


# ---------------------------------------------------------------------------
# Expected-overlay registry
# ---------------------------------------------------------------------------


class TestExpectedOverlayTemplates:
    def test_canonical_templates_present(self):
        # Spec-required templates from the Phase 2 plan
        for tid in (
            "sticky-cta", "reviews-block", "payment-badges",
            "trust-strip", "video-tile", "msrp-anchor",
        ):
            assert tid in EXPECTED_OVERLAY_TEMPLATES
            entry = EXPECTED_OVERLAY_TEMPLATES[tid]
            assert "description" in entry
            assert "default_placement" in entry
            assert "default_kind" in entry

    def test_kinds_are_schema_valid_enum_values(self):
        # default_kind must match the schema's proposed_anchor.kind enum
        valid_kinds = {"element", "section", "viewport"}
        for tid, entry in EXPECTED_OVERLAY_TEMPLATES.items():
            assert entry["default_kind"] in valid_kinds, (
                f"Template {tid} has invalid default_kind {entry['default_kind']!r}"
            )


# ---------------------------------------------------------------------------
# Sidecar writer end-to-end
# ---------------------------------------------------------------------------


class TestSidecarWriter:
    def test_writes_atomic_json_with_expected_top_level_keys(self):
        baton = _baton([
            _el(e_index="e0", tag="h1", accessible_name="Test Product"),
            _el(e_index="e1", tag="button", accessible_name="Add to cart"),
            _el(e_index="e2", text_content="$99.95"),
        ])
        with tempfile.TemporaryDirectory() as td:
            eng = Path(td)
            (eng / "baton.json").write_text(json.dumps(baton), encoding="utf-8")
            sidecar = build_anchor_candidates_sidecar(eng, "desktop")
            sidecar_path = eng / "anchor-candidates-desktop.json"
            assert sidecar_path.exists()
            on_disk = json.loads(sidecar_path.read_text(encoding="utf-8"))
            for key in (
                "engagement_id", "device", "candidates_by_role",
                "candidate_to_e_index", "expected_overlay_templates", "counts",
            ):
                assert key in on_disk
            assert on_disk == sidecar

    def test_candidate_to_e_index_maps_correctly(self):
        baton = _baton([
            _el(e_index="e5", tag="button", accessible_name="Add to cart"),
            _el(e_index="e10", text_content="$59.99"),
        ])
        with tempfile.TemporaryDirectory() as td:
            eng = Path(td)
            (eng / "baton.json").write_text(json.dumps(baton), encoding="utf-8")
            sidecar = build_anchor_candidates_sidecar(eng, "desktop")
            assert sidecar["candidate_to_e_index"]["primary-cta-1"] == "e5"
            assert sidecar["candidate_to_e_index"]["price-block-1"] == "e10"

    def test_counts_block(self):
        baton = _baton([
            _el(e_index="e0", tag="h1", accessible_name="Product"),
            _el(e_index="e1", tag="button", accessible_name="Add to cart"),
        ])
        with tempfile.TemporaryDirectory() as td:
            eng = Path(td)
            (eng / "baton.json").write_text(json.dumps(baton), encoding="utf-8")
            sidecar = build_anchor_candidates_sidecar(eng, "desktop")
            counts = sidecar["counts"]
            assert counts["baton_elements"] == 2
            assert counts["total_candidates"] == 2
            assert "by_role" in counts

    def test_mobile_baton_filename_resolution(self):
        baton = _baton([_el(e_index="e0", tag="h1", accessible_name="Mobile")], device="mobile")
        with tempfile.TemporaryDirectory() as td:
            eng = Path(td)
            (eng / "baton-mobile.json").write_text(json.dumps(baton), encoding="utf-8")
            sidecar = build_anchor_candidates_sidecar(eng, "mobile")
            assert (eng / "anchor-candidates-mobile.json").exists()
            assert sidecar["device"] == "mobile"


# ---------------------------------------------------------------------------
# Real fixture smoke + schema integration
# ---------------------------------------------------------------------------


class TestRealFixture:
    """End-to-end smoke against the committed awdmods baton — proves the
    classifier picks up the elements specialists actually cited in the
    Phase 1 fixed engagement."""

    FIXED_ENGAGEMENT = REPO_ROOT / "docs" / "ecp" / "2026-05-18-5ff7a91f-fixed"

    @pytest.fixture
    def real_baton(self) -> dict:
        if not self.FIXED_ENGAGEMENT.exists():
            pytest.skip("Fixed engagement fixture not committed")
        return json.loads((self.FIXED_ENGAGEMENT / "baton.json").read_text(encoding="utf-8"))

    def test_real_awdmods_baton_produces_key_candidates(self, real_baton: dict):
        c = build_candidates(real_baton)
        # The cluster specialists in this engagement cited e10 (price),
        # e18 (Select Color CTA), e12 (search), e20 (footer). Each must
        # appear as a candidate so Phase 4b can rely on the registry.
        assert "price-block" in c
        assert any(x["e_index"] == "e10" for x in c["price-block"])
        assert "primary-cta" in c
        assert any(x["e_index"] == "e18" for x in c["primary-cta"])
        assert "search" in c
        assert any(x["e_index"] == "e12" for x in c["search"])
        assert "footer-region" in c
        assert any(x["e_index"] == "e20" for x in c["footer-region"])


class TestResolveCandidateIds:
    """Phase 4a hardening (2026-05-18) — resolve_candidate_ids_in_emission
    substitutes candidate_id references with canonical baton_index."""

    def _emission(self, findings: list[dict]) -> dict:
        return {
            "schema_version": 1,
            "engagement_id": "2026-05-18-deadbeef",
            "cluster": "pricing",
            "device": "desktop",
            "specialist_model": {"family": "sonnet", "version": "4.6"},
            "started_at": "2026-05-18T00:00:00.000Z",
            "completed_at": "2026-05-18T00:00:01.000Z",
            "status": "complete",
            "findings": findings,
        }

    def _sidecar(self, candidate_to_e: dict[str, str]) -> dict:
        return {
            "engagement_id": "2026-05-18-deadbeef",
            "device": "desktop",
            "candidates_by_role": {},
            "candidate_to_e_index": candidate_to_e,
            "expected_overlay_templates": {},
            "counts": {"total_candidates": len(candidate_to_e), "by_role": {}, "baton_elements": 0},
        }

    def _finding_with_candidate_id(self, candidate_id: str, baton_index: str = "") -> dict:
        return {
            "cluster": "pricing", "device": "desktop", "local_id": 1,
            "verdict": "FAIL", "title": "Test", "surface": "price-block",
            "element": {
                "baton_index": baton_index,
                "text_content": "$199", "role": "text",
            },
            "severity": "MEDIUM", "scope": "page",
            "effort": {"change_type": "copy", "change_scope": "single-file"},
            "evidence_anchors": [{"type": "dom", "reference": "e0"}],
            "reference_citations": [{"source": "price-anchoring.md", "tier": "Silver"}],
            "observation": "obs", "recommendation": "rec",
            "why_this_matters": "why", "evidence_tier": "Silver",
            "visual_evidence": {
                "type": "exact_element",
                "confidence": "high",
                "observed_anchor": {"candidate_id": candidate_id},
            },
        }

    def test_resolves_candidate_id_to_baton_index(self):
        from assembly.anchor_candidates import resolve_candidate_ids_in_emission

        emission = self._emission([self._finding_with_candidate_id("price-block-1")])
        sidecar = self._sidecar({"price-block-1": "e10"})
        new_em, log = resolve_candidate_ids_in_emission(emission, sidecar)

        f = new_em["findings"][0]
        assert f["element"]["baton_index"] == "e10"
        # Also written into the observed_anchor for downstream consumers
        assert f["visual_evidence"]["observed_anchor"]["baton_index"] == "e10"
        assert log[0]["action"] == "substituted"
        assert log[0]["resolved_to"] == "e10"

    def test_does_not_overwrite_explicit_baton_index(self):
        from assembly.anchor_candidates import resolve_candidate_ids_in_emission

        emission = self._emission([
            self._finding_with_candidate_id("price-block-1", baton_index="e5"),
        ])
        sidecar = self._sidecar({"price-block-1": "e10"})
        new_em, log = resolve_candidate_ids_in_emission(emission, sidecar)

        # Explicit baton_index wins; candidate_id treated as metadata
        assert new_em["findings"][0]["element"]["baton_index"] == "e5"
        assert log[0]["action"] == "already_resolved"

    def test_substitutes_when_baton_index_is_absent(self):
        from assembly.anchor_candidates import resolve_candidate_ids_in_emission

        emission = self._emission([
            self._finding_with_candidate_id("price-block-1", baton_index="absent"),
        ])
        sidecar = self._sidecar({"price-block-1": "e10"})
        new_em, _ = resolve_candidate_ids_in_emission(emission, sidecar)
        # "absent" is treated as eligible for substitution
        assert new_em["findings"][0]["element"]["baton_index"] == "e10"

    def test_unresolved_candidate_id_strict_raises(self):
        from assembly.anchor_candidates import (
            CandidateResolutionError,
            resolve_candidate_ids_in_emission,
        )

        emission = self._emission([self._finding_with_candidate_id("price-block-99")])
        sidecar = self._sidecar({"price-block-1": "e10"})
        with pytest.raises(CandidateResolutionError):
            resolve_candidate_ids_in_emission(emission, sidecar, strict=True)

    def test_unresolved_candidate_id_non_strict_logs(self):
        from assembly.anchor_candidates import resolve_candidate_ids_in_emission

        emission = self._emission([self._finding_with_candidate_id("price-block-99")])
        sidecar = self._sidecar({"price-block-1": "e10"})
        new_em, log = resolve_candidate_ids_in_emission(emission, sidecar)
        # No substitution; baton_index unchanged
        assert new_em["findings"][0]["element"]["baton_index"] == ""
        assert log[0]["action"] == "unresolved"

    def test_no_sidecar_passes_through(self):
        from assembly.anchor_candidates import resolve_candidate_ids_in_emission

        emission = self._emission([self._finding_with_candidate_id("price-block-1")])
        new_em, log = resolve_candidate_ids_in_emission(emission, None)
        assert new_em is emission
        assert log[0]["action"] == "no_sidecar"

    def test_idempotent(self):
        from assembly.anchor_candidates import resolve_candidate_ids_in_emission

        emission = self._emission([self._finding_with_candidate_id("price-block-1")])
        sidecar = self._sidecar({"price-block-1": "e10"})
        once, _ = resolve_candidate_ids_in_emission(emission, sidecar)
        twice, _ = resolve_candidate_ids_in_emission(once, sidecar)
        assert json.dumps(once, sort_keys=True) == json.dumps(twice, sort_keys=True)


class TestParseEmissionFileWithSidecar:
    """End-to-end regression — Codex 2026-05-18 review of 84622b0 asked
    for proof that a specialist citing ONLY candidate_id results in a
    correctly-resolved baton_index in the final parse output. This is the
    contract test for the runtime resolver, not just the helper."""

    def _emission_payload(self, candidate_id: str) -> dict:
        return {
            "schema_version": 1,
            "engagement_id": "2026-05-18-deadbeef",
            "cluster": "pricing",
            "device": "desktop",
            "specialist_model": {"family": "sonnet", "version": "4.6"},
            "started_at": "2026-05-18T00:00:00.000Z",
            "completed_at": "2026-05-18T00:00:01.000Z",
            "status": "complete",
            "findings": [{
                "cluster": "pricing", "device": "desktop", "local_id": 1,
                "verdict": "FAIL", "title": "Bare price block, no anchor",
                "surface": "price-block",
                "element": {"baton_index": "", "text_content": "$399.50", "role": "text"},
                "severity": "MEDIUM", "scope": "page",
                "effort": {"change_type": "copy", "change_scope": "single-file"},
                "evidence_anchors": [{"type": "dom", "reference": "e10"}],
                "reference_citations": [{"source": "price-anchoring.md", "tier": "Silver"}],
                "observation": "obs prose long enough to pass the validator threshold",
                "recommendation": "rec prose long enough to pass the validator threshold",
                "why_this_matters": "anchoring is the highest leverage pricing pattern",
                "evidence_tier": "Silver",
                "visual_evidence": {
                    "type": "exact_element",
                    "confidence": "high",
                    "observed_anchor": {"candidate_id": candidate_id},
                },
            }],
        }

    def test_candidate_id_only_finding_resolves_via_parse_emission_file(
        self, tmp_path: Path,
    ) -> None:
        from assembly.json_parser import parse_emission_file

        payload = self._emission_payload("price-block-1")
        sidecar = {
            "engagement_id": "2026-05-18-deadbeef",
            "device": "desktop",
            "candidates_by_role": {},
            "candidate_to_e_index": {"price-block-1": "e10"},
            "expected_overlay_templates": {},
            "counts": {"total_candidates": 1, "by_role": {}, "baton_elements": 24},
        }
        emission_path = tmp_path / "cluster-pricing-desktop.json"
        emission_path.write_text(json.dumps(payload), encoding="utf-8")

        # Without sidecar: schema rejects because baton_index="" is empty
        # AND the visual-position-finding rule may fire... actually let's
        # check what happens. The key assertion is WITH sidecar it works.
        result = parse_emission_file(emission_path, anchor_candidates_sidecar=sidecar)
        finding = result.findings[0]
        assert finding.baton_index == "e10", (
            "parse_emission_file with anchor_candidates_sidecar must resolve "
            "candidate_id to baton_index BEFORE schema validation."
        )
        # And visual_evidence is preserved on the dataclass
        assert finding.visual_evidence is not None
        assert finding.visual_evidence["observed_anchor"]["baton_index"] == "e10"

    def test_candidate_id_only_finding_without_sidecar_fails_validation(
        self, tmp_path: Path,
    ) -> None:
        """Negative path: when the sidecar isn't supplied, the legacy
        validator catches the empty baton_index. This pins the contract
        that candidate_id-only is ONLY safe when the sidecar is supplied."""
        from assembly.json_parser import (
            EmissionValidationError, parse_emission_file,
        )

        payload = self._emission_payload("price-block-1")
        emission_path = tmp_path / "cluster-pricing-desktop.json"
        emission_path.write_text(json.dumps(payload), encoding="utf-8")

        # Empty baton_index is rejected by the existing schema
        with pytest.raises(EmissionValidationError):
            parse_emission_file(emission_path)  # no sidecar


class TestEndToEndCandidateIdResolution:
    """The full chain: emission with candidate_id → parse with sidecar →
    Finding dataclass carries resolved baton_index and visual_evidence →
    loader-format dict preserves both. Codex 2026-05-18 asked for an
    end-to-end test that proves the runtime resolver works, not just
    the helper."""

    def test_full_chain_preserves_visual_evidence_and_resolves_id(
        self, tmp_path: Path,
    ) -> None:
        from assembly.json_parser import parse_emission_file
        from report.v2_loader import _finding_dict

        payload = {
            "schema_version": 1, "engagement_id": "2026-05-18-deadbeef",
            "cluster": "trust-credibility", "device": "desktop",
            "specialist_model": {"family": "sonnet", "version": "4.6"},
            "started_at": "2026-05-18T00:00:00.000Z",
            "completed_at": "2026-05-18T00:00:01.000Z",
            "status": "complete",
            "findings": [{
                "cluster": "trust-credibility", "device": "desktop", "local_id": 1,
                "verdict": "FAIL", "title": "No payment badges near CTA",
                "surface": "trust-badge-cluster",
                "element": {"baton_index": "", "text_content": "Add to cart", "role": "button"},
                "severity": "HIGH", "scope": "page",
                "effort": {"change_type": "html-attr", "change_scope": "single-file"},
                "evidence_anchors": [{"type": "dom", "reference": "e18"}],
                "reference_citations": [{"source": "trust-and-credibility.md", "tier": "Gold"}],
                "observation": "Long enough observation prose to satisfy the validator threshold for FAIL.",
                "recommendation": "Long enough recommendation prose to satisfy the validator threshold for FAIL.",
                "why_this_matters": "Trust signals near the CTA reduce friction at purchase decision time.",
                "evidence_tier": "Gold",
                "visual_evidence": {
                    "type": "proxy_element",
                    "confidence": "medium",
                    "observed_anchor": {
                        "candidate_id": "primary-cta-1",
                        "selector_hint": ".add-to-cart-btn",
                    },
                    "reason": "Anchor next to the CTA so the missing badges are visually adjacent",
                },
            }],
        }
        sidecar = {
            "engagement_id": "2026-05-18-deadbeef", "device": "desktop",
            "candidates_by_role": {},
            "candidate_to_e_index": {"primary-cta-1": "e18"},
            "expected_overlay_templates": {},
            "counts": {"total_candidates": 1, "by_role": {}, "baton_elements": 24},
        }
        emission_path = tmp_path / "cluster-trust-credibility-desktop.json"
        emission_path.write_text(json.dumps(payload), encoding="utf-8")

        result = parse_emission_file(emission_path, anchor_candidates_sidecar=sidecar)
        finding = result.findings[0]
        assert finding.baton_index == "e18"
        assert finding.visual_evidence is not None

        # Round-trip through _finding_dict (loader's whitelist normalizer)
        loader_dict = _finding_dict("trust-credibility", "desktop", result.raw["findings"][0])
        assert loader_dict["baton_index"] == "e18"
        assert loader_dict["visual_evidence"] is not None
        assert loader_dict["visual_evidence"]["observed_anchor"]["candidate_id"] == "primary-cta-1"
        assert loader_dict["visual_evidence"]["observed_anchor"]["baton_index"] == "e18"


class TestPublicLoaderPreservesVisualEvidence:
    """Phase 4a hardening 2 (2026-05-18) — Codex review item 1 on ffeb1a6.
    The PUBLIC loader path (build_canonical_view + load_v2_findings) must
    preserve producer-authored visual_evidence and resolved candidate_id
    end-to-end, not just _finding_dict. Pre-fix, raw_by_ref dropped
    visual_evidence and the renderer-facing findings dict didn't surface
    it — so v2_markers couldn't honor producer-authored placement.
    """

    def _emission_payload(self, *, cluster: str, device: str, candidate_id: str) -> dict:
        return {
            "schema_version": 1, "engagement_id": "2026-05-18-deadbeef",
            "cluster": cluster, "device": device,
            "specialist_model": {"family": "sonnet", "version": "4.6"},
            "started_at": "2026-05-18T00:00:00.000Z",
            "completed_at": "2026-05-18T00:00:01.000Z",
            "status": "complete",
            "findings": [{
                "cluster": cluster, "device": device, "local_id": 1,
                "verdict": "FAIL", "title": "Test finding with candidate_id only",
                "surface": "price-block",
                "element": {"baton_index": "", "text_content": "$199.99", "role": "text"},
                "severity": "MEDIUM", "scope": "page",
                "effort": {"change_type": "copy", "change_scope": "single-file"},
                "evidence_anchors": [{"type": "dom", "reference": "e10"}],
                "reference_citations": [{"source": "price-anchoring.md", "tier": "Silver"}],
                "observation": "Long enough observation prose to satisfy the validator threshold for FAIL findings.",
                "recommendation": "Long enough recommendation prose to satisfy the validator threshold for FAIL findings.",
                "why_this_matters": "Anchoring is the highest-leverage pricing pattern for SKUs in the relevant range.",
                "evidence_tier": "Silver",
                "visual_evidence": {
                    "type": "exact_element",
                    "confidence": "high",
                    "observed_anchor": {"candidate_id": candidate_id},
                    "reason": "Anchor at the price block",
                },
            }],
        }

    def _engagement(self, tmp_path: Path, candidate_id: str = "price-block-1") -> Path:
        """Build a minimal engagement folder: one cluster emission per
        device + matching anchor-candidates sidecars."""
        eng = tmp_path / "engagement"
        eng.mkdir()
        for device in ("desktop", "mobile"):
            payload = self._emission_payload(
                cluster="pricing", device=device, candidate_id=candidate_id,
            )
            (eng / f"cluster-pricing-{device}.json").write_text(
                json.dumps(payload), encoding="utf-8",
            )
            sidecar = {
                "engagement_id": "2026-05-18-deadbeef", "device": device,
                "candidates_by_role": {},
                "candidate_to_e_index": {candidate_id: "e10"},
                "expected_overlay_templates": {},
                "counts": {"total_candidates": 1, "by_role": {}, "baton_elements": 1},
            }
            (eng / f"anchor-candidates-{device}.json").write_text(
                json.dumps(sidecar), encoding="utf-8",
            )
        return eng

    def test_build_canonical_view_surfaces_visual_evidence(self, tmp_path: Path) -> None:
        """The internal canonical view dict (raw_by_ref → merged) must
        carry visual_evidence so load_v2_findings can pass it through."""
        from report.v2_loader import build_canonical_view

        eng = self._engagement(tmp_path)
        cluster_paths = sorted(eng.glob("cluster-*.json"))
        by_canon, _aliases, _drops = build_canonical_view(cluster_paths, None)

        # At least one canonical ref must carry visual_evidence with the
        # producer-authored type and the resolved baton_index.
        with_ve = [
            ref for ref, meta in by_canon.items()
            if isinstance(meta.get("visual_evidence"), dict)
        ]
        assert with_ve, (
            "build_canonical_view dropped producer-authored visual_evidence. "
            "It must copy f.visual_evidence into raw_by_ref so the renderer "
            "can honor explicit type/confidence over derived placement."
        )
        first_meta = by_canon[with_ve[0]]
        ve = first_meta["visual_evidence"]
        assert ve.get("type") == "exact_element"
        assert ve["observed_anchor"]["candidate_id"] == "price-block-1"
        assert ve["observed_anchor"]["baton_index"] == "e10"

    def test_load_v2_findings_carries_visual_evidence(self, tmp_path: Path) -> None:
        """The PUBLIC entry point load_v2_findings must include
        visual_evidence on every returned finding dict — this is what
        v2_markers.auto_map_markers_v2 reads via derive_visual_evidence
        rule 1 (producer-authored wins)."""
        from report.v2_loader import load_v2_findings

        eng = self._engagement(tmp_path)
        # No audit-{device}.md present → loader still returns findings,
        # prose just falls back to the canonical meta. That's the right
        # shape for this test.
        findings = load_v2_findings(eng, "desktop")
        assert findings, "load_v2_findings returned no findings"

        # Find the candidate_id-only finding and assert visual_evidence
        # survived the entire public loader path.
        f = findings[0]
        ve = f.get("visual_evidence")
        assert ve is not None, (
            "load_v2_findings dropped visual_evidence from the public "
            "loader output. v2_markers cannot honor producer-authored "
            "placement without this. Closes Codex 2026-05-18 review."
        )
        assert ve.get("type") == "exact_element"
        assert ve["observed_anchor"]["candidate_id"] == "price-block-1"
        assert ve["observed_anchor"]["baton_index"] == "e10"
        # And the top-level baton_index resolved through the sidecar
        assert f.get("baton_index") == "e10"


class TestCrossDeviceVisualEvidence:
    """Phase 4a hardening 3 (2026-05-18) — Codex review of 50e1d94.
    cross_device_title_merge merges same-titled findings across devices.
    Pre-fix, visual_evidence was preserved only on the canonical winner,
    so mobile renderings of a cross-device-merged finding got the desktop
    winner's observed_anchor.baton_index even though top-level
    baton_index correctly came from baton_index_by_device.
    """

    def _emission(self, *, device: str, candidate_id: str = "price-block-1") -> dict:
        return {
            "schema_version": 1, "engagement_id": "2026-05-18-deadbeef",
            "cluster": "pricing", "device": device,
            "specialist_model": {"family": "sonnet", "version": "4.6"},
            "started_at": "2026-05-18T00:00:00.000Z",
            "completed_at": "2026-05-18T00:00:01.000Z",
            "status": "complete",
            "findings": [{
                "cluster": "pricing", "device": device, "local_id": 1,
                "verdict": "FAIL",
                # SAME TITLE on both devices → cross_device_title_merge collapses
                "title": "Price block lacks MSRP anchor",
                "surface": "price-block",
                "element": {"baton_index": "", "text_content": "$199.99", "role": "text"},
                "severity": "MEDIUM", "scope": "page",
                "effort": {"change_type": "copy", "change_scope": "single-file"},
                "evidence_anchors": [{"type": "dom", "reference": "e0"}],
                "reference_citations": [{"source": "price-anchoring.md", "tier": "Silver"}],
                "observation": "Long observation prose to satisfy the validator threshold for FAIL.",
                "recommendation": "Long recommendation prose to satisfy the validator threshold for FAIL.",
                "why_this_matters": "Anchoring is the highest leverage pricing pattern for this SKU.",
                "evidence_tier": "Silver",
                "visual_evidence": {
                    "type": "exact_element", "confidence": "high",
                    "observed_anchor": {"candidate_id": candidate_id},
                },
            }],
        }

    def _engagement_with_different_e_indexes(self, tmp_path: Path) -> Path:
        """Build an engagement where the same candidate_id maps to a
        DIFFERENT e_index on each device — the Codex repro shape."""
        eng = tmp_path / "engagement"
        eng.mkdir()
        # Desktop emission + sidecar (price-block-1 → e10)
        (eng / "cluster-pricing-desktop.json").write_text(
            json.dumps(self._emission(device="desktop")), encoding="utf-8",
        )
        (eng / "anchor-candidates-desktop.json").write_text(json.dumps({
            "engagement_id": "2026-05-18-deadbeef", "device": "desktop",
            "candidates_by_role": {},
            "candidate_to_e_index": {"price-block-1": "e10"},
            "expected_overlay_templates": {},
            "counts": {"total_candidates": 1, "by_role": {}, "baton_elements": 1},
        }), encoding="utf-8")
        # Mobile emission + sidecar (price-block-1 → e88 — different e_index)
        (eng / "cluster-pricing-mobile.json").write_text(
            json.dumps(self._emission(device="mobile")), encoding="utf-8",
        )
        (eng / "anchor-candidates-mobile.json").write_text(json.dumps({
            "engagement_id": "2026-05-18-deadbeef", "device": "mobile",
            "candidates_by_role": {},
            "candidate_to_e_index": {"price-block-1": "e88"},
            "expected_overlay_templates": {},
            "counts": {"total_candidates": 1, "by_role": {}, "baton_elements": 1},
        }), encoding="utf-8")
        return eng

    def test_desktop_rendering_gets_desktop_e_index_in_observed_anchor(
        self, tmp_path: Path,
    ) -> None:
        """The Codex repro: same title on both devices, candidate_id
        resolves to different e_indexes per device. Desktop rendering
        must see e10 in BOTH top-level baton_index AND
        visual_evidence.observed_anchor.baton_index."""
        from report.v2_loader import load_v2_findings

        eng = self._engagement_with_different_e_indexes(tmp_path)
        findings = load_v2_findings(eng, "desktop")
        assert findings, "No findings returned for desktop"
        f = findings[0]
        assert f["baton_index"] == "e10", (
            f"Top-level baton_index drift on desktop: {f.get('baton_index')!r}"
        )
        ve = f.get("visual_evidence")
        assert ve is not None, "visual_evidence missing from desktop finding"
        anchor_bi = (ve.get("observed_anchor") or {}).get("baton_index")
        assert anchor_bi == "e10", (
            f"visual_evidence.observed_anchor.baton_index={anchor_bi!r} on "
            f"desktop rendering — must be 'e10' to match top-level. "
            f"This is the Codex 2026-05-18 cross-device merge bug."
        )

    def test_mobile_rendering_gets_mobile_e_index_in_observed_anchor(
        self, tmp_path: Path,
    ) -> None:
        """Mirror test — mobile rendering must see e88 in BOTH places.
        Pre-fix this returned e10 in observed_anchor (the desktop
        canonical winner leaked through) even though top-level
        baton_index correctly said e88."""
        from report.v2_loader import load_v2_findings

        eng = self._engagement_with_different_e_indexes(tmp_path)
        findings = load_v2_findings(eng, "mobile")
        assert findings, "No findings returned for mobile"
        f = findings[0]
        assert f["baton_index"] == "e88", (
            f"Top-level baton_index drift on mobile: {f.get('baton_index')!r}"
        )
        ve = f.get("visual_evidence")
        assert ve is not None, "visual_evidence missing from mobile finding"
        anchor_bi = (ve.get("observed_anchor") or {}).get("baton_index")
        assert anchor_bi == "e88", (
            f"visual_evidence.observed_anchor.baton_index={anchor_bi!r} on "
            f"mobile rendering — must be 'e88' to match top-level. "
            f"Codex's exact repro: pre-fix returned 'e10' here (desktop "
            f"winner leak)."
        )

    def test_visual_evidence_by_device_populated_on_canonical_view(
        self, tmp_path: Path,
    ) -> None:
        """Internal contract: cross_device_title_merge populates
        visual_evidence_by_device so load_v2_findings can pick correctly."""
        from report.v2_loader import build_canonical_view

        eng = self._engagement_with_different_e_indexes(tmp_path)
        cluster_paths = sorted(eng.glob("cluster-*.json"))
        by_canon, _aliases, _drops = build_canonical_view(cluster_paths, None)

        # The merged finding's canonical meta carries per-device VE
        merged = next(iter(by_canon.values()))
        ve_by_dev = merged.get("visual_evidence_by_device") or {}
        assert "desktop" in ve_by_dev and "mobile" in ve_by_dev
        assert ve_by_dev["desktop"]["observed_anchor"]["baton_index"] == "e10"
        assert ve_by_dev["mobile"]["observed_anchor"]["baton_index"] == "e88"

    def test_singleton_finding_falls_back_to_canonical_visual_evidence(
        self, tmp_path: Path,
    ) -> None:
        """When a finding exists on only one device (singleton), no merge
        happens. The single device must still get its visual_evidence
        via the canonical fallback path."""
        from report.v2_loader import load_v2_findings

        eng = tmp_path / "engagement"
        eng.mkdir()
        (eng / "cluster-pricing-desktop.json").write_text(
            json.dumps(self._emission(device="desktop")), encoding="utf-8",
        )
        (eng / "anchor-candidates-desktop.json").write_text(json.dumps({
            "engagement_id": "2026-05-18-deadbeef", "device": "desktop",
            "candidates_by_role": {},
            "candidate_to_e_index": {"price-block-1": "e10"},
            "expected_overlay_templates": {},
            "counts": {"total_candidates": 1, "by_role": {}, "baton_elements": 1},
        }), encoding="utf-8")

        findings = load_v2_findings(eng, "desktop")
        assert findings
        f = findings[0]
        assert f["baton_index"] == "e10"
        ve = f.get("visual_evidence")
        assert ve is not None
        assert ve["observed_anchor"]["baton_index"] == "e10"


class TestLeadPrepCandidateIdResolution:
    """Phase 4a hardening 2 — Codex review item 2 on ffeb1a6.
    scripts/lead_prep.py build-canonical-frefs must accept candidate_id-only
    emissions when the anchor-candidates sidecar is present."""

    def _engagement_with_meta(self, tmp_path: Path) -> Path:
        eng = tmp_path / "engagement"
        eng.mkdir()
        meta = {
            "schema_version": 3, "id": "2026-05-18-deadbeef",
            "created": "2026-05-18T00:00:00.000Z",
            "updated": "2026-05-18T00:00:00.000Z",
            "type": "audit", "phase": "audit",
            "engagement_status": "complete", "reconciled": True,
            "page": {"url": "https://example.test", "url_normalized": "example.test",
                     "file_path": None, "type": "product"},
            "platform": "shopify", "source_mode": "url-dual",
            "devices_requested": ["desktop"], "devices_scanned": ["desktop"],
            "clusters_used": ["pricing"], "scope": "focused",
            "min_priority": None, "compare_target": None, "quick_scan": False,
            "blocked": False, "plans_queue": [], "screenshot_input": None,
        }
        (eng / "meta.json").write_text(json.dumps(meta), encoding="utf-8")

        emission = {
            "schema_version": 1, "engagement_id": "2026-05-18-deadbeef",
            "cluster": "pricing", "device": "desktop",
            "specialist_model": {"family": "sonnet", "version": "4.6"},
            "started_at": "2026-05-18T00:00:00.000Z",
            "completed_at": "2026-05-18T00:00:01.000Z",
            "status": "complete",
            "findings": [{
                "cluster": "pricing", "device": "desktop", "local_id": 1,
                "verdict": "FAIL", "title": "No MSRP anchor on price block",
                "surface": "price-block",
                # baton_index intentionally empty — candidate_id is the
                # only anchor signal. Pre-fix this fails validation in
                # lead_prep.build_canonical_frefs.
                "element": {"baton_index": "", "text_content": "$399.50", "role": "text"},
                "severity": "MEDIUM", "scope": "page",
                "effort": {"change_type": "copy", "change_scope": "single-file"},
                "evidence_anchors": [{"type": "dom", "reference": "e10"}],
                "reference_citations": [{"source": "price-anchoring.md", "tier": "Silver"}],
                "observation": "Long observation prose to satisfy the validator threshold for FAIL.",
                "recommendation": "Long recommendation prose to satisfy the validator threshold for FAIL.",
                "why_this_matters": "Anchoring is the highest leverage pricing pattern for this SKU.",
                "evidence_tier": "Silver",
                "visual_evidence": {
                    "type": "exact_element", "confidence": "high",
                    "observed_anchor": {"candidate_id": "price-block-1"},
                },
            }],
        }
        (eng / "cluster-pricing-desktop.json").write_text(
            json.dumps(emission), encoding="utf-8",
        )
        sidecar = {
            "engagement_id": "2026-05-18-deadbeef", "device": "desktop",
            "candidates_by_role": {},
            "candidate_to_e_index": {"price-block-1": "e10"},
            "expected_overlay_templates": {},
            "counts": {"total_candidates": 1, "by_role": {}, "baton_elements": 1},
        }
        (eng / "anchor-candidates-desktop.json").write_text(
            json.dumps(sidecar), encoding="utf-8",
        )
        return eng

    def test_build_canonical_frefs_accepts_candidate_id_only_emission(
        self, tmp_path: Path,
    ) -> None:
        """Direct function-level invocation of lead_prep.build_canonical_frefs
        against a candidate_id-only emission. Pre-fix returns exit code 1
        with a schema validation error; post-fix returns 0 and writes the
        manifest."""
        import importlib
        # Re-import lead_prep to pick up the patched function (test runs
        # in isolated tmp_path so no shared state risk).
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        lead_prep = importlib.import_module("lead_prep")

        eng = self._engagement_with_meta(tmp_path)
        rc = lead_prep.build_canonical_frefs(eng)
        assert rc == 0, (
            f"lead_prep.build_canonical_frefs returned {rc} against a "
            "candidate_id-only emission with sidecar present. The sidecar "
            "MUST be passed into parse_emission_file so candidate_id "
            "resolves before validation. Closes Codex 2026-05-18 review "
            "item 2 on ffeb1a6."
        )
        # Manifest was written
        manifest = eng / "canonical-f-refs-manifest.json"
        assert manifest.exists()

    def test_build_canonical_frefs_without_sidecar_still_fails_clearly(
        self, tmp_path: Path,
    ) -> None:
        """Negative path: when the sidecar is missing, a candidate_id-only
        emission can't be resolved and parse fails. This is the right
        behavior — pins the contract that the sidecar is the resolution
        source-of-truth."""
        import importlib
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        lead_prep = importlib.import_module("lead_prep")

        eng = self._engagement_with_meta(tmp_path)
        # Remove the sidecar
        (eng / "anchor-candidates-desktop.json").unlink()
        rc = lead_prep.build_canonical_frefs(eng)
        # Should fail OR produce an empty manifest; either way it must
        # NOT silently accept the candidate_id-only emission as valid
        # against a baton it can't resolve.
        manifest = eng / "canonical-f-refs-manifest.json"
        if rc == 0 and manifest.exists():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            # If the manifest was written, it must not include the
            # unresolved finding (otherwise we silently shipped a broken ref)
            assert not data.get("entries"), (
                "Without sidecar, candidate_id-only emission should not "
                "produce manifest entries; got: " + str(data.get("entries"))
            )


class TestSchemaCandidateId:
    """schema/finding-v1.json must accept the new candidate_id field on
    visual_evidence.observed_anchor."""

    @pytest.fixture
    def schema(self) -> dict:
        return json.loads((REPO_ROOT / "schema" / "finding-v1.json").read_text(encoding="utf-8"))

    @pytest.fixture
    def base_finding(self) -> dict:
        return {
            "cluster": "pricing", "device": "desktop", "local_id": 1, "verdict": "FAIL",
            "title": "No MSRP Anchor", "surface": "price-block",
            "element": {"baton_index": "e10", "text_content": "$399.50", "role": "div"},
            "severity": "MEDIUM", "scope": "page",
            "effort": {"change_type": "copy", "change_scope": "single-file"},
            "evidence_anchors": [{"type": "dom", "reference": "e10"}],
            "reference_citations": [{"source": "price-anchoring.md", "tier": "Silver"}],
            "observation": "Bare $399.50 with no compare-at framing.",
            "recommendation": "Add MSRP strikethrough above the live price.",
            "why_this_matters": "Anchoring is highest-leverage for SKUs over $50.",
            "evidence_tier": "Silver",
        }

    def test_observed_anchor_with_candidate_id_validates(self, schema, base_finding):
        from jsonschema import Draft202012Validator
        base_finding["visual_evidence"] = {
            "type": "exact_element",
            "confidence": "high",
            "observed_anchor": {
                "candidate_id": "price-block-1",
                "selector_hint": ".product-price",
                "text_quote": "$399.50",
            },
        }
        errors = [e.message for e in Draft202012Validator(schema).iter_errors(base_finding)]
        assert errors == []

    def test_candidate_id_pattern_enforced(self, schema, base_finding):
        from jsonschema import Draft202012Validator
        base_finding["visual_evidence"] = {
            "type": "exact_element",
            "confidence": "high",
            "observed_anchor": {"candidate_id": "INVALID_FORMAT"},
        }
        errors = [e.message for e in Draft202012Validator(schema).iter_errors(base_finding)]
        assert any("INVALID_FORMAT" in e for e in errors)
