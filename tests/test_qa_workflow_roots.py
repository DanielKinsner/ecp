"""Guards for portable QA workflow root defaults."""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MACHINE_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/]+Users[\\/]+|/Users/)")


def test_visual_qa_workflow_has_no_machine_root_literal():
    text = (REPO / ".claude" / "workflows" / "ecp-visual-qa.js").read_text(encoding="utf-8")
    assert not MACHINE_PATH_RE.search(text)
