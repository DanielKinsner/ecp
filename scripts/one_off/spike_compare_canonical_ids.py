"""Compare old (order-based) vs new (content-based) canonical_id stability.

Reads .OLD-orderbased backup and the freshly-regenerated content-based
canonical-f-refs.json for r01/r02/r03. Reports cross-run f_ref overlap
under each scheme.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

RUNS = {
    "r01": REPO / "docs" / "ecp" / "2026-04-29-ee4d6cc6",
    "r02": REPO / "docs" / "ecp" / "2026-04-29-d21e1ce2",
    "r03": REPO / "docs" / "ecp" / "2026-04-29-bd952a50",
}


def load_refs(canonical_path: Path) -> set[str]:
    d = json.loads(canonical_path.read_text(encoding="utf-8"))
    return set(d.get("valid_refs", []))


def report(scheme_label: str, old: dict[str, set[str]]) -> None:
    union = set().union(*old.values())
    intersection = set.intersection(*old.values())
    print(f"\n=== {scheme_label} ===")
    for label in ("r01", "r02", "r03"):
        print(f"  {label}: {len(old[label])} canonical refs")
    print(f"  union (any run): {len(union)}")
    print(f"  intersection (all 3 runs): {len(intersection)}")
    if union:
        print(f"  TARr@3 = intersection/union = {len(intersection)/len(union):.4f}")
    pairs = [
        ("r01-r02", old["r01"] & old["r02"], old["r01"] | old["r02"]),
        ("r01-r03", old["r01"] & old["r03"], old["r01"] | old["r03"]),
        ("r02-r03", old["r02"] & old["r03"], old["r02"] | old["r03"]),
    ]
    for name, inter, uni in pairs:
        print(f"  {name}: {len(inter)}/{len(uni)} = {len(inter)/len(uni):.4f}")


def main() -> None:
    old_refs = {label: load_refs(d / "canonical-f-refs.json.OLD-orderbased") for label, d in RUNS.items()}
    new_refs = {label: load_refs(d / "canonical-f-refs.json") for label, d in RUNS.items()}

    report("OLD (order-based: F-NN by emission order)", old_refs)
    report("NEW (content-based: F-NN from sha256 of cluster+surface+baton+verdict+title)", new_refs)

    # Side-by-side cluster breakdown for one run to see ID changes
    print("\n=== Sample: r01 canonical refs OLD vs NEW (first 15 sorted alphabetically) ===")
    by_cluster_old = {r.split()[0]: [] for r in old_refs["r01"]}
    by_cluster_new = {r.split()[0]: [] for r in new_refs["r01"]}
    for r in sorted(old_refs["r01"]):
        c = r.split()[0]
        by_cluster_old.setdefault(c, []).append(r)
    for r in sorted(new_refs["r01"]):
        c = r.split()[0]
        by_cluster_new.setdefault(c, []).append(r)

    for cluster in sorted(set(by_cluster_old) | set(by_cluster_new)):
        old_in_cluster = sorted(by_cluster_old.get(cluster, []))
        new_in_cluster = sorted(by_cluster_new.get(cluster, []))
        print(f"  {cluster}:")
        print(f"    OLD ({len(old_in_cluster)}): {', '.join(old_in_cluster)}")
        print(f"    NEW ({len(new_in_cluster)}): {', '.join(new_in_cluster)}")


if __name__ == "__main__":
    main()
