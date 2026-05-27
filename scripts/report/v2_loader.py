"""v2 renderer input loader (Phase G deliverable 1).

Reads the v2 engagement artifacts and produces the same shape v1
``html_builder._load_inputs`` returns, so the rest of the renderer pipeline
stays unchanged. Also surfaces v2-only fields (baton_index, scope,
evidence_anchors, severity) on each finding so v2_markers can resolve
hotspots via direct e_index lookup.

v2 engagement input contract:
- audit-{device}.md         heading-anchored structured-fields markdown
- synthesizer-emission-v1.json  priority_path + manifests + sync_refs
- cluster-{cluster}-{device}.json  per-device specialist emissions (10/device)
- ethics-findings.json       single page-scope ethics emission
- baton.json / baton-mobile.json  v1-format baton (engagement dir; has screenshots[])
- canonical-f-refs.json (optional) cross-device-merged manifest from
                                    lead_prep.py build-canonical-frefs.
                                    If absent, loader re-derives the merge
                                    inline via _normalize_title heuristic.

The v1 path through `parser.parse_findings` is NOT touched. v2_loader is
parallel; the dispatch is via the ``--v2`` flag in generate-report.py or
auto-detection of synthesizer-emission-v1.json.

Authored Phase G (2026-04-28).
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Heading-anchored markdown parser (matches contracts/synthesizer-v2.md
# "Per-finding rendering format" spec)
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(
    r"^(?:#{3,4})\s+([a-z][\w-]*)\s+F-(\d{2})(?:\s+[—\-]\s+(.*?))?\s*$",
    re.MULTILINE | re.IGNORECASE,
)
_FIELD_RE = re.compile(r"^\*\*([A-Za-z _]+):\*\*\s*(.+?)\s*$", re.MULTILINE)
_OBS_HEAD = "**OBSERVATION:**"
_REC_HEAD = "**RECOMMENDATION:**"
_WHY_HEAD = "**Why this matters:**"
# Match the synth's current citation block format:
#   ▸ filename.md, Finding 14: Optional finding title or summary [Tier]
# Earlier audits used the older ``(Author Year)`` parenthetical form; both
# the title-suffix form and the bare ``Finding N`` form (no suffix) are
# accepted here so historical engagements continue to render. The regex
# captures: (1) reference filename, (2) finding number, (3) tier — author
# parenthetical is no longer authoritative and is dropped (`citation_authors`
# is set to "" downstream).
_CITATION_RE = re.compile(
    r"^[▸>]\s+([\w\-]+\.md),\s*Finding\s*(\d+)(?::\s*.+?)?\s*\[(\w+)\]\s*$",
    re.MULTILINE,
)


def parse_v2_audit_markdown(audit_path: Path) -> dict[str, dict]:
    """Extract per-finding structured fields + paragraphs from audit-{device}.md.

    Returns a dict keyed by canonical f_ref ("audience F-01") whose values
    are dicts with keys: section, element, source, priority, observation,
    recommendation, why_matters, citation, citation_finding_no,
    citation_authors, tier, title.

    Findings are identified by ``### {f_ref} — title`` or
    ``#### {f_ref} — title`` headings (level 3 or 4; case-insensitive on the
    cluster slug). Each subsection ends at the next finding heading or
    end-of-file. Within the subsection, structured fields parse as
    ``**FIELD:** value`` lines and prose paragraphs parse as the text from
    each labeled bold marker (``**OBSERVATION:**``, ``**RECOMMENDATION:**``,
    ``**Why this matters:**``) up to the next labeled marker, blank line, or
    citation block.
    """
    text = audit_path.read_text(encoding="utf-8")
    headings = list(_HEADING_RE.finditer(text))
    out: dict[str, dict] = {}

    for i, m in enumerate(headings):
        cluster = m.group(1).lower()
        idx = int(m.group(2))
        title = (m.group(3) or "").strip()
        f_ref = f"{cluster} F-{idx:02d}"
        start = m.end()
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        body = text[start:end]

        finding: dict = {"f_ref": f_ref, "title": title}

        # Structured fields (SECTION/ELEMENT/SOURCE/PRIORITY)
        for fm in _FIELD_RE.finditer(body):
            label = fm.group(1).strip().lower().replace(" ", "_")
            value = fm.group(2).strip()
            if label in {"section", "element", "source", "priority"}:
                finding[label] = value

        # Prose paragraphs
        finding["observation"] = _slice_paragraph(body, _OBS_HEAD)
        finding["recommendation"] = _slice_paragraph(body, _REC_HEAD)
        finding["why_matters"] = _slice_paragraph(body, _WHY_HEAD)

        # Citation block (▸ filename.md, Finding N[: title suffix] [Tier])
        cite = _CITATION_RE.search(body)
        if cite:
            finding["citation"] = cite.group(1).strip()
            finding["citation_finding_no"] = cite.group(2)
            finding["citation_authors"] = ""
            finding["tier"] = cite.group(3)
        else:
            finding["citation"] = ""
            finding["tier"] = "Bronze"

        out[f_ref] = finding

    return out


def _slice_paragraph(body: str, header: str) -> str:
    """Return the prose between ``header`` and the next bold header / blank line / end.

    Mirrors scripts.assembly.synth_input._slice_section but returns "" instead
    of None on miss (renderer prefers absent string to absent key).
    """
    pos = body.find(header)
    if pos < 0:
        return ""
    start = pos + len(header)
    # Find next bold-prefixed line OR citation marker OR end.
    candidates = []
    for marker in (_OBS_HEAD, _REC_HEAD, _WHY_HEAD):
        if marker == header:
            continue
        idx = body.find(marker, start)
        if idx >= 0:
            candidates.append(idx)
    cite = body.find("▸ ", start)
    if cite >= 0:
        candidates.append(cite)
    end = min(candidates) if candidates else len(body)
    return body[start:end].strip()


# ---------------------------------------------------------------------------
# Cluster-emission JSON loader (per-device finding metadata)
# ---------------------------------------------------------------------------


def load_cluster_emission_findings(
    engagement_dir: Path,
    device: str,
    cluster_emission_paths: list[Path] | None = None,
    ethics_findings_path: Path | None = None,
) -> list[dict]:
    """Read all cluster-emission-v1.json files for a device + ethics emission.

    Returns a list of raw finding dicts (one per finding, multiple per
    cluster). Each dict carries:
        cluster, device, local_index, title, observation, recommendation,
        why_matters, severity, verdict, scope, surface, baton_index,
        evidence_anchors[], reference_citations[], change_type, change_scope,
        ethics_state, source_url

    The ``cluster_emission_paths`` and ``ethics_findings_path`` arguments
    let callers pin specific paths (the slingmods fixture has 9 desktop
    emissions in engagement dir + 1 in .phase-b-tmp/, mobile all in
    .phase-b-tmp/). When omitted, the loader globs for cluster-{cluster}-
    {device}.json under engagement_dir AND .phase-b-tmp/.
    """
    paths: list[Path] = []
    if cluster_emission_paths:
        paths = list(cluster_emission_paths)
    else:
        # Auto-discover from both candidate locations
        for d in (engagement_dir, engagement_dir.parent.parent.parent / ".phase-b-tmp"):
            if not d.exists():
                continue
            for p in sorted(d.glob(f"cluster-*-{device}.json")):
                if p.name.startswith("cluster-context-"):
                    continue
                paths.append(p)

    findings: list[dict] = []
    for p in paths:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        cluster = data.get("cluster")
        for f in data.get("findings", []):
            findings.append(_finding_dict(cluster, device, f))

    # Ethics
    if ethics_findings_path is None:
        for candidate in (
            engagement_dir / "ethics-findings.json",
            engagement_dir.parent.parent.parent / ".phase-b-tmp" / "ethics-findings.json",
        ):
            if candidate.exists():
                ethics_findings_path = candidate
                break
    if ethics_findings_path and ethics_findings_path.exists():
        try:
            data = json.loads(ethics_findings_path.read_text(encoding="utf-8"))
            for f in data.get("findings", []):
                findings.append(_finding_dict("ethics", "page", f))
        except (OSError, json.JSONDecodeError):
            pass

    return findings


def _finding_dict(cluster: str, device: str, raw: dict) -> dict:
    """Normalize a raw cluster-emission finding into a flat dict.

    This is a whitelist normalizer — fields not listed here silently drop on
    their way to the renderer. New schema fields require an entry here.
    Architectural fix B (2026-04-30): field-threading invariant.
    """
    element = raw.get("element") or {}
    proposed_anchor = raw.get("proposed_anchor")
    if proposed_anchor is not None and not isinstance(proposed_anchor, dict):
        proposed_anchor = None
    # Phase 4a hardening (2026-05-18) — preserve producer-authored
    # visual_evidence through the loader's whitelist normalizer.
    # Without this the field is silently dropped on its way to the
    # marker pipeline + review-state, breaking the Phase 2 promise that
    # producer-authored visual_evidence wins over derived values. See
    # contracts/specialist-prompt-v2.md "Anchor candidates" section.
    visual_evidence = raw.get("visual_evidence")
    if visual_evidence is not None and not isinstance(visual_evidence, dict):
        visual_evidence = None
    out = {
        "cluster": cluster,
        "device": device,
        "local_index": raw.get("local_index") or raw.get("display_index") or 0,
        "display_index": raw.get("display_index") or 0,
        "title": raw.get("title", ""),
        "observation": raw.get("observation", ""),
        "recommendation": raw.get("recommendation", ""),
        "why_matters": raw.get("why_matters", ""),
        "severity": raw.get("severity", "MEDIUM"),
        "verdict": raw.get("verdict", "FAIL"),
        "scope": raw.get("scope", "device"),
        "surface": raw.get("surface", ""),
        "baton_index": element.get("baton_index"),
        "element_selector": element.get("selector", ""),
        "element_text_content": element.get("text_content", ""),
        "element_role": element.get("role", ""),
        "element_tag": element.get("tag", ""),
        "evidence_anchors": list(raw.get("evidence_anchors") or []),
        "reference_citations": list(raw.get("reference_citations") or []),
        "change_type": (raw.get("effort") or {}).get("change_type", ""),
        "change_scope": (raw.get("effort") or {}).get("change_scope", ""),
        "ethics_state": raw.get("ethics_state"),
        "source_url": raw.get("source_url"),
        "confidence": raw.get("confidence", "MEDIUM"),
        "evidence_tier": raw.get("evidence_tier", "Bronze"),
        "proposed_anchor": proposed_anchor,
        "visual_evidence": visual_evidence,
    }
    return out


# ---------------------------------------------------------------------------
# Cross-device canonical-ref merge (Phase F.checkpoint Layer-2.5 logic
# brought into the renderer for self-contained operation)
# ---------------------------------------------------------------------------


def _normalize_title(t: str) -> str:
    """Title-normalization for cross-device duplicate merge.

    Phase H (2026-04-28): delegates to the canonical implementation in
    ``scripts.assembly.pipeline.normalize_finding_title``. Kept as a
    private alias so existing callers in this module continue to work
    without import-path churn.
    """
    import sys as _sys
    repo_root = Path(__file__).resolve().parent.parent.parent
    if str(repo_root / "scripts") not in _sys.path:
        _sys.path.insert(0, str(repo_root / "scripts"))
    from assembly.pipeline import normalize_finding_title as _canonical
    return _canonical(t)


def build_canonical_view(
    cluster_emission_paths: list[Path],
    ethics_findings_path: Path | None,
) -> tuple[dict, dict, list[dict]]:
    """Produce the canonical-merged view via the full assembly pipeline.

    Runs the canonical assembly pipeline (the same path lead_prep.py
    build-canonical-frefs serializes to canonical-f-refs.json):

        parse (json_parser.parse_emission_file)
        → deduplicate_v2 (dedup.deduplicate_v2)
        → FinalizedFindings.build (assigns display_index)
        → cross-device title merge (Layer 2.5)

    The renderer's canonical view must match the synthesizer's exactly —
    the synthesizer wrote audit markdown with canonical f_refs as headings,
    and the renderer parses those same headings. Diverging algos produce
    f_ref mismatches between markdown and renderer.

    Returns ``(by_canonical_ref, merge_aliases, dropped_emissions)``.

    ``dropped_emissions`` is a list of dicts
    ``{"path", "error_type", "error_message"}`` for every cluster emission
    (and the ethics emission) that ``parse_emission_file`` rejected as
    schema-invalid and was therefore excluded from the canonical view.
    Empty list = clean run; the caller may ignore. Non-empty = cluster
    coverage silently shrank and the caller MUST treat this as a phase-
    blocking signal. Pre-G16 these failures were swallowed by a bare
    ``except Exception: continue``, which caused engagement
    ``docs/ecp/2026-05-27-52f53a53`` to lose 6 of 12 cluster files
    (~25 high-severity FAIL findings vanished) with all structural and
    substantive canaries still PASS — exactly the §0 untraceable-
    misleading failure mode this surfacing prevents.
    """
    # Lazy-import scripts/assembly so v2_loader stays usable for callers
    # that just want the markdown parser without pulling jsonschema deps.
    import sys as _sys
    repo_root = Path(__file__).resolve().parent.parent.parent
    if str(repo_root / "scripts") not in _sys.path:
        _sys.path.insert(0, str(repo_root / "scripts"))
    from assembly.json_parser import parse_emission_file
    from assembly.dedup import deduplicate_v2
    from assembly.pipeline import FinalizedFindings

    findings_assembly = []
    clusters_used: list[str] = []
    raw_extras_by_local: dict[tuple, dict] = {}  # only for fields the dataclass doesn't carry
    # G16 (2026-05-27): record every emission that fails parse_emission_file
    # so the caller can surface it. Pre-G16 these were silently dropped via
    # `except Exception: continue` — see function docstring for the failure
    # case this surfacing is built to prevent.
    dropped_emissions: list[dict] = []

    # Phase 4a hardening (2026-05-18) — load anchor-candidates sidecars
    # from the parent engagement dir if present so candidate_id resolution
    # happens at parse time. The renderer must agree with
    # lead_prep.py build-canonical-frefs on canonical ID assignment, which
    # means both consumers must pass the same sidecar into parse_emission_file.
    sidecar_by_device: dict[str, dict | None] = {
        "desktop": None, "mobile": None, "laptop": None, "page": None,
    }
    # Also resolve engagement dir from ethics path if no cluster paths are
    # supplied (defensive — covers ethics-only test fixtures).
    eng_dir: Path | None = None
    if cluster_emission_paths:
        eng_dir = Path(cluster_emission_paths[0]).parent
    elif ethics_findings_path is not None:
        eng_dir = Path(ethics_findings_path).parent
    if eng_dir is not None:
        # Phase 4b hardening 2 (2026-05-18) — strict loader. Missing file
        # → None (legacy skip). Present-but-broken → SidecarLoadError
        # propagates to the renderer caller, which surfaces it to the
        # operator instead of silently disabling the registry rule.
        # Codex 2026-05-18 review of 64ce7f2.
        from assembly.anchor_candidates import load_anchor_candidates_sidecar_strict
        for device in ("desktop", "mobile", "laptop", "page"):
            sc_path = eng_dir / f"anchor-candidates-{device}.json"
            sidecar_by_device[device] = load_anchor_candidates_sidecar_strict(sc_path)

    for p in cluster_emission_paths:
        # Match sidecar by filename suffix so a desktop emission resolves
        # against anchor-candidates-desktop.json, mobile against mobile.
        sc = (
            sidecar_by_device["desktop"] if "-desktop.json" in p.name
            else sidecar_by_device["mobile"] if "-mobile.json" in p.name
            else sidecar_by_device["laptop"] if "-laptop.json" in p.name
            else None
        )
        try:
            res = parse_emission_file(p, anchor_candidates_sidecar=sc)
        except Exception as exc:
            # G16: was a bare `continue` that silently dropped the whole
            # cluster file. Record (path, error) instead so lead_prep.py
            # build-canonical-frefs can phase-block the audit when drops
            # occur. The cluster's findings are still excluded from this
            # build (we cannot trust partially-parsed emissions), but the
            # operator now sees what was lost.
            dropped_emissions.append({
                "path": p.name,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            })
            continue
        findings_assembly.extend(res.findings)
        if res.cluster not in clusters_used:
            clusters_used.append(res.cluster)
        # Reference citations + element selector/text_content + change_type/scope
        # are not carried by the Finding dataclass; pull from raw JSON.
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for i, rf in enumerate(raw.get("findings", []), start=1):
            # Match by (cluster, device, position) — the dataclass's local_index
            # is also 1-based parse-order. raw JSON has 'local_id' not 'local_index'.
            key = (res.cluster, rf.get("device"), i)
            raw_extras_by_local[key] = {
                "reference_citations": list(rf.get("reference_citations") or []),
                "element_selector": (rf.get("element") or {}).get("selector", ""),
                "element_text_content": (rf.get("element") or {}).get("text_content", ""),
                "element_role": (rf.get("element") or {}).get("role", ""),
                "element_tag": (rf.get("element") or {}).get("tag", ""),
                "change_type": (rf.get("effort") or {}).get("change_type", ""),
                "change_scope": (rf.get("effort") or {}).get("change_scope", ""),
                "evidence_tier": rf.get("evidence_tier", "Bronze"),
                "severity": rf.get("severity", "MEDIUM"),
                "ethics_state": rf.get("ethics_state"),
                "source_url": rf.get("source_url"),
                "proposed_anchor": rf.get("proposed_anchor"),
            }

    if ethics_findings_path and ethics_findings_path.exists():
        try:
            # Phase 4a hardening — ethics emissions have device="page".
            # Use the page-level sidecar if present, fall back to desktop
            # (most page-scope ethics refs cite desktop e_indexes).
            eth_sidecar = (
                sidecar_by_device.get("page")
                or sidecar_by_device.get("desktop")
            )
            res = parse_emission_file(ethics_findings_path, anchor_candidates_sidecar=eth_sidecar)
            findings_assembly.extend(res.findings)
            if "ethics" not in clusters_used:
                clusters_used.append("ethics")
            raw = json.loads(ethics_findings_path.read_text(encoding="utf-8"))
            for i, rf in enumerate(raw.get("findings", []), start=1):
                key = ("ethics", rf.get("device"), i)
                raw_extras_by_local[key] = {
                    "reference_citations": list(rf.get("reference_citations") or []),
                    "element_selector": (rf.get("element") or {}).get("selector", ""),
                    "element_text_content": (rf.get("element") or {}).get("text_content", ""),
                    "element_role": (rf.get("element") or {}).get("role", ""),
                    "element_tag": (rf.get("element") or {}).get("tag", ""),
                    "change_type": (rf.get("effort") or {}).get("change_type", ""),
                    "change_scope": (rf.get("effort") or {}).get("change_scope", ""),
                    "evidence_tier": rf.get("evidence_tier", "Bronze"),
                    "severity": rf.get("severity", "MEDIUM"),
                    "ethics_state": rf.get("ethics_state"),
                    "source_url": rf.get("source_url"),
                    "proposed_anchor": rf.get("proposed_anchor"),
                }
        except Exception as exc:
            # G16: ethics drops are equally invisible pre-fix. Match the
            # cluster-emission contract — record the drop, exclude the
            # ethics findings from this build, let the caller decide.
            dropped_emissions.append({
                "path": ethics_findings_path.name,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            })

    deduped = deduplicate_v2(findings_assembly)
    # Include BLOCK/ADJACENT ethics findings alongside cluster findings via the
    # canonical helper (closes 2026-05-18 namespace-drift bug — see
    # DedupeResult.all_actionable() docstring + tests/test_dedup_consumer_parity.py).
    # Pre-fix, ethics_findings was dropped here, leaving the Ethics tab empty
    # while CLEAR-ish ethics rows leaked into the cluster panel. Post-fix, this
    # consumer and lead_prep.py build-canonical-frefs share the same input universe.
    finalized = FinalizedFindings.build(deduped.all_actionable(), clusters_used)

    raw_by_ref: dict[str, dict] = {}
    devices_presence: dict[str, set] = defaultdict(set)
    for f in finalized.findings:
        ref = f"{f.cluster} F-{f.display_index:02d}"
        devices_presence[ref].add(f.device)
        extras = raw_extras_by_local.get((f.cluster, f.device, f.local_index)) or {}
        # Convert evidence_anchors dataclasses to plain dicts for downstream use.
        anchors_dicts: list[dict] = []
        for ea in (f.evidence_anchors or ()):
            anchors_dicts.append({
                "type": ea.type,
                "reference": ea.reference,
                "scroll_y": ea.scroll_y,
                "viewport": ea.viewport,
                "context": ea.context,
            })
        raw_by_ref[ref] = {
            "cluster": f.cluster,
            "title": f.title,
            "scope": getattr(f, "scope", None) or "device",
            "device": f.device,
            "verdict": f.verdict,
            "severity": extras.get("severity") or "MEDIUM",
            "priority": f.priority,
            "surface": getattr(f, "surface", "") or "",
            "baton_index": f.baton_index,
            "evidence_anchors": anchors_dicts,
            "reference_citations": extras.get("reference_citations", []),
            "proposed_anchor": extras.get("proposed_anchor"),
            "change_type": extras.get("change_type", "") or getattr(f, "change_type", ""),
            "change_scope": extras.get("change_scope", "") or getattr(f, "change_scope", ""),
            "ethics_state": extras.get("ethics_state") or f.ethics_state,
            "source_url": extras.get("source_url") or f.source_url,
            "confidence": getattr(f, "confidence", "MEDIUM"),
            "evidence_tier": extras.get("evidence_tier", "Bronze") or f.tier,
            "observation": f.observation,
            "recommendation": f.recommendation,
            "why_matters": f.why_matters,
            "element_selector": extras.get("element_selector", ""),
            "element_text_content": extras.get("element_text_content", ""),
            "element_role": extras.get("element_role", ""),
            "element_tag": extras.get("element_tag", ""),
            # Phase 4a hardening (2026-05-18) — surface producer-authored
            # visual_evidence on the canonical view so load_v2_findings
            # can pass it to the renderer. cross_device_title_merge
            # preserves "other keys" on the canonical winner, so this
            # field flows through for singletons and merged groups alike.
            # Closes Codex 2026-05-18 review item 1 on ffeb1a6.
            "visual_evidence": getattr(f, "visual_evidence", None),
        }

    # Augment devices_present from auto-merged trail (Layer 2 dedup merges
    # findings across devices when keys agree on (cluster, baton_index, verdict)).
    for merge_record in deduped.auto_merged:
        winner = merge_record.get("winner") or {}
        loser = merge_record.get("loser") or {}
        winner_cluster = winner.get("cluster")
        winner_local = winner.get("local_index")
        loser_device = loser.get("device")
        if not (winner_cluster and winner_local and loser_device):
            continue
        for f in finalized.findings:
            if f.cluster == winner_cluster and f.local_index == winner_local:
                ref = f"{f.cluster} F-{f.display_index:02d}"
                devices_presence[ref].add(loser_device)
                break

    for ref in raw_by_ref:
        raw_by_ref[ref]["devices_present"] = sorted(devices_presence[ref])

    # Layer-2.5 cross-device duplicate merge: delegated to the shared
    # implementation in scripts/assembly/pipeline.py (Phase H promotion,
    # 2026-04-28). The same algo is also called by
    # lead_prep.py build-canonical-frefs — keeping one source of
    # truth eliminates the divergence risk flagged in the Phase G handoff.
    from assembly.pipeline import cross_device_title_merge
    by_canonical_ref, merge_aliases = cross_device_title_merge(raw_by_ref)
    return by_canonical_ref, merge_aliases, dropped_emissions


# ---------------------------------------------------------------------------
# Top-level v2 finding shape (compatible with v1 renderer's expectations)
# ---------------------------------------------------------------------------


def load_v2_findings(
    engagement_dir: Path,
    device: str,
    audit_file: str = None,
    cluster_emission_paths: list[Path] | None = None,
    ethics_findings_path: Path | None = None,
) -> list[dict]:
    """Build the renderer-ready finding list for ``device``.

    Output dict shape mirrors what ``parser.parse_findings`` returns plus
    v2-only fields. Required by the v1 html_builder pipeline:
        index (1-based), verdict, cluster, title, section, element, source,
        priority, observation, recommendation, why_matters, citation, tier,
        ethics_state, source_url, reference

    v2-only additions:
        f_ref (canonical), baton_index (per device), scope, severity,
        evidence_anchors, devices_present, change_type, change_scope

    The function only emits findings that should appear on ``device``:
    page-scope findings that the device-pair contains (devices_present
    includes ``device``) AND device-scope findings whose device matches.
    Sync-ref findings get rendered identically across both audits per the
    locked synchronization invariant.
    """
    audit_file = audit_file or f"audit-{device}.md"
    audit_path = engagement_dir / audit_file

    if cluster_emission_paths is None:
        cluster_emission_paths = _engagement_cluster_emission_paths(engagement_dir)

    if ethics_findings_path is None:
        ethics_findings_path = _engagement_ethics_findings_path(engagement_dir)

    by_canonical_ref, _aliases, _drops = build_canonical_view(
        cluster_emission_paths, ethics_findings_path
    )

    # Parse audit markdown for prose. Newer synthesized audits use heading
    # anchored `### cluster F-01` sections; quick/operator-authored audits often
    # use the older fenced FINDING blocks. When no v2 emissions are present,
    # fall back to the fenced parser instead of rendering a blank report.
    prose_by_ref = parse_v2_audit_markdown(audit_path) if audit_path.exists() else {}
    if not by_canonical_ref and audit_path.exists():
        return _load_legacy_markdown_findings(engagement_dir, device, audit_path)

    findings_out: list[dict] = []
    cluster_order = [
        "audience", "category-navigation", "checkout-flows", "content-seo",
        "ethics", "performance-ux", "post-purchase", "pricing",
        "product-media", "trust-credibility", "visual-cta",
    ]
    cluster_sort_key = {c: i for i, c in enumerate(cluster_order)}

    sorted_refs = sorted(
        by_canonical_ref.keys(),
        key=lambda r: (
            cluster_sort_key.get(r.split(" F-", 1)[0], 99),
            int(r.rsplit(" F-", 1)[1]),
        ),
    )

    for canonical_ref in sorted_refs:
        meta = by_canonical_ref[canonical_ref]
        # Filter PASS findings — they note things working correctly and don't
        # need rendering as actionable items. v1 parser by design only parsed
        # FAIL/PARTIAL blocks; v2 honors that default. Operators wanting the
        # full set can pass --include-pass (future flag) or read the
        # cluster-emission JSON directly.
        verdict = (meta.get("verdict") or "").upper()
        if verdict not in ("FAIL", "PARTIAL"):
            continue

        # Ethics filtering: per `product.md` §4.1 (Adjacent ethics
        # findings as a feature) + §6 (operator manual verification),
        # only BLOCK and ADJACENT ethics findings render in the
        # customer deliverable.
        # CLEAR is telemetry-only — not surfaced to the buyer, since
        # "mention of dark patterns is never a thing unless it's in violation."
        # Pre-fix, all ethics findings were force-rendered regardless of state.
        if meta["cluster"] == "ethics":
            ethics_state = (meta.get("ethics_state") or "").upper()
            if ethics_state not in ("BLOCK", "ADJACENT"):
                continue

        # Only render findings whose canonical scope/device matches:
        # - scope='page' findings render on every device they were caught on
        # - scope='device' findings render only on their device
        # - ethics page-scope findings (cluster='ethics', device='page') always render
        if meta["cluster"] == "ethics":
            pass  # always include (BLOCK/ADJACENT only — filtered above)
        elif meta["scope"] == "page":
            if device not in meta["devices_present"]:
                continue
        else:
            if device not in meta["devices_present"]:
                continue

        prose = prose_by_ref.get(canonical_ref) or {}
        baton_index = meta["baton_index_by_device"].get(device) or meta["baton_index_by_device"].get("page")

        # Build a renderer-ready citation string from the structured
        # reference_citations[] when prose extraction didn't capture one.
        # parse_v2_audit_markdown does NOT extract the synth's
        # "▸ filename.md, Finding N (Description) [Tier]" lines into
        # prose["citation"], so without this fallback _resolve_citations
        # has nothing to look up and 0% of citations resolve to URLs.
        # Mirrors the same pattern in scripts/assembly/json_parser.py
        # _finding_from_dict.
        ref_str_from_meta = ""
        ref_cites = meta.get("reference_citations") or []
        if ref_cites:
            first = ref_cites[0]
            parts = [first.get("source", "")]
            if first.get("section"):
                parts.append(first["section"])
            elif first.get("line"):
                parts.append(f"line {first['line']}")
            ref_str_from_meta = ":".join(p for p in parts if p)

        finding = {
            # v1-compat fields
            "index": len(findings_out) + 1,
            "verdict": meta["verdict"],
            "cluster": meta["cluster"],
            "title": prose.get("title") or meta["title"],
            "section": prose.get("section") or meta["surface"] or "",
            "element": prose.get("element") or _build_element_string(meta),
            "synthesis_hint": "",
            "source": prose.get("source") or "BOTH",
            "priority": prose.get("priority") or _severity_to_priority(meta["severity"]),
            "observation": prose.get("observation") or meta["observation"],
            "recommendation": prose.get("recommendation") or meta["recommendation"],
            "why_matters": prose.get("why_matters") or meta["why_matters"],
            "reference": prose.get("citation") or ref_str_from_meta,
            "citation": prose.get("citation") or ref_str_from_meta,
            "tier": prose.get("tier") or meta["evidence_tier"] or "Bronze",
            "ethics_state": (meta.get("ethics_state") or "").upper() or None,
            "source_url": meta.get("source_url"),
            # v2-only extensions
            "f_ref": canonical_ref,
            "baton_index": baton_index,
            "scope": meta["scope"],
            "severity": meta["severity"],
            "evidence_anchors": meta["evidence_anchors"],
            "devices_present": meta["devices_present"],
            "change_type": meta["change_type"],
            "change_scope": meta["change_scope"],
            "confidence": meta["confidence"],
            "proposed_anchor": meta.get("proposed_anchor"),
            # Phase 4a hardening (2026-05-18) — surface producer-authored
            # visual_evidence to the renderer. scripts/report/v2_markers.py
            # auto_map_markers_v2 reads visual_evidence on the finding
            # and honors producer-authored type/confidence/observed_anchor
            # over derived placement (visual_evidence.derive_visual_evidence
            # rule 1: explicit producer-authored wins). Closes Codex
            # 2026-05-18 review item 1 on ffeb1a6.
            #
            # Phase 4a hardening 3 (2026-05-18) — for cross-device merged
            # findings, the per-device visual_evidence wins over the
            # canonical winner's. Without this, mobile renderings of a
            # cross-device-merged page-scope finding got desktop's
            # observed_anchor.baton_index even though top-level
            # baton_index correctly came from baton_index_by_device.
            # Closes Codex 2026-05-18 review of 50e1d94.
            "visual_evidence": _device_visual_evidence(meta, device, baton_index),
        }
        findings_out.append(finding)

    return findings_out


def _engagement_cluster_emission_paths(engagement_dir: Path) -> list[Path]:
    """Return engagement-scoped cluster emission paths for both devices."""
    paths: list[Path] = []
    if engagement_dir.exists():
        for p in sorted(engagement_dir.glob("cluster-*-desktop.json")):
            if not p.name.startswith("cluster-context-"):
                paths.append(p)
        for p in sorted(engagement_dir.glob("cluster-*-mobile.json")):
            if not p.name.startswith("cluster-context-"):
                paths.append(p)
    return paths


def _engagement_ethics_findings_path(engagement_dir: Path) -> Path | None:
    candidate = engagement_dir / "ethics-findings.json"
    return candidate if candidate.exists() else None


def _device_visual_evidence(
    meta: dict, device: str, baton_index: str | None,
) -> dict | None:
    """Select the per-device visual_evidence for a rendered finding.

    Phase 4a hardening 3 (2026-05-18) — cross_device_title_merge groups
    same-titled findings across devices into one canonical ref. Without
    this helper, every device's rendering inherits the canonical winner's
    ``visual_evidence`` — which means mobile renderings of a
    cross-device-merged page-scope finding see desktop's
    ``observed_anchor.baton_index`` even though the top-level
    ``baton_index`` correctly comes from
    ``baton_index_by_device[device]``. Codex 2026-05-18 review of 50e1d94.

    Selection priority:

    1. ``meta["visual_evidence_by_device"][device]`` — populated when the
       finding was cross-device-merged AND the source device had its own
       visual_evidence.
    2. ``meta["visual_evidence"]`` — the canonical winner's value;
       fallback for singletons or legacy emissions without per-device data.
    3. ``None`` — no producer-authored visual_evidence at all; the
       marker pipeline's ``derive_visual_evidence`` fills in a default.

    Once selected, if ``baton_index`` (the device-specific top-level
    e_index) is set, the helper rewrites
    ``visual_evidence.observed_anchor.baton_index`` to match — ensuring
    the renderer's hotspot lookup and the operator-facing tooltip both
    reference the same element.
    """
    ve_by_dev = meta.get("visual_evidence_by_device") or {}
    chosen = ve_by_dev.get(device) if isinstance(ve_by_dev, dict) else None
    if chosen is None:
        chosen = meta.get("visual_evidence")
    if not isinstance(chosen, dict):
        return None

    # If we know the device-specific baton_index, make sure the rendered
    # finding's observed_anchor.baton_index agrees. The renderer reads
    # the top-level baton_index for hotspot placement; observed_anchor is
    # operator-facing tooltip prose — if they disagree the operator sees
    # the wrong e_index in the UI.
    if baton_index and baton_index != "absent":
        anchor = chosen.get("observed_anchor") or {}
        if isinstance(anchor, dict) and anchor.get("baton_index") != baton_index:
            # Build a NEW visual_evidence dict; never mutate the canonical
            # meta in place (cross_device_title_merge consumers may run
            # twice in tests/CI and see drift).
            new_anchor = dict(anchor)
            new_anchor["baton_index"] = baton_index
            new_ve = dict(chosen)
            new_ve["observed_anchor"] = new_anchor
            return new_ve
    return chosen


def _build_element_string(meta: dict) -> str:
    """Compose an ELEMENT field string from cluster-emission element data."""
    sel = meta.get("element_selector") or ""
    if sel:
        return f"`{sel}`"

    baton_index = meta.get("baton_index")
    if baton_index and baton_index != "absent":
        tag = meta.get("element_tag") or ""
        role = meta.get("element_role") or ""
        text = (meta.get("element_text_content") or "").strip()
        label = tag or role
        if role and role != tag:
            label = f"{label} {role}".strip()
        if text:
            if len(text) > 96:
                text = text[:93].rstrip() + "..."
            return f"{baton_index} ({label}: {text})" if label else f"{baton_index} ({text})"
        return f"{baton_index} ({label})" if label else str(baton_index)

    return "(absent)"


def _severity_to_priority(severity: str) -> str:
    """Map cluster-emission severity to renderer priority."""
    s = (severity or "").upper()
    if s == "CRITICAL":
        return "HIGH"
    return s if s in {"HIGH", "MEDIUM", "LOW"} else "MEDIUM"


def _load_legacy_markdown_findings(
    engagement_dir: Path,
    device: str,
    audit_path: Path,
) -> list[dict]:
    """Render older fenced markdown audits through the v2 report/editor path."""
    try:
        from .parser import parse_findings
    except ImportError:  # pragma: no cover - script execution fallback
        from report.parser import parse_findings

    findings = parse_findings(audit_path)
    cluster_counts: dict[str, int] = defaultdict(int)
    out: list[dict] = []

    for raw in findings:
        cluster = raw.get("cluster") or "finding"
        cluster_counts[cluster] += 1
        f_ref = f"{cluster} F-{cluster_counts[cluster]:02d}"
        priority = (raw.get("priority") or "MEDIUM").upper()
        baton_index = _guess_baton_index_from_element(
            engagement_dir,
            device,
            raw.get("element", ""),
        )

        finding = {
            "index": len(out) + 1,
            "verdict": (raw.get("verdict") or "FAIL").upper(),
            "cluster": cluster,
            "title": raw.get("title", ""),
            "section": raw.get("section", ""),
            "element": raw.get("element", ""),
            "synthesis_hint": raw.get("synthesis_hint", ""),
            "source": raw.get("source", "BOTH"),
            "priority": priority,
            "observation": raw.get("observation", ""),
            "recommendation": raw.get("recommendation", ""),
            "why_matters": raw.get("why_matters", ""),
            "reference": raw.get("reference") or raw.get("citation", ""),
            "citation": raw.get("citation") or raw.get("reference", ""),
            "tier": raw.get("tier", "Bronze"),
            "ethics_state": (raw.get("ethics_state") or "").upper() or None,
            "source_url": raw.get("source_url"),
            "f_ref": f_ref,
            "baton_index": baton_index,
            "scope": "device",
            "severity": priority,
            "evidence_anchors": [],
            "devices_present": [device],
            "change_type": "",
            "change_scope": "",
            "confidence": "MEDIUM",
            "proposed_anchor": None,
            "plain_english_summary": "",
            "plain_english_action": "",
        }
        out.append(finding)

    return out


def _guess_baton_index_from_element(
    engagement_dir: Path,
    device: str,
    element: str,
) -> str | None:
    """Best-effort selector lookup for legacy markdown ELEMENT fields."""
    selector = _extract_selector_candidate(element)
    if not selector:
        return None

    baton_name = "baton.json" if device == "desktop" else f"baton-{device}.json"
    baton_path = engagement_dir / baton_name
    if not baton_path.exists():
        return None
    try:
        baton = json.loads(baton_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    elements = baton.get("elements") or []
    for idx, elem in enumerate(elements):
        elem_selector = elem.get("selector") or ""
        if elem_selector == selector:
            return f"e{idx}"

    if selector.startswith("#"):
        ident = selector.split()[0]
        for idx, elem in enumerate(elements):
            elem_selector = elem.get("selector") or ""
            if elem_selector == ident or elem_selector.startswith(ident) or ident in elem_selector:
                return f"e{idx}"

    for idx, elem in enumerate(elements):
        elem_selector = elem.get("selector") or ""
        if selector and selector in elem_selector:
            return f"e{idx}"

    return None


def _extract_selector_candidate(element: str) -> str:
    value = (element or "").strip().strip("`")
    if not value or value.startswith("("):
        return ""
    # Handle notes like "#ProductInfo... (title/price area)".
    value = re.sub(r"\s+\([^)]*\)\s*$", "", value).strip()
    # Handle compound descriptions like "promo bar + #ProductInfo...".
    id_match = re.search(r"(#[A-Za-z][\w:.-]*)", value)
    if id_match:
        return id_match.group(1)
    # Keep a simple selector token; prose labels are ignored.
    if re.match(r"^[.#A-Za-z][\w.#:> \-[\]=_\\]+$", value):
        return value
    return ""


# ---------------------------------------------------------------------------
# Priority Path loader (from synthesizer-emission-v1.json)
# ---------------------------------------------------------------------------


def load_v2_priority_path(
    engagement_dir: Path,
    actionable_refs: set[str] | None = None,
    *,
    ref_aliases: dict[str, str] | None = None,
    device: str | None = None,
    min_actionable_refs: int = 1,
) -> list[dict]:
    """Read priority_path stories from synthesizer-emission-v1.json.

    When ``actionable_refs`` is provided, filter each story's refs to only
    refs in that set (typically the current device's rendered findings).
    Stories with at least one current-device ref survive so the operator does
    not lose useful context solely because the synthesizer cited desktop-only
    siblings in a dual-device audit.

    Backward compatibility:
    - schema_version=1 emissions with ``f_refs`` remain supported.
    - future emissions may add ``refs_by_device``; those refs are tried first
      for the current device.
    - ``ref_aliases`` is exact-match only. Fuzzy anchor/citation comparison
      belongs upstream in conceptual-finding-key generation, where it can be
      validated with a threshold and provenance. The renderer must not invent
      fuzzy merges because a false merge here creates misleading UI links.

    Output shape matches what html_builder._synth_stories_to_render_shape
    produces (the renderer-internal "render shape"):
        number, title, severity, fixes_count, spans_clusters,
        description, action, underlying=[{cluster, index, label}]
    """
    path = engagement_dir / "synthesizer-emission-v1.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    stories = data.get("priority_path") or []
    out: list[dict] = []
    for i, story in enumerate(stories, start=1):
        underlying: list[dict] = []
        seen_underlying_refs: set[str] = set()
        missing_refs: list[str] = []
        raw_refs = _priority_story_refs_for_device(story, device)
        for ref in raw_refs:
            ref_str = str(ref)
            canonical_ref = ref_aliases.get(ref_str, ref_str) if ref_aliases else ref_str
            m = re.match(r"^([\w-]+)\s+F-(\d+)$", canonical_ref)
            if not m:
                continue
            if canonical_ref in seen_underlying_refs:
                continue
            seen_underlying_refs.add(canonical_ref)
            # Phase 6 (2026-05-18) — Codex Q2/Q3/Q4: instead of silently
            # dropping refs that don't resolve to the current device's
            # actionable_refs, surface them as muted "applies on another
            # device" entries. Pre-fix, a story with 3 refs where 2 were
            # desktop-only rendered as 2 underlying entries on desktop
            # and 1 on mobile, with no signal to the customer that the
            # finding existed elsewhere.
            entry = {
                "cluster": m.group(1),
                "index": int(m.group(2)),
                "label": canonical_ref,
            }
            if actionable_refs is not None and canonical_ref not in actionable_refs:
                entry["applies_on_other_device"] = True
                missing_refs.append(ref_str)
            underlying.append(entry)
        # Phase 6 — Codex Q3: instead of `continue`ing a story whose
        # underlying refs are ALL "applies on another device" on this
        # render surface (the desktop/mobile-only-story case), keep the
        # story and mark it as applies_on_other_device. The renderer
        # styles it as a faded/disabled card so the customer sees the
        # same Priority Path count across markdown and HTML.
        actionable_underlying = [
            u for u in underlying if not u.get("applies_on_other_device")
        ]
        story_applies_on_other_device = (
            actionable_refs is not None
            and underlying
            and len(actionable_underlying) < max(1, min_actionable_refs)
        )
        if (
            actionable_refs is not None
            and not story_applies_on_other_device
            and len(actionable_underlying) < max(1, min_actionable_refs)
        ):
            # Truly empty story (no refs at all, or all refs failed regex
            # parse) — drop. The new applies_on_other_device path handles
            # the "valid refs but all on other device" case explicitly.
            continue
        spans_clusters = sorted({u["cluster"] for u in underlying})
        out.append({
            "number": str(len(out) + 1),  # renumber after filtering
            "title": story.get("title", ""),
            "severity": (story.get("severity") or "MEDIUM").upper(),
            "fixes_count": len(actionable_underlying),
            "spans_clusters": spans_clusters,
            "description": (story.get("narrative") or "").strip(),
            "action": "",
            "underlying": underlying,
            "mode": story.get("mode"),
            "missing_refs": missing_refs,
            "degraded_ref_count": len(missing_refs),
            "raw_ref_count": len(raw_refs),
            "applies_on_other_device": story_applies_on_other_device,
        })
    return out


def _priority_story_refs_for_device(story: dict, device: str | None) -> list[str]:
    """Return refs for a story, preferring future per-device refs when present."""
    refs: list[str] = []
    seen: set[str] = set()
    refs_by_device = story.get("refs_by_device")
    if device and isinstance(refs_by_device, dict):
        for ref in refs_by_device.get(device) or []:
            ref_str = str(ref)
            if ref_str not in seen:
                refs.append(ref_str)
                seen.add(ref_str)
    for ref in story.get("f_refs") or []:
        ref_str = str(ref)
        if ref_str not in seen:
            refs.append(ref_str)
            seen.add(ref_str)
    return refs


# ---------------------------------------------------------------------------
# Top-level entry point (mirrors html_builder._load_inputs return shape)
# ---------------------------------------------------------------------------


def load_v2_engagement(
    engagement_dir: Path,
    device: str,
    plugin_path: Path,
    audit_file: str = None,
    baton_file: str = None,
    cluster_emission_paths: list[Path] | None = None,
    ethics_findings_path: Path | None = None,
) -> dict:
    """Top-level loader. Returns a dict consumable by the html_builder pipeline.

    Output keys: plugin_version, baton, meta, page_url, findings,
    priority_path_stories. Plus v2 extensions:
    synthesizer_emission, audit_md_text.
    """
    audit_file = audit_file or f"audit-{device}.md"
    if baton_file is None:
        baton_file = "baton.json" if device == "desktop" else f"baton-{device}.json"

    plugin_version = "unknown"
    for plugin_manifest in (
        plugin_path / ".codex-plugin" / "plugin.json",
        plugin_path / ".claude-plugin" / "plugin.json",
    ):
        if plugin_manifest.exists():
            try:
                plugin_version = json.loads(plugin_manifest.read_text(encoding="utf-8")).get(
                    "version", plugin_version
                )
            except (OSError, json.JSONDecodeError):
                pass
            break

    baton = json.loads((engagement_dir / baton_file).read_text(encoding="utf-8"))
    meta_path = engagement_dir / "meta.json"
    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            meta = {}

    resolved_cluster_paths = (
        list(cluster_emission_paths)
        if cluster_emission_paths is not None
        else _engagement_cluster_emission_paths(engagement_dir)
    )
    resolved_ethics_path = (
        ethics_findings_path
        if ethics_findings_path is not None
        else _engagement_ethics_findings_path(engagement_dir)
    )

    findings = load_v2_findings(
        engagement_dir,
        device,
        audit_file=audit_file,
        cluster_emission_paths=resolved_cluster_paths,
        ethics_findings_path=resolved_ethics_path,
    )
    actionable_refs = {f["f_ref"] for f in findings if f.get("f_ref")}
    _, ref_aliases, _drops = build_canonical_view(resolved_cluster_paths, resolved_ethics_path)
    priority_path_stories = load_v2_priority_path(
        engagement_dir,
        actionable_refs,
        ref_aliases=ref_aliases,
        device=device,
        min_actionable_refs=1,
    )

    # Phase G follow-up #3: inject humanized_findings (plain English summary
    # for HTML report customer voice) onto each finding dict so the renderer
    # can surface it in the detail panel above the dev-spec OBSERVATION/
    # RECOMMENDATION. v2.0 graceful: if humanized_findings array is absent
    # or doesn't cover a finding, the renderer falls back to dev-spec prose.
    synth_path = engagement_dir / "synthesizer-emission-v1.json"
    humanized_by_ref: dict = {}
    if synth_path.exists():
        try:
            synth_data = json.loads(synth_path.read_text(encoding="utf-8"))
            for h in synth_data.get("humanized_findings") or []:
                ref = h.get("f_ref")
                if ref:
                    humanized_by_ref[ref] = {
                        "plain_english_summary": h.get("plain_english_summary", ""),
                        "plain_english_action": h.get("plain_english_action", ""),
                    }
        except (OSError, json.JSONDecodeError):
            pass

    for f in findings:
        ref = f.get("f_ref")
        if ref and ref in humanized_by_ref:
            f["plain_english_summary"] = humanized_by_ref[ref]["plain_english_summary"]
            f["plain_english_action"] = humanized_by_ref[ref]["plain_english_action"]
        else:
            f["plain_english_summary"] = ""
            f["plain_english_action"] = ""

    page = meta.get("page") or {}
    page_url = (
        page.get("url")
        or meta.get("url")
        or meta.get("url_normalized")
        or baton.get("url")
    )

    audit_md_text = ""
    audit_path = engagement_dir / audit_file
    if audit_path.exists():
        try:
            audit_md_text = audit_path.read_text(encoding="utf-8")
        except (OSError, IOError):
            audit_md_text = ""

    synth_path = engagement_dir / "synthesizer-emission-v1.json"
    synthesizer_emission = {}
    if synth_path.exists():
        try:
            synthesizer_emission = json.loads(synth_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            synthesizer_emission = {}

    return {
        "plugin_version": plugin_version,
        "baton": baton,
        "meta": meta,
        "page_url": page_url,
        "findings": findings,
        "priority_path_stories": priority_path_stories,
        "audit_md_text": audit_md_text,
        "synthesizer_emission": synthesizer_emission,
    }
