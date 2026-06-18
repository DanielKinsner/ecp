"""Guard: a missing screenshot must not misalign later slides' hotspots.

Regression for the repo-wide-review D1 finding (2026-06-18). _process_screenshots
skips a missing screenshot file (`continue`), which COMPACTS slide_base64, but
slide_markers is keyed by absolute slide index. So a single missing screenshot
shifted every later slide's image while its hotspots kept the old index — every
later slide rendered its hotspots on the wrong picture (product.md §4.2: a wrong
hotspot is the worst outcome). The fix returns slide_index_remap (absolute ->
compacted) and the caller realigns slide_markers to it, dropping markers whose
slide image is missing.

Run:
    python -m pytest tests/test_html_builder_missing_screenshot_alignment.py
    python -m unittest tests.test_html_builder_missing_screenshot_alignment
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts"))

from report.html_builder import _process_screenshots  # noqa: E402

try:
    from PIL import Image
    _HAVE_PIL = True
except ImportError:  # pragma: no cover
    _HAVE_PIL = False


def _write_jpeg(path: Path) -> None:
    Image.new("RGB", (12, 12), (40, 40, 40)).save(str(path), "JPEG")


@unittest.skipUnless(_HAVE_PIL, "pillow required to encode screenshot fixtures")
class MissingScreenshotKeepsSlidesAligned(unittest.TestCase):
    def _baton(self, names):
        return {"viewport": {"width": 390, "height": 844},
                "screenshots": [{"path": n} for n in names]}

    def test_all_present_is_identity_remap(self):
        with tempfile.TemporaryDirectory() as d:
            eng = Path(d)
            for n in ("s0.jpg", "s1.jpg", "s2.jpg"):
                _write_jpeg(eng / n)
            out = _process_screenshots(eng, self._baton(["s0.jpg", "s1.jpg", "s2.jpg"]), {})
            self.assertEqual(len(out["slide_base64"]), 3)
            self.assertEqual(out["slide_index_remap"], {0: 0, 1: 1, 2: 2})

    def test_missing_middle_screenshot_compacts_and_remaps(self):
        with tempfile.TemporaryDirectory() as d:
            eng = Path(d)
            _write_jpeg(eng / "s0.jpg")
            # s1.jpg intentionally absent
            _write_jpeg(eng / "s2.jpg")
            out = _process_screenshots(eng, self._baton(["s0.jpg", "s1.jpg", "s2.jpg"]), {})

            # slide_base64 compacted to the two present files
            self.assertEqual(len(out["slide_base64"]), 2)
            # absolute index 2 now lives at compacted index 1; absolute 1 is gone
            self.assertEqual(out["slide_index_remap"], {0: 0, 2: 1})

            # Applying the remap (the caller's realignment) keeps slide 2's
            # markers paired with slide 2's image (now at compacted index 1),
            # and drops the missing slide 1's markers.
            slide_markers = {0: ["m_on_s0"], 1: ["m_on_missing_s1"], 2: ["m_on_s2"]}
            remap = out["slide_index_remap"]
            realigned = {remap[k]: v for k, v in slide_markers.items() if k in remap}
            self.assertEqual(realigned, {0: ["m_on_s0"], 1: ["m_on_s2"]})


if __name__ == "__main__":
    unittest.main()
