"""v2 unit tests: synthesizer_parser v2 functions (Phase F.4).

Covers the v2 path: validate_synthesizer_emission_payload,
parse_synthesizer_emission_file, build_v2_retry_prompt. The v1 path
(parse_response, validate_stories) has its own coverage in test_v1.py and
is unchanged in Phase F.

Run:
    python -m unittest tests.test_v2_synthesizer_parser
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.synthesizer_parser import (  # noqa: E402
    SynthesizerEmission,
    SynthesizerValidationError,
    build_v2_retry_prompt,
    parse_synthesizer_emission_file,
    validate_synthesizer_emission_payload,
)


VALID_REFS = {
    "pricing F-01",
    "pricing F-02",
    "pricing F-03",
    "pricing F-04",
    "visual-cta F-01",
    "performance-ux F-04",
    "checkout-flows F-02",
    "trust-credibility F-03",
    "trust-credibility F-06",
    "content-seo F-02",
}


def _valid_emission(**overrides) -> dict:
    base = {
        "schema_version": 1,
        "engagement_id": "2026-04-27-aaaaaaaa",
        "synthesizer_model": {"family": "opus", "version": "4.6"},
        "started_at": "2026-04-27T18:02:14.000Z",
        "completed_at": "2026-04-27T18:06:53.000Z",
        "status": "complete",
        "dispatch_shape": "single",
        "degraded_mode": False,
        "audit_documents": {
            "desktop": "docs/ecp/2026-04-27-aaaaaaaa/audit-desktop.md",
            "mobile": "docs/ecp/2026-04-27-aaaaaaaa/audit-mobile.md",
        },
        "priority_path": [
            {
                "mode": "bundle",
                "title": "Restore Anchor and Decision Confidence to the Price Block",
                "severity": "HIGH",
                "narrative": (
                    "The price block on this page renders $69.95 as a standalone "
                    "number. There is no MSRP strikethrough, no Affirm widget. "
                    "The fix is concentration, not invention."
                ),
                "f_refs": ["pricing F-01", "pricing F-02"],
            },
            {
                "mode": "severity",
                "title": "Sticky Mobile CTA Architecture Gap",
                "severity": "HIGH",
                "narrative": (
                    "Four cluster specialists independently flagged that the Add to "
                    "Cart button is offscreen for the bottom of the mobile page with "
                    "no persistent replacement. The convergence is the signal."
                ),
                "f_refs": [
                    "visual-cta F-01",
                    "performance-ux F-04",
                    "checkout-flows F-02",
                ],
            },
            {
                "mode": "quick-wins",
                "title": "Three Copy Changes That Pay Back the Same Day",
                "severity": "MEDIUM",
                "narrative": (
                    "Three high-confidence quick-win findings resolve inside a "
                    "single theme template edit. Affirm widget below price, "
                    "free-shipping line near ATC, price-match tooltip."
                ),
                "f_refs": ["pricing F-02", "pricing F-03", "pricing F-04"],
            },
        ],
        "quick_wins_manifest": [
            "pricing F-02",
            "pricing F-03",
            "pricing F-04",
        ],
        "severity_manifest": ["visual-cta F-01", "pricing F-01"],
        "scope_page_synchronized_refs": [
            "pricing F-01",
            "pricing F-02",
            "visual-cta F-01",
        ],
    }
    base.update(overrides)
    return base


class TestValidateHappyPath(unittest.TestCase):
    def test_valid_emission_passes(self):
        validate_synthesizer_emission_payload(_valid_emission(), VALID_REFS)

    def test_per_device_with_lead_reflection(self):
        validate_synthesizer_emission_payload(
            _valid_emission(
                dispatch_shape="per-device",
                degraded_mode=True,
                status="partial",
            ),
            VALID_REFS,
        )

    def test_failed_synthesis_drift_with_lead_reflection(self):
        validate_synthesizer_emission_payload(
            _valid_emission(
                dispatch_shape="per-device",
                degraded_mode=True,
                status="failed_synthesis_drift",
                lead_reflection_path="docs/ecp/2026-04-27-aaaaaaaa/lead-reflection.md",
            ),
            VALID_REFS,
        )


class TestSchemaErrors(unittest.TestCase):
    def test_missing_required_field(self):
        e = _valid_emission()
        del e["priority_path"]
        with self.assertRaises(SynthesizerValidationError) as ctx:
            validate_synthesizer_emission_payload(e, VALID_REFS)
        self.assertTrue(any("priority_path" in path or "priority_path" in msg
                            for path, msg in ctx.exception.schema_errors))

    def test_too_few_priority_path_stories(self):
        e = _valid_emission(priority_path=_valid_emission()["priority_path"][:2])
        with self.assertRaises(SynthesizerValidationError):
            validate_synthesizer_emission_payload(e, VALID_REFS)

    def test_too_many_priority_path_stories(self):
        story = _valid_emission()["priority_path"][0]
        e = _valid_emission(priority_path=[story] * 6)
        with self.assertRaises(SynthesizerValidationError):
            validate_synthesizer_emission_payload(e, VALID_REFS)

    def test_invalid_dispatch_shape(self):
        e = _valid_emission(dispatch_shape="hybrid")
        with self.assertRaises(SynthesizerValidationError):
            validate_synthesizer_emission_payload(e, VALID_REFS)

    def test_degraded_mode_disagreement_with_dispatch_shape(self):
        e = _valid_emission(dispatch_shape="single", degraded_mode=True)
        with self.assertRaises(SynthesizerValidationError):
            validate_synthesizer_emission_payload(e, VALID_REFS)

    def test_per_device_requires_degraded_mode_true(self):
        e = _valid_emission(dispatch_shape="per-device", degraded_mode=False)
        with self.assertRaises(SynthesizerValidationError):
            validate_synthesizer_emission_payload(e, VALID_REFS)

    def test_failed_synthesis_drift_requires_lead_reflection_path(self):
        e = _valid_emission(
            dispatch_shape="per-device",
            degraded_mode=True,
            status="failed_synthesis_drift",
        )  # no lead_reflection_path
        with self.assertRaises(SynthesizerValidationError):
            validate_synthesizer_emission_payload(e, VALID_REFS)

    def test_invalid_f_ref_format(self):
        e = _valid_emission()
        e["priority_path"][0]["f_refs"] = ["pricing-F-01"]  # missing space
        with self.assertRaises(SynthesizerValidationError):
            validate_synthesizer_emission_payload(e, VALID_REFS)

    def test_bad_engagement_id_pattern(self):
        e = _valid_emission(engagement_id="not-an-engagement-id")
        with self.assertRaises(SynthesizerValidationError):
            validate_synthesizer_emission_payload(e, VALID_REFS)


class TestAllowlistCheck(unittest.TestCase):
    def test_hallucinated_priority_path_ref(self):
        e = _valid_emission()
        e["priority_path"][0]["f_refs"] = ["pricing F-01", "pricing F-99"]
        with self.assertRaises(SynthesizerValidationError) as ctx:
            validate_synthesizer_emission_payload(e, VALID_REFS)
        # Schema-level F-NN format passes; allowlist catches hallucination.
        self.assertEqual(len(ctx.exception.schema_errors), 0)
        self.assertTrue(
            any(ref == "pricing F-99" for _, ref in ctx.exception.hallucinated_refs)
        )

    def test_hallucinated_quick_wins_manifest_ref(self):
        e = _valid_emission(quick_wins_manifest=["pricing F-02", "pricing F-77"])
        with self.assertRaises(SynthesizerValidationError) as ctx:
            validate_synthesizer_emission_payload(e, VALID_REFS)
        self.assertTrue(
            any("pricing F-77" == ref for _, ref in ctx.exception.hallucinated_refs)
        )

    def test_hallucinated_severity_manifest_ref(self):
        e = _valid_emission(severity_manifest=["visual-cta F-44"])
        with self.assertRaises(SynthesizerValidationError) as ctx:
            validate_synthesizer_emission_payload(e, VALID_REFS)
        self.assertTrue(
            any("visual-cta F-44" == ref for _, ref in ctx.exception.hallucinated_refs)
        )

    def test_hallucinated_scope_page_ref(self):
        e = _valid_emission(scope_page_synchronized_refs=["pricing F-01", "ghost F-05"])
        with self.assertRaises(SynthesizerValidationError) as ctx:
            validate_synthesizer_emission_payload(e, VALID_REFS)
        self.assertTrue(
            any("ghost F-05" == ref for _, ref in ctx.exception.hallucinated_refs)
        )


class TestParseFile(unittest.TestCase):
    def test_round_trip_happy_path(self):
        payload = _valid_emission()
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "synthesizer-emission.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            parsed = parse_synthesizer_emission_file(path, VALID_REFS)
        self.assertIsInstance(parsed, SynthesizerEmission)
        self.assertEqual(parsed.engagement_id, "2026-04-27-aaaaaaaa")
        self.assertEqual(parsed.dispatch_shape, "single")
        self.assertFalse(parsed.degraded_mode)
        self.assertEqual(len(parsed.priority_path), 3)
        self.assertEqual(len(parsed.scope_page_synchronized_refs), 3)

    def test_parse_propagates_validation_error(self):
        payload = _valid_emission(engagement_id="bad")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "synthesizer-emission.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(SynthesizerValidationError):
                parse_synthesizer_emission_file(path, VALID_REFS)


class TestRetryPromptConstruction(unittest.TestCase):
    def test_retry_prompt_cites_schema_errors(self):
        e = _valid_emission()
        del e["priority_path"]
        try:
            validate_synthesizer_emission_payload(e, VALID_REFS)
            self.fail("expected SynthesizerValidationError")
        except SynthesizerValidationError as err:
            prompt = build_v2_retry_prompt(
                "docs/ecp/x/synthesizer-emission.json", err, valid_refs=VALID_REFS
            )
        self.assertIn("Schema errors:", prompt)
        self.assertIn("schema/synthesizer-emission-v1.json", prompt)

    def test_retry_prompt_cites_hallucinated_refs(self):
        e = _valid_emission()
        e["priority_path"][0]["f_refs"] = ["pricing F-99"] * 2
        try:
            validate_synthesizer_emission_payload(e, VALID_REFS)
            self.fail("expected SynthesizerValidationError")
        except SynthesizerValidationError as err:
            prompt = build_v2_retry_prompt(
                "docs/ecp/x/synthesizer-emission.json", err, valid_refs=VALID_REFS
            )
        self.assertIn("Hallucinated f_refs", prompt)
        self.assertIn("pricing F-99", prompt)
        self.assertIn("Sample of valid f_refs", prompt)


if __name__ == "__main__":
    unittest.main()
