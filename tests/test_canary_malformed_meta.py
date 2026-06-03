"""Negative tests: canary checks must tolerate malformed meta / ethics shapes.

Covers adversarial-review findings 5, 10, 11:
- check_ethics_findings_have_source_urls: f"...{local_id:02d}" crashed on a
  string local_id (ValueError).
- check_clusters_represented: set(meta["clusters_used"]) silently char-expanded
  a string into per-character "clusters".
- check_trace_counters_reconcile_with_artifacts: clusters_used / devices_scanned
  iterated as lists silently char-expanded a string.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.canary_checks import (  # noqa: E402
    check_clusters_represented,
    check_ethics_findings_have_source_urls,
    check_trace_counters_reconcile_with_artifacts,
)


class TestEthicsLocalIdCoercion(unittest.TestCase):
    def _path(self, findings):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        p = Path(tmp.name) / "ethics-findings.json"
        p.write_text(json.dumps({"findings": findings}), encoding="utf-8")
        return p

    def test_string_local_id_does_not_crash(self):
        # Pre-fix: f"ethics F-{local_id:02d}" with local_id="3" raises ValueError.
        p = self._path([{"ethics_state": "BLOCK", "local_id": "3",
                         "source_url": "https://law.example.gov/x"}])
        r = check_ethics_findings_have_source_urls(p)
        self.assertTrue(r["passed"])  # valid source_url + no crash

    def test_int_local_id_still_flags_missing_url(self):
        p = self._path([{"ethics_state": "ADJACENT", "local_id": 3, "source_url": ""}])
        r = check_ethics_findings_have_source_urls(p)
        self.assertFalse(r["passed"])  # sanity: empty source_url still fails


class TestClustersRepresentedMalformedMeta(unittest.TestCase):
    def test_string_clusters_used_not_char_expanded(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        eng = Path(tmp.name) / "engagement"
        eng.mkdir()
        (eng / "meta.json").write_text(json.dumps({"clusters_used": "visual-cta"}), encoding="utf-8")
        (eng / "canonical-f-refs.json").write_text(
            json.dumps({"valid_refs": ["visual-cta F-01"]}), encoding="utf-8")
        r = check_clusters_represented(eng)
        # Pre-fix: set("visual-cta") expands to single chars -> bogus missing
        # clusters -> passed False. Post-fix: non-list -> empty expected -> pass.
        self.assertTrue(r["passed"])


class TestTraceCountersMalformedMeta(unittest.TestCase):
    def test_string_meta_lists_not_char_expanded(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        eng = Path(tmp.name) / "engagement"
        eng.mkdir()
        (eng / "meta.json").write_text(
            json.dumps({"clusters_used": "visual-cta", "devices_scanned": "mobile"}),
            encoding="utf-8")
        (eng / "audit-trace.log").write_text("", encoding="utf-8")
        # Decoy emission matching a char-expanded (cluster='v', device='m') pair.
        # Pre-fix the canary char-expands meta and counts this file -> observed
        # (1) > counter (0) -> FAIL. Post-fix: non-list meta yields no requested
        # pairs -> nothing counted -> reconciles.
        (eng / "cluster-v-m.json").write_text("{}", encoding="utf-8")
        r = check_trace_counters_reconcile_with_artifacts(eng)
        self.assertTrue(r["passed"])


if __name__ == "__main__":
    unittest.main()
