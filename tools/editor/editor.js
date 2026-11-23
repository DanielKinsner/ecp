(() => {
  "use strict";
  const CURRENT_REVIEW_STATE_VERSION = 1;
  const STORAGE_PREFIX = "ecp-review-state:";
  const payload = JSON.parse(document.getElementById("ecp-review-payload").textContent);
  const migrations = {};

  const SEVERITY_COLORS = {
    critical: "#EF4444",
    high: "#F97316",
    medium: "#FACC15",
    low: "#60A5FA",
    info: "#9CA3AF"
  };
  const STATUS_LABELS = {
    needs_review: "To review",
    tagged_for_ai_pass: "AI pass",
    edited: "Edited",
    approved: "Done",
    hidden: "Hidden"
  };
  const FILTERS = [
    { key: "queue", label: "Queue" },
    { key: "all", label: "All" },
    { key: "approved", label: "Done" },
    { key: "hidden", label: "Hidden" }
  ];

  // Every field the canonical renderer honors as an operator override, paired
  // with the AI original it replaces. `override` is what gets written to the
  // review state; a null override means "use the AI's words".
  const TEXT_FIELDS = [
    {
      override: "finding_title_override",
      label: "Finding title",
      rows: 2,
      hint: "The headline the client reads in the report body.",
      original: f => f.finding_title
    },
    {
      override: "observation_override",
      label: "Observation",
      rows: 4,
      hint: "What is actually on the page.",
      original: f => f.observation
    },
    {
      override: "recommendation_override",
      label: "Recommendation",
      rows: 4,
      hint: "What you are telling them to do.",
      original: f => f.recommendation
    },
    {
      override: "why_this_matters_override",
      label: "Why it matters",
      rows: 3,
      original: f => f.why_this_matters
    },
    {
      override: "element_override",
      label: "Element",
      rows: 2,
      hint: "The page element this finding points at.",
      original: f => f.raw?.element
    },
    {
      override: "callout_title_override",
      label: "Callout title",
      rows: 2,
      hint: "Shown on the screenshot overlay, not in the report body.",
      original: f => f.callout_title
    },
    {
      override: "callout_body_override",
      label: "Callout body",
      rows: 3,
      original: f => f.callout_body
    }
  ];
  const SEVERITIES = ["critical", "high", "medium", "low", "info"];

  const PREFS_KEY = "ecp-editor-prefs";
  const PRESETS_KEY = "ecp-editor-presets";
  const RENDER_MARK_PREFIX = "ecp-review-render-mark:";

  const app = {
    devices: payload.devices || Object.keys(payload.states || {}),
    inlineStates: clone(payload.states || {}),
    states: clone(payload.states || {}),
    images: payload.slide_images || {},
    activeDevice: null,
    activeFindingRef: null,
    activeSlide: 0,
    activeTool: "highlight",
    filter: "queue",
    zoom: 1,
    fitZoom: true,
    showGhosts: false,
    search: "",
    inspectorOpen: false,
    selectedEffect: null, // { slideId, index }
    drag: null,
    undoStack: [],
    redoStack: []
  };

  const el = id => document.getElementById(id);
  const stage = el("stage");
  const stageWrap = el("stageWrap");
  const slideImage = el("slideImage");

  // ---------- generic helpers ----------
  function clone(value) { return JSON.parse(JSON.stringify(value)); }
  function clamp(n, min, max) {
    n = Number(n);
    if (!Number.isFinite(n)) return min;
    return Math.min(max, Math.max(min, n));
  }
  function esc(s) {
    const div = document.createElement("div");
    div.textContent = s == null ? "" : String(s);
    return div.innerHTML;
  }
  function normalizeHex(value) {
    const v = String(value || "").trim();
    if (/^#[0-9a-fA-F]{6}$/.test(v)) return v;
    if (/^#[0-9a-fA-F]{3}$/.test(v)) {
      return "#" + v[1] + v[1] + v[2] + v[2] + v[3] + v[3];
    }
    return null;
  }
  function hexToRgba(hex, alpha) {
    const v = normalizeHex(hex) || "#FACC15";
    const r = parseInt(v.slice(1, 3), 16);
    const g = parseInt(v.slice(3, 5), 16);
    const b = parseInt(v.slice(5, 7), 16);
    return `rgba(${r},${g},${b},${alpha})`;
  }
  function nowIso() { return new Date().toISOString(); }

  // ---------- state access ----------
  function state() { return app.states[app.activeDevice]; }
  function storageKey(device, s) {
    s = s || app.states[device];
    return `${STORAGE_PREFIX}${s.engagement_id}:${device}`;
  }
  function editorPickKey(device, s) {
    s = s || app.states[device];
    return `ecp-editor-picks:${s.engagement_id}:${device}`;
  }
  function isServerBacked() {
    return location.protocol === "http:" || location.protocol === "https:";
  }
  function findingByRef(ref, s = state()) {
    return (s.findings || []).find(f => f.f_ref === ref) || null;
  }
  function activeFinding() { return findingByRef(app.activeFindingRef); }
  function markerFor(finding, s = state()) {
    if (!finding) return null;
    return (s.markers || []).find(m => m.marker_id === finding.marker_id) || null;
  }
  function currentSlide(s = state()) { return (s.slides || [])[app.activeSlide] || null; }
  function slideIndexById(slideId, s = state()) {
    return (s.slides || []).findIndex(slide => slide.slide_id === slideId);
  }
  function slideEditFor(slideId, s = state()) {
    let edit = (s.slide_edits || []).find(e => e.slide_id === slideId);
    if (!edit) {
      edit = {
        slide_id: slideId,
        crop: { x_pct: 0, y_pct: 0, w_pct: 100, h_pct: 100 },
        transform: { scale: 1.0, rotate_deg: 0, translate_x_pct: 0, translate_y_pct: 0 },
        effects: []
      };
      s.slide_edits = s.slide_edits || [];
      s.slide_edits.push(edit);
    }
    return edit;
  }
  function slideImageSrc(slide, s = state()) {
    if (!slide) return "";
    const fromPayload = app.images[app.activeDevice]?.[slide.slide_id];
    if (fromPayload) return fromPayload;
    if (slide.asset_id) {
      const asset = (s.imported_assets || []).find(a => a.asset_id === slide.asset_id);
      if (asset?.data_url) return asset.data_url;
      if (asset?.source) return asset.source;
    }
    return slide.source || "";
  }

  // ---------- marker geometry ----------
  // Normalized display box {x,y,w,h} in % of the slide, or null when unplaced.
  function markerBox(marker) {
    if (!marker || marker.hidden === true) return null;
    const shape = String(marker.shape || "").toLowerCase();
    if (shape === "polygon" || shape === "freeform") {
      const pts = (marker.points || [])
        .map(p => Array.isArray(p) ? p : (p && "x" in p ? [p.x, p.y] : null))
        .filter(p => p && Number.isFinite(Number(p[0])) && Number.isFinite(Number(p[1])));
      if (!pts.length) return null;
      const xs = pts.map(p => Number(p[0]));
      const ys = pts.map(p => Number(p[1]));
      const x = Math.min(...xs);
      const y = Math.min(...ys);
      return { x, y, w: Math.max(...xs) - x, h: Math.max(...ys) - y };
    }
    if (shape === "ellipse") {
      const cx = Number(marker.cx_pct ?? marker.cx);
      const cy = Number(marker.cy_pct ?? marker.cy);
      const rx = Number(marker.rx_pct ?? marker.rx);
      const ry = Number(marker.ry_pct ?? marker.ry);
      if (![cx, cy, rx, ry].every(Number.isFinite)) return null;
      return { x: cx - rx, y: cy - ry, w: rx * 2, h: ry * 2 };
    }
    if (shape === "point") {
      const cx = Number(marker.cx_pct ?? marker.cx);
      const cy = Number(marker.cy_pct ?? marker.cy);
      if (!Number.isFinite(cx) || !Number.isFinite(cy)) return null;
      return { x: cx - 2, y: cy - 1.2, w: 4, h: 2.4 };
    }
    const x = Number(marker.x_pct);
    const y = Number(marker.y_pct);
    const w = Number(marker.w_pct);
    const h = Number(marker.h_pct);
    if (![x, y, w, h].every(Number.isFinite) || w <= 0 || h <= 0) return null;
    return { x, y, w, h };
  }
  function needsPlacement(finding, s = state()) {
    return !markerBox(markerFor(finding, s));
  }
  function setMarkerRect(marker, box) {
    // Converting any legacy shape to a plain rect on write keeps the renderer's
    // geometry path simple and drops stale center/radius/point fields.
    delete marker.cx_pct; delete marker.cy_pct; delete marker.cx; delete marker.cy;
    delete marker.rx_pct; delete marker.ry_pct; delete marker.rx; delete marker.ry;
    delete marker.points; delete marker.closed;
    marker.shape = "rect";
    marker.hidden = false;
    marker.source = "manual";
    marker.x_pct = Math.round(box.x * 1000) / 1000;
    marker.y_pct = Math.round(box.y * 1000) / 1000;
    marker.w_pct = Math.round(box.w * 1000) / 1000;
    marker.h_pct = Math.round(box.h * 1000) / 1000;
  }
  function ensureMarker(finding, s = state()) {
    let marker = markerFor(finding, s);
    if (!marker) {
      marker = {
        marker_id: finding.marker_id || `marker-${finding.f_ref.replace(/[^a-zA-Z0-9_-]+/g, "-")}`,
        f_ref: finding.f_ref,
        slide_id: currentSlide(s)?.slide_id,
        shape: "rect",
        stroke: severityColor(finding),
        stroke_width: 3,
        source: "manual",
        snapped_baton_index: null
      };
      finding.marker_id = marker.marker_id;
      s.markers = s.markers || [];
      s.markers.push(marker);
    }
    return marker;
  }
  // The operator's severity wins over the AI's everywhere the editor shows a
  // severity — dot color, default stroke, callout chip — so what you see in
  // the editor is what the report will file the finding as.
  function activeSeverity(finding) {
    const override = String(finding?.severity_override || "").toLowerCase();
    if (SEVERITIES.includes(override)) return override;
    return String(finding?.severity || "").toLowerCase();
  }
  function severityColor(finding) {
    return SEVERITY_COLORS[activeSeverity(finding)] || "#FACC15";
  }
  function markerColor(marker, finding) {
    return normalizeHex(marker?.stroke) || severityColor(finding);
  }
  function markerStyle(marker) {
    const style = String(marker?.highlight_style || "").toLowerCase();
    if (style) return style;
    if (marker?.spotlight_visible) return "spotlight";
    return "outline";
  }

  // ---------- finding ordering / filters ----------
  function sortedFindings(s = state()) {
    const slideOrder = new Map((s.slides || []).map((slide, i) => [slide.slide_id, i]));
    const markersById = new Map((s.markers || []).map(m => [m.marker_id, m]));
    return [...(s.findings || [])].sort((a, b) => {
      const sa = slideOrder.get(markersById.get(a.marker_id)?.slide_id) ?? 999;
      const sb = slideOrder.get(markersById.get(b.marker_id)?.slide_id) ?? 999;
      const ia = Number(a.raw?.index ?? 999);
      const ib = Number(b.raw?.index ?? 999);
      return sa - sb || ia - ib || String(a.f_ref).localeCompare(String(b.f_ref));
    });
  }
  function isPicked(f) {
    if (f?.review_selected === true) return true;
    if (f?.review_selected === false) return false;
    return f?.needs_manual_edit === true;
  }
  // Free-text match across everything the operator can see or search for. Kept
  // deliberately broad (ref, both title layers, body copy, cluster, severity)
  // because on a 40-finding report you remember the wording, not the F-number.
  function matchesSearch(f, needle = app.search) {
    if (!needle) return true;
    const hay = [
      f.f_ref,
      f.finding_title, f.finding_title_override,
      f.callout_title, f.callout_title_override,
      f.callout_body, f.callout_body_override,
      f.observation, f.observation_override,
      f.recommendation, f.recommendation_override,
      f.cluster, f.severity, f.severity_override,
      f.raw?.element, f.raw?.section
    ].filter(Boolean).join(" ").toLowerCase();
    return needle.toLowerCase().split(/\s+/).filter(Boolean).every(word => hay.includes(word));
  }
  // `options.ignoreSearch` keeps the filter-tab counts honest: they always
  // report the whole bucket, so a stale search box can't make it look like
  // findings vanished from the Queue.
  function filteredFindings(filter = app.filter, s = state(), options = {}) {
    let findings = sortedFindings(s);
    if (!options.ignoreSearch) findings = findings.filter(f => matchesSearch(f));
    if (filter === "approved") return findings.filter(f => f.status === "approved");
    if (filter === "hidden") return findings.filter(f => f.status === "hidden");
    if (filter === "queue") {
      return findings.filter(f =>
        f.status !== "approved" && f.status !== "hidden" && (isPicked(f) || needsPlacement(f, s)));
    }
    return findings.filter(f => f.status !== "hidden");
  }
  function shortRef(f) {
    const raw = String(f.f_ref || "");
    return raw.includes("/") ? raw.split("/").pop() : raw;
  }

  // ---------- persistence ----------
  function saveLocal(options = {}) {
    const saved = saveStateForDevice(app.activeDevice, state(), options);
    // Stamp the edit so the Render button can tell the operator when the HTML
    // on disk is older than what is in front of them.
    if (saved) markEdited();
    return saved;
  }
  function saveStateForDevice(device, s, options = {}) {
    try {
      s.updated_at = nowIso();
      localStorage.setItem(storageKey(device, s), JSON.stringify(s));
      if (!options.quiet) flashStatus("Saved");
      return true;
    } catch (error) {
      const quota = error?.name === "QuotaExceededError"
        ? " Browser storage is full; use Save JSON to keep your work."
        : "";
      showError(`Could not save review state.${quota} ${error?.message || error || ""}`.trim());
      return false;
    }
  }
  function loadSavedState(device, inlineState) {
    const savedText = localStorage.getItem(storageKey(device, inlineState));
    if (!savedText) return null;
    try {
      const parsed = migrateForEditor(JSON.parse(savedText));
      const savedTime = Date.parse(parsed.updated_at || "");
      const inlineTime = Date.parse(inlineState.updated_at || "");
      if (Number.isFinite(inlineTime) && Number.isFinite(savedTime) && inlineTime > savedTime) {
        console.warn(`Skipped localStorage restore for ${device}: inline review state is newer.`);
        return null;
      }
      return parsed;
    } catch (error) {
      showError(error.message || String(error));
      return null;
    }
  }
  function migrateForEditor(reviewState) {
    let version = reviewState.review_state_schema_version;
    if (version === CURRENT_REVIEW_STATE_VERSION) return reviewState;
    if (version > CURRENT_REVIEW_STATE_VERSION) {
      throw new Error("This review state was produced by a newer editor. Upgrade your editor.");
    }
    while (version < CURRENT_REVIEW_STATE_VERSION) {
      const key = `${version}-to-${version + 1}`;
      if (!migrations[key]) {
        throw new Error("This review state was produced by an older editor; no migration is available.");
      }
      reviewState = migrations[key](reviewState);
      version = reviewState.review_state_schema_version;
    }
    return reviewState;
  }

  // ---------- undo / redo ----------
  function snapshot() { return { device: app.activeDevice, state: clone(state()) }; }
  function pushUndo(snap) {
    app.undoStack.push(snap);
    if (app.undoStack.length > 60) app.undoStack.shift();
    app.redoStack = [];
  }
  function mutate(fn) {
    const snap = snapshot();
    fn();
    pushUndo(snap);
    saveLocal({ quiet: true });
    render();
  }
  function undo() {
    const entry = app.undoStack.pop();
    if (!entry) return;
    app.redoStack.push({ device: entry.device, state: clone(app.states[entry.device]) });
    app.states[entry.device] = entry.state;
    app.activeDevice = entry.device;
    app.selectedEffect = null;
    saveLocal({ quiet: true });
    render();
  }
  function redo() {
    const entry = app.redoStack.pop();
    if (!entry) return;
    app.undoStack.push({ device: entry.device, state: clone(app.states[entry.device]) });
    app.states[entry.device] = entry.state;
    app.activeDevice = entry.device;
    app.selectedEffect = null;
    saveLocal({ quiet: true });
    render();
  }

  // ---------- routing / report picks ----------
  function editorRoute() {
    const params = new URLSearchParams(String(location.hash || "").replace(/^#/, ""));
    return {
      device: params.get("device") || "",
      pick: params.get("pick") || params.get("edit") || ""
    };
  }
  function findIncomingFinding(s, id) {
    const needle = String(id || "");
    if (!needle) return null;
    return (s.findings || []).find(f => {
      const candidates = [
        f.f_ref,
        String(f.f_ref || "").replace(/^(.+)\s+(F-\d+)$/, "$1/$2"),
        f.fid,
        f.raw?.fid,
        f.raw?.f_ref,
        f.raw?.short_code,
        f.short_code
      ].filter(Boolean).map(String);
      return candidates.includes(needle) || candidates.some(v => v.endsWith(`/${needle}`));
    }) || null;
  }
  function applyIncomingEditorPicks(route) {
    let activated = null;
    app.devices.forEach(device => {
      const s = app.states[device];
      if (!s) return;
      const picks = new Set();
      try {
        const stored = JSON.parse(localStorage.getItem(editorPickKey(device, s)) || "[]");
        if (Array.isArray(stored)) stored.forEach(id => picks.add(String(id)));
      } catch (error) {
        console.warn("Could not read editor queue", error);
      }
      if (route.pick && (!route.device || route.device === device)) picks.add(route.pick);
      if (!picks.size) return;
      picks.forEach(id => {
        const f = findIncomingFinding(s, id);
        if (!f) return;
        f.review_selected = true;
        if (f.status === "approved") f.status = "needs_review";
        if (!activated && device === app.activeDevice) activated = f.f_ref;
      });
      saveStateForDevice(device, s, { quiet: true });
      localStorage.removeItem(editorPickKey(device, s));
    });
    return activated;
  }

  // ---------- messages ----------
  let statusTimer = null;
  function flashStatus(text) {
    const node = el("statusMessage");
    node.textContent = text;
    clearTimeout(statusTimer);
    statusTimer = setTimeout(() => { node.textContent = ""; }, 2400);
  }
  function showError(text) {
    const node = el("errorMessage");
    node.textContent = text;
    node.hidden = !text;
  }

  // ---------- finding activation / edits ----------
  function ensureFilterShows(ref) {
    const finding = findingByRef(ref);
    if (!finding) return;
    // Status buckets only — a search box that happens to exclude the finding
    // must not bounce the operator into a different tab.
    if (filteredFindings(app.filter, state(), { ignoreSearch: true }).some(f => f.f_ref === ref)) return;
    if (finding.status === "hidden") app.filter = "hidden";
    else if (finding.status === "approved") app.filter = "approved";
    else app.filter = "all";
  }
  function activateFinding(ref, options = {}) {
    app.activeFindingRef = ref;
    app.selectedEffect = null;
    if (ref) ensureFilterShows(ref);
    const finding = activeFinding();
    if (finding && !options.staySlide) {
      const marker = markerFor(finding);
      const idx = slideIndexById(marker?.slide_id || finding.callout_slide_id);
      if (idx >= 0) app.activeSlide = idx;
    }
    render();
  }
  function touchFinding(finding) {
    if (finding.status === "needs_review" || finding.status === "approved" || finding.status === "tagged_for_ai_pass") {
      finding.status = "edited";
    }
  }
  function defaultCalloutPosition(box) {
    return {
      x_pct: Math.min(74, Math.max(4, box.x + box.w + 2)),
      y_pct: Math.min(82, Math.max(4, box.y - 4)),
      w_pct: 22,
      h_pct: 8,
      anchor: "auto"
    };
  }
  function placeMarker(finding, box) {
    const marker = ensureMarker(finding);
    setMarkerRect(marker, box);
    marker.slide_id = currentSlide().slide_id;
    if (!normalizeHex(marker.stroke)) marker.stroke = severityColor(finding);
    if (!marker.highlight_style) marker.highlight_style = "outline";
    finding.callout_slide_id = marker.slide_id;
    if (finding.hotspot_confidence === "needs-manual-marker") {
      finding.hotspot_confidence = "exact-selector";
    }
    if (!finding.callout_position || finding.callout_position_source !== "manual") {
      finding.callout_position = defaultCalloutPosition(markerBox(marker));
    }
    syncDerivedEffects(finding);
    touchFinding(finding);
  }

  // ---------- pointer interaction ----------
  function pctPoint(evt) {
    const rect = slideImage.getBoundingClientRect();
    if (!rect.width || !rect.height) return null;
    return {
      x: ((evt.clientX - rect.left) / rect.width) * 100,
      y: ((evt.clientY - rect.top) / rect.height) * 100
    };
  }
  function normalizedRect(a, b) {
    const x = Math.min(a.x, b.x);
    const y = Math.min(a.y, b.y);
    return {
      x: clamp(x, 0, 100),
      y: clamp(y, 0, 100),
      w: clamp(Math.abs(a.x - b.x), 0, 100 - clamp(x, 0, 100)),
      h: clamp(Math.abs(a.y - b.y), 0, 100 - clamp(y, 0, 100))
    };
  }

  function onStagePointerDown(evt) {
    if (evt.button !== 0) return;
    const target = evt.target;
    if (target.closest("[contenteditable]")) return;

    const handle = target.closest(".handle");
    const point = pctPoint(evt);
    if (!point) return;

    const finding = activeFinding();
    const grip = target.closest(".callout-grip");
    if (grip && finding) {
      startDrag(evt, {
        kind: "callout-move",
        start: point,
        origin: clone(finding.callout_position || defaultCalloutPosition({ x: point.x, y: point.y, w: 0, h: 0 }))
      });
      return;
    }
    if (target.closest(".callout")) return;

    if (handle) {
      const owner = handle.parentElement;
      if (owner.classList.contains("hotspot") && finding) {
        startDrag(evt, {
          kind: "marker-resize",
          dir: handle.dataset.dir,
          start: point,
          origin: markerBox(markerFor(finding))
        });
        return;
      }
      if (owner.dataset.effectIndex != null) {
        selectEffect(owner.dataset.slideId, Number(owner.dataset.effectIndex));
        startDrag(evt, {
          kind: "effect-resize",
          dir: handle.dataset.dir,
          start: point,
          origin: cloneEffectRect(owner)
        });
        return;
      }
    }

    const ghost = target.closest(".ghost-hotspot");
    if (ghost) {
      activateFinding(ghost.dataset.ref, { staySlide: true });
      return;
    }

    const hotspot = target.closest(".hotspot");
    if (hotspot && finding) {
      startDrag(evt, {
        kind: "marker-move",
        start: point,
        origin: markerBox(markerFor(finding))
      });
      return;
    }

    const region = target.closest(".blur-region, .dim-region");
    if (region) {
      selectEffect(region.dataset.slideId, Number(region.dataset.effectIndex));
      startDrag(evt, {
        kind: "effect-move",
        start: point,
        origin: cloneEffectRect(region)
      });
      return;
    }

    // Background: draw with the active tool.
    if (!finding) return;
    if (app.selectedEffect) { app.selectedEffect = null; renderStage(); }
    startDrag(evt, {
      kind: app.activeTool === "blur" ? "draw-blur" : "draw-marker",
      start: point,
      current: point
    });
  }

  function cloneEffectRect(node) {
    const slideId = node.dataset.slideId;
    const idx = Number(node.dataset.effectIndex);
    const effect = slideEditFor(slideId).effects[idx];
    return clone(effect.rect);
  }

  function startDrag(evt, drag) {
    drag.snapshot = snapshot();
    drag.moved = false;
    app.drag = drag;
    stage.setPointerCapture?.(evt.pointerId);
    evt.preventDefault();
  }

  function onStagePointerMove(evt) {
    const drag = app.drag;
    if (!drag) return;
    const point = pctPoint(evt);
    if (!point) return;
    const dx = point.x - drag.start.x;
    const dy = point.y - drag.start.y;
    if (Math.abs(dx) > 0.05 || Math.abs(dy) > 0.05) drag.moved = true;
    const finding = activeFinding();

    if (drag.kind === "draw-marker" || drag.kind === "draw-blur") {
      drag.current = point;
      renderDrawPreview(normalizedRect(drag.start, drag.current));
      return;
    }
    if (!finding) return;

    if (drag.kind === "marker-move" && drag.origin) {
      const box = { ...drag.origin };
      box.x = clamp(drag.origin.x + dx, 0, 100 - drag.origin.w);
      box.y = clamp(drag.origin.y + dy, 0, 100 - drag.origin.h);
      setMarkerRect(markerFor(finding) || ensureMarker(finding), box);
      renderStage();
      return;
    }
    if (drag.kind === "marker-resize" && drag.origin) {
      const box = resizeBox(drag.origin, drag.dir, dx, dy);
      setMarkerRect(markerFor(finding) || ensureMarker(finding), box);
      renderStage();
      return;
    }
    if (drag.kind === "callout-move" && drag.origin) {
      finding.callout_position = {
        ...drag.origin,
        x_pct: clamp(drag.origin.x_pct + dx, -80, 170),
        y_pct: clamp(drag.origin.y_pct + dy, -40, 140)
      };
      finding.callout_position_source = "manual";
      renderStage();
      return;
    }
    if ((drag.kind === "effect-move" || drag.kind === "effect-resize") && app.selectedEffect) {
      const effect = selectedEffectObject();
      if (!effect) return;
      if (drag.kind === "effect-move") {
        effect.rect = {
          x_pct: clamp(drag.origin.x_pct + dx, 0, 100 - drag.origin.w_pct),
          y_pct: clamp(drag.origin.y_pct + dy, 0, 100 - drag.origin.h_pct),
          w_pct: drag.origin.w_pct,
          h_pct: drag.origin.h_pct
        };
      } else {
        const box = resizeBox(
          { x: drag.origin.x_pct, y: drag.origin.y_pct, w: drag.origin.w_pct, h: drag.origin.h_pct },
          drag.dir, dx, dy
        );
        effect.rect = { x_pct: box.x, y_pct: box.y, w_pct: box.w, h_pct: box.h };
      }
      renderStage();
    }
  }

  function resizeBox(origin, dir, dx, dy) {
    let { x, y, w, h } = origin;
    if (dir.includes("w")) { x = origin.x + dx; w = origin.w - dx; }
    if (dir.includes("e")) { w = origin.w + dx; }
    if (dir.includes("n")) { y = origin.y + dy; h = origin.h - dy; }
    if (dir.includes("s")) { h = origin.h + dy; }
    if (w < 0) { x += w; w = -w; }
    if (h < 0) { y += h; h = -h; }
    x = clamp(x, 0, 100); y = clamp(y, 0, 100);
    return { x, y, w: clamp(w, 0.4, 100 - x), h: clamp(h, 0.4, 100 - y) };
  }

  function onStagePointerUp(evt) {
    const drag = app.drag;
    if (!drag) return;
    app.drag = null;
    clearDrawPreview();
    const finding = activeFinding();

    if (drag.kind === "draw-marker" || drag.kind === "draw-blur") {
      const point = pctPoint(evt) || drag.current || drag.start;
      const rect = normalizedRect(drag.start, point);
      if (!finding || rect.w < 0.5 || rect.h < 0.5) { render(); return; }
      if (drag.kind === "draw-marker") {
        placeMarker(finding, rect);
      } else {
        const slide = currentSlide();
        const edit = slideEditFor(slide.slide_id);
        edit.effects.push({
          type: "blur",
          f_ref: finding.f_ref,
          rect: { x_pct: rect.x, y_pct: rect.y, w_pct: rect.w, h_pct: rect.h },
          radius_px: Number(el("blurStrength").value) || 10,
          mode: "inside"
        });
        app.selectedEffect = { slideId: slide.slide_id, index: edit.effects.length - 1 };
        touchFinding(finding);
      }
      pushUndo(drag.snapshot);
      saveLocal({ quiet: true });
      render();
      return;
    }

    if (!drag.moved) { render(); return; }
    if (finding && (drag.kind === "marker-move" || drag.kind === "marker-resize")) {
      const marker = markerFor(finding);
      if (marker) {
        marker.slide_id = currentSlide().slide_id;
        finding.callout_slide_id = marker.slide_id;
        if (!finding.callout_position || finding.callout_position_source !== "manual") {
          finding.callout_position = defaultCalloutPosition(markerBox(marker));
        }
        syncDerivedEffects(finding);
      }
      touchFinding(finding);
    }
    if (finding && drag.kind === "callout-move") touchFinding(finding);
    if (drag.kind === "effect-move" || drag.kind === "effect-resize") {
      if (finding) touchFinding(finding);
    }
    pushUndo(drag.snapshot);
    saveLocal({ quiet: true });
    render();
  }

  // ---------- effects ----------
  function selectEffect(slideId, index) {
    app.selectedEffect = { slideId, index };
    renderStage();
    renderControls();
  }
  function selectedEffectObject(s = state()) {
    const sel = app.selectedEffect;
    if (!sel) return null;
    return slideEditFor(sel.slideId, s).effects[sel.index] || null;
  }
  function deleteSelectedEffect() {
    const sel = app.selectedEffect;
    if (!sel) return;
    mutate(() => {
      const edit = slideEditFor(sel.slideId);
      edit.effects.splice(sel.index, 1);
      app.selectedEffect = null;
      const finding = activeFinding();
      if (finding) touchFinding(finding);
    });
  }

  // ---------- derived effects (auto-managed, tied to the hotspot) ----------
  // "Blur surroundings" = a blur effect with mode:"outside" whose rect is the
  // hotspot box (the report blurs everything around that rect). Spotlight
  // intensity = a dim effect with NO rect — the report cuts the dim mask
  // around the hotspot at render time, so only the slide needs syncing.
  const isAroundBlur = e => String(e?.type || "").toLowerCase() === "blur" && e?.mode === "outside";
  const isSpotlightDim = e => String(e?.type || "").toLowerCase() === "dim" && !e?.rect;

  function findEffect(finding, pred, s = state()) {
    for (const se of s.slide_edits || []) {
      const index = (se.effects || []).findIndex(e => e?.f_ref === finding.f_ref && pred(e));
      if (index >= 0) return { slideEdit: se, index, effect: se.effects[index] };
    }
    return null;
  }
  function removeEffect(finding, pred) {
    const found = findEffect(finding, pred);
    if (found) found.slideEdit.effects.splice(found.index, 1);
    return !!found;
  }
  // Keep derived effects glued to the hotspot after it moves or changes slide.
  function syncDerivedEffects(finding) {
    const marker = markerFor(finding);
    const box = marker ? markerBox(marker) : null;
    [isAroundBlur, isSpotlightDim].forEach(pred => {
      const found = findEffect(finding, pred);
      if (!found) return;
      if (!box) { found.slideEdit.effects.splice(found.index, 1); return; }
      if (found.slideEdit.slide_id !== marker.slide_id) {
        found.slideEdit.effects.splice(found.index, 1);
        slideEditFor(marker.slide_id).effects.push(found.effect);
      }
      if (pred === isAroundBlur) {
        found.effect.rect = { x_pct: box.x, y_pct: box.y, w_pct: box.w, h_pct: box.h };
      }
    });
    app.selectedEffect = null;
  }

  // ---------- actions ----------
  function applyStyle(style) {
    const finding = activeFinding();
    if (!finding) return;
    mutate(() => {
      const marker = ensureMarker(finding);
      marker.highlight_style = style;
      marker.spotlight_visible = style === "spotlight";
      delete marker.fill_opacity;
      delete marker.glow_opacity;
      if (style === "glow") marker.glow_opacity = 0.65;
      if (style === "spotlight") {
        if (!findEffect(finding, isSpotlightDim)) {
          slideEditFor((markerFor(finding) || {}).slide_id || currentSlide().slide_id)
            .effects.push({ type: "dim", f_ref: finding.f_ref, opacity: 0.35 });
        }
      } else {
        removeEffect(finding, isSpotlightDim);
      }
      touchFinding(finding);
    });
  }
  function toggleAroundBlur() {
    const finding = activeFinding();
    if (!finding) return;
    const marker = markerFor(finding);
    const box = marker ? markerBox(marker) : null;
    if (!box) { flashStatus("Place the highlight box first"); return; }
    mutate(() => {
      if (removeEffect(finding, isAroundBlur)) { touchFinding(finding); return; }
      slideEditFor(marker.slide_id).effects.push({
        type: "blur",
        f_ref: finding.f_ref,
        mode: "outside",
        rect: { x_pct: box.x, y_pct: box.y, w_pct: box.w, h_pct: box.h },
        radius_px: Number(el("blurStrength").value) || 10
      });
      touchFinding(finding);
    });
  }
  function applyColor(color) {
    const finding = activeFinding();
    const hex = normalizeHex(color);
    if (!finding || !hex) return;
    mutate(() => {
      const marker = ensureMarker(finding);
      marker.stroke = hex;
      finding.callout_color = hex;
      touchFinding(finding);
    });
  }
  function approveActive() {
    const finding = activeFinding();
    if (!finding) return;
    const queue = filteredFindings();
    const idx = queue.findIndex(f => f.f_ref === finding.f_ref);
    mutate(() => {
      finding.status = "approved";
      finding.review_selected = false;
      finding.reviewed_at = nowIso();
    });
    const nextQueue = filteredFindings();
    const next = nextQueue[Math.min(idx, nextQueue.length - 1)];
    if (next) activateFinding(next.f_ref);
    flashStatus(`Approved ${shortRef(finding)}`);
  }
  function toggleHideActive() {
    const finding = activeFinding();
    if (!finding) return;
    mutate(() => {
      finding.status = finding.status === "hidden" ? "needs_review" : "hidden";
    });
  }
  function clearActivePlacement() {
    const finding = activeFinding();
    if (!finding) return;
    const marker = markerFor(finding);
    if (!marker || !markerBox(marker)) return;
    mutate(() => {
      delete marker.x_pct; delete marker.y_pct; delete marker.w_pct; delete marker.h_pct;
      delete marker.cx_pct; delete marker.cy_pct; delete marker.rx_pct; delete marker.ry_pct;
      delete marker.points;
      marker.shape = "point";
      marker.hidden = true;
      marker.source = "manual";
      finding.hotspot_confidence = "needs-manual-marker";
      syncDerivedEffects(finding);
      touchFinding(finding);
    });
  }
  function downloadState() {
    const s = state();
    saveLocal({ quiet: true });
    const blob = new Blob([JSON.stringify(s, null, 2) + "\n"], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `review-state-${s.device}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
    flashStatus(`Downloaded review-state-${s.device}.json`);
  }
  function engagementDirFromLocation() {
    // file:///C:/path/to/engagement/editor.html -> C:\path\to\engagement
    try {
      let p = decodeURIComponent(location.pathname).replace(/\/[^/]*$/, "");
      if (/^\/[A-Za-z]:/.test(p)) p = p.slice(1);
      return p.replace(/\//g, "\\");
    } catch {
      return "<engagement-folder>";
    }
  }
  function openRenderHelp() {
    const device = state().device;
    const dir = engagementDirFromLocation();
    el("cmdServe").textContent =
      `node scripts\\serve-editor.cjs --engagement "${dir}"`;
    el("cmdRender").textContent =
      `python scripts\\generate-report.py --engagement "${dir}" --device ${device} --plugin-root . --from-review review-state-${device}.json`;
    el("jsonName").textContent = `review-state-${device}.json`;
    el("finalName").textContent = `visual-report-${device}-final.html`;
    el("renderModal").hidden = false;
  }
  async function renderFinal() {
    saveLocal({ quiet: true });
    if (!isServerBacked()) {
      downloadState();
      openRenderHelp();
      return;
    }
    const button = el("exportFinal");
    button.disabled = true;
    flashStatus("Rendering…");
    try {
      const response = await fetch("/api/render-review", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ state: state() })
      });
      const result = await response.json();
      if (!result.ok) throw new Error(result.error || "render failed");
      showError("");
      markRendered();
      renderControls();
      flashStatus(`Rendered ${result.final_report}`);
      window.open(result.url, "_blank");
    } catch (error) {
      showError(`Render failed: ${error.message || error}`);
    } finally {
      button.disabled = false;
    }
  }

  // ---------- rendering ----------
  function render() {
    el("engagementLabel").textContent = `${state().engagement_id} · ${app.activeDevice}`;
    renderDeviceTabs();
    renderFilters();
    renderFindingList();
    renderSlideStrip();
    renderStage();
    renderControls();
    renderInspector();
  }

  function renderDeviceTabs() {
    const wrap = el("deviceTabs");
    wrap.innerHTML = "";
    if (app.devices.length < 2) return;
    app.devices.forEach(device => {
      const btn = document.createElement("button");
      btn.textContent = device;
      btn.className = device === app.activeDevice ? "is-active" : "";
      btn.addEventListener("click", () => {
        app.activeDevice = device;
        app.activeSlide = 0;
        app.selectedEffect = null;
        app.activeFindingRef = filteredFindings()[0]?.f_ref
          || sortedFindings()[0]?.f_ref || null;
        activateFinding(app.activeFindingRef);
      });
      wrap.appendChild(btn);
    });
  }

  function renderFilters() {
    const wrap = el("filterTabs");
    wrap.innerHTML = "";
    FILTERS.forEach(({ key, label }) => {
      const count = filteredFindings(key, state(), { ignoreSearch: true }).length;
      const btn = document.createElement("button");
      btn.textContent = `${label} (${count})`;
      btn.className = key === app.filter ? "is-active" : "";
      btn.addEventListener("click", () => {
        app.filter = key;
        savePrefs();
        renderFilters();
        renderFindingList();
      });
      wrap.appendChild(btn);
    });
  }

  function renderFindingList() {
    const wrap = el("findingList");
    wrap.innerHTML = "";
    const findings = filteredFindings();
    if (!findings.length) {
      const note = document.createElement("div");
      note.className = "empty-note";
      note.textContent = app.search
        ? `Nothing matches “${app.search}” in this tab.`
        : (app.filter === "queue"
          ? "Queue is clear — nothing waiting on you."
          : "No findings here.");
      wrap.appendChild(note);
      return;
    }
    findings.forEach(f => {
      const card = document.createElement("div");
      card.className = "finding-card" + (f.f_ref === app.activeFindingRef ? " is-active" : "");
      const unplaced = needsPlacement(f);
      const statusKey = unplaced && f.status !== "approved" && f.status !== "hidden" ? "place" : f.status;
      const statusLabel = statusKey === "place" ? "Place me" : (STATUS_LABELS[f.status] || f.status);
      const title = f.callout_title_override || f.callout_title || f.finding_title || "(untitled)";
      card.innerHTML =
        `<div class="card-head">` +
        `<span class="sev-dot" style="background:${esc(severityColor(f))}"></span>` +
        `<span class="card-ref">${esc(shortRef(f))}</span>` +
        `<span class="card-status ${esc(statusKey)}">${esc(statusLabel)}</span>` +
        `</div>` +
        `<div class="card-title">${esc(title)}</div>`;
      card.addEventListener("click", () => activateFinding(f.f_ref));
      wrap.appendChild(card);
    });
  }

  function renderSlideStrip() {
    const strip = el("slideStrip");
    strip.innerHTML = "";
    const slides = state().slides || [];
    slides.forEach((slide, idx) => {
      const thumb = document.createElement("div");
      thumb.className = "slide-thumb" + (idx === app.activeSlide ? " is-active" : "");
      const src = slideImageSrc(slide);
      thumb.innerHTML = src
        ? `<img src="${esc(src)}" alt="">`
        : `<div class="thumb-blank">${idx + 1}</div>`;
      thumb.title = slide.section_label || slide.slide_id;
      thumb.addEventListener("click", () => {
        app.activeSlide = idx;
        app.selectedEffect = null;
        renderSlideStrip();
        renderStage();
      });
      strip.appendChild(thumb);
    });
    const label = el("slideLabel");
    const slide = currentSlide();
    label.textContent = slides.length
      ? `${slide?.section_label || slide?.slide_id || ""} (${app.activeSlide + 1}/${slides.length})`
      : "No screenshots";
  }

  function renderStage() {
    const slide = currentSlide();
    const finding = activeFinding();
    const src = slideImageSrc(slide);
    if (slideImage.getAttribute("src") !== src) {
      slideImage.src = src;
      slideImage.onload = () => { applyZoom(); renderStage(); };
    }
    applyZoom();

    el("hudText").textContent = finding
      ? `${shortRef(finding)} — ${finding.callout_title_override || finding.callout_title || ""}`.trim()
      : "";

    renderEffects(slide, finding);
    renderSpotlight(slide, finding);
    renderMarkers(slide, finding);
    renderCallout(slide, finding);
    renderPlaceBanner(slide, finding);
  }

  function applyZoom() {
    if (!slideImage.naturalWidth) return;
    if (app.fitZoom) {
      const available = Math.max(320, stageWrap.clientWidth - 48);
      app.zoom = Math.min(2, available / slideImage.naturalWidth);
      el("zoomInput").value = String(Math.round(app.zoom * 100));
    }
    slideImage.style.width = `${slideImage.naturalWidth * app.zoom}px`;
  }

  function renderEffects(slide, finding) {
    const layer = el("effectLayer");
    layer.innerHTML = "";
    if (!slide || !finding) return;
    const edit = (state().slide_edits || []).find(e => e.slide_id === slide.slide_id);
    if (!edit) return;
    edit.effects.forEach((effect, index) => {
      if (effect.f_ref !== finding.f_ref) return;
      if (effect.hidden === true || !effect.rect) return;
      if (isAroundBlur(effect)) {
        // Four non-interactive pieces around the kept-clear rect, mirroring
        // the report's outside-mode rendering. Adjusted via the slider, not drag.
        const r = effect.rect;
        const radius = `${clamp(effect.radius_px ?? 10, 0, 18)}px`;
        const x = clamp(r.x_pct, 0, 100), y = clamp(r.y_pct, 0, 100);
        const w = clamp(r.w_pct, 0, 100 - x), h = clamp(r.h_pct, 0, 100 - y);
        [
          { x: 0, y: 0, w: 100, h: y },
          { x: 0, y: y + h, w: 100, h: Math.max(0, 100 - y - h) },
          { x: 0, y, w: x, h },
          { x: x + w, y, w: Math.max(0, 100 - x - w), h }
        ].forEach(piece => {
          if (piece.w <= 0 || piece.h <= 0) return;
          const div = document.createElement("div");
          div.className = "blur-around-piece";
          div.style.left = `${piece.x}%`;
          div.style.top = `${piece.y}%`;
          div.style.width = `${piece.w}%`;
          div.style.height = `${piece.h}%`;
          div.style.setProperty("--blur-r", radius);
          layer.appendChild(div);
        });
        return;
      }
      const type = String(effect.type || "").toLowerCase();
      if (type !== "blur" && type !== "dim") return;
      const node = document.createElement("div");
      node.className = type === "blur" ? "blur-region" : "dim-region";
      const selected = app.selectedEffect
        && app.selectedEffect.slideId === slide.slide_id
        && app.selectedEffect.index === index;
      if (selected) node.classList.add("is-selected");
      node.dataset.slideId = slide.slide_id;
      node.dataset.effectIndex = String(index);
      const r = effect.rect;
      node.style.left = `${clamp(r.x_pct, 0, 100)}%`;
      node.style.top = `${clamp(r.y_pct, 0, 100)}%`;
      node.style.width = `${clamp(r.w_pct, 0, 100)}%`;
      node.style.height = `${clamp(r.h_pct, 0, 100)}%`;
      if (type === "blur") node.style.setProperty("--blur-r", `${clamp(effect.radius_px ?? 10, 0, 18)}px`);
      if (type === "dim") node.style.setProperty("--dim-op", String(clamp(effect.opacity ?? 0.35, 0, 0.85)));
      ["nw", "n", "ne", "e", "se", "s", "sw", "w"].forEach(dir => {
        const handle = document.createElement("div");
        handle.className = `handle handle-${dir}`;
        handle.dataset.dir = dir;
        node.appendChild(handle);
      });
      layer.appendChild(node);
    });
  }

  function renderSpotlight(slide, finding) {
    const layer = el("spotlightLayer");
    layer.innerHTML = "";
    if (!slide || !finding) return;
    const marker = markerFor(finding);
    if (!marker || marker.slide_id !== slide.slide_id) return;
    if (markerStyle(marker) !== "spotlight") return;
    const box = markerBox(marker);
    if (!box) return;
    const opacity = clamp(findEffect(finding, isSpotlightDim)?.effect?.opacity ?? 0.28, 0, 0.85);
    const id = `spot-${Math.random().toString(36).slice(2, 9)}`;
    layer.innerHTML =
      `<defs><mask id="${id}">` +
      `<rect x="0" y="0" width="100" height="100" fill="white"/>` +
      `<rect x="${box.x}" y="${box.y}" width="${box.w}" height="${box.h}" rx="1.2" fill="black"/>` +
      `</mask></defs>` +
      `<rect class="spotlight-dim" style="fill:rgba(0,0,0,${opacity})" x="0" y="0" width="100" height="100" mask="url(#${id})"/>`;
  }

  function renderMarkers(slide, finding) {
    const layer = el("markerLayer");
    layer.innerHTML = "";
    if (!slide) return;
    const s = state();

    if (app.showGhosts) {
      sortedFindings(s).forEach(f => {
        if (f.f_ref === finding?.f_ref || f.status === "hidden") return;
        const marker = markerFor(f, s);
        if (!marker || marker.slide_id !== slide.slide_id) return;
        const box = markerBox(marker);
        if (!box) return;
        const ghost = document.createElement("div");
        ghost.className = "ghost-hotspot";
        ghost.dataset.ref = f.f_ref;
        ghost.style.left = `${box.x}%`;
        ghost.style.top = `${box.y}%`;
        ghost.style.width = `${box.w}%`;
        ghost.style.height = `${box.h}%`;
        ghost.innerHTML = `<span>${esc(shortRef(f))}</span>`;
        ghost.title = f.callout_title || f.f_ref;
        layer.appendChild(ghost);
      });
    }

    if (!finding) return;
    const marker = markerFor(finding);
    if (!marker || marker.slide_id !== slide.slide_id) return;
    const box = markerBox(marker);
    if (!box) return;
    const node = document.createElement("div");
    const style = markerStyle(marker);
    node.className = "hotspot";
    if (style === "glow") node.classList.add("style-glow");
    if (style === "fill") node.classList.add("style-fill");
    if (style === "underline") node.classList.add("style-underline");
    if (String(marker.shape).toLowerCase() === "ellipse") node.classList.add("is-ellipse");
    const color = markerColor(marker, finding);
    const glowOp = clamp(marker.glow_opacity ?? 0.65, 0.1, 0.95);
    node.style.setProperty("--sw", color);
    node.style.setProperty("--glow1", hexToRgba(color, glowOp));
    node.style.setProperty("--glow2", hexToRgba(color, glowOp * 0.6));
    node.style.setProperty("--fill", hexToRgba(color, 0.25));
    node.style.left = `${box.x}%`;
    node.style.top = `${box.y}%`;
    node.style.width = `${box.w}%`;
    node.style.height = `${box.h}%`;
    ["nw", "n", "ne", "e", "se", "s", "sw", "w"].forEach(dir => {
      const handle = document.createElement("div");
      handle.className = `handle handle-${dir}`;
      handle.dataset.dir = dir;
      node.appendChild(handle);
    });
    layer.appendChild(node);
  }

  function renderCallout(slide, finding) {
    const layer = el("calloutLayer");
    const connector = el("connectorLayer");
    layer.innerHTML = "";
    connector.innerHTML = "";
    if (!slide || !finding) return;
    if (finding.callout_visible === false) return;
    // An unplaced finding has no hotspot to point at — and a lingering callout
    // box would swallow the pointer events needed to draw the placement box.
    if (needsPlacement(finding)) return;
    const marker = markerFor(finding);
    const homeSlideId = finding.callout_slide_id || marker?.slide_id;
    if (homeSlideId !== slide.slide_id) return;

    const pos = finding.callout_position || defaultCalloutPosition(markerBox(marker) || { x: 40, y: 40, w: 20, h: 10 });
    const color = normalizeHex(finding.callout_color) || markerColor(marker, finding);
    const title = finding.callout_title_override ?? finding.callout_title ?? "";
    const body = finding.callout_body_override ?? finding.callout_body ?? "";

    const node = document.createElement("div");
    node.className = "callout";
    node.style.setProperty("--callout-accent", color);
    node.style.left = `${clamp(pos.x_pct, -80, 170)}%`;
    node.style.top = `${clamp(pos.y_pct, -40, 140)}%`;
    node.style.width = `${clamp(pos.w_pct ?? 22, 12, 100)}%`;
    node.innerHTML =
      `<div class="callout-grip"><span class="sev-chip">${esc((finding.severity || "note").toUpperCase())}</span>` +
      `<span>${esc(shortRef(finding))} — drag to move · click text to edit</span></div>` +
      `<div class="callout-title" contenteditable="true" data-edit="title" spellcheck="false">${esc(title)}</div>` +
      `<div class="callout-body" contenteditable="true" data-edit="body" spellcheck="false">${esc(body)}</div>`;
    layer.appendChild(node);

    node.querySelectorAll("[contenteditable]").forEach(field => {
      field.addEventListener("focus", () => { field.dataset.before = field.textContent; });
      field.addEventListener("blur", () => {
        const text = field.textContent.trim();
        if (text === field.dataset.before) return;
        mutate(() => {
          if (field.dataset.edit === "title") {
            finding.callout_title_override = text && text !== finding.callout_title ? text : null;
          } else {
            finding.callout_body_override = text && text !== finding.callout_body ? text : null;
          }
          touchFinding(finding);
        });
      });
      field.addEventListener("keydown", evt => {
        if (evt.key === "Enter" && field.dataset.edit === "title") { evt.preventDefault(); field.blur(); }
        if (evt.key === "Escape") { field.textContent = field.dataset.before; field.blur(); }
        evt.stopPropagation();
      });
    });

    // Connector line from the callout edge toward the hotspot center.
    const box = marker && marker.slide_id === slide.slide_id ? markerBox(marker) : null;
    if (box) {
      const cx = box.x + box.w / 2;
      const cy = box.y + box.h / 2;
      const ax = clamp(pos.x_pct, -80, 170);
      const ay = clamp(pos.y_pct, -40, 140) + 2;
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      const rect = slideImage.getBoundingClientRect();
      connector.setAttribute("viewBox", `0 0 ${rect.width || 100} ${rect.height || 100}`);
      const W = rect.width || 100, H = rect.height || 100;
      line.setAttribute("x1", String((ax / 100) * W));
      line.setAttribute("y1", String((ay / 100) * H));
      line.setAttribute("x2", String((cx / 100) * W));
      line.setAttribute("y2", String((cy / 100) * H));
      line.setAttribute("class", "connector-line");
      line.style.setProperty("--callout-accent", color);
      connector.appendChild(line);
    }
  }

  function renderPlaceBanner(slide, finding) {
    stageWrap.querySelector(".place-banner")?.remove();
    if (!slide || !finding) return;
    if (!needsPlacement(finding)) return;
    const banner = document.createElement("div");
    banner.className = "place-banner";
    banner.textContent = `${shortRef(finding)} is not placed — drag a box on the screenshot`;
    stageWrap.prepend(banner);
  }

  function renderDrawPreview(rect) {
    let preview = stage.querySelector(".draw-preview");
    if (!preview) {
      preview = document.createElement("div");
      preview.className = "draw-preview";
      stage.appendChild(preview);
    }
    preview.style.left = `${rect.x}%`;
    preview.style.top = `${rect.y}%`;
    preview.style.width = `${rect.w}%`;
    preview.style.height = `${rect.h}%`;
  }
  function clearDrawPreview() { stage.querySelector(".draw-preview")?.remove(); }

  function renderControls() {
    const finding = activeFinding();
    const marker = finding ? markerFor(finding) : null;
    document.querySelectorAll(".tool").forEach(btn => {
      btn.classList.toggle("is-active", btn.dataset.tool === app.activeTool);
    });
    const style = marker ? markerStyle(marker) : "outline";
    document.querySelectorAll(".style-btn").forEach(btn => {
      btn.classList.toggle("is-active", btn.dataset.style === style);
    });
    const color = marker ? markerColor(marker, finding) : null;
    document.querySelectorAll(".swatch").forEach(btn => {
      btn.classList.toggle("is-active", !!color && btn.dataset.color.toLowerCase() === color.toLowerCase());
    });
    if (color) el("customColor").value = color;
    el("calloutVisible").checked = finding ? finding.callout_visible !== false : true;
    el("hideFinding").textContent = finding?.status === "hidden" ? "Unhide" : "Hide";
    el("undoAction").disabled = !app.undoStack.length;
    el("redoAction").disabled = !app.redoStack.length;

    // Style intensity: glow -> marker.glow_opacity, spotlight -> dim-mask opacity.
    const intensityWrap = el("styleIntensityWrap");
    if (finding && style === "glow") {
      intensityWrap.hidden = false;
      el("styleIntensity").value = String(Math.round(clamp(marker?.glow_opacity ?? 0.65, 0.1, 0.95) * 100));
    } else if (finding && style === "spotlight") {
      intensityWrap.hidden = false;
      el("styleIntensity").value = String(Math.round(clamp(findEffect(finding, isSpotlightDim)?.effect?.opacity ?? 0.35, 0.1, 0.85) * 100));
    } else {
      intensityWrap.hidden = true;
    }

    // Blur controls: "Blur surroundings" toggle + a strength slider that edits
    // the selected region when there is one, otherwise the around-blur.
    const aroundEffect = finding ? findEffect(finding, isAroundBlur)?.effect : null;
    el("blurAround").classList.toggle("is-active", !!aroundEffect);
    const selected = selectedEffectObject();
    const selectedBlur = selected && String(selected.type).toLowerCase() === "blur" ? selected : null;
    const strengthTarget = selectedBlur || aroundEffect;
    el("blurStrengthWrap").hidden = !strengthTarget;
    if (strengthTarget) el("blurStrength").value = String(clamp(strengthTarget.radius_px ?? 10, 2, 18));
    el("deleteRegion").hidden = !selected;

    // Progress: approved out of everything still in the report.
    const all = (state().findings || []).filter(f => f.status !== "hidden");
    const done = all.filter(f => f.status === "approved").length;
    const progress = el("progressLabel");
    progress.textContent = all.length ? `Done ${done}/${all.length}` : "";
    progress.classList.toggle("all-done", all.length > 0 && done === all.length);

    const exportBtn = el("exportFinal");
    const stale = hasUnrenderedEdits();
    exportBtn.classList.toggle("has-unrendered", stale);
    exportBtn.title = stale
      ? "You have edits the rendered report does not include yet — render to update it"
      : "Write review state and render the final client report";
  }

  // ---------- UI preferences (survive a reload) ----------
  function loadPrefs() {
    let prefs = {};
    try { prefs = JSON.parse(localStorage.getItem(PREFS_KEY) || "{}") || {}; } catch { prefs = {}; }
    app.showGhosts = prefs.showGhosts === true;
    app.inspectorOpen = prefs.inspectorOpen === true;
    if (prefs.activeTool === "blur" || prefs.activeTool === "highlight") app.activeTool = prefs.activeTool;
    if (FILTERS.some(f => f.key === prefs.filter)) app.filter = prefs.filter;
    el("showGhosts").checked = app.showGhosts;
  }
  function savePrefs() {
    try {
      localStorage.setItem(PREFS_KEY, JSON.stringify({
        showGhosts: app.showGhosts,
        inspectorOpen: app.inspectorOpen,
        activeTool: app.activeTool,
        filter: app.filter
      }));
    } catch { /* prefs are a nicety; never block editing on them */ }
  }

  // ---------- "rendered report is behind your edits" mark ----------
  // Stores the review state's updated_at at the moment of the last successful
  // render, plus the updated_at of the last edit. A mismatch means the final
  // HTML on disk no longer matches what is in the editor.
  function renderMarkKey() { return `${RENDER_MARK_PREFIX}${state().engagement_id}:${app.activeDevice}`; }
  function readRenderMark() {
    try { return JSON.parse(localStorage.getItem(renderMarkKey()) || "{}") || {}; } catch { return {}; }
  }
  function writeRenderMark(patch) {
    try {
      localStorage.setItem(renderMarkKey(), JSON.stringify({ ...readRenderMark(), ...patch }));
    } catch { /* non-fatal */ }
  }
  function markEdited() { writeRenderMark({ editedAt: state().updated_at }); }
  function markRendered() { writeRenderMark({ renderedAt: state().updated_at }); }
  function hasUnrenderedEdits() {
    const mark = readRenderMark();
    return !!mark.editedAt && mark.editedAt !== mark.renderedAt;
  }

  // ---------- look presets ----------
  function readPresets() {
    try {
      const parsed = JSON.parse(localStorage.getItem(PRESETS_KEY) || "[]");
      return Array.isArray(parsed) ? parsed.filter(p => p && p.name) : [];
    } catch { return []; }
  }
  function writePresets(list) {
    try { localStorage.setItem(PRESETS_KEY, JSON.stringify(list)); }
    catch (error) { showError(`Could not save presets: ${error?.message || error}`); }
    renderPresets();
  }
  // A "look" is everything the style controls own for one finding. Presets are
  // stored per-browser, not per-engagement, so a house style carries between
  // audits. They apply to the finding you are on — never in bulk.
  function currentLook(finding) {
    const marker = markerFor(finding);
    if (!marker) return null;
    const around = findEffect(finding, isAroundBlur)?.effect;
    return {
      style: markerStyle(marker),
      color: markerColor(marker, finding),
      glow_opacity: clamp(marker.glow_opacity ?? 0.65, 0.1, 0.95),
      spotlight_opacity: clamp(findEffect(finding, isSpotlightDim)?.effect?.opacity ?? 0.35, 0.1, 0.85),
      around_blur: !!around,
      blur_radius: clamp(around?.radius_px ?? 10, 2, 18)
    };
  }
  function saveCurrentLook() {
    const finding = activeFinding();
    const look = finding ? currentLook(finding) : null;
    if (!look) { flashStatus("Place the highlight box first"); return; }
    const name = String(window.prompt("Name this look", `Look ${readPresets().length + 1}`) || "").trim();
    if (!name) return;
    const list = readPresets().filter(p => p.name !== name);
    list.push({ name, ...look });
    writePresets(list);
    el("presetSelect").value = name;
    renderPresets();
    flashStatus(`Saved look “${name}”`);
  }
  function applyPreset(name) {
    const preset = readPresets().find(p => p.name === name);
    const finding = activeFinding();
    if (!preset || !finding) return;
    const marker = markerFor(finding);
    if (!marker || !markerBox(marker)) { flashStatus("Place the highlight box first"); return; }
    mutate(() => {
      const hex = normalizeHex(preset.color);
      if (hex) { marker.stroke = hex; finding.callout_color = hex; }
      marker.highlight_style = preset.style || "outline";
      marker.spotlight_visible = preset.style === "spotlight";
      delete marker.glow_opacity;
      if (preset.style === "glow") marker.glow_opacity = clamp(preset.glow_opacity ?? 0.65, 0.1, 0.95);
      removeEffect(finding, isSpotlightDim);
      if (preset.style === "spotlight") {
        slideEditFor(marker.slide_id).effects.push({
          type: "dim",
          f_ref: finding.f_ref,
          opacity: clamp(preset.spotlight_opacity ?? 0.35, 0.1, 0.85)
        });
      }
      removeEffect(finding, isAroundBlur);
      if (preset.around_blur) {
        const box = markerBox(marker);
        slideEditFor(marker.slide_id).effects.push({
          type: "blur",
          f_ref: finding.f_ref,
          mode: "outside",
          rect: { x_pct: box.x, y_pct: box.y, w_pct: box.w, h_pct: box.h },
          radius_px: clamp(preset.blur_radius ?? 10, 2, 18)
        });
      }
      touchFinding(finding);
    });
    flashStatus(`Applied “${name}”`);
  }
  function deleteSelectedPreset() {
    const name = el("presetSelect").value;
    if (!name) return;
    if (!window.confirm(`Delete the look “${name}”?`)) return;
    writePresets(readPresets().filter(p => p.name !== name));
    el("presetSelect").value = "";
    renderPresets();
  }
  function renderPresets() {
    const select = el("presetSelect");
    const keep = select.value;
    const presets = readPresets();
    select.innerHTML = `<option value="">${presets.length ? "Apply a look…" : "Presets…"}</option>`;
    presets.forEach(p => {
      const option = document.createElement("option");
      option.value = p.name;
      option.textContent = p.name;
      select.appendChild(option);
    });
    select.value = presets.some(p => p.name === keep) ? keep : "";
    el("deletePreset").hidden = !select.value;
  }

  // ---------- severity ----------
  function setSeverity(value) {
    const finding = activeFinding();
    if (!finding) return;
    const next = SEVERITIES.includes(value) ? value : null;
    mutate(() => {
      const before = activeSeverity(finding);
      const aiSeverity = String(finding.severity || "").toLowerCase();
      // Storing null when it matches the AI keeps the review state honest
      // about what a human actually changed.
      finding.severity_override = next && next !== aiSeverity ? next : null;
      const after = activeSeverity(finding);
      const marker = markerFor(finding);
      if (marker) {
        marker.severity = after;
        // Only re-color when the stroke is still the automatic color for the
        // OLD severity — a hand-picked color is the operator's, keep it.
        const autoBefore = SEVERITY_COLORS[before];
        const current = normalizeHex(marker.stroke);
        if (!current || (autoBefore && current.toLowerCase() === autoBefore.toLowerCase())) {
          const autoAfter = SEVERITY_COLORS[after];
          if (autoAfter) { marker.stroke = autoAfter; finding.callout_color = autoAfter; }
        }
      }
      touchFinding(finding);
    });
  }

  // ---------- bulk actions ----------
  function approveAllShown() {
    const listed = filteredFindings();
    const open = listed.filter(f => f.status !== "approved" && f.status !== "hidden");
    const ready = open.filter(f => !needsPlacement(f));
    const unplaced = open.length - ready.length;
    if (!ready.length) {
      flashStatus(unplaced
        ? `Nothing to approve — ${unplaced} still need placing`
        : "Nothing to approve here");
      return;
    }
    // An unplaced finding has no hotspot, so approving it would ship a blank
    // frame to the client. Never sweep those up in a bulk action.
    const warning = unplaced
      ? `\n\n${unplaced} unplaced finding${unplaced === 1 ? "" : "s"} will be SKIPPED — they have no hotspot yet.`
      : "";
    if (!window.confirm(`Approve ${ready.length} finding${ready.length === 1 ? "" : "s"}?${warning}`)) return;
    mutate(() => {
      ready.forEach(f => {
        f.status = "approved";
        f.review_selected = false;
        f.reviewed_at = nowIso();
      });
    });
    flashStatus(`Approved ${ready.length}${unplaced ? `, skipped ${unplaced} unplaced` : ""}`);
  }

  // ---------- revert ----------
  function revertField(field) {
    const finding = activeFinding();
    if (!finding) return;
    mutate(() => {
      finding[field.override] = null;
      touchFinding(finding);
    });
    rebuildInspector();
  }
  function revertFinding() {
    const finding = activeFinding();
    if (!finding) return;
    if (!window.confirm(
      `Discard your edits to ${shortRef(finding)}?\n\nText, severity, colour, style, blur and hotspot all go back to the AI's original.`
    )) return;
    mutate(() => {
      TEXT_FIELDS.forEach(field => { finding[field.override] = null; });
      finding.finding_body_override = null;
      finding.severity_override = null;
      finding.callout_visible = true;
      finding.callout_color = severityColor(finding);
      finding.callout_position = null;
      finding.callout_position_source = null;
      // Restore the untouched AI twin the generator stored alongside every
      // marker ("{marker_id}-ai"); the renderer ignores -ai markers, so it
      // is a pristine copy of what the AI proposed.
      const twin = (state().markers || []).find(m => m.marker_id === finding.ai_suggested_marker_id);
      const marker = markerFor(finding);
      if (twin && marker) {
        const keepId = marker.marker_id;
        Object.keys(marker).forEach(key => { delete marker[key]; });
        Object.assign(marker, clone(twin));
        marker.marker_id = keepId;
        finding.callout_slide_id = marker.slide_id;
        finding.hotspot_confidence = markerBox(marker) ? "exact-selector" : "needs-manual-marker";
      }
      // Drop every effect this finding owns (blur regions, spotlight dim).
      (state().slide_edits || []).forEach(slideEdit => {
        slideEdit.effects = (slideEdit.effects || []).filter(e => e?.f_ref !== finding.f_ref);
      });
      app.selectedEffect = null;
      finding.status = "needs_review";
    });
    rebuildInspector();
    flashStatus(`Reverted ${shortRef(finding)} to the AI original`);
  }

  // ---------- inspector (finding text panel) ----------
  // Rebuilds ONLY when the active finding changes. Rebuilding on every
  // keystroke is what destroyed textarea focus mid-typing in v1.0.1 — the
  // model updates live, the DOM does not.
  let textSnap = null;
  let textSaveTimer = null;
  function textBegin() { if (!textSnap) textSnap = snapshot(); }
  function textCommit(finding) {
    clearTimeout(textSaveTimer);
    if (textSnap) { pushUndo(textSnap); textSnap = null; }
    if (finding) touchFinding(finding);
    saveLocal({ quiet: true });
    render();
  }
  function rebuildInspector() {
    el("inspectorBody").dataset.key = "";
    renderInspector();
  }
  function setTextOverride(finding, field, text) {
    const original = String(field.original(finding) ?? "").trim();
    const value = String(text ?? "").trim();
    finding[field.override] = (!value || value === original) ? null : value;
  }
  function fieldIsEdited(finding, field) {
    return !!finding[field.override];
  }

  function renderInspector() {
    const panel = el("inspector");
    panel.hidden = !app.inspectorOpen;
    el("toggleInspector").classList.toggle("is-active", app.inspectorOpen);
    if (!app.inspectorOpen) return;
    const finding = activeFinding();
    const body = el("inspectorBody");
    el("inspectorRef").textContent = finding ? shortRef(finding) : "";
    const key = finding ? `${app.activeDevice}::${finding.f_ref}` : "::none";
    if (body.dataset.key === key) { refreshInspector(finding); return; }
    body.dataset.key = key;
    body.innerHTML = "";
    if (!finding) {
      body.innerHTML = `<div class="inspector-empty">Pick a finding to edit its text.</div>`;
      return;
    }
    buildInspector(body, finding);
  }

  function buildInspector(body, finding) {
    // Severity — the one control that changes how the report FILES the
    // finding, not just how it looks.
    const sevField = document.createElement("div");
    sevField.className = "field";
    sevField.innerHTML =
      `<div class="field-head"><span class="field-label">Severity</span>` +
      `<span class="field-edited" data-role="sev-edited"${finding.severity_override ? "" : " hidden"}>edited</span></div>` +
      `<select data-role="severity">` +
      SEVERITIES.map(s => `<option value="${s}">${s[0].toUpperCase()}${s.slice(1)}</option>`).join("") +
      `</select>` +
      `<p class="field-hint">Drives the report's priority chip, colour and ordering — not just this hotspot.</p>`;
    const select = sevField.querySelector("[data-role=severity]");
    select.value = activeSeverity(finding) || "medium";
    select.addEventListener("change", evt => setSeverity(evt.target.value));
    body.appendChild(sevField);

    TEXT_FIELDS.forEach(field => {
      const original = String(field.original(finding) ?? "");
      const wrap = document.createElement("div");
      wrap.className = "field" + (fieldIsEdited(finding, field) ? " is-edited" : "");
      wrap.dataset.override = field.override;
      wrap.innerHTML =
        `<div class="field-head">` +
        `<span class="field-label">${esc(field.label)}</span>` +
        `<span class="field-edited" data-role="edited"${fieldIsEdited(finding, field) ? "" : " hidden"}>edited</span>` +
        `<button class="field-revert" data-role="revert" type="button"${fieldIsEdited(finding, field) ? "" : " disabled"}>Revert</button>` +
        `</div>` +
        `<textarea rows="${field.rows}" spellcheck="true"></textarea>` +
        (field.hint ? `<p class="field-hint">${esc(field.hint)}</p>` : "") +
        (original
          ? `<details class="field-original"><summary>AI original</summary><div class="original-text">${esc(original)}</div></details>`
          : `<p class="field-hint">No AI original — this field was empty.</p>`);
      const textarea = wrap.querySelector("textarea");
      textarea.value = finding[field.override] ?? original;
      textarea.addEventListener("input", () => {
        textBegin();
        setTextOverride(finding, field, textarea.value);
        const edited = fieldIsEdited(finding, field);
        wrap.classList.toggle("is-edited", edited);
        wrap.querySelector("[data-role=edited]").hidden = !edited;
        wrap.querySelector("[data-role=revert]").disabled = !edited;
        // Debounced background save; deliberately no re-render (focus).
        clearTimeout(textSaveTimer);
        textSaveTimer = setTimeout(() => saveLocal({ quiet: true }), 600);
      });
      textarea.addEventListener("blur", () => textCommit(finding));
      textarea.addEventListener("keydown", evt => {
        if (evt.key === "Escape") { textarea.blur(); }
        evt.stopPropagation();
      });
      wrap.querySelector("[data-role=revert]").addEventListener("click", () => revertField(field));
      body.appendChild(wrap);
    });

    // Callout geometry + visibility, mirrored from the control bar so
    // everything about the callout lives in one place.
    const pos = finding.callout_position || {};
    const calloutField = document.createElement("div");
    calloutField.className = "field";
    calloutField.innerHTML =
      `<div class="field-head"><span class="field-label">Callout width</span></div>` +
      `<div class="field-range">` +
      `<input type="range" data-role="callout-width" min="12" max="60" value="${clamp(pos.w_pct ?? 22, 12, 60)}">` +
      `<output data-role="callout-width-out">${Math.round(clamp(pos.w_pct ?? 22, 12, 60))}%</output>` +
      `</div>` +
      `<p class="field-hint">How wide the callout card sits on the screenshot.</p>`;
    const width = calloutField.querySelector("[data-role=callout-width]");
    const widthOut = calloutField.querySelector("[data-role=callout-width-out]");
    let widthSnap = null;
    width.addEventListener("input", () => {
      const f = activeFinding();
      if (!f) return;
      if (!widthSnap) widthSnap = snapshot();
      const marker = markerFor(f);
      const box = marker ? markerBox(marker) : null;
      f.callout_position = { ...(f.callout_position || defaultCalloutPosition(box || { x: 40, y: 40, w: 20, h: 10 })) };
      f.callout_position.w_pct = clamp(width.value, 12, 60);
      widthOut.textContent = `${Math.round(f.callout_position.w_pct)}%`;
      renderStage();
    });
    width.addEventListener("change", () => {
      const f = activeFinding();
      if (widthSnap) { pushUndo(widthSnap); widthSnap = null; }
      if (f) touchFinding(f);
      saveLocal({ quiet: true });
      render();
    });
    body.appendChild(calloutField);

    const revertAll = document.createElement("button");
    revertAll.type = "button";
    revertAll.className = "inspector-danger";
    revertAll.textContent = "Revert finding to AI original";
    revertAll.addEventListener("click", revertFinding);
    body.appendChild(revertAll);
  }

  // Value refresh that never touches a focused control.
  function refreshInspector(finding) {
    if (!finding) return;
    const body = el("inspectorBody");
    const sevSelect = body.querySelector("[data-role=severity]");
    if (sevSelect && document.activeElement !== sevSelect) {
      sevSelect.value = activeSeverity(finding) || "medium";
    }
    const sevEdited = body.querySelector("[data-role=sev-edited]");
    if (sevEdited) sevEdited.hidden = !finding.severity_override;
    TEXT_FIELDS.forEach(field => {
      const wrap = body.querySelector(`.field[data-override="${field.override}"]`);
      if (!wrap) return;
      const textarea = wrap.querySelector("textarea");
      const edited = fieldIsEdited(finding, field);
      wrap.classList.toggle("is-edited", edited);
      wrap.querySelector("[data-role=edited]").hidden = !edited;
      wrap.querySelector("[data-role=revert]").disabled = !edited;
      if (textarea && document.activeElement !== textarea) {
        textarea.value = finding[field.override] ?? String(field.original(finding) ?? "");
      }
    });
    const width = body.querySelector("[data-role=callout-width]");
    const widthOut = body.querySelector("[data-role=callout-width-out]");
    if (width && document.activeElement !== width) {
      const value = clamp(finding.callout_position?.w_pct ?? 22, 12, 60);
      width.value = String(value);
      if (widthOut) widthOut.textContent = `${Math.round(value)}%`;
    }
  }

  function toggleInspector(force) {
    app.inspectorOpen = force === undefined ? !app.inspectorOpen : !!force;
    savePrefs();
    renderInspector();
    if (app.fitZoom) { applyZoom(); renderStage(); }
  }

  // ---------- shell bindings ----------
  function bindShell() {
    stage.addEventListener("pointerdown", onStagePointerDown);
    stage.addEventListener("pointermove", onStagePointerMove);
    stage.addEventListener("pointerup", onStagePointerUp);
    stage.addEventListener("pointercancel", () => { app.drag = null; clearDrawPreview(); render(); });

    document.querySelectorAll(".tool").forEach(btn => {
      btn.addEventListener("click", () => {
        app.activeTool = btn.dataset.tool;
        savePrefs();
        renderControls();
      });
    });
    document.querySelectorAll(".style-btn").forEach(btn => {
      btn.addEventListener("click", () => applyStyle(btn.dataset.style));
    });
    document.querySelectorAll(".swatch").forEach(btn => {
      btn.addEventListener("click", () => applyColor(btn.dataset.color));
    });
    el("customColor").addEventListener("change", evt => applyColor(evt.target.value));

    // Sliders apply live on input and commit ONE undo entry per drag gesture.
    let sliderSnap = null;
    const sliderBegin = () => { if (!sliderSnap) sliderSnap = snapshot(); };
    const sliderEnd = finding => {
      if (sliderSnap) { pushUndo(sliderSnap); sliderSnap = null; }
      if (finding) touchFinding(finding);
      saveLocal({ quiet: true });
      renderControls();
    };
    el("blurStrength").addEventListener("input", evt => {
      const finding = activeFinding();
      const selected = selectedEffectObject();
      const target = (selected && String(selected.type).toLowerCase() === "blur")
        ? selected
        : (finding ? findEffect(finding, isAroundBlur)?.effect : null);
      if (!target) return;
      sliderBegin();
      target.radius_px = clamp(evt.target.value, 2, 18);
      renderStage();
    });
    el("blurStrength").addEventListener("change", () => sliderEnd(activeFinding()));
    el("styleIntensity").addEventListener("input", evt => {
      const finding = activeFinding();
      const marker = finding ? markerFor(finding) : null;
      if (!finding || !marker) return;
      sliderBegin();
      const value = clamp(evt.target.value, 10, 95) / 100;
      if (markerStyle(marker) === "glow") {
        marker.glow_opacity = value;
      } else if (markerStyle(marker) === "spotlight") {
        const found = findEffect(finding, isSpotlightDim);
        if (found) found.effect.opacity = Math.min(value, 0.85);
        else slideEditFor(marker.slide_id).effects.push({ type: "dim", f_ref: finding.f_ref, opacity: Math.min(value, 0.85) });
      }
      renderStage();
    });
    el("styleIntensity").addEventListener("change", () => sliderEnd(activeFinding()));
    el("blurAround").addEventListener("click", toggleAroundBlur);
    el("deleteRegion").addEventListener("click", deleteSelectedEffect);
    el("calloutVisible").addEventListener("change", evt => {
      const finding = activeFinding();
      if (!finding) return;
      mutate(() => {
        finding.callout_visible = evt.target.checked;
        touchFinding(finding);
      });
    });
    el("undoAction").addEventListener("click", undo);
    el("redoAction").addEventListener("click", redo);
    el("doneFinding").addEventListener("click", approveActive);
    el("hideFinding").addEventListener("click", toggleHideActive);
    el("saveState").addEventListener("click", downloadState);
    el("exportFinal").addEventListener("click", renderFinal);
    el("prevSlide").addEventListener("click", () => stepSlide(-1));
    el("nextSlide").addEventListener("click", () => stepSlide(1));
    el("fitStage").addEventListener("click", () => { app.fitZoom = true; applyZoom(); renderStage(); });
    el("zoomInput").addEventListener("input", evt => {
      app.fitZoom = false;
      app.zoom = clamp(evt.target.value, 25, 200) / 100;
      applyZoom();
      renderStage();
    });
    el("showGhosts").addEventListener("change", evt => {
      app.showGhosts = evt.target.checked;
      savePrefs();
      renderStage();
    });
    const search = el("findingSearch");
    search.addEventListener("input", evt => {
      app.search = String(evt.target.value || "").trim();
      renderFindingList();
    });
    search.addEventListener("keydown", evt => {
      if (evt.key === "Escape") {
        search.value = "";
        app.search = "";
        renderFindingList();
        search.blur();
      }
      if (evt.key === "Enter") {
        evt.preventDefault();
        const first = filteredFindings()[0];
        if (first) { search.blur(); activateFinding(first.f_ref); }
      }
      evt.stopPropagation();
    });
    el("approveAll").addEventListener("click", approveAllShown);
    el("toggleInspector").addEventListener("click", () => toggleInspector());
    el("closeInspector").addEventListener("click", () => toggleInspector(false));
    el("presetSelect").addEventListener("change", evt => {
      el("deletePreset").hidden = !evt.target.value;
      if (evt.target.value) applyPreset(evt.target.value);
    });
    el("savePreset").addEventListener("click", saveCurrentLook);
    el("deletePreset").addEventListener("click", deleteSelectedPreset);
    el("helpButton").addEventListener("click", () => { el("helpModal").hidden = false; });
    el("closeHelpModal").addEventListener("click", () => { el("helpModal").hidden = true; });
    el("closeRenderModal").addEventListener("click", () => { el("renderModal").hidden = true; });
    [el("helpModal"), el("renderModal")].forEach(modal => {
      modal.addEventListener("click", evt => { if (evt.target === modal) modal.hidden = true; });
    });
    document.querySelectorAll("#renderModal [data-copy]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const text = el(btn.dataset.copy).textContent;
        try {
          await navigator.clipboard.writeText(text);
          btn.textContent = "Copied!";
        } catch {
          const ta = document.createElement("textarea");
          ta.value = text;
          document.body.appendChild(ta);
          ta.select();
          document.execCommand("copy");
          ta.remove();
          btn.textContent = "Copied!";
        }
        setTimeout(() => { btn.textContent = "Copy"; }, 1600);
      });
    });
    stageWrap.addEventListener("wheel", evt => {
      if (!evt.ctrlKey) return;
      evt.preventDefault();
      app.fitZoom = false;
      app.zoom = clamp(app.zoom * (evt.deltaY < 0 ? 1.1 : 0.9), 0.25, 2);
      el("zoomInput").value = String(Math.round(app.zoom * 100));
      applyZoom();
      renderStage();
    }, { passive: false });
    window.addEventListener("resize", () => { if (app.fitZoom) { applyZoom(); renderStage(); } });
    window.addEventListener("keydown", onKeyDown);
  }

  function stepSlide(delta) {
    const slides = state().slides || [];
    if (!slides.length) return;
    app.activeSlide = (app.activeSlide + delta + slides.length) % slides.length;
    app.selectedEffect = null;
    renderSlideStrip();
    renderStage();
  }
  function stepFinding(delta) {
    const queue = filteredFindings();
    if (!queue.length) return;
    const idx = queue.findIndex(f => f.f_ref === app.activeFindingRef);
    const next = queue[(idx + delta + queue.length) % queue.length];
    if (next) activateFinding(next.f_ref);
  }

  function onKeyDown(evt) {
    if (evt.target.closest?.("[contenteditable], input, textarea, select")) return;
    const mod = evt.ctrlKey || evt.metaKey;
    if (mod && evt.key.toLowerCase() === "z" && !evt.shiftKey) { evt.preventDefault(); undo(); return; }
    if (mod && (evt.key.toLowerCase() === "y" || (evt.key.toLowerCase() === "z" && evt.shiftKey))) {
      evt.preventDefault(); redo(); return;
    }
    if (mod && evt.key.toLowerCase() === "s") { evt.preventDefault(); downloadState(); return; }
    if (mod) return;
    // Shift+arrows nudge the highlight box, Alt+arrows resize it.
    if ((evt.shiftKey || evt.altKey) && evt.key.startsWith("Arrow")) {
      const step = 0.5;
      const dx = evt.key === "ArrowLeft" ? -step : evt.key === "ArrowRight" ? step : 0;
      const dy = evt.key === "ArrowUp" ? -step : evt.key === "ArrowDown" ? step : 0;
      nudgeMarker(dx, dy, evt.altKey);
      evt.preventDefault();
      return;
    }
    switch (evt.key) {
      case "ArrowLeft": stepSlide(-1); break;
      case "ArrowRight": stepSlide(1); break;
      case "ArrowDown": evt.preventDefault(); stepFinding(1); break;
      case "ArrowUp": evt.preventDefault(); stepFinding(-1); break;
      case "?": el("helpModal").hidden = !el("helpModal").hidden; break;
      case "j": case "J": stepFinding(1); break;
      case "k": case "K": stepFinding(-1); break;
      case "f": case "F": app.fitZoom = true; applyZoom(); renderStage(); break;
      case "a": case "A": approveActive(); break;
      case "h": case "H": toggleHideActive(); break;
      case "b": case "B": app.activeTool = "blur"; savePrefs(); renderControls(); break;
      case "v": case "V": app.activeTool = "highlight"; savePrefs(); renderControls(); break;
      case "t": case "T": toggleInspector(); break;
      case "/":
        evt.preventDefault();
        el("findingSearch").focus();
        el("findingSearch").select();
        break;
      case "Delete": case "Backspace":
        if (app.selectedEffect) deleteSelectedEffect();
        else clearActivePlacement();
        break;
      case "Escape":
        if (!el("helpModal").hidden) { el("helpModal").hidden = true; }
        else if (!el("renderModal").hidden) { el("renderModal").hidden = true; }
        else if (app.drag) { app.drag = null; clearDrawPreview(); render(); }
        else if (app.selectedEffect) { app.selectedEffect = null; renderStage(); renderControls(); }
        break;
    }
  }

  function nudgeMarker(dx, dy, resize) {
    const finding = activeFinding();
    const marker = finding ? markerFor(finding) : null;
    const box = marker ? markerBox(marker) : null;
    if (!box) return;
    mutate(() => {
      if (resize) {
        box.w = clamp(box.w + dx, 0.4, 100 - box.x);
        box.h = clamp(box.h + dy, 0.4, 100 - box.y);
      } else {
        box.x = clamp(box.x + dx, 0, 100 - box.w);
        box.y = clamp(box.y + dy, 0, 100 - box.h);
      }
      setMarkerRect(marker, box);
      syncDerivedEffects(finding);
      touchFinding(finding);
    });
  }

  // ---------- boot ----------
  function init() {
    if (!app.devices.length) {
      showError("No review states found in this editor build.");
      return;
    }
    const route = editorRoute();
    app.devices.forEach(device => {
      const saved = loadSavedState(device, app.inlineStates[device]);
      if (saved) app.states[device] = saved;
    });
    app.activeDevice = route.device && app.devices.includes(route.device) ? route.device : app.devices[0];
    el("engagementLabel").textContent = `${state().engagement_id} · ${app.activeDevice}`;
    loadPrefs();
    // A pick routed in from the report always wins over a remembered filter —
    // otherwise "Open editor" can land on a tab that hides the finding.
    const incoming = applyIncomingEditorPicks(route);
    if (incoming) app.filter = "queue";
    const first = incoming || filteredFindings("queue")[0]?.f_ref || sortedFindings()[0]?.f_ref || null;
    bindShell();
    renderPresets();
    activateFinding(first);
  }

  init();
})();
