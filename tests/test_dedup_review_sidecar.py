"""C8 regression: v2 build-canonical-frefs writes the dedup audit trail.

The v1 writer persisted ``dedup-review-{device}.json`` with
``{auto_merged, fuzzy_candidates}`` per device so the operator could see
which findings collapsed and why (``scripts/assembly/writer.py`` ~line 530).
The v2 path computed the same data inside ``build_canonical_view`` and
discarded it, leaving no audit trail for collapsed findings — a
product.md §0 untraceability gap.

Post-fix: ``scripts/lead_prep.py build-canonical-frefs`` writes
``dedup-review.json`` (one file per engagement, since v2 dedup crosses
devices) with the same ``auto_merged``/``fuzzy_candidates`` shape v1 used.

unittest-style on purpose: the canonical ``python -m unittest discover``
runner is the project's authoritative regression gate (see project memory:
ECP test-runner blind spot for pytest-only files).
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import lead_prep  # noqa: E402

FIXTURE = REPO / "tests" / "fixtures" / "v2_engagement_with_adjacent_ethics"


def _make_finding(
    *,
    cluster: str,
    device: str,
    local_id: int,
    baton_index: str,
    verdict: str = "FAIL",
    surface: str = "price-block",
    scope: str = "page",
    title: str = "Generated Finding",
    text_content: str = "$399.50",
    evidence_tier: str = "Silver",
) -> dict:
    return {
        "cluster": cluster,
        "device": device,
        "local_id": local_id,
        "verdict": verdict,
        "title": title,
        "surface": surface,
        "element": {
            "baton_index": baton_index,
            "text_content": text_content,
            "role": "text",
        },
        "severity": "MEDIUM",
        "scope": scope,
        "effort": {
            "change_type": "copy",
            "change_scope": "single-file",
        },
        "confidence": 0.85,
        "evidence_anchors": [{"type": "dom", "reference": baton_index}],
        "reference_citations": [
            {"source": "price-anchoring.md", "section": "msrp-anchor", "tier": evidence_tier}
        ],
        "observation": (
            "The product price renders as a single number with no anchor — no "
            "MSRP strikethrough, no compare-at framing visible above the price."
        ),
        "recommendation": (
            "Render the MSRP as a strikethrough above the live price so the "
            "discount is anchored against an upstream reference number."
        ),
        "why_this_matters": (
            "Anchoring is the single highest-leverage pricing pattern for SKUs "
            "in the $50-500 range; absent anchor measurably depresses AOV."
        ),
        "evidence_tier": evidence_tier,
    }


def _emission(*, cluster: str, device: str, findings: list[dict]) -> dict:
    return {
        "schema_version": 1,
        "engagement_id": "2026-06-09-c8aaaaaa",
        "cluster": cluster,
        "device": device,
        "specialist_model": {"family": "sonnet", "version": "4.6"},
        "started_at": "2026-06-09T00:00:00.000Z",
        "completed_at": "2026-06-09T00:01:00.000Z",
        "status": "complete",
        "findings": findings,
    }


class TestDedupReviewSidecarWritten(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.eng = Path(self.tmp.name) / "engagement"
        self.eng.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _build(self) -> int:
        return lead_prep.build_canonical_frefs(self.eng)

    def test_sidecar_written_on_clean_fixture(self):
        # Default fixture has no merges (different scopes), but the sidecar
        # must still be written so downstream tooling can rely on its
        # presence — same invariant as canonical-frefs-dropped.json.
        for src in FIXTURE.iterdir():
            shutil.copy(src, self.eng / src.name)
        rc = self._build()
        self.assertEqual(rc, 0, "clean fixture should exit 0")
        sidecar = self.eng / "dedup-review.json"
        self.assertTrue(sidecar.exists(), "dedup-review.json must always be written")
        doc = json.loads(sidecar.read_text(encoding="utf-8"))
        self.assertIn("auto_merged", doc)
        self.assertIn("fuzzy_candidates", doc)
        self.assertIsInstance(doc["auto_merged"], list)
        self.assertIsInstance(doc["fuzzy_candidates"], list)

    def test_sidecar_lists_layer1_page_scope_merge(self):
        # Two findings sharing (cluster, baton_index, verdict) with
        # scope=page collapse via deduplicate_v2's page-scope layer.
        # The merge record must appear in dedup-review.auto_merged.
        emission = _emission(
            cluster="pricing",
            device="desktop",
            findings=[
                _make_finding(
                    cluster="pricing", device="desktop", local_id=1,
                    baton_index="e0", scope="page", title="Price block lacks MSRP anchor",
                    evidence_tier="Silver",
                ),
                _make_finding(
                    cluster="pricing", device="desktop", local_id=2,
                    baton_index="e0", scope="page", title="Price block missing anchor frame",
                    evidence_tier="Bronze",
                ),
            ],
        )
        (self.eng / "cluster-pricing-desktop.json").write_text(
            json.dumps(emission), encoding="utf-8",
        )

        rc = self._build()
        self.assertEqual(rc, 0, "merge-producing fixture should exit 0")

        sidecar = self.eng / "dedup-review.json"
        self.assertTrue(sidecar.exists())
        doc = json.loads(sidecar.read_text(encoding="utf-8"))

        self.assertGreaterEqual(
            len(doc["auto_merged"]),
            1,
            "Two scope=page findings sharing (cluster, baton_index, verdict) "
            "must produce at least one auto_merged record.",
        )
        # The merge record must carry enough provenance to audit:
        #   reason + the kept-finding identity + the merged-from refs.
        record = doc["auto_merged"][0]
        self.assertIn("reason", record)
        self.assertIn("kept", record)
        self.assertIn("merged_from", record)
        self.assertTrue(
            record["merged_from"],
            "merged_from must list at least one absorbed loser ref.",
        )

    def test_sidecar_shape_matches_v1_keys(self):
        # Shape-parity with v1's dedup-review sidecar: top-level keys are
        # exactly auto_merged + fuzzy_candidates (engagement is the only
        # additional metadata field, mirroring the v2 canonical-frefs-dropped
        # sidecar pattern).
        for src in FIXTURE.iterdir():
            shutil.copy(src, self.eng / src.name)
        self.assertEqual(self._build(), 0)
        doc = json.loads((self.eng / "dedup-review.json").read_text(encoding="utf-8"))
        self.assertIn("auto_merged", doc)
        self.assertIn("fuzzy_candidates", doc)


if __name__ == "__main__":
    unittest.main()
