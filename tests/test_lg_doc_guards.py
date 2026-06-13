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


if __name__ == "__main__":
    unittest.main()
