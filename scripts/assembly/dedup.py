"""Three-layer deduplication engine for ECP Audit Assembly.

Reduces 60+ raw findings per device to ~35-45 by merging cross-cluster duplicates.

v2 migration (Phase E, 2026-04-27):

- ``Finding`` is now ``frozen=True``. All mutations use ``dataclasses.replace()``
  to produce a new instance — eliminates the in-place writes at the v1
  ``_absorb_losers`` site (``winner.ethics_state = "ADJACENT"`` etc.) which
  shared mutable state across passes and made byte-identical determinism
  brittle.

- v2 entry point ``deduplicate_v2`` adds SCOPE-aware merging:
    - ``scope='page'`` findings dedup across device pairs (one finding emitted
      in both desktop and mobile collapses to a single rendered finding).
      Dedup key: ``(scope='page', baton_index, verdict)``.
    - ``scope='device'`` findings dedup within their own device only.
      Dedup key: ``(scope='device', device, baton_index, verdict)``.
    - Cross-cluster same-``baton_index`` collisions: KEEP both as different-lens
      findings unless they share ``(surface, verdict)`` triples — that's
      structural identity, merge with highest-evidence-tier wins.

The v1 ``deduplicate`` function preserved for backwards compat — v1 engagements
resume on the markdown-emission path. v2 engagements call ``deduplicate_v2``.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from typing import Dict, List, Tuple

from .models import DedupeResult, EVIDENCE_TIER_RANK, Finding, PassFinding


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def deduplicate(
    findings: List[Finding],
    pass_findings: List[PassFinding],
) -> DedupeResult:
    """Run three-layer dedup on a flat list of findings.

    Layer 1: Exact match on (section, element_normalized) — auto-merge.
    Layer 2: SYNTHESIS_HINT slug match with same element_normalized — auto-merge.
    Layer 3: Fuzzy candidate flagging for human review.

    BLOCK findings are removed before any dedup and returned as-is.
    Pass findings are deduped by first-80-chars of lowercased text.
    """
    result = DedupeResult()

    # --- Separate BLOCK + ADJACENT ethics findings before anything else ---
    # Both BLOCK and ADJACENT must route to result.ethics_findings so the
    # writer's _ethics_gate_header / _ethics_gate_summary can see them (they
    # read exclusively from ethics_findings per the v1.0.0 C3 fix). Routing
    # ADJACENT to `active` was the C3 regression that made the header say
    # "No BLOCK or ADJACENT ethics findings detected" while the body rendered
    # an ADJACENT finding verbatim — fixed in v1.0.1.
    ethics: List[Finding] = []
    active: List[Finding] = []
    for f in findings:
        if f.ethics_state in ("BLOCK", "ADJACENT"):
            ethics.append(f)
        else:
            active.append(f)
    # Sort ethics findings: BLOCK before ADJACENT, stable within each class.
    ethics.sort(key=lambda f: (0 if f.ethics_state == "BLOCK" else 1, f.cluster, f.local_index))
    result.ethics_findings = ethics

    # --- Layer 1: Exact match dedup ---
    active, auto_merged_1 = _layer1_exact(active)
    result.auto_merged.extend(auto_merged_1)

    # --- Layer 2: SYNTHESIS_HINT slug dedup ---
    active, auto_merged_2, synthesis_groups = _layer2_hint(active)
    result.auto_merged.extend(auto_merged_2)
    result.synthesis_groups = synthesis_groups

    # --- Layer 3: Fuzzy candidate flagging ---
    fuzzy_candidates = _layer3_fuzzy(active)
    result.fuzzy_candidates = fuzzy_candidates

    # --- Sort kept findings: priority_rank ascending (CRITICAL first) ---
    active.sort(key=lambda f: (f.priority_rank, f.cluster, f.local_index))
    result.kept = active

    # --- Dedup pass findings: first 80 chars lowercased ---
    result.pass_findings = _dedup_passes(pass_findings)

    return result


# ---------------------------------------------------------------------------
# Layer 1 — Exact match on (section, element_normalized)
# ---------------------------------------------------------------------------


def _layer1_exact(
    findings: List[Finding],
) -> Tuple[List[Finding], List[dict]]:
    """Group by (section, element_normalized); merge groups with 2+ findings."""
    # Build groups preserving insertion order
    groups: Dict[Tuple[str, str], List[Finding]] = defaultdict(list)
    for f in findings:
        key = (f.section.lower().strip(), f.element_normalized)
        groups[key].append(f)

    kept: List[Finding] = []
    auto_merged: List[dict] = []

    for key, group in groups.items():
        if len(group) == 1:
            kept.append(group[0])
            continue

        # Multiple findings with same section + element — merge them
        winner, losers = _pick_winner(group)
        winner, merge_record = _absorb_losers(winner, losers, reason=f"exact match: {key[0]} / {key[1]}")
        kept.append(winner)
        auto_merged.append(merge_record)

    return kept, auto_merged


# ---------------------------------------------------------------------------
# Layer 2 — SYNTHESIS_HINT slug dedup
# ---------------------------------------------------------------------------


def _hint_slug(hint: str) -> str:
    """Return the first word of a synthesis hint (the slug)."""
    if not hint:
        return ""
    return hint.split()[0].lower()


def _layer2_hint(
    findings: List[Finding],
) -> Tuple[List[Finding], List[dict], Dict[str, List[Finding]]]:
    """Group by synthesis hint slug; merge only if elements also match."""
    # Separate findings with and without a hint
    no_hint: List[Finding] = []
    hint_groups: Dict[str, List[Finding]] = defaultdict(list)

    for f in findings:
        slug = _hint_slug(f.synthesis_hint)
        if not slug:
            no_hint.append(f)
        else:
            hint_groups[slug].append(f)

    kept: List[Finding] = list(no_hint)
    auto_merged: List[dict] = []
    synthesis_groups: Dict[str, List[Finding]] = {}

    for slug, group in hint_groups.items():
        # Store the full hint group for Priority Path scoring (before any merge)
        synthesis_groups[slug] = list(group)

        # Sub-group by element_normalized within this hint group
        by_element: Dict[str, List[Finding]] = defaultdict(list)
        for f in group:
            by_element[f.element_normalized].append(f)

        for element, subgroup in by_element.items():
            if len(subgroup) == 1:
                kept.append(subgroup[0])
            else:
                # Same hint slug + same element → merge
                winner, losers = _pick_winner(subgroup)
                winner, merge_record = _absorb_losers(
                    winner,
                    losers,
                    reason=f"hint slug '{slug}' / element '{element}'",
                )
                kept.append(winner)
                auto_merged.append(merge_record)

    return kept, auto_merged, synthesis_groups


# ---------------------------------------------------------------------------
# Layer 3 — Fuzzy candidate flagging
# ---------------------------------------------------------------------------


def _layer3_fuzzy(findings: List[Finding]) -> List[dict]:
    """Flag groups that look like fuzzy duplicates for human review."""
    candidates: List[dict] = []
    group_id = 0

    # Check 1: (cluster, section) groups with 3+ findings
    by_cluster_section: Dict[Tuple[str, str], List[Finding]] = defaultdict(list)
    for f in findings:
        key = (f.cluster, f.section.lower().strip())
        by_cluster_section[key].append(f)

    for (cluster, section), group in by_cluster_section.items():
        if len(group) >= 3:
            group_id += 1
            candidates.append({
                "group_id": f"fuzzy-{group_id:02d}",
                "reason": f"3+ findings in cluster '{cluster}' section '{section}'",
                "action": "review",
                "findings": _summarize_group(group),
            })

    # Check 2: same element_normalized across different sections
    by_element: Dict[str, List[Finding]] = defaultdict(list)
    for f in findings:
        if f.element_normalized:
            by_element[f.element_normalized].append(f)

    for element, group in by_element.items():
        sections = {f.section.lower().strip() for f in group}
        if len(sections) >= 2:
            group_id += 1
            candidates.append({
                "group_id": f"fuzzy-{group_id:02d}",
                "reason": f"element '{element}' appears in {len(sections)} sections: {sorted(sections)}",
                "action": "review",
                "findings": _summarize_group(group),
            })

    return candidates


def _summarize_group(findings: List[Finding]) -> List[dict]:
    return [
        {
            "cluster": f.cluster,
            "finding_index": f.local_index,
            "section": f.section,
            "element": f.element,
            "priority": f.priority,
            "observation_snippet": f.observation[:120],
        }
        for f in findings
    ]


# ---------------------------------------------------------------------------
# Pass finding dedup
# ---------------------------------------------------------------------------


def _dedup_passes(passes: List[PassFinding]) -> List[PassFinding]:
    """Remove exact duplicates using first 80 chars of lowercased text."""
    seen: set[str] = set()
    deduped: List[PassFinding] = []
    for pf in passes:
        key = pf.text.lower()[:80]
        if key not in seen:
            seen.add(key)
            deduped.append(pf)
    return deduped


# ---------------------------------------------------------------------------
# Merge helpers
# ---------------------------------------------------------------------------


def _pick_winner(group: List[Finding]) -> Tuple[Finding, List[Finding]]:
    """Select the winner from a group.

    Rules (in order):
    1. Lowest priority_rank (CRITICAL=0 beats HIGH=1, etc.)
    2. On tie: longest observation (more complete analysis)
    """
    sorted_group = sorted(
        group,
        key=lambda f: (f.priority_rank, -len(f.observation)),
    )
    winner = sorted_group[0]
    losers = sorted_group[1:]
    return winner, losers


def _absorb_losers(
    winner: Finding,
    losers: List[Finding],
    reason: str,
) -> Tuple[Finding, dict]:
    """Merge loser metadata into the winner and return a merge record.

    Frozen-dataclass-safe: builds local copies of mutable state, then calls
    ``dataclasses.replace()`` once at the end to produce the new winner.
    No in-place writes to ``winner`` — the caller's reference to the original
    instance remains valid and unchanged.
    """
    absorbed_refs: List[str] = []
    new_merged_from = list(winner.merged_from)
    new_ethics_state = winner.ethics_state
    new_source_url = winner.source_url
    new_synthesis_hint = winner.synthesis_hint

    for loser in losers:
        ref = f"{loser.cluster} F-{loser.local_index:02d}"
        absorbed_refs.append(ref)
        new_merged_from.append(ref)

        if not new_ethics_state and loser.ethics_state == "ADJACENT":
            new_ethics_state = "ADJACENT"

        if not new_source_url and loser.source_url:
            new_source_url = loser.source_url

        if not new_synthesis_hint and loser.synthesis_hint:
            new_synthesis_hint = loser.synthesis_hint

    new_winner = replace(
        winner,
        merged_from=tuple(new_merged_from),
        ethics_state=new_ethics_state,
        source_url=new_source_url,
        synthesis_hint=new_synthesis_hint,
    )

    merge_record = {
        "reason": reason,
        "kept": {
            "cluster": new_winner.cluster,
            "finding_index": new_winner.local_index,
            "section": new_winner.section,
            "element": new_winner.element_normalized,
            "priority": new_winner.priority,
        },
        "merged_from": absorbed_refs,
    }

    return new_winner, merge_record


# ---------------------------------------------------------------------------
# v2 SCOPE-aware dedup
# ---------------------------------------------------------------------------


def deduplicate_v2(findings: List[Finding]) -> DedupeResult:
    """v2 SCOPE-aware dedup.

    Routing rules:
    1. Ethics findings (``ethics_state in {BLOCK, ADJACENT}``) split off first
       and route to ``result.ethics_findings``. CLEAR ethics findings stay in
       the active pool — they are recorded for telemetry but flagged with
       ``ethics_state='CLEAR'`` for the writer's skip-by-default rendering.
    2. Page-scope findings (``scope='page'``) dedup by
       ``(baton_index, verdict)`` across device pairs. A finding emitted by
       the same specialist for both desktop and mobile collapses to one.
    3. Device-scope findings (``scope='device'``) dedup by
       ``(device, baton_index, verdict)`` within their own device.
    4. Cross-cluster same-``baton_index`` collisions: KEEP both unless they
       share ``(surface, verdict)`` — that's structural identity. Merge with
       highest ``evidence_tier`` wins.

    Returns a DedupeResult with ``kept``, ``ethics_findings``,
    ``auto_merged``, and ``synthesis_groups`` populated. Pass findings are
    expected to be in the input ``findings`` list with ``verdict='PASS'`` and
    are passed through to ``kept`` unchanged (v2 PASS findings are first-class
    Finding objects, not the v1 PassFinding shape).
    """
    result = DedupeResult()

    # Split ethics BLOCK/ADJACENT off; keep CLEAR in the active pool
    ethics: List[Finding] = []
    active: List[Finding] = []
    for f in findings:
        if f.cluster == "ethics" and f.ethics_state in ("BLOCK", "ADJACENT"):
            ethics.append(f)
        else:
            active.append(f)

    # Sort ethics deterministically: BLOCK before ADJACENT, then cluster, then local_index
    ethics_sorted = sorted(
        ethics,
        key=lambda f: (0 if f.ethics_state == "BLOCK" else 1, f.cluster, f.local_index),
    )
    result.ethics_findings = ethics_sorted

    # ----- Layer 1: page-scope dedup across devices -----
    page_findings = [f for f in active if f.scope == "page"]
    device_findings = [f for f in active if f.scope != "page"]

    page_kept, page_merged = _v2_layer_page_scope(page_findings)
    result.auto_merged.extend(page_merged)

    # ----- Layer 2: device-scope dedup within each device -----
    device_kept, device_merged = _v2_layer_device_scope(device_findings)
    result.auto_merged.extend(device_merged)

    # ----- Layer 3: cross-cluster same-baton_index, same-(surface, verdict) merge -----
    combined = page_kept + device_kept
    combined, cross_merged = _v2_layer_cross_cluster_structural(combined)
    result.auto_merged.extend(cross_merged)

    # Stable sort: priority_rank, cluster, local_index (sorted iteration for determinism)
    combined_sorted = sorted(combined, key=lambda f: (f.priority_rank, f.cluster, f.local_index))
    result.kept = combined_sorted

    return result


def _v2_layer_page_scope(
    findings: List[Finding],
) -> Tuple[List[Finding], List[dict]]:
    """Page-scope findings collapse across device pairs (within the same cluster).

    Dedup key: ``(cluster, baton_index, verdict)`` — same specialist emitting
    the same finding for both devices. Cluster is part of the key so that
    cross-cluster findings (visual-cta vs pricing on the same element) survive
    this layer and get evaluated by the cross-cluster structural layer.
    Highest-tier wins.

    **'absent' baton_index findings are passed through unchanged.** Two
    findings with baton_index='absent' typically refer to different missing
    things (no JSON-LD vs no OG image) — collapsing them on baton_index would
    erase distinct content. The cross-cluster structural layer makes its own
    pass with surface as the discriminator for cross-cluster absent findings.
    """
    groups: Dict[Tuple[str, str, str], List[Finding]] = defaultdict(list)
    pass_through: List[Finding] = []  # 'absent' findings preserved as-is
    # Sorted iteration over input for deterministic group construction
    for f in sorted(findings, key=lambda f: (f.cluster, f.baton_index, f.verdict, f.device, f.local_index)):
        if not f.baton_index or f.baton_index == "absent":
            pass_through.append(f)
            continue
        key = (f.cluster, f.baton_index, f.verdict)
        groups[key].append(f)

    kept: List[Finding] = list(pass_through)
    merged: List[dict] = []

    # Sorted iteration over groups for deterministic output order
    for key in sorted(groups.keys()):
        group = groups[key]
        if len(group) == 1:
            kept.append(group[0])
            continue
        winner, losers = _v2_pick_winner_by_tier(group)
        winner, record = _absorb_losers(
            winner, losers,
            reason=(
                f"page-scope merge: cluster={key[0]} baton_index={key[1]} verdict={key[2]}"
            ),
        )
        kept.append(winner)
        merged.append(record)

    return kept, merged


def _v2_layer_device_scope(
    findings: List[Finding],
) -> Tuple[List[Finding], List[dict]]:
    """Device-scope findings dedup within their own (cluster, device) pair only.

    Dedup key: ``(cluster, device, baton_index, verdict)``. Cluster is part of
    the key so cross-cluster findings (different specialist lens on the same
    element) survive to the cross-cluster structural layer.

    **'absent' baton_index findings are passed through unchanged** — same
    rationale as the page-scope layer.
    """
    groups: Dict[Tuple[str, str, str, str], List[Finding]] = defaultdict(list)
    pass_through: List[Finding] = []
    for f in sorted(findings, key=lambda f: (f.cluster, f.device, f.baton_index, f.verdict, f.local_index)):
        if not f.baton_index or f.baton_index == "absent":
            pass_through.append(f)
            continue
        key = (f.cluster, f.device, f.baton_index, f.verdict)
        groups[key].append(f)

    kept: List[Finding] = list(pass_through)
    merged: List[dict] = []

    for key in sorted(groups.keys()):
        group = groups[key]
        if len(group) == 1:
            kept.append(group[0])
            continue
        winner, losers = _v2_pick_winner_by_tier(group)
        winner, record = _absorb_losers(
            winner, losers,
            reason=(
                f"device-scope merge: cluster={key[0]} device={key[1]} "
                f"baton_index={key[2]} verdict={key[3]}"
            ),
        )
        kept.append(winner)
        merged.append(record)

    return kept, merged


def _v2_layer_cross_cluster_structural(
    findings: List[Finding],
) -> Tuple[List[Finding], List[dict]]:
    """Cross-cluster same-(baton_index, surface, verdict) is structural identity.

    KEEP both findings unless their ``(surface, verdict)`` matches AND
    ``baton_index`` matches — that's structural identity (same element, same
    surface assertion, same verdict, just different cluster lenses), merge
    with highest evidence_tier winning.

    Same baton_index but different ``(surface, verdict)`` is two specialists
    looking at the same element from different angles → keep both. The
    synthesizer integrates in Layer 3.
    """
    groups: Dict[Tuple[str, str, str, str], List[Finding]] = defaultdict(list)
    for f in sorted(findings, key=lambda f: (f.baton_index, f.surface, f.verdict, f.device, f.cluster, f.local_index)):
        if not f.baton_index or f.baton_index == "absent":
            # 'absent' baton_index findings can't dedup structurally — preserve all
            groups[(f"_absent_{id(f)}", "", "", "")].append(f)
            continue
        key = (f.baton_index, f.surface, f.verdict, f.device)
        groups[key].append(f)

    kept: List[Finding] = []
    merged: List[dict] = []

    for key in sorted(groups.keys()):
        group = groups[key]
        if len(group) == 1:
            kept.append(group[0])
            continue
        # Multiple cross-cluster findings on same (baton_index, surface, verdict, device)
        winner, losers = _v2_pick_winner_by_tier(group)
        winner, record = _absorb_losers(
            winner, losers,
            reason=f"cross-cluster structural merge: baton_index={key[0]} surface={key[1]} verdict={key[2]} device={key[3]}",
        )
        kept.append(winner)
        merged.append(record)

    return kept, merged


def _v2_pick_winner_by_tier(group: List[Finding]) -> Tuple[Finding, List[Finding]]:
    """Pick winner: highest evidence_tier, then severity, then confidence, then stable.

    Stable order: cluster slug ascending, local_index ascending. Ensures
    determinism: same input findings produce same winner across runs.
    """
    sorted_group = sorted(
        group,
        key=lambda f: (
            -EVIDENCE_TIER_RANK.get(f.tier, 0),  # higher tier first
            f.priority_rank,                      # CRITICAL=0 first
            -(f.confidence or 0.0),               # higher confidence first
            f.cluster,                            # stable
            f.local_index,                        # stable
        ),
    )
    winner = sorted_group[0]
    losers = sorted_group[1:]
    return winner, losers
