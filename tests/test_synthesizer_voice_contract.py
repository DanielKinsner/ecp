"""Grep-guard for the synthesizer hypotheses-voice carve-out (product.md v1.2 §3.1).

`product.md` §3 frames ECP output as research-backed HYPOTHESES, not measured
outcomes ("does not promise lift"). `contracts/synthesizer-v2.md` instructs
specialists to rewrite hedges into the strongest defensible action verb (lines
~48 and ~367). Without an explicit carve-out, a future edit could read that as
a license to rewrite outcome language into measured-result promises ("will lift
conversion by N%"), silently violating §3.1.

This guard pins the clause that distinguishes ACTION-voice (stays strong: do X)
from OUTCOME-voice (stays hypothesis-framed: never promises measured results).
Textual / minimal — catches a regression where a sweep drops the carve-out.

Run:
    python -m pytest tests/test_synthesizer_voice_contract.py -q
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path


_REPO = Path(__file__).resolve().parent.parent
_CONTRACT = _REPO / "contracts" / "synthesizer-v2.md"


class TestSynthesizerHypothesesVoiceCarveOut(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(
            _CONTRACT.is_file(),
            "contracts/synthesizer-v2.md missing — the voice contract cannot be guarded.",
        )
        self.body = _CONTRACT.read_text(encoding="utf-8")

    def test_action_vs_outcome_carve_out_clause_present(self):
        """The carve-out clause distinguishes action-voice (strong) from
        outcome-voice (hypothesis-framed). The exact phrase 'Action-voice vs
        outcome-voice' is the load-bearing heading; a sweep that drops it
        regresses the §3.1 hypotheses-voice contract."""
        self.assertIn(
            "Action-voice vs outcome-voice",
            self.body,
            "synthesizer-v2.md must carry the 'Action-voice vs outcome-voice' "
            "carve-out clause that pins hypotheses-voice for OUTCOME claims "
            "(product.md §3.1).",
        )

    def test_carve_out_anchors_to_hypotheses_framing(self):
        """The clause must tie outcome language to the hypotheses framing —
        not just say 'be careful'. We check for both the 'hypotheses' anchor
        and an explicit negative on the measured-lift pattern."""
        # Positive: hypotheses anchor + an explicit prohibition pattern.
        self.assertRegex(
            self.body,
            r"hypothes[ei]s",
            "carve-out must anchor outcome language to the §3 hypotheses framing.",
        )
        # Negative pattern the clause must explicitly forbid in prose. We assert
        # the clause itself names this anti-pattern (so reviewers see the line).
        self.assertTrue(
            re.search(r"will lift|will increase|measured lift", self.body, flags=re.IGNORECASE),
            "carve-out must name the forbidden measured-lift / will-lift pattern so "
            "the prohibition is concrete, not abstract.",
        )

    def test_strong_verb_rule_still_present(self):
        """Sanity: the carve-out does not delete the strong-verb rule it
        carves out from. Both must coexist — action verbs stay strong, only
        outcome language is hypothesis-framed."""
        self.assertIn("strongest defensible verb", self.body)


if __name__ == "__main__":
    unittest.main()
