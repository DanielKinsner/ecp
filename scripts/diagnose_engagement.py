#!/usr/bin/env python3
"""ECP engagement diagnostic - stage-attribution triage for hotspot/finding defects.

THE PROBLEM THIS SOLVES: a single visible defect (a wrong hotspot, a false
finding) can be born at any pipeline stage, and right now nothing says WHICH:

    ACQUISITION  ->  BATON  ->  SPECIALIST  ->  SYNTHESIZER  ->  PLACEMENT/RENDER
   (capture the     (extract   (write the      (humanize +     (map findings to
    real page)       elements)   findings)       de-dupe)        screenshot pixels)

If the hero captured black (acquisition), the specialist's "empty hero" finding
is GARBAGE-IN - no amount of placement tuning fixes it. If the specialist anchored
"items over $1,000" to a $135 part, that's a SPECIALIST defect, not geometry. If a
region finding rendered as a stacked point-circle, that's PLACEMENT. You cannot
tune the right knob until you know which stage to blame.

This tool reads a *completed* engagement folder (offline - no browser, no live
re-fetch), attributes every finding/hotspot to the stage that owns its defect,
crops each hotspot onto its screenshot for visual confirmation, and prints a
"ship / do-not-ship" verdict plus a per-stage "tune this" list.

USAGE
    python scripts/diagnose_engagement.py --engagement docs/ecp/<id> [--device both]

OUTPUT  (under <engagement>/_diagnosis/)
    report-<device>.md           verdict + capture signals + accountability table + tune-guide
    diagnosis.json               machine-readable (for an agent to act on)
    crops/<device>-<f_ref>.png   each hotspot cropped from its section screenshot,
                                 with the marker drawn - LOOK AT THESE.

It is deterministic and conservative: it never claims a finding is true/false
(that needs your eyes or a vision model on the crops). It tells you where to LOOK
and which stage is accountable.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw
    _HAVE_PIL = True
except Exception:  # noqa: BLE001 - PIL is optional; crops are skipped without it
    _HAVE_PIL = False

# --- tunables (documented in docs/2026-06-08-hotspot-diagnosis-protocol.md) ---
STACK_RADIUS_PCT = 6.0       # markers within this %-distance on a slide = a stack
STACK_MIN = 2                # >= this many in a cluster => flagged as stacked
VOID_ROW_FRAC = 0.90         # a row counts as "void" if >=90% of px are one flat color
ABOVE_FOLD_VOID_FLAG = 0.35  # >= this fraction of above-fold void rows => capture-suspect
VOID_TOL = 16                # luminance tolerance for "same flat color"

_REGION_WORDS = re.compile(
    r"\b(band|banner|hero|above[- ]?fold|masthead|section|zone|whole|entire|"
    r"region|viewport|area|top of the page|empty (black )?space|black void)\b", re.I)
_BLANK_WORDS = re.compile(
    r"\b(empty|blank|black (band|space|void)|no (supporting )?(media|image|photo|"
    r"headline|hero|value prop)|nothing|wasted)\b", re.I)
_PRICE = re.compile(r"\$\s?([0-9][0-9,]*(?:\.[0-9]{1,2})?)")
_OVER = re.compile(r"\b(over|above|more than|greater than|exceed[s]?|north of)\b|>\s?\$", re.I)
_UNDER = re.compile(r"\b(under|below|less than|cheaper than)\b|<\s?\$", re.I)


def _load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _money(s: str) -> float:
    try:
        return float(s.replace(",", ""))
    except ValueError:
        return float("nan")


def _elements_by_index(baton: dict | None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not isinstance(baton, dict):
        return out
    for e in baton.get("elements") or []:
        idx = e.get("e_index")
        if idx:
            out[str(idx)] = e
    return out


def _anchor_index(marker: dict) -> str | None:
    snap = marker.get("snapped_baton_index")
    if snap is not None:
        return f"e{snap}" if not str(snap).startswith("e") else str(snap)
    ve = marker.get("visual_evidence") or {}
    oa = ve.get("observed_anchor") if isinstance(ve, dict) else None
    if isinstance(oa, dict) and oa.get("baton_index"):
        return str(oa["baton_index"])
    return None


def _ve_type_conf(marker: dict) -> tuple[str, str]:
    ve = marker.get("visual_evidence")
    if isinstance(ve, dict):
        return str(ve.get("type") or ""), str(ve.get("confidence") or "")
    return "", ""


# ---------------------------------------------------------------------------
# Acquisition / capture signals
# ---------------------------------------------------------------------------

def capture_signals(dom_html: str, baton: dict | None, slides: list[dict],
                    eng: Path) -> dict:
    sig: dict[str, Any] = {}
    sig["dom_scroll_trigger"] = len(re.findall(r"scroll-trigger", dom_html))
    sig["dom_animate"] = len(re.findall(r'class="[^"]*animate--', dom_html))
    sig["dom_lazy_img"] = len(re.findall(r'loading="lazy"', dom_html))
    sig["dom_video"] = len(re.findall(r"<video[\s>]", dom_html, re.I))

    # Per-slide above-fold flatness (PIL). The above-fold slide (section_index 0)
    # is the one that matters most; we score all but flag the first.
    sig["slides"] = []
    for sl in slides:
        src = eng / str(sl.get("source") or "")
        rec = {"slide_id": sl.get("slide_id"), "source": sl.get("source"),
               "section_index": sl.get("section_index"), "void_row_frac": None}
        if _HAVE_PIL and src.exists():
            rec["void_row_frac"] = _void_row_fraction(src)
        sig["slides"].append(rec)
    af = next((s for s in sig["slides"] if s.get("section_index") == 0), None)
    vr = (af or {}).get("void_row_frac")
    sig["above_fold_void_frac"] = vr
    sig["capture_suspect"] = bool(
        vr is not None and vr >= ABOVE_FOLD_VOID_FLAG
        and (sig["dom_scroll_trigger"] > 0 or sig["dom_lazy_img"] > 0 or sig["dom_video"] > 0)
    )

    # Above-fold element desert: the largest vertical gap (px) inside the first
    # viewport with NO captured element rect. A big desert next to a flat slide is
    # the signature of unrendered/filtered content (opacity:0 reveal animations).
    sig["above_fold_element_desert_px"] = _element_desert(baton)
    return sig


def _void_row_fraction(img_path: Path) -> float | None:
    try:
        im = Image.open(img_path).convert("L")
    except Exception:  # noqa: BLE001
        return None
    w, h = im.size
    data = im.tobytes()  # mode 'L' -> 1 byte/pixel, length w*h; version-robust, no numpy
    void = 0
    for r in range(h):
        row = data[r * w:(r + 1) * w]
        row_sorted = sorted(row)
        med = row_sorted[len(row_sorted) // 2]
        near = sum(1 for v in row if abs(v - med) <= VOID_TOL)
        if near >= VOID_ROW_FRAC * w:
            void += 1
    return round(void / h, 3) if h else None


def _element_desert(baton: dict | None) -> int:
    if not isinstance(baton, dict):
        return 0
    vp = baton.get("viewport") or {}
    fold = int(vp.get("height") or 900)
    ys: list[tuple[float, float]] = []
    for e in baton.get("elements") or []:
        r = e.get("rect") or {}
        try:
            y = float(r.get("y", 0)); hgt = float(r.get("height", 0))
        except (TypeError, ValueError):
            continue
        if y < fold:
            ys.append((y, y + hgt))
    if not ys:
        return fold
    ys.sort()
    covered_to = 0.0
    biggest = 0.0
    for top, bot in ys:
        if top > covered_to:
            biggest = max(biggest, top - covered_to)
        covered_to = max(covered_to, bot)
    biggest = max(biggest, fold - covered_to)
    return int(biggest)


# ---------------------------------------------------------------------------
# Stack / duplicate detection across markers
# ---------------------------------------------------------------------------

def _marker_center(m: dict) -> tuple[float | None, float | None]:
    """Resolve a marker's on-slide position percent. Box/rect markers carry
    x_pct/y_pct (top-left); point markers carry only cx_pct/cy_pct (center).
    Reading x_pct alone makes point hotspots invisible to stack/dupe detection
    and crops them to the (0,0) corner — so fall back to the center keys."""
    x = m.get("x_pct")
    if not isinstance(x, (int, float)):
        x = m.get("cx_pct")
    y = m.get("y_pct")
    if not isinstance(y, (int, float)):
        y = m.get("cy_pct")
    return (x if isinstance(x, (int, float)) else None,
            y if isinstance(y, (int, float)) else None)


def _stacks_and_dupes(markers: list[dict]) -> tuple[set[str], set[str]]:
    """Return (f_refs in a stack, f_refs that duplicate another marker's geometry)."""
    by_slide: dict[Any, list[tuple[dict, float, float]]] = {}
    for m in markers:
        # LG4: a hidden absence marker (or any genuinely coord-less marker) is
        # not rendered on the slide — it must not be counted toward stacks/dupes.
        # Point markers DO render (their position lives in cx_pct/cy_pct), so
        # _marker_center resolves them rather than dropping them as coord-less.
        if m.get("hidden") is True:
            continue
        x, y = _marker_center(m)
        if x is None or y is None:
            continue
        by_slide.setdefault(m.get("slide_id"), []).append((m, x, y))
    stacked: set[str] = set()
    duped: set[str] = set()
    for _slide, ms in by_slide.items():
        for i, (a, ax, ay) in enumerate(ms):
            close = 0
            for j, (b, bx, by) in enumerate(ms):
                if i == j:
                    continue
                dx = ax - bx
                dy = ay - by
                if abs(dx) <= 0.5 and abs(dy) <= 0.5 and a.get("f_ref") != b.get("f_ref"):
                    duped.add(a.get("f_ref"))
                if (dx * dx + dy * dy) ** 0.5 <= STACK_RADIUS_PCT:
                    close += 1
            if close >= STACK_MIN:
                stacked.add(a.get("f_ref"))
    return stacked, duped


# ---------------------------------------------------------------------------
# Per-finding attribution
# ---------------------------------------------------------------------------

STAGE_OWNER = {
    "CAPTURE_SUSPECT": "ACQUISITION",
    "PREDICATE_MISMATCH": "SPECIALIST",
    "WEAK_ANCHOR": "SPECIALIST",
    "POINT_FOR_REGION": "PLACEMENT",
    "STACKED": "PLACEMENT",
    "DUPLICATE": "PLACEMENT",
    "LOW_CONF_PLACEMENT": "PLACEMENT",
    "UNPLACED": "-",  # expected blank (manual-placement queue), not a defect
    "OK": "-",
}
TUNE_HINT = {
    "ACQUISITION": "scripts/acquire_url.py reveal/settle (scroll-trigger + lazy media); re-capture and re-check the screenshot",
    "SPECIALIST": "contracts/specialist-prompt-v2.md anchor rules (cite the element the claim is actually about; predicates like 'over $X' must anchor to an element that satisfies them, or to the section)",
    "PLACEMENT": "scripts/report/v2_markers.py + scripts/assembly/review_state.py (region findings -> box over the section; de-stack absence/head-meta; drop the -ai duplicate from the render set)",
}


def _predicate_mismatch(text: str, anchor_text: str) -> str | None:
    if not anchor_text:
        return None
    over_tokens = list(_OVER.finditer(text))
    under_tokens = list(_UNDER.finditer(text))
    if not (over_tokens or under_tokens):
        return None
    priced = [
        (m.start(), v) for m in _PRICE.finditer(text) if (v := _money(m.group(1))) == v
    ]
    anchor_prices = [p for p in (_money(m) for m in _PRICE.findall(anchor_text)) if p == p]
    if not priced or not anchor_prices:
        return None
    # Bind the threshold to the $ NEAREST the predicate token (not max() over all
    # amounts — a competitor/MSRP price elsewhere in the prose otherwise hijacks
    # it), and treat "over $X" as satisfied by ANY price over X (compare the
    # element's highest; lowest for "under"). Kept in lockstep with
    # business_rules._check_predicate_mismatch (adversarial review 2026-07-08 #3).
    is_over = bool(over_tokens)
    tok_pos = (over_tokens or under_tokens)[0].start()
    t = min(priced, key=lambda pv: abs(pv[0] - tok_pos))[1]
    p = max(anchor_prices) if is_over else min(anchor_prices)
    if is_over and p < t:
        return f"finding says OVER ${t:,.0f} but anchored to a ${p:,.2f} element"
    if not is_over and p > t:
        return f"finding says UNDER ${t:,.0f} but anchored to a ${p:,.2f} element"
    return None


def attribute(finding: dict, marker: dict | None, anchor_el: dict | None,
              capture_suspect: bool, stacked: bool, duped: bool) -> tuple[str, str]:
    title = " ".join(str(finding.get(k) or "") for k in
                     ("finding_title", "observation", "finding_body"))
    ve_type, ve_conf = _ve_type_conf(marker or {})
    source = (marker or {}).get("source", "")
    shape = (marker or {}).get("shape", "")
    anchor_text = (anchor_el or {}).get("text_content") or (anchor_el or {}).get("accessible_name") or ""

    # 1. Capture-suspect: the finding is about an empty/region above-fold AND the
    #    above-fold actually captured flat/void -> the premise is likely a capture
    #    artifact (the awdmods black-hero cascade).
    if capture_suspect and _BLANK_WORDS.search(title) and _REGION_WORDS.search(title):
        return "CAPTURE_SUSPECT", "claims empty/blank region while the above-fold captured flat/void"

    # 2. Predicate mismatch: the specialist anchored to an element that contradicts
    #    the finding's own numeric predicate.
    pm = _predicate_mismatch(title, anchor_text)
    if pm:
        return "PREDICATE_MISMATCH", pm

    # LG4: a hidden / unplaced marker is blank (queued for manual placement per
    # §4.2 exact-tier-or-blank) — it is NOT rendered, so the placement-stage
    # defects below (point-for-region, stacked, dupe, low-confidence) do not
    # apply. The content checks above (capture-suspect premise, predicate
    # mismatch) still run because they're about the finding, not its placement.
    if marker is not None and marker.get("hidden") is True:
        return "UNPLACED", "blank, queued for manual placement (absence/unplaced, §4.2)"

    # 3. Weak/absent anchor: no concrete on-page element backs the marker.
    if ve_type in ("generated_expected_zone", "generated_expected") or "proposed_anchor" in str(source):
        if _REGION_WORDS.search(title) and shape == "point":
            return "POINT_FOR_REGION", "region/banner finding rendered as a single point, not a box over the area"
        return "WEAK_ANCHOR", f"no concrete element anchor (source={source or 'n/a'}, ve={ve_type or 'n/a'})"

    # 4. Region finding rendered as a point.
    if shape == "point" and _REGION_WORDS.search(title):
        return "POINT_FOR_REGION", "region/banner finding rendered as a single point, not a box over the area"

    # 5. Stacks / duplicates / low-confidence placement.
    if stacked:
        return "STACKED", f"{STACK_MIN}+ markers within {STACK_RADIUS_PCT:.0f}% on this slide (overlapping circles)"
    if duped:
        return "DUPLICATE", "another marker shares this exact position"
    if ve_conf == "low" or ve_type == "proxy_element":
        return "LOW_CONF_PLACEMENT", f"placed via {ve_type or 'proxy'} (low confidence) - confirm the crop"

    return "OK", f"exact element anchor (e{(marker or {}).get('snapped_baton_index')}, {ve_type or 'element'}/{ve_conf or '-'})"


# ---------------------------------------------------------------------------
# Cropping
# ---------------------------------------------------------------------------

def crop_marker(eng: Path, slide: dict, marker: dict, out_path: Path, label: str) -> bool:
    if not _HAVE_PIL:
        return False
    src = eng / str(slide.get("source") or "")
    if not src.exists():
        return False
    try:
        im = Image.open(src).convert("RGB")
    except Exception:  # noqa: BLE001
        return False
    W, H = im.size
    cx, cy = _marker_center(marker)
    x = (cx if cx is not None else 0.0) / 100.0 * W
    y = (cy if cy is not None else 0.0) / 100.0 * H
    w = (marker.get("w_pct", 0) or 0) / 100.0 * W
    h = (marker.get("h_pct", 0) or 0) / 100.0 * H
    if w < 6 or h < 6:  # point marker -> synthesize a visible box
        w = h = max(w, h, 48)
        x -= w / 2; y -= h / 2
    pad_x = max(W * 0.10, 80); pad_y = max(H * 0.10, 80)
    box = (max(0, int(x - pad_x)), max(0, int(y - pad_y)),
           min(W, int(x + w + pad_x)), min(H, int(y + h + pad_y)))
    crop = im.crop(box)
    d = ImageDraw.Draw(crop)
    mx0, my0 = int(x - box[0]), int(y - box[1])
    color = (250, 204, 21)
    if (marker.get("shape") or "") == "point":
        rr = int(max(w, h) / 2)
        cx, cy = mx0 + rr, my0 + rr
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=color, width=4)
    else:
        d.rectangle([mx0, my0, mx0 + int(w), my0 + int(h)], outline=color, width=4)
    d.text((4, 4), label, fill=color)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    crop.save(out_path)
    return True


# ---------------------------------------------------------------------------
# Per-device run
# ---------------------------------------------------------------------------

def diagnose_device(eng: Path, device: str, make_crops: bool) -> dict | None:
    rs = _load(eng / f"review-state-{device}.json")
    if not isinstance(rs, dict):
        return None
    baton = _load(eng / ("baton.json" if device in ("desktop", "laptop")
                         else f"baton-{device}.json"))
    dom = ""
    dom_path = eng / ("dom.html" if device in ("desktop", "laptop") else f"dom-{device}.html")
    if dom_path.exists():
        dom = dom_path.read_text(encoding="utf-8", errors="ignore")

    slides = rs.get("slides") or []
    slide_by_id = {s.get("slide_id"): s for s in slides}
    markers = rs.get("markers") or []
    # Render set = markers a finding actually points to (drop the -ai suggestion copies).
    finding_marker_ids = {f.get("marker_id") for f in rs.get("findings") or []}
    render_markers = [m for m in markers if m.get("marker_id") in finding_marker_ids]
    marker_by_id = {m.get("marker_id"): m for m in markers}
    els = _elements_by_index(baton)

    cap = capture_signals(dom, baton, slides, eng)
    stacked, duped = _stacks_and_dupes(render_markers)

    rows = []
    counts: dict[str, int] = {}
    for f in rs.get("findings") or []:
        f_ref = f.get("f_ref") or ""
        marker = marker_by_id.get(f.get("marker_id"))
        anchor_idx = _anchor_index(marker) if marker else None
        anchor_el = els.get(anchor_idx) if anchor_idx else None
        label, reason = attribute(
            f, marker, anchor_el, cap["capture_suspect"],
            f_ref in stacked, f_ref in duped)
        counts[label] = counts.get(label, 0) + 1
        crop_rel = None
        if make_crops and marker and marker.get("slide_id") in slide_by_id:
            crop_rel = f"crops/{device}-{f_ref.replace(' ', '_')}.png"
            crop_marker(eng, slide_by_id[marker["slide_id"]], marker,
                        eng / "_diagnosis" / crop_rel, f"{f_ref} [{label}]")
        rows.append({
            "f_ref": f_ref, "cluster": f.get("cluster"), "severity": f.get("severity"),
            "title": f.get("finding_title"),
            "shape": (marker or {}).get("shape"), "source": (marker or {}).get("source"),
            "ve_type": _ve_type_conf(marker or {})[0], "ve_conf": _ve_type_conf(marker or {})[1],
            "anchor": anchor_idx,
            "anchor_text": ((anchor_el or {}).get("text_content")
                            or (anchor_el or {}).get("accessible_name") or "")[:60],
            "attribution": label, "owner": STAGE_OWNER.get(label, "-"),
            "reason": reason, "crop": crop_rel,
        })

    return {"device": device, "capture": cap, "counts": counts,
            "stacked": sorted(stacked), "duped": sorted(duped),
            "marker_total": len(markers), "render_marker_total": len(render_markers),
            "findings": rows}


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------

def _verdict(dev: dict) -> tuple[str, list[str]]:
    reasons = []
    cap = dev["capture"]
    if cap["capture_suspect"]:
        reasons.append(
            f"above-fold captured flat/void ({cap['above_fold_void_frac']:.0%} void rows) "
            f"with {cap['dom_scroll_trigger']} scroll-trigger / {cap['dom_lazy_img']} lazy / "
            f"{cap['dom_video']} video elements in the DOM - hero likely UNRENDERED")
    n = sum(dev["counts"].values()) or 1
    # UNPLACED is an expected blank (manual-placement queue per §4.2), not a
    # defect — exclude it from the bad-finding ratio like OK.
    bad = n - dev["counts"].get("OK", 0) - dev["counts"].get("UNPLACED", 0)
    if cap["above_fold_element_desert_px"] >= 220:
        reasons.append(
            f"{cap['above_fold_element_desert_px']}px above-fold element desert "
            "(a big region with no captured elements)")
    if bad / n >= 0.5:
        reasons.append(f"{bad}/{n} findings have a stage-attributed defect")
    verdict = "DO NOT SHIP - re-capture / review" if reasons else "OK to review (no blocking signal)"
    return verdict, reasons


def render_report(eng_id: str, dev: dict) -> str:
    device = dev["device"]; cap = dev["capture"]
    verdict, reasons = _verdict(dev)
    L = [f"# Engagement diagnosis - {eng_id} ({device})", ""]
    L += [f"**Verdict: {verdict}**", ""]
    for r in reasons:
        L.append(f"- {r}")
    L.append("")
    L.append("## Stage attribution (who is accountable)")
    L.append("")
    L.append("| count | attribution | owning stage | tune |")
    L.append("|---|---|---|---|")
    for label, c in sorted(dev["counts"].items(), key=lambda kv: -kv[1]):
        owner = STAGE_OWNER.get(label, "-")
        L.append(f"| {c} | {label} | {owner} | {TUNE_HINT.get(owner, '-') if owner != '-' else 'no action'} |")
    L.append("")
    L.append("## Acquisition / capture signals")
    L.append("")
    L.append(f"- DOM render-risk: scroll-trigger={cap['dom_scroll_trigger']} "
             f"animate--={cap['dom_animate']} lazy-img={cap['dom_lazy_img']} video={cap['dom_video']}")
    L.append(f"- Above-fold void-row fraction: "
             f"{cap['above_fold_void_frac'] if cap['above_fold_void_frac'] is not None else 'n/a (no PIL)'}"
             f"  (>= {ABOVE_FOLD_VOID_FLAG:.0%} + render-risk => capture-suspect={cap['capture_suspect']})")
    L.append(f"- Above-fold element desert: {cap['above_fold_element_desert_px']}px "
             "(largest no-element vertical gap in the first viewport)")
    L.append("")
    L.append("## Per-finding accountability  (LOOK AT THE CROP for each non-OK row)")
    L.append("")
    L.append("| f_ref | sev | shape/source | anchor (element text) | attribution | reason | crop |")
    L.append("|---|---|---|---|---|---|---|")
    for r in sorted(dev["findings"], key=lambda x: (x["attribution"] == "OK", x["f_ref"])):
        anchor = f"{r['anchor'] or '-'} ({r['anchor_text']})" if r["anchor_text"] else (r["anchor"] or "-")
        L.append(f"| {r['f_ref']} | {r['severity'] or ''} | {r['shape'] or '-'}/{r['source'] or '-'} | "
                 f"{anchor} | **{r['attribution']}** | {r['reason']} | {r['crop'] or '-'} |")
    L.append("")
    L.append("## How to use this")
    L.append("")
    L.append("1. Read the **Verdict**. If DO NOT SHIP, the above-fold likely didn't render - "
             "re-capture before trusting any above-fold finding.")
    L.append("2. Open the crops in `_diagnosis/crops/` for every non-OK row and confirm with your eyes "
             "(this is the visual assessment the pipeline can't do deterministically).")
    L.append("3. Group the defects by **owning stage** and tune that stage only:")
    for owner, hint in TUNE_HINT.items():
        L.append(f"   - **{owner}** -> {hint}")
    L.append("4. Re-run the audit, re-run this tool, and confirm the defect counts drop. "
             "That loop is the accountability - a stage is 'fixed' when its attributed count goes to ~0.")
    L.append("")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="ECP engagement stage-attribution diagnostic")
    ap.add_argument("--engagement", required=True, help="Path to docs/ecp/<id>")
    ap.add_argument("--device", default="both", choices=["desktop", "laptop", "mobile", "both"])
    ap.add_argument("--no-crops", action="store_true", help="Skip screenshot crops (faster)")
    args = ap.parse_args(argv)

    eng = Path(args.engagement)
    if not eng.is_dir():
        print(f"ERROR: not a directory: {eng}", file=sys.stderr)
        return 2
    devices = (["desktop", "mobile"] if args.device == "both" else [args.device])

    out_dir = eng / "_diagnosis"
    out_dir.mkdir(exist_ok=True)
    results = []
    for device in devices:
        dev = diagnose_device(eng, device, make_crops=not args.no_crops)
        if dev is None:
            continue
        results.append(dev)
        (out_dir / f"report-{device}.md").write_text(
            render_report(eng.name, dev), encoding="utf-8")
        verdict, _ = _verdict(dev)
        print(f"[{device}] {verdict} - "
              f"{ {k: v for k, v in sorted(dev['counts'].items())} }")
    if not results:
        print("No review-state-{device}.json found. Is this a v2 engagement with a render?",
              file=sys.stderr)
        return 1
    (out_dir / "diagnosis.json").write_text(
        json.dumps({"engagement": eng.name, "devices": results}, indent=2), encoding="utf-8")
    if not _HAVE_PIL:
        print("NOTE: pillow not installed - crops were skipped. `pip install pillow` for visual crops.",
              file=sys.stderr)
    print(f"\nWrote {out_dir}/report-*.md, diagnosis.json"
          + ("" if args.no_crops or not _HAVE_PIL else ", crops/*.png"))
    print("=> Open the report and LOOK AT THE CROPS for every non-OK row.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
