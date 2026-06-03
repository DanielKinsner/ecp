"""Negative tests: dom_preprocess tolerates malformed baton/meta shapes.

Covers adversarial-review findings 17, 24, 25:
- 24: for el in elements / for sec in baton_sections crashed when the baton
  had "elements": null / "sections": null (dict.get default doesn't fire on
  an explicit null).
- 17: a non-dict section entry crashed sec.get() in the per-cluster loop.
- 25: _resolve_clusters returned a non-list clusters_used verbatim (a string),
  which downstream callers then char-expanded.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from dom_preprocess import preprocess_device, _resolve_clusters  # noqa: E402

_VIEWPORT = {"width": 1440, "height": 900}


def _engagement(baton: dict) -> Path:
    tmp = tempfile.mkdtemp(prefix="ecp-dom-")
    eng = Path(tmp)
    (eng / "dom.html").write_text("<html><body><main></main></body></html>", encoding="utf-8")
    (eng / "baton.json").write_text(json.dumps(baton), encoding="utf-8")
    return eng


class TestPreprocessMalformedBaton(unittest.TestCase):
    def test_null_sections_and_elements(self):
        eng = _engagement({"sections": None, "elements": None,
                           "viewport": _VIEWPORT, "screenshots": []})
        result = preprocess_device(eng, "desktop", ["visual-cta"])
        self.assertIsInstance(result, dict)

    def test_non_dict_section_entry(self):
        eng = _engagement({"sections": [123, {"label": "hero", "slug": "hero"}],
                           "elements": [], "viewport": _VIEWPORT, "screenshots": []})
        result = preprocess_device(eng, "desktop", ["visual-cta"])
        self.assertIsInstance(result, dict)


class TestResolveClusters(unittest.TestCase):
    def test_string_clusters_used_falls_back_to_list(self):
        tmp = tempfile.mkdtemp(prefix="ecp-meta-")
        eng = Path(tmp)
        (eng / "meta.json").write_text(json.dumps({"clusters_used": "visual-cta"}), encoding="utf-8")
        result = _resolve_clusters(eng)
        # Pre-fix returned the raw string "visual-cta" (not a list).
        self.assertIsInstance(result, list)


if __name__ == "__main__":
    unittest.main()
