"""Negative tests: business rules must not CRASH on malformed emission shapes.

business_rules.validate_business_rules runs *alongside* schema validation (the
caller in test-specialist.py collects schema errors but still runs the rules),
and its try/except only catches ValueError. So a TypeError/AttributeError from a
malformed LLM emission propagates and crashes the validator instead of being
reported through the retry path. These tests feed the malformed shapes the
adversarial review confirmed (findings 1-4, 8, 9) and assert the validator
returns a list rather than raising.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.business_rules import validate_business_rules, FindingBand  # noqa: E402

_BATON = {"elements": [{"e_index": "e1", "text_content": "Buy Now"}], "sections": []}


class TestMalformedFindingsContainer(unittest.TestCase):
    def test_findings_null_does_not_crash(self):
        r = validate_business_rules({"schema_version": 1, "status": "complete", "findings": None})
        self.assertIsInstance(r, list)

    def test_findings_single_object_does_not_crash(self):
        r = validate_business_rules(
            {"schema_version": 1, "status": "complete", "findings": {"0": {"verdict": "FAIL"}}}
        )
        self.assertIsInstance(r, list)

    def test_findings_scalar_entries_do_not_crash(self):
        r = validate_business_rules(
            {"schema_version": 1, "status": "complete", "findings": [123, "x", None]}
        )
        self.assertIsInstance(r, list)

    def test_finding_count_band_with_null_findings(self):
        r = validate_business_rules(
            {"schema_version": 1, "status": "complete", "findings": None},
            target_band=FindingBand(1, 5),
        )
        self.assertIsInstance(r, list)


class TestMalformedFindingFields(unittest.TestCase):
    def test_reference_citations_as_dict(self):
        em = {"schema_version": 1, "status": "complete", "findings": [
            {"verdict": "FAIL", "evidence_tier": "Bronze",
             "reference_citations": {"0": {"tier": "Gold"}}}]}
        self.assertIsInstance(validate_business_rules(em), list)

    def test_reference_citations_as_string_list(self):
        em = {"schema_version": 1, "status": "complete", "findings": [
            {"verdict": "FAIL", "evidence_tier": "Bronze",
             "reference_citations": ["Gold", "Silver"]}]}
        self.assertIsInstance(validate_business_rules(em), list)

    def test_element_as_list(self):
        em = {"schema_version": 1, "status": "complete", "findings": [
            {"verdict": "FAIL", "element": ["not", "a", "dict"]}]}
        self.assertIsInstance(validate_business_rules(em, baton=_BATON), list)

    def test_evidence_anchors_non_dict_entries(self):
        em = {"schema_version": 1, "status": "complete", "findings": [
            {"verdict": "FAIL", "element": {"baton_index": "e1"},
             "evidence_anchors": ["x", 123]}]}
        self.assertIsInstance(validate_business_rules(em, baton=_BATON), list)

    def test_title_null_in_absent_duplicates(self):
        f = {"verdict": "FAIL", "surface": "meta-tags",
             "element": {"baton_index": "absent"}, "title": None}
        em = {"schema_version": 1, "status": "complete", "findings": [dict(f), dict(f)]}
        self.assertIsInstance(validate_business_rules(em), list)


if __name__ == "__main__":
    unittest.main()
