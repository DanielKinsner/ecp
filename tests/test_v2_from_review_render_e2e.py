"""End-to-end guard: the --from-review v2 render through generate-report.py.

The 2026-06-10 post-roadmap fix plan (V1) asked for a guard that drives
``generate_v2_report`` with a hidden, coord-less marker. The V1/V2 guards in
``test_v2_review_state_marker_render.py`` call
``_apply_review_state_to_slide_markers`` directly — one level below the entry
point that shipped the phantom-(50,50) bug (the pre-fix helper-only coverage
gap was exactly how V1 escaped). This test runs the REAL CLI
(``generate-report.py --from-review``) over the committed
``tests/fixtures/2026-05-02-9cd2a2ac`` engagement with a crafted review-state
and asserts at the final-HTML level:

  - a hidden, coord-less marker (the ``_unplaced_marker`` shape) emits NO
    phantom point hotspot at the (50,50) default — the pre-V1 signature is
    ``left:calc(50.00% - 16px);top:calc(50.00% - 16px)``,
  - a placed operator rect override renders at its exact zone geometry,
  - a point marker stored as ``cx_pct``/``cy_pct`` (the editor's point
    format, V2) renders centered at those coords, not at the 50/50 default.
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
_FIXTURE = _REPO / "tests" / "fixtures" / "2026-05-02-9cd2a2ac"

_PHANTOM_50_50 = "left:calc(50.00% - 16px);top:calc(50.00% - 16px)"


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


@unittest.skipUnless(_FIXTURE.exists(), f"committed v2 fixture missing: {_FIXTURE}")
class TestFromReviewRenderE2E(unittest.TestCase):
    """One real --from-review render, asserted three ways."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmpdir = Path(tempfile.mkdtemp(prefix="ecp-from-review-e2e-"))
        cls.engagement = cls.tmpdir / "engagement"
        shutil.copytree(_FIXTURE, cls.engagement)

        hidden_ref, rect_ref, point_ref = _desktop_refs(cls.engagement, 3)
        cls.hidden_ref = hidden_ref

        review_state = {
            "device": "desktop",
            "slides": [{"slide_id": "slide-e2e"}],
            "findings": [
                {
                    "f_ref": ref,
                    "status": "approved",
                    "callout_position": {"x_pct": 12, "y_pct": 12, "w_pct": 24, "h_pct": 8},
                    "callout_color": "#facc15",
                }
                for ref in (hidden_ref, rect_ref, point_ref)
            ],
            "markers": [
                # The _unplaced_marker shape: hidden, no geometry at all.
                {
                    "marker_id": "e2e-hidden-manual",
                    "f_ref": hidden_ref,
                    "slide_id": "slide-e2e",
                    "shape": "point",
                    "hidden": True,
                    "severity": "high",
                },
                {
                    "marker_id": "e2e-rect-manual",
                    "f_ref": rect_ref,
                    "slide_id": "slide-e2e",
                    "shape": "rect",
                    "x_pct": 10.5,
                    "y_pct": 20.25,
                    "w_pct": 30,
                    "h_pct": 12,
                    "severity": "medium",
                },
                # Editor point format (tools/editor/editor.js:931): cx/cy only.
                {
                    "marker_id": "e2e-point-manual",
                    "f_ref": point_ref,
                    "slide_id": "slide-e2e",
                    "shape": "point",
                    "cx_pct": 33.25,
                    "cy_pct": 44.5,
                    "severity": "low",
                },
            ],
        }
        review_path = cls.engagement / "review-state-e2e.json"
        review_path.write_text(json.dumps(review_state, indent=2), encoding="utf-8")

        cls.result = subprocess.run(
            [sys.executable, "scripts/generate-report.py",
             "--engagement", str(cls.engagement),
             "--device", "desktop",
             "--from-review", "review-state-e2e.json",
             "--plugin-root", str(_REPO),
             "--output", "visual-report-desktop-final.html"],
            capture_output=True, text=True, encoding="utf-8", cwd=str(_REPO),
        )
        out = cls.engagement / "visual-report-desktop-final.html"
        cls.html = out.read_text(encoding="utf-8") if out.exists() else ""

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def test_render_succeeds(self) -> None:
        self.assertEqual(
            self.result.returncode, 0,
            f"--from-review render failed. stderr: {self.result.stderr}",
        )
        self.assertGreater(len(self.html), 1000, "final HTML is implausibly small")

    def test_hidden_unplaced_marker_emits_no_phantom_50_50(self) -> None:
        self.assertNotIn(
            _PHANTOM_50_50, self.html,
            f"phantom (50,50) point hotspot in the final render — the V1 bug "
            f"class is back (hidden/coord-less marker for {self.hidden_ref} "
            f"defaulted to slide-center)",
        )

    def test_operator_rect_override_renders_exact_zone(self) -> None:
        self.assertIn(
            "left:10.50%;top:20.25%;width:30.00%;height:12.00%", self.html,
            "operator rect override did not render at its exact zone geometry",
        )

    def test_editor_point_marker_renders_at_center(self) -> None:
        self.assertIn(
            "left:calc(33.25% - 16px);top:calc(44.50% - 16px)", self.html,
            "cx_pct/cy_pct point marker did not render at its center (V2 bug "
            "class: geometry family not read, collapsed to default)",
        )


if __name__ == "__main__":
    unittest.main()
