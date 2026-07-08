"""Placement repair for hotspots the visual gate flagged as misplaced.

Strategy (per operator decision 2026-06-03):
  1. AUTO RE-ANCHOR when a confident, unambiguous baton element matches the
     finding's subject text — reusing review_state._build_snap_targets so the
     new coordinates come from the real element bbox, never a fresh guess.
  2. Otherwise FLAG for manual placement (downgrade confidence).
  3. ALWAYS write a diagnostic log entry explaining what happened and WHY it
     could/couldn't re-anchor — to gather data on the failure modes (most are
     expected to be acquirer element-capture gaps per the 2026-06-02 diagnosis).

Non-destructive: writes review-state-{device}.repaired.json (not the original)
plus placement-repair-log.json. The operator/editor adopts the repaired file.

Usage:
    python scripts/report/placement_repair.py --engagement <dir> --device desktop \
        --misplaced "pricing F-65,visual-cta F-08" --plugin-root .
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cli_io import force_utf8_io  # noqa: E402

_TOKEN = re.compile(r"[a-z0-9]+")
_STOP = frozenset({"the", "a", "an", "of", "for", "to", "in", "on", "and", "or",
                   "your", "with", "is", "are", "this", "that", "low", "no", "not"})
# oversized = likely parent container; threshold from its one home in
# assembly/visual_quality.py (a dependency-light import keeps this tool standalone).
from assembly.visual_quality import (  # noqa: E402
    DEFAULT_GIANT_HEIGHT_PCT as GIANT_H,
    DEFAULT_GIANT_WIDTH_PCT as GIANT_W,
    is_giant_exact_rect,
)

MATCH_MIN = 0.34                         # min token-overlap to trust a re-anchor
MATCH_MARGIN = 0.12                      # top match must beat 2nd by this to be unambiguous


def _tokens(s: str) -> set[str]:
    return {t for t in _TOKEN.findall((s or "").lower()) if t not in _STOP and len(t) > 1}


def _overlap(label: str, query_tokens: set[str]) -> float:
    lt = _tokens(label)
    if not lt or not query_tokens:
        return 0.0
    return len(lt & query_tokens) / len(lt | query_tokens)


def _query_tokens(finding: dict, marker: dict) -> set[str]:
    """Build the bag of words describing the element this hotspot should hit."""
    parts: list[str] = []
    ve = marker.get("visual_evidence") if isinstance(marker.get("visual_evidence"), dict) else {}
    oa = ve.get("observed_anchor") if isinstance(ve.get("observed_anchor"), dict) else {}
    for v in (oa.get("text_quote"), oa.get("selector_hint")):
        if v:
            parts.append(str(v))
    # Prefer operator-corrected text, mirroring _display_title (review_state.py) /
    # displayTitle (editor.js) — a corrected title is the real subject.
    for base in ("finding_title", "callout_title"):
        val = finding.get(f"{base}_override") or finding.get(base)
        if val:
            parts.append(str(val))
    if finding.get("element"):
        parts.append(str(finding["element"]))
    return _tokens(" ".join(parts))


def _is_oversized(t: dict) -> bool:
    """A snap target too large to be a precise subject (likely a parent container).

    The "giant container" test uses the canonical ``is_giant_exact_rect`` (wide
    AND tall), aligned with the rest of the codebase (product.md §10, 2026-07-08;
    operator ruling on review findings #8/#10). Under the old wide-OR-tall rule a
    full-width but SHORT strip (CTA bar, nav strip, price row) tripped the width
    arm alone and was wrongly dropped from the re-anchor candidate pool even
    though it is a precise anchor.

    The offset full-bleed-band screen is KEPT (spec-preserved: this function
    screens re-anchor *targets*, a different purpose): review_state clamps
    ``w_pct`` to ``100 - x_pct``, so a wide element offset past ~15% never trips
    the width arm — catch a true edge-to-edge band via right-edge + width.
    """
    w, h, x = t.get("w_pct", 0), t.get("h_pct", 0), t.get("x_pct", 0)
    if is_giant_exact_rect(w, h, max_width_pct=GIANT_W, max_height_pct=GIANT_H):
        return True
    return (x + w) >= 99 and w >= 60


def _flatten_targets(snap: dict) -> list[dict]:
    out = []
    for slide_id, lst in (snap or {}).items():
        for t in lst:
            out.append({**t, "slide_id": slide_id})
    return out


def decide_match(query_tokens: set[str], targets: list[dict], current_slide: str | None = None) -> dict:
    """Decide whether to re-anchor (confident, unambiguous text match) or flag,
    and explain why. Pure function — the testable core of the repair.

    A re-anchor is marked UNVERIFIED: it trusts the finding's anchor text, so a
    lexical match can still land on the wrong element (e.g. a finding anchored to
    the title but semantically about the description). The workflow must re-verify
    a re-anchor with vision before trusting it.

    When ``current_slide`` is given, only same-slide elements are eligible for a
    re-anchor — an auto-repair never silently relocates a finding across sections.
    A strong off-slide match is surfaced in the flag reason for a manual move.
    """
    off_best = None
    pool = targets
    if current_slide is not None:
        pool = [t for t in targets if t.get("slide_id") == current_slide]
        off = sorted(((_overlap(t["label"], query_tokens), t)
                      for t in targets if t.get("slide_id") != current_slide),
                     key=lambda st: st[0], reverse=True)
        off_best = off[0] if off else None

    scored = sorted(((_overlap(t["label"], query_tokens), t) for t in pool),
                    key=lambda st: st[0], reverse=True)
    best_score, best = (scored[0] if scored else (0.0, None))
    second_score = scored[1][0] if len(scored) > 1 else 0.0

    if best and best_score >= MATCH_MIN and (best_score - second_score) >= MATCH_MARGIN:
        return {"action": "re-anchor", "best": best, "score": best_score, "scored": scored,
                "reason": (f"confident text match to baton element '{best['label']}' "
                           f"(score {best_score:.2f}) — UNVERIFIED, re-verify with vision before trusting")}

    if not query_tokens:
        reason = "finding carries no anchorable element text (image/abstract finding) — manual placement"
    elif not pool:
        reason = "no captured elements available to anchor to (empty candidate set) — acquirer captured nothing usable"
    elif best_score == 0.0:
        reason = ("no baton element shares any subject text — intended element likely NOT captured "
                  "by the acquirer (element-capture gap)")
    elif best_score < MATCH_MIN:
        reason = (f"best candidate '{best['label']}' too weak (score {best_score:.2f} < {MATCH_MIN}) — "
                  "no confident subject element among captured elements")
    else:
        reason = (f"ambiguous: '{best['label']}' ({best_score:.2f}) vs '{scored[1][1]['label']}' "
                  f"({second_score:.2f}) within {MATCH_MARGIN} — needs human disambiguation")
    if off_best and off_best[0] >= MATCH_MIN:
        reason += (f"; a strong match exists on a different slide "
                   f"'{off_best[1].get('slide_id')}' ('{off_best[1]['label']}') — manual cross-section move")
    return {"action": "flag", "best": best, "score": best_score, "scored": scored, "reason": reason}


def repair(engagement: Path, device: str, misplaced: list[str], plugin_root: Path) -> dict:
    from assembly.review_state import _build_snap_targets

    rs_path = engagement / f"review-state-{device}.json"
    rs = json.loads(rs_path.read_text(encoding="utf-8"))
    if not isinstance(rs, dict):
        raise ValueError(f"{rs_path} root is not a JSON object")
    findings = {f["f_ref"]: f for f in rs.get("findings") or [] if isinstance(f, dict) and f.get("f_ref")}
    markers = {m["f_ref"]: m for m in rs.get("markers") or [] if isinstance(m, dict) and m.get("f_ref")}

    targets = [t for t in _flatten_targets(_build_snap_targets(engagement, plugin_root, device))
               if not _is_oversized(t)]

    log: list[dict] = []
    re_anchored = flagged = 0

    seen: set[str] = set()
    for fref in misplaced:
        if fref in seen:  # dedup: a repeated f_ref must not be double-processed
            continue
        seen.add(fref)
        marker = markers.get(fref)
        if marker is None:
            log.append({"f_ref": fref, "action": "skipped", "reason": "no marker in review-state"})
            continue
        finding = findings.get(fref)  # the dict inside rs (mutations persist), or None

        qtok = _query_tokens(finding or {}, marker)
        decision = decide_match(qtok, targets, marker.get("slide_id"))
        if decision["action"] == "re-anchor":
            best = decision["best"]
            old = {"slide_id": marker.get("slide_id"), "source": marker.get("source"),
                   "snapped_baton_index": marker.get("snapped_baton_index"),
                   "box": {k: marker.get(k) for k in ("x_pct", "y_pct", "w_pct", "h_pct")}}
            marker.update({"slide_id": best["slide_id"], "x_pct": best["x_pct"], "y_pct": best["y_pct"],
                           "w_pct": best["w_pct"], "h_pct": best["h_pct"],
                           "shape": "rect",  # a re-anchor produces a BOX. The editor renders any
                                             # non-rect/ellipse/poly shape (incl. 'point') from
                                             # cx_pct/cy_pct (default 50,50), so a stale shape='point'
                                             # would ignore the new box and keep the old/center spot.
                           "snapped_baton_index": best.get("e_index"),
                           "source": "e_index_lookup",  # valid schema enum; it is now e_index-anchored
                           "repair_status": "re_anchored_unverified"})
            # Drop stale center/ellipse/polygon geometry so no renderer falls back
            # to the pre-repair coords (mirrors the editor's convert-to-rect at
            # tools/editor/editor.js:1478).
            for _stale in ("cx_pct", "cy_pct", "rx_pct", "ry_pct", "points"):
                marker.pop(_stale, None)
            # Fail safe: an UNVERIFIED re-anchor must read "Check placement", never "Likely OK".
            # The workflow re-verify upgrades (confirmed) or downgrades (reverted) this finding.
            if finding is not None:
                finding["hotspot_confidence"] = "section-match"
            re_anchored += 1
            log.append({"f_ref": fref, "action": "re-anchored", "from": old,
                        "to": {"e_index": best.get("e_index"), "slide_id": best["slide_id"],
                               "label": best["label"], "score": round(decision["score"], 2)},
                        "reason": decision["reason"]})
        else:
            # Queue into the editor's "Place manually" worklist. The editor reads
            # FINDING-level hotspot_confidence (enum review-state-v1.json:121-123);
            # marker-level flags are inert downstream.
            if finding is not None:
                finding["hotspot_confidence"] = "needs-manual-marker"
            marker["placement_review_needed"] = True  # provenance only (schema allows; editor ignores)
            flagged += 1
            log.append({"f_ref": fref, "action": "flagged", "reason": decision["reason"],
                        "query_tokens": sorted(qtok),
                        "top_candidates": [{"label": t["label"], "score": round(s, 2)}
                                           for s, t in decision["scored"][:3]]})

    repaired_path = engagement / f"review-state-{device}.repaired.json"
    repaired_path.write_text(json.dumps(rs, indent=2), encoding="utf-8")
    log_path = engagement / "placement-repair-log.json"
    log_path.write_text(json.dumps({"engagement": engagement.name, "device": device,
                                    "re_anchored": re_anchored, "flagged": flagged, "log": log},
                                   indent=2), encoding="utf-8")
    return {"re_anchored": re_anchored, "flagged": flagged, "log": log,
            "repaired_path": str(repaired_path), "log_path": str(log_path)}


def finalize(engagement: Path, device: str, confirmed: list[str], reverted: list[str]) -> dict:
    """Apply vision re-verify verdicts to the repaired review-state.

    A re-anchor lands as the fail-safe "section-match" (check placement). After the
    workflow re-verifies it, this persists the outcome: vision-confirmed re-anchors
    become confident ("exact-selector"); vision-rejected OR never-verified ones
    queue manual placement ("needs-manual-marker") — so a re-anchor is never adopted
    confidently by omission.
    """
    rs_path = engagement / f"review-state-{device}.repaired.json"
    rs = json.loads(rs_path.read_text(encoding="utf-8"))
    if not isinstance(rs, dict):
        raise ValueError(f"{rs_path} root is not a JSON object")
    findings = {f["f_ref"]: f for f in rs.get("findings") or [] if isinstance(f, dict) and f.get("f_ref")}
    up = down = 0
    for fr in confirmed:
        f = findings.get(fr)
        if f is not None:
            f["hotspot_confidence"] = "exact-selector"
            up += 1
    for fr in reverted:
        f = findings.get(fr)
        if f is not None:
            f["hotspot_confidence"] = "needs-manual-marker"
            down += 1
    rs_path.write_text(json.dumps(rs, indent=2), encoding="utf-8")
    return {"confirmed": up, "reverted": down, "repaired_path": str(rs_path)}


def _csv(s: str | None) -> list[str]:
    return [x.strip() for x in (s or "").split(",") if x.strip()]


def main(argv: list[str] | None = None) -> int:
    force_utf8_io()
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("repair", help="re-anchor / flag misplaced findings")
    r.add_argument("--engagement", required=True, type=Path)
    r.add_argument("--device", default="desktop", choices=["desktop", "mobile"])
    r.add_argument("--misplaced", required=True, help="comma-separated f_refs flagged misplaced by the visual gate")
    r.add_argument("--plugin-root", type=Path, default=_SCRIPTS.parent)

    fz = sub.add_parser("finalize", help="apply vision re-verify verdicts to the repaired file")
    fz.add_argument("--engagement", required=True, type=Path)
    fz.add_argument("--device", default="desktop", choices=["desktop", "mobile"])
    fz.add_argument("--confirmed", default="", help="comma-separated f_refs vision confirmed on-target")
    fz.add_argument("--reverted", default="", help="comma-separated f_refs vision rejected or left unverified")

    args = p.parse_args(argv)
    if args.cmd == "repair":
        res = repair(args.engagement, args.device, _csv(args.misplaced), args.plugin_root)
        print(f"Repair: {res['re_anchored']} re-anchored, {res['flagged']} flagged for manual\n")
        for e in res["log"]:
            print(f"  [{e['action']}] {e['f_ref']}: {e.get('reason', '')}")
        print(f"\nWrote {res['repaired_path']}\nWrote {res['log_path']}")
        return 0
    if args.cmd == "finalize":
        res = finalize(args.engagement, args.device, _csv(args.confirmed), _csv(args.reverted))
        print(f"Finalize: {res['confirmed']} confirmed -> exact-selector, "
              f"{res['reverted']} reverted -> needs-manual-marker\nWrote {res['repaired_path']}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
