"""Tests for the lead-reflection format/ownership canary (G25 follow-up, 2026-05-29).

`lead-reflection.md` is a lead-owned artifact (contracts/lead-discipline.md). In
docs/ecp/2026-05-28-e4050c0e a specialist subagent wrote it instead — a
file-ownership violation. There is no write-attribution in the pipeline, so
check_lead_reflection_well_formed is a structural PROXY: when the file is present
it must conform to the lead's required format (canonical header + Pipeline +
Phase reached markers). A specialist's content dump wouldn't.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.canary_checks import (  # noqa: E402
    check_lead_reflection_well_formed,
    run_all_canaries,
)

_GOOD = """# Lead Reflection — engagement 2026-05-29-deadbeef

**Engagement timeline:** 2026-05-29T00:00:00Z to 2026-05-29T00:30:00Z
**Pipeline:** v2
**Phase reached:** complete

## Deviations observed

None caught — clean run.
"""

# What a specialist content dump in the wrong file might look like — no lead header.
_SPECIALIST_DUMP = """# Content & SEO findings

The page title is missing an H1. Meta description is 210 chars (too long).
"""


def _eng(tmp: str, content: str | None) -> Path:
    d = Path(tmp) / "eng"
    d.mkdir()
    if content is not None:
        (d / "lead-reflection.md").write_text(content, encoding="utf-8")
    return d


class TestLeadReflectionWellFormed(unittest.TestCase):
    def test_skips_when_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = check_lead_reflection_well_formed(_eng(tmp, None))
            self.assertTrue(r["passed"])
            self.assertIn("skip", r["summary"].lower())

    def test_pass_when_well_formed(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(check_lead_reflection_well_formed(_eng(tmp, _GOOD))["passed"])

    def test_fail_when_missing_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = check_lead_reflection_well_formed(_eng(tmp, _SPECIALIST_DUMP))
            self.assertFalse(r["passed"])
            self.assertIn("header", r["summary"].lower())

    def test_fail_when_missing_pipeline_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = _GOOD.replace("**Pipeline:** v2\n", "")
            self.assertFalse(check_lead_reflection_well_formed(_eng(tmp, content))["passed"])

    def test_fail_when_missing_phase_reached(self):
        with tempfile.TemporaryDirectory() as tmp:
            content = _GOOD.replace("**Phase reached:** complete\n", "")
            self.assertFalse(check_lead_reflection_well_formed(_eng(tmp, content))["passed"])


class TestWiredIntoRunAllCanaries(unittest.TestCase):
    def test_present_in_run_all_canaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / "eng"
            d.mkdir()
            out = run_all_canaries(d, include_visual_quality=False)
            self.assertIn("lead_reflection_well_formed", [r["name"] for r in out["results"]])

    def test_run_all_canaries_flags_malformed(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _eng(tmp, _SPECIALIST_DUMP)
            out = run_all_canaries(d, include_visual_quality=False)
            by = {r["name"]: r for r in out["results"]}
            self.assertFalse(by["lead_reflection_well_formed"]["passed"])
            self.assertFalse(out["all_passed"])


if __name__ == "__main__":
    unittest.main()
