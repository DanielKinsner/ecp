"""Live CI coverage for the v2 render pipeline against a COMMITTED fixture.

Most render/review-state tests skip because they gate on gitignored
`docs/ecp/` engagements that were never committed (and can't be — docs/ecp is
gitignored). That left the v2 render pipeline with no pytest coverage in CI
(adversarial review 2026-06-03 §2). This test renders the committed
`tests/fixtures/2026-05-02-9cd2a2ac` v2 engagement end-to-end and asserts the
load-bearing invariants:

  - the report HTML is produced,
  - Priority Path links resolve (no "(not found)" — the P0-3 defect class),
  - the deterministic Placement QA summary is emitted (the Fix#4 fold-in).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_FIXTURE = _REPO / "tests" / "fixtures" / "2026-05-02-9cd2a2ac"


@unittest.skipUnless(_FIXTURE.exists(), f"committed v2 fixture missing: {_FIXTURE}")
class TestV2RenderFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="ecp-v2-render-"))
        self.engagement = self.tmpdir / "engagement"
        shutil.copytree(_FIXTURE, self.engagement)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _render(self, device: str, baton: str):
        result = subprocess.run(
            [sys.executable, "scripts/generate-report.py", "--v2",
             "--engagement", str(self.engagement), "--device", device,
             "--baton", baton, "--plugin-root", str(_REPO),
             "--output", f"visual-report-{device}.html", "--skip-editor"],
            capture_output=True, text=True, encoding="utf-8", cwd=str(_REPO),
        )
        self.assertEqual(result.returncode, 0,
            f"v2 render failed for {device}. stderr: {result.stderr}")
        html = (self.engagement / f"visual-report-{device}.html").read_text(encoding="utf-8")
        return result, html

    def test_desktop_renders_clean(self) -> None:
        result, html = self._render("desktop", "baton.json")
        self.assertGreater(len(html), 1000, "report HTML is implausibly small")
        self.assertNotIn("(not found)", html,
            "Priority Path link did not resolve — F-NN numbering regression (P0-3 class)")
        # Fix#4 fold-in: the render summary surfaces placement QA deterministically.
        self.assertIn("Placement QA:", result.stdout)
        # Post-2026-06-10 the CLI summary is the live methods + an `other`
        # bucket for back-compat strings; previous `section_stacked_manual=`
        # check was a relic of the now-pruned Fix #3 distribution path.
        self.assertIn("unplaced=", result.stdout)

    def test_mobile_renders_clean(self) -> None:
        result, html = self._render("mobile", "baton-mobile.json")
        self.assertGreater(len(html), 1000)
        self.assertNotIn("(not found)", html)
        self.assertIn("Placement QA:", result.stdout)


if __name__ == "__main__":
    unittest.main()
