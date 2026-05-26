#!/usr/bin/env python3
"""Build synthesizer prompt inputs (valid_refs + candidates + findings_digest)
for a given engagement + device. Mirrors assemble-audit.py up through
FinalizedFindings.build().
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from assembly.parser import load_all_cluster_files
from assembly.dedup import deduplicate
from assembly.pipeline import FinalizedFindings
from assembly.atomic_write import atomic_write_json


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engagement", required=True)
    ap.add_argument("--device", required=True)
    args = ap.parse_args()

    eng = Path(args.engagement)
    meta = json.load(open(eng / "meta.json"))
    clusters = meta["clusters_used"]

    findings, pass_findings, _ethics = load_all_cluster_files(eng, args.device, clusters)
    result = deduplicate(findings, pass_findings)
    finalized = FinalizedFindings.build(
        list(result.ethics_findings) + list(result.kept),
        clusters,
    )

    valid_refs = sorted(finalized.valid_refs())

    cand_path = eng / f"priority-path-candidates-{args.device}.json"
    cands_raw = cand_path.read_text(encoding="utf-8")

    # Walk cluster_finding_map to recover (cluster, idx) pairs in writer order.
    digest_lines = []
    cluster_counters = {c: 0 for c in clusters}
    for f in finalized.findings:
        cluster_counters[f.cluster] += 1
        idx = cluster_counters[f.cluster]
        obs = (f.observation or "").strip().replace("\n", " ")
        if len(obs) > 140:
            obs = obs[:137] + "..."
        digest_lines.append(
            f"{f.cluster} F-{idx:02d} [{f.priority}] "
            f"{f.section} — {obs}"
        )

    out = {
        "device": args.device,
        "valid_refs": valid_refs,
        "candidates_json_text": cands_raw,
        "findings_digest": "\n".join(digest_lines),
    }
    out_path = eng / f"synth-input-{args.device}.json"
    atomic_write_json(out_path, out)
    print(
        f"{args.device}: refs={len(valid_refs)} digest_lines={len(digest_lines)} "
        f"-> {out_path}"
    )


if __name__ == "__main__":
    main()
