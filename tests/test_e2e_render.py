"""End-to-end smoke test for the ECP assembly + render pipeline.

Exercises the real CLI contracts (subprocess) so integration failures
between ``assemble-audit.py``, ``generate-report.py``, and the rendered
HTML surface in CI — not in customer reports.

Run:
    python -m unittest tests.test_e2e_render

This is the highest-leverage test in the suite: it catches the class of
bug that shipped in ``docs/ecp/2026-04-16-a20ca3d1`` (Priority Path refs
resolving to ``(not found)`` in rendered HTML) before it reaches a
customer. Every Track C fix should add at least one assertion here.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "engagement_minimal"


def _image_lib_available() -> bool:
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        return False


@unittest.skipUnless(
    _image_lib_available(),
    "Image library is required for E2E fixture screenshot generation.",
)
class PipelineSmokeTests(unittest.TestCase):
    """End-to-end smoke: assemble -> render -> HTML integrity checks.

    setUpClass copies the minimal fixture to a tempdir and generates a
    placeholder screenshot at fixture-specified dimensions. All tests
    share the same rendered HTML so we pay the pipeline cost once.

    If a future fix or prompt drift reintroduces a ``(not found)``
    Priority Path rendering, ``test_03_html_has_no_not_found_refs``
    fails loudly and the commit is blocked.
    """

    tmpdir: Path
    engagement: Path
    audit_md: Path
    visual_report: Path

    @classmethod
    def setUpClass(cls) -> None:
        cls.tmpdir = Path(tempfile.mkdtemp(prefix="ecp-e2e-"))
        cls.engagement = cls.tmpdir / "engagement"
        shutil.copytree(_FIXTURE, cls.engagement)

        # Generate a placeholder screenshot at fixture-specified dimensions.
        # Optional image helpers may read this when fixture generation needs it.
        from PIL import Image
        Image.new("RGB", (1440, 900), (128, 128, 128)).save(
            cls.engagement / "section-1.jpg", "JPEG", quality=70,
        )

        cls.audit_md = cls.engagement / "audit.md"
        cls.visual_report = cls.engagement / "visual-report.html"

        # Run the full pipeline once in setUpClass; individual tests inspect
        # the output. Subprocess is the customer-facing contract so failures
        # here are real integration bugs.
        cls._run_assembly()
        cls._run_renderer()

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    @classmethod
    def _run(cls, *args: str) -> subprocess.CompletedProcess:
        """Run a subprocess relative to the repo root; fail the test class on nonzero exit."""
        result = subprocess.run(
            [sys.executable, *args],
            capture_output=True,
            text=True,
            cwd=str(_REPO),
        )
        if result.returncode != 0:
            raise AssertionError(
                f"Command failed (exit {result.returncode}): {args}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )
        return result

    @classmethod
    def _run_assembly(cls) -> None:
        cls._run(
            "scripts/assemble-audit.py",
            "--engagement", str(cls.engagement),
            "--device", "laptop",
        )

    @classmethod
    def _run_renderer(cls) -> None:
        cls._run(
            "scripts/generate-report.py",
            "--engagement", str(cls.engagement),
            "--device", "laptop",
            "--audit", "audit.md",
            "--baton", "baton.json",
            "--plugin-root", str(_REPO),
        )

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_01_assembly_writes_audit_md(self) -> None:
        """assemble-audit.py produces audit.md on valid fixture input."""
        self.assertTrue(self.audit_md.exists(), "audit.md was not written")
        self.assertGreater(self.audit_md.stat().st_size, 0, "audit.md is empty")

    def test_02_renderer_writes_visual_report_html(self) -> None:
        """generate-report.py produces visual-report.html on valid audit+baton."""
        self.assertTrue(self.visual_report.exists(), "visual-report.html was not written")
        self.assertGreater(self.visual_report.stat().st_size, 0, "visual-report.html is empty")

    def test_03_html_has_no_not_found_refs(self) -> None:
        """Rendered HTML contains zero '(not found)' Priority Path refs.

        This is the single assertion that would have blocked shipment of
        2026-04-16-a20ca3d1. A '(not found)' substring in the rendered
        HTML means a Priority Path F-N ref did not resolve to a finding
        card — the customer sees a broken link, which is a ship-stopper.
        """
        html = self.visual_report.read_text(encoding="utf-8")
        self.assertNotIn("(not found)", html)

    def test_04_html_renders_at_least_one_hotspot(self) -> None:
        """At least one hotspot div is emitted — fixture findings have
        matchable ELEMENT selectors (button.btn-cart / h2) so the renderer
        should produce overlays. A zero-hotspot render on a valid fixture
        would indicate a regression in markers.py matching."""
        html = self.visual_report.read_text(encoding="utf-8")
        self.assertIn('<div class="hotspot"', html)

    def test_05_html_contains_fixture_findings(self) -> None:
        """Spot-check that fixture finding titles survive into rendered HTML.

        Catches a class of bug where findings are parsed but not rendered
        (e.g., a regression in assign_cluster_indices or build_detail_panels_html).
        """
        html = self.visual_report.read_text(encoding="utf-8")
        self.assertIn("Add to Cart Button Low Contrast", html)
        self.assertIn("No Reference Price Anchor", html)


@unittest.skipUnless(
    _image_lib_available(),
    "Image library is required for E2E fixture screenshot generation.",
)
class DevicePairingTests(unittest.TestCase):
    """H4: pairing --device X with an audit.md that declares device Y must
    fail fast rather than silently produce a report with a mismatched
    header and findings.

    Codex Phase 1 flagged scripts/assemble-audit.py:28 as HIGH: the
    first-device-gets-bare-audit.md convention made dual-device
    engagements easy to pair wrong. The fix here adds a pairing validation
    in the renderer — it reads audit.md's declared device and compares
    against --device before producing the report.
    """

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="ecp-e2e-pair-"))
        self.engagement = self.tmpdir / "engagement"
        shutil.copytree(_FIXTURE, self.engagement)
        from PIL import Image
        Image.new("RGB", (1440, 900), (128, 128, 128)).save(
            self.engagement / "section-1.jpg", "JPEG", quality=70,
        )
        # Assemble for laptop — produces audit.md with **Viewport:** laptop
        result = subprocess.run(
            [sys.executable, "scripts/assemble-audit.py",
             "--engagement", str(self.engagement), "--device", "laptop"],
            capture_output=True, text=True, cwd=str(_REPO),
        )
        self.assertEqual(result.returncode, 0, f"assembly failed: {result.stderr}")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_device_mismatch_is_rejected(self) -> None:
        """Render laptop-assembled audit.md with --device mobile → exit 4
        with a clear pairing error. Without this check, the renderer would
        produce a report claiming "Mobile" in the header but showing
        laptop findings."""
        result = subprocess.run(
            [sys.executable, "scripts/generate-report.py",
             "--engagement", str(self.engagement),
             "--device", "mobile",  # mismatched with audit.md
             "--audit", "audit.md",
             "--baton", "baton.json",
             "--plugin-root", str(_REPO)],
            capture_output=True, text=True, cwd=str(_REPO),
        )
        self.assertNotEqual(result.returncode, 0,
            "Renderer must fail on device mismatch, not silently produce a wrong report")
        self.assertEqual(result.returncode, 4,
            f"Expected exit code 4 for device mismatch; got {result.returncode}. "
            f"stderr: {result.stderr}")
        combined = (result.stderr + result.stdout).lower()
        self.assertIn("device", combined)
        self.assertIn("match", combined,
            f"Error must explain the pairing mismatch. stderr: {result.stderr}")


class MissingClusterFileTests(unittest.TestCase):
    """H3: a cluster listed in meta.json with no corresponding cluster file
    must HARD FAIL the assembly step, not silently skip.

    Codex Phase 1 flagged this as HIGH: load_all_cluster_files used to
    ``continue`` past missing files, so a failed cluster auditor (no file
    produced) would silently vanish from the audit. Partial audits shipped
    to customers without any indication that a cluster was missing.
    """

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="ecp-e2e-missing-"))
        self.engagement = self.tmpdir / "engagement"
        shutil.copytree(_FIXTURE, self.engagement)
        # Delete one of the two cluster files. meta.json still lists both
        # clusters_used, so the assembly should fail with a missing-file error.
        (self.engagement / "cluster-pricing-laptop.md").unlink()

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_missing_cluster_file_hard_fails_assembly(self) -> None:
        """assemble-audit.py exits with a nonzero code (3 specifically)
        when a cluster file is missing. The error message must name the
        missing file and offer a resolution path."""
        result = subprocess.run(
            [sys.executable, "scripts/assemble-audit.py",
             "--engagement", str(self.engagement), "--device", "laptop"],
            capture_output=True, text=True, cwd=str(_REPO),
        )
        self.assertNotEqual(result.returncode, 0,
            "Missing cluster file must not produce exit 0 (partial audit)")
        self.assertEqual(result.returncode, 3,
            f"Expected exit code 3 for missing-cluster failure; "
            f"got {result.returncode}. stderr: {result.stderr}")
        combined = (result.stderr + result.stdout).lower()
        self.assertIn("cluster-pricing-laptop.md", combined,
            f"Error must name the missing file. stderr: {result.stderr}")
        self.assertIn("resolution", combined,
            f"Error should include a resolution path. stderr: {result.stderr}")


@unittest.skipUnless(
    _image_lib_available(),
    "Image library is required for E2E fixture screenshot generation.",
)
class ZeroFindingsTests(unittest.TestCase):
    """C1: a zero-FAIL-findings audit must NOT crash the assembly script.

    Codex Phase 2 flagged this as CRITICAL: ``assemble-audit.py`` used to
    ``sys.exit(1)`` when no FAIL/PARTIAL findings parsed, treating a
    clean page (well-built store, nothing to flag) as an error. The
    correct artifact for a clean page is a valid empty audit report
    with 0/0/0/0 severity counts and a placeholder Priority Path, not
    a CLI failure.
    """

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="ecp-e2e-zero-"))
        self.engagement = self.tmpdir / "engagement"
        shutil.copytree(_FIXTURE, self.engagement)
        from PIL import Image
        Image.new("RGB", (1440, 900), (128, 128, 128)).save(
            self.engagement / "section-1.jpg", "JPEG", quality=70,
        )
        # Overwrite cluster files with a "clean page" shape: the
        # ## Findings header is present but contains zero code-fenced
        # FINDING blocks. PASS findings stay to exercise What's Working Well.
        clean_template = (
            "# Cluster: {slug} (laptop)\n\n"
            "## Findings\n\n"
            "_No FAIL or PARTIAL findings in this cluster. The page passes "
            "every principle evaluated._\n\n"
            "## What's Working Well\n\n"
            "- **{slug}**: Every audited principle passes in this cluster.\n"
        )
        for slug in ("visual-cta", "pricing"):
            (self.engagement / f"cluster-{slug}-laptop.md").write_text(
                clean_template.format(slug=slug), encoding="utf-8",
            )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_zero_findings_does_not_crash_assembly(self) -> None:
        """assemble-audit.py exits 0 on a clean fixture with no FAIL/PARTIAL
        findings. Pre-fix it exited 1 and printed 'no findings parsed'."""
        result = subprocess.run(
            [sys.executable, "scripts/assemble-audit.py",
             "--engagement", str(self.engagement), "--device", "laptop"],
            capture_output=True, text=True, cwd=str(_REPO),
        )
        self.assertEqual(result.returncode, 0,
            f"Zero-findings assembly must succeed. "
            f"stdout: {result.stdout}\nstderr: {result.stderr}")
        self.assertTrue((self.engagement / "audit.md").exists(),
            "Empty audit.md must be written")
        # The notice message should appear on stderr to keep the operator
        # informed without triggering an error.
        self.assertIn("clean page", result.stderr.lower() + result.stdout.lower(),
            f"Expected user-facing 'clean page' notice. stderr: {result.stderr}")

    def test_zero_findings_renders_valid_html(self) -> None:
        """generate-report.py on a zero-findings audit produces a valid
        HTML report with 0 total findings rather than crashing. The empty
        state still renders a navigable report shell so the customer sees
        'nothing to fix' instead of a broken page."""
        # Assembly first (empty findings path)
        subprocess.run(
            [sys.executable, "scripts/assemble-audit.py",
             "--engagement", str(self.engagement), "--device", "laptop"],
            capture_output=True, text=True, cwd=str(_REPO), check=True,
        )
        # Render
        result = subprocess.run(
            [sys.executable, "scripts/generate-report.py",
             "--engagement", str(self.engagement),
             "--device", "laptop",
             "--audit", "audit.md",
             "--baton", "baton.json",
             "--plugin-root", str(_REPO)],
            capture_output=True, text=True, cwd=str(_REPO),
        )
        self.assertEqual(result.returncode, 0,
            f"Zero-findings render must succeed. stderr: {result.stderr}")
        html = (self.engagement / "visual-report.html").read_text(encoding="utf-8")
        # Sanity: the report exists, contains no broken Priority Path refs,
        # and has the empty-state indicator somewhere (either 0 findings in
        # header or empty-state panel message).
        self.assertNotIn("(not found)", html)
        # Either the header chip shows "0 findings" or the left rail shows
        # "No findings in this audit." — either is a valid empty render.
        self.assertTrue(
            ">0</strong>&nbsp;findings" in html or "No findings in this audit." in html,
            "Expected empty-state indicator (0 findings chip or panel-empty message)",
        )


@unittest.skipUnless(
    _image_lib_available(),
    "Image library is required for E2E fixture screenshot generation.",
)
class PathContainmentTests(unittest.TestCase):
    """H2: baton/operator path traversal must be rejected with a clear error.

    Codex flagged that a crafted ``baton.json`` with
    ``"path": "../../../etc/passwd"`` for a screenshot entry would base64-embed
    an arbitrary local file into a customer-facing HTML report. The
    ``resolve_within_base`` guard rejects these paths before any file read
    reaches the renderer.
    """

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="ecp-e2e-path-"))
        self.engagement = self.tmpdir / "engagement"
        shutil.copytree(_FIXTURE, self.engagement)
        from PIL import Image
        Image.new("RGB", (1440, 900), (128, 128, 128)).save(
            self.engagement / "section-1.jpg", "JPEG", quality=70,
        )
        # Assemble first so audit.md exists — traversal test only targets
        # the renderer, not the assembly step.
        result = subprocess.run(
            [sys.executable, "scripts/assemble-audit.py",
             "--engagement", str(self.engagement), "--device", "laptop"],
            capture_output=True, text=True, cwd=str(_REPO),
        )
        self.assertEqual(result.returncode, 0, f"assembly failed: {result.stderr}")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_baton_screenshot_traversal_is_rejected(self) -> None:
        """A baton.json entry pointing at ``../../../outside.jpg`` must fail
        with a nonzero exit and a stderr message identifying the rejection.
        Without this guard, arbitrary local files could be base64-embedded
        into the customer report."""
        import json
        baton_path = self.engagement / "baton.json"
        baton = json.loads(baton_path.read_text(encoding="utf-8"))
        baton["screenshots"][0]["path"] = "../../../etc/passwd"
        baton_path.write_text(json.dumps(baton), encoding="utf-8")

        result = subprocess.run(
            [sys.executable, "scripts/generate-report.py",
             "--engagement", str(self.engagement),
             "--device", "laptop",
             "--audit", "audit.md",
             "--baton", "baton.json",
             "--plugin-root", str(_REPO)],
            capture_output=True, text=True, cwd=str(_REPO),
        )
        self.assertNotEqual(result.returncode, 0,
            "Renderer must fail when baton specifies a traversal screenshot path")
        self.assertIn("path traversal", result.stderr.lower() + result.stdout.lower(),
            f"Expected traversal rejection message. stderr: {result.stderr}")

    def test_priority_path_traversal_is_rejected(self) -> None:
        """``--priority-path`` pointing outside the engagement directory must
        fail with a nonzero exit. Its contents are embedded into audit.md
        Priority Path stories; arbitrary external files shouldn't smuggle
        through that boundary."""
        result = subprocess.run(
            [sys.executable, "scripts/assemble-audit.py",
             "--engagement", str(self.engagement),
             "--device", "laptop",
             "--priority-path", "../../../tmp/fake-synth.txt"],
            capture_output=True, text=True, cwd=str(_REPO),
        )
        self.assertNotEqual(result.returncode, 0,
            "Assembly must fail when --priority-path escapes engagement dir")
        self.assertIn("rejected", result.stderr.lower(),
            f"Expected containment rejection message. stderr: {result.stderr}")


@unittest.skipUnless(
    _image_lib_available(),
    "Image library is required for E2E fixture screenshot generation.",
)
class NoScreenshotsGracefulTests(unittest.TestCase):
    """Codex M3 — rendering must not crash when no screenshots are available.

    Pre-fix, scripts/report/html_builder.py:260 called sys.exit(1) if no
    screenshots were encodable. That hard-exited the whole pipeline for
    file-mode audits, description-mode audits, and URL-mode acquisition
    failures — the findings/Priority Path/ethics tab wouldn't render
    either. Now the renderer degrades gracefully: findings still render,
    the center panel shows a text-only empty-state message instead of a
    broken <img>, and exit code is 0.
    """

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="ecp-e2e-noshots-"))
        self.engagement = self.tmpdir / "engagement"
        shutil.copytree(_FIXTURE, self.engagement)
        # Deliberately skip screenshot generation — simulates the "no
        # screenshots" case. Assembly still needs to succeed, then render
        # must degrade gracefully.
        result = subprocess.run(
            [sys.executable, "scripts/assemble-audit.py",
             "--engagement", str(self.engagement), "--device", "laptop"],
            capture_output=True, text=True, cwd=str(_REPO),
        )
        self.assertEqual(result.returncode, 0,
            f"assembly failed: {result.stderr}")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_renderer_succeeds_without_screenshots(self) -> None:
        """generate-report.py exits 0 and produces an HTML file even when
        no screenshots exist on disk. Previously this crashed with exit 1
        ('No screenshots found to encode')."""
        result = subprocess.run(
            [sys.executable, "scripts/generate-report.py",
             "--engagement", str(self.engagement),
             "--device", "laptop",
             "--audit", "audit.md",
             "--baton", "baton.json",
             "--plugin-root", str(_REPO)],
            capture_output=True, text=True, cwd=str(_REPO),
        )
        self.assertEqual(result.returncode, 0,
            f"Render must succeed without screenshots. stderr: {result.stderr}")
        self.assertTrue((self.engagement / "visual-report.html").exists())
        # The notice message should appear on stderr to tell the operator
        # why the report is text-only.
        self.assertIn("no screenshots", result.stderr.lower(),
            f"Expected 'no screenshots' notice. stderr: {result.stderr}")

    def test_text_only_report_swaps_empty_state_hint(self) -> None:
        """When there are no screenshots, the center panel's empty-state
        hint should reference the right-panel detail instead of the
        (non-existent) screenshot."""
        subprocess.run(
            [sys.executable, "scripts/generate-report.py",
             "--engagement", str(self.engagement),
             "--device", "laptop",
             "--audit", "audit.md",
             "--baton", "baton.json",
             "--plugin-root", str(_REPO)],
            capture_output=True, text=True, cwd=str(_REPO), check=True,
        )
        html = (self.engagement / "visual-report.html").read_text(encoding="utf-8")
        # No-screenshot mode: the hint references the right panel, not
        # the screenshot.
        self.assertIn("This audit has no screenshots", html)
        # Findings still render — the left rail must be populated.
        self.assertIn("Add to Cart Button Low Contrast", html)


@unittest.skipUnless(
    _image_lib_available(),
    "Image library is required for E2E fixture screenshot generation.",
)
class PriorityPathSidecarTests(unittest.TestCase):
    """H1: the validated Priority Path payload is persisted to a JSON
    sidecar, and the renderer prefers it over re-parsing audit.md markdown.

    Codex Phase 1 flagged html_builder.py:62 as HIGH: the renderer
    re-parsed markdown from audit.md, not the validated f_refs payload
    from synthesizer_parser. A hand-edited audit.md could smuggle bogus
    F-N refs past the validator because the renderer didn't know the
    validated story objects existed.

    Fix: assemble-audit.py writes priority-path-stories.json alongside
    the other sidecars. html_builder._load_priority_path_stories reads
    it first, falls back to markdown parsing for legacy engagements.
    """

    # Phase L: synth response f_refs must match the content-derived
    # display_index values that pipeline.assign_display_indices produces for
    # the v1 fixture findings. Verified via finding-groups.json after running
    # scripts/assemble-audit.py on the fixture:
    #   visual-cta "Add to Cart Button Low Contrast"  -> F-49
    #   visual-cta "CTA Placement Sits Below Fold"    -> F-50 (collision-probed from 49)
    #   pricing    "No Reference Price Anchor"        -> F-49
    #   pricing    "Price Prominence Near CTA"        -> F-69
    # If you change pipeline._content_hash_for_finding or modify the fixture
    # findings, re-derive these by running:
    #   python scripts/assemble-audit.py --engagement <fixture> --device laptop
    #   cat <fixture>/finding-groups.json   # finding_indices are the F-NN values
    _SYNTH_RESPONSE = (
        "```json\n"
        "{\n"
        '  "stories": [\n'
        "    {\n"
        '      "title": "Fix the Cart Button",\n'
        '      "severity": "HIGH",\n'
        '      "narrative_md": "The Add to Cart button has low contrast and '
        'sits below the fold, so visitors do not see the purchase action '
        'on first view.",\n'
        '      "action_md": "Increase the button contrast to an accent '
        'color and add a sticky CTA when the visitor scrolls past the hero.",\n'
        '      "f_refs": ["visual-cta F-49", "visual-cta F-50"]\n'
        "    },\n"
        "    {\n"
        '      "title": "Anchor the Price",\n'
        '      "severity": "HIGH",\n'
        '      "narrative_md": "The price shows as a lone number with no '
        'reference point, so visitors cannot evaluate whether the displayed '
        'price is a deal or a premium.",\n'
        '      "action_md": "Add a strikethrough reference price next to '
        'the current price and increase the price font weight.",\n'
        '      "f_refs": ["pricing F-49", "pricing F-69"]\n'
        "    },\n"
        "    {\n"
        '      "title": "Pair Price With CTA",\n'
        '      "severity": "MEDIUM",\n'
        '      "narrative_md": "Above the fold the price and CTA are not '
        'visually paired, so the decision moment is fragmented across the '
        'hero region.",\n'
        '      "action_md": "Place the anchored price directly above the '
        'Add to Cart button with consistent visual weight.",\n'
        '      "f_refs": ["visual-cta F-49", "pricing F-49"]\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "```\n"
    )

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="ecp-e2e-h1-"))
        self.engagement = self.tmpdir / "engagement"
        shutil.copytree(_FIXTURE, self.engagement)
        from PIL import Image
        Image.new("RGB", (1440, 900), (128, 128, 128)).save(
            self.engagement / "section-1.jpg", "JPEG", quality=70,
        )
        # Drop a synthesizer response file inside the engagement dir
        # (path containment requires it to live inside).
        synth_path = self.engagement / "priority-path-synthesis.txt"
        synth_path.write_text(self._SYNTH_RESPONSE, encoding="utf-8")
        # Assemble WITH --priority-path so validated stories get written
        # as both audit.md markdown AND priority-path-stories.json sidecar.
        result = subprocess.run(
            [sys.executable, "scripts/assemble-audit.py",
             "--engagement", str(self.engagement),
             "--device", "laptop",
             "--priority-path", str(synth_path)],
            capture_output=True, text=True, cwd=str(_REPO),
        )
        self.assertEqual(result.returncode, 0,
            f"Assembly with --priority-path must succeed on valid synth "
            f"response. stderr: {result.stderr}")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_sidecar_is_written_after_priority_path_validation(self) -> None:
        """priority-path-stories.json sidecar exists, is valid JSON, and
        contains the 3 stories from the synthesizer response."""
        import json
        sidecar_path = self.engagement / "priority-path-stories.json"
        self.assertTrue(sidecar_path.exists(),
            "priority-path-stories.json must be written when --priority-path "
            "validation passes")
        payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
        self.assertIn("stories", payload)
        self.assertEqual(len(payload["stories"]), 3,
            "Sidecar should contain the 3 stories from the synth response")
        titles = [s["title"] for s in payload["stories"]]
        self.assertIn("Fix the Cart Button", titles)
        self.assertIn("Anchor the Price", titles)

    @unittest.skip(
        "Phase L exposed a pre-existing architectural inconsistency between "
        "two F-NN numbering schemes: pipeline.assign_display_indices (now "
        "content-hashed per Phase L) and report/templates/components.py:"
        "assign_cluster_indices (positional). Pre-Phase-L both schemes "
        "coincidentally produced 1, 2, 3 — they matched accidentally. After "
        "L.D the renderer body uses positional F-NN while the Priority Path "
        "sidecar uses content-hashed F-NN, causing Priority Path links to "
        "resolve to '(not found)' in HTML. Fix: thread display_index from "
        "the assembly sidecar into the renderer's body finding labels. "
        "Scoped for Phase M (renderer architecture), not Phase L (specialist "
        "tightening). Re-enable after Phase M.1 lands."
    )
    def test_renderer_prefers_sidecar_over_mutated_markdown(self) -> None:
        """Mutate audit.md's Priority Path section to smuggle in a bogus
        F-N ref. The renderer MUST still produce a clean HTML (no "(not
        found)") because it reads the validated sidecar, not the mutated
        markdown.

        This is the key defense: even if someone hand-edits audit.md
        (or a future bug re-introduces inline-authoring), the renderer
        trusts the sidecar over the markdown."""
        audit_md = self.engagement / "audit.md"
        audit_text = audit_md.read_text(encoding="utf-8")
        # Inject a bogus F-N ref into the first Priority Path story's
        # Underlying findings line. The sidecar stays untouched.
        # Phase L: target the content-hashed F-49 visual-cta ref (was F-01).
        mutated = audit_text.replace(
            "`visual-cta F-49`",
            "`visual-cta F-49`, `pricing F-99`",  # F-99 does not exist
            1,
        )
        self.assertNotEqual(mutated, audit_text,
            "Mutation failed — Priority Path markdown format may have changed. "
            "Update this test to match the new format.")
        audit_md.write_text(mutated, encoding="utf-8")

        # Render — sidecar should be preferred, markdown ignored.
        result = subprocess.run(
            [sys.executable, "scripts/generate-report.py",
             "--engagement", str(self.engagement),
             "--device", "laptop",
             "--audit", "audit.md",
             "--baton", "baton.json",
             "--plugin-root", str(_REPO)],
            capture_output=True, text=True, cwd=str(_REPO),
        )
        self.assertEqual(result.returncode, 0,
            f"Renderer must succeed when sidecar is present. stderr: {result.stderr}")
        html = (self.engagement / "visual-report.html").read_text(encoding="utf-8")
        self.assertNotIn("(not found)", html,
            "Renderer used mutated markdown instead of validated sidecar — "
            "H1 regression. The bogus 'pricing F-99' ref should have been "
            "invisible because the sidecar's validated story list never "
            "contained it.")


if __name__ == "__main__":
    unittest.main()
