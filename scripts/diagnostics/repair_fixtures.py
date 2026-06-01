#!/usr/bin/env python3
"""Idempotent fixture refresh for the 2026-04-30 absent->proposed_anchor rule (fix B3).

The checked-in fixtures ``fixtures/slingmods-pdp`` and ``fixtures/awdmods-homepage``
pre-date two schema rules and therefore fail validation on the current schema,
which makes ``report.v2_loader.build_canonical_view`` silently drop the whole
emission and return 0 canonical refs:

1. finding-v1.json "Architectural fix B" (2026-04-30): a finding whose
   ``element.baton_index == "absent"`` MUST carry a ``proposed_anchor``.
2. ethics findings with ``ethics_state == "CLEAR"`` must declare
   ``effort.change_type == "not_applicable"`` and
   ``effort.change_scope == "not_applicable"`` (a CLEAR finding needs no change).

This script rewrites every per-device cluster emission
(``cluster-*-{device}.json``) and the page-level ``ethics-findings.json`` in
both fixture dirs, SKIPPING the ``cluster-context-*`` sidecars (those are not
emissions). It is safe to run repeatedly: a finding that already satisfies a
rule is left untouched, so re-running produces no further changes.

Repairs applied to every finding:
  * ``element.baton_index == "absent"`` and no dict ``proposed_anchor`` ->
    inject the schema-minimal section anchor::

        {"kind": "section", "placement": "after-section",
         "section_index": 0, "viewport": <device>}

    where <device> is the finding's own ``device`` if it is "mobile" or
    "desktop", otherwise "desktop" (e.g. the ethics findings' "page").
  * ``ethics_state == "CLEAR"`` -> set ``effort.change_type`` and
    ``effort.change_scope`` to "not_applicable".

Files are written back with ``indent=2`` and LF line endings; all other fields
are preserved exactly (key order, values, ``ensure_ascii=False`` so non-ASCII
text is kept verbatim).

USAGE (Windows-safe; run from the repo root)
--------------------------------------------
    python scripts/diagnostics/repair_fixtures.py
    python scripts/diagnostics/repair_fixtures.py fixtures/slingmods-pdp fixtures/awdmods-homepage
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# --- Windows console safety (repo P1-1 note: non-ASCII -> cp1252 crash) ---
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_FIXTURES = [
    REPO_ROOT / "fixtures" / "slingmods-pdp",
    REPO_ROOT / "fixtures" / "awdmods-homepage",
]


def _emission_files(fixture: Path) -> list[Path]:
    """Per-device cluster emissions + the page-level ethics emission.

    Skips ``cluster-context-*`` sidecars, which are not findings emissions."""
    out: list[Path] = []
    for p in sorted(fixture.glob("cluster-*.json")):
        if p.name.startswith("cluster-context-"):
            continue
        out.append(p)
    ethics = fixture / "ethics-findings.json"
    if ethics.exists():
        out.append(ethics)
    return out


def _device_for(finding: dict) -> str:
    dev = finding.get("device")
    return dev if dev in ("mobile", "desktop") else "desktop"


def repair_file(path: Path) -> dict:
    """Repair one emission file in place. Returns a per-file stats dict.

    Only rewrites the file when at least one finding was changed, so the run is
    idempotent and produces no spurious diffs."""
    stats = {"file": str(path), "anchors_injected": 0, "effort_reset": 0, "changed": False}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        stats["error"] = repr(exc)
        return stats

    changed = False
    for f in data.get("findings") or []:
        if not isinstance(f, dict):
            continue

        # Rule 1: absent baton_index requires a proposed_anchor.
        elem = f.get("element") or {}
        if elem.get("baton_index") == "absent" and not isinstance(f.get("proposed_anchor"), dict):
            f["proposed_anchor"] = {
                "kind": "section",
                "placement": "after-section",
                "section_index": 0,
                "viewport": _device_for(f),
            }
            stats["anchors_injected"] += 1
            changed = True

        # Rule 2: CLEAR ethics findings declare a not_applicable effort.
        if f.get("ethics_state") == "CLEAR":
            effort = f.get("effort")
            if not isinstance(effort, dict):
                effort = {}
                f["effort"] = effort
            if effort.get("change_type") != "not_applicable" or \
                    effort.get("change_scope") != "not_applicable":
                effort["change_type"] = "not_applicable"
                effort["change_scope"] = "not_applicable"
                stats["effort_reset"] += 1
                changed = True

    if changed:
        # indent=2, LF line endings, trailing newline; preserve non-ASCII text.
        text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        path.write_text(text, encoding="utf-8", newline="\n")
        stats["changed"] = True
    return stats


def repair_fixture(fixture: Path) -> list[dict]:
    return [repair_file(p) for p in _emission_files(fixture)]


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    fixtures = [Path(a).resolve() for a in args] if args else DEFAULT_FIXTURES

    total_files = 0
    total_anchors = 0
    total_effort = 0
    for fixture in fixtures:
        if not fixture.is_dir():
            print(f"[skip] not a directory: {fixture}", file=sys.stderr)
            continue
        print(f"=== {fixture} ===")
        for s in repair_fixture(fixture):
            if s.get("error"):
                print(f"  [error] {Path(s['file']).name}: {s['error']}")
                continue
            if s["changed"]:
                total_files += 1
                total_anchors += s["anchors_injected"]
                total_effort += s["effort_reset"]
                print(f"  [fixed] {Path(s['file']).name}: "
                      f"+{s['anchors_injected']} anchor(s), "
                      f"+{s['effort_reset']} effort reset(s)")
            else:
                print(f"  [ok]    {Path(s['file']).name}: already current")
    print(f"\nSUMMARY: {total_files} file(s) changed, "
          f"{total_anchors} anchor(s) injected, {total_effort} effort reset(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
