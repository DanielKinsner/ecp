"""Regression test for the canonical-f-refs consolidation (post-migration).

`build_canonical_f_refs.py` — which wrote canonical-f-refs.json in the
{valid_refs, by_canonical_ref} shape the synthesizer dispatch consumes — was
dropped in the 2026-05-26 migration. Its job is now folded into
`lead_prep.py build-canonical-frefs`, which serializes the SAME by_ref it
builds the manifest from into BOTH artifacts: one source of truth
(report/v2_loader.build_canonical_view), no drift.

unittest-style on purpose: the canonical `python -m unittest discover` runner
must catch a regression here. The pytest-only tests that previously guarded
this contract are invisible to that runner (see project memory: ECP test-runner
blind spot).
"""
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


class TestBuildCanonicalFrefsWritesBothShapes(unittest.TestCase):
    def _build(self) -> Path:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        eng = tmp / "engagement"
        shutil.copytree(FIXTURE, eng)
        rc = lead_prep.build_canonical_frefs(eng)
        self.assertEqual(rc, 0, "build-canonical-frefs should succeed on the fixture")
        return eng

    def test_writes_consumer_and_manifest(self):
        eng = self._build()
        self.assertTrue((eng / "canonical-f-refs.json").exists(), "consumer-shape file missing")
        self.assertTrue((eng / "canonical-f-refs-manifest.json").exists(), "manifest missing")

    def test_consumer_shape_is_what_dispatch_reads(self):
        eng = self._build()
        consumer = json.loads((eng / "canonical-f-refs.json").read_text(encoding="utf-8"))
        self.assertIn("valid_refs", consumer)
        self.assertIn("by_canonical_ref", consumer)
        # valid_refs is exactly the keys of by_canonical_ref (the allowlist).
        self.assertEqual(
            sorted(consumer["valid_refs"]), sorted(consumer["by_canonical_ref"].keys())
        )
        self.assertTrue(consumer["valid_refs"], "fixture should yield >=1 canonical ref")
        # Each entry carries the fields build_canonical_f_refs_block / validate read.
        sample = next(iter(consumer["by_canonical_ref"].values()))
        for field in ("title", "scope", "devices_present"):
            self.assertIn(field, sample)

    def test_no_drift_between_consumer_and_manifest(self):
        eng = self._build()
        consumer = json.loads((eng / "canonical-f-refs.json").read_text(encoding="utf-8"))
        manifest = json.loads((eng / "canonical-f-refs-manifest.json").read_text(encoding="utf-8"))
        manifest_refs = {e["f_ref"] for e in manifest["entries"]}
        self.assertEqual(
            set(consumer["valid_refs"]),
            manifest_refs,
            "consumer file and manifest must list the same canonical refs",
        )


if __name__ == "__main__":
    unittest.main()
