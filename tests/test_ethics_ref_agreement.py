"""End-to-end agreement on ethics f_refs across pipeline surfaces.

This test invokes the real ``scripts/lead_prep.py build-canonical-frefs`` as a
subprocess against the synthetic v2 fixture, then asserts:

1. The generated ``canonical-f-refs.json`` includes every ADJACENT/BLOCK
   ethics finding from the source ``ethics-findings.json``.
2. The (cluster, F-N) keys assigned to those ethics findings match what the
   v2 renderer loader would assign.

Pre-fix (2026-05-18), canonical-f-refs.json dropped the 3 ADJACENT ethics
findings while the renderer included them — markdown and HTML showed the
same conceptual finding under different F-N namespaces. This test fails
loudly if that regression recurs.

The fixture is intentionally minimal (1 cluster x 2 devices + 1 ADJACENT +
1 CLEAR ethics) so the test is fast and the failure surface is small.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from assembly.dedup import deduplicate_v2
from assembly.json_parser import parse_emission_file
from assembly.pipeline import FinalizedFindings
from report.v2_loader import (
    _engagement_cluster_emission_paths,
    _engagement_ethics_findings_path,
    build_canonical_view,
)

FIXTURE_SOURCE = REPO_ROOT / "tests" / "fixtures" / "v2_engagement_with_adjacent_ethics"
SCRIPT = REPO_ROOT / "scripts" / "lead_prep.py"


@pytest.fixture
def fixture_engagement(tmp_path: Path) -> Path:
    """Copy the read-only fixture into a writable tmp dir so the build script
    can write canonical-f-refs.json without polluting the repo."""
    dest = tmp_path / "engagement"
    shutil.copytree(FIXTURE_SOURCE, dest)
    return dest


def _adjacent_ethics_titles(eng_dir: Path) -> set[str]:
    payload = json.loads((eng_dir / "ethics-findings.json").read_text(encoding="utf-8"))
    return {
        f["title"]
        for f in payload["findings"]
        if f.get("ethics_state") in {"BLOCK", "ADJACENT"}
    }


def test_build_canonical_f_refs_includes_adjacent_ethics(fixture_engagement: Path) -> None:
    """The script must emit canonical f_refs covering every ADJACENT/BLOCK
    ethics finding present in ethics-findings.json. Closes the 2026-05-18
    namespace-drift bug."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "build-canonical-frefs", "--engagement", str(fixture_engagement)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"build_canonical_f_refs.py exited {result.returncode}\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )

    canon_path = fixture_engagement / "canonical-f-refs.json"
    assert canon_path.exists(), "canonical-f-refs.json was not written"
    canon = json.loads(canon_path.read_text(encoding="utf-8"))

    canon_ethics_titles = {
        meta["title"]
        for ref, meta in canon["by_canonical_ref"].items()
        if ref.startswith("ethics") and meta.get("verdict") == "FAIL"
    }

    expected_titles = _adjacent_ethics_titles(fixture_engagement)

    missing = expected_titles - canon_ethics_titles
    assert not missing, (
        f"canonical-f-refs.json is missing ADJACENT/BLOCK ethics findings: "
        f"{sorted(missing)}\n"
        f"This is the 2026-05-18 bug. Confirm build_canonical_f_refs.py uses "
        f"deduped.all_actionable() (not deduped.kept) when calling "
        f"FinalizedFindings.build."
    )


def test_canonical_and_loader_assign_same_f_n_to_ethics(fixture_engagement: Path) -> None:
    """The (cluster, F-N) keys for actionable ethics findings must match
    between the canonical-refs builder (subprocess) and the v2_loader's
    finalized output (in-process)."""
    # Build canonical-f-refs via subprocess (real builder)
    subprocess.run(
        [sys.executable, str(SCRIPT), "build-canonical-frefs", "--engagement", str(fixture_engagement)],
        check=True,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    canon = json.loads((fixture_engagement / "canonical-f-refs.json").read_text(encoding="utf-8"))

    canon_ethics_refs = {
        ref for ref, meta in canon["by_canonical_ref"].items()
        if ref.startswith("ethics") and meta.get("verdict") == "FAIL"
    }

    # Build loader-equivalent finalized in-process
    findings = []
    clusters: list[str] = []
    for p in sorted(fixture_engagement.glob("cluster-*.json")):
        r = parse_emission_file(p)
        findings.extend(r.findings)
        if r.cluster not in clusters:
            clusters.append(r.cluster)
    eth = parse_emission_file(fixture_engagement / "ethics-findings.json")
    findings.extend(eth.findings)
    if "ethics" not in clusters:
        clusters.append("ethics")

    deduped = deduplicate_v2(findings)
    loader_finalized = FinalizedFindings.build(deduped.all_actionable(), clusters)
    loader_ethics_refs = {
        f"ethics F-{f.display_index:02d}"
        for f in loader_finalized.findings
        if f.cluster == "ethics" and f.verdict == "FAIL"
    }

    assert canon_ethics_refs == loader_ethics_refs, (
        f"Canonical and loader disagree on ethics F-Ns.\n"
        f"  canon only:  {sorted(canon_ethics_refs - loader_ethics_refs)}\n"
        f"  loader only: {sorted(loader_ethics_refs - canon_ethics_refs)}\n"
        "Same finding identity must produce same F-N on both surfaces."
    )


def test_real_v2_loader_canonical_view_includes_adjacent_ethics(
    fixture_engagement: Path,
) -> None:
    """True integration test: invoke ``scripts.report.v2_loader.build_canonical_view``
    (the real renderer entry point) and compare its output against canonical
    refs from the build script.

    This is the regression guardrail the parity tests cannot provide on their
    own. The previous tests reconstruct ``FinalizedFindings.build(deduped.
    all_actionable(), clusters)`` inline — they pass even if v2_loader.py
    silently reverts to ``deduped.kept``. This test imports and calls the real
    loader function, so a regression in that file fails the test directly.

    Per Codex review 2026-05-18 — the missing integration-level guardrail.
    """
    # 1. Build canonical-f-refs.json via the real script subprocess
    subprocess.run(
        [sys.executable, str(SCRIPT), "build-canonical-frefs", "--engagement", str(fixture_engagement)],
        check=True,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    canon = json.loads((fixture_engagement / "canonical-f-refs.json").read_text(encoding="utf-8"))
    canon_ethics_fail_refs = {
        ref for ref, meta in canon["by_canonical_ref"].items()
        if ref.startswith("ethics") and meta.get("verdict") == "FAIL"
    }
    expected_titles = _adjacent_ethics_titles(fixture_engagement)

    # 2. Invoke the REAL renderer canonical-view function — not a re-implementation
    cluster_paths = _engagement_cluster_emission_paths(fixture_engagement)
    ethics_path = _engagement_ethics_findings_path(fixture_engagement)
    loader_by_canonical_ref, _aliases = build_canonical_view(cluster_paths, ethics_path)

    # 3. Loader's canonical view must contain every ADJACENT ethics finding
    loader_ethics_fail_refs = {
        ref for ref, meta in loader_by_canonical_ref.items()
        if ref.startswith("ethics") and (meta.get("verdict") or "").upper() == "FAIL"
    }
    loader_ethics_fail_titles = {
        meta.get("title")
        for ref, meta in loader_by_canonical_ref.items()
        if ref.startswith("ethics") and (meta.get("verdict") or "").upper() == "FAIL"
    }

    missing_titles = expected_titles - loader_ethics_fail_titles
    assert not missing_titles, (
        f"scripts/report/v2_loader.build_canonical_view() dropped ADJACENT/"
        f"BLOCK ethics findings: {sorted(missing_titles)}\n"
        f"Confirm v2_loader.py calls deduped.all_actionable() (not "
        f"deduped.kept) when building findings_assembly's finalized list.\n"
        f"Loader returned ethics-FAIL refs: {sorted(loader_ethics_fail_refs)}"
    )

    # 4. The two real consumers must agree on the (cluster, F-N) keys for
    #    those findings — same content_hash → same display_index.
    assert canon_ethics_fail_refs == loader_ethics_fail_refs, (
        f"build_canonical_f_refs.py (subprocess) and "
        f"scripts.report.v2_loader.build_canonical_view (in-process) "
        f"disagree on ethics-FAIL (cluster, F-N) keys.\n"
        f"  canon only:  {sorted(canon_ethics_fail_refs - loader_ethics_fail_refs)}\n"
        f"  loader only: {sorted(loader_ethics_fail_refs - canon_ethics_fail_refs)}\n"
        f"Both must use deduped.all_actionable() to feed FinalizedFindings.build."
    )
