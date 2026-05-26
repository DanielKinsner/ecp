"""v2 unit tests: assembly.finding_stability (Phase J substantially-similar metric).

Two tiers of tests:

1. **Pure-Python helpers** — Jaccard, severity-distance, Levenshtein.
   Fast (<1s), no model load, no network access.

2. **Embedding helpers** — prose_cosine_similarity, semscore_document,
   compare_findings_stability with embeddings enabled. Loads
   ``all-MiniLM-L6-v2`` once via ``setUpClass``; first run on a fresh
   machine downloads the ~80MB model from HuggingFace
   (cached under ~/.cache/huggingface/ thereafter). Skipped if
   sentence-transformers isn't importable.

Run all:
    python -m unittest tests.test_v2_finding_stability

Run only fast tier:
    python -m unittest tests.test_v2_finding_stability.TestJaccard \\
        tests.test_v2_finding_stability.TestSeverity \\
        tests.test_v2_finding_stability.TestLevenshtein \\
        tests.test_v2_finding_stability.TestStructuralOnly
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.finding_stability import (  # noqa: E402
    _index_by_ref,
    _load_findings,
    _split_sentences,
    _tokenize,
    compare_findings_stability,
    diff_engagements,
    levenshtein_distance,
    levenshtein_ratio,
    severity_distance,
    severity_rank,
    title_token_set_jaccard,
)


# ---------------------------------------------------------------------------
# Pure-Python helpers (no model required)
# ---------------------------------------------------------------------------


class TestTokenize(unittest.TestCase):
    def test_lowercase_alphanumeric(self):
        self.assertEqual(_tokenize("Hero CTA Button"), {"hero", "cta", "button"})

    def test_punctuation_dropped(self):
        self.assertEqual(_tokenize("Add-to-Cart!"), {"add", "to", "cart"})

    def test_numbers_kept(self):
        self.assertEqual(_tokenize("Section 3 — header"), {"section", "3", "header"})

    def test_empty_input(self):
        self.assertEqual(_tokenize(""), set())
        self.assertEqual(_tokenize(None or ""), set())


class TestJaccard(unittest.TestCase):
    def test_identical_titles(self):
        self.assertEqual(
            title_token_set_jaccard("Hero CTA Color", "Hero CTA Color"),
            1.0,
        )

    def test_case_insensitive(self):
        self.assertEqual(
            title_token_set_jaccard("Hero CTA Color", "HERO cta COLOR"),
            1.0,
        )

    def test_punctuation_ignored(self):
        self.assertEqual(
            title_token_set_jaccard("Add-to-Cart Button", "Add to Cart Button"),
            1.0,
        )

    def test_partial_overlap(self):
        # {hero, cta, color} vs {hero, cta, contrast} → 2/4 = 0.5
        self.assertAlmostEqual(
            title_token_set_jaccard("Hero CTA Color", "Hero CTA Contrast"),
            0.5,
        )

    def test_no_overlap(self):
        self.assertEqual(
            title_token_set_jaccard("Privacy Policy Footer", "Hero CTA Color"),
            0.0,
        )

    def test_both_empty(self):
        self.assertEqual(title_token_set_jaccard("", ""), 1.0)

    def test_one_empty(self):
        self.assertEqual(title_token_set_jaccard("Hero CTA", ""), 0.0)
        self.assertEqual(title_token_set_jaccard("", "Hero CTA"), 0.0)

    def test_above_default_threshold(self):
        # Real-world: synthesizer sometimes adds/drops a determiner.
        # "ATC Button Color" vs "The ATC Button Color"
        # {atc, button, color} vs {the, atc, button, color} → 3/4 = 0.75
        result = title_token_set_jaccard(
            "ATC Button Color", "The ATC Button Color"
        )
        self.assertGreaterEqual(result, 0.7)


class TestSeverity(unittest.TestCase):
    def test_known_ranks(self):
        self.assertEqual(severity_rank("CRITICAL"), 4)
        self.assertEqual(severity_rank("HIGH"), 3)
        self.assertEqual(severity_rank("MEDIUM"), 2)
        self.assertEqual(severity_rank("LOW"), 1)

    def test_lowercase_normalized(self):
        self.assertEqual(severity_rank("high"), 3)
        self.assertEqual(severity_rank("Low"), 1)

    def test_unknown_severity_returns_zero(self):
        self.assertEqual(severity_rank("urgent"), 0)
        self.assertEqual(severity_rank(""), 0)
        self.assertEqual(severity_rank(None or ""), 0)

    def test_distance_identical(self):
        self.assertEqual(severity_distance("HIGH", "HIGH"), 0)

    def test_distance_adjacent(self):
        self.assertEqual(severity_distance("CRITICAL", "HIGH"), 1)
        self.assertEqual(severity_distance("HIGH", "MEDIUM"), 1)
        self.assertEqual(severity_distance("MEDIUM", "LOW"), 1)

    def test_distance_max(self):
        # 4 - 1 = 3
        self.assertEqual(severity_distance("CRITICAL", "LOW"), 3)

    def test_distance_with_unknown(self):
        # Unknown ranks as 0; HIGH is 3; distance is 3 (fails default threshold)
        self.assertEqual(severity_distance("HIGH", "URGENT"), 3)


class TestLevenshtein(unittest.TestCase):
    def test_identical(self):
        self.assertEqual(levenshtein_distance("hello", "hello"), 0)
        self.assertEqual(levenshtein_ratio("hello", "hello"), 1.0)

    def test_one_substitution(self):
        self.assertEqual(levenshtein_distance("hello", "hallo"), 1)
        self.assertAlmostEqual(levenshtein_ratio("hello", "hallo"), 0.8)

    def test_one_insertion(self):
        self.assertEqual(levenshtein_distance("hello", "helloo"), 1)

    def test_one_deletion(self):
        self.assertEqual(levenshtein_distance("hello", "ello"), 1)

    def test_completely_different(self):
        # 3-char vs 3-char, all-substitute = 3 edits, ratio = 0.0
        self.assertEqual(levenshtein_distance("abc", "xyz"), 3)
        self.assertEqual(levenshtein_ratio("abc", "xyz"), 0.0)

    def test_empty_strings(self):
        self.assertEqual(levenshtein_distance("", ""), 0)
        self.assertEqual(levenshtein_ratio("", ""), 1.0)

    def test_one_empty(self):
        self.assertEqual(levenshtein_distance("hello", ""), 5)
        self.assertEqual(levenshtein_distance("", "hello"), 5)
        self.assertEqual(levenshtein_ratio("hello", ""), 0.0)

    def test_ratio_in_zero_one_range(self):
        # Random-ish prose; ratio must be bounded
        a = "The Add to Cart button is hard to see on mobile."
        b = "The Add to Cart button is difficult to spot on mobile."
        ratio = levenshtein_ratio(a, b)
        self.assertGreater(ratio, 0.0)
        self.assertLess(ratio, 1.0)

    def test_catastrophic_drift_below_tripwire(self):
        a = "The Add to Cart button is the same grey as the page background."
        b = "Privacy policy points to a staging-domain URL."
        # These share almost no substring; ratio should be < 0.3
        self.assertLess(levenshtein_ratio(a, b), 0.3)

    def test_long_strings_use_short_first_optimization(self):
        # Sanity check that swapping operands doesn't change the result.
        long_str = "x" * 100
        short_str = "y" * 5
        d1 = levenshtein_distance(long_str, short_str)
        d2 = levenshtein_distance(short_str, long_str)
        self.assertEqual(d1, d2)


# ---------------------------------------------------------------------------
# Sentence splitter
# ---------------------------------------------------------------------------


class TestSentenceSplitter(unittest.TestCase):
    def test_single_sentence(self):
        self.assertEqual(
            _split_sentences("The button is grey."),
            ["The button is grey."],
        )

    def test_multiple_sentences_period_capital(self):
        result = _split_sentences("The button is grey. The page is white. Both fail.")
        self.assertEqual(len(result), 3)

    def test_question_mark(self):
        result = _split_sentences("Is the button visible? It uses #6B6B6B fill.")
        self.assertEqual(len(result), 2)

    def test_exclamation_mark(self):
        result = _split_sentences("Look out! Something is wrong here.")
        self.assertEqual(len(result), 2)

    def test_paragraph_break(self):
        result = _split_sentences("Paragraph one\n\nParagraph two without terminator")
        self.assertEqual(len(result), 2)

    def test_empty_input(self):
        self.assertEqual(_split_sentences(""), [])
        self.assertEqual(_split_sentences("   "), [])

    def test_open_paren_starts_next_sentence(self):
        result = _split_sentences("Issue here. (See screenshot for context.)")
        self.assertEqual(len(result), 2)


# ---------------------------------------------------------------------------
# compare_findings_stability — structural-only path (no model load)
# ---------------------------------------------------------------------------


def _make_finding(**overrides) -> dict:
    """Build a schema-conformant finding dict with sensible defaults."""
    base = {
        "cluster": "visual-cta",
        "device": "mobile",
        "local_id": 1,
        "verdict": "FAIL",
        "title": "ATC Button Color Blends Into Page",
        "surface": "primary-cta",
        "element": {"baton_index": "e47", "role": "button"},
        "severity": "MEDIUM",
        "scope": "device",
        "effort": {"change_type": "css", "change_scope": "single-file"},
        "evidence_anchors": [{"type": "dom", "reference": "e47"}],
        "reference_citations": [
            {"source": "color-psychology.md", "tier": "Silver"}
        ],
        "observation": (
            "The Add to Cart button uses a mid-grey fill that matches three "
            "other interactive elements within the same viewport."
        ),
        "recommendation": (
            "Apply the brand accent red to the Add to Cart button background "
            "and reserve that color for purchase actions only."
        ),
        "why_this_matters": (
            "On mobile product pages the buy button is the only conversion "
            "action that matters; if it doesn't visually own the page, every "
            "conversion costs more attention than it should."
        ),
        "evidence_tier": "Silver",
    }
    base.update(overrides)
    return base


class TestStructuralOnly(unittest.TestCase):
    """compare_findings_stability with include_embeddings=False — model never loads."""

    def test_identical_findings_pass(self):
        f = _make_finding()
        result = compare_findings_stability(f, dict(f), include_embeddings=False)
        self.assertTrue(result["passed"], msg=result["failures"])
        self.assertTrue(result["metrics"]["element_baton_index_equal"])
        self.assertTrue(result["metrics"]["surface_equal"])
        self.assertEqual(result["metrics"]["title_jaccard"], 1.0)
        self.assertEqual(result["metrics"]["severity_distance"], 0)
        # Embedding metrics None when skipped
        self.assertIsNone(result["metrics"]["observation_cosine"])
        self.assertIsNone(result["metrics"]["recommendation_cosine"])
        self.assertIsNone(result["metrics"]["document_semscore"])

    def test_baton_index_mismatch_fails(self):
        golden = _make_finding()
        candidate = _make_finding(element={"baton_index": "e99"})
        result = compare_findings_stability(golden, candidate, include_embeddings=False)
        self.assertFalse(result["passed"])
        self.assertFalse(result["metrics"]["element_baton_index_equal"])
        self.assertTrue(any("baton_index" in f for f in result["failures"]))

    def test_surface_mismatch_fails(self):
        golden = _make_finding()
        candidate = _make_finding(surface="footer-policy-links")
        result = compare_findings_stability(golden, candidate, include_embeddings=False)
        self.assertFalse(result["passed"])
        self.assertFalse(result["metrics"]["surface_equal"])

    def test_title_below_jaccard_threshold_fails(self):
        golden = _make_finding(title="Hero CTA Color Blends Into Background")
        candidate = _make_finding(title="Privacy Policy Footer Link Broken")
        result = compare_findings_stability(golden, candidate, include_embeddings=False)
        self.assertFalse(result["passed"])
        self.assertLess(result["metrics"]["title_jaccard"], 0.7)

    def test_severity_one_tier_drift_passes(self):
        golden = _make_finding(severity="HIGH")
        candidate = _make_finding(severity="MEDIUM")
        result = compare_findings_stability(golden, candidate, include_embeddings=False)
        self.assertEqual(result["metrics"]["severity_distance"], 1)
        # severity drift alone shouldn't fail (within max_severity_distance=1)
        self.assertTrue(result["passed"], msg=result["failures"])

    def test_severity_two_tier_drift_fails(self):
        golden = _make_finding(severity="CRITICAL")
        candidate = _make_finding(severity="MEDIUM")
        result = compare_findings_stability(golden, candidate, include_embeddings=False)
        self.assertFalse(result["passed"])
        self.assertEqual(result["metrics"]["severity_distance"], 2)

    def test_levenshtein_tripwire_on_observation_fails(self):
        golden = _make_finding(
            observation=(
                "The Add to Cart button uses a mid-grey fill that matches "
                "three other interactive elements within the same viewport."
            )
        )
        candidate = _make_finding(
            observation=(
                "Privacy policy URL points to a Shopify staging domain "
                "instead of the canonical storefront path."
            )
        )
        result = compare_findings_stability(golden, candidate, include_embeddings=False)
        self.assertFalse(result["passed"])
        self.assertLess(result["metrics"]["observation_levenshtein"], 0.3)
        self.assertTrue(
            any("observation Levenshtein" in f for f in result["failures"])
        )

    def test_minor_prose_rewording_passes_levenshtein(self):
        # Realistic re-run drift — same intent, slightly different wording.
        golden = _make_finding(
            observation=(
                "The Add to Cart button uses a mid-grey fill that matches "
                "three other interactive elements within the same viewport."
            )
        )
        candidate = _make_finding(
            observation=(
                "The Add to Cart button uses a mid-grey fill matching "
                "three other interactive elements in the same viewport."
            )
        )
        result = compare_findings_stability(golden, candidate, include_embeddings=False)
        # Levenshtein ratio should be well above 0.3 — same prose, minor edits
        self.assertGreater(result["metrics"]["observation_levenshtein"], 0.7)
        self.assertTrue(result["passed"], msg=result["failures"])

    def test_missing_optional_fields_handled(self):
        # Bare-bones finding dict — only the fields the metric needs.
        golden = {
            "title": "Hero CTA Color",
            "surface": "primary-cta",
            "element": {"baton_index": "e47"},
            "severity": "MEDIUM",
            "observation": "Body copy.",
            "recommendation": "Fix it.",
        }
        candidate = dict(golden)
        result = compare_findings_stability(golden, candidate, include_embeddings=False)
        self.assertTrue(result["passed"], msg=result["failures"])

    def test_completely_missing_element_dict(self):
        golden = _make_finding()
        candidate = _make_finding(element={})  # baton_index absent
        result = compare_findings_stability(golden, candidate, include_embeddings=False)
        self.assertFalse(result["passed"])
        self.assertFalse(result["metrics"]["element_baton_index_equal"])

    def test_failures_list_collects_all_drift(self):
        # Many things drift — verify failures list captures them all rather
        # than aborting at the first.
        golden = _make_finding()
        candidate = _make_finding(
            element={"baton_index": "e99"},
            surface="footer",
            title="Privacy Policy Broken Link",
            severity="LOW",
            observation="Something completely different here.",
            recommendation="Different recommendation entirely now.",
        )
        result = compare_findings_stability(golden, candidate, include_embeddings=False)
        self.assertFalse(result["passed"])
        # Expect failures for: baton_index, surface, title_jaccard, severity_distance,
        # observation_levenshtein, recommendation_levenshtein → 6 failures
        self.assertGreaterEqual(len(result["failures"]), 5)


# ---------------------------------------------------------------------------
# Embedding-based tests — load the model once via setUpClass
# ---------------------------------------------------------------------------


def _embeddings_available() -> bool:
    """True when sentence-transformers is importable. Used as test guard."""
    try:
        import sentence_transformers  # noqa: F401, PLC0415
        return True
    except ImportError:
        return False


@unittest.skipUnless(
    _embeddings_available(),
    "sentence-transformers not installed; skipping embedding tests",
)
class TestProseCosineSimilarity(unittest.TestCase):
    """Embedding-based per-field cosine. Loads model on first call."""

    @classmethod
    def setUpClass(cls):
        from assembly.finding_stability import _get_model
        # Warm the cache once for all tests in this class.
        _get_model()

    def test_identical_prose_high_cosine(self):
        from assembly.finding_stability import prose_cosine_similarity
        text = (
            "The Add to Cart button uses a mid-grey fill matching other "
            "interactive elements within the same viewport."
        )
        self.assertGreater(prose_cosine_similarity(text, text), 0.999)

    def test_paraphrased_prose_above_threshold(self):
        from assembly.finding_stability import prose_cosine_similarity
        # Close paraphrase — same subject, same complement, single-word swap
        # of "blends into" ↔ "matches". MiniLM-L6 cosine is sensitive to
        # surface form even at small edits; the canonical 0.85 threshold
        # tolerates light rewording but flags meaningful drift.
        a = "The Add to Cart button color blends into the page background."
        b = "The Add to Cart button color matches the page background."
        self.assertGreater(prose_cosine_similarity(a, b), 0.85)

    def test_unrelated_prose_below_threshold(self):
        from assembly.finding_stability import prose_cosine_similarity
        a = "The Add to Cart button color blends with the page background."
        b = "Privacy policy URL points to a Shopify staging domain."
        # Unrelated topics → cosine should be below 0.85
        self.assertLess(prose_cosine_similarity(a, b), 0.85)

    def test_empty_inputs(self):
        from assembly.finding_stability import prose_cosine_similarity
        self.assertEqual(prose_cosine_similarity("", ""), 1.0)
        self.assertEqual(prose_cosine_similarity("hello", ""), 0.0)
        self.assertEqual(prose_cosine_similarity("", "hello"), 0.0)


@unittest.skipUnless(
    _embeddings_available(),
    "sentence-transformers not installed; skipping embedding tests",
)
class TestSemScoreDocument(unittest.TestCase):
    """Document-level mean-pooled cosine."""

    @classmethod
    def setUpClass(cls):
        from assembly.finding_stability import _get_model
        _get_model()

    def test_identical_documents(self):
        from assembly.finding_stability import semscore_document
        doc = (
            "The button color blends in. Visitors can't find the buy action. "
            "The mid-grey fill matches three other UI elements above the fold."
        )
        self.assertGreater(semscore_document(doc, doc), 0.999)

    def test_paraphrased_documents_above_threshold(self):
        from assembly.finding_stability import semscore_document
        # Tight sentence-level paraphrasing — each sentence keeps its subject
        # and predicate, with only a synonym swap. Document-level SemScore
        # over the mean-pooled sentence vectors should clear 0.80.
        a = (
            "The button color blends into the background. "
            "Visitors struggle to find the primary action. "
            "The fill matches three other interactive elements."
        )
        b = (
            "The button color blends into the background area. "
            "Visitors struggle to locate the primary action. "
            "The fill matches three other interactive page elements."
        )
        self.assertGreater(semscore_document(a, b), 0.80)

    def test_unrelated_documents_below_threshold(self):
        from assembly.finding_stability import semscore_document
        a = (
            "The button color blends with the page background. Visitors can't "
            "find the primary action."
        )
        b = (
            "Privacy policy URL points to a Shopify staging domain instead of "
            "the canonical storefront. Disclosure chain is broken."
        )
        self.assertLess(semscore_document(a, b), 0.80)

    def test_empty_inputs(self):
        from assembly.finding_stability import semscore_document
        self.assertEqual(semscore_document("", ""), 1.0)
        self.assertEqual(semscore_document("hello", ""), 0.0)


@unittest.skipUnless(
    _embeddings_available(),
    "sentence-transformers not installed; skipping embedding tests",
)
class TestCompareFindingsStabilityWithEmbeddings(unittest.TestCase):
    """End-to-end: full stability check including embedding-based metrics."""

    @classmethod
    def setUpClass(cls):
        from assembly.finding_stability import _get_model
        _get_model()

    def test_identical_findings_full_pass(self):
        f = _make_finding()
        result = compare_findings_stability(f, dict(f))
        self.assertTrue(result["passed"], msg=result["failures"])
        self.assertGreater(result["metrics"]["observation_cosine"], 0.999)
        self.assertGreater(result["metrics"]["recommendation_cosine"], 0.999)
        self.assertGreater(result["metrics"]["document_semscore"], 0.999)

    def test_paraphrased_finding_passes(self):
        # Realistic re-run: same intent, paraphrased prose, same severity.
        golden = _make_finding(
            observation=(
                "The Add to Cart button uses a mid-grey fill that matches "
                "three other interactive elements within the same viewport."
            ),
            recommendation=(
                "Apply the brand accent red to the Add to Cart button "
                "background and reserve that color for purchase actions only."
            ),
        )
        candidate = _make_finding(
            observation=(
                "The Add to Cart button uses a mid-grey fill matching three "
                "other interactive elements in the same viewport."
            ),
            recommendation=(
                "Use the brand red as the Add to Cart button background and "
                "reserve that color exclusively for purchase actions."
            ),
        )
        result = compare_findings_stability(golden, candidate)
        self.assertTrue(result["passed"], msg=result["failures"])

    def test_completely_drifted_finding_fails_multiple_gates(self):
        golden = _make_finding()
        candidate = _make_finding(
            observation=(
                "The footer privacy policy link points at the store's Shopify "
                "staging domain instead of a canonical first-party URL."
            ),
            recommendation=(
                "Replace the staging-domain href with a first-party policy URL "
                "on the canonical store domain."
            ),
        )
        result = compare_findings_stability(golden, candidate)
        self.assertFalse(result["passed"])
        # Should fail on Levenshtein tripwire AND embedding cosines AND SemScore
        self.assertLess(result["metrics"]["observation_cosine"], 0.85)
        self.assertLess(result["metrics"]["recommendation_cosine"], 0.85)
        self.assertLess(result["metrics"]["document_semscore"], 0.80)


class TestIndexByRef(unittest.TestCase):
    def test_indexes_by_cluster_local_id(self):
        findings = [
            {"cluster": "pricing", "local_id": 1, "title": "A"},
            {"cluster": "pricing", "local_id": 2, "title": "B"},
            {"cluster": "trust-credibility", "local_id": 1, "title": "C"},
        ]
        idx = _index_by_ref(findings)
        self.assertEqual(len(idx), 3)
        self.assertIn(("pricing", 1), idx)
        self.assertIn(("pricing", 2), idx)
        self.assertIn(("trust-credibility", 1), idx)

    def test_drops_findings_missing_cluster(self):
        findings = [
            {"local_id": 1, "title": "no cluster"},
            {"cluster": "pricing", "local_id": 2, "title": "B"},
        ]
        idx = _index_by_ref(findings)
        self.assertEqual(len(idx), 1)

    def test_drops_findings_missing_local_id(self):
        findings = [
            {"cluster": "pricing", "title": "no local_id"},
            {"cluster": "pricing", "local_id": 2, "title": "B"},
        ]
        idx = _index_by_ref(findings)
        self.assertEqual(len(idx), 1)

    def test_coerces_local_id_to_int(self):
        # Some emitters serialize local_id as a string; the index keys are
        # always int tuples to keep pairing reliable across producers.
        findings = [{"cluster": "pricing", "local_id": "3", "title": "A"}]
        idx = _index_by_ref(findings)
        self.assertIn(("pricing", 3), idx)

    def test_drops_unparseable_local_id(self):
        findings = [{"cluster": "pricing", "local_id": "foo", "title": "A"}]
        idx = _index_by_ref(findings)
        self.assertEqual(len(idx), 0)


class TestLoadFindings(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_reads_findings_array(self):
        path = self.tmp_path / "synthesizer-emission-v1.json"
        path.write_text(json.dumps({"findings": [{"cluster": "pricing", "local_id": 1}]}),
                        encoding="utf-8")
        findings = _load_findings(path)
        self.assertEqual(len(findings), 1)

    def test_missing_findings_array_raises(self):
        path = self.tmp_path / "synthesizer-emission-v1.json"
        path.write_text(json.dumps({"other_field": "x"}), encoding="utf-8")
        with self.assertRaises(ValueError):
            _load_findings(path)

    def test_findings_not_a_list_raises(self):
        path = self.tmp_path / "synthesizer-emission-v1.json"
        path.write_text(json.dumps({"findings": "not a list"}), encoding="utf-8")
        with self.assertRaises(ValueError):
            _load_findings(path)

    def test_missing_file_raises_filenotfound(self):
        path = self.tmp_path / "does-not-exist.json"
        with self.assertRaises(FileNotFoundError):
            _load_findings(path)


class TestDiffEngagementsStructural(unittest.TestCase):
    """diff_engagements with include_embeddings=False (no model load)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.golden_dir = Path(self.tmp.name) / "golden"
        self.candidate_dir = Path(self.tmp.name) / "candidate"
        self.golden_dir.mkdir()
        self.candidate_dir.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, path: Path, findings: list[dict]):
        emission = path / "synthesizer-emission-v1.json"
        emission.write_text(json.dumps({"findings": findings}), encoding="utf-8")

    def test_identical_emissions_pass(self):
        findings = [_make_finding(local_id=1), _make_finding(local_id=2, cluster="pricing")]
        self._write(self.golden_dir, findings)
        self._write(self.candidate_dir, [dict(f) for f in findings])

        report = diff_engagements(
            self.golden_dir, self.candidate_dir, include_embeddings=False
        )
        self.assertTrue(report["all_passed"])
        self.assertEqual(report["paired_total"], 2)
        self.assertEqual(report["paired_passed"], 2)
        self.assertEqual(report["paired_failed"], 0)
        self.assertEqual(report["orphans_in_golden"], [])
        self.assertEqual(report["orphans_in_candidate"], [])

    def test_orphan_in_golden_fails(self):
        # Golden has F-01 + F-02; candidate only has F-01
        self._write(self.golden_dir, [
            _make_finding(local_id=1),
            _make_finding(local_id=2, cluster="pricing"),
        ])
        self._write(self.candidate_dir, [_make_finding(local_id=1)])

        report = diff_engagements(
            self.golden_dir, self.candidate_dir, include_embeddings=False
        )
        self.assertFalse(report["all_passed"])
        self.assertEqual(report["paired_total"], 1)
        self.assertEqual(report["orphans_in_golden"], ["pricing F-02"])

    def test_orphan_in_candidate_fails(self):
        self._write(self.golden_dir, [_make_finding(local_id=1)])
        self._write(self.candidate_dir, [
            _make_finding(local_id=1),
            _make_finding(local_id=5, cluster="trust-credibility"),
        ])

        report = diff_engagements(
            self.golden_dir, self.candidate_dir, include_embeddings=False
        )
        self.assertFalse(report["all_passed"])
        self.assertEqual(report["orphans_in_candidate"], ["trust-credibility F-05"])

    def test_drifted_candidate_fails(self):
        # Pair exists, but candidate's element baton_index doesn't match
        self._write(self.golden_dir, [_make_finding(local_id=1)])
        self._write(self.candidate_dir, [_make_finding(local_id=1, element={"baton_index": "e99"})])

        report = diff_engagements(
            self.golden_dir, self.candidate_dir, include_embeddings=False
        )
        self.assertFalse(report["all_passed"])
        self.assertEqual(report["paired_failed"], 1)
        self.assertEqual(len(report["failures"]), 1)
        self.assertEqual(report["failures"][0]["f_ref"], "visual-cta F-01")

    def test_missing_emission_file_raises(self):
        # Candidate dir exists but has no synthesizer-emission-v1.json
        self._write(self.golden_dir, [_make_finding(local_id=1)])
        with self.assertRaises(FileNotFoundError):
            diff_engagements(
                self.golden_dir, self.candidate_dir, include_embeddings=False
            )

    def test_aggregate_counts_partial_failure(self):
        # 3 paired findings: 2 identical (pass), 1 drifted (fail)
        self._write(self.golden_dir, [
            _make_finding(local_id=1),
            _make_finding(local_id=2, cluster="pricing"),
            _make_finding(local_id=3, cluster="trust-credibility"),
        ])
        self._write(self.candidate_dir, [
            _make_finding(local_id=1),
            _make_finding(local_id=2, cluster="pricing"),
            _make_finding(
                local_id=3, cluster="trust-credibility",
                element={"baton_index": "e99"},  # drift
            ),
        ])

        report = diff_engagements(
            self.golden_dir, self.candidate_dir, include_embeddings=False
        )
        self.assertFalse(report["all_passed"])
        self.assertEqual(report["paired_total"], 3)
        self.assertEqual(report["paired_passed"], 2)
        self.assertEqual(report["paired_failed"], 1)


@unittest.skipUnless(
    _embeddings_available(),
    "sentence-transformers not installed; skipping embedding tests",
)
class TestDiffEngagementsWithEmbeddings(unittest.TestCase):
    """diff_engagements with embeddings — full stability check."""

    @classmethod
    def setUpClass(cls):
        from assembly.finding_stability import _get_model
        _get_model()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.golden_dir = Path(self.tmp.name) / "golden"
        self.candidate_dir = Path(self.tmp.name) / "candidate"
        self.golden_dir.mkdir()
        self.candidate_dir.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _write(self, path: Path, findings: list[dict]):
        emission = path / "synthesizer-emission-v1.json"
        emission.write_text(json.dumps({"findings": findings}), encoding="utf-8")

    def test_identical_full_stability_pass(self):
        f = _make_finding()
        self._write(self.golden_dir, [f])
        self._write(self.candidate_dir, [dict(f)])

        report = diff_engagements(self.golden_dir, self.candidate_dir)
        self.assertTrue(report["all_passed"])
        # Embedding metrics populated (not None) when include_embeddings=True
        first = report["paired_results"][0]
        self.assertIsNotNone(first["metrics"]["observation_cosine"])
        self.assertGreater(first["metrics"]["observation_cosine"], 0.999)


if __name__ == "__main__":
    unittest.main()
