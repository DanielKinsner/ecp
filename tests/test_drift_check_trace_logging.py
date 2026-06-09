"""C9 regression: the cross-device drift gate logs its verdict to the trace.

awdmods 2026-06-08 run-review §7-P2/§8-#7: when a drift FAIL is resolved by
editing a synced finding, only the corrected state survives in the artifacts —
the pre-fix ratio lived in lead prose and was unreconstructable. ``drift-check``
now appends a ``# DRIFT GATE`` block to ``audit-trace.log`` on every run, so the
FAIL -> fix -> re-PASS sequence is reconstructable from adjacent blocks.

unittest-style for ``python -m unittest discover`` runner compatibility.

Run:
    python -m unittest tests.test_drift_check_trace_logging
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.synth_input import DriftReport  # noqa: E402


def _load_test_specialist_module():
    """Load scripts/test-specialist.py (hyphenated -> not importable normally).
    Mirrors tests/test_b0_prompt_resolution.py: register in sys.modules before
    exec so @dataclass type-hint resolution doesn't KeyError."""
    spec = importlib.util.spec_from_file_location(
        "test_specialist_cli_drift", _REPO / "scripts" / "test-specialist.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_TS = _load_test_specialist_module()


class TestFormatDriftTraceBlock(unittest.TestCase):
    def test_pass_block_has_verdict_and_ratio_no_worst_line(self):
        report = DriftReport(
            ok=True, threshold=0.10, max_ratio=0.0,
            per_finding=(("F-32", 0.0, 0.0, 0.0),), missing=(),
        )
        block = _TS._format_drift_trace_block(report, ref_count=2)
        self.assertIn("# DRIFT GATE", block)
        self.assertIn("verdict: PASS", block)
        self.assertIn("max_ratio=0.0000", block)
        self.assertIn("threshold=0.10", block)
        self.assertIn("refs_checked: 2, missing: 0", block)
        # All ratios are 0 -> no diagnostic worst line.
        self.assertNotIn("worst:", block)

    def test_fail_block_names_worst_finding(self):
        report = DriftReport(
            ok=False, threshold=0.10, max_ratio=0.1108,
            per_finding=(("F-32", 0.1108, 0.0, 0.0), ("F-16", 0.0, 0.0, 0.0)),
            missing=(),
        )
        block = _TS._format_drift_trace_block(report, ref_count=2)
        self.assertIn("verdict: FAIL", block)
        self.assertIn("max_ratio=0.1108", block)
        self.assertIn("worst: F-32 obs=0.1108", block)


class TestAppendDriftTraceBlock(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.eng = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_appends_to_existing_trace(self):
        trace = self.eng / "audit-trace.log"
        trace.write_text("# ECP Audit Forensic Trace\n", encoding="utf-8")
        report = DriftReport(
            ok=True, threshold=0.10, max_ratio=0.0,
            per_finding=(), missing=(),
        )
        _TS._append_drift_trace_block(trace, report, ref_count=0)
        text = trace.read_text(encoding="utf-8")
        self.assertIn("# ECP Audit Forensic Trace", text)  # preamble preserved
        self.assertIn("# DRIFT GATE", text)
        self.assertIn("verdict: PASS", text)

    def test_two_runs_leave_two_blocks(self):
        """FAIL then PASS must both survive so the fix is reconstructable."""
        trace = self.eng / "audit-trace.log"
        trace.write_text("# header\n", encoding="utf-8")
        fail = DriftReport(ok=False, threshold=0.10, max_ratio=0.1108,
                           per_finding=(("F-32", 0.1108, 0.0, 0.0),), missing=())
        ok = DriftReport(ok=True, threshold=0.10, max_ratio=0.0,
                         per_finding=(("F-32", 0.0, 0.0, 0.0),), missing=())
        _TS._append_drift_trace_block(trace, fail, ref_count=1)
        _TS._append_drift_trace_block(trace, ok, ref_count=1)
        text = trace.read_text(encoding="utf-8")
        self.assertEqual(text.count("# DRIFT GATE"), 2)
        self.assertIn("verdict: FAIL", text)
        self.assertIn("verdict: PASS", text)

    def test_missing_trace_is_a_silent_noop(self):
        """A missing audit-trace.log must never fail the gate."""
        report = DriftReport(ok=True, threshold=0.10, max_ratio=0.0,
                             per_finding=(), missing=())
        # Must not raise.
        _TS._append_drift_trace_block(self.eng / "nope.log", report, ref_count=0)
        self.assertFalse((self.eng / "nope.log").exists())


if __name__ == "__main__":
    unittest.main()
