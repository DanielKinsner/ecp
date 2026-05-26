"""Lead-side normalization for r03 emissions per Phase K handoff fixup patterns.

Idempotent. Apply known fixups so canonical f_refs build passes:
- effort.change_type 'config' -> 'feature'
- missing effort -> default {feature, single-file}
- element.role/text_content null -> empty string
- telemetry.reference_files_read items: strip "(partial)" suffix
- missing evidence_anchors / reference_citations on PASS findings -> empty array
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ENG_DIR = Path("docs/ecp/2026-04-29-bd952a50")


def normalize_finding(f: dict) -> bool:
    changed = False
    # effort
    if isinstance(f.get("effort"), dict):
        if f["effort"].get("change_type") == "config":
            f["effort"]["change_type"] = "feature"
            changed = True
    else:
        if "effort" not in f:
            f["effort"] = {"change_type": "feature", "change_scope": "single-file"}
            changed = True
    # element null fields
    if isinstance(f.get("element"), dict):
        for k in ("role", "text_content"):
            if f["element"].get(k) is None:
                f["element"][k] = ""
                changed = True
    # missing arrays for PASS
    for arr_field in ("evidence_anchors", "reference_citations"):
        if arr_field not in f:
            f[arr_field] = []
            changed = True
    return changed


def normalize_telemetry(d: dict) -> bool:
    changed = False
    tel = d.get("telemetry")
    if isinstance(tel, dict):
        rf = tel.get("reference_files_read")
        if isinstance(rf, list):
            new_rf = [re.sub(r"\s*\(partial\)\s*$", "", s) for s in rf]
            if new_rf != rf:
                tel["reference_files_read"] = new_rf
                changed = True
    return changed


def main() -> None:
    fixed = []
    for path in sorted(ENG_DIR.glob("cluster-*.json")):
        if "cluster-context-" in path.name:
            continue
        d = json.loads(path.read_text(encoding="utf-8"))
        changed = any(normalize_finding(f) for f in d.get("findings", []))
        if normalize_telemetry(d):
            changed = True
        if changed:
            path.write_text(json.dumps(d, indent=2), encoding="utf-8")
            fixed.append(path.name)

    eth = ENG_DIR / "ethics-findings.json"
    e = json.loads(eth.read_text(encoding="utf-8"))
    echanged = any(normalize_finding(f) for f in e.get("findings", []))
    if normalize_telemetry(e):
        echanged = True
    if echanged:
        eth.write_text(json.dumps(e, indent=2), encoding="utf-8")
        fixed.append(eth.name)

    print(f"Normalized {len(fixed)} files:")
    for f in fixed:
        print(f"  {f}")


if __name__ == "__main__":
    main()
