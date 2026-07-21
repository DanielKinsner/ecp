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
  function severityColor(finding) {
    return SEVERITY_COLORS[String(finding?.severity || "").toLowerCase()] || "#FACC15";
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
  function filteredFindings(filter = app.filter, s = state()) {
    const findings = sortedFindings(s);
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
  function saveLocal(options = {}) { return saveStateForDevice(app.activeDevice, state(), options); }
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
    if (filteredFindings().some(f => f.f_ref === ref)) return;
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
  async function renderFinal() {
    saveLocal({ quiet: true });
    if (!isServerBacked()) {
      downloadState();
      showError("Render needs the editor server. Run: node scripts/serve-editor.cjs --engagement <dir> — or use the downloaded JSON with generate-report.py --from-review.");
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
      const count = filteredFindings(key).length;
      const btn = document.createElement("button");
      btn.textContent = `${label} (${count})`;
      btn.className = key === app.filter ? "is-active" : "";
      btn.addEventListener("click", () => {
        app.filter = key;
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
      note.textContent = app.filter === "queue"
        ? "Queue is clear — nothing waiting on you."
        : "No findings here.";
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
    const id = `spot-${Math.random().toString(36).slice(2, 9)}`;
    layer.innerHTML =
      `<defs><mask id="${id}">` +
      `<rect x="0" y="0" width="100" height="100" fill="white"/>` +
      `<rect x="${box.x}" y="${box.y}" width="${box.w}" height="${box.h}" rx="1.2" fill="black"/>` +
      `</mask></defs>` +
      `<rect class="spotlight-dim" x="0" y="0" width="100" height="100" mask="url(#${id})"/>`;
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
    node.style.setProperty("--sw", color);
    node.style.setProperty("--glow1", hexToRgba(color, 0.65));
    node.style.setProperty("--glow2", hexToRgba(color, 0.4));
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

    const effect = selectedEffectObject();
    const regionControls = el("regionControls");
    regionControls.hidden = !effect;
    if (effect && String(effect.type).toLowerCase() === "blur") {
      el("blurStrength").value = String(clamp(effect.radius_px ?? 10, 2, 18));
      el("blurStrength").parentElement.style.display = "";
    } else if (effect) {
      el("blurStrength").parentElement.style.display = "none";
    }
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
    el("blurStrength").addEventListener("input", evt => {
      const effect = selectedEffectObject();
      if (!effect) return;
      effect.radius_px = clamp(evt.target.value, 2, 18);
      saveLocal({ quiet: true });
      renderStage();
    });
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
      renderStage();
    });
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
    switch (evt.key) {
      case "ArrowLeft": stepSlide(-1); break;
      case "ArrowRight": stepSlide(1); break;
      case "j": case "J": stepFinding(1); break;
      case "k": case "K": stepFinding(-1); break;
      case "f": case "F": app.fitZoom = true; applyZoom(); renderStage(); break;
      case "a": case "A": approveActive(); break;
      case "h": case "H": toggleHideActive(); break;
      case "b": case "B": app.activeTool = "blur"; renderControls(); break;
      case "v": case "V": app.activeTool = "highlight"; renderControls(); break;
      case "Delete": case "Backspace":
        if (app.selectedEffect) deleteSelectedEffect();
        else clearActivePlacement();
        break;
      case "Escape":
        if (app.drag) { app.drag = null; clearDrawPreview(); render(); }
        else if (app.selectedEffect) { app.selectedEffect = null; renderStage(); renderControls(); }
        break;
    }
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
    const incoming = applyIncomingEditorPicks(route);
    const first = incoming || filteredFindings("queue")[0]?.f_ref || sortedFindings()[0]?.f_ref || null;
    bindShell();
    activateFinding(first);
  }

  init();
})();
