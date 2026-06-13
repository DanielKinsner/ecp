"""LG9-LG16 + Minor (2026-06-12 live gate) — doc/contract reconciliation
grep-guards.

These contracts and SKILL.md are LOAD-BEARING: the audit lead reads them at
runtime, so their wording IS the contract. Each guard pins the corrected
wording so a future edit can't silently re-introduce the contradiction the
live gate surfaced. Doc-only changes; no runtime Python behavior depends on
the assertions here beyond the wording itself.
"""
from __future__ import annotations

import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent


def _read(*parts: str) -> str:
    return (_REPO.joinpath(*parts)).read_text(encoding="utf-8")


def _section(text: str, start_header: str, end_header: str) -> str:
    start = text.index(start_header)
    end = text.index(end_header, start + len(start_header))
    return text[start:end]


class TestLG9LoadOrderRepoRootAnchor(unittest.TestCase):
    """LG9: the Runtime Load Order section gave no base anchor, so a lead
    resolved the bare ``contracts/*`` paths against skills/audit/ and the first
    6 Reads failed. The section must state the paths resolve from the repo
    root (matching the shell-command anchor in the next section)."""

    def test_runtime_load_order_states_repo_root(self):
        skill = _read("skills", "audit", "SKILL.md")
        section = _section(
            skill, "## Runtime Load Order", "## Validation, Synthesis, and Rendering"
        )
        self.assertIn("repo root", section)

    def test_load_order_paths_resolve_from_repo_root(self):
        for rel in (
            "contracts/lead-discipline.md",
            "contracts/flags.md",
            "contracts/audit-state-machine.md",
            "contracts/dispatch-contract.md",
            "contracts/device-semantics.md",
            "contracts/meta-schema.md",
        ):
            self.assertTrue((_REPO / rel).exists(), f"{rel} must exist at repo root")


class TestLG11NormalizeExampleNamesProposedAnchor(unittest.TestCase):
    """LG11: SKILL.md's normalize example "a stray-anchor removal" was read as
    evidence_anchors (not in NORMALIZE_ALLOWED_FIELDS), but the supported
    mechanism is a whole-block proposed_anchor removal via the `<delete>`
    sentinel. Name the allowlisted field so the example isn't misleading."""

    def test_normalize_example_names_proposed_anchor(self):
        skill = _read("skills", "audit", "SKILL.md")
        idx = skill.index("a surface-field correction")
        end = skill.index("coercion", idx)
        para = skill[idx : end + len("coercion")]
        self.assertIn("proposed_anchor", para)
        self.assertNotIn("stray-anchor removal", para)


class TestLG16EthicsAdjacentHedgeCoversAllFields(unittest.TestCase):
    """LG16 (already enforced — regression pin): the ethics ADJACENT hedge rule
    already covers observation, recommendation, AND why_this_matters (the canary
    ethics_findings_hedge_law_on_adjacent scans all three). Pin the contract so a
    future edit can't silently drop why_this_matters from the carve-out."""

    def test_adjacent_carveout_names_all_three_prose_fields(self):
        ethics = _read("contracts", "ethics-subagent-v2.md")
        idx = ethics.index("ADJACENT carve-out")
        para = ethics[idx : idx + 700]
        for field in ("observation", "recommendation", "why_this_matters"):
            self.assertIn(field, para)
        self.assertIn("MUST hedge", para)


class TestLGMinorPrepareSynthHelpScope(unittest.TestCase):
    """LG-MINOR: the --cluster-emission help said "10 specialists per device",
    which only holds under --focus all. The canonical scope is page-type-aware
    (2-10 per contracts/cluster-routing.md; product-page standard is 6)."""

    def test_help_string_not_stale_specialist_count(self):
        src = _read("scripts", "test-specialist.py")
        self.assertNotIn("10 specialists per device", src)
        self.assertIn("per cluster per device", src)


class TestLGMinorAcquireSchemaVersionDisambiguation(unittest.TestCase):
    """LG-MINOR: a baton with schema_version: 1 inside a meta schema_version: 3
    engagement read as a contradiction. acquire.md's Implementation note must
    state baton- and meta-schema versioning are separate axes."""

    def test_acquire_note_disambiguates_schema_axes(self):
        acquire = _read("workflows", "acquire.md")
        self.assertIn(
            "baton schema versioning and meta schema versioning are separate axes",
            acquire,
        )


class TestLG10DeviceKeyedNaming(unittest.TestCase):
    """LG10: device-semantics.md prescribed ORDER-keyed naming (first device
    bare, second `-{device}`, table showing `baton-desktop.json`) but the
    runtime is DEVICE-keyed — mobile gets `-mobile`, non-mobile (desktop/laptop)
    is bare. `baton-desktop.json` is never written by acquisition."""

    def test_doc_states_device_keyed(self):
        doc = _read("contracts", "device-semantics.md")
        self.assertIn("device-keyed", doc)
        self.assertNotIn("baton-desktop.json", doc)

    def test_runtime_writes_device_keyed_baton(self):
        acq = _read("scripts", "acquire_url.py")
        self.assertIn("baton-mobile.json", acq)
        self.assertIn('"baton.json"', acq)
        self.assertNotIn("baton-desktop.json", acq)

    def test_skill_artifact_contract_has_no_desktop_or_laptop_baton_literal(self):
        skill = _read("skills", "audit", "SKILL.md")
        self.assertNotIn("baton-desktop.json", skill)
        self.assertNotIn("baton-laptop.json", skill)


class TestLG12V2LoaderDocumented(unittest.TestCase):
    """LG12: the v2 Findings loader (assembly.json_parser.parse_emission_file(s))
    exists and is used in production (lead_prep.py), but SKILL.md's trim step
    didn't name it — leaving the lead to improvise — and assembly/parser.py (the
    v1 markdown loader, FileNotFoundError on v2) wasn't in the "do NOT run" list.
    """

    def test_skill_trim_step_names_v2_loader(self):
        skill = _read("skills", "audit", "SKILL.md")
        step3 = _section(
            skill, "Trim each device baton", "Prepare and dispatch the synthesizer"
        )
        self.assertIn("json_parser", step3)

    def test_dont_run_list_names_v1_markdown_loader(self):
        skill = _read("skills", "audit", "SKILL.md")
        idx = skill.index("Legacy v1 tools")
        para = skill[idx : idx + 800]
        self.assertIn("assembly/parser.py", para)
        self.assertIn("load_all_cluster_files", para)

    def test_determinism_gate_has_no_phantom_trim_cli(self):
        src = _read("scripts", "run-determinism-gate.py")
        self.assertNotIn("synth_input.py trim-batons", src)


if __name__ == "__main__":
    unittest.main()
