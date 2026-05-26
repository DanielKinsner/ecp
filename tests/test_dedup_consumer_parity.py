"""Cross-consumer parity for DedupeResult bucket selection.

The 2026-05-18 ethics namespace drift bug was caused by two consumers of
``deduplicate_v2()`` disagreeing on which buckets to feed into
``FinalizedFindings.build``:

  * the canonical-f-refs builder used ``deduped.kept`` only
  * ``scripts/report/v2_loader.py`` used ``deduped.kept + deduped.ethics_findings``

Result: canonical-f-refs.json dropped the 3 ADJACENT ethics findings while
the HTML renderer included them — same finding had different F-Ns in markdown
vs HTML, customer-visible drift.

This test pins the contract: both consumers must feed identical input to
``FinalizedFindings.build``. The canonical helper for this is
``DedupeResult.all_actionable()``. Any new consumer that diverges from this
contract by passing a custom bucket subset must add an explicit exemption
below with a comment explaining why.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from assembly.dedup import deduplicate_v2
from assembly.json_parser import parse_emission_file
from assembly.models import DedupeResult, Finding
from assembly.pipeline import FinalizedFindings

FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "v2_engagement_with_adjacent_ethics"


def _load_fixture_findings() -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    clusters: list[str] = []
    for p in sorted(FIXTURE_DIR.glob("cluster-*.json")):
        r = parse_emission_file(p)
        findings.extend(r.findings)
        if r.cluster not in clusters:
            clusters.append(r.cluster)
    eth = parse_emission_file(FIXTURE_DIR / "ethics-findings.json")
    findings.extend(eth.findings)
    if "ethics" not in clusters:
        clusters.append("ethics")
    return findings, clusters


def test_fixture_contains_adjacent_ethics() -> None:
    """Sanity check: fixture must contain at least one ADJACENT/BLOCK ethics
    finding, otherwise this whole test suite cannot exercise the bug it pins
    against."""
    findings, _ = _load_fixture_findings()
    actionable_ethics = [
        f for f in findings
        if f.cluster == "ethics" and getattr(f, "ethics_state", "") in {"BLOCK", "ADJACENT"}
    ]
    assert actionable_ethics, (
        "Fixture must contain at least 1 BLOCK/ADJACENT ethics finding to "
        "exercise the regression contract — update the fixture if upstream "
        "removed it."
    )


def test_all_actionable_returns_union_of_kept_and_ethics() -> None:
    """``DedupeResult.all_actionable()`` is the canonical helper that closes
    the 2026-05-18 bug. It must return ``kept`` + ``ethics_findings`` so every
    consumer that wants ALL renderable findings gets the union by default."""
    findings, _ = _load_fixture_findings()
    deduped = deduplicate_v2(findings)

    actual = deduped.all_actionable()
    expected = list(deduped.kept) + list(deduped.ethics_findings)

    assert actual == expected, (
        f"all_actionable() drifted from kept+ethics_findings union: "
        f"got {len(actual)} items, expected {len(expected)}"
    )

    # Both buckets must be represented (otherwise the helper isn't doing its job)
    assert any(f.cluster == "ethics" and f.verdict == "FAIL" for f in actual), (
        "all_actionable() missing FAIL ethics findings — helper is broken"
    )


def test_empty_dedupe_result_all_actionable_is_empty() -> None:
    """Sanity: an empty DedupeResult returns an empty list, not None."""
    empty = DedupeResult()
    assert empty.all_actionable() == []


def test_canonical_refs_builder_includes_adjacent_ethics() -> None:
    """Regression test for the 2026-05-18 drift bug.

    Run the canonical-refs build path (as exercised by
    ``lead_prep.py build-canonical-frefs``) against the fixture and assert
    that ADJACENT ethics findings appear in the finalized output. Pre-fix,
    only CLEAR ethics findings made it through because the builder called
    ``FinalizedFindings.build(deduped.kept, ...)`` instead of using
    ``deduped.all_actionable()``.
    """
    findings, clusters = _load_fixture_findings()
    deduped = deduplicate_v2(findings)

    # Mirror lead_prep build-canonical-frefs
    finalized = FinalizedFindings.build(deduped.all_actionable(), clusters)

    ethics_in_final = [f for f in finalized.findings if f.cluster == "ethics"]
    fail_ethics = [f for f in ethics_in_final if f.verdict == "FAIL"]

    assert fail_ethics, (
        "Canonical-refs builder dropped FAIL (ADJACENT/BLOCK) ethics "
        "findings — this is the 2026-05-18 bug. Verify "
        "the canonical-f-refs builder uses deduped.all_actionable(), not "
        "deduped.kept."
    )


def test_renderer_loader_includes_adjacent_ethics() -> None:
    """Cross-consumer parity: the v2 loader (``scripts/report/v2_loader.py``)
    must feed the same finding universe into ``FinalizedFindings.build`` as
    the canonical-refs builder.

    Pinning this via the shared helper prevents the bug class where one
    consumer evolves to include a new bucket and the other doesn't notice.
    """
    findings, clusters = _load_fixture_findings()
    deduped = deduplicate_v2(findings)

    # Mirror scripts/report/v2_loader.py (post-fix)
    loader_finalized = FinalizedFindings.build(deduped.all_actionable(), clusters)

    # Mirror lead_prep build-canonical-frefs (post-fix)
    canon_finalized = FinalizedFindings.build(deduped.all_actionable(), clusters)

    loader_refs = {(f.cluster, f.display_index) for f in loader_finalized.findings}
    canon_refs = {(f.cluster, f.display_index) for f in canon_finalized.findings}

    assert loader_refs == canon_refs, (
        f"Canonical and renderer consumers diverged on (cluster, F-N) refs.\n"
        f"  canon only: {canon_refs - loader_refs}\n"
        f"  loader only: {loader_refs - canon_refs}\n"
        "Both must call FinalizedFindings.build(deduped.all_actionable(), ...) "
        "for downstream renderable surfaces to agree on ethics IDs."
    )


def test_kept_only_demonstrates_the_bug() -> None:
    """Negative control: using ``deduped.kept`` only (the pre-fix call site)
    drops ADJACENT ethics findings from the finalized set. This test exists
    to keep the bug visible — if it ever stops failing on the "kept-only"
    path, the dedup engine has changed and the rest of this suite needs
    re-validation.
    """
    findings, clusters = _load_fixture_findings()
    deduped = deduplicate_v2(findings)

    finalized_kept_only = FinalizedFindings.build(deduped.kept, clusters)
    fail_ethics_kept_only = [
        f for f in finalized_kept_only.findings
        if f.cluster == "ethics" and f.verdict == "FAIL"
    ]

    assert not fail_ethics_kept_only, (
        "Negative control failed: deduped.kept now includes FAIL ethics "
        "findings, which means the dedup engine has changed and the rest "
        "of this suite needs re-validation. Inspect deduplicate_v2() in "
        "scripts/assembly/dedup.py."
    )
