"""Pipeline orchestration primitives.

This module owns four things:

1. ``PIPELINE_STAGES`` — the canonical ordering of reconciliation +
   assembly stages. Any code that runs a stage calls ``_assert_stage(name)``
   at entry to guarantee the call order matches the declared pipeline.
   A reviewer verifies ordering by greping for ``_assert_stage`` rather
   than tracing call sites.

2. ``assign_display_indices(findings, clusters_used)`` — assigns each
   finding its final 1-based position within its cluster AFTER the
   priority-rank sort that the writer applies. Fixes C2: before this,
   ``scoring._finding_ref`` returned refs based on pre-dedup
   ``local_index``, but the renderer resolved refs by post-dedup
   displayed order. Priority Path stories could cite ``visual-cta F-04``
   and the rendered report would show a different finding at F-04.

3. ``FinalizedFindings`` — an immutable dataclass produced after
   dedup + display-index assignment. The writer accepts this container
   as input and asserts every Priority Path ``f_ref`` resolves to a
   key in its ``cluster_finding_map`` before rendering.

4. ``cross_device_title_merge`` (Phase H — 2026-04-28) — Layer-2.5
   step that catches cross-device duplicate findings whose desktop
   and mobile specialists cited different baton elements (or 'absent')
   for the same logical issue. Layer-2 dedup keys on
   (cluster, baton_index, verdict) and misses these duplicates;
   Layer-2.5 groups same-cluster findings whose titles share a
   normalized prefix. Promoted from ``.phase-b-tmp/build_canonical_f_refs.py``
   and ``scripts/report/v2_loader.build_canonical_view`` so both
   callers share one implementation. Closes the divergence-risk
   item flagged in the Phase G handoff.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace
from hashlib import sha256
from types import MappingProxyType
from typing import Iterable, List, Mapping, Sequence, Tuple

from .models import Finding

# Canonical pipeline order. Stages are (name, short description).
# Any module entering a stage calls _assert_stage(name, expected_index).
PIPELINE_STAGES: Tuple[Tuple[str, str], ...] = (
    ("parse", "Parse cluster files into Finding objects"),
    ("dedup", "Deduplicate and group findings"),
    ("assign_display_indices", "Assign post-dedup display_index per finding"),
    ("score", "Score Priority Path candidates from synthesis groups"),
    ("write_audit", "Write audit.md with optional Priority Path stories"),
    ("write_sidecars", "Emit JSON sidecars"),
)

_STAGE_NAMES = tuple(name for name, _ in PIPELINE_STAGES)


def _assert_stage(name: str, expected_index: int) -> None:
    """Raise if ``name`` is not the stage at ``expected_index``.

    Lets every stage entry declare where it fits in the pipeline so a
    reviewer can verify ordering with ``grep _assert_stage scripts/``
    rather than tracing callers.
    """
    if expected_index < 0 or expected_index >= len(PIPELINE_STAGES):
        raise AssertionError(
            f"_assert_stage: expected_index={expected_index} out of range "
            f"for PIPELINE_STAGES (0..{len(PIPELINE_STAGES) - 1})"
        )
    actual_name = _STAGE_NAMES[expected_index]
    if actual_name != name:
        raise AssertionError(
            f"_assert_stage: stage mismatch at index {expected_index}: "
            f"declared {name!r}, canonical {actual_name!r}"
        )


def _content_hash_for_finding(f: Finding) -> int:
    """Phase L: Content-derived F-NN hash for a finding.

    Maps (surface, baton_index, verdict) to an integer in [1, 99]. The same
    conceptual finding (same tuple) gets the same F-NN across runs, which is
    the point — order-based numbering produced positional coincidence that
    inflated TARr metrics.

    Title is deliberately excluded from the hash because specialists rephrase
    titles creatively per run; including title would defeat content stability.

    Mod 99 + 1 produces values 1..99. With <50 findings per audit (operator-
    confirmed), per-cluster collision risk is low; collisions are resolved by
    deterministic linear probing in ``assign_display_indices``.
    """
    surface = (f.surface or "unknown").lower().strip()
    baton = f.baton_index or "absent"
    verdict = (f.verdict or "?").upper()
    key = f"{surface}|{baton}|{verdict}".encode()
    return int(sha256(key).hexdigest()[:6], 16) % 99 + 1


def assign_display_indices(
    findings: Sequence[Finding],
    clusters_used: Sequence[str],
) -> List[Finding]:
    """Sort findings the same way the writer will render them and tag each
    with a content-derived ``display_index`` within its cluster.

    The writer's render order is:

    1. Group by cluster, preserving ``clusters_used`` order (orphan clusters
       appended at the end).
    2. Within each cluster, sort by ``(priority_rank, local_index)``.

    The display_index VALUE is content-derived (Phase L, 2026-04-29):
    ``F-{NN}`` where NN = ``sha256(surface|baton_index|verdict)[:6] mod 99 + 1``.
    Same conceptual finding → same F-NN across runs, eliminating the positional
    coincidence that inflated TARr metrics under the prior order-based scheme.
    Collisions within a cluster are resolved by deterministic linear probing
    after sorting by (hash, title, local_index).

    After calling this function, every finding's ``display_index`` is set to a
    content-derived integer in [1, 99]. ``scoring._finding_ref`` reads
    ``display_index`` if nonzero. Render order is still priority-based — only
    the display_index VALUES changed.

    Returns the same findings in the priority-sorted order the writer will use,
    so callers can pass the result forward without re-sorting.
    """
    _assert_stage("assign_display_indices", 2)

    # Group by cluster, preserving clusters_used order
    cluster_order = list(clusters_used)
    seen = set(cluster_order)
    by_cluster: dict[str, List[Finding]] = {c: [] for c in cluster_order}
    orphans: List[str] = []

    for f in findings:
        if f.cluster not in by_cluster:
            by_cluster[f.cluster] = []
            if f.cluster not in seen:
                orphans.append(f.cluster)
                seen.add(f.cluster)
        by_cluster[f.cluster].append(f)

    final_order: List[str] = cluster_order + orphans

    ordered: List[Finding] = []
    for cluster in final_order:
        bucket = by_cluster.get(cluster, [])

        # Phase 1: assign content-based display_index per finding within this
        # cluster, with deterministic collision resolution (linear probe after
        # sorting by (hash, title, local_index) so collisions resolve the same
        # way across runs when specialist labels are stable).
        sorted_for_hashing = sorted(
            bucket,
            key=lambda f: (_content_hash_for_finding(f), f.title or "", f.local_index),
        )
        used: set[int] = set()
        index_for_finding: dict[int, int] = {}  # id(f) -> assigned display_index
        for f in sorted_for_hashing:
            h = _content_hash_for_finding(f)
            attempts = 0
            while h in used and attempts < 99:
                h = (h % 99) + 1
                attempts += 1
            if h in used:
                # Cluster has >99 findings (extremely unlikely; operator-confirmed
                # <50 total per audit). Fall back to first unused slot.
                for candidate in range(1, 100):
                    if candidate not in used:
                        h = candidate
                        break
            used.add(h)
            index_for_finding[id(f)] = h

        # Phase 2: emit findings in PRIORITY order (writer expects this) but
        # with the content-derived display_index values from phase 1.
        bucket.sort(key=lambda f: (f.priority_rank, f.local_index))
        for f in bucket:
            ordered.append(replace(f, display_index=index_for_finding[id(f)]))

    return ordered


def build_cluster_finding_map(
    findings: Iterable[Finding],
) -> Mapping[str, Tuple[int, ...]]:
    """Return an immutable map of cluster -> tuple of display indices.

    Consumers (writer, synthesizer_parser.validate_stories) use this to
    verify every ``"{cluster} F-{NN}"`` reference resolves to a real
    finding. Wrapped in ``MappingProxyType`` so it cannot be mutated
    after construction.
    """
    raw: dict[str, List[int]] = {}
    for f in findings:
        if f.display_index <= 0:
            raise AssertionError(
                f"build_cluster_finding_map: finding in cluster {f.cluster!r} "
                f"has no display_index — assign_display_indices must run first"
            )
        raw.setdefault(f.cluster, []).append(f.display_index)

    frozen = {cluster: tuple(sorted(indices)) for cluster, indices in raw.items()}
    return MappingProxyType(frozen)


@dataclass(frozen=True)
class FinalizedFindings:
    """Immutable post-dedup + display-index-assigned finding container.

    The writer consumes this. Priority Path stories are validated
    against ``cluster_finding_map`` before rendering; any story citing
    a ``f_ref`` not in the map triggers an ERROR render rather than a
    broken anchor.
    """

    findings: Tuple[Finding, ...]
    cluster_finding_map: Mapping[str, Tuple[int, ...]]

    @classmethod
    def build(
        cls,
        findings: Sequence[Finding],
        clusters_used: Sequence[str],
    ) -> "FinalizedFindings":
        ordered = assign_display_indices(findings, clusters_used)
        return cls(
            findings=tuple(ordered),
            cluster_finding_map=build_cluster_finding_map(ordered),
        )

    def valid_refs(self) -> set[str]:
        """Return the flat set of ``"{cluster} F-{NN}"`` strings the synthesizer
        is allowed to cite."""
        refs: set[str] = set()
        for cluster, indices in self.cluster_finding_map.items():
            for idx in indices:
                refs.add(f"{cluster} F-{idx:02d}")
        return refs


# ---------------------------------------------------------------------------
# Layer-2.5 cross-device duplicate merge (Phase H promotion)
# ---------------------------------------------------------------------------


_SEVERITY_RANK: Mapping[str, int] = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
}


def normalize_finding_title(title: str) -> str:
    """Title-normalization for cross-device duplicate detection.

    Strategy:

    1. Lowercase and strip leading/trailing whitespace.
    2. If the title contains an em-dash (``—``), space-padded hyphen
       (`` - ``), space-padded colon (`` : ``), or space-padded pipe
       (`` | ``), keep only the FIRST clause before that separator —
       specialists frequently extend titles with the same prefix and
       different suffixes ("...Image — Missing fetchpriority and Preload"
       vs "...Image — Missing fetchpriority='high' Attribute"); merging
       on the prefix collapses the duplicate.
    3. Collapse interior whitespace to single spaces.

    Examples:

    >>> normalize_finding_title("Hero Product Image Missing fetchpriority")
    'hero product image missing fetchpriority'
    >>> normalize_finding_title("Hero Product Image — Missing fetchpriority='high' Attribute")
    'hero product image'
    >>> normalize_finding_title("  No  MSRP  Anchor  ")
    'no msrp anchor'
    """
    t = title.lower().strip()
    for sep in ("—", " - ", " : ", " | "):
        if sep in t:
            t = t.split(sep)[0].strip()
            break
    return " ".join(t.split())


def _has_key(raw_by_ref: Mapping[str, dict], key: str) -> bool:
    """True if any ref's metadata dict contains ``key``."""
    return any(key in meta for meta in raw_by_ref.values())


def cross_device_title_merge(
    raw_by_ref: Mapping[str, dict],
) -> Tuple[dict[str, dict], dict[str, str]]:
    """Merge cross-device duplicate findings within each cluster (Layer 2.5).

    The Layer-2 dedup engine (``scripts.assembly.dedup.deduplicate_v2``)
    keys on ``(cluster, baton_index, verdict)`` and misses cross-device
    duplicates when desktop and mobile specialists cite different baton
    elements (or one cites a real element and the other ``"absent"``)
    for the same logical issue. This Layer-2.5 step groups same-cluster
    findings whose normalized titles share a prefix and collapses each
    group into the lowest-numbered F-NN.

    On slingmods (2026-04-28) this absorbed 14 of 100 raw refs into 86
    canonical refs.

    Args:
        raw_by_ref: mapping from ``"{cluster} F-{NN}"`` to a finding-metadata
            dict. Required keys: ``title``. Optional keys (merged when
            present in the input):

            ============================  ==========================================
            Key                           Merge behavior
            ============================  ==========================================
            ``scope``                     ``'page'`` wins across the group
            ``devices_present``           Set-union (sorted) across the group
            ``severity``                  Highest in
                                          ``{CRITICAL, HIGH, MEDIUM, LOW}``
            ``baton_index`` + ``device``  Map produced as
                                          ``baton_index_by_device``
            ``evidence_anchors``          Deduplicated by
                                          ``(type, reference)``
            ``reference_citations``       Deduplicated by ``(section, url)``
            ============================  ==========================================

            Other keys: preserved on the canonical winner only.

    Returns:
        ``(by_canonical_ref, merge_aliases)``:

        * ``by_canonical_ref``: dict mapping canonical ref ->
          merged metadata. Each canonical ref is the lowest-numbered
          F-NN within its ``(cluster, normalized_title)`` group.
        * ``merge_aliases``: dict mapping each absorbed (non-canonical)
          ref -> its canonical ref. Useful for downstream code that
          rewrites references in priority_path / manifests.

    Singletons (groups of size 1) appear in ``by_canonical_ref`` with
    no entry in ``merge_aliases``.
    """
    if not raw_by_ref:
        return {}, {}

    has_evidence_anchors = _has_key(raw_by_ref, "evidence_anchors")
    has_reference_citations = _has_key(raw_by_ref, "reference_citations")
    has_baton_index = _has_key(raw_by_ref, "baton_index")
    has_severity = _has_key(raw_by_ref, "severity")
    has_devices_present = _has_key(raw_by_ref, "devices_present")
    has_scope = _has_key(raw_by_ref, "scope")
    has_visual_evidence = _has_key(raw_by_ref, "visual_evidence")

    refs_by_cluster: dict[str, list[str]] = defaultdict(list)
    for ref in raw_by_ref:
        cluster = ref.rsplit(" F-", 1)[0]
        refs_by_cluster[cluster].append(ref)

    by_canonical_ref: dict[str, dict] = {}
    merge_aliases: dict[str, str] = {}

    for cluster, refs in refs_by_cluster.items():
        by_norm: dict[str, list[str]] = defaultdict(list)
        for ref in refs:
            norm = normalize_finding_title(raw_by_ref[ref].get("title", ""))
            by_norm[norm].append(ref)

        for _norm, group_refs in by_norm.items():
            group_sorted = sorted(
                group_refs, key=lambda r: int(r.rsplit(" F-", 1)[1])
            )
            canonical = group_sorted[0]
            canonical_meta = dict(raw_by_ref[canonical])

            merged_devices: set[str] = set()
            scope_page = False
            severities: list[str] = []
            anchors_merged: list[dict] = []
            seen_anchors: set[tuple] = set()
            refs_merged: list[dict] = []
            seen_refs: set[tuple] = set()
            baton_by_dev: dict[str, str] = {}
            # Phase 4a hardening 3 (2026-05-18) — accumulate visual_evidence
            # by device so cross-device merged findings can return the
            # CORRECT device's observed_anchor.baton_index. Pre-fix,
            # visual_evidence was preserved only on the canonical winner;
            # load_v2_findings then handed mobile renderings the desktop
            # winner's visual_evidence with desktop's e_index inside
            # observed_anchor, while the top-level baton_index correctly
            # came from baton_index_by_device. Closes Codex 2026-05-18
            # review of 50e1d94 (cross-device merge bug).
            visual_evidence_by_dev: dict[str, dict] = {}

            for r in group_sorted:
                meta = raw_by_ref[r]
                if has_devices_present:
                    merged_devices.update(meta.get("devices_present") or [])
                if has_scope and meta.get("scope") == "page":
                    scope_page = True
                if has_severity and meta.get("severity"):
                    severities.append(meta["severity"])
                if has_baton_index:
                    bi = meta.get("baton_index")
                    dev = meta.get("device")
                    if bi and dev:
                        baton_by_dev[dev] = bi
                if has_evidence_anchors:
                    for ea in meta.get("evidence_anchors") or []:
                        key = (ea.get("type"), ea.get("reference"))
                        if key not in seen_anchors:
                            seen_anchors.add(key)
                            anchors_merged.append(ea)
                if has_reference_citations:
                    for rc in meta.get("reference_citations") or []:
                        key = (rc.get("section"), rc.get("url"))
                        if key not in seen_refs:
                            seen_refs.add(key)
                            refs_merged.append(rc)
                if has_visual_evidence:
                    ve = meta.get("visual_evidence")
                    dev = meta.get("device")
                    if isinstance(ve, dict) and dev:
                        # Earlier members of the group (lower F-NN) win
                        # ties within the same device — matches the
                        # canonical-winner-first ordering above.
                        visual_evidence_by_dev.setdefault(dev, ve)

            if has_scope:
                canonical_meta["scope"] = (
                    "page" if scope_page else canonical_meta.get("scope", "device")
                )
            if has_devices_present:
                canonical_meta["devices_present"] = sorted(merged_devices)
            if has_severity and severities:
                canonical_meta["severity"] = min(
                    severities, key=lambda s: _SEVERITY_RANK.get(s, 9)
                )
            if has_baton_index:
                canonical_meta["baton_index_by_device"] = baton_by_dev
            if has_evidence_anchors:
                canonical_meta["evidence_anchors"] = anchors_merged
            if has_reference_citations:
                canonical_meta["reference_citations"] = refs_merged
            if has_visual_evidence:
                # canonical_meta["visual_evidence"] (the canonical
                # winner's value) is the fallback for legacy / single-
                # device readers. visual_evidence_by_device is what
                # device-aware readers (load_v2_findings) should consult.
                canonical_meta["visual_evidence_by_device"] = visual_evidence_by_dev

            by_canonical_ref[canonical] = canonical_meta

            for absorbed in group_sorted[1:]:
                merge_aliases[absorbed] = canonical

    return by_canonical_ref, merge_aliases
