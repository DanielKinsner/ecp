"""Guard: the report/editor runtime JS must define clampNumber exactly once.

Regression for adversarial review 2026-07-08 #9. Two clampNumber functions
coexisted in the runtime IIFE: a 3-arg one (non-finite -> min) and a later 4-arg
one (non-finite -> fallback). JS function declarations hoist and the LAST wins,
so every 3-arg caller (the effect-rect normalizers) silently got
fallback=undefined -> non-finite input returned undefined, corrupting effect
rects rendered from hand-editable review-state. The fix merges them into one
definition whose fallback defaults to `min` when omitted.

Run:
    python -m pytest tests/test_editor_js_clampnumber.py
    python -m unittest tests.test_editor_js_clampnumber
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.templates.js import get_report_js  # noqa: E402


def _render() -> str:
    return get_report_js("[]", "[]", "[]", '""', engagement_id="x", device="desktop")


class EditorJsClampNumber(unittest.TestCase):
    def test_single_clampnumber_definition(self):
        js = _render()
        self.assertEqual(
            js.count("function clampNumber("), 1,
            "clampNumber must be defined exactly once — a second same-name "
            "function declaration hoists over the first and changes non-finite "
            "semantics for every 3-arg caller (review 2026-07-08 #9).",
        )

    def test_fallback_defaults_to_min(self):
        js = _render()
        self.assertIn(
            "fallback === undefined ? min : fallback", js,
            "The merged clampNumber must default fallback to `min` so 3-arg "
            "callers keep the intended non-finite -> min behavior.",
        )

    @unittest.skipUnless(shutil.which("node"), "node required for JS syntax check")
    def test_rendered_js_is_syntactically_valid(self):
        js = _render()
        tmp = tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8")
        try:
            tmp.write(js)
            tmp.close()
            result = subprocess.run(
                ["node", "--check", tmp.name], capture_output=True, text=True,
            )
            self.assertEqual(
                result.returncode, 0,
                f"rendered editor JS failed node --check: {result.stderr}",
            )
        finally:
            os.unlink(tmp.name)


if __name__ == "__main__":
    unittest.main()
