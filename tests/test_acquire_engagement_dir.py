"""C1 + C2 regression: acquire_url merges into the lead's dir and auto-upgrades
batons to v2.

awdmods 2026-06-08 run-review:
  C2 — SKILL phase order writes meta.json + audit-trace.log BEFORE acquisition,
       but acquire_url refused a non-empty engagement dir, so the acquirer had
       to wipe the lead's state. _prepare_engagement_dir + --allow-existing +
       _merge_meta let it merge instead of clobber.
  C1 — acquire_url emitted a v1-shape baton and the load-bearing v1->v2
       conversion was an undocumented manual step. _upgrade_batons_to_v2 wires
       it into acquisition (desktop+mobile; idempotent; best-effort).

These exercise the extracted pure helpers — no agent-browser / live capture.

Run:
    python -m unittest tests.test_acquire_engagement_dir
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import acquire_url  # noqa: E402

_EID = "2026-05-29-3e7bd452"
_DOM = (
    "<!doctype html><html><head><title>Stinger</title>"
    '<meta name="description" content="x"/></head><body><h1>Stinger</h1></body></html>'
)


def _v1_baton(device: str = "desktop") -> dict:
    return {
        "status": "COMPLETE",
        "engagement_id": _EID,
        "device": device,
        "dpr": 1,
        "viewport": {"width": 1920, "height": 1080, "dpr": 1},
        "viewport_clear": True,
        "screenshots": [
            {"index": 1, "label": "Above the fold", "scrollY": 0, "path": "section-1.jpg"},
        ],
        "sections": [
            {"label": "Above the fold", "scrollY": 0, "height": 900,
             "clusters": ["visual-cta"], "screenshot_index": 1},
        ],
        "elements": [
            {"selector": "h1", "tag": "h1", "text": "Stinger", "class": "name",
             "x": 10, "y": 20, "width": 100, "height": 30, "visible": True},
        ],
        "url": "https://example.com/x",
        "url_final": "https://example.com/x",
        "title": "Stinger",
        "structured_data": [],
        "pre_hydration_warning": False,
    }


class TestPrepareEngagementDir(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_fresh_dir_is_created_and_proceeds(self):
        eng = self.root / "fresh"
        self.assertIsNone(acquire_url._prepare_engagement_dir(eng, allow_existing=False))
        self.assertTrue(eng.is_dir())

    def test_existing_empty_dir_proceeds(self):
        eng = self.root / "empty"
        eng.mkdir()
        self.assertIsNone(acquire_url._prepare_engagement_dir(eng, allow_existing=False))

    def test_nonempty_dir_without_flag_aborts(self):
        eng = self.root / "lead"
        eng.mkdir()
        (eng / "meta.json").write_text("{}", encoding="utf-8")
        self.assertEqual(acquire_url._prepare_engagement_dir(eng, allow_existing=False), 1)

    def test_nonempty_dir_with_flag_proceeds(self):
        eng = self.root / "lead"
        eng.mkdir()
        (eng / "meta.json").write_text("{}", encoding="utf-8")
        self.assertIsNone(acquire_url._prepare_engagement_dir(eng, allow_existing=True))


class TestMergeMeta(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.eng = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_existing_meta_returns_acquirer_meta(self):
        acq = {"engagement_id": _EID, "mode": "quick-scan", "status": "in_progress"}
        self.assertEqual(acquire_url._merge_meta(self.eng, acq), acq)

    def test_lead_fields_win_acquirer_fills_gaps(self):
        lead = {
            "engagement_id": _EID,
            "engagement_status": "in_progress",
            "report_state": "draft",
            "reflection_state": "draft",
            "clusters": ["pricing", "visual-cta"],
            "status": "lead-set",
        }
        (self.eng / "meta.json").write_text(json.dumps(lead), encoding="utf-8")
        acq = {"engagement_id": _EID, "mode": "quick-scan", "status": "in_progress",
               "confidence": "High"}
        merged = acquire_url._merge_meta(self.eng, acq)
        # Lead-authored fields preserved.
        self.assertEqual(merged["engagement_status"], "in_progress")
        self.assertEqual(merged["report_state"], "draft")
        self.assertEqual(merged["clusters"], ["pricing", "visual-cta"])
        self.assertEqual(merged["status"], "lead-set")  # lead wins over acquirer
        # Acquirer-only field still added.
        self.assertEqual(merged["confidence"], "High")

    def test_corrupt_existing_meta_falls_back_to_acquirer(self):
        (self.eng / "meta.json").write_text("{not json", encoding="utf-8")
        acq = {"engagement_id": _EID, "mode": "quick-scan"}
        self.assertEqual(acquire_url._merge_meta(self.eng, acq), acq)


class TestUpgradeBatonsToV2(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.eng = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _write_v1(self, name: str = "baton.json", device: str = "desktop"):
        (self.eng / name).write_text(json.dumps(_v1_baton(device)), encoding="utf-8")
        (self.eng / ("dom.html" if name == "baton.json" else "dom-mobile.html")).write_text(
            _DOM, encoding="utf-8")

    def test_desktop_baton_upgraded_to_v2_with_backup(self):
        self._write_v1()
        acquire_url._upgrade_batons_to_v2(self.eng, ("desktop",), _EID)
        v2 = json.loads((self.eng / "baton.json").read_text(encoding="utf-8"))
        self.assertEqual(v2.get("schema_version"), 1)
        self.assertIn("capture_state", v2)
        self.assertTrue(v2["elements"][0]["e_index"].startswith("e"))
        # v1 raw preserved for idempotency / recovery.
        self.assertTrue((self.eng / "baton.v1raw.json").exists())

    def test_laptop_is_left_as_v1(self):
        self._write_v1()
        acquire_url._upgrade_batons_to_v2(self.eng, ("laptop",), _EID)
        baton = json.loads((self.eng / "baton.json").read_text(encoding="utf-8"))
        self.assertNotIn("schema_version", baton)  # untouched v1
        self.assertFalse((self.eng / "baton.v1raw.json").exists())

    def test_non_schema_engagement_id_skips_gracefully(self):
        """A legacy non-canonical id (ecp-cursor-...) does not match the
        schema id regex; conversion must be skipped, not raised, leaving v1."""
        self._write_v1()
        # Must not raise.
        acquire_url._upgrade_batons_to_v2(self.eng, ("desktop",), "ecp-cursor-deadbeef99")
        baton = json.loads((self.eng / "baton.json").read_text(encoding="utf-8"))
        self.assertNotIn("schema_version", baton)  # still v1

    def test_default_engagement_id_is_schema_canonical(self):
        """The 2026-06-10 live smoke caught the old ecp-cursor-* default: it
        failed the YYYY-MM-DD-<8hex> schema pattern, so the auto-convert
        best-effort-refused EVERY default-id run. The default must be canonical
        so conversion succeeds end-to-end."""
        import re
        eid = acquire_url._default_engagement_id()
        self.assertRegex(eid, r"^\d{4}-\d{2}-\d{2}-[0-9a-f]{8}$")
        # And it must round-trip the converter (the actual failure mode).
        self._write_v1()
        acquire_url._upgrade_batons_to_v2(self.eng, ("desktop",), eid)
        baton = json.loads((self.eng / "baton.json").read_text(encoding="utf-8"))
        self.assertIn("capture_state", baton)  # converted to v2


class TestRevealLazyAndAnimations(unittest.TestCase):
    """Plumbing for the pre-capture reveal (the JS behavior needs a live browser;
    here we cover that it returns the eval result and is failure-safe, and that the
    injected JS targets the right things — the awdmods 2026-06-08 root cause)."""

    def test_returns_eval_report(self):
        report = {"lazy_imgs": 19, "reveal_els": 19, "error": None}
        self.assertEqual(acquire_url._reveal_lazy_and_animations(lambda src: report), report)

    def test_swallows_eval_failure(self):
        def boom(src):
            raise RuntimeError("agent-browser eval failed")
        self.assertEqual(acquire_url._reveal_lazy_and_animations(boom), {})

    def test_non_dict_result_is_normalized(self):
        self.assertEqual(acquire_url._reveal_lazy_and_animations(lambda src: None), {})

    def test_injected_js_targets_the_failure_mode(self):
        js = acquire_url._REVEAL_LAZY_AND_ANIMATIONS_JS
        # Shopify Dawn scroll-trigger reveal neutralization + lazy eager-load.
        self.assertIn("scroll-trigger--offscreen", js)
        self.assertIn('animate--', js)
        self.assertIn("loading='eager'", js)
        self.assertIn("opacity", js)


class EngagementIdTraversalGuard(unittest.TestCase):
    """Adversarial review 2026-07-08 #12: --engagement-id is joined onto
    docs/ecp/ to build the output dir. A value like '../../scripts' or an
    absolute path would let acquisition write / _prepare_engagement_dir clear
    files outside the engagement tree. _validate_engagement_id restricts it to
    a filename slug."""

    def test_accepts_valid_slugs(self):
        for eid in ("2026-07-08-deadbeef", "2300-slingmods_pdp", "ok-1", "abc123"):
            self.assertIsNone(acquire_url._validate_engagement_id(eid), eid)

    def test_rejects_traversal_and_absolute(self):
        for eid in ("../../scripts", "..", "a/b", "a\\b", "C:/Windows",
                    "/etc/passwd", "", "   ", " has space", ".hidden"):
            self.assertIsNotNone(
                acquire_url._validate_engagement_id(eid),
                f"{eid!r} should be rejected as unsafe",
            )


if __name__ == "__main__":
    unittest.main()
