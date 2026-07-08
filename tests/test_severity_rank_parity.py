"""Parity guard: the two hand-mirrored severity-rank maps must stay identical.

Regression for adversarial review 2026-07-08 #20. ``placement._COPLACE_SEVERITY_RANK``
carries a "Mirrors assembly.finding_stability.severity_rank" comment, but nothing
enforced the equality. The two maps are consumed independently — placement uses it
to keep the highest-severity box when hotspots co-place on one element;
finding_stability uses it for severity-distance in the determinism gate — so a
silent divergence would ship two different severity orderings with no test to
catch it. This guard pins them together (or forces promotion to one shared home).

Run:
    python -m pytest tests/test_severity_rank_parity.py
    python -m unittest tests.test_severity_rank_parity
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))


class SeverityRankParity(unittest.TestCase):
    def test_maps_are_identical(self):
        from report.placement import _COPLACE_SEVERITY_RANK
        from assembly.finding_stability import _SEVERITY_RANK
        self.assertEqual(
            dict(_COPLACE_SEVERITY_RANK), dict(_SEVERITY_RANK),
            "placement._COPLACE_SEVERITY_RANK and finding_stability._SEVERITY_RANK "
            "must stay identical (placement.py:233 claims it mirrors the other). "
            "Update BOTH together, or promote the map to one shared home.",
        )

    def test_severity_rank_helper_agrees_with_placement_map(self):
        from report.placement import _COPLACE_SEVERITY_RANK
        from assembly.finding_stability import severity_rank
        for sev, rank in _COPLACE_SEVERITY_RANK.items():
            self.assertEqual(severity_rank(sev), rank, f"rank mismatch for {sev!r}")
        # Both treat unknown/empty severity as 0 (placement uses .get(..., 0)).
        self.assertEqual(severity_rank("bogus"), 0)
        self.assertEqual(severity_rank(""), 0)


if __name__ == "__main__":
    unittest.main()
