"""Cluster-specialist subagent-vs-teammate parity diff harness.

Phase H deliverable 5 (2026-04-28). Compares two `cluster-emission-v1.json`
files produced by dispatching the SAME specialist prompt as a subagent
(`Task` tool) vs as a teammate (`Agent` tool with team_name). If they're
byte-identical (modulo irreducible-variance fields like timestamps and
telemetry), v2.1 can flip cluster specialists to subagent dispatch.

Phase H deliverable 5: see contracts/dispatch-contract.md for the
specialist dispatch shape that v2.1 may flip from teammate to subagent.

Usage:
    python scripts/test-cluster-specialist-parity.py \\
        --subagent parity-test-pricing-desktop.subagent.json \\
        --teammate parity-test-pricing-desktop.teammate.json \\
        --report parity-test-pricing-desktop.report.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


# Fields whose values are EXPECTED to differ between runs (timestamps,
# self-reported telemetry counts). Excluded from byte-equality comparison.
IRREDUCIBLE_VARIANCE_FIELDS: tuple[tuple[str, ...], ...] = (
    ("started_at",),
    ("completed_at",),
    ("specialist_model", "version"),  # may include build hash
    ("telemetry", "reference_files_read"),  # order may vary
    ("telemetry", "duration_ms"),
    ("telemetry", "tokens_in"),
    ("telemetry", "tokens_out"),
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a deep copy with irreducible-variance fields stripped."""
    out = json.loads(json.dumps(payload))  # cheap deep copy
    for field_path in IRREDUCIBLE_VARIANCE_FIELDS:
        node = out
        for key in field_path[:-1]:
            if not isinstance(node, dict) or key not in node:
                break
            node = node[key]
        else:
            if isinstance(node, dict):
                node.pop(field_path[-1], None)
    # Sort reference_files_read if present (set semantics, not list)
    tel = out.get("telemetry") or {}
    if isinstance(tel.get("reference_files_read"), list):
        tel["reference_files_read"] = sorted(tel["reference_files_read"])
    return out


def diff_dicts(
    a: Any,
    b: Any,
    path: str = "",
    diffs: list[str] | None = None,
) -> list[str]:
    """Walk two JSON-shaped dicts in parallel; collect human-readable diffs."""
    if diffs is None:
        diffs = []
    if type(a) is not type(b):
        diffs.append(f"{path}: type mismatch ({type(a).__name__} vs {type(b).__name__})")
        return diffs
    if isinstance(a, dict):
        keys = set(a) | set(b)
        for k in sorted(keys):
            sub = f"{path}.{k}" if path else k
            if k not in a:
                diffs.append(f"{sub}: only in teammate")
                continue
            if k not in b:
                diffs.append(f"{sub}: only in subagent")
                continue
            diff_dicts(a[k], b[k], sub, diffs)
    elif isinstance(a, list):
        if len(a) != len(b):
            diffs.append(f"{path}: list length differs ({len(a)} vs {len(b)})")
        for i, (sa, sb) in enumerate(zip(a, b)):
            diff_dicts(sa, sb, f"{path}[{i}]", diffs)
    else:
        if a != b:
            # Truncate long string diffs for readability
            sa, sb = str(a), str(b)
            if max(len(sa), len(sb)) > 80:
                sa, sb = sa[:77] + "...", sb[:77] + "..."
            diffs.append(f"{path}: {sa!r} != {sb!r}")
    return diffs


def levenshtein_ratio(a: str, b: str) -> float:
    """Lightweight Levenshtein ratio (inline; avoids dep on python-Levenshtein).

    Returns the edit-distance / max(len) ratio. 0.0 = identical, 1.0 = completely different.
    """
    if a == b:
        return 0.0
    if not a or not b:
        return 1.0
    # Wagner-Fischer iterative DP
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            curr[j] = min(
                prev[j] + 1,
                curr[j - 1] + 1,
                prev[j - 1] + (0 if ca == cb else 1),
            )
        prev = curr
    return prev[-1] / max(len(a), len(b))


def classify_drift(
    sub: dict[str, Any],
    team: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    """Classify the parity result as PASS / PARTIAL / FAIL.

    PASS = byte-equal after normalize.
    PARTIAL = structural fields equal; only prose drift (Levenshtein <0.10).
    FAIL = structural divergence.
    """
    norm_sub = normalize(sub)
    norm_team = normalize(team)

    if json.dumps(norm_sub, sort_keys=True) == json.dumps(norm_team, sort_keys=True):
        return ("PASS", {"reason": "byte-equal in normalized form"})

    # Compare structural finding-list metadata (counts, verdicts, baton_indexes)
    sub_findings = sub.get("findings") or []
    team_findings = team.get("findings") or []

    if len(sub_findings) != len(team_findings):
        return (
            "FAIL",
            {"reason": f"finding count differs ({len(sub_findings)} vs {len(team_findings)})"},
        )

    structural_keys = ("verdict", "severity", "scope", "surface")
    element_keys = ("baton_index",)

    structural_diffs: list[str] = []
    prose_diffs: list[tuple[str, str, str, float]] = []
    for i, (sf, tf) in enumerate(zip(sub_findings, team_findings)):
        for k in structural_keys:
            if sf.get(k) != tf.get(k):
                structural_diffs.append(
                    f"findings[{i}].{k}: {sf.get(k)!r} vs {tf.get(k)!r}"
                )
        sf_el = sf.get("element") or {}
        tf_el = tf.get("element") or {}
        for k in element_keys:
            if sf_el.get(k) != tf_el.get(k):
                structural_diffs.append(
                    f"findings[{i}].element.{k}: {sf_el.get(k)!r} vs {tf_el.get(k)!r}"
                )
        for prose_field in ("observation", "recommendation", "why_this_matters"):
            sa = sf.get(prose_field) or ""
            sb = tf.get(prose_field) or ""
            ratio = levenshtein_ratio(sa, sb)
            if ratio > 0.0:
                prose_diffs.append((f"findings[{i}].{prose_field}", sa, sb, ratio))

    if structural_diffs:
        return ("FAIL", {"structural_diffs": structural_diffs, "prose_diffs": prose_diffs})

    # Structural fields all equal — check if prose drift is within tolerance
    max_prose_ratio = max((d[3] for d in prose_diffs), default=0.0)
    if max_prose_ratio < 0.10:
        return (
            "PARTIAL",
            {
                "reason": f"prose drift Levenshtein <0.10 (max {max_prose_ratio:.3f})",
                "prose_diffs": prose_diffs,
            },
        )
    return ("FAIL", {"reason": f"prose drift exceeds 0.10 (max {max_prose_ratio:.3f})", "prose_diffs": prose_diffs})


def render_report(
    subagent_path: Path,
    teammate_path: Path,
    classification: str,
    detail: dict[str, Any],
) -> str:
    lines = [
        f"# Cluster-specialist parity diff",
        f"",
        f"- Subagent run: `{subagent_path}`",
        f"- Teammate run: `{teammate_path}`",
        f"- Classification: **{classification}**",
        f"",
        f"## Detail",
        f"",
    ]
    if classification == "PASS":
        lines.append("Output is byte-equal after normalization. Cluster specialist dispatch shape (subagent vs teammate) does not affect emission for this run.")
        lines.append("")
        lines.append("Recommendation: log this run as PASS evidence in the engagement's "
                     "lead-reflection.md. Need 5 runs of each shape per cluster before declaring v2.1-ready.")
    elif classification == "PARTIAL":
        lines.append(f"Reason: {detail.get('reason')}")
        lines.append("")
        lines.append("Structural fields match (verdict, severity, scope, surface, baton_index, finding count). "
                     "Prose drifts within Levenshtein 10% — not byte-equal but functionally the same audit.")
        lines.append("")
        lines.append("### Prose drift detail")
        for path, a, b, ratio in detail.get("prose_diffs", []):
            lines.append(f"- {path} — Levenshtein {ratio:.3f}")
            lines.append(f"  - subagent: {a[:120]!r}")
            lines.append(f"  - teammate: {b[:120]!r}")
    else:  # FAIL
        lines.append(f"Reason: {detail.get('reason', 'structural divergence')}")
        lines.append("")
        if detail.get("structural_diffs"):
            lines.append("### Structural diffs")
            for diff in detail["structural_diffs"]:
                lines.append(f"- {diff}")
            lines.append("")
        if detail.get("prose_diffs"):
            lines.append("### Prose diffs (only after structural divergence is resolved)")
            for path, a, b, ratio in detail["prose_diffs"][:10]:
                lines.append(f"- {path} — Levenshtein {ratio:.3f}")
            if len(detail["prose_diffs"]) > 10:
                lines.append(f"- ... and {len(detail['prose_diffs']) - 10} more")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subagent", required=True, type=Path, help="Path to subagent-dispatched cluster-emission JSON")
    parser.add_argument("--teammate", required=True, type=Path, help="Path to teammate-dispatched cluster-emission JSON")
    parser.add_argument("--report", type=Path, help="Optional output path for the markdown diff report")
    parser.add_argument("--exit-on-fail", action="store_true", help="Return non-zero exit code on FAIL classification")
    args = parser.parse_args(argv)

    if not args.subagent.exists():
        print(f"ERROR: subagent emission not found at {args.subagent}", file=sys.stderr)
        return 2
    if not args.teammate.exists():
        print(f"ERROR: teammate emission not found at {args.teammate}", file=sys.stderr)
        return 2

    sub = load_json(args.subagent)
    team = load_json(args.teammate)

    classification, detail = classify_drift(sub, team)
    report = render_report(args.subagent, args.teammate, classification, detail)
    print(report)

    if args.report:
        args.report.write_text(report, encoding="utf-8")
        print(f"\nReport written to {args.report}", file=sys.stderr)

    if args.exit_on_fail and classification == "FAIL":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
