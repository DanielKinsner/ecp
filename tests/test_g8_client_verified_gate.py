"""G8 (product.md §6) — Draft -> Client-Ready verification gate.

A generated report is always DRAFT. Promotion to CLIENT-VERIFIED is a manual
operator attestation; automated / --auto execution can NEVER set it. These
tests lock in:

- read_report_state defaults to "draft" for missing/blank/garbage values.
- set_client_verified(auto=False) promotes + stamps `updated` (with a clean
  placement queue).
- set_client_verified(auto=True) refuses with AutoPromotionError and does NOT
  mutate the file — regardless of `force`.
- the meta validator flags an invalid report_state enum value.
- the generate-report.py --mark-client-verified CLI verb enforces the same
  guard end-to-end (refuses under --auto, promotes otherwise).

Phase-0 A9 (2026-06-10) — the §6 placement gate grows teeth:

- set_client_verified refuses with UnplacedMarkerError when the engagement's
  review-state-{device}.json file(s) report findings with
  hotspot_confidence == "needs-manual-marker".
- set_client_verified refuses with UnplacedMarkerError when NO review-state
  file exists for any device (placement was never finalized).
- force=True bypasses both refusals and records `forced: true` on the
  attestation block.
- A successful promotion writes report_state_attestation = {
      promoted_at, unplaced_counts: {device: count}, forced: bool
  } on meta.json.
- The CLI --force flag plumbs through end-to-end.
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
    UnplacedMarkerError,
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


def _write_review_state(
    tmp: Path,
    device: str,
    *,
    unplaced: int = 0,
    placed: int = 1,
    resolved_unplaced: tuple[str, ...] = (),
) -> Path:
    """Write a synthetic review-state-{device}.json with the requested mix.

    Only the fields ``set_client_verified`` actually reads are populated —
    ``findings[].hotspot_confidence`` and ``findings[].status``. Other keys
    are present but minimal so no other consumer of these tests stumbles on
    partial state. ``resolved_unplaced`` adds one needs-manual-marker finding
    per given status (e.g. "hidden", "approved") — the operator decline/keep
    paths that must NOT count against the gate.
    """
    findings = []
    for i in range(unplaced):
        findings.append({
            "f_ref": f"{device}/U-{i:02d}",
            "hotspot_confidence": "needs-manual-marker",
        })
    for i, status in enumerate(resolved_unplaced):
        findings.append({
            "f_ref": f"{device}/R-{i:02d}",
            "hotspot_confidence": "needs-manual-marker",
            "status": status,
        })
    for i in range(placed):
        findings.append({
            "f_ref": f"{device}/P-{i:02d}",
            "hotspot_confidence": "exact-selector",
        })
    state = {
        "review_state_schema_version": 1,
        "engagement_id": "2026-05-26-deadbeef",
        "device": device,
        "findings": findings,
        "markers": [],
        "slides": [],
        "slide_edits": [],
    }
    path = tmp / f"review-state-{device}.json"
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
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


class TestSetClientVerifiedBasics(unittest.TestCase):
    """Core behavior: auto-refusal (with or without --force), clean-queue promote."""

    def setUp(self):
        import tempfile
        self._tmp = Path(tempfile.mkdtemp())

    def test_manual_promotion_with_clean_queue_promotes_and_records_attestation(self):
        path = _write_meta(self._tmp)
        _write_review_state(self._tmp, "desktop", unplaced=0, placed=3)
        meta = set_client_verified(path, auto=False, now="2026-05-26T12:00:00Z")
        self.assertEqual(meta["report_state"], REPORT_STATE_CLIENT_VERIFIED)
        self.assertEqual(meta["updated"], "2026-05-26T12:00:00Z")
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(on_disk["report_state"], REPORT_STATE_CLIENT_VERIFIED)
        # Attestation stamped, forced=False, unplaced_counts present.
        attestation = on_disk["report_state_attestation"]
        self.assertEqual(attestation["promoted_at"], "2026-05-26T12:00:00Z")
        self.assertEqual(attestation["forced"], False)
        self.assertEqual(attestation["unplaced_counts"], {"desktop": 0})

    def test_auto_promotion_refused_and_file_untouched(self):
        path = _write_meta(self._tmp)
        _write_review_state(self._tmp, "desktop", unplaced=0, placed=3)
        before = path.read_text(encoding="utf-8")
        with self.assertRaises(AutoPromotionError):
            set_client_verified(path, auto=True)
        self.assertEqual(path.read_text(encoding="utf-8"), before, "file must be unchanged")

    def test_auto_promotion_refused_even_with_force(self):
        # --force does NOT bypass the --auto refusal; that guard is absolute.
        path = _write_meta(self._tmp)
        before = path.read_text(encoding="utf-8")
        with self.assertRaises(AutoPromotionError):
            set_client_verified(path, auto=True, force=True)
        self.assertEqual(path.read_text(encoding="utf-8"), before)


class TestPlacementGate(unittest.TestCase):
    """Phase-0 A9: unplaced-marker refusal, --force escape, attestation."""

    def setUp(self):
        import tempfile
        self._tmp = Path(tempfile.mkdtemp())

    def test_no_review_state_files_refuses(self):
        path = _write_meta(self._tmp)
        before = path.read_text(encoding="utf-8")
        with self.assertRaises(UnplacedMarkerError) as cm:
            set_client_verified(path, auto=False)
        self.assertEqual(cm.exception.unplaced_counts, {})
        self.assertEqual(path.read_text(encoding="utf-8"), before)

    def test_no_review_state_files_force_bypasses(self):
        path = _write_meta(self._tmp)
        meta = set_client_verified(path, auto=False, force=True, now="2026-05-26T12:30:00Z")
        self.assertEqual(meta["report_state"], REPORT_STATE_CLIENT_VERIFIED)
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(on_disk["report_state_attestation"]["forced"], True)
        self.assertEqual(on_disk["report_state_attestation"]["unplaced_counts"], {})

    def test_hidden_unplaced_does_not_block(self):
        """Editor decline path (status=hidden) clears the gate — product.md §4.2
        'places or DECLINES them manually'. Without this, every absence-carrying
        engagement would be un-promotable without --force."""
        path = _write_meta(self._tmp)
        _write_review_state(
            self._tmp, "desktop", unplaced=0, placed=2,
            resolved_unplaced=("hidden", "hidden"),
        )
        meta = set_client_verified(path, auto=False, now="2026-05-26T14:00:00Z")
        self.assertEqual(meta["report_state"], REPORT_STATE_CLIENT_VERIFIED)
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(on_disk["report_state_attestation"]["unplaced_counts"], {"desktop": 0})
        self.assertEqual(on_disk["report_state_attestation"]["forced"], False)

    def test_approved_unplaced_does_not_block(self):
        """Explicit operator keep (status=approved) is a deliberate blank — neutral
        per §4.2; only an UNREVIEWED blank blocks promotion."""
        path = _write_meta(self._tmp)
        _write_review_state(
            self._tmp, "desktop", unplaced=0, placed=1,
            resolved_unplaced=("approved",),
        )
        meta = set_client_verified(path, auto=False, now="2026-05-26T14:05:00Z")
        self.assertEqual(meta["report_state"], REPORT_STATE_CLIENT_VERIFIED)

    def test_edited_unplaced_still_blocks(self):
        """status=edited means the operator touched the finding text, not the
        marker — the placement decision is still outstanding."""
        path = _write_meta(self._tmp)
        _write_review_state(
            self._tmp, "desktop", unplaced=0, placed=1,
            resolved_unplaced=("edited", "tagged_for_ai_pass"),
        )
        with self.assertRaises(UnplacedMarkerError) as cm:
            set_client_verified(path, auto=False)
        self.assertEqual(cm.exception.unplaced_counts, {"desktop": 2})

    def test_filename_map_matches_review_state_builder(self):
        """The gate duplicates the review-state filename map (to stay off the v2
        renderer's import graph); this pins the copy to the canonical map so a
        new device can't silently bypass the gate."""
        from assembly.report_state import _REVIEW_STATE_FILENAMES
        from assembly.review_state import REVIEW_STATE_FILENAMES
        self.assertEqual(_REVIEW_STATE_FILENAMES, REVIEW_STATE_FILENAMES)

    def test_unplaced_markers_refuse_without_force(self):
        path = _write_meta(self._tmp)
        _write_review_state(self._tmp, "desktop", unplaced=2, placed=3)
        _write_review_state(self._tmp, "mobile", unplaced=1, placed=4)
        before = path.read_text(encoding="utf-8")
        with self.assertRaises(UnplacedMarkerError) as cm:
            set_client_verified(path, auto=False)
        self.assertEqual(cm.exception.unplaced_counts, {"desktop": 2, "mobile": 1})
        # Message lists per-device counts.
        msg = str(cm.exception)
        self.assertIn("desktop=2", msg)
        self.assertIn("mobile=1", msg)
        self.assertEqual(path.read_text(encoding="utf-8"), before, "file must be unchanged")

    def test_unplaced_markers_force_promotes_and_records_counts(self):
        path = _write_meta(self._tmp)
        _write_review_state(self._tmp, "desktop", unplaced=2, placed=3)
        _write_review_state(self._tmp, "mobile", unplaced=1, placed=4)
        meta = set_client_verified(
            path, auto=False, force=True, now="2026-05-26T13:00:00Z"
        )
        self.assertEqual(meta["report_state"], REPORT_STATE_CLIENT_VERIFIED)
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        attestation = on_disk["report_state_attestation"]
        self.assertEqual(attestation["forced"], True)
        self.assertEqual(attestation["unplaced_counts"], {"desktop": 2, "mobile": 1})
        self.assertEqual(attestation["promoted_at"], "2026-05-26T13:00:00Z")

    def test_clean_queue_with_multiple_devices_promotes(self):
        path = _write_meta(self._tmp)
        _write_review_state(self._tmp, "desktop", unplaced=0, placed=5)
        _write_review_state(self._tmp, "mobile", unplaced=0, placed=2)
        meta = set_client_verified(path, auto=False, now="2026-05-26T14:00:00Z")
        self.assertEqual(meta["report_state"], REPORT_STATE_CLIENT_VERIFIED)
        self.assertEqual(
            meta["report_state_attestation"]["unplaced_counts"],
            {"desktop": 0, "mobile": 0},
        )
        self.assertFalse(meta["report_state_attestation"]["forced"])

    def test_malformed_review_state_file_is_skipped(self):
        # A single broken review-state file must not block a real engagement
        # whose other devices are clean. (And the corresponding device is
        # absent from unplaced_counts.)
        path = _write_meta(self._tmp)
        _write_review_state(self._tmp, "desktop", unplaced=0, placed=2)
        (self._tmp / "review-state-mobile.json").write_text(
            "not json {{{", encoding="utf-8"
        )
        meta = set_client_verified(path, auto=False, now="2026-05-26T14:30:00Z")
        self.assertEqual(meta["report_state"], REPORT_STATE_CLIENT_VERIFIED)
        self.assertEqual(
            meta["report_state_attestation"]["unplaced_counts"],
            {"desktop": 0},
            "malformed mobile file must not appear in counts",
        )


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
        env_overrides = {"PYTHONIOENCODING": "utf-8"}
        import os
        env = os.environ.copy()
        env.update(env_overrides)
        return subprocess.run(
            [
                sys.executable,
                str(_REPO / "scripts" / "generate-report.py"),
                "--engagement", str(self._tmp),
                "--mark-client-verified",
                *extra,
            ],
            capture_output=True,
            text=True,
            env=env,
        )

    def test_cli_promotes_with_clean_queue(self):
        _write_meta(self._tmp)
        _write_review_state(self._tmp, "desktop", unplaced=0, placed=2)
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        on_disk = json.loads((self._tmp / "meta.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk["report_state"], "client-verified")
        self.assertFalse(on_disk["report_state_attestation"]["forced"])

    def test_cli_refuses_under_auto(self):
        _write_meta(self._tmp)
        _write_review_state(self._tmp, "desktop", unplaced=0, placed=2)
        result = self._run("--auto")
        self.assertNotEqual(result.returncode, 0)
        on_disk = json.loads((self._tmp / "meta.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk["report_state"], "draft", "must stay draft under --auto")

    def test_cli_refuses_with_unplaced_markers(self):
        _write_meta(self._tmp)
        _write_review_state(self._tmp, "desktop", unplaced=3, placed=1)
        result = self._run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("desktop=3", result.stderr)
        on_disk = json.loads((self._tmp / "meta.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk["report_state"], "draft")

    def test_cli_force_bypasses_unplaced_gate(self):
        _write_meta(self._tmp)
        _write_review_state(self._tmp, "desktop", unplaced=3, placed=1)
        result = self._run("--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        on_disk = json.loads((self._tmp / "meta.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk["report_state"], "client-verified")
        self.assertTrue(on_disk["report_state_attestation"]["forced"])
        self.assertEqual(
            on_disk["report_state_attestation"]["unplaced_counts"],
            {"desktop": 3},
        )

    def test_cli_force_does_not_bypass_auto(self):
        _write_meta(self._tmp)
        _write_review_state(self._tmp, "desktop", unplaced=0, placed=2)
        result = self._run("--auto", "--force")
        self.assertNotEqual(result.returncode, 0)
        on_disk = json.loads((self._tmp / "meta.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk["report_state"], "draft")

    def test_cli_refuses_with_no_review_state(self):
        _write_meta(self._tmp)
        result = self._run()
        self.assertNotEqual(result.returncode, 0)
        on_disk = json.loads((self._tmp / "meta.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk["report_state"], "draft")

    def test_cli_force_promotes_with_no_review_state(self):
        _write_meta(self._tmp)
        result = self._run("--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        on_disk = json.loads((self._tmp / "meta.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk["report_state"], "client-verified")
        self.assertTrue(on_disk["report_state_attestation"]["forced"])
        self.assertEqual(on_disk["report_state_attestation"]["unplaced_counts"], {})


if __name__ == "__main__":
    unittest.main()
