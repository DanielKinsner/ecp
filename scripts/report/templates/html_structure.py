"""HTML skeleton for the v1.0 three-panel app-shell report.

Redesigned 2026-04-14: the old scroll-document layout (single vertical
stream of summary cards + sticky screenshot + long finding stack)
becomes a three-panel app shell:

  header                              — engagement info + Export button
  main (3-col flex):
    panel-left   (400px)              — tab switcher + cluster / priority / ethics lists
    panel-center (flex:1)             — screenshot + hotspot zones + nav
    panel-right  (400px)              — selected-finding detail OR empty state
  bottom-bar                          — brief counter + Export

Dark chrome is preserved (#0f0f0f outer / #141414 panels / amber headline
accent / severity palette). Findings are re-numbered per cluster
(F-01..F-NN within each cluster) per Dan's 2026-04-14 feedback — the
single-stream "All" numbering felt unorganized on a 74-finding audit.
"""

from ..utils import escape_html
from .css import get_report_css
from .js import get_report_js


def assemble_html(ctx):
    """Assemble the complete HTML report from a context dictionary."""
    font_css = ctx["font_css"]
    device_frame_css = ctx["device_frame_css"]
    engagement_id = ctx["engagement_id"]
    device = ctx["device"]
    editor_href = ctx.get("editor_href", "editor.html")
    page_url = ctx["page_url"]
    ethics_main = ctx["ethics_main"]
    ethics_main_class = ctx["ethics_main_class"]
    ethics_icon = ctx["ethics_icon"]
    severity_counts = ctx.get("severity_counts") or {}

    # Build the inline severity breakdown for the header — chips colored
    # per severity, zero-count severities omitted. Gives instant urgency
    # read without the user having to open a cluster.
    severity_chips_parts = []
    for sev_key, sev_label in (
        ("critical", "CRITICAL"),
        ("high", "HIGH"),
        ("medium", "MEDIUM"),
        ("low", "LOW"),
    ):
        count = severity_counts.get(sev_key, 0)
        if count > 0:
            severity_chips_parts.append(
                f'<span class="header-sev-chip {sev_key}"><strong>{count}</strong>&nbsp;{sev_label}</span>'
            )
    severity_chips_html = "".join(severity_chips_parts)

    # Left-panel tab contents
    clusters_tab_html = ctx["clusters_tab_html"]
    priority_tab_html = ctx["priority_tab_html"]
    ethics_tab_html = ctx["ethics_tab_html"]
    default_tab = "priority" if ctx.get("has_priority_path_stories") else "clusters"
    clusters_active = " active" if default_tab == "clusters" else ""
    priority_active = " active" if default_tab == "priority" else ""
    clusters_selected = "true" if default_tab == "clusters" else "false"
    priority_selected = "true" if default_tab == "priority" else "false"
    clusters_hidden = "" if default_tab == "clusters" else " hidden"
    priority_hidden = "" if default_tab == "priority" else " hidden"

    # Center panel
    initial_slide_aspect_ratio = ctx["initial_slide_aspect_ratio"]
    hotspot_overlays_html = ctx["hotspot_overlays_html"]
    device_stand_html = ctx["device_stand_html"]
    has_screenshots = ctx.get("has_screenshots", True)

    # M3 — swap the empty-state hint based on whether screenshots are
    # available. Text-only audits (file mode, description mode, acquisition
    # failure) don't have a center screenshot, so the "outlined on the
    # screenshot" language is misleading. The JS runtime also keeps the
    # empty-state visible permanently in this mode (see selectFinding gate
    # in js.py) so the hint below is what the user sees throughout.
    empty_state_hint = (
        "The chosen finding will appear here with its zone outlined on the screenshot."
        if has_screenshots
        else "This audit has no screenshots — select a finding to read its detail in the right panel."
    )

    # Right panel (detail cards per finding, hidden until selected)
    detail_panels_html = ctx["detail_panels_html"]

    # Footer / metadata
    plugin_version = ctx["plugin_version"]
    generated_date = ctx["generated_date"]
    device_label = ctx["device_label"]
    total_findings = ctx["total_findings"]
    ethics_count = ctx.get("ethics_count", 0)
    clusters_count = ctx.get("clusters_count", 0)
    page_type = ctx["page_type"]
    platform = ctx["platform"]
    source_mode = ctx["source_mode"]
    date_str = ctx["date_str"]

    # JSON payloads for JS runtime
    slide_sources_json = ctx["slide_sources_json"]
    slide_aspect_ratios_json = ctx["slide_aspect_ratios_json"]
    findings_json = ctx["findings_json"]
    export_markdown_json = ctx["export_markdown_json"]

    report_css = get_report_css(device_frame_css)
    report_js = get_report_js(
        slide_sources_json, slide_aspect_ratios_json,
        findings_json, export_markdown_json,
        engagement_id=engagement_id,
        device=device,
        editor_href=editor_href,
    )

    # Bold PASS / ADVISORY / BLOCK pill in the header — always rendered,
    # state-colored so the user sees ethics standing at a glance without
    # having to open the Ethics tab.
    if ethics_count == 0:
        ethics_label = "ETHICS: PASS"
        ethics_state_class = "pass"
    else:
        upper = (ethics_main or "").upper()
        if "BLOCK" in upper or "CRITICAL" in upper or "FAIL" in upper or "VIOLATION" in upper:
            ethics_label = "ETHICS: BLOCK"
            ethics_state_class = "block"
        else:
            ethics_label = f"ETHICS: ADVISORY ({ethics_count})"
            ethics_state_class = "advisory"
    ethics_pill_html = (
        f'<button class="ethics-pill {ethics_state_class}" '
        f'onclick="switchTab(\'ethics\')" title="Open Ethics tab">'
        f'<span class="ethics-pill-label">{escape_html(ethics_label)}</span>'
        f'</button>'
    )

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; font-src data:;">
  <title>ECP Audit — {escape_html(engagement_id)} ({escape_html(device.title())})</title>
  <style>{font_css}</style>
  <style>
{report_css}
  </style>
</head>
<body>
  <header class="app-header">
    <div class="app-header-left">
      <span class="app-logo">ECP v{escape_html(plugin_version)}</span>
      <h1 class="app-title">E-Commerce <span class="amber">Psychology</span> Audit</h1>
    </div>
    <div class="app-header-meta">
      <span class="header-chip"><strong>{total_findings}</strong>&nbsp;findings</span>
      <span class="header-chip"><strong>{clusters_count}</strong>&nbsp;clusters</span>
      <span class="header-sev-group" role="group" aria-label="Severity breakdown">{severity_chips_html}</span>
      <span class="header-chip">{escape_html(device.title())}&nbsp;·&nbsp;{escape_html(page_url)}</span>
      {ethics_pill_html}
    </div>
    <div class="app-header-actions">
      <button class="btn btn-ghost" onclick="openEditor()">Open Editor</button>
      <button class="btn btn-ghost" onclick="clearBrief()">Clear brief</button>
      <button class="btn btn-primary" id="exportBtn" onclick="openExport()" disabled>Export Brief (<span id="briefCount">0</span>)</button>
    </div>
  </header>

  <main class="app-main">

    <aside class="panel-left">
      <div class="panel-tabs" role="tablist">
        <button class="panel-tab{clusters_active}" data-tab="clusters" onclick="switchTab('clusters')" role="tab" aria-selected="{clusters_selected}">By Cluster</button>
        <button class="panel-tab{priority_active}" data-tab="priority" onclick="switchTab('priority')" role="tab" aria-selected="{priority_selected}">Priority Path</button>
        <button class="panel-tab" data-tab="ethics" onclick="switchTab('ethics')" role="tab" aria-selected="false">
          Ethics{f' <span class="tab-badge">{ethics_count}</span>' if ethics_count else ''}
        </button>
      </div>

      <div class="panel-scroll" id="panelClusters" data-panel="clusters"{clusters_hidden}>
        {clusters_tab_html}
      </div>
      <div class="panel-scroll" id="panelPriority" data-panel="priority"{priority_hidden}>
        {priority_tab_html}
      </div>
      <div class="panel-scroll" id="panelEthics" data-panel="ethics" hidden>
        {ethics_tab_html}
      </div>
    </aside>

    <section class="panel-center" id="panelCenter" data-state="empty">

      <div class="center-empty" id="centerEmpty">
        <div class="center-empty-ring">
          <span class="center-empty-icon">◎</span>
        </div>
        <div class="center-empty-title">Pick a finding to spotlight it</div>
        <div class="center-empty-hint">
          Use <strong>By Cluster</strong>, <strong>Priority Path</strong>, or <strong>Ethics</strong> on the left.
          <br>{empty_state_hint}
        </div>
        <div class="onboarding-steps">
          <div class="onboarding-step"><span class="onboarding-step-num">1</span>Open a cluster on the left rail</div>
          <div class="onboarding-step"><span class="onboarding-step-num">2</span>Click a finding row to see it here</div>
          <div class="onboarding-step"><span class="onboarding-step-num">3</span>Check the box on findings you want in your brief</div>
          <div class="onboarding-step"><span class="onboarding-step-num">4</span>Hit <strong>Export Brief</strong> to copy them out</div>
        </div>
      </div>

      <div class="center-stage" id="centerStage">
        <div class="center-head">
          <span class="center-head-label">Interface Evidence</span>
          <div class="center-nav">
            <button class="nav-btn" onclick="prevSlide()" aria-label="Previous slide" title="Previous slide">&#x2039;</button>
            <span class="slide-pos"><span id="slidePos">1</span> / <span id="slideTotal">1</span></span>
            <button class="nav-btn" onclick="nextSlide()" aria-label="Next slide" title="Next slide">&#x203A;</button>
            <button class="nav-btn center-close-btn" onclick="clearSelection()" aria-label="Dismiss screenshot" title="Dismiss">&times;</button>
          </div>
        </div>

        <div class="screenshot-wrapper">
          <div class="screenshot-stage" id="screenshotStage">
            <div class="device-frame">
              <div class="screenshot-container" id="mainSlide" style="--slide-aspect-ratio:{initial_slide_aspect_ratio};">
                <img id="mainImage" src="" alt="Screenshot" />
                <div class="screenshot-overlay"></div>
                <div class="review-effect-layer" id="reviewEffectLayer" aria-hidden="true"></div>
                {hotspot_overlays_html}
              </div>
            </div>
            <div class="device-base"></div>
            {device_stand_html}
          </div>
          <!-- Callout rendered as a SIBLING of the screenshot so it lives
               beside the image, never overlapping. JS positions + populates
               it on finding selection; a ::before pseudo draws the pointer. -->
          <div class="callout" id="callout" aria-hidden="true"></div>
        </div>
      </div>
    </section>

    <aside class="panel-right" id="detailPanel">
      <div class="detail-empty" id="detailEmpty">
        <div class="detail-empty-icon">◎</div>
        <div class="detail-empty-label">No finding selected</div>
        <div class="detail-empty-hint">Pick a finding from the list or click a marker on the screenshot.</div>
      </div>
      {detail_panels_html}
    </aside>

  </main>

  <footer class="app-bottom">
    <div class="bottom-left">
      <span id="briefStatus" class="brief-count">
        <strong id="briefCountBottom">0</strong> findings in brief
      </span>
      <span class="bottom-meta">{escape_html(device_label)} · {escape_html(page_type)} · {escape_html(platform)} · {escape_html(source_mode)} · {escape_html(date_str)} · engagement {escape_html(engagement_id)} · generated {generated_date}</span>
    </div>
    <div class="bottom-actions">
      <button class="btn btn-ghost" onclick="toggleSelectAllHigh()" title="Add every CRITICAL and HIGH finding to your brief (toggle)">Select HIGH</button>
      <button class="btn btn-ghost" onclick="toggleSelectAllVisible()">Select all visible</button>
      <button class="btn btn-primary" onclick="openExport()" id="exportBtnBottom" disabled>Export Brief</button>
    </div>
  </footer>

  <div class="modal-overlay" id="exportModal" onclick="if(event.target===this)closeExport()">
    <div class="modal" role="dialog" aria-modal="true" aria-label="Export brief">
      <div class="modal-head">
        <h2>Export Brief</h2>
        <button class="modal-close" onclick="closeExport()" aria-label="Close">&times;</button>
      </div>
      <div class="modal-body">
        <div class="export-tabs">
          <button class="export-tab active" data-format="bullets" onclick="switchExportFormat('bullets')">Bulleted list</button>
          <button class="export-tab" data-format="markdown" onclick="switchExportFormat('markdown')">Markdown (audit mirror)</button>
        </div>
        <textarea class="export-preview" id="exportPreview" spellcheck="false" aria-label="Brief preview — editable before copying"></textarea>
        <div class="export-hint">Tweak any wording before copying — edits here only affect the copy you take to clipboard.</div>
      </div>
      <div class="modal-foot">
        <button class="btn btn-ghost" onclick="closeExport()">Close</button>
        <button class="btn btn-primary" onclick="copyExport()">Copy to clipboard</button>
      </div>
    </div>
  </div>

  <script>
{report_js}
  </script>
</body>
</html>'''

    return html
