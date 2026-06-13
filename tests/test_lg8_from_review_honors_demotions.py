"""LG8 (2026-06-12 live gate) — --from-review must honor repaired confidence
demotions.

The placement-repair pass demotes a vision-rejected finding by setting
``hotspot_confidence`` to ``needs-manual-marker`` / ``section-match`` (status
stays ``needs_review``, no override fields). But _apply_review_state_to_slide_markers
only re-applied markers for *override-enabled* findings; a demotion-only review
state has no override-enabled findings, so the function early-returned and the
ORIGINAL auto-mapped marker survived — a demoted finding rendered at its
vision-rejected coordinates with high-confidence styling (18/18 in the repro).

The fix drops auto-mapped markers for any finding whose persisted
``hotspot_confidence`` is demoted, so it renders blank (manual queue) per
product.md §4.2 exact-tier-or-blank. Both the v2 and v1 builders are pinned.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.v2_html_builder import (  # noqa: E402
    _apply_review_state_to_slide_markers as apply_v2,
)
from report.html_builder import (  # noqa: E402
    _apply_review_state_to_slide_markers as apply_v1,
)

_REF = "trust-credibility/F-01"


def _refs(result: dict) -> set[str]:
    return {m.get("f_ref") for marks in result.values() for m in marks}


def _slide_markers() -> dict:
    return {0: [{"f_ref": _REF, "finding_index": 1, "x_pct": 12.0, "y_pct": 13.0,
                 "match_method": "e_index_lookup"}]}


def _review_state(confidence: str) -> dict:
    return {
        "slides": [{"slide_id": "s1"}],
        "markers": [],
        "findings": [{"f_ref": _REF, "status": "needs_review",
                      "hotspot_confidence": confidence}],
    }


def _findings() -> list[dict]:
    return [{"f_ref": _REF, "fid": "trust-credibility/F-01", "index": 1,
             "cluster": "trust-credibility", "cluster_index": 1}]


class TestLG8FromReviewHonorsDemotions(unittest.TestCase):
    def test_v2_demoted_finding_renders_blank(self):
        out = apply_v2(_slide_markers(), _review_state("needs-manual-marker"), _findings())
        self.assertNotIn(_REF, _refs(out),
                         "LG8: a demoted finding must drop its auto-marker (blank)")

    def test_v2_section_match_renders_blank(self):
        out = apply_v2(_slide_markers(), _review_state("section-match"), _findings())
        self.assertNotIn(_REF, _refs(out))

    def test_v2_exact_selector_marker_survives(self):
        # Positive control: a non-demoted finding keeps its auto-marker.
        out = apply_v2(_slide_markers(), _review_state("exact-selector"), _findings())
        self.assertIn(_REF, _refs(out))

    def test_v1_demoted_finding_renders_blank(self):
        out = apply_v1(_slide_markers(), _review_state("needs-manual-marker"), _findings())
        self.assertNotIn(_REF, _refs(out))

    def test_v1_exact_selector_marker_survives(self):
        out = apply_v1(_slide_markers(), _review_state("exact-selector"), _findings())
        self.assertIn(_REF, _refs(out))


if __name__ == "__main__":
    unittest.main()
