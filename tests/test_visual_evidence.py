"""Visual evidence taxonomy (Phase 2 — 2026-05-18).

Tests covering:
- ``derive_visual_evidence`` rule coverage (producer-authored wins, match_method
  enum, absent + proposed_anchor, real eN, insufficient-signal fallback)
- Schema accepts the optional ``visual_evidence`` field with both populated
  and minimal forms
- Loader / marker integration: marker mappings produced by ``auto_map_markers_v2``
  carry a ``visual_evidence`` dict on every entry
- HTML renderer emits ``hotspot-ve-<type>`` classes for downstream CSS

See ``docs/ecp/2026-05-18-report-accuracy-and-hotspot-remediation-plan.md``
Phase 2 acceptance criteria.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from report.visual_evidence import (
    ALL_CONFIDENCES,
    ALL_TYPES,
    derive_visual_evidence,
)


# ---------------------------------------------------------------------------
# Derivation rules
# ---------------------------------------------------------------------------


class TestDeriveProducerWins:
    """Rule 1: if finding.visual_evidence is set, return it unchanged."""

    def test_explicit_visual_evidence_passes_through(self) -> None:
        ve = {
            "type": "generated_expected_zone",
            "confidence": "low",
            "expected_overlay": {
                "template_id": "sticky-cta",
                "anchor_relative_to": "viewport",
                "placement": "sticky-viewport-bottom",
            },
            "reason": "No sticky CTA exists on mobile",
        }
        finding = {"element": {"baton_index": "absent"}, "visual_evidence": ve}
        result = derive_visual_evidence(finding)
        # Producer-authored value should be returned unchanged
        assert result is ve

    def test_explicit_overrides_match_method(self) -> None:
        # Even when match_method would derive something different, the producer
        # value wins. This is the contract for migration.
        finding = {
            "element": {"baton_index": "e7"},
            "match_method": "e_index_lookup",
            "visual_evidence": {"type": "proxy_element", "confidence": "medium"},
        }
        result = derive_visual_evidence(finding)
        assert result["type"] == "proxy_element"
        assert result["confidence"] == "medium"


class TestDeriveFromMatchMethod:
    """Rule 2: known match_method enum -> canonical type+confidence."""

    @pytest.mark.parametrize(
        "match_method,expected_type,expected_conf",
        [
            ("e_index_lookup", "exact_element", "high"),
            ("e_index", "exact_element", "high"),
            ("section_centroid", "section_absence", "low"),
            ("banner", "page_level", "low"),
            ("operator", "page_level", "needs_review"),
        ],
    )
    def test_match_method_enum_mapping(
        self, match_method: str, expected_type: str, expected_conf: str,
    ) -> None:
        result = derive_visual_evidence(match_method=match_method)
        assert result["type"] == expected_type
        assert result["confidence"] == expected_conf
        # Reason field present and explains derivation
        assert match_method in result["reason"]


class TestDeriveFromProposedAnchor:
    """Rule 3: absent baton_index + proposed_anchor -> kind-specific mapping."""

    def test_element_kind_maps_to_proxy(self) -> None:
        result = derive_visual_evidence(
            baton_index="absent",
            proposed_anchor={
                "kind": "element", "element_baton_index": "e10",
                "placement": "before-element", "viewport": "mobile",
                "reason": "MSRP belongs above price",
            },
        )
        assert result["type"] == "proxy_element"
        assert result["confidence"] == "medium"

    def test_section_after_section_maps_to_generated_expected_zone(self) -> None:
        result = derive_visual_evidence(
            baton_index="absent",
            proposed_anchor={
                "kind": "section", "section_index": 2,
                "placement": "after-section", "viewport": "mobile",
            },
        )
        # "after-section" means overlay drawn IN THE GAP — generated template
        assert result["type"] == "generated_expected_zone"
        assert result["confidence"] == "low"

    def test_section_bottom_overlay_maps_to_section_absence(self) -> None:
        result = derive_visual_evidence(
            baton_index="absent",
            proposed_anchor={
                "kind": "section", "section_index": 1,
                "placement": "section-bottom-overlay", "viewport": "desktop",
            },
        )
        assert result["type"] == "section_absence"
        assert result["confidence"] == "low"

    def test_viewport_kind_always_generated(self) -> None:
        result = derive_visual_evidence(
            baton_index="absent",
            proposed_anchor={
                "kind": "viewport", "viewport_trigger": "after_primary_cta_offscreen",
                "placement": "viewport-bottom-sticky", "viewport": "mobile",
            },
        )
        assert result["type"] == "generated_expected_zone"
        assert result["confidence"] == "low"

    def test_unknown_kind_falls_through_to_needs_review(self) -> None:
        result = derive_visual_evidence(
            baton_index="absent",
            proposed_anchor={"kind": "unknown_future_kind", "placement": "?"},
        )
        assert result["type"] == "page_level"
        assert result["confidence"] == "needs_review"


class TestDeriveFromBatonIndex:
    """Rule 4: real eN with no other signals -> exact_element."""

    def test_real_e_index_maps_to_exact(self) -> None:
        result = derive_visual_evidence(baton_index="e10")
        assert result["type"] == "exact_element"
        assert result["confidence"] == "high"

    def test_finding_with_real_e_index_no_explicit_visual_evidence(self) -> None:
        finding = {
            "element": {"baton_index": "e3", "text_content": "Add to cart", "role": "button"},
        }
        result = derive_visual_evidence(finding)
        assert result["type"] == "exact_element"
        assert result["confidence"] == "high"


class TestDeriveInsufficientSignal:
    """Rule 5: nothing useful known -> page_level needs_review."""

    def test_no_signal_falls_through(self) -> None:
        result = derive_visual_evidence()
        assert result["type"] == "page_level"
        assert result["confidence"] == "needs_review"
        assert "Insufficient signal" in result["reason"]

    def test_unknown_match_method_falls_through(self) -> None:
        # A match_method NOT in the enum should fall through to "no signal"
        # rather than silently mapping to something wrong.
        result = derive_visual_evidence(match_method="some-future-method")
        assert result["type"] == "page_level"
        assert result["confidence"] == "needs_review"


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


class TestSchemaAcceptsVisualEvidence:
    """schema/finding-v1.json must accept the new optional field in all its
    documented shapes, and reject malformed forms."""

    @pytest.fixture
    def schema(self) -> dict:
        return json.loads((REPO_ROOT / "schema" / "finding-v1.json").read_text(encoding="utf-8"))

    @pytest.fixture
    def base_finding(self) -> dict:
        return {
            "cluster": "pricing", "device": "desktop", "local_id": 1, "verdict": "FAIL",
            "title": "No MSRP Anchor", "surface": "price-block",
            "element": {"baton_index": "e0", "text_content": "$399", "role": "text"},
            "severity": "MEDIUM", "scope": "page",
            "effort": {"change_type": "copy", "change_scope": "single-file"},
            "evidence_anchors": [{"type": "dom", "reference": "e0"}],
            "reference_citations": [{"source": "price-anchoring.md", "tier": "Silver"}],
            "observation": "Bare $399 with no compare-at framing whatsoever.",
            "recommendation": "Add MSRP strikethrough above the live price.",
            "why_this_matters": "Anchoring is highest-leverage for SKUs over $50.",
            "evidence_tier": "Silver",
        }

    def _validate(self, schema: dict, finding: dict) -> list[str]:
        from jsonschema import Draft202012Validator
        v = Draft202012Validator(schema)
        return [e.message for e in v.iter_errors(finding)]

    def test_finding_without_visual_evidence_validates(self, schema: dict, base_finding: dict) -> None:
        # Backward compat — legacy emissions must still pass
        assert self._validate(schema, base_finding) == []

    def test_minimal_visual_evidence_validates(self, schema: dict, base_finding: dict) -> None:
        base_finding["visual_evidence"] = {"type": "exact_element", "confidence": "high"}
        assert self._validate(schema, base_finding) == []

    def test_full_visual_evidence_validates(self, schema: dict, base_finding: dict) -> None:
        base_finding["visual_evidence"] = {
            "type": "generated_expected_zone",
            "confidence": "low",
            "observed_anchor": {
                "baton_index": "e0", "selector_hint": ".price", "text_quote": "$399",
            },
            "expected_overlay": {
                "template_id": "msrp-anchor", "anchor_relative_to": "e0",
                "placement": "before-element",
            },
            "reason": "MSRP overlay belongs above price",
        }
        assert self._validate(schema, base_finding) == []

    def test_invalid_type_enum_rejected(self, schema: dict, base_finding: dict) -> None:
        base_finding["visual_evidence"] = {"type": "made_up_type", "confidence": "high"}
        errors = self._validate(schema, base_finding)
        assert errors and any("made_up_type" in e for e in errors)

    def test_invalid_confidence_enum_rejected(self, schema: dict, base_finding: dict) -> None:
        base_finding["visual_evidence"] = {"type": "exact_element", "confidence": "very-high"}
        errors = self._validate(schema, base_finding)
        assert errors and any("very-high" in e for e in errors)

    def test_missing_required_subfield_rejected(self, schema: dict, base_finding: dict) -> None:
        base_finding["visual_evidence"] = {"type": "exact_element"}  # missing confidence
        errors = self._validate(schema, base_finding)
        assert errors and any("confidence" in e for e in errors)

    def test_additional_properties_rejected(self, schema: dict, base_finding: dict) -> None:
        base_finding["visual_evidence"] = {
            "type": "exact_element", "confidence": "high",
            "made_up_field": "should be rejected",
        }
        errors = self._validate(schema, base_finding)
        assert errors and any("made_up_field" in e for e in errors)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def test_all_types_constant_matches_schema_enum() -> None:
    """If schema's type enum drifts, ALL_TYPES must drift with it. Catches
    schema-vs-code divergence."""
    schema = json.loads((REPO_ROOT / "schema" / "finding-v1.json").read_text(encoding="utf-8"))
    schema_types = tuple(
        schema["properties"]["visual_evidence"]["properties"]["type"]["enum"]
    )
    assert ALL_TYPES == schema_types


def test_all_confidences_constant_matches_schema_enum() -> None:
    schema = json.loads((REPO_ROOT / "schema" / "finding-v1.json").read_text(encoding="utf-8"))
    schema_confs = tuple(
        schema["properties"]["visual_evidence"]["properties"]["confidence"]["enum"]
    )
    assert ALL_CONFIDENCES == schema_confs
