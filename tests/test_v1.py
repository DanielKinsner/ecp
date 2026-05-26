"""v1.0 regression tests for silent-failure surfaces introduced or modified
by the v1.0 shippability pass.

Run:
    python -m unittest tests.test_v1

No pytest dependency. Only stdlib + the repo's scripts/ package.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.models import Finding, DedupeResult  # noqa: E402
from assembly.pipeline import (  # noqa: E402
    PIPELINE_STAGES,
    FinalizedFindings,
    _assert_stage,
    assign_display_indices,
    build_cluster_finding_map,
)
from assembly.scoring import _finding_ref  # noqa: E402
from assembly.synthesizer_parser import (  # noqa: E402
    parse_response,
    validate_stories,
    MIN_STORIES,
    MAX_STORIES,
    MIN_F_REFS_PER_STORY,
    MAX_F_REFS_PER_STORY,
)
from assembly.writer import _ethics_gate_header, _ethics_gate_summary  # noqa: E402
from report.citations import is_safe_citation_url, resolve_citation_url  # noqa: E402


def _mk(
    cluster: str,
    local_index: int,
    priority: str,
    *,
    section: str = "section",
    element: str = "el",
    ethics_state: str = "",
) -> Finding:
    """Minimal Finding factory for test cases."""
    priority_rank_map = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    return Finding(
        cluster=cluster,
        device="laptop",
        local_index=local_index,
        verdict="FAIL",
        section=section,
        element=element,
        element_normalized=element.lower(),
        source="VISUAL",
        priority=priority,
        priority_rank=priority_rank_map[priority],
        observation="",
        recommendation="",
        reference="",
        ethics_state=ethics_state,
    )


class EthicsGateHeaderSummaryTests(unittest.TestCase):
    """Test #1 — Header and summary cannot disagree on count.

    Before v1.0, _ethics_gate_header took an ethics_status string that was
    computed independently via _detect_ethics_status, which inferred BLOCK
    from prose inside ## Ethics Gate section even when no structured
    ETHICS_STATE: was set. The summary read from result.ethics_findings
    (which could be empty). Result: header said VIOLATIONS FOUND, summary
    said "0 BLOCK findings detected" in the SAME audit.md.

    In v1.0, both derive from the same ethics_findings list. They cannot
    disagree.
    """

    def test_zero_block_findings_shows_clear(self):
        header = _ethics_gate_header([])
        summary = _ethics_gate_summary([])
        self.assertEqual(header, "CLEAR")
        self.assertIn("No BLOCK or ADJACENT", summary)

    def test_one_block_finding(self):
        ethics = [_mk("trust-credibility", 1, "CRITICAL", ethics_state="BLOCK")]
        header = _ethics_gate_header(ethics)
        summary = _ethics_gate_summary(ethics)
        self.assertEqual(header, "VIOLATIONS FOUND")
        self.assertIn("1 BLOCK", summary)
        self.assertIn("finding detected", summary)  # singular

    def test_three_block_findings_plural_word(self):
        ethics = [
            _mk("trust-credibility", i, "CRITICAL", ethics_state="BLOCK")
            for i in range(1, 4)
        ]
        header = _ethics_gate_header(ethics)
        summary = _ethics_gate_summary(ethics)
        self.assertEqual(header, "VIOLATIONS FOUND")
        self.assertIn("3 BLOCK", summary)
        self.assertIn("findings detected", summary)  # plural

    def test_adjacent_only_shows_advisory(self):
        ethics = [_mk("pricing", 1, "HIGH", ethics_state="ADJACENT")]
        header = _ethics_gate_header(ethics)
        summary = _ethics_gate_summary(ethics)
        self.assertEqual(header, "ADVISORY")
        self.assertIn("1 ADJACENT", summary)

    def test_block_and_adjacent_mix_shows_violations_found(self):
        ethics = [
            _mk("trust-credibility", 1, "CRITICAL", ethics_state="BLOCK"),
            _mk("pricing", 1, "HIGH", ethics_state="ADJACENT"),
        ]
        header = _ethics_gate_header(ethics)
        summary = _ethics_gate_summary(ethics)
        self.assertEqual(header, "VIOLATIONS FOUND")
        # Summary reports only the BLOCK count because BLOCK dominates
        self.assertIn("1 BLOCK", summary)


class FNPostDedupConsistencyTests(unittest.TestCase):
    """Test #2 — After assign_display_indices, _finding_ref emits refs
    keyed to the displayed position within the cluster. Before v1.0,
    scoring._finding_ref used local_index; the writer re-sorted by
    priority_rank; Priority Path links went to the wrong cards (C2).
    """

    def test_critical_finding_renders_first_in_priority_order(self):
        # Phase L: display_index is now content-derived (not 1, 2, 3...) but
        # render order is still priority-based. Two pricing findings: MEDIUM
        # (local_index=1) and CRITICAL (local_index=2). Writer should still
        # render CRITICAL first regardless of how display_index is computed.
        findings = [
            _mk("pricing", 1, "MEDIUM"),
            _mk("pricing", 2, "CRITICAL"),
            _mk("trust-credibility", 1, "HIGH"),
        ]
        ordered = assign_display_indices(findings, ["pricing", "trust-credibility"])

        pricing_sorted = [f for f in ordered if f.cluster == "pricing"]

        # Render order: CRITICAL (local_index=2) before MEDIUM (local_index=1)
        self.assertEqual(pricing_sorted[0].local_index, 2)
        self.assertEqual(pricing_sorted[1].local_index, 1)

        # display_index is content-derived integer in [1, 99]; both pricing
        # findings get unique values within the cluster
        self.assertGreaterEqual(pricing_sorted[0].display_index, 1)
        self.assertLessEqual(pricing_sorted[0].display_index, 99)
        self.assertGreaterEqual(pricing_sorted[1].display_index, 1)
        self.assertLessEqual(pricing_sorted[1].display_index, 99)
        self.assertNotEqual(
            pricing_sorted[0].display_index, pricing_sorted[1].display_index
        )

        # _finding_ref emits "pricing F-{NN}" with the content-derived NN
        ref0 = _finding_ref(pricing_sorted[0])
        ref1 = _finding_ref(pricing_sorted[1])
        self.assertTrue(ref0.startswith("pricing F-"))
        self.assertTrue(ref1.startswith("pricing F-"))
        self.assertNotEqual(ref0, ref1)

    def test_finalized_findings_valid_refs_matches_rendering_order(self):
        # Phase L: valid_refs contains content-derived F-NN values. Test that
        # we have the right NUMBER of refs across the right clusters, not
        # specific F-NN values (which depend on content hashes).
        findings = [
            _mk("pricing", 1, "MEDIUM"),
            _mk("pricing", 2, "CRITICAL"),
            _mk("trust-credibility", 1, "HIGH"),
        ]
        ff = FinalizedFindings.build(findings, ["pricing", "trust-credibility"])
        refs = ff.valid_refs()

        pricing_refs = [r for r in refs if r.startswith("pricing F-")]
        trust_refs = [r for r in refs if r.startswith("trust-credibility F-")]
        self.assertEqual(len(pricing_refs), 2)
        self.assertEqual(len(trust_refs), 1)
        # All refs are well-formed
        for r in refs:
            self.assertRegex(r, r"^[a-z-]+ F-\d{1,2}$")
        # Frozen — mutation raises
        with self.assertRaises(Exception):
            ff.findings = ()  # type: ignore[misc]

    def test_build_cluster_finding_map_requires_display_index(self):
        # An untagged finding should be rejected; this is the invariant
        # that write_audit_md and synthesizer_parser rely on.
        f = _mk("pricing", 1, "HIGH")
        self.assertEqual(f.display_index, 0)  # default
        with self.assertRaises(AssertionError):
            build_cluster_finding_map([f])


class CitationURLResolutionTests(unittest.TestCase):
    """Test #3 — resolve_citation_url returns the expected URL from a
    bare-URL sources_lookup. Regression guard if anyone later reformats
    sources.md; as written sources.md uses bare URLs and the parser in
    report/parser.parse_sources expects that format.
    """

    def test_bare_url_lookup_finding_number(self):
        lookup = {"checkout-optimization.md:3": "https://baymard.com/blog/cart-abandonment"}
        self.assertEqual(
            resolve_citation_url("checkout-optimization.md Finding 3", lookup),
            "https://baymard.com/blog/cart-abandonment",
        )

    def test_file_level_fallback_when_no_finding_number(self):
        lookup = {"checkout-optimization.md:3": "https://baymard.com/blog/cart-abandonment"}
        # Reference cites the file with no number — still returns SOMETHING
        self.assertEqual(
            resolve_citation_url("checkout-optimization.md § Section 1", lookup),
            "https://baymard.com/blog/cart-abandonment",
        )

    def test_empty_lookup_returns_none(self):
        self.assertIsNone(resolve_citation_url("any.md Finding 1", {}))
        self.assertIsNone(resolve_citation_url("", {"x.md:1": "https://x"}))


class SynthesizerValidatorTests(unittest.TestCase):
    """Test #4 — The synthesizer_parser enforces F-N allowlist,
    story count, and f_refs count bounds. This is the only gate
    protecting the headline feature (Priority Path) from hallucinated
    references that would render as broken anchors in the report.
    """

    valid_refs = {
        "pricing F-01",
        "pricing F-02",
        "pricing F-03",
        "visual-cta F-01",
        "visual-cta F-02",
        "trust-credibility F-01",
    }

    def _mk_story(self, f_refs):
        return {
            "title": "t",
            "severity": "HIGH",
            "narrative_md": "n",
            "action_md": "a",
            "f_refs": list(f_refs),
        }

    def test_three_valid_stories_pass(self):
        stories = [
            self._mk_story(["pricing F-03", "trust-credibility F-01"]),
            self._mk_story(["pricing F-01", "pricing F-02"]),
            self._mk_story(["visual-cta F-01", "visual-cta F-02"]),
        ]
        ok, reason = validate_stories(stories, self.valid_refs)
        self.assertTrue(ok, f"expected valid, got: {reason}")

    def test_hallucinated_f_ref_rejected(self):
        stories = [
            self._mk_story(["pricing F-99", "trust-credibility F-01"]),
            self._mk_story(["pricing F-01", "pricing F-02"]),
            self._mk_story(["visual-cta F-01", "visual-cta F-02"]),
        ]
        ok, reason = validate_stories(stories, self.valid_refs)
        self.assertFalse(ok)
        self.assertIn("F-99", reason)

    def test_wrong_cluster_f_ref_rejected(self):
        # pricing F-03 is valid; visual-cta F-03 is NOT (no such F-03 in visual-cta)
        stories = [
            self._mk_story(["visual-cta F-03", "trust-credibility F-01"]),
            self._mk_story(["pricing F-01", "pricing F-02"]),
            self._mk_story(["visual-cta F-01", "visual-cta F-02"]),
        ]
        ok, reason = validate_stories(stories, self.valid_refs)
        self.assertFalse(ok)
        self.assertIn("visual-cta F-03", reason)

    def test_too_few_stories_rejected(self):
        stories = [
            self._mk_story(["pricing F-01", "pricing F-02"]),
            self._mk_story(["visual-cta F-01", "visual-cta F-02"]),
        ]
        ok, reason = validate_stories(stories, self.valid_refs)
        self.assertFalse(ok)
        self.assertIn("out of range", reason)
        self.assertIn(f"[{MIN_STORIES}, {MAX_STORIES}]", reason)

    def test_too_many_f_refs_per_story_rejected(self):
        stories = [
            self._mk_story(["pricing F-01", "pricing F-02", "pricing F-03",
                            "visual-cta F-01", "visual-cta F-02"]),
            self._mk_story(["pricing F-01", "pricing F-02"]),
            self._mk_story(["visual-cta F-01", "visual-cta F-02"]),
        ]
        ok, reason = validate_stories(stories, self.valid_refs)
        self.assertFalse(ok)
        self.assertIn(f"[{MIN_F_REFS_PER_STORY}, {MAX_F_REFS_PER_STORY}]", reason)

    def test_parse_response_missing_fence_returns_none(self):
        self.assertIsNone(parse_response("no code fence anywhere"))
        self.assertIsNone(parse_response(""))
        self.assertIsNone(parse_response(None))  # type: ignore[arg-type]

    def test_parse_response_malformed_json_returns_none(self):
        bad = "Here is my output:\n\n```json\n{\"stories\": [ truncated\n```\n"
        self.assertIsNone(parse_response(bad))

    def test_parse_response_good_extracts_stories(self):
        good = (
            "Here you go:\n\n"
            "```json\n"
            "{\n"
            '  "stories": [\n'
            "    {\n"
            '      "title": "Fix CTA contrast",\n'
            '      "severity": "HIGH",\n'
            '      "narrative_md": "The button is hard to see.",\n'
            '      "action_md": "Darken the background.",\n'
            '      "f_refs": ["pricing F-03", "visual-cta F-01"]\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "```\n"
        )
        parsed = parse_response(good)
        self.assertIsNotNone(parsed)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["title"], "Fix CTA contrast")


class URLAllowlistTests(unittest.TestCase):
    """Test #5 — is_safe_citation_url fuzz list. This is the single gate
    protecting the rendered HTML report from javascript:/data:/private-IP
    XSS and SSRF vectors.
    """

    REJECT = [
        "javascript:alert(1)",
        "JAVASCRIPT:alert(1)",
        "Javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "file:///etc/passwd",
        "file://localhost/etc/passwd",
        "ftp://example.com/",
        "mailto:x@y.com",
        # Private / loopback / link-local / IMDS
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.1/",
        "http://10.255.255.255/",
        "http://172.16.0.1/",
        "http://172.31.255.255/",
        "http://192.168.1.1/",
        "http://127.0.0.1/",
        "http://[::1]/",
        "http://[fc00::1]/",  # ULA
        "http://[fe80::1]/",  # link-local v6
        "http://localhost/",
        "http://localhost:8080/",
        # Formatting / size
        "",
        " ",
        None,
        "http://example.com/" + "a" * 3000,  # over 2048
        "http://example.com/path\nwith-newline",
        "http://example.com/path\twith-tab",
    ]

    ACCEPT = [
        "http://example.com/",
        "https://example.com/path",
        "https://ftc.gov/legal-library/browse/rules/fake-reviews-rule",
        "HTTPS://WWW.LAW.CORNELL.EDU/uscode/text/15/45",
        "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
    ]

    def test_reject_unsafe(self):
        for url in self.REJECT:
            with self.subTest(url=url):
                self.assertFalse(
                    is_safe_citation_url(url),
                    f"expected REJECT: {url!r}",
                )

    def test_accept_safe(self):
        for url in self.ACCEPT:
            with self.subTest(url=url):
                self.assertTrue(
                    is_safe_citation_url(url),
                    f"expected ACCEPT: {url!r}",
                )


class PipelineStageAssertions(unittest.TestCase):
    """Bonus — the ordering-enforcement mechanism. If a future change
    rearranges PIPELINE_STAGES, every _assert_stage call across the
    codebase has to be re-numbered. This test pins the count and the
    stage names so a reviewer sees the diff immediately.
    """

    def test_pipeline_stages_shape(self):
        # If this changes, every _assert_stage(name, index) call site
        # must be reviewed.
        self.assertEqual(
            tuple(name for name, _ in PIPELINE_STAGES),
            (
                "parse",
                "dedup",
                "assign_display_indices",
                "score",
                "write_audit",
                "write_sidecars",
            ),
        )

    def test_assert_stage_catches_mismatch(self):
        _assert_stage("parse", 0)  # correct
        with self.assertRaises(AssertionError):
            _assert_stage("score", 0)  # wrong index for 'score'




# ============================================================================
# v1.0.1 regression tests — four postmortem fixes shipped after the v1.0.0 tag
# ============================================================================


class ReportRuntimeJsonInHtmlEscape(unittest.TestCase):
    r"""The </script>-in-JSON bug that silently truncated the desktop JS
    runtime. Any JSON payload embedded in <script>...</script> must have
    </ escaped as <\/ so the HTML parser can't close the tag early."""

    def test_script_close_in_finding_is_escaped(self):
        from scripts.report.html_builder import _build_html_fragments
        f = {
            "index": 1,
            "verdict": "FAIL",
            "cluster": "performance-ux",
            "priority": "HIGH",
            "section": "speculation-rules",
            "element": "head script",
            "observation": "No Speculation Rules present.",
            "recommendation": (
                'Add <script type="speculationrules">{"prerender":[{"where":'
                '{"href_matches":"/collections/*"}}]}</script> to the head.'
            ),
        }
        fragments = _build_html_fragments(
            findings=[f],
            priority_path_stories=[],
            slide_markers={},
            metrics={"severity_counts": {"critical": 0, "high": 1, "medium": 0, "low": 0}, "total_findings": 1, "evidence_confidence_label": "HIGH", "evidence_confidence_class": "", "projected_lift": 0},
            has_ethics_violations=False,
            screenshots={"slide_base64": [], "slide_aspect_ratios": [], "default_slide_aspect_ratio": "16 / 9"},
            audit_md_text="",
        )
        for key in ("findings_json", "export_markdown_json"):
            payload = fragments.get(key, "")
            self.assertNotIn(
                "</script",
                payload,
                f"{key} has an unescaped </script> that would truncate runtime",
            )


class ReportMetadataSchemaFallback(unittest.TestCase):
    """meta.json schema drift: writers emit engagement_id + top-level url
    while the reader used to require id + page.url. Header rendered
    Unknown URL on every recent engagement. Fixed in v1.0.1."""

    def test_loads_url_from_top_level(self):
        from scripts.report.html_builder import _load_metadata
        from pathlib import Path
        meta = {"engagement_id": "2026-04-14-abc", "url": "https://example.com/"}
        baton = {"viewport": {"width": 1920, "height": 1080}}
        r = _load_metadata(Path("/tmp"), baton, meta, "desktop", Path("/tmp"))
        self.assertEqual(r["page_url"], "https://example.com/")
        self.assertEqual(r["engagement_id"], "2026-04-14-abc")

    def test_loads_url_from_nested_page(self):
        from scripts.report.html_builder import _load_metadata
        from pathlib import Path
        meta = {"id": "old", "page": {"url": "https://nested.example/", "type": "product"}}
        baton = {"viewport": {"width": 1920, "height": 1080}}
        r = _load_metadata(Path("/tmp"), baton, meta, "desktop", Path("/tmp"))
        self.assertEqual(r["page_url"], "https://nested.example/")
        self.assertEqual(r["engagement_id"], "old")
        self.assertEqual(r["page_type"], "Product")

    def test_url_normalized_fallback(self):
        from scripts.report.html_builder import _load_metadata
        from pathlib import Path
        meta = {"engagement_id": "x", "url_normalized": "example.com/"}
        baton = {"viewport": {"width": 1920, "height": 1080}}
        r = _load_metadata(Path("/tmp"), baton, meta, "desktop", Path("/tmp"))
        self.assertEqual(r["page_url"], "example.com/")

    def test_truly_missing_url_is_honest(self):
        from scripts.report.html_builder import _load_metadata
        from pathlib import Path
        meta = {"engagement_id": "x"}
        baton = {"viewport": {"width": 1920, "height": 1080}}
        r = _load_metadata(Path("/tmp"), baton, meta, "desktop", Path("/tmp"))
        self.assertEqual(r["page_url"], "Unknown URL")


class ClusterSeverityChipWorstWins(unittest.TestCase):
    """Cluster chip = WORST severity present. 3 HIGH + 4 MEDIUM used to
    render 4 MEDIUM (plurality dominated). Fixed in v1.0.1."""

    def test_worst_severity_wins_over_plurality(self):
        from scripts.report.templates.components import build_clusters_tab_html
        findings_by_cluster = {"visual-cta": [
            {"fid": f"visual-cta/F-{i:02d}", "cluster": "visual-cta", "cluster_index": i, "priority": "HIGH",   "title": str(i)} for i in range(1, 4)
        ] + [
            {"fid": f"visual-cta/F-{i:02d}", "cluster": "visual-cta", "cluster_index": i, "priority": "MEDIUM", "title": str(i)} for i in range(4, 8)
        ]}
        html = build_clusters_tab_html(findings_by_cluster)
        self.assertIn('cluster-sev-tag high">3 HIGH<', html)
        self.assertNotIn('cluster-sev-tag medium">4 MEDIUM<', html)

    def test_critical_beats_high(self):
        from scripts.report.templates.components import build_clusters_tab_html
        findings_by_cluster = {"pricing": [
            {"fid": "pricing/F-01", "cluster": "pricing", "cluster_index": 1, "priority": "CRITICAL", "title": "x"},
            {"fid": "pricing/F-02", "cluster": "pricing", "cluster_index": 2, "priority": "HIGH",     "title": "y"},
            {"fid": "pricing/F-03", "cluster": "pricing", "cluster_index": 3, "priority": "HIGH",     "title": "z"},
        ]}
        html = build_clusters_tab_html(findings_by_cluster)
        self.assertIn('cluster-sev-tag critical">1 CRITICAL<', html)


from report.markers import (  # noqa: E402
    auto_map_markers,
    match_element_to_baton,
    fuzzy_match_element,
    _match_element_id,
    _match_exact_selector,
    _is_bare_id_selector,
)
from assembly.meta_validator import (  # noqa: E402
    validate_meta_json,
    _parse_with_duplicate_detection,
)


class MetaJsonValidatorTests(unittest.TestCase):
    """Codex M2 — meta.json duplicate-key + invariant validation.

    The duplicate-key bug in docs/ecp/2026-04-15-36bf19a6/meta.json
    (devices_scanned written twice, second write empty) was invisible
    under json.load default behavior. These tests lock in the
    validator's ability to detect both the duplicate key itself and
    the signature invariant violations (active phase with empty
    devices_scanned) that the bug produces downstream.
    """

    def _write_meta(self, text: str) -> Path:
        import tempfile
        f = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8",
        )
        f.write(text)
        f.close()
        return Path(f.name)

    def test_clean_meta_produces_no_warnings(self):
        path = self._write_meta(
            '{"phase": "audit", "devices_requested": ["laptop"], '
            '"devices_scanned": ["laptop"]}'
        )
        self.assertEqual(validate_meta_json(path), [])
        path.unlink()

    def test_duplicate_key_is_detected(self):
        # JSON technically allows duplicate keys; json.load silently
        # drops all but the last. This is the M2 bug signature.
        path = self._write_meta(
            '{"phase": "audit", "devices_scanned": ["laptop"], '
            '"devices_scanned": []}'
        )
        warnings = validate_meta_json(path)
        self.assertTrue(any("duplicate key" in w for w in warnings),
            f"Expected duplicate-key warning, got: {warnings}")
        path.unlink()

    def test_empty_devices_scanned_with_active_phase_warns(self):
        """The downstream signature of the M2 bug: phase says audit ran
        but devices_scanned is []. Caught as an invariant violation even
        if the duplicate key is no longer textually visible (e.g., after
        a manual cleanup that kept the wrong value)."""
        path = self._write_meta(
            '{"phase": "complete", "devices_requested": ["mobile"], '
            '"devices_scanned": []}'
        )
        warnings = validate_meta_json(path)
        self.assertTrue(
            any("devices_scanned is empty" in w for w in warnings),
            f"Expected empty-devices warning, got: {warnings}",
        )
        path.unlink()

    def test_scanned_not_subset_of_requested_warns(self):
        path = self._write_meta(
            '{"phase": "audit", "devices_requested": ["laptop"], '
            '"devices_scanned": ["desktop"]}'
        )
        warnings = validate_meta_json(path)
        self.assertTrue(
            any("not in devices_requested" in w for w in warnings),
            f"Expected subset warning, got: {warnings}",
        )
        path.unlink()

    def test_missing_file_warns(self):
        warnings = validate_meta_json(Path("/nonexistent/meta.json"))
        self.assertTrue(any("not found" in w for w in warnings))

    def test_invalid_json_warns(self):
        path = self._write_meta("{not valid json")
        warnings = validate_meta_json(path)
        self.assertTrue(any("not valid JSON" in w for w in warnings))
        path.unlink()

    def test_parse_hook_returns_last_value_on_duplicates(self):
        """Sanity check: the duplicate-detection hook still keeps the
        last value (matching json.load default) so callers that use
        the returned dict don't get surprised by a different shape."""
        data, dupes = _parse_with_duplicate_detection(
            '{"x": 1, "x": 2}'
        )
        self.assertEqual(data, {"x": 2})
        self.assertEqual(dupes, ["x"])


class TieredResolverTier1Tests(unittest.TestCase):
    """Track B Design 3 — Tier 1 (element_id) tests.

    Tier 1 fires for bare-ID selectors only, and only when baton elements
    carry ``id`` or ``element_id`` fields. It's a forward-compat hook
    for the Design 1 element_id registry — today baton rarely populates
    these fields, so most tests here assert Tier 1 returns None and
    delegation to Tier 2 proceeds correctly.
    """

    def test_tier1_exact_id_match(self):
        """Baton element with id matching bare-ID selector returns that index."""
        els = [
            {"selector": "button", "tag": "button", "class": "misc"},
            {"selector": "button", "tag": "button", "id": "button-cart",
             "class": "btn-primary"},
        ]
        self.assertEqual(_match_element_id("#button-cart", els), 1)

    def test_tier1_element_ref_field_match(self):
        """element_id field (forward-compat with Design 1) also satisfies Tier 1."""
        els = [
            {"selector": "div", "tag": "div"},
            {"selector": "button", "tag": "button", "element_id": "button-cart"},
        ]
        self.assertEqual(_match_element_id("#button-cart", els), 1)

    def test_tier1_no_id_in_baton_returns_none(self):
        """When no baton element carries id/element_id, Tier 1 returns None
        and the orchestrator falls through to Tier 2."""
        els = [
            {"selector": "button", "tag": "button", "class": "btn-cart"},
        ]
        self.assertIsNone(_match_element_id("#button-cart", els))


class TieredResolverTier2Tests(unittest.TestCase):
    """Track B Design 3 — Tier 2 (exact CSS selector) tests.

    Tier 2 wraps the pre-Design-3 Strategy 1 (direct + tag.class), 1b
    (bare-ID class-token), and 2 (attribute selector). Strict — returns
    None on miss, does NOT fuzzy-fall-through.
    """

    def test_tier2_tag_class_match(self):
        """'button.btn-cart' matches element with tag=button, class contains btn-cart."""
        els = [
            {"selector": "div", "tag": "div", "class": "wrapper"},
            {"selector": "button", "tag": "button", "class": "btn-cart btn-primary"},
        ]
        self.assertEqual(_match_exact_selector("button.btn-cart", els), 1)

    def test_tier2_bare_id_no_match_returns_none(self):
        """Bare ID with no matching element returns None (Fix 2 behavior).
        MUST NOT fuzzy-fall-through."""
        els = [
            # Intentionally shares the substring 'cart' but is NOT the button-cart element
            {"selector": "button", "tag": "button", "class": "header-cart-toggle"},
        ]
        self.assertIsNone(_match_exact_selector("#button-cart", els))

    def test_tier2_attribute_selector(self):
        """'[class*="newsletter"]' matches element whose class contains newsletter."""
        els = [
            {"selector": "div", "tag": "div", "class": "newsletter-popup"},
        ]
        self.assertEqual(_match_exact_selector('[class*="newsletter"]', els), 0)


class TieredResolverTier4Tests(unittest.TestCase):
    """Track B Design 3 — Tier 4 (fuzzy keyword) tests.

    Tier 4 is the last-resort element guess. Threshold tightened from
    the pre-Design-3 50% to 2+ matches on multi-keyword selectors.
    Text field deliberately excluded to reduce false positives.
    """

    def test_tier4_tightened_threshold_rejects_single_match(self):
        """3-keyword selector with only 1 keyword matching returns None.

        Pre-Design-3 this was 1-of-3 (33%, above the max(1, 3//2)=1
        threshold) → matched. Design 3 requires 2+ matches for
        multi-keyword selectors to reduce false positives on descriptive
        selectors the auditor writes."""
        els = [
            # Only 'payment' matches from ['footer', 'payment', 'icons']
            {"tag": "section", "class": "payment-section"},
        ]
        self.assertIsNone(fuzzy_match_element("footer .payment-icons", els))

    def test_tier4_accepts_strong_match(self):
        """3-keyword selector with 3 matches returns the best element."""
        els = [
            {"tag": "footer", "class": "payment-icons"},
        ]
        self.assertEqual(fuzzy_match_element("footer .payment-icons", els), 0)

    def test_tier4_text_field_is_not_searched(self):
        """Matches against tag + class only. Text field was a false-positive
        source (a button finding matching an h1 whose text mentions 'button')."""
        els = [
            # 'button' only appears in text, not tag/class
            {"tag": "h1", "class": "hero-title", "text": "The button is below"},
        ]
        # 2-keyword selector needs 2 matches; text excluded → 0 matches.
        self.assertIsNone(fuzzy_match_element("button cart", els))

    def test_tier4_single_keyword_selector_still_matches(self):
        """1-keyword selectors still match on 1 hit (threshold = 1 for len==1)."""
        els = [
            {"tag": "nav", "class": "main-nav"},
        ]
        self.assertEqual(fuzzy_match_element("nav", els), 0)


class TieredResolverOrchestrationTests(unittest.TestCase):
    """Track B Design 3 — integration tests for match_element_to_baton
    (Tier 1 + Tier 2, no fuzzy) and the _is_bare_id_selector helper.

    Section-slug routing (Tier 3) is orchestrated inside
    ``auto_map_markers`` and tested via the E2E suite in
    tests/test_e2e_render.py — unit-testing it here would require a
    full baton fixture that belongs at the integration boundary.
    """

    def test_match_element_to_baton_no_fuzzy_fallback(self):
        """match_element_to_baton is strict-only now. A selector whose keywords
        would have fuzzy-matched under Strategy 3 gets None here — fuzzy
        has moved into fuzzy_match_element and is called separately by
        auto_map_markers."""
        els = [
            # Shares keywords with the selector but no exact match.
            {"tag": "div", "class": "cart-widget"},
        ]
        # Pre-Design-3: Strategy 3 fuzzy would match on "cart" keyword.
        # Post-Design-3: strict matcher returns None; fuzzy happens only
        # via fuzzy_match_element (called from auto_map_markers after
        # section routing).
        self.assertIsNone(match_element_to_baton(".cart-widget", [{"tag": "div", "class": "other"}]))

    def test_is_bare_id_selector_recognizes_plain_ids(self):
        self.assertTrue(_is_bare_id_selector("#foo"))
        self.assertTrue(_is_bare_id_selector("#foo-bar"))
        self.assertTrue(_is_bare_id_selector("#button-cart"))

    def test_is_bare_id_selector_rejects_compound_selectors(self):
        """Compound selectors like '#foo span.bar' are NOT bare IDs.
        They should fall through to Tier 2/4 normally rather than
        being treated as strict-no-fuzzy."""
        self.assertFalse(_is_bare_id_selector("#foo span.bar"))
        self.assertFalse(_is_bare_id_selector("button#foo"))
        self.assertFalse(_is_bare_id_selector(".foo"))
        self.assertFalse(_is_bare_id_selector("button"))


class MarkerMappingRegressionTests(unittest.TestCase):
    """Regression coverage for real-world hotspot placement failures."""

    def test_css_coords_with_mobile_dpr_do_not_collapse_to_slide_zero(self):
        """Elements captured in CSS px should still map to the correct slide
        even when viewport.dpr > 1 in baton metadata."""
        baton = {
            "viewport": {"width": 390, "height": 664, "dpr": 3},
            "screenshots": [
                {"index": 1, "scrollY": 0},
                {"index": 2, "scrollY": 700},
                {"index": 3, "scrollY": 1300},
            ],
            "sections": [],
            "elements": [
                {
                    "selector": "span.price-item.price-item--regular",
                    "tag": "span",
                    "class": "price-item price-item--regular",
                    "x": 40,
                    "y": 1373,  # CSS px -> should be slide index 2 (3rd screenshot)
                    "width": 100,
                    "height": 24,
                }
            ],
        }
        findings = [{
            "index": 1,
            "cluster_index": 1,
            "priority": "MEDIUM",
            "element": "span.price-item.price-item--regular",
            "section": "price-transparency",
            "cluster": "pricing",
        }]
        mappings = auto_map_markers(findings, baton)
        self.assertEqual(mappings[0]["slide"], 2)

    def test_repeated_selector_prefers_cluster_scoped_slide(self):
        """When multiple elements share a selector, prefer the one on the
        slide family implied by the finding's cluster metadata."""
        baton = {
            "viewport": {"width": 390, "height": 664, "dpr": 1},
            "screenshots": [
                {"index": 1, "scrollY": 0},
                {"index": 2, "scrollY": 700},
                {"index": 3, "scrollY": 1300},
            ],
            "sections": [
                {"label": "Header", "screenshot_index": 1, "clusters": ["visual-cta"]},
                {"label": "Cards", "screenshot_index": 3, "clusters": ["pricing"]},
            ],
            "elements": [
                {
                    "selector": "span.price-item.price-item--regular",
                    "tag": "span",
                    "class": "price-item price-item--regular",
                    "x": 12,
                    "y": 90,    # top/header instance
                    "width": 90,
                    "height": 20,
                },
                {
                    "selector": "span.price-item.price-item--regular",
                    "tag": "span",
                    "class": "price-item price-item--regular",
                    "x": 40,
                    "y": 1373,  # product-card instance
                    "width": 100,
                    "height": 24,
                },
            ],
        }
        findings = [{
            "index": 1,
            "cluster_index": 1,
            "priority": "MEDIUM",
            "element": "span.price-item.price-item--regular",
            "section": "price-transparency",
            "cluster": "pricing",
        }]
        mappings = auto_map_markers(findings, baton)
        self.assertEqual(mappings[0]["slide"], 2)
        self.assertEqual(mappings[0]["baton_element_index"], 1)


class DeadCliSurfaceRemoved(unittest.TestCase):
    """--apply-dedup was advertised in --help but always exited "Not yet
    implemented". Removed in v1.0.1."""

    def test_apply_dedup_not_in_help(self):
        import subprocess, sys as _sys
        from pathlib import Path
        result = subprocess.run(
            [_sys.executable, "scripts/assemble-audit.py", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parent.parent,
        )
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("--apply-dedup", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
