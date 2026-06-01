"""Regression guard for the synthesizer dispatch f_ref contract.

This test pins the contract that ties the canonical f_refs manifest to the
synthesizer dispatch prompt:

  1. The canonical f_refs manifest is built from a fixture's cluster
     emissions via the REAL lead-prep path -- ``lead_prep.build_canonical_frefs``,
     which delegates to ``report.v2_loader.build_canonical_view`` (cluster
     emissions + ethics, deduped, content-hash display indices). We import
     those functions rather than re-deriving f_refs, so the test cannot drift
     from the authoritative allowlist the renderer enforces.

  2. The synthesizer dispatch prompt is rendered via the REAL
     ``scripts/test-specialist.py`` ``render_synthesizer_prompt`` /
     ``build_canonical_f_refs_block`` path (the same code the
     ``prepare-synthesizer`` CLI runs).

  3. The rendered prompt MUST have no unresolved ``{{...}}`` or ``${...}``
     placeholder tokens left behind, and it MUST reference the manifest it was
     built from (the canonical f_refs appear verbatim in the prompt).

  4. A small/empty render (empty manifest, no emissions) MUST NOT crash --
     the dispatch path degrades gracefully rather than raising.

The test is hermetic: it copies only the cluster emission + ethics files out
of the checked-in fixture into a temp engagement dir, builds the manifest
there, and renders from in-repo template sources. Nothing is written under the
real fixture tree. It is Windows-safe: no non-ASCII in source or printed
output, and ``test-specialist.py`` (hyphenated) is loaded via importlib and
registered in ``sys.modules`` before ``exec_module`` so its module-scope
``@dataclass`` decorators resolve.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

import pytest

# --------------------------------------------------------------------------
# Repo layout: scripts/ is on sys.path so modules import as
# `from report.X import ...` / `import lead_prep`.
# --------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
FIXTURE_DIR = REPO_ROOT / "fixtures" / "slingmods-pdp"
TEST_SPECIALIST_PATH = SCRIPTS_DIR / "test-specialist.py"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_test_specialist():
    """Load the hyphenated scripts/test-specialist.py module.

    It must be registered in sys.modules under a stable name BEFORE
    exec_module, because it defines @dataclass at module scope and the
    dataclass machinery looks the module up by __name__ during class
    creation.
    """
    spec = importlib.util.spec_from_file_location(
        "test_specialist", TEST_SPECIALIST_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["test_specialist"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def lead_prep_mod():
    if not TEST_SPECIALIST_PATH.is_file():
        pytest.skip("scripts/test-specialist.py not present")
    return importlib.import_module("lead_prep")


@pytest.fixture(scope="module")
def specialist_mod():
    if not TEST_SPECIALIST_PATH.is_file():
        pytest.skip("scripts/test-specialist.py not present")
    return _load_test_specialist()


@pytest.fixture
def hermetic_engagement(tmp_path: Path) -> Path:
    """Copy only the cluster emissions + ethics from the slingmods fixture
    into a temp engagement dir. Hermetic: nothing is written under the real
    fixture, and the manifest artifacts land in tmp_path."""
    if not FIXTURE_DIR.is_dir():
        pytest.skip("slingmods-pdp fixture not present")
    eng = tmp_path / "engagement"
    eng.mkdir()
    copied = 0
    for path in sorted(FIXTURE_DIR.glob("cluster-*.json")):
        # cluster-context-* are DOM slices, not emissions -- the real
        # _cluster_emissions / _engagement_cluster_emission_paths skip them,
        # but copying them too lets us prove the skip is exercised end to end.
        shutil.copy2(path, eng / path.name)
        copied += 1
    ethics = FIXTURE_DIR / "ethics-findings.json"
    if ethics.is_file():
        shutil.copy2(ethics, eng / "ethics-findings.json")
    assert copied > 0, "fixture should contain cluster emission files"
    return eng


# --------------------------------------------------------------------------
# Token guards
# --------------------------------------------------------------------------
# {{name}} mustache-style placeholders the renderer substitutes.
CURLY_TOKEN_RE = re.compile(r"\{\{[a-zA-Z_][a-zA-Z_0-9]*\}\}")
# ${NAME} shell-style placeholders (e.g. ${CLAUDE_PLUGIN_ROOT}) the renderer
# expands at render time so spawned teammates get absolute paths.
DOLLAR_TOKEN_RE = re.compile(r"\$\{[A-Za-z_][A-Za-z_0-9]*\}")


def _build_manifest(lead_prep_mod, engagement: Path) -> dict:
    """Run the REAL lead-prep manifest builder over the engagement dir and
    return the parsed canonical-f-refs.json (the shape the synthesizer
    dispatch consumes)."""
    rc = lead_prep_mod.build_canonical_frefs(engagement)
    assert rc == 0, f"build_canonical_frefs returned {rc} (expected 0, clean run)"
    consumer_path = engagement / "canonical-f-refs.json"
    assert consumer_path.is_file(), "build must write canonical-f-refs.json"
    data = json.loads(consumer_path.read_text(encoding="utf-8"))
    assert set(data.keys()) >= {"valid_refs", "by_canonical_ref"}
    return data


def test_manifest_builds_from_fixture_via_real_lead_prep(
    lead_prep_mod, hermetic_engagement
):
    """The canonical f_refs manifest builds from the fixture's cluster
    emissions via the real lead_prep -> v2_loader path and is non-empty."""
    data = _build_manifest(lead_prep_mod, hermetic_engagement)

    valid_refs = data["valid_refs"]
    by_ref = data["by_canonical_ref"]
    assert valid_refs, "manifest must contain at least one canonical f_ref"
    assert len(valid_refs) == len(by_ref), "valid_refs must mirror by_canonical_ref"

    # Every ref is the renderer's allowlist key shape: "{cluster} F-{NN}".
    ref_shape = re.compile(r"^[a-z0-9-]+ F-\d{2}$")
    for ref in valid_refs:
        assert ref_shape.match(ref), f"unexpected canonical ref shape: {ref!r}"

    # build_canonical_view loads cluster emissions AND ethics-findings.json;
    # the fixture carries an ethics emission, so ethics refs must be present.
    assert any(r.startswith("ethics F-") for r in valid_refs), (
        "ethics emission should contribute refs to the canonical view"
    )


def test_rendered_synthesizer_prompt_has_no_unresolved_tokens_and_cites_manifest(
    lead_prep_mod, specialist_mod, hermetic_engagement
):
    """Full render: the synthesizer dispatch prompt resolves every template
    placeholder and embeds the canonical f_refs manifest verbatim."""
    data = _build_manifest(lead_prep_mod, hermetic_engagement)

    # Render the manifest block via the REAL formatter, then the full prompt
    # via the REAL renderer -- the exact path `prepare-synthesizer` runs.
    block = specialist_mod.build_canonical_f_refs_block(data)

    emission_paths = sorted(
        str(p)
        for p in hermetic_engagement.glob("cluster-*.json")
        if not p.name.startswith("cluster-context-")
    )
    assert emission_paths, "expected cluster emission paths for the dispatch"

    rendered = specialist_mod.render_synthesizer_prompt(
        engagement_id="slingmods-pdp",
        cluster_emission_paths=emission_paths,
        ethics_findings_path=str(hermetic_engagement / "ethics-findings.json"),
        desktop_baton_path=str(FIXTURE_DIR / "baton.json"),
        mobile_baton_path=str(FIXTURE_DIR / "baton-mobile.json"),
        desktop_screenshot_paths=[],
        mobile_screenshot_paths=[],
        desktop_viewport="1440x900",
        mobile_viewport="390x844",
        page_type="product-page",
        platform="shopify",
        page_summary="hermetic regression render",
        canonical_f_refs_block=block,
    )

    assert isinstance(rendered, str) and rendered.strip()

    # No unresolved placeholders of either flavor.
    curly = sorted(set(CURLY_TOKEN_RE.findall(rendered)))
    dollar = sorted(set(DOLLAR_TOKEN_RE.findall(rendered)))
    assert not curly, f"unresolved curly placeholders remain: {curly}"
    assert not dollar, f"unresolved dollar placeholders remain: {dollar}"

    # The prompt must actually reference the manifest it was built from:
    # the formatted block is embedded, and the canonical refs appear verbatim.
    assert block in rendered, "rendered prompt must embed the manifest block"
    for ref in data["valid_refs"][:5]:
        assert ref in rendered, f"canonical ref {ref!r} missing from prompt"


def test_empty_manifest_and_no_emissions_render_does_not_crash(specialist_mod):
    """Degenerate small case: an empty manifest and no cluster emissions must
    render a prompt (with safe placeholder prose) rather than raising, and
    still leave no unresolved template tokens."""
    block = specialist_mod.build_canonical_f_refs_block(
        {"valid_refs": [], "by_canonical_ref": {}}
    )
    assert isinstance(block, str) and block.strip()

    rendered = specialist_mod.render_synthesizer_prompt(
        engagement_id="empty-case",
        cluster_emission_paths=[],
        ethics_findings_path="/nonexistent/ethics-findings.json",
        desktop_baton_path="/nonexistent/baton.json",
        mobile_baton_path="/nonexistent/baton-mobile.json",
        desktop_screenshot_paths=[],
        mobile_screenshot_paths=[],
        desktop_viewport="1440x900",
        mobile_viewport="390x844",
        page_type="product-page",
        platform="unknown",
        page_summary="(no page summary supplied)",
        canonical_f_refs_block=block,
    )

    assert isinstance(rendered, str) and rendered.strip()
    assert not CURLY_TOKEN_RE.findall(rendered), "empty render left curly tokens"
    assert not DOLLAR_TOKEN_RE.findall(rendered), "empty render left dollar tokens"
    # The empty-manifest block is still embedded (the dispatch carries the
    # "no canonical f_refs supplied" prose forward rather than dropping it).
    assert block in rendered
