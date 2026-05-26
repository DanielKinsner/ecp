"""v2 unit tests: dedup.deduplicate_v2 SCOPE-aware merging.

Run:
    python -m unittest tests.test_v2_dedup

Phase E.3 deliverable. Verifies:
- page-scope findings dedup across device pairs
- device-scope findings dedup within their own device only
- cross-cluster same-baton_index keep-both unless (surface, verdict) match
- byte-identical determinism: run twice, output equal
"""
from __future__ import annotations

import json
import sys
import unittest
from dataclasses import asdict
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.dedup import deduplicate_v2  # noqa: E402
from assembly.models import Finding  # noqa: E402


def _f(**overrides) -> Finding:
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
        reference="r",
        title="T",
        tier="Silver",
        baton_index="e7",
        surface="price-block",
        scope="device",
    )
    base.update(overrides)
    return Finding(**base)


def _findings_to_dict(findings):
    return [asdict(f) for f in findings]


class TestPageScopeDedup(unittest.TestCase):
    def test_same_baton_verdict_across_devices_collapses(self):
        f_d = _f(scope="page", device="desktop", local_index=1, baton_index="e7", tier="Silver")
        f_m = _f(scope="page", device="mobile", local_index=1, baton_index="e7", tier="Gold")
        result = deduplicate_v2([f_d, f_m])
        self.assertEqual(len(result.kept), 1)
        # Higher tier wins
        self.assertEqual(result.kept[0].tier, "Gold")

    def test_different_verdict_does_not_merge(self):
        f1 = _f(scope="page", device="desktop", verdict="FAIL", baton_index="e7")
        f2 = _f(scope="page", device="mobile", verdict="PARTIAL", baton_index="e7")
        result = deduplicate_v2([f1, f2])
        self.assertEqual(len(result.kept), 2)


class TestDeviceScopeDedup(unittest.TestCase):
    def test_same_device_baton_verdict_collapses(self):
        f1 = _f(scope="device", device="mobile", local_index=1, baton_index="e7", tier="Bronze")
        f2 = _f(scope="device", device="mobile", local_index=2, baton_index="e7", tier="Silver")
        result = deduplicate_v2([f1, f2])
        self.assertEqual(len(result.kept), 1)
        self.assertEqual(result.kept[0].tier, "Silver")

    def test_different_devices_do_not_merge(self):
        f_d = _f(scope="device", device="desktop", baton_index="e7")
        f_m = _f(scope="device", device="mobile", baton_index="e7")
        result = deduplicate_v2([f_d, f_m])
        self.assertEqual(len(result.kept), 2)


class TestCrossClusterDedup(unittest.TestCase):
    def test_same_baton_different_cluster_different_surface_keeps_both(self):
        # visual-cta and pricing both flag e7, but different surfaces
        f1 = _f(cluster="visual-cta", baton_index="e7", surface="cta-contrast")
        f2 = _f(cluster="pricing", baton_index="e7", surface="price-block")
        result = deduplicate_v2([f1, f2])
        self.assertEqual(len(result.kept), 2)

    def test_same_baton_same_surface_same_verdict_merges(self):
        # Two specialists both flag e7 at price-block with FAIL verdict — structural identity
        f1 = _f(cluster="visual-cta", baton_index="e7", surface="price-block",
                verdict="FAIL", tier="Bronze", local_index=1)
        f2 = _f(cluster="pricing", baton_index="e7", surface="price-block",
                verdict="FAIL", tier="Gold", local_index=1)
        result = deduplicate_v2([f1, f2])
        self.assertEqual(len(result.kept), 1)
        self.assertEqual(result.kept[0].tier, "Gold")
        # The merged record references both source findings
        self.assertEqual(len(result.auto_merged), 1)


class TestEthicsRouting(unittest.TestCase):
    def test_block_ethics_finding_routes_separately(self):
        f1 = _f(cluster="pricing", verdict="FAIL")
        e1 = _f(cluster="ethics", device="page", ethics_state="BLOCK",
                priority="CRITICAL", priority_rank=0)
        result = deduplicate_v2([f1, e1])
        self.assertEqual(len(result.kept), 1)
        self.assertEqual(result.kept[0].cluster, "pricing")
        self.assertEqual(len(result.ethics_findings), 1)
        self.assertEqual(result.ethics_findings[0].ethics_state, "BLOCK")

    def test_clear_ethics_stays_in_active_pool(self):
        # CLEAR ethics findings record telemetry but are not "ethics gate" entries
        e_clear = _f(cluster="ethics", device="page", ethics_state="CLEAR",
                     verdict="PASS", priority="LOW", priority_rank=3)
        result = deduplicate_v2([e_clear])
        self.assertEqual(len(result.kept), 1)
        self.assertEqual(len(result.ethics_findings), 0)


class TestDeterminism(unittest.TestCase):
    def test_run_twice_produces_byte_identical_kept_list(self):
        # Build a varied set of findings and verify dedup_v2 output is stable
        inputs = [
            _f(cluster="pricing", local_index=1, baton_index="e7", tier="Gold", scope="page"),
            _f(cluster="visual-cta", local_index=1, baton_index="e3", tier="Silver", scope="device"),
            _f(cluster="pricing", local_index=2, baton_index="e7", tier="Silver", scope="page",
               device="desktop"),
            _f(cluster="trust-credibility", local_index=1, baton_index="e3",
               surface="reviews", tier="Bronze", scope="device"),
            _f(cluster="ethics", device="page", ethics_state="BLOCK", local_index=1,
               priority="CRITICAL", priority_rank=0, scope="page"),
        ]
        r1 = deduplicate_v2(list(inputs))
        r2 = deduplicate_v2(list(inputs))
        # Convert to dict for byte-comparable serialization (frozen dataclasses)
        s1 = json.dumps(_findings_to_dict(r1.kept), sort_keys=True, default=str)
        s2 = json.dumps(_findings_to_dict(r2.kept), sort_keys=True, default=str)
        self.assertEqual(s1, s2)
        s_eth1 = json.dumps(_findings_to_dict(r1.ethics_findings), sort_keys=True, default=str)
        s_eth2 = json.dumps(_findings_to_dict(r2.ethics_findings), sort_keys=True, default=str)
        self.assertEqual(s_eth1, s_eth2)


if __name__ == "__main__":
    unittest.main()
