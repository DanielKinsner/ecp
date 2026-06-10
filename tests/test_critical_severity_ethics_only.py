"""severity=CRITICAL is reserved for ethics findings (M3, 2026-06-10).

contracts/ethics-subagent-v2.md (~32, ~154-156) and
contracts/specialist-prompt-v2.md (~150) state cluster specialists never
emit ``severity: "CRITICAL"`` — but pre-M3 the schema's severity enum was
flat, so a pricing specialist could emit CRITICAL and inflate Priority
Path weighting without failing validation. This test pins the new
``allOf`` rule that ties CRITICAL to cluster='ethics'.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

SCHEMA = json.loads((REPO_ROOT / "schema" / "finding-v1.json").read_text(encoding="utf-8"))


def _ethics_block_finding(*, severity: str = "CRITICAL") -> dict:
    return {
        "cluster": "ethics", "device": "page", "local_id": 1, "verdict": "FAIL",
        "ethics_state": "BLOCK",
        "source_url": "https://www.ftc.gov/legal-library/browse/rules/guides-against-deceptive-pricing-16-cfr-part-233",
        "title": "Fabricated countdown timer on PDP",
        "surface": "scarcity-marker",
        "element": {
            "baton_index": "e7", "text_content": "Only 2 left!", "role": "text",
        },
        "severity": severity, "scope": "page",
        "effort": {"change_type": "component", "change_scope": "component"},
        "confidence": 0.9,
        "evidence_anchors": [{"type": "dom", "reference": "e7"}],
        "reference_citations": [
            {"source": "ethics-gate.md", "section": "ftc-deception", "tier": "Gold"}
        ],
        "observation": "Countdown timer resets on every page reload with no inventory backing; fabricated urgency under FTC Act § 5.",
        "recommendation": "Remove the countdown timer or wire it to a real inventory signal with documented reset rules.",
        "why_this_matters": "Fabricated scarcity violates FTC Act § 5 deception standards and is enforceable.",
        "evidence_tier": "Gold",
    }


def _pricing_fail_finding(*, severity: str = "HIGH") -> dict:
    return {
        "cluster": "pricing", "device": "desktop", "local_id": 1, "verdict": "FAIL",
        "title": "No MSRP anchor on price block",
        "surface": "price-block",
        "element": {
            "baton_index": "e10", "text_content": "$199.99", "role": "text",
        },
        "severity": severity, "scope": "page",
        "effort": {"change_type": "copy", "change_scope": "single-file"},
        "evidence_anchors": [{"type": "dom", "reference": "e10"}],
        "reference_citations": [{"source": "price-anchoring.md", "tier": "Silver"}],
        "observation": "Bare $199.99 with no compare-at framing or MSRP strikethrough whatsoever.",
        "recommendation": "Render the MSRP as a strikethrough above the live price for visual anchoring.",
        "why_this_matters": "Anchoring is the single highest-leverage pricing pattern for SKUs over $50.",
        "evidence_tier": "Silver",
    }


def _visual_cta_fail_finding(*, severity: str = "HIGH") -> dict:
    return {
        "cluster": "visual-cta", "device": "mobile", "local_id": 1, "verdict": "FAIL",
        "title": "ATC button blends into card background",
        "surface": "primary-cta",
        "element": {
            "baton_index": "e47", "text_content": "Add to Cart", "role": "button",
        },
        "severity": severity, "scope": "device",
        "effort": {"change_type": "css", "change_scope": "single-file"},
        "evidence_anchors": [{"type": "dom", "reference": "e47"}],
        "reference_citations": [
            {"source": "cta-design.md", "section": "primary-action-contrast", "tier": "Silver"}
        ],
        "observation": "Add to Cart button uses mid-grey fill matching three other interactive elements within the same viewport.",
        "recommendation": "Apply the brand accent color to the Add to Cart button background and reserve it for purchase actions.",
        "why_this_matters": "On mobile PDPs the ATC button is the only conversion action; without visual primacy it costs more attention.",
        "evidence_tier": "Silver",
    }


def _errs(finding: dict) -> list[str]:
    return [e.message for e in Draft202012Validator(SCHEMA).iter_errors(finding)]


# ---------------------------------------------------------------------------
# Ethics CRITICAL validates
# ---------------------------------------------------------------------------


class TestEthicsCriticalValidates:
    def test_ethics_block_critical_validates(self):
        errs = _errs(_ethics_block_finding(severity="CRITICAL"))
        assert errs == [], f"ethics BLOCK CRITICAL should validate; got: {errs}"

    def test_ethics_block_high_validates(self):
        # Jurisdiction-narrow ethics rules may downshift to HIGH per contract.
        errs = _errs(_ethics_block_finding(severity="HIGH"))
        assert errs == []


# ---------------------------------------------------------------------------
# Non-ethics CRITICAL is rejected
# ---------------------------------------------------------------------------


class TestNonEthicsCriticalRejected:
    def test_pricing_critical_is_rejected(self):
        """The premise of M3: a pricing specialist emitting CRITICAL would
        pre-M3 pass schema validation and inflate Priority Path weighting."""
        errs = _errs(_pricing_fail_finding(severity="CRITICAL"))
        assert errs, "pricing CRITICAL must be rejected"

    def test_visual_cta_critical_is_rejected(self):
        errs = _errs(_visual_cta_fail_finding(severity="CRITICAL"))
        assert errs, "visual-cta CRITICAL must be rejected"

    def test_pricing_high_validates_unchanged(self):
        """Sanity: the new rule does not affect non-ethics findings using
        HIGH/MEDIUM/LOW."""
        errs = _errs(_pricing_fail_finding(severity="HIGH"))
        assert errs == []

    def test_visual_cta_medium_validates_unchanged(self):
        errs = _errs(_visual_cta_fail_finding(severity="MEDIUM"))
        assert errs == []
