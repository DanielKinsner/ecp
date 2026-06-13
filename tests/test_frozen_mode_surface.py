"""Frozen-mode non-invokability guard for the plugin surface."""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def test_frozen_mode_skill_dirs_are_not_present():
    forbidden = {"build", "compare", "quick-scan", "resume"}
    present = {p.name for p in (REPO / "skills").iterdir() if p.is_dir()}
    assert present.isdisjoint(forbidden)


def test_plugin_manifest_exposes_only_audit_command():
    manifest = json.loads((REPO / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    commands = sorted(set(re.findall(r"/ecp:[A-Za-z0-9_-]+", json.dumps(manifest))))
    assert commands == ["/ecp:audit"]
