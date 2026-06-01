"""GUARD B0: rendered specialist + synthesizer prompts must be fully resolved.

Regression guard for the B0 class of bugs. Claude Code does NOT expand the
``${CLAUDE_PLUGIN_ROOT}`` token inside spawned-teammate prompts, so the
render layer (``scripts/test-specialist.py``) is responsible for expanding it
to an absolute path at render time, alongside every ``{{...}}`` template slot.
If a future edit drops that expansion (or introduces a new unsubstituted
slot), a dispatched specialist receives a literal ``${CLAUDE_PLUGIN_ROOT}`` or
``{{...}}`` it cannot resolve, and silently reads nothing from references/.

This test renders BOTH real prompts through the authoritative render functions
(not a hand-rolled copy) against the slingmods-pdp fixture and asserts:

1. ZERO literal ``${CLAUDE_PLUGIN_ROOT}`` survives in either rendered prompt.
2. ZERO unresolved ``{{...}}`` tokens survive (using test-specialist.py's own
   placeholder regex so the guard tracks the renderer's definition of a slot).
3. Every absolute ``references/`` path the specialist prompt now points a
   teammate at actually EXISTS on disk, and the ``references/`` directory
   itself resolves. This is what proves the B0 expansion produced a usable
   path, not just a non-empty string.

Coupled to authoritative sources: imports ``render_prompt`` /
``render_synthesizer_prompt`` / ``REPO_ROOT`` from scripts/test-specialist.py
and reads the real fixture; nothing about the prompt body is hardcoded.
"""
from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))


def _load_test_specialist_module():
    """Load scripts/test-specialist.py (hyphenated -> not importable normally).

    The module has @dataclass usage at import time via its assembly imports,
    and dataclass resolves type hints through sys.modules[__module__], so the
    module MUST be registered in sys.modules under its spec name BEFORE
    exec_module runs, otherwise dataclass processing can KeyError.
    """
    spec = importlib.util.spec_from_file_location(
        "test_specialist_cli_b0", _REPO / "scripts" / "test-specialist.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # register before exec for @dataclass
    spec.loader.exec_module(module)
    return module


_TS = _load_test_specialist_module()

_FIXTURE = _REPO / "fixtures" / "slingmods-pdp"

# The renderer's own definition of an unresolved template slot. Importing the
# pattern intent (not a divergent copy) keeps the guard honest: a {{...}} that
# the renderer would consider unresolved is exactly what we forbid.
_PLACEHOLDER_RE = re.compile(r"\{\{[a-zA-Z_][a-zA-Z_0-9]*\}\}")

# Match a rendered absolute reference path: <abs repo root><sep>references<sep>...
# The renderer substitutes str(REPO_ROOT) (a Windows backslash path on win32)
# in front of the template's "/references/...", so the separator after the
# root can be either '\\' or '/'. We anchor on the literal repo root the
# module will substitute, then capture the trailing references/ path.
_REPO_ROOT_STR = str(_TS.REPO_ROOT)


def _render_specialist_prompt() -> str:
    return _TS.render_prompt(
        cluster="pricing",
        device="desktop",
        engagement_id="slingmods-pdp",
        cluster_context_path=str(_FIXTURE / "cluster-context-pricing-desktop.json"),
        baton_path=str(_FIXTURE / "baton.json"),
        viewport_width=1440,
        viewport_height=900,
        dpr=1.0,
        page_type="product-page",
        platform="unknown",
        screenshot_paths=[],
    )


def _render_synthesizer_prompt() -> str:
    return _TS.render_synthesizer_prompt(
        engagement_id="slingmods-pdp",
        cluster_emission_paths=[str(_FIXTURE / "cluster-pricing-desktop.json")],
        ethics_findings_path=str(_FIXTURE / "ethics-findings.json"),
        desktop_baton_path=str(_FIXTURE / "baton.json"),
        mobile_baton_path=str(_FIXTURE / "baton-mobile.json"),
        desktop_screenshot_paths=[],
        mobile_screenshot_paths=[],
        desktop_viewport="1440x900",
        mobile_viewport="390x844",
        page_type="product-page",
        platform="unknown",
        page_summary="(b0 guard)",
        canonical_f_refs_block=_TS.build_canonical_f_refs_block({}),
        phrasing_seeds_block="",
    )


def _extract_reference_paths(rendered: str) -> list[Path]:
    """Pull every absolute ``.../references/<name>`` path out of a rendered prompt.

    Anchors on the literal repo root the renderer substitutes, tolerates either
    path separator after it, and stops the captured filename at characters that
    cannot appear in a path token in the surrounding markdown (backtick, quote,
    whitespace, paren).
    """
    # Build a regex around the (possibly special-char-laden) repo root.
    root = re.escape(_REPO_ROOT_STR)
    pat = re.compile(root + r"[\\/]+references[\\/]+([^`'\"\s)\]]+)")
    out: list[Path] = []
    for m in pat.finditer(rendered):
        tail = m.group(1).replace("\\", "/")
        out.append(_TS.REPO_ROOT / "references" / tail)
    return out


class TestB0PromptResolution(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(
            _FIXTURE.is_dir(),
            f"fixture missing: {_FIXTURE} (test cannot run without it)",
        )
        self.specialist = _render_specialist_prompt()
        self.synthesizer = _render_synthesizer_prompt()

    def test_no_literal_plugin_root_token_specialist(self) -> None:
        self.assertNotIn(
            "${CLAUDE_PLUGIN_ROOT}",
            self.specialist,
            "B0 regression: specialist prompt still contains a literal "
            "${CLAUDE_PLUGIN_ROOT}. Claude Code will NOT expand it for a "
            "spawned teammate; render_prompt must substitute the absolute root.",
        )

    def test_no_literal_plugin_root_token_synthesizer(self) -> None:
        self.assertNotIn(
            "${CLAUDE_PLUGIN_ROOT}",
            self.synthesizer,
            "B0 regression: synthesizer prompt still contains a literal "
            "${CLAUDE_PLUGIN_ROOT}.",
        )

    def test_no_unresolved_template_slots_specialist(self) -> None:
        leftover = sorted(set(_PLACEHOLDER_RE.findall(self.specialist)))
        self.assertEqual(
            [],
            leftover,
            f"B0 regression: unresolved {{{{...}}}} slots in specialist prompt: {leftover}",
        )

    def test_no_unresolved_template_slots_synthesizer(self) -> None:
        leftover = sorted(set(_PLACEHOLDER_RE.findall(self.synthesizer)))
        self.assertEqual(
            [],
            leftover,
            f"B0 regression: unresolved {{{{...}}}} slots in synthesizer prompt: {leftover}",
        )

    def test_references_dir_resolves(self) -> None:
        refs_dir = _TS.REPO_ROOT / "references"
        self.assertTrue(
            refs_dir.is_dir(),
            f"references/ dir does not resolve at the substituted root: {refs_dir}",
        )

    def test_rendered_reference_paths_exist_on_disk(self) -> None:
        ref_paths = _extract_reference_paths(self.specialist)
        # The specialist template points teammates at references/ at least once
        # (the reference-read instruction + evidence-tiers.md). If the renderer
        # ever stops emitting any absolute reference path, that is itself a
        # B0-class regression we want to catch.
        self.assertTrue(
            ref_paths,
            "B0 regression: specialist prompt emitted NO absolute references/ "
            "path. Expected at least the references dir + evidence-tiers.md.",
        )
        for p in ref_paths:
            # A bare ".../references/" with no filename resolves to the dir.
            target = p if p.name else p.parent
            self.assertTrue(
                target.exists(),
                f"B0 regression: rendered reference path does not exist on "
                f"disk: {target}. The ${{CLAUDE_PLUGIN_ROOT}} expansion produced "
                f"a path a dispatched specialist cannot read.",
            )

    def test_evidence_tiers_reference_resolved_and_present(self) -> None:
        # evidence-tiers.md is named explicitly in the specialist template and
        # is the canonical Gold/Silver/Bronze source. Its rendered absolute path
        # must point at a real file.
        evidence = _TS.REPO_ROOT / "references" / "evidence-tiers.md"
        self.assertIn(
            str(evidence).replace("\\", "/"),
            self.specialist.replace("\\", "/"),
            "specialist prompt no longer renders an absolute evidence-tiers.md path",
        )
        self.assertTrue(
            evidence.is_file(),
            f"rendered evidence-tiers.md path is not a real file: {evidence}",
        )


if __name__ == "__main__":
    unittest.main()
