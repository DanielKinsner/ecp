"""Grep guards for the LANE C contract-reword sweep (v1.2).

LANE C covers the four live-path contracts the audit lead loads at runtime and
that must therefore stay internally v2-true:

  - contracts/lead-discipline.md        (consent chain, scope selection)
  - contracts/dispatch-contract.md      (v1 cluster-auditor teammate template)
  - contracts/audit-reconciliation.md   (cluster file path references)
  - contracts/priority-path-synthesis.md (live ERROR-block rule + assemble-audit.py framing)

Each guard targets the SPECIFIC drift class the v1.2 sweep is closing — not
a broad "lint" pass — so a future edit that re-introduces the live-voiced v1
language fails here at the contract layer instead of slipping through to a
live ``/ecp:audit`` invocation.

These tests sit alongside `test_specialist_subagent_dispatch.py` (which pins
the v2-default dispatch shape) and `test_v2_pipeline_doc.py` (which pins the
SKILL.md command flow). This file is the contract-content half of the
overall v1.2 conformance fence.

Run:
    python -m pytest tests/test_contract_sweep_live_path.py -q
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent


def _read(path: str) -> str:
    return (_REPO / path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Verdict 1 — contracts/lead-discipline.md: no live audit -> plan -> review -> build chain
# ---------------------------------------------------------------------------
def test_lead_discipline_drops_live_voiced_audit_plan_review_build_chain():
    """The live consent line for `/ecp:audit` may not describe a multi-phase
    plan -> review -> build pipeline.

    product.md §2.4 freezes plan / review / build as the build family; the
    canonical audit STOPS at findings + Priority Path + visual report. Any
    live-voiced text instructing the lead to run that downstream chain is a
    spec-conformance bug.
    """
    content = _read("contracts/lead-discipline.md")

    # The literal "/ecp:audit -> ... -> plan -> ... -> review -> ... -> build" arrow chain
    # is the exact stale form we removed. Catch both arrow glyphs (-> / →).
    forbidden_chain = re.compile(
        r"/ecp:audit\s*(?:->|→).*?plan.*?(?:->|→).*?review.*?(?:->|→).*?build",
        re.IGNORECASE | re.DOTALL,
    )
    match = forbidden_chain.search(content)
    assert match is None, (
        "contracts/lead-discipline.md re-introduced a live /ecp:audit -> plan "
        "-> review -> build consent chain at offset "
        f"{match.start() if match else -1}. product.md §2.4 says the audit "
        "STOPS after findings / Priority Path / visual report; plan / review / "
        "build are frozen (product.md §5). Any forward-pipeline text for "
        "/ecp:audit must be frozen-voice."
    )

    # The audit STOP boundary (product.md §2.4) must be acknowledged somewhere.
    # We do not pin exact wording, just that the file names the deliverable
    # boundary instead of pretending the audit hands off to plan.
    assert "§2.4" in content or "deliverable boundary" in content or "stops" in content.lower(), (
        "contracts/lead-discipline.md must name the product.md §2.4 deliverable "
        "boundary (audit STOPS at findings/PP/visual report)."
    )

    # The audit checkpoint is the live decision point — not plan/review checkpoints.
    # Loose check: the words 'plan' and 'review' may still appear in frozen-mode
    # bullets, but they must not appear as live checkpoints between phases.
    assert "checkpoint" in content.lower(), (
        "contracts/lead-discipline.md must mention the audit checkpoint."
    )


def test_lead_discipline_scope_menu_uses_v1_2_taxonomy():
    """The audit-scope pre-flight prompt must offer the v1.2 menu (standard /
    everything / custom), not the retired focused / standard / comprehensive
    / custom four-tier menu.

    product.md §2.3 (ruling A3) retired the 3–4-cluster default and named the
    former 'comprehensive' set 'standard'. The pre-flight scope prompt must
    reflect that.
    """
    content = _read("contracts/lead-discipline.md")
    # The retired four-tier offering must not appear verbatim.
    assert "focused / standard / comprehensive / custom" not in content, (
        "contracts/lead-discipline.md still offers the retired four-tier "
        "scope menu. v1.2 menu is 'standard / everything / custom'."
    )


# ---------------------------------------------------------------------------
# Verdict 2 — contracts/dispatch-contract.md: no MANDATORY-broadcast teammate template
# ---------------------------------------------------------------------------
def test_dispatch_contract_drops_v1_mandatory_broadcast_teammate_template():
    """The v1 cluster-auditor teammate prompt template — including the
    MANDATORY Step 1b intent huddle and the MANDATORY handoff broadcast —
    was removed in v1.2.

    v2 specialists dispatch as one-shot subagents per `specialist-prompt-v2.md`
    and explicitly DO NOT coordinate via SendMessage. The v1 template's
    huddle/handoff machinery contradicts the v2 'No coordination' rule and
    is a load-bearing prune target.
    """
    content = _read("contracts/dispatch-contract.md")

    # The verbatim teammate-template strings are gone.
    forbidden_strings = [
        # Team-context block from the v1 template body
        "name: `auditor-{cluster}-{device}`",
        "Lead: `team-lead`",
        # The two MANDATORY broadcasts
        "Intent huddle at Step 1b (BEFORE auditing)",
        "Handoff broadcast after writing your cluster file",
        # The per-finding overlap SendMessage helper
        "Per-finding overlap flag (optional, use when cross-cluster overlap is detected mid-audit)",
        # The completion checklist that closes the template
        "Fire the handoff broadcast to the team (above)",
        # The TaskUpdate claim line
        "TaskUpdate with owner=your name, status=in_progress",
    ]
    for needle in forbidden_strings:
        assert needle not in content, (
            f"contracts/dispatch-contract.md re-introduced the v1 teammate "
            f"template fragment: {needle!r}. v2 specialists do NOT coordinate; "
            f"see contracts/specialist-prompt-v2.md '## No coordination'."
        )

    # The v2 spec-prompt-v2.md pointer must replace it.
    assert "specialist-prompt-v2.md" in content, (
        "contracts/dispatch-contract.md must point at "
        "contracts/specialist-prompt-v2.md as the canonical v2 cluster-specialist "
        "prompt template."
    )

    # The v2 dispatch table row must still pin the no-team_name shape.
    # (Mirrors test_specialist_subagent_dispatch.test_specialist_dispatch_shape_is_subagent.)
    assert "| Cluster specialist (a.k.a. cluster auditor)" in content, (
        "The per-role table row for the cluster specialist must remain — "
        "test_specialist_subagent_dispatch pins it."
    )


# ---------------------------------------------------------------------------
# Verdict 3 — contracts/audit-reconciliation.md: live steps name the v2 JSON file
# ---------------------------------------------------------------------------
def test_audit_reconciliation_live_steps_reference_v2_json_artifact():
    """The reconciliation contract's live-path file references must include
    `cluster-{cluster}-{device}.json` (the v2 specialist emission name).

    The substantive v1 markdown rules (code-fenced FINDING blocks, TITLE
    uniqueness, etc.) are retained inside Step 0 / 0b / 0c as the v1 replay
    contract — those pins live in `test_specialist_subagent_dispatch.py`
    and we do NOT re-assert them here. This guard only catches the case
    where the file's live-voiced overview / reconciliation-process section
    forgets to name the v2 artifact at all.
    """
    content = _read("contracts/audit-reconciliation.md")

    # The v2 JSON filename pattern must appear somewhere in the live overview
    # or reconciliation-process sections — not just buried in a cross-reference.
    assert "cluster-{cluster}-{device}.json" in content, (
        "contracts/audit-reconciliation.md must reference the v2 emission "
        "file `cluster-{cluster}-{device}.json`. v2 (JSON) is the live "
        "/ecp:audit emission per specialist-prompt-v2.md; the contract "
        "cannot describe only the v1 markdown form as the live path."
    )

    # The Reconciliation-process section (the one that says
    # 'Only run AFTER format validation AND voice check ...') must list the
    # v2 JSON form when telling the lead what to read. We slice on the
    # section header and require the v2 name inside that slice.
    proc_marker = "## Reconciliation process per device"
    assert proc_marker in content, (
        "Reconciliation-process section header missing — file structure "
        "may have shifted."
    )
    proc_section = content[content.index(proc_marker):]
    # Cut at the next H2 so we only look at the process body.
    next_h2 = re.search(r"\n## ", proc_section[len(proc_marker):])
    if next_h2:
        proc_section = proc_section[: len(proc_marker) + next_h2.start()]
    assert "cluster-{cluster}-{device}.json" in proc_section, (
        "Reconciliation-process section must name "
        "`cluster-{cluster}-{device}.json` in its file-list step — the v2 "
        "live emission is the default to enumerate."
    )

    # And the v2 SKILL.md validation entry-point must be named somewhere.
    assert "test-specialist.py validate" in content, (
        "contracts/audit-reconciliation.md must name the v2 validation "
        "entry-point (`test-specialist.py validate`) so the lead knows the "
        "live JSON validation flow that supersedes the v1 markdown rules."
    )


# ---------------------------------------------------------------------------
# Verdict 4 — contracts/priority-path-synthesis.md: ERROR-block rule preserved at line 15;
# no live assemble-audit.py instruction
# ---------------------------------------------------------------------------
def test_priority_path_synthesis_keeps_visible_error_block_rule_at_line_15():
    """`scripts/report/html_builder.py:89` / `:124` and
    `scripts/report/templates/components.py:300` cite this contract at
    `contracts/priority-path-synthesis.md:15`. That line MUST keep stating
    the visible-ERROR-block rule for sidecar / synthesizer validation
    failures.
    """
    content = _read("contracts/priority-path-synthesis.md")
    lines = content.splitlines()
    assert len(lines) >= 15, (
        "contracts/priority-path-synthesis.md has fewer than 15 lines — "
        "the load-bearing line-15 ERROR-block rule was lost."
    )
    line_15 = lines[14]  # 1-indexed line 15
    # The rule says validation failures render a visible ERROR block.
    assert "visible ERROR block" in line_15, (
        f"contracts/priority-path-synthesis.md line 15 lost the visible "
        f"ERROR-block rule. Current line 15: {line_15!r}. scripts/report/"
        f"html_builder.py:89/:124 and scripts/report/templates/components.py:300 "
        f"cite this file:line by exact offset — renumbering breaks the "
        f"callers' attribution and the rule itself MUST stay on line 15."
    )


def test_priority_path_synthesis_has_no_live_assemble_audit_instruction():
    """The file frames `assemble-audit.py` as the v1 replay path, not as a
    live instruction for the v2 audit lead.

    `skills/audit/SKILL.md` and `test_v2_pipeline_doc.py` already pin that
    the live v2 pipeline does NOT run `assemble-audit.py`. This guard
    catches the converse drift inside this contract: a future edit that
    re-words the assemble-audit.py calls as live present-tense lead
    instructions ("dispatch the synthesizer, then run
    assemble-audit.py --priority-path ...") fails here.
    """
    content = _read("contracts/priority-path-synthesis.md")

    # Frozen-voice marker must be visible somewhere in the header.
    head = content[:2000]
    assert (
        "v1 replay" in head.lower()
        or "frozen" in head.lower()
        or "historical" in head.lower()
        or "supersedes" in head.lower()
    ), (
        "contracts/priority-path-synthesis.md must mark itself as the v1 "
        "replay / frozen / historical contract in its header. The live v2 "
        "synthesis path lives in contracts/synthesizer-v2.md per "
        "product.md §5 / §7."
    )

    # The v2 supersession pointer must be present.
    assert "synthesizer-v2.md" in content, (
        "contracts/priority-path-synthesis.md must point at "
        "contracts/synthesizer-v2.md as the v2 live supersession."
    )

    # No live-voiced "the lead dispatches ... then runs assemble-audit.py"
    # sequencing as the present-tense instruction. The historical form uses
    # past-tense ('ran' / 'dispatched' / 'wrote'); a re-introduced present
    # tense form is the drift we are guarding against.
    forbidden_live_phrases = [
        # The exact stale present-tense sequencing the v1.0 contract used.
        "the lead dispatches the synthesizer subagent per",
        "and re-runs `assemble-audit.py --priority-path PATH`",
    ]
    for needle in forbidden_live_phrases:
        assert needle not in content, (
            f"contracts/priority-path-synthesis.md re-introduced live-voiced "
            f"v1 instruction: {needle!r}. The v1 orchestration steps must "
            f"read as historical (past-tense / frozen-voice); the only live "
            f"piece is the visible-ERROR-block rule guarded above."
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
