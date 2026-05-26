"""Parse + validate the Priority Path synthesizer subagent's response.

The lead (Claude Code agent) dispatches a synthesizer subagent per
``contracts/synthesizer-subagent.md`` (v1) or ``contracts/synthesizer-v2.md``
(v2). v1 returns a single fenced JSON code block containing a
``{"stories": [...]}`` object; v2 writes ``synthesizer-emission-v1.json``
directly to disk validating against ``schema/synthesizer-emission-v1.json``.

This module exposes two parser surfaces:

- v1 path (unchanged per Kieran's no-touch rule):
  ``parse_response(text)`` and ``validate_stories(stories, valid_refs)``.

- v2 path (Phase F.4 deliverable):
  ``validate_synthesizer_emission_payload(payload, valid_refs)`` and
  ``parse_synthesizer_emission_file(path, valid_refs)``. Both validate
  via ``referencing.Registry`` (same offline-only pattern json_parser.py
  uses) plus the JSON-derived allowlist check across priority_path[].f_refs,
  quick_wins_manifest, severity_manifest, and scope_page_synchronized_refs.

Deliberately subagent-agnostic: we do not know or care what the SDK
shape was on the subagent side. All we consume is the file the lead
captures from disk. If the subagent ever moves to direct SDK calls (v1.1
or v2.1), the parser does not change.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Set, Tuple, TypedDict


class Story(TypedDict, total=False):
    """Shape the synthesizer must produce and the writer consumes."""

    title: str
    severity: str            # CRITICAL / HIGH / MEDIUM / LOW
    narrative_md: str        # 2-4 sentence markdown paragraph
    action_md: str           # 1-2 sentence markdown imperative
    f_refs: List[str]        # "{cluster} F-{NN}" strings from the allowlist


# Matches ```json ... ``` or ``` ... ``` (language tag optional). Greedy non-greedy.
_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)\n```", re.DOTALL)

# Matches the reference format "{cluster} F-{NN}" used by scoring._finding_ref
# — cluster is kebab-case (letters, numbers, hyphens); F-NN is zero-padded.
_REF_RE = re.compile(r"^[a-z][a-z0-9-]* F-\d{2}$")

_VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}

MIN_STORIES = 3
MAX_STORIES = 5
MIN_F_REFS_PER_STORY = 2
MAX_F_REFS_PER_STORY = 4


def parse_response(text: str) -> "List[Story] | None":
    """Extract ``stories`` from the first fenced JSON code block in ``text``.

    Returns ``None`` for anything malformed:

    - no fenced code block in the text
    - fenced block is not valid JSON
    - JSON root is not an object, or lacks a ``stories`` key
    - ``stories`` is not a list of objects

    Returns the ``stories`` list otherwise. The caller MUST then run
    ``validate_stories`` — ``parse_response`` only verifies the envelope
    shape, not the hard constraints.
    """
    if not isinstance(text, str) or not text:
        return None
    match = _FENCE_RE.search(text)
    if not match:
        return None
    try:
        payload = json.loads(match.group(1))
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    stories = payload.get("stories")
    if not isinstance(stories, list):
        return None
    out: List[Story] = []
    for item in stories:
        if not isinstance(item, dict):
            # One malformed entry → whole response is invalid (fail-loud).
            return None
        out.append(item)  # type: ignore[arg-type]
    return out


def validate_stories(
    stories: "List[Story]",
    valid_refs: Set[str],
) -> Tuple[bool, str]:
    """Return ``(True, "")`` when stories pass every hard constraint.

    Returns ``(False, reason)`` with a single-line reason string
    otherwise. ``reason`` is safe to surface to the operator and can be
    injected as a correction turn on synthesizer retry.

    Constraints enforced:

    - ``MIN_STORIES <= len(stories) <= MAX_STORIES``
    - Each story has a non-empty ``title`` (str).
    - ``severity`` is one of CRITICAL / HIGH / MEDIUM / LOW.
    - ``narrative_md`` and ``action_md`` are non-empty strings.
    - ``MIN_F_REFS_PER_STORY <= len(f_refs) <= MAX_F_REFS_PER_STORY``.
    - Every ``f_ref`` matches the ``{cluster} F-{NN}`` format AND is
      present in ``valid_refs``. ``valid_refs`` is built from the
      finalized ``cluster_finding_map``
      (``FinalizedFindings.valid_refs()``) so any hallucinated F-N
      fails.
    """
    if not isinstance(stories, list):
        return False, "stories must be a list"
    if not (MIN_STORIES <= len(stories) <= MAX_STORIES):
        return False, (
            f"story count {len(stories)} out of range "
            f"[{MIN_STORIES}, {MAX_STORIES}]"
        )
    for i, story in enumerate(stories, start=1):
        if not isinstance(story, dict):
            return False, f"story {i} is not an object"
        title = story.get("title")
        if not isinstance(title, str) or not title.strip():
            return False, f"story {i} has no title"
        severity = (story.get("severity") or "").upper()
        if severity not in _VALID_SEVERITIES:
            return False, f"story {i} severity {severity!r} not in {sorted(_VALID_SEVERITIES)}"
        narrative = story.get("narrative_md")
        if not isinstance(narrative, str) or not narrative.strip():
            return False, f"story {i} has no narrative_md"
        action = story.get("action_md")
        if not isinstance(action, str) or not action.strip():
            return False, f"story {i} has no action_md"
        refs = story.get("f_refs")
        if not isinstance(refs, list):
            return False, f"story {i} f_refs must be a list"
        if not (MIN_F_REFS_PER_STORY <= len(refs) <= MAX_F_REFS_PER_STORY):
            return False, (
                f"story {i} has {len(refs)} f_refs, expected "
                f"[{MIN_F_REFS_PER_STORY}, {MAX_F_REFS_PER_STORY}]"
            )
        for ref in refs:
            if not isinstance(ref, str):
                return False, f"story {i} has a non-string f_ref"
            if not _REF_RE.match(ref):
                return False, f"story {i} f_ref {ref!r} is malformed (expected '{{cluster}} F-NN')"
            if ref not in valid_refs:
                return False, f"story {i} f_ref {ref!r} is not in the allowlist (hallucinated)"
    return True, ""


# ---------------------------------------------------------------------------
# v2 synthesizer-emission-v1.json validator (Phase F.4)
# ---------------------------------------------------------------------------


_SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "schema"
_SYNTHESIZER_SCHEMA_PATH = _SCHEMA_DIR / "synthesizer-emission-v1.json"

_v2_validator = None  # built lazily on first use


def _build_v2_validator():
    """Build the v2 synthesizer-emission validator with referencing.Registry.

    Same offline-only pattern as json_parser._build_validator(). The
    synthesizer-emission schema is self-contained (no external $ref) so the
    Registry holds only the synthesizer schema. Registered under its $id so
    self-referencing patterns (none today, but reserved for future use) work
    without network fetch.
    """
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012

    schema = json.loads(_SYNTHESIZER_SCHEMA_PATH.read_text(encoding="utf-8"))
    resource = Resource.from_contents(schema, default_specification=DRAFT202012)
    registry = Registry().with_resources(
        [("https://ecp.local/schema/synthesizer-emission-v1.json", resource)]
    )
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(
        schema,
        registry=registry,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )


def _get_v2_validator():
    global _v2_validator
    if _v2_validator is None:
        _v2_validator = _build_v2_validator()
    return _v2_validator


@dataclass(frozen=True)
class SynthesizerValidationError(Exception):
    """Raised when a synthesizer emission fails validation.

    Carries enough structured detail for the lead's retry-prompt construction
    to cite the specific failure (schema field path + message, or list of
    hallucinated f_refs from the allowlist check).
    """

    emission_path: str
    schema_errors: tuple[tuple[str, str], ...]  # (path, message) pairs
    hallucinated_refs: tuple[tuple[str, str], ...]  # (location, ref) pairs

    def __str__(self) -> str:
        if self.schema_errors:
            path, msg = self.schema_errors[0]
            return f"{self.emission_path}: schema: {path}: {msg}"
        if self.hallucinated_refs:
            location, ref = self.hallucinated_refs[0]
            return f"{self.emission_path}: hallucinated f_ref {ref!r} at {location}"
        return self.emission_path


@dataclass(frozen=True)
class SynthesizerEmission:
    """Parsed synthesizer-emission-v1.json — frozen for safe pipeline transit."""

    schema_version: int
    engagement_id: str
    status: str
    dispatch_shape: str
    degraded_mode: bool
    audit_documents: dict
    priority_path: tuple[dict, ...]
    quick_wins_manifest: tuple[str, ...]
    severity_manifest: tuple[str, ...]
    scope_page_synchronized_refs: tuple[str, ...]
    raw: dict


def validate_synthesizer_emission_payload(
    payload: dict,
    valid_refs: Set[str],
    *,
    source_path: str = "<payload>",
) -> None:
    """Validate a parsed synthesizer-emission dict.

    Two-layer validation:

    1. Schema: against schema/synthesizer-emission-v1.json via Draft202012Validator
       with referencing.Registry. Catches required-field omissions, enum drift,
       allOf rules (degraded_mode <-> dispatch_shape agreement, failed_synthesis_drift
       requires lead_reflection_path).

    2. Allowlist: every f_ref in priority_path[].f_refs, quick_wins_manifest,
       severity_manifest, and scope_page_synchronized_refs must resolve to a
       real (cluster, display_index) entry in valid_refs (built by
       FinalizedFindings.valid_refs() in pipeline.py).

    Raises SynthesizerValidationError on any failure. Returns None on success.
    """
    validator = _get_v2_validator()
    schema_errors_raw = sorted(
        validator.iter_errors(payload), key=lambda e: list(e.absolute_path)
    )
    schema_errors = tuple(
        (".".join(str(p) for p in e.absolute_path), e.message) for e in schema_errors_raw
    )

    hallucinated: list[tuple[str, str]] = []
    if not schema_errors:
        # Allowlist check only runs when the schema-level shape is correct;
        # otherwise we'd be probing fields that may not be the right type.
        for i, story in enumerate(payload.get("priority_path", []) or []):
            for j, ref in enumerate(story.get("f_refs", []) or []):
                if ref not in valid_refs:
                    hallucinated.append((f"priority_path[{i}].f_refs[{j}]", ref))
        for label in ("quick_wins_manifest", "severity_manifest", "scope_page_synchronized_refs"):
            for j, ref in enumerate(payload.get(label, []) or []):
                if ref not in valid_refs:
                    hallucinated.append((f"{label}[{j}]", ref))

    if not schema_errors and not hallucinated:
        return

    raise SynthesizerValidationError(
        emission_path=source_path,
        schema_errors=schema_errors,
        hallucinated_refs=tuple(hallucinated),
    )


def parse_synthesizer_emission_file(
    path: Path | str,
    valid_refs: Set[str],
) -> SynthesizerEmission:
    """Read, parse, validate a synthesizer-emission-v1.json file.

    Returns a frozen SynthesizerEmission instance the renderer (Phase G) and
    parity-test runner (Phase K) consume. Raises SynthesizerValidationError
    on schema failure or hallucinated f_ref.

    The v1 ``parse_response`` flow is unchanged; v1 audits keep working
    against the legacy stories-in-fenced-block shape.
    """
    path = Path(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_synthesizer_emission_payload(payload, valid_refs, source_path=str(path))

    return SynthesizerEmission(
        schema_version=int(payload["schema_version"]),
        engagement_id=str(payload["engagement_id"]),
        status=str(payload["status"]),
        dispatch_shape=str(payload["dispatch_shape"]),
        degraded_mode=bool(payload["degraded_mode"]),
        audit_documents=dict(payload["audit_documents"]),
        priority_path=tuple(payload["priority_path"]),
        quick_wins_manifest=tuple(payload["quick_wins_manifest"]),
        severity_manifest=tuple(payload["severity_manifest"]),
        scope_page_synchronized_refs=tuple(payload["scope_page_synchronized_refs"]),
        raw=payload,
    )


def build_v2_retry_prompt(
    emission_path: str,
    error: SynthesizerValidationError,
    *,
    valid_refs: Set[str] | None = None,
) -> str:
    """Build a retry prompt the lead embeds on synthesizer re-dispatch.

    Cites schema-field paths and hallucinated f_refs with as much specificity
    as the validator can give. Mirrors the json_parser.build_retry_prompt
    pattern so specialists/synthesizer prompts have a consistent retry feel.
    """
    lines = [
        f"Your previous synthesizer emission at {emission_path} failed validation.",
    ]
    if error.schema_errors:
        lines += ["", "Schema errors:"]
        for path, msg in error.schema_errors[:24]:
            lines.append(f"- {path}: {msg}")
        if len(error.schema_errors) > 24:
            lines.append(f"- ... and {len(error.schema_errors) - 24} more")
    if error.hallucinated_refs:
        lines += ["", "Hallucinated f_refs (not in JSON-derived allowlist):"]
        for location, ref in error.hallucinated_refs[:24]:
            lines.append(f"- {location}: {ref!r}")
        if len(error.hallucinated_refs) > 24:
            lines.append(f"- ... and {len(error.hallucinated_refs) - 24} more")
        if valid_refs:
            sample = sorted(valid_refs)[:20]
            lines += [
                "",
                "Sample of valid f_refs you may cite:",
                *(f"- {r}" for r in sample),
            ]
            if len(valid_refs) > 20:
                lines.append(f"- ... ({len(valid_refs) - 20} more available)")
    lines += [
        "",
        "Re-emit a single JSON object validating against schema/synthesizer-emission-v1.json.",
        "Address the errors above directly - do not regenerate from scratch.",
        "Cite only f_refs that resolve to real cluster emissions in this engagement.",
        "No prose, no markdown fences, no preamble.",
    ]
    return "\n".join(lines)


__all__ = [
    "MIN_F_REFS_PER_STORY",
    "MAX_F_REFS_PER_STORY",
    "MIN_STORIES",
    "MAX_STORIES",
    "Story",
    "SynthesizerEmission",
    "SynthesizerValidationError",
    "build_v2_retry_prompt",
    "parse_response",
    "parse_synthesizer_emission_file",
    "validate_stories",
    "validate_synthesizer_emission_payload",
]
