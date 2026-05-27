"""G16 regression: build_canonical_view surfaces schema-validation drops.

Pre-G16, ``scripts/report/v2_loader.build_canonical_view`` wrapped each
``parse_emission_file`` call in a bare ``except Exception: continue`` —
schema-invalid cluster emissions were silently excluded from the canonical
view with no observability. Engagement
``docs/ecp/2026-05-27-52f53a53`` lost 6 of 12 cluster files this way
(trust-credibility + content-seo entirely, half of performance-ux +
product-media; ~25 high-severity FAIL findings vanished) while every
canary reported PASS — the §0 untraceable-misleading failure mode the
trust contract forbids.

Post-G16:
- ``build_canonical_view`` returns a 3-tuple
  ``(by_canonical_ref, merge_aliases, dropped_emissions)`` where
  ``dropped_emissions`` records every emission that failed schema
  validation.
- ``scripts/lead_prep.py build-canonical-frefs`` writes the drops to
  ``canonical-frefs-dropped.json`` (always — empty list on a clean run
  so downstream tooling can rely on its presence) and exits non-zero
  (code 4) on any drops.

unittest-style on purpose: the canonical ``python -m unittest discover``
runner is the project's authoritative regression gate (see project
memory: ECP test-runner blind spot for pytest-only files).

Run:
    python -m unittest tests.test_g16_canonical_view_surfaces_drops
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.v2_loader import build_canonical_view  # noqa: E402


_VALID_FIXTURE = _REPO / "tests" / "fixtures" / "v2_engagement_with_adjacent_ethics"


class TestBuildCanonicalViewSurfacesDrops(unittest.TestCase):
    """Direct unit test of build_canonical_view's 3-tuple contract."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.eng = Path(self.tmp.name) / "engagement"
        self.eng.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _copy_valid_cluster(self) -> Path:
        """Copy one known-good cluster emission into the tmp engagement."""
        src = _VALID_FIXTURE / "cluster-pricing-desktop.json"
        dst = self.eng / "cluster-pricing-desktop.json"
        shutil.copy(src, dst)
        return dst

    def _write_invalid_cluster(self) -> Path:
        """Write a cluster file that parse_emission_file is guaranteed to reject.

        Using a clearly-malformed top-level shape (missing the required
        ``findings`` field, wrong type elsewhere) rather than a subtle
        per-finding violation keeps the test stable against schema
        evolution — what matters is that the file is rejected and the
        rejection is surfaced.
        """
        path = self.eng / "cluster-content-seo-desktop.json"
        path.write_text(
            json.dumps({"oops": "this is not a valid cluster emission"}),
            encoding="utf-8",
        )
        return path

    def test_returns_three_tuple(self):
        """Signature contract: 3-tuple (by_ref, aliases, dropped_emissions)."""
        valid = self._copy_valid_cluster()
        result = build_canonical_view([valid], None)
        self.assertEqual(
            len(result),
            3,
            "build_canonical_view must return (by_canonical_ref, merge_aliases, "
            "dropped_emissions) — see G16 contract change.",
        )
        by_ref, aliases, drops = result
        self.assertIsInstance(by_ref, dict)
        self.assertIsInstance(aliases, dict)
        self.assertIsInstance(drops, list)

    def test_clean_run_has_empty_drops(self):
        valid = self._copy_valid_cluster()
        by_ref, _aliases, drops = build_canonical_view([valid], None)
        self.assertEqual(
            drops,
            [],
            "Valid cluster emission must produce an empty dropped_emissions list.",
        )
        self.assertTrue(
            by_ref,
            "Valid cluster emission must yield at least one canonical ref.",
        )

    def test_invalid_cluster_is_recorded_not_swallowed(self):
        """The core G16 contract: a schema-invalid file must appear in drops."""
        valid = self._copy_valid_cluster()
        invalid = self._write_invalid_cluster()

        by_ref, _aliases, drops = build_canonical_view([valid, invalid], None)

        self.assertEqual(
            len(drops),
            1,
            f"Exactly one cluster emission should be recorded as dropped; "
            f"got {len(drops)}: {drops}",
        )
        drop = drops[0]
        self.assertEqual(drop["path"], invalid.name)
        self.assertIn(
            "error_type",
            drop,
            "Drop record must carry error_type for operator triage.",
        )
        self.assertIn(
            "error_message",
            drop,
            "Drop record must carry error_message for operator triage.",
        )

        # The valid cluster's findings still made it through; the invalid
        # cluster's findings are absent (we cannot trust partially-parsed
        # emissions, so excluding them is correct — recording them is what
        # was missing pre-G16).
        clusters_in_view = {v.get("cluster") for v in by_ref.values()}
        self.assertIn("pricing", clusters_in_view)
        self.assertNotIn("content-seo", clusters_in_view)


class TestLeadPrepCLISurfacesDrops(unittest.TestCase):
    """End-to-end: lead_prep build-canonical-frefs writes the drops file
    and exits non-zero when any emission is dropped."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.eng = Path(self.tmp.name) / "engagement"
        self.eng.mkdir()
        # Provide one valid cluster so by_ref is non-empty (otherwise
        # lead_prep returns 3 for "no canonical findings produced").
        shutil.copy(
            _VALID_FIXTURE / "cluster-pricing-desktop.json",
            self.eng / "cluster-pricing-desktop.json",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def _run_cli(self) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                sys.executable,
                str(_REPO / "scripts" / "lead_prep.py"),
                "build-canonical-frefs",
                "--engagement",
                str(self.eng),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def test_clean_run_writes_empty_drops_file_and_exits_zero(self):
        result = self._run_cli()
        self.assertEqual(
            result.returncode,
            0,
            f"Clean run should exit 0. stderr={result.stderr!r}",
        )
        dropped_path = self.eng / "canonical-frefs-dropped.json"
        self.assertTrue(
            dropped_path.exists(),
            "canonical-frefs-dropped.json must be written even on a clean "
            "run so the clusters_represented canary has a stable file.",
        )
        doc = json.loads(dropped_path.read_text(encoding="utf-8"))
        self.assertEqual(doc.get("dropped_count"), 0)
        self.assertEqual(doc.get("dropped"), [])

    def test_dropped_run_writes_drops_and_exits_non_zero(self):
        # Add a schema-invalid cluster file.
        (self.eng / "cluster-content-seo-desktop.json").write_text(
            json.dumps({"oops": "not a valid emission"}),
            encoding="utf-8",
        )

        result = self._run_cli()
        # Pre-G16 this returned 0 silently. Post-G16 it must signal failure
        # so the audit lead's CLI flow phase-blocks.
        self.assertEqual(
            result.returncode,
            4,
            f"A dropped emission must produce exit code 4 (G16 phase-block). "
            f"Got {result.returncode}. stderr={result.stderr!r}",
        )
        # Loud stderr surfaces the failure to the operator.
        self.assertIn("[G16]", result.stderr)
        self.assertIn("cluster-content-seo-desktop.json", result.stderr)

        dropped_path = self.eng / "canonical-frefs-dropped.json"
        self.assertTrue(dropped_path.exists())
        doc = json.loads(dropped_path.read_text(encoding="utf-8"))
        self.assertEqual(doc.get("dropped_count"), 1)
        self.assertEqual(len(doc.get("dropped") or []), 1)
        self.assertEqual(
            doc["dropped"][0]["path"], "cluster-content-seo-desktop.json"
        )


if __name__ == "__main__":
    unittest.main()
