"""Phase J substantially-similar finding-stability metric (2026-04-28).

Compares two findings (a "golden" reference and a "candidate" re-run) and
returns a structured pass/fail result with the underlying metrics. Used by
the v2 fixture-diff CI script (``scripts/test-fixture-stability.py``) to
detect drift between the captured fixture's golden outputs and the audit
chain's re-run output.

Per the canonical plan §J.3, "substantially similar" decomposes into:

**Structural (must match exactly):**
- ``element.baton_index`` byte-equal
- ``surface`` byte-equal

**Loose structural similarity:**
- title token-set Jaccard >= 0.7
- severity-distance <= 1 (one severity tier of difference acceptable)

**Embedding similarity for prose** (OBSERVATION + RECOMMENDATION):
- per-field sentence-level cosine via ``all-MiniLM-L6-v2`` >= 0.85
- document-level SemScore (mean-pooled sentence embeddings of the
  concatenated OBSERVATION + RECOMMENDATION) >= 0.80

**Catastrophic-drift tripwire:**
- normalized Levenshtein similarity < 0.3 on OBSERVATION or RECOMMENDATION
  fails the comparison regardless of embedding cosine (catches the case
  where two findings hit the same embedding ballpark but read as totally
  different prose).

The pure-Python helpers (``title_token_set_jaccard``, ``severity_distance``,
``levenshtein_distance``, ``levenshtein_ratio``) are dependency-free and
suitable for use in environments without ML packages installed. The
embedding helpers (``prose_cosine_similarity``, ``semscore_document``)
lazy-import ``sentence-transformers``; the model
(``all-MiniLM-L6-v2``, ~80MB) downloads on first use and caches locally
under ``~/.cache/huggingface/``.

Authored Phase J (2026-04-28). See:
- docs/plans/2026-04-27-feat-ecp-v2-redesign-plan.md Phase J.3
- docs/plans/2026-04-27-phase-j-handoff.md "Deliverable 3"
- schema/finding-v1.json (golden/candidate input shape)
"""
from __future__ import annotations

import math
import re
from typing import TypedDict


_MODEL_NAME = "all-MiniLM-L6-v2"
_MODEL = None  # populated by _get_model() on first call (process-cached)


# ---------------------------------------------------------------------------
# Result shape
# ---------------------------------------------------------------------------


class StabilityResult(TypedDict):
    """Returned by ``compare_findings_stability``."""

    passed: bool
    metrics: dict
    failures: list[str]


# ---------------------------------------------------------------------------
# Pure-Python helpers (no ML imports)
# ---------------------------------------------------------------------------


_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> set[str]:
    """Lowercase alphanumeric word-set extraction; punctuation discarded."""
    return set(_TOKEN_RE.findall((text or "").lower()))


def title_token_set_jaccard(a: str, b: str) -> float:
    """Token-set Jaccard similarity in [0, 1].

    Tokenizes each input as lowercased alphanumeric runs (punctuation
    treated as separator), then returns ``|A ∩ B| / |A ∪ B|``. Two empty
    titles count as identical (1.0). One empty + one non-empty is 0.0.
    """
    ta, tb = _tokenize(a), _tokenize(b)
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


_SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


def severity_rank(severity: str) -> int:
    """Map severity to integer rank: CRITICAL=4, HIGH=3, MEDIUM=2, LOW=1.

    Unknown / empty severity returns 0. The distance helper computes
    ``abs(rank(a) - rank(b))``, so an unknown severity vs any known
    severity will surface as a distance >= 1 (which fails the default
    threshold) — making typos and missing severity fields visible.
    """
    return _SEVERITY_RANK.get((severity or "").upper(), 0)


def severity_distance(a: str, b: str) -> int:
    """Absolute distance between two severity ranks.

    Identical severity = 0. Adjacent tiers (HIGH vs MEDIUM, etc.) = 1.
    CRITICAL vs LOW = 3 (the maximum across the four tiers).
    """
    return abs(severity_rank(a) - severity_rank(b))


def levenshtein_distance(a: str, b: str) -> int:
    """Classic edit distance via two-row dynamic programming.

    Returns the minimum number of single-character insertions, deletions,
    or substitutions required to transform ``a`` into ``b``. Iterative
    implementation; O(min(|a|, |b|)) memory.
    """
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    # Always iterate over the shorter string for better space usage
    if len(a) > len(b):
        a, b = b, a
    prev = list(range(len(a) + 1))
    for j, bc in enumerate(b, start=1):
        curr = [j]
        for i, ac in enumerate(a, start=1):
            cost = 0 if ac == bc else 1
            curr.append(min(
                curr[i - 1] + 1,        # insertion
                prev[i] + 1,            # deletion
                prev[i - 1] + cost,     # substitution
            ))
        prev = curr
    return prev[-1]


def levenshtein_ratio(a: str, b: str) -> float:
    """Normalized Levenshtein similarity in [0, 1]; 1.0 = identical.

    Defined as ``1 - distance(a, b) / max(|a|, |b|)``. Two empty strings
    return 1.0. The "Levenshtein < 0.3" catastrophic-drift tripwire in the
    canonical plan §J.3 reads against this ratio.
    """
    if not a and not b:
        return 1.0
    longest = max(len(a), len(b))
    if longest == 0:
        return 1.0
    return 1.0 - (levenshtein_distance(a, b) / longest)


# ---------------------------------------------------------------------------
# Embedding-based helpers (lazy-import sentence-transformers)
# ---------------------------------------------------------------------------


def _get_model():
    """Lazy load + process-cache the sentence-transformers model.

    Raises ImportError with an actionable install hint if the package
    isn't available. The model file (~80MB for all-MiniLM-L6-v2)
    downloads on first call and is cached under
    ``~/.cache/huggingface/`` thereafter — subsequent process starts
    skip the download.
    """
    global _MODEL
    if _MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "prose_cosine_similarity and semscore_document require "
                "sentence-transformers (added to requirements.txt for Phase J). "
                "Install with: python -m pip install -r requirements.txt"
            ) from exc
        _MODEL = SentenceTransformer(_MODEL_NAME)
    return _MODEL


def _cosine(v1, v2) -> float:
    """Cosine similarity for two iterables of floats (no numpy required)."""
    v1 = list(v1)
    v2 = list(v2)
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    num = sum(a * b for a, b in zip(v1, v2))
    da = math.sqrt(sum(a * a for a in v1))
    db = math.sqrt(sum(b * b for b in v2))
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


def prose_cosine_similarity(a: str, b: str) -> float:
    """Cosine similarity of MiniLM-encoded embeddings for two prose strings.

    Per-finding similarity for OBSERVATION and RECOMMENDATION fields. The
    model encodes each input as a single mean-pooled vector via the
    sentence-transformers default pooling; returns the cosine of the two
    vectors clamped to [-1.0, 1.0]. The all-MiniLM-L6-v2 token limit is
    256; very long inputs are truncated by the model itself, but
    OBSERVATION + RECOMMENDATION typically fit (max 1200 chars per
    schema/finding-v1.json).

    Two empty strings return 1.0 (identical). One empty + one non-empty
    returns 0.0 (no similarity).
    """
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    model = _get_model()
    emb = model.encode([a, b], convert_to_numpy=True, normalize_embeddings=True)
    # normalize_embeddings=True means cosine = dot product
    return float(emb[0] @ emb[1])


_SENTENCE_SPLIT_RE = re.compile(
    r"(?<=[.!?])\s+(?=[A-Z(])"      # end-of-sentence followed by capital or open paren
    r"|(?<=[.!?])\s*\n+\s*"          # OR end-of-sentence followed by newline(s)
    r"|\n{2,}"                        # OR paragraph break
)


def _split_sentences(text: str) -> list[str]:
    """Naive sentence splitter for SemScore mean-pooling.

    Splits on:
    - period/!/? followed by whitespace + uppercase letter (or open paren)
    - period/!/? followed by newline
    - paragraph break (>= 2 newlines)

    Returns trimmed non-empty sentences. Falls back to ``[text]`` for
    single-sentence inputs (no split point detected).
    """
    text = (text or "").strip()
    if not text:
        return []
    parts = _SENTENCE_SPLIT_RE.split(text)
    return [p.strip() for p in parts if p and p.strip()]


def semscore_document(a: str, b: str) -> float:
    """Document-level SemScore: cosine of mean-pooled sentence embeddings.

    Per the SemScore paper (Aynetdinov & Akbik, arxiv:2401.17072), each
    document is split into sentences, each sentence is embedded
    independently, the sentence embeddings are mean-pooled into a single
    document-level vector, and cosine similarity is computed between the
    two document vectors. This is the spec the canonical plan §J.3
    requires for the document-level >= 0.80 threshold.

    Single-sentence inputs degenerate to the same result as
    ``prose_cosine_similarity`` (one mean-pool vector = the lone sentence
    embedding). Two empty inputs return 1.0; one empty + one non-empty
    returns 0.0.
    """
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    sa = _split_sentences(a) or [a]
    sb = _split_sentences(b) or [b]
    model = _get_model()
    emb_a = model.encode(sa, convert_to_numpy=True)
    emb_b = model.encode(sb, convert_to_numpy=True)
    pooled_a = emb_a.mean(axis=0)
    pooled_b = emb_b.mean(axis=0)
    return _cosine(pooled_a.tolist(), pooled_b.tolist())


# ---------------------------------------------------------------------------
# Top-level — compare a pair of findings end-to-end
# ---------------------------------------------------------------------------


def compare_findings_stability(
    golden: dict,
    candidate: dict,
    *,
    jaccard_threshold: float = 0.7,
    max_severity_distance: int = 1,
    prose_cosine_threshold: float = 0.85,
    document_semscore_threshold: float = 0.80,
    levenshtein_min: float = 0.3,
    include_embeddings: bool = True,
) -> StabilityResult:
    """Compare two findings against the substantially-similar threshold set.

    The full check covers:
    1. Structural byte-equal: ``element.baton_index`` and ``surface``.
    2. Loose structural: title Jaccard >= ``jaccard_threshold``,
       severity distance <= ``max_severity_distance``.
    3. Catastrophic-drift tripwire: Levenshtein ratio of OBSERVATION
       and RECOMMENDATION must each be >= ``levenshtein_min``.
    4. Embedding-based prose similarity (when ``include_embeddings``):
       per-field cosine >= ``prose_cosine_threshold`` for OBSERVATION
       and RECOMMENDATION, plus document-level SemScore over the
       concatenation >= ``document_semscore_threshold``.

    All checks run regardless of intermediate failures — the result
    captures every metric so the operator can see the full drift
    picture, not just the first failing check.

    Args:
        golden: parsed reference finding dict (per schema/finding-v1.json
            shape; only the fields used by the metrics are required).
        candidate: parsed re-run finding dict to compare against golden.
        jaccard_threshold: minimum title token-set Jaccard. Default 0.7.
        max_severity_distance: maximum allowed severity-rank delta.
            Default 1 (one tier of drift).
        prose_cosine_threshold: minimum per-field embedding cosine.
            Default 0.85.
        document_semscore_threshold: minimum document-level SemScore.
            Default 0.80.
        levenshtein_min: catastrophic-drift floor on per-field
            Levenshtein ratio. Default 0.3.
        include_embeddings: when False, skips the model-loading prose
            checks and returns structural metrics only. Useful for fast
            structural smoke tests in environments where loading the
            sentence-transformers model is undesirable.

    Returns:
        StabilityResult with:
            - passed: True iff no failure conditions triggered
            - metrics: dict of every computed value (for trace logging
              and operator triage)
            - failures: list of human-readable failure strings; empty
              when passed=True
    """
    metrics: dict = {}
    failures: list[str] = []

    # --- Structural byte-equal ---
    g_bidx = ((golden.get("element") or {}).get("baton_index") or "")
    c_bidx = ((candidate.get("element") or {}).get("baton_index") or "")
    metrics["element_baton_index_golden"] = g_bidx
    metrics["element_baton_index_candidate"] = c_bidx
    metrics["element_baton_index_equal"] = (g_bidx == c_bidx)
    if not metrics["element_baton_index_equal"]:
        failures.append(
            f"element.baton_index differs (golden={g_bidx!r}, candidate={c_bidx!r})"
        )

    g_surface = golden.get("surface") or ""
    c_surface = candidate.get("surface") or ""
    metrics["surface_golden"] = g_surface
    metrics["surface_candidate"] = c_surface
    metrics["surface_equal"] = (g_surface == c_surface)
    if not metrics["surface_equal"]:
        failures.append(
            f"surface differs (golden={g_surface!r}, candidate={c_surface!r})"
        )

    # --- Loose structural ---
    g_title = golden.get("title") or ""
    c_title = candidate.get("title") or ""
    metrics["title_jaccard"] = title_token_set_jaccard(g_title, c_title)
    if metrics["title_jaccard"] < jaccard_threshold:
        failures.append(
            f"title_jaccard={metrics['title_jaccard']:.3f} below threshold "
            f"{jaccard_threshold:.2f} (golden={g_title!r}, candidate={c_title!r})"
        )

    g_sev = golden.get("severity") or ""
    c_sev = candidate.get("severity") or ""
    metrics["severity_distance"] = severity_distance(g_sev, c_sev)
    if metrics["severity_distance"] > max_severity_distance:
        failures.append(
            f"severity_distance={metrics['severity_distance']} above max "
            f"{max_severity_distance} (golden={g_sev!r}, candidate={c_sev!r})"
        )

    # --- Catastrophic-drift tripwires (Levenshtein, no model required) ---
    g_obs = golden.get("observation") or ""
    c_obs = candidate.get("observation") or ""
    g_rec = golden.get("recommendation") or ""
    c_rec = candidate.get("recommendation") or ""

    metrics["observation_levenshtein"] = levenshtein_ratio(g_obs, c_obs)
    metrics["recommendation_levenshtein"] = levenshtein_ratio(g_rec, c_rec)
    if metrics["observation_levenshtein"] < levenshtein_min:
        failures.append(
            f"observation Levenshtein={metrics['observation_levenshtein']:.3f} "
            f"below tripwire {levenshtein_min:.2f} (catastrophic drift)"
        )
    if metrics["recommendation_levenshtein"] < levenshtein_min:
        failures.append(
            f"recommendation Levenshtein={metrics['recommendation_levenshtein']:.3f} "
            f"below tripwire {levenshtein_min:.2f} (catastrophic drift)"
        )

    # --- Embedding-based prose similarity ---
    if include_embeddings:
        metrics["observation_cosine"] = prose_cosine_similarity(g_obs, c_obs)
        metrics["recommendation_cosine"] = prose_cosine_similarity(g_rec, c_rec)
        if metrics["observation_cosine"] < prose_cosine_threshold:
            failures.append(
                f"observation cosine={metrics['observation_cosine']:.3f} "
                f"below threshold {prose_cosine_threshold:.2f}"
            )
        if metrics["recommendation_cosine"] < prose_cosine_threshold:
            failures.append(
                f"recommendation cosine={metrics['recommendation_cosine']:.3f} "
                f"below threshold {prose_cosine_threshold:.2f}"
            )

        g_doc = "\n\n".join(s for s in (g_obs, g_rec) if s).strip()
        c_doc = "\n\n".join(s for s in (c_obs, c_rec) if s).strip()
        metrics["document_semscore"] = semscore_document(g_doc, c_doc)
        if metrics["document_semscore"] < document_semscore_threshold:
            failures.append(
                f"document SemScore={metrics['document_semscore']:.3f} "
                f"below threshold {document_semscore_threshold:.2f}"
            )
    else:
        metrics["observation_cosine"] = None
        metrics["recommendation_cosine"] = None
        metrics["document_semscore"] = None

    return {
        "passed": not failures,
        "metrics": metrics,
        "failures": failures,
    }


# ---------------------------------------------------------------------------
# Fixture-vs-fixture diff (Phase J Deliverable 4 helper)
# ---------------------------------------------------------------------------


def _load_findings(emission_path):
    """Read findings list from a synthesizer-emission-v1.json file.

    Returns the ``findings`` array. Raises FileNotFoundError on missing
    file, json.JSONDecodeError on bad JSON, and ValueError when the
    payload doesn't have a ``findings`` array — the caller surfaces
    these as input errors.
    """
    import json
    data = json.loads(emission_path.read_text(encoding="utf-8"))
    findings = data.get("findings")
    if not isinstance(findings, list):
        raise ValueError(
            f"{emission_path} has no 'findings' array (got {type(findings).__name__})"
        )
    return findings


def _index_by_ref(findings):
    """Index findings by (cluster, local_id) tuple — the canonical f_ref key.

    Findings missing either ``cluster`` or ``local_id`` are dropped. Phase F
    locked the (cluster, local_id) emission convention; this index is the
    pairing key for cross-fixture diff.
    """
    index = {}
    for f in findings:
        cluster = f.get("cluster")
        local_id = f.get("local_id")
        if cluster is None or local_id is None:
            continue
        try:
            local_id_int = int(local_id)
        except (TypeError, ValueError):
            continue
        index[(cluster, local_id_int)] = f
    return index


def diff_engagements(
    golden_dir,
    candidate_dir,
    *,
    include_embeddings: bool = True,
    jaccard_threshold: float = 0.7,
    max_severity_distance: int = 1,
    prose_cosine_threshold: float = 0.85,
    document_semscore_threshold: float = 0.80,
    levenshtein_min: float = 0.3,
) -> dict:
    """Diff a candidate engagement against a frozen golden fixture.

    Reads ``synthesizer-emission-v1.json`` from each side, pairs findings
    by ``(cluster, local_id)``, runs ``compare_findings_stability`` on
    each pair, and reports per-pair pass/fail plus orphan f_refs that
    exist on only one side.

    Args:
        golden_dir: pathlib.Path to the frozen golden fixture (e.g.,
            ``fixtures/awdmods-homepage/``).
        candidate_dir: pathlib.Path to the candidate engagement (e.g.,
            a re-run captured under ``docs/ecp/{engagement-id}/``).
        include_embeddings, jaccard_threshold, ..., levenshtein_min:
            forwarded to ``compare_findings_stability``. Defaults match
            the canonical plan §J.3 thresholds.

    Returns:
        Dict with keys:
            - 'golden_dir', 'candidate_dir': str paths
            - 'all_passed': True iff every pair passed AND no orphans
            - 'paired_total', 'paired_passed', 'paired_failed': counts
            - 'orphans_in_golden', 'orphans_in_candidate': lists of f_refs
            - 'failures': list of failing per-pair entries
            - 'paired_results': full per-pair detail (pass and fail)
    """
    golden_emission = golden_dir / "synthesizer-emission-v1.json"
    candidate_emission = candidate_dir / "synthesizer-emission-v1.json"

    golden_findings = _load_findings(golden_emission)
    candidate_findings = _load_findings(candidate_emission)

    golden_idx = _index_by_ref(golden_findings)
    candidate_idx = _index_by_ref(candidate_findings)

    golden_keys = set(golden_idx.keys())
    candidate_keys = set(candidate_idx.keys())
    paired_keys = golden_keys & candidate_keys

    orphans_golden = sorted(
        f"{c} F-{i:02d}" for (c, i) in (golden_keys - candidate_keys)
    )
    orphans_candidate = sorted(
        f"{c} F-{i:02d}" for (c, i) in (candidate_keys - golden_keys)
    )

    paired_results: list[dict] = []
    failures: list[dict] = []
    paired_passed = 0

    for key in sorted(paired_keys):
        cluster, local_id = key
        f_ref = f"{cluster} F-{local_id:02d}"
        result = compare_findings_stability(
            golden_idx[key],
            candidate_idx[key],
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
        and not orphans_golden
        and not orphans_candidate
    )

    return {
        "golden_dir": str(golden_dir),
        "candidate_dir": str(candidate_dir),
        "all_passed": all_passed,
        "paired_total": paired_total,
        "paired_passed": paired_passed,
        "paired_failed": paired_failed,
        "orphans_in_golden": orphans_golden,
        "orphans_in_candidate": orphans_candidate,
        "failures": failures,
        "paired_results": paired_results,
    }


# ---------------------------------------------------------------------------
# CLI entry point — compare two finding JSON files end-to-end
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """CLI: compare two finding JSON files. Exits non-zero on stability failure.

    Useful for spot-checking individual finding pairs during fixture
    development. The full fixture-vs-fixture diff lives in
    ``scripts/test-fixture-stability.py``.
    """
    import argparse
    import json
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--golden", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--no-embeddings", action="store_true",
                        help="Skip sentence-transformers checks (structural-only)")
    parser.add_argument("--jaccard-threshold", default=0.7, type=float)
    parser.add_argument("--max-severity-distance", default=1, type=int)
    parser.add_argument("--prose-cosine-threshold", default=0.85, type=float)
    parser.add_argument("--document-semscore-threshold", default=0.80, type=float)
    parser.add_argument("--levenshtein-min", default=0.3, type=float)
    args = parser.parse_args(argv)

    golden = json.loads(args.golden.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))

    result = compare_findings_stability(
        golden,
        candidate,
        jaccard_threshold=args.jaccard_threshold,
        max_severity_distance=args.max_severity_distance,
        prose_cosine_threshold=args.prose_cosine_threshold,
        document_semscore_threshold=args.document_semscore_threshold,
        levenshtein_min=args.levenshtein_min,
        include_embeddings=not args.no_embeddings,
    )

    print(json.dumps(result, indent=2, default=str))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv[1:]))
