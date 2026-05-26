"""v2 unit tests: business_rules.validate_business_rules.

Run:
    python -m unittest tests.test_v2_business_rules

Phase E.6 deliverable. Verifies each business rule fires on a malformed fixture.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.business_rules import (  # noqa: E402
    BusinessRuleViolation,
    FindingBand,
    build_retry_prompt,
    validate_business_rules,
)


def _emission(findings: list[dict], cluster: str = "pricing", device: str = "mobile") -> dict:
    return {
        "schema_version": 1,
        "engagement_id": "2026-04-27-aaaaaaaa",
        "cluster": cluster,
        "device": device,
        "specialist_model": {"family": "sonnet", "version": "4.6"},
        "started_at": "2026-04-27T16:14:02.000Z",
        "completed_at": "2026-04-27T16:15:38.000Z",
        "status": "complete",
        "findings": findings,
    }


def _baton(e_indexes: list[str]) -> dict:
    return {"elements": [{"e_index": e} for e in e_indexes]}


def _finding(**overrides) -> dict:
    base = {
        "cluster": "pricing",
        "device": "mobile",
        "local_id": 1,
        "verdict": "FAIL",
        "title": "Test",
        "surface": "price-block",
        "element": {"baton_index": "e7"},
        "severity": "HIGH",
        "scope": "page",
        "effort": {"change_type": "copy", "change_scope": "single-file"},
        "evidence_anchors": [{"type": "dom", "reference": "e7"}],
        "reference_citations": [{"source": "x.md", "tier": "Silver"}],
        "observation": "x" * 25,
        "recommendation": "y" * 25,
        "why_this_matters": "z" * 25,
        "evidence_tier": "Silver",
    }
    base.update(overrides)
    return base


class TestEvidenceTierRule(unittest.TestCase):
    def test_evidence_tier_matches_max_citation_passes(self):
        f = _finding(
            reference_citations=[
                {"source": "a.md", "tier": "Bronze"},
                {"source": "b.md", "tier": "Silver"},
            ],
            evidence_tier="Silver",
        )
        violations = validate_business_rules(_emission([f]))
        self.assertEqual(len(violations), 0)

    def test_evidence_tier_lower_than_max_citation_violates(self):
        # Schema's allOf would also catch this, but the business rule is a
        # secondary defense.
        f = _finding(
            reference_citations=[
                {"source": "a.md", "tier": "Gold"},
            ],
            evidence_tier="Silver",  # should be Gold
        )
        violations = validate_business_rules(_emission([f]))
        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].rule, "evidence_tier_matches_max_citation_tier")
        self.assertEqual(violations[0].actual, "Silver")
        self.assertEqual(violations[0].expected, "Gold")


class TestBatonIndexRule(unittest.TestCase):
    def test_baton_index_resolves_to_real_e_index(self):
        f = _finding(
            element={"baton_index": "e3"},
            evidence_anchors=[{"type": "dom", "reference": "e3"}],
        )
        violations = validate_business_rules(
            _emission([f]), baton=_baton(["e0", "e3", "e7"])
        )
        self.assertEqual(len(violations), 0)

    def test_baton_index_not_in_baton_violates(self):
        f = _finding(element={"baton_index": "e47"})
        violations = validate_business_rules(
            _emission([f]), baton=_baton(["e0", "e3", "e7"])  # no e47
        )
        self.assertGreater(len(violations), 0)
        rules = [v.rule for v in violations]
        self.assertIn("baton_index_resolves", rules)

    def test_absent_sentinel_passes(self):
        # Absent sentinel passes baton resolution. Use a visual-only anchor
        # to keep the anchor-resolution rule from firing on the default e7
        # reference (which wouldn't resolve against this test's small baton).
        f = _finding(
            element={"baton_index": "absent"},
            evidence_anchors=[
                {"type": "visual", "reference": "section-1-mobile.jpg", "scroll_y": 100}
            ],
        )
        violations = validate_business_rules(
            _emission([f]), baton=_baton(["e0", "e3"])
        )
        self.assertEqual(len(violations), 0)

    def test_no_baton_skips_check(self):
        f = _finding(element={"baton_index": "e47"})
        # Without a baton, the rule can't evaluate — silent pass
        violations = validate_business_rules(_emission([f]))
        baton_violations = [v for v in violations if "baton" in v.rule]
        self.assertEqual(len(baton_violations), 0)


class TestAnchorResolutionRule(unittest.TestCase):
    def test_visual_anchor_with_screenshot_pattern_passes(self):
        f = _finding(evidence_anchors=[
            {"type": "visual", "reference": "section-2-mobile.jpg", "scroll_y": 480}
        ])
        violations = validate_business_rules(_emission([f]), baton=_baton(["e7"]))
        self.assertEqual(len(violations), 0)

    def test_visual_anchor_bad_pattern_violates(self):
        f = _finding(evidence_anchors=[
            {"type": "visual", "reference": "https://example.com/img.png", "scroll_y": 480}
        ])
        violations = validate_business_rules(_emission([f]), baton=_baton(["e7"]))
        anchor_violations = [v for v in violations if "anchor" in v.rule]
        self.assertGreater(len(anchor_violations), 0)

    def test_dom_anchor_e_index_resolves(self):
        f = _finding(evidence_anchors=[
            {"type": "dom", "reference": "e7"}
        ])
        violations = validate_business_rules(_emission([f]), baton=_baton(["e7"]))
        self.assertEqual(len(violations), 0)

    def test_dom_anchor_e_index_unresolved_violates(self):
        f = _finding(evidence_anchors=[
            {"type": "dom", "reference": "e99"}
        ])
        violations = validate_business_rules(_emission([f]), baton=_baton(["e7"]))
        anchor_violations = [v for v in violations if "anchor" in v.rule]
        self.assertGreater(len(anchor_violations), 0)

    def test_dom_anchor_css_selector_skipped(self):
        # Free-form CSS selector / DOM path can't be checked without DOM tree
        f = _finding(evidence_anchors=[
            {"type": "dom", "reference": "div.product-card[data-id='42']"}
        ])
        violations = validate_business_rules(_emission([f]), baton=_baton(["e7"]))
        # No violation — accepted as uncheckable
        self.assertEqual(len(violations), 0)


class TestRetryPromptConstruction(unittest.TestCase):
    def test_retry_prompt_contains_violations(self):
        f = _finding(element={"baton_index": "e99"})
        violations = validate_business_rules(_emission([f]), baton=_baton(["e7"]))
        prompt = build_retry_prompt("pricing", "mobile", violations)
        self.assertIn("e99", prompt)
        self.assertIn("baton_index", prompt)
        self.assertIn("No prose, no markdown fences", prompt)


# ---------------------------------------------------------------------------
# Phase L tests — surface vocabulary, baton precedence, within-emission
# uniqueness, finding count band, schema_version assertion
# ---------------------------------------------------------------------------


def _baton_with_sections(e_indexes: list[str], sections: list[str] | None = None) -> dict:
    return {
        "elements": [{"e_index": e} for e in e_indexes],
        "sections": [{"slug": s} for s in (sections or [])],
    }


class TestSurfaceInVocabularyRule(unittest.TestCase):
    def test_surface_in_vocabulary_passes(self):
        f = _finding(surface="price-block")
        violations = validate_business_rules(
            _emission([f]),
            cluster_vocab={"price-block", "msrp-anchor"},
        )
        self.assertEqual(len(violations), 0)

    def test_surface_not_in_vocabulary_violates(self):
        f = _finding(surface="invented-surface")
        violations = validate_business_rules(
            _emission([f]),
            cluster_vocab={"price-block", "msrp-anchor"},
        )
        rules = [v.rule for v in violations]
        self.assertIn("surface_in_vocabulary", rules)

    def test_baton_section_slug_passes(self):
        # Baton-derived section slug should always validate even if not in
        # cluster baseline vocab (runtime adds baton sections to effective vocab)
        f = _finding(surface="hero-pricing-paypal")
        violations = validate_business_rules(
            _emission([f]),
            baton=_baton_with_sections(["e7"], sections=["hero-pricing-paypal"]),
            cluster_vocab={"price-block"},
        )
        # Filter to surface-vocab violations only (baton resolution rule may fire on e7 issues)
        surface_violations = [v for v in violations if v.rule == "surface_in_vocabulary"]
        self.assertEqual(len(surface_violations), 0)

    def test_other_with_note_passes(self):
        f = _finding(surface="other", surface_note="Page has a unique cookie-banner-overlay surface")
        violations = validate_business_rules(
            _emission([f]),
            cluster_vocab={"price-block"},
        )
        surface_violations = [v for v in violations if v.rule.startswith("surface_")]
        self.assertEqual(len(surface_violations), 0)

    def test_other_without_note_violates(self):
        f = _finding(surface="other")  # no surface_note
        violations = validate_business_rules(
            _emission([f]),
            cluster_vocab={"price-block"},
        )
        rules = [v.rule for v in violations]
        self.assertIn("surface_other_requires_note", rules)

    def test_other_with_blank_note_violates(self):
        f = _finding(surface="other", surface_note="   ")
        violations = validate_business_rules(
            _emission([f]),
            cluster_vocab={"price-block"},
        )
        rules = [v.rule for v in violations]
        self.assertIn("surface_other_requires_note", rules)

    def test_no_vocab_skips_check(self):
        # Without cluster_vocab the rule is not evaluated
        f = _finding(surface="anything")
        violations = validate_business_rules(_emission([f]))
        surface_violations = [v for v in violations if v.rule.startswith("surface_")]
        self.assertEqual(len(surface_violations), 0)


class TestBatonPrecedenceRule(unittest.TestCase):
    def test_verbatim_quote_matches_cited_element_passes(self):
        f = _finding(
            element={"baton_index": "e7"},
            observation='The product price renders as "$59.95" with no anchor — ' + "x" * 25,
        )
        baton = {
            "elements": [
                {"e_index": "e7", "text_content": "$59.95"},
                {"e_index": "e8", "text_content": "Add to Cart"},
            ]
        }
        violations = validate_business_rules(_emission([f]), baton=baton)
        precedence_violations = [v for v in violations if v.rule.startswith("baton_precedence")]
        self.assertEqual(len(precedence_violations), 0)

    def test_verbatim_quote_matches_other_element_violates(self):
        # Prose quotes "$59.95" but cites e8 ("Add to Cart") — heuristic should flag
        f = _finding(
            element={"baton_index": "e8"},
            observation='The product price renders as "$59.95" with no anchor — ' + "x" * 25,
        )
        baton = {
            "elements": [
                {"e_index": "e7", "text_content": "$59.95"},
                {"e_index": "e8", "text_content": "Add to Cart"},
            ]
        }
        violations = validate_business_rules(_emission([f]), baton=baton)
        rules = [v.rule for v in violations]
        self.assertIn("baton_precedence_verbatim_anchor", rules)

    def test_no_quotes_skips_check(self):
        # No verbatim quotes in prose → can't apply heuristic, no violation
        f = _finding(
            element={"baton_index": "e7"},
            observation="The price is presented without an anchor or comparison" + "x" * 25,
        )
        baton = {
            "elements": [
                {"e_index": "e7", "text_content": "$59.95"},
                {"e_index": "e8", "text_content": "Add to Cart"},
            ]
        }
        violations = validate_business_rules(_emission([f]), baton=baton)
        precedence_violations = [v for v in violations if v.rule.startswith("baton_precedence")]
        self.assertEqual(len(precedence_violations), 0)

    def test_absent_skips_check(self):
        f = _finding(
            element={"baton_index": "absent"},
            observation='The page has no "MSRP" anchor visible — ' + "x" * 25,
            evidence_anchors=[
                {"type": "visual", "reference": "section-1-mobile.jpg", "scroll_y": 100}
            ],
        )
        baton = {"elements": [{"e_index": "e7", "text_content": "MSRP $89.95"}]}
        violations = validate_business_rules(_emission([f]), baton=baton)
        precedence_violations = [v for v in violations if v.rule.startswith("baton_precedence")]
        self.assertEqual(len(precedence_violations), 0)


class TestWithinEmissionUniquenessRule(unittest.TestCase):
    def test_unique_tuples_pass(self):
        f1 = _finding(local_id=1, surface="price-block", element={"baton_index": "e7"}, verdict="FAIL")
        f2 = _finding(local_id=2, surface="msrp-anchor", element={"baton_index": "e7"}, verdict="FAIL")
        violations = validate_business_rules(_emission([f1, f2]))
        uniqueness_violations = [v for v in violations if v.rule.startswith("within_emission_unique")]
        self.assertEqual(len(uniqueness_violations), 0)

    def test_duplicate_tuple_violates(self):
        f1 = _finding(local_id=1, surface="price-block", element={"baton_index": "e7"}, verdict="FAIL")
        f2 = _finding(local_id=2, surface="price-block", element={"baton_index": "e7"}, verdict="FAIL")
        violations = validate_business_rules(_emission([f1, f2]))
        rules = [v.rule for v in violations]
        self.assertIn("within_emission_unique_anchors", rules)

    def test_absent_with_distinct_titles_passes(self):
        # 3 absent findings with low title-token Jaccard — protects content-seo case
        f1 = _finding(
            local_id=1, title="No JSON-LD product schema",
            surface="meta-tag", element={"baton_index": "absent"}, verdict="FAIL",
            evidence_anchors=[{"type": "visual", "reference": "section-1.jpg", "scroll_y": 0}],
        )
        f2 = _finding(
            local_id=2, title="No Open Graph image",
            surface="meta-tag", element={"baton_index": "absent"}, verdict="FAIL",
            evidence_anchors=[{"type": "visual", "reference": "section-1.jpg", "scroll_y": 0}],
        )
        f3 = _finding(
            local_id=3, title="No GTIN identifier",
            surface="meta-tag", element={"baton_index": "absent"}, verdict="FAIL",
            evidence_anchors=[{"type": "visual", "reference": "section-1.jpg", "scroll_y": 0}],
        )
        violations = validate_business_rules(_emission([f1, f2, f3]))
        uniqueness_violations = [v for v in violations if v.rule.startswith("within_emission_unique")]
        self.assertEqual(len(uniqueness_violations), 0)

    def test_absent_with_similar_titles_violates(self):
        # Two absent findings with high title-Jaccard — should flag.
        # Realistic near-duplicate scenario: same conceptual finding rephrased.
        f1 = _finding(
            local_id=1, title="Missing trust badges near CTA button",
            surface="trust-badge-cluster", element={"baton_index": "absent"}, verdict="FAIL",
            evidence_anchors=[{"type": "visual", "reference": "section-1.jpg", "scroll_y": 0}],
        )
        f2 = _finding(
            local_id=2, title="Missing trust badges near CTA",
            surface="trust-badge-cluster", element={"baton_index": "absent"}, verdict="FAIL",
            evidence_anchors=[{"type": "visual", "reference": "section-1.jpg", "scroll_y": 0}],
        )
        # Tokens (post-stopword filter):
        #   {missing, trust, badges, near, cta, button} ∩ {missing, trust, badges, near, cta}
        #   = 5; union = 6 → Jaccard 0.833 ≥ 0.7 → flag
        violations = validate_business_rules(_emission([f1, f2]))
        rules = [v.rule for v in violations]
        self.assertIn("within_emission_unique_anchors_absent", rules)

    def test_absent_with_low_jaccard_titles_passes(self):
        # The Phase K content-seo case: 3 absent findings, distinct conceptual issues,
        # low Jaccard between any pair. These should NOT be flagged.
        f1 = _finding(
            local_id=1, title="Breadcrumb skips intermediate categories",
            surface="meta-tag", element={"baton_index": "absent"}, verdict="FAIL",
            evidence_anchors=[{"type": "visual", "reference": "section-1.jpg", "scroll_y": 0}],
        )
        f2 = _finding(
            local_id=2, title="No BreadcrumbList structured data",
            surface="meta-tag", element={"baton_index": "absent"}, verdict="FAIL",
            evidence_anchors=[{"type": "visual", "reference": "section-1.jpg", "scroll_y": 0}],
        )
        f3 = _finding(
            local_id=3, title="No history breadcrumb for filter-state return",
            surface="meta-tag", element={"baton_index": "absent"}, verdict="FAIL",
            evidence_anchors=[{"type": "visual", "reference": "section-1.jpg", "scroll_y": 0}],
        )
        violations = validate_business_rules(_emission([f1, f2, f3]))
        uniqueness_violations = [v for v in violations if v.rule.startswith("within_emission_unique")]
        self.assertEqual(len(uniqueness_violations), 0)


class TestFindingCountBandRule(unittest.TestCase):
    def test_in_band_passes(self):
        findings = [_finding(local_id=i + 1) for i in range(3)]
        violations = validate_business_rules(
            _emission(findings),
            target_band=FindingBand(2, 5),
        )
        count_violations = [v for v in violations if v.rule == "finding_count_in_band"]
        self.assertEqual(len(count_violations), 0)

    def test_below_band_violates(self):
        findings = [_finding(local_id=1)]
        violations = validate_business_rules(
            _emission(findings),
            target_band=FindingBand(3, 5),
        )
        rules = [v.rule for v in violations]
        self.assertIn("finding_count_in_band", rules)

    def test_above_band_violates(self):
        findings = [_finding(local_id=i + 1) for i in range(7)]
        violations = validate_business_rules(
            _emission(findings),
            target_band=FindingBand(3, 5),
        )
        rules = [v.rule for v in violations]
        self.assertIn("finding_count_in_band", rules)

    def test_skipped_status_skips_check(self):
        # status='skipped' short-circuits ALL Phase L checks including band
        emission = _emission([])
        emission["status"] = "skipped"
        emission["skip_reason"] = "no relevant surfaces on this page"
        violations = validate_business_rules(emission, target_band=FindingBand(3, 5))
        count_violations = [v for v in violations if v.rule == "finding_count_in_band"]
        self.assertEqual(len(count_violations), 0)

    def test_no_band_skips_check(self):
        findings = [_finding(local_id=1)]
        violations = validate_business_rules(_emission(findings))
        count_violations = [v for v in violations if v.rule == "finding_count_in_band"]
        self.assertEqual(len(count_violations), 0)

    def test_findingband_parse(self):
        self.assertEqual(FindingBand.parse("3-5"), FindingBand(3, 5))
        self.assertEqual(FindingBand.parse("1-10"), FindingBand(1, 10))


class TestSchemaVersionAssertion(unittest.TestCase):
    def test_missing_schema_version_raises(self):
        emission_no_version = {
            "engagement_id": "test",
            "cluster": "pricing",
            "device": "mobile",
            "status": "complete",
            "findings": [],
        }
        with self.assertRaises(ValueError) as ctx:
            validate_business_rules(emission_no_version)
        self.assertIn("schema_version", str(ctx.exception))

    def test_skipped_emission_short_circuits_all_phase_l_rules(self):
        # status='skipped' should bypass ALL Phase L checks: vocab, count band,
        # within-emission uniqueness — even if the data would otherwise violate.
        emission = _emission([])
        emission["status"] = "skipped"
        emission["skip_reason"] = "page has no relevant surfaces"
        violations = validate_business_rules(
            emission,
            cluster_vocab={"price-block"},
            target_band=FindingBand(3, 5),
        )
        self.assertEqual(len(violations), 0)


class TestRetryPromptDeterminism(unittest.TestCase):
    def test_violations_sorted_for_cache_friendliness(self):
        # Same set of violations in different orders should produce identical prompts
        f1 = _finding(local_id=1, surface="bad-1", element={"baton_index": "e99"})
        f2 = _finding(local_id=2, surface="bad-2", element={"baton_index": "e98"})
        emission = _emission([f1, f2])

        violations = validate_business_rules(
            emission,
            baton=_baton(["e7"]),
            cluster_vocab={"price-block"},
        )
        prompt_a = build_retry_prompt("pricing", "mobile", violations)
        prompt_b = build_retry_prompt("pricing", "mobile", list(reversed(violations)))
        self.assertEqual(prompt_a, prompt_b)


if __name__ == "__main__":
    unittest.main()
