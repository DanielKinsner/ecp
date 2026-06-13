"""hc-C4 (ruling A7, 2026-06-10) — normalize verb + consistency canary.

The narrow, logged, mechanical-only normalize tier between autofix and
re-dispatch (sanctioned in skills/audit/SKILL.md +
contracts/dispatch-contract.md) is safe ONLY when the trail is
diff-auditable. Two halves wired here:

1. **Write chokepoint** — ``scripts/test-specialist.py normalize`` is
   the ONLY supported writer; it enforces the
   schema/placement-only field allowlist in code (a prose field
   like ``observation`` is refused with exit 2, distinct from a
   generic validation failure at exit 1).

2. **Consistency canary** —
   ``assembly.canary_checks.check_lead_normalizations_consistent``
   asserts every recorded ``after`` value still equals the
   emission's current value at that field, so a later un-trailed
   edit breaks the trail and fails the canary.

unittest-style for ``python -m unittest discover`` runner compatibility;
the same classes are picked up by ``python -m pytest tests/`` because
unittest classes inherit Test* discovery in pytest too.

Run:
    python -m pytest tests/test_normalizations_canary.py -v
    python -m unittest tests.test_normalizations_canary
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.canary_checks import check_lead_normalizations_consistent  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures: minimal valid cluster emission + helper to write it to a path
# ---------------------------------------------------------------------------


def _make_finding(local_id: int = 1, **overrides) -> dict:
    base = {
        "cluster": "trust-credibility",
        "device": "desktop",
        "local_id": local_id,
        "verdict": "FAIL",
        "title": f"Finding {local_id}",
        "surface": "primary-content-block",
        "element": {"baton_index": "e7", "text_content": "x", "role": "div"},
        "severity": "MEDIUM",
        "scope": "device",
        "effort": {"change_type": "copy", "change_scope": "single-file"},
        "confidence": 0.9,
        "evidence_anchors": [
            {"type": "dom", "reference": "e7"},
        ],
        "reference_citations": [
            {"source": "trust-credibility.md", "tier": "Silver"},
        ],
        "observation": "Observation prose long enough to clear the schema's minLength requirement.",
        "recommendation": "Recommendation prose long enough to clear the schema's minLength requirement.",
        "why_this_matters": "Why-this-matters prose long enough to clear the schema's minLength requirement.",
        "evidence_tier": "Silver",
    }
    base.update(overrides)
    return base


def _make_emission(findings: list[dict] | None = None, **overrides) -> dict:
    base = {
        "schema_version": 1,
        "engagement_id": "2026-06-10-deadbeef",
        "cluster": "trust-credibility",
        "device": "desktop",
        "specialist_model": {"family": "sonnet", "version": "4.6"},
        "started_at": "2026-06-10T00:00:00.000Z",
        "completed_at": "2026-06-10T00:00:01.000Z",
        "status": "complete",
        "findings": findings if findings is not None else [_make_finding()],
    }
    base.update(overrides)
    return base


def _run_normalize(*args: str) -> subprocess.CompletedProcess:
    """Invoke ``scripts/test-specialist.py normalize`` as a subprocess.

    Subprocess (rather than importing main()) so the CLI's exit codes
    and stderr surface exactly as a real lead invocation would see
    them — this is the contract the consistency canary banks on.
    """
    return subprocess.run(
        [sys.executable, str(_REPO / "scripts" / "test-specialist.py"), "normalize", *args],
        capture_output=True,
        text=True,
        env={"PYTHONIOENCODING": "utf-8", **__import__("os").environ},
    )


# ---------------------------------------------------------------------------
# CLI: normalize verb writes sidecar + re-validates + refuses prose fields
# ---------------------------------------------------------------------------


class TestNormalizeVerbWritesSidecar(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.eng = Path(self.tmp.name)
        self.emission_path = self.eng / "cluster-trust-credibility-desktop.json"

    def tearDown(self):
        self.tmp.cleanup()

    def _write_emission(self, emission: dict) -> None:
        self.emission_path.write_text(json.dumps(emission, indent=2), encoding="utf-8")

    def test_writes_sidecar_and_revalidates(self):
        """normalize edit on a schema field writes <emission>.normalizations.json
        with the {finding_local_id, field, before, after, reason, applied_at}
        shape AND the post-edit emission re-validates clean."""
        self._write_emission(_make_emission())
        result = _run_normalize(
            "--emission-path", str(self.emission_path),
            "--field", "surface",
            "--new-value", "purchase-zone",
            "--finding-local-id", "1",
            "--reason", "specialist emitted out-of-vocab surface; corrected to closest baton section",
            "--in-place",
        )
        self.assertEqual(
            result.returncode, 0,
            f"normalize should succeed; stderr=\n{result.stderr}",
        )
        trail_path = self.eng / "cluster-trust-credibility-desktop.normalizations.json"
        self.assertTrue(trail_path.exists(), "sidecar should be written")
        trail = json.loads(trail_path.read_text(encoding="utf-8"))
        self.assertEqual(trail["normalizations_count"], 1)
        entry = trail["normalizations"][0]
        # Required record keys per the SKILL.md contract.
        for key in ("finding_local_id", "field", "before", "after", "reason", "applied_at"):
            self.assertIn(key, entry, f"trail entry missing required key {key!r}")
        self.assertEqual(entry["finding_local_id"], 1)
        self.assertEqual(entry["field"], "surface")
        self.assertEqual(entry["before"], "primary-content-block")
        self.assertEqual(entry["after"], "purchase-zone")
        # applied_at must be an ISO-8601-Z UTC stamp (the same shape every
        # other state-stamping module uses).
        self.assertTrue(
            re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", entry["applied_at"]),
            f"applied_at must be ISO-8601-Z; got {entry['applied_at']!r}",
        )
        # The emission was edited in place.
        edited = json.loads(self.emission_path.read_text(encoding="utf-8"))
        self.assertEqual(edited["findings"][0]["surface"], "purchase-zone")

    def test_refuses_prose_field_with_exit_2(self):
        """Refusing exit code is distinct from a schema-validation failure
        (exit 1) so the lead's wrapper can tell the difference."""
        self._write_emission(_make_emission())
        for prose_field in ("observation", "recommendation", "why_this_matters", "title"):
            with self.subTest(field=prose_field):
                result = _run_normalize(
                    "--emission-path", str(self.emission_path),
                    "--field", prose_field,
                    "--new-value", "lead-rewritten-prose",
                    "--finding-local-id", "1",
                    "--reason", "test",
                    "--in-place",
                )
                self.assertEqual(
                    result.returncode, 2,
                    f"prose field {prose_field!r} must be refused with exit 2; "
                    f"got {result.returncode}\nstderr={result.stderr}",
                )
                self.assertIn("REFUSE", result.stderr)
                # And the emission must not have been edited.
                still = json.loads(self.emission_path.read_text(encoding="utf-8"))
                self.assertNotEqual(
                    still["findings"][0].get(prose_field),
                    "lead-rewritten-prose",
                    f"refused normalize must not have written {prose_field!r}",
                )

    def test_revalidates_business_rules_before_writing(self):
        self._write_emission(_make_emission())
        baton_path = self.eng / "baton.json"
        baton_path.write_text(
            json.dumps({"elements": [{"e_index": "e7"}]}),
            encoding="utf-8",
        )
        before = self.emission_path.read_text(encoding="utf-8")

        result = _run_normalize(
            "--emission-path", str(self.emission_path),
            "--field", "element.baton_index",
            "--new-value", "e999",
            "--finding-local-id", "1",
            "--reason", "probe fabricated baton index",
            "--baton-path", str(baton_path),
            "--in-place",
        )

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("BUSINESS", result.stderr)
        self.assertIn("baton_index_resolves", result.stderr)
        self.assertEqual(self.emission_path.read_text(encoding="utf-8"), before)
        self.assertFalse(
            (self.eng / "cluster-trust-credibility-desktop.normalizations.json").exists()
        )

    def test_refuses_proposed_anchor_reason_prose(self):
        """proposed_anchor.reason is operator-tooltip prose (schema 200-char
        cap; renderer MUST NOT parse it). It's prose-class and must be
        refused even though its parent block is in the allowlist."""
        finding = _make_finding(local_id=1)
        finding["element"]["baton_index"] = "absent"
        finding["proposed_anchor"] = {
            "kind": "section",
            "section_index": 0,
            "placement": "section-bottom-overlay",
            "viewport": "desktop",
            "reason": "operator-authored tooltip",
        }
        self._write_emission(_make_emission([finding]))
        result = _run_normalize(
            "--emission-path", str(self.emission_path),
            "--field", "proposed_anchor.reason",
            "--new-value", "lead-rewritten-tooltip",
            "--finding-local-id", "1",
            "--reason", "test",
            "--in-place",
        )
        self.assertEqual(result.returncode, 2, f"stderr={result.stderr}")

    def test_unknown_field_refused(self):
        """A field that's neither in the allowlist nor the explicit prose
        list (e.g., a typo or a hallucinated new field) is also refused
        with exit 2."""
        self._write_emission(_make_emission())
        result = _run_normalize(
            "--emission-path", str(self.emission_path),
            "--field", "made_up_field",
            "--new-value", "x",
            "--finding-local-id", "1",
            "--reason", "test",
            "--in-place",
        )
        self.assertEqual(result.returncode, 2, f"stderr={result.stderr}")

    def test_normalize_that_breaks_schema_fails_with_exit_1(self):
        """A normalize that lands on an allowlisted field but produces a
        schema-invalid emission MUST exit 1 (validation failure) — NOT
        write the trail. The lead's wrapper picks up the failure and
        backs out."""
        self._write_emission(_make_emission())
        result = _run_normalize(
            "--emission-path", str(self.emission_path),
            "--field", "verdict",
            "--new-value", "MAYBE",  # not in enum: FAIL|PARTIAL|PASS
            "--finding-local-id", "1",
            "--reason", "test",
            "--in-place",
        )
        self.assertEqual(
            result.returncode, 1,
            f"schema-invalid normalize must exit 1; stderr={result.stderr}",
        )
        # Sidecar must NOT have been written (no trail entry pointing at
        # an emission state that never made it to disk).
        trail_path = self.eng / "cluster-trust-credibility-desktop.normalizations.json"
        self.assertFalse(
            trail_path.exists(),
            "sidecar must not be written when the normalize fails to validate",
        )

    def test_telemetry_field_is_emission_scoped(self):
        """``telemetry.reference_files_read`` is emission-scoped, not
        finding-scoped. The CLI accepts the edit without
        ``--finding-local-id``."""
        emission = _make_emission()
        emission["telemetry"] = {"reference_files_read": ["references/ethics-gate.md"]}
        self._write_emission(emission)
        result = _run_normalize(
            "--emission-path", str(self.emission_path),
            "--field", "telemetry.reference_files_read",
            "--new-value", '["ethics-gate.md"]',
            "--reason", "strip path prefix per schema",
            "--in-place",
        )
        self.assertEqual(result.returncode, 0, f"stderr={result.stderr}")
        edited = json.loads(self.emission_path.read_text(encoding="utf-8"))
        self.assertEqual(
            edited["telemetry"]["reference_files_read"], ["ethics-gate.md"],
        )


# ---------------------------------------------------------------------------
# Canary: passes on consistent trail, fails on tampered emission, skips when absent
# ---------------------------------------------------------------------------


class TestNormalizationsCanary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.eng = Path(self.tmp.name)
        self.emission_path = self.eng / "cluster-trust-credibility-desktop.json"

    def tearDown(self):
        self.tmp.cleanup()

    def _write_emission(self, emission: dict) -> None:
        self.emission_path.write_text(json.dumps(emission, indent=2), encoding="utf-8")

    def test_skip_passes_when_no_trail_files(self):
        """Mirror of the reflection canaries' skip posture: an engagement
        that never used the normalize tier MUST NOT fail this canary."""
        result = check_lead_normalizations_consistent(self.eng)
        self.assertTrue(result["passed"], result["summary"])
        self.assertIn("skipped", result["summary"])

    def test_skip_passes_on_missing_engagement_dir(self):
        result = check_lead_normalizations_consistent(self.eng / "nope")
        self.assertTrue(result["passed"], result["summary"])

    def test_passes_on_consistent_trail(self):
        """The happy path: normalize verb edits a field + writes the
        trail; the canary reads both and confirms they agree."""
        self._write_emission(_make_emission())
        result = _run_normalize(
            "--emission-path", str(self.emission_path),
            "--field", "surface",
            "--new-value", "purchase-zone",
            "--finding-local-id", "1",
            "--reason", "out-of-vocab surface; corrected",
            "--in-place",
        )
        self.assertEqual(result.returncode, 0, f"stderr={result.stderr}")
        canary = check_lead_normalizations_consistent(self.eng)
        self.assertTrue(
            canary["passed"],
            f"canary should pass on a freshly-recorded normalize; got "
            f"summary={canary['summary']!r} detail={canary['detail']!r}",
        )
        self.assertEqual(canary["detail"]["entries_checked"], 1)
        self.assertEqual(canary["detail"]["mismatches"], [])

    def test_fails_when_emission_was_tampered_post_trail(self):
        """The point of the canary: an unrecorded edit AFTER the trail was
        written breaks the audit trail, so the canary MUST fail."""
        self._write_emission(_make_emission())
        result = _run_normalize(
            "--emission-path", str(self.emission_path),
            "--field", "surface",
            "--new-value", "purchase-zone",
            "--finding-local-id", "1",
            "--reason", "out-of-vocab surface; corrected",
            "--in-place",
        )
        self.assertEqual(result.returncode, 0, f"stderr={result.stderr}")
        # Lead tampers with the emission AFTER the trail is written, without
        # going through the normalize verb. The canary should catch this.
        tampered = json.loads(self.emission_path.read_text(encoding="utf-8"))
        tampered["findings"][0]["surface"] = "hand-edited-surface"
        self.emission_path.write_text(json.dumps(tampered, indent=2), encoding="utf-8")
        canary = check_lead_normalizations_consistent(self.eng)
        self.assertFalse(
            canary["passed"],
            "tampered emission must break the canary; got "
            f"summary={canary['summary']!r}",
        )
        mismatches = canary["detail"]["mismatches"]
        self.assertEqual(len(mismatches), 1)
        self.assertEqual(mismatches[0]["field"], "surface")
        self.assertEqual(mismatches[0]["recorded_after"], "purchase-zone")
        self.assertEqual(mismatches[0]["current_value"], "hand-edited-surface")

    def test_fails_when_trail_references_missing_emission(self):
        """A trail file that names a deleted emission is itself a drift —
        the deletion erased what the trail was vouching for."""
        # Write a trail file pointing at a deleted emission.
        trail_path = self.eng / "cluster-pricing-desktop.normalizations.json"
        trail_path.write_text(json.dumps({
            "engagement": str(self.eng),
            "source_emission": str(self.eng / "cluster-pricing-desktop.json"),
            "normalizations_count": 1,
            "normalizations": [
                {
                    "finding_local_id": 1,
                    "field": "surface",
                    "before": "x",
                    "after": "y",
                    "reason": "test",
                    "applied_at": "2026-06-10T00:00:00Z",
                },
            ],
        }), encoding="utf-8")
        canary = check_lead_normalizations_consistent(self.eng)
        self.assertFalse(canary["passed"], canary["summary"])
        self.assertEqual(len(canary["detail"]["missing_emissions"]), 1)

    def test_passes_after_normalize_overwrites_an_earlier_normalize(self):
        """When the same (finding_local_id, field) is normalized twice,
        the canary checks the LAST-applied entry — earlier entries are
        historical and don't fail the gate."""
        self._write_emission(_make_emission())
        # First normalize
        r1 = _run_normalize(
            "--emission-path", str(self.emission_path),
            "--field", "surface",
            "--new-value", "first-try",
            "--finding-local-id", "1",
            "--reason", "first attempt",
            "--in-place",
        )
        self.assertEqual(r1.returncode, 0, f"stderr={r1.stderr}")
        # Second normalize on the same field
        r2 = _run_normalize(
            "--emission-path", str(self.emission_path),
            "--field", "surface",
            "--new-value", "purchase-zone",
            "--finding-local-id", "1",
            "--reason", "second attempt; better fit",
            "--in-place",
        )
        self.assertEqual(r2.returncode, 0, f"stderr={r2.stderr}")
        canary = check_lead_normalizations_consistent(self.eng)
        self.assertTrue(canary["passed"], canary["summary"])
        # Both entries were recorded in the trail (no overwrite of history),
        # but only the latest one is checked against the emission's current
        # value. detail.entries_checked counts collapsed-to-latest keys.
        trail = json.loads(
            (self.eng / "cluster-trust-credibility-desktop.normalizations.json")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(trail["normalizations_count"], 2)

    def test_applied_at_present_on_every_trail_entry(self):
        """Lock in the contract that the trail stamps every entry with
        an applied_at timestamp; the consistency canary doesn't enforce
        timestamp format directly but the operator audit trail relies on
        it being present and ISO-shaped."""
        self._write_emission(_make_emission())
        result = _run_normalize(
            "--emission-path", str(self.emission_path),
            "--field", "severity",
            "--new-value", "HIGH",
            "--finding-local-id", "1",
            "--reason", "specialist mis-tiered severity",
            "--in-place",
        )
        self.assertEqual(result.returncode, 0, f"stderr={result.stderr}")
        trail = json.loads(
            (self.eng / "cluster-trust-credibility-desktop.normalizations.json")
            .read_text(encoding="utf-8")
        )
        for entry in trail["normalizations"]:
            self.assertIn("applied_at", entry)
            self.assertTrue(
                re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", entry["applied_at"]),
                f"applied_at must be ISO-8601-Z UTC; got {entry['applied_at']!r}",
            )


if __name__ == "__main__":
    unittest.main()
