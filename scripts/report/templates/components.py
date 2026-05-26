"""Component builders for the v1.0 three-panel app-shell report.

Left-rail tab builders:
- ``build_clusters_tab_html`` — collapsible cluster cards
- ``build_priority_tab_html`` — priority-path cards with clickable refs
- ``build_ethics_tab_html`` — ethics-only cards (BLOCK + ADJACENT)

Center + right panels:
- ``build_hotspot_overlays_html`` — click-to-spotlight hotspot rectangles
  over the screenshot + fallback points for head/absence findings
- ``build_detail_panels_html`` — one detail card per finding (hidden
  until the user selects the finding from the left rail)

Header chrome:
- ``build_severity_bars`` — severity distribution bar chart
- ``build_severity_text_html`` — inline severity chips + segments for
  the header summary line
- ``build_ethics_html`` — ethics pill state + violation detail HTML

Export + shared:
- ``build_export_markdown_blocks`` — per-finding markdown blocks for the
  "audit.md mirror" export format
- ``assign_cluster_indices`` — add ``cluster_index`` + ``fid`` to each
  finding (cluster-scoped F-NN numbering per Dan's 2026-04-14 feedback)

Pre-v1.0 scroll-document builders (build_tab_bar_html,
build_priority_path_cards_html, build_finding_cards_html,
build_pass_cards_html) were removed when the app-shell redesign
shipped. If a future caller needs them, the git history has the
implementations.
"""

import re

from ..utils import (
    CLUSTER_LABELS,
    CLUSTER_TAB_ORDER,
    SVG_CHECK,
    SVG_X,
    escape_html,
    slug_to_title,
    get_severity_class,
)
from ..citations import humanize_reference


# ============================================================================
# v1.0 helpers
# ============================================================================

def _finding_title(f):
    """Fallback title derivation for findings authored before v1.1.

    Since v1.1, auditors author the ``TITLE:`` field directly on every
    FAIL/PARTIAL finding (workflows/audit.md Step 4d). The caller in
    ``assign_cluster_indices`` prefers ``f.get("title")`` when present,
    so this function only runs for legacy engagements whose cluster
    files pre-date the TITLE field.

    Legacy fallback order:
    1. SECTION slug titleized — produces the v1.0 default that caused
       the duplicate-title problem this function's caller was written
       to replace. Kept to render legacy audits without crashing.
    2. First clause of OBSERVATION up to a dash/colon/period, capped at
       72 chars.
    3. ELEMENT selector, truncated.
    """
    section = f.get("section") or ""
    if section and section not in ("general", "unknown", "site-global"):
        candidate = slug_to_title(section)
        if 4 <= len(candidate) <= 60:
            return candidate

    obs = (f.get("observation") or "").strip()
    if obs:
        clause = re.split(r"\s(?:[—:]|–)\s|\. ", obs, maxsplit=1)[0]
        if len(clause) > 72:
            clause = clause[:72].rstrip(" ,;:") + "…"
        return clause

    if section:
        return slug_to_title(section)
    element = (f.get("element") or "").strip()
    if element:
        return element[:72]
    return "(untitled finding)"


# ----------------------------------------------------------------------------
# Variegated cluster colors — break up the all-amber aesthetic Dan flagged on
# 2026-04-14. Each cluster gets a 2-letter chip tinted with a pastel/dark
# accent drawn from the site's broader palette (not solid amber).
# ----------------------------------------------------------------------------

_CLUSTER_CHIP_PALETTE = {
    "visual-cta":           ("VC", "visual"),
    "trust-credibility":    ("TC", "trust"),
    "pricing":              ("PR", "price"),
    "checkout-flows":       ("CF", "checkout"),
    "performance-ux":       ("PU", "perf"),
    "product-media":        ("PM", "media"),
    "category-navigation":  ("CN", "nav"),
    "content-seo":          ("CS", "seo"),
    "post-purchase":        ("PP", "post"),
    "audience":             ("AU", "audience"),
    # Legacy v1.0 slug — maps to same chip as performance-ux so resumed
    # engagements with clusters_used: ["mobile-performance"] still render.
    "mobile-performance":   ("PU", "perf"),
}


def _cluster_chip(cluster):
    """Return (initials, palette_class) for the cluster's chip."""
    return _CLUSTER_CHIP_PALETTE.get(cluster, (_initials(cluster).upper(), "default"))


def _finding_short_code(cluster, local_index):
    """Compact label for a finding row, e.g. ``VC-01`` (visual-cta finding 1).

    Dan's 2026-04-14 feedback: the left-rail F-NN label is redundant now
    that clusters are grouped, so encode the cluster into the label itself
    via the 2-letter chip abbreviation. Collisions are impossible across
    the 10-cluster set because each cluster has a unique 2-letter code.
    """
    initials, _palette = _cluster_chip(cluster)
    return f"{initials}-{local_index:02d}"


def assign_cluster_indices(findings):
    """Mutate ``findings`` list in place: add ``cluster_index`` and ``fid``
    (``"{cluster}/F-{NN:02d}"``) using the canonical display index emitted
    by the assembly pipeline (Phase L.D content-hashed F-NN).

    Prefers ``f["display_index"]`` (the canonical value from
    ``scripts/assembly/pipeline.py:assign_display_indices``); falls back to
    parsing it out of ``f["f_ref"]`` (e.g. ``"pricing F-39"``); finally falls
    back to a positional counter for legacy paths that don't surface either
    field. The positional fallback is a last resort — when it fires, Priority
    Path links and the rendered F-NN diverge from synth's emission, which is
    what the M.2 bug surfaced.

    Returns ``(findings_by_cluster, findings_by_fid)`` as dicts keyed by
    cluster slug / fid string respectively.
    """
    findings_by_cluster = {}
    findings_by_fid = {}
    cluster_counters = {}
    for f in findings:
        cluster = f.get("cluster") or "uncategorized"
        cluster_counters.setdefault(cluster, 0)
        cluster_counters[cluster] += 1

        # Prefer canonical display_index from the pipeline; fall back to
        # parsing f_ref; finally fall back to positional counter.
        canonical_idx = f.get("display_index")
        if not canonical_idx and f.get("f_ref"):
            try:
                canonical_idx = int(str(f["f_ref"]).rsplit(" F-", 1)[1])
            except (IndexError, ValueError):
                canonical_idx = None
        f["cluster_index"] = canonical_idx or cluster_counters[cluster]
        f["fid"] = "{cluster}/F-{n:02d}".format(cluster=cluster, n=f["cluster_index"])
        # Pre-compute the cluster-prefix short code (e.g. "VC-84") so the
        # JS runtime callout can match the sidebar's label format. Without
        # this, the sidebar shows "VC-84" while the hotspot tooltip shows
        # "F-84" for the same finding — same number, different prefix.
        f["short_code"] = _finding_short_code(cluster, f["cluster_index"])
        f["title"] = f.get("title") or _finding_title(f)
        findings_by_cluster.setdefault(cluster, []).append(f)
        findings_by_fid[f["fid"]] = f
    return findings_by_cluster, findings_by_fid


def _initials(cluster):
    """Two-letter tag for the cluster chip (e.g. visual-cta -> VC)."""
    parts = [p for p in re.split(r"[\s\-/]+", cluster) if p]
    if not parts:
        return (cluster[:2] or "?").upper()
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def build_clusters_tab_html(findings_by_cluster):
    """Render the "By Cluster" tab of the left rail.

    Each cluster becomes a collapsible card. Clusters are ordered per
    ``CLUSTER_TAB_ORDER`` when known, else alphabetically. Inside a card,
    findings are shown in parse order (= F-01, F-02, ...) — not re-sorted
    by severity, because parse order already reflects auditor-chosen
    priority within the cluster.
    """
    if not findings_by_cluster:
        return '<div class="panel-empty">No findings in this audit.</div>'

    known = [c for c in CLUSTER_TAB_ORDER if c in findings_by_cluster]
    unknown = sorted(c for c in findings_by_cluster if c not in set(known))
    ordered = known + unknown

    parts = []
    for cluster in ordered:
        items = findings_by_cluster[cluster]
        cluster_label = CLUSTER_LABELS.get(cluster, slug_to_title(cluster))
        total = len(items)
        # Cluster severity summary: lead with the WORST severity present and
        # show its count. Old logic was `max` by (count, priority_desc) which
        # let plurality dominate — a cluster with 3 HIGH + 4 MEDIUM rendered
        # "4 MEDIUM" even though HIGH findings were present (codebase audit
        # #4, 2026-04-14). Fixed by scanning CRITICAL -> HIGH -> MEDIUM ->
        # LOW in that order and stopping at the first non-zero bucket.
        sev_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for f in items:
            sev = (f.get("priority") or "MEDIUM").upper()
            sev_counts[sev] = sev_counts.get(sev, 0) + 1
        top_sev = "MEDIUM"
        top_count = 0
        for candidate in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            if sev_counts.get(candidate, 0) > 0:
                top_sev = candidate
                top_count = sev_counts[candidate]
                break
        top_sev_class = get_severity_class(top_sev)

        rows_html = []
        for f in items:
            fid = f["fid"]
            sev = (f.get("priority") or "MEDIUM").upper()
            sev_class = get_severity_class(sev)
            short_code = _finding_short_code(cluster, f["cluster_index"])
            rows_html.append(
                '<div class="finding-row" data-fid="{fid}" tabindex="0">'
                '<span class="finding-check" role="checkbox" aria-checked="false"></span>'
                '<div class="finding-body">'
                '<div class="finding-head-line">'
                '<span class="finding-id">{code}</span>'
                '<span class="finding-sev {sev_class}">{sev}</span>'
                '</div>'
                '<div class="finding-title">{title}</div>'
                '</div>'
                '</div>'.format(
                    fid=escape_html(fid),
                    code=escape_html(short_code),
                    sev_class=sev_class,
                    sev=sev,
                    title=escape_html(f["title"]),
                )
            )

        expanded_class = " expanded" if cluster == ordered[0] else ""
        chip_initials, chip_palette = _cluster_chip(cluster)
        parts.append(
            '<div class="cluster-card{exp}" data-cluster="{slug}">'
            '<div class="cluster-head" role="button" tabindex="0" aria-expanded="{ariaexp}">'
            '<span class="cluster-chip chip-{palette}">{initials}</span>'
            '<div class="cluster-info">'
            '<div class="cluster-name">{label}</div>'
            '<div class="cluster-meta">'
            '<span class="cluster-count">{total} finding{plural}</span>'
            '{sev_tag}'
            '</div>'
            '</div>'
            '<span class="cluster-chev">\u25bc</span>'
            '</div>'
            '<div class="cluster-body">{rows}</div>'
            '</div>'.format(
                exp=expanded_class,
                ariaexp="true" if expanded_class else "false",
                slug=escape_html(cluster),
                initials=escape_html(chip_initials),
                palette=chip_palette,
                label=escape_html(cluster_label),
                total=total,
                plural="s" if total != 1 else "",
                sev_tag=(
                    '<span class="cluster-sev-tag {cls}">{n} {sev}</span>'.format(
                        cls=top_sev_class, n=top_count, sev=top_sev
                    )
                    if top_count > 0 else ""
                ),
                rows="".join(rows_html),
            )
        )
    return "".join(parts)


def build_priority_tab_html(priority_path_stories, findings_by_fid):
    """Render the "Priority Path" tab of the left rail.

    Each story is a card. The card header has a numbered pill + the story
    title. Under the card, each underlying finding ref (``{cluster} F-NN``)
    gets a clickable row with its own brief checkbox. Rows use the same
    ``data-fid`` as the findings-by-cluster tab so brief state stays in sync.
    """
    if not priority_path_stories:
        return '<div class="panel-empty">No priority path stories for this audit.</div>'

    parts = []
    for i, story in enumerate(priority_path_stories, 1):
        title = escape_html(story.get("title") or f"Priority {i}")
        spans = story.get("spans_clusters") or []
        # Parser uses "fixes_count" + "underlying" (not the earlier draft names
        # "fixes_findings" / "underlying_findings") — keep both for safety.
        fix_n = story.get("fixes_count") or story.get("fixes_findings")
        cluster_n = len(spans) or story.get("spans_cluster_count")
        meta_bits = []
        if fix_n:
            meta_bits.append(f"Fixes {fix_n} findings")
        if cluster_n:
            meta_bits.append(f"across {cluster_n} cluster{'s' if cluster_n != 1 else ''}")
        if spans:
            meta_bits.append("(" + ", ".join(escape_html(s) for s in spans) + ")")
        meta_line = " ".join(meta_bits)

        story_action = story.get("action") or story.get("description") or ""

        # Phase 6 (2026-05-18) — Codex Q2/Q3/Q4: cross-device Priority
        # Path coverage. Cards whose refs ALL resolve on the other device
        # render as faded "applies elsewhere" cards instead of being
        # dropped. Per-ref applies_on_other_device entries render as
        # muted struck-through rows so the customer can see the finding
        # exists on the other device.
        story_applies_elsewhere = bool(story.get("applies_on_other_device"))

        ref_rows = []
        for ref in story.get("underlying") or story.get("underlying_findings") or []:
            cluster = ref.get("cluster")
            idx = ref.get("index") or 0
            if not cluster or not idx:
                continue
            fid = f"{cluster}/F-{idx:02d}"
            ref_applies_elsewhere = bool(ref.get("applies_on_other_device"))
            row_class = "priority-ref-row"
            if ref_applies_elsewhere:
                row_class += " underlying-applies-elsewhere"
            finding = findings_by_fid.get(fid)
            if ref_applies_elsewhere:
                # Phase 6 hardening (2026-05-18) — Codex 19a4f51 review.
                # The faded row is non-interactive: no detail card exists
                # for this fid on the current device, so DO NOT attach
                # data-fid. The shared click delegator
                # (templates/js.py "Delegated click handler") gates on
                # `row.hasAttribute('data-fid')` — without the attribute,
                # click / brief-toggle / select-all-visible / keyboard nav
                # all naturally skip the row. The display-only `data-ref`
                # carries the f_ref string for hover/tooltip + tests;
                # `data-applies-on-other-device="true"` is the sentinel
                # any future selector should use to find these rows.
                # `aria-disabled` on the wrapper makes screen readers
                # announce the disabled state.
                ref_rows.append(
                    '<div class="{cls}" data-ref="{fid}" data-applies-on-other-device="true" '
                    'aria-disabled="true" title="This finding applies on the other device — see that device\'s report">'
                    '<span class="priority-ref-check" role="checkbox" aria-checked="false" aria-disabled="true"></span>'
                    '<span class="priority-ref-label"><strong>{fid}</strong> — applies on the other device</span>'
                    '</div>'.format(cls=row_class, fid=escape_html(fid))
                )
                continue
            if finding is None:
                ref_rows.append(
                    '<div class="{cls}" data-fid="{fid}">'
                    '<span class="priority-ref-check" role="checkbox" aria-checked="false"></span>'
                    '<span class="priority-ref-label"><strong>{fid}</strong> — (not found)</span>'
                    '</div>'.format(cls=row_class, fid=escape_html(fid))
                )
                continue
            ref_rows.append(
                '<div class="{cls}" data-fid="{fid}">'
                '<span class="priority-ref-check" role="checkbox" aria-checked="false"></span>'
                '<span class="priority-ref-label"><strong>{fid}</strong> — {title}</span>'
                '</div>'.format(
                    cls=row_class,
                    fid=escape_html(fid),
                    title=escape_html(finding["title"]),
                )
            )

        card_class = "priority-card"
        applies_elsewhere_banner = ""
        if story_applies_elsewhere:
            card_class += " priority-card-applies-elsewhere"
            applies_elsewhere_banner = (
                '<div class="priority-card-elsewhere-banner" '
                'title="Underlying findings live on the other device — switch to the other device\'s report to act on this priority">'
                'Applies on the other device — see that device\'s report'
                '</div>'
            )

        parts.append(
            '<div class="{cls}">'
            '<div class="priority-card-head">'
            '<span class="priority-card-num">{n}</span>'
            '<span class="priority-card-title">{title}</span>'
            '</div>'
            '{banner}'
            '{meta}'
            '{action}'
            '<div class="priority-refs-label">Underlying findings</div>'
            '<div class="priority-refs">{refs}</div>'
            '</div>'.format(
                cls=card_class,
                n=i,
                title=title,
                banner=applies_elsewhere_banner,
                meta=f'<div class="priority-card-meta">{escape_html(meta_line)}</div>' if meta_line else "",
                action=(
                    f'<div class="priority-card-action">{escape_html(story_action[:260])}{"…" if len(story_action) > 260 else ""}</div>'
                    if story_action else ""
                ),
                refs="".join(ref_rows) if ref_rows else '<div class="priority-ref-row" style="font-size:11px;color:var(--text-muted);font-style:italic;padding:6px 4px">No specific findings listed.</div>',
            )
        )
    return "".join(parts)


def build_ethics_tab_html(findings_by_fid):
    """Render the "Ethics" tab of the left rail.

    Lists every finding whose ``ethics_state`` is BLOCK or ADJACENT,
    regardless of cluster. BLOCK items render first, then ADJACENT.
    """
    ethics = [
        f for f in findings_by_fid.values()
        if (f.get("ethics_state") or "").upper() in ("BLOCK", "ADJACENT")
    ]
    if not ethics:
        return '<div class="ethics-empty">No ethics findings. <br><br>Ethics findings are BLOCK (hard violations) or ADJACENT (one step from a violation). A clean slate here means nothing in the audit triggered the ethics gate.</div>'

    ethics.sort(key=lambda f: (0 if f.get("ethics_state").upper() == "BLOCK" else 1, f.get("cluster", ""), f.get("cluster_index", 0)))

    parts = []
    for f in ethics:
        state = (f.get("ethics_state") or "").upper()
        state_class = "block" if state == "BLOCK" else "adjacent"
        source_url = f.get("source_url") or ""
        parts.append(
            '<div class="ethics-card {state_class}">'
            '<div class="ethics-card-head">'
            '<span class="ethics-state-pill {state_class}">{state}</span>'
            '<span class="ethics-card-title">{title}</span>'
            '</div>'
            '<div class="finding-row" data-fid="{fid}" style="border:none;padding:0;margin:0">'
            '<span class="finding-check" role="checkbox" aria-checked="false"></span>'
            '<div class="finding-body">'
            '<div class="finding-head-line">'
            '<span class="finding-id">{fid_short}</span>'
            '<span class="finding-sev {sev_class}">{sev}</span>'
            '<span style="font-size:10px;color:var(--text-muted);margin-left:4px">{cluster_label}</span>'
            '</div>'
            '<div class="finding-title" style="font-size:11.5px">Click to open details.</div>'
            '</div>'
            '</div>'
            '{url}'
            '</div>'.format(
                state_class=state_class,
                state=state,
                title=escape_html(f["title"]),
                fid=escape_html(f["fid"]),
                fid_short=escape_html(f["fid"].split("/")[-1]),
                sev_class=get_severity_class(f.get("priority") or "MEDIUM"),
                sev=(f.get("priority") or "MEDIUM").upper(),
                cluster_label=escape_html(CLUSTER_LABELS.get(f.get("cluster", ""), f.get("cluster", ""))),
                url=(
                    '<a class="ethics-card-link" href="{u}" target="_blank" rel="noopener noreferrer">{u}</a>'.format(u=escape_html(source_url))
                    if source_url else ""
                ),
            )
        )
    return "".join(parts)


def build_detail_panels_html(findings):
    """Render one ``.detail-card`` per finding. All hidden until the user
    selects a finding via ``selectFinding(fid)`` in the runtime JS."""
    parts = []
    for f in findings:
        fid = f["fid"]
        sev = (f.get("priority") or "MEDIUM").upper()
        sev_class = get_severity_class(sev)
        cluster = f.get("cluster", "")
        cluster_label = CLUSTER_LABELS.get(cluster, slug_to_title(cluster))
        ethics_state = (f.get("ethics_state") or "").upper()
        source_url = f.get("source_url") or ""
        citation = f.get("citation") or ""
        tier = (f.get("tier") or "").title()
        tier_class = tier.lower()

        ethics_banner = ""
        if ethics_state in ("BLOCK", "ADJACENT"):
            banner_class = "block" if ethics_state == "BLOCK" else ""
            ethics_banner = (
                '<div class="detail-ethics-banner {cls}">'
                '<strong>ETHICS: {state}</strong> — this finding flags a compliance risk that is tracked on the Ethics tab.'
                '</div>'.format(cls=banner_class, state=ethics_state)
            )

        sections_html = []
        # v2 humanized voice (Phase G follow-up #3): plain English summary
        # surfaced FIRST so the operator/customer reading the HTML report
        # gets the business-context framing before the dev-spec details.
        # When absent (v1 findings, or v2 humanized_findings entry missing),
        # the section is silently skipped and the renderer falls back to
        # the dev-spec OBSERVATION/RECOMMENDATION below.
        if f.get("plain_english_summary"):
            summary_html = (
                '<div class="detail-section detail-summary-card">'
                '<div class="detail-text">{t}</div>'
            ).format(t=escape_html(f.get("plain_english_summary")))
            if f.get("plain_english_action"):
                summary_html += (
                    '<div class="detail-summary-action">'
                    '<strong>What changes:</strong> {a}'
                    '</div>'
                ).format(a=escape_html(f.get("plain_english_action")))
            summary_html += '</div>'
            sections_html.append(summary_html)
        if f.get("element"):
            sections_html.append(
                '<div class="detail-section">'
                '<h4>Element</h4>'
                '<div class="detail-element">{el}</div>'
                '</div>'.format(el=escape_html(f.get("element")))
            )
        if f.get("observation"):
            sections_html.append(
                '<div class="detail-section">'
                '<h4>Observation</h4>'
                '<div class="detail-text">{t}</div>'
                '</div>'.format(t=escape_html(f.get("observation")))
            )
        if f.get("recommendation"):
            sections_html.append(
                '<div class="detail-section">'
                '<h4>Recommendation</h4>'
                '<div class="detail-rec">{t}</div>'
                '</div>'.format(t=escape_html(f.get("recommendation")))
            )
        if f.get("why_matters"):
            sections_html.append(
                '<div class="detail-section">'
                '<h4>Why this matters</h4>'
                '<div class="detail-text">{t}</div>'
                '</div>'.format(t=escape_html(f.get("why_matters")))
            )
        # v2: per-finding evidence anchors panel (Phase G deliverable 4).
        # When v2_html_builder pre-attaches ``evidence_anchors_html`` to each
        # finding (a ready-to-include HTML snippet listing anchor type/
        # reference/context with screenshot link), surface it here. v1
        # findings don't carry this key so the section is silently skipped.
        if f.get("evidence_anchors_html"):
            sections_html.append(f.get("evidence_anchors_html"))
        if citation or source_url or tier:
            source_name = humanize_reference(f.get("reference")) or citation or "Research reference"
            tier_badge = f'<span class="tier {tier_class}">{escape_html(tier.upper())}</span>' if tier else ""
            url_link = (
                f'<a href="{escape_html(source_url)}" target="_blank" rel="noopener noreferrer">Open primary source ↗</a>'
                if source_url else ""
            )
            sections_html.append(
                '<div class="detail-section">'
                '<h4>Source</h4>'
                '<div class="detail-source">'
                '<div class="detail-source-name">{name}</div>'
                '<div class="detail-source-tier">{tier}{url}</div>'
                '</div>'
                '</div>'.format(
                    name=escape_html(source_name),
                    tier=tier_badge,
                    url=url_link,
                )
            )

        short_code = _finding_short_code(cluster, f.get("cluster_index") or 0)
        parts.append(
            '<div class="detail-card" data-fid="{fid}">'
            '<div class="detail-head">'
            '<div class="detail-head-row">'
            '<span class="detail-id">{code}</span>'
            '<span class="detail-sev {sev_class}">{sev}</span>'
            '<span class="detail-cluster-tag">{cluster_label}</span>'
            '</div>'
            '<div class="detail-title">{title}</div>'
            '</div>'
            '<div class="detail-body">{ethics}{sections}</div>'
            '<div class="detail-actions">'
            '<button class="detail-btn detail-btn-skip">Skip</button>'
            '<button class="detail-btn detail-btn-editor-queue" data-fid="{fid}">Queue edit</button>'
            '<button class="detail-btn detail-btn-editor-open" data-fid="{fid}">Open editor</button>'
            '<button class="detail-btn detail-btn-add" data-fid="{fid}">Add to brief</button>'
            '</div>'
            '</div>'.format(
                fid=escape_html(fid),
                code=escape_html(short_code),
                sev_class=sev_class,
                sev=sev,
                cluster_label=escape_html(cluster_label),
                title=escape_html(f["title"]),
                ethics=ethics_banner,
                sections="".join(sections_html),
            )
        )
    return "".join(parts)


def build_hotspot_overlays_html(findings, slide_markers):
    """Render clickable hotspot rectangles over the screenshot.

    ``slide_markers`` is ``{slide_idx: [marker, ...]}`` from
    ``compute_marker_positions``. Each marker has ``number`` (the global
    finding index), ``x_pct``/``y_pct``, ``severity``, and optionally a
    ``zone`` dict with pixel-percentage bounding box.

    The hotspot's ``data-fid`` comes from the finding at the corresponding
    global index — we look it up via the ``findings`` list (1-based indices).
    """
    findings_by_idx = {f.get("index"): f for f in findings}
    parts = []
    for slide_idx, markers in slide_markers.items():
        for m in markers:
            # m["number"] is now the cluster-local F-NN (matches the burned PNG);
            # m["finding_index"] carries the global index used to look up the
            # finding record. Falls back to "number" for legacy manual markers.
            global_idx = m.get("finding_index") or m.get("number")
            finding = findings_by_idx.get(global_idx)
            if finding is None:
                continue
            fid = finding["fid"]
            sev = m.get("severity") or "medium"
            zone = m.get("zone")
            if zone and zone.get("w_pct", 0) >= 2 and zone.get("h_pct", 0) >= 2:
                # Zone rectangle — primary case for element-pinned findings.
                marker_style = _hotspot_inline_style(m)
                marker_class = _hotspot_class(m)
                marker_data = _hotspot_data_attrs(m)
                parts.append(
                    '<div class="{cls}" hidden data-slide="{s}" data-fid="{fid}" data-severity="{sev}" data-number="{n}" {data}'
                    'style="left:{l:.2f}%;top:{t:.2f}%;width:{w:.2f}%;height:{h:.2f}%;{style}" '
                    'title="Finding {fid_short}"></div>'.format(
                        cls=marker_class,
                        s=int(slide_idx), fid=escape_html(fid), sev=escape_html(sev),
                        n=finding["cluster_index"], fid_short=escape_html(fid.split("/")[-1]),
                        l=zone["left_pct"], t=zone["top_pct"],
                        w=zone["w_pct"], h=zone["h_pct"],
                        data=marker_data,
                        style=marker_style,
                    )
                )
            else:
                # Point fallback — head-scoped / absence / tiny-element findings.
                cx = m.get("x_pct") or 92
                cy = m.get("y_pct") or 10
                marker_style = _hotspot_inline_style(m)
                marker_class = _hotspot_class(m)
                marker_data = _hotspot_data_attrs(m)
                parts.append(
                    '<div class="{cls}" hidden data-slide="{s}" data-fid="{fid}" data-severity="{sev}" data-number="{n}" {data}'
                    'style="left:calc({cx:.2f}% - 16px);top:calc({cy:.2f}% - 16px);width:32px;height:32px;border-radius:50%;{style}" '
                    'title="Finding {fid_short}"></div>'.format(
                        cls=marker_class,
                        s=int(slide_idx), fid=escape_html(fid), sev=escape_html(sev),
                        n=finding["cluster_index"], fid_short=escape_html(fid.split("/")[-1]),
                        cx=cx, cy=cy,
                        data=marker_data,
                        style=marker_style,
                    )
                )
    return "".join(parts)


def _hotspot_class(marker):
    shape = (marker.get("shape") or "rect").lower()
    classes = ["hotspot"]
    if shape == "ellipse":
        classes.append("hotspot-ellipse")
    # Phase 2 visual evidence taxonomy — emit a typed class so the CSS can
    # render each visual_evidence.type with distinct styling (solid rect,
    # dashed proxy, ghost overlay, section pill, page banner). The renderer's
    # CSS is in scripts/report/templates/styles.py; rules are scoped to
    # `.hotspot.hotspot-ve-<type>` so legacy reports without visual_evidence
    # render unchanged.
    ve = marker.get("visual_evidence") or {}
    ve_type = ve.get("type")
    if ve_type:
        # Sanitize: only emit known type strings as CSS classes.
        if ve_type in (
            "exact_element", "proxy_element", "generated_expected_zone",
            "section_absence", "page_level",
        ):
            classes.append("hotspot-ve-" + ve_type.replace("_", "-"))
    ve_confidence = ve.get("confidence")
    if ve_confidence in ("high", "medium", "low", "needs_review"):
        classes.append("hotspot-ve-conf-" + ve_confidence.replace("_", "-"))
    return " ".join(classes)


def _hotspot_data_attrs(marker):
    attrs = []
    style_tokens = []
    highlight_style = str(marker.get("highlight_style") or "").strip().lower()
    if highlight_style:
        style_tokens.append(highlight_style)
    if marker.get("spotlight_visible") and "spotlight" not in style_tokens:
        style_tokens.append("spotlight")
    try:
        fill_opacity = float(marker.get("fill_opacity") or 0)
    except (TypeError, ValueError):
        fill_opacity = 0.0
    if fill_opacity > 0 and "fill" not in style_tokens:
        style_tokens.append("fill")
    try:
        glow_opacity = float(marker.get("glow_opacity") or 0)
    except (TypeError, ValueError):
        glow_opacity = 0.0
    if glow_opacity > 0 and "glow" not in style_tokens:
        style_tokens.append("glow")
    if style_tokens:
        attrs.append('data-review-style="{style}"'.format(style=escape_html(" ".join(style_tokens))))
    safe_color = _safe_hex_color(marker.get("stroke"))
    if safe_color:
        attrs.append('data-review-color="{color}"'.format(color=escape_html(safe_color)))
    return (" ".join(attrs) + " ") if attrs else ""


def _hotspot_inline_style(marker):
    color = _safe_hex_color(marker.get("stroke"))
    if not color:
        return ""
    style = [f"border-color:{color};"]
    fill_opacity = marker.get("fill_opacity")
    try:
        fill_opacity = float(fill_opacity)
    except (TypeError, ValueError):
        fill_opacity = 0.0
    if fill_opacity > 0:
        style.append(f"background:{_hex_to_rgba(color, min(fill_opacity, 0.85))};")
    glow_opacity = marker.get("glow_opacity")
    try:
        glow_opacity = float(glow_opacity)
    except (TypeError, ValueError):
        glow_opacity = 0.0
    if (marker.get("highlight_style") or "").lower() == "glow" or glow_opacity > 0:
        opacity = glow_opacity if glow_opacity > 0 else 0.65
        style.append(
            "box-shadow:0 0 0 2px rgba(0,0,0,0.55),"
            f"0 0 22px {_hex_to_rgba(color, min(opacity, 0.95))},"
            f"0 0 48px {_hex_to_rgba(color, min(opacity * 0.6, 0.75))};"
        )
    if (marker.get("shape") or "").lower() == "ellipse":
        style.append("border-radius:999px;")
    return "".join(style)


def _safe_hex_color(value):
    if not isinstance(value, str):
        return ""
    value = value.strip()
    if re.fullmatch(r"#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?", value):
        return value
    return ""


def _hex_to_rgba(value, opacity):
    value = value.strip()
    if not value.startswith("#") or len(value) not in (4, 7):
        return f"rgba(255,255,255,{opacity:.3f})"
    if len(value) == 4:
        r = int(value[1] * 2, 16)
        g = int(value[2] * 2, 16)
        b = int(value[3] * 2, 16)
    else:
        r = int(value[1:3], 16)
        g = int(value[3:5], 16)
        b = int(value[5:7], 16)
    return f"rgba({r},{g},{b},{opacity:.3f})"


def build_export_markdown_blocks(findings, audit_md_text):
    """Build the ``EXPORT_MARKDOWN`` list the JS runtime uses for the
    "Markdown (audit mirror)" export format.

    Each entry is ``{"fid": str, "block": str}``. The ``block`` string is
    the verbatim FINDING code-fenced block from ``audit.md`` (if we can
    find it) — preserving original formatting. If we can't match, we
    synthesize a minimal block from the structured fields.
    """
    # Index FINDING blocks in audit.md by their sequential appearance order.
    raw_blocks = []
    for m in re.finditer(r"```\s*\nFINDING:\s*(?:FAIL|PARTIAL)\s*\n(.*?)\n```", audit_md_text, re.DOTALL):
        raw_blocks.append("```\nFINDING: " + m.group(0).split("FINDING: ", 1)[1])
    out = []
    for i, f in enumerate(findings):
        fid = f["fid"]
        block = raw_blocks[i] if i < len(raw_blocks) else _synthesize_block(f)
        out.append({"fid": fid, "block": block})
    return out


def _synthesize_block(f):
    """Fallback FINDING block when audit.md's raw block isn't available."""
    lines = [
        "```",
        f"FINDING: {f.get('verdict', 'FAIL')}",
        f"CLUSTER: {f.get('cluster', 'uncategorized')} ({f['fid']})",
    ]
    for key_upper, val_key in [
        ("SECTION", "section"), ("ELEMENT", "element"),
        ("PRIORITY", "priority"), ("OBSERVATION", "observation"),
        ("RECOMMENDATION", "recommendation"), ("REFERENCE", "reference"),
        ("ETHICS_STATE", "ethics_state"), ("SOURCE_URL", "source_url"),
    ]:
        v = f.get(val_key)
        if v:
            lines.append(f"{key_upper}: {v}")
    lines.append("```")
    return "\n".join(lines)



def build_severity_bars(severity_counts):
    """Build severity distribution bar HTML."""
    max_count = max(severity_counts.values()) if any(severity_counts.values()) else 1
    severity_bars = ""
    for sev_name in ["critical", "high", "medium", "low"]:
        count = severity_counts[sev_name]
        if count > 0:
            width_pct = count / max_count * 100
            severity_bars += f'''
      <div class="severity-bar">
        <div class="severity-bar-header">
          <span class="severity-bar-label">{sev_name.title()}</span>
          <span class="severity-bar-count {sev_name}">{count}</span>
        </div>
        <div class="severity-bar-track">
          <div class="severity-bar-fill {sev_name}" style="width:{width_pct:.0f}%"></div>
        </div>
      </div>
'''
    return severity_bars


def build_severity_text_html(severity_counts, total_findings):
    """Build inline severity stats, segments, and text HTML."""
    severity_total = max(total_findings, 1)
    severity_inline_stats = ""
    severity_inline_segments = ""
    severity_text_items = []
    for sev_name in ["critical", "high", "medium", "low"]:
        count = severity_counts[sev_name]
        if count > 0:
            width_pct = count / severity_total * 100
            severity_inline_stats += f'<span class="summary-severity-chip {sev_name}">{sev_name[0].upper()} {count}</span>'
            severity_inline_segments += f'<span class="summary-severity-fill {sev_name}" style="width:{width_pct:.1f}%"></span>'
            severity_text_items.append(
                f'<span class="summary-severity-item {sev_name}"><span class="summary-severity-dot {sev_name}"></span><span>{count} {sev_name.title()}</span></span>'
            )

    severity_text_html = '<span class="summary-severity-text">' + '<span class="summary-severity-separator">·</span>'.join(severity_text_items) + '</span>'

    return severity_inline_stats, severity_inline_segments, severity_text_html


def build_ethics_html(has_ethics_violations, findings):
    """Build ethics card and violation detail HTML."""
    if has_ethics_violations:
        ethics_main = "FAIL"
        ethics_main_class = "critical"
        ethics_note = "Dark pattern detected in findings"
        ethics_icon = SVG_X
    else:
        ethics_main = "PASS"
        ethics_main_class = "green"
        ethics_note = "No dark patterns detected"
        ethics_icon = SVG_CHECK

    ethics_violation_detail_html = ""
    if has_ethics_violations:
        violating = []
        for f in findings:
            priority = (f.get("priority") or "").upper()
            ref = (f.get("reference") or "").lower()
            obs = (f.get("observation") or "").lower()
            if priority == "CRITICAL" and (
                "ethics" in ref
                or "ftc" in obs
                or "fake review" in obs
                or "dsa art" in obs
                or "dark pattern" in obs
            ):
                violating.append(f)

        if violating:
            link_items = []
            for vf in violating:
                vf_idx = vf.get("index", 0)
                section_title = slug_to_title(vf.get("section", "unknown"))
                cluster_slug = vf.get("cluster", "")
                cluster_label = CLUSTER_LABELS.get(cluster_slug, cluster_slug)
                link_items.append(
                    f'<a class="ethics-violation-link" href="#finding-{vf_idx}" '
                    f'data-finding-target="{vf_idx}">'
                    f'<span class="ethics-violation-num">#{vf_idx:02d}</span>'
                    f'<span class="ethics-violation-label">{escape_html(section_title)}</span>'
                    f'<span class="ethics-violation-cluster">{escape_html(cluster_label)}</span>'
                    f'</a>'
                )
            count = len(violating)
            count_label = f"{count} violation{'s' if count != 1 else ''}"
            ethics_violation_detail_html = (
                f'<div class="ethics-violation-detail">'
                f'<div class="ethics-violation-count">{count_label} — click to review</div>'
                f'<div class="ethics-violation-list">{"".join(link_items)}</div>'
                f'</div>'
            )

    return ethics_main, ethics_main_class, ethics_note, ethics_icon, ethics_violation_detail_html
