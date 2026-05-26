"""Phase 4b — mandatory candidate registry contract (2026-05-18).

Tests covering:
- Schema accepts the new ``intentional_outside_registry`` opt-out fields
- Schema rejects ``intentional_outside_registry=true`` without a non-empty reason
- ``check_baton_index_in_candidate_registry`` rejects FAIL findings whose
  baton_index isn't in the registry, AND accepts them when the opt-out
  flag is set with a reason
- PASS findings exempt; absent findings exempt; sidecar-absent skips check
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from assembly.business_rules import validate_business_rules

SCHEMA = json.loads((REPO_ROOT / "schema" / "finding-v1.json").read_text(encoding="utf-8"))


def _base_finding(
    *,
    verdict: str = "FAIL",
    baton_index: str = "e10",
    **extra,
) -> dict:
    f = {
        "cluster": "pricing", "device": "desktop", "local_id": 1,
        "verdict": verdict, "title": "Test finding for registry contract",
        "surface": "price-block",
        "element": {"baton_index": baton_index, "text_content": "$199.99", "role": "text"},
        "severity": "MEDIUM", "scope": "page",
        "effort": {"change_type": "copy", "change_scope": "single-file"},
        "evidence_anchors": [{"type": "dom", "reference": baton_index or "e0"}],
        "reference_citations": [{"source": "price-anchoring.md", "tier": "Silver"}],
        "observation": "Long observation prose to satisfy the validator threshold for FAIL findings.",
        "recommendation": "Long recommendation prose to satisfy the validator threshold for FAIL findings.",
        "why_this_matters": "Anchoring is the highest leverage pricing pattern for this SKU.",
        "evidence_tier": "Silver",
    }
    f.update(extra)
    return f


def _base_emission(findings: list[dict]) -> dict:
    return {
        "schema_version": 1, "engagement_id": "2026-05-18-deadbeef",
        "cluster": "pricing", "device": "desktop",
        "specialist_model": {"family": "sonnet", "version": "4.6"},
        "started_at": "2026-05-18T00:00:00.000Z",
        "completed_at": "2026-05-18T00:00:01.000Z",
        "status": "complete",
        "findings": findings,
    }


def _baton(e_indexes: list[str]) -> dict:
    return {
        "schema_version": 1, "engagement_id": "2026-05-18-deadbeef",
        "device": "desktop", "url": "https://example.test",
        "captured_at": "2026-05-18T00:00:00.000Z",
        "viewport": {"width": 1920, "height": 1080, "dpr_requested": 1, "dpr_actual": 1},
        "capture_state": {"hydration": "post-hydration", "overlays_detected": [], "page_height_px": 3000},
        "elements": [
            {"e_index": e, "tag": "div", "rect": {"x": 0, "y": 0, "width": 200, "height": 40}}
            for e in e_indexes
        ],
        "sections": [], "page_head": {},
    }


def _sidecar(candidate_to_e: dict[str, str]) -> dict:
    return {
        "engagement_id": "2026-05-18-deadbeef", "device": "desktop",
        "candidates_by_role": {},
        "candidate_to_e_index": candidate_to_e,
        "expected_overlay_templates": {},
        "counts": {"total_candidates": len(candidate_to_e), "by_role": {}, "baton_elements": 0},
    }


# ---------------------------------------------------------------------------
# Schema acceptance for new opt-out fields
# ---------------------------------------------------------------------------


class TestSchemaOptOutFields:
    def test_opt_out_with_reason_validates(self):
        f = _base_finding(
            intentional_outside_registry=True,
            intentional_outside_registry_reason="Custom sticky CTA pattern not in classifier",
        )
        errors = [e.message for e in Draft202012Validator(SCHEMA).iter_errors(f)]
        assert errors == []

    def test_opt_out_without_reason_rejected(self):
        f = _base_finding(intentional_outside_registry=True)
        errors = [e.message for e in Draft202012Validator(SCHEMA).iter_errors(f)]
        assert errors, "Schema should require intentional_outside_registry_reason when flag is true"

    def test_opt_out_with_empty_reason_rejected(self):
        f = _base_finding(
            intentional_outside_registry=True,
            intentional_outside_registry_reason="",
        )
        errors = [e.message for e in Draft202012Validator(SCHEMA).iter_errors(f)]
        assert errors, "Schema should require non-empty reason"

    def test_opt_out_false_or_absent_validates_unchanged(self):
        # No flag, default false — legacy behavior, no reason required
        f = _base_finding()
        errors = [e.message for e in Draft202012Validator(SCHEMA).iter_errors(f)]
        assert errors == []

        f["intentional_outside_registry"] = False
        errors = [e.message for e in Draft202012Validator(SCHEMA).iter_errors(f)]
        assert errors == []


# ---------------------------------------------------------------------------
# business_rules: check_baton_index_in_candidate_registry
# ---------------------------------------------------------------------------


class TestRegistryMembershipRule:
    def test_baton_index_in_registry_passes(self):
        emission = _base_emission([_base_finding(baton_index="e10")])
        sidecar = _sidecar({"price-block-1": "e10"})
        violations = validate_business_rules(
            emission, baton=_baton(["e10"]),
            anchor_candidates_sidecar=sidecar,
        )
        # No violations from the registry rule
        assert not any(
            v.rule == "baton_index_in_candidate_registry" for v in violations
        )

    def test_baton_index_outside_registry_fails(self):
        emission = _base_emission([_base_finding(baton_index="e47")])
        sidecar = _sidecar({"price-block-1": "e10"})  # e47 NOT in registry
        violations = validate_business_rules(
            emission, baton=_baton(["e10", "e47"]),
            anchor_candidates_sidecar=sidecar,
        )
        registry_violations = [
            v for v in violations if v.rule == "baton_index_in_candidate_registry"
        ]
        assert registry_violations, (
            "FAIL finding with baton_index outside registry MUST violate "
            "Phase 4b registry rule"
        )
        assert "e47" in registry_violations[0].actual
        # Error message should include a sample of registry mappings
        assert "price-block-1" in registry_violations[0].message

    def test_opt_out_with_reason_accepted(self):
        emission = _base_emission([_base_finding(
            baton_index="e47",
            intentional_outside_registry=True,
            intentional_outside_registry_reason=(
                "Mobile sticky bottom-bar pattern the classifier doesn't recognize yet"
            ),
        )])
        sidecar = _sidecar({"price-block-1": "e10"})
        violations = validate_business_rules(
            emission, baton=_baton(["e10", "e47"]),
            anchor_candidates_sidecar=sidecar,
        )
        # Opt-out with reason is accepted
        assert not any(
            v.rule == "baton_index_in_candidate_registry" for v in violations
        )

    def test_opt_out_with_empty_reason_rejected_by_business_rules(self):
        # Even if schema validation is bypassed somehow, business_rules
        # also enforces non-empty reason. Belt + suspenders.
        emission = _base_emission([_base_finding(
            baton_index="e47",
            intentional_outside_registry=True,
            intentional_outside_registry_reason="   ",  # whitespace-only
        )])
        sidecar = _sidecar({"price-block-1": "e10"})
        violations = validate_business_rules(
            emission, baton=_baton(["e10", "e47"]),
            anchor_candidates_sidecar=sidecar,
        )
        reason_violations = [
            v for v in violations
            if v.rule == "intentional_outside_registry_reason_required"
        ]
        assert reason_violations

    def test_pass_finding_exempt(self):
        emission = _base_emission([_base_finding(
            verdict="PASS",
            baton_index="e47",  # outside registry
        )])
        sidecar = _sidecar({"price-block-1": "e10"})
        violations = validate_business_rules(
            emission, baton=_baton(["e10", "e47"]),
            anchor_candidates_sidecar=sidecar,
        )
        assert not any(
            v.rule == "baton_index_in_candidate_registry" for v in violations
        )

    def test_absent_baton_index_exempt(self):
        emission = _base_emission([_base_finding(baton_index="absent")])
        sidecar = _sidecar({"price-block-1": "e10"})
        violations = validate_business_rules(
            emission, baton=_baton(["e10"]),
            anchor_candidates_sidecar=sidecar,
        )
        assert not any(
            v.rule == "baton_index_in_candidate_registry" for v in violations
        )

    def test_no_sidecar_skips_check_entirely(self):
        """Legacy engagements without a sidecar shouldn't trip the rule.
        Pre-Phase-4b emissions continue to work."""
        emission = _base_emission([_base_finding(baton_index="e47")])
        violations = validate_business_rules(
            emission, baton=_baton(["e10", "e47"]),
            anchor_candidates_sidecar=None,
        )
        assert not any(
            v.rule == "baton_index_in_candidate_registry" for v in violations
        )

    def test_empty_sidecar_treated_as_present_but_empty_registry(self):
        """Sidecar exists but has zero candidates — every FAIL with a real
        baton_index violates the rule. This is a degenerate case but the
        contract is consistent."""
        emission = _base_emission([_base_finding(baton_index="e10")])
        sidecar = _sidecar({})
        violations = validate_business_rules(
            emission, baton=_baton(["e10"]),
            anchor_candidates_sidecar=sidecar,
        )
        registry_violations = [
            v for v in violations if v.rule == "baton_index_in_candidate_registry"
        ]
        assert registry_violations


# ---------------------------------------------------------------------------
# CLI: scripts/test-specialist.py validate must wire the sidecar through
# (Codex 2026-05-18 review of 4b30742 — direct-unit-test coverage alone
# is not enough; the real lead-invoked CLI must enforce the rule)
# ---------------------------------------------------------------------------


class TestCliEnforcement:
    """Subprocess tests against scripts/test-specialist.py validate."""

    SCRIPT = REPO_ROOT / "scripts" / "test-specialist.py"

    def _write_fixture(
        self,
        tmp: Path,
        *,
        baton_index: str,
        registry: dict[str, str],
        opt_out: bool = False,
        opt_out_reason: str | None = None,
        write_sidecar: bool = True,
    ) -> Path:
        """Write baton + sidecar + emission. Returns emission path.

        ``baton`` includes e10 and e47 so both in-registry and
        out-of-registry tests can vary the finding's baton_index without
        tripping the unrelated baton_index_resolves check.
        """
        baton = {
            "schema_version": 1, "engagement_id": "2026-05-18-deadbeef",
            "device": "desktop", "url": "https://example.test",
            "captured_at": "2026-05-18T00:00:00.000Z",
            "viewport": {"width": 1920, "height": 1080, "dpr_requested": 1, "dpr_actual": 1},
            "capture_state": {
                "hydration": "post-hydration", "overlays_detected": [],
                "page_height_px": 3000,
            },
            "elements": [
                {"e_index": e, "tag": "div",
                 "text_content": "$199" if e == "e10" else "Other",
                 "role": "text", "accessible_name": "",
                 "rect": {"x": 0, "y": 0, "width": 200, "height": 40}}
                for e in ("e10", "e47")
            ],
            "sections": [], "page_head": {},
        }
        (tmp / "baton.json").write_text(json.dumps(baton), encoding="utf-8")

        if write_sidecar:
            sidecar = {
                "engagement_id": "2026-05-18-deadbeef", "device": "desktop",
                "candidates_by_role": {}, "candidate_to_e_index": registry,
                "expected_overlay_templates": {},
                "counts": {"total_candidates": len(registry), "by_role": {}, "baton_elements": 2},
            }
            (tmp / "anchor-candidates-desktop.json").write_text(
                json.dumps(sidecar), encoding="utf-8",
            )

        text_at_e = "$199" if baton_index == "e10" else "Other"
        opt_out_kwargs: dict = {}
        if opt_out:
            opt_out_kwargs["intentional_outside_registry"] = True
            opt_out_kwargs["intentional_outside_registry_reason"] = opt_out_reason or ""
        finding = _base_finding(baton_index=baton_index, **opt_out_kwargs)
        # Make the finding's element fields match the baton element exactly so
        # the unrelated Phase M element_text_matches_baton check doesn't trip.
        finding["element"]["text_content"] = text_at_e
        finding["evidence_anchors"][0]["reference"] = baton_index
        # status='partial' exempts emissions from the target_finding_count
        # band check so this fixture doesn't need to pad to 3+ findings
        # (which would introduce duplicate-anchor noise unrelated to the
        # registry rule under test).
        emission = _base_emission([finding])
        emission["status"] = "partial"
        emission_path = tmp / "cluster-pricing-desktop.json"
        emission_path.write_text(json.dumps(emission), encoding="utf-8")
        return emission_path

    def _run(self, emission_path: Path, baton_path: Path, *extra: str) -> subprocess.CompletedProcess:
        import subprocess  # local import keeps top-of-file lean
        return subprocess.run(
            [sys.executable, str(self.SCRIPT), "validate",
             "--emission-path", str(emission_path),
             "--baton-path", str(baton_path), *extra],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )

    def test_cli_rejects_out_of_registry_baton_index(self, tmp_path: Path):
        """The exact Codex repro: baton_index=e47, registry only allows e10.
        Without --anchor-candidates-path, auto-discovery picks up the
        sibling anchor-candidates-desktop.json. CLI must exit non-zero
        with the rule name in stderr."""
        emission_path = self._write_fixture(
            tmp_path, baton_index="e47", registry={"price-block-1": "e10"},
        )
        result = self._run(emission_path, tmp_path / "baton.json")
        assert result.returncode != 0, (
            f"CLI should have rejected out-of-registry baton_index. "
            f"stdout={result.stdout!r} stderr={result.stderr!r}"
        )
        assert "baton_index_in_candidate_registry" in result.stderr, (
            f"Expected rule name in stderr; got: {result.stderr!r}"
        )

    def test_cli_accepts_in_registry_baton_index(self, tmp_path: Path):
        emission_path = self._write_fixture(
            tmp_path, baton_index="e10", registry={"price-block-1": "e10"},
        )
        result = self._run(emission_path, tmp_path / "baton.json")
        assert result.returncode == 0, (
            f"CLI should have accepted in-registry baton_index. "
            f"stderr={result.stderr!r}"
        )

    def test_cli_accepts_opt_out_with_reason(self, tmp_path: Path):
        emission_path = self._write_fixture(
            tmp_path, baton_index="e47", registry={"price-block-1": "e10"},
            opt_out=True,
            opt_out_reason="Mobile sticky bottom-bar pattern the classifier doesn't recognize yet",
        )
        result = self._run(emission_path, tmp_path / "baton.json")
        assert result.returncode == 0, (
            f"CLI should have accepted intentional opt-out with reason. "
            f"stderr={result.stderr!r}"
        )

    def test_cli_legacy_path_no_sidecar_no_enforcement(self, tmp_path: Path):
        """When no sidecar is on disk AND no --anchor-candidates-path is
        provided, the registry rule is silently skipped (legacy
        preservation)."""
        emission_path = self._write_fixture(
            tmp_path, baton_index="e47", registry={"price-block-1": "e10"},
            write_sidecar=False,
        )
        result = self._run(emission_path, tmp_path / "baton.json")
        # Should NOT fail due to baton_index_in_candidate_registry
        assert "baton_index_in_candidate_registry" not in result.stderr, (
            "Legacy run (no sidecar) should not trigger the registry rule. "
            f"stderr={result.stderr!r}"
        )

    def test_cli_explicit_sidecar_path_overrides_auto_discovery(self, tmp_path: Path):
        """--anchor-candidates-path takes precedence over sibling discovery.
        Tests with the sidecar in a non-sibling location."""
        emission_path = self._write_fixture(
            tmp_path, baton_index="e47", registry={"price-block-1": "e10"},
            write_sidecar=False,
        )
        # Write sidecar in a different directory
        sidecar_dir = tmp_path / "sidecars"
        sidecar_dir.mkdir()
        sidecar_path = sidecar_dir / "custom-anchor-candidates.json"
        sidecar_path.write_text(json.dumps({
            "engagement_id": "2026-05-18-deadbeef", "device": "desktop",
            "candidates_by_role": {}, "candidate_to_e_index": {"price-block-1": "e10"},
            "expected_overlay_templates": {},
            "counts": {"total_candidates": 1, "by_role": {}, "baton_elements": 2},
        }), encoding="utf-8")

        result = self._run(
            emission_path, tmp_path / "baton.json",
            "--anchor-candidates-path", str(sidecar_path),
        )
        assert "baton_index_in_candidate_registry" in result.stderr, (
            "Explicit --anchor-candidates-path should activate the registry rule. "
            f"stderr={result.stderr!r}"
        )

    def test_cli_explicit_sidecar_missing_path_fails_fast(self, tmp_path: Path):
        """Like baton-path: if user explicitly supplies a path that's not
        on disk, fail fast with exit 3."""
        emission_path = self._write_fixture(
            tmp_path, baton_index="e10", registry={"price-block-1": "e10"},
        )
        bogus = tmp_path / "does-not-exist.json"
        result = self._run(
            emission_path, tmp_path / "baton.json",
            "--anchor-candidates-path", str(bogus),
        )
        assert result.returncode == 3, (
            f"Missing explicit sidecar path should fail with exit 3 (got {result.returncode}). "
            f"stderr={result.stderr!r}"
        )

    def test_cli_opt_out_with_empty_reason_rejected(self, tmp_path: Path):
        """Belt + suspenders: opt-out flag without a real reason still
        fails business_rules even if it slips past schema."""
        emission_path = self._write_fixture(
            tmp_path, baton_index="e47", registry={"price-block-1": "e10"},
            opt_out=True, opt_out_reason="   ",  # whitespace-only
        )
        result = self._run(emission_path, tmp_path / "baton.json")
        assert result.returncode != 0
        # Either the schema rejects it (intentional_outside_registry_reason
        # required + minLength 1 — whitespace passes minLength but
        # business_rules treats whitespace-only as empty) OR business_rules
        # rejects via intentional_outside_registry_reason_required rule.
        # Both stderr signals are valid.
        assert (
            "intentional_outside_registry_reason" in result.stderr
            or "intentional_outside_registry_reason_required" in result.stderr
        ), f"Expected reason-required signal in stderr; got: {result.stderr!r}"
