"""Phase 6 ethics/legal enforcement batch (2026-06-10) — C18 + H2 + H3.

Three new canaries that close product.md §4.1 and §8 guardrails which had
no enforcement surface before this batch:

- C18: ``ethics_findings_hedge_law_on_adjacent`` — ADJACENT findings must
  hedge any law/regulation citation (product.md §4.1 misquoted-law rule).
- H2:  ``ethics_source_url_against_registry`` — every BLOCK/ADJACENT
  source_url must be in the Source Registry parsed at runtime from
  references/ethics-gate.md; vacated-rule URLs fail with a distinct
  message.
- H3:  ``recommendations_no_dark_patterns`` — no finding recommendation
  and no synth priority_path narrative may RECOMMEND a dark pattern
  ("add a countdown timer"); removal phrasing passes
  ("remove the fake countdown timer").

Run::

    python -m unittest tests.test_phase6_ethics_legal_canaries
    python -m pytest tests/test_phase6_ethics_legal_canaries.py
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.canary_checks import (  # noqa: E402
    check_ethics_findings_hedge_law_on_adjacent,
    check_ethics_source_url_against_registry,
    check_recommendations_no_dark_patterns,
    run_all_canaries,
)


# ---------------------------------------------------------------------------
# C18 — hedge-on-ADJACENT
# ---------------------------------------------------------------------------


class TestC18HedgeOnAdjacent(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, findings: list[dict]) -> Path:
        path = self.tmp_path / "ethics-findings.json"
        path.write_text(json.dumps({"findings": findings}), encoding="utf-8")
        return path

    def test_missing_file_skips(self):
        result = check_ethics_findings_hedge_law_on_adjacent(
            self.tmp_path / "does-not-exist.json"
        )
        self.assertTrue(result["passed"])
        self.assertIn("skipped", result["summary"])

    def test_adjacent_finding_unhedged_law_fails(self):
        # Pre-fix fixture shape: ADJACENT finding citing FTC 16 CFR 233.1
        # with no hedge phrasing.
        path = self._write([
            {
                "local_id": 1,
                "ethics_state": "ADJACENT",
                "title": "X",
                "observation": "Strikethrough $469.50 needs documented prior-selling-price evidence under FTC 16 CFR 233.1.",
                "recommendation": "Provide pricing records.",
                "why_this_matters": "Unsupported reference prices are deceptive under FTC Act § 5.",
            }
        ])
        result = check_ethics_findings_hedge_law_on_adjacent(path)
        self.assertFalse(result["passed"], result["summary"])
        self.assertEqual(result["detail"]["adjacent_total"], 1)
        self.assertEqual(len(result["detail"]["unhedged"]), 1)
        self.assertEqual(result["detail"]["unhedged"][0]["f_ref"], "ethics F-01")

    def test_adjacent_finding_hedged_law_passes(self):
        # The fix the fixture takes: weave "may implicate ... — verify"
        # into the prose. The canonical hedge plus any of the alternate
        # tokens listed in _HEDGE_TOKENS all satisfy the contract.
        path = self._write([
            {
                "local_id": 1,
                "ethics_state": "ADJACENT",
                "title": "X",
                "observation": "Strikethrough $469.50 may implicate FTC 16 CFR 233.1 — verify documentation.",
                "recommendation": "Provide pricing records; consult counsel if borderline.",
                "why_this_matters": "Unsupported reference prices may appear deceptive under FTC Act § 5 — verify before launch.",
            }
        ])
        result = check_ethics_findings_hedge_law_on_adjacent(path)
        self.assertTrue(result["passed"], result["summary"])
        self.assertEqual(result["detail"]["adjacent_total"], 1)

    def test_adjacent_finding_no_law_citation_passes(self):
        # ADJACENT findings that don't cite any law at all are fine —
        # nothing to hedge.
        path = self._write([
            {
                "local_id": 1,
                "ethics_state": "ADJACENT",
                "title": "X",
                "observation": "Strikethrough price lacks supporting documentation.",
                "recommendation": "Provide pricing records.",
                "why_this_matters": "Unsupported reference prices erode shopper trust.",
            }
        ])
        result = check_ethics_findings_hedge_law_on_adjacent(path)
        self.assertTrue(result["passed"], result["summary"])

    def test_block_finding_unhedged_law_passes(self):
        # BLOCK findings are explicitly UNAFFECTED by the hedge rule —
        # they SHOULD be direct (contracts/ethics-subagent-v2.md voice
        # contract).
        path = self._write([
            {
                "local_id": 1,
                "ethics_state": "BLOCK",
                "title": "Y",
                "observation": "The fabricated countdown timer violates FTC Act § 5.",
                "recommendation": "Remove the timer.",
                "why_this_matters": "FTC Section 5 prohibits fabricated urgency.",
            }
        ])
        result = check_ethics_findings_hedge_law_on_adjacent(path)
        self.assertTrue(result["passed"], result["summary"])

    def test_mixed_states_only_adjacent_fires(self):
        path = self._write([
            {
                "local_id": 1,
                "ethics_state": "BLOCK",
                "observation": "violates FTC Act § 5",
                "recommendation": "remove the offending widget",
                "why_this_matters": "FTC § 5",
            },
            {
                "local_id": 2,
                "ethics_state": "ADJACENT",
                "observation": "May implicate GDPR — verify.",  # hedged
                "recommendation": "Confirm consent banner copy.",
                "why_this_matters": "GDPR Art 7 — verify.",
            },
            {
                "local_id": 3,
                "ethics_state": "ADJACENT",
                "observation": "GDPR requires opt-in.",  # UNHEDGED
                "recommendation": "Get consent.",
                "why_this_matters": "GDPR Art 6.",
            },
        ])
        result = check_ethics_findings_hedge_law_on_adjacent(path)
        self.assertFalse(result["passed"], result["summary"])
        f_refs = [u["f_ref"] for u in result["detail"]["unhedged"]]
        self.assertIn("ethics F-03", f_refs)
        self.assertNotIn("ethics F-01", f_refs)
        self.assertNotIn("ethics F-02", f_refs)


# ---------------------------------------------------------------------------
# H2 — source_url against registry + vacated tracker
# ---------------------------------------------------------------------------


class TestH2SourceUrlAgainstRegistry(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, findings: list[dict]) -> Path:
        path = self.tmp_path / "ethics-findings.json"
        path.write_text(json.dumps({"findings": findings}), encoding="utf-8")
        return path

    def test_missing_file_skips(self):
        result = check_ethics_source_url_against_registry(
            self.tmp_path / "does-not-exist.json"
        )
        self.assertTrue(result["passed"])
        self.assertIn("skipped", result["summary"])

    def test_registry_url_passes(self):
        # FTC Act Section 5 — verbatim from references/ethics-gate.md Source Registry
        path = self._write([
            {
                "local_id": 1,
                "ethics_state": "BLOCK",
                "title": "X",
                "source_url": "https://www.law.cornell.edu/uscode/text/15/45",
                "observation": "x",
                "recommendation": "x",
                "why_this_matters": "x",
            }
        ])
        result = check_ethics_source_url_against_registry(path)
        self.assertTrue(result["passed"], result["summary"])

    def test_invented_url_fails(self):
        path = self._write([
            {
                "local_id": 1,
                "ethics_state": "BLOCK",
                "title": "X",
                "source_url": "https://example.invalid/made-up-rule",
                "observation": "x",
                "recommendation": "x",
                "why_this_matters": "x",
            }
        ])
        result = check_ethics_source_url_against_registry(path)
        self.assertFalse(result["passed"], result["summary"])
        self.assertEqual(len(result["detail"]["not_in_registry"]), 1)
        self.assertEqual(len(result["detail"]["vacated_hits"]), 0)
        self.assertIn("not in Source Registry", result["summary"])

    def test_vacated_url_fails_with_distinct_message(self):
        # FTC Click-to-Cancel — VACATED Jul 8, 2025 per the Vacated Rules
        # Tracker in references/ethics-gate.md.
        path = self._write([
            {
                "local_id": 1,
                "ethics_state": "BLOCK",
                "title": "X",
                "source_url": "https://www.ecfr.gov/current/title-16/chapter-I/subchapter-D/part-425",
                "observation": "x",
                "recommendation": "x",
                "why_this_matters": "x",
            }
        ])
        result = check_ethics_source_url_against_registry(path)
        self.assertFalse(result["passed"], result["summary"])
        self.assertEqual(len(result["detail"]["vacated_hits"]), 1)
        self.assertEqual(len(result["detail"]["not_in_registry"]), 0)
        self.assertIn("VACATED", result["summary"])

    def test_url_normalization_trailing_slash(self):
        # The registry URL has no trailing slash; tolerate findings that
        # add one.
        path = self._write([
            {
                "local_id": 1,
                "ethics_state": "BLOCK",
                "title": "X",
                "source_url": "https://www.law.cornell.edu/uscode/text/15/45/",
                "observation": "x",
                "recommendation": "x",
                "why_this_matters": "x",
            }
        ])
        result = check_ethics_source_url_against_registry(path)
        self.assertTrue(result["passed"], result["summary"])

    def test_clear_finding_with_no_url_unaffected(self):
        path = self._write([
            {"local_id": 1, "ethics_state": "CLEAR", "title": "x"}
        ])
        result = check_ethics_source_url_against_registry(path)
        self.assertTrue(result["passed"], result["summary"])
        self.assertEqual(result["detail"]["total_actionable"], 0)


# ---------------------------------------------------------------------------
# H3 — recommendations / priority-path stories must not recommend dark patterns
# ---------------------------------------------------------------------------


class TestH3RecommendationsNoDarkPatterns(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.eng = Path(self.tmp.name) / "engagement"
        self.eng.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _write_cluster(self, cluster: str, device: str, findings: list[dict]) -> Path:
        path = self.eng / f"cluster-{cluster}-{device}.json"
        path.write_text(
            json.dumps({"cluster": cluster, "device": device, "findings": findings}),
            encoding="utf-8",
        )
        return path

    def _write_synth(self, stories: list[dict]) -> Path:
        path = self.eng / "synthesizer-emission-v1.json"
        path.write_text(json.dumps({"priority_path": stories}), encoding="utf-8")
        return path

    def test_empty_engagement_passes(self):
        result = check_recommendations_no_dark_patterns(self.eng)
        self.assertTrue(result["passed"], result["summary"])
        self.assertEqual(result["detail"]["sources_scanned"], 0)

    def test_add_countdown_timer_fails(self):
        # The canonical product.md §8 violation — recommendation that
        # explicitly tells the operator to add a fabricated urgency widget.
        self._write_cluster("pricing", "desktop", [
            {
                "local_id": 1,
                "title": "x",
                "recommendation": "Add a countdown timer that resets per visit to boost urgency.",
            }
        ])
        result = check_recommendations_no_dark_patterns(self.eng)
        self.assertFalse(result["passed"], result["summary"])
        self.assertEqual(len(result["detail"]["violations"]), 1)
        v = result["detail"]["violations"][0]
        self.assertIn("countdown", v["matched_pattern"].lower())

    def test_remove_countdown_passes(self):
        # Removal recommendations are explicitly ALLOWED — the false-
        # positive control product.md §8 demands.
        self._write_cluster("pricing", "desktop", [
            {
                "local_id": 1,
                "title": "x",
                "recommendation": "Remove the misleading countdown timer; replace with a 'Limited time' badge if the sale window is genuine.",
            }
        ])
        result = check_recommendations_no_dark_patterns(self.eng)
        self.assertTrue(result["passed"], result["summary"])

    def test_without_exclusion_phrase_passes(self):
        # "display X WITHOUT <dark pattern>" opposes the pattern — the term is
        # the object of an exclusion, not a recommendation (review defect #4).
        self._write_cluster("trust-credibility", "desktop", [
            {
                "local_id": 1,
                "title": "x",
                "recommendation": "Display the actual review count without filtering out negative reviews, so the rating reflects the full distribution.",
            }
        ])
        result = check_recommendations_no_dark_patterns(self.eng)
        self.assertTrue(result["passed"], result["summary"])

    def test_clean_recommendation_passes(self):
        self._write_cluster("pricing", "desktop", [
            {
                "local_id": 1,
                "title": "x",
                "recommendation": "Surface the existing free-shipping threshold on the price block so shoppers can see total cost at a glance.",
            }
        ])
        result = check_recommendations_no_dark_patterns(self.eng)
        self.assertTrue(result["passed"], result["summary"])
        self.assertEqual(result["detail"]["sources_scanned"], 1)

    def test_pre_check_box_fails(self):
        self._write_cluster("checkout-flows", "mobile", [
            {
                "local_id": 7,
                "title": "x",
                "recommendation": "Pre-check the newsletter opt-in box so signup volume rises.",
            }
        ])
        result = check_recommendations_no_dark_patterns(self.eng)
        self.assertFalse(result["passed"], result["summary"])

    def test_hide_the_fee_fails(self):
        self._write_cluster("pricing", "desktop", [
            {
                "local_id": 3,
                "title": "x",
                "recommendation": "Hide the convenience fee until the final review screen to keep CTR high.",
            }
        ])
        result = check_recommendations_no_dark_patterns(self.eng)
        self.assertFalse(result["passed"], result["summary"])

    def test_synth_priority_path_narrative_scanned(self):
        # Synth Priority Path stories are dev-handoff prose too — they get
        # the same lint pass as per-finding recommendations.
        self._write_synth([
            {
                "mode": "bundle",
                "title": "Boost urgency",
                "narrative": "Add a countdown timer to the price block to lift conversion.",
                "f_refs": ["pricing F-01"],
            }
        ])
        result = check_recommendations_no_dark_patterns(self.eng)
        self.assertFalse(result["passed"], result["summary"])
        self.assertTrue(
            any(v["source"].startswith("priority_path[")
                for v in result["detail"]["violations"]),
            result["detail"],
        )

    def test_ethics_findings_recommendation_scanned(self):
        # The ethics subagent's own recommendation field must also clear
        # §8 — if the ethics emission tells the operator to ADD a dark
        # pattern, the canary fires.
        (self.eng / "ethics-findings.json").write_text(
            json.dumps({"findings": [
                {
                    "local_id": 1,
                    "ethics_state": "ADJACENT",
                    "recommendation": "Implement a countdown timer that resets each visit.",
                }
            ]}),
            encoding="utf-8",
        )
        result = check_recommendations_no_dark_patterns(self.eng)
        self.assertFalse(result["passed"], result["summary"])

    def test_describes_dark_pattern_without_recommending_passes(self):
        # Observations / narratives describing the dark pattern without an
        # add-shaped verb are fine — only recommend-voice fires.
        self._write_synth([
            {
                "mode": "bundle",
                "title": "Why no countdown",
                "narrative": "The page does not use a fabricated countdown timer. This is the correct choice.",
                "f_refs": ["pricing F-01"],
            }
        ])
        result = check_recommendations_no_dark_patterns(self.eng)
        self.assertTrue(result["passed"], result["summary"])


# ---------------------------------------------------------------------------
# Contract grep-guard for the ADJACENT carve-out text in the subagent contract
# ---------------------------------------------------------------------------


class TestEthicsSubagentContractContainsAdjacentCarveOut(unittest.TestCase):
    """The hedge-on-ADJACENT canary depends on the ethics subagent contract
    actually instructing subagents to hedge. If a future edit drops the
    carve-out, the canary becomes a trap (subagents emit unhedged prose,
    every audit fires the canary, operators learn to ignore it). This
    grep-guard asserts the carve-out language is present so the contract
    update and the canary stay in lockstep."""

    def test_contract_has_adjacent_carve_out(self):
        contract = (
            _REPO / "contracts" / "ethics-subagent-v2.md"
        ).read_text(encoding="utf-8")
        # Two load-bearing phrases the carve-out paragraph must contain.
        # If a future edit reorganizes the contract, search-and-replace
        # may break the wording — this guard catches it.
        self.assertIn("ADJACENT carve-out", contract)
        self.assertIn("may implicate", contract)
        # Voice rule still names BLOCK as the direct-voice case, so the
        # rule keeps differentiating BLOCK from ADJACENT.
        self.assertIn("BLOCK", contract)


# ---------------------------------------------------------------------------
# run_all_canaries wiring — all three new canaries appear in results
# ---------------------------------------------------------------------------


class TestPhase6CanariesWiredIntoRunAll(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.eng = Path(self.tmp.name) / "docs" / "ecp" / "test-eng"
        self.eng.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_all_three_phase6_canaries_present(self):
        # Clean ethics + clean recommendations — the three Phase 6 canaries
        # should each PASS regardless of whether the older infra canaries
        # (element_index_match_rate etc.) have data to evaluate on this
        # minimal fixture.
        (self.eng / "ethics-findings.json").write_text(
            json.dumps({"findings": [
                {"local_id": 1, "ethics_state": "CLEAR", "title": "x"},
            ]}),
            encoding="utf-8",
        )
        out = run_all_canaries(self.eng, include_visual_quality=False)
        names = [r["name"] for r in out["results"]]
        self.assertIn("ethics_findings_hedge_law_on_adjacent", names)
        self.assertIn("ethics_source_url_against_registry", names)
        self.assertIn("recommendations_no_dark_patterns", names)
        by_name = {r["name"]: r for r in out["results"]}
        self.assertTrue(by_name["ethics_findings_hedge_law_on_adjacent"]["passed"])
        self.assertTrue(by_name["ethics_source_url_against_registry"]["passed"])
        self.assertTrue(by_name["recommendations_no_dark_patterns"]["passed"])

    def test_unhedged_adjacent_propagates_failure(self):
        (self.eng / "ethics-findings.json").write_text(
            json.dumps({"findings": [
                {
                    "local_id": 1,
                    "ethics_state": "ADJACENT",
                    "title": "x",
                    "source_url": "https://www.law.cornell.edu/uscode/text/15/45",
                    "observation": "GDPR Art 6 requires explicit opt-in here.",
                    "recommendation": "Add a consent banner.",
                    "why_this_matters": "GDPR Art 6.",
                },
            ]}),
            encoding="utf-8",
        )
        out = run_all_canaries(self.eng, include_visual_quality=False)
        self.assertFalse(out["all_passed"])
        by_name = {r["name"]: r for r in out["results"]}
        self.assertFalse(by_name["ethics_findings_hedge_law_on_adjacent"]["passed"])

    def test_dark_pattern_recommendation_propagates_failure(self):
        (self.eng / "ethics-findings.json").write_text(
            json.dumps({"findings": [
                {"local_id": 1, "ethics_state": "CLEAR", "title": "x"},
            ]}),
            encoding="utf-8",
        )
        (self.eng / "cluster-pricing-desktop.json").write_text(
            json.dumps({"cluster": "pricing", "device": "desktop", "findings": [
                {
                    "local_id": 1,
                    "title": "x",
                    "recommendation": "Add a countdown timer that resets each visit to boost urgency.",
                }
            ]}),
            encoding="utf-8",
        )
        out = run_all_canaries(self.eng, include_visual_quality=False)
        self.assertFalse(out["all_passed"])
        by_name = {r["name"]: r for r in out["results"]}
        self.assertFalse(by_name["recommendations_no_dark_patterns"]["passed"])


if __name__ == "__main__":
    unittest.main()
