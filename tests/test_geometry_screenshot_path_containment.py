"""Guard: screenshot_natural_size must not read outside the engagement dir.

Regression for the repo-wide-review D3 finding (2026-06-18). screenshot_ref is
baton/section-controlled, and screenshot_natural_size opened
``engagement_dir / screenshot_ref`` with no containment check — unlike the
guarded sibling read in html_builder._process_screenshots. A crafted baton with
``screenshot_ref: "../../secret.jpg"`` could point the reader at an arbitrary
local file. The fix routes the ref through resolve_within_base and falls back to
the viewport size on escape.

Run:
    python -m pytest tests/test_geometry_screenshot_path_containment.py
    python -m unittest tests.test_geometry_screenshot_path_containment
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts"))

from report.geometry import screenshot_natural_size  # noqa: E402

try:
    from PIL import Image
    _HAVE_PIL = True
except ImportError:  # pragma: no cover
    _HAVE_PIL = False


@unittest.skipUnless(_HAVE_PIL, "pillow required to encode screenshot fixtures")
class ScreenshotPathContainment(unittest.TestCase):
    def test_in_engagement_screenshot_returns_real_size(self):
        with tempfile.TemporaryDirectory() as d:
            eng = Path(d) / "eng"
            eng.mkdir()
            Image.new("RGB", (61, 43)).save(str(eng / "shot.jpg"), "JPEG")
            self.assertEqual(
                screenshot_natural_size("shot.jpg", eng, {"width": 300, "height": 600}),
                (61, 43),
            )

    def test_escaping_ref_does_not_leak_outside_file(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            eng = root / "eng"
            eng.mkdir()
            # An image OUTSIDE the engagement dir with distinctive dimensions.
            Image.new("RGB", (999, 777)).save(str(root / "outside.jpg"), "JPEG")

            result = screenshot_natural_size("../outside.jpg", eng, {"width": 300, "height": 600})

            # The escaping ref must NOT resolve to the outside file's dimensions;
            # it falls back to a viewport-derived size instead.
            self.assertNotEqual(result, (999, 777))


if __name__ == "__main__":
    unittest.main()
