"""Pin the INTENDED cross-device title merge (repo-wide-review #5 investigation).

The repo-wide-review flagged cross_device_title_merge for collapsing same-cluster
findings on title-prefix alone (potential silent data loss). Investigation
(2026-06-18) concluded it is a *latent* mechanism risk, NOT an active bug:

  * The specialist title contract (specialist-prompt-v2.md:147) requires titles to
    name "the specific element or sub-issue (NOT the surface slug)", which keeps
    genuinely-distinct findings differentiated.
  * The ONLY within-cluster prefix collision in the real slingmods fixture is a
    CORRECT cross-device merge: content-seo "priceValidUntil Expires Tomorrow — …"
    appears on desktop and mobile, both scope=page, describing the same stale
    priceValidUntil issue — exactly what the prefix merge is meant to union.
  * Every proposed "fix" (require same baton_index/surface, or merge only across
    different devices) would BREAK a legitimate merge. The merge deliberately
    ignores device/baton_index so it can union cross-device pairs like this one.

So the algorithm is intentionally left unchanged. This test pins that intent: a
desktop+mobile page-scope pair sharing a title prefix merges into one canonical
finding with devices_present unioned — so a future "fix" can't silently break the
cross-device union the merge exists to provide.

Run:
    python -m pytest tests/test_cross_device_title_merge_intent.py
    python -m unittest tests.test_cross_device_title_merge_intent
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.pipeline import cross_device_title_merge  # noqa: E402


class CrossDeviceTitleMergeIntent(unittest.TestCase):
    def test_priceValidUntil_desktop_mobile_pair_unions(self):
        raw_by_ref = {
            "content-seo F-03": {
                "title": "priceValidUntil Expires Tomorrow — Rich Result Eligibility at Risk",
                "device": "mobile", "scope": "page", "devices_present": ["mobile"],
                "severity": "MEDIUM",
            },
            "content-seo F-05": {
                "title": "priceValidUntil Expires Tomorrow — Stale Within 24 Hours",
                "device": "desktop", "scope": "page", "devices_present": ["desktop"],
                "severity": "MEDIUM",
            },
        }
        by_canonical, aliases = cross_device_title_merge(raw_by_ref)

        # one canonical finding, lowest F-NN wins
        self.assertEqual(list(by_canonical), ["content-seo F-03"])
        self.assertEqual(aliases, {"content-seo F-05": "content-seo F-03"})
        # devices unioned -> the whole point of the cross-device merge
        self.assertEqual(by_canonical["content-seo F-03"]["devices_present"],
                         ["desktop", "mobile"])
        self.assertEqual(by_canonical["content-seo F-03"]["scope"], "page")

    def test_distinct_prefixes_are_kept_separate(self):
        # The contract-conformant case: issue-specific prefixes do NOT collide.
        raw_by_ref = {
            "pricing F-01": {"title": "No MSRP Anchor on $59.95 Price Block",
                             "device": "desktop", "scope": "device", "devices_present": ["desktop"]},
            "pricing F-02": {"title": "No Installment Messaging Near Add-to-Cart",
                             "device": "desktop", "scope": "device", "devices_present": ["desktop"]},
        }
        by_canonical, aliases = cross_device_title_merge(raw_by_ref)
        self.assertEqual(len(by_canonical), 2)
        self.assertEqual(aliases, {})


if __name__ == "__main__":
    unittest.main()
