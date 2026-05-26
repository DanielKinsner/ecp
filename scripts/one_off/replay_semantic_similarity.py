"""Compute semantic (embedding-based) similarity across the 3 synth replays.

Uses the same all-MiniLM-L6-v2 model the gate's finding_stability uses, so
the numbers are directly comparable to TARa thresholds (cosine >= 0.85).
"""
from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from assembly.finding_stability import prose_cosine_similarity

REPLAYS = {
    "A": REPO / "docs" / "ecp" / "2026-04-29-aaaaaaa1" / "synthesizer-emission-v1.json",
    "B": REPO / "docs" / "ecp" / "2026-04-29-aaaaaaa2" / "synthesizer-emission-v1.json",
    "C": REPO / "docs" / "ecp" / "2026-04-29-aaaaaaa3" / "synthesizer-emission-v1.json",
}


def index_humanized(path: Path) -> dict[str, dict]:
    d = json.loads(path.read_text(encoding="utf-8"))
    return {f["f_ref"]: f for f in d.get("humanized_findings", [])}


def main() -> None:
    indexed = {k: index_humanized(v) for k, v in REPLAYS.items()}
    refs_in_all = sorted(set(indexed["A"]) & set(indexed["B"]) & set(indexed["C"]))
    print(f"f_refs in all 3 replays: {len(refs_in_all)}")
    print()

    out_lines: list[str] = []

    def p(s: str = "") -> None:
        out_lines.append(s)
        print(s)

    p("=== Semantic similarity (sentence-transformers cosine) — 3 synth replays on identical input ===")
    p()
    p("Threshold reminder: gate's TARa requires cosine >= 0.85 for OBSERVATION + RECOMMENDATION.")
    p()

    cosines: dict[tuple[str, str], list[float]] = {}
    for x, y in combinations(["A", "B", "C"], 2):
        cosines[(x, y)] = []

    for ref in refs_in_all:
        prose_per_replay = {}
        for k in ("A", "B", "C"):
            f = indexed[k][ref]
            prose_per_replay[k] = (
                (f.get("plain_english_summary") or "") + " " + (f.get("plain_english_action") or "")
            ).strip()
        for x, y in combinations(["A", "B", "C"], 2):
            try:
                cos = prose_cosine_similarity(prose_per_replay[x], prose_per_replay[y])
                cosines[(x, y)].append((ref, cos))
            except Exception as e:
                p(f"  WARN: cosine failed for {ref} {x}-{y}: {e}")

    p(f"{'pair':<8} {'avg cosine':<12} {'>=0.85':<10} {'>=0.70':<10} {'>=0.50':<10}")
    p("-" * 50)
    all_cosines: list[float] = []
    for (x, y), pairs in cosines.items():
        scores = [s for _, s in pairs]
        if not scores:
            continue
        all_cosines.extend(scores)
        avg = sum(scores) / len(scores)
        above_85 = sum(1 for s in scores if s >= 0.85)
        above_70 = sum(1 for s in scores if s >= 0.70)
        above_50 = sum(1 for s in scores if s >= 0.50)
        p(f"{x}-{y:<6} {avg:<12.4f} {above_85}/{len(scores):<8} {above_70}/{len(scores):<8} {above_50}/{len(scores):<8}")

    if all_cosines:
        avg_all = sum(all_cosines) / len(all_cosines)
        p(f"\noverall avg cosine across all pairs: {avg_all:.4f}")
        p(f"min cosine: {min(all_cosines):.4f}")
        p(f"max cosine: {max(all_cosines):.4f}")
        median = sorted(all_cosines)[len(all_cosines) // 2]
        p(f"median cosine: {median:.4f}")

    out_path = REPO / "docs" / "plans" / "2026-04-29-synth-replay-semantic.txt"
    out_path.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
