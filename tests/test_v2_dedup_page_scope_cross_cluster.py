"""Guard: cross-cluster page-scope dupes merge regardless of device label.

Regression for the repo-wide-review D1 finding (2026-06-18). Page-scope findings
are device-agnostic, but Layer 1 (_v2_layer_page_scope) collapses them across
devices PER CLUSTER, so two cross-cluster page dupes can reach the cross-cluster
structural layer (Layer 3) with divergent winner-device labels (one "desktop",
one "mobile"). Layer 3 keyed on device, so those dupes got different keys and
both survived (dedup-too-narrow). The fix neutralizes device in the Layer-3 key
for page-scope findings only; device-scope findings still key on device.

Run:
    python -m pytest tests/test_v2_dedup_page_scope_cross_cluster.py
    python -m unittest tests.test_v2_dedup_page_scope_cross_cluster
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.dedup import _v2_layer_cross_cluster_structural  # noqa: E402
from assembly.models import Finding  # noqa: E402


def _f(**overrides) -> Finding:
    base = dict(
        cluster="visual-cta", device="desktop", local_index=1, verdict="FAIL",
        section="hero", element="button.atc", element_normalized="button.atc",
        source="DOM", priority="HIGH", priority_rank=1,
        observation="obs", recommendation="rec", reference="r1",
        title="t", tier="Silver", baton_index="e5", surface="hero", scope="page",
    )
    base.update(overrides)
    return Finding(**base)


class CrossClusterPageScopeDedup(unittest.TestCase):
    def test_page_scope_dupes_merge_across_divergent_devices(self):
        # Same (baton_index, surface, verdict), different cluster lenses, and the
        # Layer-1 winners landed on different devices.
        f1 = _f(cluster="visual-cta", device="desktop", scope="page", tier="Gold")
        f2 = _f(cluster="pricing", device="mobile", scope="page", tier="Silver")
        kept, merged = _v2_layer_cross_cluster_structural([f1, f2])
        self.assertEqual(len(kept), 1, "page-scope cross-cluster dupes must merge")
        self.assertEqual(len(merged), 1)
        self.assertEqual(kept[0].tier, "Gold", "highest tier wins")

    def test_device_scope_different_devices_still_kept_separate(self):
        # Control: device-scope findings on different devices must NOT merge.
        f1 = _f(cluster="visual-cta", device="desktop", scope="device")
        f2 = _f(cluster="pricing", device="mobile", scope="device")
        kept, _ = _v2_layer_cross_cluster_structural([f1, f2])
        self.assertEqual(len(kept), 2, "device must still discriminate device-scope findings")

    def test_device_scope_same_device_cross_cluster_still_merges(self):
        # Control: existing same-device cross-cluster structural merge is unchanged.
        f1 = _f(cluster="visual-cta", device="desktop", scope="device", tier="Gold")
        f2 = _f(cluster="pricing", device="desktop", scope="device", tier="Silver")
        kept, merged = _v2_layer_cross_cluster_structural([f1, f2])
        self.assertEqual(len(kept), 1)
        self.assertEqual(len(merged), 1)


if __name__ == "__main__":
    unittest.main()
