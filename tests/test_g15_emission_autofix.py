"""G15 P1-3 regression: ethics-emission pre-validation autofix.

Three runs of catalogued failure modes
(``docs/ecp/2026-05-27-{b0051311,af72a2ae,52f53a53}`` lead-reflections)
inform what the autofix repairs:

- Path-form ``telemetry.reference_files_read`` entries
  (e.g., ``references/ethics-gate.md`` instead of bare filename).
- Duplicate ``(surface, baton_index, verdict)`` finding tuples.
- ``proposed_anchor.reason`` exceeding the 200-char schema cap.

Each repair has a "fires on bad input" + "no-op on clean input" pair,
plus an idempotency test (re-running autofix on the fixed output
produces no further repairs).

Pre-v1.2 the autofix also injected a default ``proposed_anchor`` on
absent findings that omitted one (the schema required it). After
product.md §4.2 v1.2 rulings A1+A2 (operationalized 2026-06-10),
``proposed_anchor`` is an OPTIONAL editor hint and absent findings
render BLANK — the injection is gone, and
``TestAbsentFindingsKeepNoProposedAnchor`` locks in the no-op behavior
+ confirms the unannotated absent finding still passes
schema/finding-v1.json validation.

unittest-style for ``python -m unittest discover`` runner compatibility.

Run:
    python -m unittest tests.test_g15_emission_autofix
"""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.emission_autofix import (  # noqa: E402
    PROPOSED_ANCHOR_REASON_MAX_LEN,
    autofix_emission,
)


def _make_finding(
    local_id: int = 1,
    surface: str = "primary-content-block",
    baton_index: str = "e7",
    verdict: str = "FAIL",
    **extras,
) -> dict:
    """Minimal finding shape with the dedup-key fields populated."""
    base = {
        "cluster": "trust-credibility",
        "device": "desktop",
        "local_id": local_id,
        "verdict": verdict,
        "title": f"Finding {local_id}",
        "surface": surface,
        "element": {"baton_index": baton_index, "text_content": "x", "role": "div"},
        "severity": "MEDIUM",
        "scope": "device",
        "effort": {"change_type": "copy", "change_scope": "single-file"},
        "confidence": 0.9,
        "observation": "obs",
        "recommendation": "rec",
        "why_this_matters": "why",
        "evidence_tier": "Silver",
    }
    base.update(extras)
    return base


def _emission(findings: list[dict] | None = None, **top_level) -> dict:
    base = {
        "schema_version": 1,
        "engagement_id": "test",
        "cluster": "trust-credibility",
        "device": "desktop",
        "started_at": "2026-05-27T00:00:00.000Z",
        "completed_at": "2026-05-27T00:01:00.000Z",
        "status": "complete",
        "findings": findings if findings is not None else [_make_finding()],
    }
    base.update(top_level)
    return base


# ---------------------------------------------------------------------------
# Repair 1 — path-form telemetry strip
# ---------------------------------------------------------------------------


class TestRepairTelemetryPaths(unittest.TestCase):
    def test_strips_references_prefix(self):
        emission = _emission(
            telemetry={
                "reference_files_read": [
                    "references/ethics-gate.md",
                    "references/evidence-tiers.md",
                ],
            },
        )
        fixed, repairs = autofix_emission(emission)
        self.assertEqual(
            fixed["telemetry"]["reference_files_read"],
            ["ethics-gate.md", "evidence-tiers.md"],
        )
        self.assertEqual(len(repairs), 2)
        for r in repairs:
            self.assertEqual(r["field"], "telemetry.reference_files_read[]")
            self.assertTrue(r["before"].startswith("references/"))
            self.assertFalse(r["after"].startswith("references/"))

    def test_no_op_on_clean_paths(self):
        emission = _emission(
            telemetry={
                "reference_files_read": ["ethics-gate.md", "evidence-tiers.md"],
            },
        )
        fixed, repairs = autofix_emission(emission)
        self.assertEqual(
            fixed["telemetry"]["reference_files_read"],
            ["ethics-gate.md", "evidence-tiers.md"],
        )
        self.assertEqual(repairs, [])

    def test_handles_missing_telemetry_block_gracefully(self):
        emission = _emission()  # no telemetry key
        fixed, repairs = autofix_emission(emission)
        self.assertNotIn("telemetry", fixed)
        # Other repairs may or may not fire (here: nothing else to repair).
        path_repairs = [r for r in repairs if r["field"].startswith("telemetry")]
        self.assertEqual(path_repairs, [])

    def test_handles_subdirectory_paths(self):
        """Multi-segment ``references/sub/file.md`` strips just the prefix."""
        emission = _emission(
            telemetry={"reference_files_read": ["references/sub/file.md"]},
        )
        fixed, _ = autofix_emission(emission)
        self.assertEqual(fixed["telemetry"]["reference_files_read"], ["sub/file.md"])


# ---------------------------------------------------------------------------
# Repair 2 — duplicate finding dedup
# ---------------------------------------------------------------------------


class TestRepairDuplicateFindings(unittest.TestCase):
    def test_drops_duplicate_keeps_earlier(self):
        f1 = _make_finding(local_id=1, surface="hero", baton_index="e3", verdict="FAIL")
        f2 = _make_finding(local_id=2, surface="hero", baton_index="e3", verdict="FAIL")
        f3 = _make_finding(local_id=3, surface="footer", baton_index="e9", verdict="PASS")
        fixed, repairs = autofix_emission(_emission([f1, f2, f3]))

        self.assertEqual(len(fixed["findings"]), 2)
        kept_ids = [f["local_id"] for f in fixed["findings"]]
        self.assertEqual(kept_ids, [1, 3], "Earlier finding (local_id=1) must win.")
        self.assertEqual(len(repairs), 1)
        self.assertEqual(repairs[0]["finding_local_id"], 2)
        self.assertEqual(repairs[0]["after"], "<dropped>")

    def test_no_op_on_unique_findings(self):
        findings = [
            _make_finding(local_id=1, surface="hero", baton_index="e3"),
            _make_finding(local_id=2, surface="hero", baton_index="e4"),
            _make_finding(local_id=3, surface="footer", baton_index="e9"),
        ]
        fixed, repairs = autofix_emission(_emission(findings))
        self.assertEqual(len(fixed["findings"]), 3)
        dedup_repairs = [r for r in repairs if r["field"] == "findings[]"]
        self.assertEqual(dedup_repairs, [])

    def test_missing_dedup_key_components_keeps_finding(self):
        """If surface/verdict/baton_index is missing, autofix does NOT
        accidentally collapse two such findings together — schema
        validation will flag the missing field separately."""
        f1 = _make_finding(local_id=1)
        f1.pop("surface")  # break the dedup key
        f2 = _make_finding(local_id=2)
        f2.pop("surface")
        fixed, repairs = autofix_emission(_emission([f1, f2]))
        self.assertEqual(len(fixed["findings"]), 2)


class TestAbsentFindingsNotDeduped(unittest.TestCase):
    """Regression (adversarial review 2026-07-08): autofix must NOT collapse
    two conceptually-distinct ``absent`` findings that merely share
    ``(surface, verdict)``.

    A meta-tags / structured-data cluster routinely emits several distinct
    *missing* findings on one surface — e.g. "no JSON-LD", "no OG image",
    "no GTIN" — all ``(surface='meta-tags', baton_index='absent',
    verdict='FAIL')`` but conceptually different. autofix runs BEFORE schema
    + business-rule validation; ``business_rules._check_within_emission_unique_anchors``
    only merges ``absent`` dupes when the title-token Jaccard >= 0.7 (that is
    the layer that decides real absent duplicates). If autofix keys ``absent``
    on the bare ``(surface, absent, verdict)`` tuple it silently drops the
    2nd..Nth distinct finding before that smarter check ever runs — a direct
    hit on product.md §0 "never silently misleading."
    """

    def test_distinct_absent_findings_not_dropped(self):
        f1 = _make_finding(local_id=1, surface="meta-tags", baton_index="absent",
                           verdict="FAIL", title="No JSON-LD product schema")
        f2 = _make_finding(local_id=2, surface="meta-tags", baton_index="absent",
                           verdict="FAIL", title="No Open Graph image tag")
        f3 = _make_finding(local_id=3, surface="meta-tags", baton_index="absent",
                           verdict="FAIL", title="No GTIN in structured data")
        fixed, repairs = autofix_emission(_emission([f1, f2, f3]))
        self.assertEqual(
            len(fixed["findings"]), 3,
            "Distinct absent findings on one surface must all survive autofix; "
            "business_rules' Jaccard check owns real absent-dedup, not autofix.",
        )
        dedup_repairs = [r for r in repairs if r["field"] == "findings[]"]
        self.assertEqual(dedup_repairs, [])

    def test_concrete_element_dupes_still_dropped(self):
        """The absent carve-out must NOT weaken concrete-element dedup: two
        findings on the SAME real baton element/surface/verdict are true
        duplicates and are still collapsed."""
        f1 = _make_finding(local_id=1, surface="hero", baton_index="e3", verdict="FAIL")
        f2 = _make_finding(local_id=2, surface="hero", baton_index="e3", verdict="FAIL")
        fixed, repairs = autofix_emission(_emission([f1, f2]))
        self.assertEqual(len(fixed["findings"]), 1)
        self.assertEqual([r["field"] for r in repairs if r["field"] == "findings[]"],
                         ["findings[]"])


# ---------------------------------------------------------------------------
# Repair 3 — proposed_anchor.reason length cap
# ---------------------------------------------------------------------------


class TestRepairOverlongProposedAnchorReason(unittest.TestCase):
    def test_truncates_overlong_reason(self):
        long_reason = (
            "Product image gallery renders above and left of the h1 title. "
            "Without reserved dimensions, images loading late shift the product "
            "title and price block downward — anchoring the finding above the "
            "product title marks the affected zone accurately."
        )
        self.assertGreater(len(long_reason), PROPOSED_ANCHOR_REASON_MAX_LEN)

        finding = _make_finding(local_id=1, baton_index="absent")
        finding["proposed_anchor"] = {
            "kind": "section",
            "placement": "section-bottom",
            "viewport": "desktop",
            "reason": long_reason,
        }
        fixed, repairs = autofix_emission(_emission([finding]))
        new_reason = fixed["findings"][0]["proposed_anchor"]["reason"]
        self.assertLessEqual(len(new_reason), PROPOSED_ANCHOR_REASON_MAX_LEN)
        self.assertTrue(new_reason.endswith("..."))
        # The repair record names the field correctly.
        cap_repairs = [r for r in repairs if r["field"] == "proposed_anchor.reason"]
        self.assertEqual(len(cap_repairs), 1)

    def test_no_op_on_short_reason(self):
        finding = _make_finding(local_id=1, baton_index="absent")
        finding["proposed_anchor"] = {
            "kind": "viewport",
            "placement": "above-fold-banner",
            "viewport": "both",
            "reason": "Short and within cap.",
        }
        fixed, repairs = autofix_emission(_emission([finding]))
        self.assertEqual(
            fixed["findings"][0]["proposed_anchor"]["reason"],
            "Short and within cap.",
        )
        cap_repairs = [r for r in repairs if r["field"] == "proposed_anchor.reason"]
        self.assertEqual(cap_repairs, [])

    def test_truncation_breaks_at_word_boundary(self):
        # Crafted so the cap falls mid-word; truncation should retreat to
        # the previous space.
        reason = "word " * 60  # well over the cap
        finding = _make_finding(local_id=1, baton_index="absent")
        finding["proposed_anchor"] = {
            "kind": "viewport",
            "placement": "above-fold-banner",
            "viewport": "both",
            "reason": reason,
        }
        fixed, _ = autofix_emission(_emission([finding]))
        new_reason = fixed["findings"][0]["proposed_anchor"]["reason"]
        # No mid-word break: the part before "..." must end at a whole word.
        before_ellipsis = new_reason[:-3]
        self.assertFalse(
            before_ellipsis.rstrip().endswith("wor"),
            "Truncation must not leave a partial word like 'wor'",
        )


# ---------------------------------------------------------------------------
# Absent findings + proposed_anchor: post-v1.2 NO injection happens
# ---------------------------------------------------------------------------


class TestAbsentFindingsKeepNoProposedAnchor(unittest.TestCase):
    """Per product.md §4.2 v1.2 (Phase-0 rulings A1+A2, operationalized
    2026-06-10), absence findings always render BLANK and ``proposed_anchor``
    is an OPTIONAL editor hint — not a placement directive. The autofix's
    former Repair 4 (inject a default section-bottom-overlay anchor on
    absent findings missing one) was the chief source of wrong-placement
    violations and has been removed. These tests lock in the no-op
    behavior and confirm an unannotated absent finding still passes
    schema validation."""

    def test_no_injection_on_absent_without_proposed_anchor(self):
        finding = _make_finding(local_id=1, baton_index="absent", device="desktop")
        # No proposed_anchor field at all.
        fixed, repairs = autofix_emission(_emission([finding]))
        self.assertNotIn(
            "proposed_anchor",
            fixed["findings"][0],
            "absent finding without a proposed_anchor must stay that way; "
            "the autofix MUST NOT inject a default — per product.md §4.2 "
            "v1.2 the renderer leaves the hotspot blank for the operator.",
        )
        inject_repairs = [r for r in repairs if r.get("field") == "proposed_anchor" and r.get("before") == "<missing>"]
        self.assertEqual(
            inject_repairs,
            [],
            "No 'proposed_anchor <missing>' repair record should be emitted.",
        )

    def test_absent_without_proposed_anchor_passes_real_schema_validator(self):
        """Schema/finding-v1.json must accept an absent finding with NO
        ``proposed_anchor`` field after the v1.2 prune. Pre-v1.2 the schema
        required ``proposed_anchor`` whenever ``baton_index='absent'``; that
        rule has been dropped. This guards against accidentally re-adding it."""
        import sys as _sys
        from pathlib import Path as _Path
        _sys.path.insert(0, str(_Path(__file__).resolve().parent.parent / "scripts"))
        from assembly.json_parser import get_validator

        finding = _make_finding(local_id=1, baton_index="absent", device="desktop")
        emission = _emission([finding])
        fixed, _ = autofix_emission(emission)

        validator = get_validator()
        errors = sorted(validator.iter_errors(fixed), key=lambda e: list(e.absolute_path))
        pa_errors = [
            f"{list(e.absolute_path)}: {e.message}"
            for e in errors
            if any(seg == "proposed_anchor" for seg in e.absolute_path)
        ]
        self.assertEqual(
            pa_errors,
            [],
            f"Schema should accept absent findings with no proposed_anchor. "
            f"Errors: {pa_errors}",
        )

    def test_existing_proposed_anchor_is_preserved_untouched(self):
        finding = _make_finding(local_id=1, baton_index="absent")
        finding["proposed_anchor"] = {
            "kind": "section",
            "section_index": 1,
            "placement": "section-bottom-overlay",
            "viewport": "desktop",
            "reason": "operator-authored placement",
        }
        fixed, repairs = autofix_emission(_emission([finding]))
        self.assertEqual(
            fixed["findings"][0]["proposed_anchor"]["reason"],
            "operator-authored placement",
            "Existing proposed_anchor must be preserved as an editor hint.",
        )
        inject_repairs = [r for r in repairs if r.get("before") == "<missing>"]
        self.assertEqual(inject_repairs, [])

    def test_no_proposed_anchor_added_on_non_absent_findings(self):
        finding = _make_finding(local_id=1, baton_index="e7")
        fixed, repairs = autofix_emission(_emission([finding]))
        self.assertNotIn(
            "proposed_anchor",
            fixed["findings"][0],
            "Findings whose element exists in the baton must not get a "
            "proposed_anchor injected.",
        )
        self.assertEqual(repairs, [])


# ---------------------------------------------------------------------------
# Cross-cutting: idempotency, immutability, combined cases
# ---------------------------------------------------------------------------


class TestAutofixCrossCutting(unittest.TestCase):
    def test_idempotent_on_already_clean_emission(self):
        emission = _emission(
            telemetry={"reference_files_read": ["ethics-gate.md"]},
        )
        fixed, repairs = autofix_emission(emission)
        self.assertEqual(repairs, [])
        # Second pass produces nothing further.
        fixed2, repairs2 = autofix_emission(fixed)
        self.assertEqual(repairs2, [])

    def test_idempotent_after_initial_repair(self):
        """After fix-pass-1 lands repairs, fix-pass-2 should be a no-op."""
        emission = _emission(
            telemetry={"reference_files_read": ["references/ethics-gate.md"]},
            findings=[
                _make_finding(local_id=1, baton_index="absent"),
                _make_finding(local_id=2, surface="hero", baton_index="e3"),
                _make_finding(local_id=3, surface="hero", baton_index="e3"),  # dup
            ],
        )
        fixed1, repairs1 = autofix_emission(emission)
        self.assertGreater(len(repairs1), 0, "First pass should produce repairs.")
        fixed2, repairs2 = autofix_emission(fixed1)
        self.assertEqual(
            repairs2,
            [],
            f"Second pass on already-fixed emission must be a no-op. "
            f"Re-fires: {repairs2}",
        )

    def test_does_not_mutate_input(self):
        emission = _emission(
            telemetry={"reference_files_read": ["references/ethics-gate.md"]},
        )
        before_snapshot = copy.deepcopy(emission)
        autofix_emission(emission)
        self.assertEqual(
            emission,
            before_snapshot,
            "autofix_emission must not mutate its input emission "
            "(deep-copy semantics).",
        )

    def test_combined_repairs_all_fire(self):
        """Single emission carrying every live repair-class; assert each of
        the three remaining repair classes fires on the same pass. The
        former Repair 4 (inject default proposed_anchor on absent) was
        removed in 2026-06-10 with the §4.2 v1.2 absence-blank rulings."""
        finding_absent = _make_finding(local_id=1, baton_index="absent")
        # finding_absent intentionally missing proposed_anchor — must NOT be
        # injected (post-v1.2: absences ship blank, operator places by hand).
        finding_hero_a = _make_finding(local_id=2, surface="hero", baton_index="e3")
        finding_hero_b = _make_finding(local_id=3, surface="hero", baton_index="e3")  # dup → repair 2
        # Distinct surface so dedup doesn't collapse finding_overlong into finding_absent.
        finding_overlong = _make_finding(local_id=4, surface="footer", baton_index="absent")
        finding_overlong["proposed_anchor"] = {
            "kind": "section",
            "section_index": 0,
            "placement": "section-bottom-overlay",
            "viewport": "desktop",
            "reason": "x" * (PROPOSED_ANCHOR_REASON_MAX_LEN + 50),  # repair 3 fires
        }
        emission = _emission(
            telemetry={"reference_files_read": ["references/ethics-gate.md"]},  # repair 1
            findings=[finding_absent, finding_hero_a, finding_hero_b, finding_overlong],
        )
        fixed, repairs = autofix_emission(emission)
        repair_fields = {r["field"] for r in repairs}
        self.assertIn("telemetry.reference_files_read[]", repair_fields)
        self.assertIn("findings[]", repair_fields)
        self.assertIn("proposed_anchor.reason", repair_fields)
        # The retired Repair 4 (proposed_anchor inject on absent) must NOT
        # fire anywhere in this combined emission.
        self.assertNotIn(
            "proposed_anchor",
            repair_fields,
            "Repair 4 (inject default proposed_anchor) was removed with the "
            "§4.2 v1.2 absence-blank rulings; absence findings now ship "
            "blank for the operator's manual queue.",
        )
        self.assertNotIn("proposed_anchor", fixed["findings"][0])


if __name__ == "__main__":
    unittest.main()
