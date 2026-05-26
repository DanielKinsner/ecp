"""v2 unit tests: Finding frozen + replace, EvidenceAnchor sort_key, tier rank.

Run:
    python -m unittest tests.test_v2_models

Phase E.2a deliverable. Verifies the frozen-dataclass invariant and the
deterministic-iteration helpers.
"""
from __future__ import annotations

import sys
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.models import (  # noqa: E402
    EVIDENCE_TIER_BY_RANK,
    EVIDENCE_TIER_RANK,
    EvidenceAnchor,
    Finding,
    PRIORITY_ORDER,
)


def _make_finding(**overrides) -> Finding:
    base = dict(
        cluster="pricing",
        device="mobile",
        local_index=1,
        verdict="FAIL",
        section="price-block",
        element="$69.95",
        element_normalized="$69.95",
        source="VISUAL",
        priority="HIGH",
        priority_rank=1,
        observation="x" * 25,
        recommendation="y" * 25,
        reference="price-anchoring.md",
    )
    base.update(overrides)
    return Finding(**base)


class TestFindingFrozen(unittest.TestCase):
    def test_finding_is_frozen(self):
        f = _make_finding()
        with self.assertRaises(FrozenInstanceError):
            f.cluster = "visual-cta"

    def test_replace_returns_new_instance_unchanged_original(self):
        f = _make_finding()
        f2 = replace(f, display_index=5)
        self.assertEqual(f.display_index, 0)
        self.assertEqual(f2.display_index, 5)
        # Identity check: distinct instances
        self.assertIsNot(f, f2)

    def test_v2_fields_default_empty(self):
        f = _make_finding()
        self.assertEqual(f.scope, "device")
        self.assertEqual(f.change_type, "")
        self.assertEqual(f.change_scope, "")
        self.assertEqual(f.evidence_anchors, ())
        self.assertIsNone(f.confidence)
        self.assertEqual(f.baton_index, "")
        self.assertEqual(f.surface, "")

    def test_merged_from_is_tuple(self):
        f = _make_finding()
        # Tuples are hashable and immutable — frozen-safe
        self.assertIsInstance(f.merged_from, tuple)
        f2 = replace(f, merged_from=("pricing F-02", "visual-cta F-03"))
        self.assertEqual(len(f2.merged_from), 2)


class TestEvidenceAnchor(unittest.TestCase):
    def test_anchor_is_frozen(self):
        a = EvidenceAnchor(type="visual", reference="section-1.jpg")
        with self.assertRaises(FrozenInstanceError):
            a.type = "dom"

    def test_sort_key_total_ordering(self):
        a1 = EvidenceAnchor(type="dom", reference="e10")
        a2 = EvidenceAnchor(type="visual", reference="section-2.jpg", scroll_y=480)
        a3 = EvidenceAnchor(type="visual", reference="section-2.jpg", scroll_y=900)
        sorted_anchors = sorted([a3, a1, a2], key=lambda x: x.sort_key())
        # 'dom' < 'visual'; among visuals, scroll_y=480 < 900
        self.assertEqual(sorted_anchors[0].type, "dom")
        self.assertEqual(sorted_anchors[1].scroll_y, 480)
        self.assertEqual(sorted_anchors[2].scroll_y, 900)

    def test_anchor_with_none_scroll_y_sorts_first(self):
        a_with = EvidenceAnchor(type="dom", reference="e1", scroll_y=100)
        a_without = EvidenceAnchor(type="dom", reference="e1")
        sorted_pair = sorted([a_with, a_without], key=lambda x: x.sort_key())
        # None encoded as -1; sorts before 100
        self.assertIsNone(sorted_pair[0].scroll_y)


class TestTierRank(unittest.TestCase):
    def test_tier_rank_ordering(self):
        self.assertEqual(EVIDENCE_TIER_RANK["Bronze"], 1)
        self.assertEqual(EVIDENCE_TIER_RANK["Silver"], 2)
        self.assertEqual(EVIDENCE_TIER_RANK["Gold"], 3)

    def test_tier_by_rank_is_inverse(self):
        for tier, rank in EVIDENCE_TIER_RANK.items():
            self.assertEqual(EVIDENCE_TIER_BY_RANK[rank], tier)


class TestPriorityOrder(unittest.TestCase):
    def test_priority_ordering(self):
        # CRITICAL=0 first (lowest rank = highest priority)
        self.assertLess(PRIORITY_ORDER["CRITICAL"], PRIORITY_ORDER["HIGH"])
        self.assertLess(PRIORITY_ORDER["HIGH"], PRIORITY_ORDER["MEDIUM"])
        self.assertLess(PRIORITY_ORDER["MEDIUM"], PRIORITY_ORDER["LOW"])


if __name__ == "__main__":
    unittest.main()
