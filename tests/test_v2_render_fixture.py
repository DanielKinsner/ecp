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


class TestBulletedTriagePriorityOrder(unittest.TestCase):
    """Regression (adversarial review 2026-07-08): the triage bullet list
    (``render_bulleted``) must order **CRITICAL first**. CRITICAL is the tier
    reserved for ethics BLOCK findings — the single most urgent thing an
    operator must action. A local rank map ``{HIGH:0, MEDIUM:1, LOW:2}`` omitted
    CRITICAL, folding it into the unknown-priority default and sinking BLOCK
    findings to the BOTTOM of the scan list. The fix reuses the canonical
    ``assembly.models.PRIORITY_ORDER`` (CRITICAL:0). No committed engagement is
    needed — the sort key is a pure function."""

    def _key(self):
        sys.path.insert(0, str(_REPO / "scripts"))
        from report.v2_renderers import _bulleted_sort_key
        return _bulleted_sort_key

    def test_critical_sorts_first(self) -> None:
        key = self._key()
        findings = [
            {"priority": "LOW", "cluster": "pricing", "f_ref": "pricing F-01", "index": 1},
            {"priority": "CRITICAL", "cluster": "trust-credibility", "f_ref": "ethics F-09", "index": 9},
            {"priority": "HIGH", "cluster": "pricing", "f_ref": "pricing F-02", "index": 2},
            {"priority": "MEDIUM", "cluster": "pricing", "f_ref": "pricing F-03", "index": 3},
        ]
        ordered = [f["priority"] for f in sorted(findings, key=key)]
        self.assertEqual(
            ordered[0], "CRITICAL",
            "CRITICAL (ethics BLOCK) must head the triage list, not sink to the bottom.",
        )
        self.assertEqual(ordered, ["CRITICAL", "HIGH", "MEDIUM", "LOW"])

    def test_unknown_priority_still_sorts_last(self) -> None:
        key = self._key()
        findings = [
            {"priority": "WEIRD", "cluster": "pricing", "f_ref": "pricing F-01", "index": 1},
            {"priority": "HIGH", "cluster": "pricing", "f_ref": "pricing F-02", "index": 2},
        ]
        ordered = [f["priority"] for f in sorted(findings, key=key)]
        self.assertEqual(ordered, ["HIGH", "WEIRD"])


if __name__ == "__main__":
    unittest.main()
