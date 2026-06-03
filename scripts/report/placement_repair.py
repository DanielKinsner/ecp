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
GIANT_W, GIANT_H = 85.0, 70.0           # oversized = likely parent container
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
    for k in ("finding_title", "callout_title", "element"):
        if finding.get(k):
            parts.append(str(finding[k]))
    return _tokens(" ".join(parts))


def _flatten_targets(snap: dict) -> list[dict]:
    out = []
    for slide_id, lst in (snap or {}).items():
        for t in lst:
            out.append({**t, "slide_id": slide_id})
    return out


def decide_match(query_tokens: set[str], targets: list[dict]) -> dict:
    """Decide whether to re-anchor (confident, unambiguous text match) or flag,
    and explain why. Pure function — the testable core of the repair.

    A re-anchor is marked UNVERIFIED: it trusts the finding's anchor text, so a
    lexical match can still land on the wrong element (e.g. a finding anchored to
    the title but semantically about the description). The workflow must re-verify
    a re-anchor with vision before trusting it.
    """
    scored = sorted(((_overlap(t["label"], query_tokens), t) for t in targets),
                    key=lambda st: st[0], reverse=True)
    best_score, best = (scored[0] if scored else (0.0, None))
    second_score = scored[1][0] if len(scored) > 1 else 0.0

    if best and best_score >= MATCH_MIN and (best_score - second_score) >= MATCH_MARGIN:
        return {"action": "re-anchor", "best": best, "score": best_score, "scored": scored,
                "reason": (f"confident text match to baton element '{best['label']}' "
                           f"(score {best_score:.2f}) — UNVERIFIED, re-verify with vision before trusting")}

    if not query_tokens:
        reason = "finding carries no anchorable element text (image/abstract finding) — manual placement"
    elif best_score == 0.0:
        reason = ("no baton element shares any subject text — intended element likely NOT captured "
                  "by the acquirer (element-capture gap)")
    elif best_score < MATCH_MIN:
        reason = (f"best candidate '{best['label']}' too weak (score {best_score:.2f} < {MATCH_MIN}) — "
                  "no confident subject element among captured elements")
    else:
        reason = (f"ambiguous: '{best['label']}' ({best_score:.2f}) vs '{scored[1][1]['label']}' "
                  f"({second_score:.2f}) within {MATCH_MARGIN} — needs human disambiguation")
    return {"action": "flag", "best": best, "score": best_score, "scored": scored, "reason": reason}


def repair(engagement: Path, device: str, misplaced: list[str], plugin_root: Path) -> dict:
    from assembly.review_state import _build_snap_targets

    rs_path = engagement / f"review-state-{device}.json"
    rs = json.loads(rs_path.read_text(encoding="utf-8"))
    findings = {f["f_ref"]: f for f in rs.get("findings") or [] if isinstance(f, dict) and f.get("f_ref")}
    markers = {m["f_ref"]: m for m in rs.get("markers") or [] if isinstance(m, dict) and m.get("f_ref")}

    targets = [t for t in _flatten_targets(_build_snap_targets(engagement, plugin_root, device))
               if not (t.get("w_pct", 0) > GIANT_W or t.get("h_pct", 0) > GIANT_H)]

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
        decision = decide_match(qtok, targets)
        if decision["action"] == "re-anchor":
            best = decision["best"]
            old = {"slide_id": marker.get("slide_id"), "source": marker.get("source"),
                   "snapped_baton_index": marker.get("snapped_baton_index"),
                   "box": {k: marker.get(k) for k in ("x_pct", "y_pct", "w_pct", "h_pct")}}
            marker.update({"slide_id": best["slide_id"], "x_pct": best["x_pct"], "y_pct": best["y_pct"],
                           "w_pct": best["w_pct"], "h_pct": best["h_pct"],
                           "snapped_baton_index": best.get("e_index"),
                           "source": "e_index_lookup",  # valid schema enum; it is now e_index-anchored
                           "repair_status": "re_anchored_unverified"})
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


def main(argv: list[str] | None = None) -> int:
    force_utf8_io()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--engagement", required=True, type=Path)
    p.add_argument("--device", default="desktop", choices=["desktop", "mobile"])
    p.add_argument("--misplaced", required=True, help="comma-separated f_refs flagged misplaced by the visual gate")
    p.add_argument("--plugin-root", type=Path, default=_SCRIPTS.parent)
    args = p.parse_args(argv)

    misplaced = [x.strip() for x in args.misplaced.split(",") if x.strip()]
    res = repair(args.engagement, args.device, misplaced, args.plugin_root)
    print(f"Repair: {res['re_anchored']} re-anchored, {res['flagged']} flagged for manual\n")
    for e in res["log"]:
        print(f"  [{e['action']}] {e['f_ref']}: {e.get('reason', '')}")
    print(f"\nWrote {res['repaired_path']}\nWrote {res['log_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
