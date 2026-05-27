"""Phase J Deliverable 4 — fixture stability diff CLI.

Compares a candidate v2 engagement against a frozen golden fixture using
the substantially-similar finding-stability metric defined in
``scripts/assembly/finding_stability.py``. Reads the synthesizer emission
from each side, pairs findings by ``(cluster, local_id)``, and reports
per-pair pass/fail plus an aggregate verdict.

This script is the diff-only half of the v2 fixture stability check.
Re-running the v2 dispatch chain against frozen DOM is the lead's job
(Claude Code orchestrates Agent + Task spawns); Python can't dispatch
specialists, so this script never re-runs the chain — it only compares
two pre-captured engagements.

For Phase J, the script just runs the diff and reports results. Phase K
wires it into a 10-run determinism gate (per the canonical plan).

Usage:
    python scripts/test-fixture-stability.py \\
        --golden fixtures/awdmods-homepage \\
        --candidate docs/ecp/2026-04-28-NNNN-awdmods-homepage

    # Structural-only (no model load — useful for fast smoke checks):
    python scripts/test-fixture-stability.py \\
        --golden fixtures/awdmods-homepage \\
        --candidate docs/ecp/{engagement} \\
        --no-embeddings

Exit codes:
    0 — all paired findings pass the stability threshold
    1 — at least one paired finding failed; orphans on either side
        also count as failure
    2 — input error (missing fixture, unreadable JSON, etc.)

Authored Phase J (2026-04-28). See:
- scripts/assembly/finding_stability.py — diff_engagements lives here
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.finding_stability import diff_engagements  # noqa: E402


def _format_human_summary(report: dict) -> str:
    """Build a human-readable summary block for stdout."""
    lines: list[str] = []
    lines.append(f"golden:    {report['golden_dir']}")
    lines.append(f"candidate: {report['candidate_dir']}")
    lines.append("")
    lines.append(
        f"paired findings: {report['paired_total']} "
        f"({report['paired_passed']} passed, {report['paired_failed']} failed)"
    )
    if report["orphans_in_golden"]:
        lines.append(
            f"orphans in golden ({len(report['orphans_in_golden'])}): "
            + ", ".join(report["orphans_in_golden"])
        )
    if report["orphans_in_candidate"]:
        lines.append(
            f"orphans in candidate ({len(report['orphans_in_candidate'])}): "
            + ", ".join(report["orphans_in_candidate"])
        )
    if report["failures"]:
        lines.append("")
        lines.append(f"failures ({len(report['failures'])}):")
        for entry in report["failures"]:
            lines.append(f"  - {entry['f_ref']}:")
            for reason in entry["failures"]:
                lines.append(f"      * {reason}")
    lines.append("")
    verdict = "PASS" if report["all_passed"] else "FAIL"
    lines.append(f"VERDICT: {verdict}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", required=True, type=Path,
                        help="Path to the frozen golden fixture directory")
    parser.add_argument("--candidate", required=True, type=Path,
                        help="Path to the candidate engagement directory")
    parser.add_argument("--no-embeddings", action="store_true",
                        help="Skip sentence-transformers checks (structural-only)")
    parser.add_argument("--json", action="store_true",
                        help="Emit the full report as JSON to stdout (default: human summary)")
    parser.add_argument("--jaccard-threshold", default=0.7, type=float)
    parser.add_argument("--max-severity-distance", default=1, type=int)
    parser.add_argument("--prose-cosine-threshold", default=0.85, type=float)
    parser.add_argument("--document-semscore-threshold", default=0.80, type=float)
    parser.add_argument("--levenshtein-min", default=0.3, type=float)
    args = parser.parse_args(argv)

    if not args.golden.is_dir():
        print(f"error: --golden directory not found: {args.golden}", file=sys.stderr)
        return 2
    if not args.candidate.is_dir():
        print(f"error: --candidate directory not found: {args.candidate}", file=sys.stderr)
        return 2

    try:
        report = diff_engagements(
            args.golden,
            args.candidate,
            include_embeddings=not args.no_embeddings,
            jaccard_threshold=args.jaccard_threshold,
            max_severity_distance=args.max_severity_distance,
            prose_cosine_threshold=args.prose_cosine_threshold,
            document_semscore_threshold=args.document_semscore_threshold,
            levenshtein_min=args.levenshtein_min,
        )
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"error: failed to read synthesizer-emission-v1.json: {exc}",
              file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(_format_human_summary(report))

    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
