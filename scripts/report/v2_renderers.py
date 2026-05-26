"""v2 alternative renderers (Phase G deliverable 5).

Multiple render targets from the same JSON source: HTML (in
v2_html_builder), markdown audit-mirror (deterministic projection from JSON
that should be byte-identical between two runs of the same input),
bulleted list (one-line-per-finding triage list), plain prose (flowing
paragraph form for executive readers), future PDF.

Determinism contract for markdown-mirror: given the same set of input
files and the same canonical f_refs manifest, two consecutive calls to
``generate_v2_alt_render(alt_format='markdown-mirror')`` produce
byte-identical output. This is a Phase K parity-test invariant. The
renderer never embeds timestamps, random IDs, or non-deterministic
ordering — finding order is alphabetical-by-cluster-then-canonical-F-NN.

Authored Phase G (2026-04-28).
"""
from __future__ import annotations

from pathlib import Path

from .v2_loader import load_v2_engagement


def _format_finding_markdown_mirror(f: dict) -> str:
    """Render one finding as v1-style structured-fields markdown.

    Output mirrors the contracts/synthesizer-v2.md "Per-finding rendering
    format" spec with the canonical f_ref heading + structured fields +
    paragraphs + ▸ citation block. The emission is deterministic — no
    timestamps, no positional ordering of dict keys (we explicitly order
    the field list).
    """
    f_ref = f.get("f_ref") or f"{f.get('cluster','unknown')} F-{f.get('index',0):02d}"
    title = f.get("title", "")
    section = f.get("section") or f.get("surface") or ""
    element = f.get("element") or "(absent)"
    source = f.get("source") or "BOTH"
    priority = f.get("priority") or "MEDIUM"
    observation = f.get("observation", "")
    recommendation = f.get("recommendation", "")
    why_matters = f.get("why_matters", "")
    citation = f.get("citation", "")
    tier = f.get("tier", "Bronze")

    parts = [f"#### {f_ref} — {title}", ""]
    parts.append(f"**SECTION:** {section}")
    parts.append(f"**ELEMENT:** {element}")
    parts.append(f"**SOURCE:** {source}")
    parts.append(f"**PRIORITY:** {priority}")
    parts.append("")
    if observation:
        parts.append(f"**OBSERVATION:** {observation}")
        parts.append("")
    if recommendation:
        parts.append(f"**RECOMMENDATION:** {recommendation}")
        parts.append("")
    if why_matters:
        parts.append(f"**Why this matters:** {why_matters}")
        parts.append("")
    if citation:
        parts.append(f"▸ {citation} [{tier}]")
        parts.append("")
    return "\n".join(parts)


def _format_finding_bulleted(f: dict) -> str:
    """Render one finding as a single bulleted-list line.

    Format: ``- [PRIORITY] {f_ref} — {title} (section: ..., element: ...)``
    Compact, scannable. Useful for triage / standup status.
    """
    f_ref = f.get("f_ref") or f"{f.get('cluster','unknown')} F-{f.get('index',0):02d}"
    title = (f.get("title") or "").strip()
    priority = (f.get("priority") or "MEDIUM").upper()
    section = (f.get("section") or f.get("surface") or "").strip()
    element = (f.get("element") or "").strip()
    bits = [f"- [{priority}] {f_ref} — {title}"]
    suffix_parts: list[str] = []
    if section:
        suffix_parts.append(f"section: {section}")
    if element and element != "(absent)":
        suffix_parts.append(f"element: {element}")
    if suffix_parts:
        bits.append(f"  ({'; '.join(suffix_parts)})")
    return "\n".join(bits)


def _format_finding_plain_prose(f: dict) -> str:
    """Render one finding as a flowing prose paragraph.

    No heading, no fields, no citation marker — just OBSERVATION +
    RECOMMENDATION joined with a sentence connector. Useful for executive
    readers who want a clean read-through without dev-spec metadata.
    """
    obs = (f.get("observation") or "").strip()
    rec = (f.get("recommendation") or "").strip()
    bits: list[str] = []
    if obs:
        bits.append(obs)
    if rec:
        # Connector lead-in
        if obs:
            bits.append(f"Resolution: {rec}")
        else:
            bits.append(rec)
    return " ".join(bits)


def _sort_key(f: dict) -> tuple:
    """Deterministic finding sort: cluster (in CLUSTER_TAB_ORDER), then F-NN.

    Markdown-mirror's byte-identical determinism contract requires this
    ordering be totally pinned regardless of input file order or hash
    iteration order.
    """
    from .utils import CLUSTER_TAB_ORDER
    cluster_priority = {c: i for i, c in enumerate(CLUSTER_TAB_ORDER)}
    cluster = f.get("cluster", "")
    f_ref = f.get("f_ref") or ""
    try:
        idx = int(f_ref.rsplit(" F-", 1)[1]) if " F-" in f_ref else f.get("index", 0)
    except (ValueError, IndexError):
        idx = f.get("index", 0)
    return (cluster_priority.get(cluster, 99), cluster, idx)


def render_markdown_mirror(engagement_dir: Path, device: str, plugin_root: Path) -> str:
    """Deterministic markdown projection of the v2 emission for ``device``.

    Output structure mirrors the synthesizer's audit-{device}.md but is
    rebuilt from the structured emission (synthesizer-emission-v1.json +
    cluster-emission JSONs) so it round-trips: render-then-parse should
    yield the same finding set.

    Phase K parity test: two consecutive calls produce byte-identical
    output (no timestamps, no positional ordering surprises).
    """
    inputs = load_v2_engagement(engagement_dir, device, plugin_root)
    findings = sorted(inputs["findings"], key=_sort_key)
    page_summary = (inputs.get("meta") or {}).get("page_summary") or ""
    if not page_summary:
        # Fall back to a generic page reference; the source-of-truth for
        # the human-readable page title is whatever the synthesizer used.
        page_summary = (inputs.get("meta") or {}).get("url") or "page"

    parts: list[str] = []
    parts.append(f"# Audit Mirror — {page_summary} ({device.title()})")
    parts.append("")
    parts.append(
        "Deterministic projection of the v2 structured emission. Re-running this command "
        "with the same inputs produces byte-identical output."
    )
    parts.append("")

    # Group findings by cluster so the structure matches the synthesizer's
    # "Findings by Cluster" section.
    from .utils import CLUSTER_LABELS, CLUSTER_TAB_ORDER, slug_to_title
    by_cluster: dict[str, list[dict]] = {}
    for f in findings:
        by_cluster.setdefault(f.get("cluster", "unknown"), []).append(f)

    cluster_order = list(CLUSTER_TAB_ORDER) + sorted(
        c for c in by_cluster if c not in CLUSTER_TAB_ORDER
    )
    parts.append("## Findings by Cluster")
    parts.append("")
    for cluster in cluster_order:
        cluster_findings = by_cluster.get(cluster) or []
        if not cluster_findings:
            continue
        cluster_label = CLUSTER_LABELS.get(cluster, slug_to_title(cluster))
        parts.append(f"### {cluster_label}")
        parts.append("")
        for f in cluster_findings:
            parts.append(_format_finding_markdown_mirror(f))

    return "\n".join(parts)


def render_bulleted(engagement_dir: Path, device: str, plugin_root: Path) -> str:
    """One-bullet-per-finding scan list, ordered by priority then cluster."""
    inputs = load_v2_engagement(engagement_dir, device, plugin_root)
    findings = inputs["findings"]
    priority_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    findings_sorted = sorted(
        findings,
        key=lambda f: (
            priority_rank.get((f.get("priority") or "MEDIUM").upper(), 9),
            *_sort_key(f),
        ),
    )

    parts: list[str] = []
    parts.append(f"# Audit Triage List — {device.title()}")
    parts.append("")
    parts.append(f"Total findings: {len(findings_sorted)}")
    parts.append("")
    for f in findings_sorted:
        parts.append(_format_finding_bulleted(f))
    parts.append("")
    return "\n".join(parts)


def render_plain_prose(engagement_dir: Path, device: str, plugin_root: Path) -> str:
    """Flowing prose form of the v2 audit, organized by Priority Path then by cluster.

    Skips the structured-fields metadata; reads as a continuous executive
    summary. Each Priority Path story renders as a heading + narrative
    paragraph; per-cluster sections compress to one paragraph per finding.
    """
    inputs = load_v2_engagement(engagement_dir, device, plugin_root)
    findings = sorted(inputs["findings"], key=_sort_key)
    priority_path = inputs.get("priority_path_stories") or []

    parts: list[str] = []
    parts.append(f"# Audit Summary — {device.title()}")
    parts.append("")

    if priority_path:
        parts.append("## Top Priorities")
        parts.append("")
        for story in priority_path:
            parts.append(f"### {story.get('title','')}")
            parts.append("")
            description = (story.get("description") or "").strip()
            if description:
                parts.append(description)
                parts.append("")

    from .utils import CLUSTER_LABELS, CLUSTER_TAB_ORDER, slug_to_title
    by_cluster: dict[str, list[dict]] = {}
    for f in findings:
        by_cluster.setdefault(f.get("cluster", "unknown"), []).append(f)

    parts.append("## Findings (continuous read)")
    parts.append("")
    cluster_order = list(CLUSTER_TAB_ORDER) + sorted(
        c for c in by_cluster if c not in CLUSTER_TAB_ORDER
    )
    for cluster in cluster_order:
        cluster_findings = by_cluster.get(cluster) or []
        if not cluster_findings:
            continue
        cluster_label = CLUSTER_LABELS.get(cluster, slug_to_title(cluster))
        parts.append(f"### {cluster_label}")
        parts.append("")
        for f in cluster_findings:
            paragraph = _format_finding_plain_prose(f)
            if paragraph:
                parts.append(paragraph)
                parts.append("")

    return "\n".join(parts)


def generate_v2_alt_render(
    engagement_dir: Path,
    device: str,
    plugin_root: Path,
    alt_format: str,
    audit_file: str | None = None,
    baton_file: str | None = None,
    output_file: str | None = None,
) -> Path:
    """Top-level entry point for v2 alt renderers.

    ``alt_format`` is one of ``markdown-mirror``, ``bulleted``, or
    ``plain-prose``. Writes to engagement_dir; returns the output Path.
    """
    engagement_path = Path(engagement_dir)
    plugin_path = Path(plugin_root)

    if alt_format == "markdown-mirror":
        text = render_markdown_mirror(engagement_path, device, plugin_path)
        default_name = f"audit-mirror-{device}.md"
    elif alt_format == "bulleted":
        text = render_bulleted(engagement_path, device, plugin_path)
        default_name = f"audit-bulleted-{device}.md"
    elif alt_format == "plain-prose":
        text = render_plain_prose(engagement_path, device, plugin_path)
        default_name = f"audit-prose-{device}.md"
    else:
        raise ValueError(f"Unknown alt_format: {alt_format}")

    output_path = engagement_path / (output_file or default_name)
    output_path.write_text(text, encoding="utf-8")
    return output_path
