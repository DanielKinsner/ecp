"""Phase K determinism-gate orchestration CLI (2026-04-29).

Runs the v2 dispatch chain against a frozen Phase J fixture N times and
aggregates per-finding stability + per-run canaries into a gate verdict.

**Architectural model — the lead is the orchestrator, this script is the coordinator:**

Python cannot dispatch specialists/ethics/synthesizer agents (Anthropic API
gating; Claude Code Agent tool is the lead's primitive). This script
provides the surrounding plumbing — scratch dir prep, per-run validation,
aggregate metric computation. The actual LLM dispatches happen in the lead
session BETWEEN ``prep-run`` and ``validate-run`` invocations.

**Two modes, same aggregate gate, different scratch-dir init:**

- **Mode A (canonical determinism gate):** frozen-input replay via
  ``prep-run --fixture FIXT``. Each run-N gets a scratch dir seeded with
  the fixture's frozen DOM + screenshots + cluster contexts + batons +
  meta. The dispatch chain runs against identical inputs; variance is
  purely model output drift. **This is the Phase K gate per §K of the
  canonical plan.**

- **Mode B (production validation):** re-acquire each run via
  ``init-run --target-url URL``. Each run-N starts as an empty engagement
  dir; the lead dispatches the acquirer into it, then the rest of the
  chain. Variance includes acquisition + JS-timing + model output drift.
  Useful as a post-K validation against a live URL before client delivery,
  but per §K Mode A is the canonical gate.

**Subcommands:**

  prep-run        Mode A — seed a scratch run dir from a frozen fixture.
                  Copies frozen inputs (DOM, screenshots, cluster contexts,
                  batons, meta, context.md). Does NOT copy outputs (cluster
                  emissions, ethics, synth, audits) — those are what the
                  lead's dispatch chain produces.

  init-run        Mode B — initialize an empty scratch run dir for fresh
                  acquisition. Writes a meta.json template with the target
                  URL and engagement-id; lead dispatches the acquirer into
                  the dir, then the rest of the chain.

  validate-run    Run all 4 canaries + citations validity on a completed
                  run dir. Writes a per-run JSON report.

  aggregate       Phase K headline gate — read N completed run dirs,
                  compute TARr@N + TARa@N + per-run canary green-rate +
                  citations validity, assert gate criteria, emit aggregate
                  report. Exit non-zero on gate FAIL.

  dry-run         Smoke test the loop at $0 — copy the fixture EVERYTHING
                  (including outputs) into N replicas, run aggregate,
                  expect TARr=TARa=1.0 + gate pass. Catches script bugs
                  before the operator commits ~5-12 hours of LLM time.

  list-fixture-files  Informational: show what prep-run will copy from a
                      fixture. Useful for verifying fixture completeness.

**Dispatch sequence the lead executes (Mode A):**

    for N in 1..n_runs:
        python scripts/run-determinism-gate.py prep-run \\
            --fixture fixtures/slingmods-pdp \\
            --runs-root engagements/det-gate-slingmods-pdp \\
            --run N
        # Lead dispatches 20 specialists in parallel (cluster-{cluster}-{device})
        # Lead waits for 20 cluster-emission-v1.json files
        # Lead dispatches ethics subagent
        # Lead waits for ethics-findings.json
        # Lead runs lead_prep.py build-canonical-frefs + synth_input.py trim-batons
        # Lead dispatches synthesizer subagent (opus)
        # Lead waits for audit-{device}.md + synthesizer-emission-v1.json
        # Lead writes audit-trace.log header + counters per Phase H/I contract
        python scripts/run-determinism-gate.py validate-run \\
            --run-dir engagements/det-gate-slingmods-pdp/run-{N:02d}

    python scripts/run-determinism-gate.py aggregate \\
        --runs-root engagements/det-gate-slingmods-pdp \\
        --audited-domain slingmods.com

The aggregate exit code is the gate verdict (0 pass / 1 fail).

Authored Phase K (2026-04-29). See:
- docs/plans/2026-04-27-feat-ecp-v2-redesign-plan.md Phase K
- docs/plans/2026-04-27-phase-k-handoff.md (operator entry doc)
- docs/plans/2026-04-27-phase-k-runbook.md (operator execution guide)
- scripts/assembly/determinism_gate.py — helpers
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from assembly.determinism_gate import (  # noqa: E402
    aggregate_runs,
    validate_run,
)
from assembly.atomic_write import atomic_write_text  # noqa: E402


# ---------------------------------------------------------------------------
# Constants — what gets copied during prep-run (Mode A frozen-input replay)
# ---------------------------------------------------------------------------

# Files that MUST be copied for the dispatch chain to run. Specialists need
# cluster-context-*; ethics needs batons; synth needs audit-context (DOM,
# screenshots) for visual reference. Lead reads meta.json for engagement-id.
_PREP_FROZEN_FILES = (
    "dom.html",
    "dom-mobile.html",
    "context.md",
    "meta.json",
    "baton.json",
    "baton-mobile.json",
)

# Glob patterns for files copied during prep-run.
_PREP_FROZEN_GLOBS = (
    "section-*.jpg",                 # screenshots
    "cluster-context-*.json",        # specialist cluster contexts
)

# Files explicitly NOT copied in prep-run — the dispatch chain regenerates
# these. Listed for documentation; prep-run uses an allowlist (above).
_PREP_REGENERATED_FILES = (
    "cluster-*-desktop.json",        # specialists produce
    "cluster-*-mobile.json",         # specialists produce (excluding -context)
    "ethics-findings.json",          # ethics produces
    "canonical-f-refs.json",         # lead builds from cluster + ethics
    "baton-desktop-trimmed.json",    # lead trims for synth input
    "baton-mobile-trimmed.json",     # lead trims for synth input
    "audit-desktop.md",              # synth produces
    "audit-mobile.md",               # synth produces
    "synthesizer-emission-v1.json",  # synth produces
    "audit-trace.log",               # lead writes throughout
    "lead-reflection.md",            # lead writes at completion
    "visual-report-*.html",          # renderer produces
)


# ---------------------------------------------------------------------------
# prep-run — seed a scratch dir from a frozen fixture
# ---------------------------------------------------------------------------


def cmd_prep_run(args) -> int:
    fixture_dir = args.fixture.resolve()

    # Two run-dir naming modes:
    # - Default: <runs-root>/run-{N:02d}/ (clean for Mode A determinism gates;
    #   schema engagement_id is rewritten to a generic 'det-{slug}-r{N}' form
    #   that won't match the strict ^YYYY-MM-DD-[0-9a-f]{8}$ pattern but works
    #   if the caller doesn't need schema-validating outputs).
    # - --engagement-id <YYYY-MM-DD-hex8>: places run at docs/ecp/{id}/ to
    #   match the v2 dispatch chain's path convention. Specialists write to
    #   docs/ecp/{engagement_id}/cluster-{cluster}-{device}.json per
    #   contracts/specialist-prompt-v2.md, so this mode is required when
    #   running the actual LLM dispatch chain (not just the dry-run smoke).
    if args.engagement_id:
        run_dir = REPO_ROOT / "docs" / "ecp" / args.engagement_id
        new_engagement_id = args.engagement_id
    else:
        runs_root = args.runs_root.resolve()
        run_dir = runs_root / f"run-{args.run:02d}"
        new_engagement_id = None  # set later

    if not fixture_dir.is_dir():
        print(f"error: fixture not found: {fixture_dir}", file=sys.stderr)
        return 2

    if run_dir.exists():
        if not args.force:
            print(
                f"error: run dir already exists: {run_dir}\n"
                f"       (re-run with --force to overwrite)",
                file=sys.stderr,
            )
            return 2
        shutil.rmtree(run_dir)

    run_dir.parent.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)

    # Copy explicit frozen files.
    copied: list[str] = []
    for name in _PREP_FROZEN_FILES:
        src = fixture_dir / name
        if src.exists():
            shutil.copy2(src, run_dir / name)
            copied.append(name)
        elif args.strict:
            print(
                f"error: required frozen file missing from fixture: {name}",
                file=sys.stderr,
            )
            return 2

    # Copy globbed frozen files.
    for pattern in _PREP_FROZEN_GLOBS:
        for src in fixture_dir.glob(pattern):
            shutil.copy2(src, run_dir / src.name)
            copied.append(src.name)

    # Rewrite meta.json with the new engagement_id reflecting this run.
    if new_engagement_id is None:
        fixture_slug = fixture_dir.name
        new_engagement_id = (
            f"det-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-"
            f"{fixture_slug}-r{args.run:02d}"
        )
    meta_path = run_dir / "meta.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"error: meta.json unreadable: {exc}", file=sys.stderr)
            return 2
        meta["engagement_id"] = new_engagement_id
        meta["fixture_source"] = str(fixture_dir.relative_to(REPO_ROOT))
        meta["phase"] = "pending"
        meta.pop("findings_count", None)
        meta.pop("priority_path_synthesized", None)
        meta.pop("priority_path_stories", None)
        meta.pop("priority_path_modes", None)
        meta.pop("scope_page_synchronized_refs_count", None)
        meta.pop("humanized_findings_count", None)
        meta.pop("visual_reports", None)
        meta.pop("hotspot_match_methods", None)
        meta.pop("substantive_canaries", None)
        meta["determinism_run"] = {
            "run_number": args.run,
            "n_runs_total": args.n_runs,
            "prepared_at": datetime.now(timezone.utc).isoformat(),
        }
        atomic_write_text(meta_path, json.dumps(meta, indent=2, ensure_ascii=False))

    print(
        f"prepared run-{args.run:02d} at {run_dir}\n"
        f"  engagement_id: {new_engagement_id}\n"
        f"  files copied: {len(copied)}\n"
        f"  next: lead dispatches specialists + ethics + synth into this dir."
    )
    return 0


# ---------------------------------------------------------------------------
# init-run — Mode B — initialize an empty scratch dir for fresh acquisition
# ---------------------------------------------------------------------------


def cmd_init_run(args) -> int:
    runs_root = args.runs_root.resolve()
    run_dir = runs_root / f"run-{args.run:02d}"

    if run_dir.exists():
        if not args.force:
            print(
                f"error: run dir already exists: {run_dir}\n"
                f"       (re-run with --force to overwrite)",
                file=sys.stderr,
            )
            return 2
        shutil.rmtree(run_dir)

    runs_root.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)

    # Build a meta.json template the lead's acquire workflow will
    # extend with baton + screenshots + context.md.
    from urllib.parse import urlparse
    host = ""
    if args.target_url:
        try:
            host = urlparse(args.target_url).netloc
            if host.startswith("www."):
                host = host[4:]
        except ValueError:
            host = ""
    target_slug = (host.replace(".", "-") or "unknown") + (
        urlparse(args.target_url).path.replace("/", "-") if args.target_url else ""
    )
    target_slug = target_slug.strip("-") or "target"
    new_engagement_id = (
        f"det-prod-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}-"
        f"{target_slug[:32]}-r{args.run:02d}"
    )

    meta = {
        "engagement_id": new_engagement_id,
        "schema_version": 3,
        "phase": "pending",
        "url": args.target_url,
        "target_url": args.target_url,
        "audited_domain": host,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "determinism_run": {
            "mode": "B",
            "run_number": args.run,
            "n_runs_total": args.n_runs,
            "prepared_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    atomic_write_text(
        run_dir / "meta.json",
        json.dumps(meta, indent=2, ensure_ascii=False),
    )

    print(
        f"initialized run-{args.run:02d} (Mode B) at {run_dir}\n"
        f"  engagement_id: {new_engagement_id}\n"
        f"  target_url:    {args.target_url or '(not set)'}\n"
        f"  next: lead dispatches acquirer into this dir, then specialists +"
        f" ethics + synth as Mode A."
    )
    return 0


# ---------------------------------------------------------------------------
# validate-run — run all 4 canaries + citations on a completed run
# ---------------------------------------------------------------------------


def cmd_validate_run(args) -> int:
    run_dir = args.run_dir.resolve()
    if not run_dir.is_dir():
        print(f"error: run dir not found: {run_dir}", file=sys.stderr)
        return 2

    audited_domain = args.audited_domain or _resolve_audited_domain(run_dir)
    references_dir = (args.references_dir or REPO_ROOT / "references").resolve()

    report = validate_run(
        run_dir,
        audited_domain=audited_domain,
        references_dir=references_dir,
        expected_specialist_count=args.expected_specialist_count,
        element_threshold=args.element_threshold,
        ethics_max_diff=args.ethics_max_diff,
    )

    out_path = run_dir / "phase-k-validate-report.json"
    atomic_write_text(out_path, json.dumps(dict(report), indent=2, default=str))

    if args.json:
        print(json.dumps(dict(report), indent=2, default=str))
    else:
        print(f"validate-run report -> {out_path}")
        print(f"  all_passed: {report['all_passed']}")
        for c in report["canaries"]:
            mark = "PASS" if c.get("passed") else "FAIL"
            print(f"  [{mark}] {c.get('name')}: {c.get('summary')}")
        cit = report["citations"]
        cit_mark = "PASS" if cit.get("passed") else "FAIL"
        print(f"  [{cit_mark}] {cit.get('name')}: {cit.get('summary')}")

    return 0 if report["all_passed"] else 1


def _resolve_audited_domain(run_dir: Path) -> str:
    """Best-effort extraction of the audited domain from meta.json."""
    meta_path = run_dir / "meta.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return ""
        url = meta.get("url") or meta.get("target_url") or ""
        if "://" in url:
            from urllib.parse import urlparse
            try:
                host = urlparse(url).netloc
                if host.startswith("www."):
                    host = host[4:]
                return host
            except ValueError:
                return ""
    return ""


# ---------------------------------------------------------------------------
# aggregate — Phase K headline gate
# ---------------------------------------------------------------------------


def cmd_aggregate(args) -> int:
    # Two ways to specify runs:
    # - --runs-root <DIR>: glob run-*/ underneath (Mode A determinism gate
    #   with the canonical nested structure).
    # - --run-dirs <DIR1> <DIR2> ...: explicit list (when each run is its
    #   own top-level engagement dir at docs/ecp/{id}/, which is required
    #   for real LLM dispatch — see prep-run --engagement-id).
    if args.run_dirs:
        run_dirs = [Path(p).resolve() for p in args.run_dirs]
        for d in run_dirs:
            if not d.is_dir():
                print(f"error: run dir not found: {d}", file=sys.stderr)
                return 2
        runs_root = run_dirs[0].parent  # for the report-output location
    elif args.runs_root:
        runs_root = args.runs_root.resolve()
        if not runs_root.is_dir():
            print(f"error: runs-root not found: {runs_root}", file=sys.stderr)
            return 2
        run_dirs = sorted(d for d in runs_root.glob("run-*") if d.is_dir())
    else:
        print(
            "error: must pass either --runs-root <DIR> or --run-dirs <DIR1> <DIR2> ...",
            file=sys.stderr,
        )
        return 2

    if args.n_runs is not None and len(run_dirs) != args.n_runs:
        print(
            f"warning: --n-runs={args.n_runs} but found {len(run_dirs)} run dirs "
            f"(proceeding with what's on disk)",
            file=sys.stderr,
        )

    if not run_dirs:
        print(f"error: no run dirs found", file=sys.stderr)
        return 2

    audited_domain = args.audited_domain or _resolve_audited_domain(run_dirs[0])
    references_dir = (args.references_dir or REPO_ROOT / "references").resolve()

    report = aggregate_runs(
        run_dirs,
        audited_domain=audited_domain,
        references_dir=references_dir,
        reference_run=args.reference_run,
        stability_threshold=args.stability_threshold,
        expected_specialist_count=args.expected_specialist_count,
        element_threshold=args.element_threshold,
        ethics_max_diff=args.ethics_max_diff,
        include_embeddings=not args.no_embeddings,
        jaccard_threshold=args.jaccard_threshold,
        max_severity_distance=args.max_severity_distance,
        prose_cosine_threshold=args.prose_cosine_threshold,
        document_semscore_threshold=args.document_semscore_threshold,
        levenshtein_min=args.levenshtein_min,
    )

    if args.out:
        out_path = args.out.resolve()
    else:
        out_path = runs_root / "phase-k-aggregate-report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(out_path, json.dumps(dict(report), indent=2, default=str))

    if args.json:
        print(json.dumps(dict(report), indent=2, default=str))
    else:
        _print_aggregate_summary(report, out_path)

    return 0 if report["gate_passed"] else 1


def _print_aggregate_summary(report: dict, out_path: Path) -> None:
    print(f"\n=== Phase K Determinism Gate -- Aggregate Report ===")
    print(f"runs:                  {report['n_runs']}")
    print(f"reference run:         run-{report['reference_run']:02d}")
    print(f"runs passing canaries: "
          f"{report['runs_passing_canaries']}/{report['n_runs']}")
    print(f"TARr@N (presence):     {report['tar_r']:.4f}")
    print(f"TARa@N (semantic):     {report['tar_a']:.4f}")
    print(f"  paired findings:     "
          f"{report['paired_findings_passed']}/{report['paired_findings_total']} "
          f"passed stability")
    print(f"stability threshold:   {report['stability_threshold']:.2f}")
    print(f"")
    if report["gate_passed"]:
        print("VERDICT: [PASS] GATE PASSED")
    else:
        print("VERDICT: [FAIL] GATE FAILED")
        print("violations:")
        for v in report["gate_violations"]:
            print(f"  - {v}")
        if report["runs_failing_canaries"]:
            print("\nfailing runs:")
            for r in report["runs_failing_canaries"]:
                print(
                    f"  run-{r['run_index']:02d}: "
                    f"{r['failed_canaries'] or '[citations]'}"
                )
    print(f"\nfull report -> {out_path}")


# ---------------------------------------------------------------------------
# dry-run — smoke test the loop at $0
# ---------------------------------------------------------------------------


def cmd_dry_run(args) -> int:
    fixture_dir = args.fixture.resolve()
    runs_root = (
        args.runs_root.resolve()
        if args.runs_root
        else REPO_ROOT / "engagements" / f"det-dryrun-{fixture_dir.name}"
    )
    n_runs = args.n_runs

    if not fixture_dir.is_dir():
        print(f"error: fixture not found: {fixture_dir}", file=sys.stderr)
        return 2

    print(
        f"dry-run mode: copying {fixture_dir} verbatim into {n_runs} replica runs.\n"
        f"  runs-root: {runs_root}\n"
        f"  expected outcome: TARr=TARa=1.0, all canaries pass, gate passes."
    )

    if runs_root.exists():
        if not args.force:
            print(
                f"error: runs-root exists: {runs_root}\n"
                f"       (re-run with --force to overwrite)",
                file=sys.stderr,
            )
            return 2
        shutil.rmtree(runs_root)

    runs_root.mkdir(parents=True)
    for n in range(1, n_runs + 1):
        run_dir = runs_root / f"run-{n:02d}"
        shutil.copytree(fixture_dir, run_dir)
        print(f"  prepared run-{n:02d} ({sum(1 for _ in run_dir.iterdir())} files)")

    audited_domain = args.audited_domain or _resolve_audited_domain(
        runs_root / "run-01"
    )
    references_dir = (args.references_dir or REPO_ROOT / "references").resolve()

    print(f"\nrunning aggregate against {n_runs} replicas...")
    report = aggregate_runs(
        [runs_root / f"run-{n:02d}" for n in range(1, n_runs + 1)],
        audited_domain=audited_domain,
        references_dir=references_dir,
        reference_run=1,
        stability_threshold=args.stability_threshold,
        include_embeddings=not args.no_embeddings,
    )

    out_path = runs_root / "phase-k-aggregate-report.json"
    atomic_write_text(out_path, json.dumps(dict(report), indent=2, default=str))
    _print_aggregate_summary(report, out_path)

    # Dry-run validates the plumbing — the gate MUST pass on identical runs.
    # If it doesn't, the script has a bug (or the fixture itself is broken).
    if not report["gate_passed"]:
        print(
            "\nERROR: dry-run failed against byte-identical replicas -- "
            "this is a script bug or fixture defect, not a real gate failure.",
            file=sys.stderr,
        )
        return 1

    print("\nDry-run OK -- plumbing is sound. Real-LLM runs would dispatch into prep-run dirs.")
    return 0


# ---------------------------------------------------------------------------
# list-fixture-files — informational
# ---------------------------------------------------------------------------


def cmd_list_fixture_files(args) -> int:
    fixture_dir = args.fixture.resolve()
    if not fixture_dir.is_dir():
        print(f"error: fixture not found: {fixture_dir}", file=sys.stderr)
        return 2

    print(f"Files prep-run will copy from {fixture_dir}:")
    print(f"\n  Required files (must exist):")
    for name in _PREP_FROZEN_FILES:
        src = fixture_dir / name
        mark = "OK     " if src.exists() else "MISSING"
        size = src.stat().st_size if src.exists() else 0
        print(f"    [{mark}] {name} ({size} bytes)")

    print(f"\n  Glob patterns:")
    for pattern in _PREP_FROZEN_GLOBS:
        matches = list(fixture_dir.glob(pattern))
        print(f"    [{len(matches)}] {pattern}")
        for m in matches[:3]:
            print(f"        - {m.name}")
        if len(matches) > 3:
            print(f"        ... ({len(matches) - 3} more)")

    print(f"\n  NOT copied (regenerated by dispatch chain):")
    for pattern in _PREP_REGENERATED_FILES:
        matches = list(fixture_dir.glob(pattern))
        if matches:
            print(f"    [{len(matches)}] {pattern}")
    return 0


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="run-determinism-gate.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # prep-run
    p_prep = sub.add_parser("prep-run", help="Seed a scratch run dir from a fixture.")
    p_prep.add_argument("--fixture", required=True, type=Path,
                        help="Path to the frozen fixture (e.g., fixtures/slingmods-pdp).")
    p_prep.add_argument("--runs-root", default=None, type=Path,
                        help="Path under which run-N dirs are created (mutually "
                             "exclusive with --engagement-id).")
    p_prep.add_argument("--run", default=1, type=int, help="Run number (1-based).")
    p_prep.add_argument("--n-runs", type=int, default=10,
                        help="Total runs in this gate (recorded in meta.json).")
    p_prep.add_argument("--engagement-id", default=None, type=str,
                        help="Schema-compliant engagement_id (YYYY-MM-DD-hex8). "
                             "When set, run is placed at docs/ecp/{id}/ (path "
                             "convention specialists write to per "
                             "contracts/specialist-prompt-v2.md). Required for "
                             "real LLM dispatch; --runs-root is for smoke tests.")
    p_prep.add_argument("--force", action="store_true",
                        help="Overwrite an existing run dir.")
    p_prep.add_argument("--strict", action="store_true",
                        help="Fail if any required frozen file is missing.")

    # validate-run
    p_val = sub.add_parser("validate-run", help="Run 4 canaries + citations on a completed run.")
    p_val.add_argument("--run-dir", required=True, type=Path)
    p_val.add_argument("--audited-domain", default=None, type=str,
                       help="Override domain extraction from meta.json.")
    p_val.add_argument("--references-dir", default=None, type=Path,
                       help="Override default references/ path.")
    p_val.add_argument("--expected-specialist-count", default=None, type=int)
    p_val.add_argument("--element-threshold", default=0.8, type=float)
    p_val.add_argument("--ethics-max-diff", default=1, type=int)
    p_val.add_argument("--json", action="store_true",
                       help="Emit full JSON report to stdout (default: human summary).")

    # aggregate
    p_agg = sub.add_parser("aggregate", help="Phase K gate verdict -- N-run aggregate.")
    p_agg.add_argument("--runs-root", default=None, type=Path,
                       help="Glob run-*/ under this dir (mutually exclusive with --run-dirs).")
    p_agg.add_argument("--run-dirs", default=None, nargs="+",
                       help="Explicit list of run engagement dirs (e.g., docs/ecp/2026-04-29-{hex8}).")
    p_agg.add_argument("--out", default=None, type=Path,
                       help="Override aggregate-report.json output path.")
    p_agg.add_argument("--audited-domain", default=None, type=str)
    p_agg.add_argument("--references-dir", default=None, type=Path)
    p_agg.add_argument("--reference-run", default=1, type=int,
                       help="1-based index of run to use as TARa reference.")
    p_agg.add_argument("--n-runs", default=None, type=int,
                       help="Expected total runs (warn if mismatch).")
    p_agg.add_argument("--stability-threshold", default=0.9, type=float,
                       help="TARr/TARa cutoff (default 0.9 per canonical plan §K).")
    p_agg.add_argument("--expected-specialist-count", default=None, type=int)
    p_agg.add_argument("--element-threshold", default=0.8, type=float)
    p_agg.add_argument("--ethics-max-diff", default=1, type=int)
    p_agg.add_argument("--no-embeddings", action="store_true",
                       help="Skip MiniLM embedding checks (structural-only TARa).")
    p_agg.add_argument("--jaccard-threshold", default=0.7, type=float)
    p_agg.add_argument("--max-severity-distance", default=1, type=int)
    p_agg.add_argument("--prose-cosine-threshold", default=0.85, type=float)
    p_agg.add_argument("--document-semscore-threshold", default=0.80, type=float)
    p_agg.add_argument("--levenshtein-min", default=0.3, type=float)
    p_agg.add_argument("--json", action="store_true")

    # dry-run
    p_dry = sub.add_parser("dry-run", help="Smoke test plumbing at $0 (replicates fixture).")
    p_dry.add_argument("--fixture", required=True, type=Path)
    p_dry.add_argument("--runs-root", default=None, type=Path)
    p_dry.add_argument("--n-runs", default=3, type=int)
    p_dry.add_argument("--audited-domain", default=None, type=str)
    p_dry.add_argument("--references-dir", default=None, type=Path)
    p_dry.add_argument("--stability-threshold", default=0.9, type=float)
    p_dry.add_argument("--no-embeddings", action="store_true")
    p_dry.add_argument("--force", action="store_true")

    # init-run (Mode B)
    p_init = sub.add_parser(
        "init-run",
        help="Mode B — initialize empty run dir for fresh acquisition.",
    )
    p_init.add_argument("--runs-root", required=True, type=Path)
    p_init.add_argument("--run", required=True, type=int)
    p_init.add_argument("--n-runs", type=int, default=10)
    p_init.add_argument("--target-url", required=True, type=str,
                        help="Live URL the acquirer will scrape into this run dir.")
    p_init.add_argument("--force", action="store_true")

    # list-fixture-files
    p_list = sub.add_parser("list-fixture-files", help="Show what prep-run will copy.")
    p_list.add_argument("--fixture", required=True, type=Path)

    args = parser.parse_args(argv)

    handlers = {
        "prep-run": cmd_prep_run,
        "init-run": cmd_init_run,
        "validate-run": cmd_validate_run,
        "aggregate": cmd_aggregate,
        "dry-run": cmd_dry_run,
        "list-fixture-files": cmd_list_fixture_files,
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
