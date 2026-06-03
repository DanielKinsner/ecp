"""Container-level malformed-input guards (Codex round-2 gate review).

The first round of type-guard fixes handled malformed *entries* (e.g.
findings: [123]) but not the *container itself* being a non-list scalar/object
(e.g. findings: 123). Iterating such a container raises before any per-entry
isinstance guard runs. These tests pin every such site across the surfaces the
review touched; all crash against the entry-only fix and pass after the
container coercion.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.business_rules import validate_business_rules  # noqa: E402
from assembly.canary_checks import check_ethics_findings_have_source_urls  # noqa: E402
from assembly.review_state import validate_review_state  # noqa: E402
from dom_preprocess import preprocess_device  # noqa: E402
from report.v2_html_builder import _build_evidence_anchors_html  # noqa: E402
from report.v2_loader import load_v2_priority_path  # noqa: E402


def _tmp(files: dict[str, object]) -> Path:
    d = Path(tempfile.mkdtemp(prefix="ecp-cont-"))
    for name, content in files.items():
        text = content if isinstance(content, str) else json.dumps(content)
        (d / name).write_text(text, encoding="utf-8")
    return d


class TestReviewStateScalarContainers(unittest.TestCase):
    def test_findings_scalar(self):
        self.assertIsInstance(
            validate_review_state({"findings": 123, "markers": [], "slides": []}), list)

    def test_markers_scalar(self):
        self.assertIsInstance(
            validate_review_state({"findings": [], "markers": 123, "slides": []}), list)


class TestCanaryEthicsScalarRoot(unittest.TestCase):
    def test_root_is_list(self):
        eng = _tmp({"ethics-findings.json": []})
        r = check_ethics_findings_have_source_urls(eng / "ethics-findings.json")
        self.assertIsInstance(r, dict)
        self.assertFalse(r["passed"])

    def test_findings_entry_non_dict(self):
        eng = _tmp({"ethics-findings.json": {"findings": ["bad"]}})
        r = check_ethics_findings_have_source_urls(eng / "ethics-findings.json")
        self.assertIsInstance(r, dict)


class TestEvidenceAnchorsContainer(unittest.TestCase):
    def test_anchors_list_of_non_dict(self):
        self.assertIsInstance(_build_evidence_anchors_html({"evidence_anchors": ["bad"]}), str)

    def test_anchors_is_dict(self):
        self.assertIsInstance(_build_evidence_anchors_html({"evidence_anchors": {"type": "visual"}}), str)


class TestBusinessRulesScalarArrays(unittest.TestCase):
    def test_reference_citations_scalar(self):
        em = {"schema_version": 1, "status": "complete",
              "findings": [{"verdict": "FAIL", "reference_citations": 123}]}
        self.assertIsInstance(validate_business_rules(em), list)

    def test_evidence_anchors_scalar(self):
        em = {"schema_version": 1, "status": "complete",
              "findings": [{"verdict": "FAIL", "element": {"baton_index": "e1"},
                            "evidence_anchors": 123}]}
        baton = {"elements": [{"e_index": "e1"}], "sections": []}
        self.assertIsInstance(validate_business_rules(em, baton=baton), list)


class TestDomPreprocessScalarContainers(unittest.TestCase):
    def test_sections_and_elements_scalar(self):
        eng = _tmp({
            "dom.html": "<html></html>",
            "baton.json": {"sections": 123, "elements": 123,
                           "viewport": {"width": 1440, "height": 900}, "screenshots": []},
        })
        self.assertIsInstance(preprocess_device(eng, "desktop", ["visual-cta"]), dict)


class TestV2LoaderScalarPriorityPath(unittest.TestCase):
    def test_priority_path_scalar(self):
        eng = _tmp({"synthesizer-emission-v1.json": {"priority_path": 123}})
        self.assertIsInstance(load_v2_priority_path(eng), list)


if __name__ == "__main__":
    unittest.main()
