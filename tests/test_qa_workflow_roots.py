"""Guards for portable QA workflow root defaults."""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MACHINE_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/]+Users[\\/]+|/Users/)")
# docs/ecp/ engagement-id convention: YYYY-MM-DD-<8 hex>
ENGAGEMENT_ID_RE = re.compile(r"\b20\d{2}-\d{2}-\d{2}-[0-9a-f]{8}\b")


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


def test_visual_qa_workflow_has_no_hardcoded_engagement_id():
    """LG7: visual-qa must not fall back to a stale specific engagement id.
    Engagement IDs are per-run and operator-supplied; the hardcoded
    2026-06-01-749a3c3d default silently ran the wrong (stale) engagement
    when args.engagement wasn't forwarded (observed live 2026-06-12)."""
    text = (REPO / ".claude" / "workflows" / "ecp-visual-qa.js").read_text(encoding="utf-8")
    assert not ENGAGEMENT_ID_RE.search(text), (
        "ecp-visual-qa.js must not hardcode an engagement id — require args.engagement"
    )


def test_report_qa_workflow_has_no_hardcoded_engagement_id():
    """Mirror guard for the sibling QA workflow (defaults to a tracked
    fixture, not a per-run engagement id) — pins it against future drift."""
    text = (REPO / ".claude" / "workflows" / "ecp-report-qa.js").read_text(encoding="utf-8")
    assert not ENGAGEMENT_ID_RE.search(text)


def test_report_qa_workflow_has_no_machine_root_literal():
    text = (REPO / ".claude" / "workflows" / "ecp-report-qa.js").read_text(encoding="utf-8")
    assert not MACHINE_PATH_RE.search(text)


def test_report_qa_workflow_uses_no_node_api():
    """Same sandbox constraint as the visual-QA guard above."""
    text = (REPO / ".claude" / "workflows" / "ecp-report-qa.js").read_text(encoding="utf-8")
    assert not re.search(r"\bprocess\s*\.", text)
