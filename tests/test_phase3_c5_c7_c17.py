"""Phase 3 + C17 (2026-06-10) — reference-chain fixes.

C5: scripts/report/v2_loader.py mis-labels every ref absent from the
current device as ``applies_on_other_device=True`` — including
hallucinated refs the synthesizer prompt-level validator missed. The
report renders a confident "applies on the other device — see that
device's report" chip pointing at nothing.
Fix: before labelling, check the ref against the full cross-device
canonical view; a ref absent from BOTH devices renders as a visible
blocked/flagged ``ref_resolution_failed`` entry; a ref present on the
other device still gets the existing ``applies_on_other_device`` chip.

C7: scripts/assembly/dedup.py ``_absorb_losers`` discards loser
evidence_anchors, reference_citations, and evidence_tier when merging.
v2_loader.py reads ``merge_record["winner"]/["loser"]`` keys the
producer never emitted, so the devices_present augmentation is a dead
loop and cross-device merges report as single-device.
Fix: union loser evidence_anchors + reference_citations into the
winner; promote winner.tier to max(winner.tier, max(loser.tier)); fix
the v2_loader producer/consumer key mismatch so cross-device merges
populate devices_present.

C17: scripts/report/html_builder.py ``_compute_metrics`` computes
projected_lift; the legacy v1 baseline templates render it as a
"Projected Lift" KPI card. product.md §3 forbids ECP from promising
lift.
Fix: remove the metric entirely; assert no rendered v1 path and no
template carries the string ``Projected Lift`` / ``projected_lift``.

Mixed pytest + unittest style — both runners must discover.
"""
from __future__ import annotations

import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))


# ---------------------------------------------------------------------------
# C5 — other-device mislabel
# ---------------------------------------------------------------------------


def _write_synth(tmp: Path, stories: list[dict]) -> None:
    (tmp / "synthesizer-emission-v1.json").write_text(
        json.dumps({"priority_path": stories}), encoding="utf-8",
    )


class TestC5OtherDeviceMislabel:
    """The Priority Path loader must distinguish three cases:
        a) ref in current device's actionable_refs → normal interactive row
        b) ref absent from current device, present on the other device
           (i.e. present in canonical_refs) → faded ``applies_on_other_device``
        c) ref absent from BOTH devices (canonical_refs) → visible
           ``ref_resolution_failed`` blocked/flagged entry
    """

    def test_unresolved_ref_renders_as_blocked_not_other_device(self, tmp_path: Path):
        """The exact C5 bug: a story citing a ref absent from BOTH
        devices must NOT render as the confident
        ``applies_on_other_device`` chip pointing at nothing."""
        from report.v2_loader import load_v2_priority_path

        _write_synth(tmp_path, [{
            "title": "Hallucinated story",
            "severity": "HIGH",
            "f_refs": ["pricing F-99"],  # invented by the synthesizer
        }])
        stories = load_v2_priority_path(
            tmp_path,
            actionable_refs={"trust-credibility F-01"},
            device="desktop",
            canonical_refs={"trust-credibility F-01"},  # F-99 NOT in canonical
        )
        assert len(stories) == 1
        story = stories[0]
        # Must NOT be flagged as applies_on_other_device — the chip
        # would direct the customer at a finding that doesn't exist
        # anywhere.
        assert story["applies_on_other_device"] is False
        underlying = story["underlying"]
        assert len(underlying) == 1
        entry = underlying[0]
        assert entry.get("ref_resolution_failed") is True
        assert entry.get("applies_on_other_device") is not True
        assert story.get("unresolved_ref_count") == 1

    def test_genuine_other_device_ref_still_gets_chip(self, tmp_path: Path):
        """A ref absent from the current device but present in the
        canonical universe (i.e. it exists on the other device) keeps
        the existing applies_on_other_device chip."""
        from report.v2_loader import load_v2_priority_path

        _write_synth(tmp_path, [{
            "title": "Cross-device story",
            "severity": "HIGH",
            "f_refs": ["pricing F-10"],  # exists on mobile only
        }])
        stories = load_v2_priority_path(
            tmp_path,
            actionable_refs={"trust-credibility F-01"},  # desktop has F-01
            device="desktop",
            # Mobile carries pricing F-10; canonical universe sees both
            canonical_refs={"trust-credibility F-01", "pricing F-10"},
        )
        assert len(stories) == 1
        story = stories[0]
        underlying = story["underlying"]
        assert len(underlying) == 1
        entry = underlying[0]
        assert entry.get("applies_on_other_device") is True
        assert entry.get("ref_resolution_failed") is not True

    def test_mixed_unresolved_and_other_device_keeps_story_visible(self, tmp_path: Path):
        """A story with one unresolved ref and one cross-device ref
        must still render so the operator sees the failure."""
        from report.v2_loader import load_v2_priority_path

        _write_synth(tmp_path, [{
            "title": "Mixed story",
            "severity": "HIGH",
            "f_refs": ["pricing F-99", "pricing F-10"],
        }])
        stories = load_v2_priority_path(
            tmp_path,
            actionable_refs={"trust-credibility F-01"},
            device="desktop",
            canonical_refs={"trust-credibility F-01", "pricing F-10"},
        )
        assert len(stories) == 1
        story = stories[0]
        flags = [
            (u.get("ref_resolution_failed"), u.get("applies_on_other_device"))
            for u in story["underlying"]
        ]
        # The F-99 entry is unresolved; the F-10 entry is cross-device.
        assert (True, None) in flags or (True, False) in flags
        assert (None, True) in flags or (False, True) in flags

    def test_legacy_callers_without_canonical_refs_still_work(self, tmp_path: Path):
        """When the caller passes no canonical_refs (legacy), the
        pre-C5 behavior is preserved (everything missing → cross-device
        chip). Keeps backward compatibility while the renderer threads
        the new arg through."""
        from report.v2_loader import load_v2_priority_path

        _write_synth(tmp_path, [{
            "title": "Legacy story",
            "severity": "HIGH",
            "f_refs": ["pricing F-99"],
        }])
        stories = load_v2_priority_path(
            tmp_path,
            actionable_refs={"trust-credibility F-01"},
            device="desktop",
            # canonical_refs deliberately omitted
        )
        assert len(stories) == 1
        story = stories[0]
        # Legacy behavior: gets the applies_on_other_device chip
        assert story["underlying"][0].get("applies_on_other_device") is True

    def test_components_renders_unresolved_as_visible_alert(self):
        """The components.py renderer must surface ref_resolution_failed
        as an alert role with no data-fid (no detail card to link to)
        and explicit UNRESOLVED REF copy."""
        from report.templates.components import build_priority_tab_html

        stories = [{
            "title": "Hallucinated story",
            "severity": "HIGH",
            "fixes_count": 0,
            "spans_clusters": ["pricing"],
            "description": "",
            "action": "",
            "applies_on_other_device": False,
            "underlying": [{
                "cluster": "pricing",
                "index": 99,
                "label": "pricing F-99",
                "ref_resolution_failed": True,
            }],
            "mode": "severity",
        }]
        html = build_priority_tab_html(stories, findings_by_fid={})
        # Visible alert
        assert 'role="alert"' in html
        # No data-fid on the row (shared JS click delegator gates on it)
        assert 'data-fid="pricing/F-99"' not in html
        # Sentinel + UNRESOLVED REF copy present
        assert 'data-ref-resolution-failed="true"' in html
        assert "UNRESOLVED REF" in html
        # Class hook for styling
        assert "underlying-unresolved" in html


# ---------------------------------------------------------------------------
# C7 — merge data loss + dead attribution loop
# ---------------------------------------------------------------------------


def _f(**overrides):
    from assembly.models import EvidenceAnchor, Finding

    base = dict(
        cluster="pricing",
        device="desktop",
        local_index=1,
        verdict="FAIL",
        section="price-block",
        element="$69.95",
        element_normalized="$69.95",
        source="VISUAL",
        priority="HIGH",
        priority_rank=1,
        observation="x" * 25,
        recommendation="y" * 25,
        reference="r",
        title="T",
        tier="Silver",
        baton_index="e7",
        surface="price-block",
        scope="page",
        evidence_anchors=(EvidenceAnchor(type="dom", reference="e7"),),
    )
    base.update(overrides)
    return Finding(**base)


class TestC7AbsorbLosersUnionsFields(unittest.TestCase):
    """``_absorb_losers`` must union loser evidence_anchors into the
    winner, promote evidence_tier to max(winner, losers), and emit
    merged_keys / merged_devices so the consumer can union out-of-
    dataclass fields (reference_citations) too.
    """

    def test_evidence_anchors_unioned_across_losers(self):
        from assembly.dedup import _absorb_losers
        from assembly.models import EvidenceAnchor

        winner = _f(
            local_index=1, device="desktop",
            evidence_anchors=(EvidenceAnchor(type="dom", reference="e7"),),
        )
        loser = _f(
            local_index=2, device="mobile",
            evidence_anchors=(
                EvidenceAnchor(type="dom", reference="e7"),     # duplicate, dedup
                EvidenceAnchor(type="visual", reference="section-2.jpg"),
            ),
        )
        new_winner, record = _absorb_losers(winner, [loser], reason="test")
        anchors = list(new_winner.evidence_anchors)
        self.assertEqual(len(anchors), 2, "duplicate (dom, e7) anchor should dedup")
        refs = sorted(a.reference for a in anchors)
        self.assertEqual(refs, ["e7", "section-2.jpg"])

    def test_tier_promoted_when_loser_outranks_winner(self):
        from assembly.dedup import _absorb_losers

        winner = _f(tier="Silver", local_index=1, device="desktop")
        loser = _f(tier="Gold", local_index=2, device="mobile")
        new_winner, _ = _absorb_losers(winner, [loser], reason="test")
        self.assertEqual(
            new_winner.tier, "Gold",
            "Gold loser must promote winner.tier to keep schema "
            "invariant evidence_tier == max(citation tiers)."
        )

    def test_tier_kept_when_winner_already_outranks_loser(self):
        from assembly.dedup import _absorb_losers

        winner = _f(tier="Gold", local_index=1, device="desktop")
        loser = _f(tier="Silver", local_index=2, device="mobile")
        new_winner, _ = _absorb_losers(winner, [loser], reason="test")
        self.assertEqual(new_winner.tier, "Gold")

    def test_merge_record_emits_merged_devices_and_keys(self):
        from assembly.dedup import _absorb_losers

        winner = _f(local_index=1, device="desktop")
        loser = _f(local_index=2, device="mobile", cluster="pricing")
        _, record = _absorb_losers(winner, [loser], reason="test")
        # Shape symmetry with the v2_loader consumer
        self.assertIn("kept", record)
        self.assertEqual(record["kept"].get("device"), "desktop")
        self.assertIn("merged_devices", record)
        self.assertEqual(record["merged_devices"], ["mobile"])
        self.assertIn("merged_keys", record)
        self.assertEqual(record["merged_keys"][0]["device"], "mobile")
        self.assertEqual(record["merged_keys"][0]["local_index"], 2)


class TestC7DedupConsumerKeysAlign(unittest.TestCase):
    """The v2_loader's devices_present augmentation reads merge_record
    keys the producer must emit. Pre-fix it read winner/loser; post-fix
    it reads kept/merged_devices/merged_keys. This test pins the
    contract so the two ends can't drift again.
    """

    def test_consumer_keys_present_in_producer_output(self):
        from assembly.dedup import deduplicate_v2

        # Two scope=page findings sharing (cluster, baton_index, verdict)
        # — page-scope layer collapses them.
        a = _f(local_index=1, device="desktop")
        b = _f(local_index=2, device="mobile")
        result = deduplicate_v2([a, b])
        self.assertEqual(len(result.kept), 1, "page-scope layer should merge them")
        self.assertEqual(len(result.auto_merged), 1)
        record = result.auto_merged[0]
        # Consumer (v2_loader.build_canonical_view augmentation) reads
        # exactly these keys — pin them here so a refactor of either
        # end can't silently regress to a dead loop again.
        self.assertIn("kept", record)
        self.assertIn("merged_from", record)
        self.assertIn("merged_devices", record)
        self.assertIn("merged_keys", record)
        # And the kept dict carries the canonical winner's device so
        # the augmentation can union it into devices_present even when
        # the layer doesn't merge.
        self.assertIn("device", record["kept"])


class TestC7CrossDevicePageScopeMergeRoundTrip(unittest.TestCase):
    """End-to-end: a page-scope merge of a desktop-Gold + mobile-Silver
    finding yields ``devices_present = ["desktop", "mobile"]`` and the
    union of citations on the canonical winner.
    """

    def _build_engagement(self, tmp: Path) -> None:
        """Two cluster emissions citing the same baton_index with
        scope=page, different devices, different evidence tiers."""
        def _emission(cluster, device, findings):
            return {
                "schema_version": 1,
                "engagement_id": "2026-06-10-c7c7c7c7",
                "cluster": cluster,
                "device": device,
                "specialist_model": {"family": "sonnet", "version": "4.6"},
                "started_at": "2026-06-10T00:00:00.000Z",
                "completed_at": "2026-06-10T00:01:00.000Z",
                "status": "complete",
                "findings": findings,
            }

        def _finding(local_id, device, tier, citation_section):
            return {
                "cluster": "pricing",
                "device": device,
                "local_id": local_id,
                "verdict": "FAIL",
                "title": "Price block lacks MSRP anchor",
                "surface": "price-block",
                "element": {
                    "baton_index": "e7",
                    "text_content": "$69.95",
                    "role": "text",
                },
                "severity": "HIGH",
                "scope": "page",
                "effort": {
                    "change_type": "copy",
                    "change_scope": "single-file",
                },
                "confidence": 0.85,
                "evidence_anchors": [{"type": "dom", "reference": "e7"}],
                "reference_citations": [
                    {
                        "source": "price-anchoring.md",
                        "section": citation_section,
                        "tier": tier,
                    }
                ],
                "observation": (
                    "The product price renders as a single number with no "
                    "anchor — no MSRP strikethrough or compare-at framing."
                ),
                "recommendation": (
                    "Render the MSRP as a strikethrough above the live "
                    "price so the discount is anchored against a reference."
                ),
                "why_this_matters": (
                    "Anchoring is the highest-leverage pricing pattern for "
                    "SKUs in the $50-500 range; absent anchor lowers AOV."
                ),
                "evidence_tier": tier,
            }

        (tmp / "cluster-pricing-desktop.json").write_text(
            json.dumps(_emission(
                "pricing", "desktop",
                [_finding(1, "desktop", "Gold", "gold-anchor")],
            )),
            encoding="utf-8",
        )
        (tmp / "cluster-pricing-mobile.json").write_text(
            json.dumps(_emission(
                "pricing", "mobile",
                [_finding(1, "mobile", "Silver", "silver-anchor")],
            )),
            encoding="utf-8",
        )

    def test_devices_present_and_citation_union(self):
        import tempfile
        from report.v2_loader import build_canonical_view

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            self._build_engagement(tmp)
            cluster_paths = sorted(tmp.glob("cluster-pricing-*.json"))
            by_ref, _aliases, dropped = build_canonical_view(cluster_paths, None)
            # The two device emissions must have collapsed to one
            # canonical ref via the page-scope layer.
            self.assertEqual(
                len(by_ref), 1,
                f"page-scope merge should collapse to one canonical ref "
                f"(got {len(by_ref)}: {list(by_ref.keys())}) — dropped={dropped}",
            )
            (canonical_ref,) = by_ref.keys()
            meta = by_ref[canonical_ref]
            # C7: devices_present must reflect BOTH devices, not just
            # the canonical winner's device.
            self.assertEqual(
                sorted(meta["devices_present"]),
                ["desktop", "mobile"],
                "devices_present must be {desktop, mobile} after page-"
                "scope merge — pre-fix the dead loop kept it single.",
            )
            # C7: citation union must include both refs.
            citation_sections = sorted(
                rc.get("section") for rc in (meta.get("reference_citations") or [])
            )
            self.assertEqual(
                citation_sections,
                ["gold-anchor", "silver-anchor"],
                "Loser reference_citations must union onto the kept finding.",
            )
            # And the evidence_tier on the renderer-facing view must be
            # the max of the unioned tiers (Gold > Silver).
            self.assertEqual(meta.get("evidence_tier"), "Gold")


# ---------------------------------------------------------------------------
# C17 — projected_lift purge
# ---------------------------------------------------------------------------


class TestC17ProjectedLiftPurged(unittest.TestCase):
    """``_compute_metrics`` must not emit projected_lift. The rendered
    HTML and shipped templates must not contain the string ``Projected
    Lift`` or ``projected_lift`` — product.md §3 forbids ECP from
    promising lift.
    """

    def test_compute_metrics_returns_no_projected_lift_key(self):
        from report.html_builder import _compute_metrics

        findings = [
            {"priority": "CRITICAL", "tier": "Gold"},
            {"priority": "HIGH", "tier": "Silver"},
            {"priority": "MEDIUM", "tier": "Bronze"},
            {"priority": "LOW", "tier": "Bronze"},
        ]
        metrics = _compute_metrics(findings)
        self.assertNotIn("projected_lift", metrics)
        # Sanity: the other keys we still rely on are present.
        for required in (
            "severity_counts",
            "total_findings",
            "evidence_confidence_label",
            "evidence_confidence_class",
        ):
            self.assertIn(required, metrics)

    def test_v1_renderer_output_does_not_render_projected_lift(self):
        """Hit the html_builder._build_html_fragments path with the
        post-fix metrics dict (no projected_lift) and confirm none of
        the rendered fragments contain the forbidden strings."""
        from report.html_builder import _build_html_fragments

        f = {
            "index": 1,
            "verdict": "FAIL",
            "cluster": "performance-ux",
            "priority": "HIGH",
            "section": "speculation-rules",
            "element": "head script",
            "observation": "No Speculation Rules present.",
            "recommendation": "Add Speculation Rules.",
        }
        fragments = _build_html_fragments(
            findings=[f],
            priority_path_stories=[],
            slide_markers={},
            metrics={
                "severity_counts": {
                    "critical": 0, "high": 1, "medium": 0, "low": 0,
                },
                "total_findings": 1,
                "evidence_confidence_label": "HIGH",
                "evidence_confidence_class": "",
            },
            has_ethics_violations=False,
            screenshots={
                "slide_base64": [],
                "slide_aspect_ratios": [],
                "default_slide_aspect_ratio": "16 / 9",
            },
            audit_md_text="",
        )
        for key, value in fragments.items():
            if not isinstance(value, str):
                continue
            self.assertNotIn(
                "Projected Lift", value,
                f"fragment {key} renders 'Projected Lift' — product.md §3 "
                f"forbids ECP from promising lift.",
            )
            self.assertNotIn("projected_lift", value)

    def test_templates_do_not_contain_projected_lift(self):
        """Grep-guard the active scripts/report/templates/ directory.
        Baseline HTML fixtures under tests/baseline are legacy
        artifacts (see tests/baseline/README.md) and NOT in scope."""
        templates_dir = REPO_ROOT / "scripts" / "report" / "templates"
        for py_file in templates_dir.glob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            self.assertNotIn(
                "Projected Lift", text,
                f"{py_file} mentions 'Projected Lift' — product.md §3 "
                f"forbids ECP from promising lift.",
            )
            self.assertNotIn(
                "projected_lift", text,
                f"{py_file} references projected_lift — the metric was "
                f"removed in C17 (2026-06-10).",
            )

    def test_html_builder_no_longer_computes_projected_lift(self):
        """Grep-guard the html_builder itself: no projected_lift symbol
        in the module body (the docstring mention is fine because
        it documents WHY the metric was removed)."""
        builder_path = REPO_ROOT / "scripts" / "report" / "html_builder.py"
        text = builder_path.read_text(encoding="utf-8")
        # Strip docstring mentions before grepping for live references:
        # the C17 comment block in _compute_metrics intentionally cites
        # the removed name to document the change.
        lines = text.split("\n")
        in_docstring = False
        suspect_lines = []
        for ln in lines:
            stripped = ln.lstrip()
            # Naive: treat lines inside triple-quoted regions as
            # documentation. Good enough for a grep-guard.
            if '"""' in stripped:
                # Toggle on every triple-quote occurrence
                in_docstring = not in_docstring if stripped.count('"""') % 2 == 1 else in_docstring
                continue
            if in_docstring:
                continue
            if stripped.startswith("#"):
                continue
            if "projected_lift" in stripped or "Projected Lift" in stripped:
                suspect_lines.append(ln)
        self.assertEqual(
            suspect_lines, [],
            "html_builder.py still has live references to projected_lift: "
            + repr(suspect_lines),
        )


if __name__ == "__main__":
    unittest.main()
