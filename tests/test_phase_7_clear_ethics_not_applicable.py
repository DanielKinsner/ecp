"""Phase 7 — CLEAR ethics findings use change_type/change_scope = not_applicable
(2026-05-18).

Closes Codex Q7 from the original 13-question review. Pre-Phase-7, the
schema accepted ``change_type: "copy"`` on CLEAR ethics findings because
nothing else fit — the lead had to inline-patch 5 such findings on the
awdmods 2026-05-18 run after the specialist emitted ``change_type: "none"``
(not even a schema-valid value). Phase 7 adds an explicit
``not_applicable`` enum value and a conditional rule that ties it to
CLEAR ethics findings symmetrically (CLEAR MUST use it; everything else
MUST NOT).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

SCHEMA = json.loads((REPO_ROOT / "schema" / "finding-v1.json").read_text(encoding="utf-8"))


def _clear_ethics_finding(*, effort: dict | None = None) -> dict:
    return {
        "cluster": "ethics", "device": "page", "local_id": 1, "verdict": "PASS",
        "ethics_state": "CLEAR",
        "title": "No countdown timer or fabricated urgency",
        "surface": "scarcity-marker",
        "element": {"baton_index": "absent"},
        "severity": "LOW", "scope": "page",
        "effort": effort or {
            "change_type": "not_applicable", "change_scope": "not_applicable",
        },
        "confidence": 0.95,
        "proposed_anchor": {
            "kind": "viewport", "viewport_trigger": "before_first_scroll",
            "placement": "viewport-bottom-sticky", "viewport": "desktop",
            "reason": "absence-confirmed page-global check",
        },
        "evidence_anchors": [],
        "reference_citations": [],
        "observation": "No countdown or urgency timer elements detected.",
        "recommendation": "Maintain absence of fabricated urgency.",
        "why_this_matters": "Fabricated scarcity violates FTC Act § 5 deception standards.",
        "evidence_tier": "Bronze",
    }


def _adjacent_ethics_finding(*, effort: dict | None = None) -> dict:
    return {
        "cluster": "ethics", "device": "page", "local_id": 1, "verdict": "FAIL",
        "ethics_state": "ADJACENT",
        "source_url": "https://www.ftc.gov/legal-library/browse/rules/guides-against-deceptive-pricing-16-cfr-part-233",
        "title": "Compare-At Price Unverifiable",
        "surface": "msrp-anchor",
        "element": {
            "baton_index": "e0", "text_content": "$469.50", "role": "text",
        },
        "severity": "MEDIUM", "scope": "page",
        "effort": effort or {
            "change_type": "copy", "change_scope": "single-file",
        },
        "confidence": 0.85,
        "evidence_anchors": [{"type": "dom", "reference": "e0"}],
        "reference_citations": [
            {"source": "ethics-gate.md", "section": "ftc-pricing", "tier": "Gold"}
        ],
        "observation": "Strikethrough $469.50 compare-at price needs documented prior-selling-price evidence under FTC 16 CFR 233.1.",
        "recommendation": "Provide pricing records demonstrating the $469.50 was a bona fide prior selling price.",
        "why_this_matters": "Unsupported reference prices are deceptive under FTC Act § 5.",
        "evidence_tier": "Gold",
    }


def _pricing_fail_finding(*, effort: dict | None = None) -> dict:
    return {
        "cluster": "pricing", "device": "desktop", "local_id": 1, "verdict": "FAIL",
        "title": "No MSRP anchor on price block",
        "surface": "price-block",
        "element": {
            "baton_index": "e10", "text_content": "$199.99", "role": "text",
        },
        "severity": "MEDIUM", "scope": "page",
        "effort": effort or {
            "change_type": "copy", "change_scope": "single-file",
        },
        "evidence_anchors": [{"type": "dom", "reference": "e10"}],
        "reference_citations": [{"source": "price-anchoring.md", "tier": "Silver"}],
        "observation": "Bare $199.99 with no compare-at framing or MSRP strikethrough whatsoever.",
        "recommendation": "Render the MSRP as a strikethrough above the live price for visual anchoring.",
        "why_this_matters": "Anchoring is the single highest-leverage pricing pattern for SKUs over $50.",
        "evidence_tier": "Silver",
    }


def _errs(finding: dict) -> list[str]:
    return [e.message for e in Draft202012Validator(SCHEMA).iter_errors(finding)]


# ---------------------------------------------------------------------------
# CLEAR ethics MUST use not_applicable
# ---------------------------------------------------------------------------


class TestClearEthicsRequiresNotApplicable:
    def test_clear_with_not_applicable_validates(self):
        errs = _errs(_clear_ethics_finding())
        assert errs == []

    def test_clear_with_copy_single_file_is_rejected(self):
        """Pre-Phase-7 this was the only way to ship CLEAR findings (the
        lead had to patch the specialist's invalid `change_type: "none"`
        to `copy` on the awdmods 2026-05-18 run). Post-Phase-7 it fails
        schema validation, forcing the specialist to emit not_applicable."""
        errs = _errs(_clear_ethics_finding(effort={
            "change_type": "copy", "change_scope": "single-file",
        }))
        assert errs, "CLEAR ethics with change_type=copy must be rejected"

    def test_clear_with_html_attr_single_file_is_rejected(self):
        errs = _errs(_clear_ethics_finding(effort={
            "change_type": "html-attr", "change_scope": "single-file",
        }))
        assert errs

    def test_clear_with_mixed_not_applicable_and_normal_is_rejected(self):
        """Both fields must be not_applicable — partial use is rejected
        so the contract reads as a single semantic decision per finding."""
        errs = _errs(_clear_ethics_finding(effort={
            "change_type": "not_applicable", "change_scope": "single-file",
        }))
        assert errs

        errs2 = _errs(_clear_ethics_finding(effort={
            "change_type": "copy", "change_scope": "not_applicable",
        }))
        assert errs2


# ---------------------------------------------------------------------------
# Non-CLEAR findings MUST NOT use not_applicable
# ---------------------------------------------------------------------------


class TestNonClearRejectsNotApplicable:
    def test_adjacent_ethics_with_not_applicable_is_rejected(self):
        """ADJACENT/BLOCK ethics findings have a real change to ship —
        the operator must update pricing records, change a URL, etc.
        not_applicable misrepresents that."""
        errs = _errs(_adjacent_ethics_finding(effort={
            "change_type": "not_applicable", "change_scope": "not_applicable",
        }))
        assert errs, "ADJACENT ethics with not_applicable must be rejected"

    def test_pricing_fail_with_not_applicable_is_rejected(self):
        errs = _errs(_pricing_fail_finding(effort={
            "change_type": "not_applicable", "change_scope": "not_applicable",
        }))
        assert errs, "pricing FAIL with not_applicable must be rejected"

    def test_pricing_fail_with_copy_validates_unchanged(self):
        """Sanity: the new conditional rules don't reject normal
        non-ethics findings that use the original enum values."""
        errs = _errs(_pricing_fail_finding())
        assert errs == []

    def test_adjacent_ethics_with_copy_validates_unchanged(self):
        """Sanity: ADJACENT ethics with copy/single-file still validates."""
        errs = _errs(_adjacent_ethics_finding())
        assert errs == []


# ---------------------------------------------------------------------------
# Enum extension itself
# ---------------------------------------------------------------------------


class TestEnumExtension:
    def test_change_type_enum_contains_not_applicable(self):
        enum = SCHEMA["properties"]["effort"]["properties"]["change_type"]["enum"]
        assert "not_applicable" in enum
        # Pre-existing values must still be present (no removal)
        for required in ("copy", "css", "html-attr", "component", "feature"):
            assert required in enum

    def test_change_scope_enum_contains_not_applicable(self):
        enum = SCHEMA["properties"]["effort"]["properties"]["change_scope"]["enum"]
        assert "not_applicable" in enum
        for required in ("single-file", "component", "cross-cutting"):
            assert required in enum
