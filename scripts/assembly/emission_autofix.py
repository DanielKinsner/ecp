"""Pre-validation autofix for cluster + ethics emissions (G15 P1-3).

The specialist subagents that emit cluster-emission-v1.json and
ethics-findings.json bounce on a small set of known shape traps that
appear across runs. Each bounce costs a retry dispatch + lead nudge +
~30-90s of wall-clock. Three live runs on the same URL
(``docs/ecp/2026-05-27-{b0051311,af72a2ae,52f53a53}``) catalogued the
exact shapes:

- ``telemetry.reference_files_read`` entries prefixed with
  ``references/`` (specialist quoted the path verbatim instead of the
  bare filename the schema expects).
- Duplicate ``(surface, baton_index, verdict)`` tuples — the specialist
  emitted two findings about the same surface/element/verdict triple
  (e.g., two "global-nav / e7 / FAIL" entries).
- ``proposed_anchor.reason`` over the 200-character schema cap.

This module applies semantically-conservative repairs to these specific
failure modes without changing the actual finding content. The lead
runs autofix BEFORE the schema validator; anything autofix can't
repair (out-of-enum verdicts, missing required prose, etc.) still
bounces the specialist as before.

The autofix's repair log is the audit trail: every change is recorded
with ``{finding_local_id, field, before, after, why}`` so the operator
can verify nothing material was rewritten. An empty repairs list means
the emission was already clean — autofix is idempotent.

Authored G15 P1-3 (2026-05-27); shrunk 2026-06-10 when the §4.2 (v1.2)
operationalization made ``proposed_anchor`` an OPTIONAL editor hint
instead of a schema-required placement directive — the default-anchor
injection (former repair 4) was the chief source of wrong-placed absent
hotspots and was removed; absent findings now ship without a
``proposed_anchor`` and the renderer leaves them blank for the operator.
"""
from __future__ import annotations

import copy
from typing import Any


# Schema cap for proposed_anchor.reason. The synthesizer prompt already
# tells specialists to keep this under 200 chars; the autofix is the
# safety net for when the specialist exceeds it anyway.
PROPOSED_ANCHOR_REASON_MAX_LEN = 200


def autofix_emission(emission: dict) -> tuple[dict, list[dict]]:
    """Apply pre-validation autofix repairs to a cluster/ethics emission.

    Returns ``(fixed_emission, repairs)`` where ``fixed_emission`` is a
    deep copy with repairs applied and ``repairs`` is a list of records
    describing every change. ``fixed_emission == emission`` is **not**
    guaranteed by Python equality; use the repairs list (empty = no
    change) as the source of truth for "was anything repaired?".

    Repairs applied (each one independent — running them in any order
    produces the same result; autofix runs them in the order listed):

    1. **Path-form telemetry strip.** ``telemetry.reference_files_read``
       entries that start with ``references/`` get the prefix stripped.
       Multi-segment paths (e.g., ``references/sub/file.md``) keep
       everything after ``references/`` — the schema expects bare
       references-relative filenames.
    2. **Duplicate finding dedup.** Findings sharing the same
       ``(surface, baton_index, verdict)`` triple are deduped; the
       earliest-occurring one wins. ``local_id`` values on survivors
       are *not* renumbered (preserving the specialist's authored
       sequence; renumbering would mask audit-trail intent).
    3. **proposed_anchor.reason cap.** Reason strings over
       ``PROPOSED_ANCHOR_REASON_MAX_LEN`` characters truncate at the
       last whole word boundary at or below the cap, with a trailing
       ``...`` ellipsis marker.

    Pre-v1.2 there was a Repair 4 that injected a default
    ``proposed_anchor`` (section_index=0, section-bottom-overlay) on
    every absent finding that omitted one — back when the schema
    required ``proposed_anchor`` for absent and the renderer
    auto-pinned a section centroid from it. After product.md §4.2 v1.2
    (rulings A1+A2), absences ship blank and ``proposed_anchor`` is an
    optional editor hint, so the injection is gone — anything that
    auto-pinned an absent finding was the chief source of
    wrong-placement violations.

    Idempotency: re-running autofix on an already-fixed emission
    produces an empty repairs list (every repair-guard short-circuits
    when the data is already correct).

    Notes on what autofix does NOT do (deliberate non-scope):

    - **No enum coercion.** ``effort.change_type`` values like
      ``"template"`` or ``"content"`` that don't match the schema enum
      are NOT mapped to nearest-valid synonyms — that risks silently
      changing the meaning of the finding. Schema validation still
      bounces these, by design.
    - **No registry reconciliation.** When ``baton_index`` resolves in
      the actual baton but not in the candidate registry, this v1 does
      not auto-flag ``intentional_outside_registry``. That repair
      requires loading the baton + registry sidecar and is a separate
      planned extension (G15 P1-3 v2).
    - **No additional-property strip.** Keys like ``template_id`` or
      ``expected_overlay`` that violate ``additionalProperties: false``
      are NOT removed — they often signal an emission-shape drift the
      specialist itself needs to learn from. The bounce-and-retry
      surfaces this for the prompt-tightening feedback loop.
    """
    fixed = copy.deepcopy(emission)
    repairs: list[dict] = []

    _repair_telemetry_paths(fixed, repairs)
    _repair_duplicate_findings(fixed, repairs)
    _repair_overlong_proposed_anchor_reasons(fixed, repairs)

    return fixed, repairs


# ---------------------------------------------------------------------------
# Repair 1 — telemetry.reference_files_read path-prefix strip
# ---------------------------------------------------------------------------


def _repair_telemetry_paths(emission: dict, repairs: list[dict]) -> None:
    telemetry = emission.get("telemetry")
    if not isinstance(telemetry, dict):
        return
    paths = telemetry.get("reference_files_read")
    if not isinstance(paths, list):
        return
    new_paths: list[str] = []
    for p in paths:
        if isinstance(p, str) and p.startswith("references/"):
            stripped = p[len("references/"):]
            new_paths.append(stripped)
            repairs.append({
                "finding_local_id": None,
                "field": "telemetry.reference_files_read[]",
                "before": p,
                "after": stripped,
                "why": (
                    "Path-form telemetry entry; the schema expects bare "
                    "references-relative filenames (e.g., 'ethics-gate.md', "
                    "not 'references/ethics-gate.md')."
                ),
            })
        else:
            new_paths.append(p)
    telemetry["reference_files_read"] = new_paths


# ---------------------------------------------------------------------------
# Repair 2 — duplicate finding dedup
# ---------------------------------------------------------------------------


def _finding_dedup_key(finding: dict) -> tuple[str, str, str] | None:
    """Key for ``(surface, baton_index, verdict)`` dedup. Returns None
    when any component is missing so the finding isn't accidentally
    deduped against another missing-key entry."""
    surface = finding.get("surface")
    verdict = finding.get("verdict")
    element = finding.get("element") or {}
    baton_index = element.get("baton_index") if isinstance(element, dict) else None
    if not (isinstance(surface, str) and isinstance(verdict, str) and isinstance(baton_index, str)):
        return None
    return (surface, baton_index, verdict)


def _repair_duplicate_findings(emission: dict, repairs: list[dict]) -> None:
    findings = emission.get("findings")
    if not isinstance(findings, list):
        return
    seen: dict[tuple[str, str, str], int] = {}
    kept: list[dict] = []
    for i, f in enumerate(findings):
        if not isinstance(f, dict):
            kept.append(f)
            continue
        key = _finding_dedup_key(f)
        if key is None:
            kept.append(f)
            continue
        if key in seen:
            repairs.append({
                "finding_local_id": f.get("local_id"),
                "field": "findings[]",
                "before": f"duplicate of local_id={findings[seen[key]].get('local_id')!r} on (surface={key[0]!r}, baton_index={key[1]!r}, verdict={key[2]!r})",
                "after": "<dropped>",
                "why": (
                    "Duplicate (surface, baton_index, verdict) tuple; "
                    "kept the earlier-occurring finding to preserve "
                    "specialist sequencing."
                ),
            })
            continue
        seen[key] = i
        kept.append(f)
    emission["findings"] = kept


# ---------------------------------------------------------------------------
# Repair 3 — proposed_anchor.reason length cap
# ---------------------------------------------------------------------------


def _truncate_at_word_boundary(text: str, max_len: int) -> str:
    """Truncate ``text`` at the last whitespace boundary at or below
    ``max_len - 3`` (room for the ``...`` marker). Falls back to a hard
    truncate at ``max_len - 3`` if no boundary exists."""
    if len(text) <= max_len:
        return text
    headroom = max_len - 3  # leave room for ellipsis marker
    if headroom <= 0:
        return text[:max_len]
    candidate = text[:headroom]
    last_space = candidate.rfind(" ")
    if last_space >= 0:
        candidate = candidate[:last_space]
    return candidate.rstrip(" .,;:") + "..."


def _repair_overlong_proposed_anchor_reasons(
    emission: dict, repairs: list[dict],
) -> None:
    findings = emission.get("findings")
    if not isinstance(findings, list):
        return
    for f in findings:
        if not isinstance(f, dict):
            continue
        pa = f.get("proposed_anchor")
        if not isinstance(pa, dict):
            continue
        reason = pa.get("reason")
        if not isinstance(reason, str):
            continue
        if len(reason) <= PROPOSED_ANCHOR_REASON_MAX_LEN:
            continue
        truncated = _truncate_at_word_boundary(reason, PROPOSED_ANCHOR_REASON_MAX_LEN)
        pa["reason"] = truncated
        repairs.append({
            "finding_local_id": f.get("local_id"),
            "field": "proposed_anchor.reason",
            "before": f"{len(reason)} chars: {reason[:80]!r}...",
            "after": f"{len(truncated)} chars: {truncated!r}",
            "why": (
                f"proposed_anchor.reason exceeds the {PROPOSED_ANCHOR_REASON_MAX_LEN}-char "
                f"schema cap; truncated at the last word boundary."
            ),
        })


__all__ = [
    "PROPOSED_ANCHOR_REASON_MAX_LEN",
    "autofix_emission",
]
