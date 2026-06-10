"""GUARD B3 - frozen fixtures must not silently downgrade to the pre-2026-04-30
emission shape.

The two golden engagement fixtures (``fixtures/slingmods-pdp`` and
``fixtures/awdmods-homepage``) are the load-bearing inputs for the report
builder, the determinism probe, and a dozen regression tests. Two post-
2026-04-30 schema evolutions are easy to silently revert when a fixture
is hand-edited or regenerated against an older specialist:

  B3.1  ``proposed_anchor`` shape, when present, is a dict. Was a strict
        "absent baton_index MUST carry a dict proposed_anchor" rule pre-
        v1.2; product.md §4.2 v1.2 (2026-06-10) demoted proposed_anchor to
        an OPTIONAL editor hint and the schema's mandatory rule was
        removed. The fixture guard now just enforces that when the field
        IS present, it stays a dict (not a stringly-typed regression to a
        prose pseudo-anchor).

  B3.2  Every ethics finding with ``ethics_state == 'CLEAR'`` MUST set
        ``effort.change_type == 'not_applicable'`` and
        ``effort.change_scope == 'not_applicable'`` (Phase 7, 2026-05-18).
        Pre-Phase-7 these findings carried a bogus ``copy`` / ``single-file``
        change because nothing else fit; a regressed fixture reintroduces
        that lie.

This test is deliberately coupled to authoritative sources rather than
hardcoded literals:

  * The set of emission files (cluster-*.json minus cluster-context-*,
    plus ethics-findings.json) comes from
    ``diagnostics.determinism_probe._emission_files`` - the same enumerator
    the determinism probe and fixture-repair tooling use.
  * The string constants ('absent', 'CLEAR', 'not_applicable') are pulled
    out of ``schema/finding-v1.json``'s conditional ``allOf`` branches, so
    if the schema renames a const this test tracks it instead of asserting
    a stale literal.

Windows-safe: no non-ASCII in source or printed output; all JSON read with
an explicit utf-8 encoding.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
# The repo puts scripts/ on sys.path so modules import as
# 'from assembly.X import ...' / 'from diagnostics.X import ...'.
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from diagnostics.determinism_probe import _emission_files  # noqa: E402

FIXTURE_NAMES = ("slingmods-pdp", "awdmods-homepage")
SCHEMA = json.loads(
    (REPO_ROOT / "schema" / "finding-v1.json").read_text(encoding="utf-8")
)


# ---------------------------------------------------------------------------
# Pull the load-bearing string constants out of the schema's allOf branches
# instead of hardcoding them, so the guard tracks a schema rename.
# ---------------------------------------------------------------------------


def _allof_branches() -> list[dict]:
    branches = SCHEMA.get("allOf")
    assert isinstance(branches, list) and branches, (
        "schema/finding-v1.json must define a non-empty allOf with the "
        "conditional shape rules this guard depends on"
    )
    return branches


def _absent_const() -> str:
    """The const value flagged as 'no baton anchor'. Pulled from the schema's
    element.baton_index oneOf branch that pins the absent literal, so a
    schema rename of the literal would track here automatically. The pre-
    v1.2 hop through the (now removed) absent->proposed_anchor allOf branch
    was replaced 2026-06-10 when §4.2 v1.2 demoted proposed_anchor to an
    optional editor hint."""
    schema_elem = (
        SCHEMA.get("properties", {}).get("element", {})
        .get("properties", {}).get("baton_index", {})
    )
    for branch in schema_elem.get("oneOf", []):
        const = branch.get("const")
        if isinstance(const, str) and const:
            return const
    pytest.fail(
        "Could not locate the element.baton_index 'absent' const in "
        "schema/finding-v1.json; the guard's coupling to the schema is broken "
        "(did the const rename or get removed?)."
    )


def _clear_ethics_consts() -> tuple[str, str, str]:
    """Return (ethics_const, clear_const, not_applicable_const) from the
    Phase-7 'CLEAR ethics MUST use not_applicable' allOf branch."""
    for branch in _allof_branches():
        if_props = (branch.get("if") or {}).get("properties") or {}
        cluster = (if_props.get("cluster") or {}).get("const")
        ethics_state = (if_props.get("ethics_state") or {}).get("const")
        if cluster is None or ethics_state is None:
            continue
        then_effort = (
            ((branch.get("then") or {}).get("properties") or {}).get("effort")
            or {}
        ).get("properties") or {}
        change_type_const = (then_effort.get("change_type") or {}).get("const")
        change_scope_const = (then_effort.get("change_scope") or {}).get("const")
        if change_type_const is None or change_scope_const is None:
            continue
        assert change_type_const == change_scope_const, (
            "schema CLEAR-ethics branch expected matching not_applicable "
            "consts for change_type and change_scope"
        )
        assert all(
            isinstance(v, str) and v
            for v in (cluster, ethics_state, change_type_const)
        )
        return cluster, ethics_state, change_type_const
    pytest.fail(
        "Could not locate the Phase-7 CLEAR-ethics -> not_applicable "
        "conditional in schema/finding-v1.json; the guard's coupling to "
        "the schema is broken."
    )


ABSENT = _absent_const()
ETHICS_CLUSTER, CLEAR, NOT_APPLICABLE = _clear_ethics_consts()


# ---------------------------------------------------------------------------
# Fixture / emission helpers
# ---------------------------------------------------------------------------


def _fixture_dir(name: str) -> Path:
    d = REPO_ROOT / "fixtures" / name
    assert d.is_dir(), f"missing fixture directory: {d}"
    return d


def _load_findings(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    findings = data.get("findings") if isinstance(data, dict) else data
    assert isinstance(findings, list), (
        f"emission {path.name} has no 'findings' list"
    )
    return findings


def _all_emission_paths() -> list[tuple[str, Path]]:
    out: list[tuple[str, Path]] = []
    for name in FIXTURE_NAMES:
        files = _emission_files(_fixture_dir(name))
        # Never let cluster-context-* slices leak into the guard.
        for p in files:
            assert not p.name.startswith("cluster-context-"), (
                f"_emission_files leaked a context slice: {p.name}"
            )
        out.extend((name, p) for p in files)
    return out


EMISSION_PATHS = _all_emission_paths()


def _emission_id(item: tuple[str, Path]) -> str:
    name, path = item
    return f"{name}/{path.name}"


# ---------------------------------------------------------------------------
# Sanity: the corpus we are guarding is non-trivial
# ---------------------------------------------------------------------------


def test_corpus_is_non_empty_for_both_fixtures():
    """If a fixture lost its emission files the per-emission tests would
    vacuously pass; assert each fixture contributes emissions including its
    ethics-findings.json."""
    for name in FIXTURE_NAMES:
        files = _emission_files(_fixture_dir(name))
        names = {p.name for p in files}
        assert names, f"{name} contributed no emission files"
        assert "ethics-findings.json" in names, (
            f"{name} is missing ethics-findings.json"
        )
        assert any(
            n.startswith("cluster-") and not n.startswith("cluster-context-")
            for n in names
        ), f"{name} has no cluster emission files"


# ---------------------------------------------------------------------------
# B3.1 - proposed_anchor, when present, must be a dict
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("item", EMISSION_PATHS, ids=_emission_id)
def test_proposed_anchor_when_present_is_dict_shaped(item):
    """Post product.md §4.2 v1.2 (2026-06-10) proposed_anchor is OPTIONAL on
    absent findings — the renderer never auto-pins from it; absences ship
    blank for the operator's manual queue. The fixture guard is now: when
    proposed_anchor IS present (on absent or anywhere else), it must be a
    structured dict, never a stringly-typed prose pseudo-anchor that would
    silently regress the editor-hint flow."""
    name, path = item
    offenders: list[str] = []
    for f in _load_findings(path):
        if not isinstance(f, dict):
            continue
        if "proposed_anchor" not in f:
            continue  # absent field is fine post-v1.2
        pa = f.get("proposed_anchor")
        if not isinstance(pa, dict):
            offenders.append(
                f"local_id={f.get('local_id')!r} proposed_anchor={type(pa).__name__}"
            )
    assert not offenders, (
        f"{name}/{path.name}: proposed_anchor present but not a dict "
        f"(stringly-typed regression): {offenders}"
    )


def test_some_absent_findings_exist_across_the_corpus():
    """Coverage guard: at least one absent-anchored finding must exist in
    the corpus, otherwise downstream guards that exercise absence flow
    (renderer Strategy 4, editor manual queue) are vacuously green and a
    real regression could slip through."""
    total_absent = 0
    for _name, path in EMISSION_PATHS:
        for f in _load_findings(path):
            element = f.get("element") or {} if isinstance(f, dict) else {}
            if isinstance(element, dict) and element.get("baton_index") == ABSENT:
                total_absent += 1
    assert total_absent > 0, (
        "no absent-anchored findings found in either fixture; the B3.1 "
        "guard would be vacuous"
    )


# ---------------------------------------------------------------------------
# B3.2 - CLEAR ethics findings use not_applicable change_type and change_scope
# ---------------------------------------------------------------------------


def _clear_ethics_findings() -> list[tuple[str, Path, dict]]:
    out: list[tuple[str, Path, dict]] = []
    for name in FIXTURE_NAMES:
        path = _fixture_dir(name) / "ethics-findings.json"
        for f in _load_findings(path):
            if not isinstance(f, dict):
                continue
            if f.get("cluster") == ETHICS_CLUSTER and f.get("ethics_state") == CLEAR:
                out.append((name, path, f))
    return out


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_clear_ethics_findings_use_not_applicable(name):
    path = _fixture_dir(name) / "ethics-findings.json"
    offenders: list[str] = []
    clear_count = 0
    for f in _load_findings(path):
        if not isinstance(f, dict):
            continue
        if f.get("cluster") != ETHICS_CLUSTER or f.get("ethics_state") != CLEAR:
            continue
        clear_count += 1
        effort = f.get("effort") or {}
        ct = effort.get("change_type") if isinstance(effort, dict) else None
        cs = effort.get("change_scope") if isinstance(effort, dict) else None
        if ct != NOT_APPLICABLE or cs != NOT_APPLICABLE:
            offenders.append(
                f"local_id={f.get('local_id')!r} "
                f"change_type={ct!r} change_scope={cs!r}"
            )
    assert clear_count > 0, (
        f"{name}/ethics-findings.json has no CLEAR ethics findings; the "
        f"B3.2 guard would be vacuous for this fixture"
    )
    assert not offenders, (
        f"{name}/ethics-findings.json: CLEAR ethics findings not using "
        f"'{NOT_APPLICABLE}' for change_type/change_scope (Phase-7 "
        f"regression): {offenders}"
    )


def test_clear_ethics_corpus_is_non_empty():
    """Both fixtures together must contribute CLEAR ethics findings."""
    clears = _clear_ethics_findings()
    assert clears, "no CLEAR ethics findings in either fixture; B3.2 vacuous"
