"""Tests for the durable v1->v2 baton converter (scripts/baton_v1_to_v2.py).

See docs/superpowers/specs/2026-05-29-durable-baton-converter-design.md.

The pure `convert_baton(v1, dom_html, *, device, engagement_id, captured_at)`
maps an acquire_url.py-shape (v1) baton onto schema/baton-v1.json (v2). These
tests pin the behaviors that the per-engagement prototypes got wrong or skipped:
schema validity, e_index sequencing, rect clamping (G14), disjoint sections,
canonical screenshot_ref, title-omit-when-empty, cluster preserve-vs-enrich,
page_head extraction, and overlays-empty-when-occluded.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from jsonschema import Draft202012Validator  # noqa: E402

import baton_v1_to_v2 as conv  # noqa: E402

_SCHEMA = json.loads((REPO / "schema" / "baton-v1.json").read_text(encoding="utf-8"))
_EID = "2026-05-29-3e7bd452"
_CAPTURED = "2026-05-29T15:19:55.000Z"

_DOM = """<!doctype html><html><head>
<title>Stinger Trailer for the Can-Am Ryker</title>
<link rel="canonical" href="https://www.slingmods.com/x"/>
<meta name="description" content="Tow your Ryker with our foldable trailer"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<meta property="og:image" content="https://img.example/x.jpg"/>
</head><body><h1>Stinger</h1></body></html>"""


def _v1(device: str = "desktop", **over: object) -> dict:
    """A minimal, realistic acquire_url.py-shape v1 baton."""
    v1: dict = {
        "status": "COMPLETE",
        "engagement_id": _EID,
        "device": device,
        "dpr": 1,
        "viewport": {"width": 1920, "height": 1080, "dpr": 1},
        "viewport_clear": True,
        "screenshots": [
            {"index": 1, "label": "Above the fold", "scrollY": 0, "path": "desktop-section-1.jpg"},
            {"index": 2, "label": "Sale price block", "scrollY": 900, "path": "desktop-section-2.jpg"},
        ],
        "sections": [
            {"label": "Above the fold (hero and primary CTA)", "scrollY": 0,
             "height": 900, "clusters": ["visual-cta"], "screenshot_index": 1},
            {"label": "Sale price and discounts", "scrollY": 900,
             "height": 900, "clusters": [], "screenshot_index": 2},
        ],
        "elements": [
            {"selector": "h1", "tag": "h1", "text": "Stinger", "class": "product-name",
             "x": 10, "y": 20, "width": 100, "height": 30, "visible": True},
            {"selector": "footer", "tag": "footer", "text": "Info", "class": "",
             "x": -13, "y": -4, "width": 180, "height": 40, "visible": True},
        ],
        "url": "https://www.slingmods.com/x",
        "url_final": "https://www.slingmods.com/x",
        "title": "Stinger Trailer for the Can-Am Ryker",
        "structured_data": [{"@type": "Product", "name": "Stinger"}],
        "pre_hydration_warning": False,
    }
    v1.update(over)
    return v1


def _convert(device: str = "desktop", dom: str = _DOM, **over: object) -> dict:
    return conv.convert_baton(
        _v1(device, **over), dom, device=device,
        engagement_id=_EID, captured_at=_CAPTURED,
    )


class TestSchemaValidity(unittest.TestCase):
    def test_desktop_output_is_schema_valid(self):
        errs = sorted(Draft202012Validator(_SCHEMA).iter_errors(_convert("desktop")),
                      key=lambda e: list(e.path))
        self.assertEqual(errs, [], msg="; ".join(f"{list(e.path)}: {e.message}" for e in errs))

    def test_mobile_output_is_schema_valid(self):
        errs = list(Draft202012Validator(_SCHEMA).iter_errors(_convert("mobile")))
        self.assertEqual(errs, [], msg="; ".join(f"{list(e.path)}: {e.message}" for e in errs))


class TestElements(unittest.TestCase):
    def test_e_index_is_sequential(self):
        v2 = _convert()
        self.assertEqual([e["e_index"] for e in v2["elements"]], ["e0", "e1"])

    def test_negative_rect_coords_clamp_to_zero(self):
        # The footer element has x=-13, y=-4 in the v1 fixture (G14 invariant).
        rects = [e["rect"] for e in _convert()["elements"]]
        footer = rects[1]
        self.assertEqual(footer["x"], 0)
        self.assertEqual(footer["y"], 0)
        self.assertEqual(footer["width"], 180)

    def test_role_derived_from_tag(self):
        v2 = _convert()
        self.assertEqual(v2["elements"][0]["role"], "heading")  # h1
        self.assertEqual(v2["elements"][1]["role"], "contentinfo")  # footer

    def test_is_offscreen_from_visible(self):
        v2 = _convert(elements=[
            {"selector": "div", "tag": "div", "text": "", "class": "",
             "x": 0, "y": 0, "width": 1, "height": 1, "visible": False},
        ])
        self.assertTrue(v2["elements"][0]["is_offscreen"])


class TestSections(unittest.TestCase):
    def test_sections_are_disjoint(self):
        secs = _convert()["sections"]
        for a, b in zip(secs, secs[1:]):
            self.assertLess(a["scroll_y_bottom"], b["scroll_y_top"])

    def test_screenshot_ref_canonical_desktop(self):
        for s in _convert("desktop")["sections"]:
            self.assertRegex(s["screenshot_ref"], r"^section-[0-9]+\.jpg$")

    def test_screenshot_ref_canonical_mobile(self):
        for s in _convert("mobile")["sections"]:
            self.assertRegex(s["screenshot_ref"], r"^section-[0-9]+-mobile\.jpg$")

    def test_clusters_preserved_when_present(self):
        # First section had clusters=["visual-cta"] in the fixture.
        self.assertEqual(_convert()["sections"][0]["clusters"], ["visual-cta"])

    def test_clusters_enriched_when_empty(self):
        # Second section had clusters=[] and a "Sale price and discounts" label.
        clusters = _convert()["sections"][1]["clusters"]
        self.assertTrue(clusters, "empty clusters should be enriched, not left empty")
        self.assertIn("pricing", clusters)

    def test_slug_is_schema_valid(self):
        for s in _convert()["sections"]:
            self.assertRegex(s["slug"], r"^[a-z][a-z0-9-]*$")


class TestPageHead(unittest.TestCase):
    def test_page_head_parsed_from_dom(self):
        ph = _convert()["page_head"]
        self.assertEqual(ph["canonical"], "https://www.slingmods.com/x")
        self.assertEqual(ph["meta_description"], "Tow your Ryker with our foldable trailer")
        self.assertEqual(ph["viewport_meta"], "width=device-width, initial-scale=1")
        self.assertEqual(ph["og_image"], "https://img.example/x.jpg")

    def test_schema_jsonld_from_structured_data(self):
        self.assertEqual(_convert()["page_head"]["schema_jsonld"],
                         [{"@type": "Product", "name": "Stinger"}])

    def test_title_present_when_set(self):
        self.assertEqual(_convert()["page_head"]["title"],
                         "Stinger Trailer for the Can-Am Ryker")

    def test_title_omitted_when_empty(self):
        # Empty v1 title must NOT become null (schema title is non-nullable string).
        v2 = _convert(title="")
        self.assertNotIn("title", v2["page_head"])
        errs = list(Draft202012Validator(_SCHEMA).iter_errors(v2))
        self.assertEqual(errs, [])


class TestCaptureState(unittest.TestCase):
    def test_overlays_empty_when_occluded(self):
        # viewport_clear=False must NOT yield an overlay with e_index=None.
        v2 = _convert(viewport_clear=False)
        self.assertEqual(v2["capture_state"]["overlays_detected"], [])
        errs = list(Draft202012Validator(_SCHEMA).iter_errors(v2))
        self.assertEqual(errs, [])

    def test_page_height_covers_extents(self):
        # footer bottom = 0 (clamped y) + 40; section 2 bottom ~ 1799; viewport 1080.
        v2 = _convert()
        self.assertGreaterEqual(v2["capture_state"]["page_height_px"], 1799)

    def test_hydration_from_warning(self):
        self.assertEqual(_convert(pre_hydration_warning=True)["capture_state"]["hydration"],
                         "pre-hydration")
        self.assertEqual(_convert(pre_hydration_warning=False)["capture_state"]["hydration"],
                         "post-hydration")

    def test_dpr_actual_falls_back(self):
        v2 = _convert("mobile", dpr_fallback=True, viewport={"width": 390, "height": 844, "dpr": 3})
        self.assertEqual(v2["viewport"]["dpr_requested"], 3)
        self.assertEqual(v2["viewport"]["dpr_actual"], 1.0)


class TestEngagementId(unittest.TestCase):
    def test_bad_engagement_id_raises(self):
        with self.assertRaises(conv.BatonConversionError):
            conv.convert_baton(_v1(), _DOM, device="desktop",
                               engagement_id="not-a-valid-id", captured_at=_CAPTURED)

    def test_engagement_id_propagates(self):
        self.assertEqual(_convert()["engagement_id"], _EID)


def _make_engagement(root: str, devices=("desktop", "mobile"), with_shots: bool = True) -> Path:
    d = Path(root) / _EID
    d.mkdir(parents=True, exist_ok=True)
    (d / "baton.json").write_text(json.dumps(_v1("desktop")), encoding="utf-8")
    (d / "dom.html").write_text(_DOM, encoding="utf-8")
    if "mobile" in devices:
        (d / "baton-mobile.json").write_text(json.dumps(_v1("mobile")), encoding="utf-8")
        (d / "dom-mobile.html").write_text(_DOM, encoding="utf-8")
    if with_shots:
        for i in (1, 2):
            (d / f"section-{i}.jpg").write_bytes(b"x")
            (d / f"section-{i}-mobile.jpg").write_bytes(b"x")
    return d


class TestConvertEngagement(unittest.TestCase):
    def test_writes_both_devices_schema_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _make_engagement(tmp)
            res = conv.convert_engagement(d, captured_at=_CAPTURED)
            self.assertEqual(res["desktop"]["status"], "written")
            self.assertEqual(res["mobile"]["status"], "written")
            for name in ("baton.json", "baton-mobile.json"):
                v2 = json.loads((d / name).read_text(encoding="utf-8"))
                self.assertEqual(v2["schema_version"], 1)
                self.assertEqual(list(Draft202012Validator(_SCHEMA).iter_errors(v2)), [])

    def test_v1raw_backup_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _make_engagement(tmp)
            original = json.loads((d / "baton.json").read_text(encoding="utf-8"))
            conv.convert_engagement(d, captured_at=_CAPTURED)
            raw = json.loads((d / "baton.v1raw.json").read_text(encoding="utf-8"))
            self.assertEqual(raw, original)
            self.assertNotIn("schema_version", raw)  # the preserved v1

    def test_idempotent_backup_preserves_v1raw(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _make_engagement(tmp)
            original = json.loads((d / "baton.json").read_text(encoding="utf-8"))
            conv.convert_engagement(d, captured_at=_CAPTURED)
            conv.convert_engagement(d, captured_at=_CAPTURED)  # re-run
            raw = json.loads((d / "baton.v1raw.json").read_text(encoding="utf-8"))
            self.assertEqual(raw, original, "re-run must not clobber v1raw with the v2")
            self.assertEqual(json.loads((d / "baton.json").read_text(encoding="utf-8"))["schema_version"], 1)

    def test_missing_device_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _make_engagement(tmp, devices=("desktop",))
            res = conv.convert_engagement(d, captured_at=_CAPTURED)
            self.assertEqual(res["mobile"]["status"], "skipped")
            self.assertFalse((d / "baton-mobile.json").exists())

    def test_missing_screenshot_warns_but_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _make_engagement(tmp, with_shots=False)
            res = conv.convert_engagement(d, captured_at=_CAPTURED)
            self.assertTrue(any("section-1.jpg" in w for w in res["desktop"]["warnings"]))
            self.assertTrue((d / "baton.json").exists())

    def test_out_dir_leaves_source_untouched(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as out:
            d = _make_engagement(tmp)
            src_before = (d / "baton.json").read_text(encoding="utf-8")
            conv.convert_engagement(d, out_dir=out, captured_at=_CAPTURED)
            self.assertEqual((d / "baton.json").read_text(encoding="utf-8"), src_before)
            self.assertFalse((d / "baton.v1raw.json").exists())
            self.assertEqual(json.loads((Path(out) / "baton.json").read_text(encoding="utf-8"))["schema_version"], 1)

    def test_engagement_id_from_dir_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _make_engagement(tmp)
            conv.convert_engagement(d, captured_at=_CAPTURED)
            self.assertEqual(json.loads((d / "baton.json").read_text(encoding="utf-8"))["engagement_id"], _EID)


class TestCli(unittest.TestCase):
    def test_main_returns_zero_and_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _make_engagement(tmp)
            self.assertEqual(conv.main([str(d)]), 0)
            self.assertEqual(json.loads((d / "baton.json").read_text(encoding="utf-8"))["schema_version"], 1)

    def test_main_device_flag_only_converts_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = _make_engagement(tmp)
            conv.main([str(d), "--device", "desktop"])
            mobile = json.loads((d / "baton-mobile.json").read_text(encoding="utf-8"))
            self.assertNotIn("schema_version", mobile)  # mobile left as v1


if __name__ == "__main__":
    unittest.main()
