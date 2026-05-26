"""Phase 4b hardening 2 — every anchor-candidates sidecar consumer must
fail loud on present-but-broken sidecars (Codex 2026-05-18 review of 64ce7f2).

Pre-fix, every consumer (test-specialist.py, build_canonical_f_refs.py,
v2_loader.py, lead_prep.py, build_synthesizer_emission_fallback.py)
swallowed OSError + JSONDecodeError and silently treated a broken sidecar
as "no sidecar" — which disabled the Phase 4b mandatory candidate-registry
rule without any visible signal.

Convention enforced by tests below:
- missing file → loader returns None (legacy skip is correct)
- present but unreadable / malformed → raises SidecarLoadError; consumer
  surfaces it as a non-zero exit or a propagated error
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from assembly.anchor_candidates import (
    SidecarLoadError,
    load_anchor_candidates_sidecar_strict,
)


# ---------------------------------------------------------------------------
# Shared loader — the canonical "missing vs broken" decision
# ---------------------------------------------------------------------------


class TestSidecarStrictLoader:
    def test_missing_file_returns_none(self, tmp_path: Path):
        assert load_anchor_candidates_sidecar_strict(tmp_path / "absent.json") is None

    def test_valid_json_returns_dict(self, tmp_path: Path):
        p = tmp_path / "sidecar.json"
        p.write_text(json.dumps({"candidate_to_e_index": {"price-block-1": "e10"}}), encoding="utf-8")
        loaded = load_anchor_candidates_sidecar_strict(p)
        assert loaded == {"candidate_to_e_index": {"price-block-1": "e10"}}

    def test_malformed_json_raises(self, tmp_path: Path):
        p = tmp_path / "sidecar.json"
        p.write_text("this is { not valid json {{{", encoding="utf-8")
        with pytest.raises(SidecarLoadError) as exc_info:
            load_anchor_candidates_sidecar_strict(p)
        assert str(p) in str(exc_info.value)
        assert "invalid JSON" in str(exc_info.value)

    def test_non_dict_top_level_raises(self, tmp_path: Path):
        """A bare list or string at the top level isn't a sidecar shape."""
        p = tmp_path / "sidecar.json"
        p.write_text('["just", "an", "array"]', encoding="utf-8")
        with pytest.raises(SidecarLoadError) as exc_info:
            load_anchor_candidates_sidecar_strict(p)
        assert "list" in str(exc_info.value)


# ---------------------------------------------------------------------------
# CLI: scripts/test-specialist.py validate
# ---------------------------------------------------------------------------


def _baton(eindexes: list[str]) -> dict:
    return {
        "schema_version": 1, "engagement_id": "2026-05-18-deadbeef", "device": "desktop",
        "url": "https://example.test", "captured_at": "2026-05-18T00:00:00.000Z",
        "viewport": {"width": 1920, "height": 1080, "dpr_requested": 1, "dpr_actual": 1},
        "capture_state": {"hydration": "post-hydration", "overlays_detected": [], "page_height_px": 3000},
        "elements": [
            {"e_index": e, "tag": "div", "text_content": "x", "role": "text",
             "accessible_name": "", "rect": {"x": 0, "y": 0, "width": 200, "height": 40}}
            for e in eindexes
        ],
        "sections": [], "page_head": {},
    }


def _emission_out_of_registry(baton_index: str = "e47") -> dict:
    return {
        "schema_version": 1, "engagement_id": "2026-05-18-deadbeef",
        "cluster": "pricing", "device": "desktop",
        "specialist_model": {"family": "sonnet", "version": "4.6"},
        "started_at": "2026-05-18T00:00:00.000Z",
        "completed_at": "2026-05-18T00:00:01.000Z",
        "status": "partial",
        "findings": [{
            "cluster": "pricing", "device": "desktop", "local_id": 1,
            "verdict": "FAIL", "title": "Out-of-registry baton_index test",
            "surface": "price-block",
            "element": {"baton_index": baton_index, "text_content": "x", "role": "text"},
            "severity": "MEDIUM", "scope": "page",
            "effort": {"change_type": "copy", "change_scope": "single-file"},
            "evidence_anchors": [{"type": "dom", "reference": baton_index}],
            "reference_citations": [{"source": "price-anchoring.md", "tier": "Silver"}],
            "observation": "Long observation prose to satisfy validator threshold for FAIL.",
            "recommendation": "Long recommendation prose to satisfy validator threshold for FAIL.",
            "why_this_matters": "Anchoring is highest leverage pricing pattern for this SKU.",
            "evidence_tier": "Silver",
        }],
    }


class TestTestSpecialistCliFailsLoudOnBrokenSidecar:
    """The exact scenario Codex caught: sibling anchor-candidates-desktop.json
    exists but is malformed; emission has out-of-registry baton_index.
    Pre-fix, validate returned 0 silently because the auto-discovery
    helper swallowed JSONDecodeError. Post-fix, validate exits non-zero
    with a clear 'not valid/readable' message."""

    SCRIPT = REPO_ROOT / "scripts" / "test-specialist.py"

    def test_malformed_sibling_sidecar_fails_loud(self, tmp_path: Path):
        # Sibling sidecar exists but is unparseable
        (tmp_path / "anchor-candidates-desktop.json").write_text(
            "this is { not valid json {{{", encoding="utf-8",
        )
        (tmp_path / "baton.json").write_text(json.dumps(_baton(["e47"])), encoding="utf-8")
        emission_path = tmp_path / "cluster-pricing-desktop.json"
        emission_path.write_text(json.dumps(_emission_out_of_registry()), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "validate",
             "--emission-path", str(emission_path),
             "--baton-path", str(tmp_path / "baton.json")],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode != 0, (
            "Auto-discovered malformed sidecar must NOT be silently treated as "
            "absent — that disables the registry rule without any visible signal. "
            f"stderr={result.stderr!r}"
        )
        # Clear human-readable error message
        assert (
            "anchor-candidates sidecar at" in result.stderr
            and ("invalid JSON" in result.stderr or "not valid/readable" in result.stderr)
        ), f"Expected loud sidecar-load error in stderr; got: {result.stderr!r}"

    def test_missing_sibling_sidecar_preserves_legacy_behavior(self, tmp_path: Path):
        """Missing sidecar (file doesn't exist) → registry rule silently
        skipped. Pre-Phase-4a engagements must keep working."""
        (tmp_path / "baton.json").write_text(json.dumps(_baton(["e47"])), encoding="utf-8")
        emission_path = tmp_path / "cluster-pricing-desktop.json"
        emission_path.write_text(json.dumps(_emission_out_of_registry()), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "validate",
             "--emission-path", str(emission_path),
             "--baton-path", str(tmp_path / "baton.json")],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        # Should NOT fail on baton_index_in_candidate_registry (no sidecar = skip)
        assert "baton_index_in_candidate_registry" not in result.stderr

    def test_explicit_sidecar_path_malformed_fails_loud(self, tmp_path: Path):
        (tmp_path / "broken-sidecar.json").write_text("garbage", encoding="utf-8")
        (tmp_path / "baton.json").write_text(json.dumps(_baton(["e47"])), encoding="utf-8")
        emission_path = tmp_path / "cluster-pricing-desktop.json"
        emission_path.write_text(json.dumps(_emission_out_of_registry()), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "validate",
             "--emission-path", str(emission_path),
             "--baton-path", str(tmp_path / "baton.json"),
             "--anchor-candidates-path", str(tmp_path / "broken-sidecar.json")],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode != 0
        assert "anchor-candidates sidecar" in result.stderr


# ---------------------------------------------------------------------------
# Library consumers: build_canonical_f_refs._load_sidecar, v2_loader
# build_canonical_view, lead_prep.build_canonical_frefs,
# build_synthesizer_emission_fallback.collect_findings
# ---------------------------------------------------------------------------


# NOTE: the former TestBuildCanonicalFRefsCliFailsLoudOnBrokenSidecar was removed
# when build_canonical_f_refs.py was consolidated into
# `lead_prep.py build-canonical-frefs` (the single canonical-f-refs builder, which
# now writes canonical-f-refs.json). TestLeadPrepCliFailsLoudOnBrokenSidecar below
# covers the same fail-loud-on-broken-sidecar intent against the surviving builder.


class TestLoaderBuildCanonicalViewRaisesOnBrokenSidecar:
    """scripts/report/v2_loader.build_canonical_view must propagate
    SidecarLoadError when an anchor-candidates-{device}.json in the
    engagement dir is broken. Pre-fix it silently used None."""

    def test_broken_sidecar_raises(self, tmp_path: Path):
        from report.v2_loader import build_canonical_view

        # Minimal cluster emission (won't reach parse; broken sidecar raises first)
        cluster_path = tmp_path / "cluster-pricing-desktop.json"
        cluster_path.write_text(json.dumps({
            "schema_version": 1, "engagement_id": "2026-05-18-deadbeef",
            "cluster": "pricing", "device": "desktop",
            "specialist_model": {"family": "sonnet", "version": "4.6"},
            "started_at": "2026-05-18T00:00:00.000Z",
            "completed_at": "2026-05-18T00:00:01.000Z",
            "status": "skipped", "skip_reason": "no findings", "findings": [],
        }), encoding="utf-8")
        # Broken sibling sidecar
        (tmp_path / "anchor-candidates-desktop.json").write_text("garbage", encoding="utf-8")

        with pytest.raises(SidecarLoadError) as exc_info:
            build_canonical_view([cluster_path], None)
        assert "anchor-candidates-desktop.json" in str(exc_info.value)


class TestLeadPrepCliFailsLoudOnBrokenSidecar:
    """scripts/lead_prep.py build-canonical-frefs must exit non-zero on
    broken sidecar."""

    SCRIPT = REPO_ROOT / "scripts" / "lead_prep.py"

    def test_broken_sidecar_fails(self, tmp_path: Path):
        eng = tmp_path / "engagement"
        eng.mkdir()
        (eng / "meta.json").write_text(json.dumps({
            "schema_version": 3, "id": "2026-05-18-deadbeef",
            "created": "2026-05-18T00:00:00.000Z", "updated": "2026-05-18T00:00:00.000Z",
            "type": "audit", "phase": "audit", "engagement_status": "complete",
            "reconciled": True,
            "page": {"url": "x", "url_normalized": "x", "file_path": None, "type": "product"},
            "platform": "shopify", "source_mode": "url-dual",
            "devices_requested": ["desktop"], "devices_scanned": ["desktop"],
            "clusters_used": ["pricing"], "scope": "focused",
            "min_priority": None, "compare_target": None, "quick_scan": False,
            "blocked": False, "plans_queue": [], "screenshot_input": None,
        }), encoding="utf-8")
        (eng / "anchor-candidates-desktop.json").write_text("not json", encoding="utf-8")
        # A cluster emission is required so build_canonical_view actually reaches
        # the (broken) sidecar. Without it, lead_prep short-circuits with
        # "no cluster emissions found" before the strict loader runs (this is the
        # consolidation behavior gap vs the dropped build_canonical_f_refs.py,
        # which loaded sidecars eagerly).
        (eng / "cluster-pricing-desktop.json").write_text(json.dumps({
            "schema_version": 1, "engagement_id": "2026-05-18-deadbeef",
            "cluster": "pricing", "device": "desktop",
            "specialist_model": {"family": "sonnet", "version": "4.6"},
            "started_at": "2026-05-18T00:00:00.000Z",
            "completed_at": "2026-05-18T00:00:01.000Z",
            "status": "skipped", "skip_reason": "no findings", "findings": [],
        }), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(self.SCRIPT), "build-canonical-frefs",
             "--engagement", str(eng)],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode != 0
        assert "anchor-candidates" in result.stderr and "not valid/readable" in result.stderr


class TestSynthFallbackRaisesOnBrokenSidecar:
    """scripts/build_synthesizer_emission_fallback.collect_findings must
    propagate SidecarLoadError when a sidecar is present but broken."""

    def test_broken_sidecar_raises(self, tmp_path: Path):
        # Direct library invocation to keep the assertion focused on the
        # loader-propagation behavior; the CLI wrapper at __main__ converts
        # this to exit 1 (see scripts/build_synthesizer_emission_fallback.py
        # if __name__ == "__main__" block).
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import importlib.util as _imp
        spec = _imp.spec_from_file_location(
            "build_synth_fallback",
            REPO_ROOT / "scripts" / "build_synthesizer_emission_fallback.py",
        )
        mod = _imp.module_from_spec(spec)
        spec.loader.exec_module(mod)

        eng = tmp_path / "engagement"
        eng.mkdir()
        (eng / "anchor-candidates-desktop.json").write_text("garbage", encoding="utf-8")
        # No emissions needed — the broken sidecar trips the loader first
        with pytest.raises(SidecarLoadError):
            mod.collect_findings(eng)
