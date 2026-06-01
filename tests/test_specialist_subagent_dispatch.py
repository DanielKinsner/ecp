"""test_specialist_subagent_dispatch.py

Phase H.2 (2026-06-01): Verify specialist dispatch migrated from Agent-Teams
(team_spawned_specialists counter) to GA one-shot subagents
(subagent_spawned_specialists counter). Consolidated guard tests for the
"cluster specialists off Agent Teams" migration. Functions are appended to this
file task-by-task so the suite stays green after each commit.

Run:
    python -m pytest tests/test_specialist_subagent_dispatch.py -v
"""
import re
import sys
import tempfile
import unittest
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.determinism_gate import parse_trace_assertions


def _read_repo_file(rel_path: str) -> str:
    """Read a contract / skill / script file relative to the repo root."""
    return (_REPO / rel_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Task 1 — determinism-gate counter-alias normalization
# ---------------------------------------------------------------------------
class TestSubagentSpecialistsCounterAlias(unittest.TestCase):
    """Verify counter normalization for the subagent_spawned_specialists migration.

    Post-migration the trace counter must use 'subagent_spawned_specialists' as
    the canonical name. The parser must accept both legacy v1
    'team_spawned_auditors' and intermediate v2 'team_spawned_specialists' and
    normalize both to the canonical name.
    """

    def test_v1_team_spawned_auditors_aliases_to_canonical(self):
        """V1 audit trace with team_spawned_auditors -> subagent_spawned_specialists."""
        with tempfile.TemporaryDirectory() as td:
            trace = Path(td) / "audit-trace.log"
            trace.write_text(
                """# ECP Audit Forensic Trace
# Engagement: test-v1
# Pipeline: v1
# ASSERTIONS:
#   expected_auditor_count: 10
#   team_spawned_auditors: 10
#   cluster_files_written: 10
#   ethics_gate_executed: true
""",
                encoding="utf-8",
            )
            result = parse_trace_assertions(trace)
            c = result["counters"]
            self.assertIn("subagent_spawned_specialists", c)
            self.assertEqual(c["subagent_spawned_specialists"], 10)
            self.assertNotIn(
                "team_spawned_auditors", c, "Alias should be folded to canonical name"
            )

    def test_v2_team_spawned_specialists_aliases_to_canonical(self):
        """Legacy v2 with team_spawned_specialists -> subagent_spawned_specialists."""
        with tempfile.TemporaryDirectory() as td:
            trace = Path(td) / "audit-trace.log"
            trace.write_text(
                """# ECP Audit Forensic Trace
# Engagement: test-v2-legacy
# Pipeline: v2
# ASSERTIONS:
#   expected_specialist_count: 20
#   team_spawned_specialists: 20
#   cluster_files_written: 20
#   subagent_spawned_synthesizer: 1
#   subagent_spawned_ethics: 1
#   ethics_gate_executed: true
""",
                encoding="utf-8",
            )
            result = parse_trace_assertions(trace)
            c = result["counters"]
            self.assertIn("subagent_spawned_specialists", c)
            self.assertEqual(c["subagent_spawned_specialists"], 20)
            self.assertNotIn(
                "team_spawned_specialists", c, "Alias should be folded to canonical name"
            )

    def test_new_subagent_spawned_specialists_direct(self):
        """New post-migration trace with subagent_spawned_specialists direct."""
        with tempfile.TemporaryDirectory() as td:
            trace = Path(td) / "audit-trace.log"
            trace.write_text(
                """# ECP Audit Forensic Trace
# Engagement: test-post-migration
# Pipeline: v2
# ASSERTIONS:
#   expected_specialist_count: 20
#   subagent_spawned_specialists: 20
#   cluster_files_written: 20
#   subagent_spawned_synthesizer: 1
#   subagent_spawned_ethics: 1
#   ethics_gate_executed: true
""",
                encoding="utf-8",
            )
            result = parse_trace_assertions(trace)
            c = result["counters"]
            self.assertIn("subagent_spawned_specialists", c)
            self.assertEqual(c["subagent_spawned_specialists"], 20)

    def test_mixed_legacy_and_canonical_both_map_correctly(self):
        """Edge case: trace has both legacy team_spawned_specialists and the canonical
        subagent_spawned_specialists. Documents last-write-wins behavior.
        """
        with tempfile.TemporaryDirectory() as td:
            trace = Path(td) / "audit-trace.log"
            trace.write_text(
                """# ECP Audit Forensic Trace
# Engagement: test-edge
# Pipeline: v2
# ASSERTIONS:
#   expected_specialist_count: 20
#   team_spawned_specialists: 15
#   subagent_spawned_specialists: 20
#   cluster_files_written: 20
#   subagent_spawned_synthesizer: 1
#   subagent_spawned_ethics: 1
#   ethics_gate_executed: true
""",
                encoding="utf-8",
            )
            result = parse_trace_assertions(trace)
            c = result["counters"]
            self.assertEqual(c["subagent_spawned_specialists"], 20)


# ---------------------------------------------------------------------------
# Task 2 — test-specialist.py --write-retry-prompt flag + Agent-dispatch wording
# ---------------------------------------------------------------------------
def test_test_specialist_supports_write_retry_prompt_and_agent_wording():
    """test-specialist.py must expose --write-retry-prompt on the `validate`
    subcommand and describe itself as an 'Agent' dispatch harness."""
    src = _read_repo_file("scripts/test-specialist.py")
    assert "--write-retry-prompt" in src, "validate must accept --write-retry-prompt"
    assert "specialist Agent dispatch" in src or "specialist Agent + synthesizer dispatch" in src, (
        "module/parser docstring should reference 'Agent' dispatch wording"
    )


# ---------------------------------------------------------------------------
# Task 3 — --max-concurrent documented in contracts/flags.md
# ---------------------------------------------------------------------------
def test_max_concurrent_flag_in_flags_md():
    """--max-concurrent must be documented in contracts/flags.md and supported by audit."""
    flags_md = _read_repo_file("contracts/flags.md")
    assert "--max-concurrent" in flags_md, (
        "--max-concurrent flag must be documented in contracts/flags.md per shared convention"
    )
    assert re.search(r"--max-concurrent.*?audit", flags_md, re.IGNORECASE | re.DOTALL), (
        "--max-concurrent must be listed as supported by /ecp:audit"
    )


if __name__ == "__main__":
    unittest.main()
