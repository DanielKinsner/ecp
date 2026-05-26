"""v2 unit tests: scoring.score_groups determinism + tiebreaker.

Run:
    python -m unittest tests.test_v2_scoring

Phase E.4 deliverable. Verifies sorted iteration yields byte-identical output
across runs and the suggested_title tiebreaker resolves equal scores.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.models import Finding  # noqa: E402
from assembly.scoring import score_groups  # noqa: E402


def _f(**overrides) -> Finding:
    base = dict(
        cluster="pricing",
        device="mobile",
        local_index=1,
        verdict="FAIL",
        section="price-block",
        element="x",
        element_normalized="x",
        source="VISUAL",
        priority="HIGH",
        priority_rank=1,
        observation="x" * 25,
        recommendation="y" * 25,
        reference="r",
        display_index=1,
    )
    base.update(overrides)
    return Finding(**base)


class TestScoringDeterminism(unittest.TestCase):
    def test_run_twice_same_output(self):
        f1 = _f(cluster="pricing", local_index=1)
        f2 = _f(cluster="visual-cta", local_index=1, priority="CRITICAL", priority_rank=0)
        f3 = _f(cluster="trust-credibility", local_index=1, ethics_state="BLOCK",
                priority="HIGH", priority_rank=1)
        groups = {
            "msrp-anchor": [f1],
            "cta-contrast": [f2],
        }
        c1 = score_groups(groups, [f1, f2, f3])
        c2 = score_groups(groups, [f1, f2, f3])
        self.assertEqual(json.dumps(c1, sort_keys=True), json.dumps(c2, sort_keys=True))

    def test_synthesis_groups_iteration_order_does_not_change_output(self):
        # Build two equivalent dicts in different insertion orders. Output should match.
        f1 = _f(cluster="pricing", local_index=1)
        f2 = _f(cluster="visual-cta", local_index=1)
        groups_a = {"msrp": [f1], "cta": [f2]}
        groups_b = {"cta": [f2], "msrp": [f1]}
        c_a = score_groups(groups_a, [f1, f2])
        c_b = score_groups(groups_b, [f1, f2])
        # Sorted iteration in scoring should produce identical output regardless of insertion order
        self.assertEqual(json.dumps(c_a, sort_keys=True), json.dumps(c_b, sort_keys=True))


class TestSuggestedTitleTiebreaker(unittest.TestCase):
    def test_equal_score_tiebreaks_on_title(self):
        # Two synthesis groups with the same score — should sort by title alphabetically
        f1 = _f(cluster="pricing", local_index=1)
        f2 = _f(cluster="visual-cta", local_index=1)
        groups = {
            "zebra-finding": [f1],
            "alpha-finding": [f2],
        }
        candidates = score_groups(groups, [f1, f2])
        # Both have score 5 (HIGH=5 + 3 cluster bonus); tiebreak on title
        # Alpha Finding < Zebra Finding alphabetically
        self.assertEqual(candidates[0]["suggested_title"], "Alpha Finding")
        self.assertEqual(candidates[1]["suggested_title"], "Zebra Finding")


class TestEthicsTiebreaker(unittest.TestCase):
    def test_ethics_finding_outranks_non_ethics_at_equal_score(self):
        f1 = _f(cluster="pricing", local_index=1, priority="CRITICAL", priority_rank=0)
        f2 = _f(cluster="ethics", device="page", local_index=1, ethics_state="BLOCK",
                priority="CRITICAL", priority_rank=0)
        # Both ungrouped CRITICAL; ethics has has_ethics=True, should rank higher
        candidates = score_groups({}, [f1, f2])
        self.assertEqual(candidates[0]["has_ethics"], True)


if __name__ == "__main__":
    unittest.main()
