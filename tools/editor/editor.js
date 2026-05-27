(() => {
  const CURRENT_REVIEW_STATE_VERSION = 1;
  const MAX_IMPORT_BYTES = 5 * 1024 * 1024;
  const MAX_BROWSER_FALLBACK_IMPORT_BYTES = 2 * 1024 * 1024;
  const STORAGE_PREFIX = "ecp-review-state:";
  const payload = JSON.parse(document.getElementById("ecp-review-payload").textContent);
  const migrations = {};
  const statusMeta = {
    needs_review: { label: "Needs Review", tone: "review" },
    tagged_for_ai_pass: { label: "AI Pass", tone: "ai" },
    edited: { label: "Edited", tone: "edited" },
    approved: { label: "Approved", tone: "approved" },
    hidden: { label: "Hidden", tone: "hidden" }
  };
  const statusOrder = ["needs_review", "tagged_for_ai_pass", "edited", "approved", "hidden"];
  const riskyConfidence = ["needs-manual-marker", "fallback-absence", "section-match"];
  const severityPalette = {
    critical: "#EF4444",
    high: "#F97316",
    medium: "#FACC15",
    low: "#60A5FA",
    info: "#9CA3AF"
  };
  const highlightStyles = ["outline", "glow", "fill", "spotlight", "underline"];
  const styleToggles = [
    { key: "outline", label: "Outline" },
    { key: "glow", label: "Glow" },
    { key: "fill", label: "Fill" },
    { key: "underline", label: "Underline" },
    { key: "spotlight", label: "Spotlight" }
  ];
  const CALLOUT_MIN_W_PCT = 12;
  const CALLOUT_MAX_W_PCT = 100;
  const CALLOUT_MIN_SCALE_PCT = 70;
  const CALLOUT_MAX_SCALE_PCT = 180;
  const calloutAnchors = ["auto", "left", "right", "top", "bottom"];

  const app = {
    devices: payload.devices || Object.keys(payload.states || {}),
    inlineStates: clone(payload.states || {}),
    states: clone(payload.states || {}),
    images: payload.slide_images || {},
    snapTargets: payload.snap_targets || {},
    activeDevice: null,
    activeFindingRef: null,
    activeSlide: 0,
    activeTool: "rect",
    drag: null,
    undoStack: [],
    redoStack: [],
    saveTimer: null,
    activeLayer: "marker",
    activeEffectIndex: null,
    advancedInspectorOpen: false,
    contextMenu: null,
    findingMode: "all",
    previewMode: "final",
    polyDraft: null,           // { points: [[x,y],...], cursor: {x,y} } while drawing polygon
    lassoDraft: null,          // { points: [...] } while recording lasso
    clipboard: null,           // { marker, finding } snapshot for paste
    selection: new Set(),      // additional selected f_refs (active is implicit primary)
    manualCounter: 0           // for unique manual/M-NN refs
  };

  function init() {
    const route = editorRoute();
    app.devices.forEach(device => {
      const inlineState = app.inlineStates[device];
      const saved = loadSavedState(device, inlineState);
      if (saved) app.states[device] = saved;
    });
    app.activeDevice = route.device && app.devices.includes(route.device) ? route.device : app.devices[0];
    const incomingRef = applyIncomingEditorPicks(route);
    app.activeFindingRef = incomingRef || defaultActiveFinding(state())?.f_ref || null;
    const initialMarker = markerFor(activeFinding());
    const initialSlideIndex = state().slides.findIndex(slide => slide.slide_id === initialMarker?.slide_id);
    if (initialSlideIndex >= 0) app.activeSlide = initialSlideIndex;
    bindShell();
    render();
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
        throw new Error("This review state was produced by an older editor; please contact maintainer for migration.");
      }
      reviewState = migrations[key](reviewState);
      version = reviewState.review_state_schema_version;
      console.info(`Migrated review state to v${version}`);
    }
    return reviewState;
  }

  function state() { return app.states[app.activeDevice]; }
  function storageKey(device, overrideState) {
    const s = overrideState || app.states[device];
    return `${STORAGE_PREFIX}${s.engagement_id}:${device}`;
  }
  function isServerBackedEditor() {
    return location.protocol === "http:" || location.protocol === "https:";
  }
  function editorPickKey(device, overrideState) {
    const s = overrideState || app.states[device];
    return `ecp-editor-picks:${s.engagement_id}:${device}`;
  }
  function editorRoute() {
    const params = new URLSearchParams(String(location.hash || "").replace(/^#/, ""));
    return {
      device: params.get("device") || "",
      pick: params.get("pick") || params.get("edit") || ""
    };
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
        activated ||= device === app.activeDevice ? f.f_ref : null;
      });
      saveStateForDevice(device, s, { quiet: true });
      localStorage.removeItem(editorPickKey(device, s));
    });
    if (activated) app.findingMode = "selected";
    return activated;
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
        f.short_code,
        `${f.cluster}/F-${String(f.display_index || f.raw?.display_index || "").padStart(2, "0")}`,
        `${f.cluster}/F-${String(f.raw?.cluster_index || "").padStart(2, "0")}`
      ].filter(Boolean).map(String);
      return candidates.includes(needle) || candidates.some(value => value.endsWith(`/${needle}`));
    }) || null;
  }
  function rememberUndo(label) {
    app.undoStack.push({ label, device: app.activeDevice, state: clone(state()) });
    if (app.undoStack.length > 50) app.undoStack.shift();
    app.redoStack = [];
  }
  function mutate(label, fn) {
    rememberUndo(label);
    fn();
    saveLocal();
  }
  function saveLocal(options = {}) {
    const s = state();
    return saveStateForDevice(app.activeDevice, s, options);
  }
  function saveStateForDevice(device, s, options = {}) {
    try {
      s.updated_at = new Date().toISOString();
      localStorage.setItem(storageKey(device, s), JSON.stringify(s));
      if (!options.quiet) flashStatus("Saved to browser");
      return true;
    } catch (error) {
      const quota = error?.name === "QuotaExceededError"
        ? " Browser storage is full; download the review state or use the local editor server for large imported screenshots."
        : "";
      showError(`Could not save review state.${quota} ${error?.message || error || ""}`.trim());
      return false;
    }
  }
  function sortedFindings(s) {
    const slideOrder = new Map((s.slides || []).map((slide, index) => [slide.slide_id, index]));
    const markersById = new Map((s.markers || []).map(marker => [marker.marker_id, marker]));
    return [...(s.findings || [])].sort((a, b) => {
      const ma = markersById.get(a.marker_id);
      const mb = markersById.get(b.marker_id);
      const slideA = slideOrder.get(ma?.slide_id) ?? 999;
      const slideB = slideOrder.get(mb?.slide_id) ?? 999;
      const indexA = Number(a.raw?.index ?? a.index ?? 999);
      const indexB = Number(b.raw?.index ?? b.index ?? 999);
      return slideA - slideB
        || indexA - indexB
        || String(a.f_ref).localeCompare(String(b.f_ref));
    });
  }
  function queueFindings(s = state(), mode = app.findingMode) {
    const findings = sortedFindings(s);
    if (mode === "selected") return findings.filter(f => !isHiddenFinding(f) && isPickedForEdit(f) && f.status !== "approved");
    if (mode === "place") return findings.filter(f => !isHiddenFinding(f) && f.status !== "approved" && needsMarkerPlacement(f, s));
    if (mode === "fix") return findings.filter(needsHumanPlacementFix);
    if (mode === "ok") return findings.filter(f => !isHiddenFinding(f) && isLikelyOkFinding(f));
    if (mode === "approved") return findings.filter(f => !isHiddenFinding(f) && f.status === "approved");
    if (mode === "hidden") return findings.filter(isHiddenFinding);
    return findings.filter(f => !isHiddenFinding(f));
  }
  function defaultActiveFinding(s = state()) {
    return queueFindings(s, "selected")[0] || queueFindings(s, "all")[0] || sortedFindings(s)[0];
  }
  function isPickedForEdit(f) {
    // User input is authoritative: if review_selected is explicitly set
    // (true OR false), honor it. Only fall back to the AI-suggested
    // needs_manual_edit hint when the operator has not yet expressed a
    // preference. Without this, clicking "Picked" on an AI-flagged card
    // toggled review_selected to false but the card stayed Picked because
    // needs_manual_edit kept winning — the click looked dead.
    if (f?.review_selected === true) return true;
    if (f?.review_selected === false) return false;
    return f?.needs_manual_edit === true;
  }
  function needsHumanPlacementFix(f) {
    if (!f || isHiddenFinding(f)) return false;
    if (f.status === "approved") return false;
    return riskyConfidence.includes(f.hotspot_confidence)
      || (f.lint_violations || []).length > 0
      || f.status === "tagged_for_ai_pass"
      || f.status === "edited";
  }
  function isLikelyOkFinding(f) {
    return f?.hotspot_confidence === "exact-selector"
      && !(f.lint_violations || []).length
      && !["hidden", "tagged_for_ai_pass", "edited"].includes(f.status);
  }
  function isHiddenFinding(f) { return f?.status === "hidden"; }
  function placementVerdict(f) {
    if (isHiddenFinding(f)) return { label: "Hidden", tone: "hidden" };
    if ((f.lint_violations || []).length) return { label: "Lint flag", tone: "hidden" };
    if (f.hotspot_confidence === "needs-manual-marker") return { label: "Place manually", tone: "ai" };
    if (f.hotspot_confidence === "fallback-absence") return { label: "Fallback guess", tone: "edited" };
    if (f.hotspot_confidence === "section-match") return { label: "Check placement", tone: "edited" };
    if (f.status === "edited") return { label: "Edited", tone: "edited" };
    if (f.status === "tagged_for_ai_pass") return { label: "AI pass", tone: "ai" };
    if (f.hotspot_confidence === "exact-selector") return { label: "Likely OK", tone: "approved" };
    return { label: "Review", tone: "review" };
  }
  function activeFinding() { return state().findings.find(f => f.f_ref === app.activeFindingRef); }
  function markerFor(finding) { return state().markers.find(m => m.marker_id === finding?.marker_id); }
  function isMarkerPlaced(marker) { return Boolean(marker && marker.hidden !== true); }
  function needsMarkerPlacement(f, s = state()) {
    // A finding needs manual placement when its marker is unplaced (hidden /
    // coord-less, e.g. a G4 "unplaced" absence finding) or it still carries the
    // needs-manual-marker confidence. This is the worklist the "Place" queue and
    // the stage placement hint surface.
    if (!f) return false;
    const marker = (s.markers || []).find(m => m.marker_id === f.marker_id);
    return f.hotspot_confidence === "needs-manual-marker" || !isMarkerPlaced(marker);
  }
  function slideById(slideId) {
    return state().slides.find(slide => slide.slide_id === slideId) || null;
  }
  function markerSlide(marker) {
    return slideById(marker?.slide_id);
  }
  function calloutSlideId(finding, marker = markerFor(finding)) {
    return finding?.callout_slide_id || marker?.slide_id || null;
  }
  function calloutSlide(finding, marker = markerFor(finding)) {
    return slideById(calloutSlideId(finding, marker)) || markerSlide(marker) || state().slides[app.activeSlide] || null;
  }
  function calloutIsOnSlide(finding, slideId, marker = markerFor(finding)) {
    return Boolean(finding && slideId && calloutSlideId(finding, marker) === slideId);
  }
  function originalFindingFor(finding) {
    return app.inlineStates[app.activeDevice]?.findings?.find(f => f.f_ref === finding?.f_ref) || finding;
  }
  function aiMarkerFor(finding) {
    const original = originalFindingFor(finding);
    return app.inlineStates[app.activeDevice]?.markers?.find(m => m.marker_id === original?.marker_id)
      || state().markers.find(m => m.marker_id === original?.marker_id)
      || markerFor(finding);
  }
  function slideEdit(id) {
    let edit = state().slide_edits.find(e => e.slide_id === id);
    if (!edit) {
      edit = defaultSlideEdit(id);
      state().slide_edits.push(edit);
    }
    return edit;
  }

  function bindShell() {
    document.getElementById("prevSlide").addEventListener("click", () => setActiveSlide(app.activeSlide - 1));
    document.getElementById("nextSlide").addEventListener("click", () => setActiveSlide(app.activeSlide + 1));
    document.getElementById("saveState").addEventListener("click", downloadState);
    document.getElementById("exportFinal").addEventListener("click", exportReviewStateForFinal);
    document.getElementById("doneFinding")?.addEventListener("click", completeActiveFinding);
    document.getElementById("previewToggle")?.addEventListener("click", togglePreviewMode);
    document.getElementById("previewFinding")?.addEventListener("click", previewActiveFinding);
    document.getElementById("exportFindingBundle")?.addEventListener("click", exportActiveFindingBundle);
    document.getElementById("exportFrameLayer")?.addEventListener("click", exportActiveFrameLayer);
    document.getElementById("exportCalloutLayer")?.addEventListener("click", exportActiveCalloutLayer);
    document.getElementById("fitStage")?.addEventListener("click", fitActiveSlide);
  document.getElementById("zoomInput").addEventListener("input", event => {
      const slide = state().slides[app.activeSlide];
      mutate("Scale slide", () => { slideEdit(slide.slide_id).transform.scale = Number(event.target.value) / 100; });
      renderStage();
  });
  document.getElementById("importImage").addEventListener("change", importImage);
  document.getElementById("closePreview")?.addEventListener("click", closePreviewModal);
    document.getElementById("previewModal")?.addEventListener("click", event => {
      if (event.target?.id === "previewModal") closePreviewModal();
    });
    document.getElementById("dimToggle").addEventListener("click", toggleDim);
    document.getElementById("snapMarker").addEventListener("click", snapToAiMarker);
    document.getElementById("undoAction").addEventListener("click", undoLastAction);
    document.getElementById("redoAction").addEventListener("click", redoLastAction);
    window.addEventListener("keydown", handleHotkey);
    window.addEventListener("click", closeContextMenu);
    window.addEventListener("resize", closeContextMenu);
    window.addEventListener("pointermove", pointerMove);
    window.addEventListener("pointerup", pointerUp);
    window.addEventListener("pointercancel", cancelDrag);
    document.querySelectorAll(".tool").forEach(btn => {
      btn.addEventListener("click", () => {
        setTool(btn.dataset.tool, { quiet: true });
      });
    });
  }

  function render() {
    renderTabs();
    renderReviewStats();
    renderFindings();
    renderSlideStrip();
    renderStage();
    renderInspector();
  }
  function setActiveSlide(index) {
    const next = Number(index);
    if (!Number.isFinite(next)) return;
    app.activeSlide = clamp(next, 0, Math.max(0, state().slides.length - 1));
    renderReviewStats();
    renderSlideStrip();
    renderStage();
    renderInspector();
  }
  function renderTabs() {
    const tabs = document.getElementById("deviceTabs");
    tabs.innerHTML = app.devices.map(device => `<button class="${device === app.activeDevice ? "is-active" : ""}" data-device="${device}">${device}</button>`).join("");
    tabs.querySelectorAll("button").forEach(btn => btn.addEventListener("click", () => {
      app.activeDevice = btn.dataset.device;
      app.activeSlide = 0;
      app.activeFindingRef = defaultActiveFinding(state())?.f_ref || null;
      render();
    }));
  }
  function renderReviewStats() {
    const s = state();
    const findings = s.findings || [];
    const total = findings.length || 1;
    const counts = findings.reduce((acc, f) => {
      acc[f.status] = (acc[f.status] || 0) + 1;
      return acc;
    }, {});
    const reviewed = (counts.approved || 0) + (counts.edited || 0) + (counts.hidden || 0);
    const active = activeFinding();
    const progress = Math.round((reviewed / total) * 100);
    const qa = qaSummary(s);
    const verdict = placementVerdict(active);
    document.getElementById("reviewStats").innerHTML = `
      <div class="progress-card">
        <div class="progress-head">
          <span>Review</span>
          <strong>${progress}%</strong>
        </div>
        <div class="progress-track"><span style="width:${progress}%"></span></div>
      </div>
      <div class="stat-grid">
        ${statusOrder.map(status => `<button class="stat-pill tone-${statusMeta[status].tone}" data-filter-status="${status}"><span>${counts[status] || 0}</span>${statusMeta[status].label}</button>`).join("")}
      </div>
      <div class="active-brief">
        <span>${escapeHtml(active?.f_ref || "No finding")}</span>
        <strong class="tone-${verdict.tone}">${escapeHtml(verdict.label)}</strong>
      </div>
      <div class="qa-card">
        <div class="qa-head"><span>Report Set</span><strong>${qa.score}%</strong></div>
        ${qa.items.map(item => `<button class="qa-row tone-${item.tone}" data-qa="${item.key}"><span>${item.count}</span>${item.label}</button>`).join("")}
      </div>`;
    document.querySelectorAll("[data-filter-status]").forEach(btn => btn.addEventListener("click", () => {
      const next = sortedFindings(s).find(f => f.status === btn.dataset.filterStatus);
      if (!next) return;
      app.findingMode = "all";
      app.activeFindingRef = next.f_ref;
      const marker = markerFor(next);
      const idx = s.slides.findIndex(slide => slide.slide_id === marker?.slide_id);
      if (idx >= 0) app.activeSlide = idx;
      render();
    }));
    document.querySelectorAll("[data-qa]").forEach(btn => btn.addEventListener("click", () => {
      app.findingMode = ["selected", "all", "approved", "hidden"].includes(btn.dataset.qa) ? btn.dataset.qa : "all";
      const next = qaFindings(s, btn.dataset.qa)[0];
      if (next) activateFinding(next);
      else renderFindings();
    }));
  }
  function qaSummary(s) {
    const findings = s.findings || [];
    const selected = queueFindings(s, "selected").length;
    const all = queueFindings(s, "all").length;
    const needsReview = qaFindings(s, "needs_review").length;
    const approved = queueFindings(s, "approved").length;
    const edited = qaFindings(s, "edited").length;
    const hidden = qaFindings(s, "hidden").length;
    const reviewed = approved + edited + hidden;
    return {
      score: clamp(Math.round((reviewed / Math.max(findings.length, 1)) * 100), 0, 100),
      items: [
        { key: "selected", label: "Edit Set", count: selected, tone: selected ? "review" : "approved" },
        { key: "all", label: "All Findings", count: all, tone: "edited" },
        { key: "needs_review", label: "Needs Review", count: needsReview, tone: needsReview ? "review" : "approved" },
        { key: "approved", label: "Approved", count: approved, tone: "approved" },
        { key: "edited", label: "Edited", count: edited, tone: "edited" },
        { key: "hidden", label: "Hidden", count: hidden, tone: hidden ? "hidden" : "approved" }
      ]
    };
  }
  function qaFindings(s, key) {
    const findings = s.findings || [];
    if (key === "selected") return queueFindings(s, "selected");
    if (key === "all") return queueFindings(s, "all");
    if (key === "needs_review") return findings.filter(f => !isHiddenFinding(f) && f.status === "needs_review");
    if (key === "approved") return queueFindings(s, "approved");
    if (key === "edited") return findings.filter(f => !isHiddenFinding(f) && f.status === "edited");
    if (key === "unresolved") return queueFindings(s, "fix");
    if (key === "manual") return findings.filter(f => f.hotspot_confidence === "needs-manual-marker");
    if (key === "confidence") return findings.filter(f => riskyConfidence.includes(f.hotspot_confidence));
    if (key === "lint") return findings.filter(f => (f.lint_violations || []).length);
    if (key === "hidden") return findings.filter(f => f.status === "hidden");
    if (key === "ok") return findings.filter(isLikelyOkFinding);
    return [];
  }
  function renderFindings() {
    const host = document.getElementById("findingList");
    const counts = {
      selected: queueFindings(state(), "selected").length,
      place: queueFindings(state(), "place").length,
      all: queueFindings(state(), "all").length,
      approved: queueFindings(state(), "approved").length,
      hidden: queueFindings(state(), "hidden").length
    };
    const queued = queueFindings(state());
    const groups = {};
    queued.forEach(f => {
      const group = findingReportGroup(f);
      (groups[group.key] ||= { group, findings: [] }).findings.push(f);
    });
    host.innerHTML = `
      <div class="queue-switch" aria-label="Finding queue">
        <button data-queue-mode="all" class="${app.findingMode === "all" ? "is-active" : ""}"><span>${counts.all}</span>All Findings</button>
        <button data-queue-mode="place" class="${app.findingMode === "place" ? "is-active" : ""}"><span>${counts.place}</span>Place</button>
        <button data-queue-mode="selected" class="${app.findingMode === "selected" ? "is-active" : ""}"><span>${counts.selected}</span>Edit Set</button>
        <button data-queue-mode="approved" class="${app.findingMode === "approved" ? "is-active" : ""}"><span>${counts.approved}</span>Approved</button>
        <button data-queue-mode="hidden" class="${app.findingMode === "hidden" ? "is-active" : ""}"><span>${counts.hidden}</span>Hidden</button>
      </div>
      ${app.findingMode === "selected" && !queued.length ? `<div class="queue-note">No findings are in the edit set yet. Switch to All Findings and mark Edit on the cards you want to touch.</div>` : ""}
      ${app.findingMode === "place" && !queued.length ? `<div class="queue-note">Nothing left to place — every finding has a hotspot. Absence findings and low-confidence guesses show up here until you draw a box for them.</div>` : ""}
      ${queued.length ? Object.values(groups).map(group => {
        return `
        <div class="group-label tone-${group.group.tone}">${escapeHtml(group.group.label)} (${group.findings.length})</div>
        ${group.findings.map(f => findingCardHtml(f)).join("")}`;
      }).join("") : `<div class="empty-panel">No findings in this queue.</div>`}`;
    host.querySelectorAll("[data-queue-mode]").forEach(btn => btn.addEventListener("click", () => {
      app.findingMode = btn.dataset.queueMode;
      app.activeFindingRef = queueFindings(state())[0]?.f_ref || defaultActiveFinding(state())?.f_ref || null;
      if (app.activeFindingRef) {
        const marker = markerFor(activeFinding());
        const idx = state().slides.findIndex(s => s.slide_id === marker?.slide_id);
        if (idx >= 0) app.activeSlide = idx;
      }
      app.selection.clear();
      render();
    }));
    host.querySelectorAll("[data-pick-ref]").forEach(btn => btn.addEventListener("click", event => {
      event.stopPropagation();
      toggleFindingEditPick(btn.dataset.pickRef);
    }));
    host.querySelectorAll(".finding-card").forEach(card => card.addEventListener("click", () => {
      app.activeFindingRef = card.dataset.ref;
      const marker = markerFor(activeFinding());
      const idx = state().slides.findIndex(s => s.slide_id === marker?.slide_id);
      if (idx >= 0) app.activeSlide = idx;
      render();
    }));
  }
  function findingReportGroup(f) {
    const marker = markerFor(f);
    const slide = state().slides.find(item => item.slide_id === marker?.slide_id);
    return {
      key: slide?.slide_id || f.cluster || "findings",
      label: slide?.section_label || f.cluster || "Findings",
      tone: isPickedForEdit(f) ? "review" : "edited"
    };
  }
  function findingCardHtml(f, meta = placementVerdict(f)) {
    const picked = isPickedForEdit(f);
    return `
      <article class="finding-card tone-${meta.tone} ${f.f_ref === app.activeFindingRef ? "is-active" : ""}" data-ref="${escapeAttr(f.f_ref)}">
        <button class="pick-toggle ${picked ? "is-picked" : ""}" data-pick-ref="${escapeAttr(f.f_ref)}">${picked ? "Picked" : "Edit"}</button>
        <h3>${escapeHtml(displayTitle(f))}</h3>
        <p><span>${escapeHtml(f.f_ref)}</span><span>${escapeHtml(f.hotspot_confidence || "")}</span></p>
        <div class="badges">
          <span class="badge tone-${meta.tone}">${escapeHtml(meta.label)}</span>
          <span class="badge">${escapeHtml(f.cluster || "cluster")}</span>
          ${(f.lint_violations || []).map(v => `<span class="badge warn">${escapeHtml(v)}</span>`).join("")}
        </div>
      </article>`;
  }
  function renderSlideStrip() {
    const s = state();
    const host = document.getElementById("slideStrip");
    if (!host) return;
    host.innerHTML = (s.slides || []).map((slide, index) => {
      const img = app.images[app.activeDevice]?.[slide.slide_id] || "";
      const markerCount = visibleStageMarkers(slide.slide_id).length;
      return `
        <button class="slide-thumb ${index === app.activeSlide ? "is-active" : ""}" data-slide-index="${index}">
          <img src="${img}" alt="${escapeAttr(slide.section_label || slide.slide_id)}">
          <span>${index + 1}</span>
          <strong>${markerCount}</strong>
        </button>`;
    }).join("");
    host.querySelectorAll("[data-slide-index]").forEach(btn => btn.addEventListener("click", () => setActiveSlide(btn.dataset.slideIndex)));
  }
  function renderStage() {
    const s = state();
    const slide = s.slides[app.activeSlide] || s.slides[0];
    if (!slide) return;
    const edit = slideEdit(slide.slide_id);
    const transform = edit.transform || defaultSlideEdit(slide.slide_id).transform;
    const scale = Number(transform.scale || 1);
    document.getElementById("zoomInput").value = Math.round(scale * 100);
    document.getElementById("slideLabel").textContent = `${slide.section_label || slide.slide_id} (${app.activeSlide + 1}/${s.slides.length})`;
    const img = app.images[app.activeDevice]?.[slide.slide_id] || "";
    const finding = activeFinding();
    const beforeMode = app.previewMode === "before";
    const previewBtn = document.getElementById("previewToggle");
    if (previewBtn) previewBtn.textContent = beforeMode ? "Corrected View" : "AI Draft View";
    const draftFinding = beforeMode ? originalFindingFor(finding) : finding;
    const editedMarker = markerFor(finding);
    const activeMarker = beforeMode ? aiMarkerFor(finding) : markerFor(finding);
    const stageFinding = beforeMode ? draftFinding : finding;
    const stageCalloutMarker = beforeMode ? activeMarker : editedMarker;
    const showCallout = calloutIsOnSlide(stageFinding, slide.slide_id, stageCalloutMarker);
    const markers = beforeMode ? (activeMarker && activeMarker.slide_id === slide.slide_id ? [activeMarker] : []) : visibleStageMarkers(slide.slide_id);
    const effects = beforeMode ? "" : activeEffectEntries(edit, finding).map(({ effect, index }) => effectHtml(effect, index)).join("");
    const cropStyle = beforeMode ? "" : clipPathStyle(edit.crop);
    const crop = beforeMode ? "" : cropHtml(edit.crop);
    const connectors = showCallout && activeMarker && activeMarker.slide_id === slide.slide_id
      ? connectorSvg(activeMarker, true, stageFinding)
      : "";
    let overlay = app.drag && !app.drag.handle && app.drag.mode !== "move-marker" && app.drag.mode !== "pan"
      ? previewSvg(app.drag.start, app.drag.current || app.drag.start, app.drag.mode)
      : "";
    if (app.polyDraft && app.polyDraft.points.length) {
      const pts = app.polyDraft.points.concat([[app.polyDraft.cursor.x, app.polyDraft.cursor.y]]);
      overlay += `<polyline class="preview-shape" points="${pointsAttr(pts)}" fill="rgba(250,204,21,.08)" stroke="#facc15" stroke-width=".35" stroke-dasharray="1,1"></polyline>` +
        app.polyDraft.points.map(p => `<circle class="preview-shape" cx="${p[0]}" cy="${p[1]}" r=".7" fill="#facc15"></circle>`).join("");
    }
    if (app.lassoDraft && app.lassoDraft.points.length > 1) {
      overlay += `<path class="preview-shape" d="${pathD(app.lassoDraft.points, false)}" fill="rgba(250,204,21,.06)" stroke="#facc15" stroke-width=".35" stroke-linejoin="round"></path>`;
    }
    const stage = document.getElementById("stage");
    stage.classList.toggle("is-before-preview", beforeMode);
    stage.style.setProperty("--stage-width", `${displayWidth(slide) * scale}px`);
    stage.style.transform = `translate(${Number(transform.translate_x_pct || 0)}%, ${Number(transform.translate_y_pct || 0)}%)`;
    const needsPlacement = !beforeMode && finding && !isMarkerPlaced(editedMarker);
    stage.innerHTML = `
      <div class="stage-hud">
        <span>${beforeMode ? "AI Draft View" : escapeHtml(toolLabel(app.activeTool))}</span>
        <strong>${markers.length} visible / ${queueFindings(s).length} ${escapeHtml(findingModeLabel(app.findingMode))}</strong>
      </div>
      ${needsPlacement ? `<div class="stage-place-hint">No hotspot yet — draw a <b>${escapeHtml(toolLabel(app.activeTool))}</b> on the screenshot to place <b>${escapeHtml(displayTitle(finding))}</b>.</div>` : ""}
      <img style="${cropStyle}" src="${img}" alt="${escapeAttr(slide.section_label || slide.slide_id)}">
      ${effects}${crop}
      <svg class="marker-layer" viewBox="0 0 100 100" preserveAspectRatio="none">${connectors}${markers.map(m => markerSvg(m, m.marker_id === activeMarker?.marker_id)).join("")}${overlay}</svg>
      ${showCallout ? calloutHtml(stageFinding, stageCalloutMarker) : ""}`;
    const svg = document.querySelector(".marker-layer");
    svg.addEventListener("pointerdown", pointerDown);
    svg.addEventListener("pointermove", pointerMove);
    svg.addEventListener("pointerup", pointerUp);
    svg.addEventListener("pointercancel", cancelDrag);
    svg.addEventListener("contextmenu", openStageContextMenu);
    const stageEl = document.getElementById("stage");
    stageEl.removeEventListener("contextmenu", openStageContextMenu);
    stageEl.addEventListener("contextmenu", openStageContextMenu);
    const callout = document.querySelector(".callout");
    if (callout) bindCalloutDrag(callout);
    bindCropDrag(stageEl);
    bindEffectDrag(stageEl);
  }
  function visibleStageMarkers(slideId) {
    const visibleRefs = new Set(app.selection);
    if (app.activeFindingRef && app.findingMode !== "hidden") visibleRefs.add(app.activeFindingRef);
    return state().markers.filter(marker => {
      if (marker.slide_id !== slideId || marker.marker_id.endsWith("-ai") || marker.hidden === true) return false;
      const finding = state().findings.find(f => f.marker_id === marker.marker_id || f.f_ref === marker.f_ref);
      if (!finding || isHiddenFinding(finding)) return false;
      return visibleRefs.has(finding.f_ref);
    });
  }
  function renderInspector() {
    const f = activeFinding();
    const host = document.getElementById("inspector");
    if (!f) { host.innerHTML = ""; return; }
    const previousAdvanced = host.querySelector(".advanced-inspector");
    if (previousAdvanced?.open) app.advancedInspectorOpen = true;
    const marker = markerFor(f);
    const slide = state().slides[app.activeSlide];
    const edit = slideEdit(slide.slide_id);
    const raw = f.raw || {};
    const flags = findingFlags(f);
    const verdict = placementVerdict(f);
    const calloutHome = calloutSlide(f, marker);
    const calloutHomeLabel = calloutHome
      ? `${calloutHome.section_label || calloutHome.slide_id}${calloutHome.slide_id === slide.slide_id ? "" : " (other screenshot)"}`
      : "Current screenshot";
    host.innerHTML = `
      <div class="panel-title">
        <span>Properties</span>
        <strong>${escapeHtml(f.f_ref)}</strong>
      </div>
      <div class="finding-summary">
        <div class="summary-row"><span>Placement</span><strong class="tone-${verdict.tone}">${escapeHtml(verdict.label)}</strong></div>
        <div class="summary-row"><span>Severity</span><strong class="severity-${escapeAttr(String(f.severity || "medium").toLowerCase())}">${escapeHtml(f.severity || "MEDIUM")}</strong></div>
        <div class="summary-row"><span>Cluster</span><strong>${escapeHtml(f.cluster || "")}</strong></div>
        <div class="summary-row"><span>Section</span><strong>${escapeHtml(raw.section || slide.section_label || "")}</strong></div>
        <div class="summary-row"><span>Callout</span><strong>${escapeHtml(calloutHomeLabel)}</strong></div>
        <div class="summary-row"><span>Match</span><strong>${escapeHtml(raw.match_method || f.hotspot_confidence || "")}</strong></div>
        ${flags.length ? `<div class="flag-list">${flags.map(flag => `<span class="flag-pill tone-${flag.tone}">${escapeHtml(flag.label)}</span>`).join("")}</div>` : ""}
      </div>
      <div class="workflow-row">
        <button data-workflow="done">Done</button>
        <button data-workflow="preview">Preview</button>
        <button data-workflow="bundle">Export Bundle</button>
        ${calloutIsOnSlide(f, slide.slide_id, marker) ? "" : `<button data-workflow="move-callout-here">Move Callout Here</button>`}
      </div>
      ${inspectorFocusHtml(f, marker, edit)}
      <details class="advanced-inspector" ${app.advancedInspectorOpen ? "open" : ""}>
        <summary>Full finding controls</summary>
      <div class="inspector-grid">
        <div class="field"><label>Finding title override</label><input data-field="finding_title_override" value="${escapeAttr(f.finding_title_override || "")}" placeholder="${escapeAttr(f.finding_title || "")}"></div>
        <div class="field"><label>Callout title override</label><input data-field="callout_title_override" value="${escapeAttr(f.callout_title_override || "")}" placeholder="${escapeAttr(f.callout_title || "")}"></div>
        <div class="field"><label>Callout body</label><textarea data-field="callout_body">${escapeHtml(f.callout_body || "")}</textarea></div>
        <div class="field"><label>Review notes</label><textarea data-field="review_notes">${escapeHtml(f.review_notes || "")}</textarea></div>
        <div class="field ai-pass-field"><label>AI pass note</label><textarea data-field="ai_pass_instruction">${escapeHtml(f.ai_pass_instruction || "")}</textarea></div>
      </div>
      <div class="panel-title">
        <span>Geometry</span>
        <strong>${escapeHtml(marker?.shape || "none")}</strong>
      </div>
      <div class="geometry-grid">
        ${markerControls(marker)}
        ${calloutControls(f)}
        ${cropControls(edit.crop)}
      </div>
      ${effectControls(edit, f)}
      <div class="panel-title">
        <span>Visual Style</span>
        <strong>${escapeHtml(styleSummary(marker))}</strong>
      </div>
      ${styleToggleControls(marker)}
      ${styleOpacityControls(marker)}
      <div class="swatch-row">
        ${colorSwatches("color-preset", marker?.stroke || severityColor(f.severity))}
      </div>
      <div class="panel-title">
        <span>Callout Color</span>
        <strong>${escapeHtml(calloutColor(f))}</strong>
      </div>
      <div class="swatch-row">
        ${colorSwatches("callout-color-preset", calloutColor(f))}
      </div>
      <div class="quick-row">
        <button data-quick="toggle-callout">${f.callout_visible === false ? "Show Callout" : "Hide Callout"}</button>
        <button data-quick="center-callout">Center Callout</button>
        ${calloutHomeActionHtml(f, marker)}
        <button data-quick="match-severity">Match Severity</button>
        <button data-quick="reset-crop">Reset Crop</button>
        <button data-quick="clear-effects">Clear Effects</button>
      </div>
      <div class="status-row">
        ${["approved", "edited", "hidden", "tagged_for_ai_pass", "needs_review"].map(status => `<button data-status="${status}" class="${f.status === status ? "is-active" : ""}">${status.replaceAll("_", " ")}</button>`).join("")}
        <span class="subtle">${escapeHtml(f.f_ref)} - ${escapeHtml(f.hotspot_confidence || "")}</span>
      </div>
      <div class="panel-title">
        <span>Layers</span>
        <strong>${escapeHtml(slide.section_label || slide.slide_id)}</strong>
      </div>
      <div class="layer-stack">
        ${layerRow("marker", "Marker", isMarkerPlaced(marker) ? marker.shape || "none" : "not placed", "marker", { visible: isMarkerPlaced(marker), toggle: "marker-visible", removable: marker ? "marker-clear" : null })}
        ${layerRow("callout", "Callout", f.callout_visible === false ? "hidden" : "visible", "layer-callout", { visible: f.callout_visible !== false, toggle: "callout-visible" })}
        ${layerRow("effects", "Finding Effects", `${activeEffectEntries(edit, f).length}`, "layer-effects")}
        ${activeEffectEntries(edit, f).map(({ effect, index }) => layerRow(`effect:${index}`, effect.type === "blur" ? "Blur" : (effect.rect ? "Dim Region" : "Spotlight"), effectLabel(effect), "layer-effects", { visible: effect.hidden !== true, toggle: `effect-visible:${index}`, removable: `effect-remove:${index}` })).join("")}
        ${layerRow("crop", "Crop", isFullCrop(edit.crop) ? "full" : "custom", "layer-crop")}
        ${layerRow("evidence", "Evidence Image", slide.viewport || slide.device || "", "layer-evidence")}
      </div>
      <div class="panel-title">
        <span>Evidence</span>
        <strong>${escapeHtml(raw.baton_index || "manual")}</strong>
      </div>
       <div class="evidence-box">
         <p>${escapeHtml(raw.element || "No raw element recorded.")}</p>
       </div>
       </details>`;
    const advancedInspector = host.querySelector(".advanced-inspector");
    if (advancedInspector) {
      advancedInspector.querySelector("summary")?.addEventListener("click", () => {
        app.advancedInspectorOpen = !advancedInspector.open;
      });
    }
    // Text-edit handler — debounced to fix three prior defects:
    //  (1) per-keystroke rememberUndo() filled the 50-entry undo cap in seconds,
    //  (2) per-keystroke renderFindings()+renderStage() blew away textarea focus,
    //  (3) status flipped to "edited" only for *_override fields, so callout_body
    //      / review_notes / ai_pass_instruction edits silently failed to mark the
    //      finding as touched. Now: live model update on every keystroke (no
    //      re-render), one undo entry per editing burst (snapshot taken at first
    //      keystroke), debounced localStorage save, full re-render on blur. The
    //      status flip covers all editable content fields.
    const EDITABLE_BODY_FIELDS = new Set(["callout_body", "review_notes", "ai_pass_instruction"]);
    host.querySelectorAll("[data-field]").forEach(input => {
      let preEditState = null;
      let saveTimer = null;
      let dirty = false;

      function flushQuiet() {
        // Debounced flush during typing: undo + localStorage save, no DOM rebuild.
        if (!dirty || !preEditState) return;
        app.undoStack.push({ label: "Edit finding", device: app.activeDevice, state: preEditState });
        if (app.undoStack.length > 50) app.undoStack.shift();
        app.redoStack = [];
        if (!saveLocal({ quiet: true })) return;
        flashStatus("Saved to browser");
        preEditState = null;
        dirty = false;
      }

      input.addEventListener("input", () => {
        if (!preEditState) preEditState = clone(state());
        f[input.dataset.field] = input.value || (input.dataset.field.endsWith("_override") ? null : "");
        dirty = true;
        clearTimeout(saveTimer);
        saveTimer = setTimeout(flushQuiet, 600);
      });

      input.addEventListener("blur", () => {
        clearTimeout(saveTimer);
        flushQuiet();
        // Status flip on blur: any user-touched content field marks the
        // finding as edited (not just *_override fields). Skip if the
        // operator already set an explicit terminal status.
        const field = input.dataset.field;
        if (field.endsWith("_override") || EDITABLE_BODY_FIELDS.has(field)) {
          if (f.status === "needs_review" || f.status === "approved") {
            f.status = "edited";
            saveLocal({ quiet: true });
          }
        }
        renderReviewStats();
        renderFindings();
        renderStage();
      });
    });
    host.querySelectorAll("[data-geom]").forEach(input => input.addEventListener("change", () => {
      mutate("Edit geometry", () => applyGeometryInput(input.dataset.geom, Number(input.value)));
      renderStage();
      renderInspector();
    }));
    host.querySelectorAll("[data-geom-select]").forEach(input => input.addEventListener("change", () => {
      mutate("Edit callout", () => applyGeometrySelect(input.dataset.geomSelect, input.value));
      renderStage();
      renderInspector();
    }));
    host.querySelectorAll("[data-quick]").forEach(btn => btn.addEventListener("click", () => {
      applyQuickAction(btn.dataset.quick);
    }));
    host.querySelectorAll("[data-preset]").forEach(btn => btn.addEventListener("click", () => applyVisualPreset(btn.dataset.preset)));
    host.querySelectorAll("[data-workflow]").forEach(btn => btn.addEventListener("click", () => {
      if (btn.dataset.workflow === "done") completeActiveFinding();
      if (btn.dataset.workflow === "preview") previewActiveFinding();
      if (btn.dataset.workflow === "bundle") exportActiveFindingBundle();
      if (btn.dataset.workflow === "move-callout-here") applyQuickAction("move-callout-here");
    }));
    host.querySelectorAll("[data-effect]").forEach(input => input.addEventListener("input", () => {
      mutate("Edit effect", () => applyEffectInput(input.dataset.effect, Number(input.value)));
      renderStage();
      renderInspector();
    }));
    host.querySelectorAll("[data-style-control]").forEach(input => input.addEventListener("input", () => {
      mutate("Edit highlight style", () => applyStyleInput(input.dataset.styleControl, Number(input.value)));
      renderStage();
      renderInspector();
    }));
    host.querySelectorAll("[data-layer]").forEach(btn => btn.addEventListener("click", () => selectLayer(btn.dataset.layer)));
    host.querySelectorAll("[data-layer-toggle]").forEach(btn => btn.addEventListener("click", () => toggleLayerVisibility(btn.dataset.layerToggle)));
    host.querySelectorAll("[data-layer-remove]").forEach(btn => btn.addEventListener("click", () => removeLayer(btn.dataset.layerRemove)));
    host.querySelectorAll("[data-style-preset]").forEach(btn => btn.addEventListener("click", () => applyStylePreset(btn.dataset.stylePreset)));
    host.querySelectorAll("[data-color-preset]").forEach(btn => btn.addEventListener("click", () => applySeverityColor(btn.dataset.colorPreset)));
    host.querySelectorAll("[data-callout-color-preset]").forEach(btn => btn.addEventListener("click", () => applyCalloutColor(btn.dataset.calloutColorPreset)));
    host.querySelectorAll("[data-status]").forEach(btn => btn.addEventListener("click", () => {
      if (btn.dataset.status === "tagged_for_ai_pass" && !String(f.ai_pass_instruction || "").trim()) {
        host.querySelector(".ai-pass-field")?.classList.add("field-error");
        showError("Add an AI pass note before tagging this finding.");
        return;
      }
      mutate("Change status", () => {
        f.status = btn.dataset.status;
        f.tagged_for_ai_pass = f.status === "tagged_for_ai_pass";
      });
      render();
    }));
  }

  function pointerDown(event) {
    const p = svgPoint(event);
    const handle = event.target?.dataset?.handle;
    const markerRef = event.target?.dataset?.ref;
    if (markerRef) {
      // Shift-click toggles selection (multi-select); plain click activates.
      if (event.shiftKey && markerRef !== app.activeFindingRef) {
        if (app.selection.has(markerRef)) app.selection.delete(markerRef);
        else app.selection.add(markerRef);
        render();
        return;
      }
      if (markerRef !== app.activeFindingRef) {
        app.selection.clear();
        app.activeFindingRef = markerRef;
        render();
        return;
      }
    }
    if (app.activeTool === "polygon") {
      // Click adds a vertex; double-click closes.
      app.polyDraft ||= { points: [], cursor: p };
      app.polyDraft.points.push([p.x, p.y]);
      app.polyDraft.cursor = p;
      if (event.detail >= 2 && app.polyDraft.points.length >= 3) commitPolygon();
      else renderStage();
      return;
    }
    if (app.activeTool === "lasso") {
      app.lassoDraft = { points: [[p.x, p.y]] };
      event.currentTarget.setPointerCapture?.(event.pointerId);
      renderStage();
      return;
    }
    const markerHit = Boolean(markerRef);
    const mode = markerHit ? "move-marker" : app.activeTool;
    app.drag = { start: p, current: p, handle, mode, originalMarker: clone(markerFor(activeFinding())), originalTransform: clone(slideEdit(state().slides[app.activeSlide].slide_id).transform) };
    if (markerHit || handle || mode === "pan") event.currentTarget.setPointerCapture?.(event.pointerId);
    if (markerHit || handle || mode === "pan") rememberUndo(mode);
  }
  function pointerMove(event) {
    if (app.polyDraft) {
      app.polyDraft.cursor = svgPoint(event);
      renderStage();
      return;
    }
    if (app.lassoDraft) {
      const p = svgPoint(event);
      const last = app.lassoDraft.points[app.lassoDraft.points.length - 1];
      // Throttle to ~1.2% movement so we don't record 500 points per stroke.
      if (Math.hypot(p.x - last[0], p.y - last[1]) > 1.2) app.lassoDraft.points.push([p.x, p.y]);
      renderStage();
      return;
    }
    if (!app.drag) return;
    app.drag.current = svgPoint(event);
    if (app.drag.mode === "move-marker" || app.drag.handle) {
      updateDraggedMarker();
      renderStage();
    } else if (app.drag.mode === "pan") {
      updatePan();
      renderStage();
    } else {
      renderStage();
    }
  }
  function pointerUp(event) {
    if (app.lassoDraft) {
      commitLasso();
      return;
    }
    if (!app.drag) return;
    const drag = app.drag;
    const end = svgPoint(event);
    const start = drag.start;
    app.drag = null;
    const rect = normalizeRect(start, end);
    mutate(`Draw ${drag.mode}`, () => {
      if (drag.mode === "move-marker" || drag.handle || drag.mode === "pan") return;
      if (drag.mode === "point") setMarker({ shape: "point", cx_pct: end.x, cy_pct: end.y, source: "manual" });
      if (drag.mode === "blur") addFindingEffect({ type: "blur", rect, mode: "outside", strength_pct: 36, radius_px: 10, feather_pct: 18 });
      if (drag.mode === "dim") addFindingEffect({ type: "dim", rect, opacity: 0.38 });
      if (drag.mode === "crop") slideEdit(state().slides[app.activeSlide].slide_id).crop = rect;
      if (drag.mode === "rect") setMarker({ shape: "rect", x_pct: rect.x_pct, y_pct: rect.y_pct, w_pct: rect.w_pct, h_pct: rect.h_pct, source: "manual" });
      if (drag.mode === "ellipse") setMarker({ shape: "ellipse", cx_pct: rect.x_pct + rect.w_pct / 2, cy_pct: rect.y_pct + rect.h_pct / 2, rx_pct: rect.w_pct / 2, ry_pct: rect.h_pct / 2, source: "manual" });
    });
    if (drag.mode === "move-marker" || drag.handle || drag.mode === "pan") saveLocal();
    render();
  }
  function cancelDrag() { app.drag = null; app.polyDraft = null; app.lassoDraft = null; renderStage(); }
  function commitPolygon() {
    const points = app.polyDraft?.points || [];
    app.polyDraft = null;
    if (points.length < 3) { renderStage(); return; }
    mutate("Draw polygon", () => setMarker({ shape: "polygon", points, source: "manual" }));
    render();
  }
  function commitLasso() {
    const points = app.lassoDraft?.points || [];
    app.lassoDraft = null;
    if (points.length < 3) { renderStage(); return; }
    mutate("Draw lasso", () => setMarker({ shape: "freeform", points, source: "manual" }));
    render();
  }

  function setMarker(fields) {
    const f = activeFinding();
    const marker = markerFor(f);
    if (!marker) return;
    const previousSlideId = marker.slide_id;
    const nextSlideId = state().slides[app.activeSlide].slide_id;
    Object.keys(marker).forEach(key => {
      if (["cx_pct", "cy_pct", "x_pct", "y_pct", "w_pct", "h_pct", "rx_pct", "ry_pct", "points"].includes(key)) delete marker[key];
    });
    const preservedStroke = marker.stroke || severityColor(f?.severity);
    const preservedWidth = marker.stroke_width || 3;
    Object.assign(marker, fields, {
      slide_id: nextSlideId,
      stroke: preservedStroke,
      stroke_width: preservedWidth,
      hidden: false,
    });
    // A deliberate hand-placement is the highest-trust placement signal
    // (product.md §4.2: manual placement is a designed step). Clear any
    // risky/needs-placement confidence so the finding drains out of the
    // Place / fix queues and reads as resolved — without this, a finding the
    // operator just placed stays flagged "Place manually" forever. Mirrors
    // snapToNearestBaton, which also promotes confidence on placement.
    if (f && riskyConfidence.includes(f.hotspot_confidence)) {
      f.hotspot_confidence = "exact-selector";
    }
    if (f && (!f.callout_slide_id || f.callout_slide_id === previousSlideId)) {
      f.callout_slide_id = nextSlideId;
    }
  }
  function updateDraggedMarker() {
    const marker = markerFor(activeFinding());
    const original = app.drag.originalMarker;
    if (!marker || !original) return;
    const dx = app.drag.current.x - app.drag.start.x;
    const dy = app.drag.current.y - app.drag.start.y;
    if (app.drag.handle) return resizeMarker(marker, original, dx, dy, app.drag.handle);
    if (marker.shape === "rect") {
      marker.x_pct = clamp((original.x_pct || 0) + dx, 0, 100 - (original.w_pct || 1));
      marker.y_pct = clamp((original.y_pct || 0) + dy, 0, 100 - (original.h_pct || 1));
    } else if ((marker.shape === "polygon" || marker.shape === "freeform") && Array.isArray(original.points)) {
      marker.points = original.points.map(p => [clamp(p[0] + dx, 0, 100), clamp(p[1] + dy, 0, 100)]);
    } else {
      marker.cx_pct = clamp((original.cx_pct || 50) + dx, 0, 100);
      marker.cy_pct = clamp((original.cy_pct || 50) + dy, 0, 100);
    }
  }
  function resizeMarker(marker, original, dx, dy, handle) {
    if (marker.shape === "rect") {
      let x = original.x_pct || 0, y = original.y_pct || 0, w = original.w_pct || 4, h = original.h_pct || 4;
      if (handle.includes("e")) w = clamp(w + dx, 1, 100 - x);
      if (handle.includes("s")) h = clamp(h + dy, 1, 100 - y);
      if (handle.includes("w")) { x = clamp(x + dx, 0, x + w - 1); w = clamp((original.x_pct || 0) + (original.w_pct || 4) - x, 1, 100 - x); }
      if (handle.includes("n")) { y = clamp(y + dy, 0, y + h - 1); h = clamp((original.y_pct || 0) + (original.h_pct || 4) - y, 1, 100 - y); }
      Object.assign(marker, { x_pct: x, y_pct: y, w_pct: w, h_pct: h });
    } else if (marker.shape === "ellipse") {
      const signX = handle.includes("w") ? -1 : 1;
      const signY = handle.includes("n") ? -1 : 1;
      marker.rx_pct = clamp((original.rx_pct || 4) + (dx * signX), 1, 50);
      marker.ry_pct = clamp((original.ry_pct || 3) + (dy * signY), 1, 50);
    }
  }
  function updatePan() {
    const slide = state().slides[app.activeSlide];
    const edit = slideEdit(slide.slide_id);
    const dx = app.drag.current.x - app.drag.start.x;
    const dy = app.drag.current.y - app.drag.start.y;
    edit.transform.translate_x_pct = clamp(Number(app.drag.originalTransform.translate_x_pct || 0) + dx / 2, -80, 80);
    edit.transform.translate_y_pct = clamp(Number(app.drag.originalTransform.translate_y_pct || 0) + dy / 2, -80, 80);
  }
  function svgPoint(event) {
    const target = event.currentTarget?.getBoundingClientRect
      ? event.currentTarget
      : document.querySelector(".marker-layer");
    const rect = target.getBoundingClientRect();
    return pointFromRect(event, rect);
  }
  function stagePoint(event) {
    const rect = document.getElementById("stage").getBoundingClientRect();
    return pointFromRect(event, rect);
  }
  function pointFromRect(event, rect) {
    return {
      x: clamp(((event.clientX - rect.left) / rect.width) * 100, 0, 100),
      y: clamp(((event.clientY - rect.top) / rect.height) * 100, 0, 100)
    };
  }
  function normalizeRect(a, b) {
    const x = Math.min(a.x, b.x), y = Math.min(a.y, b.y);
    return { x_pct: x, y_pct: y, w_pct: Math.max(0.5, Math.abs(a.x - b.x)), h_pct: Math.max(0.5, Math.abs(a.y - b.y)) };
  }
  function normalizeRectObject(rect = {}) {
    const x = clamp(Number(rect.x_pct ?? 0), 0, 99.5);
    const y = clamp(Number(rect.y_pct ?? 0), 0, 99.5);
    const w = clamp(Number(rect.w_pct ?? 0), 0.5, 100 - x);
    const h = clamp(Number(rect.h_pct ?? 0), 0.5, 100 - y);
    return { x_pct: x, y_pct: y, w_pct: w, h_pct: h };
  }
  function bindCalloutDrag(el) {
    el.addEventListener("pointerdown", event => {
      if (event.button === 2) return;
      const f = activeFinding();
      const stage = document.getElementById("stage").getBoundingClientRect();
      const start = { x: event.clientX, y: event.clientY, pos: { ...(f.callout_position || {}) } };
      const isResize = event.target?.dataset?.calloutResize === "true";
      const controller = new AbortController();
      const opts = { signal: controller.signal };
      el.setPointerCapture(event.pointerId);
      rememberUndo(isResize ? "Resize callout" : "Move callout");
      const moveCallout = move => {
        if (isResize) {
          f.callout_position = {
            ...start.pos,
            w_pct: clamp((start.pos.w_pct ?? 24) + ((move.clientX - start.x) / stage.width) * 100, CALLOUT_MIN_W_PCT, CALLOUT_MAX_W_PCT)
          };
          el.style.width = `${f.callout_position.w_pct}%`;
          return;
        }
        f.callout_position = {
          ...start.pos,
          x_pct: clamp((start.pos.x_pct ?? 60) + ((move.clientX - start.x) / stage.width) * 100, -80, 170),
          y_pct: clamp((start.pos.y_pct ?? 20) + ((move.clientY - start.y) / stage.height) * 100, -40, 140)
        };
        el.style.left = `${f.callout_position.x_pct}%`;
        el.style.top = `${f.callout_position.y_pct}%`;
      };
      const finish = () => {
        controller.abort();
        saveLocal();
        renderStage();
      };
      window.addEventListener("pointermove", moveCallout, opts);
      window.addEventListener("pointerup", finish, { ...opts, once: true });
      window.addEventListener("pointercancel", finish, { ...opts, once: true });
    });
  }
  function bindCropDrag(stageEl) {
    const crop = stageEl.querySelector(".crop-box");
    if (!crop) return;
    crop.addEventListener("pointerdown", event => {
      if (event.button === 2) return;
      event.preventDefault();
      const edit = slideEdit(state().slides[app.activeSlide].slide_id);
      const handle = event.target?.dataset?.cropHandle || "move";
      const start = stagePoint(event);
      const original = { ...(edit.crop || defaultSlideEdit("").crop) };
      app.activeLayer = "crop";
      rememberUndo(handle === "move" ? "Move crop" : "Resize crop");
      const controller = new AbortController();
      const opts = { signal: controller.signal };
      const move = pointer => {
        const current = stagePoint(pointer);
        const dx = current.x - start.x;
        const dy = current.y - start.y;
        edit.crop = resizeRectByHandle(original, dx, dy, handle);
        renderStage();
      };
      const finish = () => {
        controller.abort();
        normalizeCrop(edit.crop);
        saveLocal();
        render();
      };
      window.addEventListener("pointermove", move, opts);
      window.addEventListener("pointerup", finish, { ...opts, once: true });
      window.addEventListener("pointercancel", finish, { ...opts, once: true });
    });
  }
  function bindEffectDrag(stageEl) {
    stageEl.querySelectorAll("[data-effect-index]").forEach(el => {
      el.addEventListener("pointerdown", event => {
        if (event.button === 2) return;
        const index = Number(el.dataset.effectIndex);
        const edit = slideEdit(state().slides[app.activeSlide].slide_id);
        const effect = edit.effects[index];
        if (!effect?.rect) return;
        event.preventDefault();
        const handle = event.target?.dataset?.effectHandle || "move";
        const start = stagePoint(event);
        const original = { ...effect.rect };
        app.activeLayer = `effect:${index}`;
        app.activeEffectIndex = index;
        rememberUndo(handle === "move" ? "Move effect" : "Resize effect");
        const controller = new AbortController();
        const opts = { signal: controller.signal };
        const move = pointer => {
          const current = stagePoint(pointer);
          const dx = current.x - start.x;
          const dy = current.y - start.y;
          effect.rect = resizeRectByHandle(original, dx, dy, handle);
          renderStage();
        };
        const finish = () => {
          controller.abort();
          saveLocal();
          render();
        };
        window.addEventListener("pointermove", move, opts);
        window.addEventListener("pointerup", finish, { ...opts, once: true });
        window.addEventListener("pointercancel", finish, { ...opts, once: true });
      });
    });
  }
  function resizeRectByHandle(original, dx, dy, handle) {
    let x = original.x_pct || 0;
    let y = original.y_pct || 0;
    let w = original.w_pct || 1;
    let h = original.h_pct || 1;
    if (handle === "move") {
      x = clamp(x + dx, 0, 100 - w);
      y = clamp(y + dy, 0, 100 - h);
      return { x_pct: x, y_pct: y, w_pct: w, h_pct: h };
    }
    if (handle.includes("e")) w = clamp(w + dx, 1, 100 - x);
    if (handle.includes("s")) h = clamp(h + dy, 1, 100 - y);
    if (handle.includes("w")) {
      const right = x + w;
      x = clamp(x + dx, 0, right - 1);
      w = clamp(right - x, 1, 100 - x);
    }
    if (handle.includes("n")) {
      const bottom = y + h;
      y = clamp(y + dy, 0, bottom - 1);
      h = clamp(bottom - y, 1, 100 - y);
    }
    return { x_pct: x, y_pct: y, w_pct: w, h_pct: h };
  }
  function normalizeCrop(crop) {
    crop.x_pct = clamp(Number(crop.x_pct || 0), 0, 99);
    crop.y_pct = clamp(Number(crop.y_pct || 0), 0, 99);
    crop.w_pct = clamp(Number(crop.w_pct || 1), 1, 100 - crop.x_pct);
    crop.h_pct = clamp(Number(crop.h_pct || 1), 1, 100 - crop.y_pct);
  }
  function toggleDim() {
    const f = activeFinding();
    const marker = markerFor(f);
    if (!marker) return;
    mutate("Toggle dim", () => {
      const edit = slideEdit(marker.slide_id);
      const idx = edit.effects.findIndex(e => e.type === "dim" && effectBelongsToFinding(e, f));
      if (idx >= 0) edit.effects.splice(idx, 1);
      else edit.effects.push(scopedEffect({ type: "dim", opacity: 0.45 }, f));
    });
    renderStage();
  }
  function snapToAiMarker() {
    const f = activeFinding();
    const marker = markerFor(f);
    const ai = state().markers.find(m => m.marker_id === f?.ai_suggested_marker_id);
    if (!marker || !ai) return;
    mutate("Snap marker", () => {
      const previousSlideId = marker.slide_id;
      const replacement = clone(ai);
      replacement.marker_id = marker.marker_id;
      replacement.source = "manual";
      const idx = state().markers.findIndex(m => m.marker_id === marker.marker_id);
      state().markers[idx] = replacement;
      if (!f.callout_slide_id || f.callout_slide_id === previousSlideId) f.callout_slide_id = replacement.slide_id;
    });
    render();
  }
  function undoLastAction() {
    const snapshot = app.undoStack.pop();
    if (!snapshot) return showError("Nothing to undo.");
    app.redoStack.push({ label: snapshot.label, device: app.activeDevice, state: clone(state()) });
    app.states[snapshot.device] = clone(snapshot.state);
    app.activeDevice = snapshot.device;
    saveLocal();
    render();
    flashStatus(`Undid: ${snapshot.label}`);
  }
  function redoLastAction() {
    const snapshot = app.redoStack.pop();
    if (!snapshot) return showError("Nothing to redo.");
    app.undoStack.push({ label: snapshot.label, device: app.activeDevice, state: clone(state()) });
    app.states[snapshot.device] = clone(snapshot.state);
    app.activeDevice = snapshot.device;
    saveLocal();
    render();
    flashStatus(`Redone: ${snapshot.label}`);
  }
  function handleHotkey(event) {
    const key = event.key.toLowerCase();
    const mod = event.ctrlKey || event.metaKey;
    if (mod && key === "z") {
      event.preventDefault();
      if (event.shiftKey) redoLastAction();
      else undoLastAction();
      return;
    }
    if (mod && key === "y") {
      event.preventDefault();
      redoLastAction();
      return;
    }
    if (mod && key === "s") {
      event.preventDefault();
      downloadState();
      return;
    }
    if (isTypingTarget(event.target)) return;
    if (mod && key === "c") { event.preventDefault(); copySelection(); return; }
    if (mod && key === "x") { event.preventDefault(); cutSelection(); return; }
    if (mod && key === "v") { event.preventDefault(); pasteFromClipboard(); return; }
    if (mod && key === "d") { event.preventDefault(); duplicateSelection(); return; }
    if (event.key === "Enter" && app.polyDraft && app.polyDraft.points.length >= 3) {
      event.preventDefault();
      commitPolygon();
      return;
    }
    if (event.key === "Escape") {
      event.preventDefault();
      if (document.getElementById("previewModal")?.hidden === false) { closePreviewModal(); return; }
      if (app.polyDraft || app.lassoDraft) { app.polyDraft = null; app.lassoDraft = null; renderStage(); return; }
      if (app.selection.size) { app.selection.clear(); render(); return; }
      app.drag = null;
      setTool("point");
      renderStage();
      return;
    }
    if (["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key) && (event.altKey || event.shiftKey)) {
      event.preventDefault();
      nudgeActiveVisual(event.key, event.shiftKey ? 2 : 0.5, event.altKey);
      return;
    }
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      app.activeSlide = Math.max(0, app.activeSlide - 1);
      renderStage();
      renderSlideStrip();
      renderReviewStats();
      return;
    }
    if (event.key === "ArrowRight") {
      event.preventDefault();
      app.activeSlide = Math.min(state().slides.length - 1, app.activeSlide + 1);
      renderStage();
      renderSlideStrip();
      renderReviewStats();
      return;
    }
    if (key === "j" || key === "k") {
      event.preventDefault();
      moveActiveFinding(key === "j" ? 1 : -1);
      return;
    }
    if (key === "f") {
      event.preventDefault();
      fitActiveSlide();
      return;
    }
    if (event.key === "+" || event.key === "=") {
      event.preventDefault();
      adjustScale(0.1);
      return;
    }
    if (event.key === "-" || event.key === "_") {
      event.preventDefault();
      adjustScale(-0.1);
      return;
    }
    const tools = { "1": "point", "2": "rect", "3": "ellipse", "4": "pan", "5": "crop", "6": "blur", "7": "dim" };
    if (tools[event.key]) {
      event.preventDefault();
      setTool(tools[event.key]);
      return;
    }
    if (key === "a") {
      event.preventDefault();
      setStatus("approved");
      return;
    }
    if (key === "c") {
      event.preventDefault();
      applyQuickAction("toggle-callout");
      return;
    }
    if (key === "g") {
      event.preventDefault();
      cycleStylePreset();
      return;
    }
    if (key === "s" && !mod) {
      event.preventDefault();
      snapToNearestBaton();
      return;
    }
    if (key === "m") {
      event.preventDefault();
      applyQuickAction("match-severity");
      return;
    }
    if (key === "0") {
      event.preventDefault();
      applyQuickAction("center-callout");
      return;
    }
    if (event.key === "Delete" || event.key === "Backspace") {
      event.preventDefault();
      if (event.shiftKey) hideSelectedFindings();
      else clearActiveMarkerPlacement();
      return;
    }
    if (key === "h") {
      event.preventDefault();
      hideSelectedFindings();
      return;
    }
  }
  // ---------- Clipboard / duplicate / multi-select helpers ----------
  function selectedFindingRefs() {
    const refs = new Set(app.selection);
    if (app.activeFindingRef) refs.add(app.activeFindingRef);
    return [...refs];
  }
  function hideSelectedFindings() {
    const refs = selectedFindingRefs();
    if (!refs.length) return;
    const hidden = new Set(refs);
    mutate(refs.length > 1 ? "Hide selection" : "Hide finding", () => {
      state().findings.forEach(f => {
        if (hidden.has(f.f_ref)) {
          f.status = "hidden";
          f.callout_visible = false;
        }
      });
    });
    app.selection.clear();
    app.activeFindingRef = queueFindings(state())[0]?.f_ref || defaultActiveFinding(state())?.f_ref || null;
    if (app.activeFindingRef) {
      const marker = markerFor(activeFinding());
      const idx = state().slides.findIndex(slide => slide.slide_id === marker?.slide_id);
      if (idx >= 0) app.activeSlide = idx;
    }
    render();
  }
  function copySelection() {
    const refs = selectedFindingRefs();
    if (!refs.length) return;
    app.clipboard = refs.map(ref => {
      const f = state().findings.find(x => x.f_ref === ref);
      const m = markerFor(f);
      return { finding: clone(f), marker: clone(m) };
    }).filter(x => x.finding && x.marker);
    flashStatus(`Copied ${app.clipboard.length} marker${app.clipboard.length === 1 ? "" : "s"}`);
  }
  function cutSelection() {
    copySelection();
    if (!app.clipboard?.length) return;
    const refs = new Set(app.clipboard.map(c => c.finding.f_ref));
    mutate("Cut selection", () => {
      state().findings.forEach(f => { if (refs.has(f.f_ref)) f.status = "hidden"; });
    });
    app.selection.clear();
    render();
  }
  function pasteFromClipboard(offsetPct = 4) {
    if (!app.clipboard?.length) return showError("Nothing on the clipboard.");
    const slide = state().slides[app.activeSlide];
    if (!slide) return;
    mutate("Paste markers", () => {
      app.clipboard.forEach(({ finding, marker }) => {
        const newRef = nextManualRef(finding.cluster || "manual");
        const newMarkerId = `marker-${newRef.replace(/[^a-z0-9]/gi, "-").toLowerCase()}`;
        const newMarker = { ...clone(marker), marker_id: newMarkerId, f_ref: newRef, slide_id: slide.slide_id, source: "manual" };
        offsetMarker(newMarker, offsetPct, offsetPct);
        const newFinding = clone(finding);
        newFinding.f_ref = newRef;
        newFinding.marker_id = newMarkerId;
        newFinding.ai_suggested_marker_id = newMarkerId;
        newFinding.status = "needs_review";
        newFinding.hotspot_confidence = "needs-manual-marker";
        newFinding.tagged_for_ai_pass = false;
        newFinding.lint_violations = [];
        newFinding.raw = { ...(newFinding.raw || {}), match_method: "manual" };
        state().markers.push(newMarker);
        state().findings.push(newFinding);
        app.activeFindingRef = newRef;
      });
    });
    flashStatus(`Pasted ${app.clipboard.length} marker${app.clipboard.length === 1 ? "" : "s"}`);
    render();
  }
  function duplicateSelection() {
    copySelection();
    pasteFromClipboard(4);
  }
  function offsetMarker(m, dx, dy) {
    if (m.shape === "rect") { m.x_pct = clamp((m.x_pct || 0) + dx, 0, 100); m.y_pct = clamp((m.y_pct || 0) + dy, 0, 100); }
    else if (m.shape === "ellipse") { m.cx_pct = clamp((m.cx_pct || 50) + dx, 0, 100); m.cy_pct = clamp((m.cy_pct || 50) + dy, 0, 100); }
    else if ((m.shape === "polygon" || m.shape === "freeform") && Array.isArray(m.points)) {
      m.points = m.points.map(p => [clamp(p[0] + dx, 0, 100), clamp(p[1] + dy, 0, 100)]);
    } else { m.cx_pct = clamp((m.cx_pct || 50) + dx, 0, 100); m.cy_pct = clamp((m.cy_pct || 50) + dy, 0, 100); }
  }
  function nextManualRef(clusterHint) {
    // Avoid colliding with any existing f_ref.
    const used = new Set(state().findings.map(f => f.f_ref));
    let ref;
    do { app.manualCounter += 1; ref = `${clusterHint || "manual"}/M-${String(app.manualCounter).padStart(2, "0")}`; } while (used.has(ref));
    return ref;
  }
  function snapToNearestBaton() {
    const f = activeFinding();
    const marker = markerFor(f);
    if (!marker) return showError("No marker to snap.");
    const slide = state().slides[app.activeSlide];
    const targets = (app.snapTargets?.[app.activeDevice] || {})[slide?.slide_id] || [];
    if (!targets.length) return showError("No baton targets on this slide (try a non-imported slide).");
    const c = markerCenter(marker);
    let best = null;
    let bestDist = Infinity;
    for (const t of targets) {
      const tcx = t.x_pct + t.w_pct / 2;
      const tcy = t.y_pct + t.h_pct / 2;
      const d = Math.hypot(tcx - c.x, tcy - c.y);
      if (d < bestDist) { bestDist = d; best = t; }
    }
    if (!best) return;
    mutate("Snap to baton element", () => {
      // Strip variant geometry, then assign rect from the snap target.
      ["cx_pct", "cy_pct", "rx_pct", "ry_pct", "points"].forEach(k => delete marker[k]);
      marker.shape = "rect";
      marker.x_pct = best.x_pct;
      marker.y_pct = best.y_pct;
      marker.w_pct = best.w_pct;
      marker.h_pct = best.h_pct;
      marker.source = "manual";
      marker.snapped_baton_index = best.e_index;
      f.hotspot_confidence = "exact-selector";
    });
    flashStatus(`Snapped to ${best.e_index}${best.label ? ` (${best.label})` : ""}`);
    render();
  }
  function exportActiveFrameLayer() {
    const slide = state().slides[app.activeSlide];
    const dataUrl = app.images[app.activeDevice]?.[slide?.slide_id];
    if (!slide || !dataUrl) return showError("No screenshot frame to export.");
    const filename = `${exportBaseName(slide)}-frame.${dataUrlExtension(dataUrl, "png")}`;
    downloadDataUrl(dataUrl, filename);
    flashStatus(`Downloaded ${filename} to the browser Downloads folder.`);
  }
  function imageForSlide(slide) {
    return app.images[app.activeDevice]?.[slide?.slide_id] || "";
  }
  function markerHomeSlide(finding, marker = markerFor(finding)) {
    return markerSlide(marker) || state().slides[app.activeSlide] || null;
  }
  function exportActiveCalloutLayer() {
    const finding = activeFinding();
    const marker = markerFor(finding);
    const slide = calloutSlide(finding, marker);
    if (!slide || !finding || !marker) return showError("Select a finding before exporting its callout layer.");
    const { w, h } = exportDimensions(slide);
    const svg = calloutLayerSvg(finding, marker, w, h);
    const filename = `${exportBaseName(slide, finding)}-callout-layer.svg`;
    download(new Blob([svg], { type: "image/svg+xml" }), filename);
    flashStatus(`Downloaded ${filename} to the browser Downloads folder.`);
  }
  function exportActiveFindingBundle() {
    const finding = activeFinding();
    const marker = markerFor(finding);
    const slide = markerHomeSlide(finding, marker);
    const calloutHome = calloutSlide(finding, marker) || slide;
    const dataUrl = imageForSlide(slide);
    if (!slide || !finding || !marker || !dataUrl) return showError("Select a finding with a screenshot before exporting a bundle.");
    const { w, h } = exportDimensions(slide);
    const calloutDims = exportDimensions(calloutHome);
    const base = exportBaseName(slide, finding);
    downloadDataUrl(dataUrl, `${base}-frame.${dataUrlExtension(dataUrl, "png")}`);
    download(new Blob([markerLayerSvg(marker, finding, w, h)], { type: "image/svg+xml" }), `${base}-hotspot-layer.svg`);
    download(new Blob([connectorLayerSvg(marker, finding, w, h)], { type: "image/svg+xml" }), `${base}-connector-layer.svg`);
    download(new Blob([calloutLayerSvg(finding, marker, calloutDims.w, calloutDims.h)], { type: "image/svg+xml" }), `${base}-callout-layer.svg`);
    download(new Blob([JSON.stringify(findingManifest(slide, finding, marker), null, 2)], { type: "application/json" }), `${base}-manifest.json`);
    flashStatus(`Downloaded ${base} frame and SVG layers to the browser Downloads folder.`);
  }
  function findingManifest(slide, finding, marker) {
    return {
      engagement_id: state().engagement_id,
      device: app.activeDevice,
      slide_id: slide.slide_id,
      finding_ref: finding.f_ref,
      title: displayTitle(finding),
      callout_title: displayCalloutTitle(finding),
      callout_body: finding.callout_body || "",
      severity: finding.severity,
      callout_color: calloutColor(finding),
      callout_slide_id: calloutSlideId(finding, marker),
      marker,
      callout_position: calloutPosition(finding),
      effects: activeEffectEntries(slideEdit(slide.slide_id), finding).map(({ effect }) => effect)
    };
  }
  function previewActiveFinding() {
    const finding = activeFinding();
    const marker = markerFor(finding);
    const slide = markerHomeSlide(finding, marker);
    const image = imageForSlide(slide);
    if (!slide || !finding || !marker || !image) return showError("Select a finding with a screenshot before previewing.");
    const html = focusedPreviewHtml(slide, finding, marker, image);
    const modal = document.getElementById("previewModal");
    const frame = document.getElementById("previewFrame");
    const title = document.getElementById("previewTitle");
    if (modal && frame) {
      if (title) title.textContent = displayTitle(finding);
      frame.srcdoc = html;
      modal.hidden = false;
      flashStatus("Opened focused preview in the editor.");
      return;
    }
    const url = URL.createObjectURL(new Blob([html], { type: "text/html" }));
    window.open(url, "_blank", "noopener,noreferrer");
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }
  function closePreviewModal() {
    const modal = document.getElementById("previewModal");
    const frame = document.getElementById("previewFrame");
    if (frame) frame.srcdoc = "";
    if (modal) modal.hidden = true;
  }
  function focusedPreviewHtml(slide, finding, marker, image) {
    const { w, h } = exportDimensions(slide);
    const edit = slideEdit(slide.slide_id);
    const effects = activeEffectEntries(edit, finding).map(({ effect, index }) => effectHtml(effect, index)).join("");
    const crop = cropHtml(edit.crop);
    const cropStyle = clipPathStyle(edit.crop);
    const showCallout = calloutIsOnSlide(finding, slide.slide_id, marker);
    const connector = showCallout ? connectorSvg(marker, true, finding) : "";
    return `<!doctype html><html><head><meta charset="utf-8"><title>${escapeHtml(displayTitle(finding))}</title><style>
      body{margin:0;background:#111;color:#fff;font-family:Arial,sans-serif;display:grid;place-items:center;min-height:100vh}
      .frame{position:relative;width:min(96vw,${w}px);aspect-ratio:${w}/${h};background:#191919;box-shadow:0 28px 90px rgba(0,0,0,.65);overflow:visible}
      img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}
      .marker-layer{position:absolute;inset:0;width:100%;height:100%;overflow:visible}
      .callout{position:absolute;z-index:8;background:#0d100f;color:#fff;border:2px solid #facc15;border-radius:10px;padding:calc(14px * var(--callout-scale, 1)) calc(16px * var(--callout-scale, 1));box-shadow:0 18px 40px rgba(0,0,0,.35);font-size:calc(14px * var(--callout-scale, 1));line-height:1.45}
      .callout strong{display:block;margin-bottom:8px}
      .callout p{margin:0}.callout-resize,.handle,.effect-handle,.crop-box{display:none}
      .callout::before,.callout::after{content:"";position:absolute;width:0;height:0;border-style:solid}
      .callout-arrow-left::before{top:28px;right:100%;border-width:9px 10px 9px 0;border-color:transparent currentColor transparent transparent;transform:translateY(-50%)}
      .callout-arrow-left::after{top:28px;right:calc(100% - 1px);border-width:8px 9px 8px 0;border-color:transparent #0d100f transparent transparent;transform:translateY(-50%)}
      .callout-arrow-right::before{top:28px;left:100%;border-width:9px 0 9px 10px;border-color:transparent transparent transparent currentColor;transform:translateY(-50%)}
      .callout-arrow-right::after{top:28px;left:calc(100% - 1px);border-width:8px 0 8px 9px;border-color:transparent transparent transparent #0d100f;transform:translateY(-50%)}
      .callout-arrow-top::before{left:28px;bottom:100%;border-width:0 9px 10px 9px;border-color:transparent transparent currentColor transparent;transform:translateX(-50%)}
      .callout-arrow-top::after{left:28px;bottom:calc(100% - 1px);border-width:0 8px 9px 8px;border-color:transparent transparent #0d100f transparent;transform:translateX(-50%)}
      .callout-arrow-bottom::before{left:28px;top:100%;border-width:10px 9px 0 9px;border-color:currentColor transparent transparent transparent;transform:translateX(-50%)}
      .callout-arrow-bottom::after{left:28px;top:calc(100% - 1px);border-width:9px 8px 0 8px;border-color:#0d100f transparent transparent transparent;transform:translateX(-50%)}
      .blur-box{position:absolute;z-index:2;backdrop-filter:blur(var(--blur));-webkit-backdrop-filter:blur(var(--blur));border:1px solid rgba(250,204,21,.5)}
      .blur-outside-piece{position:absolute;z-index:2;backdrop-filter:blur(var(--blur));-webkit-backdrop-filter:blur(var(--blur));background:rgba(10,10,10,.04)}
      .blur-focus-rect{position:absolute;z-index:3;border:1px solid rgba(250,204,21,.55);box-shadow:0 0 0 1px rgba(250,204,21,.18)}
      .dim-box{position:absolute;inset:0;background:#000;z-index:1;pointer-events:none}
      @keyframes markerGlowPulse{0%,100%{opacity:var(--glow-opacity,.72)}50%{opacity:calc(var(--glow-opacity,.72) * .38)}}
      .marker-glow{mix-blend-mode:screen;animation:markerGlowPulse 1.45s ease-in-out infinite;transform-box:fill-box;transform-origin:center}
      .connector-line{stroke-dasharray:1.4 1;stroke-width:.25;opacity:.75}.connector-active{opacity:1}
    </style></head><body><main class="frame"><img style="${cropStyle}" src="${image}" alt="">${effects}${crop}<svg class="marker-layer" viewBox="0 0 100 100" preserveAspectRatio="none">${connector}${markerSvg(marker, true)}</svg>${showCallout ? calloutHtml(finding, marker) : ""}</main></body></html>`;
  }
  function exportDimensions(slide) {
    const w = Number(slide.natural_width || 0) || displayWidth(slide);
    const h = Number(slide.natural_height || 0) || Math.round(w * 0.75);
    return { w, h };
  }
  function exportBaseName(slide, finding = activeFinding()) {
    return safeFilename(`${app.activeDevice}-${slide?.slide_id || "frame"}${finding?.f_ref ? `-${finding.f_ref}` : ""}`);
  }
  function downloadDataUrl(dataUrl, filename) {
    const a = document.createElement("a");
    a.href = dataUrl;
    a.download = filename;
    a.click();
  }
  function dataUrlExtension(dataUrl, fallback) {
    const match = /^data:image\/([^;,]+)/.exec(dataUrl || "");
    const ext = match?.[1]?.toLowerCase();
    if (ext === "jpeg") return "jpg";
    return ext || fallback;
  }
  function markerLayerSvg(marker, finding, w, h) {
    const stroke = marker.stroke || severityColor(finding.severity);
    return svgShell(w, h, markerShapeSvg(marker, w, h, {
      stroke,
      fill: "none",
      strokeWidth: Math.max(4, w * 0.003),
      opacity: 1
    }));
  }
  function connectorLayerSvg(marker, finding, w, h) {
    const c = markerCenter(marker);
    const pos = finding.callout_position || { x_pct: 62, y_pct: 20 };
    const stroke = calloutColor(finding);
    return svgShell(w, h, `<line x1="${pctX(c.x, w)}" y1="${pctY(c.y, h)}" x2="${pctX(pos.x_pct, w)}" y2="${pctY(pos.y_pct, h)}" stroke="${escapeXml(stroke)}" stroke-width="${Math.max(2, w * 0.0016)}" stroke-dasharray="8 8" opacity=".75"/>`);
  }
  function calloutLayerSvg(finding, marker, w, h) {
    const stroke = calloutColor(finding);
    const pos = calloutPosition(finding);
    const scale = clamp(Number(pos.scale_pct ?? 100), CALLOUT_MIN_SCALE_PCT, CALLOUT_MAX_SCALE_PCT) / 100;
    const x = pctX(pos.x_pct ?? 62, w);
    const y = pctY(pos.y_pct ?? 20, h);
    const width = Math.max(220, pctX(pos.w_pct ?? 24, w));
    const pad = 18 * scale;
    const titleLines = wrapText(displayCalloutTitle(finding), 28);
    const bodyLines = wrapText(finding.callout_body || "", 44);
    const titleLineHeight = 26 * scale;
    const bodyLineHeight = 21 * scale;
    const titleSize = 20 * scale;
    const bodySize = 16 * scale;
    const height = pad * 2 + titleLines.length * titleLineHeight + bodyLines.length * bodyLineHeight + 10 * scale;
    const title = titleLines.map((line, i) => `<text x="${x + pad}" y="${y + pad + 22 * scale + i * titleLineHeight}" font-family="Arial, sans-serif" font-size="${titleSize}" font-weight="700" fill="${escapeXml(stroke)}">${escapeXml(line)}</text>`).join("");
    const bodyY = y + pad + 30 * scale + titleLines.length * titleLineHeight;
    const body = bodyLines.map((line, i) => `<text x="${x + pad}" y="${bodyY + i * bodyLineHeight}" font-family="Arial, sans-serif" font-size="${bodySize}" fill="#f2f2f0">${escapeXml(line)}</text>`).join("");
    return svgShell(w, h, `
      <rect x="${x}" y="${y}" width="${width}" height="${height}" rx="10" fill="#0d100f" fill-opacity=".96" stroke="${escapeXml(stroke)}" stroke-width="2"/>
      ${title}${body}
    `);
  }
  function markerShapeSvg(marker, w, h, opts) {
    const stroke = escapeXml(opts.stroke || "#FACC15");
    const fill = escapeXml(opts.fill || "none");
    const sw = Number(opts.strokeWidth || 4);
    if (marker.shape === "rect") return `<rect x="${pctX(marker.x_pct || 0, w)}" y="${pctY(marker.y_pct || 0, h)}" width="${pctX(marker.w_pct || 4, w)}" height="${pctY(marker.h_pct || 4, h)}" rx="8" fill="${fill}" stroke="${stroke}" stroke-width="${sw}"/>`;
    if (marker.shape === "ellipse") return `<ellipse cx="${pctX(marker.cx_pct || 50, w)}" cy="${pctY(marker.cy_pct || 50, h)}" rx="${pctX(marker.rx_pct || 4, w)}" ry="${pctY(marker.ry_pct || 3, h)}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}"/>`;
    if (marker.shape === "polygon" && Array.isArray(marker.points)) return `<polygon points="${marker.points.map(p => `${pctX(p[0], w)},${pctY(p[1], h)}`).join(" ")}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" stroke-linejoin="round"/>`;
    if (marker.shape === "freeform" && Array.isArray(marker.points)) return `<path d="${pathD(marker.points.map(p => [pctX(p[0], w), pctY(p[1], h)]), true)}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}" stroke-linejoin="round"/>`;
    return `<circle cx="${pctX(marker.cx_pct || 50, w)}" cy="${pctY(marker.cy_pct || 50, h)}" r="${Math.max(10, w * 0.01)}" fill="${fill}" stroke="${stroke}" stroke-width="${sw}"/>`;
  }
  function svgShell(w, h, body) {
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${body}</svg>`;
  }
  function pctX(value, width) { return (Number(value || 0) / 100) * width; }
  function pctY(value, height) { return (Number(value || 0) / 100) * height; }
  function wrapText(text, maxChars) {
    const words = String(text || "").replace(/\s+/g, " ").trim().split(" ").filter(Boolean);
    const lines = [];
    let line = "";
    words.forEach(word => {
      const next = line ? `${line} ${word}` : word;
      if (next.length > maxChars && line) { lines.push(line); line = word; }
      else line = next;
    });
    if (line) lines.push(line);
    return lines.slice(0, 12);
  }
  function setTool(tool, options = {}) {
    app.activeTool = tool;
    document.querySelectorAll(".tool").forEach(btn => btn.classList.toggle("is-active", btn.dataset.tool === tool));
    const hudTool = document.querySelector(".stage-hud span");
    if (hudTool) hudTool.textContent = toolLabel(tool);
    if (!options.quiet) flashStatus(`Tool: ${toolLabel(tool)}`);
  }
  function toolLabel(tool) {
    return {
      rect: "Highlight Box",
      blur: "Blur Region",
      point: "Point Marker",
      ellipse: "Ellipse Marker",
      pan: "Pan",
      crop: "Crop",
      dim: "Dim Region",
      polygon: "Polygon",
      lasso: "Lasso"
    }[tool] || tool;
  }
  function findingModeLabel(mode) {
    return {
      all: "all findings",
      place: "to place",
      selected: "in edit set",
      approved: "approved",
      hidden: "hidden",
      fix: "needs placement fix",
      ok: "likely ok"
    }[mode] || "shown";
  }
  function adjustScale(delta) {
    const slide = state().slides[app.activeSlide];
    const edit = slideEdit(slide.slide_id);
    mutate("Scale slide", () => {
      edit.transform.scale = clamp(Number(edit.transform.scale || 1) + delta, 0.6, 2.2);
    });
    renderStage();
  }
  function fitActiveSlide() {
    const slide = state().slides[app.activeSlide];
    if (!slide) return;
    mutate("Fit slide", () => {
      const transform = slideEdit(slide.slide_id).transform;
      transform.scale = 1;
      transform.translate_x_pct = 0;
      transform.translate_y_pct = 0;
      transform.rotate_deg = 0;
    });
    renderStage();
    flashStatus("Fit slide to workspace");
  }
  function setStatus(status) {
    const f = activeFinding();
    if (!f) return;
    mutate("Change status", () => {
      f.status = status;
      f.tagged_for_ai_pass = status === "tagged_for_ai_pass";
    });
    if (!queueFindings(state()).some(item => item.f_ref === f.f_ref)) {
      app.activeFindingRef = queueFindings(state())[0]?.f_ref || defaultActiveFinding(state())?.f_ref || null;
      if (app.activeFindingRef) {
        const marker = markerFor(activeFinding());
        const idx = state().slides.findIndex(slide => slide.slide_id === marker?.slide_id);
        if (idx >= 0) app.activeSlide = idx;
      }
    }
    render();
  }
  function completeActiveFinding() {
    const f = activeFinding();
    if (!f) return;
    const currentRef = f.f_ref;
    mutate("Done with finding", () => {
      f.status = "approved";
      f.review_selected = false;
      f.tagged_for_ai_pass = false;
    });
    const next = queueFindings(state(), "selected")[0]
      || queueFindings(state(), app.findingMode).find(item => item.f_ref !== currentRef)
      || defaultActiveFinding(state());
    if (next) activateFinding(next);
    else render();
  }
  function togglePreviewMode() {
    app.previewMode = app.previewMode === "before" ? "final" : "before";
    const btn = document.getElementById("previewToggle");
    if (btn) btn.textContent = app.previewMode === "before" ? "Corrected View" : "AI Draft View";
    renderStage();
  }
  function activateFinding(finding) {
    if (!finding) return;
    app.activeFindingRef = finding.f_ref;
    const marker = markerFor(finding);
    const idx = state().slides.findIndex(slide => slide.slide_id === marker?.slide_id);
    if (idx >= 0) app.activeSlide = idx;
    render();
  }
  function toggleFindingEditPick(fRef) {
    const f = state().findings.find(item => item.f_ref === fRef);
    if (!f) return;
    mutate("Toggle edit set", () => {
      f.review_selected = !isPickedForEdit(f);
      if (f.review_selected && f.status === "approved") f.status = "needs_review";
    });
    app.activeFindingRef = f.f_ref;
    const marker = markerFor(f);
    const idx = state().slides.findIndex(slide => slide.slide_id === marker?.slide_id);
    if (idx >= 0) app.activeSlide = idx;
    render();
  }
  function moveActiveFinding(delta) {
    const findings = queueFindings(state());
    if (!findings.length) return;
    const current = findings.findIndex(f => f.f_ref === app.activeFindingRef);
    const next = findings[clamp(current + delta, 0, findings.length - 1)] || findings[0];
    activateFinding(next);
  }
  function findingFlags(f) {
    const flags = [];
    if (f.status === "needs_review") flags.push({ label: "Needs human approval", tone: "review" });
    if (f.hotspot_confidence === "needs-manual-marker") flags.push({ label: "Place marker manually", tone: "ai" });
    if (["fallback-absence", "section-match"].includes(f.hotspot_confidence)) flags.push({ label: "Check placement", tone: "edited" });
    (f.lint_violations || []).forEach(v => flags.push({ label: v, tone: "hidden" }));
    if (String(f.severity || "").toUpperCase() === "HIGH") flags.push({ label: "High severity", tone: "ai" });
    return flags;
  }
  function severityColor(severity) {
    return severityPalette[String(severity || "medium").toLowerCase()] || severityPalette.medium;
  }
  function calloutColor(f) {
    return f?.callout_color || severityColor(f?.severity);
  }
  function colorSwatches(attr, activeColor = "") {
    return Object.entries(severityPalette).map(([name, color]) => {
      const active = String(activeColor).toLowerCase() === String(color).toLowerCase() ? " is-active" : "";
      return `<button data-${attr}="${name}" class="color-swatch${active}" style="--swatch:${color}" title="${name}">${name}</button>`;
    }).join("");
  }
  function calloutHomeActionHtml(f, marker = markerFor(f)) {
    const slide = state().slides[app.activeSlide];
    if (!slide || calloutIsOnSlide(f, slide.slide_id, marker)) return "";
    return `<button data-quick="move-callout-here">Move Callout Here</button>`;
  }
  function inspectorFocusHtml(f, marker, edit) {
    const focus = app.activeLayer || "marker";
    const selectedEffect = /^effect:(\d+)$/.exec(focus);
    if (focus === "callout") {
      return `
        <section class="focus-panel">
          <div class="panel-title"><span>Callout</span><strong>text + placement</strong></div>
          <div class="inspector-grid">
            <div class="field"><label>Callout title override</label><input data-field="callout_title_override" value="${escapeAttr(f.callout_title_override || "")}" placeholder="${escapeAttr(f.callout_title || "")}"></div>
            <div class="field"><label>Callout body</label><textarea data-field="callout_body">${escapeHtml(f.callout_body || "")}</textarea></div>
          </div>
          <div class="geometry-grid">${calloutControls(f)}</div>
          <div class="panel-title"><span>Callout color</span><strong>${escapeHtml(calloutColor(f))}</strong></div>
          <div class="swatch-row">
            ${colorSwatches("callout-color-preset", calloutColor(f))}
          </div>
          <div class="quick-row">
            <button data-quick="toggle-callout">${f.callout_visible === false ? "Show Callout" : "Hide Callout"}</button>
            <button data-quick="center-callout">Center Callout</button>
            ${calloutHomeActionHtml(f, marker)}
          </div>
        </section>`;
    }
    if (selectedEffect) {
      const index = Number(selectedEffect[1]);
      const effect = edit.effects?.[index];
      return `
        <section class="focus-panel">
          <div class="panel-title"><span>Selected Effect</span><strong>${escapeHtml(effect?.type || "none")}</strong></div>
          ${effect ? effectControl(effect, index) : `<div class="empty-panel">Select a dim or blur effect layer.</div>`}
        </section>`;
    }
    if (focus === "effects") {
      return `<section class="focus-panel">${effectControls(edit, f)}</section>`;
    }
    if (focus === "crop") {
      return `
        <section class="focus-panel">
          <div class="panel-title"><span>Crop</span><strong>${isFullCrop(edit.crop) ? "full frame" : "custom"}</strong></div>
          <div class="geometry-grid">${cropControls(edit.crop)}</div>
          <div class="quick-row"><button data-quick="reset-crop">Reset Crop</button></div>
        </section>`;
    }
    return `
      <section class="focus-panel">
        <div class="panel-title"><span>Hotspot</span><strong>${escapeHtml(marker?.shape || "none")}</strong></div>
        <div class="geometry-grid">${markerControls(marker)}</div>
        <div class="preset-row">
          <button data-preset="problem-highlight">Problem Highlight</button>
          <button data-preset="soft-blur">Soft Background Blur</button>
          <button data-preset="premium-callout">Premium Callout</button>
          <button data-preset="dim-background">Dim Background</button>
          <button data-preset="clean-yellow">Clean Yellow</button>
        </div>
        ${styleToggleControls(marker)}
        ${styleOpacityControls(marker)}
        <div class="swatch-row">
          ${colorSwatches("color-preset", marker?.stroke || severityColor(f.severity))}
        </div>
        <div class="panel-title"><span>Callout color</span><strong>${escapeHtml(calloutColor(f))}</strong></div>
        <div class="swatch-row">
          ${colorSwatches("callout-color-preset", calloutColor(f))}
        </div>
      </section>`;
  }
  function markerControls(marker) {
    if (!marker || marker.hidden === true) return `<div class="field"><label>Hotspot</label><input value="No hotspot placed. Draw a Highlight Box to replace it." disabled></div>`;
    if (marker.shape === "rect") {
      return [
        numericControl("marker.x", "Marker X", marker.x_pct ?? 0, -80, 170),
        numericControl("marker.y", "Marker Y", marker.y_pct ?? 0, -40, 140),
        numericControl("marker.w", "Marker W", marker.w_pct ?? 4, 1, 100),
        numericControl("marker.h", "Marker H", marker.h_pct ?? 4, 1, 100)
      ].join("");
    }
    if (marker.shape === "ellipse") {
      return [
        numericControl("marker.cx", "Marker X", marker.cx_pct ?? 50, 0, 100),
        numericControl("marker.cy", "Marker Y", marker.cy_pct ?? 50, 0, 100),
        numericControl("marker.rx", "Marker RX", marker.rx_pct ?? 4, 1, 50),
        numericControl("marker.ry", "Marker RY", marker.ry_pct ?? 3, 1, 50)
      ].join("");
    }
    return [
      numericControl("marker.cx", "Marker X", marker.cx_pct ?? 50, 0, 100),
      numericControl("marker.cy", "Marker Y", marker.cy_pct ?? 50, 0, 100)
    ].join("");
  }
  function calloutControls(f) {
    const pos = f.callout_position || { x_pct: 62, y_pct: 20, w_pct: 24 };
    return [
      numericControl("callout.x", "Callout X", pos.x_pct ?? 62, -80, 170),
      numericControl("callout.y", "Callout Y", pos.y_pct ?? 20, -40, 140),
      numericControl("callout.w", "Callout W", pos.w_pct ?? 24, CALLOUT_MIN_W_PCT, CALLOUT_MAX_W_PCT),
      numericControl("callout.scale", "Callout Scale", pos.scale_pct ?? 100, CALLOUT_MIN_SCALE_PCT, CALLOUT_MAX_SCALE_PCT),
      selectControl("callout.anchor", "Arrow", normalizeCalloutAnchor(pos.anchor), calloutAnchors)
    ].join("");
  }
  function cropControls(crop) {
    const c = crop || { x_pct: 0, y_pct: 0, w_pct: 100, h_pct: 100 };
    return [
      numericControl("crop.x", "Crop X", c.x_pct ?? 0, 0, 99),
      numericControl("crop.y", "Crop Y", c.y_pct ?? 0, 0, 99),
      numericControl("crop.w", "Crop W", c.w_pct ?? 100, 1, 100),
      numericControl("crop.h", "Crop H", c.h_pct ?? 100, 1, 100)
    ].join("");
  }
  function activeEffectEntries(edit, finding = activeFinding()) {
    return (edit.effects || [])
      .map((effect, index) => ({ effect, index }))
      .filter(({ effect }) => effectBelongsToFinding(effect, finding));
  }
  function effectBelongsToFinding(effect, finding) {
    return Boolean(effect?.f_ref && finding?.f_ref && effect.f_ref === finding.f_ref);
  }
  function scopedEffect(effect, finding = activeFinding()) {
    return { ...effect, f_ref: finding?.f_ref || app.activeFindingRef };
  }
  function addFindingEffect(effect) {
    const f = activeFinding();
    const slide = state().slides[app.activeSlide];
    if (!f || !slide) return;
    slideEdit(slide.slide_id).effects.push(scopedEffect(effect, f));
  }
  function removeEffectsForFinding(edit, finding = activeFinding()) {
    edit.effects = (edit.effects || []).filter(effect => !effectBelongsToFinding(effect, finding));
  }
  function clearActiveFindingEffects() {
    const f = activeFinding();
    const slide = state().slides[app.activeSlide];
    if (!f || !slide) return;
    removeEffectsForFinding(slideEdit(slide.slide_id), f);
  }
  function blurStrength(effect) {
    if (Number.isFinite(Number(effect.strength_pct))) return clamp(Number(effect.strength_pct), 0, 100);
    return clamp(Math.round((Number(effect.radius_px ?? 8) / 28) * 100), 0, 100);
  }
  function strengthToBlurPx(strength) {
    return Math.round((clamp(Number(strength || 0), 0, 100) / 100) * 28);
  }
  function effectControls(edit, finding) {
    const entries = activeEffectEntries(edit, finding);
    if (!entries.length) return `
      <div class="panel-title"><span>Finding Effects</span><strong>blank slate</strong></div>
      <div class="empty-panel">This finding has no blur or dim edits yet. Draw a Blur region or click Dim to add one only to this finding.</div>`;
    return `
      <div class="panel-title"><span>Finding Effects</span><strong>${entries.length}</strong></div>
      <div class="effect-stack">
        ${entries.map(({ effect, index }) => effectControl(effect, index)).join("")}
      </div>`;
  }
  function effectControl(effect, index) {
    if (effect.type === "dim") {
      const opacity = Number(effect.opacity ?? 0.45);
      const label = effect.rect ? "Dim region" : "Dim / spotlight";
      return `
        <div class="effect-card">
          <div class="effect-head"><span>${label}</span><button data-layer="effect:${index}">Select</button></div>
          ${rangeControl(`effect:${index}:opacity`, "Amount", opacity, 0, 0.9, 0.05)}
        </div>`;
    }
    if (effect.type === "blur") {
      return `
        <div class="effect-card">
          <div class="effect-head"><span>Blur region</span><button data-layer="effect:${index}">Select</button></div>
          ${rangeControl(`effect:${index}:strength`, "Blur Amount", blurStrength(effect), 0, 100, 1, "%")}
          ${rangeControl(`effect:${index}:feather`, "Edge Roll-off", Number(effect.feather_pct ?? 18), 0, 45, 1, "%")}
        </div>`;
    }
    return "";
  }
  function styleOpacityControls(marker) {
    if (!marker) return "";
    const controls = [
      styleRangeControl("stroke_width", "Outline Width", markerStrokeWidth(marker) * 10, 1, 12, 1, "px"),
      styleRangeControl("fill_opacity", "Fill Opacity", Math.round(markerFillOpacity(marker) * 100), 0, 80, 1, "%"),
      styleRangeControl("glow_opacity", "Glow Opacity", Math.round(markerGlowOpacity(marker) * 100), 0, 100, 1, "%")
    ];
    return `<div class="style-opacity-panel">${controls.join("")}</div>`;
  }
  function styleToggleControls(marker) {
    return `<div class="style-grid">${styleToggles.map(({ key, label }) => {
      const active = markerStyleEnabled(marker, key);
      return `<button data-style-preset="${key}" class="${active ? "is-active" : ""}">${label}</button>`;
    }).join("")}</div>`;
  }
  function styleSummary(marker) {
    if (!marker) return "none";
    const active = styleToggles.filter(({ key }) => markerStyleEnabled(marker, key)).map(({ label }) => label);
    return active.length ? active.join(" + ") : "none";
  }
  function rangeControl(name, label, value, min, max, step, suffix = "") {
    return `<div class="field range-field"><label>${label}<strong>${round1(value)}${suffix}</strong></label><input data-effect="${name}" type="range" min="${min}" max="${max}" step="${step}" value="${round1(value)}"></div>`;
  }
  function styleRangeControl(name, label, value, min, max, step, suffix = "") {
    return `<div class="field range-field"><label>${label}<strong>${round1(value)}${suffix}</strong></label><input data-style-control="${name}" type="range" min="${min}" max="${max}" step="${step}" value="${round1(value)}"></div>`;
  }
  function layerRow(id, label, meta, dot, opts = {}) {
    const active = app.activeLayer === id;
    const eye = opts.toggle ? `<button class="layer-eye ${opts.visible === false ? "is-off" : ""}" data-layer-toggle="${escapeAttr(opts.toggle)}" title="Toggle visibility">${opts.visible === false ? "○" : "●"}</button>` : "";
    const trash = opts.removable ? `<button class="layer-trash" data-layer-remove="${escapeAttr(opts.removable)}" title="Delete layer">×</button>` : "";
    return `<div class="layer-row ${active ? "is-active" : ""}">${eye}<button class="layer-row-body" data-layer="${escapeAttr(id)}"><span class="layer-dot ${escapeAttr(dot)}"></span><span>${escapeHtml(label)}</span><strong>${escapeHtml(meta)}</strong></button>${trash}</div>`;
  }
  function effectLabel(effect) {
    if (effect.type === "dim") return `${Math.round(Number(effect.opacity ?? 0.45) * 100)}%`;
    if (effect.type === "blur") return `${blurStrength(effect)}% / ${effect.feather_pct ?? 18}%`;
    return effect.type || "";
  }
  function numericControl(name, label, value, min, max) {
    return `<div class="field compact-field"><label>${label}</label><input data-geom="${name}" type="number" step="0.5" min="${min}" max="${max}" value="${round1(value)}"></div>`;
  }
  function selectControl(name, label, value, options) {
    const selected = value || options[0];
    return `<div class="field compact-field"><label>${label}</label><select data-geom-select="${name}">${options.map(option => `<option value="${escapeAttr(option)}" ${option === selected ? "selected" : ""}>${escapeHtml(option)}</option>`).join("")}</select></div>`;
  }
  function applyGeometryInput(name, value) {
    if (!Number.isFinite(value)) return;
    const f = activeFinding();
    const marker = markerFor(f);
    if (name.startsWith("marker.") && marker) {
      const key = name.split(".")[1];
      const map = { x: "x_pct", y: "y_pct", w: "w_pct", h: "h_pct", cx: "cx_pct", cy: "cy_pct", rx: "rx_pct", ry: "ry_pct" };
      marker[map[key]] = value;
      marker.source = "manual";
    }
    if (name.startsWith("callout.")) {
      f.callout_position ||= { x_pct: 62, y_pct: 20, w_pct: 24 };
      const key = name.split(".")[1];
      const map = { x: "x_pct", y: "y_pct", w: "w_pct", scale: "scale_pct" };
      if (!map[key]) return;
      if (key === "w") value = clamp(value, CALLOUT_MIN_W_PCT, CALLOUT_MAX_W_PCT);
      if (key === "scale") value = clamp(value, CALLOUT_MIN_SCALE_PCT, CALLOUT_MAX_SCALE_PCT);
      f.callout_position[map[key]] = value;
    }
    if (name.startsWith("crop.")) {
      const edit = slideEdit(state().slides[app.activeSlide].slide_id);
      edit.crop ||= { x_pct: 0, y_pct: 0, w_pct: 100, h_pct: 100 };
      const key = name.split(".")[1];
      const map = { x: "x_pct", y: "y_pct", w: "w_pct", h: "h_pct" };
      edit.crop[map[key]] = value;
      normalizeCrop(edit.crop);
    }
  }
  function applyGeometrySelect(name, value) {
    const f = activeFinding();
    if (!f) return;
    if (name === "callout.anchor") {
      f.callout_position ||= { x_pct: 62, y_pct: 20, w_pct: 24 };
      f.callout_position.anchor = normalizeCalloutAnchor(value);
    }
  }
  function applyEffectInput(name, value) {
    if (!Number.isFinite(value)) return;
    const [, indexText, prop] = name.split(":");
    const effect = slideEdit(state().slides[app.activeSlide].slide_id).effects?.[Number(indexText)];
    if (!effect) return;
    if (prop === "opacity") effect.opacity = clamp(value, 0, 0.9);
    if (prop === "strength") {
      effect.strength_pct = clamp(value, 0, 100);
      effect.radius_px = strengthToBlurPx(effect.strength_pct);
    }
    if (prop === "radius") {
      effect.radius_px = clamp(value, 0, 28);
      effect.strength_pct = blurStrength(effect);
    }
    if (prop === "feather") effect.feather_pct = clamp(value, 0, 45);
  }
  function applyStyleInput(name, value) {
    if (!Number.isFinite(value)) return;
    const marker = markerFor(activeFinding());
    if (!marker) return;
    if (name === "fill_opacity") marker.fill_opacity = clamp(value / 100, 0, 0.8);
    if (name === "glow_opacity") marker.glow_opacity = clamp(value / 100, 0, 1);
    if (name === "stroke_width") marker.stroke_width = clamp(value, 1, 12);
    marker.highlight_style = dominantHighlightStyle(marker);
  }
  function selectLayer(layer) {
    app.activeLayer = layer;
    const match = /^effect:(\d+)$/.exec(layer);
    app.activeEffectIndex = match ? Number(match[1]) : null;
    render();
  }
  function toggleLayerVisibility(token) {
    const f = activeFinding();
    if (!f) return;
    const edit = slideEdit(state().slides[app.activeSlide].slide_id);
    mutate("Toggle layer visibility", () => {
      if (token === "marker-visible") {
        const marker = markerFor(f);
        if (marker) marker.hidden = !marker.hidden;
      }
      else if (token === "callout-visible") f.callout_visible = f.callout_visible === false;
      else if (token.startsWith("effect-visible:")) {
        const idx = Number(token.split(":")[1]);
        const e = edit.effects?.[idx];
        if (e) e.hidden = !e.hidden;
      }
    });
    render();
  }
  function removeLayer(token) {
    const edit = slideEdit(state().slides[app.activeSlide].slide_id);
    mutate("Remove layer", () => {
      if (token.startsWith("effect-remove:")) {
        const idx = Number(token.split(":")[1]);
        edit.effects?.splice(idx, 1);
      } else if (token === "marker-clear") {
        clearActiveMarkerPlacement({ insideMutation: true });
      }
    });
    render();
  }
  function clearActiveMarkerPlacement(options = {}) {
    const apply = () => {
      const f = activeFinding();
      const marker = markerFor(f);
      if (marker) {
        ["x_pct", "y_pct", "w_pct", "h_pct", "cx_pct", "cy_pct", "rx_pct", "ry_pct", "points"].forEach(k => delete marker[k]);
        marker.hidden = true;
        marker.source = "manual";
        delete marker.snapped_baton_index;
      }
      if (f) {
        f.hotspot_confidence = "needs-manual-marker";
        if (f.status === "approved") f.status = "needs_review";
      }
    };
    if (options.insideMutation) return apply();
    mutate("Delete hotspot placement", apply);
    app.activeLayer = "marker";
    render();
  }
  function applyQuickAction(action) {
    const f = activeFinding();
    if (!f) return;
    mutate("Quick visual action", () => {
      if (action === "toggle-callout") f.callout_visible = f.callout_visible === false;
      if (action === "center-callout") f.callout_position = { ...(f.callout_position || {}), x_pct: 62, y_pct: 20, w_pct: f.callout_position?.w_pct || 24 };
      if (action === "move-callout-here") {
        const slide = state().slides[app.activeSlide];
        if (slide) {
          f.callout_slide_id = slide.slide_id;
          f.callout_visible = true;
        }
      }
      if (action === "match-severity") {
        const marker = markerFor(f);
        if (marker) marker.stroke = severityColor(f.severity);
      }
      if (action === "reset-crop") slideEdit(state().slides[app.activeSlide].slide_id).crop = { x_pct: 0, y_pct: 0, w_pct: 100, h_pct: 100 };
      if (action === "clear-effects") clearActiveFindingEffects();
    });
    render();
  }
  function applyVisualPreset(name) {
    const f = activeFinding();
    const marker = markerFor(f);
    if (!f || !marker) return;
    mutate("Apply visual preset", () => {
      const edit = slideEdit(marker.slide_id);
      if (name === "problem-highlight") {
        marker.stroke = severityColor(f.severity);
        marker.stroke_width = 4;
        marker.highlight_style = "glow";
        marker.outline_visible = true;
        marker.fill_opacity = 0.06;
        marker.glow_opacity = 0.88;
        f.callout_visible = true;
      }
      if (name === "soft-blur") {
        const rect = expandRect(markerBounds(marker), 4);
        edit.effects.push(scopedEffect({ type: "blur", rect, mode: "outside", strength_pct: 30, radius_px: strengthToBlurPx(30), feather_pct: 26 }, f));
      }
      if (name === "premium-callout") {
        marker.stroke = severityColor(f.severity);
        marker.stroke_width = 3;
        marker.highlight_style = "outline";
        marker.outline_visible = true;
        marker.fill_opacity = 0;
        marker.glow_opacity = 0;
        f.callout_visible = true;
        f.callout_position = { ...(f.callout_position || {}), x_pct: 62, y_pct: 20, w_pct: Math.max(26, f.callout_position?.w_pct || 24) };
      }
      if (name === "dim-background") {
        marker.highlight_style = "spotlight";
        marker.spotlight_visible = true;
        marker.stroke = severityColor(f.severity);
        if (!edit.effects.some(e => e.type === "dim" && effectBelongsToFinding(e, f))) {
          edit.effects.push(scopedEffect({ type: "dim", opacity: 0.48 }, f));
        }
      }
      if (name === "clean-yellow") {
        marker.stroke = severityPalette.medium;
        marker.stroke_width = 3;
        marker.highlight_style = "outline";
        marker.outline_visible = true;
        marker.underline_visible = false;
        marker.spotlight_visible = false;
        marker.fill_opacity = 0;
        marker.glow_opacity = 0;
      }
      if (f.status === "needs_review" || f.status === "approved") f.status = "edited";
    });
    render();
  }
  function applyStylePreset(style) {
    const f = activeFinding();
    const marker = markerFor(f);
    if (!marker) return;
    mutate("Change highlight style", () => {
      marker.stroke ||= severityColor(f.severity);
      if (style === "outline") {
        marker.outline_visible = !markerStyleEnabled(marker, "outline");
        if (marker.outline_visible) marker.stroke_width = marker.stroke_width || 3;
      } else if (style === "fill") {
        marker.fill_opacity = markerFillOpacity(marker) > 0 ? 0 : 0.24;
      } else if (style === "glow") {
        marker.glow_opacity = markerGlowOpacity(marker) > 0 ? 0 : 0.72;
        if (marker.glow_opacity > 0) marker.stroke_width = Math.max(Number(marker.stroke_width || 0), 5);
      } else if (style === "underline") {
        marker.underline_visible = !markerStyleEnabled(marker, "underline");
        if (marker.underline_visible) marker.stroke_width = Math.max(Number(marker.stroke_width || 0), 4);
      } else if (style === "spotlight") {
        marker.spotlight_visible = !markerStyleEnabled(marker, "spotlight");
        const edit = slideEdit(marker.slide_id);
        if (marker.spotlight_visible && !edit.effects.some(e => e.type === "dim" && effectBelongsToFinding(e, f))) {
          edit.effects.push(scopedEffect({ type: "dim", opacity: 0.45 }, f));
        }
      }
      marker.highlight_style = dominantHighlightStyle(marker);
      if (!markerStyleEnabled(marker, "fill")) {
        marker.fill_opacity = 0;
      }
    });
    render();
  }
  function cycleStylePreset() {
    const marker = markerFor(activeFinding());
    if (!marker) return;
    const current = marker.highlight_style || "outline";
    const next = highlightStyles[(highlightStyles.indexOf(current) + 1) % highlightStyles.length];
    applyStylePreset(next);
  }
  function applySeverityColor(name) {
    const marker = markerFor(activeFinding());
    if (!marker) return;
    mutate("Change severity color", () => {
      marker.stroke = severityPalette[name] || severityPalette.medium;
      marker.stroke_width = marker.stroke_width || 3;
    });
    render();
  }
  function applyCalloutColor(name) {
    const f = activeFinding();
    if (!f) return;
    mutate("Change callout color", () => {
      f.callout_color = severityPalette[name] || severityColor(f.severity);
      if (f.status === "needs_review" || f.status === "approved") f.status = "edited";
    });
    render();
  }
  function openStageContextMenu(event) {
    event.preventDefault();
    event.stopPropagation();
    closeContextMenu();
    const target = event.target;
    const markerRef = target?.dataset?.ref;
    const effectIndex = target?.closest?.("[data-effect-index]")?.dataset?.effectIndex;
    const isCrop = Boolean(target?.closest?.(".crop-box"));
    const isCallout = Boolean(target?.closest?.(".callout"));
    if (markerRef && markerRef !== app.activeFindingRef) app.activeFindingRef = markerRef;
    const items = contextMenuItems({ markerRef, effectIndex, isCrop, isCallout });
    if (!items.length) return;
    const el = document.createElement("div");
    el.className = "context-menu";
    el.style.left = `${event.clientX}px`;
    el.style.top = `${event.clientY}px`;
    el.innerHTML = items.map(item => {
      if (item.type === "sep") return `<div class="context-sep"></div>`;
      if (item.type === "swatches") {
        return `<div class="context-swatches">${
          Object.entries(severityPalette).map(([name, color]) =>
            `<button class="context-swatch" data-context-action="set-color" data-color="${escapeAttr(color)}" style="background:${color}" title="${escapeAttr(name)}"></button>`
          ).join("")
        }<button class="context-swatch context-swatch-pick" data-context-action="pick-color" title="Custom color">+</button></div>`;
      }
      return `<button data-context-action="${escapeAttr(item.action)}">${escapeHtml(item.label)}${item.hint ? `<kbd>${escapeHtml(item.hint)}</kbd>` : ""}</button>`;
    }).join("");
    document.body.appendChild(el);
    // viewport-clamp the menu after layout
    const rect = el.getBoundingClientRect();
    const pad = 6;
    if (rect.right > window.innerWidth) el.style.left = `${Math.max(pad, window.innerWidth - rect.width - pad)}px`;
    if (rect.bottom > window.innerHeight) el.style.top = `${Math.max(pad, window.innerHeight - rect.height - pad)}px`;
    app.contextMenu = el;
    el.addEventListener("contextmenu", e => e.preventDefault());
    el.querySelectorAll("[data-context-action]").forEach(btn => btn.addEventListener("click", click => {
      click.stopPropagation();
      const color = btn.dataset.color;
      runContextAction(btn.dataset.contextAction, { effectIndex: Number(effectIndex), color });
      closeContextMenu();
    }));
  }
  function contextMenuItems({ markerRef, effectIndex, isCrop, isCallout }) {
    if (markerRef || (isCallout && activeFinding())) return [
      { type: "swatches" },
      { action: "match-severity", label: "Match severity color", hint: "M" },
      { type: "sep" },
      { action: "fill-toggle", label: "Toggle hotspot fill" },
      { action: "cycle-style", label: "Cycle highlight style", hint: "G" },
      { type: "sep" },
      { action: "shape-rect", label: "Change to rectangle" },
      { action: "shape-ellipse", label: "Change to ellipse" },
      { action: "shape-point", label: "Change to point" },
      { type: "sep" },
      { action: "expand-marker", label: "Expand highlight" },
      { action: "shrink-marker", label: "Shrink highlight" },
      { type: "sep" },
      { action: "snap-ai", label: "Snap to AI placement" },
      { action: "snap-baton", label: "Snap to nearest baton element", hint: "S" },
      { action: "approve-finding", label: "Approve finding", hint: "A" },
      { action: "clear-marker-placement", label: "Delete hotspot only", hint: "Del" },
      { action: "delete-marker", label: "Hide entire finding", hint: "H" }
    ];
    if (Number.isFinite(Number(effectIndex))) return [
      { action: "expand-effect", label: "Expand effect" },
      { action: "delete-effect", label: "Delete effect" }
    ];
    if (isCrop) return [
      { action: "expand-crop", label: "Expand crop" },
      { action: "reset-crop", label: "Reset crop" }
    ];
    return [
      { action: "add-dim", label: "Add dim spotlight" },
      { action: "reset-crop", label: "Reset crop" },
      { action: "clear-effects", label: "Clear effects" },
      { type: "sep" },
      { action: "undo", label: "Undo", hint: "Ctrl+Z" },
      { action: "redo", label: "Redo", hint: "Ctrl+Y" }
    ];
  }
  function runContextAction(action, meta = {}) {
    const f = activeFinding();
    const marker = markerFor(f);
    const edit = slideEdit(state().slides[app.activeSlide].slide_id);
    if (action === "undo") return undoLastAction();
    if (action === "redo") return redoLastAction();
    if (action === "snap-ai") return snapToAiMarker();
    if (action === "snap-baton") return snapToNearestBaton();
    if (action === "approve-finding") return setStatus("approved");
    if (action === "clear-marker-placement") return clearActiveMarkerPlacement();
    if (action === "delete-marker") return hideSelectedFindings();
    if (action === "cycle-style") return cycleStylePreset();
    if (action.startsWith("shape-")) return convertMarkerShape(action.replace("shape-", ""));
    if (action === "pick-color" && marker) {
      const picker = document.createElement("input");
      picker.type = "color";
      picker.value = (marker.stroke && /^#[0-9a-fA-F]{6}$/.test(marker.stroke)) ? marker.stroke : "#facc15";
      picker.style.position = "fixed";
      picker.style.opacity = "0";
      picker.style.pointerEvents = "none";
      document.body.appendChild(picker);
      picker.addEventListener("change", () => {
        const color = picker.value;
        mutate("Pick marker color", () => {
          marker.stroke = color;
          marker.fill_opacity = marker.fill_opacity || 0.18;
        });
        picker.remove();
        render();
      }, { once: true });
      picker.click();
      return;
    }
    mutate("Context action", () => {
      if (action === "set-color" && marker && meta.color) {
        marker.stroke = meta.color;
      }
      if (action === "fill-toggle" && marker) {
        const filled = (marker.fill_opacity || 0) > 0 || marker.highlight_style === "fill";
        marker.fill_opacity = filled ? 0 : 0.18;
        marker.highlight_style = filled ? "outline" : "fill";
      }
      if (action === "match-severity" && marker) marker.stroke = severityColor(f.severity);
      if (action === "expand-marker" && marker) expandMarker(marker, 2);
      if (action === "shrink-marker" && marker) expandMarker(marker, -2);
      if (action === "delete-effect") edit.effects.splice(meta.effectIndex, 1);
      if (action === "expand-effect" && edit.effects[meta.effectIndex]?.rect) edit.effects[meta.effectIndex].rect = expandRect(edit.effects[meta.effectIndex].rect, 2);
      if (action === "expand-crop") edit.crop = expandRect(edit.crop || defaultSlideEdit("").crop, -2);
      if (action === "reset-crop") edit.crop = { x_pct: 0, y_pct: 0, w_pct: 100, h_pct: 100 };
      if (action === "clear-effects") removeEffectsForFinding(edit, f);
      if (action === "add-dim" && !edit.effects.some(e => e.type === "dim" && effectBelongsToFinding(e, f))) edit.effects.push(scopedEffect({ type: "dim", opacity: 0.45 }, f));
    });
    render();
  }
  function closeContextMenu() {
    app.contextMenu?.remove();
    app.contextMenu = null;
  }
  function convertMarkerShape(shape) {
    const marker = markerFor(activeFinding());
    if (!marker) return;
    mutate("Convert marker shape", () => {
      const bounds = markerBounds(marker);
      const center = markerCenter(marker);
      if (shape === "rect") {
        setMarker({
          shape: "rect",
          x_pct: clamp(bounds.x_pct, 0, 99),
          y_pct: clamp(bounds.y_pct, 0, 99),
          w_pct: clamp(bounds.w_pct, 1, 100 - clamp(bounds.x_pct, 0, 99)),
          h_pct: clamp(bounds.h_pct, 1, 100 - clamp(bounds.y_pct, 0, 99)),
          source: "manual"
        });
      }
      if (shape === "ellipse") {
        setMarker({
          shape: "ellipse",
          cx_pct: clamp(center.x, 0, 100),
          cy_pct: clamp(center.y, 0, 100),
          rx_pct: clamp(bounds.w_pct / 2, 1, 50),
          ry_pct: clamp(bounds.h_pct / 2, 1, 50),
          source: "manual"
        });
      }
      if (shape === "point") {
        setMarker({ shape: "point", cx_pct: clamp(center.x, 0, 100), cy_pct: clamp(center.y, 0, 100), source: "manual" });
      }
    });
    render();
  }
  function markerBounds(marker) {
    if (marker.shape === "rect") return { x_pct: marker.x_pct || 0, y_pct: marker.y_pct || 0, w_pct: marker.w_pct || 4, h_pct: marker.h_pct || 4 };
    if (marker.shape === "ellipse") {
      const rx = marker.rx_pct || 4;
      const ry = marker.ry_pct || 3;
      return { x_pct: (marker.cx_pct || 50) - rx, y_pct: (marker.cy_pct || 50) - ry, w_pct: rx * 2, h_pct: ry * 2 };
    }
    if ((marker.shape === "polygon" || marker.shape === "freeform") && Array.isArray(marker.points) && marker.points.length) {
      const xs = marker.points.map(p => Number(p[0])).filter(Number.isFinite);
      const ys = marker.points.map(p => Number(p[1])).filter(Number.isFinite);
      if (!xs.length || !ys.length) return { x_pct: 48, y_pct: 48, w_pct: 4, h_pct: 4 };
      const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
      return { x_pct: minX, y_pct: minY, w_pct: Math.max(maxX - minX, 1), h_pct: Math.max(maxY - minY, 1) };
    }
    return { x_pct: (marker.cx_pct || 50) - 2, y_pct: (marker.cy_pct || 50) - 2, w_pct: 4, h_pct: 4 };
  }
  function expandMarker(marker, amount) {
    if (marker.shape === "rect") {
      const next = expandRect(marker, amount);
      Object.assign(marker, next);
    } else if (marker.shape === "ellipse") {
      marker.rx_pct = clamp((marker.rx_pct || 4) + amount, 1, 50);
      marker.ry_pct = clamp((marker.ry_pct || 3) + amount, 1, 50);
    }
    marker.source = "manual";
  }
  function expandRect(rect, amount) {
    const x = clamp((rect.x_pct || 0) - amount, 0, 99);
    const y = clamp((rect.y_pct || 0) - amount, 0, 99);
    const right = clamp((rect.x_pct || 0) + (rect.w_pct || 1) + amount, x + 1, 100);
    const bottom = clamp((rect.y_pct || 0) + (rect.h_pct || 1) + amount, y + 1, 100);
    return { ...rect, x_pct: x, y_pct: y, w_pct: right - x, h_pct: bottom - y };
  }
  function nudgeActiveVisual(key, amount, resize) {
    const f = activeFinding();
    const marker = markerFor(f);
    if (!f || !marker) return;
    const dx = key === "ArrowLeft" ? -amount : key === "ArrowRight" ? amount : 0;
    const dy = key === "ArrowUp" ? -amount : key === "ArrowDown" ? amount : 0;
    mutate(resize ? "Resize marker" : "Nudge marker", () => {
      if (resize) {
        if (marker.shape === "rect") {
          marker.w_pct = clamp((marker.w_pct || 4) + dx, 1, 100);
          marker.h_pct = clamp((marker.h_pct || 4) + dy, 1, 100);
        } else if (marker.shape === "ellipse") {
          marker.rx_pct = clamp((marker.rx_pct || 4) + dx, 1, 50);
          marker.ry_pct = clamp((marker.ry_pct || 3) + dy, 1, 50);
        } else if ((marker.shape === "polygon" || marker.shape === "freeform") && Array.isArray(marker.points)) {
          resizeMarkerPoints(marker, dx, dy);
        }
      } else if (marker.shape === "rect") {
        marker.x_pct = clamp((marker.x_pct || 0) + dx, 0, 100);
        marker.y_pct = clamp((marker.y_pct || 0) + dy, 0, 100);
      } else if ((marker.shape === "polygon" || marker.shape === "freeform") && Array.isArray(marker.points)) {
        marker.points = marker.points.map(point => [clamp(Number(point[0]) + dx, 0, 100), clamp(Number(point[1]) + dy, 0, 100)]);
      } else {
        marker.cx_pct = clamp((marker.cx_pct || 50) + dx, 0, 100);
        marker.cy_pct = clamp((marker.cy_pct || 50) + dy, 0, 100);
      }
      marker.source = "manual";
    });
    render();
  }
  function resizeMarkerPoints(marker, dx, dy) {
    const bounds = markerBounds(marker);
    const center = markerCenter(marker);
    const nextW = clamp(bounds.w_pct + dx * 2, 1, 100);
    const nextH = clamp(bounds.h_pct + dy * 2, 1, 100);
    const sx = bounds.w_pct ? nextW / bounds.w_pct : 1;
    const sy = bounds.h_pct ? nextH / bounds.h_pct : 1;
    marker.points = marker.points.map(point => [
      clamp(center.x + (Number(point[0]) - center.x) * sx, 0, 100),
      clamp(center.y + (Number(point[1]) - center.y) * sy, 0, 100)
    ]);
  }
  async function persistImportedAsset(assetId, file, dataUrl) {
    if (!isServerBackedEditor()) return null;
    try {
      const response = await fetch("/api/import-asset", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          asset_id: assetId,
          filename: file.name,
          mime_type: file.type,
          data_url: dataUrl
        })
      });
      const result = await response.json();
      if (!response.ok || !result.ok) throw new Error(result.error || "Import persistence failed");
      return result.asset || null;
    } catch (error) {
      console.warn("Could not persist imported screenshot through the local editor server", error);
      return null;
    }
  }
  function importImage(event) {
    clearMessages();
    const file = event.target.files[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) return showError("Import rejected: choose an image file.");
    if (file.size > MAX_IMPORT_BYTES) return showError("Import rejected: image must be 5MB or smaller.");
    const reader = new FileReader();
    reader.onerror = () => showError("Import failed: the browser could not read that image.");
    reader.onload = async () => {
      const assetId = `import-${Date.now()}`;
      const serverAsset = await persistImportedAsset(assetId, file, reader.result);
      if (!serverAsset && file.size > MAX_BROWSER_FALLBACK_IMPORT_BYTES) {
        showError("Import rejected: this image is too large for browser-only storage. Open the editor through the local server, or use an image 2MB or smaller.");
        event.target.value = "";
        return;
      }
      mutate("Import screenshot", () => {
        const s = state();
        const source = serverAsset?.source || `user-imports/${safeFilename(file.name)}`;
        const asset = {
          asset_id: assetId,
          name: file.name,
          source,
          mime_type: file.type,
          created_at: new Date().toISOString(),
          persistence: serverAsset ? "server" : "browser-fallback"
        };
        if (!serverAsset) asset.data_url = reader.result;
        s.imported_assets.push(asset);
        const slide = { slide_id: `${s.device}-import-${s.imported_assets.length}`, source, asset_id: assetId, viewport: s.device, device: s.device, section_index: s.slides.length, section_label: `Imported: ${file.name}`, user_imported: true };
        s.slides.push(slide);
        s.slide_edits.push(defaultSlideEdit(slide.slide_id));
        app.images[app.activeDevice][slide.slide_id] = reader.result;
        app.activeSlide = s.slides.length - 1;
      });
      flashStatus(serverAsset ? "Imported screenshot and saved it into the engagement folder." : "Note: browser-only import - stored as a data URL until this session ends.");
      render();
    };
    reader.readAsDataURL(file);
  }

  function markerSvg(marker, active) {
    if (!isMarkerPlaced(marker)) return "";
    const selected = app.selection.has(marker.f_ref);
    const activeClass = (active || selected) ? " marker-active" : "";
    const ref = escapeAttr(marker.f_ref || "");
    const stroke = escapeAttr(marker.stroke || severityPalette.medium);
    const styleName = dominantHighlightStyle(marker);
    const sw = markerStrokeWidth(marker) / 10;
    const fillOpacity = markerFillOpacity(marker);
    const fill = fillOpacity > 0 ? stroke : "transparent";
    const outline = markerStyleEnabled(marker, "outline");
    const shapeStroke = outline ? stroke : "transparent";
    const glow = markerGlowHalo(marker, stroke, sw);
    const glowFilter = markerGlowOpacity(marker) > 0 ? `filter:drop-shadow(0 0 2px ${stroke});` : "";
    const styleAttr = `stroke:${shapeStroke};stroke-width:${sw};fill:${fill};fill-opacity:${fillOpacity};${glowFilter}`;
    if (marker.shape === "rect") {
      const x = marker.x_pct || 0, y = marker.y_pct || 0, w = marker.w_pct || 4, h = marker.h_pct || 4;
      const underline = markerStyleEnabled(marker, "underline") ? `<line data-ref="${ref}" class="marker-underline${activeClass}" x1="${x}" y1="${y + h}" x2="${x + w}" y2="${y + h}" style="stroke:${stroke};stroke-width:${Math.max(sw * 1.8, .6)}"></line>` : "";
      return `<g>${glow}<rect data-marker="${active ? "active" : ""}" data-ref="${ref}" class="marker-shape marker-style-${styleName}${activeClass}" style="${styleAttr}" x="${x}" y="${y}" width="${w}" height="${h}" rx="1"></rect>${underline}${active ? handlesForRect(x, y, w, h) : ""}</g>`;
    }
    if (marker.shape === "ellipse") {
      const cx = marker.cx_pct || 50, cy = marker.cy_pct || 50, rx = marker.rx_pct || 4, ry = marker.ry_pct || 3;
      return `<g>${glow}<ellipse data-marker="${active ? "active" : ""}" data-ref="${ref}" class="marker-shape marker-style-${styleName}${activeClass}" style="${styleAttr}" cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}"></ellipse>${active ? handlesForEllipse(cx, cy, rx, ry) : ""}</g>`;
    }
    if (marker.shape === "polygon" && Array.isArray(marker.points)) {
      const pts = pointsAttr(marker.points);
      return `<g>${glow}<polygon data-marker="${active ? "active" : ""}" data-ref="${ref}" class="marker-shape marker-style-${styleName}${activeClass}" style="${styleAttr};stroke-linejoin:round" points="${pts}"></polygon></g>`;
    }
    if (marker.shape === "freeform" && Array.isArray(marker.points)) {
      const d = pathD(marker.points, true);
      return `<g>${glow}<path data-marker="${active ? "active" : ""}" data-ref="${ref}" class="marker-shape marker-style-${styleName}${activeClass}" style="${styleAttr};stroke-linecap:round;stroke-linejoin:round" d="${d}"></path></g>`;
    }
    return `<g>${glow}<circle data-marker="${active ? "active" : ""}" data-ref="${ref}" class="marker-point marker-style-${styleName}${activeClass}" style="${styleAttr}" cx="${marker.cx_pct || 50}" cy="${marker.cy_pct || 50}" r="${active ? 2.1 : 1.35}"></circle></g>`;
  }
  function markerFillOpacity(marker) {
    return clamp(Number(marker?.fill_opacity ?? 0), 0, 0.8);
  }
  function markerGlowOpacity(marker) {
    return clamp(Number(marker?.glow_opacity ?? ((marker?.highlight_style || "") === "glow" ? 0.72 : 0)), 0, 1);
  }
  function markerStrokeWidth(marker) {
    return clamp(Number(marker?.stroke_width || 3), 1, 12);
  }
  function markerStyleEnabled(marker, key) {
    const style = marker?.highlight_style || "outline";
    if (key === "outline") return marker?.outline_visible !== false;
    if (key === "fill") return markerFillOpacity(marker) > 0;
    if (key === "glow") return markerGlowOpacity(marker) > 0;
    if (key === "underline") return marker?.underline_visible === true || style === "underline";
    if (key === "spotlight") return marker?.spotlight_visible === true || style === "spotlight";
    return false;
  }
  function dominantHighlightStyle(marker) {
    if (markerStyleEnabled(marker, "glow")) return "glow";
    if (markerStyleEnabled(marker, "fill")) return "fill";
    if (markerStyleEnabled(marker, "underline")) return "underline";
    if (markerStyleEnabled(marker, "spotlight")) return "spotlight";
    if (markerStyleEnabled(marker, "outline")) return "outline";
    return "none";
  }
  function markerGlowHalo(marker, stroke, sw) {
    const opacity = markerGlowOpacity(marker);
    if (opacity <= 0) return "";
    const haloWidth = Math.max(sw * 6.5, 1.8);
    const style = `stroke:${stroke};stroke-width:${haloWidth};fill:none;opacity:${opacity};--glow-opacity:${opacity};filter:drop-shadow(0 0 3px ${stroke}) drop-shadow(0 0 14px ${stroke}) drop-shadow(0 0 28px ${stroke});pointer-events:none;vector-effect:non-scaling-stroke;`;
    if (marker.shape === "rect") return `<rect class="marker-glow" style="${style}" x="${marker.x_pct || 0}" y="${marker.y_pct || 0}" width="${marker.w_pct || 4}" height="${marker.h_pct || 4}" rx="1"></rect>`;
    if (marker.shape === "ellipse") return `<ellipse class="marker-glow" style="${style}" cx="${marker.cx_pct || 50}" cy="${marker.cy_pct || 50}" rx="${marker.rx_pct || 4}" ry="${marker.ry_pct || 3}"></ellipse>`;
    if (marker.shape === "polygon" && Array.isArray(marker.points)) return `<polygon class="marker-glow" style="${style};stroke-linejoin:round" points="${pointsAttr(marker.points)}"></polygon>`;
    if (marker.shape === "freeform" && Array.isArray(marker.points)) return `<path class="marker-glow" style="${style};stroke-linecap:round;stroke-linejoin:round" d="${pathD(marker.points, true)}"></path>`;
    return `<circle class="marker-glow" style="${style}" cx="${marker.cx_pct || 50}" cy="${marker.cy_pct || 50}" r="2.1"></circle>`;
  }
  function pointsAttr(points) {
    return points.map(p => `${Number(p[0]).toFixed(2)},${Number(p[1]).toFixed(2)}`).join(" ");
  }
  function pathD(points, closed) {
    if (!points.length) return "";
    const parts = [`M ${points[0][0]} ${points[0][1]}`];
    for (let i = 1; i < points.length; i++) parts.push(`L ${points[i][0]} ${points[i][1]}`);
    if (closed) parts.push("Z");
    return parts.join(" ");
  }
  function polygonCentroid(points) {
    if (!points?.length) return { x: 50, y: 50 };
    const x = points.reduce((s, p) => s + p[0], 0) / points.length;
    const y = points.reduce((s, p) => s + p[1], 0) / points.length;
    return { x, y };
  }
  function handlesForRect(x, y, w, h) {
    return [["nw", x, y], ["n", x + w / 2, y], ["ne", x + w, y], ["e", x + w, y + h / 2], ["se", x + w, y + h], ["s", x + w / 2, y + h], ["sw", x, y + h], ["w", x, y + h / 2]]
      .map(([name, hx, hy]) => `<rect data-handle="${name}" class="marker-handle" x="${hx - .8}" y="${hy - .8}" width="1.6" height="1.6"></rect>`).join("");
  }
  function handlesForEllipse(cx, cy, rx, ry) {
    return [["nw", cx - rx, cy - ry], ["ne", cx + rx, cy - ry], ["sw", cx - rx, cy + ry], ["se", cx + rx, cy + ry]]
      .map(([name, hx, hy]) => `<rect data-handle="${name}" class="marker-handle" x="${hx - .8}" y="${hy - .8}" width="1.6" height="1.6"></rect>`).join("");
  }
  function markerCenter(marker) {
    if (!marker) return { x: 50, y: 50 };
    if (marker.shape === "rect") return { x: (marker.x_pct || 0) + (marker.w_pct || 0) / 2, y: (marker.y_pct || 0) + (marker.h_pct || 0) / 2 };
    if ((marker.shape === "polygon" || marker.shape === "freeform") && Array.isArray(marker.points)) return polygonCentroid(marker.points);
    return { x: marker.cx_pct || 50, y: marker.cy_pct || 50 };
  }
  function normalizeCalloutAnchor(value) {
    return calloutAnchors.includes(value) ? value : "auto";
  }
  function calloutPosition(f) {
    return {
      x_pct: 62,
      y_pct: 20,
      w_pct: 24,
      scale_pct: 100,
      anchor: "auto",
      ...(f?.callout_position || {})
    };
  }
  function resolvedCalloutAnchor(f, marker) {
    const pos = calloutPosition(f);
    const explicit = normalizeCalloutAnchor(pos.anchor);
    if (explicit !== "auto") return explicit;
    if (!marker) return "left";
    const center = markerCenter(marker);
    const calloutCenter = {
      x: Number(pos.x_pct ?? 62) + Number(pos.w_pct ?? 24) / 2,
      y: Number(pos.y_pct ?? 20) + 10
    };
    const dx = center.x - calloutCenter.x;
    const dy = center.y - calloutCenter.y;
    return Math.abs(dx) > Math.abs(dy)
      ? (dx < 0 ? "left" : "right")
      : (dy < 0 ? "top" : "bottom");
  }
  function calloutConnectorTarget(f, marker) {
    const pos = calloutPosition(f);
    const anchor = resolvedCalloutAnchor(f, marker);
    const x = Number(pos.x_pct ?? 62);
    const y = Number(pos.y_pct ?? 20);
    const w = Number(pos.w_pct ?? 24);
    if (anchor === "right") return { x: x + w, y: y + 10 };
    if (anchor === "top") return { x: x + w / 2, y };
    if (anchor === "bottom") return { x: x + w / 2, y: y + 20 };
    return { x, y: y + 10 };
  }
  function connectorSvg(marker, active, findingOverride = null) {
    if (!isMarkerPlaced(marker)) return "";
    const f = findingOverride || state().findings.find(item => item.marker_id === marker.marker_id);
    if (!f || f.callout_visible === false) return "";
    const c = markerCenter(marker);
    const pos = calloutConnectorTarget(f, marker);
    const stroke = escapeAttr(calloutColor(f));
    return `<line class="connector-line ${active ? "connector-active" : ""}" style="stroke:${stroke}" x1="${c.x}" y1="${c.y}" x2="${pos.x}" y2="${pos.y}"></line>`;
  }
  function calloutHtml(f, markerOverride = null) {
    if (f.callout_visible === false) return "";
    const pos = calloutPosition(f);
    const stroke = escapeAttr(calloutColor(f));
    const anchor = resolvedCalloutAnchor(f, markerOverride);
    const scale = clamp(Number(pos.scale_pct ?? 100), CALLOUT_MIN_SCALE_PCT, CALLOUT_MAX_SCALE_PCT) / 100;
    return `<article class="callout callout-arrow-${escapeAttr(anchor)}" data-callout-anchor="${escapeAttr(anchor)}" style="left:${pos.x_pct}%;top:${pos.y_pct}%;width:${pos.w_pct || 24}%;border-color:${stroke};color:${stroke};--callout-scale:${scale}"><strong style="color:${stroke}">${escapeHtml(displayCalloutTitle(f))}</strong><p>${escapeHtml(f.callout_body || "")}</p><span class="callout-resize" style="background:${stroke}" data-callout-resize="true"></span></article>`;
  }
  function effectHtml(effect, index) {
    if (effect.hidden) return "";
    if (effect.type === "blur") {
      const r = effect.rect || {};
      const feather = clamp(Number(effect.feather_pct ?? 18), 0, 45);
      const active = app.activeLayer === `effect:${index}`;
      if ((effect.mode || "outside") === "outside") {
        return blurOutsideHtml(r, effect, index, active);
      }
      return `<div class="blur-box ${active ? "is-active" : ""}" data-effect-index="${index}" style="left:${r.x_pct}%;top:${r.y_pct}%;width:${r.w_pct}%;height:${r.h_pct}%;--blur:${effect.radius_px || 8}px;--feather:${feather}%">
        ${rectHandles("effect")}
      </div>`;
    }
    if (effect.type === "dim" && effect.rect) {
      const r = effect.rect || {};
      const opacity = clamp(Number(effect.opacity ?? 0.38), 0, 0.9);
      const active = app.activeLayer === `effect:${index}`;
      return `<div class="dim-region ${active ? "is-active" : ""}" data-effect-index="${index}" style="left:${r.x_pct}%;top:${r.y_pct}%;width:${r.w_pct}%;height:${r.h_pct}%;--dim-opacity:${opacity}">
        ${rectHandles("effect")}
      </div>`;
    }
    if (effect.type === "dim") return dimEffectHtml(effect);
    return "";
  }
  function blurOutsideHtml(rect, effect, index, active = false) {
    const r = normalizeRectObject(rect);
    const blur = Number(effect.radius_px || 8);
    const style = `--blur:${blur}px`;
    const pieces = [
      { left: 0, top: 0, width: 100, height: r.y_pct },
      { left: 0, top: r.y_pct + r.h_pct, width: 100, height: Math.max(0, 100 - (r.y_pct + r.h_pct)) },
      { left: 0, top: r.y_pct, width: r.x_pct, height: r.h_pct },
      { left: r.x_pct + r.w_pct, top: r.y_pct, width: Math.max(0, 100 - (r.x_pct + r.w_pct)), height: r.h_pct }
    ].filter(piece => piece.width > 0 && piece.height > 0);
    return `${pieces.map(piece => `<div class="blur-outside-piece" style="left:${piece.left}%;top:${piece.top}%;width:${piece.width}%;height:${piece.height}%;${style}"></div>`).join("")}
      <div class="blur-focus-rect ${active ? "is-active" : ""}" data-effect-index="${index}" style="left:${r.x_pct}%;top:${r.y_pct}%;width:${r.w_pct}%;height:${r.h_pct}%">
        ${rectHandles("effect")}
      </div>`;
  }
  function dimEffectHtml(effect) {
    const slide = state().slides[app.activeSlide];
    const opacity = clamp(Number(effect.opacity ?? 0.45), 0, 0.9);
    const owner = state().findings.find(f => f.f_ref === effect.f_ref);
    const ownerMarker = markerFor(owner);
    const placedOwnerMarker = isMarkerPlaced(ownerMarker) ? ownerMarker : null;
    const slideMarkers = placedOwnerMarker ? [placedOwnerMarker] : visibleStageMarkers(slide?.slide_id);
    if (!slideMarkers.length) return `<div class="dim-box" style="opacity:${opacity}"></div>`;
    // SVG mask: white background = dimmed, black shapes = cutouts (visible). Mirrors the Python renderer.
    const maskId = `editor-dim-mask-${slide.slide_id.replace(/[^a-z0-9]/gi, "-")}`;
    const cutouts = slideMarkers.map(m => {
      if (m.shape === "rect") return `<rect x="${m.x_pct || 0}" y="${m.y_pct || 0}" width="${m.w_pct || 4}" height="${m.h_pct || 4}" rx="1" fill="black"/>`;
      if (m.shape === "ellipse") return `<ellipse cx="${m.cx_pct || 50}" cy="${m.cy_pct || 50}" rx="${m.rx_pct || 4}" ry="${m.ry_pct || 3}" fill="black"/>`;
      if (m.shape === "polygon" && Array.isArray(m.points)) return `<polygon points="${pointsAttr(m.points)}" fill="black"/>`;
      if (m.shape === "freeform" && Array.isArray(m.points)) return `<path d="${pathD(m.points, true)}" fill="black"/>`;
      return `<circle cx="${m.cx_pct || 50}" cy="${m.cy_pct || 50}" r="2.4" fill="black"/>`;
    }).join("");
    return `<svg class="dim-overlay" viewBox="0 0 100 100" preserveAspectRatio="none">
      <defs><mask id="${maskId}" maskUnits="userSpaceOnUse" x="0" y="0" width="100" height="100">
        <rect x="0" y="0" width="100" height="100" fill="white"/>${cutouts}
      </mask></defs>
      <rect x="0" y="0" width="100" height="100" fill="black" fill-opacity="${opacity}" mask="url(#${maskId})"/>
    </svg>`;
  }
  function cropHtml(crop) {
    if (!crop || isFullCrop(crop)) return "";
    return `<div class="crop-box ${app.activeLayer === "crop" ? "is-active" : ""}" style="left:${crop.x_pct}%;top:${crop.y_pct}%;width:${crop.w_pct}%;height:${crop.h_pct}%">
      ${rectHandles("crop")}
    </div>`;
  }
  function rectHandles(kind) {
    return ["nw", "n", "ne", "e", "se", "s", "sw", "w"]
      .map(handle => `<span class="box-handle handle-${handle}" data-${kind}-handle="${handle}"></span>`)
      .join("");
  }
  function previewSvg(a, b, mode) {
    if (mode === "point") return `<circle class="preview-shape" cx="${b.x}" cy="${b.y}" r="1.6"></circle>`;
    const r = normalizeRect(a, b);
    if (mode === "ellipse") return `<ellipse class="preview-shape" cx="${r.x_pct + r.w_pct / 2}" cy="${r.y_pct + r.h_pct / 2}" rx="${r.w_pct / 2}" ry="${r.h_pct / 2}"></ellipse>`;
    if (["rect", "blur", "crop", "dim"].includes(mode)) return `<rect class="preview-shape" x="${r.x_pct}" y="${r.y_pct}" width="${r.w_pct}" height="${r.h_pct}" rx="1"></rect>`;
    return "";
  }
  function displayTitle(f) { return f.finding_title_override || f.finding_title || f.callout_title || f.f_ref; }
  function displayCalloutTitle(f) { return f.callout_title_override || f.callout_title || displayTitle(f); }
  function downloadState() {
    state().updated_at = new Date().toISOString();
    const blob = new Blob([JSON.stringify(state(), null, 2)], { type: "application/json" });
    download(blob, `review-state-${app.activeDevice}.json`);
    flashStatus("Downloaded review state");
  }
  async function exportReviewStateForFinal() {
    if (location.protocol === "http:" || location.protocol === "https:") {
      try {
        const s = state();
        s.updated_at = new Date().toISOString();
        flashStatus("Rendering final report...");
        const response = await fetch("/api/render-review", {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ state: s })
        });
        const result = await response.json();
        if (!response.ok || !result.ok) throw new Error(result.error || "Render failed");
        saveLocal();
        flashStatus(`Rendered ${result.final_report}`);
        window.open(result.url, "_blank", "noopener");
        return;
      } catch (error) {
        showError(error.message || String(error));
        return;
      }
    }
    downloadState();
    flashStatus(`Downloaded review state. Run generate-report.py --from-review review-state-${app.activeDevice}.json to render final HTML.`);
  }
  function download(blob, filename) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }
  function flashStatus(message) {
    const el = document.getElementById("statusMessage");
    el.textContent = message;
    clearTimeout(app.saveTimer);
    app.saveTimer = setTimeout(() => { el.textContent = ""; }, 1800);
  }
  function showError(message) { document.getElementById("errorMessage").textContent = message; }
  function clearMessages() { showError(""); }
  function displayWidth(slide) {
    const width = Number(slide.natural_width || 0);
    if (width > 0) {
      if (slide.device === "mobile" || slide.viewport === "mobile") {
        const cssWidth = width > 700 ? width / 3 : width;
        return clamp(cssWidth, 320, 430);
      }
      return clamp(width, 640, 960);
    }
    return slide.device === "mobile" ? 390 : 960;
  }
  function defaultSlideEdit(slideId) {
    return { slide_id: slideId, crop: { x_pct: 0, y_pct: 0, w_pct: 100, h_pct: 100 }, transform: { scale: 1, rotate_deg: 0, translate_x_pct: 0, translate_y_pct: 0 }, effects: [] };
  }
  function clipPathStyle(crop) {
    if (!crop || isFullCrop(crop)) return "";
    const right = 100 - (crop.x_pct + crop.w_pct);
    const bottom = 100 - (crop.y_pct + crop.h_pct);
    return `clip-path:inset(${crop.y_pct}% ${right}% ${bottom}% ${crop.x_pct}%);`;
  }
  function isFullCrop(crop) { return crop.x_pct === 0 && crop.y_pct === 0 && crop.w_pct === 100 && crop.h_pct === 100; }
  function safeFilename(name) { return String(name || "imported-image").replace(/[^a-zA-Z0-9._-]+/g, "-").replace(/^-+|-+$/g, "") || "imported-image"; }
  function isTypingTarget(target) {
    if (!target) return false;
    const tag = target.tagName?.toLowerCase();
    return tag === "input" || tag === "textarea" || tag === "select" || target.isContentEditable;
  }
  function escapeHtml(value) { return String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
  function escapeAttr(value) { return escapeHtml(value); }
  function escapeXml(value) { return escapeHtml(value); }
  function clamp(n, min, max) { return Math.max(min, Math.min(max, n)); }
  function round1(value) { return Math.round(Number(value || 0) * 10) / 10; }
  function clone(value) { return JSON.parse(JSON.stringify(value)); }

  init();
})();
