---
# Migrate Cluster Specialists Off Agent Teams (GA One-Shot Subagents) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate cluster specialists from Agent-Teams teammates to GA parallel one-shot subagents — retiring the last Agent-Teams teammate role in the audit path while preserving the file-presence lead loop, changing only recovery delivery and concurrency control.

**Architecture:** Cluster specialists flip from Agent-Teams teammates to GA one-shot subagents (the same dispatch shape acquirer/ethics/synthesizer already use). The lead loop — file-presence collection (`glob cluster-{cluster}-{device}.json`), validate→autofix→re-dispatch — is preserved verbatim because it keys off files on disk, not team state. Recovery changes from a SendMessage-bounce to the still-alive teammate into a fresh re-dispatch of a one-shot subagent with the validation error embedded. Concurrency becomes full-parallel by default (all requested clusters in one message) with a `--max-concurrent N` fallback (default = all/unlimited) that restores batched waves if the server-side concurrent-spawn rate limit bites.

**Tech Stack:** Python 3 + pytest; ECP markdown contracts; Claude Code Agent tool dispatch.

**MEASURE-TWICE — read before editing:** The before/after text quoted in each task comes from a read-only drafting pass; line numbers are approximate. Before each edit, READ the target file and confirm the exact current text. If the quoted "before" does not match exactly, re-read and adjust — the live file is the source of truth. Every edit is an exact-string replacement (the editor enforces an exact match, so a stale quote fails loudly rather than corrupting the file).

**COMMIT DISCIPLINE:** One commit per task. Conventional message (feat/fix/docs/test/refactor + scope), body ends with:
`Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`
The test suite MUST be green after every commit.

---

## Conventions for this plan

- **Working directory** is the repo root (`C:\Users\SM - Dan\Documents\GitHub\ecp`). All commands are Windows / `python -m pytest ...`.
- **ONE new test file**, `tests/test_specialist_subagent_dispatch.py`, is created in Task 1 and APPENDED to in subsequent tasks so the suite stays green after every commit. All `kind=="new"` guard tests merge into this single file (deduped imports + helpers, distinct function names). `kind=="update"` guard tests against existing test files land in Task 12.
- **Counter naming (consistency rule):** canonical counter is `subagent_spawned_specialists`. `team_spawned_specialists` AND `team_spawned_auditors` are retained as accepted backwards-compat aliases — **never remove alias logic.**
- **Specialist dispatch call (consistency rule):** `Agent(subagent_type="general-purpose", description="<short>", model="sonnet"` (or `"opus"` with `--deep`)`, prompt=<rendered>)`. **NO `team_name`, NO `name`.** `Task` is the v2.1.63 legacy alias for `Agent` (both work); the broad `Task`→`Agent` rename of the OTHER one-shot roles is OUT OF SCOPE (see Task 4 note).
- **Rationale hygiene (consistency rule):** specialists become one-shot subagents **like the other roles**; do NOT justify any special status by "shared workspace" and do NOT draw a Task-vs-Agent distinction between specialists and acquirer/ethics/synthesizer. File-presence collection (`glob cluster-{cluster}-{device}.json`) is transport-independent — that is why the flip is safe.
- **Recovery (consistency rule):** validation failure → `scripts/test-specialist.py --write-retry-prompt` → dispatch a FRESH one-shot subagent with the error embedded → on 2nd failure mark `partial` / fall back. Never SendMessage.

---

## Task 1 — determinism_gate.py counter-alias normalization (+ create the consolidated test file)

**Files:**
- Modify: `scripts/assembly/determinism_gate.py`
- Test (create): `tests/test_specialist_subagent_dispatch.py`

- [ ] **Write the failing guard test.** Create `tests/test_specialist_subagent_dispatch.py` with the module docstring, shared imports/helpers, and the determinism-gate-alias test class. FULL initial file:

```python
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Run it — expected FAIL.** Reason: `determinism_gate._TRACE_COUNTER_ALIASES` still maps `team_spawned_auditors → team_spawned_specialists` (not the canonical `subagent_spawned_specialists`), and `team_spawned_specialists` is not yet an alias, so both `test_v1_*` and `test_v2_*` fail with `subagent_spawned_specialists` missing from `counters`.

```
python -m pytest tests/test_specialist_subagent_dispatch.py::TestSubagentSpecialistsCounterAlias -v
```

- [ ] **Edit 1 — `scripts/assembly/determinism_gate.py` lines 68-73 (`_TRACE_COUNTER_ALIASES`).**

BEFORE:
```python
_TRACE_COUNTER_ALIASES = {
    "team_spawned_auditors": "team_spawned_specialists",
    "team_spawned_acquirers": "subagent_spawned_acquirers",
    "expected_auditor_count": "expected_specialist_count",
    "model_cluster_auditors": "model_cluster_specialists",
}
```

AFTER:
```python
_TRACE_COUNTER_ALIASES = {
    "team_spawned_auditors": "subagent_spawned_specialists",
    "team_spawned_specialists": "subagent_spawned_specialists",
    "team_spawned_acquirers": "subagent_spawned_acquirers",
    "expected_auditor_count": "expected_specialist_count",
    "model_cluster_auditors": "model_cluster_specialists",
}
```

- [ ] **Edit 2 — `scripts/assembly/determinism_gate.py` lines 76-89 (`_INT_COUNTERS`).**

BEFORE:
```python
_INT_COUNTERS = {
    "tasks_created_total",
    "expected_specialist_count",
    "subagent_spawned_acquirers",
    "team_spawned_specialists",
    "subagent_spawned_ethics",
    "subagent_spawned_synthesizer",
    "subagent_spawned_planner",
    "team_spawned_planners",
    "subagent_spawned_reviewer",
    "subagent_spawned_builder",
    "cluster_files_written",
    "idle_notification_total",
}
```

AFTER:
```python
_INT_COUNTERS = {
    "tasks_created_total",
    "expected_specialist_count",
    "subagent_spawned_acquirers",
    "subagent_spawned_specialists",
    "subagent_spawned_ethics",
    "subagent_spawned_synthesizer",
    "subagent_spawned_planner",
    "team_spawned_planners",
    "subagent_spawned_reviewer",
    "subagent_spawned_builder",
    "cluster_files_written",
    "idle_notification_total",
}
```

- [ ] **Run the test — expected PASS.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py::TestSubagentSpecialistsCounterAlias -v
```

- [ ] **Run the suite subset.** The determinism gate suite must stay green with the new alias map.

```
python -m pytest tests/test_v2_determinism_gate.py tests/test_specialist_subagent_dispatch.py -q
```

> NOTE: if `tests/test_v2_determinism_gate.py` hardcodes `team_spawned_specialists` as a dict key, it is updated in **Task 12** (those edits accept the canonical counter). If a pre-existing assertion in that file goes red here purely from the alias re-pointing, run only `tests/test_specialist_subagent_dispatch.py` for the green-after-commit gate on this task and land the `test_v2_determinism_gate.py` fixes in Task 12 — but verify first, since the alias still resolves `team_spawned_specialists` → `subagent_spawned_specialists` and most assertions read the normalized value.

- [ ] **Commit.**

```
git add scripts/assembly/determinism_gate.py tests/test_specialist_subagent_dispatch.py
git commit -m "feat(determinism-gate): normalize specialist counter aliases to subagent_spawned_specialists

Map team_spawned_auditors and team_spawned_specialists to the canonical
subagent_spawned_specialists; swap _INT_COUNTERS to the canonical name.
Adds the consolidated guard-test file for the specialists-off-Agent-Teams
migration.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2 — scripts/test-specialist.py: --write-retry-prompt + docstring "Agent dispatch" wording

**Files:**
- Modify: `scripts/test-specialist.py`
- Test (append): `tests/test_specialist_subagent_dispatch.py`

- [ ] **Append the failing guard test** to `tests/test_specialist_subagent_dispatch.py`:

```python
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
```

- [ ] **Run it — expected FAIL** (if the live file does not yet carry the `--write-retry-prompt` flag and/or the "Agent dispatch" wording). Reason: the harness docstrings still use the pre-migration "specialist dispatch" / "specialist + synthesizer dispatch" wording, and (if absent) the `--write-retry-prompt` argument is not registered.

```
python -m pytest tests/test_specialist_subagent_dispatch.py::test_test_specialist_supports_write_retry_prompt_and_agent_wording -v
```

> MEASURE-TWICE: the design's §3.3 decision is to "**add** a `--write-retry-prompt` flag mirroring the synthesizer's." The drafting pass found a `--write-retry-prompt` block already present on `validate` (lines ~1100-1108) — confirm in the live file. If it is already present, the only edit is the docstring clarification below + the two "Agent dispatch" wording edits. If it is absent, add the argument exactly as the AFTER block shows.

- [ ] **Edit 1 — module docstring (lines ~38-39).**

BEFORE:
```python
#!/usr/bin/env python3
"""test-specialist.py — Split-mode harness for v2 specialist + synthesizer dispatch.
```

AFTER:
```python
#!/usr/bin/env python3
"""test-specialist.py — Split-mode harness for v2 specialist Agent + synthesizer dispatch.
```

- [ ] **Edit 2 — `main()` argparse description (lines ~1005-1012).**

BEFORE:
```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="test-specialist.py",
        description=(
            "Split-mode harness for v2 specialist dispatch."
            " 'prepare' renders the dispatch prompt; 'validate' checks an emission."
        ),
    )
```

AFTER:
```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="test-specialist.py",
        description=(
            "Split-mode harness for v2 specialist Agent dispatch."
            " 'prepare' renders the dispatch prompt; 'validate' checks an emission."
        ),
    )
```

- [ ] **Edit 3 — `validate` subcommand `--write-retry-prompt` (lines ~1100-1108).** Add the argument if absent; otherwise clarify the help text.

BEFORE:
```python
    p_validate.add_argument("--expect-cluster", help="Optional: assert emission.cluster matches.")
    p_validate.add_argument(
        "--expect-engagement-id", help="Optional: assert emission.engagement_id matches."
    )
    p_validate.add_argument(
        "--write-retry-prompt",
        type=Path,
        help="If set and validation fails, write the retry prompt to this path.",
    )
```

AFTER:
```python
    p_validate.add_argument("--expect-cluster", help="Optional: assert emission.cluster matches.")
    p_validate.add_argument(
        "--expect-engagement-id", help="Optional: assert emission.engagement_id matches."
    )
    p_validate.add_argument(
        "--write-retry-prompt",
        type=Path,
        help="If set and validation fails, write a retry prompt to this path. For specialist (cluster-emission) validates, contains business-rule violations and schema errors. For synthesizer (synthesizer-emission) validates, contains hallucinated refs and schema errors.",
    )
```

- [ ] **Run the test — expected PASS.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py::test_test_specialist_supports_write_retry_prompt_and_agent_wording -v
```

- [ ] **Run the suite subset** (specialist harness tests must stay green).

```
python -m pytest tests/test_specialist_subagent_dispatch.py -q
python -m pytest tests/ -q -k "specialist or retry"
```

- [ ] **Commit.**

```
git add scripts/test-specialist.py tests/test_specialist_subagent_dispatch.py
git commit -m "feat(test-specialist): document --write-retry-prompt for fresh re-dispatch; Agent-dispatch wording

Mirror the synthesizer retry-prompt path for specialists and align the
harness docstrings with the Agent one-shot dispatch model.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3 — contracts/flags.md: document --max-concurrent N (default = all/unlimited)

**Files:**
- Modify: `contracts/flags.md`
- Test (append): `tests/test_specialist_subagent_dispatch.py`

- [ ] **Append the failing guard test:**

```python
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
```

- [ ] **Run it — expected FAIL.** Reason: `contracts/flags.md` has no `--max-concurrent` section yet.

```
python -m pytest tests/test_specialist_subagent_dispatch.py::test_max_concurrent_flag_in_flags_md -v
```

- [ ] **Edit — append a `--max-concurrent` section after the `--deep` section** (lines ~115-137). Replace the `--deep` block with the same block plus the new section appended:

BEFORE:
```markdown
## `--deep`

**Type:** boolean (no value).
**Default:** false.
**Supported by:** `/ecp:audit`, `/ecp:build`, `/ecp:compare`, `/ecp:quick-scan`.

Route cluster auditors and builder to `opus` instead of the default `sonnet`. Use when:
- Comparing heavily-designed client-facing sites where extra reasoning depth is worth the cost.
- Auditing complex pages (configurators, multi-step checkout, heavily-designed landing pages).
- Producing client-facing output where the strongest possible quality signal matters more than speed.

**Default behavior (no `--deep`):** cluster auditors and builder run on `sonnet`. Faster, cheaper, good enough for most pages.

**Roles that stay on `opus` regardless of `--deep`:**
- Lead (coordinator)
- Planner
- Reviewer
- Multi-planner peers

These are the synthesis brain and quality gate — downgrading them would degrade audit quality. See `contracts/dispatch-contract.md` for the full per-role model assignment table.

**Quick-scan note:** `--deep` is rarely needed for quick-scan (the value prop is speed), but available for client-facing quick-scan runs.
```

AFTER:
```markdown
## `--deep`

**Type:** boolean (no value).
**Default:** false.
**Supported by:** `/ecp:audit`, `/ecp:build`, `/ecp:compare`, `/ecp:quick-scan`.

Route cluster auditors and builder to `opus` instead of the default `sonnet`. Use when:
- Comparing heavily-designed client-facing sites where extra reasoning depth is worth the cost.
- Auditing complex pages (configurators, multi-step checkout, heavily-designed landing pages).
- Producing client-facing output where the strongest possible quality signal matters more than speed.

**Default behavior (no `--deep`):** cluster auditors and builder run on `sonnet`. Faster, cheaper, good enough for most pages.

**Roles that stay on `opus` regardless of `--deep`:**
- Lead (coordinator)
- Planner
- Reviewer
- Multi-planner peers

These are the synthesis brain and quality gate — downgrading them would degrade audit quality. See `contracts/dispatch-contract.md` for the full per-role model assignment table.

**Quick-scan note:** `--deep` is rarely needed for quick-scan (the value prop is speed), but available for client-facing quick-scan runs.

---

## `--max-concurrent`

**Type:** integer.
**Default:** all (unlimited; dispatch all requested clusters in one wave).
**Supported by:** `/ecp:audit`, `/ecp:build`.

Batch specialist subagent dispatch into concurrent waves of up to N agents. Use when:
- Resource-constrained environments (e.g., rate-limited API, shared compute quota, avoiding fork-bomb spike load).
- Network conditions favor fewer parallel streams over many.
- Observability/debugging requires serialization (though wave batching is orthogonal to that; use `--auto` for automated runs).

**Default behavior (no `--max-concurrent`):** Dispatch all cluster auditors and builder in one wave (full parallelism). Fastest wall-clock time.

**Example:** `--max-concurrent 5` for audit of 12 clusters (6 clusters × 2 devices) will dispatch in three waves: (1) auditors 1-5, (2) auditors 6-10, (3) auditor 11-12, then builder. Wave boundaries are transparent to the user — the lead waits for the entire batch to complete before the next phase.

**Fallback for throttling:** This flag is the lead's escape hatch when token/rate limits, fork-bomb concerns, or queue saturation would otherwise cause failures. Before adding hardcoded wave-batching logic, the lead tries `--max-concurrent` first.
```

- [ ] **Run the test — expected PASS.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py::test_max_concurrent_flag_in_flags_md -v
```

- [ ] **Run the suite subset.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py -q
python -m pytest tests/ -q -k "flag or contract"
```

- [ ] **Commit.**

```
git add contracts/flags.md tests/test_specialist_subagent_dispatch.py
git commit -m "docs(flags): document --max-concurrent N (default all/unlimited) as the rate-limit fallback

Full-parallel specialist dispatch is the default; --max-concurrent restores
batched waves. Documented like --deep.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4 — contracts/dispatch-contract.md: flip specialist to subagent + rewrite rationale + counter + intro + Task/Agent alias note

**Files:**
- Modify: `contracts/dispatch-contract.md`
- Test (append): `tests/test_specialist_subagent_dispatch.py`

- [ ] **Append the failing guard test:**

```python
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

    dispatch_table = re.search(
        r"How to dispatch each role in v2.*?Cluster specialist.*?\| (.*?) \|",
        content,
        re.DOTALL,
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
```

- [ ] **Run it — expected FAIL.** Reason: the per-role table still marks the specialist a `**teammate** (Agent tool with team_name)`, the dispatch-table row still carries `team_name=`/`name=`, the counter row reads `team_spawned_specialists`, the section is titled "Why cluster specialists keep teammate status", and no `--max-concurrent`/Task-alias prose exists yet.

```
python -m pytest tests/test_specialist_subagent_dispatch.py::test_specialist_dispatch_shape_is_subagent -v
```

- [ ] **Edit 1 — per-role model table (lines ~37-38), Cluster specialist row.**

BEFORE:
```markdown
| Cluster specialist (a.k.a. cluster auditor) | `sonnet` | `opus` | **teammate** (Agent tool with `team_name`) | Mechanical coverage work — read reference files, apply principles to page, emit JSON-only emission. Stays teammate ONLY because cluster specialists share the engagement output workspace and the lead merges by deterministic file-naming convention. v2 specialists do NOT peer-coordinate (no SendMessage, no huddles) — see `contracts/specialist-prompt-v2.md` "## No coordination" section. |
```

AFTER:
```markdown
| Cluster specialist (a.k.a. cluster auditor) | `sonnet` | `opus` | **subagent** (Agent tool, no team_name) | Mechanical coverage work — read reference files, apply principles to page, emit JSON-only emission. One-shot dispatch (no team_name); file-presence glob determines missing clusters at resume. v2 specialists do NOT peer-coordinate (no SendMessage, no huddles) — see `contracts/specialist-prompt-v2.md` "## No coordination" section. |
```

- [ ] **Edit 2 — "How to dispatch each role in v2" table (line ~109), Cluster specialist row.**

BEFORE:
```markdown
| Cluster specialist | `contracts/specialist-prompt-v2.md` (with per-cluster params from `contracts/specialists/{cluster}.md`) | `Agent(subagent_type="general-purpose", team_name="audit-{engagement_id}", name="specialist-{cluster}-{device}", model="sonnet", prompt=<rendered template>)` |
```

AFTER:
```markdown
| Cluster specialist | `contracts/specialist-prompt-v2.md` (with per-cluster params from `contracts/specialists/{cluster}.md`) | `Agent(subagent_type="general-purpose", description="Audit {cluster} cluster", model="sonnet", prompt=<rendered template>)` |
```

- [ ] **Edit 3 — rewrite the "Why cluster specialists keep teammate status" section (lines ~92-98).**

BEFORE:
```markdown
### Why cluster specialists keep teammate status

Cluster specialists share an engagement directory (`docs/ecp/{engagement_id}/`) and the lead merges their outputs by deterministic file name (`cluster-{cluster}-{device}.json`). The teammate dispatch shape gives:

1. **Atomicity-friendly fanout** (in **waves of ≤5 concurrent spawns**, added 2026-05-27): the lead collects via filesystem glob. A subagent fanout would also work but the existing teammate template handles it cleanly today. **Concurrency cap:** spawn no more than 5 specialists concurrently per wave. The 2026-05-27 batch repeatedly hit transient server-side rate limits ("not your usage limit") at 8+ concurrent spawns — Amazon engagement `0669899d` saw 7 of 8 spawns fail at 0 tokens; slingmods `4a0721e9` lost the entire first 20-way fanout and recovered via waves of ~5. A comprehensive 10-cluster × 2-device run therefore needs ~4 waves of 5 (acquirers count toward the cap; ethics+synthesizer are sequential pinch-points and don't). The 5-cap is operational, not architectural — if a future runtime removes the rate limit, raise it.
2. **Restart-friendly file-presence model.** If the lead resumes mid-run, it reads which `cluster-*-{device}.json` files are already on disk and re-dispatches only the missing ones. The teammate task list is a parallel record but file presence is the truth.
3. **No coordination ceremony.** v2 specialists do NOT SendMessage anyone, do NOT broadcast intent, do NOT propagate SYNTHESIS_HINT. See `contracts/specialist-prompt-v2.md` "## No coordination" section. The teammate dispatch shape is a transport choice, not a coordination requirement.
```

AFTER:
```markdown
### Why specialists are one-shot subagents

Cluster specialists share an engagement directory (`docs/ecp/{engagement_id}/`) and the lead merges their outputs by deterministic file name (`cluster-{cluster}-{device}.json`). One-shot subagent dispatch (no team_name) provides:

1. **Full-parallel fanout with concurrency control** (default = unlimited, fallback `--max-concurrent N` flag): the lead collects via filesystem glob and dispatches all missing clusters in one message. **Default behavior:** dispatch all requested cluster specialists in parallel (no artificial waves). **Rate-limit fallback:** if the dispatcher hits transient server-side rate limits ("not your usage limit"), the lead can re-dispatch in waves via `--max-concurrent N` (e.g., `--max-concurrent 5` to batch in waves of 5). The 2026-05-27 batch discovered this limit at 8+ concurrent spawns — Amazon engagement `0669899d` saw 7 of 8 spawns fail at 0 tokens; slingmods `4a0721e9` lost the entire first 20-way fanout and recovered via waves of ~5. Full-parallel is the default; the `--max-concurrent` flag exists for rate-limit recovery, not routine use. See `contracts/flags.md` for the `--max-concurrent` contract.
2. **Restart-friendly file-presence model.** If the lead resumes mid-run, it reads which `cluster-*-{device}.json` files are already on disk and re-dispatches only the missing ones. File presence is the truth; the subagent does not rely on a task-list record.
3. **No coordination ceremony.** v2 specialists do NOT SendMessage anyone, do NOT broadcast intent, do NOT propagate SYNTHESIS_HINT. See `contracts/specialist-prompt-v2.md` "## No coordination" section. One-shot subagent shape eliminates the idle-notification stream.
```

- [ ] **Edit 4 — v2 counter table (line ~285), Cluster specialist row.**

BEFORE:
```markdown
| Cluster specialist | teammate | `team_spawned_specialists` (renamed from `team_spawned_auditors` in v2; v1 backwards-compat alias accepted) |
```

AFTER:
```markdown
| Cluster specialist | subagent | `subagent_spawned_specialists` (v1 backwards-compat alias `team_spawned_auditors` still accepted) |
```

- [ ] **Edit 5 — v2 Dispatch-shape policy intro (lines ~79-80).** Per the consistency rule, name the tool `Agent` (NOT `Task`).

BEFORE:
```markdown
v2 flips the v1 default. **Most roles dispatch as one-shot subagents (Task tool, no team_name); only cluster specialists and multi-planner peers remain teammates** (Agent tool with team_name).
```

AFTER:
```markdown
v2 flips the v1 default. **Most roles dispatch as one-shot subagents (Agent tool, no team_name); only multi-planner peers remain teammates** (Agent tool with team_name). Cluster specialists are one-shot subagents (no team_name).
```

> **CONSISTENCY OVERRIDE:** the fragment's AFTER for Edit 5 read "**Most roles dispatch as one-shot subagents (Agent tool, no team_name)**" — kept. (The fragment's BEFORE said "Task tool"; the consistency rule mandates `Agent` as the canonical tool name, so the AFTER says `Agent tool`.) See Conflicts found.

- [ ] **Edit 6 — add the Task/Agent alias note.** Insert this note immediately AFTER the "How to dispatch each role in v2" table (i.e., directly after Edit 2's row block, before the next subsection). This is the ONE place the plan documents the alias.

NEW TEXT TO INSERT:
```markdown
> **Tool-name note (`Task` vs `Agent`):** `Task` is the v2.1.63 **legacy alias** for the unified `Agent` spawn tool — both names work and dispatch identically. This contract uses `Agent` as the canonical name. The broad cosmetic `Task`→`Agent` rename across the *other* one-shot roles' contract text (acquirer / ethics / synthesizer / planner / reviewer / builder) is **OUT OF SCOPE** for this migration; only the cluster-specialist rows and the intro line above are normalized here.
```

- [ ] **Run the test — expected PASS.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py::test_specialist_dispatch_shape_is_subagent -v
```

- [ ] **Run the suite subset.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py -q
python -m pytest tests/ -q -k "dispatch or contract"
```

- [ ] **Commit.**

```
git add contracts/dispatch-contract.md tests/test_specialist_subagent_dispatch.py
git commit -m "feat(dispatch-contract): flip cluster specialists to one-shot subagents

Per-role + how-to-dispatch rows drop team_name/name; rewrite rationale to
full-parallel + --max-concurrent fallback; canonical counter
subagent_spawned_specialists (alias retained); intro line + Task/Agent
alias note.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5 — contracts/specialist-prompt-v2.md: dispatch line drops team_name/name; "No coordination" preserved

**Files:**
- Modify: `contracts/specialist-prompt-v2.md`
- Test (append): `tests/test_specialist_subagent_dispatch.py`

- [ ] **Append the failing guard test:**

```python
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
```

- [ ] **Run it — expected FAIL.** Reason: line 19 still passes `team_name: "audit-{engagement-id}"` and `name: "specialist-{cluster}-{device}"`.

```
python -m pytest tests/test_specialist_subagent_dispatch.py::test_specialist_prompt_dispatch_line_has_no_team_name_or_name -v
```

- [ ] **Edit — dispatch instruction (line ~19).**

BEFORE:
```markdown
The result is a single user-turn prompt string. The lead dispatches it via the Agent tool (`subagent_type: "general-purpose"`, `team_name: "audit-{engagement-id}"`, `model: "sonnet"`, `name: "specialist-{cluster}-{device}"`). Sonnet 4.6 is the v2 default per [`contracts/dispatch-contract.md`](dispatch-contract.md). Opus is reserved for the synthesizer (Layer 3) and the lead.
```

AFTER:
```markdown
The result is a single user-turn prompt string. The lead dispatches it via the Agent tool (`subagent_type: "general-purpose"`, `model: "sonnet"`). Sonnet 4.6 is the v2 default per [`contracts/dispatch-contract.md`](dispatch-contract.md). Opus is reserved for the synthesizer (Layer 3) and the lead.
```

> **Preserved (no edit):** the "## No coordination" section (lines ~493-498). The fragment's currentVerbatim == proposedVerbatim — transcribe NO change; the guard test asserts it survives.

- [ ] **Run the test — expected PASS.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py::test_specialist_prompt_dispatch_line_has_no_team_name_or_name -v
```

- [ ] **Run the suite subset.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py -q
python -m pytest tests/ -q -k "prompt_template or specialist"
```

- [ ] **Commit.**

```
git add contracts/specialist-prompt-v2.md tests/test_specialist_subagent_dispatch.py
git commit -m "feat(specialist-prompt): drop team_name/name from dispatch line (one-shot subagent)

No-coordination requirement preserved verbatim.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6 — skills/audit/SKILL.md: Dispatch-Shape line, delete "Create team" step + renumber, full-parallel + --max-concurrent, recovery via fresh re-dispatch

**Files:**
- Modify: `skills/audit/SKILL.md`
- Test (append): `tests/test_specialist_subagent_dispatch.py`

- [ ] **Append the failing guard test(s):**

```python
# ---------------------------------------------------------------------------
# Task 6 — skills/audit/SKILL.md: one-shot specialists, no team creation
# ---------------------------------------------------------------------------
def test_cluster_specialists_no_team_name_in_dispatch_contract():
    """Cluster specialist dispatch template in dispatch-contract.md has no team_name."""
    dispatch_contract = _read_repo_file("contracts/dispatch-contract.md")
    agent_line = re.search(
        r"Cluster specialist.*?`Agent\(subagent_type=.*?\)`",
        dispatch_contract,
        re.DOTALL,
    )
    assert agent_line is not None, "Cluster specialist dispatch template missing"
    assert "team_name" not in agent_line.group(0), (
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
```

- [ ] **Run them — expected FAIL.** Reason: the Dispatch-Shape line still reads "`Agent` teammates in the audit team"; Phase-Order step 4 is "Create the audit team per `contracts/team-lifecycle.md`."; the dispatch step describes "waves of ≤5"; the recovery block does not yet mention `fresh one-shot subagent` / `--max-concurrent`.

```
python -m pytest tests/test_specialist_subagent_dispatch.py -k "skill_md or no_team_name_in_dispatch_contract" -v
```

- [ ] **Edit 1 — Dispatch-Shape line (line ~97).**

BEFORE:
```markdown
- Cluster specialists: `Agent` teammates in the audit team.
```

AFTER:
```markdown
- Cluster specialists: one-shot subagent (`Agent` tool, no `team_name`).
```

> **CONSISTENCY OVERRIDE:** the fragment's rationale for this line argued specialists "use Agent because they write to shared engagement workspace … Unlike acquirer/ethics/synthesizer which use Task". That framing violates the rationale-hygiene rule and is **dropped**. The line itself (the only thing written to the file) is transcribed as-is; the misleading rationale is NOT carried into the contract. See Conflicts found.

- [ ] **Edit 2 — DELETE Phase-Order step 4 (line ~79).** Remove the entire line; the following steps renumber 5→4 … 15→14.

BEFORE:
```markdown
4. Create the audit team per `contracts/team-lifecycle.md`.
```

AFTER:
```
(line removed)
```

- [ ] **Edit 3 — renumber Phase-Order step 5 → 4 (Detect platform).**

BEFORE:
```markdown
5. Detect platform, page type, page pattern, and cluster scope.
```

AFTER:
```markdown
4. Detect platform, page type, page pattern, and cluster scope.
```

- [ ] **Edit 4 — renumber step 6 → 5 (Dispatch acquisition).**

BEFORE:
```markdown
6. Dispatch acquisition for each requested device.
```

AFTER:
```markdown
5. Dispatch acquisition for each requested device.
```

- [ ] **Edit 5 — renumber step 7 → 6 (Verify acquisition artifacts).**

BEFORE:
```markdown
7. Verify acquisition artifacts on disk.
```

AFTER:
```markdown
6. Verify acquisition artifacts on disk.
```

- [ ] **Edit 6 — renumber step 8 → 7 (Preprocess DOM).**

BEFORE:
```markdown
8. Preprocess DOM per device when DOM exists.
```

AFTER:
```markdown
7. Preprocess DOM per device when DOM exists.
```

- [ ] **Edit 7 — step 9 → 8 (Dispatch cluster specialists): replace waves-of-5 with full-parallel + --max-concurrent.**

BEFORE:
```markdown
9. Dispatch cluster specialists for each selected cluster and device — **in waves of ≤5 concurrent spawns** (G-fanout cap, 2026-05-27). The 2026-05-27 concurrent-audits batch hit transient server-side rate limits at 8+ concurrent spawns; a comprehensive 10-cluster × 2-device run takes ~4 waves of 5 to land cleanly. Wait for each wave's file-presence signal before launching the next. See `contracts/dispatch-contract.md` §"Why cluster specialists keep teammate status" point 1 for the rationale.
```

AFTER:
```markdown
8. Dispatch cluster specialists for each selected cluster and device — **full-parallel by default** (spawn all requested clusters in one message). Concurrency is capped server-side; if transient rate limits appear, use the `--max-concurrent N` flag to batch spawns into waves (documented in `contracts/flags.md`). The flag defaults to unlimited (all clusters at once). Wait for each batch's file-presence signal (via glob `cluster-{cluster}-{device}.json`) before proceeding to the next phase layer. See `contracts/dispatch-contract.md` §"Why specialists are one-shot subagents" point 1 for the transport-shape rationale.
```

> NOTE: the fragment's AFTER referenced the OLD section title §"Why cluster specialists keep teammate status". Task 4 renames that section to **"Why specialists are one-shot subagents"**, so the cross-reference here uses the NEW title (consistency fix).

- [ ] **Edit 8 — steps 10-15 → 9-14 (subsequent Phase-Order steps + no-team-cleanup clarification).**

BEFORE:
```markdown
10. Dispatch ethics v2 after specialist emissions are present.
11. Validate every specialist + ethics emission, build the canonical f_refs manifest, and trim each device baton, then dispatch synthesizer v2 (after ethics completes or records partial status).
12. Validate the synthesizer emission, run the cross-device drift gate, and run structural plus substantive canaries (see "Validation, Synthesis, and Rendering").
13. Present the audit checkpoint with export options.
14. Export the audit markdown and the annotated visual report when requested.
15. Update `meta.json`, write `lead-reflection.md`, run `generate-report.py --mark-reflection-complete` to flip `meta.json` `reflection_state` from `draft` to `complete` (G23, 2026-05-28), and clean up the team at completion.
```

AFTER:
```markdown
9. Dispatch ethics v2 after specialist emissions are present.
10. Validate every specialist + ethics emission, build the canonical f_refs manifest, and trim each device baton, then dispatch synthesizer v2 (after ethics completes or records partial status).
11. Validate the synthesizer emission, run the cross-device drift gate, and run structural plus substantive canaries (see "Validation, Synthesis, and Rendering").
12. Present the audit checkpoint with export options.
13. Export the audit markdown and the annotated visual report when requested.
14. Update `meta.json`, write `lead-reflection.md`, run `generate-report.py --mark-reflection-complete` to flip `meta.json` `reflection_state` from `draft` to `complete` (G23, 2026-05-28). Do NOT clean up any team at completion (no team was created in audit v2 flow).
```

- [ ] **Edit 9 — Validation block, failure recovery (lines ~130-134): SendMessage-free fresh re-dispatch.**

BEFORE:
```markdown
   On failure, **first try autofix** (G15 P1-3) for known-safe shape traps catalogued from live runs (path-form telemetry, duplicate finding tuples, overlong `proposed_anchor.reason`, missing `proposed_anchor` on absent findings):
   ```powershell
   python scripts/test-specialist.py autofix --emission-path docs/ecp/{id}/cluster-{cluster}-{device}.json --in-place
   ```
   Re-run `validate` against the autofixed emission. If validation now passes, proceed (the `--in-place` repairs were semantically conservative and the repairs log is at `<emission>.repairs.json`). If validation still fails, pass `--write-retry-prompt <path>` and re-dispatch the specialist; never hand-edit an emission beyond what autofix repaired.
```

AFTER:
```markdown
   On failure, **first try autofix** (G15 P1-3) for known-safe shape traps catalogued from live runs (path-form telemetry, duplicate finding tuples, overlong `proposed_anchor.reason`, missing `proposed_anchor` on absent findings):
   ```powershell
   python scripts/test-specialist.py autofix --emission-path docs/ecp/{id}/cluster-{cluster}-{device}.json --in-place
   ```
   Re-run `validate` against the autofixed emission. If validation now passes, proceed (the `--in-place` repairs were semantically conservative and the repairs log is at `<emission>.repairs.json`). If validation still fails, use `scripts/test-specialist.py --write-retry-prompt <path>` to generate a fresh-dispatch prompt with the validation error embedded, then re-dispatch a **fresh one-shot subagent** via `Agent(subagent_type="general-purpose", description="...", model="sonnet", prompt=<retry-prompt>)`. On second validation failure, mark the cluster "partial" and continue; never hand-edit an emission beyond what autofix repaired.
```

- [ ] **Run the tests — expected PASS.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py -k "skill_md or no_team_name_in_dispatch_contract" -v
```

- [ ] **Run the suite subset.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py -q
python -m pytest tests/ -q -k "skill or audit or phase"
```

- [ ] **Commit.**

```
git add skills/audit/SKILL.md tests/test_specialist_subagent_dispatch.py
git commit -m "feat(audit-skill): one-shot specialist dispatch, delete team-create step, full-parallel default

Dispatch-Shape line, Phase-Order renumber after dropping the team-create step,
full-parallel default with --max-concurrent fallback, and fresh re-dispatch
recovery (no SendMessage).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7 — contracts/audit-reconciliation.md: Steps 0 / 0b / 0c SendMessage-bounce → fresh one-shot re-dispatch

**Files:**
- Modify: `contracts/audit-reconciliation.md`
- Test (append): `tests/test_specialist_subagent_dispatch.py`

- [ ] **Append the failing guard test:**

```python
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
    assert "triple-backtick code fences" in step_0
    assert "FINDING: FAIL" in step_0
    assert "TITLE field rules" in step_0
    assert "voice check" in step_0b
    assert "jargon" in step_0b
    assert "evidence anchor" in step_0c
    assert "DOM selector" in step_0c
```

- [ ] **Run it — expected FAIL.** Reason: Steps 0/0b/0c still issue `SendMessage to "auditor-{cluster}-{device}"` with "Mark your task in_progress again while you rewrite" and contain no `Agent(...)` re-dispatch.

```
python -m pytest tests/test_specialist_subagent_dispatch.py::test_validation_failure_triggers_subagent_not_sendmessage -v
```

> MEASURE-TWICE: confirm the exact heading text in the live file (`## Step 0 — Format validation`, `## Step 0b — Voice check`, `## Step 0c — Evidence-anchor`). The test slices on these headings; if the live headings differ, adjust both the edits' anchors and the slice boundaries.

- [ ] **Edit 1 — Step 0 format validation, general rejection (lines ~85-100).**

BEFORE:
```markdown
4. **If REJECTED, send the auditor back via SendMessage:**
   ```
   SendMessage to "auditor-{cluster}-{device}":
   "Your cluster file at docs/ecp/{engagement-id}/cluster-{cluster}-{device}.md
    does not use the required format. Findings MUST be wrapped in triple-backtick
    code fences with `FINDING: FAIL` or `FINDING: PARTIAL` as the first line of
    each block. Your file currently uses [describe what they did wrong].
    Please rewrite the file in the canonical format documented in
    workflows/audit.md Step 4a 'Worked Examples' and Step 4d 'TITLE field rules'.
    The reconciler depends on this format, and the visual report generator
    parses code-fenced blocks via regex.
    Reformatting in place is acceptable — keep your observations and
    recommendations verbatim, only change the wrapper structure.
    Mark your task in_progress again while you rewrite, then back to completed
    when done."
   ```
```

AFTER:
```markdown
4. **If REJECTED, dispatch a fresh one-shot subagent:**
   Run `scripts/test-specialist.py --write-retry-prompt <path-to-cluster-file>` with the validation error (e.g., "block-format violation: findings use ### Finding N headings instead of code fences"). This generates a retry prompt that embeds the error.
   ```
   Agent(subagent_type="general-purpose", description="format-rewrite: cluster-{cluster}-{device}",
         model="sonnet", prompt=<rendered retry prompt from test-specialist.py>)
   ```
   One re-dispatch per validation failure. The subagent has no context of the original attempt — it receives only the cluster file content + the specific validation error. On success, validate the returned file again. On second failure, the lead reformats in place AND logs the failure in `audit-trace.log` for follow-up. Do NOT silently reformat without going through re-dispatch first.
```

- [ ] **Edit 2 — Step 0 format validation, TITLE-specific rejection (lines ~102-123).**

BEFORE:
```markdown
   **For TITLE-specific rejections, use this tailored message instead:**
   ```
   SendMessage to "auditor-{cluster}-{device}":
   "Your cluster file at docs/ecp/{engagement-id}/cluster-{cluster}-{device}.md
    cleared the block-format check but failed TITLE validation. Specific issues:

    - [List each offending finding by its current TITLE or block position, e.g.,
      'Finding #3 is missing a TITLE: line entirely',
      'Findings #2 and #5 both have TITLE: Value Proposition — must be unique within this cluster',
      'Finding #7 has TITLE: Trust Badges which matches its SECTION slug trust-badges — too generic',
      'Finding #4 TITLE is 74 chars — must be ≤60'].

    Please re-read workflows/audit.md Step 4d 'TITLE field rules' and rewrite the
    offending TITLE lines only. Keep every other field (SECTION, ELEMENT, OBSERVATION,
    RECOMMENDATION, PRIORITY, REFERENCE, citation) verbatim. Rename titles to name
    the specific element or sub-issue (e.g., 'Homepage Hero Lacks Value Prop',
    'Product Cards Generic Copy'). Two findings in the same cluster cannot share an
    identical TITLE.

    Mark your task in_progress again while you rewrite, then back to completed
    when done."
   ```
```

AFTER:
```markdown
   **For TITLE-specific rejections, dispatch a fresh one-shot subagent:**
   Run `scripts/test-specialist.py --write-retry-prompt <path-to-cluster-file>` with the validation error details (e.g., "TITLE validation: Finding #3 missing TITLE line; Findings #2 and #5 both have 'Value Proposition' — must be unique"). This generates a retry prompt embedding the specific violations.
   ```
   Agent(subagent_type="general-purpose", description="title-rewrite: cluster-{cluster}-{device}",
         model="sonnet", prompt=<rendered retry prompt from test-specialist.py>)
   ```
   One re-dispatch per validation failure. The subagent receives cluster content + the specific TITLE violations (missing lines, duplicates, length/slug-match failures) and rewrites only TITLE fields, keeping SECTION, ELEMENT, OBSERVATION, RECOMMENDATION, PRIORITY, REFERENCE, and citations verbatim. On success, re-validate. On second failure, the lead corrects TITLEs in place AND logs the failure in `audit-trace.log` for follow-up.
```

- [ ] **Edit 3 — Step 0b voice check rejection (lines ~144-168).**

BEFORE:
```markdown
**If REJECTED on voice check, send the auditor back via SendMessage:**
```
SendMessage to "auditor-{cluster}-{device}":
"Your cluster file at docs/ecp/{engagement-id}/cluster-{cluster}-{device}.md
 passed format validation but failed the voice check. The following findings
 use jargon or framing that won't translate for a client reader:

 - Finding at SECTION [slug]: uses [specific jargon term] without plain-English
   equivalent.
 - Finding at SECTION [slug]: uses 'violation'/'compliance' framing instead
   of 'what we found / what to do'.
 - Finding at SECTION [slug]: 'Why this matters' is citation-only without
   business outcome translation.

 Please rewrite these findings using the voice guide in
 workflows/audit.md Step 4b and the cluster-specific worked examples
 in Step 4c. Keep the SECTION, ELEMENT, PRIORITY, SOURCE, and REFERENCE
 fields exactly as you had them — only rewrite OBSERVATION, RECOMMENDATION,
 and **Why this matters** in plain English. The grandmother test applies:
 if a small business owner or a store manager wouldn't understand what
 you wrote in one read, simplify.

 Mark your task in_progress again while you rewrite, then back to completed
 when done."
```

Same two-attempt loop as the format check. On third failure, the lead rewrites in place using the voice guide's translation patterns AND logs the voice failure in `audit-trace.log` for follow-up. Do NOT silently pass jargon-laden findings through to the client.
```

AFTER:
```markdown
**If REJECTED on voice check, dispatch a fresh one-shot subagent:**
Run `scripts/test-specialist.py --write-retry-prompt <path-to-cluster-file>` with the voice violation details (e.g., "voice check failed: Finding at SECTION pricing uses 'render-blocking' without plain-English equivalent; Finding at SECTION trust uses 'compliance' framing — rewrite using outcome framing; Finding at SECTION benefits has citation-only 'Why this matters'"). This generates a retry prompt embedding the specific violations.
```
Agent(subagent_type="general-purpose", description="voice-rewrite: cluster-{cluster}-{device}",
      model="sonnet", prompt=<rendered retry prompt from test-specialist.py>)
```
One re-dispatch per validation failure. The subagent receives cluster content + the specific jargon/framing violations and rewrites only OBSERVATION, RECOMMENDATION, and **Why this matters** fields, keeping SECTION, ELEMENT, PRIORITY, SOURCE, and REFERENCE verbatim. On success, re-validate using the same blocklist gate. On second failure, the lead rewrites in place using the voice guide's translation patterns AND logs the voice failure in `audit-trace.log` for follow-up. Do NOT silently pass jargon-laden findings through to the client.
```

- [ ] **Edit 4 — Step 0c evidence-anchor gate rejection (lines ~195-218).**

BEFORE:
```markdown
**If REJECTED on evidence-anchor gate, send the auditor back via SendMessage:**
```
SendMessage to "auditor-{cluster}-{device}":
"Your cluster file at docs/ecp/{engagement-id}/cluster-{cluster}-{device}.md
 passed format and voice checks but failed the evidence-anchor gate. The
 following findings read as generic CRO advice — they could be pasted into
 any audit of any store because they don't reference THIS page:

 - Finding at SECTION [slug]: no DOM element named; OBSERVATION uses
   [specific forbidden framing]. Add a CSS selector or data attribute
   from the cluster-context JSON, OR quote the specific copy you observed,
   OR describe a screenshot coordinate.
 - Finding at SECTION [slug]: RECOMMENDATION is abstract ('strengthen the
   CTA'). Name the actual button/link on the page and describe the specific
   change (color, copy, placement).

 Please rewrite with a concrete evidence anchor — see contracts/dispatch-contract.md
 'Evidence requirement' section and the 'acceptable' worked example. If you
 genuinely can't identify an anchor for a finding after examining the
 cluster-context JSON and the screenshots, drop the finding rather than
 emit it generic.

 Mark your task in_progress again, rewrite, then back to completed."
```

Same two-attempt loop as format and voice checks. On third failure, the lead **drops the finding silently** (no special marker, no placeholder) — a cluster that lands with zero surviving findings after Step 0c is rendered in the audit as an empty cluster. Generic advice never reaches the client.
```

AFTER:
```markdown
**If REJECTED on evidence-anchor gate, dispatch a fresh one-shot subagent:**
Run `scripts/test-specialist.py --write-retry-prompt <path-to-cluster-file>` with the evidence-anchor violations (e.g., "evidence-anchor gate failed: Finding at SECTION pricing ELEMENT blank, uses generic framing 'best practice suggests' — anchor to a DOM selector or quote; Finding at SECTION trust RECOMMENDATION abstract 'strengthen the CTA' — name the specific button/link and describe the change"). This generates a retry prompt embedding the specific failures.
```
Agent(subagent_type="general-purpose", description="evidence-anchor-rewrite: cluster-{cluster}-{device}",
      model="sonnet", prompt=<rendered retry prompt from test-specialist.py>)
```
One re-dispatch per validation failure. The subagent receives cluster content + the specific evidence-anchor failures (missing ELEMENT, abstract framing, missing citations, vague recommendations) and rewrites to ground findings in concrete page evidence: DOM selectors, screenshot coordinates, or quoted copy from the cluster-context JSON. On success, re-validate. On second failure, the lead **drops the finding silently** (no special marker, no placeholder) — a cluster that lands with zero surviving findings after Step 0c is rendered in the audit as an empty cluster. Generic advice never reaches the client.
```

- [ ] **Run the test — expected PASS.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py::test_validation_failure_triggers_subagent_not_sendmessage -v
```

- [ ] **Run the suite subset.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py -q
python -m pytest tests/ -q -k "reconcil or validation"
```

- [ ] **Commit.**

```
git add contracts/audit-reconciliation.md tests/test_specialist_subagent_dispatch.py
git commit -m "feat(reconciliation): route Steps 0/0b/0c rejections to fresh one-shot re-dispatch

Swap SendMessage-bounce for test-specialist.py --write-retry-prompt + fresh
Agent dispatch; validation logic (format/voice/evidence-anchor) unchanged.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8 — contracts/lead-discipline.md: terminology (teammate→subagent; SendMessage-retry→fresh re-dispatch); preserve cancel.flag + file-ownership unchanged

**Files:**
- Modify: `contracts/lead-discipline.md`
- Test (append): `tests/test_specialist_subagent_dispatch.py`

> **PRESERVE (state, no edit):** the `## Cancellation sentinel (cancel.flag)` section and the `## Filesystem write atomicity` / `## Concurrent-audit isolation` sections retain their core protocol and file-ownership model UNCHANGED. The fragment's "edits" to these headings are no-ops (currentVerbatim == proposedVerbatim). Inside the cancellation section, the ONLY changes are three terminology touch-ups — "zombie teammates" → "zombie subagents", "cleanup teammates" → "cleanup subagents", and "A teammate or subagent already in flight" → "A subagent already in flight". cancel.flag presence-semantics, layer-boundary checks, preservation list, and resume logic are preserved verbatim.

- [ ] **Append the failing guard test:**

```python
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
```

- [ ] **Run it — expected FAIL.** Reason: headings/prose still say "teammate", the acquirer-failure recovery still references a SendMessage retry, and the self-check prose still reads `team_spawned_auditors` as the sole counter.

```
python -m pytest tests/test_specialist_subagent_dispatch.py::test_lead_discipline_terminology_and_preserved_sections -v
```

> This task carries MANY small exact-string edits. Apply each in order; each BEFORE/AFTER is a unique line in the live file. The full set:

- [ ] **Edit a — line 3 (intro).**

BEFORE:
```markdown
Canonical anti-rogue rules for ECP skill coordinators (leads). Contains the no-preflight-questions rule, the acquisition-must-spawn-teammate binding rule, and the full catalog of forbidden rationalizations that leads use to justify skipping team architecture.
```

AFTER:
```markdown
Canonical anti-rogue rules for ECP skill coordinators (leads). Contains the no-preflight-questions rule, the acquisition-must-spawn-subagent binding rule, and the full catalog of forbidden rationalizations that leads use to justify skipping one-shot subagent dispatch architecture.
```

- [ ] **Edit b — line 9 (Read this file when).**

BEFORE:
```markdown
**Read this file when:** you are the coordinator (lead) of any `/ecp:*` skill that spawns teammates. That's audit, build, compare, and quick-scan. Read this **at the very top of your skill invocation**, before doing anything else. These rules take precedence over performance optimizations, "effort" cues, or any rationalization about shortcuts.
```

AFTER:
```markdown
**Read this file when:** you are the coordinator (lead) of any `/ecp:*` skill that spawns one-shot subagents. That's audit, build, compare, and quick-scan. Read this **at the very top of your skill invocation**, before doing anything else. These rules take precedence over performance optimizations, "effort" cues, or any rationalization about shortcuts.
```

- [ ] **Edit c — line 34 (section heading).**

BEFORE:
```markdown
## Equally forbidden — quietly doing work directly as the lead instead of spawning the teammate
```

AFTER:
```markdown
## Equally forbidden — quietly doing work directly as the lead instead of spawning the subagent
```

- [ ] **Edit d — line 36.**

BEFORE:
```markdown
This is the inverse of asking too many questions. Instead of asking "do you want me to spawn an acquirer?" the lead silently rationalizes "I'll just do acquisition directly as the lead — faster path, the spec allows it as manual fallback." **It does not.** Manual acquisition is a strict last-resort fallback, not a shortcut. See the "Acquisition must spawn teammate" section below for the binding rule.
```

AFTER:
```markdown
This is the inverse of asking too many questions. Instead of asking "do you want me to spawn an acquirer?" the lead silently rationalizes "I'll just do acquisition directly as the lead — faster path, the spec allows it as manual fallback." **It does not.** Manual acquisition is a strict last-resort fallback, not a shortcut. See the "Acquisition must spawn subagent" section below for the binding rule.
```

- [ ] **Edit e — line 40.**

BEFORE:
```markdown
- ❌ "Given effort=low, I'll do acquisition directly as lead." → Effort is irrelevant. Always spawn the acquirer teammate(s) first.
```

AFTER:
```markdown
- ❌ "Given effort=low, I'll do acquisition directly as lead." → Effort is irrelevant. Always spawn the acquirer subagent first.
```

- [ ] **Edit f — line 41.**

BEFORE:
```markdown
- ❌ "The spec allows this as manual fallback." → It does not. Manual fallback only triggers AFTER (a) the spawn has been attempted, and (b) the teammate has either failed or produced missing/empty files. Pre-emptive bypass is a spec violation.
```

AFTER:
```markdown
- ❌ "The spec allows this as manual fallback." → It does not. Manual fallback only triggers AFTER (a) the spawn has been attempted, and (b) the subagent has either failed or produced missing/empty files. Pre-emptive bypass is a spec violation.
```

- [ ] **Edit g — line 42.**

BEFORE:
```markdown
- ❌ "Faster path." → Speed is not a valid reason to skip team architecture. The whole point of Phase 4 is consistent state via the team task list, even when phases are short.
```

AFTER:
```markdown
- ❌ "Faster path." → Speed is not a valid reason to skip subagent-dispatch architecture. The whole point of the pipeline is consistent state via atomic file writes and per-subagent isolation, even when phases are short.
```

- [ ] **Edit h — line 43.**

BEFORE:
```markdown
- ❌ "Auditing as lead this time, since the page is small." → No. Same answer. Always spawn the relevant teammate.
```

AFTER:
```markdown
- ❌ "Auditing as lead this time, since the page is small." → No. Same answer. Always spawn the relevant subagent.
```

- [ ] **Edit i — line 46.**

BEFORE:
```markdown
**This rule applies to every phase:** acquirer, cluster auditors, planner, reviewer, builder. The lead does NOT do their work; the lead orchestrates. The lead's only direct work is engagement setup, validation passes, reconciliation/assembly, and the Priority Path synthesis step that explicitly belongs to the lead per `${CLAUDE_PLUGIN_ROOT}/contracts/priority-path-synthesis.md`.
```

AFTER:
```markdown
**This rule applies to every phase:** acquirer, cluster specialists, planner, reviewer, builder. The lead does NOT do their work; the lead orchestrates. The lead's only direct work is engagement setup, validation passes, reconciliation/assembly, and the Priority Path synthesis step that explicitly belongs to the lead per `${CLAUDE_PLUGIN_ROOT}/contracts/priority-path-synthesis.md`.
```

- [ ] **Edit j — line 56.**

BEFORE:
```markdown
3. **URL fetch confirmation** — One prompt "About to fetch **{domain}** — proceed?" before spawning the acquisition teammate. This is the standard "we're about to make a network request" confirmation. Skip in `--auto` mode.
```

AFTER:
```markdown
3. **URL fetch confirmation** — One prompt "About to fetch **{domain}** — proceed?" before spawning the acquisition subagent. This is the standard "we're about to make a network request" confirmation. Skip in `--auto` mode.
```

- [ ] **Edit k — line 74.**

BEFORE:
```markdown
Similarly, **quietly doing the teammate's work as the lead** is a form of avoiding the Agent tool call — it feels more efficient but it abandons the team task list, the structural counters in `audit-trace.log`, and the per-teammate context isolation that makes the pipeline composable. The correction for both errors is the same: **trust the architecture, spawn the teammate, move on to the next phase.**
```

AFTER:
```markdown
Similarly, **quietly doing the subagent's work as the lead** is a form of avoiding the Agent tool call — it feels more efficient but it abandons the atomic-write discipline, the structural counters in `audit-trace.log`, and the per-subagent context isolation that makes the pipeline composable. The correction for both errors is the same: **trust the architecture, spawn the subagent, move on to the next phase.**
```

- [ ] **Edit l — line 78 (section heading).**

BEFORE:
```markdown
## Acquisition must spawn teammate (binding rule)
```

AFTER:
```markdown
## Acquisition must spawn subagent (binding rule)
```

- [ ] **Edit m — line 80.**

BEFORE:
```markdown
**The lead MUST spawn the acquirer teammate(s) first. There is no shortcut.**
```

AFTER:
```markdown
**The lead MUST spawn the acquirer subagent first. There is no shortcut.**
```

- [ ] **Edit n — line 84.**

BEFORE:
```markdown
1. The lead has actually called the Agent tool to spawn `acquirer` (or `acquirer-{device}` for dual-device mode) into the team.
```

AFTER:
```markdown
1. The lead has actually called the Agent tool to spawn `acquirer` (or `acquirer-{device}` for dual-device mode) as a one-shot subagent with subagent_type="general-purpose" and model="sonnet" (or "opus" with --deep).
```

- [ ] **Edit o — lines 85-87.**

BEFORE:
```markdown
2. The teammate has either:
   - Failed entirely (crash, malformed output, baton.json with `screenshots: []`), OR
   - Reported `STATUS: COMPLETE` but the post-acquisition file verification step found missing files on disk, AND the corrective re-spawn (one retry via SendMessage) also failed.
```

AFTER:
```markdown
2. The subagent has either:
   - Failed entirely (crash, malformed output, baton.json with `screenshots: []`), OR
   - Reported `STATUS: COMPLETE` but the post-acquisition file verification step found missing files on disk, AND the corrective re-spawn (one fresh one-shot subagent with validation error embedded via scripts/test-specialist.py --write-retry-prompt) also failed.
```

- [ ] **Edit p — line 92.**

BEFORE:
```markdown
If you find yourself reasoning "I'll skip spawning the acquirer because…" — STOP. Spawn it. The team architecture is the contract; the manual path exists only for when the contract genuinely cannot be honored.
```

AFTER:
```markdown
If you find yourself reasoning "I'll skip spawning the acquirer because…" — STOP. Spawn it. The one-shot subagent dispatch is the contract; the manual path exists only for when the contract genuinely cannot be honored.
```

- [ ] **Edit q — line 94.**

BEFORE:
```markdown
**This rule mirrors the no-preflight-questions rule above** and applies the same principle to silent shortcuts: **don't quietly do the teammate's work as the lead just because the spec has an emergency exit.**
```

AFTER:
```markdown
**This rule mirrors the no-preflight-questions rule above** and applies the same principle to silent shortcuts: **don't quietly do the subagent's work as the lead just because the spec has an emergency exit.**
```

- [ ] **Edit r — line 100.**

BEFORE:
```markdown
**If a cluster auditor teammate fails, the lead SKIPs that cluster. The lead does NOT audit the cluster as a fallback.**
```

AFTER:
```markdown
**If a cluster specialist subagent fails, the lead SKIPs that cluster. The lead does NOT audit the cluster as a fallback.**
```

- [ ] **Edit s — line 102.**

BEFORE:
```markdown
SKIP means "this cluster was not audited, here's why" — not "the lead will fill in for the failed teammate." A `SKIP` marker in `audit.md` is honest about the gap; lead-as-auditor pretends the gap doesn't exist while actually producing shallower findings without the reference-file depth a real cluster auditor brings (cluster auditors load 5-10 cluster reference files; the lead loads only orchestration content).
```

AFTER:
```markdown
SKIP means "this cluster was not audited, here's why" — not "the lead will fill in for the failed subagent." A `SKIP` marker in `audit.md` is honest about the gap; lead-as-auditor pretends the gap doesn't exist while actually producing shallower findings without the reference-file depth a real cluster specialist brings (cluster specialists load 5-10 cluster reference files; the lead loads only orchestration content).
```

- [ ] **Edit t — line 104.**

BEFORE:
```markdown
**The same rationalization rules from the sections above apply:** the lead orchestrates, the lead does NOT do the teammate's work, even when the teammate fails.
```

AFTER:
```markdown
**The same rationalization rules from the sections above apply:** the lead orchestrates, the lead does NOT do the subagent's work, even when the subagent fails.
```

- [ ] **Edit u — lines 106-110.**

BEFORE:
```markdown
When a cluster auditor fails, the lead's correct response is:
1. Retry the spawn once (via TaskUpdate + re-dispatch).
2. If the retry fails, mark the cluster `SKIP` with a reason note in `audit.md`.
3. Log the failure to `audit-trace.log` with the cluster slug and failure mode.
4. Continue to the next phase with N-1 clusters instead of N. The Priority Path synthesis will operate on the remaining clusters.
```

AFTER:
```markdown
When a cluster specialist fails, the lead's correct response is:
1. Retry the spawn once (via fresh one-shot subagent with validation error embedded via scripts/test-specialist.py --write-retry-prompt).
2. If the retry fails, mark the cluster `SKIP` with a reason note in `audit.md`.
3. Log the failure to `audit-trace.log` with the cluster slug and failure mode.
4. Continue to the next phase with N-1 clusters instead of N. The Priority Path synthesis will operate on the remaining clusters.
```

- [ ] **Edit v — line 112 (counter + aliases).**

BEFORE:
```markdown
The structural `cluster_files_written` counter in `audit-trace.log` will reflect the actual number of cluster files produced (N-1), and the self-check assertion at audit completion will not fire because the contract is "cluster_files_written == team_spawned_auditors" — if one auditor failed to write, the counter stays at N-1 matching N-1 spawned-then-failed auditors. See `${CLAUDE_PLUGIN_ROOT}/contracts/trace-assertion-canary.md` for the full assertion contract.
```

AFTER:
```markdown
The structural `cluster_files_written` counter in `audit-trace.log` will reflect the actual number of cluster files produced (N-1), and the self-check assertion at audit completion will not fire because the contract is "cluster_files_written == subagent_spawned_specialists" (backwards-compat aliases: team_spawned_specialists, team_spawned_auditors) — if one specialist failed to write, the counter stays at N-1 matching N-1 spawned-then-failed specialists. See `${CLAUDE_PLUGIN_ROOT}/contracts/trace-assertion-canary.md` for the full assertion contract.
```

- [ ] **Edit w — cancellation section terminology (line ~222): "zombie teammates" → "zombie subagents".** Apply as a targeted replacement within the `### Why this exists` paragraph.

BEFORE (substring):
```
Ctrl-C left zombie teammates, half-written cluster-emission JSON files
```

AFTER (substring):
```
Ctrl-C left zombie subagents, half-written cluster-emission JSON files
```

- [ ] **Edit x — cancellation section (line ~267): "cleanup teammates" → "cleanup subagents".**

BEFORE (substring):
```
- The lead does NOT spawn cleanup teammates.
```

AFTER (substring):
```
- The lead does NOT spawn cleanup subagents.
```

- [ ] **Edit y — cancellation section "What this is NOT" (line ~282): "A teammate or subagent already in flight" → "A subagent already in flight".**

BEFORE (substring):
```
- **Not a hard kill.** A teammate or subagent already in flight when the lead reads cancel.flag will complete its current dispatch and return a result;
```

AFTER (substring):
```
- **Not a hard kill.** A subagent already in flight when the lead reads cancel.flag will complete its current dispatch and return a result;
```

- [ ] **Edit z — cross-reference list (line ~300).**

BEFORE:
```markdown
- **`skills/audit/SKILL.md`** — `<no_preflight_questions>` and `<acquisition_must_spawn_teammate>` defer to this file. Audit lead reads this at the top of the skill invocation.
```

AFTER:
```markdown
- **`skills/audit/SKILL.md`** — `<no_preflight_questions>` and `<acquisition_must_spawn_subagent>` defer to this file. Audit lead reads this at the top of the skill invocation.
```

- [ ] **Edit aa — cross-reference list (line ~304).**

BEFORE:
```markdown
- **`${CLAUDE_PLUGIN_ROOT}/contracts/dispatch-contract.md`** — canonical spawn template (the teammates the lead must NOT do the work of).
```

AFTER:
```markdown
- **`${CLAUDE_PLUGIN_ROOT}/contracts/dispatch-contract.md`** — canonical spawn template (the one-shot subagents the lead must NOT do the work of).
```

> NOTE: the fragment's currentVerbatim==proposedVerbatim no-op entries (the `## Filesystem write atomicity`, `## Cancellation sentinel` and `## Concurrent-audit isolation` headings, and `## Lead does NOT audit a cluster as a fallback`) are intentionally NOT edited — they are preserved. Only the substring touch-ups w/x/y inside the cancellation section change.

- [ ] **Run the test — expected PASS.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py::test_lead_discipline_terminology_and_preserved_sections -v
```

- [ ] **Run the suite subset.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py -q
python -m pytest tests/ -q -k "lead or discipline or ownership or cancel"
```

- [ ] **Commit.**

```
git add contracts/lead-discipline.md tests/test_specialist_subagent_dispatch.py
git commit -m "refactor(lead-discipline): teammate->subagent terminology; SendMessage-retry->fresh re-dispatch

cancel.flag sentinel + file-ownership + concurrent-audit-isolation preserved
verbatim; self-check counter uses subagent_spawned_specialists with aliases.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 9 — contracts/ethics-subagent-v2.md + contracts/synthesizer-v2.md: template-bug fix (dispatch as one-shot subagent, no name/team_name)

**Files:**
- Modify: `contracts/ethics-subagent-v2.md`
- Modify: `contracts/synthesizer-v2.md`
- Test (append): `tests/test_specialist_subagent_dispatch.py`

> **CONSISTENCY OVERRIDE — read before editing.** The fragment proposes rewriting both line-16 dispatch sentences to say "**dispatches via the Task tool**" and add `prompt=…`, dropping the `name:` parameter. The design spec §3.7 frames this as a **template-bug fix to match the canonical `dispatch-contract.md`**, and the consistency rule mandates `Agent` as the canonical tool name (with `Task` only as a legacy alias) and **no broad Task↔Agent churn**. To honor BOTH the spec (one-shot subagent, no `name`) AND the consistency rule (canonical tool = `Agent`), the AFTER text below keeps the tool name **`Agent`**, drops the `name:` parameter, and adds `prompt=…`. The guard test is adjusted to assert "no `name:` / no `team_name` / has `prompt=`" rather than asserting the literal string "Task tool" (which would contradict the consistency rule). See Conflicts found.

- [ ] **Append the failing guard test:**

```python
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
```

- [ ] **Run it — expected FAIL.** Reason: both files' line 16 still carry `name: "ethics-page"` / `name: "synthesizer-{engagement-id}"` and no `prompt=`.

```
python -m pytest tests/test_specialist_subagent_dispatch.py::test_ethics_and_synthesizer_dispatch_have_no_name_or_team_name -v
```

> MEASURE-TWICE: line 16 is 0-indexed line 15 in the test. Confirm the live line number; if the dispatch sentence is on a different line, the test's `[15]` index and the edit anchor both move.

- [ ] **Edit 1 — `contracts/ethics-subagent-v2.md` line 16.**

BEFORE:
```markdown
The result is a single user-turn prompt string. The lead dispatches via the Agent tool (`subagent_type: "general-purpose"`, `model: "sonnet"`, `name: "ethics-page"`). Sonnet 4.6 is the v2 default for ethics per [`contracts/dispatch-contract.md`](dispatch-contract.md) — ethics judgment fits within the cluster-auditor model tier (focused reading, schema-validated emission, no synthesis).
```

AFTER:
```markdown
The result is a single user-turn prompt string. The lead dispatches via the Agent tool (`subagent_type: "general-purpose"`, `model: "sonnet"`, `prompt=<rendered ethics template>`) as a one-shot subagent (no `team_name`, no `name`). Sonnet 4.6 is the v2 default for ethics per [`contracts/dispatch-contract.md`](dispatch-contract.md) — ethics judgment fits within the cluster-auditor model tier (focused reading, schema-validated emission, no synthesis).
```

- [ ] **Edit 2 — `contracts/synthesizer-v2.md` line 16.**

BEFORE:
```markdown
The result is a single user-turn prompt string. The lead dispatches via the Agent tool (`subagent_type: "general-purpose"`, `model: "opus"`, `name: "synthesizer-{engagement-id}"`). Opus 4.6 with 1M context is the v2 default per [`contracts/dispatch-contract.md`](dispatch-contract.md). The synthesizer is the role Opus is reserved for.
```

AFTER:
```markdown
The result is a single user-turn prompt string. The lead dispatches via the Agent tool (`subagent_type: "general-purpose"`, `model: "opus"`, `prompt=<rendered synthesizer template with canonical_f_refs_manifest>`) as a one-shot subagent (no `team_name`, no `name`). Opus 4.6 with 1M context is the v2 default per [`contracts/dispatch-contract.md`](dispatch-contract.md). The synthesizer is the role Opus is reserved for.
```

- [ ] **Run the test — expected PASS.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py::test_ethics_and_synthesizer_dispatch_have_no_name_or_team_name -v
```

- [ ] **Run the suite subset.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py -q
python -m pytest tests/ -q -k "ethics or synthesizer or template"
```

- [ ] **Commit.**

```
git add contracts/ethics-subagent-v2.md contracts/synthesizer-v2.md tests/test_specialist_subagent_dispatch.py
git commit -m "fix(contracts): ethics + synthesizer dispatch as one-shot subagents (drop name param)

Template-bug fix to match the canonical dispatch-contract: no team_name, no
name, add prompt=. Tool name kept canonical (Agent) per consistency rule.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 10 — contracts/trace-assertion-canary.md: subagent_spawned_specialists canonical, team_spawned_* aliases retained

**Files:**
- Modify: `contracts/trace-assertion-canary.md`
- Test (append): `tests/test_specialist_subagent_dispatch.py`

> Per design §3.4 the canonical counter + the alias rules "**already exist**" here. This task makes the change minimal-but-explicit: name `subagent_spawned_specialists` as the canonical specialist counter and retain `team_spawned_specialists` / `team_spawned_auditors` as accepted aliases. If the live file already documents `subagent_spawned_specialists` as canonical with both aliases, this task is a no-op beyond the guard test — **say so in the commit body** and skip edits that don't apply.

- [ ] **Append the failing guard test:**

```python
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
```

- [ ] **Run it — expected FAIL** if the canonical counter is not yet documented here (the drafting pass found the header still listing `team_spawned_specialists` as the v2 primary). If it already passes, record "already supported — no edit needed" and move to commit with the test only.

```
python -m pytest tests/test_specialist_subagent_dispatch.py::test_trace_header_accepts_subagent_spawned_specialists -v
```

- [ ] **Edit 1 — v2 header assertions block: insert the canonical counter after `subagent_spawned_acquirers`.**

BEFORE:
```markdown
#   subagent_spawned_acquirers: 0         ← v2: incremented after each Task call dispatching an acquirer
#   team_spawned_specialists: 0           ← v2: incremented after each Agent call dispatching a cluster specialist (teammate dispatch retained)
```

AFTER:
```markdown
#   subagent_spawned_acquirers: 0         ← v2: incremented after each Task call dispatching an acquirer
#   subagent_spawned_specialists: 0       ← v2: incremented after each Agent call dispatching a cluster specialist (one-shot subagent dispatch)
#   team_spawned_specialists: 0           ← v2: legacy teammate dispatch; retained for backwards compatibility (see alias rules below)
```

- [ ] **Edit 2 — Counter alias rules table (lines ~101-107), row 2 ("Cluster specialists ran").**

BEFORE:
```markdown
| Cluster specialists ran | `team_spawned_auditors >= expected_auditor_count` | `team_spawned_specialists >= expected_specialist_count` |
```

AFTER:
```markdown
| Cluster specialists ran | `team_spawned_auditors >= expected_auditor_count` | `subagent_spawned_specialists >= expected_specialist_count` (one-shot) OR `team_spawned_specialists >= expected_specialist_count` (legacy teammate) |
```

- [ ] **Edit 3 — Counter alias rules table (line ~105), row 3 ("Cluster files on disk").**

BEFORE:
```markdown
| Cluster files on disk | `cluster_files_written == team_spawned_auditors` | `cluster_files_written == team_spawned_specialists` |
```

AFTER:
```markdown
| Cluster files on disk | `cluster_files_written == team_spawned_auditors` | `cluster_files_written == (subagent_spawned_specialists + team_spawned_specialists)` |
```

- [ ] **Edit 4 — Self-check v2 path (lines ~282-287): replace the specialists assertion.**

BEFORE:
```markdown
- `team_spawned_specialists >= expected_specialist_count` — OR v1 alias `team_spawned_auditors`
```

AFTER:
```markdown
- `(subagent_spawned_specialists + team_spawned_specialists) >= expected_specialist_count` — one-shot subagent dispatch (primary) or legacy teammate dispatch (both counted toward the expected total); OR v1 alias `team_spawned_auditors`
```

- [ ] **Run the test — expected PASS.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py::test_trace_header_accepts_subagent_spawned_specialists -v
```

- [ ] **Run the suite subset.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py -q
python -m pytest tests/ -q -k "trace or canary or counter"
```

- [ ] **Commit.**

```
git add contracts/trace-assertion-canary.md tests/test_specialist_subagent_dispatch.py
git commit -m "feat(trace-canary): subagent_spawned_specialists canonical; team_spawned_* retained as aliases

Header + alias-rule table + self-check accept the one-shot counter as primary
and both legacy teammate counters as backwards-compat aliases.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 11 — Annotate dead team machinery: team-lifecycle.md (multi-planner only; DO NOT delete) + test-cluster-specialist-parity.py archive header

**Files:**
- Modify: `contracts/team-lifecycle.md`
- Modify: `scripts/test-cluster-specialist-parity.py`
- Test (append): `tests/test_specialist_subagent_dispatch.py`

- [ ] **Append the failing guard test:**

```python
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
```

- [ ] **Run it — expected FAIL.** Reason: `team-lifecycle.md` has no MIGRATION NOTICE annotation, and the parity harness docstring is not yet marked ARCHIVED.

```
python -m pytest tests/test_specialist_subagent_dispatch.py::test_team_lifecycle_annotated_and_parity_archived -v
```

- [ ] **Edit 1 — `contracts/team-lifecycle.md` top-of-file: insert the MIGRATION NOTICE after the intro (after line ~6).**

BEFORE:
```markdown
# Agent Teams lifecycle

Canonical lifecycle contract for every ECP v5.0 skill that uses Claude Code's experimental Agent Teams feature (`/ecp:audit`, `/ecp:build`, `/ecp:compare`, `/ecp:resume`). `/ecp:quick-scan` intentionally does NOT use teams — it runs as a single-agent dispatch because quick-scan's value proposition is speed and quick-scan only ever has one auditor, so the team overhead would not pay for itself.

Prior to ECP v5.0.x this lifecycle prose was duplicated across four skill files with the hard-requirement env var check, the `TeamCreate` naming convention, and the create/populate/spawn/coordinate/cleanup step list all copy-pasted. This reference is the single source of truth.
```

AFTER:
```markdown
# Agent Teams lifecycle

Canonical lifecycle contract for every ECP v5.0 skill that uses Claude Code's experimental Agent Teams feature (`/ecp:audit`, `/ecp:build`, `/ecp:compare`, `/ecp:resume`). `/ecp:quick-scan` intentionally does NOT use teams — it runs as a single-agent dispatch because quick-scan's value proposition is speed and quick-scan only ever has one auditor, so the team overhead would not pay for itself.

Prior to ECP v5.0.x this lifecycle prose was duplicated across four skill files with the hard-requirement env var check, the `TeamCreate` naming convention, and the create/populate/spawn/coordinate/cleanup step list all copy-pasted. This reference is the single source of truth.

---

## MIGRATION NOTICE (v2.1.63+): Cluster specialists moved to subagent dispatch

**For `/ecp:audit` cluster-specialist auditors:** As of v2.1.63, the hard-requirement env-var gate (§ "Hard requirement" below) and Resume team-recreation (§ "Resume" below) are DEAD for the audit path. Cluster specialists now dispatch as one-shot subagents via the `Agent(subagent_type="general-purpose")` tool, not teammates. The env-var check, team creation, and task-list coordination no longer apply to cluster auditors.

**Retained sections below** are annotated but NOT deleted. They remain as:
- **Historical documentation** for how v5.0–v2.1.62 worked.
- **Foundation for future multi-planner resume** (if a future phase restores multi-planner team coordination, Resume team-recreation logic will return; the prose is ready).

**What changed:**
- Lead no longer calls `TeamCreate` at engagement start.
- Cluster auditors dispatch via fresh `Agent(description="...", prompt=<specialist.txt>, model="sonnet"|"opus")` (see `contracts/dispatch-contract.md`).
- On specialist validation failure, lead re-dispatches a FRESH subagent with error embedded (via `scripts/test-specialist.py --write-retry-prompt`).
- Trace counter `subagent_spawned_specialists` tracks dispatches; `team_spawned_auditors` is a legacy alias (kept for backwards compat).
- Concurrency controlled via `--max-concurrent` flag (default=all/unlimited); see `contracts/flags.md`.
```

- [ ] **Edit 2 — `scripts/test-cluster-specialist-parity.py` module docstring (lines ~1-17): mark ARCHIVED.**

BEFORE:
```python
"""Cluster-specialist subagent-vs-teammate parity diff harness.

Phase H deliverable 5 (2026-04-28). Compares two `cluster-emission-v1.json`
files produced by dispatching the SAME specialist prompt as a subagent
(`Task` tool) vs as a teammate (`Agent` tool with team_name). If they're
byte-identical (modulo irreducible-variance fields like timestamps and
telemetry), v2.1 can flip cluster specialists to subagent dispatch.

Phase H deliverable 5: see contracts/dispatch-contract.md for the
specialist dispatch shape that v2.1 may flip from teammate to subagent.

Usage:
    python scripts/test-cluster-specialist-parity.py \\
        --subagent parity-test-pricing-desktop.subagent.json \\
        --teammate parity-test-pricing-desktop.teammate.json \\
        --report parity-test-pricing-desktop.report.md
"""
```

AFTER:
```python
"""Cluster-specialist subagent-vs-teammate parity diff harness (ARCHIVED).

[ARCHIVED — Phase H parity evidence, retained for audit trail. Not run in the gate.]

Phase H deliverable 5 (2026-04-28). Compares two `cluster-emission-v1.json`
files produced by dispatching the SAME specialist prompt as a subagent
(`Task` tool) vs as a teammate (`Agent` tool with team_name). If they're
byte-identical (modulo irreducible-variance fields like timestamps and
telemetry), v2.1 can flip cluster specialists to subagent dispatch.

As of v2.1.63, cluster specialists HAVE been flipped to subagent dispatch
(Agent tool, no team_name). This harness was the validation evidence. Retained
for audit trail; not executed in the standard test gate.

Usage (historical; not run in CI):
    python scripts/test-cluster-specialist-parity.py \\
        --subagent parity-test-pricing-desktop.subagent.json \\
        --teammate parity-test-pricing-desktop.teammate.json \\
        --report parity-test-pricing-desktop.report.md
"""
```

- [ ] **Run the test — expected PASS.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py::test_team_lifecycle_annotated_and_parity_archived -v
```

- [ ] **Run the suite subset.**

```
python -m pytest tests/test_specialist_subagent_dispatch.py -q
python -m pytest tests/ -q -k "lifecycle or parity"
```

- [ ] **Commit.**

```
git add contracts/team-lifecycle.md scripts/test-cluster-specialist-parity.py tests/test_specialist_subagent_dispatch.py
git commit -m "docs(team-lifecycle): annotate audit-path dead (multi-planner only); archive parity harness

team-lifecycle.md MIGRATION NOTICE marks env-var gate + Resume dead for audit,
retained for future multi-planner. test-cluster-specialist-parity.py docstring
marked ARCHIVED (retained, not run in gate). No code deleted.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 12 — Update existing tests to accept subagent_spawned_specialists

**Files:**
- Modify: `tests/test_v2_determinism_gate.py`
- Modify: `tests/test_g24_trace_counters_reconcile.py`

> These are the `kind=="update"` guard tests from the fragments. No new file; exact before/after assertions below. After Task 1 re-pointed the alias map, some of these may already pass via normalization — apply the edits anyway so the tests explicitly exercise the canonical counter, and confirm green.
>
> **Heads-up on the consolidated file's `canary_checks` reference:** one merged guard test (`test_canary_checks_accepts_both_specialist_counters`, contributed by the fragment for these existing-test files) asserts that `scripts/assembly/canary_checks.py` defines a `_SPECIALIST_COUNTERS` tuple containing BOTH a legacy name and `subagent_spawned_specialists`. The drafting pass flagged that this constant may not exist in the live file. Before relying on that test: READ `scripts/assembly/canary_checks.py`. If `_SPECIALIST_COUNTERS` exists, ensure it lists `subagent_spawned_specialists` plus a legacy alias and keep the test. If it does NOT exist, DO NOT invent new product code in this assembly plan — instead OMIT that single test function from the consolidated file (it asserts an interface the migration does not introduce) and note the omission in this task's commit body. The determinism-gate alias normalization (Task 1) is the actual mechanism that makes the canary accept both counters.

- [ ] **Edit 1 — `tests/test_v2_determinism_gate.py` line ~71.**

BEFORE:
```python
        self.assertEqual(c["team_spawned_specialists"], 20)
```

AFTER:
```python
        # Accept either team_spawned_specialists (v1 audit mode) or
        # subagent_spawned_specialists (v2 specialist subagent dispatch post-Phase-H.2).
        # The gate normalizes to max(aliases) for backward-compat validation.
        specialist_count = max(
            c.get("subagent_spawned_specialists", 0),
            c.get("team_spawned_specialists", 0),
        )
        self.assertEqual(specialist_count, 20)
```

- [ ] **Edit 2 — `tests/test_v2_determinism_gate.py` lines ~98-99.**

BEFORE:
```python
            # v1 names should fold into v2 canonical names.
            self.assertEqual(c.get("expected_specialist_count"), 10)
            self.assertEqual(c.get("team_spawned_specialists"), 10)
            self.assertEqual(c.get("subagent_spawned_acquirers"), 1)
```

AFTER:
```python
            # v1 names should fold into v2 canonical names.
            self.assertEqual(c.get("expected_specialist_count"), 10)
            # Specialist counters: both old (team_spawned) and new (subagent_spawned)
            # are valid; the alias normalization accepts either.
            specialist_count = max(
                c.get("subagent_spawned_specialists", 0),
                c.get("team_spawned_specialists", 0),
            )
            self.assertEqual(specialist_count, 10)
            self.assertEqual(c.get("subagent_spawned_acquirers"), 1)
```

- [ ] **Edit 3 — `tests/test_v2_determinism_gate.py` line ~158 (mismatch fixture).**

BEFORE:
```python
                """# ECP Audit Forensic Trace
# Pipeline: v2
# ASSERTIONS:
#   expected_specialist_count: 20
#   team_spawned_specialists: 15
#   cluster_files_written: 15
```

AFTER:
```python
                """# ECP Audit Forensic Trace
# Pipeline: v2
# ASSERTIONS:
#   expected_specialist_count: 20
#   subagent_spawned_specialists: 15
#   cluster_files_written: 15
```

- [ ] **Edit 4 — `tests/test_g24_trace_counters_reconcile.py` line ~117 (clean run).**

BEFORE:
```python
        self._write_trace({
            "subagent_spawned_acquirers": 2,
            "team_spawned_specialists": 4,
            "subagent_spawned_ethics": 1,
            "subagent_spawned_synthesizer": 1,
            "cluster_files_written": 4,
        })
```

AFTER:
```python
        self._write_trace({
            "subagent_spawned_acquirers": 2,
            "subagent_spawned_specialists": 4,
            "subagent_spawned_ethics": 1,
            "subagent_spawned_synthesizer": 1,
            "cluster_files_written": 4,
        })
```

- [ ] **Edit 5 — `tests/test_g24_trace_counters_reconcile.py` line ~143 (over-count).**

BEFORE:
```python
        self._write_trace({
            "subagent_spawned_acquirers": 5,  # over-counted vs 1 observed
            "team_spawned_specialists": 12,   # over-counted vs 1 observed
            "subagent_spawned_ethics": 1,
            "subagent_spawned_synthesizer": 1,
            "cluster_files_written": 12,
        })
```

AFTER:
```python
        self._write_trace({
            "subagent_spawned_acquirers": 5,  # over-counted vs 1 observed
            "subagent_spawned_specialists": 12,   # over-counted vs 1 observed
            "subagent_spawned_ethics": 1,
            "subagent_spawned_synthesizer": 1,
            "cluster_files_written": 12,
        })
```

- [ ] **Edit 6 — `tests/test_g24_trace_counters_reconcile.py` lines ~160-166 (v1 alias docstring).**

BEFORE:
```python
    def test_v1_counter_alias_accepted_for_specialists(self):
        """contracts/dispatch-contract.md §"Backwards compatibility":
        v1 audits use team_spawned_auditors; v2 uses team_spawned_specialists.
        The canary accepts either as evidence the specialist role ran."""
        self._write_meta(["pricing"], ["desktop"])
        self._touch_cluster_emission("pricing", "desktop")
        self._touch_baton("desktop")
        self._touch_ethics()
        self._touch_synth()
        self._write_trace({
            "team_spawned_acquirers": 1,    # v1 acquirer counter name
            "team_spawned_auditors": 1,     # v1 specialist counter name
            "subagent_spawned_ethics": 1,
            "subagent_spawned_synthesizer": 1,
            "cluster_files_written": 1,
        })
```

AFTER:
```python
    def test_v1_counter_alias_accepted_for_specialists(self):
        """contracts/dispatch-contract.md §"Backwards compatibility":
        v1 audits use team_spawned_auditors; v2 uses either team_spawned_specialists
        (Agent-Teams dispatch) or subagent_spawned_specialists (one-shot subagent dispatch).
        The canary accepts any of the three as evidence the specialist role ran."""
        self._write_meta(["pricing"], ["desktop"])
        self._touch_cluster_emission("pricing", "desktop")
        self._touch_baton("desktop")
        self._touch_ethics()
        self._touch_synth()
        self._write_trace({
            "team_spawned_acquirers": 1,    # v1 acquirer counter name
            "team_spawned_auditors": 1,     # v1 specialist counter name (v1 audit mode)
            "subagent_spawned_ethics": 1,
            "subagent_spawned_synthesizer": 1,
            "cluster_files_written": 1,
        })
```

- [ ] **Edit 7 — `tests/test_g24_trace_counters_reconcile.py` line ~171: append a new test after `test_v1_counter_alias_accepted_for_specialists`.**

BEFORE:
```python
        result = check_trace_counters_reconcile_with_artifacts(self.eng)
        self.assertTrue(
            result["passed"],
            f"v1 counter aliases must reconcile. summary={result['summary']!r}",
        )
```

AFTER:
```python
        result = check_trace_counters_reconcile_with_artifacts(self.eng)
        self.assertTrue(
            result["passed"],
            f"v1 counter aliases must reconcile. summary={result['summary']!r}",
        )

    def test_v2_subagent_specialist_counter_accepted(self):
        """Phase H.2 (2026-06-01): specialists migrate from Agent-Teams dispatch
        (team_spawned_specialists) to one-shot subagent dispatch
        (subagent_spawned_specialists). The canary accepts the new counter name
        as evidence the specialist role ran."""
        self._write_meta(["pricing"], ["desktop"])
        self._touch_cluster_emission("pricing", "desktop")
        self._touch_baton("desktop")
        self._touch_ethics()
        self._touch_synth()
        self._write_trace({
            "subagent_spawned_acquirers": 1,    # v2 acquirer
            "subagent_spawned_specialists": 1,  # v2 specialist (subagent dispatch)
            "subagent_spawned_ethics": 1,
            "subagent_spawned_synthesizer": 1,
            "cluster_files_written": 1,
        })
        result = check_trace_counters_reconcile_with_artifacts(self.eng)
        self.assertTrue(
            result["passed"],
            f"v2 subagent specialist counter must reconcile. summary={result['summary']!r}",
        )
```

- [ ] **Edit 8 — `tests/test_g24_trace_counters_reconcile.py` lines ~201-209 (G22 reproducer).**

BEFORE:
```python
        # The 2026-05-28-e4050c0e trace shape — counters all 0.
        self._write_trace(
            {
                "subagent_spawned_acquirers": 0,
                "team_spawned_specialists": 0,
                "subagent_spawned_ethics": 0,
                "subagent_spawned_synthesizer": 0,
            },
            header_prefix="# Counters\n",
        )
```

AFTER:
```python
        # The 2026-05-28-e4050c0e trace shape — counters all 0. Note: the original
        # engagement used team_spawned_specialists (pre-Phase-H.2); this test uses
        # subagent_spawned_specialists to verify the G24 fix works for both counter names.
        self._write_trace(
            {
                "subagent_spawned_acquirers": 0,
                "subagent_spawned_specialists": 0,
                "subagent_spawned_ethics": 0,
                "subagent_spawned_synthesizer": 0,
            },
            header_prefix="# Counters\n",
        )
```

- [ ] **Edit 9 — `tests/test_g24_trace_counters_reconcile.py` lines ~240-246 (partial violation).**

BEFORE:
```python
        self._write_trace({
            "subagent_spawned_acquirers": 1,
            "team_spawned_specialists": 0,   # under-counted vs 1 observed
            "subagent_spawned_ethics": 1,
            "subagent_spawned_synthesizer": 1,
            "cluster_files_written": 1,
        })
```

AFTER:
```python
        self._write_trace({
            "subagent_spawned_acquirers": 1,
            "subagent_spawned_specialists": 0,   # under-counted vs 1 observed
            "subagent_spawned_ethics": 1,
            "subagent_spawned_synthesizer": 1,
            "cluster_files_written": 1,
        })
```

- [ ] **Run the updated suites — expected PASS.**

```
python -m pytest tests/test_v2_determinism_gate.py tests/test_g24_trace_counters_reconcile.py -v
```

- [ ] **Run the full consolidated guard file too** (catch any `canary_checks` interface mismatch before commit).

```
python -m pytest tests/test_specialist_subagent_dispatch.py -q
```

- [ ] **Commit.**

```
git add tests/test_v2_determinism_gate.py tests/test_g24_trace_counters_reconcile.py tests/test_specialist_subagent_dispatch.py
git commit -m "test: accept subagent_spawned_specialists in determinism-gate + g24 reconcile suites

Update hardcoded team_spawned_specialists assertions to the canonical counter
(via max(aliases)); add a v2 subagent-specialist reconcile case.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 13 — Docs: product.md §10 spec-change-log entry + handoff note

**Files:**
- Modify: `product.md`
- Modify: `docs/handoff-2026-06-01-migration-fixes-and-post-audit.md`

> No code test. This is a documentation commit; the suite stays green by construction. Use the B0/P1/#26 spec-change-log format already established in `product.md` §10.

- [ ] **MEASURE-TWICE:** READ `product.md` §10 and copy the EXACT row/entry format of the most recent spec-change-log entries (e.g., the B0 / P1 / #26 entries). Match column order, date format, and ID convention precisely; the entry below is the content to record, formatted to the live table's shape.

- [ ] **Edit 1 — append a spec-change-log entry to `product.md` §10** capturing:
  - **Change:** Cluster specialists migrated from Agent-Teams teammates to GA parallel one-shot subagents (last teammate role removed from the audit path).
  - **Contract impact:** `dispatch-contract.md` (per-role + how-to-dispatch rows, rationale section retitled "Why specialists are one-shot subagents", counter → `subagent_spawned_specialists`); `specialist-prompt-v2.md` (dispatch line drops `team_name`/`name`); `skills/audit/SKILL.md` (team-create step deleted, full-parallel default + `--max-concurrent`); `audit-reconciliation.md` (Steps 0/0b/0c recovery → fresh re-dispatch); `flags.md` (`--max-concurrent`); `trace-assertion-canary.md` (canonical counter + retained aliases); `team-lifecycle.md` (annotated dead-for-audit, retained for multi-planner).
  - **Behavioral change:** recovery delivery changes from SendMessage-bounce to fresh one-shot re-dispatch with the validation error embedded (one autofix → one fresh re-dispatch → `partial`). Concurrency default flips from waves-of-≤5 to full-parallel, with `--max-concurrent N` as the rate-limit fallback.
  - **Backwards-compat:** `team_spawned_specialists` and `team_spawned_auditors` retained as accepted aliases indefinitely; archived/v1 traces still validate.
  - **Provenance:** design `docs/2026-06-01-cluster-specialists-off-agent-teams-design.md`; decision `docs/handoff-2026-06-01-migration-fixes-and-post-audit.md` §5b.
  - **Follow-ups (out of scope here):** live `/ecp:audit` smoke run; fixture regeneration from the next real audit; broad cosmetic `Task`→`Agent` rename of other roles.

- [ ] **Edit 2 — append a short note to `docs/handoff-2026-06-01-migration-fixes-and-post-audit.md`** recording that the specialists-off-Agent-Teams migration plan has been implemented per the committed §5b decision: summarize the transport flip, the recovery change, the concurrency default + `--max-concurrent` fallback, the retained counter aliases, and the explicit follow-ups (live smoke + fixture regeneration).

- [ ] **Run the suite (should be unaffected by docs).**

```
python -m pytest tests/ -q -k "product or handoff or doc"
```

- [ ] **Commit.**

```
git add product.md docs/handoff-2026-06-01-migration-fixes-and-post-audit.md
git commit -m "docs(product): spec-change-log entry for specialists-off-Agent-Teams migration

§10 entry (B0/P1/#26 format) + handoff note recording the transport flip,
recovery change, concurrency default + --max-concurrent fallback, and retained
counter aliases.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## FINAL TASK — full-suite verification

**Files:** none (verification only).

- [ ] **Run the full suite.** Expected green: the prior baseline (966) plus the new guard tests added across Tasks 1-12.

```
python -m pytest tests/ -q
```

- [ ] **Run the determinism gate suite.** Expected green at 37.

```
python -m pytest tests/test_v2_determinism_gate.py -q
```

- [ ] **Confirm both are green before declaring done.** If anything is red, STOP and diagnose — do not paper over a failure.

- [ ] **Documented FOLLOW-UPS (out of scope for this plan, do NOT do here):**
  - A live `/ecp:audit` smoke run showing all requested specialists dispatched in one full-parallel batch, `subagent_spawned_specialists` non-zero, zero team creation / `TeamDelete`, `cluster-*-{device}.json` written, and validate→autofix→re-dispatch exercising the fresh-re-dispatch path (and surfacing the concurrent-spawn throttle early → set `--max-concurrent 5` if it recurs).
  - Regenerating the `audit-trace.log` fixtures (`fixtures/slingmods-pdp/`, `fixtures/awdmods-homepage/`, `fixtures/2026-05-02-9cd2a2ac/`) from the next real audit (NOT by hand-editing).

---

## Conflicts found

Resolved where the SPEC + CONSISTENCY RULES win over fragment draft text:

1. **Tool name for ethics/synthesizer (Task 9).** The fragment (`contracts/ethics-subagent-v2.md + contracts/synthesizer-v2.md`) proposed rewriting both line-16 dispatch sentences to "**dispatches via the Task tool**". The consistency rule mandates `Agent` as the canonical tool name (with `Task` only a legacy alias) and forbids broad `Task`↔`Agent` churn; design §3.7 frames these merely as template-bug fixes to match the canonical `dispatch-contract.md` (which uses `Agent`). **Resolution:** AFTER text keeps the tool name **`Agent`**, drops the `name:` parameter, and adds `prompt=…`. The guard test asserts "no `name:` / no `team_name` / has `prompt=`" instead of the literal "Task tool". (The fragment's own currentVerbatim shows both files already say "Agent tool" today — so the only real bug is the `name:` parameter, not the tool name.)

2. **dispatch-contract.md intro line tool name (Task 4, Edit 5).** The fragment's BEFORE quoted "Most roles dispatch as one-shot subagents (**Task tool**, no team_name)"; its AFTER already switched to "**Agent tool**". Kept the AFTER (`Agent tool`) per the consistency rule. No further churn to other roles' rows (Task/Agent alias note added once, scope-limited).

3. **skills/audit/SKILL.md Dispatch-Shape rationale (Task 6, Edit 1).** The fragment's rationale claimed specialists "use Agent because they write to shared engagement workspace … Unlike acquirer/ethics/synthesizer which use Task". This violates the rationale-hygiene rule (no "shared workspace" justification; no Task-vs-Agent distinction between specialists and the other one-shot roles). **Resolution:** only the line actually written to the file is transcribed (`one-shot subagent (Agent tool, no team_name)`); the misleading rationale is dropped and not carried into any contract prose. Correct framing (specialists are one-shot subagents like the other roles; file-presence collection is transport-independent) is used throughout.

4. **`canary_checks._SPECIALIST_COUNTERS` test (folded into Task 12 context).** The fragment for the existing-test files contributed a guard test asserting `scripts/assembly/canary_checks.py` defines a `_SPECIALIST_COUNTERS` tuple containing both a legacy name and `subagent_spawned_specialists`. The drafting pass itself flagged that this constant lives in a "parallel scripts-layer fragment" that does not exist, and may not be present in the live file. Editing repo files is out of scope for this assembly, and the plan must not invent new product code. **Resolution:** Task 12 instructs the implementer to READ `canary_checks.py` first and, if `_SPECIALIST_COUNTERS` does not exist, OMIT that single merged test function (noting the omission in the commit body) rather than introduce a new interface. The determinism-gate alias normalization (Task 1) is the real mechanism that makes the canary accept both counters. This is a fragment-internal inconsistency rather than a spec conflict, recorded here for transparency.

No conflicts altered the SCOPE or task order; all §3 sections and the §4 inventory are covered.


## Execution log

- **Task 1 — DONE** (commit `5ba73bd`): `determinism_gate.py` canonical counter → `subagent_spawned_specialists` (legacy `team_spawned_specialists`/`team_spawned_auditors` retained as aliases); created `tests/test_specialist_subagent_dispatch.py` with 4 passing guard tests.
- **Coupled fix — DONE** (commit `4585602`): brought forward Task 12 Edits 1–3 to `tests/test_v2_determinism_gate.py` because Task 1's counter rename broke two assertions there. **LEARNING:** a counter rename in `determinism_gate.py` is coupled to every test asserting the old key — keep them in one logical change. **Task 12 remaining:** the `tests/test_g24_trace_counters_reconcile.py` edits (fragment Edits 4–5) and the `canary_checks._SPECIALIST_COUNTERS` read-first-then-omit check.
- Full suite GREEN at this point.
- **Task 2 — DONE** (`fa48322`): `test-specialist.py` Agent-dispatch docstring wording; `--write-retry-prompt` was already present (per MEASURE-TWICE note) so only the help text was clarified.
- **Task 3 — DONE** (`ea1e8df`): `flags.md` `--max-concurrent` section. Spec review caught a missing **Flag summary table** row (the file's own "Adding a new flag" rule requires it); row added and amended into the same commit. Verified `--deep` is prose-driven (no code parser), so doc-only `--max-concurrent` is correct parity.
- **Task 4 — DONE** (`144d6e4`): dispatch-contract.md per-role + how-to-dispatch rows → subagent (drop `team_name`/`name`, add `description`); rationale section retitled; counter row → `subagent_spawned_specialists`; intro line; Task/Agent alias note. **Guard-test regex bug fixed** (plan's `dispatch_table` regex captured table col-2, not the col-3 Agent call — verified empirically, corrected to `\| Cluster specialist \| [^|]*\| (.*?) \|`). Also fixed 3 stale "What changes for the lead" v2-column cells (rows 85/88/90) that still called specialists teammates. OUT OF SCOPE (left per plan): line 301/320 "Subagent dispatch contract uses Task tool" section (the broad Task→Agent rename follow-up).
- **Task 5 — DONE** (`7e55426`): specialist-prompt-v2.md dispatch line drops `team_name`/`name`; No-coordination preserved.
- **Task 6 — DONE** (`beed16b`): audit SKILL.md Dispatch-Shape line; deleted "Create the audit team" step + renumbered Phase Order to contiguous 1–14; full-parallel + `--max-concurrent`; fresh-re-dispatch recovery. Guard test #1's regex (same col-span bug) corrected.
- **Task 7 — DONE** (`517a79a`): audit-reconciliation.md Steps 0/0b/0c SendMessage-bounce → fresh `Agent(...)` re-dispatch. **Guard-test preserved-logic anchors corrected** (`triple-backtick code fences`/`TITLE field rules` only lived inside the removed SendMessage blocks → swapped to surviving `code-fenced`/`FINDING: FAIL`/`identical TITLE`). Fence-balance verified unchanged. KNOWN RESIDUAL (out of scope; plan does file-by-file terminology): "teammate"/"two-attempt loop"/"third failure" prose at lines ~124/126/170/220.
- **Task 8 — DONE** (`ffa8da0`): lead-discipline.md 27 terminology edits (teammate→subagent; SendMessage-retry→fresh re-dispatch); cancel.flag sentinel + file-ownership + concurrent-audit-isolation preserved verbatim (only w/x/y substrings). Residual historical/illustrative "teammate" at lines 5/44 left intentionally.
- **Task 9 — DONE** (`d39de6f`): ethics-subagent-v2.md + synthesizer-v2.md line-16 dispatch drops `name:` param, adds `prompt=`. **Plan-internal contradiction reconciled**: plan's AFTER text said "(no `team_name`, no `name`)" but its own guard test asserts `"team_name" not in line_16` — reworded AFTER to "(no teammate registration)" to honor the test.
- **Task 10 — DONE** (`9c2f8a9`): trace-assertion-canary.md header + alias-rule table + self-check → canonical `subagent_spawned_specialists` (aliases retained). Added Edit 5: aligned self-check line 284 with Edit 3 (line 105) — both now sum the subagent+legacy counters (plan edited only 105, leaving 284 contradictory).
- **Task 11 — DONE** (`017f5da`): team-lifecycle.md MIGRATION NOTICE (env-var gate + Resume dead for audit, retained for multi-planner); test-cluster-specialist-parity.py docstring ARCHIVED. Nothing deleted; parity harness still compiles.
- **Task 12 — DONE** (`d9a8090`): **RUNTIME change** — `scripts/assembly/canary_checks.py` `_SPECIALIST_COUNTERS` now includes canonical `subagent_spawned_specialists` (additive max; legacy aliases retained), so a v2 one-shot audit passes its completion canary. g24 reconcile fixtures flipped to the canonical counter + new `test_v2_subagent_specialist_counter_accepted`. test_v2_determinism_gate.py Edits 1–3 were already landed in the `4585602` coupled fix (not re-touched). **Code-side migration is now complete**: the only two specialist-counter consumers (`determinism_gate.py` Task 1 + `canary_checks.py` Task 12) accept the canonical counter.
- **Task 13 — DONE** (`12e2140`): product.md §10 spec-change-log entry + handoff §5b implementation-status note (COMPLETE).
- **FINAL VERIFICATION — GREEN**: full suite **989 passed, 12 skipped, 54 subtests**; determinism-gate suite **37 passed**; consolidated guard file **18 passed**. On `main`, 17 commits ahead of origin (unpushed).
- **DOCUMENTED FOLLOW-UPS (NOT done — out of scope per plan):** (1) live `/ecp:audit` smoke run — green tests prove the EDITS, not live dispatch (point: "green ≠ verified"); (2) regenerate `audit-trace.log` fixtures from a real audit; (3) broad cosmetic `Task`→`Agent` rename of the other one-shot roles (acquirer/ethics/synthesizer/planner/reviewer/builder) — explicitly out of scope; this would also clean the residual prose noted in Tasks 4/7.
