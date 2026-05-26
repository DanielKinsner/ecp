from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.v2_loader import load_v2_priority_path  # noqa: E402


class TestV2PriorityPathLoader(unittest.TestCase):
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

    def test_keeps_single_actionable_story_with_cross_device_ref_surfaced(self):
        """Phase 6 (2026-05-18) — Codex Q4: cross-device refs are surfaced
        as muted underlying[].applies_on_other_device entries instead of
        being silently dropped. Pre-Phase-6 contract was to drop the
        non-actionable ref entirely; new contract preserves it with a
        muted annotation so the customer sees the cross-device coverage.
        Test name + assertions updated accordingly.
        """
        self._write_synth([
            {
                "title": "Mixed device story",
                "severity": "HIGH",
                "f_refs": ["pricing F-17", "pricing F-64", "visual-cta F-31"],
            }
        ])
        stories = load_v2_priority_path(
            self.engagement,
            {"pricing F-17"},
            ref_aliases={"pricing F-64": "pricing F-17"},
            device="mobile",
        )
        self.assertEqual(len(stories), 1)
        # Story is NOT a faded "applies elsewhere" — it has an actionable ref
        self.assertFalse(stories[0].get("applies_on_other_device"))
        # fixes_count counts only actionable refs (excludes applies_on_other_device)
        self.assertEqual(stories[0]["fixes_count"], 1)
        # underlying[] surfaces BOTH the actionable ref AND the other-device ref;
        # the other-device ref carries applies_on_other_device=True so the
        # renderer styles it muted/struck-through.
        labels = [u["label"] for u in stories[0]["underlying"]]
        self.assertEqual(labels, ["pricing F-17", "visual-cta F-31"])
        applies_elsewhere_flags = [
            u.get("applies_on_other_device", False) for u in stories[0]["underlying"]
        ]
        self.assertEqual(applies_elsewhere_flags, [False, True])
        self.assertEqual(stories[0]["missing_refs"], ["visual-cta F-31"])

    def test_future_refs_by_device_are_preferred_but_f_refs_remain_supported(self):
        self._write_synth([
            {
                "title": "Concept story",
                "severity": "MEDIUM",
                "refs_by_device": {"mobile": ["visual-cta F-31"]},
                "f_refs": ["visual-cta F-99"],
            }
        ])
        stories = load_v2_priority_path(
            self.engagement,
            {"visual-cta F-31"},
            device="mobile",
        )
        self.assertEqual(len(stories), 1)
        self.assertEqual(stories[0]["underlying"][0]["label"], "visual-cta F-31")
        self.assertEqual(stories[0]["missing_refs"], ["visual-cta F-99"])


if __name__ == "__main__":
    unittest.main()
