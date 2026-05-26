"""v2 unit tests: pipeline.cross_device_title_merge + normalize_finding_title.

Phase H deliverable 8 (2026-04-28). Promoted Layer-2.5 cross-device merge
from .phase-b-tmp/build_canonical_f_refs.py and
scripts/report/v2_loader.build_canonical_view into the canonical
scripts/assembly/pipeline.py module so both callers share one
implementation.

Run:
    python -m unittest tests.test_v2_pipeline_merge
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.pipeline import (  # noqa: E402
    cross_device_title_merge,
    normalize_finding_title,
)


class TestNormalizeFindingTitle(unittest.TestCase):
    def test_simple_lowercase(self):
        self.assertEqual(
            normalize_finding_title("Hero Product Image Missing fetchpriority"),
            "hero product image missing fetchpriority",
        )

    def test_em_dash_split_keeps_first_clause(self):
        self.assertEqual(
            normalize_finding_title("Hero Product Image — Missing fetchpriority='high' Attribute"),
            "hero product image",
        )

    def test_space_padded_hyphen_split(self):
        self.assertEqual(
            normalize_finding_title("BNPL Widget - Position Mismatch"),
            "bnpl widget",
        )

    def test_space_padded_colon_split(self):
        self.assertEqual(
            normalize_finding_title("Trust Badge : Below Fold"),
            "trust badge",
        )

    def test_space_padded_pipe_split(self):
        self.assertEqual(
            normalize_finding_title("Mobile Sticky CTA | Missing"),
            "mobile sticky cta",
        )

    def test_whitespace_collapse(self):
        self.assertEqual(
            normalize_finding_title("  No   MSRP    Anchor  "),
            "no msrp anchor",
        )

    def test_empty_string(self):
        self.assertEqual(normalize_finding_title(""), "")

    def test_only_whitespace(self):
        self.assertEqual(normalize_finding_title("   \t\n  "), "")

    def test_inline_hyphen_not_split(self):
        # Hyphen WITHOUT surrounding spaces should not split (it's part of a word)
        self.assertEqual(
            normalize_finding_title("State-of-the-art widget"),
            "state-of-the-art widget",
        )

    def test_first_separator_wins_when_multiple(self):
        # Em-dash appears first; the colon after should NOT also split
        self.assertEqual(
            normalize_finding_title("Hero — Missing : Detail"),
            "hero",
        )


class TestCrossDeviceTitleMergeBasics(unittest.TestCase):
    def test_empty_input(self):
        by_canonical, aliases = cross_device_title_merge({})
        self.assertEqual(by_canonical, {})
        self.assertEqual(aliases, {})

    def test_single_finding_returns_singleton(self):
        raw = {
            "pricing F-01": {
                "title": "No MSRP Anchor",
                "scope": "page",
                "devices_present": ["desktop"],
            }
        }
        by_canonical, aliases = cross_device_title_merge(raw)
        self.assertEqual(set(by_canonical.keys()), {"pricing F-01"})
        self.assertEqual(aliases, {})
        # Optional fields preserved
        self.assertEqual(by_canonical["pricing F-01"]["scope"], "page")
        self.assertEqual(by_canonical["pricing F-01"]["devices_present"], ["desktop"])

    def test_two_unrelated_findings_no_merge(self):
        raw = {
            "pricing F-01": {"title": "No MSRP Anchor", "devices_present": ["desktop"]},
            "pricing F-02": {"title": "Missing BNPL Widget", "devices_present": ["mobile"]},
        }
        by_canonical, aliases = cross_device_title_merge(raw)
        self.assertEqual(set(by_canonical.keys()), {"pricing F-01", "pricing F-02"})
        self.assertEqual(aliases, {})

    def test_minimal_dict_with_only_title(self):
        # Must not crash if only 'title' is provided
        raw = {
            "audience F-01": {"title": "Foo"},
            "audience F-02": {"title": "Bar"},
        }
        by_canonical, aliases = cross_device_title_merge(raw)
        self.assertEqual(len(by_canonical), 2)
        self.assertEqual(aliases, {})


class TestCrossDeviceMergeBehavior(unittest.TestCase):
    def test_lowest_fnn_wins_as_canonical(self):
        raw = {
            "pricing F-03": {"title": "No MSRP Anchor", "devices_present": ["desktop"]},
            "pricing F-01": {"title": "No MSRP Anchor", "devices_present": ["mobile"]},
        }
        by_canonical, aliases = cross_device_title_merge(raw)
        # F-01 wins (lowest); F-03 is absorbed
        self.assertEqual(set(by_canonical.keys()), {"pricing F-01"})
        self.assertEqual(aliases, {"pricing F-03": "pricing F-01"})

    def test_devices_present_unions_across_group(self):
        raw = {
            "pricing F-01": {
                "title": "No MSRP Anchor",
                "devices_present": ["desktop"],
            },
            "pricing F-02": {
                "title": "No MSRP Anchor",
                "devices_present": ["mobile"],
            },
        }
        by_canonical, _ = cross_device_title_merge(raw)
        self.assertEqual(
            by_canonical["pricing F-01"]["devices_present"],
            ["desktop", "mobile"],
        )

    def test_scope_page_promotion(self):
        # Even one group member with scope='page' promotes the canonical
        raw = {
            "pricing F-01": {
                "title": "No MSRP Anchor",
                "scope": "device",
                "devices_present": ["desktop"],
            },
            "pricing F-02": {
                "title": "No MSRP Anchor",
                "scope": "page",
                "devices_present": ["mobile"],
            },
        }
        by_canonical, _ = cross_device_title_merge(raw)
        self.assertEqual(by_canonical["pricing F-01"]["scope"], "page")

    def test_severity_highest_wins(self):
        # MEDIUM + HIGH + LOW collapses to HIGH
        raw = {
            "pricing F-01": {
                "title": "No MSRP Anchor",
                "severity": "MEDIUM",
            },
            "pricing F-02": {
                "title": "No MSRP Anchor",
                "severity": "HIGH",
            },
            "pricing F-03": {
                "title": "No MSRP Anchor",
                "severity": "LOW",
            },
        }
        by_canonical, _ = cross_device_title_merge(raw)
        self.assertEqual(by_canonical["pricing F-01"]["severity"], "HIGH")

    def test_severity_critical_beats_high(self):
        raw = {
            "pricing F-01": {"title": "X", "severity": "HIGH"},
            "pricing F-02": {"title": "X", "severity": "CRITICAL"},
        }
        by_canonical, _ = cross_device_title_merge(raw)
        self.assertEqual(by_canonical["pricing F-01"]["severity"], "CRITICAL")

    def test_baton_index_by_device_map(self):
        raw = {
            "pricing F-01": {
                "title": "No MSRP Anchor",
                "baton_index": "e23",
                "device": "desktop",
            },
            "pricing F-02": {
                "title": "No MSRP Anchor",
                "baton_index": "absent",
                "device": "mobile",
            },
        }
        by_canonical, _ = cross_device_title_merge(raw)
        self.assertEqual(
            by_canonical["pricing F-01"]["baton_index_by_device"],
            {"desktop": "e23", "mobile": "absent"},
        )

    def test_evidence_anchors_deduplicated(self):
        anchor1 = {"type": "dom", "reference": "e23"}
        anchor2 = {"type": "visual", "reference": "section-2.jpg"}
        raw = {
            "pricing F-01": {
                "title": "No MSRP Anchor",
                "evidence_anchors": [anchor1, anchor2],
            },
            "pricing F-02": {
                "title": "No MSRP Anchor",
                "evidence_anchors": [anchor1],  # duplicate of anchor1
            },
        }
        by_canonical, _ = cross_device_title_merge(raw)
        # Should have anchor1 + anchor2, not anchor1 twice
        self.assertEqual(len(by_canonical["pricing F-01"]["evidence_anchors"]), 2)

    def test_reference_citations_deduplicated(self):
        cite1 = {"section": "msrp-anchor", "url": "https://example.com/a"}
        cite2 = {"section": "msrp-anchor", "url": "https://example.com/b"}
        raw = {
            "pricing F-01": {
                "title": "No MSRP Anchor",
                "reference_citations": [cite1],
            },
            "pricing F-02": {
                "title": "No MSRP Anchor",
                "reference_citations": [cite1, cite2],  # cite1 dup
            },
        }
        by_canonical, _ = cross_device_title_merge(raw)
        self.assertEqual(
            len(by_canonical["pricing F-01"]["reference_citations"]),
            2,
        )


class TestCrossDeviceMergeClusters(unittest.TestCase):
    def test_different_clusters_never_merge_same_title(self):
        # Same title in different clusters stays separate
        raw = {
            "pricing F-01": {"title": "Missing schema", "devices_present": ["desktop"]},
            "content-seo F-01": {"title": "Missing schema", "devices_present": ["desktop"]},
        }
        by_canonical, aliases = cross_device_title_merge(raw)
        self.assertEqual(
            set(by_canonical.keys()),
            {"pricing F-01", "content-seo F-01"},
        )
        self.assertEqual(aliases, {})

    def test_multiple_groups_within_cluster(self):
        raw = {
            "pricing F-01": {"title": "No MSRP Anchor", "devices_present": ["desktop"]},
            "pricing F-02": {"title": "No MSRP Anchor", "devices_present": ["mobile"]},
            "pricing F-03": {"title": "Missing BNPL", "devices_present": ["desktop"]},
            "pricing F-04": {"title": "Missing BNPL", "devices_present": ["mobile"]},
        }
        by_canonical, aliases = cross_device_title_merge(raw)
        self.assertEqual(set(by_canonical.keys()), {"pricing F-01", "pricing F-03"})
        self.assertEqual(
            aliases,
            {"pricing F-02": "pricing F-01", "pricing F-04": "pricing F-03"},
        )


class TestSlingmodsScenario(unittest.TestCase):
    """Reproduce the slingmods cross-device merge that absorbed 14 of 100 raw refs.

    Specific case: the same finding caught with different baton_index across
    devices — desktop says e23, mobile says 'absent', titles differ slightly
    in suffix but share normalized prefix.
    """

    def test_em_dash_subtitle_variance_merges(self):
        raw = {
            "content-seo F-01": {
                "title": "Hero Product Image Missing fetchpriority and Preload",
                "scope": "page",
                "devices_present": ["desktop"],
                "device": "desktop",
                "baton_index": "e23",
                "severity": "HIGH",
            },
            "content-seo F-05": {
                "title": "Hero Product Image — Missing fetchpriority='high' Attribute",
                "scope": "page",
                "devices_present": ["mobile"],
                "device": "mobile",
                "baton_index": "absent",
                "severity": "MEDIUM",
            },
        }
        by_canonical, aliases = cross_device_title_merge(raw)
        # NOTE: the v2_loader version's _normalize_title splits on em-dash,
        # so "Hero Product Image Missing fetchpriority and Preload" (no em-dash)
        # vs "Hero Product Image — Missing fetchpriority='high' Attribute"
        # normalize differently. The Phase G follow-up handoff documented
        # this case (1 of 15 cross-device duplicates missed because only one
        # has the em-dash). Verify the function preserves that behavior.
        # If both titles had em-dashes, they'd merge. Document via test:
        self.assertEqual(len(by_canonical), 2)  # NOT merged due to em-dash asymmetry

    def test_em_dash_on_both_sides_does_merge(self):
        raw = {
            "content-seo F-01": {
                "title": "Hero Product Image — Missing fetchpriority and Preload",
                "scope": "page",
                "devices_present": ["desktop"],
                "device": "desktop",
                "baton_index": "e23",
                "severity": "HIGH",
            },
            "content-seo F-05": {
                "title": "Hero Product Image — Missing fetchpriority='high' Attribute",
                "scope": "page",
                "devices_present": ["mobile"],
                "device": "mobile",
                "baton_index": "absent",
                "severity": "MEDIUM",
            },
        }
        by_canonical, aliases = cross_device_title_merge(raw)
        # Both normalize to "hero product image" — merge wins
        self.assertEqual(set(by_canonical.keys()), {"content-seo F-01"})
        self.assertEqual(aliases, {"content-seo F-05": "content-seo F-01"})
        # Severity wins: HIGH (highest)
        self.assertEqual(by_canonical["content-seo F-01"]["severity"], "HIGH")
        # devices_present unions
        self.assertEqual(
            by_canonical["content-seo F-01"]["devices_present"],
            ["desktop", "mobile"],
        )
        # baton_index_by_device captures both
        self.assertEqual(
            by_canonical["content-seo F-01"]["baton_index_by_device"],
            {"desktop": "e23", "mobile": "absent"},
        )


class TestDeterminism(unittest.TestCase):
    def test_two_runs_produce_identical_output(self):
        raw = {
            "pricing F-01": {
                "title": "No MSRP Anchor",
                "scope": "page",
                "devices_present": ["desktop"],
                "device": "desktop",
                "baton_index": "e23",
                "severity": "HIGH",
                "evidence_anchors": [{"type": "dom", "reference": "e23"}],
            },
            "pricing F-02": {
                "title": "No MSRP Anchor",
                "scope": "page",
                "devices_present": ["mobile"],
                "device": "mobile",
                "baton_index": "e10",
                "severity": "MEDIUM",
                "evidence_anchors": [{"type": "visual", "reference": "section-2.jpg"}],
            },
        }
        out1 = cross_device_title_merge(dict(raw))
        out2 = cross_device_title_merge(dict(raw))
        self.assertEqual(out1, out2)
        # devices_present should be sorted (deterministic order)
        self.assertEqual(
            out1[0]["pricing F-01"]["devices_present"],
            ["desktop", "mobile"],
        )

    def test_input_dict_not_mutated(self):
        raw_original = {
            "pricing F-01": {"title": "X", "devices_present": ["desktop"]},
            "pricing F-02": {"title": "X", "devices_present": ["mobile"]},
        }
        # Snapshot original
        snapshot = {k: dict(v) for k, v in raw_original.items()}
        snapshot["pricing F-01"]["devices_present"] = list(
            snapshot["pricing F-01"]["devices_present"]
        )
        snapshot["pricing F-02"]["devices_present"] = list(
            snapshot["pricing F-02"]["devices_present"]
        )

        cross_device_title_merge(raw_original)

        # Original dict's per-finding metadata should be unchanged
        self.assertEqual(
            raw_original["pricing F-01"]["devices_present"],
            snapshot["pricing F-01"]["devices_present"],
        )
        self.assertEqual(
            raw_original["pricing F-02"]["devices_present"],
            snapshot["pricing F-02"]["devices_present"],
        )


if __name__ == "__main__":
    unittest.main()
