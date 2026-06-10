"""Pin: ``raw_extras_by_local`` keys by JSON ``local_id`` (the same value the
dataclass's ``local_index`` is parsed from), not by enumerate-position.

Pre-fix (C9 audit): ``build_canonical_view`` built the extras map with
``enumerate(..., start=1)`` but looked it up by ``f.local_index``. The schema
(``schema/finding-v1.json``) only constrains ``local_id`` to 1..99 — no
uniqueness, no monotonic sequence. Any emission whose local_ids didn't equal
array positions silently lost ``reference_citations`` / ``proposed_anchor`` /
``change_type`` / ``element_*`` and defaulted ``severity`` to MEDIUM through
``extras.get("severity") or "MEDIUM"`` (~v2_loader.py:491). A Gold-cited HIGH
finding rendered uncited at MEDIUM.

This test emits two findings with ``local_id`` [2, 1] (reverse of positions)
and asserts each finding carries its OWN severity + citations through the
public loader, plus that the duplicate-local_id degenerate case is
deterministic (first-wins via setdefault).
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.v2_loader import build_canonical_view, load_v2_findings  # noqa: E402


def _finding(*, local_id: int, severity: str, title: str, citation_source: str,
             tier: str = "Silver", change_type: str = "copy",
             baton_index: str | None = None) -> dict:
    bi = baton_index or f"e{local_id}0"
    return {
        "cluster": "pricing",
        "device": "desktop",
        "local_id": local_id,
        "verdict": "FAIL",
        "title": title,
        "surface": "price-block",
        "element": {"baton_index": bi, "text_content": "$199.99", "role": "text"},
        "severity": severity,
        "scope": "device",
        "effort": {"change_type": change_type, "change_scope": "single-file"},
        "evidence_anchors": [{"type": "dom", "reference": bi}],
        "reference_citations": [{"source": citation_source, "tier": tier}],
        "observation": (
            "Long enough observation prose to satisfy the validator threshold "
            "for FAIL findings."
        ),
        "recommendation": (
            "Long enough recommendation prose to satisfy the validator "
            "threshold for FAIL findings."
        ),
        "why_this_matters": (
            "Anchoring is the highest-leverage pricing pattern for SKUs in "
            "the relevant range."
        ),
        "evidence_tier": tier,
    }


def _write_emission(eng: Path, *, cluster: str, device: str, findings: list[dict]) -> Path:
    payload = {
        "schema_version": 1,
        "engagement_id": "2026-06-10-c9c9c9c9",
        "cluster": cluster,
        "device": device,
        "specialist_model": {"family": "sonnet", "version": "4.6"},
        "started_at": "2026-06-10T00:00:00.000Z",
        "completed_at": "2026-06-10T00:00:01.000Z",
        "status": "complete",
        "findings": findings,
    }
    p = eng / f"cluster-{cluster}-{device}.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


class TestExtrasKeyedByLocalId(unittest.TestCase):
    """C9 regression: extras map keys/lookups must use JSON local_id."""

    def test_reverse_order_local_ids_keep_own_severity_and_citations(self):
        """Emit two findings with local_id [2, 1] (reverse of array positions).
        Each finding's severity + reference_citations must survive into the
        canonical view tied to the correct finding (i.e. the HIGH/Gold finding
        keeps HIGH/Gold; pre-fix it lost both and rendered as MEDIUM/Silver).
        """
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            eng = Path(tmp) / "engagement"
            eng.mkdir()
            # Array position 1 carries local_id=2 (the original "second" finding).
            # Array position 2 carries local_id=1 (the original "first" finding).
            f_lid2 = _finding(
                local_id=2,
                severity="HIGH",
                title="High severity finding with local_id 2",
                citation_source="price-anchoring.md",
                tier="Gold",
                change_type="copy",
            )
            f_lid1 = _finding(
                local_id=1,
                severity="LOW",
                title="Low severity finding with local_id 1",
                citation_source="cta-design.md",
                tier="Bronze",
                change_type="css",
            )
            _write_emission(eng, cluster="pricing", device="desktop",
                            findings=[f_lid2, f_lid1])

            cluster_paths = sorted(eng.glob("cluster-*.json"))
            by_canon, _aliases, _drops = build_canonical_view(cluster_paths, None)

            # display_index is assigned in parse order; pull both findings out
            # by title so the assertions don't depend on display_index ordering.
            by_title = {meta["title"]: meta for meta in by_canon.values()}
            self.assertIn("High severity finding with local_id 2", by_title)
            self.assertIn("Low severity finding with local_id 1", by_title)

            high = by_title["High severity finding with local_id 2"]
            low = by_title["Low severity finding with local_id 1"]

            # Pre-fix: high.severity == "LOW" (it picked up f_lid1's extras
            # because enumerate-position 1 matched local_index=2's lookup of
            # key=(cluster, device, 1) — wait, off-by-the-cross-wired-way:
            # extras[(cluster,desktop,1)] held f_lid2's data, lookup for the
            # finding parsed-as-local_index=2 (which IS f_lid2) used key
            # (cluster,desktop,2) and got f_lid1's extras. The net effect:
            # severity + citations swap between the two findings.
            self.assertEqual(high["severity"], "HIGH")
            self.assertEqual(high["evidence_tier"], "Gold")
            self.assertEqual(high["change_type"], "copy")
            self.assertEqual(
                [c["source"] for c in high["reference_citations"]],
                ["price-anchoring.md"],
            )

            self.assertEqual(low["severity"], "LOW")
            self.assertEqual(low["evidence_tier"], "Bronze")
            self.assertEqual(low["change_type"], "css")
            self.assertEqual(
                [c["source"] for c in low["reference_citations"]],
                ["cta-design.md"],
            )

    def test_reverse_order_local_ids_round_trip_through_public_loader(self):
        """End-to-end: load_v2_findings (the renderer-facing entry point) must
        surface each finding's own severity/tier/reference string. The C9 bug
        manifested at this layer — the HIGH/Gold finding rendered uncited at
        MEDIUM in the customer report.
        """
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            eng = Path(tmp) / "engagement"
            eng.mkdir()
            f_lid2 = _finding(
                local_id=2, severity="HIGH",
                title="High severity finding with local_id 2",
                citation_source="price-anchoring.md", tier="Gold",
            )
            f_lid1 = _finding(
                local_id=1, severity="LOW",
                title="Low severity finding with local_id 1",
                citation_source="cta-design.md", tier="Bronze",
            )
            _write_emission(eng, cluster="pricing", device="desktop",
                            findings=[f_lid2, f_lid1])

            findings = load_v2_findings(eng, "desktop")
            by_title = {f["title"]: f for f in findings}

            high = by_title["High severity finding with local_id 2"]
            low = by_title["Low severity finding with local_id 1"]

            self.assertEqual(high["severity"], "HIGH")
            self.assertEqual(high["tier"], "Gold")
            self.assertIn("price-anchoring.md", high["reference"])

            self.assertEqual(low["severity"], "LOW")
            self.assertEqual(low["tier"], "Bronze")
            self.assertIn("cta-design.md", low["reference"])

    def test_duplicate_local_ids_resolve_first_wins_deterministically(self):
        """Schema permits two findings sharing a local_id within one (cluster,
        device) file. The fix uses setdefault so the first-seen finding's
        extras win. This is the explicit contract — pin it so a future
        refactor that swaps to last-wins (raw_extras_by_local[key] = ...) is
        caught.
        """
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            eng = Path(tmp) / "engagement"
            eng.mkdir()
            f_first = _finding(
                local_id=1, severity="HIGH",
                title="First finding with local_id 1",
                citation_source="first.md", tier="Gold",
                baton_index="e11",
            )
            f_dup = _finding(
                local_id=1, severity="LOW",
                title="Duplicate finding with local_id 1",
                citation_source="second.md", tier="Bronze",
                baton_index="e12",
            )
            _write_emission(eng, cluster="pricing", device="desktop",
                            findings=[f_first, f_dup])

            by_canon, _aliases, _drops = build_canonical_view(
                sorted(eng.glob("cluster-*.json")), None,
            )

            # Both findings flow through the dataclass (they have different
            # titles; dedup keys on (cluster, baton_index, verdict, normalized
            # element/title)). Whichever one(s) end up in raw_by_ref will look
            # up the SAME extras key — the first-seen extras must win.
            for meta in by_canon.values():
                self.assertEqual(meta["severity"], "HIGH")
                self.assertEqual(meta["evidence_tier"], "Gold")
                self.assertEqual(
                    [c["source"] for c in meta["reference_citations"]],
                    ["first.md"],
                )


if __name__ == "__main__":
    unittest.main()
