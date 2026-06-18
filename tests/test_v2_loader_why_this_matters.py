"""Guard: v2_loader._finding_dict must read the cluster-emission stakes field.

Regression for the repo-wide-review D2 finding (2026-06-18). Cluster-emission
findings name the stakes prose `why_this_matters` (schema/cluster-emission-v1.json),
and the active parser reads it (json_parser.py:404). But the whitelist
normalizer _finding_dict read `why_matters`, so it silently emptied the stakes
prose for every emission finding it loaded. Now it reads `why_this_matters`
with a `why_matters` fallback for any internal dict.

Run:
    python -m pytest tests/test_v2_loader_why_this_matters.py
    python -m unittest tests.test_v2_loader_why_this_matters
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts"))

from report.v2_loader import _finding_dict  # noqa: E402


class FindingDictReadsStakesField(unittest.TestCase):
    def test_reads_why_this_matters_from_emission(self):
        raw = {"title": "t", "why_this_matters": "every conversion costs more attention"}
        out = _finding_dict("pricing", "desktop", raw)
        self.assertEqual(out["why_matters"], "every conversion costs more attention")

    def test_falls_back_to_why_matters_for_internal_dict(self):
        raw = {"title": "t", "why_matters": "legacy internal prose"}
        out = _finding_dict("pricing", "desktop", raw)
        self.assertEqual(out["why_matters"], "legacy internal prose")

    def test_why_this_matters_wins_when_both_present(self):
        raw = {"why_this_matters": "canonical", "why_matters": "stale"}
        out = _finding_dict("pricing", "desktop", raw)
        self.assertEqual(out["why_matters"], "canonical")


if __name__ == "__main__":
    unittest.main()
