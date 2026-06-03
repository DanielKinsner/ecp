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
import re
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


def analyze_device(engagement: Path, device: str, review_state_path: Path | None = None) -> dict | None:
    path = review_state_path or (engagement / f"review-state-{device}.json")
    if not path.exists():
        return None
    rs = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rs, dict):
        return None
    markers = _dedup_by_fref(rs.get("markers") or [])
    findings = rs.get("findings") or []

    stacks = _find_stacks(markers)
    stacked_frefs: dict[str, int] = {}
    for frefs in stacks.values():
        for fr in frefs:
            stacked_frefs[fr] = len(frefs)

    flagged: list[dict] = []
    strong_frefs: list[str] = []
    for m in markers:
        reasons = score_marker(m)
        fref = m.get("f_ref") or m.get("marker_id")
        if fref in stacked_frefs:
            reasons.append(f"stacked: {stacked_frefs[fref]} findings on one pixel")
        if not reasons:
            strong_frefs.append(fref)
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
        "strong": len(strong_frefs),
        "strong_frefs": strong_frefs,
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


# ---------------------------------------------------------------------------
# Tier-1 input: composite the marker box onto its screenshot and crop
# ---------------------------------------------------------------------------


def _screenshot_for(engagement: Path, slide_id: str | None) -> Path | None:
    """Map a slide_id (e.g. 'mobile-section-2') to its section screenshot file."""
    if not slide_id:
        return None
    n = slide_id.rsplit("-", 1)[-1]
    name = f"section-{n}-mobile.jpg" if slide_id.startswith("mobile") else f"section-{n}.jpg"
    cand = engagement / name
    return cand if cand.exists() else None


def _finding_index(rs: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for f in rs.get("findings") or []:
        if isinstance(f, dict) and f.get("f_ref"):
            out[f["f_ref"]] = f
    return out


def make_crop(engagement: Path, marker: dict, finding: dict | None,
              reasons: list[str], classification: str, out_dir: Path) -> dict | None:
    """Draw the marker box on its screenshot, crop to box+context, save a PNG."""
    from PIL import Image, ImageDraw

    shot = _screenshot_for(engagement, marker.get("slide_id"))
    if shot is None:
        return None
    try:
        img = Image.open(shot).convert("RGB")  # convert() forces load -> truncated/corrupt raises here
    except OSError:
        return None  # corrupt/truncated/non-image file -> skip like a missing screenshot
    W, H = img.size

    def pct(k: str) -> float:
        v = marker.get(k)
        return float(v) if isinstance(v, (int, float)) else 0.0

    left, top = pct("x_pct") / 100 * W, pct("y_pct") / 100 * H
    bw, bh = pct("w_pct") / 100 * W, pct("h_pct") / 100 * H

    draw = ImageDraw.Draw(img)
    draw.rectangle([left, top, left + bw, top + bh], outline=(249, 115, 22),
                   width=max(4, W // 240))

    margin = max(max(bw, bh) * 0.6, 220)
    crop = img.crop((max(0, int(left - margin)), max(0, int(top - margin)),
                     min(W, int(left + bw + margin)), min(H, int(top + bh + margin))))
    if max(crop.size) > 900:  # cap to keep vision-token cost low
        s = 900 / max(crop.size)
        crop = crop.resize((int(crop.size[0] * s), int(crop.size[1] * s)))

    fref = marker.get("f_ref") or "marker"
    slug = re.sub(r"[^a-z0-9]+", "-", fref.lower()).strip("-")
    out_path = out_dir / f"{marker.get('slide_id', 'slide')}__{slug}.png"
    crop.save(out_path, "PNG")

    ve = marker.get("visual_evidence") if isinstance(marker.get("visual_evidence"), dict) else {}
    oa = ve.get("observed_anchor") if isinstance(ve.get("observed_anchor"), dict) else {}
    f = finding or {}
    return {
        "f_ref": fref,
        "png": str(out_path),
        "slide_id": marker.get("slide_id"),
        "severity": marker.get("severity"),
        "classification": classification,
        "reasons": reasons,
        "finding_title": f.get("finding_title_override") or f.get("finding_title") or f.get("title", ""),
        "observation": (f.get("observation_override") or f.get("observation") or "")[:400],
        "element_hint": oa.get("selector_hint") or oa.get("text_quote") or "",
    }


def _select_for_mix(rep: dict, mix: int) -> list[tuple[str, list[str], str]]:
    """Pick a representative sample: stacked + HIGH-severity weak first, plus
    a couple of strong markers as controls. Returns (f_ref, reasons, class)."""
    def rank(f: dict) -> tuple:
        stacked = any("stacked" in r for r in f["reasons"])
        return (0 if stacked else 1, 0 if f.get("severity") == "HIGH" else 1)

    weak_sorted = sorted(rep["flagged"], key=rank)
    n_weak = max(1, mix - 2)
    picks = [(f["f_ref"], f["reasons"], "weak") for f in weak_sorted[:n_weak]]
    for fr in rep.get("strong_frefs", [])[: max(0, mix - len(picks))]:
        picks.append((fr, ["strong: exact element anchor (control)"], "strong"))
    return picks


def _cmd_audit(args: argparse.Namespace) -> int:
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


def _cmd_crops(args: argparse.Namespace) -> int:
    args.out.mkdir(parents=True, exist_ok=True)
    rs_path = args.review_state or (args.engagement / f"review-state-{args.device}.json")
    rs = json.loads(rs_path.read_text(encoding="utf-8"))
    if not isinstance(rs, dict):
        print(f"review-state root is not a JSON object: {rs_path}", file=sys.stderr)
        return 2
    raw_by_fref = {m["f_ref"]: m for m in _dedup_by_fref(rs.get("markers") or []) if m.get("f_ref")}
    findings = _finding_index(rs)
    rep = analyze_device(args.engagement, args.device, rs_path)

    if args.f_refs:
        flagged_reasons = {f["f_ref"]: f["reasons"] for f in rep["flagged"]}
        picks = [(fr, flagged_reasons.get(fr, ["strong (control)"]),
                  "weak" if fr in flagged_reasons else "strong")
                 for fr in [x.strip() for x in args.f_refs.split(",") if x.strip()]]
    else:
        picks = _select_for_mix(rep, args.mix)

    manifest = []
    for fref, reasons, classification in picks:
        m = raw_by_fref.get(fref)
        if not m:
            continue
        entry = make_crop(args.engagement, m, findings.get(fref), reasons, classification, args.out)
        if entry:
            manifest.append(entry)
            print(f"  {classification:6s} {fref}: {entry['png']}")

    man_path = args.out / "crops-manifest.json"
    man_path.write_text(json.dumps({"engagement": args.engagement.name, "device": args.device,
                                    "crops": manifest}, indent=2), encoding="utf-8")
    print(f"\nWrote {len(manifest)} crops + {man_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    force_utf8_io()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("audit", help="Tier-0 placement-confidence report")
    a.add_argument("--engagement", required=True, type=Path)
    a.add_argument("--device", default="both", choices=["desktop", "mobile", "both"])
    a.add_argument("--json", type=Path, default=None, help="write the full report JSON here")

    c = sub.add_parser("crops", help="composite marker boxes onto screenshots (Tier-1 input)")
    c.add_argument("--engagement", required=True, type=Path)
    c.add_argument("--device", default="desktop", choices=["desktop", "mobile"])
    c.add_argument("--out", required=True, type=Path)
    c.add_argument("--mix", type=int, default=6, help="auto-select N markers (weak + strong controls)")
    c.add_argument("--f-refs", default=None, help="comma-separated f_refs to crop (overrides --mix)")
    c.add_argument("--review-state", type=Path, default=None,
                   help="override the review-state file (e.g. a .repaired.json for re-verify)")

    args = parser.parse_args(argv)
    if args.cmd == "audit":
        return _cmd_audit(args)
    if args.cmd == "crops":
        return _cmd_crops(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
