"""Guard: the report CSS must contain only well-formed hex color tokens.

Regression for the repo-wide-review D7 finding (2026-06-18): the
``--severity-critical`` custom property was set to ``#9300a`` — a 5-digit
hex, which is invalid as a CSS color. A custom property accepts it at parse
time, but every ``color: var(--severity-critical)`` / ``border-color:
var(--severity-critical)`` then becomes invalid at computed-value time and
falls back to the inherited/unset color (the ``var(..., #fallback)`` default
is NOT used for a set-but-invalid value). Result: CRITICAL severity text and
borders silently lost their red-black styling across the client-facing report.

A valid CSS hex color has 3, 4, 6, or 8 digits. This test pins that every hex
token emitted by ``get_report_css`` is one of those lengths, so a malformed
token like ``#9300a`` can never ship again.

Run:
    python -m pytest tests/test_css_severity_color_tokens.py
    python -m unittest tests.test_css_severity_color_tokens
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts"))

from scripts.report.templates.css import get_report_css  # noqa: E402

_VALID_HEX_LENGTHS = {3, 4, 6, 8}
_HEX_TOKEN = re.compile(r"#([0-9a-fA-F]+)\b")


class CssHexTokensWellFormed(unittest.TestCase):
    def test_every_hex_color_token_has_a_valid_length(self):
        css = get_report_css("")
        bad = []
        for m in _HEX_TOKEN.finditer(css):
            digits = m.group(1)
            if len(digits) not in _VALID_HEX_LENGTHS:
                # column context for a readable failure message
                start = max(0, m.start() - 30)
                bad.append((m.group(0), css[start:m.end() + 10].replace("\n", " ")))
        self.assertEqual(
            bad, [],
            "Malformed hex color token(s) in report CSS "
            "(valid lengths are 3/4/6/8 digits): "
            + "; ".join(f"{tok!r} near …{ctx}…" for tok, ctx in bad),
        )

    def test_critical_severity_color_is_present_and_valid(self):
        # The specific token the finding was about. Pin its corrected value so a
        # future edit can't silently regress it to another invalid length.
        css = get_report_css("")
        self.assertIn("--severity-critical: #93000a;", css)


if __name__ == "__main__":
    unittest.main()
