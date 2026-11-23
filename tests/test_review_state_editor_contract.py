"""Guard: the hotspot editor's review-state edits actually reach the report.

Every field the editor writes is only worth writing if the canonical renderer
reads it. Two of them silently did not, found 2026-07-24:

  1. ``callout_visible: false`` — the editor's "Callout" tick box. The renderer
     only used it to gate ``review_callout_position``; the report's
     ``renderCallout`` had no visibility check at all, so unticking the box
     hid the callout in the EDITOR and it came straight back in the client
     deliverable. Root cause: a falsy-but-meaningful flag inside an
     ``any(...)`` truthiness sweep (``_review_override_enabled``) plus a
     missing last-mile gate in the report runtime.
  2. severity — the editor's color swatches are LABELLED by severity
     ("Critical red", "High orange") but only ever set ``marker.stroke``. The
     finding's real priority (sidebar chip, severity CSS class, metric counts,
     sort order) was unreachable from the editor. ``severity_override`` is the
     explicit, opt-in field for it.

These assert at the FINAL-HTML level through the real
``generate-report.py --from-review`` CLI, because both bugs lived in the gap
between "helper writes the field" and "runtime honors the field" — the exact
seam a helper-level unit test steps over.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from report import html_builder as v1  # noqa: E402
from report import v2_html_builder as v2  # noqa: E402

_REPO = Path(__file__).resolve().parent.parent
_FIXTURE = _REPO / "tests" / "fixtures" / "2026-05-02-9cd2a2ac"


def _desktop_refs(engagement: Path, count: int) -> list[str]:
    manifest = json.loads(
        (engagement / "canonical-f-refs-manifest.json").read_text(encoding="utf-8")
    )
    refs = [
        e["f_ref"]
        for e in manifest.get("entries", [])
        if "desktop" in (e.get("devices_present") or [])
    ]
    if len(refs) < count:
        raise AssertionError(
            f"fixture manifest has only {len(refs)} desktop refs, need {count}"
        )
    return refs[:count]


class TestReviewOverrideGate(unittest.TestCase):
    """`_review_override_enabled` must see falsy-but-deliberate operator edits."""

    def test_callout_visible_false_alone_enables_overrides(self) -> None:
        review = {"f_ref": "x", "status": "needs_review", "callout_visible": False}
        self.assertTrue(
            v1._review_override_enabled(review),
            "callout_visible:false as the only edit read as 'untouched' — the "
            "hidden-callout bug is back (falsy value lost in the any() sweep)",
        )

    def test_callout_visible_true_alone_does_not_enable_overrides(self) -> None:
        # The generator seeds every finding with callout_visible:True. If that
        # counted as an edit, EVERY finding would take the override path and
        # untouched AI markers would be replaced wholesale.
        review = {"f_ref": "x", "status": "needs_review", "callout_visible": True}
        self.assertFalse(
            v1._review_override_enabled(review),
            "the default callout_visible:True must not count as an operator edit",
        )

    def test_severity_override_enables_overrides(self) -> None:
        review = {"f_ref": "x", "status": "needs_review", "severity_override": "critical"}
        self.assertTrue(v1._review_override_enabled(review))

    def test_v1_and_v2_gates_agree(self) -> None:
        # v1 and v2 keep near-duplicate copies of this gate. A fix landing in
        # only one path is this repo's recurring drift class.
        cases = [
            {"f_ref": "x", "status": "needs_review", "callout_visible": False},
            {"f_ref": "x", "status": "needs_review", "callout_visible": True},
            {"f_ref": "x", "status": "needs_review", "severity_override": "high"},
            {"f_ref": "x", "status": "needs_review", "element_override": ".price"},
            {"f_ref": "x", "status": "approved"},
            {"f_ref": "x", "status": "needs_review"},
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(
                    v1._review_override_enabled(case),
                    v2._review_override_enabled(case),
                    "v1 and v2 review-override gates disagree — one path was fixed",
                )


class TestReviewSeverityNormalization(unittest.TestCase):
    """Only real severities may repriority a finding."""

    def test_accepts_known_severities_case_insensitively(self) -> None:
        for value in ("critical", "HIGH", " Medium ", "low", "info"):
            with self.subTest(value=value):
                self.assertEqual(v1._review_severity({"severity_override": value}),
                                 value.strip().lower())

    def test_rejects_unknown_and_empty(self) -> None:
        for value in (None, "", "  ", "urgent", "P0", 3, True):
            with self.subTest(value=value):
                self.assertIsNone(v1._review_severity({"severity_override": value}))


@unittest.skipUnless(_FIXTURE.exists(), f"committed v2 fixture missing: {_FIXTURE}")
class TestEditorEditsReachFinalReport(unittest.TestCase):
    """One real --from-review render; assert the editor's edits survived it."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmpdir = Path(tempfile.mkdtemp(prefix="ecp-editor-contract-"))
        cls.engagement = cls.tmpdir / "engagement"
        shutil.copytree(_FIXTURE, cls.engagement)

        cls.hidden_callout_ref, cls.severity_ref, cls.text_ref = _desktop_refs(
            cls.engagement, 3
        )

        review_state = {
            "device": "desktop",
            "slides": [{"slide_id": "slide-contract"}],
            "findings": [
                {
                    # Only edit: hide the callout. Status stays needs_review so
                    # the falsy-flag path is what carries it.
                    "f_ref": cls.hidden_callout_ref,
                    "status": "needs_review",
                    "callout_visible": False,
                },
                {
                    "f_ref": cls.severity_ref,
                    "status": "edited",
                    "severity_override": "critical",
                },
                {
                    "f_ref": cls.text_ref,
                    "status": "edited",
                    "finding_title_override": "OPERATOR REWROTE THIS TITLE",
                    "recommendation_override": "OPERATOR REWROTE THIS RECOMMENDATION",
                    "callout_body_override": "OPERATOR REWROTE THIS CALLOUT BODY",
                },
            ],
            "markers": [
                {
                    "marker_id": "contract-rect",
                    "f_ref": cls.severity_ref,
                    "slide_id": "slide-contract",
                    "shape": "rect",
                    "x_pct": 15,
                    "y_pct": 25,
                    "w_pct": 20,
                    "h_pct": 10,
                    "severity": "critical",
                    "source": "manual",
                },
            ],
        }
        (cls.engagement / "review-state-contract.json").write_text(
            json.dumps(review_state, indent=2), encoding="utf-8"
        )

        cls.result = subprocess.run(
            [sys.executable, "scripts/generate-report.py",
             "--engagement", str(cls.engagement),
             "--device", "desktop",
             "--from-review", "review-state-contract.json",
             "--plugin-root", str(_REPO),
             "--output", "visual-report-desktop-final.html"],
            capture_output=True, text=True, encoding="utf-8", cwd=str(_REPO),
        )
        out = cls.engagement / "visual-report-desktop-final.html"
        cls.html = out.read_text(encoding="utf-8") if out.exists() else ""
        cls.payload = cls._extract_findings_payload(cls.html)

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    @staticmethod
    def _extract_findings_payload(html: str) -> list[dict]:
        """Pull the `var FINDINGS = [...]` runtime payload back out of the HTML."""
        match = re.search(r"var FINDINGS\s*=\s*(\[.*?\]);\n", html, re.DOTALL)
        if not match:
            return []
        raw = match.group(1).replace("<\\/", "</").replace("<\\!--", "<!--")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return []

    def _finding(self, ref: str) -> dict:
        for entry in self.payload:
            if entry.get("f_ref") == ref:
                return entry
        raise AssertionError(f"{ref} missing from the rendered FINDINGS payload")

    def test_render_succeeds(self) -> None:
        self.assertEqual(
            self.result.returncode, 0,
            f"--from-review render failed. stderr: {self.result.stderr}",
        )
        self.assertTrue(self.payload, "could not parse the FINDINGS runtime payload")

    def test_callout_visible_false_marks_callout_hidden(self) -> None:
        self.assertTrue(
            self._finding(self.hidden_callout_ref).get("review_callout_hidden"),
            "callout_visible:false did not reach the report payload — unticking "
            "'Callout' in the editor is a no-op again",
        )

    def test_untouched_findings_keep_their_callout(self) -> None:
        others = [
            f for f in self.payload
            if f.get("f_ref") != self.hidden_callout_ref
        ]
        self.assertTrue(others, "fixture rendered only one finding")
        self.assertFalse(
            any(f.get("review_callout_hidden") for f in others),
            "hiding one callout suppressed callouts on other findings",
        )

    def test_report_runtime_honors_the_hidden_callout_flag(self) -> None:
        # The payload field is useless without the last-mile gate in the report
        # JS — that missing gate WAS the bug.
        self.assertIn(
            "review_callout_hidden", self.html.split("var FINDINGS")[0] + self.html,
        )
        self.assertRegex(
            self.html,
            r"if \(f\.review_callout_hidden\)",
            "report runtime lost its renderCallout visibility gate",
        )

    def test_severity_override_repriorities_the_finding(self) -> None:
        self.assertEqual(
            self._finding(self.severity_ref).get("priority"), "CRITICAL",
            "severity_override did not change the finding's rendered priority — "
            "editor severity is cosmetic again",
        )

    def test_text_overrides_reach_the_report(self) -> None:
        entry = self._finding(self.text_ref)
        self.assertEqual(entry.get("title"), "OPERATOR REWROTE THIS TITLE")
        self.assertEqual(
            entry.get("recommendation"), "OPERATOR REWROTE THIS RECOMMENDATION"
        )
        self.assertEqual(
            entry.get("review_callout_body"), "OPERATOR REWROTE THIS CALLOUT BODY"
        )


if __name__ == "__main__":
    unittest.main()
