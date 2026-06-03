"""Negative tests for the remaining P3 type guards.

Covers adversarial-review findings 22, 23, 28, 31:
- 22: finding_stability._tokenize crashed on a non-string (numeric) title.
- 23: visual_quality._ve crashed on a non-dict finding/marker element.
- 28: v2_loader.load_v2_priority_path crashed on non-dict stories / non-dict
  synthesizer payload.
- 31: validate-cluster-files._page_netloc_from_meta crashed on a non-dict
  meta.json or a non-dict "page".
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.finding_stability import _tokenize  # noqa: E402
from assembly.visual_quality import _ve  # noqa: E402
from report.v2_loader import load_v2_priority_path  # noqa: E402


def _load_validate_cluster_files():
    spec = importlib.util.spec_from_file_location(
        "validate_cluster_files", _REPO / "scripts" / "validate-cluster-files.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestTokenize(unittest.TestCase):
    def test_numeric_text_does_not_crash(self):
        self.assertEqual(_tokenize(123), set())


class TestVisualEvidence(unittest.TestCase):
    def test_non_dict_element_returns_none(self):
        self.assertIsNone(_ve("not-a-dict"))
        self.assertIsNone(_ve(123))


class TestPriorityPathStories(unittest.TestCase):
    def _eng(self, payload):
        eng = Path(tempfile.mkdtemp(prefix="ecp-pp-"))
        (eng / "synthesizer-emission-v1.json").write_text(json.dumps(payload), encoding="utf-8")
        return eng

    def test_non_dict_stories(self):
        eng = self._eng({"priority_path": ["a", 123, None]})
        self.assertIsInstance(load_v2_priority_path(eng), list)

    def test_non_dict_payload(self):
        eng = self._eng([1, 2, 3])
        self.assertIsInstance(load_v2_priority_path(eng), list)


class TestPageNetlocFromMeta(unittest.TestCase):
    def setUp(self):
        self.mod = _load_validate_cluster_files()

    def _eng(self, meta):
        eng = Path(tempfile.mkdtemp(prefix="ecp-vc-"))
        (eng / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
        return eng

    def test_meta_as_list(self):
        self.assertIsNone(self.mod._page_netloc_from_meta(self._eng([1, 2])))

    def test_page_as_string(self):
        self.assertIsNone(self.mod._page_netloc_from_meta(self._eng({"page": "x"})))


if __name__ == "__main__":
    unittest.main()
