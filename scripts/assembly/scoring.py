"""Priority Path candidate scoring for the ECP Audit Assembly package.

Scores synthesis hint groups and ungrouped CRITICAL findings to produce
a ranked list of Priority Path candidates.

v2 determinism updates (Phase E.4, 2026-04-27):
- All set/dict iterations are sorted explicitly so byte-identical output
  is reproducible across runs even though Python's dict ordering is
  insertion-deterministic by spec.
- Final candidate sort tie-breaks on ``suggested_title`` ascending so two
  candidates with identical (has_ethics, score) always sort the same way
  regardless of the upstream insertion order.
"""

from __future__ import annotations

from typing import Dict, List

from .models import Finding, PRIORITY_ORDER

ABOVE_FOLD_SECTIONS = {
    "hero-layout",
    "visual-hierarchy",
    "above-fold-content",
    "scan-pattern",
    "primary-cta",
    "cta-contrast",
    "cta-placement",
}

_SEVERITY_SCORE = {
    "CRITICAL": 10,
    "HIGH": 5,
    "MEDIUM": 2,
    "LOW": 1,
}


def _score_findings(findings: List[Finding]) -> int:
    """Compute the raw numeric score for a group of findings."""
    score = 0

    # Severity points
    for f in findings:
        score += _SEVERITY_SCORE.get(f.priority, 0)

    # Cluster span bonus (+3 per unique cluster)
    unique_clusters = {f.cluster for f in findings}
    score += 3 * len(unique_clusters)

    # Above-fold bonus (+2 if any finding's section is in ABOVE_FOLD_SECTIONS)
    sections = {f.section.lower().strip() for f in findings}
    if sections & ABOVE_FOLD_SECTIONS:
        score += 2

    return score


def _highest_severity(findings: List[Finding]) -> str:
    """Return the highest-severity priority label in a group."""
    return min(findings, key=lambda f: f.priority_rank).priority


def _has_ethics(findings: List[Finding]) -> bool:
    """Return True if any finding has a BLOCK or ADJACENT ethics state."""
    return any(f.ethics_state in ("BLOCK", "ADJACENT") for f in findings)


def _above_fold(findings: List[Finding]) -> bool:
    """Return True if any finding's section is in ABOVE_FOLD_SECTIONS."""
    return any(f.section.lower().strip() in ABOVE_FOLD_SECTIONS for f in findings)


def _finding_ref(f: Finding) -> str:
    """Return a stable reference string for a finding.

    Uses the post-dedup ``display_index`` set by
    ``scripts/assembly/pipeline.assign_display_indices``. Falls back to
    ``local_index`` for legacy callers that haven't yet tagged findings
    (callers that go straight from dedup to scoring without calling
    ``assign_display_indices`` — the assemble-audit orchestration always
    tags before scoring after v1.0).
    """
    idx = f.display_index if f.display_index > 0 else f.local_index
    return f"{f.cluster} F-{idx:02d}"


def _slug_to_title(slug: str) -> str:
    """Convert a hint slug to a human-readable title."""
    return slug.replace("-", " ").replace("_", " ").title()


def score_groups(
    synthesis_groups: Dict[str, List[Finding]],
    all_findings: List[Finding],
) -> List[dict]:
    """Score synthesis hint groups and ungrouped CRITICALs into ranked candidates.

    Args:
        synthesis_groups: hint_slug -> list[Finding] from the dedup result.
        all_findings: The ``kept`` list from the dedup result (all surviving
            non-BLOCK findings after dedup).

    Returns:
        A list of candidate dicts sorted by ethics-tiebreaker then score,
        each assigned a 1-based rank.
    """
    candidates: List[dict] = []

    # --- Build the set of finding refs that appear in any synthesis group ---
    # Sorted iteration for deterministic construction even though sets ignore order
    grouped_refs: set[str] = set()
    for slug in sorted(synthesis_groups.keys()):
        for f in sorted(synthesis_groups[slug], key=lambda f: (f.cluster, f.local_index)):
            grouped_refs.add(_finding_ref(f))

    # --- Score each synthesis hint group (sorted by slug for determinism) ---
    for slug in sorted(synthesis_groups.keys()):
        findings = synthesis_groups[slug]
        score = _score_findings(findings)
        has_eth = _has_ethics(findings)
        clusters = sorted({f.cluster for f in findings})
        refs = [_finding_ref(f) for f in findings]
        severity = _highest_severity(findings)
        above = _above_fold(findings)

        candidates.append({
            "rank": 0,  # assigned after sort
            "score": score,
            "suggested_title": _slug_to_title(slug),
            "severity": severity,
            "clusters_spanned": clusters,
            "finding_refs": refs,
            "above_fold": above,
            "has_ethics": has_eth,
        })

    # --- Ungrouped CRITICAL findings become standalone candidates ---
    # Sorted iteration over all_findings for deterministic candidate order
    for f in sorted(all_findings, key=lambda f: (f.priority_rank, f.cluster, f.local_index)):
        if f.priority != "CRITICAL":
            continue
        ref = _finding_ref(f)
        if ref in grouped_refs:
            continue

        findings = [f]
        score = _score_findings(findings)
        has_eth = _has_ethics(findings)
        above = _above_fold(findings)

        # Derive title from section, falling back to element
        title_source = f.section or f.element or ref
        title = title_source.replace("-", " ").replace("_", " ").title()

        candidates.append({
            "rank": 0,
            "score": score,
            "suggested_title": title,
            "severity": "CRITICAL",
            "clusters_spanned": [f.cluster],
            "finding_refs": [ref],
            "above_fold": above,
            "has_ethics": has_eth,
        })

    # --- Sort: ethics tiebreaker first (True > False), then score descending,
    # --- then suggested_title ascending as final tiebreaker (deterministic).
    # The explicit title tiebreaker prevents two candidates with identical
    # (has_ethics, score) from ranking differently across runs based on
    # upstream insertion order.
    candidates.sort(
        key=lambda c: (
            -(1 if c["has_ethics"] else 0),  # has_ethics first (negate so True→-1<0)
            -c["score"],                       # score descending
            c["suggested_title"],              # title ascending — deterministic tie-break
        )
    )

    # --- Assign ranks ---
    for i, candidate in enumerate(candidates, start=1):
        candidate["rank"] = i

    return candidates
