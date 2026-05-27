"""G16 regression: the clusters_represented canary.

The canary catches engagements where canonical-f-refs.json doesn't
represent every CRO cluster the operator requested. That includes both:

- The Run 2026-05-27-52f53a53 failure mode: build_canonical_view's bare
  ``except: continue`` silently dropped trust-credibility + content-seo
  emissions, so their clusters never appear in canonical-f-refs at all.
- A weaker variant: canonical-frefs-dropped.json records ≥1 drop. Even
  if the surviving emissions on the OTHER device left ≥1 finding per
  cluster (so the missing-clusters check passes), the drop itself is
  trust-relevant and the operator must address it before phase advance.

unittest-style for ``python -m unittest discover`` runner compatibility.

Run:
    python -m unittest tests.test_g16_clusters_represented_canary
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.canary_checks import check_clusters_represented  # noqa: E402


def _meta(clusters: list[str]) -> dict:
    return {
        "id": "test-engagement",
        "page": {"url": "https://example.com", "type": "product"},
        "platform": "test",
        "source_mode": "url-dual",
        "devices_requested": ["desktop", "mobile"],
        "devices_scanned": ["desktop", "mobile"],
        "clusters_used": clusters,
        "scope": "comprehensive",
        "schema_version": 3,
        "type": "audit",
    }


def _canonical(refs: list[str]) -> dict:
    """Minimal canonical-f-refs.json shape sufficient for the canary."""
    return {
        "valid_refs": refs,
        "by_canonical_ref": {ref: {"cluster": ref.split(" F-")[0]} for ref in refs},
    }


class TestClustersRepresentedCanary(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.eng = Path(self.tmp.name) / "engagement"
        self.eng.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _write_meta(self, clusters: list[str]):
        (self.eng / "meta.json").write_text(
            json.dumps(_meta(clusters)), encoding="utf-8"
        )

    def _write_canonical(self, refs: list[str]):
        (self.eng / "canonical-f-refs.json").write_text(
            json.dumps(_canonical(refs)), encoding="utf-8"
        )

    def _write_drops(self, drops: list[dict]):
        (self.eng / "canonical-frefs-dropped.json").write_text(
            json.dumps({"dropped_count": len(drops), "dropped": drops}),
            encoding="utf-8",
        )

    # --- Pass cases ---

    def test_all_clusters_represented_no_drops_passes(self):
        self._write_meta(["pricing", "content-seo"])
        self._write_canonical(["pricing F-01", "content-seo F-01"])
        self._write_drops([])

        result = check_clusters_represented(self.eng)
        self.assertTrue(
            result["passed"],
            f"All clusters represented + no drops should PASS. "
            f"summary={result['summary']!r}",
        )
        self.assertEqual(result["detail"]["missing_clusters"], [])
        self.assertEqual(result["detail"]["dropped_count"], 0)

    def test_drops_file_absent_treated_as_zero_drops(self):
        """Legacy pre-G16 engagement fixtures don't have the drops file."""
        self._write_meta(["pricing"])
        self._write_canonical(["pricing F-01"])
        # No canonical-frefs-dropped.json written.

        result = check_clusters_represented(self.eng)
        self.assertTrue(result["passed"])
        self.assertEqual(result["detail"]["dropped_count"], 0)

    def test_ethics_in_clusters_used_is_excluded_from_expected(self):
        """Ethics is page-scope, not a CRO cluster — it doesn't count toward
        the expected set so its presence/absence here doesn't affect the
        canary verdict.
        """
        self._write_meta(["pricing", "ethics"])
        self._write_canonical(["pricing F-01"])
        # Note: no ethics ref in canonical, but ethics is excluded from
        # expected so this should still PASS.

        result = check_clusters_represented(self.eng)
        self.assertTrue(
            result["passed"],
            "Ethics must be excluded from the expected-cluster set so its "
            "absence from canonical doesn't false-positive the canary.",
        )
        self.assertNotIn("ethics", result["detail"]["expected_clusters"])

    # --- Fail cases ---

    def test_missing_cluster_fails_and_names_the_cluster(self):
        """The headline failure mode: Run C lost trust-credibility entirely."""
        self._write_meta(
            ["visual-cta", "trust-credibility", "pricing", "content-seo"]
        )
        # Only visual-cta and pricing represented; trust-credibility +
        # content-seo dropped silently pre-G16.
        self._write_canonical(["visual-cta F-01", "pricing F-22"])
        self._write_drops([])

        result = check_clusters_represented(self.eng)
        self.assertFalse(
            result["passed"],
            "Missing clusters must fail the canary.",
        )
        self.assertEqual(
            result["detail"]["missing_clusters"],
            ["content-seo", "trust-credibility"],
        )
        # The summary must name the specific clusters so the operator can
        # see what's missing without reading detail.
        self.assertIn("trust-credibility", result["summary"])
        self.assertIn("content-seo", result["summary"])

    def test_drops_recorded_fails_even_when_no_clusters_missing(self):
        """Weaker-but-still-real signal: a drop record exists even though
        every cluster has ≥1 surviving finding. Pre-G16, this engagement
        would have looked clean; post-G16 the drop itself blocks phase
        advance.
        """
        self._write_meta(["pricing", "content-seo"])
        self._write_canonical(["pricing F-01", "content-seo F-01"])
        self._write_drops(
            [
                {
                    "path": "cluster-content-seo-desktop.json",
                    "error_type": "EmissionValidationError",
                    "error_message": "findings.4.proposed_anchor: "
                    "Additional properties are not allowed ('template_id' was unexpected)",
                }
            ]
        )

        result = check_clusters_represented(self.eng)
        self.assertFalse(
            result["passed"],
            "A non-zero dropped_count must fail the canary even when every "
            "requested cluster has at least one surviving canonical ref.",
        )
        self.assertEqual(result["detail"]["missing_clusters"], [])
        self.assertEqual(result["detail"]["dropped_count"], 1)
        self.assertIn("dropped", result["summary"])

    def test_both_failure_modes_combined(self):
        """Run C's actual shape: missing clusters AND drops in the file."""
        self._write_meta(
            ["visual-cta", "trust-credibility", "pricing", "content-seo"]
        )
        self._write_canonical(["visual-cta F-01", "pricing F-22"])
        self._write_drops(
            [
                {
                    "path": "cluster-trust-credibility-desktop.json",
                    "error_type": "EmissionValidationError",
                    "error_message": "'proposed_anchor' is a required property",
                },
                {
                    "path": "cluster-content-seo-desktop.json",
                    "error_type": "EmissionValidationError",
                    "error_message": "'template_id' was unexpected",
                },
            ]
        )

        result = check_clusters_represented(self.eng)
        self.assertFalse(result["passed"])
        # Summary should mention BOTH failure modes so the operator sees
        # the full picture from the trace line.
        self.assertIn("missing", result["summary"])
        self.assertIn("dropped", result["summary"])

    # --- Skip / edge cases ---

    def test_missing_meta_skips_with_pass(self):
        """Pre-canonical-stage fixture: meta.json absent → informational PASS."""
        # No meta.json or canonical-f-refs.json written.
        result = check_clusters_represented(self.eng)
        self.assertTrue(
            result["passed"],
            "Pre-canonical-stage engagement must skip cleanly (PASS).",
        )
        self.assertIn("skipped", result["summary"])

    def test_missing_canonical_skips_with_pass(self):
        self._write_meta(["pricing"])
        # canonical-f-refs.json intentionally absent.

        result = check_clusters_represented(self.eng)
        self.assertTrue(result["passed"])
        self.assertIn("skipped", result["summary"])


if __name__ == "__main__":
    unittest.main()
