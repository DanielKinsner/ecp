"""DOM-modified capture caveat banner (adversarial review 2026-07-08 #15).

contracts/trace-assertion-canary.md §260 + product.md §0: when the acquirer
dismisses overlays (cart drawer, newsletter/media modal, cookie banner, nav
drawer) to reveal the full page, the captured DOM differs from a normal user's
first view. The visual report MUST surface that as a caveat banner so
layout / whitespace / cognitive-load findings carry honest framing. The
mandate existed in the contract but NO renderer implemented it (silently
dropped) until this change.

Pure-helper tests are fast + always run; the end-to-end render test gates on a
committed fixture and Pillow (the renderer encodes screenshot geometry).

Run:
    python -m pytest tests/test_dom_capture_caveat.py
    python -m unittest tests.test_dom_capture_caveat
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.html_builder import dom_capture_caveat, render_dom_caveat_banner  # noqa: E402

_CAVEAT_TEXT = "Captured view was modified during acquisition"
_FIXTURE = _REPO / "tests" / "fixtures" / "2026-05-02-9cd2a2ac"


class DomCaptureCaveatHelper(unittest.TestCase):
    def test_none_when_no_capture_state(self):
        self.assertIsNone(dom_capture_caveat({}))
        self.assertIsNone(dom_capture_caveat({"capture_state": {}}))
        self.assertIsNone(dom_capture_caveat("not a dict"))

    def test_none_when_no_overlays(self):
        self.assertIsNone(dom_capture_caveat({"capture_state": {"overlays_detected": []}}))

    def test_counts_and_dedupes_types(self):
        caveat = dom_capture_caveat({"capture_state": {"overlays_detected": [
            {"type": "cart-drawer"}, {"type": "newsletter-modal"}, {"type": "cart-drawer"},
        ]}})
        self.assertEqual(caveat["count"], 3)
        self.assertEqual(caveat["types"], ["cart-drawer", "newsletter-modal"])

    def test_render_empty_when_none(self):
        self.assertEqual(render_dom_caveat_banner(None), "")

    def test_render_includes_class_types_and_grammar(self):
        html = render_dom_caveat_banner({"count": 1, "types": ["cookie-banner"]})
        self.assertIn('class="dom-caveat-banner"', html)
        self.assertIn(_CAVEAT_TEXT, html)
        self.assertIn("cookie-banner", html)
        self.assertIn("1 overlay was dismissed", html)  # singular grammar

    def test_render_plural_grammar(self):
        html = render_dom_caveat_banner({"count": 2, "types": ["a", "b"]})
        self.assertIn("2 overlays were dismissed", html)


try:
    import PIL  # noqa: F401
    _HAVE_PIL = True
except ImportError:  # pragma: no cover
    _HAVE_PIL = False


@unittest.skipUnless(_FIXTURE.exists() and _HAVE_PIL, "committed fixture + pillow required")
class DomCaptureCaveatRender(unittest.TestCase):
    def _render(self, engagement: Path) -> str:
        result = subprocess.run(
            [sys.executable, "scripts/generate-report.py", "--v2",
             "--engagement", str(engagement), "--device", "desktop",
             "--baton", "baton.json", "--plugin-root", str(_REPO),
             "--output", "vr.html", "--skip-editor"],
            capture_output=True, text=True, encoding="utf-8", cwd=str(_REPO),
        )
        self.assertEqual(result.returncode, 0, f"render failed: {result.stderr[-500:]}")
        return (engagement / "vr.html").read_text(encoding="utf-8")

    def test_no_banner_when_dom_unmodified(self):
        with tempfile.TemporaryDirectory() as td:
            eng = Path(td) / "e"
            shutil.copytree(_FIXTURE, eng)
            self.assertNotIn(_CAVEAT_TEXT, self._render(eng))

    def test_banner_when_overlays_dismissed(self):
        with tempfile.TemporaryDirectory() as td:
            eng = Path(td) / "e"
            shutil.copytree(_FIXTURE, eng)
            baton = json.loads((eng / "baton.json").read_text(encoding="utf-8"))
            baton.setdefault("capture_state", {})["overlays_detected"] = [
                {"type": "cart-drawer", "e_index": "e0"},
                {"type": "newsletter-modal", "e_index": "e1"},
            ]
            (eng / "baton.json").write_text(json.dumps(baton), encoding="utf-8")
            html = self._render(eng)
            self.assertIn(_CAVEAT_TEXT, html)
            self.assertIn("cart-drawer, newsletter-modal", html)


if __name__ == "__main__":
    unittest.main()
