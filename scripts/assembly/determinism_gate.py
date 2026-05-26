"""Phase K determinism-gate helpers (2026-04-29).

Aggregates N-run determinism metrics on top of Phase J's per-pair finding-stability
metric. The gate reads N completed engagement directories (one per run), verifies
every run's substantive + structural canaries pass, runs a citations-validity
fabrication check on each emission, and computes TARr@N + TARa@N agreement
metrics against a designated reference run.

**Architectural constraint (carried from `scripts/test-fixture-stability.py`):**
Python cannot dispatch specialists/ethics/synthesizer agents — that's the
Claude Code lead's responsibility. This module operates only on completed
run directories. The outer CLI (`scripts/run-determinism-gate.py`) provides
prep-run / validate-run / aggregate-runs subcommands the lead invokes between
its own dispatch waves.

**Finding-data sourcing (Phase K, 2026-04-29):**

The synthesizer emission (``synthesizer-emission-v1.json``) does NOT carry
the full per-finding data shape. It exposes ``humanized_findings`` (reduced
to ``f_ref + plain_english_summary + plain_english_action``),
``severity_manifest`` (f_refs only), and ``priority_path`` (curated stories).

The full per-finding data (cluster, local_id, element, severity, citations,
observation, recommendation, etc. per ``schema/finding-v1.json``) lives in
the per-cluster ``cluster-{cluster}-{device}.json`` files (20 of them) and
``ethics-findings.json``. Phase K aggregates findings from those files for
per-pair stability comparison — a workaround for ``finding_stability.py``'s
``diff_engagements`` which assumes a ``findings`` array directly on the
synth emission. See "v2.1 follow-ups" in the Phase K handoff for the
upstream fix; Phase K does not block on it.

**Phase K deliverables this module covers** (per canonical plan §K):
- D3 + D4: aggregate stability gate ≥ 90% across N runs
- D4: per-run 4-canary green-rate (3 substantive from canary_checks + 1 structural
      from audit-trace.log counter parse)
- D5: citations-validity check (`reference_citations[].source` resolves in
      `references/`; `.section` matches a real heading)
- D6: TARr@N + TARa@N reporting per arXiv 2410.03492 + 2502.20747

Authored Phase K (2026-04-29). See:
- docs/plans/2026-04-27-feat-ecp-v2-redesign-plan.md Phase K
- docs/plans/2026-04-27-phase-k-handoff.md (operator entry doc)
- docs/plans/2026-04-27-phase-k-runbook.md (operator execution guide)
- scripts/assembly/finding_stability.py — pairwise stability primitive
- scripts/assembly/canary_checks.py — Phase I substantive canaries
- contracts/trace-assertion-canary.md — structural counter contract
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import TypedDict

# ---------------------------------------------------------------------------
# Trace-assertion counter parsing (4th structural canary)
# ---------------------------------------------------------------------------

# Lines like "#   team_spawned_specialists: 20" or "#   ethics_gate_executed: true"
# OR header lines like "# Pipeline: v2", "# Devices: desktop, mobile". Key
# matching is case-insensitive at parse time; the consumer normalizes to
# lowercase before comparing against known counter sets.
_TRACE_COUNTER_RE = re.compile(
    r"^#\s+(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*:\s*(?P<value>[^\s#]+(?:\s+[^\s#]+)*?)\s*(?:←.*)?$",
    re.MULTILINE,
)

# Counter name aliases (v2 → v1 fallback). The audit-trace contract accepts
# either naming style; this map normalizes to v2 names internally.
_TRACE_COUNTER_ALIASES = {
    "team_spawned_auditors": "team_spawned_specialists",
    "team_spawned_acquirers": "subagent_spawned_acquirers",
    "expected_auditor_count": "expected_specialist_count",
    "model_cluster_auditors": "model_cluster_specialists",
}

# Counters that are integer-valued in the header.
_INT_COUNTERS = {
    "tasks_created_total",
    "expected_specialist_count",
    "subagent_spawned_acquirers",
    "team_spawned_specialists",
    "subagent_spawned_ethics",
    "subagent_spawned_synthesizer",
    "subagent_spawned_planner",
    "team_spawned_planners",
    "subagent_spawned_reviewer",
    "subagent_spawned_builder",
    "cluster_files_written",
    "idle_notification_total",
}

# Counters with subagent_retried_<role> prefix accepted; treated as integer.
_INT_COUNTER_PREFIXES = ("subagent_retried_",)

# Counters that are bool-valued (lowercase string in trace).
_BOOL_COUNTERS = {"ethics_gate_executed"}


class TraceAssertions(TypedDict):
    """Parsed audit-trace.log header — counters + cost-trace + raw lines."""

    counters: dict
    """Normalized v2 counter names → int/bool values. Aliased v1 names fold in."""

    pipeline: str
    """'v1' | 'v2' | '' if absent."""

    flags: str
    """The 'Flags:' line value (e.g., '--auto --deep' or '')."""

    devices: list[str]
    """Parsed from 'Devices:' line, e.g., ['desktop', 'mobile']."""

    raw_lines: list[str]
    """The header lines as read (for diagnostic surfacing)."""


def parse_trace_assertions(trace_path: Path) -> TraceAssertions:
    """Parse an audit-trace.log header into structured counter dict.

    Reads only the header (lines up to the first non-comment line). Tolerates
    missing counters (returns 0/false defaults), v1 alias counter names (folded
    to v2 names), and unknown counter lines (preserved in counters dict at
    string value).

    Args:
        trace_path: path to audit-trace.log

    Returns:
        TraceAssertions dict with counters normalized to v2 names.

    Raises:
        FileNotFoundError: if trace_path does not exist.
    """
    if not trace_path.exists():
        raise FileNotFoundError(f"audit-trace.log not found at {trace_path}")

    text = trace_path.read_text(encoding="utf-8")

    # Header is everything up to first non-`#` non-blank line, or the first
    # `[YYYY-MM-DD...]` event-log line — whichever comes first.
    header_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            break
        header_lines.append(line)
    header_text = "\n".join(header_lines)

    counters: dict = {}
    pipeline = ""
    flags = ""
    devices: list[str] = []

    for match in _TRACE_COUNTER_RE.finditer(header_text):
        raw_key = match.group("key")
        key = raw_key.lower()
        value = match.group("value").rstrip()

        # Top-level header fields (Pipeline, Flags, Devices) are also
        # counter-shaped lines but live outside the ASSERTIONS block.
        if key == "pipeline":
            pipeline = value
            continue
        if key == "flags":
            flags = value
            continue
        if key == "devices":
            devices = [d.strip() for d in value.split(",") if d.strip()]
            continue

        # Skip non-counter informational header lines like "Engagement:",
        # "Target:", "Started:", "Display label:", "Scope:", "Clusters:",
        # "URL:". These use Title Case or full-prose values and aren't part
        # of the ASSERTIONS or COST TRACE blocks.
        if key in {
            "engagement", "target", "started", "displaylabel",
            "display_label", "scope", "clusters", "url",
        }:
            continue
        if raw_key[0].isupper():
            # Any other uppercase-led line is informational — skip it.
            continue

        # Apply alias normalization.
        canonical_key = _TRACE_COUNTER_ALIASES.get(key, key)

        # Coerce to int for known integer counters (incl. retry-counter prefix).
        if canonical_key in _INT_COUNTERS or any(
            canonical_key.startswith(p) for p in _INT_COUNTER_PREFIXES
        ):
            try:
                counters[canonical_key] = int(value)
            except (TypeError, ValueError):
                counters[canonical_key] = 0
        elif canonical_key in _BOOL_COUNTERS:
            counters[canonical_key] = value.strip().lower() in ("true", "1", "yes")
        else:
            # Unknown counter — preserve as raw string for diagnostic surfacing.
            counters[canonical_key] = value

    return TraceAssertions(
        counters=counters,
        pipeline=pipeline,
        flags=flags,
        devices=devices,
        raw_lines=header_lines,
    )


class StructuralCanaryResult(TypedDict):
    """The 4th canary (structural) result shape — parallel to CanaryResult."""

    name: str
    passed: bool
    summary: str
    detail: dict


def check_structural_canary(
    trace_path: Path,
    expected_specialist_count: int | None = None,
) -> StructuralCanaryResult:
    """Phase K's 4th canary: parse audit-trace.log + assert structural counters.

    Per ``contracts/trace-assertion-canary.md`` the v2 self-check at audit
    completion asserts:

        cluster_files_written == expected_specialist_count
        subagent_spawned_synthesizer >= 1
        subagent_spawned_ethics >= 1
        ethics_gate_executed == true

    Phase K's gate re-runs this check on every determinism run because the
    gate may invoke the audit pipeline outside the normal completion path
    (e.g., from a fresh scratch dir whose lead is replaying frozen fixture
    inputs). If any structural assertion fails, the run did not honor the
    architecture contract and is excluded from stability aggregation.

    Args:
        trace_path: path to the run's audit-trace.log
        expected_specialist_count: override the trace's own
            ``expected_specialist_count`` value. None = use the trace's.

    Returns:
        StructuralCanaryResult with detail keys:
            - 'cluster_files_written': observed counter
            - 'expected_specialist_count': observed (or passed-in) counter
            - 'subagent_spawned_synthesizer': observed counter
            - 'subagent_spawned_ethics': observed counter
            - 'ethics_gate_executed': observed bool
            - 'failures': list of human-readable assertion failure strings
    """
    if not trace_path.exists():
        return StructuralCanaryResult(
            name="structural_assertions",
            passed=False,
            summary=f"audit-trace.log not found at {trace_path}",
            detail={"file_missing": True},
        )

    trace = parse_trace_assertions(trace_path)
    counters = trace["counters"]

    cluster_files = counters.get("cluster_files_written", 0)
    expected = (
        expected_specialist_count
        if expected_specialist_count is not None
        else counters.get("expected_specialist_count", 0)
    )
    synth = counters.get("subagent_spawned_synthesizer", 0)
    ethics = counters.get("subagent_spawned_ethics", 0)
    ethics_gate = bool(counters.get("ethics_gate_executed", False))

    failures: list[str] = []
    if expected <= 0:
        failures.append(
            f"expected_specialist_count={expected} (must be > 0; ran an empty audit?)"
        )
    if cluster_files != expected:
        failures.append(
            f"cluster_files_written={cluster_files} != expected_specialist_count={expected}"
        )
    if synth < 1:
        failures.append(f"subagent_spawned_synthesizer={synth} (synthesizer never ran)")
    if ethics < 1:
        failures.append(
            f"subagent_spawned_ethics={ethics} (ethics subagent never ran)"
        )
    if not ethics_gate:
        failures.append("ethics_gate_executed=false (ethics gate did not complete)")

    passed = not failures
    summary = (
        f"structural counters OK ({cluster_files}/{expected} specialists, "
        f"synth={synth}, ethics={ethics}, gate={ethics_gate})"
        if passed
        else f"structural assertion failures: {len(failures)}"
    )

    return StructuralCanaryResult(
        name="structural_assertions",
        passed=passed,
        summary=summary,
        detail={
            "cluster_files_written": cluster_files,
            "expected_specialist_count": expected,
            "subagent_spawned_synthesizer": synth,
            "subagent_spawned_ethics": ethics,
            "ethics_gate_executed": ethics_gate,
            "failures": failures,
        },
    )


# ---------------------------------------------------------------------------
# Citations validity (D5: hallucinated-citation guard)
# ---------------------------------------------------------------------------


# A markdown heading line: matches `# Title`, `## Title`, etc. Captures the
# heading text (without the leading `#` runs).
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)


class CitationsValidityResult(TypedDict):
    """Citations-validity check result."""

    name: str
    passed: bool
    summary: str
    detail: dict


def _list_findings_from_emission(emission_path: Path) -> list[dict]:
    """Read findings list from a single emission file (cluster or ethics).

    Specialist cluster emissions (``cluster-{cluster}-{device}.json``) and the
    ethics emission (``ethics-findings.json``) both expose ``findings`` as a
    top-level list of finding dicts conforming to ``schema/finding-v1.json``.
    The synthesizer emission does NOT — see module docstring "Finding-data
    sourcing" for the architectural note. Returns an empty list if the file
    is missing or malformed (caller's job to surface that as a failure).
    """
    if not emission_path.exists():
        return []
    try:
        data = json.loads(emission_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    findings = data.get("findings")
    return findings if isinstance(findings, list) else []


def aggregate_findings_from_engagement(engagement_dir: Path) -> list[dict]:
    """Aggregate all findings from cluster + ethics emissions in an engagement dir.

    Reads:
    - All ``cluster-{cluster}-{device}.json`` files (excluding the
      ``cluster-context-*`` files that aren't emissions).
    - ``ethics-findings.json`` if present.

    Returns a flat list of finding dicts conforming to
    ``schema/finding-v1.json``. The list preserves emission order
    (cluster-by-cluster, then ethics) for deterministic indexing across runs.

    Mirrors the file-discovery pattern from
    ``scripts/lead_prep.py build-canonical-frefs`` — same source-of-truth as
    the canonical f_refs builder uses, so determinism comparison aligns with
    what the dedup engine sees.

    Args:
        engagement_dir: path to the engagement dir (a fixture root or a
            scratch run dir).

    Returns:
        List of finding dicts. Empty if no cluster/ethics emissions found.
    """
    findings: list[dict] = []
    if not engagement_dir.is_dir():
        return findings

    desktop_paths = sorted(
        p for p in engagement_dir.glob("cluster-*-desktop.json")
        if not p.name.startswith("cluster-context-")
    )
    mobile_paths = sorted(
        p for p in engagement_dir.glob("cluster-*-mobile.json")
        if not p.name.startswith("cluster-context-")
    )
    for p in desktop_paths + mobile_paths:
        findings.extend(_list_findings_from_emission(p))

    ethics_path = engagement_dir / "ethics-findings.json"
    if ethics_path.exists():
        findings.extend(_list_findings_from_emission(ethics_path))

    return findings


def _index_findings_by_ref(findings: list[dict]) -> dict[tuple[str, int], dict]:
    """Index findings by (cluster, local_id) tuple — the canonical f_ref key.

    Mirrors ``finding_stability._index_by_ref`` but kept local to avoid
    circular dependency. Findings missing either field are dropped.
    """
    out: dict[tuple[str, int], dict] = {}
    for f in findings:
        cluster = f.get("cluster")
        local_id = f.get("local_id")
        if cluster is None or local_id is None:
            continue
        try:
            local_id_int = int(local_id)
        except (TypeError, ValueError):
            continue
        out[(cluster, local_id_int)] = f
    return out


def _extract_headings(markdown_path: Path) -> set[str]:
    """Return the set of heading text strings in a markdown file.

    Strips trailing punctuation/whitespace; case-folded for forgiving match.
    Returns empty set if the file is missing or unreadable.
    """
    if not markdown_path.exists():
        return set()
    try:
        text = markdown_path.read_text(encoding="utf-8")
    except OSError:
        return set()
    return {_normalize_heading(m.group(1)) for m in _HEADING_RE.finditer(text)}


def _normalize_heading(s: str) -> str:
    """Normalize a heading string for forgiving comparison.

    Citation `section` fields can use slug-style ('regulatory-disclosure'),
    Title Case ('Regulatory Disclosure'), or full heading text
    ('Finding 3: Above-fold CTAs convert 32% better'). The check accepts a
    match if EITHER the slug-folded form OR the lowercased prose form matches.
    """
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def check_citations_validity(
    findings: list[dict],
    references_dir: Path,
    *,
    section_pass_threshold: float = 0.85,
) -> CitationsValidityResult:
    """Verify each finding's reference_citations[] resolve to real files + sections.

    Per the canonical plan §K.5: "every cited URL/selector in
    reference_citations[] must resolve in the frozen DOM (fixture runs) or
    live page (production runs). Catches hallucinated citations (66% of LLM
    citation failures per arXiv 2602.05930)."

    Phase K splits the check into TWO classes of failure:

    **Hard failures (gate-blocking — real fabrication):**
    - ``reference_citations[].source`` does NOT exist at
      ``references/{source}`` — the specialist invented a reference filename.

    **Soft failures (advisory — formatting drift):**
    - ``reference_citations[].section`` is non-empty AND doesn't match any
      heading in the source markdown. The reference file IS real; only the
      section anchor is wrong, which is a less severe class of error than
      a fabricated source. Specialists drift on section-heading format
      (slug vs Title Case vs full heading text) without inventing sources.

    The canary ``passed`` flag is True iff there are zero missing sources.
    The ``section_pass_rate`` is reported separately and falls below
    ``section_pass_threshold`` only as a soft warning the operator can
    review. URL validation (HTTP fetch) is NOT performed here — for fixture
    replay the URLs are trusted from the golden capture. Mode B (production
    validation, separate script) layers HTTP fetching on top.

    Args:
        findings: list of finding dicts from a synthesizer or specialist emission.
        references_dir: path to ``references/`` (the ECP reference markdown
            corpus).
        section_pass_threshold: soft threshold for the section-anchor match
            rate. Default 0.85 — empirically matches real specialist output
            (slingmods Phase J D2 fixture: 124/142 = 87.3%).

    Returns:
        CitationsValidityResult with detail keys:
            - 'total_findings': count scanned
            - 'total_citations': count of reference_citations entries
            - 'missing_sources': list of {f_ref, source} where the file
              doesn't exist (HARD failure; gate-blocking)
            - 'invalid_sections': list of {f_ref, source, section} where
              the section heading isn't found (SOFT failure; advisory)
            - 'source_pass_rate': fraction of citations whose source file
              resolves (the gate criterion)
            - 'section_pass_rate': fraction of citations with a non-empty
              section that matched a real heading (advisory)
            - 'section_pass_threshold': the threshold used
            - 'section_below_threshold': bool — True if section pass rate
              under the threshold (advisory warning, not gate-blocking)
    """
    if not references_dir.is_dir():
        return CitationsValidityResult(
            name="citations_validity",
            passed=False,
            summary=f"references directory not found: {references_dir}",
            detail={"references_dir_missing": True},
        )

    missing_sources: list[dict] = []
    invalid_sections: list[dict] = []
    total_citations = 0
    citations_with_section = 0

    # Cache of markdown_path → heading set so we don't re-read files.
    heading_cache: dict[Path, set[str]] = {}

    for f in findings:
        cluster = f.get("cluster") or "?"
        local_id = f.get("local_id")
        f_ref = (
            f"{cluster} F-{local_id:02d}"
            if isinstance(local_id, int)
            else f"{cluster} F-??"
        )
        for cite in f.get("reference_citations") or []:
            total_citations += 1
            source = cite.get("source")
            if not source:
                missing_sources.append({"f_ref": f_ref, "source": "(empty)"})
                continue
            ref_path = references_dir / source
            if not ref_path.is_file():
                missing_sources.append({"f_ref": f_ref, "source": source})
                continue

            section = cite.get("section")
            if section:
                citations_with_section += 1
                if ref_path not in heading_cache:
                    heading_cache[ref_path] = _extract_headings(ref_path)
                section_norm = _normalize_heading(section)
                if section_norm not in heading_cache[ref_path]:
                    invalid_sections.append({
                        "f_ref": f_ref,
                        "source": source,
                        "section": section,
                    })

    source_pass_rate = (
        (total_citations - len(missing_sources)) / total_citations
        if total_citations > 0
        else 1.0
    )
    section_pass_rate = (
        (citations_with_section - len(invalid_sections)) / citations_with_section
        if citations_with_section > 0
        else 1.0
    )
    section_below_threshold = (
        citations_with_section > 0 and section_pass_rate < section_pass_threshold
    )
    # Hard fail criterion: NO fabricated sources. Section drift is advisory.
    passed = len(missing_sources) == 0

    summary = (
        f"citations_validity: source={total_citations - len(missing_sources)}/"
        f"{total_citations} resolved (rate={source_pass_rate:.3f}); "
        f"section={citations_with_section - len(invalid_sections)}/"
        f"{citations_with_section} matched (rate={section_pass_rate:.3f})"
    )

    return CitationsValidityResult(
        name="citations_validity",
        passed=passed,
        summary=summary,
        detail={
            "total_findings": len(findings),
            "total_citations": total_citations,
            "citations_with_section": citations_with_section,
            "missing_sources": missing_sources,
            "invalid_sections": invalid_sections,
            "source_pass_rate": source_pass_rate,
            "section_pass_rate": section_pass_rate,
            "section_pass_threshold": section_pass_threshold,
            "section_below_threshold": section_below_threshold,
        },
    )


# ---------------------------------------------------------------------------
# TARr@N — Total Agreement Raw (presence-based agreement)
# ---------------------------------------------------------------------------


class TARrResult(TypedDict):
    """TARr@N computation result."""

    n_runs: int
    union_size: int
    intersection_size: int
    tar_r: float
    per_ref_presence: dict
    union_refs: list[str]
    intersection_refs: list[str]


def _engagement_f_ref_set(engagement_dir: Path) -> set[tuple[str, int]]:
    """Aggregate findings from cluster + ethics emissions, return f_ref set."""
    return set(_index_findings_by_ref(
        aggregate_findings_from_engagement(engagement_dir)
    ).keys())


def compute_tar_r(run_engagement_dirs: list[Path]) -> TARrResult:
    """TARr@N — fraction of unique f_refs (across all runs) that appear in EVERY run.

    Per arXiv 2410.03492 + 2502.20747 the "total agreement raw" metric for
    open-ended generation: collect the union of unique outputs (here:
    canonical f_refs) across N runs; the agreement rate is the fraction of
    that union that appears in every single run.

    For a perfectly determinstic chain, TARr@N = 1.0 (every run produces the
    same set of f_refs). Lower scores indicate either (a) findings drop in/out
    of runs (variance in specialist coverage) or (b) the dedup engine merged
    differently across runs (fewer canonical f_refs survived).

    F_refs are aggregated from per-cluster + ethics emissions in each run dir
    (see ``aggregate_findings_from_engagement`` — same source the dedup
    engine reads, so TARr aligns with the canonical-f_refs surface).

    Args:
        run_engagement_dirs: list of paths to engagement dirs, one per run.
            Each dir should contain cluster-{cluster}-{device}.json files
            and ethics-findings.json. Empty or missing dirs contribute the
            empty set.

    Returns:
        TARrResult dict.
    """
    if not run_engagement_dirs:
        return TARrResult(
            n_runs=0,
            union_size=0,
            intersection_size=0,
            tar_r=0.0,
            per_ref_presence={},
            union_refs=[],
            intersection_refs=[],
        )

    per_run_keys: list[set[tuple[str, int]]] = [
        _engagement_f_ref_set(d) for d in run_engagement_dirs
    ]
    union_keys = set().union(*per_run_keys) if per_run_keys else set()
    intersection_keys = (
        set.intersection(*per_run_keys) if per_run_keys and per_run_keys[0] else set()
    )
    if not per_run_keys[0] and len(per_run_keys) > 1:
        # First run was empty — intersection collapses to empty regardless;
        # set.intersection of an empty set yields empty.
        intersection_keys = set()

    per_ref_presence: dict = {}
    for key in sorted(union_keys):
        cluster, local_id = key
        ref = f"{cluster} F-{local_id:02d}"
        presence_count = sum(1 for keys in per_run_keys if key in keys)
        per_ref_presence[ref] = {
            "present_in_runs": presence_count,
            "total_runs": len(per_run_keys),
            "presence_rate": presence_count / len(per_run_keys),
        }

    union_size = len(union_keys)
    intersection_size = len(intersection_keys)
    tar_r = intersection_size / union_size if union_size > 0 else 1.0

    return TARrResult(
        n_runs=len(per_run_keys),
        union_size=union_size,
        intersection_size=intersection_size,
        tar_r=tar_r,
        per_ref_presence=per_ref_presence,
        union_refs=sorted(f"{c} F-{i:02d}" for (c, i) in union_keys),
        intersection_refs=sorted(f"{c} F-{i:02d}" for (c, i) in intersection_keys),
    )


# ---------------------------------------------------------------------------
# TARa@N — Total Agreement Parsed (semantic agreement via Phase J stability)
# ---------------------------------------------------------------------------


class TARaResult(TypedDict):
    """TARa@N computation result."""

    n_pairs_compared: int
    paired_total: int
    paired_passed: int
    paired_failed: int
    tar_a: float
    per_pair_summaries: list[dict]


def _diff_engagement_findings(
    reference_dir: Path,
    candidate_dir: Path,
    *,
    include_embeddings: bool,
    jaccard_threshold: float,
    max_severity_distance: int,
    prose_cosine_threshold: float,
    document_semscore_threshold: float,
    levenshtein_min: float,
) -> dict:
    """Pairwise diff using cluster+ethics aggregation (not synth emission).

    Mirrors ``finding_stability.diff_engagements``'s shape but reads findings
    from cluster-{cluster}-{device}.json + ethics-findings.json directly,
    routing around the latent bug where diff_engagements expects a
    ``findings`` array on synth emissions (which doesn't exist on real
    output). See module docstring "Finding-data sourcing" for the rationale
    and the spawned task for the upstream fix.

    Returns the same dict shape as diff_engagements: ``paired_total``,
    ``paired_passed``, ``paired_failed``, ``orphans_in_golden``,
    ``orphans_in_candidate``, ``failures``, ``paired_results``,
    ``all_passed``.
    """
    from assembly.finding_stability import compare_findings_stability  # lazy

    ref_findings = aggregate_findings_from_engagement(reference_dir)
    cand_findings = aggregate_findings_from_engagement(candidate_dir)

    ref_idx = _index_findings_by_ref(ref_findings)
    cand_idx = _index_findings_by_ref(cand_findings)

    ref_keys = set(ref_idx.keys())
    cand_keys = set(cand_idx.keys())
    paired_keys = ref_keys & cand_keys

    orphans_ref = sorted(
        f"{c} F-{i:02d}" for (c, i) in (ref_keys - cand_keys)
    )
    orphans_cand = sorted(
        f"{c} F-{i:02d}" for (c, i) in (cand_keys - ref_keys)
    )

    paired_results: list[dict] = []
    failures: list[dict] = []
    paired_passed = 0

    for key in sorted(paired_keys):
        cluster, local_id = key
        f_ref = f"{cluster} F-{local_id:02d}"
        result = compare_findings_stability(
            ref_idx[key],
            cand_idx[key],
            include_embeddings=include_embeddings,
            jaccard_threshold=jaccard_threshold,
            max_severity_distance=max_severity_distance,
            prose_cosine_threshold=prose_cosine_threshold,
            document_semscore_threshold=document_semscore_threshold,
            levenshtein_min=levenshtein_min,
        )
        entry = {
            "f_ref": f_ref,
            "passed": result["passed"],
            "metrics": result["metrics"],
            "failures": result["failures"],
        }
        paired_results.append(entry)
        if result["passed"]:
            paired_passed += 1
        else:
            failures.append(entry)

    paired_total = len(paired_keys)
    paired_failed = paired_total - paired_passed
    all_passed = (
        paired_failed == 0
        and not orphans_ref
        and not orphans_cand
    )

    return {
        "golden_dir": str(reference_dir),
        "candidate_dir": str(candidate_dir),
        "all_passed": all_passed,
        "paired_total": paired_total,
        "paired_passed": paired_passed,
        "paired_failed": paired_failed,
        "orphans_in_golden": orphans_ref,
        "orphans_in_candidate": orphans_cand,
        "failures": failures,
        "paired_results": paired_results,
    }


def compute_tar_a(
    reference_engagement_dir: Path,
    candidate_engagement_dirs: list[Path],
    *,
    include_embeddings: bool = True,
    jaccard_threshold: float = 0.7,
    max_severity_distance: int = 1,
    prose_cosine_threshold: float = 0.85,
    document_semscore_threshold: float = 0.80,
    levenshtein_min: float = 0.3,
) -> TARaResult:
    """TARa@N — fraction of paired f_refs (reference vs each candidate) passing stability.

    For each candidate run, runs the per-pair stability check against the
    reference run via ``_diff_engagement_findings``. Pairs are made by
    ``(cluster, local_id)`` aggregated from the per-cluster + ethics
    emissions in each engagement dir; each paired finding is checked against
    the Phase J substantially-similar threshold set (Jaccard, severity,
    prose cosine, SemScore, Levenshtein tripwire). The TARa@N rate
    aggregates pass/fail across all (N-1) pairwise comparisons.

    Per the canonical plan §K spec, TARa@N is the "parsed" agreement — it
    measures whether paired findings are substantively the same, not just
    whether they appear by f_ref. Combined with TARr@N (presence agreement),
    the two together give the operator a clean read on where determinism
    drift lives: missing findings (TARr<1) vs drifted findings (TARa<1).

    Args:
        reference_engagement_dir: path to the run designated as reference
            (typically run-1).
        candidate_engagement_dirs: paths to all OTHER run engagement dirs
            (typically run-2 through run-N).
        include_embeddings, jaccard_threshold, ..., levenshtein_min:
            forwarded to compare_findings_stability. Defaults match
            canonical plan §J.3.

    Returns:
        TARaResult dict.
    """
    paired_total_total = 0
    paired_passed_total = 0
    paired_failed_total = 0
    per_pair_summaries: list[dict] = []

    for idx, candidate_dir in enumerate(candidate_engagement_dirs, start=2):
        try:
            report = _diff_engagement_findings(
                reference_engagement_dir,
                candidate_dir,
                include_embeddings=include_embeddings,
                jaccard_threshold=jaccard_threshold,
                max_severity_distance=max_severity_distance,
                prose_cosine_threshold=prose_cosine_threshold,
                document_semscore_threshold=document_semscore_threshold,
                levenshtein_min=levenshtein_min,
            )
        except (FileNotFoundError, ValueError) as exc:
            per_pair_summaries.append({
                "candidate_run": idx,
                "candidate_dir": str(candidate_dir),
                "error": str(exc),
                "paired_total": 0,
                "paired_passed": 0,
                "paired_failed": 0,
            })
            continue

        per_pair_summaries.append({
            "candidate_run": idx,
            "candidate_dir": str(candidate_dir),
            "paired_total": report["paired_total"],
            "paired_passed": report["paired_passed"],
            "paired_failed": report["paired_failed"],
            "orphans_in_reference": len(report["orphans_in_golden"]),
            "orphans_in_candidate": len(report["orphans_in_candidate"]),
            "all_passed": report["all_passed"],
        })
        paired_total_total += report["paired_total"]
        paired_passed_total += report["paired_passed"]
        paired_failed_total += report["paired_failed"]

    tar_a = (
        paired_passed_total / paired_total_total
        if paired_total_total > 0
        else 1.0
    )

    return TARaResult(
        n_pairs_compared=len(candidate_engagement_dirs),
        paired_total=paired_total_total,
        paired_passed=paired_passed_total,
        paired_failed=paired_failed_total,
        tar_a=tar_a,
        per_pair_summaries=per_pair_summaries,
    )


# ---------------------------------------------------------------------------
# Per-run validation (citations + 4 canaries combined)
# ---------------------------------------------------------------------------


class PerRunReport(TypedDict):
    """Per-run validation summary."""

    run_dir: str
    all_passed: bool
    canaries: list
    citations: dict
    structural: dict


def validate_run(
    engagement_dir: Path,
    audited_domain: str,
    references_dir: Path,
    *,
    expected_specialist_count: int | None = None,
    element_threshold: float = 0.8,
    ethics_max_diff: int = 1,
) -> PerRunReport:
    """Run all 4 canaries + citations-validity check on a completed run.

    Combines:
    - 3 substantive canaries from ``canary_checks.run_all_canaries``
      (ethics_findings_have_source_urls, element_index_match_rate,
      cross_device_ethics_diff)
    - 1 structural canary from ``check_structural_canary`` (counter parsing
      of audit-trace.log)
    - 1 citations-validity check from ``check_citations_validity``

    A run "passes" iff all 4 canaries + citations validity all pass. The
    aggregate gate (``aggregate_runs``) excludes any failing run from
    stability calculation by default.

    Args:
        engagement_dir: path to the completed run's engagement dir.
        audited_domain: domain of the page being audited (for ethics
            self-cite check).
        references_dir: path to references/ for citations validity.
        expected_specialist_count: override for structural canary.
        element_threshold: pass threshold for element_index_match_rate.
        ethics_max_diff: pass threshold for cross_device_ethics_diff.

    Returns:
        PerRunReport dict.
    """
    from assembly.canary_checks import run_all_canaries  # lazy local import

    substantive = run_all_canaries(
        engagement_dir,
        audited_domain=audited_domain,
        element_threshold=element_threshold,
        ethics_max_diff=ethics_max_diff,
    )

    structural = check_structural_canary(
        engagement_dir / "audit-trace.log",
        expected_specialist_count=expected_specialist_count,
    )

    findings = aggregate_findings_from_engagement(engagement_dir)
    citations = check_citations_validity(findings, references_dir)

    canaries = list(substantive["results"]) + [dict(structural)]

    all_passed = (
        substantive["all_passed"]
        and structural["passed"]
        and citations["passed"]
    )

    return PerRunReport(
        run_dir=str(engagement_dir),
        all_passed=all_passed,
        canaries=canaries,
        citations=dict(citations),
        structural=dict(structural),
    )


# ---------------------------------------------------------------------------
# Aggregate gate (the headline Phase K verdict)
# ---------------------------------------------------------------------------


class AggregateReport(TypedDict):
    """Phase K aggregate gate report."""

    n_runs: int
    reference_run: int
    runs_passing_canaries: int
    runs_failing_canaries: list[dict]
    tar_r: float
    tar_a: float
    paired_findings_passed: int
    paired_findings_total: int
    stability_rate: float
    stability_threshold: float
    gate_passed: bool
    gate_violations: list[str]
    per_run_reports: list[dict]
    tar_r_detail: dict
    tar_a_detail: dict


def aggregate_runs(
    run_dirs: list[Path],
    *,
    audited_domain: str,
    references_dir: Path,
    reference_run: int = 1,
    stability_threshold: float = 0.9,
    expected_specialist_count: int | None = None,
    element_threshold: float = 0.8,
    ethics_max_diff: int = 1,
    include_embeddings: bool = True,
    jaccard_threshold: float = 0.7,
    max_severity_distance: int = 1,
    prose_cosine_threshold: float = 0.85,
    document_semscore_threshold: float = 0.80,
    levenshtein_min: float = 0.3,
) -> AggregateReport:
    """Phase K headline gate — aggregate N-run determinism verdict.

    Gate passes iff:
    1. Every run's 4 canaries + citations check pass (no soft tolerance;
       a single failing run fails the gate).
    2. TARa@N aggregate stability rate (paired-passed / paired-total) >=
       ``stability_threshold`` (default 0.9 per canonical plan §K).
    3. TARr@N >= ``stability_threshold`` (presence agreement; same threshold).

    The gate is intentionally strict — Phase K's whole purpose is to
    demonstrate that the v2 pipeline is sufficiently deterministic to ship.
    Any softening of these thresholds belongs in v2.1.

    Args:
        run_dirs: paths to the N completed run engagement dirs, ordered
            run-1 → run-N.
        audited_domain: domain for ethics self-cite check.
        references_dir: path to references/ for citations validity.
        reference_run: 1-based index of the reference run for TARa@N.
            Default 1 (compare runs 2..N against run-1). Must be in 1..N.
        stability_threshold: TARr/TARa cutoff. Default 0.9.
        expected_specialist_count: override for structural canary.
        element_threshold, ethics_max_diff: passed to canaries.
        include_embeddings, jaccard_threshold, ...: passed to TARa stability.

    Returns:
        AggregateReport dict.
    """
    n_runs = len(run_dirs)
    if n_runs < 2:
        return AggregateReport(
            n_runs=n_runs,
            reference_run=reference_run,
            runs_passing_canaries=0,
            runs_failing_canaries=[],
            tar_r=0.0,
            tar_a=0.0,
            paired_findings_passed=0,
            paired_findings_total=0,
            stability_rate=0.0,
            stability_threshold=stability_threshold,
            gate_passed=False,
            gate_violations=[
                f"need >= 2 runs for determinism gate (got {n_runs})"
            ],
            per_run_reports=[],
            tar_r_detail={},
            tar_a_detail={},
        )
    if not (1 <= reference_run <= n_runs):
        raise ValueError(
            f"reference_run={reference_run} must be in 1..{n_runs}"
        )

    # Per-run validation — canaries + citations
    per_run_reports: list[dict] = []
    runs_passing_canaries = 0
    runs_failing_canaries: list[dict] = []
    for idx, run_dir in enumerate(run_dirs, start=1):
        report = validate_run(
            run_dir,
            audited_domain=audited_domain,
            references_dir=references_dir,
            expected_specialist_count=expected_specialist_count,
            element_threshold=element_threshold,
            ethics_max_diff=ethics_max_diff,
        )
        per_run_reports.append({
            "run_index": idx,
            "run_dir": str(run_dir),
            "all_passed": report["all_passed"],
            "canaries": [
                {"name": c.get("name"), "passed": c.get("passed"),
                 "summary": c.get("summary")}
                for c in report["canaries"]
            ],
            "citations": {
                "passed": report["citations"].get("passed"),
                "summary": report["citations"].get("summary"),
            },
        })
        if report["all_passed"]:
            runs_passing_canaries += 1
        else:
            runs_failing_canaries.append({
                "run_index": idx,
                "run_dir": str(run_dir),
                "failed_canaries": [
                    c.get("name") for c in report["canaries"]
                    if not c.get("passed")
                ],
                "citations_passed": report["citations"].get("passed"),
            })

    # TARr@N: presence agreement across all N runs (aggregated from
    # cluster + ethics emissions, see compute_tar_r).
    tar_r_result = compute_tar_r(run_dirs)

    # TARa@N: stability of paired findings, reference vs each candidate
    ref_dir = run_dirs[reference_run - 1]
    candidate_dirs = [d for i, d in enumerate(run_dirs, start=1) if i != reference_run]
    tar_a_result = compute_tar_a(
        ref_dir,
        candidate_dirs,
        include_embeddings=include_embeddings,
        jaccard_threshold=jaccard_threshold,
        max_severity_distance=max_severity_distance,
        prose_cosine_threshold=prose_cosine_threshold,
        document_semscore_threshold=document_semscore_threshold,
        levenshtein_min=levenshtein_min,
    )

    # Stability rate is the TARa rate (paired-passed / paired-total).
    # TARr is reported separately; both must clear threshold for gate pass.
    stability_rate = tar_a_result["tar_a"]

    gate_violations: list[str] = []
    if runs_failing_canaries:
        gate_violations.append(
            f"{len(runs_failing_canaries)} of {n_runs} runs failed canaries: "
            + ", ".join(
                f"run-{r['run_index']}({','.join(r['failed_canaries']) or 'citations'})"
                for r in runs_failing_canaries
            )
        )
    if stability_rate < stability_threshold:
        gate_violations.append(
            f"TARa@{n_runs}={stability_rate:.3f} below threshold "
            f"{stability_threshold:.2f} ({tar_a_result['paired_failed']} of "
            f"{tar_a_result['paired_total']} paired findings drifted)"
        )
    if tar_r_result["tar_r"] < stability_threshold:
        gate_violations.append(
            f"TARr@{n_runs}={tar_r_result['tar_r']:.3f} below threshold "
            f"{stability_threshold:.2f} ({tar_r_result['union_size']} unique "
            f"f_refs across runs; only {tar_r_result['intersection_size']} "
            f"appear in every run)"
        )

    gate_passed = not gate_violations

    return AggregateReport(
        n_runs=n_runs,
        reference_run=reference_run,
        runs_passing_canaries=runs_passing_canaries,
        runs_failing_canaries=runs_failing_canaries,
        tar_r=tar_r_result["tar_r"],
        tar_a=tar_a_result["tar_a"],
        paired_findings_passed=tar_a_result["paired_passed"],
        paired_findings_total=tar_a_result["paired_total"],
        stability_rate=stability_rate,
        stability_threshold=stability_threshold,
        gate_passed=gate_passed,
        gate_violations=gate_violations,
        per_run_reports=per_run_reports,
        tar_r_detail=dict(tar_r_result),
        tar_a_detail=dict(tar_a_result),
    )
