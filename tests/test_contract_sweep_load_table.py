"""Grep-guard for the v1->v2 contract sweep (Lane A — SKILL load table + dead files).

The 2026-06-09 contract-reword sweep (product.md spec v1.2 conformance) removed
five legacy-era files from `skills/audit/SKILL.md`'s runtime load table because a
lead following the load order could be pulled onto mutually exclusive paths (v2
JSON / no-team from SKILL itself vs v1 markdown / Agent-Teams from the loaded
files):

  - `workflows/audit.md`                 (v1 Agent-Teams teammate model)
  - `contracts/synthesizer-subagent.md`  (v1 per-device synthesizer flow,
                                          superseded by `synthesizer-v2.md`)
  - `contracts/audit-assembly.md`        (v1 `audit.md` template, v2 emits
                                          `audit-{device}.md` from the
                                          synthesizer directly)
  - `contracts/progress-comparison.md`   (frozen per product.md §5, compare
                                          family)
  - `contracts/team-lifecycle.md`        (dead for the audit path since the
                                          2026-06-01 §10 migration; retained
                                          as a §7 interface contract for the
                                          frozen multi-planner family)

This test pins three guarantees so the sweep does not silently regress:

  1. NONE of the five dead files appears in `SKILL.md`'s phase-by-phase load
     table. (They may still be mentioned elsewhere in the file — e.g. the "Do
     NOT load these legacy files" annotation immediately under the table — but
     the table itself must not list them.)
  2. EACH dead file's body carries a header annotation that plainly marks it
     dead or frozen per product.md §5 — so a reader who follows a stale
     pointer from somewhere else still sees the warning at the top.
  3. `SKILL.md` carries no live-voiced TeamCreate / team_name / SendMessage
     broadcast instructions for the audit path (G21-style guard). It may
     still mention `team_name` in the dispatch-shape section as the v2
     "Cluster specialists: one-shot subagent (Agent tool, no team_name)"
     callout — that is a frozen-voice instruction, not a live-voice one.

Run:
    python -m pytest tests/test_contract_sweep_load_table.py -q
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SKILL = _REPO / "skills" / "audit" / "SKILL.md"

# The five files Lane A pulled out of the load table.
DEAD_FILES = (
    "workflows/audit.md",
    "contracts/synthesizer-subagent.md",
    "contracts/audit-assembly.md",
    "contracts/progress-comparison.md",
    "contracts/team-lifecycle.md",
)


def _read(rel_path: str) -> str:
    return (_REPO / rel_path).read_text(encoding="utf-8")


def _load_table_block(skill_md: str) -> str:
    """Extract the `## Runtime Load Order` phase-by-phase load table.

    The table is a markdown grid starting with `| Phase | Load when needed |`
    and ending at the first blank line after the last data row. Anything
    OUTSIDE this block (the always-load numbered list above it, the
    "Do NOT load these legacy files" annotation immediately below it, the
    rest of SKILL.md) is intentionally NOT in scope for the dead-file check
    — those surfaces are allowed to reference dead files by name (the
    annotation under the table NAMES every dead file to explain why it was
    pulled).
    """
    header = "| Phase | Load when needed |"
    start = skill_md.find(header)
    assert start != -1, "SKILL.md is missing the `| Phase | Load when needed |` table"
    # Walk forward, accumulating lines until we hit the first blank line that
    # is not part of the table.
    lines = skill_md[start:].splitlines()
    block_lines: list[str] = []
    for line in lines:
        if not line.strip() and block_lines:
            # End of the table block.
            break
        block_lines.append(line)
    block = "\n".join(block_lines)
    # Sanity: the table must contain at least the separator row.
    assert "| --- |" in block, (
        "extracted table block is missing the markdown header separator row — "
        "the extractor probably picked up the wrong region"
    )
    return block


def test_dead_files_absent_from_skill_load_table():
    """None of the five Lane A dead files appears in the phase-load table."""
    skill_md = _read("skills/audit/SKILL.md")
    table = _load_table_block(skill_md)
    leaked = [dead for dead in DEAD_FILES if dead in table]
    assert not leaked, (
        "SKILL.md `Runtime Load Order` table still references dead/frozen "
        f"file(s): {leaked}. Each of these carries a dead/frozen header and "
        "must not appear in the table that the audit lead loads at phase "
        "entry. (The 'Do NOT load these legacy files' annotation below the "
        "table is allowed to name them — that is what flags them as dead.)"
    )


# Pairs of (file, regex). Each dead file's header annotation must match the
# regex within the first ~50 lines of the file. We pin to a regex (not a
# literal) so the prose can evolve without retargeting the test, while still
# requiring the LOAD-BEARING phrase that flags it dead/frozen.
DEAD_HEADER_REGEXES = {
    "workflows/audit.md": re.compile(
        r"(?i)DEAD\s+for\s+the\s+audit\s+path",
    ),
    "contracts/synthesizer-subagent.md": re.compile(
        r"(?i)DEAD\s+for\s+the\s+audit\s+path|superseded\s+by\s+`contracts/synthesizer-v2\.md`",
    ),
    "contracts/audit-assembly.md": re.compile(
        r"(?i)LEGACY-RENDER\s+REFERENCE|not\s+loaded\s+by\s+`skills/audit/SKILL\.md`\s+for\s+v2",
    ),
    "contracts/progress-comparison.md": re.compile(
        r"(?i)FROZEN\s+per\s+`product\.md`\s+§5|frozen\s+per\s+product\.md\s+§5",
    ),
    "contracts/team-lifecycle.md": re.compile(
        r"(?i)DEAD\s+for\s+the\s+audit\s+path",
    ),
}


@pytest.mark.parametrize("dead_path,header_re", list(DEAD_HEADER_REGEXES.items()))
def test_dead_file_carries_header_annotation(dead_path, header_re):
    """Each dead file's body carries a header annotation flagging it dead/frozen.

    The annotation must appear within the first 50 lines so a reader who
    follows a stale pointer from somewhere else sees the warning before
    they start reading the v1-era body.
    """
    body = _read(dead_path)
    head = "\n".join(body.splitlines()[:50])
    assert header_re.search(head), (
        f"{dead_path}: missing a dead/frozen header annotation in the first 50 "
        f"lines. Expected something matching {header_re.pattern!r} so a reader "
        f"following a stale pointer sees the warning before reading the body."
    )


def test_skill_md_has_no_live_voiced_team_instructions_for_audit():
    """G21-style guard: SKILL.md does not instruct the audit lead to do v1
    Agent-Teams ceremony.

    The v2 audit lead does not call `TeamCreate`, does not pass `team_name=`
    to dispatched agents, does not run a `SendMessage` peer huddle, and does
    not broadcast `SendMessage to "*"`. These are all v1 mechanics. SKILL.md
    may still MENTION `team_name` in frozen-voice form — the v2 "Cluster
    specialists: one-shot subagent (`Agent` tool, no `team_name`)" callout
    is literally telling the lead NOT to pass it — but it must not carry the
    live v1 instructions.
    """
    skill_md = _read("skills/audit/SKILL.md")

    # No TeamCreate call instruction for the audit path.
    assert "TeamCreate" not in skill_md, (
        "SKILL.md must not instruct the v2 audit lead to call TeamCreate — "
        "cluster specialists are one-shot subagents (no team) since the "
        "2026-06-01 §10 migration."
    )

    # No SendMessage broadcasts. v2 specialists do not coordinate.
    assert 'SendMessage to "*"' not in skill_md, (
        "SKILL.md must not instruct a SendMessage broadcast — v2 specialists "
        'have "No coordination" per contracts/specialist-prompt-v2.md.'
    )
    # No `SendMessage to <name>` directed broadcasts either — those are the v1
    # huddle/handoff/retry mechanic. A descriptive mention in the "Do NOT load
    # these legacy files" annotation explaining WHY workflows/audit.md is dead
    # (e.g. "SendMessage huddles") is fine; a live `SendMessage to "..."`
    # instruction is not.
    assert "SendMessage to " not in skill_md, (
        "SKILL.md must not contain a live `SendMessage to ...` instruction — "
        "v2 specialists do not peer-message, and validation-failure recovery "
        "is a fresh Agent() re-dispatch with the error embedded via "
        "`scripts/test-specialist.py --write-retry-prompt`."
    )

    # `team_name=` would mean a live instruction to PASS a team_name on a
    # dispatch call. The frozen-voice "no `team_name`" callout uses backticks
    # without `=`, so this pattern catches live calls without flagging the
    # callout.
    assert "team_name=" not in skill_md, (
        "SKILL.md must not contain a live `team_name=` dispatch instruction. "
        "The v2 cluster-specialist dispatch is `Agent(subagent_type=..., "
        "no team_name)`; the frozen-voice 'no `team_name`' callout is fine, "
        "a literal `team_name=` call is not."
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
