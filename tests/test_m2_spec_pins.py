"""M2 (2026-06-10) — spec-conformance pins for two unguarded surfaces.

Pin 1 — ten-cluster set (product.md §2.3 canonical list).
=========================================================
The constitution declares the canonical ten clusters at product.md §2.3
(lines ~60-62). Multiple runtime/schema surfaces re-encode that list
verbatim, but no test compared them back to the constitution. A reword
in product.md or a drift in any one surface used to land silently.
This pin parses the ten cluster slugs out of product.md and asserts
equality with three surfaces:

  - ``schema/finding-v1.json`` ``properties.cluster.enum`` (~30-42)
  - ``schema/cluster-emission-v1.json`` ``properties.cluster.enum``
    (~33-45)
  - ``scripts/dom_preprocess.py`` ``CLUSTERS_DEFAULT`` (~60-69)

Both schema enums legitimately include ``"ethics"`` on top of the ten
canonical clusters (the ethics subagent is a sibling of the cluster
specialists in v2). The test strips ``"ethics"`` before comparing to
keep the pin tight against §2.3 — drift in the ten or accidental
removal of ``"ethics"`` both surface as distinct failures.

Pin 2 — rendered-state allOf branch (visual-position-finding).
==============================================================
``schema/finding-v1.json`` ~602-632 enforces that FAIL/PARTIAL findings
whose observation makes an above-fold / below-fold / sticky / fixed
position / hidden-on-scroll claim MUST carry at least one visual (or
both) evidence_anchor with a scroll_y. This was added to close the
§18.2.3 vehicle-selector-position-error class — a finding that claims
"this CTA is below the fold" without a screenshot anchor is unfalsifiable
prose. Pre-M2 the allOf branch had zero test coverage, so a regression
that weakened or removed the rule would land green.

Two cases:
  - FAIL finding with an above-fold observation but only a ``dom`` anchor
    (no scroll_y) -> validation fails.
  - Same finding with a ``visual`` anchor carrying scroll_y -> validation
    passes.

Mixed-class style (unittest.TestCase) — both pytest and unittest
runners must discover it.
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

PRODUCT_MD = (REPO_ROOT / "product.md").read_text(encoding="utf-8")
FINDING_SCHEMA = json.loads(
    (REPO_ROOT / "schema" / "finding-v1.json").read_text(encoding="utf-8")
)
CLUSTER_EMISSION_SCHEMA = json.loads(
    (REPO_ROOT / "schema" / "cluster-emission-v1.json").read_text(encoding="utf-8")
)


def _parse_clusters_from_product_md() -> list[str]:
    """Extract the ten canonical cluster slugs from product.md §2.3.

    §2.3 renders the list as:
        `visual-cta` . `trust-credibility` . `pricing` . `checkout-flows` .
        `performance-ux` . `product-media` . `category-navigation` . `content-seo` .
        `post-purchase` . `audience`
    on three consecutive lines (separator char varies — middle dot, etc.).

    Parse strategy: locate the ``### 2.3`` heading, then collect every
    backticked slug until the next blank line that follows at least one
    slug. Ten in canonical order.
    """
    lines = PRODUCT_MD.splitlines()
    section_idx = next(
        (i for i, ln in enumerate(lines) if ln.strip().startswith("### 2.3")),
        None,
    )
    assert section_idx is not None, "product.md §2.3 heading not found"
    slugs: list[str] = []
    started = False
    for ln in lines[section_idx + 1:]:
        found = re.findall(r"`([a-z][a-z0-9-]*)`", ln)
        if found:
            slugs.extend(found)
            started = True
        elif started and not ln.strip():
            # Blank line AFTER we've started collecting marks end of
            # the list. The "backed by the full evidence-tiered..."
            # paragraph below would otherwise leak in via `Gold`/etc.
            break
    return slugs


# ---------------------------------------------------------------------------
# Pin 1 — ten-cluster set
# ---------------------------------------------------------------------------


class TestM2TenClusterSetPinned(unittest.TestCase):
    """One test, four surfaces pinned to product.md §2.3."""

    def test_ten_cluster_set_matches_constitution(self):
        product_md_clusters = _parse_clusters_from_product_md()

        # Sanity: §2.3 lists EXACTLY ten clusters in canonical order.
        # If product.md is reworded to add an 11th or drop one, this
        # tripwire fires before the per-surface comparisons so the
        # author sees the constitutional change spelled out.
        self.assertEqual(
            len(product_md_clusters),
            10,
            f"product.md §2.3 must list exactly 10 clusters; "
            f"parsed {product_md_clusters!r}",
        )
        self.assertEqual(
            product_md_clusters,
            [
                "visual-cta",
                "trust-credibility",
                "pricing",
                "checkout-flows",
                "performance-ux",
                "product-media",
                "category-navigation",
                "content-seo",
                "post-purchase",
                "audience",
            ],
            "product.md §2.3 canonical order drifted",
        )

        # finding-v1.json — strip 'ethics' (legitimate addition for the
        # ethics subagent) and compare the remainder.
        finding_clusters = list(
            FINDING_SCHEMA["properties"]["cluster"]["enum"]
        )
        self.assertIn(
            "ethics",
            finding_clusters,
            "finding-v1.json cluster enum must keep 'ethics' for the "
            "ethics subagent — its absence would be a separate "
            "regression, but we surface it here too.",
        )
        finding_ten = [c for c in finding_clusters if c != "ethics"]
        self.assertEqual(
            finding_ten,
            product_md_clusters,
            "finding-v1.json cluster enum (minus 'ethics') diverged from "
            "product.md §2.3",
        )

        # cluster-emission-v1.json — same shape.
        cluster_emission_clusters = list(
            CLUSTER_EMISSION_SCHEMA["properties"]["cluster"]["enum"]
        )
        self.assertIn(
            "ethics",
            cluster_emission_clusters,
            "cluster-emission-v1.json cluster enum must keep 'ethics'",
        )
        cluster_emission_ten = [
            c for c in cluster_emission_clusters if c != "ethics"
        ]
        self.assertEqual(
            cluster_emission_ten,
            product_md_clusters,
            "cluster-emission-v1.json cluster enum (minus 'ethics') "
            "diverged from product.md §2.3",
        )

        # dom_preprocess.py CLUSTERS_DEFAULT — runtime list, ordered.
        # Import lazily so an import-time error in dom_preprocess (which
        # pulls Pillow on some surfaces) is attributed to the test that
        # exercises it.
        from dom_preprocess import CLUSTERS_DEFAULT
        self.assertEqual(
            list(CLUSTERS_DEFAULT),
            product_md_clusters,
            "scripts/dom_preprocess.py CLUSTERS_DEFAULT diverged from "
            "product.md §2.3",
        )


# ---------------------------------------------------------------------------
# Pin 2 — finding-v1.json visual-position-finding allOf branch
# ---------------------------------------------------------------------------


def _visual_position_finding(
    *, with_visual_anchor: bool,
) -> dict:
    """Build a FAIL finding whose observation makes an above-fold claim.

    The allOf rule (~602-632) fires when verdict ∈ {FAIL, PARTIAL} AND
    observation matches the (above-fold|below-fold|sticky|fixed-position|
    hidden-on-scroll) regex. The 'then' branch requires
    evidence_anchors to contain at least one entry with type ∈
    {visual, both} and a scroll_y.

    To keep the test honest, we always include a dom anchor (so the
    minItems>=1 rule passes regardless), and only toggle whether a
    visual anchor with scroll_y is also present. That isolates the
    visual-position rule from the other allOf branches.
    """
    anchors = [
        {"type": "dom", "reference": "e7"},
    ]
    if with_visual_anchor:
        anchors.append(
            {
                "type": "visual",
                "reference": "section-2-desktop.jpg",
                "scroll_y": 1800,
                "viewport": "desktop",
            }
        )
    return {
        "cluster": "visual-cta",
        "device": "desktop",
        "local_id": 1,
        "verdict": "FAIL",
        "title": "Primary CTA is below the fold on desktop",
        "surface": "hero-cta",
        "element": {
            "baton_index": "e7",
            "text_content": "Buy Now",
            "role": "button",
        },
        "severity": "HIGH",
        "scope": "page",
        "effort": {"change_type": "copy", "change_scope": "single-file"},
        "evidence_anchors": anchors,
        "reference_citations": [
            {"source": "cta-visibility.md", "tier": "Silver"}
        ],
        # Observation explicitly carries the trigger phrase 'above-fold'
        # (the regex is case-insensitive and accepts space or hyphen).
        "observation": (
            "The primary CTA does not appear above-fold on the desktop "
            "viewport; users must scroll past the hero image to reach it."
        ),
        "recommendation": (
            "Move the primary CTA into the hero block so it renders "
            "above-fold at 1920x1080 with no scrolling required."
        ),
        "why_this_matters": (
            "Above-fold CTA visibility correlates with conversion lift "
            "in controlled tests."
        ),
        "evidence_tier": "Silver",
    }


class TestM2VisualPositionFindingPinned(unittest.TestCase):
    """The visual-position-finding allOf branch (finding-v1.json ~602-632)."""

    def setUp(self):
        self.validator = Draft202012Validator(FINDING_SCHEMA)

    def test_above_fold_claim_without_visual_anchor_fails_validation(self):
        finding = _visual_position_finding(with_visual_anchor=False)
        errors = [e.message for e in self.validator.iter_errors(finding)]
        # Sanity: the finding must trip the visual-position rule
        # specifically — not some unrelated allOf branch we accidentally
        # broke when constructing it.
        self.assertTrue(
            errors,
            "Schema should reject an above-fold claim without a visual "
            "anchor + scroll_y (visual-position-finding allOf branch, "
            "finding-v1.json ~602-632).",
        )

    def test_above_fold_claim_with_visual_anchor_validates(self):
        finding = _visual_position_finding(with_visual_anchor=True)
        errors = [e.message for e in self.validator.iter_errors(finding)]
        self.assertEqual(
            errors,
            [],
            f"Schema should accept the conforming visual-position "
            f"finding; got errors: {errors!r}",
        )


if __name__ == "__main__":
    unittest.main()
