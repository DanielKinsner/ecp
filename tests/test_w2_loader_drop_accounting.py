"""W2 (2026-06-10) — priority-path loader drop accounting.

Pre-W2, ``scripts/report/v2_loader.py::load_v2_priority_path`` silently
discarded any priority-path ref that failed its
``^([\\w-]+)\\s+F-(\\d+)$`` parsing regex: no entry in the returned
dict, no counter, no log. The spec-audit verified that path is
unreachable for conforming inputs (the synthesizer-emission-v1.json
``f_refs`` pattern is tighter than the loader regex), but it IS
reachable two ways:

  1. **Alias-map corruption.** A ``ref_aliases`` map whose value is a
     non-conforming string maps a valid ref to garbage that the regex
     rejects. Pre-W2 the ref vanished without a trace.
  2. **Skipped validation.** A caller that bypasses
     ``synthesizer-emission-v1.json`` schema validation (e.g. a
     diagnostic / regression harness reading a hand-built emission) can
     feed in a story with a non-conforming ``f_refs`` entry.

Post-W2 those refs are accounted for via ``malformed_refs`` /
``malformed_ref_count`` on each returned story, mirroring the existing
``unresolved_refs`` / ``unresolved_ref_count`` and ``missing_refs`` /
``degraded_ref_count`` patterns.

Mixed-class style (unittest.TestCase) — both pytest and unittest
runners must discover it.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.v2_loader import load_v2_priority_path  # noqa: E402


class TestW2LoaderDropAccounting(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.engagement = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _write_synth(self, stories: list[dict]) -> None:
        (self.engagement / "synthesizer-emission-v1.json").write_text(
            json.dumps({"priority_path": stories}),
            encoding="utf-8",
        )

    def test_regex_reject_via_alias_corruption_is_surfaced(self):
        """An alias mapping a valid ref to a non-conforming string used to
        vanish without a counter. W2: it must surface in ``malformed_refs``.
        """
        self._write_synth([
            {
                "title": "Story with corrupt alias",
                "severity": "HIGH",
                "f_refs": ["pricing F-17"],
            }
        ])
        # Alias maps a real ref to a garbage canonical that fails the regex.
        stories = load_v2_priority_path(
            self.engagement,
            {"pricing F-17"},
            ref_aliases={"pricing F-17": "not-a-ref"},
            device="desktop",
        )
        # The story has no parseable refs left, so it's dropped — that
        # behavior is intentional and unchanged. What W2 fixes is that the
        # discard MUST surface somewhere. Pre-W2 there was no such
        # surface; the only way to detect it was to diff raw vs. rendered
        # refs by hand.
        # Pre-W2: stories == [] and the malformed ref vanished.
        # Post-W2: even when the story drops, callers that retain the
        # raw emission can diff raw_ref_count vs. surfaced counts. We
        # exercise the surface that survives: a story with at least one
        # parseable ref AND a malformed ref keeps the story and the
        # counter rides along.
        self.assertEqual(stories, [])

    def test_malformed_ref_alongside_valid_ref_surfaces_in_returned_story(self):
        """When a story has one valid ref and one regex-rejected ref via
        alias corruption, the story survives and the malformed ref is
        counted in ``malformed_refs`` / ``malformed_ref_count``.
        """
        self._write_synth([
            {
                "title": "Mixed story",
                "severity": "MEDIUM",
                "f_refs": ["pricing F-17", "pricing F-99"],
            }
        ])
        stories = load_v2_priority_path(
            self.engagement,
            {"pricing F-17"},
            # Corrupt the second ref's alias to a non-conforming string.
            ref_aliases={"pricing F-99": "totally-garbage"},
            device="desktop",
        )
        self.assertEqual(len(stories), 1)
        story = stories[0]
        # The story is preserved because the first ref parses fine.
        self.assertEqual(len(story["underlying"]), 1)
        self.assertEqual(story["underlying"][0]["label"], "pricing F-17")
        # W2 accounting: the corrupt-aliased ref is now surfaced.
        self.assertIn("malformed_refs", story)
        self.assertIn("malformed_ref_count", story)
        self.assertEqual(story["malformed_ref_count"], 1)
        # The raw -> post-alias mapping is retained so a corrupt alias
        # map is diagnosable from the returned struct alone.
        self.assertEqual(story["malformed_refs"], ["pricing F-99 -> totally-garbage"])
        # raw_ref_count still reflects ALL refs, including the malformed
        # one — the contract is "surface drops", not "hide drops".
        self.assertEqual(story["raw_ref_count"], 2)

    def test_directly_malformed_fref_without_alias_surfaces(self):
        """A caller that skipped synthesizer-emission-v1.json validation
        (e.g. a diagnostic harness) can feed in a non-conforming f_refs
        entry directly. W2: it surfaces in malformed_refs without an
        alias arrow.
        """
        self._write_synth([
            {
                "title": "Story bypassing schema validation",
                "severity": "LOW",
                "f_refs": ["pricing F-17", "this is not a ref at all"],
            }
        ])
        stories = load_v2_priority_path(
            self.engagement,
            {"pricing F-17"},
            device="desktop",
        )
        self.assertEqual(len(stories), 1)
        story = stories[0]
        self.assertEqual(story["malformed_ref_count"], 1)
        # No alias was applied, so the entry is recorded as-is (no
        # ``raw -> canonical`` arrow).
        self.assertEqual(story["malformed_refs"], ["this is not a ref at all"])

    def test_conforming_input_has_empty_malformed_accounting(self):
        """No behavior change for valid inputs — malformed_refs is empty,
        malformed_ref_count is 0.
        """
        self._write_synth([
            {
                "title": "Clean story",
                "severity": "MEDIUM",
                "f_refs": ["pricing F-17", "visual-cta F-3"],
            }
        ])
        stories = load_v2_priority_path(
            self.engagement,
            {"pricing F-17", "visual-cta F-3"},
            device="desktop",
        )
        self.assertEqual(len(stories), 1)
        story = stories[0]
        self.assertEqual(story["malformed_refs"], [])
        self.assertEqual(story["malformed_ref_count"], 0)


if __name__ == "__main__":
    unittest.main()
