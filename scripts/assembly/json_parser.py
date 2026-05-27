"""v2 JSON-emission parser for the ECP Audit Assembly package.

Reads ``cluster-emission-v1.json`` files written by Layer 1 specialists, validates
against the canonical schema (with cross-file ``$ref`` resolution via
``referencing.Registry``), and converts emissions into ``Finding`` dataclass
instances ready for Layer 2 dedup/scoring.

v1 ``parser.py`` (regex-based markdown parser) stays as the v1 engagement path
per Kieran's no-touch rule. v2 engagements call ``parse_emission_file`` here.

Design notes:
- Validators are compiled once at module load. ``referencing.Registry`` resolves
  the ``finding-v1.json`` $ref from ``cluster-emission-v1.json`` against an
  in-memory mapping — no network fetch, by design (offline-only behavior is
  the v2 invariant).
- ``ValidationError.absolute_path`` is preserved on raised
  ``EmissionValidationError`` so the lead's retry-prompt construction can
  cite the exact field that failed.
- ``parse_emission_file`` returns the wrapper ``EmissionParseResult`` so the
  caller can distinguish:
    - ``status='complete' | 'partial'`` with ``findings`` populated
    - ``status='skipped'`` with ``skip_reason`` and empty ``findings``

Authored 2026-04-27 as Phase E.2 deliverable. See:
- schema/cluster-emission-v1.json
- schema/finding-v1.json
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError, best_match
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from .models import EVIDENCE_TIER_RANK, EvidenceAnchor, Finding, PRIORITY_ORDER, ProposedAnchor

# ---------------------------------------------------------------------------
# Schema loading + validator compilation (module-load, run once)
# ---------------------------------------------------------------------------

_SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "schema"
_FINDING_SCHEMA_PATH = _SCHEMA_DIR / "finding-v1.json"
_CLUSTER_SCHEMA_PATH = _SCHEMA_DIR / "cluster-emission-v1.json"


def _load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_validator() -> Draft202012Validator:
    finding_schema = _load_schema(_FINDING_SCHEMA_PATH)
    cluster_schema = _load_schema(_CLUSTER_SCHEMA_PATH)

    finding_resource = Resource.from_contents(finding_schema, default_specification=DRAFT202012)
    cluster_resource = Resource.from_contents(cluster_schema, default_specification=DRAFT202012)
    registry = Registry().with_resources(
        [
            ("https://ecp.local/schema/finding-v1.json", finding_resource),
            ("https://ecp.local/schema/cluster-emission-v1.json", cluster_resource),
        ]
    )
    Draft202012Validator.check_schema(cluster_schema)
    return Draft202012Validator(
        cluster_schema,
        registry=registry,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )


_VALIDATOR = _build_validator()


def get_validator() -> Draft202012Validator:
    """Return the module-level Draft202012Validator built against
    ``schema/cluster-emission-v1.json`` + ``schema/finding-v1.json``.

    G16 Layer 3 (2026-05-27): exposed as the single source of truth
    for cluster/ethics emission validation so ``test-specialist.py
    validate`` and ``build_canonical_view`` agree by construction.
    Pre-G16-Layer-3, ``scripts/test-specialist.py:_load_schemas`` built
    a duplicate validator instance from the same schema files — the
    code was byte-equivalent but two copies risk drifting under future
    edits. Both callers now share this one instance.
    """
    return _VALIDATOR


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EmissionValidationError(Exception):
    """Raised when a specialist emission fails JSON Schema validation.

    Carries the structured error list so the lead's retry-prompt construction
    can cite specific fields. ``best_error`` is the highest-relevance single
    error (per ``jsonschema.exceptions.best_match``); ``all_errors`` is the
    flat list useful for surfacing "N errors total" to the operator.
    """

    emission_path: str
    best_error_path: str
    best_error_message: str
    all_errors: tuple[tuple[str, str], ...]  # (path, message) pairs

    def __str__(self) -> str:
        return f"{self.emission_path}: {self.best_error_path}: {self.best_error_message}"


@dataclass(frozen=True)
class EmissionParseResult:
    """Output of ``parse_emission_file``.

    Frozen so the caller can pass it forward through the pipeline without
    worrying about downstream mutations.
    """

    schema_version: int
    engagement_id: str
    cluster: str
    device: str
    status: str  # complete | partial | skipped
    skip_reason: str  # populated when status='skipped'
    findings: tuple[Finding, ...]
    notes: tuple[str, ...]
    raw: dict  # original parsed JSON for downstream consumers (synthesizer, telemetry)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_emission_payload(payload: dict, *, source_path: str = "<payload>") -> None:
    """Validate a parsed emission dict against cluster-emission-v1.json.

    Raises ``EmissionValidationError`` on failure with structured error data.
    Returns None on success.
    """
    errors = sorted(_VALIDATOR.iter_errors(payload), key=lambda e: list(e.absolute_path))
    if not errors:
        return
    best = best_match(iter(errors))
    all_errors = tuple(
        (".".join(str(p) for p in e.absolute_path), e.message) for e in errors
    )
    raise EmissionValidationError(
        emission_path=source_path,
        best_error_path=".".join(str(p) for p in best.absolute_path),
        best_error_message=best.message,
        all_errors=all_errors,
    )


def parse_emission_file(
    path: Path | str,
    *,
    anchor_candidates_sidecar: dict | None = None,
) -> EmissionParseResult:
    """Parse and validate a cluster-emission-v1.json file.

    Pipeline:
    1. Read file, parse JSON.
    2. (Phase 4a hardening) If ``anchor_candidates_sidecar`` is provided,
       resolve any ``visual_evidence.observed_anchor.candidate_id`` into
       canonical ``element.baton_index`` by looking up the
       ``candidate_to_e_index`` map. This runs BEFORE schema validation so
       resolved findings validate cleanly even when the specialist cited
       only candidate_id.
    3. Validate against cluster-emission-v1.json (raises EmissionValidationError on failure).
    4. Convert each finding object into a frozen ``Finding`` dataclass instance.
    5. Return a frozen ``EmissionParseResult`` with the structured findings.

    The caller gates on ``result.status``:
    - ``complete`` / ``partial``: process ``result.findings`` into the dedup pipeline
    - ``skipped``: log ``result.skip_reason`` and emit zero findings to the audit

    Args:
        path: path to the cluster-emission JSON file.
        anchor_candidates_sidecar: optional anchor-candidates-{device}.json
            payload (already loaded). When provided, candidate_id references
            in observed_anchor are resolved to canonical baton_index. When
            None, findings are passed through unchanged (legacy path).
    """
    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))

    if anchor_candidates_sidecar is not None:
        # Lazy import to avoid pulling assembly.anchor_candidates into the
        # critical schema-validation path when no sidecar is provided.
        from .anchor_candidates import resolve_candidate_ids_in_emission
        payload, _resolution_log = resolve_candidate_ids_in_emission(
            payload, anchor_candidates_sidecar,
        )

    validate_emission_payload(payload, source_path=str(path))

    findings: List[Finding] = []
    cluster = payload["cluster"]
    device = payload["device"]
    for f_dict in payload.get("findings", []):
        findings.append(_finding_from_dict(f_dict))

    return EmissionParseResult(
        schema_version=int(payload["schema_version"]),
        engagement_id=str(payload["engagement_id"]),
        cluster=cluster,
        device=device,
        status=payload.get("status", "complete"),
        skip_reason=payload.get("skip_reason", ""),
        findings=tuple(findings),
        notes=tuple(payload.get("notes") or []),
        raw=payload,
    )


def parse_emission_files(
    paths: list[Path | str],
    *,
    anchor_candidates_sidecars: dict[str, dict | None] | None = None,
) -> list[EmissionParseResult]:
    """Parse multiple emission files in deterministic order (sorted by path).

    Used by the pipeline orchestrator to build the union of findings across
    all dispatched specialists for a given engagement.

    Phase 4a hardening (2026-05-18): ``anchor_candidates_sidecars`` is a
    ``{device: sidecar_dict | None}`` map. For each path, the helper
    picks the sidecar by matching ``-{device}.json`` in the filename
    suffix; ethics-findings.json falls back to ``"page"`` then
    ``"desktop"``. When the map is None, no resolution happens (legacy
    behavior preserved for callers that haven't adopted Phase 4a).
    """
    sorted_paths = sorted(Path(p) for p in paths)
    if anchor_candidates_sidecars is None:
        return [parse_emission_file(p) for p in sorted_paths]

    sidecars = anchor_candidates_sidecars
    out: list[EmissionParseResult] = []
    for p in sorted_paths:
        sc: dict | None = None
        name = p.name
        for dev in ("desktop", "mobile", "laptop"):
            if f"-{dev}.json" in name and sidecars.get(dev) is not None:
                sc = sidecars[dev]
                break
        if sc is None and name == "ethics-findings.json":
            sc = sidecars.get("page") or sidecars.get("desktop")
        out.append(parse_emission_file(p, anchor_candidates_sidecar=sc))
    return out


# ---------------------------------------------------------------------------
# Retry prompt construction
# ---------------------------------------------------------------------------


def build_retry_prompt(
    emission_path: str,
    cluster: str,
    device: str,
    error: EmissionValidationError,
) -> str:
    """Build a retry prompt string the lead embeds on re-dispatch.

    Cites the specific path and message from ``best_match`` so the specialist
    can fix the field rather than re-generating from scratch. Lists all errors
    inline up to a soft cap so the specialist sees the full picture.
    """
    lines = [
        f"Your previous emission for cluster={cluster!r} device={device!r} failed schema validation.",
        f"File: {emission_path}",
        "",
        f"Primary error (jsonschema.best_match): {error.best_error_path}: {error.best_error_message}",
        "",
        "All errors:",
    ]
    for path, msg in error.all_errors[:24]:
        lines.append(f"- {path}: {msg}")
    if len(error.all_errors) > 24:
        lines.append(f"- ... and {len(error.all_errors) - 24} more")
    lines += [
        "",
        "Re-emit a single JSON object validating against schema/cluster-emission-v1.json.",
        "Address the errors above directly — do not regenerate from scratch.",
        "No prose, no markdown fences, no preamble.",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Internal: finding dict -> Finding dataclass
# ---------------------------------------------------------------------------


def _finding_from_dict(d: dict) -> Finding:
    """Convert a single finding object from cluster-emission-v1.json into a Finding.

    Maps v2 field names to the migrated dataclass shape:
    - ``element.baton_index`` → ``baton_index``
    - ``element.text_content`` → ``element`` (preserves v1 element field semantics)
    - ``effort.change_type`` / ``change_scope`` → top-level fields
    - ``evidence_anchors[]`` → tuple of frozen ``EvidenceAnchor`` instances
    - ``severity`` → ``priority`` (v1 used PRIORITY, v2 uses severity; same enum)
    - ``reference_citations`` → first-citation reference + tier (v1 had only one)
    """
    cluster = d["cluster"]
    device = d["device"]
    severity = d.get("severity", "")
    priority_rank = PRIORITY_ORDER.get(severity, len(PRIORITY_ORDER))

    element_obj = d.get("element") or {}
    baton_index = element_obj.get("baton_index", "")
    element_text = element_obj.get("text_content", "")

    effort = d.get("effort") or {}

    cites = d.get("reference_citations") or []
    primary_ref = ""
    primary_tier = d.get("evidence_tier", "")
    if cites:
        first = cites[0]
        ref_parts = [first.get("source", "")]
        if first.get("section"):
            ref_parts.append(first["section"])
        elif first.get("line"):
            ref_parts.append(f"line {first['line']}")
        primary_ref = ":".join(p for p in ref_parts if p)

    anchors = []
    for a in d.get("evidence_anchors") or []:
        anchors.append(
            EvidenceAnchor(
                type=a.get("type", ""),
                reference=a.get("reference", ""),
                scroll_y=a.get("scroll_y"),
                viewport=a.get("viewport", ""),
                context=a.get("context", ""),
            )
        )
    # Sort anchors deterministically so byte-identical output across runs
    anchors_sorted = tuple(sorted(anchors, key=lambda a: a.sort_key()))

    pa_raw = d.get("proposed_anchor")
    proposed_anchor = None
    if isinstance(pa_raw, dict) and pa_raw.get("kind"):
        proposed_anchor = ProposedAnchor(
            kind=pa_raw.get("kind", ""),
            placement=pa_raw.get("placement", ""),
            viewport=pa_raw.get("viewport", ""),
            element_baton_index=pa_raw.get("element_baton_index", ""),
            section_index=pa_raw.get("section_index"),
            viewport_trigger=pa_raw.get("viewport_trigger", ""),
            reason=pa_raw.get("reason", ""),
        )

    surface = d.get("surface", "")
    # v1 element/section semantics: section ~= surface, element ~= element.text_content
    # v1 element_normalized derived from element string for v1 dedup compatibility.
    section = surface
    element_str = element_text or baton_index
    element_normalized = Finding.normalize_element(element_str) if element_str else ""

    # Phase 4a hardening (2026-05-18) — preserve producer-authored
    # visual_evidence so it survives the parse pipeline. Without this
    # the field landed on the raw JSON, was schema-validated, then
    # silently dropped when the Finding dataclass was constructed.
    # Producer-authored visual_evidence is the FIRST priority signal
    # for hotspot rendering (see scripts/report/visual_evidence.py
    # derive_visual_evidence rule 1).
    ve_raw = d.get("visual_evidence")
    visual_evidence: dict | None = ve_raw if isinstance(ve_raw, dict) else None

    return Finding(
        cluster=cluster,
        device=device,
        local_index=int(d.get("local_id", 0)),
        verdict=d.get("verdict", ""),
        section=section,
        element=element_str,
        element_normalized=element_normalized,
        source="BOTH" if any(a.type == "both" for a in anchors) else (
            "VISUAL" if any(a.type == "visual" for a in anchors) else (
                "CODE" if any(a.type == "dom" for a in anchors) else ""
            )
        ),
        priority=severity,
        priority_rank=priority_rank,
        observation=d.get("observation", ""),
        recommendation=d.get("recommendation", ""),
        reference=primary_ref,
        title=d.get("title", ""),
        why_matters=d.get("why_this_matters", ""),
        citation=primary_ref,
        tier=primary_tier,
        synthesis_hint="",  # v2 has no SYNTHESIS_HINT — synthesizer integrates
        ethics_state=d.get("ethics_state", ""),
        source_url=d.get("source_url", ""),
        raw_block="",  # v2 has no markdown raw_block
        merged_from=tuple(d.get("merged_from") or ()),
        # v2 fields
        scope=d.get("scope", "device"),
        change_type=effort.get("change_type", ""),
        change_scope=effort.get("change_scope", ""),
        evidence_anchors=anchors_sorted,
        confidence=d.get("confidence"),
        baton_index=baton_index,
        surface=surface,
        proposed_anchor=proposed_anchor,
        visual_evidence=visual_evidence,
    )


__all__ = [
    "EmissionParseResult",
    "EmissionValidationError",
    "build_retry_prompt",
    "parse_emission_file",
    "parse_emission_files",
    "validate_emission_payload",
]
