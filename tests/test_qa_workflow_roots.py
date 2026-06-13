"""Guards for portable QA workflow root defaults."""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MACHINE_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/]+Users[\\/]+|/Users/)")


def test_visual_qa_workflow_has_no_machine_root_literal():
    text = (REPO / ".claude" / "workflows" / "ecp-visual-qa.js").read_text(encoding="utf-8")
    assert not MACHINE_PATH_RE.search(text)


def test_visual_qa_workflow_uses_no_node_api():
    """The Workflow tool runs scripts in a sandbox with NO Node API —
    `process` is not defined there, so any `process.` reference kills the
    script with a ReferenceError before it spawns a single agent
    (observed live 2026-06-12 on the canonical no-root invocation)."""
    text = (REPO / ".claude" / "workflows" / "ecp-visual-qa.js").read_text(encoding="utf-8")
    assert not re.search(r"\bprocess\s*\.", text)


def test_report_qa_workflow_has_no_machine_root_literal():
    text = (REPO / ".claude" / "workflows" / "ecp-report-qa.js").read_text(encoding="utf-8")
    assert not MACHINE_PATH_RE.search(text)
