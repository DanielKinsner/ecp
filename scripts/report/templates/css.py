"""CSS for the v1.0 three-panel app-shell report.

Dark chrome preserved from the v5/v6 scroll-document shell:
- Outer bg  #0f0f0f
- Panels    #141414
- Borders   rgba(255,255,255,0.08)
- Text      rgba(255,255,255,0.92)
- Dim       rgba(255,255,255,0.50)
- Amber     #ff9f00 (headline accent)
- Severity  critical #9300a (red-black) / high #ef4444 / medium #eab308 / low #22c55e / pass #22c55e

Layout is a flex 3-panel app shell: 400px left (tabs + cluster/priority/
ethics list), flex:1 center (screenshot + hotspot zones), 400px right
(selected-finding detail). Header + bottom bar frame the shell.
"""

def get_report_css(device_frame_css):
    """Compose full report CSS. ``device_frame_css`` is the per-device frame
    block (monitor stand for desktop, phone chrome for mobile, laptop lid
    for laptop) injected from ``utils.get_device_frame_css``."""
    return _BASE_CSS.format(device_frame_css=device_frame_css)


_BASE_CSS = """
:root {{
  --bg: #0f0f0f;
  --panel: #141414;
  --panel-hover: #1a1a1a;
  --panel-raised: #1f1f1f;
  --border: rgba(255,255,255,0.08);
  --border-light: rgba(255,255,255,0.05);
  --border-strong: rgba(255,255,255,0.14);
  --text: rgba(255,255,255,0.92);
  --text-dim: rgba(255,255,255,0.50);
  --text-muted: rgba(255,255,255,0.34);
  --amber: #ff9f00;
  --amber-dim: rgba(255,159,0,0.18);

  --severity-critical: #9300a;
  --severity-critical-bg: rgba(147,0,10,0.14);
  --severity-critical-border: rgba(147,0,10,0.52);
  --severity-high: #ef4444;
  --severity-high-bg: rgba(239,68,68,0.12);
  --severity-high-border: rgba(239,68,68,0.46);
  --severity-medium: #eab308;
  --severity-medium-bg: rgba(234,179,8,0.12);
  --severity-medium-border: rgba(234,179,8,0.44);
  --severity-low: #22c55e;
  --severity-low-bg: rgba(34,197,94,0.12);
  --severity-low-border: rgba(34,197,94,0.40);
  --success: #22c55e;
  --danger: #ef4444;

  --tier-gold-bg: rgba(234,179,8,0.14);
  --tier-gold-text: #eab308;
  --tier-silver-bg: rgba(148,163,184,0.14);
  --tier-silver-text: #cbd5e1;
  --tier-bronze-bg: rgba(180,83,9,0.18);
  --tier-bronze-text: #f59e0b;

  --radius-sm: 0.375rem;
  --radius: 0.625rem;
  --radius-lg: 0.875rem;

  --panel-width-left: 400px;
  --panel-width-right: 400px;
  --header-h: 60px;
  --bottom-h: 58px;
}}

*, *::before, *::after {{ box-sizing: border-box; }}

/* Root hidden-attribute enforcement. Browsers occasionally honor `hidden`
   weakly inside flex/grid containers — make it !important so nothing leaks
   into the center stage when data-state="empty". */
[hidden] {{ display: none !important; }}

html, body {{
  margin: 0;
  padding: 0;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, "Helvetica Neue", sans-serif;
  font-size: 14px;
  line-height: 1.5;
  height: 100vh;
  overflow: hidden;
}}

button {{
  font-family: inherit;
  cursor: pointer;
  color: inherit;
}}

a {{ color: var(--amber); text-decoration: none; }}
a:hover {{ text-decoration: underline; }}

/* ============================================================
   Header
   ============================================================ */
.app-header {{
  height: var(--header-h);
  padding: 0 20px;
  background: #0a0a0a;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 20px;
  flex-shrink: 0;
}}
.app-header-left {{
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}}
.app-logo {{
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--text-muted);
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: 999px;
  white-space: nowrap;
}}
.app-title {{
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  white-space: nowrap;
}}
.app-title .amber {{ color: var(--amber); font-weight: 700; }}
.app-header-meta {{
  display: flex;
  gap: 8px;
  flex: 1;
  min-width: 0;
  overflow: hidden;
}}
.header-chip {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 999px;
  font-size: 12px;
  color: var(--text-dim);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.header-chip strong {{ color: var(--text); font-weight: 600; }}
.header-chip.advisory, .header-chip.warning {{ color: var(--amber); border-color: var(--amber-dim); }}
.header-chip.critical, .header-chip.block {{ color: var(--severity-high); border-color: var(--severity-high-border); }}
.header-chip.clear, .header-chip.pass {{ color: var(--success); border-color: var(--severity-low-border); }}
.header-chip svg {{ width: 12px; height: 12px; flex-shrink: 0; }}

/* Severity breakdown in the header — chips per severity bucket with the
   severity's signature color. Zero-count buckets are omitted upstream. */
.header-sev-group {{
  display: inline-flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}}
.header-sev-chip {{
  display: inline-flex;
  align-items: baseline;
  gap: 4px;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-dim);
  white-space: nowrap;
}}
.header-sev-chip strong {{ font-size: 12px; font-weight: 700; color: var(--text); }}
.header-sev-chip.critical {{ color: var(--severity-critical, #dc2626); border-color: color-mix(in srgb, var(--severity-critical, #dc2626) 45%, transparent); }}
.header-sev-chip.critical strong {{ color: var(--severity-critical, #dc2626); }}
.header-sev-chip.high {{ color: var(--severity-high, #ef4444); border-color: color-mix(in srgb, var(--severity-high, #ef4444) 45%, transparent); }}
.header-sev-chip.high strong {{ color: var(--severity-high, #ef4444); }}
.header-sev-chip.medium {{ color: var(--severity-medium, #eab308); border-color: color-mix(in srgb, var(--severity-medium, #eab308) 45%, transparent); }}
.header-sev-chip.medium strong {{ color: var(--severity-medium, #eab308); }}
.header-sev-chip.low {{ color: var(--severity-low, #22c55e); border-color: color-mix(in srgb, var(--severity-low, #22c55e) 45%, transparent); }}
.header-sev-chip.low strong {{ color: var(--severity-low, #22c55e); }}

/* Ethics pill — bigger, bolder, always visible, always state-colored. */
.ethics-pill {{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  font-size: 11.5px;
  font-weight: 800;
  letter-spacing: 0.08em;
  border-radius: 999px;
  border: 1.5px solid transparent;
  background: transparent;
  cursor: pointer;
  transition: transform 0.12s ease, filter 0.12s ease;
  white-space: nowrap;
}}
.ethics-pill:hover {{ transform: translateY(-1px); filter: brightness(1.15); }}
.ethics-pill.pass {{
  background: var(--severity-low-bg);
  border-color: var(--severity-low-border);
  color: var(--success);
}}
.ethics-pill.pass::before {{ content: "\\2713\\00a0"; font-weight: 900; }}
.ethics-pill.advisory {{
  background: var(--severity-medium-bg);
  border-color: var(--severity-medium-border);
  color: var(--severity-medium);
}}
.ethics-pill.advisory::before {{ content: "\\26a0\\fe0f\\00a0"; }}
.ethics-pill.block {{
  background: var(--severity-high-bg);
  border-color: var(--severity-high-border);
  color: var(--severity-high);
  box-shadow: 0 0 0 3px rgba(239,68,68,0.08);
}}
.ethics-pill.block::before {{ content: "\\2717\\00a0"; font-weight: 900; }}

.app-header-actions {{
  display: flex;
  gap: 8px;
  margin-left: auto;
  flex-shrink: 0;
}}

/* ============================================================
   Buttons
   ============================================================ */
.btn {{
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 600;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
  white-space: nowrap;
}}
.btn:disabled {{ opacity: 0.42; cursor: not-allowed; }}
.btn-ghost {{
  background: transparent;
  color: var(--text-dim);
  border-color: var(--border);
}}
.btn-ghost:hover:not(:disabled) {{ color: var(--text); border-color: var(--border-strong); }}
.btn-primary {{
  background: var(--amber);
  color: #141414;
}}
.btn-primary:hover:not(:disabled) {{ background: #ffb43c; }}
.btn-primary:disabled {{ background: rgba(255,159,0,0.32); color: rgba(20,20,20,0.6); }}

/* ============================================================
   Main 3-panel app shell
   ============================================================ */
.app-main {{
  display: flex;
  height: calc(100vh - var(--header-h) - var(--bottom-h));
  overflow: hidden;
}}

.panel-left,
.panel-right {{
  width: var(--panel-width-left);
  flex-shrink: 0;
  background: var(--panel);
  display: flex;
  flex-direction: column;
  min-height: 0;
}}
.panel-left {{
  border-right: 1px solid var(--border);
}}
.panel-right {{
  width: var(--panel-width-right);
  border-left: 1px solid var(--border);
  position: relative;
}}

.panel-center {{
  flex: 1;
  min-width: 0;
  background: var(--bg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px;
  position: relative;
}}
/* Empty state / stage swap based on data-state="empty" attribute. */
.panel-center[data-state="empty"] .center-stage,
.panel-center[data-state="empty"] .screenshot-stage,
.panel-center[data-state="empty"] #mainSlide,
.panel-center[data-state="empty"] .callout {{ display: none !important; }}
.panel-center[data-state="active"] .center-empty {{ display: none !important; }}
.panel-center .center-empty {{
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 24px;
  text-align: center;
}}
.center-empty-ring {{
  width: 96px; height: 96px;
  border-radius: 50%;
  border: 2px dashed var(--border-strong);
  display: flex; align-items: center; justify-content: center;
  color: var(--amber);
  opacity: 0.8;
}}
.center-empty-icon {{
  font-size: 36px;
  animation: centerPulse 2.4s ease-in-out infinite;
}}
@keyframes centerPulse {{
  0%, 100% {{ transform: scale(1); opacity: 0.85; }}
  50% {{ transform: scale(1.08); opacity: 1; }}
}}
.center-empty-title {{
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
  margin-top: 8px;
}}
.center-empty-hint {{
  font-size: 13px;
  color: var(--text-dim);
  line-height: 1.6;
  max-width: 480px;
}}
.center-empty-hint strong {{ color: var(--amber); font-weight: 700; }}
.onboarding-steps {{
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(2, minmax(220px, 1fr));
  gap: 10px;
  max-width: 540px;
  width: 100%;
}}
.onboarding-step {{
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 12px;
  color: var(--text-dim);
  text-align: left;
  line-height: 1.4;
}}
.onboarding-step strong {{ color: var(--amber); font-weight: 700; }}
.onboarding-step-num {{
  width: 22px; height: 22px;
  border-radius: 50%;
  background: var(--amber-dim);
  color: var(--amber);
  display: flex; align-items: center; justify-content: center;
  font-size: 11px;
  font-weight: 800;
  flex-shrink: 0;
}}
.center-stage {{
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}}
.center-close-btn {{ color: var(--text-dim); }}
.center-close-btn:hover {{ color: var(--severity-high); }}

/* ============================================================
   Left panel tabs + scrollable content
   ============================================================ */
.panel-tabs {{
  display: flex;
  background: #0a0a0a;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}}
.panel-tab {{
  flex: 1;
  padding: 12px 10px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-dim);
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  letter-spacing: 0.02em;
  transition: color 0.15s ease, background 0.15s ease, border-color 0.15s ease;
}}
.panel-tab:hover {{
  color: var(--text);
  background: var(--panel-hover);
}}
.panel-tab.active {{
  color: #ffffff;
  background: var(--panel);
  border-bottom-color: rgba(255,255,255,0.88);
}}
.tab-badge {{
  display: inline-block;
  margin-left: 4px;
  padding: 1px 6px;
  font-size: 10px;
  font-weight: 700;
  background: var(--severity-high-bg);
  color: var(--severity-high);
  border-radius: 999px;
}}

.panel-scroll {{
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 10px;
  scrollbar-width: thin;
  scrollbar-color: var(--border-strong) transparent;
}}
.panel-scroll::-webkit-scrollbar {{ width: 8px; }}
.panel-scroll::-webkit-scrollbar-thumb {{ background: var(--border-strong); border-radius: 4px; }}
.panel-scroll::-webkit-scrollbar-track {{ background: transparent; }}

/* ============================================================
   Cluster card (collapsible)
   ============================================================ */
.cluster-card {{
  background: var(--panel-raised);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  margin-bottom: 8px;
  overflow: hidden;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}}
.cluster-card:hover {{ border-color: var(--border-strong); }}
.cluster-card.expanded {{ border-color: var(--border-strong); box-shadow: 0 6px 20px rgba(0,0,0,0.3); }}

.cluster-head {{
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 14px;
  background: linear-gradient(180deg, #1c1c1c 0%, #161616 100%);
  cursor: pointer;
  user-select: none;
}}
.cluster-head:hover {{ background: linear-gradient(180deg, #212121 0%, #1a1a1a 100%); }}
.cluster-chip {{
  width: 36px; height: 36px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 800;
  flex-shrink: 0;
  letter-spacing: 0.05em;
  border: 1px solid rgba(255,255,255,0.06);
}}
/* Cluster chips — whiter-leaning per Dan's 2026-04-14 r4 feedback. Each
   cluster still has a tiny color accent (left border) so you can tell them
   apart at a glance, but the fill is neutral white-ish for a calmer rail. */
.cluster-chip {{
  background: rgba(255,255,255,0.06);
  color: rgba(255,255,255,0.90);
  border-left: 3px solid rgba(255,255,255,0.30);
}}
.cluster-chip.chip-visual   {{ border-left-color: rgba(165,180,252,0.75); }}
.cluster-chip.chip-trust    {{ border-left-color: rgba(134,239,172,0.75); }}
.cluster-chip.chip-price    {{ border-left-color: rgba(253,186,116,0.75); }}
.cluster-chip.chip-checkout {{ border-left-color: rgba(125,211,252,0.75); }}
.cluster-chip.chip-perf     {{ border-left-color: rgba(249,168,212,0.75); }}
.cluster-chip.chip-media    {{ border-left-color: rgba(216,180,254,0.75); }}
.cluster-chip.chip-nav      {{ border-left-color: rgba(103,232,249,0.75); }}
.cluster-chip.chip-seo      {{ border-left-color: rgba(253,224,71,0.80); }}
.cluster-chip.chip-post     {{ border-left-color: rgba(252,165,165,0.75); }}
.cluster-chip.chip-audience {{ border-left-color: rgba(203,213,225,0.75); }}
.cluster-chip.chip-default  {{ border-left-color: rgba(255,159,0,0.80); }}

.cluster-info {{
  flex: 1;
  min-width: 0;
}}
.cluster-name {{
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  text-transform: none;
  letter-spacing: -0.01em;
  margin-bottom: 3px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.cluster-meta {{
  display: flex;
  gap: 6px;
  align-items: center;
  flex-shrink: 0;
}}
.cluster-count {{
  font-size: 10px;
  font-weight: 700;
  color: var(--text-dim);
  padding: 2px 7px;
  background: #0f0f0f;
  border: 1px solid var(--border);
  border-radius: 999px;
}}
.cluster-sev-tag {{
  font-size: 9px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 3px;
  letter-spacing: 0.04em;
}}
.cluster-sev-tag.critical {{ background: var(--severity-critical-bg); color: var(--severity-critical); }}
.cluster-sev-tag.high {{ background: var(--severity-high-bg); color: var(--severity-high); }}
.cluster-sev-tag.medium {{ background: var(--severity-medium-bg); color: var(--severity-medium); }}
.cluster-sev-tag.low {{ background: var(--severity-low-bg); color: var(--severity-low); }}
.cluster-chev {{
  color: var(--text-muted);
  font-size: 11px;
  transition: transform 0.2s ease;
}}
.cluster-card.expanded .cluster-chev {{ transform: rotate(180deg); }}

.cluster-body {{
  display: none;
  border-top: 1px solid var(--border);
  background: #121212;
}}
.cluster-card.expanded .cluster-body {{ display: block; }}

/* ============================================================
   Finding row (inside cluster body + priority card)
   ============================================================ */
.finding-row {{
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-top: 1px solid var(--border-light);
  cursor: pointer;
  transition: background 0.15s ease;
}}
.finding-row:first-child {{ border-top: none; }}
.finding-row:hover {{ background: var(--panel-hover); }}
.finding-row.selected {{
  background: rgba(255,255,255,0.05);
  border-left: 2px solid rgba(255,255,255,0.85);
  padding-left: 10px;
}}

.finding-check {{
  width: 16px;
  height: 16px;
  border-radius: 4px;
  border: 1.5px solid var(--border-strong);
  background: transparent;
  flex-shrink: 0;
  margin-top: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s ease, border-color 0.15s ease;
}}
.finding-check::after {{
  content: "";
  display: block;
  width: 9px;
  height: 9px;
  border-radius: 2px;
  background: var(--amber);
  opacity: 0;
  transition: opacity 0.15s ease;
}}
.finding-row.in-brief .finding-check {{ border-color: rgba(255,255,255,0.92); background: rgba(255,255,255,0.08); }}
.finding-row.in-brief .finding-check::after {{ opacity: 1; background: rgba(255,255,255,0.95); }}

.finding-body {{
  flex: 1;
  min-width: 0;
}}
.finding-head-line {{
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
}}
.finding-id {{
  font-size: 10px;
  font-weight: 700;
  color: var(--text-dim);
  letter-spacing: 0.04em;
  font-variant-numeric: tabular-nums;
}}
.finding-sev {{
  font-size: 9px;
  font-weight: 800;
  padding: 1px 5px;
  border-radius: 3px;
  letter-spacing: 0.04em;
}}
.finding-sev.critical {{ background: var(--severity-critical-bg); color: var(--severity-critical); }}
.finding-sev.high {{ background: var(--severity-high-bg); color: var(--severity-high); }}
.finding-sev.medium {{ background: var(--severity-medium-bg); color: var(--severity-medium); }}
.finding-sev.low {{ background: var(--severity-low-bg); color: var(--severity-low); }}
.finding-title {{
  font-size: 12.5px;
  line-height: 1.42;
  color: var(--text);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}}

/* ============================================================
   Priority path cards (left panel "Priority" tab)
   ============================================================ */
.priority-card {{
  background: var(--panel-raised);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  margin-bottom: 10px;
  padding: 12px 14px;
}}
.priority-card-head {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}}
.priority-card-num {{
  width: 26px; height: 26px;
  border-radius: 50%;
  background: rgba(255,255,255,0.9);
  color: #0f0f0f;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 800;
  flex-shrink: 0;
}}
.priority-card-title {{
  flex: 1;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.35;
  color: var(--text);
}}
.priority-card-meta {{
  margin-top: 4px;
  font-size: 11px;
  color: var(--text-dim);
}}
.priority-card-action {{
  margin-top: 8px;
  padding: 10px 12px;
  background: rgba(255,159,0,0.06);
  border-left: 2px solid var(--amber);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  font-size: 11.5px;
  line-height: 1.5;
  color: var(--text);
}}
.priority-refs-label {{
  margin: 12px 0 4px 0;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--text-muted);
}}
.priority-refs {{
  padding-top: 4px;
  border-top: 1px solid var(--border-light);
}}
.priority-ref-row {{
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 4px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.15s ease;
}}
.priority-ref-row:hover {{ background: var(--panel-hover); }}
.priority-ref-row.in-brief .priority-ref-check {{ border-color: var(--amber); background: rgba(255,159,0,0.08); }}
.priority-ref-row.in-brief .priority-ref-check::after {{ opacity: 1; }}

/* Phase 6 (2026-05-18) — Codex Q2/Q3/Q4 cross-device Priority Path
   coverage. Stories whose underlying refs all live on the other device
   render as faded "applies elsewhere" cards (instead of being silently
   dropped, which made desktop HTML show 4 cards while desktop markdown
   showed 5). Per-ref applies-elsewhere rows render muted + struck-through
   so the customer sees the cross-device coverage without losing trust
   in the count. */
.priority-card.priority-card-applies-elsewhere {{
  opacity: 0.55;
  border-color: var(--border-strong);
  background: var(--panel-muted, rgba(255, 255, 255, 0.02));
}}
.priority-card-elsewhere-banner {{
  font-size: 11px;
  font-style: italic;
  color: var(--text-muted);
  padding: 4px 8px;
  margin: 4px 0;
  border-left: 2px solid var(--amber, #ff9f00);
  background: rgba(255, 159, 0, 0.04);
  border-radius: 2px;
}}
.priority-ref-row.underlying-applies-elsewhere {{
  opacity: 0.55;
}}
.priority-ref-row.underlying-applies-elsewhere .priority-ref-label {{
  text-decoration: line-through;
  text-decoration-thickness: 1px;
  text-decoration-color: var(--text-muted);
}}
.priority-ref-row.underlying-applies-elsewhere:hover {{
  background: transparent;
  cursor: not-allowed;
}}
.priority-ref-check {{
  width: 14px; height: 14px;
  border-radius: 3px;
  border: 1.5px solid var(--border-strong);
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}}
.priority-ref-check::after {{
  content: "";
  display: block;
  width: 8px; height: 8px;
  border-radius: 2px;
  background: var(--amber);
  opacity: 0;
}}
.priority-ref-label {{
  flex: 1;
  font-size: 11px;
  color: var(--text-dim);
  font-variant-numeric: tabular-nums;
}}
.priority-ref-label strong {{ color: var(--text); font-weight: 600; font-family: ui-monospace, "SF Mono", monospace; }}

/* ============================================================
   Ethics tab (left panel "Ethics" tab)
   ============================================================ */
.ethics-empty,
.panel-empty {{
  padding: 40px 24px;
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
}}
.ethics-card {{
  background: var(--panel-raised);
  border: 1px solid var(--severity-high-border);
  border-radius: var(--radius);
  margin-bottom: 10px;
  padding: 12px 14px;
}}
.ethics-card.adjacent {{ border-color: var(--severity-medium-border); }}
.ethics-card.block {{ border-color: var(--severity-high-border); }}
.ethics-card-head {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}}
.ethics-state-pill {{
  font-size: 10px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 999px;
  letter-spacing: 0.06em;
}}
.ethics-state-pill.block {{ background: var(--severity-high-bg); color: var(--severity-high); }}
.ethics-state-pill.adjacent {{ background: var(--severity-medium-bg); color: var(--severity-medium); }}
.ethics-card-title {{
  flex: 1;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.35;
  color: var(--text);
}}
.ethics-card-link {{
  font-size: 11px;
  color: var(--amber);
  padding: 6px 0;
  display: inline-block;
  word-break: break-all;
}}

/* ============================================================
   Center panel: screenshot + hotspot zones
   ============================================================ */
.center-head {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}}
.center-head-label {{
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--text-muted);
}}
.center-nav {{
  display: flex;
  align-items: center;
  gap: 8px;
}}
.nav-btn {{
  width: 30px; height: 30px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--panel);
  color: var(--text);
  font-size: 16px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s ease, border-color 0.15s ease;
}}
.nav-btn:hover {{ background: var(--panel-hover); border-color: var(--border-strong); }}
.slide-pos {{
  font-size: 11px;
  color: var(--text-dim);
  font-variant-numeric: tabular-nums;
  min-width: 32px;
  text-align: center;
}}

{device_frame_css}

.screenshot-wrapper {{
  position: relative;
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 24px;
  max-width: 100%;
  padding: 4px 24px;
  overflow: visible;
}}
.screenshot-stage {{
  display: flex;
  flex-direction: column;
  align-items: stretch;
  flex-shrink: 0;
  /* Bumped 780px -> 880px (+13%) per Dan's 2026-04-14 size request. */
  max-width: min(100%, 880px);
}}
/* Screenshot container takes ~60% of the center panel height. The
   aspect-ratio var preserves the natural shape; max-width keeps wide
   desktop screenshots from stretching past the design's visual rhythm. */
.screenshot-container {{
  position: relative;
  aspect-ratio: var(--slide-aspect-ratio, 16 / 9);
  /* Bumped 780px -> 880px / 60vh -> 70vh (+13% / +17%) per Dan's size
     request — main image gets more visual weight without pushing the
     callout off-screen. */
  max-width: min(100%, 880px);
  max-height: 70vh;
  margin: 0 auto;
  border-radius: 10px;
  overflow: visible;
  background: #0a0a0a;
  flex-shrink: 0;
  display: block;
  box-shadow: 0 18px 50px rgba(0,0,0,0.6);
}}
.screenshot-container img {{
  width: 100%; height: 100%;
  object-fit: contain;
  display: block;
  border-radius: 10px;
}}
.screenshot-overlay {{
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: linear-gradient(180deg, transparent 60%, rgba(0,0,0,0.25) 100%);
}}
.review-effect-layer {{
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  border-radius: 10px;
  z-index: 4;
}}
.review-dim-region {{
  position: absolute;
  background: rgba(0,0,0,var(--review-dim-opacity,0.35));
  border-radius: 8px;
}}
.review-dim-mask {{
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}}
.review-blur-piece {{
  position: absolute;
  background: rgba(255,255,255,0.012);
  backdrop-filter: blur(var(--review-blur-radius,6px));
  -webkit-backdrop-filter: blur(var(--review-blur-radius,6px));
}}
.review-blur-focus {{
  position: absolute;
  border: 1px dashed rgba(255,255,255,0.28);
  border-radius: 8px;
  box-shadow: 0 0 32px rgba(255,255,255,0.12);
}}

/* Hotspot zones — hidden by default. Only the single selected finding's
   hotspot renders. Uses a neutral white outline by default; severity
   color only reinforces the class via filter/shadow glow — not all-amber. */
.hotspot {{
  position: absolute;
  border: 2.5px solid rgba(255,255,255,0.95);
  border-radius: 6px;
  background: rgba(255,255,255,0.04);
  /* pointer-events: auto so clicks on a visible hotspot route through
     the delegated click handler (Dan 2026-04-14: clicking a hotspot did
     nothing). Hotspots are display:none by default anyway, so inactive
     ones never intercept clicks. */
  pointer-events: auto;
  cursor: pointer;
  z-index: 5;
  box-shadow: 0 0 0 2px rgba(0,0,0,0.5), 0 0 24px rgba(255,255,255,0.2);
  display: none;
}}
.hotspot.selected {{
  display: block;
  animation: hotspotFadeIn 0.28s ease-out both, hotspotPulse 2.2s ease-in-out 0.28s infinite;
}}
.hotspot-ellipse {{
  border-radius: 999px;
}}
.hotspot[data-review-style~="glow"].selected {{
  border-width: 4px;
  animation: hotspotFadeIn 0.28s ease-out both, reviewHotspotGlow 1.8s ease-in-out 0.28s infinite;
}}
@keyframes hotspotFadeIn {{
  from {{ opacity: 0; transform: scale(0.92); }}
  to   {{ opacity: 1; transform: scale(1); }}
}}
@keyframes hotspotPulse {{
  0%, 100% {{ box-shadow: 0 0 0 2px rgba(0,0,0,0.5), 0 0 22px rgba(255,255,255,0.22); }}
  50%     {{ box-shadow: 0 0 0 2px rgba(0,0,0,0.5), 0 0 32px rgba(255,255,255,0.38); }}
}}
@keyframes reviewHotspotGlow {{
  0%, 100% {{ filter: brightness(1); transform: scale(1); }}
  50% {{ filter: brightness(1.25); transform: scale(1.01); }}
}}
.hotspot[data-severity="critical"] {{ border-color: var(--severity-critical); background: var(--severity-critical-bg); }}
.hotspot[data-severity="high"]     {{ border-color: var(--severity-high);     background: var(--severity-high-bg); }}
.hotspot[data-severity="medium"]   {{ border-color: var(--severity-medium);   background: var(--severity-medium-bg); }}
.hotspot[data-severity="low"]      {{ border-color: var(--severity-low);      background: var(--severity-low-bg); }}

/* Phase 2 visual evidence taxonomy (2026-05-18) — distinct styling per
   visual_evidence.type so absent / proxy / generated overlays read as
   visually different from exact element selections. Scoped to
   ``.hotspot-ve-<type>`` classes emitted by _hotspot_class in
   templates/components.py. Legacy reports without visual_evidence
   render unchanged (no class match, default .hotspot rules apply).

   - exact_element: solid border (default, no override needed)
   - proxy_element: dashed border signaling "near the subject, not exact"
   - generated_expected_zone: thick dashed ghost outline; transparent fill
     with a label suggesting where the missing UI should appear
   - section_absence: dotted border with rounded pill shape
   - page_level: top-of-page banner indicator with thicker border */
.hotspot-ve-proxy-element {{
  border-style: dashed !important;
  border-width: 2px;
}}
.hotspot-ve-generated-expected-zone {{
  border-style: dashed !important;
  border-width: 3px;
  background-image:
    repeating-linear-gradient(
      45deg,
      transparent,
      transparent 6px,
      rgba(255, 255, 255, 0.04) 6px,
      rgba(255, 255, 255, 0.04) 12px
    );
}}
.hotspot-ve-section-absence {{
  border-style: dotted !important;
  border-width: 2px;
  border-radius: 999px;
}}
.hotspot-ve-page-level {{
  border-width: 3px;
  border-style: solid;
}}
/* Confidence dimming — needs_review hotspots float to the operator's
   attention via reduced opacity until they're reviewed. */
.hotspot-ve-conf-needs-review {{
  opacity: 0.65;
}}
.hotspot-ve-conf-needs-review.selected {{
  opacity: 1;
}}

/* Callout — dark-mode card that lives BESIDE the screenshot, never
   overlapping it. A left-pointing triangle on the card's left edge acts
   as the leader line pointing at the selected hotspot. JS sets the top
   offset so the triangle aligns with the hotspot's vertical center. */
.callout {{
  position: relative;
  z-index: 8;
  display: none;
  --callout-scale: 1;
  /* Bumped 280 -> 320 (+14%) + padding 14/16 -> 16/18 per Dan's size
     request. Callout matches the larger screenshot in visual weight. */
  width: calc(320px * var(--callout-scale));
  flex-shrink: 0;
  padding: calc(16px * var(--callout-scale)) calc(18px * var(--callout-scale));
  background: var(--panel-raised);
  color: var(--text);
  border: 1px solid var(--callout-accent, var(--border-strong));
  border-radius: var(--radius);
  box-shadow: 0 18px 50px rgba(0,0,0,0.55);
  font-size: calc(13px * var(--callout-scale));
  line-height: 1.5;
  animation: calloutIn 0.28s ease-out both;
}}
.callout[data-visible="true"] {{ display: block; }}
.callout.review-positioned {{
  z-index: 12;
  pointer-events: auto;
  box-shadow: 0 22px 54px rgba(0,0,0,0.62);
}}
/* Leader arrow. Direction is persisted from the editor through
   review_callout_position.anchor; JS also aligns it to the selected hotspot. */
.callout::before,
.callout::after {{
  content: "";
  position: absolute;
  width: 0; height: 0;
  border-style: solid;
}}
.callout-arrow-left::before,
.callout-arrow-left::after {{
  top: var(--pointer-top, 28px);
  right: 100%;
  transform: translateY(-50%);
}}
.callout-arrow-left::before {{
  border-width: 9px 10px 9px 0;
  border-color: transparent var(--callout-accent, var(--border-strong)) transparent transparent;
}}
.callout-arrow-left::after {{
  right: calc(100% - 1px);
  border-width: 8px 9px 8px 0;
  border-color: transparent var(--panel-raised) transparent transparent;
}}
.callout-arrow-right::before,
.callout-arrow-right::after {{
  top: var(--pointer-top, 28px);
  left: 100%;
  transform: translateY(-50%);
}}
.callout-arrow-right::before {{
  border-width: 9px 0 9px 10px;
  border-color: transparent transparent transparent var(--callout-accent, var(--border-strong));
}}
.callout-arrow-right::after {{
  left: calc(100% - 1px);
  border-width: 8px 0 8px 9px;
  border-color: transparent transparent transparent var(--panel-raised);
}}
.callout-arrow-top::before,
.callout-arrow-top::after {{
  left: var(--pointer-left, 28px);
  bottom: 100%;
  transform: translateX(-50%);
}}
.callout-arrow-top::before {{
  border-width: 0 9px 10px 9px;
  border-color: transparent transparent var(--callout-accent, var(--border-strong)) transparent;
}}
.callout-arrow-top::after {{
  bottom: calc(100% - 1px);
  border-width: 0 8px 9px 8px;
  border-color: transparent transparent var(--panel-raised) transparent;
}}
.callout-arrow-bottom::before,
.callout-arrow-bottom::after {{
  left: var(--pointer-left, 28px);
  top: 100%;
  transform: translateX(-50%);
}}
.callout-arrow-bottom::before {{
  border-width: 10px 9px 0 9px;
  border-color: var(--callout-accent, var(--border-strong)) transparent transparent transparent;
}}
.callout-arrow-bottom::after {{
  top: calc(100% - 1px);
  border-width: 9px 8px 0 8px;
  border-color: var(--panel-raised) transparent transparent transparent;
}}
@keyframes calloutIn {{
  from {{ opacity: 0; transform: translateX(6px); }}
  to   {{ opacity: 1; transform: translateX(0); }}
}}
.callout-head {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}}
.callout-id {{
  font-size: calc(11px * var(--callout-scale));
  font-weight: 800;
  color: var(--text);
  padding: calc(3px * var(--callout-scale)) calc(8px * var(--callout-scale));
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.14);
  border-radius: var(--radius-sm);
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.05em;
}}
.callout-sev {{
  font-size: calc(9px * var(--callout-scale));
  font-weight: 800;
  padding: calc(2px * var(--callout-scale)) calc(7px * var(--callout-scale));
  border-radius: 3px;
  letter-spacing: 0.05em;
}}
.callout-sev.critical {{ background: var(--severity-critical-bg); color: var(--severity-critical); }}
.callout-sev.high     {{ background: var(--severity-high-bg);     color: var(--severity-high); }}
.callout-sev.medium   {{ background: var(--severity-medium-bg);   color: var(--severity-medium); }}
.callout-sev.low      {{ background: var(--severity-low-bg);      color: var(--severity-low); }}
.callout-title {{
  font-size: calc(13px * var(--callout-scale));
  font-weight: 700;
  line-height: 1.4;
  margin-bottom: 8px;
  color: var(--callout-accent, var(--text));
}}
.callout-rec {{
  font-size: calc(11.5px * var(--callout-scale));
  color: #7ee2a3;
  line-height: 1.5;
  padding-top: calc(8px * var(--callout-scale));
  border-top: 1px solid var(--border-light);
}}

/* Thumbnails strip */
.thumbnails {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(72px, 1fr));
  gap: 8px;
  margin-top: 12px;
  flex-shrink: 0;
}}
.thumb {{
  aspect-ratio: var(--thumb-aspect-ratio, 16 / 10);
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1px solid var(--border);
  opacity: 0.6;
  cursor: pointer;
  transition: all 0.2s ease;
}}
.thumb:hover {{ opacity: 1; border-color: var(--border-strong); }}
.thumb.active {{ opacity: 1; border-color: var(--amber); box-shadow: 0 0 0 1px var(--amber); }}
.thumb img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}

/* Legacy .instruction block (v6). Removed from html_structure.py in v1.0
   redesign — replaced by the .center-empty onboarding tiles. Rules kept
   here as no-ops in case any saved report still references the element. */
.instruction {{ display: none; }}

/* ============================================================
   Right panel: detail cards
   ============================================================ */
.detail-empty {{
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  text-align: center;
  color: var(--text-dim);
}}
.detail-empty-icon {{ font-size: 42px; opacity: 0.4; margin-bottom: 12px; }}
.detail-empty-label {{ font-size: 14px; font-weight: 600; color: var(--text); margin-bottom: 6px; }}
.detail-empty-hint {{ font-size: 12px; color: var(--text-muted); line-height: 1.5; max-width: 260px; }}

.detail-card {{
  display: none;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}}
.detail-card.visible {{ display: flex; }}

.detail-head {{
  padding: 14px 16px;
  background: linear-gradient(180deg, #161616, #121212);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}}
.detail-head-row {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}}
.detail-id {{
  font-size: 11px;
  font-weight: 800;
  padding: 3px 8px;
  background: rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.95);
  border-radius: var(--radius-sm);
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.05em;
  border: 1px solid rgba(255,255,255,0.12);
}}
.detail-sev {{
  font-size: 9px;
  font-weight: 800;
  padding: 2px 7px;
  border-radius: var(--radius-sm);
  letter-spacing: 0.06em;
}}
.detail-sev.critical {{ background: var(--severity-critical-bg); color: var(--severity-critical); }}
.detail-sev.high {{ background: var(--severity-high-bg); color: var(--severity-high); }}
.detail-sev.medium {{ background: var(--severity-medium-bg); color: var(--severity-medium); }}
.detail-sev.low {{ background: var(--severity-low-bg); color: var(--severity-low); }}
.detail-cluster-tag {{
  margin-left: auto;
  font-size: 10px;
  color: var(--text-muted);
  text-transform: capitalize;
  letter-spacing: 0.02em;
}}
.detail-title {{
  font-size: 14.5px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--text);
}}

.detail-body {{
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  scrollbar-width: thin;
  scrollbar-color: var(--border-strong) transparent;
}}
.detail-body::-webkit-scrollbar {{ width: 8px; }}
.detail-body::-webkit-scrollbar-thumb {{ background: var(--border-strong); border-radius: 4px; }}

.detail-section {{ margin-bottom: 18px; }}
.detail-section:last-child {{ margin-bottom: 0; }}
.detail-section h4 {{
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin: 0 0 8px 0;
}}
.detail-text {{
  font-size: 12.5px;
  line-height: 1.6;
  color: var(--text);
}}
.detail-element {{
  font-family: ui-monospace, "SF Mono", Monaco, monospace;
  font-size: 11px;
  background: var(--panel-raised);
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  color: var(--text-dim);
  line-height: 1.5;
  word-break: break-word;
}}
.detail-rec {{
  background: rgba(34,197,94,0.08);
  border-left: 3px solid var(--success);
  padding: 12px 14px;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  font-size: 12.5px;
  line-height: 1.55;
  color: var(--text);
}}
.detail-source {{
  background: var(--panel-raised);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  font-size: 12px;
}}
.detail-source-name {{
  color: var(--amber);
  font-weight: 500;
  margin-bottom: 6px;
  word-break: break-word;
}}
.detail-source-tier {{
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: var(--text-muted);
}}
.tier {{
  font-size: 9px;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 3px;
  letter-spacing: 0.04em;
}}
.tier.gold {{ background: var(--tier-gold-bg); color: var(--tier-gold-text); }}
.tier.silver {{ background: var(--tier-silver-bg); color: var(--tier-silver-text); }}
.tier.bronze {{ background: var(--tier-bronze-bg); color: var(--tier-bronze-text); }}

.detail-source a {{ color: var(--amber); word-break: break-all; }}

.detail-ethics-banner {{
  background: var(--severity-medium-bg);
  border: 1px solid var(--severity-medium-border);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  margin-bottom: 14px;
  font-size: 12px;
  color: var(--severity-medium);
}}
.detail-ethics-banner.block {{ background: var(--severity-high-bg); border-color: var(--severity-high-border); color: var(--severity-high); }}
.detail-ethics-banner strong {{ letter-spacing: 0.05em; }}

.detail-actions {{
  padding: 12px 16px;
  border-top: 1px solid var(--border);
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  flex-shrink: 0;
}}
.detail-btn {{
  flex: 1;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
  border: 1px solid transparent;
  transition: all 0.15s ease;
  text-align: center;
}}
.detail-btn-skip {{
  background: transparent;
  border-color: var(--border);
  color: var(--text-dim);
}}
.detail-btn-skip:hover {{ color: var(--text); border-color: var(--border-strong); }}
.detail-btn-add {{
  background: var(--amber);
  color: #141414;
}}
.detail-btn-add:hover {{ background: #ffb43c; }}
.detail-btn-add.added {{
  background: var(--success);
  color: #0a0a0a;
}}
.detail-btn-editor-queue,
.detail-btn-editor-open {{
  background: var(--panel-raised);
  border-color: var(--border);
  color: var(--text);
}}
.detail-btn-editor-open {{
  border-color: var(--amber-dim);
  color: var(--amber);
}}
.detail-btn-editor-queue:hover,
.detail-btn-editor-open:hover {{
  border-color: var(--border-strong);
}}
.detail-btn-editor-queue.queued {{
  background: rgba(34,197,94,0.12);
  border-color: var(--severity-low-border);
  color: var(--success);
}}

/* ============================================================
   Bottom bar
   ============================================================ */
.app-bottom {{
  height: var(--bottom-h);
  padding: 0 20px;
  background: #0a0a0a;
  border-top: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}}
.bottom-left {{
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}}
.brief-count {{
  font-size: 13px;
  color: var(--text-dim);
}}
.brief-count strong {{
  color: var(--amber);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}}
.bottom-meta {{
  font-size: 10px;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.bottom-disclaimer {{
  font-size: 10px;
  font-style: italic;
  color: var(--text-muted);
  opacity: 0.8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}
.bottom-actions {{
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}}

/* ============================================================
   Export modal
   ============================================================ */
.modal-overlay {{
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.62);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.18s ease;
  z-index: 100;
}}
.modal-overlay.visible {{ opacity: 1; pointer-events: auto; }}

.modal {{
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  width: min(760px, 92vw);
  max-height: 82vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 24px 80px rgba(0,0,0,0.6);
  transform: scale(0.97);
  transition: transform 0.18s ease;
}}
.modal-overlay.visible .modal {{ transform: scale(1); }}

.modal-head {{
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}}
.modal-head h2 {{ font-size: 16px; font-weight: 700; margin: 0; }}
.modal-close {{
  width: 30px; height: 30px;
  border: 1px solid var(--border);
  background: var(--panel-raised);
  border-radius: var(--radius-sm);
  color: var(--text-dim);
  font-size: 18px;
  display: flex; align-items: center; justify-content: center;
}}
.modal-close:hover {{ color: var(--text); }}

.modal-body {{
  flex: 1;
  overflow: hidden;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}}
.export-tabs {{
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}}
.export-tab {{
  padding: 7px 14px;
  font-size: 12px;
  font-weight: 600;
  background: var(--panel-raised);
  color: var(--text-dim);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}}
.export-tab.active {{ background: var(--amber-dim); color: var(--amber); border-color: var(--amber); }}

.export-preview {{
  flex: 1;
  min-height: 280px;
  background: #0a0a0a;
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 14px 16px;
  font-family: ui-monospace, "SF Mono", Monaco, monospace;
  font-size: 12px;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
  resize: none;
  caret-color: var(--amber);
}}
.export-preview:focus {{
  outline: none;
  border-color: var(--amber-dim);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--amber-dim) 28%, transparent);
}}
.export-hint {{
  margin-top: 8px;
  font-size: 11px;
  color: var(--text-muted);
  font-style: italic;
}}
.modal-foot {{
  padding: 12px 20px;
  border-top: 1px solid var(--border);
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}}

/* ============================================================
   Responsive — below 1280 collapse right panel, below 1024 stack
   ============================================================ */
@media (max-width: 1440px) {{
  .callout {{ width: 296px; }}
}}
@media (max-width: 1280px) {{
  :root {{ --panel-width-left: 360px; --panel-width-right: 360px; }}
  .screenshot-wrapper {{ gap: 16px; padding: 4px 12px; }}
}}
@media (max-width: 1100px) {{
  :root {{ --panel-width-left: 340px; --panel-width-right: 340px; }}
  .app-header-meta {{ display: none; }}
}}
@media (max-width: 960px) {{
  html, body {{ overflow-y: auto; height: auto; }}
  .app-main {{ flex-direction: column; height: auto; }}
  .panel-left, .panel-right {{ width: 100%; max-height: none; border-right: none; border-left: none; border-bottom: 1px solid var(--border); }}
  .panel-center {{ order: -1; }}
  /* Stack callout below screenshot; flip the leader arrow to point up. */
  .screenshot-wrapper {{ flex-direction: column; gap: 14px; }}
  .callout {{ width: 100%; max-width: 520px; }}
  .callout:not(.review-positioned)::before, .callout:not(.review-positioned)::after {{
    top: -10px;
    right: auto;
    left: 32px;
    border-width: 0 9px 10px 9px;
    border-color: transparent transparent var(--border-strong) transparent;
    transform: none;
  }}
  .callout:not(.review-positioned)::after {{
    top: -9px;
    border-width: 0 8px 9px 8px;
    border-color: transparent transparent var(--panel-raised) transparent;
  }}
}}
"""
