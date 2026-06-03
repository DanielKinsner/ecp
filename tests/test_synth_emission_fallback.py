"""Regression tests for scripts/build_synthesizer_emission_fallback.py.

These pin two silent type-contract bugs found in the Phase J D2 emergency
fallback builder: it read the *JSON* field names against the *Finding*
dataclass, which renames/flattens them in json_parser._finding_from_dict.
Because getattr(..., None) does not raise, the manifests degraded silently:

- derive_severity_manifest read f.severity / f.evidence_tier (Finding has
  f.priority / f.tier) -> every row collapsed to (0, "Bronze") and the
  manifest sorted by confidence only, ignoring severity.
- derive_quick_wins read f.effort.change_type (Finding has top-level
  f.change_type) -> quick_wins_manifest was always empty.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.models import Finding  # noqa: E402
import build_synthesizer_emission_fallback as fb  # noqa: E402


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


class TestSeverityManifestOrdering(unittest.TestCase):
    def test_orders_by_severity_then_tier_not_confidence(self):
        # CRITICAL with LOW confidence must outrank LOW with HIGH confidence.
        # Under the f.severity bug, severity is invisible and the LOW-but-
        # high-confidence finding would sort first.
        crit_bronze = _make_finding(
            cluster="pricing", local_index=1,
            priority="CRITICAL", priority_rank=0, tier="Bronze", confidence=0.1,
        )
        crit_gold = _make_finding(
            cluster="checkout", local_index=3,
            priority="CRITICAL", priority_rank=0, tier="Gold", confidence=0.5,
        )
        low_gold = _make_finding(
            cluster="visual-cta", local_index=2,
            priority="LOW", priority_rank=3, tier="Gold", confidence=0.9,
        )
        findings = [crit_bronze, low_gold, crit_gold]
        valid = {"pricing F-01", "checkout F-03", "visual-cta F-02"}

        result = fb.derive_severity_manifest(findings, valid)

        # Severity dominates; among CRITICALs, Gold tier outranks Bronze.
        self.assertEqual(
            result, ["checkout F-03", "pricing F-01", "visual-cta F-02"]
        )

    def test_respects_valid_refs_allowlist(self):
        keep = _make_finding(cluster="pricing", local_index=1, priority="HIGH")
        drop = _make_finding(cluster="seo", local_index=9, priority="CRITICAL", priority_rank=0)
        result = fb.derive_severity_manifest([keep, drop], {"pricing F-01"})
        self.assertEqual(result, ["pricing F-01"])


class TestQuickWins(unittest.TestCase):
    def test_reads_flattened_change_fields(self):
        qual_css = _make_finding(
            cluster="pricing", local_index=1,
            change_type="css", change_scope="single-file",
        )
        qual_copy = _make_finding(
            cluster="visual-cta", local_index=2,
            change_type="copy", change_scope="component",
        )
        wrong_type = _make_finding(
            cluster="trust", local_index=3,
            change_type="feature", change_scope="single-file",
        )
        wrong_scope = _make_finding(
            cluster="checkout", local_index=4,
            change_type="css", change_scope="cross-cutting",
        )
        findings = [qual_css, qual_copy, wrong_type, wrong_scope]
        valid = {f"{c} F-{i:02d}" for c, i in
                 [("pricing", 1), ("visual-cta", 2), ("trust", 3), ("checkout", 4)]}

        result = fb.derive_quick_wins(findings, valid)

        # Only the copy/css + single-file/component findings qualify.
        self.assertEqual(result, ["pricing F-01", "visual-cta F-02"])

    def test_quick_wins_respects_valid_refs(self):
        qual = _make_finding(
            cluster="seo", local_index=9,
            change_type="css", change_scope="single-file",
        )
        result = fb.derive_quick_wins([qual], valid_refs=set())
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
