"""Per-checkpoint pipeline metrics across r01, r02, r03.

Pulls real numbers from each run dir's emission files. No estimates.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

RUNS = [
    ("r01", REPO / "docs" / "ecp" / "2026-04-29-ee4d6cc6"),
    ("r02", REPO / "docs" / "ecp" / "2026-04-29-d21e1ce2"),
    ("r03", REPO / "docs" / "ecp" / "2026-04-29-bd952a50"),
]

CLUSTERS = [
    "audience", "category-navigation", "checkout-flows", "content-seo",
    "performance-ux", "post-purchase", "pricing", "product-media",
    "trust-credibility", "visual-cta",
]


def load_emission(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def count_findings(d: dict | None) -> tuple[int, int, int]:
    if not d:
        return (0, 0, 0)
    findings = d.get("findings", [])
    fail = sum(1 for f in findings if f.get("verdict") == "FAIL")
    partial = sum(1 for f in findings if f.get("verdict") == "PARTIAL")
    pass_ = sum(1 for f in findings if f.get("verdict") == "PASS")
    return (fail, partial, pass_)


def pretty_size(path: Path) -> str:
    if not path.exists():
        return "MISSING"
    return f"{path.stat().st_size:,}"


print("=" * 100)
print("LAYER 1 (specialists, sonnet) — findings emitted per cluster × device per run")
print("=" * 100)
print(f"{'cluster':<22} {'device':<8} {'r01 (F/P/Pass)':<18} {'r02 (F/P/Pass)':<18} {'r03 (F/P/Pass)':<18}")
print("-" * 100)
totals_per_run = {"r01": [0, 0, 0], "r02": [0, 0, 0], "r03": [0, 0, 0]}
for cluster in CLUSTERS:
    for device in ("desktop", "mobile"):
        row = [f"{cluster:<22}", f"{device:<8}"]
        for label, run_dir in RUNS:
            path = run_dir / f"cluster-{cluster}-{device}.json"
            d = load_emission(path)
            f, p, ps = count_findings(d)
            for i, v in enumerate((f, p, ps)):
                totals_per_run[label][i] += v
            row.append(f"{f}/{p}/{ps}".ljust(18))
        print("".join(row))
print("-" * 100)
print(f"{'TOTAL':<22} {'':<8} ", end="")
for label in ("r01", "r02", "r03"):
    f, p, ps = totals_per_run[label]
    print(f"{f}/{p}/{ps} (sum={f+p+ps})".ljust(18), end=" ")
print()

print()
print("=" * 100)
print("LAYER 1.5 (ethics, sonnet) — ethics findings per run")
print("=" * 100)
for label, run_dir in RUNS:
    eth = load_emission(run_dir / "ethics-findings.json")
    if not eth:
        print(f"  {label}: MISSING")
        continue
    findings = eth.get("findings", [])
    desktop = sum(1 for f in findings if f.get("device") == "desktop")
    mobile = sum(1 for f in findings if f.get("device") == "mobile")
    page = sum(1 for f in findings if f.get("device") == "page")
    states = {}
    for f in findings:
        s = f.get("ethics_state", "?")
        states[s] = states.get(s, 0) + 1
    print(f"  {label}: {len(findings)} findings (desktop={desktop} mobile={mobile} page={page}) | states={states}")

print()
print("=" * 100)
print("LAYER 2 (lead-side Python pipeline) — deterministic transformations")
print("=" * 100)
for label, run_dir in RUNS:
    cfr = load_emission(run_dir / "canonical-f-refs.json")
    bd = load_emission(run_dir / "baton.json")
    bm = load_emission(run_dir / "baton-mobile.json")
    btd = load_emission(run_dir / "baton-desktop-trimmed.json")
    btm = load_emission(run_dir / "baton-mobile-trimmed.json")
    cfr_count = len(cfr.get("valid_refs", [])) if cfr else 0
    by_canon = cfr.get("by_canonical_ref", {}) if cfr else {}
    page_scope = sum(1 for v in by_canon.values() if v.get("scope") == "page")
    device_scope = sum(1 for v in by_canon.values() if v.get("scope") == "device")
    bd_count = len(bd.get("elements", [])) if bd else 0
    bm_count = len(bm.get("elements", [])) if bm else 0
    btd_count = len(btd.get("elements", [])) if btd else 0
    btm_count = len(btm.get("elements", [])) if btm else 0
    print(f"  {label}:")
    print(f"    canonical f_refs:           {cfr_count} ({page_scope} page-scope + {device_scope} device-scope)")
    print(f"    baton trim (desktop):       {bd_count} -> {btd_count} elements ({btd_count/bd_count*100:.0f}% kept)" if bd_count else "    baton trim (desktop):       MISSING")
    print(f"    baton trim (mobile):        {bm_count} -> {btm_count} elements ({btm_count/bm_count*100:.0f}% kept)" if bm_count else "    baton trim (mobile):        MISSING")

print()
print("=" * 100)
print("VALIDATE-RUN canaries — pass/fail per run with concrete numbers")
print("=" * 100)
for label, run_dir in RUNS:
    rep = load_emission(run_dir / "phase-k-validate-report.json")
    if not rep:
        print(f"  {label}: validate report MISSING")
        continue
    print(f"  {label}: all_passed={rep.get('all_passed')}")
    for c in rep.get("canaries", []):
        passed = "PASS" if c.get("passed") else "FAIL"
        print(f"    [{passed}] {c.get('name'):42} {c.get('summary')}")
    cit = rep.get("citations") or rep.get("citations_validity")
    if cit:
        print(f"    citations: {cit.get('summary', cit)}")

print()
print("=" * 100)
print("LAYER 3 (synth, opus) — output file sizes per run")
print("=" * 100)
print(f"{'':<10} {'synth-emission.json':<22} {'audit-desktop.md':<22} {'audit-mobile.md':<22}")
for label, run_dir in RUNS:
    sj = pretty_size(run_dir / "synthesizer-emission-v1.json")
    ad = pretty_size(run_dir / "audit-desktop.md")
    am = pretty_size(run_dir / "audit-mobile.md")
    print(f"  {label}:    {sj:<22} {ad:<22} {am:<22}")

print()
print("=" * 100)
print("Synth-emission contents — finding count + scope split")
print("=" * 100)
for label, run_dir in RUNS:
    s = load_emission(run_dir / "synthesizer-emission-v1.json")
    if not s:
        print(f"  {label}: MISSING")
        continue
    pp = s.get("priority_path") or []
    fbc = s.get("findings_by_canonical_ref") or s.get("findings") or {}
    if isinstance(fbc, dict):
        n_findings = len(fbc)
    else:
        n_findings = len(fbc)
    print(f"  {label}: priority_path entries={len(pp)} | total findings in emission={n_findings}")
