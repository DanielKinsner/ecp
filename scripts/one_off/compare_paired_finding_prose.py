"""Pull paired finding prose from r01, r02, r03 synth emissions.

For findings that exist in all 3 runs (per canonical f_ref), show the
synthesizer's title + observation + recommendation side by side so the
operator can judge whether prose drift is creative phrasing or
substantively different claims.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

RUNS = {
    "r01": REPO / "docs" / "ecp" / "2026-04-29-ee4d6cc6" / "synthesizer-emission-v1.json",
    "r02": REPO / "docs" / "ecp" / "2026-04-29-d21e1ce2" / "synthesizer-emission-v1.json",
    "r03": REPO / "docs" / "ecp" / "2026-04-29-bd952a50" / "synthesizer-emission-v1.json",
}


def index_findings(emission_path: Path) -> dict:
    """Return {f_ref: humanized_finding_dict}."""
    d = json.loads(emission_path.read_text(encoding="utf-8"))
    out = {}
    for f in d.get("humanized_findings", []):
        ref = f.get("f_ref")
        if ref:
            out[ref] = f
    return out


def main() -> None:
    indexed = {label: index_findings(p) for label, p in RUNS.items()}
    for label, fmap in indexed.items():
        print(f"{label}: {len(fmap)} humanized findings")

    refs_in_all = sorted(set(indexed["r01"]) & set(indexed["r02"]) & set(indexed["r03"]))
    print(f"\nFindings in ALL 3 runs: {len(refs_in_all)}")
    print()

    # Sample 5 spread across the alphabet (different clusters) for variety
    sample = []
    seen_clusters = set()
    for ref in refs_in_all:
        cluster = ref.split()[0]
        if cluster not in seen_clusters:
            sample.append(ref)
            seen_clusters.add(cluster)
        if len(sample) >= 5:
            break

    for ref in sample:
        print("=" * 100)
        print(f"f_ref: {ref}")
        print("=" * 100)
        for label in ("r01", "r02", "r03"):
            f = indexed[label].get(ref, {})
            summary = f.get("plain_english_summary", "(missing)")
            action = f.get("plain_english_action", "(missing)")
            print(f"\n--- {label} ---")
            print(f"SUMMARY: {summary}")
            print(f"ACTION:  {action}")
        print()


if __name__ == "__main__":
    main()
