"""Re-pair r01 vs r03 findings by content-based stable key.

If the canonical_id stability problem is real, switching from order-based
(F-01, F-02 by emission order) to content-based (cluster + surface +
baton_index + verdict) should produce clean pairs across runs.

Output:
- Number of pairs found (vs the 47 the order-based gate found)
- Number of orphans on each side
- 5 sample paired findings showing prose side-by-side from r01 and r03
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def load_run_findings(run_dir: Path) -> list[dict]:
    """Return all findings (specialist + ethics) from a run dir."""
    findings = []
    for path in sorted(run_dir.glob("cluster-*.json")):
        if "cluster-context-" in path.name:
            continue
        d = json.loads(path.read_text(encoding="utf-8"))
        for f in d.get("findings", []):
            findings.append(f)
    eth_path = run_dir / "ethics-findings.json"
    if eth_path.exists():
        e = json.loads(eth_path.read_text(encoding="utf-8"))
        for f in e.get("findings", []):
            findings.append(f)
    return findings


def content_key(f: dict) -> tuple[str, str, str, str]:
    """Stable content-based key. cluster + surface + baton_index + verdict."""
    cluster = f.get("cluster", "?")
    surface = f.get("surface", "?")
    baton = (f.get("element") or {}).get("baton_index", "absent")
    verdict = f.get("verdict", "?")
    return (cluster, surface, baton, verdict)


def main() -> None:
    out_lines = []

    def p(s: str = "") -> None:
        out_lines.append(s)

    r01 = load_run_findings(REPO / "docs" / "ecp" / "2026-04-29-ee4d6cc6")
    r03 = load_run_findings(REPO / "docs" / "ecp" / "2026-04-29-bd952a50")
    p(f"r01: {len(r01)} findings")
    p(f"r03: {len(r03)} findings")

    r01_by_key: dict = defaultdict(list)
    for f in r01:
        r01_by_key[content_key(f)].append(f)
    r03_by_key: dict = defaultdict(list)
    for f in r03:
        r03_by_key[content_key(f)].append(f)

    paired_keys = set(r01_by_key) & set(r03_by_key)
    only_r01 = set(r01_by_key) - paired_keys
    only_r03 = set(r03_by_key) - paired_keys
    p(f"\n=== Content-based pairing ===")
    p(f"Pairs (same content-key in both runs): {len(paired_keys)}")
    p(f"Only in r01: {len(only_r01)}")
    p(f"Only in r03: {len(only_r03)}")
    p(f"Compare to order-based: 47 paired, with most pairs comparing different findings")

    # Pull spread of clusters for sample
    samples = []
    seen_clusters = set()
    for k in sorted(paired_keys):
        cluster = k[0]
        if cluster not in seen_clusters and cluster != "ethics":
            samples.append(k)
            seen_clusters.add(cluster)
        if len(samples) >= 5:
            break

    p()
    for key in samples:
        r01_f = r01_by_key[key][0]
        r03_f = r03_by_key[key][0]
        p("=" * 100)
        p(f"content key: cluster={key[0]} surface={key[1]} baton={key[2]} verdict={key[3]}")
        p("=" * 100)
        p(f"\n--- r01 (specialist's local_id={r01_f.get('local_id')}) ---")
        p(f"TITLE:          {r01_f.get('title')}")
        p(f"OBSERVATION:    {(r01_f.get('observation') or '')[:600]}")
        p(f"RECOMMENDATION: {(r01_f.get('recommendation') or '')[:600]}")
        p(f"\n--- r03 (specialist's local_id={r03_f.get('local_id')}) ---")
        p(f"TITLE:          {r03_f.get('title')}")
        p(f"OBSERVATION:    {(r03_f.get('observation') or '')[:600]}")
        p(f"RECOMMENDATION: {(r03_f.get('recommendation') or '')[:600]}")
        p()

    # Distribution of orphans by cluster
    p("=" * 100)
    p("Orphan distribution (findings unique to one run)")
    p("=" * 100)
    orphan_clusters_r01: dict = defaultdict(int)
    orphan_clusters_r03: dict = defaultdict(int)
    for k in only_r01:
        orphan_clusters_r01[k[0]] += 1
    for k in only_r03:
        orphan_clusters_r03[k[0]] += 1
    all_clusters = sorted(set(orphan_clusters_r01) | set(orphan_clusters_r03))
    p(f"{'cluster':<24} {'only-r01':<10} {'only-r03':<10}")
    p("-" * 44)
    for c in all_clusters:
        p(f"{c:<24} {orphan_clusters_r01.get(c, 0):<10} {orphan_clusters_r03.get(c, 0):<10}")

    out_path = REPO / "docs" / "plans" / "2026-04-29-content-pairing-output.txt"
    out_path.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"Wrote {len(out_lines)} lines to {out_path}")


if __name__ == "__main__":
    main()
