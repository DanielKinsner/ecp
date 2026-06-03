"""Tier-0 hotspot-placement confidence audit (deterministic, zero-token).

The renderer reports "0 unplaced" when every finding received *some* coordinate
via the 4-strategy resolver — but that says nothing about whether the hotspot
landed on the right element. This tool reads the review-state markers and flags
the placements that are statistically suspect WITHOUT looking at pixels:

  - section / viewport fallbacks (no element anchor)
  - low-confidence / proxy (G6-downranked parent-container) markers
  - oversized rectangles (likely a parent container, not the subject)
  - markers with no snapped baton element
  - STACKS: 3+ distinct findings resolving to the same pixel (the
    "section-bottom-overlay collapse" failure from the 2026-06-02 diagnosis)

It is the free first stage of the visual-QA gate: cull the obviously-fine
element-anchored hotspots so the paid vision verifier only looks at suspects.
Implements Fix #4 from docs/2026-06-02-hotspot-placement-diagnosis.md as a
standalone analyzer (does not modify the renderer / any frozen contract).

Usage:
    python scripts/report/placement_audit.py audit --engagement <dir> [--device both]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cli_io import force_utf8_io  # noqa: E402

# Thresholds mirror scripts/assembly/visual_quality.py (kept in sync by intent;
# inlined so this tool stays dependency-light and standalone).
GIANT_WIDTH_PCT = 85.0
GIANT_HEIGHT_PCT = 70.0
NON_EXACT_TYPES = frozenset(
    {"proxy_element", "generated_expected_zone", "section_absence", "page_level"}
)
WEAK_SOURCES = {
    "proposed_anchor_section": "section-fallback (no element anchor)",
    "proposed_anchor_viewport": "viewport-fallback (no element anchor)",
}
STACK_MIN = 3  # >= this many distinct findings on one pixel = a stack
_DEVICES = ("desktop", "mobile")


def score_marker(m: dict) -> list[str]:
    """Return a list of weak-placement reasons for a marker; empty == strong."""
    reasons: list[str] = []
    source = m.get("source") or ""
    ve = m.get("visual_evidence") if isinstance(m.get("visual_evidence"), dict) else {}
    conf = ve.get("confidence")
    vtype = ve.get("type")

    if source in WEAK_SOURCES:
        reasons.append(WEAK_SOURCES[source])
    if conf == "low":
        reasons.append("low confidence")
    if vtype in NON_EXACT_TYPES:
        reasons.append(f"non-exact placement type ({vtype})")

    w = m.get("w_pct")
    h = m.get("h_pct")
    if isinstance(w, (int, float)) and w > GIANT_WIDTH_PCT:
        reasons.append(f"oversized width {w:.0f}% (likely parent container)")
    if isinstance(h, (int, float)) and h > GIANT_HEIGHT_PCT:
        reasons.append(f"oversized height {h:.0f}% (likely parent container)")

    if source.startswith("proposed_anchor") and m.get("snapped_baton_index") is None:
        reasons.append("no snapped baton element")
    return reasons


def _dedup_by_fref(markers: list[dict]) -> list[dict]:
    """Collapse AI-twin markers: one marker per f_ref (first wins)."""
    seen: set[str] = set()
    out: list[dict] = []
    for m in markers:
        if not isinstance(m, dict):
            continue
        fref = m.get("f_ref") or m.get("marker_id") or id(m)
        if fref in seen:
            continue
        seen.add(fref)
        out.append(m)
    return out


def _find_stacks(markers: list[dict]) -> dict[tuple, list[str]]:
    """Group distinct f_refs by (slide_id, rounded pixel); keep stacks >= STACK_MIN."""
    groups: dict[tuple, list[str]] = defaultdict(list)
    for m in markers:
        x = m.get("x_pct")
        y = m.get("y_pct")
        if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
            continue
        key = (m.get("slide_id"), round(x, 1), round(y, 1))
        fref = m.get("f_ref") or m.get("marker_id")
        if fref not in groups[key]:
            groups[key].append(fref)
    return {k: v for k, v in groups.items() if len(v) >= STACK_MIN}


def analyze_device(engagement: Path, device: str) -> dict | None:
    path = engagement / f"review-state-{device}.json"
    if not path.exists():
        return None
    rs = json.loads(path.read_text(encoding="utf-8"))
    markers = _dedup_by_fref(rs.get("markers") or [])
    findings = rs.get("findings") or []

    stacks = _find_stacks(markers)
    stacked_frefs: dict[str, int] = {}
    for frefs in stacks.values():
        for fr in frefs:
            stacked_frefs[fr] = len(frefs)

    flagged: list[dict] = []
    strong = 0
    for m in markers:
        reasons = score_marker(m)
        fref = m.get("f_ref") or m.get("marker_id")
        if fref in stacked_frefs:
            reasons.append(f"stacked: {stacked_frefs[fref]} findings on one pixel")
        if not reasons:
            strong += 1
            continue
        ve = m.get("visual_evidence") if isinstance(m.get("visual_evidence"), dict) else {}
        flagged.append(
            {
                "f_ref": fref,
                "slide_id": m.get("slide_id"),
                "severity": m.get("severity"),
                "source": m.get("source"),
                "confidence": ve.get("confidence"),
                "type": ve.get("type"),
                "box": {k: m.get(k) for k in ("x_pct", "y_pct", "w_pct", "h_pct")},
                "reasons": reasons,
            }
        )

    return {
        "device": device,
        "total_markers": len(markers),
        "total_findings": len(findings),
        "strong": strong,
        "weak": len(flagged),
        "stacks": [
            {"slide_id": k[0], "x_pct": k[1], "y_pct": k[2], "f_refs": v}
            for k, v in sorted(stacks.items(), key=lambda kv: -len(kv[1]))
        ],
        "flagged": flagged,
    }


def analyze(engagement: Path, devices: tuple[str, ...] = _DEVICES) -> dict:
    out = {"engagement": engagement.name, "devices": {}}
    for dev in devices:
        res = analyze_device(engagement, dev)
        if res is not None:
            out["devices"][dev] = res
    return out


def _print_summary(report: dict) -> None:
    print(f"== Placement audit: {report['engagement']} ==")
    for dev, r in report["devices"].items():
        print(
            f"\n[{dev}] {r['total_markers']} markers / {r['total_findings']} findings"
            f"  ->  {r['strong']} strong, {r['weak']} weak"
        )
        if r["stacks"]:
            print(f"  STACKS ({len(r['stacks'])}): distinct findings collapsed to one pixel")
            for s in r["stacks"]:
                print(
                    f"    - {s['slide_id']} @ ({s['x_pct']}, {s['y_pct']}): "
                    f"{len(s['f_refs'])} findings -> {', '.join(map(str, s['f_refs']))}"
                )
        if r["flagged"]:
            print(f"  WEAK PLACEMENTS ({r['weak']}):")
            for f in r["flagged"]:
                print(f"    - {f['f_ref']} [{f['severity']}] {f['slide_id']}: {'; '.join(f['reasons'])}")


def main(argv: list[str] | None = None) -> int:
    force_utf8_io()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("audit", help="Tier-0 placement-confidence report")
    a.add_argument("--engagement", required=True, type=Path)
    a.add_argument("--device", default="both", choices=["desktop", "mobile", "both"])
    a.add_argument("--json", type=Path, default=None, help="write the full report JSON here")
    args = parser.parse_args(argv)

    devices = _DEVICES if args.device == "both" else (args.device,)
    report = analyze(args.engagement, devices)
    if not report["devices"]:
        print(f"No review-state-*.json found under {args.engagement}", file=sys.stderr)
        return 2
    _print_summary(report)
    out_path = args.json or (args.engagement / "placement-audit.json")
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
