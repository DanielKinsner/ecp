"""Compare 3 synth-replay outputs against each other.

All 3 replays ran with byte-identical inputs (same r01 cluster JSONs, ethics,
batons, screenshots, canonical-f-refs). Only the synth's sampling differed.

Outputs:
- f_ref overlap across the 3 replays (which findings every replay surfaced)
- Per-paired-finding prose comparison: plain_english_summary + plain_english_action
- Identical-byte rate (extreme stability)
- Token-set Jaccard similarity (loose stability)
- Levenshtein ratio (lexical stability)
"""
from __future__ import annotations

import json
import re
from itertools import combinations
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

REPLAYS = {
    "A": REPO / "docs" / "ecp" / "2026-04-29-aaaaaaa1" / "synthesizer-emission-v1.json",
    "B": REPO / "docs" / "ecp" / "2026-04-29-aaaaaaa2" / "synthesizer-emission-v1.json",
    "C": REPO / "docs" / "ecp" / "2026-04-29-aaaaaaa3" / "synthesizer-emission-v1.json",
}


def index_humanized(path: Path) -> dict[str, dict]:
    d = json.loads(path.read_text(encoding="utf-8"))
    return {f["f_ref"]: f for f in d.get("humanized_findings", [])}


_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall((text or "").lower()))


def jaccard(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def lev_ratio(a: str, b: str) -> float:
    """Normalized Levenshtein similarity in [0, 1]."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    m, n = len(a), len(b)
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        cur = [i] + [0] * n
        for j in range(1, n + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    dist = prev[n]
    return 1.0 - dist / max(m, n)


def main() -> None:
    indexed = {k: index_humanized(v) for k, v in REPLAYS.items()}
    out_lines: list[str] = []

    def p(s: str = "") -> None:
        out_lines.append(s)

    p("=== Synth-replay comparison: 3 opus instances on byte-identical r01 inputs ===")
    for k, fmap in indexed.items():
        p(f"  replay-{k}: {len(fmap)} humanized findings")

    refs_in_all = set(indexed["A"]) & set(indexed["B"]) & set(indexed["C"])
    refs_union = set(indexed["A"]) | set(indexed["B"]) | set(indexed["C"])
    p()
    p(f"f_refs in all 3 replays: {len(refs_in_all)} / union {len(refs_union)} = {len(refs_in_all)/max(len(refs_union),1):.4f}")
    p(f"  (this is the synth-only TARr@3 — pure synth variance on identical input)")

    # Per-pair stats
    p()
    p("=== Per-pair prose stability ===")
    p(f"{'pair':<8} {'shared f_refs':<15} {'identical bytes':<18} {'jaccard>=0.7':<15} {'lev>=0.8':<10}")
    for x, y in combinations(["A", "B", "C"], 2):
        shared = set(indexed[x]) & set(indexed[y])
        if not shared:
            continue
        identical = 0
        jaccard_pass = 0
        lev_pass = 0
        for ref in shared:
            ax = indexed[x][ref]
            ay = indexed[y][ref]
            sx = (ax.get("plain_english_summary") or "") + " " + (ax.get("plain_english_action") or "")
            sy = (ay.get("plain_english_summary") or "") + " " + (ay.get("plain_english_action") or "")
            if sx == sy:
                identical += 1
            if jaccard(sx, sy) >= 0.7:
                jaccard_pass += 1
            if lev_ratio(sx, sy) >= 0.8:
                lev_pass += 1
        p(f"{x}-{y:<6} {len(shared):<15} {identical:<18} {jaccard_pass:<15} {lev_pass:<10}")

    # Aggregate across all 3 replays for f_refs in all 3
    p()
    p("=== All-3-replay agreement on f_refs present everywhere ===")
    if refs_in_all:
        all3_identical = 0
        all3_jaccard = 0
        all3_lev = 0
        for ref in refs_in_all:
            a = indexed["A"][ref]
            b = indexed["B"][ref]
            c = indexed["C"][ref]
            sa = (a.get("plain_english_summary") or "") + " " + (a.get("plain_english_action") or "")
            sb = (b.get("plain_english_summary") or "") + " " + (b.get("plain_english_action") or "")
            sc = (c.get("plain_english_summary") or "") + " " + (c.get("plain_english_action") or "")
            if sa == sb == sc:
                all3_identical += 1
            if min(jaccard(sa, sb), jaccard(sa, sc), jaccard(sb, sc)) >= 0.7:
                all3_jaccard += 1
            if min(lev_ratio(sa, sb), lev_ratio(sa, sc), lev_ratio(sb, sc)) >= 0.8:
                all3_lev += 1
        p(f"  Of {len(refs_in_all)} f_refs in all 3 replays:")
        p(f"    byte-identical prose across A/B/C:    {all3_identical}/{len(refs_in_all)} ({all3_identical/len(refs_in_all)*100:.1f}%)")
        p(f"    token-Jaccard >= 0.7 across all pairs: {all3_jaccard}/{len(refs_in_all)} ({all3_jaccard/len(refs_in_all)*100:.1f}%)")
        p(f"    Levenshtein >= 0.8 across all pairs:   {all3_lev}/{len(refs_in_all)} ({all3_lev/len(refs_in_all)*100:.1f}%)")

    # Show 3 sample paired findings to give a feel for the prose drift
    p()
    p("=== Sample paired findings (first 3 f_refs in all 3 replays) ===")
    sample = sorted(refs_in_all)[:3]
    for ref in sample:
        p()
        p("=" * 100)
        p(f"f_ref: {ref}")
        p("=" * 100)
        for k in ("A", "B", "C"):
            f = indexed[k][ref]
            p(f"\n--- replay-{k} ---")
            p(f"SUMMARY: {f.get('plain_english_summary', '')}")
            p(f"ACTION:  {f.get('plain_english_action', '')}")

    out_path = REPO / "docs" / "plans" / "2026-04-29-synth-replay-output.txt"
    out_path.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"Wrote {len(out_lines)} lines to {out_path}")


if __name__ == "__main__":
    main()
