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

    def test_fabricated_element_self_skips_when_baton_proves_absence(self):
        f = _finding(
            element={"baton_index": "e999"},
            evidence_anchors=[{"type": "dom", "reference": "e999"}],
        )
        violations = validate_business_rules(_emission([f]), baton=_baton(["e7"]))
        rules = {v.rule for v in violations}

        self.assertIn("baton_index_resolves", rules)
        self.assertIn("anchor_baton_resolves", rules)

        prompt = build_retry_prompt("pricing", "mobile", violations)
        self.assertIn("If you cannot ground a finding to a real baton element", prompt)
        self.assertIn("do not", prompt)
        self.assertIn("emit it", prompt)


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


class TestG19BatonPrecedenceFalsePositiveFixes(unittest.TestCase):
    """G19 (2026-05-27): two specific false-positive classes the
    baton_precedence_verbatim_anchor rule had been bouncing
    correctly-anchored findings on. Each test reproduces the exact
    scenario from a 2026-05-27 live-run lead-reflection."""

    def test_html_attribute_token_does_not_false_match(self):
        """docs/ecp/2026-05-27-0669899d (Amazon): a performance-ux
        finding correctly anchored to the hero LCP image (e3) cited
        ``fetchpriority="high"`` in prose. The pre-G19 extractor pulled
        bare "high" out of the attribute and substring-matched it
        against an unrelated "Amazon's Choice — highly rated" badge
        element (e60), bouncing the finding. Post-G19 the attribute
        gets stripped before quote extraction."""
        f = _finding(
            element={"baton_index": "e3"},
            observation=(
                'The hero LCP image is served without fetchpriority="high", '
                'delaying the Largest Contentful Paint metric — ' + "x" * 25
            ),
        )
        baton = {
            "elements": [
                {"e_index": "e3", "text_content": "Nordic Naturals Ultimate Omega"},
                {"e_index": "e60", "text_content": "Amazon's Choice — highly rated"},
            ]
        }
        violations = validate_business_rules(_emission([f]), baton=baton)
        precedence_violations = [
            v for v in violations if v.rule.startswith("baton_precedence")
        ]
        self.assertEqual(
            precedence_violations,
            [],
            f"G19: fetchpriority=\"high\" must not false-match elements "
            f"whose text contains the substring 'high'. Got: {precedence_violations}",
        )

    def test_short_generic_word_does_not_false_match(self):
        """docs/ecp/2026-05-27-4a0721e9 (slingmods): a category-navigation
        finding correctly anchored to the search submit button (e2, empty
        text) cited the word "Search" in prose. The pre-G19 extractor
        treated bare "Search" as authoritative element text and
        substring-matched it against a large header element (e1) whose
        text blob contained "Search" → bounced the finding."""
        f = _finding(
            element={"baton_index": "e2"},
            observation=(
                'The "Search" button has no aria-label for screen readers — '
                + "x" * 25
            ),
        )
        baton = {
            "elements": [
                {
                    "e_index": "e1",
                    "text_content": "Home | Shop | Search this site | Cart | Account | Help",
                },
                {"e_index": "e2", "text_content": ""},  # the search submit control
            ]
        }
        violations = validate_business_rules(_emission([f]), baton=baton)
        precedence_violations = [
            v for v in violations if v.rule.startswith("baton_precedence")
        ]
        self.assertEqual(
            precedence_violations,
            [],
            f"G19: short generic word 'Search' must not false-match an "
            f"element whose text blob contains it. Got: {precedence_violations}",
        )

    def test_price_token_still_triggers_real_mismatch(self):
        """Guard against over-correction: short tokens that contain a
        digit or identifier-marker char ARE substantive ("$59.95", "30%",
        "SKU123"). The original test_verbatim_quote_matches_other_element_violates
        already covers $59.95; this test adds % and # variants."""
        # Each quote must be ≥4 chars (the substantive-quote min) AND
        # contain a digit or identifier char — both conditions are real
        # specialist patterns we want to keep catching.
        for quoted_text, other_text in (
            ('"100%"', "100% guaranteed"),  # 4-char percentage
            ('"SKU123"', "SKU123 in stock"),  # identifier with digits
            ('"$33.99"', "Now $33.99 sale"),  # price with $ and digits
        ):
            with self.subTest(quote=quoted_text):
                f = _finding(
                    element={"baton_index": "e8"},
                    observation=(
                        f'The page mentions {quoted_text} but the cite '
                        f'points to a different element — ' + "x" * 25
                    ),
                )
                baton = {
                    "elements": [
                        {"e_index": "e7", "text_content": other_text},
                        {"e_index": "e8", "text_content": "Add to Cart"},
                    ]
                }
                violations = validate_business_rules(_emission([f]), baton=baton)
                rules = [v.rule for v in violations]
                self.assertIn(
                    "baton_precedence_verbatim_anchor",
                    rules,
                    f"G19: short tokens with digits/identifier chars "
                    f"({quoted_text}) must still trigger the rule on real "
                    f"mismatches. Got rules: {rules}",
                )

    def test_multi_word_quote_still_triggers_real_mismatch(self):
        """Multi-word phrases like "Read More" remain substantive and
        the rule still fires on legitimate mismatches."""
        f = _finding(
            element={"baton_index": "e8"},
            observation=(
                'The page has a "Read More" link but the cite points '
                'to an unrelated CTA — ' + "x" * 25
            ),
        )
        baton = {
            "elements": [
                {"e_index": "e7", "text_content": "Read More about shipping"},
                {"e_index": "e8", "text_content": "Add to Cart"},
            ]
        }
        violations = validate_business_rules(_emission([f]), baton=baton)
        rules = [v.rule for v in violations]
        self.assertIn(
            "baton_precedence_verbatim_anchor",
            rules,
            "G19: multi-word phrase quotes must still trigger the rule on "
            "real mismatches (Read More cited but anchored to Add to Cart).",
        )


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


class TestLG2BatonPrecedenceDeviceScoping(unittest.TestCase):
    """LG2 (2026-06-12 live gate): ``_check_baton_precedence`` pooled
    desktop + mobile elements into one ``by_e_index`` map (dict-comp =
    last-baton-wins) and scanned BOTH devices' elements. e_index spaces
    overlap across devices, so a correct desktop anchor was resolved to /
    bounced toward a mobile element.

    Live repro ``2026-06-12-d662a8d3`` (ethics, page-scope, both batons):
    desktop ``e166`` = ``$1,847.99`` (the strikethrough price — the correct
    anchor) while mobile ``e166`` = ``Quick view``. The pooled map let mobile
    e166 shadow desktop e166, falsely bouncing the factually-correct anchor.
    The fix scopes the check to a SINGLE baton chosen by the finding's device
    (page-scope ethics defaults to the desktop/primary baton).
    """

    def test_cross_device_collision_does_not_false_fire(self):
        # Page-scope ethics finding (no proposed_anchor → desktop default),
        # cites e166. Desktop e166 IS the quoted strikethrough price; mobile
        # e166 is an unrelated "Quick view". A mobile decoy (e200) also holds
        # the price string, so the pre-fix pooled scan would resolve the cited
        # e166 to mobile "Quick view", miss the quote, then BOUNCE to e200.
        f = _finding(
            cluster="ethics",
            device="page",
            element={"baton_index": "e166"},
            surface="other",
            surface_note="strikethrough price comparison",
            evidence_anchors=[{"type": "dom", "reference": "e166"}],
            observation=(
                'The strikethrough comparison shows "$1,847.99" as the prior '
                "price next to the sale figure on the Borla card — " + "x" * 25
            ),
        )
        desktop_baton = {
            "elements": [
                {"e_index": "e166", "text_content": "$1,847.99"},
                {"e_index": "e10", "text_content": "Add to Cart"},
            ]
        }
        mobile_baton = {
            "elements": [
                {"e_index": "e166", "text_content": "Quick view"},
                {"e_index": "e200", "text_content": "$1,847.99"},
            ]
        }
        violations = validate_business_rules(
            _emission([f], cluster="ethics", device="page"),
            desktop_baton=desktop_baton,
            mobile_baton=mobile_baton,
        )
        precedence = [v for v in violations if v.rule.startswith("baton_precedence")]
        self.assertEqual(
            precedence,
            [],
            "LG2: a page-scope finding correctly anchored to desktop e166 "
            "($1,847.99) must not be bounced by a colliding mobile e166 / "
            f"decoy. Got: {precedence}",
        )

    def test_other_device_element_cannot_satisfy_a_real_mismatch(self):
        # A genuinely mis-anchored DESKTOP finding: cites e166 (desktop
        # "Quick view") but quotes "Add to Cart", which lives at desktop e10.
        # Mobile e166 happens to be "Add to Cart" — pre-fix, the pooled
        # last-wins map resolved the cited e166 to the MOBILE element, which
        # matched the quote and silently SATISFIED (masked) the real desktop
        # mismatch. Scoped to desktop, the rule must still fire.
        f = _finding(
            element={"baton_index": "e166"},
            proposed_anchor={"kind": "element", "viewport": "desktop"},
            evidence_anchors=[{"type": "dom", "reference": "e166"}],
            observation=(
                'The "Add to Cart" control is the intended anchor here — '
                + "x" * 25
            ),
        )
        desktop_baton = {
            "elements": [
                {"e_index": "e166", "text_content": "Quick view"},
                {"e_index": "e10", "text_content": "Add to Cart"},
            ]
        }
        mobile_baton = {
            "elements": [
                {"e_index": "e166", "text_content": "Add to Cart"},
            ]
        }
        violations = validate_business_rules(
            _emission([f], cluster="ethics", device="page"),
            desktop_baton=desktop_baton,
            mobile_baton=mobile_baton,
        )
        rules = [v.rule for v in violations]
        self.assertIn(
            "baton_precedence_verbatim_anchor",
            rules,
            "LG2: scoping to the finding's device must not let the OTHER "
            "device's same-index element mask a real anchor mismatch. "
            f"Got rules: {rules}",
        )

    def test_single_device_emission_check_stays_active(self):
        # Regression guard for the fix's edge: a per-device emission passes
        # only ``baton`` (desktop/mobile None). The check must NOT be disabled
        # — a real mismatch there still fires (baton wins regardless of any
        # viewport hint on the finding).
        f = _finding(
            element={"baton_index": "e8"},
            proposed_anchor={"kind": "element", "viewport": "mobile"},
            observation='The product price renders as "$59.95" — ' + "x" * 25,
        )
        baton = {
            "elements": [
                {"e_index": "e7", "text_content": "$59.95"},
                {"e_index": "e8", "text_content": "Add to Cart"},
            ]
        }
        violations = validate_business_rules(_emission([f]), baton=baton)
        rules = [v.rule for v in violations]
        self.assertIn(
            "baton_precedence_verbatim_anchor",
            rules,
            "LG2: single-baton emissions must keep the precedence check "
            f"active regardless of a finding's viewport hint. Got: {rules}",
        )


class TestLG3VerbatimQuoteEdgePunctuation(unittest.TestCase):
    """LG3 (2026-06-12 live gate): ``_VERBATIM_QUOTE_PATTERN`` captures inner
    punctuation, so prose ending a sentence inside the quotes — ``"$1,847.99."``
    — yields the quote ``$1,847.99.`` (trailing period). That never substring-
    matches element text ``$1,847.99``, so the correct anchor (e166) was
    rejected and the check bounced to a wrong element.

    Fix: strip leading/trailing punctuation from each quote ONLY in the
    substring comparison loops (not at the ``_is_substantive_quote`` gate,
    where a stripped 9-char price would risk failing the substantive test).
    Internal punctuation stays intact — ``$1,847.99`` must remain ``$1,847.99``.
    """

    def test_trailing_punct_quote_matches_cited_element(self):
        # Correct anchor: e166 IS the bare strikethrough price. A decoy
        # sentence-element (e50) contains the price WITH a trailing period, so
        # pre-fix the period-bearing quote skips the correct e166 and bounces
        # to e50.
        f = _finding(
            element={"baton_index": "e166"},
            evidence_anchors=[{"type": "dom", "reference": "e166"}],
            observation=(
                'The strikethrough lists the prior price as "$1,847.99." next '
                "to the sale figure — " + "x" * 25
            ),
        )
        baton = {
            "elements": [
                {"e_index": "e166", "text_content": "$1,847.99"},
                {"e_index": "e50", "text_content": "Compare at $1,847.99. Limited time"},
            ]
        }
        violations = validate_business_rules(_emission([f]), baton=baton)
        precedence = [v for v in violations if v.rule.startswith("baton_precedence")]
        self.assertEqual(
            precedence,
            [],
            "LG3: a quote with a trailing period ('$1,847.99.') must still "
            "match the bare-price element it correctly anchors. Got: "
            f"{precedence}",
        )

    def test_mis_anchored_price_with_trailing_punct_still_flags(self):
        # Stripping must not disable the rule: a genuinely mis-anchored price
        # (cites e10 'Add to Cart', quotes the price) must still bounce to the
        # element that actually holds it.
        f = _finding(
            element={"baton_index": "e10"},
            evidence_anchors=[{"type": "dom", "reference": "e10"}],
            observation=(
                'The figure "$1,847.99." is the prior price but the cite '
                "points elsewhere — " + "x" * 25
            ),
        )
        baton = {
            "elements": [
                {"e_index": "e10", "text_content": "Add to Cart"},
                {"e_index": "e166", "text_content": "$1,847.99"},
            ]
        }
        violations = validate_business_rules(_emission([f]), baton=baton)
        rules = [v.rule for v in violations]
        self.assertIn(
            "baton_precedence_verbatim_anchor",
            rules,
            "LG3: stripping edge punctuation must not suppress real anchor "
            f"mismatches. Got rules: {rules}",
        )

    def test_internal_punctuation_preserved(self):
        # Quote "($1,847.99)." carries BOTH leading and trailing edge punct;
        # edge-only stripping yields "$1,847.99" (internal comma+decimal
        # intact) → matches the cited price element → no violation. A digit-
        # only decoy (e50 = "$184799 bundle") would be bounced to ONLY if the
        # fix wrongly stripped the internal comma+decimal too — so this test
        # turns red on an over-stripping regression while staying green for
        # the correct edge-only strip.
        f = _finding(
            element={"baton_index": "e166"},
            evidence_anchors=[{"type": "dom", "reference": "e166"}],
            observation=(
                'The card shows the crossed-out figure "($1,847.99)." beside '
                "the sale price — " + "x" * 25
            ),
        )
        baton = {
            "elements": [
                {"e_index": "e166", "text_content": "$1,847.99"},
                {"e_index": "e50", "text_content": "$184799 bundle"},
            ]
        }
        violations = validate_business_rules(_emission([f]), baton=baton)
        precedence = [v for v in violations if v.rule.startswith("baton_precedence")]
        self.assertEqual(
            precedence,
            [],
            "LG3: edge-only stripping must leave '$1,847.99' intact (internal "
            f"comma+decimal preserved), not bounce to a digit-only decoy. Got: {precedence}",
        )


class TestLG6PredicateMismatchRule(unittest.TestCase):
    """LG6 (= PR-97, 2026-06-12 live gate): a finding whose prose carries a
    numeric predicate ("over $X" / "under $X") must anchor an element whose
    price text satisfies it. Previously this was caught only post-hoc by the
    operator diagnostic (diagnose_engagement._predicate_mismatch); nothing
    bounced it at validation, so awdmods pricing F-16 ("9 of 10 prices OVER
    $1,766") shipped anchored to a $135.99 element.

    The runtime rule mirrors the diagnostic and is gated on BOTH an OVER/UNDER
    marker AND a $N threshold in title/observation/recommendation, so it never
    fires on non-pricing findings.
    """

    def test_over_threshold_anchored_to_cheaper_element_violates(self):
        f = _finding(
            title="No MSRP Anchor on Items Over $1,000",
            element={"baton_index": "e7"},
            evidence_anchors=[{"type": "dom", "reference": "e7"}],
            observation="Nine of ten featured prices sit over $1,000 with no MSRP anchor — "
            + "x" * 25,
        )
        baton = {"elements": [{"e_index": "e7", "text_content": "From $135.99"}]}
        violations = validate_business_rules(_emission([f]), baton=baton)
        rules = [v.rule for v in violations]
        self.assertIn("anchor_satisfies_numeric_predicate", rules)

    def test_over_threshold_anchored_to_qualifying_element_passes(self):
        f = _finding(
            title="No MSRP Anchor on Items Over $1,000",
            element={"baton_index": "e7"},
            evidence_anchors=[{"type": "dom", "reference": "e7"}],
            observation="Nine of ten featured prices sit over $1,000 with no MSRP anchor — "
            + "x" * 25,
        )
        baton = {"elements": [{"e_index": "e7", "text_content": "$1,899.00"}]}
        violations = validate_business_rules(_emission([f]), baton=baton)
        rules = [v.rule for v in violations]
        self.assertNotIn("anchor_satisfies_numeric_predicate", rules)

    def test_no_predicate_no_check(self):
        # Anchor has a price, but the prose carries no over/under predicate —
        # must not fire (gate on predicate presence).
        f = _finding(
            element={"baton_index": "e7"},
            evidence_anchors=[{"type": "dom", "reference": "e7"}],
            observation="The hero has no headline above the fold — " + "x" * 25,
        )
        baton = {"elements": [{"e_index": "e7", "text_content": "From $135.99"}]}
        violations = validate_business_rules(_emission([f]), baton=baton)
        rules = [v.rule for v in violations]
        self.assertNotIn("anchor_satisfies_numeric_predicate", rules)

    def test_absent_skips_check(self):
        f = _finding(
            title="Items Over $1,000 lack an MSRP anchor",
            element={"baton_index": "absent"},
            observation="Nine of ten featured prices sit over $1,000 — " + "x" * 25,
            evidence_anchors=[
                {"type": "visual", "reference": "section-1-mobile.jpg", "scroll_y": 100}
            ],
        )
        baton = {"elements": [{"e_index": "e7", "text_content": "$135.99"}]}
        violations = validate_business_rules(_emission([f]), baton=baton)
        rules = [v.rule for v in violations]
        self.assertNotIn("anchor_satisfies_numeric_predicate", rules)

    def test_contract_documents_the_predicate_rule(self):
        spec = (_REPO / "contracts" / "specialist-prompt-v2.md").read_text(encoding="utf-8")
        self.assertIn("anchor_satisfies_numeric_predicate", spec)

    def test_real_f16_engagement_case(self):
        """Pinned to the live mis-anchor on disk at
        docs/ecp/2026-06-12-d662a8d3/cluster-pricing-desktop.json (gitignored,
        so the real title / e90 text / threshold are baked in here): pricing
        F-16 "No MSRP Anchor on 9 of 10 Featured Prices" claims prices up to
        $1,766.00 but anchors e90 whose text is "Regular price From $135.99".
        The rule flags it; re-anchoring the set-level claim to absent is clean.
        """
        e90_text = "Regular price\n          \n            From $135.99\n          "
        obs = (
            "Across the ten Featured Collection product tiles from $19.99 through "
            "$1,766.00, only the Borla exhaust shows a compare-at strikethrough. "
            "The other nine tiles over $1,500 carry no MSRP anchor — " + "x" * 25
        )
        mis = _finding(
            title="No MSRP Anchor on 9 of 10 Featured Prices",
            element={"baton_index": "e90"},
            evidence_anchors=[{"type": "dom", "reference": "e90"}],
            observation=obs,
        )
        baton = {"elements": [{"e_index": "e90", "text_content": e90_text}]}
        rules = [
            v.rule
            for v in validate_business_rules(_emission([mis]), baton=baton)
        ]
        self.assertIn("anchor_satisfies_numeric_predicate", rules)

        # The correct fix — a set-level claim anchors absent at the section.
        fixed = _finding(
            title="No MSRP Anchor on 9 of 10 Featured Prices",
            element={"baton_index": "absent"},
            observation=obs,
            evidence_anchors=[
                {"type": "visual", "reference": "section-1.jpg", "scroll_y": 100}
            ],
        )
        fixed_rules = [
            v.rule for v in validate_business_rules(_emission([fixed]), baton=baton)
        ]
        self.assertNotIn("anchor_satisfies_numeric_predicate", fixed_rules)

    def test_competitor_price_in_prose_does_not_false_bounce(self):
        # Adversarial review 2026-07-08 #3: the threshold binds to the $ NEAREST
        # the predicate token, not max() over all amounts. A recommendation that
        # cites a larger competitor/MSRP price must not hijack the threshold and
        # bounce a correctly-anchored finding.
        f = _finding(
            title="Bundle priced over $200 with no value framing",
            element={"baton_index": "e7"},
            evidence_anchors=[{"type": "dom", "reference": "e7"}],
            observation="The bundle is priced over $200 but shows no anchor — " + "x" * 25,
            recommendation="Competitors charge $600 for a comparable kit; frame the saving.",
        )
        baton = {"elements": [{"e_index": "e7", "text_content": "$250.00"}]}
        rules = [v.rule for v in validate_business_rules(_emission([f]), baton=baton)]
        self.assertNotIn(
            "anchor_satisfies_numeric_predicate", rules,
            "$250 satisfies 'over $200'; the unrelated $600 competitor price must "
            "not be treated as the threshold (was max()-bounced pre-fix).",
        )

    def test_multi_price_element_with_a_qualifying_price_passes(self):
        # "over $X" is satisfied if ANY of the element's prices is over X — the
        # check compares the element's HIGHEST, not its first-listed price.
        f = _finding(
            title="Featured prices over $1,766 lack MSRP anchors",
            element={"baton_index": "e7"},
            evidence_anchors=[{"type": "dom", "reference": "e7"}],
            observation="Nine of ten featured prices sit over $1,766 with no anchor — " + "x" * 25,
        )
        baton = {"elements": [{"e_index": "e7", "text_content": "From $135.99 up to $1,800.00"}]}
        rules = [v.rule for v in validate_business_rules(_emission([f]), baton=baton)]
        self.assertNotIn("anchor_satisfies_numeric_predicate", rules)


if __name__ == "__main__":
    unittest.main()
