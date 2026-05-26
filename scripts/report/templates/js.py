"""JS runtime for the v1.0 three-panel app-shell report.

Responsibilities:
- Slide navigation (prev/next/thumbnail) — hotspot visibility filtered per slide.
- Tab switching (By Cluster / Priority Path / Ethics) — left-rail only.
- Finding selection: click row or hotspot -> detail panel on the right.
- Add-to-brief toggle with localStorage persistence per engagement.
- Export modal: bullets + markdown-mirror formats, clipboard copy.
"""

import json


def get_report_js(slide_sources_json, slide_aspect_ratios_json,
                  findings_json, export_markdown_json,
                  engagement_id="", device="", editor_href="editor.html"):
    """Compose the runtime JS with baked-in data (CSP-safe, no fetch)."""
    return _RUNTIME_JS.format(
        slide_sources=slide_sources_json,
        slide_aspect_ratios=slide_aspect_ratios_json,
        findings=findings_json,
        export_markdown=export_markdown_json,
        engagement_id=json.dumps(engagement_id),
        device=json.dumps(device),
        editor_href=json.dumps(editor_href),
    )


_RUNTIME_JS = r"""
(function() {{
  "use strict";

  // ----- Baked-in data -----------------------------------------------------
  var SLIDE_SOURCES       = {slide_sources};
  var SLIDE_ASPECT_RATIOS = {slide_aspect_ratios};
  var FINDINGS            = {findings};
  var EXPORT_MARKDOWN     = {export_markdown};
  var ENGAGEMENT_ID       = {engagement_id};
  var DEVICE              = {device};
  var EDITOR_HREF         = {editor_href};

  // ----- DOM refs ----------------------------------------------------------
  var mainImg   = document.getElementById('mainImage');
  var mainSlide = document.getElementById('mainSlide');
  var slidePos  = document.getElementById('slidePos');
  var slideTot  = document.getElementById('slideTotal');
  var briefCount = document.getElementById('briefCount');
  var briefCountBottom = document.getElementById('briefCountBottom');
  var exportBtn = document.getElementById('exportBtn');
  var exportBtnBottom = document.getElementById('exportBtnBottom');
  var detailEmpty = document.getElementById('detailEmpty');
  var modal = document.getElementById('exportModal');
  var exportPreview = document.getElementById('exportPreview');
  var panelCenter = document.getElementById('panelCenter');
  var callout = document.getElementById('callout');
  var screenshotWrapper = document.querySelector('.screenshot-wrapper');
  var originalCalloutParent = callout ? callout.parentElement : null;
  var reviewEffectLayer = document.getElementById('reviewEffectLayer');

  // ----- State -------------------------------------------------------------
  var slideIdx = 0;
  var selectedFid = null;
  var exportFormat = 'bullets';
  var STORAGE_KEY = 'ecp-brief-' + (document.title || 'default');
  var EDITOR_PICK_KEY = 'ecp-editor-picks:' + ENGAGEMENT_ID + ':' + DEVICE;

  var brief = new Set();
  try {{
    var raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {{
      var arr = JSON.parse(raw);
      if (Array.isArray(arr)) arr.forEach(function(id) {{ brief.add(id); }});
    }}
  }} catch (e) {{ /* session-only brief */ }}

  var findingByFid = {{}};
  FINDINGS.forEach(function(f) {{ findingByFid[f.fid] = f; }});

  // ----- Manual editor queue ----------------------------------------------
  function readEditorQueue() {{
    try {{
      var raw = localStorage.getItem(EDITOR_PICK_KEY);
      var arr = raw ? JSON.parse(raw) : [];
      return Array.isArray(arr) ? arr : [];
    }} catch (e) {{
      return [];
    }}
  }}
  function writeEditorQueue(arr) {{
    try {{ localStorage.setItem(EDITOR_PICK_KEY, JSON.stringify(arr)); }} catch (e) {{}}
    updateEditorQueueUI();
  }}
  function queueForEditor(fid) {{
    if (!fid) fid = selectedFid;
    if (!fid) return;
    var arr = readEditorQueue();
    if (arr.indexOf(fid) === -1) arr.push(fid);
    writeEditorQueue(arr);
  }}
  function editorUrl(fid) {{
    var joiner = EDITOR_HREF.indexOf('#') >= 0 ? '&' : '#';
    return EDITOR_HREF + joiner + 'pick=' + encodeURIComponent(fid || selectedFid || '') + '&device=' + encodeURIComponent(DEVICE || '');
  }}
  function openEditor(fid) {{
    if (fid) queueForEditor(fid);
    window.open(editorUrl(fid), '_blank', 'noopener,noreferrer');
  }}
  function updateEditorQueueUI() {{
    var queued = readEditorQueue();
    var btns = document.querySelectorAll('.detail-btn-editor-queue');
    for (var i = 0; i < btns.length; i++) {{
      var fid = btns[i].getAttribute('data-fid');
      var isQueued = queued.indexOf(fid) !== -1;
      btns[i].classList.toggle('queued', isQueued);
      btns[i].textContent = isQueued ? 'Queued for edit ✓' : 'Queue edit';
    }}
  }}
  window.queueForEditor = queueForEditor;
  window.openEditor = openEditor;

  // ----- Slide navigation --------------------------------------------------
  function setSlide(i) {{
    if (!SLIDE_SOURCES || !SLIDE_SOURCES.length) return;
    var n = SLIDE_SOURCES.length;
    slideIdx = ((i % n) + n) % n;
    mainImg.src = SLIDE_SOURCES[slideIdx];
    if (SLIDE_ASPECT_RATIOS[slideIdx]) {{
      mainSlide.style.setProperty('--slide-aspect-ratio', SLIDE_ASPECT_RATIOS[slideIdx]);
    }}
    var thumbs = document.querySelectorAll('.thumb');
    for (var ti = 0; ti < thumbs.length; ti++) {{
      thumbs[ti].classList.toggle('active', ti === slideIdx);
    }}
    if (slidePos) slidePos.textContent = String(slideIdx + 1);
    if (slideTot) slideTot.textContent = String(n);
    var hotspots = document.querySelectorAll('.hotspot');
    for (var hi = 0; hi < hotspots.length; hi++) {{
      var hs = parseInt(hotspots[hi].getAttribute('data-slide'), 10);
      hotspots[hi].hidden = (hs !== slideIdx);
    }}
    if (selectedFid) {{
      renderReviewEffects(selectedFid, document.querySelector('.hotspot.selected'));
    }}
  }}
  function prevSlide() {{ setSlide(slideIdx - 1); }}
  function nextSlide() {{ setSlide(slideIdx + 1); }}
  window.setSlide = setSlide;
  window.prevSlide = prevSlide;
  window.nextSlide = nextSlide;

  // ----- Tabs --------------------------------------------------------------
  function switchTab(name) {{
    var tabs = document.querySelectorAll('.panel-tab');
    for (var i = 0; i < tabs.length; i++) {{
      var active = tabs[i].getAttribute('data-tab') === name;
      tabs[i].classList.toggle('active', active);
      tabs[i].setAttribute('aria-selected', active ? 'true' : 'false');
    }}
    var panels = document.querySelectorAll('.panel-scroll');
    for (var j = 0; j < panels.length; j++) {{
      panels[j].hidden = (panels[j].getAttribute('data-panel') !== name);
    }}
  }}
  window.switchTab = switchTab;

  // ----- Finding selection -------------------------------------------------
  function selectFinding(fid) {{
    selectedFid = fid;
    // Flip center panel from empty state -> active stage, but only when
    // there are actually screenshots to show. In text-only mode (file
    // audits, description audits, acquisition failures — Codex M3) the
    // SLIDE_SOURCES array is empty; flipping to "active" would reveal a
    // broken <img> tag. Keep empty-state visible in that case — the
    // detail panel on the right still populates so the user can read
    // the finding content.
    if (panelCenter && SLIDE_SOURCES.length > 0) {{
      panelCenter.setAttribute('data-state', 'active');
    }}
    var rows = document.querySelectorAll('.finding-row, .priority-ref-row');
    for (var i = 0; i < rows.length; i++) {{
      rows[i].classList.toggle('selected', rows[i].getAttribute('data-fid') === fid);
    }}
    var cards = document.querySelectorAll('.detail-card');
    for (var j = 0; j < cards.length; j++) {{
      cards[j].classList.toggle('visible', cards[j].getAttribute('data-fid') === fid);
    }}
    if (detailEmpty) detailEmpty.style.display = 'none';
    // Hotspot — only the SELECTED finding's hotspot is visible, per Dan's
    // "nothing on the screenshot until a finding is clicked" guidance.
    var hotspots = document.querySelectorAll('.hotspot');
    for (var k = 0; k < hotspots.length; k++) {{
      hotspots[k].classList.toggle('selected', hotspots[k].getAttribute('data-fid') === fid);
    }}
    var activeHotspot = document.querySelector('.hotspot.selected');
    if (activeHotspot) {{
      var hs = parseInt(activeHotspot.getAttribute('data-slide'), 10);
      if (!isNaN(hs) && hs !== slideIdx) setSlide(hs);
    }} else {{
      // Finding without a hotspot (head-scoped / absence). Still jump to
      // slide 0 so the user sees the hero as context rather than whatever
      // slide they were on before.
      if (slideIdx !== 0) setSlide(0);
    }}
    // Render the animated callout tooltip near the selected hotspot.
    renderReviewEffects(fid, activeHotspot);
    renderCallout(fid, activeHotspot);
    var row = document.querySelector('.finding-row[data-fid="' + cssEscape(fid) + '"]');
    if (row) {{
      var parent = row.closest('.cluster-card');
      if (parent && !parent.classList.contains('expanded')) parent.classList.add('expanded');
      try {{ row.scrollIntoView({{ block: 'nearest', behavior: 'smooth' }}); }} catch (e) {{}}
    }}
  }}

  function clampNumber(value, min, max) {{
    var n = Number(value);
    if (!isFinite(n)) n = min;
    if (n < min) return min;
    if (n > max) return max;
    return n;
  }}

  function normalizeEffectRect(rect) {{
    if (!rect) return null;
    var x = clampNumber(rect.x_pct, 0, 100);
    var y = clampNumber(rect.y_pct, 0, 100);
    var w = clampNumber(rect.w_pct, 0, 100 - x);
    var h = clampNumber(rect.h_pct, 0, 100 - y);
    if (w <= 0 || h <= 0) return null;
    return {{ x: x, y: y, w: w, h: h }};
  }}

  function hotspotRectPct(hotspotEl) {{
    if (!hotspotEl || !mainSlide) return null;
    var slideRect = mainSlide.getBoundingClientRect();
    var hotRect = hotspotEl.getBoundingClientRect();
    if (!slideRect.width || !slideRect.height || !hotRect.width || !hotRect.height) return null;
    return {{
      x: clampNumber(((hotRect.left - slideRect.left) / slideRect.width) * 100, -25, 125),
      y: clampNumber(((hotRect.top - slideRect.top) / slideRect.height) * 100, -25, 125),
      w: clampNumber((hotRect.width / slideRect.width) * 100, 0.2, 150),
      h: clampNumber((hotRect.height / slideRect.height) * 100, 0.2, 150)
    }};
  }}

  function reviewStyleHas(hotspotEl, token) {{
    if (!hotspotEl) return false;
    var raw = hotspotEl.getAttribute('data-review-style') || '';
    return raw.split(/\\s+/).indexOf(token) !== -1;
  }}

  function safeMaskId(seed) {{
    return String(seed || 'effect').replace(/[^a-z0-9_-]/gi, '-');
  }}

  function dimMaskHtml(rect, opacity, seed, shape) {{
    if (!rect) return '';
    var op = clampNumber(opacity, 0, 0.85);
    var id = 'review-dim-' + safeMaskId(seed) + '-' + slideIdx;
    var cutout = '';
    if (shape === 'ellipse') {{
      cutout = '<ellipse cx=\"' + (rect.x + rect.w / 2).toFixed(3) + '%\" cy=\"' + (rect.y + rect.h / 2).toFixed(3) + '%\" rx=\"' + Math.max(rect.w / 2, 0.2).toFixed(3) + '%\" ry=\"' + Math.max(rect.h / 2, 0.2).toFixed(3) + '%\" fill=\"black\" />';
    }} else {{
      cutout = '<rect x=\"' + rect.x.toFixed(3) + '%\" y=\"' + rect.y.toFixed(3) + '%\" width=\"' + rect.w.toFixed(3) + '%\" height=\"' + rect.h.toFixed(3) + '%\" rx=\"1.2%\" fill=\"black\" />';
    }}
    return '<svg class=\"review-dim-mask\" viewBox=\"0 0 100 100\" preserveAspectRatio=\"none\">' +
      '<defs><mask id=\"' + id + '\"><rect x=\"0\" y=\"0\" width=\"100\" height=\"100\" fill=\"white\" />' + cutout + '</mask></defs>' +
      '<rect x=\"0\" y=\"0\" width=\"100\" height=\"100\" fill=\"rgba(0,0,0,' + op.toFixed(3) + ')\" mask=\"url(#' + id + ')\" />' +
      '</svg>';
  }}

  function regionStyle(rect) {{
    return 'left:' + rect.x.toFixed(3) + '%;top:' + rect.y.toFixed(3) + '%;width:' + rect.w.toFixed(3) + '%;height:' + rect.h.toFixed(3) + '%;';
  }}

  function dimRegionHtml(effect, idx) {{
    var rect = normalizeEffectRect(effect.rect);
    if (!rect) return '';
    var op = clampNumber(effect.opacity, 0, 0.85);
    return '<div class=\"review-dim-region\" style=\"' + regionStyle(rect) + '--review-dim-opacity:' + op.toFixed(3) + ';\"></div>';
  }}

  function blurPieceHtml(rect, radius) {{
    if (!rect || rect.w <= 0 || rect.h <= 0) return '';
    return '<div class=\"review-blur-piece\" style=\"' + regionStyle(rect) + '--review-blur-radius:' + radius.toFixed(2) + 'px;\"></div>';
  }}

  function blurEffectHtml(effect) {{
    var rect = normalizeEffectRect(effect.rect);
    if (!rect) return '';
    var strength = clampNumber(effect.strength_pct, 1, 20);
    var radius = clampNumber(effect.radius_px, 0, 18) || strength * 1.6;
    if ((effect.mode || 'inside') === 'outside') {{
      var pieces = [
        {{ x: 0, y: 0, w: 100, h: rect.y }},
        {{ x: 0, y: rect.y + rect.h, w: 100, h: Math.max(0, 100 - rect.y - rect.h) }},
        {{ x: 0, y: rect.y, w: rect.x, h: rect.h }},
        {{ x: rect.x + rect.w, y: rect.y, w: Math.max(0, 100 - rect.x - rect.w), h: rect.h }}
      ];
      return pieces.map(function(piece) {{ return blurPieceHtml(piece, radius); }}).join('') +
        '<div class=\"review-blur-focus\" style=\"' + regionStyle(rect) + '\"></div>';
    }}
    return '<div class=\"review-blur-piece\" style=\"' + regionStyle(rect) + '--review-blur-radius:' + radius.toFixed(2) + 'px;\"></div>';
  }}

  function renderReviewEffects(fid, hotspotEl) {{
    if (!reviewEffectLayer) return;
    var f = findingByFid[fid];
    if (!f) {{
      reviewEffectLayer.innerHTML = '';
      return;
    }}
    var activeHotspot = hotspotEl || document.querySelector('.hotspot.selected');
    var effects = Array.isArray(f.review_effects) ? f.review_effects : [];
    var html = [];
    var hasOwnerDimMask = false;
    for (var i = 0; i < effects.length; i++) {{
      var effect = effects[i] || {{}};
      if (Number(effect.slide) !== slideIdx || effect.hidden === true) continue;
      if (effect.type === 'dim') {{
        if (effect.rect) {{
          html.push(dimRegionHtml(effect, i));
        }} else {{
          var rect = hotspotRectPct(activeHotspot);
          var shape = activeHotspot && activeHotspot.classList.contains('hotspot-ellipse') ? 'ellipse' : 'rect';
          html.push(dimMaskHtml(rect, effect.opacity == null ? 0.35 : effect.opacity, fid + '-' + i, shape));
          hasOwnerDimMask = true;
        }}
      }} else if (effect.type === 'blur') {{
        html.push(blurEffectHtml(effect));
      }}
    }}
    if (!hasOwnerDimMask && reviewStyleHas(activeHotspot, 'spotlight')) {{
      var spotRect = hotspotRectPct(activeHotspot);
      var spotShape = activeHotspot && activeHotspot.classList.contains('hotspot-ellipse') ? 'ellipse' : 'rect';
      html.unshift(dimMaskHtml(spotRect, 0.28, fid + '-spotlight', spotShape));
    }}
    reviewEffectLayer.innerHTML = html.join('');
  }}

  function clearReviewEffects() {{
    if (reviewEffectLayer) reviewEffectLayer.innerHTML = '';
  }}

  function renderCallout(fid, hotspotEl) {{
    if (!callout) return;
    var f = findingByFid[fid];
    if (!f) {{ hideCallout(); return; }}
    var sev = (f.priority || 'MEDIUM').toLowerCase();
    var title = f.review_callout_title || f.title || '(untitled finding)';
    var rec = (f.review_callout_body || f.recommendation || '').trim();
    if (rec.length > 160) rec = rec.slice(0, 160).replace(/[,;:.\s]+$/, '') + '\u2026';
    // Prefer the cluster-prefix short_code (e.g. "VC-84") so the callout
    // matches the sidebar's finding-id label format. Fall back to the
    // canonical F-NN slice if short_code wasn't pre-computed.
    var fidShort = f.short_code || (f.fid || fid).split('/').pop();
    callout.innerHTML =
      '<div class="callout-head">' +
        '<span class="callout-id">' + esc(fidShort) + '</span>' +
        '<span class="callout-sev ' + esc(sev) + '">' + esc(f.priority || 'MEDIUM') + '</span>' +
      '</div>' +
      '<div class="callout-title">' + esc(title) + '</div>' +
      (rec ? '<div class="callout-rec">\u2192 ' + esc(rec) + '</div>' : '');
    callout.setAttribute('data-visible', 'true');
    callout.setAttribute('aria-hidden', 'false');
    if (f.review_callout_color && /^#[0-9a-fA-F]{{3}}([0-9a-fA-F]{{3}})?$/.test(f.review_callout_color)) {{
      callout.style.setProperty('--callout-accent', f.review_callout_color);
    }} else {{
      callout.style.removeProperty('--callout-accent');
    }}
    // Call positionCallout AFTER making the callout visible — getBoundingClientRect
    // returns 0/0/0/0 for display:none elements, and positionCallout's clamp
    // math (min=16, max=callRect.height-16) would force pointerTop to -16px,
    // putting the leader arrow above the callout's top where it gets clipped
    // by screenshot-wrapper's overflow:hidden. This was the "arrow goes to
    // the wrong place on first click" bug; subsequent clicks worked because
    // the callout was already visible from the previous render.
    if (f.review_callout_position) {{
      positionReviewCallout(f, hotspotEl);
    }} else {{
      positionCallout(hotspotEl);
    }}
  }}

  function positionCallout(hotspotEl) {{
    if (!callout) return;
    if (originalCalloutParent && callout.parentElement !== originalCalloutParent) {{
      originalCalloutParent.appendChild(callout);
    }}
    callout.classList.remove('review-positioned');
    callout.style.position = '';
    callout.style.left = '';
    callout.style.top = '';
    callout.style.width = '';
    callout.style.minWidth = '';
    callout.style.maxWidth = '';
    callout.style.removeProperty('--callout-scale');
    // The callout is a flex sibling of the screenshot-stage, so horizontal
    // position is handled by CSS. We only need to align the leader arrow
    // on the callout's left edge with the vertical center of the hotspot.
    setCalloutArrow('left', hotspotEl);
  }}

  function clampNumber(value, min, max, fallback) {{
    var n = Number(value);
    if (!Number.isFinite(n)) n = fallback;
    if (n < min) return min;
    if (n > max) return max;
    return n;
  }}

  function normalizeCalloutAnchor(value) {{
    var anchor = String(value || 'auto').toLowerCase();
    return ['auto', 'left', 'right', 'top', 'bottom'].indexOf(anchor) >= 0 ? anchor : 'auto';
  }}

  function resolveCalloutAnchor(value, hotspotEl) {{
    var anchor = normalizeCalloutAnchor(value);
    if (anchor !== 'auto') return anchor;
    if (!callout || !hotspotEl) return 'left';
    var callRect = callout.getBoundingClientRect();
    var hRect = hotspotEl.getBoundingClientRect();
    var callCenterX = callRect.left + callRect.width / 2;
    var callCenterY = callRect.top + callRect.height / 2;
    var hotCenterX = hRect.left + hRect.width / 2;
    var hotCenterY = hRect.top + hRect.height / 2;
    var dx = hotCenterX - callCenterX;
    var dy = hotCenterY - callCenterY;
    if (Math.abs(dx) > Math.abs(dy)) return dx < 0 ? 'left' : 'right';
    return dy < 0 ? 'top' : 'bottom';
  }}

  function setCalloutArrow(value, hotspotEl) {{
    if (!callout) return;
    var anchor = resolveCalloutAnchor(value, hotspotEl);
    callout.classList.remove('callout-arrow-left', 'callout-arrow-right', 'callout-arrow-top', 'callout-arrow-bottom');
    callout.classList.add('callout-arrow-' + anchor);
    callout.setAttribute('data-arrow', anchor);
    callout.style.setProperty('--pointer-top', '28px');
    callout.style.setProperty('--pointer-left', '28px');
    if (!hotspotEl) return;
    var callRect = callout.getBoundingClientRect();
    var hRect = hotspotEl.getBoundingClientRect();
    if (anchor === 'left' || anchor === 'right') {{
      var pointerTop = (hRect.top + hRect.height / 2) - callRect.top;
      var minTop = 16;
      var maxTop = Math.max(minTop, callRect.height - 16);
      callout.style.setProperty('--pointer-top', clampNumber(pointerTop, minTop, maxTop, 28) + 'px');
      return;
    }}
    var pointerLeft = (hRect.left + hRect.width / 2) - callRect.left;
    var minLeft = 16;
    var maxLeft = Math.max(minLeft, callRect.width - 16);
    callout.style.setProperty('--pointer-left', clampNumber(pointerLeft, minLeft, maxLeft, 28) + 'px');
  }}

  function positionReviewCallout(f, hotspotEl) {{
    if (!callout || !screenshotWrapper || !mainSlide || !f.review_callout_position) {{
      positionCallout(hotspotEl);
      return;
    }}
    var pos = f.review_callout_position;
    var x = clampNumber(pos.x_pct, -80, 170, 0);
    var y = clampNumber(pos.y_pct, -40, 140, 0);
    var w = clampNumber(pos.w_pct, 12, 100, 22);
    var scale = clampNumber(pos.scale_pct, 70, 180, 100);
    if (callout.parentElement !== mainSlide) {{
      mainSlide.appendChild(callout);
    }}
    callout.classList.add('review-positioned');
    callout.style.position = 'absolute';
    callout.style.left = x + '%';
    callout.style.top = y + '%';
    callout.style.width = w + '%';
    callout.style.minWidth = '180px';
    callout.style.maxWidth = 'none';
    callout.style.setProperty('--callout-scale', String(scale / 100));
    setCalloutArrow(pos.anchor, hotspotEl);
  }}

  function hideCallout() {{
    if (!callout) return;
    callout.removeAttribute('data-visible');
    callout.setAttribute('aria-hidden', 'true');
  }}

  function esc(s) {{
    var div = document.createElement('div');
    div.textContent = s == null ? '' : String(s);
    return div.innerHTML;
  }}
  window.selectFinding = selectFinding;

  function cssEscape(s) {{
    if (window.CSS && CSS.escape) return CSS.escape(s);
    return String(s).replace(/[^a-zA-Z0-9_\-]/g, function(ch) {{ return '\\' + ch; }});
  }}

  function clearSelection() {{
    selectedFid = null;
    if (panelCenter) panelCenter.setAttribute('data-state', 'empty');
    var rows = document.querySelectorAll('.finding-row.selected, .priority-ref-row.selected');
    for (var i = 0; i < rows.length; i++) rows[i].classList.remove('selected');
    var cards = document.querySelectorAll('.detail-card.visible');
    for (var j = 0; j < cards.length; j++) cards[j].classList.remove('visible');
    var hotspots = document.querySelectorAll('.hotspot.selected');
    for (var k = 0; k < hotspots.length; k++) hotspots[k].classList.remove('selected');
    if (detailEmpty) detailEmpty.style.display = '';
    hideCallout();
    clearReviewEffects();
  }}
  window.clearSelection = clearSelection;

  // Reposition callout on window resize so it stays anchored to the hotspot.
  window.addEventListener('resize', function() {{
    if (!selectedFid) return;
    var hotspotEl = document.querySelector('.hotspot.selected');
    var f = findingByFid[selectedFid];
    if (f && f.review_callout_position) positionReviewCallout(f, hotspotEl);
    else positionCallout(hotspotEl);
    renderReviewEffects(selectedFid, hotspotEl);
  }});

  // ----- Brief management --------------------------------------------------
  function persistBrief() {{
    try {{
      var arr = [];
      brief.forEach(function(id) {{ arr.push(id); }});
      localStorage.setItem(STORAGE_KEY, JSON.stringify(arr));
    }} catch (e) {{ /* session-only */ }}
    updateBriefUI();
  }}

  function toggleBrief(fid) {{
    if (brief.has(fid)) brief.delete(fid);
    else brief.add(fid);
    persistBrief();
  }}
  window.toggleBrief = toggleBrief;

  function clearBrief() {{
    brief.clear();
    persistBrief();
  }}
  window.clearBrief = clearBrief;

  function updateBriefUI() {{
    var n = brief.size;
    if (briefCount) briefCount.textContent = String(n);
    if (briefCountBottom) briefCountBottom.textContent = String(n);
    if (exportBtn) exportBtn.disabled = (n === 0);
    if (exportBtnBottom) exportBtnBottom.disabled = (n === 0);
    var allRows = document.querySelectorAll('.finding-row, .priority-ref-row');
    for (var i = 0; i < allRows.length; i++) {{
      var fid = allRows[i].getAttribute('data-fid');
      if (fid) allRows[i].classList.toggle('in-brief', brief.has(fid));
    }}
    var btns = document.querySelectorAll('.detail-btn-add');
    for (var j = 0; j < btns.length; j++) {{
      var bfid = btns[j].getAttribute('data-fid');
      if (!bfid) continue;
      var inBrief = brief.has(bfid);
      btns[j].classList.toggle('added', inBrief);
      btns[j].textContent = inBrief ? 'Added to brief \u2713' : 'Add to brief';
    }}
  }}

  function toggleSelectAllVisible() {{
    var rows = Array.prototype.slice.call(document.querySelectorAll('.panel-scroll:not([hidden]) .finding-row, .panel-scroll:not([hidden]) .priority-ref-row'));
    var fids = [];
    for (var i = 0; i < rows.length; i++) {{
      var f = rows[i].getAttribute('data-fid');
      if (f) fids.push(f);
    }}
    if (!fids.length) return;
    var allIn = fids.every(function(fid) {{ return brief.has(fid); }});
    if (allIn) fids.forEach(function(fid) {{ brief.delete(fid); }});
    else fids.forEach(function(fid) {{ brief.add(fid); }});
    persistBrief();
  }}
  window.toggleSelectAllVisible = toggleSelectAllVisible;

  function toggleSelectAllHigh() {{
    // Collect every CRITICAL + HIGH finding across all clusters (not scoped
    // to the visible tab — the whole point of this button is the global
    // "give me all the urgent ones" shortcut).
    var urgent = [];
    for (var i = 0; i < FINDINGS.length; i++) {{
      var p = (FINDINGS[i].priority || 'MEDIUM').toUpperCase();
      if (p === 'CRITICAL' || p === 'HIGH') urgent.push(FINDINGS[i].fid);
    }}
    if (!urgent.length) return;
    var allIn = urgent.every(function(fid) {{ return brief.has(fid); }});
    if (allIn) urgent.forEach(function(fid) {{ brief.delete(fid); }});
    else urgent.forEach(function(fid) {{ brief.add(fid); }});
    persistBrief();
  }}
  window.toggleSelectAllHigh = toggleSelectAllHigh;

  // ----- Export modal ------------------------------------------------------
  function openExport() {{
    if (brief.size === 0) return;
    buildExportPreview();
    if (modal) modal.classList.add('visible');
  }}
  function closeExport() {{ if (modal) modal.classList.remove('visible'); }}
  window.openExport = openExport;
  window.closeExport = closeExport;

  function switchExportFormat(fmt) {{
    exportFormat = fmt;
    var tabs = document.querySelectorAll('.export-tab');
    for (var i = 0; i < tabs.length; i++) {{
      tabs[i].classList.toggle('active', tabs[i].getAttribute('data-format') === fmt);
    }}
    buildExportPreview();
  }}
  window.switchExportFormat = switchExportFormat;

  function buildExportPreview() {{
    if (!exportPreview) return;
    var selected = [];
    brief.forEach(function(id) {{ selected.push(id); }});
    if (exportFormat === 'bullets') exportPreview.value = buildBulletedExport(selected);
    else exportPreview.value = buildMarkdownExport(selected);
  }}

  function buildBulletedExport(fids) {{
    if (!fids.length) return 'No findings in brief.';
    var byCluster = {{}};
    fids.forEach(function(fid) {{
      var f = findingByFid[fid];
      if (!f) return;
      var c = f.cluster || 'uncategorized';
      if (!byCluster[c]) byCluster[c] = [];
      byCluster[c].push(f);
    }});
    var lines = ['# Remediation Brief', ''];
    lines.push('- ' + fids.length + ' findings selected across ' + Object.keys(byCluster).length + ' clusters.');
    lines.push('');
    Object.keys(byCluster).sort().forEach(function(cluster) {{
      lines.push('## ' + cluster);
      byCluster[cluster].sort(function(a, b) {{ return a.cluster_index - b.cluster_index; }}).forEach(function(f) {{
        lines.push('- **' + f.fid + '** (' + (f.priority || 'MEDIUM') + ') \u2014 ' + (f.title || '(no title)'));
        if (f.recommendation) lines.push('  - Fix: ' + f.recommendation);
      }});
      lines.push('');
    }});
    return lines.join('\n');
  }}

  function buildMarkdownExport(fids) {{
    if (!fids.length) return 'No findings in brief.';
    var fidSet = {{}};
    fids.forEach(function(fid) {{ fidSet[fid] = true; }});
    var parts = EXPORT_MARKDOWN.filter(function(m) {{ return fidSet[m.fid]; }});
    if (!parts.length) return 'No matching findings found in the audit.md mirror.';
    var header = '# Remediation Brief (audit.md mirror)\n\n' +
                 '- ' + parts.length + ' findings selected\n\n---\n\n';
    return header + parts.map(function(p) {{ return p.block; }}).join('\n\n---\n\n');
  }}

  function copyExport() {{
    if (!exportPreview) return;
    var text = exportPreview.value;
    function onSuccess() {{
      var btn = document.querySelector('.modal-foot .btn-primary');
      if (btn) {{
        var orig = btn.textContent;
        btn.textContent = 'Copied \u2713';
        setTimeout(function() {{ btn.textContent = orig; }}, 1400);
      }}
    }}
    if (navigator.clipboard && navigator.clipboard.writeText) {{
      navigator.clipboard.writeText(text).then(onSuccess).catch(function() {{
        exportPreview.select();
        try {{ document.execCommand('copy'); onSuccess(); }} catch (e) {{}}
      }});
    }} else {{
      exportPreview.select();
      try {{ document.execCommand('copy'); onSuccess(); }} catch (e) {{}}
    }}
  }}
  window.copyExport = copyExport;

  // ----- Keyboard ---------------------------------------------------------
  function moveFindingSelection(direction) {{
    var visiblePanel = document.querySelector('.panel-scroll:not([hidden])');
    if (!visiblePanel) return;
    var rows = Array.prototype.slice.call(
      visiblePanel.querySelectorAll('.finding-row[data-fid], .priority-ref-row[data-fid]')
    );
    if (!rows.length) return;
    var currentIdx = -1;
    for (var i = 0; i < rows.length; i++) {{
      if (rows[i].getAttribute('data-fid') === selectedFid) {{
        currentIdx = i;
        break;
      }}
    }}
    var nextIdx;
    if (currentIdx === -1) {{
      nextIdx = direction > 0 ? 0 : rows.length - 1;
    }} else {{
      nextIdx = (currentIdx + direction + rows.length) % rows.length;
    }}
    var nextFid = rows[nextIdx].getAttribute('data-fid');
    if (nextFid) selectFinding(nextFid);
  }}

  document.addEventListener('keydown', function(e) {{
    var t = e.target;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA')) return;
    if (modal && modal.classList.contains('visible')) {{
      if (e.key === 'Escape') {{ closeExport(); return; }}
    }}
    if (e.key === 'ArrowLeft' && !e.metaKey && !e.ctrlKey) prevSlide();
    else if (e.key === 'ArrowRight' && !e.metaKey && !e.ctrlKey) nextSlide();
    else if (e.key === 'ArrowDown' && !e.metaKey && !e.ctrlKey && !e.altKey) {{
      e.preventDefault();
      moveFindingSelection(1);
    }}
    else if (e.key === 'ArrowUp' && !e.metaKey && !e.ctrlKey && !e.altKey) {{
      e.preventDefault();
      moveFindingSelection(-1);
    }}
    else if (e.key === 'Escape') clearSelection();
  }});

  // ----- Delegated click handler ------------------------------------------
  document.addEventListener('click', function(e) {{
    var thumb = e.target.closest('.thumb');
    if (thumb) {{
      var idx = Array.prototype.indexOf.call(thumb.parentNode.children, thumb);
      if (idx >= 0) setSlide(idx);
      return;
    }}
    var row = e.target.closest('.finding-row, .priority-ref-row');
    if (row && row.hasAttribute('data-fid')) {{
      if (e.target.closest('.finding-check') || e.target.closest('.priority-ref-check')) {{
        e.stopPropagation();
        toggleBrief(row.getAttribute('data-fid'));
        return;
      }}
      selectFinding(row.getAttribute('data-fid'));
      return;
    }}
    var hotspot = e.target.closest('.hotspot');
    if (hotspot && hotspot.hasAttribute('data-fid')) {{
      switchTab('clusters');
      selectFinding(hotspot.getAttribute('data-fid'));
      return;
    }}
    var addBtn = e.target.closest('.detail-btn-add');
    if (addBtn && addBtn.hasAttribute('data-fid')) {{
      toggleBrief(addBtn.getAttribute('data-fid'));
      return;
    }}
    var queueBtn = e.target.closest('.detail-btn-editor-queue');
    if (queueBtn && queueBtn.hasAttribute('data-fid')) {{
      queueForEditor(queueBtn.getAttribute('data-fid'));
      return;
    }}
    var openEditorBtn = e.target.closest('.detail-btn-editor-open');
    if (openEditorBtn && openEditorBtn.hasAttribute('data-fid')) {{
      openEditor(openEditorBtn.getAttribute('data-fid'));
      return;
    }}
    var skipBtn = e.target.closest('.detail-btn-skip');
    if (skipBtn) {{ clearSelection(); return; }}
    var clusterHead = e.target.closest('.cluster-head');
    if (clusterHead) {{
      var card = clusterHead.closest('.cluster-card');
      if (card) card.classList.toggle('expanded');
      return;
    }}
  }});

  // Initial render — prime the first slide image but leave the center
  // panel in its empty-state until the user clicks a finding. setSlide(0)
  // populates mainImg.src so that when the user clicks into a finding,
  // the screenshot is already there and appears instantly.
  if (SLIDE_SOURCES.length) setSlide(0);
  updateBriefUI();
  updateEditorQueueUI();
}})();
"""
