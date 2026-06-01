#!/usr/bin/env python3
"""ECP determinism probe — empirical harness for the 2026-05-31 diagnosis.

Companion to ``docs/2026-05-31-dynamic-workflows-determinism-plan.md``.

WHAT THIS PROVES (and what it deliberately does NOT)
----------------------------------------------------
This exercises ONLY the deterministic Layer-2 structuring path against FROZEN,
REAL fixture inputs:

    report.v2_loader.build_canonical_view
        -> assembly.json_parser.parse_emission_file   (schema validation)
        -> assembly.dedup.deduplicate_v2
        -> assembly.pipeline.FinalizedFindings.build   (assign_display_indices)
        -> assembly.pipeline.cross_device_title_merge

It CANNOT and DOES NOT measure LLM variance (specialists / synthesizer) or
acquisition variance — those are the dominant real-world causes and require the
N-run determinism gate (``scripts/run-determinism-gate.py``, Mode A frozen-input
replay). This probe isolates the one layer we can test hermetically and answers:
"given identical inputs, is the deterministic Python actually deterministic, and
how sensitive are the finding identifiers to the LLM-authored text that feeds
them?"

Three probes
------------
1. in-process stability  — build the canonical view N times in ONE process; the
   ref-set + per-ref metadata fingerprint must be identical every time.
2. cross-process stability — re-run the build in fresh subprocesses under
   different PYTHONHASHSEED values. Catches hidden set/dict iteration-order or
   built-in hash() salting. Expectation: STABLE (the code uses sha256 + sorted()).
3. input-sensitivity     — perturb ONE finding's ``title`` (then, separately, its
   ``surface``) in a COPY of the fixture, rebuild, and measure how the canonical
   ref-set / F-NN values shift. Demonstrates the real mechanism behind "findings
   differ run-to-run / hotspots drift": the deterministic hash key
   (surface|baton_index|verdict) and the cross-device merge key (normalized
   title) are fed LLM-authored text, so model word-choice — not the Python —
   moves the identifiers.

NOTE ON STALE FIXTURES (the 2026-05-31 finding)
-----------------------------------------------
The checked-in fixtures pre-date the ``proposed_anchor``-required-for-absent rule
(finding-v1.json allOf, "Architectural fix B" 2026-04-30). On the current schema
their absent findings fail validation, so ``build_canonical_view`` silently DROPS
the whole emission and returns 0 refs — which would make probe #3 a false
negative (empty universe in, empty out). Pass ``--repair-absent-anchors`` to inject
a schema-minimal ``proposed_anchor`` into absent findings that lack one (in a temp
copy only — the real fixtures are never modified), which both makes probe #3
conclusive AND demonstrates that the drop was caused solely by that one field.

USAGE (Windows-safe; run from the repo root)
--------------------------------------------
    python scripts/diagnostics/determinism_probe.py probe --fixture fixtures/slingmods-pdp
    python scripts/diagnostics/determinism_probe.py probe --fixture fixtures/slingmods-pdp --repair-absent-anchors
    python scripts/diagnostics/determinism_probe.py build --fixture fixtures/slingmods-pdp
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# --- Windows console safety (repo P1-1 note: non-ASCII -> cp1252 crash) ---
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_builder():
    try:
        from report.v2_loader import (  # noqa: E402
            build_canonical_view,
            _engagement_cluster_emission_paths,
            _engagement_ethics_findings_path,
        )
    except Exception as exc:  # ImportError or missing dep (jsonschema/referencing)
        print(f"[FATAL] could not import the canonical-view builder: {exc!r}", file=sys.stderr)
        print("        (needs `jsonschema` and `referencing` on this interpreter)", file=sys.stderr)
        raise SystemExit(3)
    return build_canonical_view, _engagement_cluster_emission_paths, _engagement_ethics_findings_path


def _fingerprint(by_ref: dict) -> str:
    blob = json.dumps(by_ref, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _build_one(fixture: Path):
    """Run build_canonical_view against an engagement dir.

    Returns (sorted_refs, fingerprint, dropped_list)."""
    build_canonical_view, cluster_paths_fn, ethics_path_fn = _load_builder()
    cluster_paths = cluster_paths_fn(fixture)
    ethics_path = ethics_path_fn(fixture)
    by_ref, _aliases, dropped = build_canonical_view(cluster_paths, ethics_path)
    return sorted(by_ref.keys()), _fingerprint(by_ref), dropped


def _emission_files(src: Path):
    """All cluster + ethics emission files (skipping the cluster-context slices)."""
    out = []
    for p in list(src.glob("cluster-*.json")) + list(src.glob("ethics-findings.json")) + \
            list(src.glob("anchor-candidates-*.json")):
        if p.name.startswith("cluster-context-"):
            continue
        out.append(p)
    return out


def _repair_absent_anchors_in_file(path: Path) -> int:
    """Inject a schema-minimal proposed_anchor into absent findings that lack one.

    Returns the number of findings repaired. The minimal section-variant anchor
    satisfies finding-v1.json's oneOf (kind=section requires section_index and a
    section placement; forbids element_baton_index / viewport_trigger)."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    repaired = 0
    for f in data.get("findings") or []:
        elem = f.get("element") or {}
        if elem.get("baton_index") == "absent" and not isinstance(f.get("proposed_anchor"), dict):
            dev = f.get("device") if f.get("device") in ("mobile", "desktop") else "desktop"
            f["proposed_anchor"] = {
                "kind": "section",
                "placement": "after-section",
                "section_index": 0,
                "viewport": dev,
            }
            repaired += 1
    if repaired:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return repaired


def _materialize(fixture: Path, repair: bool) -> tuple[Path, "tempfile.TemporaryDirectory | None", int]:
    """Return a working fixture dir. If repair=False, the original. If repair=True,
    a temp copy of just the emission files with absent-anchors injected."""
    if not repair:
        return fixture, None, 0
    td = tempfile.TemporaryDirectory(prefix="ecp-det-repair-")
    tmp = Path(td.name)
    total = 0
    for p in _emission_files(fixture):
        dst = tmp / p.name
        shutil.copy2(p, dst)
        total += _repair_absent_anchors_in_file(dst)
    return tmp, td, total


# ---------------------------------------------------------------------------
# Subcommand: build (single build, prints a fingerprint line)
# ---------------------------------------------------------------------------
def cmd_build(args) -> int:
    fixture = Path(args.fixture).resolve()
    refs, fp, dropped = _build_one(fixture)
    print(f"FINGERPRINT {fp}")
    print(f"REFCOUNT {len(refs)}")
    print(f"DROPPED {len(dropped)}")
    print(f"HASHSEED {os.environ.get('PYTHONHASHSEED', '(unset)')}")
    return 0


# ---------------------------------------------------------------------------
# Subcommand: probe (all three probes)
# ---------------------------------------------------------------------------
def _perturb_copy(work: Path, field: str) -> tuple[list[str], str, str]:
    """Copy the working emission set to a temp dir, mutate the first finding's
    ``field`` in one cluster emission, rebuild, return (refs, fingerprint, note)."""
    _, cluster_paths_fn, ethics_path_fn = _load_builder()
    build_canonical_view = _load_builder()[0]
    with tempfile.TemporaryDirectory(prefix="ecp-det-probe-") as td:
        tmp = Path(td)
        for p in _emission_files(work):
            shutil.copy2(p, tmp / p.name)

        target = tmp / "cluster-visual-cta-desktop.json"
        note = ""
        if target.exists():
            data = json.loads(target.read_text(encoding="utf-8"))
            findings = data.get("findings") or []
            if findings:
                old = findings[0].get(field, "")
                if field == "title":
                    findings[0][field] = (old or "Untitled") + " (reworded by specialist)"
                else:  # surface
                    findings[0][field] = (old or "hero") + "-zone"
                note = f"{target.name}:findings[0].{field}  {old!r} -> {findings[0][field]!r}"
                target.write_text(json.dumps(data, indent=2), encoding="utf-8")

        cluster_paths = cluster_paths_fn(tmp)
        ethics_path = ethics_path_fn(tmp)
        by_ref, _a, _d = build_canonical_view(cluster_paths, ethics_path)
        return sorted(by_ref.keys()), _fingerprint(by_ref), note


def cmd_probe(args) -> int:
    fixture = Path(args.fixture).resolve()
    n = args.iterations
    work, _td_handle, repaired = _materialize(fixture, args.repair_absent_anchors)
    report: dict = {
        "fixture": str(fixture.relative_to(REPO_ROOT)),
        "iterations": n,
        "repair_absent_anchors": args.repair_absent_anchors,
        "absent_findings_repaired": repaired,
    }
    ok = True

    print(f"=== ECP determinism probe :: {fixture.name} ===")
    if args.repair_absent_anchors:
        print(f"    (repair mode: injected proposed_anchor into {repaired} absent finding(s) "
              f"in a temp copy)\n")
    else:
        print()

    # -- Probe 1: in-process stability ------------------------------------
    refs0, fp0, dropped0 = _build_one(work)
    fps = {fp0}
    for _ in range(n - 1):
        _r, fp, _d = _build_one(work)
        fps.add(fp)
    p1_stable = len(fps) == 1
    ok = ok and p1_stable
    report["probe1_in_process"] = {
        "stable": p1_stable, "distinct_fingerprints": len(fps),
        "ref_count": len(refs0), "dropped_emissions": len(dropped0),
    }
    print(f"[Probe 1] in-process x{n}: "
          f"{'STABLE' if p1_stable else 'UNSTABLE'} "
          f"({len(fps)} distinct fingerprint(s); {len(refs0)} canonical refs; "
          f"{len(dropped0)} dropped emission(s))")

    inputs_valid = (len(refs0) > 0 and len(dropped0) == 0)
    report["inputs_valid"] = inputs_valid
    if not inputs_valid:
        print(f"  [!] INPUTS INCOMPLETE: {len(dropped0)} emission(s) dropped by schema "
              f"validation -> only {len(refs0)} canonical refs survived.")
        for d in dropped0[:3]:
            print(f"      - {d.get('path')}: {d.get('error_type')}: "
                  f"{(d.get('error_message') or '')[:110]}")
        if not args.repair_absent_anchors:
            print("      Re-run with --repair-absent-anchors to make probe #3 conclusive, OR")
            print("      point --fixture at a freshly-produced engagement on the current schema.")

    # -- Probe 2: cross-process stability (PYTHONHASHSEED) ----------------
    seeds = ["0", "1", "12345"]
    seed_fps: dict[str, str] = {}
    for s in seeds:
        env = {**os.environ, "PYTHONHASHSEED": s}
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "build", "--fixture", str(work)],
            capture_output=True, text=True, env=env,
        )
        fp = ""
        for line in proc.stdout.splitlines():
            if line.startswith("FINGERPRINT "):
                fp = line.split(" ", 1)[1].strip()
        seed_fps[s] = fp or f"(no-fingerprint rc={proc.returncode})"
    p2_stable = all(v == fp0 for v in seed_fps.values())
    ok = ok and p2_stable
    report["probe2_cross_process"] = {"stable": p2_stable, "in_process_fp": fp0, "per_seed": seed_fps}
    print(f"[Probe 2] cross-process (PYTHONHASHSEED={','.join(seeds)}): "
          f"{'STABLE' if p2_stable else 'UNSTABLE'}")
    for s, fp in seed_fps.items():
        mark = "==" if fp == fp0 else "!="
        print(f"            seed={s:>6}  {str(fp)[:16]}  {mark} in-process")

    # -- Probe 3: input-sensitivity (title, then surface) -----------------
    # Runs on any NON-EMPTY universe (residual drops are fine — we only need the
    # visual-cta finding present). Only truly-empty (all-dropped) inputs skip it.
    if len(refs0) == 0:
        report["probe3_input_sensitivity"] = {
            "status": "inconclusive",
            "reason": "all emissions dropped (see Probe 1); run with --repair-absent-anchors",
        }
        print("\n[Probe 3] input-sensitivity: INCONCLUSIVE "
              "(every emission dropped — see Probe 1).")
    else:
        base_set = set(refs0)
        title_refs, title_fp, title_note = _perturb_copy(work, "title")
        surface_refs, surface_fp, surface_note = _perturb_copy(work, "surface")

        def _delta(new_refs):
            new_set = set(new_refs)
            return sorted(base_set - new_set), sorted(new_set - base_set)

        t_removed, t_added = _delta(title_refs)
        s_removed, s_added = _delta(surface_refs)
        report["probe3_input_sensitivity"] = {
            "status": "ok",
            "baseline_ref_count": len(refs0),
            "title": {"note": title_note, "fingerprint_changed": title_fp != fp0,
                      "refs_removed": t_removed, "refs_added": t_added},
            "surface": {"note": surface_note, "fingerprint_changed": surface_fp != fp0,
                        "refs_removed": s_removed, "refs_added": s_added},
        }
        print(f"\n[Probe 3] input-sensitivity (one finding perturbed in a fixture copy; "
              f"baseline={len(refs0)} refs):")
        print(f"            title  : {title_note or '(no visual-cta desktop findings)'}")
        print(f"                     fingerprint_changed={title_fp != fp0}  "
              f"refs -{len(t_removed)} / +{len(t_added)}  "
              f"removed={t_removed[:3]} added={t_added[:3]}")
        print(f"            surface: {surface_note or '(no visual-cta desktop findings)'}")
        print(f"                     fingerprint_changed={surface_fp != fp0}  "
              f"refs -{len(s_removed)} / +{len(s_added)}  "
              f"removed={s_removed[:3]} added={s_added[:3]}")

    # -- Verdict ----------------------------------------------------------
    print("\n=== VERDICT ===")
    print(f"  deterministic-given-input (probes 1+2): {'PASS' if (p1_stable and p2_stable) else 'FAIL'}")
    if len(refs0) > 0:
        p3 = report["probe3_input_sensitivity"]
        sensitive = p3["title"]["fingerprint_changed"] or p3["surface"]["fingerprint_changed"]
        print(f"  identifiers move when LLM text changes (probe 3): {'YES' if sensitive else 'no'}")
    if len(dropped0) > 0:
        print(f"  [B1] {len(dropped0)} emission(s) SILENTLY dropped by build_canonical_view "
              f"(renderer ignores _drops) -> findings vanish from the report with no error.")

    out_path = Path.cwd() / "determinism-probe-report.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nfull report -> {out_path}")
    return 0 if ok else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_probe = sub.add_parser("probe", help="Run all three determinism probes.")
    p_probe.add_argument("--fixture", required=True, help="Path to a frozen engagement fixture dir.")
    p_probe.add_argument("--iterations", type=int, default=5, help="In-process repeat count (probe 1).")
    p_probe.add_argument("--repair-absent-anchors", action="store_true",
                         help="Inject a schema-minimal proposed_anchor into absent findings lacking "
                              "one (temp copy only) so stale fixtures validate and probe #3 is "
                              "conclusive. Also proves the drop cause.")

    p_build = sub.add_parser("build", help="Single build; prints one fingerprint line.")
    p_build.add_argument("--fixture", required=True)

    args = parser.parse_args(argv)
    if args.cmd == "build":
        return cmd_build(args)
    if args.cmd == "probe":
        return cmd_probe(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
