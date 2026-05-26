"""Phase 6 — cross-device Priority Path coverage (2026-05-18).

Closes Codex Q2/Q3/Q4 from the 2026-05-18 awdmods review. Pre-Phase-6,
``scripts/report/v2_loader.load_v2_priority_path`` silently dropped
stories whose underlying refs all resolved on the OTHER device, and
silently dropped individual cross-device refs from a story's
underlying[]. Result: desktop HTML showed 4 priority cards while desktop
markdown showed 5, and per-card ref lists were quietly trimmed without
any signal to the customer.

Phase 6 contract:
- Stories with 0 actionable refs on the current device but ≥1 actionable
  ref on the other device are KEPT and marked
  ``applies_on_other_device: True`` — the renderer styles them as faded
  "applies elsewhere" cards.
- Refs within a story that don't resolve to current-device actionable
  refs are surfaced as muted ``underlying[].applies_on_other_device: True``
  entries — the renderer renders them struck-through.
- A new soft canary (``priority_path_count_parity``) asserts that the
  renderer's per-device story count equals the synth's
  ``priority_path[]`` count.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from report.v2_loader import load_v2_priority_path


def _synth_with_stories(tmp: Path, stories: list[dict]) -> None:
    (tmp / "synthesizer-emission-v1.json").write_text(
        json.dumps({"priority_path": stories}), encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Story-level: keep, mark applies_on_other_device, don't drop
# ---------------------------------------------------------------------------


class TestStoryAppliesOnOtherDevice:
    def test_story_with_all_refs_on_other_device_is_kept_as_faded(self, tmp_path: Path):
        """Codex Q3 repro: a mobile-only story (all refs are mobile-specific)
        should appear on desktop HTML as a faded card, not silently dropped."""
        _synth_with_stories(tmp_path, [
            {
                "title": "Mobile-only sticky CTA",
                "severity": "HIGH",
                "f_refs": ["visual-cta F-67", "performance-ux F-18"],
            }
        ])
        # Desktop's actionable refs include neither mobile-only ref
        stories = load_v2_priority_path(
            tmp_path,
            actionable_refs={"pricing F-10"},  # unrelated desktop ref
            device="desktop",
        )
        assert len(stories) == 1, (
            "Pre-Phase-6 this returned 0. Codex Q3: customer must see "
            "the same Priority Path count across markdown and HTML."
        )
        story = stories[0]
        assert story["applies_on_other_device"] is True
        assert story["fixes_count"] == 0  # no actionable refs on desktop
        # Every underlying entry is flagged applies_on_other_device
        assert all(
            u.get("applies_on_other_device") is True for u in story["underlying"]
        )

    def test_story_with_mixed_refs_is_not_faded(self, tmp_path: Path):
        """A story with at least one current-device actionable ref is a
        normal card; only its non-actionable refs are muted."""
        _synth_with_stories(tmp_path, [
            {
                "title": "Mixed-device story",
                "severity": "HIGH",
                "f_refs": ["pricing F-10", "visual-cta F-67"],
            }
        ])
        stories = load_v2_priority_path(
            tmp_path,
            actionable_refs={"pricing F-10"},  # desktop has F-10, not F-67
            device="desktop",
        )
        assert len(stories) == 1
        story = stories[0]
        assert story["applies_on_other_device"] is False
        assert story["fixes_count"] == 1  # only pricing F-10 actionable
        # One actionable + one applies-elsewhere
        flags = [u.get("applies_on_other_device", False) for u in story["underlying"]]
        assert flags == [False, True]

    def test_story_with_all_actionable_refs_is_normal(self, tmp_path: Path):
        """Sanity: nothing changes for stories fully on the current device."""
        _synth_with_stories(tmp_path, [
            {
                "title": "All-desktop story",
                "severity": "MEDIUM",
                "f_refs": ["pricing F-10", "trust-credibility F-27"],
            }
        ])
        stories = load_v2_priority_path(
            tmp_path,
            actionable_refs={"pricing F-10", "trust-credibility F-27"},
            device="desktop",
        )
        assert len(stories) == 1
        story = stories[0]
        assert story["applies_on_other_device"] is False
        assert story["fixes_count"] == 2
        assert all(
            not u.get("applies_on_other_device", False) for u in story["underlying"]
        )

    def test_truly_empty_story_still_dropped(self, tmp_path: Path):
        """Stories with no parseable refs at all (regex mismatch on every
        entry) still drop — only the cross-device case is preserved."""
        _synth_with_stories(tmp_path, [
            {"title": "Junk story", "severity": "LOW", "f_refs": ["not-a-real-ref"]}
        ])
        stories = load_v2_priority_path(
            tmp_path, actionable_refs={"pricing F-10"}, device="desktop",
        )
        assert stories == []


# ---------------------------------------------------------------------------
# Cross-device count parity matches Codex's awdmods repro shape
# ---------------------------------------------------------------------------


class TestAwdmodsLikeCrossDeviceParity:
    """The exact Codex repro shape: 5 synth stories, one of them mobile-only.
    Desktop and mobile loaders must both return 5 stories, with the
    mobile-only one rendered as applies_on_other_device on desktop."""

    def test_desktop_and_mobile_counts_agree_with_synth(self, tmp_path: Path):
        _synth_with_stories(tmp_path, [
            {"title": "Variant pre-selection", "severity": "HIGH",
             "f_refs": ["visual-cta F-31", "performance-ux F-65"]},
            {"title": "Price-block concentration", "severity": "HIGH",
             "f_refs": ["pricing F-35", "trust-credibility F-10"]},
            {"title": "Mobile overlay storm", "severity": "HIGH",
             "f_refs": ["performance-ux F-67", "product-media F-20",
                        "performance-ux F-18", "visual-cta F-67"]},  # mobile-only
            {"title": "Schema rebuild", "severity": "MEDIUM",
             "f_refs": ["trust-credibility F-75", "content-seo F-61"]},
            {"title": "Quick wins", "severity": "MEDIUM",
             "f_refs": ["content-seo F-33", "ethics F-05"]},
        ])
        desktop_actionable = {
            "visual-cta F-31", "performance-ux F-65", "pricing F-35",
            "trust-credibility F-10", "trust-credibility F-75",
            "content-seo F-61", "content-seo F-33", "ethics F-05",
        }
        mobile_actionable = {
            "visual-cta F-31", "performance-ux F-65", "pricing F-35",
            "trust-credibility F-10",
            "performance-ux F-67", "product-media F-20",
            "performance-ux F-18", "visual-cta F-67",
            "trust-credibility F-75", "content-seo F-61",
            "content-seo F-33", "ethics F-05",
        }
        desktop_stories = load_v2_priority_path(
            tmp_path, actionable_refs=desktop_actionable, device="desktop",
        )
        mobile_stories = load_v2_priority_path(
            tmp_path, actionable_refs=mobile_actionable, device="mobile",
        )

        # The Codex-visible bug: pre-fix this was 4 on desktop, 5 on mobile
        assert len(desktop_stories) == 5, (
            "Desktop story count must match synth count (5). Pre-Phase-6 "
            "the mobile-only 'overlay storm' story was silently dropped on "
            "desktop. Codex 2026-05-18 review Q3."
        )
        assert len(mobile_stories) == 5

        # The third story (mobile overlay storm) is faded on desktop, normal on mobile
        assert desktop_stories[2]["applies_on_other_device"] is True
        assert mobile_stories[2]["applies_on_other_device"] is False


# ---------------------------------------------------------------------------
# Canary: priority_path_count_parity
# ---------------------------------------------------------------------------


class TestAppliesOnOtherDeviceRowNonInteractive:
    """Phase 6 hardening (2026-05-18) — Codex 19a4f51 review.
    The faded "applies on the other device" rows were visually disabled
    but functionally still selectable: the shared click delegator,
    brief toggle, select-all-visible, and keyboard nav all gate on
    .priority-ref-row[data-fid], so a row with both
    `priority-card-applies-elsewhere` styling AND data-fid could
    silently add a non-existent finding to the brief or "select" a fid
    with no detail card. Fix: drop data-fid from those rows entirely so
    every existing JS path naturally skips them. Sentinel
    data-applies-on-other-device="true" + data-ref carry the f_ref
    string for tooltip/display without making the row interactive.
    """

    def _render(self) -> str:
        from report.templates.components import build_priority_tab_html
        stories = [{
            "title": "Mixed-device story",
            "severity": "HIGH",
            "fixes_count": 1,
            "spans_clusters": ["pricing", "visual-cta"],
            "description": "Some description",
            "action": "",
            "applies_on_other_device": False,
            "underlying": [
                {"cluster": "pricing", "index": 10, "label": "pricing F-10"},
                {"cluster": "visual-cta", "index": 67, "label": "visual-cta F-67",
                 "applies_on_other_device": True},
            ],
            "mode": "severity",
        }]
        findings_by_fid = {
            "pricing/F-10": {"title": "Local desktop finding"},
            # visual-cta/F-67 deliberately NOT in this map — it's the
            # "other device" finding the renderer must NOT make
            # selectable. Pre-fix, a click on the faded row would fire
            # selectFinding("visual-cta/F-67") and the UI would clear
            # the empty state with no detail card to show.
        }
        return build_priority_tab_html(stories, findings_by_fid)

    def test_applies_elsewhere_row_has_no_data_fid(self):
        """The exact regression Codex flagged: applies-elsewhere row
        must not carry data-fid, so the shared click delegator (which
        gates on row.hasAttribute('data-fid')) skips it."""
        html = self._render()
        # The applies-elsewhere row must be present in output...
        assert "underlying-applies-elsewhere" in html
        # ...but it must NOT carry data-fid pointing at the other-device fid
        assert 'data-fid="visual-cta/F-67"' not in html, (
            "applies-elsewhere row carries data-fid='visual-cta/F-67' — "
            "the shared JS click delegator will treat this as selectable, "
            "select a non-existent finding, and silently add it to the "
            "brief. Codex 2026-05-18 review of 19a4f51."
        )

    def test_applies_elsewhere_row_carries_sentinel_and_data_ref(self):
        """The sentinel is what future selectors should use to find
        these rows; data-ref carries the f_ref string for display only."""
        html = self._render()
        assert 'data-applies-on-other-device="true"' in html
        assert 'data-ref="visual-cta/F-67"' in html
        assert 'aria-disabled="true"' in html

    def test_normal_underlying_row_still_has_data_fid(self):
        """Sanity: only applies-elsewhere rows lose data-fid. Normal
        rows must stay fully interactive."""
        html = self._render()
        assert 'data-fid="pricing/F-10"' in html

    def test_js_handler_selectors_skip_applies_elsewhere_row(self):
        """Behavioral proxy: parse the rendered HTML and emulate the
        querySelectors the four shipped JS handlers use. None of them
        should return the applies-elsewhere row.

        Selectors audited (from scripts/report/templates/js.py):
          - Click delegator + brief toggle: '.finding-row, .priority-ref-row'
            then gated on row.hasAttribute('data-fid')
          - updateBriefUI ('in-brief' class): '.finding-row, .priority-ref-row'
            then `if (fid)` guard
          - toggleSelectAllVisible: '.priority-ref-row' then `if (f)` guard
          - Keyboard nav: '.priority-ref-row[data-fid]' (selector-level
            filter)
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            pytest.skip("BeautifulSoup not installed; behavioral proxy skipped")

        soup = BeautifulSoup(self._render(), "html.parser")

        # Selector 1: keyboard nav uses the strictest selector — applies-
        # elsewhere row must NOT match
        kbd_rows = soup.select(".priority-ref-row[data-fid]")
        kbd_fids = {r.get("data-fid") for r in kbd_rows}
        assert "visual-cta/F-67" not in kbd_fids
        assert "pricing/F-10" in kbd_fids

        # Selector 2: brief/click handlers iterate all priority-ref-row
        # then gate on data-fid existence in JS. Emulate the guard:
        all_rows = soup.select(".priority-ref-row")
        interactive_fids = [
            r.get("data-fid") for r in all_rows if r.get("data-fid")
        ]
        assert "visual-cta/F-67" not in interactive_fids
        assert "pricing/F-10" in interactive_fids

        # Sanity: the applies-elsewhere row IS present in the DOM (just
        # not interactive) — proves we didn't regress the visibility fix
        applies_rows = soup.select(
            ".priority-ref-row.underlying-applies-elsewhere"
        )
        assert len(applies_rows) == 1
        assert applies_rows[0].get("data-fid") is None

    def test_faded_story_card_does_not_attach_data_fid_to_inner_rows(self):
        """Story-level faded cards (whole story applies elsewhere) have
        EVERY underlying row flagged applies_on_other_device. None of
        those rows should carry data-fid."""
        from report.templates.components import build_priority_tab_html
        stories = [{
            "title": "Mobile-only story",
            "severity": "HIGH",
            "fixes_count": 0,
            "spans_clusters": ["visual-cta", "performance-ux"],
            "description": "",
            "action": "",
            "applies_on_other_device": True,
            "underlying": [
                {"cluster": "visual-cta", "index": 67, "label": "visual-cta F-67",
                 "applies_on_other_device": True},
                {"cluster": "performance-ux", "index": 18,
                 "label": "performance-ux F-18", "applies_on_other_device": True},
            ],
            "mode": "severity",
        }]
        html = build_priority_tab_html(stories, findings_by_fid={})
        # Card is faded
        assert "priority-card-applies-elsewhere" in html
        # None of the underlying refs have data-fid
        assert 'data-fid="visual-cta/F-67"' not in html
        assert 'data-fid="performance-ux/F-18"' not in html
        # All carry the sentinel
        assert html.count('data-applies-on-other-device="true"') == 2


class TestPriorityPathCountParityCanary:
    def test_canary_skips_when_no_synth(self, tmp_path: Path):
        from assembly.canary_checks import check_priority_path_count_parity
        result = check_priority_path_count_parity(
            tmp_path / "synthesizer-emission-v1.json", tmp_path,
        )
        assert result["passed"] is True
        assert "skipped" in result["summary"]

    def test_canary_passes_when_counts_agree(self, tmp_path: Path):
        # Build a minimal engagement: synth + audit-{device}.md present,
        # no cluster emissions or batons. load_v2_findings returns []
        # (no actionable refs), so every synth story becomes
        # applies_on_other_device — but the canary checks COUNTS, not
        # which device a story lives on. 1 synth story → 1 loader card
        # on each device.
        _synth_with_stories(tmp_path, [
            {"title": "Test story", "severity": "MEDIUM",
             "f_refs": ["pricing F-10"]},
        ])
        # Empty audit files so the renderer can run
        (tmp_path / "audit-desktop.md").write_text("# audit", encoding="utf-8")
        (tmp_path / "audit-mobile.md").write_text("# audit", encoding="utf-8")
        from assembly.canary_checks import check_priority_path_count_parity
        result = check_priority_path_count_parity(
            tmp_path / "synthesizer-emission-v1.json", tmp_path,
        )
        assert result["passed"] is True, f"Got: {result}"
        assert result["detail"]["synth_count"] == 1

    def test_canary_in_run_all_canaries_block(self, tmp_path: Path):
        """The canary is wired into run_all_canaries as the 4th result."""
        # Minimal engagement that satisfies the other 3 canaries' inputs
        (tmp_path / "ethics-findings.json").write_text(json.dumps({
            "schema_version": 1, "engagement_id": "2026-05-18-deadbeef",
            "cluster": "ethics", "device": "page",
            "specialist_model": {"family": "sonnet", "version": "4.6"},
            "started_at": "2026-05-18T00:00:00.000Z",
            "completed_at": "2026-05-18T00:00:01.000Z",
            "status": "complete", "findings": [],
        }), encoding="utf-8")
        (tmp_path / "audit-desktop.md").write_text("# audit", encoding="utf-8")
        (tmp_path / "audit-mobile.md").write_text("# audit", encoding="utf-8")

        from assembly.canary_checks import run_all_canaries
        out = run_all_canaries(tmp_path, include_visual_quality=False)
        names = [r["name"] for r in out["results"]]
        assert "priority_path_count_parity" in names