"""v2 unit tests: json_parser.parse_emission_file + retry prompt construction.

Run:
    python -m unittest tests.test_v2_json_parser

Phase E.2 deliverable. Verifies the schema-validation-then-Finding-build path.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.json_parser import (  # noqa: E402
    EmissionValidationError,
    build_retry_prompt,
    parse_emission_file,
    validate_emission_payload,
)


def _valid_emission(**overrides) -> dict:
    base = {
        "schema_version": 1,
        "engagement_id": "2026-04-27-aaaaaaaa",
        "cluster": "pricing",
        "device": "mobile",
        "specialist_model": {"family": "sonnet", "version": "4.6"},
        "started_at": "2026-04-27T16:14:02.000Z",
        "completed_at": "2026-04-27T16:15:38.000Z",
        "status": "complete",
        "findings": [
            {
                "cluster": "pricing",
                "device": "mobile",
                "local_id": 1,
                "verdict": "FAIL",
                "title": "No MSRP Anchor",
                "surface": "price-block",
                "element": {"baton_index": "e7", "text_content": "$69.95", "role": "div"},
                "severity": "HIGH",
                "scope": "page",
                "effort": {"change_type": "copy", "change_scope": "single-file"},
                "confidence": 0.85,
                "evidence_anchors": [
                    {
                        "type": "visual",
                        "reference": "section-2-mobile.jpg",
                        "scroll_y": 480,
                        "viewport": "mobile",
                    }
                ],
                "reference_citations": [
                    {"source": "price-anchoring.md", "section": "msrp", "tier": "Silver"}
                ],
                "observation": "Price has no anchor and reads expensive.",
                "recommendation": "Add an MSRP strikethrough above the live price.",
                "why_this_matters": "Anchoring is the highest-leverage pricing pattern.",
                "evidence_tier": "Silver",
            }
        ],
    }
    base.update(overrides)
    return base


class TestParseEmissionFile(unittest.TestCase):
    def test_parses_valid_emission(self):
        emission = _valid_emission()
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(emission, f)
            tmp_path = Path(f.name)
        try:
            result = parse_emission_file(tmp_path)
            self.assertEqual(result.cluster, "pricing")
            self.assertEqual(result.device, "mobile")
            self.assertEqual(result.status, "complete")
            self.assertEqual(len(result.findings), 1)
            f0 = result.findings[0]
            self.assertEqual(f0.baton_index, "e7")
            self.assertEqual(f0.scope, "page")
            self.assertEqual(f0.change_type, "copy")
            self.assertEqual(f0.change_scope, "single-file")
            self.assertEqual(f0.tier, "Silver")
            self.assertAlmostEqual(f0.confidence, 0.85)
            self.assertEqual(len(f0.evidence_anchors), 1)
            self.assertEqual(f0.evidence_anchors[0].scroll_y, 480)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_raises_on_missing_required_field(self):
        emission = _valid_emission()
        del emission["engagement_id"]
        with self.assertRaises(EmissionValidationError) as ctx:
            validate_emission_payload(emission, source_path="<test>")
        self.assertIn("engagement_id", str(ctx.exception))

    def test_raises_on_bad_enum_value(self):
        emission = _valid_emission()
        emission["findings"][0]["severity"] = "URGENT"  # not in enum
        with self.assertRaises(EmissionValidationError) as ctx:
            validate_emission_payload(emission, source_path="<test>")
        self.assertIn("URGENT", str(ctx.exception))

    def test_raises_on_evidence_tier_promotion_violation(self):
        # Schema's allOf rule: any Gold citation forces evidence_tier=Gold.
        # Declaring Silver while citing Gold should fail validation.
        emission = _valid_emission()
        emission["findings"][0]["reference_citations"][0]["tier"] = "Gold"
        emission["findings"][0]["evidence_tier"] = "Silver"  # contradicts the Gold citation
        with self.assertRaises(EmissionValidationError):
            validate_emission_payload(emission, source_path="<test>")

    def test_status_skipped_with_reason(self):
        emission = _valid_emission(
            status="skipped",
            skip_reason="No pricing surface routed",
            findings=[],
        )
        # Should validate cleanly — schema's allOf accepts skipped + empty findings + skip_reason
        validate_emission_payload(emission, source_path="<test>")


class TestRetryPromptConstruction(unittest.TestCase):
    def test_retry_prompt_cites_best_error_and_lists_all(self):
        emission = _valid_emission()
        del emission["engagement_id"]
        emission["findings"][0]["severity"] = "URGENT"
        try:
            validate_emission_payload(emission, source_path="<test>")
            self.fail("Expected validation error")
        except EmissionValidationError as e:
            prompt = build_retry_prompt("<test>", "pricing", "mobile", e)
            self.assertIn("schema validation", prompt)
            self.assertIn("All errors:", prompt)
            self.assertIn("Re-emit a single JSON object", prompt)
            self.assertIn("No prose, no markdown fences", prompt)


if __name__ == "__main__":
    unittest.main()
