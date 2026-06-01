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


# ---------------------------------------------------------------------------
# Task 4 — dispatch-contract.md: specialist is a one-shot subagent
# ---------------------------------------------------------------------------
def test_specialist_dispatch_shape_is_subagent():
    """Cluster specialists dispatch as one-shot subagents, not teammates."""
    content = _read_repo_file("contracts/dispatch-contract.md")

    assert "| Cluster specialist (a.k.a. cluster auditor)" in content
    specialist_row = re.search(
        r"\| Cluster specialist.*?\| \*\*subagent\*\* \(Agent tool, no team_name\)",
        content,
        re.DOTALL,
    )
    assert specialist_row, "Cluster specialist should be listed as subagent dispatch shape"

    # The "How to dispatch each role in v2" table is 3-column
    # (Role | Template/prompt source | Tool call). Consume column 2 with [^|]*
    # so group(1) captures column 3 (the Tool call); a bare lazy `.*?` would
    # capture column 2 and the dispatch-call assertions could never hold.
    dispatch_table = re.search(
        r"\| Cluster specialist \| [^|]*\| (.*?) \|",
        content,
    )
    assert dispatch_table, "Cluster specialist dispatch table row exists"
    dispatch_call = dispatch_table.group(1)
    assert "team_name=" not in dispatch_call, "Specialist dispatch must NOT include team_name"
    assert "name=" not in dispatch_call, "Specialist dispatch must NOT include name"
    assert "description=" in dispatch_call, "Specialist dispatch MUST include description"
    assert 'subagent_type="general-purpose"' in dispatch_call, "Specialist uses Agent subagent_type"

    counter_row = re.search(
        r"\| Cluster specialist \| subagent \| `([^`]+)`", content
    )
    assert counter_row, "Counter row for cluster specialist exists"
    assert counter_row.group(1).startswith("subagent_spawned_specialists"), (
        f"Counter should be subagent_spawned_specialists, got {counter_row.group(1)}"
    )

    assert "### Why specialists are one-shot subagents" in content
    assert "### Why cluster specialists keep teammate status" not in content

    assert "--max-concurrent" in content
    assert "full-parallel" in content.lower() or "full parallel" in content.lower()
    assert "unlimited" in content

    waves_hardcoded = re.search(
        r"waves of ≤5 concurrent spawns.*?operational", content, re.DOTALL
    )
    assert waves_hardcoded is None, "Hardcoded waves-of-5 policy should be replaced"

    # Task/Agent alias note present (Task is the v2.1.63 legacy alias for Agent)
    assert "Task" in content and "alias" in content.lower()


# ---------------------------------------------------------------------------
# Task 5 — specialist-prompt-v2.md dispatch line drops team_name/name
# ---------------------------------------------------------------------------
def test_specialist_prompt_dispatch_line_has_no_team_name_or_name():
    """The dispatch instruction must not carry team_name / name=; No coordination preserved."""
    content = _read_repo_file("contracts/specialist-prompt-v2.md")
    dispatch_line = next(
        ln for ln in content.split("\n") if "The lead dispatches it via the Agent tool" in ln
    )
    assert "team_name" not in dispatch_line, "dispatch line must not include team_name"
    assert "name:" not in dispatch_line, "dispatch line must not include a name: parameter"
    assert "## No coordination" in content, "No coordination section must be preserved"
    assert "You do not SendMessage anyone." in content


# ---------------------------------------------------------------------------
# Task 6 — skills/audit/SKILL.md: one-shot specialists, no team creation
# ---------------------------------------------------------------------------
def test_cluster_specialists_no_team_name_in_dispatch_contract():
    """Cluster specialist dispatch template in dispatch-contract.md has no team_name."""
    dispatch_contract = _read_repo_file("contracts/dispatch-contract.md")
    # Capture column 3 (the Tool call) of the cluster-specialist dispatch-table row.
    # A broad `Cluster specialist.*?Agent(...)` span (DOTALL) would also sweep the
    # per-role table's "no team_name" prose and false-fail; anchor to the row and
    # grab the backticked Agent(...) call directly.
    agent_call = re.search(
        r"\| Cluster specialist \| [^|]*\| `(Agent\(subagent_type=.*?\))`",
        dispatch_contract,
    )
    assert agent_call is not None, "Cluster specialist dispatch template missing"
    assert "team_name" not in agent_call.group(1), (
        "Cluster specialist Agent call must NOT contain team_name in v2"
    )


def test_skill_md_no_team_create_for_audit():
    """Audit SKILL.md Phase Order must NOT create the audit team."""
    skill_md = _read_repo_file("skills/audit/SKILL.md")
    assert "Create the audit team" not in skill_md, (
        "Phase Order must NOT create audit team in v2 (specialists are one-shot subagents)"
    )


def test_skill_md_dispatch_shape_line():
    """Dispatch Shape section describes cluster specialists as one-shot subagents."""
    skill_md = _read_repo_file("skills/audit/SKILL.md")
    assert "one-shot subagent" in skill_md or "no `team_name`" in skill_md, (
        "Dispatch Shape must state cluster specialists are one-shot subagents"
    )
    assert "Agent` teammates in the audit team" not in skill_md, (
        "Cluster specialists must not be described as team teammates in v2"
    )


def test_skill_md_specialist_recovery_is_fresh_redispatch():
    """Specialist validation-failure recovery re-dispatches a fresh subagent, not SendMessage."""
    skill_md = _read_repo_file("skills/audit/SKILL.md")
    assert "--write-retry-prompt" in skill_md
    assert "fresh one-shot subagent" in skill_md
    assert "full-parallel" in skill_md.lower()
    assert "--max-concurrent" in skill_md


# ---------------------------------------------------------------------------
# Task 7 — audit-reconciliation.md Steps 0/0b/0c: fresh re-dispatch, not SendMessage
# ---------------------------------------------------------------------------
def test_validation_failure_triggers_subagent_not_sendmessage():
    """Steps 0/0b/0c rejections dispatch fresh one-shot subagents, not SendMessage."""
    content = _read_repo_file("contracts/audit-reconciliation.md")

    step_0 = content[content.find("## Step 0 — Format validation"):content.find("## Step 0b")]
    step_0b = content[content.find("## Step 0b — Voice check"):content.find("## Step 0c")]
    step_0c = content[content.find("## Step 0c — Evidence-anchor"):content.find("## Step 1")]

    for section, name in [(step_0, "Step 0"), (step_0b, "Step 0b"), (step_0c, "Step 0c")]:
        assert "Mark your task in_progress again while you rewrite" not in section, (
            f"{name}: still contains in-place SendMessage correction instruction"
        )
        assert 'Agent(subagent_type="general-purpose"' in section, f"{name}: missing Agent() dispatch"
        assert "test-specialist.py --write-retry-prompt" in section, (
            f"{name}: missing test-specialist.py --write-retry-prompt"
        )
        assert "team_name=" not in section, f"{name}: Agent() must not include team_name"
        assert 'model="sonnet"' in section, f'{name}: Agent() must specify model="sonnet"'

    # Validation logic preserved (delivery changes only)
    assert "code-fenced" in step_0
    assert "FINDING: FAIL" in step_0
    assert "identical TITLE" in step_0
    assert "voice check" in step_0b
    assert "jargon" in step_0b
    assert "evidence anchor" in step_0c
    assert "DOM selector" in step_0c


# ---------------------------------------------------------------------------
# Task 8 — lead-discipline.md terminology + preserved cancel.flag
# ---------------------------------------------------------------------------
def test_lead_discipline_terminology_and_preserved_sections():
    """teammate->subagent + SendMessage-retry->fresh re-dispatch; cancel.flag preserved."""
    content = _read_repo_file("contracts/lead-discipline.md")
    # Migrated section headings
    assert "## Acquisition must spawn subagent (binding rule)" in content
    assert "## Acquisition must spawn teammate (binding rule)" not in content
    assert "spawning the subagent" in content
    # Recovery via fresh one-shot subagent with embedded error (not SendMessage retry)
    assert "fresh one-shot subagent" in content
    assert "--write-retry-prompt" in content
    # Canonical counter wired into the self-check prose, aliases retained
    assert "subagent_spawned_specialists" in content
    assert "team_spawned_auditors" in content  # alias retained
    # Preserved sections intact
    assert "## Cancellation sentinel (cancel.flag)" in content
    assert "at EVERY layer boundary" in content
    assert "## Concurrent-audit isolation" in content


# ---------------------------------------------------------------------------
# Task 9 — ethics-subagent-v2.md + synthesizer-v2.md one-shot dispatch (no name/team_name)
# ---------------------------------------------------------------------------
def test_ethics_and_synthesizer_dispatch_have_no_name_or_team_name():
    """Both template line-16 dispatch sentences drop name:/team_name: and carry prompt=."""
    for fname in ("contracts/ethics-subagent-v2.md", "contracts/synthesizer-v2.md"):
        line_16 = _read_repo_file(fname).split("\n")[15]
        assert "name:" not in line_16, f"{fname} line 16 must not carry a name: parameter"
        assert "team_name" not in line_16, f"{fname} line 16 must not carry team_name"
        assert "prompt=" in line_16, f"{fname} line 16 must carry prompt="
        assert "subagent" in line_16.lower() or "Agent tool" in line_16, (
            f"{fname} line 16 should describe a one-shot subagent dispatch"
        )


# ---------------------------------------------------------------------------
# Task 10 — trace-assertion-canary.md canonical counter + retained aliases
# ---------------------------------------------------------------------------
def test_trace_header_accepts_subagent_spawned_specialists():
    """audit-trace.log header documents subagent_spawned_specialists; aliases retained."""
    contract = _read_repo_file("contracts/trace-assertion-canary.md")
    assert "subagent_spawned_specialists" in contract, (
        "subagent_spawned_specialists counter not found in v2 header definition"
    )
    assert "subagent_spawned_specialists >= expected_specialist_count" in contract, (
        "Alias rule missing: subagent_spawned_specialists primary assertion"
    )
    assert "team_spawned_specialists" in contract and "legacy" in contract.lower(), (
        "Legacy team_spawned_specialists path not documented as backwards-compatible"
    )
    assert "subagent_spawned_specialists" in contract and "team_spawned_specialists" in contract, (
        "Self-check must accept both one-shot and legacy specialist dispatch patterns"
    )


# ---------------------------------------------------------------------------
# Task 11 — team-lifecycle.md annotated dead-for-audit; parity harness archived
# ---------------------------------------------------------------------------
def test_team_lifecycle_annotated_and_parity_archived():
    """team-lifecycle.md marks audit-path dead (retained for multi-planner); parity harness archived."""
    lifecycle = _read_repo_file("contracts/team-lifecycle.md")
    assert "MIGRATION NOTICE" in lifecycle
    assert "DEAD for the audit path" in lifecycle
    assert "multi-planner" in lifecycle.lower()
    # Not deleted: the canonical lifecycle prose still present
    assert "# Agent Teams lifecycle" in lifecycle

    parity = _read_repo_file("scripts/test-cluster-specialist-parity.py")
    assert "ARCHIVED" in parity
    assert "not" in parity.lower() and "gate" in parity.lower()


if __name__ == "__main__":
    unittest.main()
