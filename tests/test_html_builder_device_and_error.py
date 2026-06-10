"""Regression tests for html_builder.py C4 + C6.

C4 (device suffix): ``_attach_display_indices`` must honour the same
device-suffix naming rule as ``_load_priority_path_stories``. Before the
fix, every non-laptop render missed its ``finding-groups-{device}.json``,
display indices stayed positional, and Priority Path refs degraded to
``(not found)``.

C6 (loud fallback): when the Priority Path sidecar is present but
malformed/unreadable, ``_load_priority_path_stories`` MUST surface a
visible ERROR card instead of silently regex-scraping audit.md. When
the sidecar is absent and the markdown fallback runs, parsed refs MUST
be validated against the actual findings set and dropped if they do not
resolve.

Run:
    python -m pytest tests/test_html_builder_device_and_error.py
    python -m unittest tests.test_html_builder_device_and_error
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts"))

from scripts.report.html_builder import (  # noqa: E402
    _attach_display_indices,
    _load_priority_path_stories,
)
from scripts.report.templates.components import build_priority_tab_html  # noqa: E402


class AttachDisplayIndicesDeviceSuffix(unittest.TestCase):
    """C4: finding-groups-{device}.json must be read for non-laptop devices."""

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="ecp-c4-"))
        self.findings = [
            {"cluster": "visual-cta", "section": "hero", "title": "A"},
            {"cluster": "visual-cta", "section": "hero", "title": "B"},
            {"cluster": "pricing", "section": "price-block", "title": "C"},
        ]
        self.groups = [
            {
                "cluster": "visual-cta",
                "section": "hero",
                "finding_indices": [49, 50],
            },
            {
                "cluster": "pricing",
                "section": "price-block",
                "finding_indices": [69],
            },
        ]

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_groups(self, name: str) -> None:
        (self.tmpdir / name).write_text(
            json.dumps(self.groups), encoding="utf-8",
        )

    def test_desktop_uses_device_suffixed_groups_file(self) -> None:
        """desktop render reads finding-groups-desktop.json."""
        self._write_groups("finding-groups-desktop.json")
        findings = [dict(f) for f in self.findings]
        _attach_display_indices(findings, self.tmpdir, device="desktop")
        self.assertEqual(findings[0]["display_index"], 49)
        self.assertEqual(findings[1]["display_index"], 50)
        self.assertEqual(findings[2]["display_index"], 69)

    def test_mobile_uses_device_suffixed_groups_file(self) -> None:
        """mobile render reads finding-groups-mobile.json."""
        self._write_groups("finding-groups-mobile.json")
        findings = [dict(f) for f in self.findings]
        _attach_display_indices(findings, self.tmpdir, device="mobile")
        self.assertEqual(findings[0]["display_index"], 49)
        self.assertEqual(findings[2]["display_index"], 69)

    def test_laptop_uses_bare_groups_file(self) -> None:
        """laptop keeps the historic bare finding-groups.json filename."""
        self._write_groups("finding-groups.json")
        findings = [dict(f) for f in self.findings]
        _attach_display_indices(findings, self.tmpdir, device="laptop")
        self.assertEqual(findings[0]["display_index"], 49)
        self.assertEqual(findings[2]["display_index"], 69)

    def test_desktop_does_not_read_bare_groups_file(self) -> None:
        """Cross-check: if only the bare file exists and device=desktop,
        no display_index is stamped (no silent cross-device leak)."""
        self._write_groups("finding-groups.json")
        findings = [dict(f) for f in self.findings]
        _attach_display_indices(findings, self.tmpdir, device="desktop")
        for f in findings:
            self.assertNotIn("display_index", f)

    def test_default_device_argument_still_laptop(self) -> None:
        """Back-compat: callers that omit the device kwarg get the laptop
        behaviour (bare filename)."""
        self._write_groups("finding-groups.json")
        findings = [dict(f) for f in self.findings]
        _attach_display_indices(findings, self.tmpdir)
        self.assertEqual(findings[0]["display_index"], 49)


class LoadPriorityPathStoriesLoudFallback(unittest.TestCase):
    """C6: loud fallback when sidecar present but malformed; markdown-fallback
    refs validated against findings.
    """

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="ecp-c6-"))
        # Minimal findings set: pricing F-49 resolves, anything else does not.
        self.findings = [
            {
                "cluster": "pricing",
                "section": "price",
                "display_index": 49,
                "title": "Real finding",
            },
        ]

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_audit_md(self, content: str) -> None:
        (self.tmpdir / "audit.md").write_text(content, encoding="utf-8")

    def test_malformed_sidecar_renders_visible_error_marker(self) -> None:
        """Sidecar exists but is not valid JSON -> error sentinel returned,
        and the rendered HTML surfaces a priority-card-error block. The
        legacy silent regex-scrape MUST NOT run."""
        sidecar = self.tmpdir / "priority-path-stories.json"
        sidecar.write_text("{ this is not json", encoding="utf-8")
        # Provide audit.md with refs that WOULD parse if the silent
        # fallback ran — proof of the error path: no scraped refs leak.
        self._write_audit_md(
            "## Priority Path\n\n"
            "### 1. Bogus story (HIGH)\n\n"
            "Body.\n\n"
            "**Do this:** something\n\n"
            "**Underlying findings:** pricing F-99\n\n"
        )
        stories = _load_priority_path_stories(
            self.tmpdir, "laptop", "audit.md", findings=self.findings,
        )
        self.assertEqual(len(stories), 1)
        self.assertTrue(stories[0].get("priority_path_error"))
        # Scraped audit.md refs must not have leaked through.
        for story in stories:
            for ref in story.get("underlying") or []:
                self.assertNotEqual(ref.get("index"), 99)
        html = build_priority_tab_html(stories, findings_by_fid={})
        self.assertIn("priority-card-error", html)
        self.assertIn("ERROR", html)

    def test_sidecar_invalid_shape_renders_visible_error(self) -> None:
        """Sidecar is valid JSON but missing the stories list -> visible
        error, not silent fallback."""
        sidecar = self.tmpdir / "priority-path-stories.json"
        sidecar.write_text(json.dumps({"not_stories": []}), encoding="utf-8")
        self._write_audit_md("")
        stories = _load_priority_path_stories(
            self.tmpdir, "laptop", "audit.md", findings=self.findings,
        )
        self.assertEqual(len(stories), 1)
        self.assertTrue(stories[0].get("priority_path_error"))

    def test_absent_sidecar_drops_bogus_parsed_refs(self) -> None:
        """No sidecar at all -> markdown fallback runs, but any parsed F-N
        that does not resolve against ``findings`` is dropped instead of
        rendering as a confident (not found) row downstream."""
        # No sidecar written. audit.md cites a bogus ref.
        self._write_audit_md(
            "## Priority Path\n\n"
            "### 1. Mixed refs (HIGH)\n\n"
            "Body.\n\n"
            "**Do this:** something\n\n"
            "**Underlying findings:** pricing F-49, pricing F-99\n\n"
        )
        stories = _load_priority_path_stories(
            self.tmpdir, "laptop", "audit.md", findings=self.findings,
        )
        # Markdown parser produced one story; the bogus F-99 must have
        # been dropped, the real F-49 kept.
        self.assertEqual(len(stories), 1)
        story = stories[0]
        self.assertFalse(story.get("priority_path_error"))
        underlying = story.get("underlying") or []
        indices = sorted(u.get("index") for u in underlying)
        self.assertEqual(indices, [49])
        self.assertEqual(story.get("fixes_count"), 1)

        # And rendering the result: no "(not found)" string anywhere.
        findings_by_fid = {
            "pricing/F-49": {
                "cluster": "pricing",
                "cluster_index": 49,
                "fid": "pricing/F-49",
                "title": "Real finding",
            },
        }
        html = build_priority_tab_html(stories, findings_by_fid=findings_by_fid)
        self.assertNotIn("(not found)", html)


if __name__ == "__main__":
    unittest.main()
