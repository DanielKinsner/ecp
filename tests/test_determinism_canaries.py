"""GUARD B4/B5: determinism canaries for the deterministic canonical-view build.

This regression test fences off the two determinism hazards that the
2026-05-31 dynamic-workflows diagnosis surfaced in the deterministic Layer-2
structuring path (the only layer that CAN be tested hermetically; LLM /
acquisition variance is out of scope and lives in the N-run gate):

GUARD B4/B5 (a) -- build determinism
    Building the canonical view from the FROZEN slingmods-pdp fixture must be
    byte-stable. We assert it twice:
      * in-process x2 -> identical fingerprint + identical canonical-ref count;
      * cross-process under several PYTHONHASHSEED values (fresh subprocess
        each) -> the same fingerprint, catching hidden set/dict iteration-order
        or built-in hash() salting (the code is meant to use sha256 + sorted()).
    The build is reused from scripts/diagnostics/determinism_probe.py when its
    helpers import cleanly; otherwise it falls back to
    report.v2_loader.build_canonical_view directly. Either way the fingerprint
    formula is taken from the authoritative source, never re-implemented here.

GUARD B4/B5 (b) -- absent-finding group key is content-derived, not id()-based
    scripts/assembly/dedup.py's cross-cluster structural layer groups
    baton_index='absent' findings by a STABLE, content-derived key
    (_absent_content_key). The pre-fix code keyed them by id(f), which is the
    process-address of the object and therefore non-deterministic across runs
    (and across PYTHONHASHSEED). This is an AST static guard: it asserts
    _absent_content_key exists AND that _v2_layer_cross_cluster_structural
    contains no id(...) call. AST (not substring) keeps the docstring mention of
    "id(f)" from producing a false PASS/FAIL.

Hermetic + Windows-safe: reads only the checked-in fixture, prints ASCII only,
copies nothing it mutates. Authored as a pytest module but uses no pytest-only
features, so the project's `python -m unittest discover` runner also collects it.

Run:
    python -m pytest tests/test_determinism_canaries.py
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_SCRIPTS = _REPO / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

SLINGMODS_FIXTURE = _REPO / "fixtures" / "slingmods-pdp"
DEDUP_PATH = _SCRIPTS / "assembly" / "dedup.py"
PROBE_PATH = _SCRIPTS / "diagnostics" / "determinism_probe.py"

# The slingmods fixture is the frozen reference engagement. Its deterministic
# canonical-ref count is pinned here. Coupling to this number guards against a
# silent shrink in cluster coverage (the G16 failure mode) as well as ref drift.
# 2026-06-18: lowered 83 -> 82. The cross-cluster structural dedup layer was
# keying on `device` for page-scope findings, which are device-agnostic; one
# real cross-cluster page-scope duplicate in this fixture (Layer-1 collapsed to
# divergent winner-device labels) therefore survived. The dedup fix merges it
# (dropped still 0, fingerprint still STABLE) — an intended one-ref shrink.
EXPECTED_SLINGMODS_REFCOUNT = 82


# ---------------------------------------------------------------------------
# Authoritative build, sourced from the probe when importable
# ---------------------------------------------------------------------------


def _load_probe_module():
    """Load scripts/diagnostics/determinism_probe.py as a module.

    The file is hyphen-free so it imports cleanly, but it lives outside a
    package, so we load it by path via importlib and register it in
    sys.modules BEFORE exec so its subprocess re-entry (build subcommand)
    and any dataclass/module-scope references resolve.
    """
    spec = importlib.util.spec_from_file_location("ecp_determinism_probe", PROBE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["ecp_determinism_probe"] = module
    spec.loader.exec_module(module)
    return module


def _fingerprint_from_by_ref(by_ref: dict) -> str:
    """Recompute the canonical fingerprint EXACTLY as the probe does.

    Mirrors scripts/diagnostics/determinism_probe.py:_fingerprint. Only used
    on the fallback path (when the probe helpers aren't importable); the
    primary path calls the probe's own _build_one so the formula is shared.
    """
    blob = json.dumps(by_ref, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _build_once(fixture: Path) -> tuple[int, str, int]:
    """Build the canonical view once. Returns (ref_count, fingerprint, dropped).

    Prefers the probe's _build_one (the authoritative helper); falls back to
    report.v2_loader.build_canonical_view + the probe's fingerprint formula.
    """
    try:
        probe = _load_probe_module()
        refs, fp, dropped = probe._build_one(fixture)
        return len(refs), fp, len(dropped)
    except Exception:
        from report.v2_loader import (
            build_canonical_view,
            _engagement_cluster_emission_paths,
            _engagement_ethics_findings_path,
        )
        cluster_paths = _engagement_cluster_emission_paths(fixture)
        ethics_path = _engagement_ethics_findings_path(fixture)
        by_ref, _aliases, dropped = build_canonical_view(cluster_paths, ethics_path)
        return len(by_ref), _fingerprint_from_by_ref(by_ref), len(dropped)


# ---------------------------------------------------------------------------
# GUARD B4/B5 (a): in-process + cross-process build determinism
# ---------------------------------------------------------------------------


def test_slingmods_fixture_present():
    """The frozen fixture this guard depends on must exist."""
    assert SLINGMODS_FIXTURE.is_dir(), (
        f"slingmods fixture missing at {SLINGMODS_FIXTURE} -- the determinism "
        f"canary cannot run without the frozen reference engagement."
    )


def test_inprocess_build_is_byte_stable():
    """Two in-process builds of the frozen fixture must be identical.

    Identical fingerprint AND identical canonical-ref count, with zero dropped
    emissions (a drop would mean cluster coverage silently shrank -- the G16
    untraceable-misleading failure mode).
    """
    refs1, fp1, dropped1 = _build_once(SLINGMODS_FIXTURE)
    refs2, fp2, dropped2 = _build_once(SLINGMODS_FIXTURE)

    assert dropped1 == 0, (
        f"build dropped {dropped1} emission(s) -- cluster coverage shrank; "
        f"the deterministic build is no longer operating on the full universe."
    )
    assert dropped2 == 0
    assert refs1 == refs2, (
        f"canonical-ref count changed between two in-process builds: "
        f"{refs1} vs {refs2} -- the deterministic path is not deterministic."
    )
    assert fp1 == fp2, (
        f"canonical-view fingerprint changed between two in-process builds: "
        f"{fp1} vs {fp2} -- the deterministic path is not deterministic."
    )


def test_inprocess_refcount_matches_probe_contract():
    """Coupling guard: the slingmods canonical-ref count is pinned at 82.

    A change here means either the fixture changed or the dedup/merge algo
    changed the canonical universe -- both warrant an explicit review, not a
    silent drift. (Lowered 83 -> 82 on 2026-06-18 by the page-scope dedup fix;
    see EXPECTED_SLINGMODS_REFCOUNT note above.)
    """
    refs, _fp, dropped = _build_once(SLINGMODS_FIXTURE)
    assert dropped == 0
    assert refs == EXPECTED_SLINGMODS_REFCOUNT, (
        f"slingmods canonical-ref count is {refs}, expected "
        f"{EXPECTED_SLINGMODS_REFCOUNT} (per the determinism_probe contract). "
        f"If this is intentional, update EXPECTED_SLINGMODS_REFCOUNT and the "
        f"probe docstring together."
    )


def _build_fingerprint_in_subprocess(fixture: Path, hashseed: str) -> tuple[str, int]:
    """Run the probe's `build` subcommand in a fresh process under a seed.

    Returns (fingerprint, refcount) parsed from the probe's stdout lines.
    A fresh interpreter with an explicit PYTHONHASHSEED is the only way to
    catch hash-salting / iteration-order nondeterminism, which is invisible
    within a single process.
    """
    env = {**os.environ, "PYTHONHASHSEED": hashseed}
    proc = subprocess.run(
        [sys.executable, str(PROBE_PATH), "build", "--fixture", str(fixture)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=str(_REPO),
    )
    assert proc.returncode == 0, (
        f"probe build subprocess failed (seed={hashseed}, rc={proc.returncode}). "
        f"stderr={proc.stderr!r}"
    )
    fingerprint = ""
    refcount = -1
    for line in proc.stdout.splitlines():
        if line.startswith("FINGERPRINT "):
            fingerprint = line.split(" ", 1)[1].strip()
        elif line.startswith("REFCOUNT "):
            refcount = int(line.split(" ", 1)[1].strip())
    assert fingerprint, f"no FINGERPRINT line in probe output: {proc.stdout!r}"
    return fingerprint, refcount


def test_cross_process_build_stable_across_pythonhashseed():
    """The fingerprint must be identical across PYTHONHASHSEED-varied processes.

    This is the strong guard: it exercises fresh interpreters with different
    hash salts, catching any reliance on set/dict iteration order or built-in
    hash() that the in-process test cannot see.
    """
    inproc_refs, inproc_fp, inproc_dropped = _build_once(SLINGMODS_FIXTURE)
    assert inproc_dropped == 0

    seeds = ["0", "1", "12345"]
    seen_fps: dict[str, str] = {}
    for seed in seeds:
        fp, refcount = _build_fingerprint_in_subprocess(SLINGMODS_FIXTURE, seed)
        seen_fps[seed] = fp
        assert refcount == inproc_refs, (
            f"refcount under PYTHONHASHSEED={seed} ({refcount}) != in-process "
            f"build ({inproc_refs})."
        )

    distinct = set(seen_fps.values()) | {inproc_fp}
    assert len(distinct) == 1, (
        f"canonical-view fingerprint is NOT stable across PYTHONHASHSEED: "
        f"in-process={inproc_fp[:16]} per-seed="
        f"{ {s: v[:16] for s, v in seen_fps.items()} } -- the build depends on "
        f"hash salting or iteration order."
    )


# ---------------------------------------------------------------------------
# GUARD B4/B5 (b): absent-finding group key is content-derived, not id()-based
# ---------------------------------------------------------------------------


def _dedup_ast() -> ast.Module:
    return ast.parse(DEDUP_PATH.read_text(encoding="utf-8"), filename=str(DEDUP_PATH))


def _function_node(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    return None


def test_absent_content_key_helper_exists():
    """The content-derived absent-key helper must exist (replaces id()-keying)."""
    tree = _dedup_ast()
    fn = _function_node(tree, "_absent_content_key")
    assert fn is not None, (
        "scripts/assembly/dedup.py must define _absent_content_key -- the "
        "stable, content-derived identity that replaced the non-deterministic "
        "id(f) grouping key for 'absent' baton_index findings."
    )
    # The helper must also be wired into the cross-cluster structural layer
    # (otherwise it exists but isn't used for the absent group key).
    cross = _function_node(tree, "_v2_layer_cross_cluster_structural")
    assert cross is not None, (
        "scripts/assembly/dedup.py must define _v2_layer_cross_cluster_structural."
    )
    calls_helper = any(
        isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "_absent_content_key"
        for n in ast.walk(cross)
    )
    assert calls_helper, (
        "_v2_layer_cross_cluster_structural must build its 'absent' group key "
        "via _absent_content_key, not an ad-hoc/id()-based key."
    )


def test_cross_cluster_absent_key_not_id_based():
    """The cross-cluster structural layer must not use id(...) for any key.

    AST guard (not a substring scan) so the docstring's historical mention of
    'id(f)' does not trip the check. A live id(...) call inside this function
    would reintroduce the process-address-keyed, non-deterministic grouping.
    """
    tree = _dedup_ast()
    cross = _function_node(tree, "_v2_layer_cross_cluster_structural")
    assert cross is not None

    id_calls = [
        n
        for n in ast.walk(cross)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "id"
    ]
    assert not id_calls, (
        "_v2_layer_cross_cluster_structural calls id(...) -- the absent-finding "
        "group key must be content-derived (_absent_content_key), never id()-"
        "based, or determinism across runs/PYTHONHASHSEED breaks."
    )


def test_dedup_module_has_no_id_based_grouping_key_anywhere():
    """Belt-and-suspenders: no id(...) appears in executable code of dedup.py.

    The only legitimate reference to id(f) in this module is the historical
    note inside _absent_content_key's docstring; an AST walk ignores that and
    flags any real id(...) call site.
    """
    tree = _dedup_ast()
    id_calls = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "id"
    ]
    assert not id_calls, (
        f"scripts/assembly/dedup.py contains {len(id_calls)} id(...) call(s) in "
        f"executable code -- id() keys are process-dependent and break "
        f"determinism."
    )


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-v"]))
