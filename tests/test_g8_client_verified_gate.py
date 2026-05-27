"""G8 (product.md §6) — Draft -> Client-Ready verification gate.

A generated report is always DRAFT. Promotion to CLIENT-VERIFIED is a manual
operator attestation; automated / --auto execution can NEVER set it. These
tests lock in:

- read_report_state defaults to "draft" for missing/blank/garbage values.
- set_client_verified(auto=False) promotes + stamps `updated`.
- set_client_verified(auto=True) refuses with AutoPromotionError and does NOT
  mutate the file.
- the meta validator flags an invalid report_state enum value.
- the generate-report.py --mark-client-verified CLI verb enforces the same
  guard end-to-end (refuses under --auto, promotes otherwise).
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.report_state import (  # noqa: E402
    AutoPromotionError,
    REPORT_STATE_CLIENT_VERIFIED,
    REPORT_STATE_DRAFT,
    read_report_state,
    set_client_verified,
)
from assembly.meta_validator import validate_meta_json  # noqa: E402


def _write_meta(tmp: Path, **overrides) -> Path:
    meta = {
        "schema_version": 3,
        "id": "2026-05-26-deadbeef",
        "created": "2026-05-26T10:00:00.000Z",
        "updated": "2026-05-26T10:00:00.000Z",
        "type": "audit",
        "phase": "complete",
        "report_state": "draft",
    }
    meta.update(overrides)
    path = tmp / "meta.json"
    path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return path


class TestReadReportState(unittest.TestCase):
    def test_defaults_to_draft_when_missing(self):
        self.assertEqual(read_report_state({}), REPORT_STATE_DRAFT)

    def test_garbage_value_reads_as_draft(self):
        self.assertEqual(read_report_state({"report_state": "shipped"}), REPORT_STATE_DRAFT)
        self.assertEqual(read_report_state({"report_state": None}), REPORT_STATE_DRAFT)

    def test_valid_values_pass_through(self):
        self.assertEqual(read_report_state({"report_state": "draft"}), REPORT_STATE_DRAFT)
        self.assertEqual(
            read_report_state({"report_state": "client-verified"}),
            REPORT_STATE_CLIENT_VERIFIED,
        )


class TestSetClientVerified(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = Path(tempfile.mkdtemp())

    def test_manual_promotion_sets_state_and_updates_timestamp(self):
        path = _write_meta(self._tmp)
        meta = set_client_verified(path, auto=False, now="2026-05-26T12:00:00Z")
        self.assertEqual(meta["report_state"], REPORT_STATE_CLIENT_VERIFIED)
        self.assertEqual(meta["updated"], "2026-05-26T12:00:00Z")
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(on_disk["report_state"], REPORT_STATE_CLIENT_VERIFIED)

    def test_auto_promotion_refused_and_file_untouched(self):
        path = _write_meta(self._tmp)
        before = path.read_text(encoding="utf-8")
        with self.assertRaises(AutoPromotionError):
            set_client_verified(path, auto=True)
        self.assertEqual(path.read_text(encoding="utf-8"), before, "file must be unchanged")


class TestMetaValidatorEnum(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = Path(tempfile.mkdtemp())

    def test_valid_report_state_no_warning(self):
        path = _write_meta(self._tmp, report_state="client-verified")
        self.assertFalse(any("report_state" in w for w in validate_meta_json(path)))

    def test_invalid_report_state_warns(self):
        path = _write_meta(self._tmp, report_state="published")
        warnings = validate_meta_json(path)
        self.assertTrue(any("report_state" in w for w in warnings), warnings)


class TestCliVerb(unittest.TestCase):
    def setUp(self):
        import tempfile
        self._tmp = Path(tempfile.mkdtemp())

    def _run(self, *extra):
        return subprocess.run(
            [
                sys.executable,
                str(_REPO / "scripts" / "generate-report.py"),
                "--engagement", str(self._tmp),
                "--device", "laptop",
                "--plugin-root", str(_REPO),
                "--mark-client-verified",
                *extra,
            ],
            capture_output=True,
            text=True,
        )

    def test_cli_promotes_without_auto(self):
        _write_meta(self._tmp)
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        on_disk = json.loads((self._tmp / "meta.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk["report_state"], "client-verified")

    def test_cli_refuses_under_auto(self):
        _write_meta(self._tmp)
        result = self._run("--auto")
        self.assertNotEqual(result.returncode, 0)
        on_disk = json.loads((self._tmp / "meta.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk["report_state"], "draft", "must stay draft under --auto")


if __name__ == "__main__":
    unittest.main()
