"""Tests for the lead-reflection-stale canary (G23 follow-up, 2026-05-29).

Consumer-side check: when an engagement is marked complete (``phase: complete``
or ``engagement_status: complete``) but the lead never flipped
``reflection_state`` from ``draft`` to ``complete``, the lead-reflection.md
narrative is stale relative to the finished pipeline — the
``docs/ecp/2026-05-28-e4050c0e`` premature-reflection failure class.

Back-compat invariant (mirrors test_g23_reflection_state_gate): an ABSENT
reflection_state field is pre-G23 and must NOT be flagged, only an explicitly
``draft`` field on a completed engagement. This keeps the Phase-J fixtures
(phase: complete, no reflection_state) green.
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
    check_lead_reflection_not_stale,
    run_all_canaries,
)


def _eng(tmp: str, **meta_over) -> Path:
    d = Path(tmp) / "docs" / "ecp" / "2026-05-29-deadbeef"
    d.mkdir(parents=True)
    meta = {"id": "2026-05-29-deadbeef", "schema_version": 3}
    meta.update(meta_over)
    (d / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return d


class TestLeadReflectionStaleCanary(unittest.TestCase):
    def test_skips_when_no_meta(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "eng"
            d.mkdir()
            r = check_lead_reflection_not_stale(d)
            self.assertTrue(r["passed"])
            self.assertIn("skip", r["summary"].lower())

    def test_pass_phase_complete_reflection_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _eng(tmp, phase="complete", reflection_state="complete")
            self.assertTrue(check_lead_reflection_not_stale(d)["passed"])

    def test_fail_phase_complete_reflection_draft(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _eng(tmp, phase="complete", reflection_state="draft")
            r = check_lead_reflection_not_stale(d)
            self.assertFalse(r["passed"])
            self.assertIn("reflection_state", r["summary"])

    def test_fail_engagement_status_complete_reflection_draft(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _eng(tmp, engagement_status="complete", reflection_state="draft")
            self.assertFalse(check_lead_reflection_not_stale(d)["passed"])

    def test_pass_when_not_complete(self):
        # Mid-run draft is expected and must not be flagged.
        with tempfile.TemporaryDirectory() as tmp:
            d = _eng(tmp, phase="audit", reflection_state="draft")
            self.assertTrue(check_lead_reflection_not_stale(d)["passed"])

    def test_pass_pre_g23_absent_field(self):
        # phase: complete but NO reflection_state field (Phase-J fixtures / pre-G23).
        with tempfile.TemporaryDirectory() as tmp:
            d = _eng(tmp, phase="complete")
            r = check_lead_reflection_not_stale(d)
            self.assertTrue(r["passed"], "absent reflection_state is back-compat, not stale")

    def test_fail_when_meta_unreadable(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "eng"
            d.mkdir()
            (d / "meta.json").write_text("{not json", encoding="utf-8")
            self.assertFalse(check_lead_reflection_not_stale(d)["passed"])


class TestWiredIntoRunAllCanaries(unittest.TestCase):
    def test_present_in_run_all_canaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "eng"
            d.mkdir()
            out = run_all_canaries(d, include_visual_quality=False)
            self.assertIn("lead_reflection_not_stale", [r["name"] for r in out["results"]])

    def test_run_all_canaries_flags_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _eng(tmp, phase="complete", reflection_state="draft")
            out = run_all_canaries(d, include_visual_quality=False)
            by = {r["name"]: r for r in out["results"]}
            self.assertFalse(by["lead_reflection_not_stale"]["passed"])
            self.assertFalse(out["all_passed"])


if __name__ == "__main__":
    unittest.main()
