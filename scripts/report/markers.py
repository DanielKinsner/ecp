"""Marker auto-mapping and position computation.

Design 3 tiered resolver (Track B). Finding.ELEMENT strings resolve to
baton element indices (and from there to pixel coordinates) via a
five-tier cascade orchestrated by ``auto_map_markers``:

    Tier 1  element_id      Exact id / element_id field on baton element.
                              Opportunistic — fires when baton populates
                              id (rare today; the forward-compat hook for
                              the Design 1 element_id registry).

    Tier 2  exact selector   tag.class, [class*="..."], bare-ID against
                              class-token or stored selector. Strict —
                              returns None on miss (does NOT fuzzy).

    Tier 3  region slug      Section-slug keyword match against baton
                              sections[]. Handled in ``auto_map_markers``
                              because it yields a SLIDE, not an element
                              index. Promoted above fuzzy (Design 3) so
                              ELEMENTs like "above-fold area" route to
                              the hero section instead of getting
                              keyword-matched to a random element that
                              happens to share the substring "fold".

    Tier 4  fuzzy keyword    Last-resort element guess from keyword
                              overlap (tag + class; text field EXCLUDED
                              to reduce false positives). Threshold
                              tightened from 50% to 2+ matches.

    Tier 5  head/absence     Reserved slots on first/last slide for
                              head-scoped and site-wide-absence findings
                              that can't be pinned to any element.

Tier 1 + Tier 2 live inside ``match_element_to_baton`` (strict matcher,
no fuzzy fallback). Tier 4 is a separate public function
``fuzzy_match_element`` so ``auto_map_markers`` can call it AFTER the
Tier 3 section attempt. This split is what implements the Design 3
preference "section before fuzzy" — a pragmatic correctness win
without requiring a full element_id registry refactor.

Bare-ID selectors (``#foo-bar``) are special: if Tier 1 + Tier 2 both
miss, ``auto_map_markers`` skips Tier 4 entirely. Rationale from Fix 2:
a bare ID names a specific element, and fuzzy-matching "cart" to a
header cart dropdown when the finding wanted the Add-to-Cart button
is actively misleading. Return None honestly and route to fallback
or drop the marker.
"""

import logging
import re

from .geometry import element_rect_css, element_rect_raw, infer_element_coord_scale, viewport_dpr

log = logging.getLogger(__name__)


_BARE_ID_RE = re.compile(r"^#([a-z0-9_-]+)$")


def _is_bare_id_selector(sel):
    """Return True when ``sel`` is a bare ID selector like ``#foo-bar``.

    Callers use this to gate the Tier 4 fuzzy fallback — bare IDs must
    NOT fuzzy-fall-through because they name a specific element and a
    keyword collision paints the wrong hotspot. See Fix 2.
    """
    return bool(_BARE_ID_RE.match(sel))


def _match_element_id(sel, elements):
    """Tier 1 — exact match against baton element.id / element.element_id.

    Only fires for bare-ID selectors (``#foo``). Returns the element
    index or None. Forward-compat hook for Design 1's element_id
    registry: when baton elements eventually carry stable ``element_id``
    values, auditor ELEMENT selectors of the form ``#el-042`` resolve
    here with zero fuzzy risk.

    Today baton elements rarely carry ``id`` fields, so Tier 1 mostly
    returns None and Tier 2 does the work. That's fine — Tier 1 costs
    nothing when it misses.
    """
    m = _BARE_ID_RE.match(sel)
    if not m:
        return None
    id_part = m.group(1)
    for i, el in enumerate(elements):
        if (el.get("id") or "").lower() == id_part:
            return i
        # Forward-compat with Design 1: baton may eventually carry
        # element_id separately from id.
        if (el.get("element_id") or "").lower() == id_part:
            return i
    return None


def _match_exact_selector(sel, elements):
    """Tier 2 — exact CSS selector match (direct, tag.class, attr, bare-ID).

    Returns element index or None. Does NOT fuzzy. For bare-ID selectors
    that miss Tier 1, also tries class-token match and stored-selector
    equality before returning None (preserves Fix 2 behavior).
    """
    bare_id_only = _is_bare_id_selector(sel)

    # Direct selector + tag.class match (shared loop)
    for i, el in enumerate(elements):
        el_class = (el.get("class") or "").lower()
        el_tag = (el.get("tag") or "").lower()
        el_selector = (el.get("selector") or "").lower()

        if sel == el_selector:
            return i

        # Skip tag.class parse when the selector is a bare ID — "#foo"
        # contains no "." so this branch never triggers, but the check
        # documents intent.
        if not bare_id_only and "." in sel:
            parts = sel.split(".", 1)
            tag_part = parts[0].strip()
            class_part = parts[1].strip()
            if (not tag_part or tag_part == el_tag) and class_part in el_class:
                return i

    # Bare-ID: also accept class-token match (Fix 2) once direct/tag.class
    # failed. Still strict — returns None without falling through to fuzzy.
    if bare_id_only:
        id_part = _BARE_ID_RE.match(sel).group(1)
        for i, el in enumerate(elements):
            if id_part in (el.get("class") or "").lower().split():
                return i
        return None

    # Attribute selector (e.g., [class*="newsletter"])
    attr_match = re.match(r'\[class\*=["\']([^"\']+)["\']\]', sel)
    if attr_match:
        keyword = attr_match.group(1).lower()
        for i, el in enumerate(elements):
            if keyword in (el.get("class") or "").lower():
                return i

    return None


def fuzzy_match_element(element_selector, elements):
    """Tier 4 — last-resort keyword fuzzy match.

    Extracts 3-char+ keywords from the selector, scores each baton
    element by keyword overlap in ``tag + class``, returns the
    highest-scoring element whose score clears the tightened threshold.

    Threshold (tightened from the pre-Design-3 Strategy 3 50% cutoff):
        1 keyword  -> requires 1 match (100%)
        2+ keywords -> requires at least 2 matches

    The old ``max(1, len // 2)`` threshold accepted a coinflip on
    2-keyword selectors. Tightening reduces false positives on the
    descriptive selectors auditors often write (``"footer menu link"``
    used to match any element with "menu" in its class, which was
    frequently wrong).

    Text field is deliberately excluded. Matching on el["text"] caused
    a different class of false positive: a finding about a button
    could match an ``<h1>`` whose text happens to mention "button".
    Restrict the search to structural metadata.

    Callers (currently only ``auto_map_markers``) should skip this
    function when ``_is_bare_id_selector(sel)`` — bare IDs name a
    specific element and must not fuzzy-fall-through. See Fix 2.
    """
    if not element_selector or not elements:
        return None
    sel = element_selector.strip().lower()
    keywords = re.findall(r"[a-z]{3,}", sel)
    if not keywords:
        return None

    if len(keywords) == 1:
        required = 1
    else:
        required = 2

    best_score = 0
    best_idx = None
    for i, el in enumerate(elements):
        el_class = (el.get("class") or "").lower()
        el_tag = (el.get("tag") or "").lower()
        # Text field intentionally excluded — see docstring.
        combined = f"{el_tag} {el_class}"
        score = sum(1 for kw in keywords if kw in combined)
        if score > best_score and score >= required:
            best_score = score
            best_idx = i
    return best_idx


def match_element_to_baton(element_selector, elements):
    """Strict tiered element match — Tier 1 (element_id) + Tier 2 (exact selector).

    Returns the baton element index when a strict match exists, or None
    otherwise. Does NOT fuzzy-fall-through. Callers that want fuzzy
    behavior should invoke ``fuzzy_match_element`` separately (see
    ``auto_map_markers`` for the canonical orchestration).

    Split from the pre-Design-3 four-strategy cascade: strict and fuzzy
    now live in separate functions so ``auto_map_markers`` can insert
    Tier 3 (section-slug routing) between them. Bare-ID selectors still
    refuse to fuzzy-fall-through (Fix 2 behavior preserved at the
    orchestration layer).
    """
    if not element_selector or not elements:
        return None

    sel = element_selector.strip().lower()

    # Tier 1 — opportunistic element_id lookup. Bare-ID only; other
    # selector shapes fall straight through to Tier 2.
    idx = _match_element_id(sel, elements)
    if idx is not None:
        return idx

    # Tier 2 — exact CSS selector family (direct, tag.class, bare-ID
    # class-token, attribute). Strict — returns None on miss.
    return _match_exact_selector(sel, elements)


_HEAD_SCOPED_HINTS = (
    "head >", "head>", "<head", "meta[", "meta name", "meta property",
    "link[rel", "link rel", "canonical", "application/ld+json", "ld+json",
    "og:", "twitter:", "twitter-card", "schema", "structured data",
    "viewport", "<title", "title tag", "hreflang", "preconnect", "preload",
    "shipping service", "mainentity", "aggregaterating", "organization schema",
    "gtin/mpn", "gtin", "mpn", "merchantreturnpolicy", "itemlist",
)

_ABSENCE_HINTS = (
    "site-global", "site global", "site-wide", "sitewide", "dom scan",
    "dom-wide", "full dom", "zero instances", "no instances", " no cookie",
    " no loyalty", " no referral", " no return", " no warranty",
    " no guarantee", " no satisfaction", " no gdpr", " no bnpl",
    "missing on page", "not found in dom", "absent", " no h1 present",
    " (no h1", "no h1)", "page-level",
)


def _infer_element_coord_scale(elements, screenshots, viewport, dpr):
    """Infer whether baton element coordinates are CSS px or DPR-scaled px.

    Historically, different acquisition paths have emitted ``elements[]`` in
    two formats:
    - CSS pixels (x/y/width/height in viewport units)
    - DPR-scaled pixels (same values multiplied by viewport.dpr)

    Marker mapping uses screenshot ``scrollY`` metadata, which is always CSS px.
    If we compare DPR-scaled element ``y`` values directly against CSS scroll
    windows, hotspots collapse onto the wrong slide. We infer scale from the
    observed coordinate range relative to screenshot+viewport geometry:

    - return ``dpr`` when values clearly fit a DPR-scaled envelope
    - otherwise return ``1.0`` (treat as CSS px)
    """
    return infer_element_coord_scale(elements, screenshots, viewport, dpr)


def _classify_unmatched(element_selector: str, section_slug: str) -> str:
    """Return 'head', 'absence', or 'other' for findings with no element coords.

    Used by the v1.0.1 default-marker fallback to route unmatched findings to
    reserved positions on the first/last slide instead of dropping them silently.
    """
    haystack = f" {element_selector.lower()} | {section_slug.lower()} "
    if any(hint in haystack for hint in _HEAD_SCOPED_HINTS):
        return "head"
    if any(hint in haystack for hint in _ABSENCE_HINTS):
        return "absence"
    # Fall-back: treat clearly non-visual sections as absence too
    if section_slug.lower() in (
        "cookie-consent", "loyalty", "referral", "return-policy",
        "warranty-absence", "social-channels", "social-commerce",
        "value-proposition", "personalization", "cross-cultural",
        "mobile-specific",
    ):
        return "absence"
    return "other"


def auto_map_markers(findings, baton_data):
    """Automatically create marker mappings from findings by matching ELEMENT fields to baton elements.

    Returns a list of marker mapping dicts compatible with the manual markers.json format.

    Findings whose ELEMENT cannot be matched to a baton element rect AND whose
    SECTION keyword doesn't match any baton section are routed to reserved
    fallback slots on the first or last slide (v1.0.1 default-markers fix) —
    head-scoped findings pin to the first slide, site-wide absence findings
    pin to the last slide. This means head-tag and DOM-absence findings get
    a visible marker instead of being silently dropped.
    """
    elements = baton_data.get("elements", [])
    sections = baton_data.get("sections", [])
    screenshots = baton_data.get("screenshots", [])
    dpr = viewport_dpr(baton_data.get("viewport", {}))

    element_coord_scale = _infer_element_coord_scale(elements, screenshots, baton_data.get("viewport", {}), dpr)

    mappings = []
    # Track how many fallback markers have been placed on each slide so we
    # can stack them without overlapping.
    fallback_counts = {"head": 0, "absence": 0}

    viewport_h_css = float(baton_data.get("viewport", {}).get("height", 1080) or 1080)

    def _slide_for_element_y(elem_y):
        """Return slide index containing ``elem_y`` after scale normalization."""
        try:
            elem_y_css = float(elem_y) / element_coord_scale
        except (TypeError, ValueError, ZeroDivisionError):
            return None
        for si, ss in enumerate(screenshots):
            ss_scroll_css = ss.get("scrollY", 0) if isinstance(ss, dict) else 0
            if ss_scroll_css <= elem_y_css < ss_scroll_css + viewport_h_css:
                return si
        return None

    def _slide_for_section_slug(section_slug):
        """Tier 3: route SECTION slug to a slide via baton.sections[] label match.

        Returns slide index or None. Promoted above Tier 4 (fuzzy) so a
        finding with SECTION=``above-fold-content`` lands in the hero
        section instead of getting keyword-matched to a random element.
        """
        slug_lower = section_slug.lower()
        if not slug_lower:
            return None
        slug_words = [w for w in slug_lower.replace("-", " ").split() if len(w) >= 3]
        if not slug_words:
            return None
        for si, sec in enumerate(sections):
            if not isinstance(sec, dict):
                continue
            sec_label = (sec.get("label") or "").lower()
            sec_name = (sec.get("name") or "").lower()
            combined = f"{sec_label} {sec_name}"
            if any(w in combined for w in slug_words):
                # Prefer the section's declared screenshot_index (1-based)
                # over the sections-array position.
                ss_idx = sec.get("screenshot_index")
                if ss_idx is not None:
                    candidate = ss_idx - 1
                    if 0 <= candidate < len(screenshots):
                        return candidate
                    return None
                return si
        return None

    def _slides_for_cluster(cluster_slug):
        """Return ordered slide indices whose section metadata includes cluster_slug."""
        if not cluster_slug:
            return []
        wanted = str(cluster_slug).lower()
        out = []
        for sec in sections:
            if not isinstance(sec, dict):
                continue
            sec_clusters = sec.get("clusters") or []
            if any(str(c).lower() == wanted for c in sec_clusters):
                ss_idx = sec.get("screenshot_index")
                if ss_idx is None:
                    continue
                candidate = ss_idx - 1
                if 0 <= candidate < len(screenshots) and candidate not in out:
                    out.append(candidate)
        return out

    def _exact_selector_candidates(selector):
        """Return every exact-selector candidate index for ambiguity resolution."""
        if not selector:
            return []
        sel = selector.strip().lower()
        out = []

        # Mirror Tier 1 behavior for bare IDs.
        id_idx = _match_element_id(sel, elements)
        if id_idx is not None:
            return [id_idx]

        bare_id_only = _is_bare_id_selector(sel)
        for i, el in enumerate(elements):
            el_selector = (el.get("selector") or "").lower()
            el_class = (el.get("class") or "").lower()
            el_tag = (el.get("tag") or "").lower()
            if sel == el_selector and i not in out:
                out.append(i)
            if not bare_id_only and "." in sel:
                tag_part, class_part = sel.split(".", 1)
                tag_part = tag_part.strip()
                class_part = class_part.strip()
                if (not tag_part or tag_part == el_tag) and class_part in el_class and i not in out:
                    out.append(i)

        if bare_id_only:
            id_part = _BARE_ID_RE.match(sel).group(1)
            for i, el in enumerate(elements):
                tokens = (el.get("class") or "").lower().split()
                if id_part in tokens and i not in out:
                    out.append(i)
            return out

        attr_match = re.match(r'\[class\*=["\']([^"\']+)["\']\]', sel)
        if attr_match:
            keyword = attr_match.group(1).lower()
            for i, el in enumerate(elements):
                if keyword in (el.get("class") or "").lower() and i not in out:
                    out.append(i)
        return out

    def _choose_best_candidate(candidates, preferred_slides):
        """Pick the best candidate index using cluster/section slide context."""
        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]

        first_pref = preferred_slides[0] if preferred_slides else None

        def _score(idx):
            el = elements[idx]
            rect = element_rect_raw(el) or {"y": 0.0}
            slide = _slide_for_element_y(rect.get("y", 0))
            y_css = (rect.get("y", 0.0) or 0.0) / (element_coord_scale or 1.0)

            if preferred_slides:
                if slide in preferred_slides:
                    pref_rank = preferred_slides.index(slide)
                elif slide is not None:
                    pref_rank = len(preferred_slides) + abs(slide - first_pref)
                else:
                    pref_rank = len(preferred_slides) + 99
            else:
                pref_rank = 0

            # Tie-breaker: prefer lower on-page elements for repeated card
            # selectors, which avoids the chronic "first header-ish match"
            # behavior on long ecommerce pages.
            return (pref_rank, -y_css, idx)

        return sorted(candidates, key=_score)[0]

    for f in findings:
        idx = f["index"]
        # Cluster-local F-NN — what hotspots, callouts, and left-rail rows
        # all display. Keeping this cluster-local avoids list/callout mismatch.
        burn_number = f.get("cluster_index") or idx
        severity = (f.get("priority") or "medium").lower()
        element_selector = f.get("element", "")
        section_slug = f.get("section", "")
        cluster_slug = f.get("cluster", "")
        sel_lower = element_selector.strip().lower()

        section_slide = _slide_for_section_slug(section_slug)
        cluster_slides = _slides_for_cluster(cluster_slug)
        preferred_slides = []
        if section_slide is not None:
            preferred_slides.append(section_slide)
        for s in cluster_slides:
            if s not in preferred_slides:
                preferred_slides.append(s)

        # Design 3 tiered resolution:
        #   Tier 1+2 (match_element_to_baton) -> element coords
        #   Tier 3 (section slug) -> section-center coords
        #   Tier 4 (fuzzy_match_element) -> element coords, only when
        #                                   selector is not a bare ID
        #   Tier 5 (head/absence fallback) -> reserved slot
        baton_idx = match_element_to_baton(element_selector, elements)
        slide = None
        match_method = None

        # Resolve ambiguous exact-selector matches using section/cluster context.
        exact_candidates = _exact_selector_candidates(element_selector)
        if exact_candidates:
            chosen = _choose_best_candidate(exact_candidates, preferred_slides)
            if chosen is not None:
                baton_idx = chosen

        if baton_idx is not None:
            # Tier 1 or Tier 2 matched — pixel-precise element coords.
            elem_rect = element_rect_raw(elements[baton_idx]) or {}
            elem_y = elem_rect.get("y", 0)
            slide = _slide_for_element_y(elem_y)
            if slide is not None:
                match_method = "element-contextual" if len(exact_candidates) > 1 else "element"

        if slide is None:
            # Tier 3 — section slug routing. Tries before fuzzy so a
            # descriptive ELEMENT ("above-fold area") with a canonical
            # SECTION ("above-fold-content") lands in the right region
            # instead of getting keyword-matched to whatever element
            # shares a substring. Design 3 correctness > pixel precision.
            if section_slide is not None:
                slide = section_slide
                match_method = "section"

        if slide is None and sel_lower and not _is_bare_id_selector(sel_lower):
            # Tier 4 — fuzzy element match. Gated on non-bare-ID selector
            # per Fix 2: bare IDs name a specific element and MUST NOT
            # fall through to fuzzy, even when Tier 3 also missed.
            fuzzy_idx = fuzzy_match_element(element_selector, elements)
            if fuzzy_idx is not None:
                elem_rect = element_rect_raw(elements[fuzzy_idx]) or {}
                elem_y = elem_rect.get("y", 0)
                slide = _slide_for_element_y(elem_y)
                if slide is not None:
                    baton_idx = fuzzy_idx
                    match_method = "fuzzy"

        # Default-marker fallback: head-scoped → slide 0, absence → last slide
        fallback_role = None
        fallback_position = None
        if slide is None:
            klass = _classify_unmatched(element_selector, section_slug)
            if klass in ("head", "absence") and screenshots:
                # Route head-scoped findings to slide 0 (top-right stack)
                # and absence findings to the last slide (bottom-right stack).
                slide = 0 if klass == "head" else max(0, len(screenshots) - 1)
                match_method = f"fallback-{klass}"
                fallback_role = klass
                # Stack marker: each successive fallback marker shifts ~80px
                # down the right edge. Start at 8% from right edge, 10% down.
                stack_n = fallback_counts[klass]
                fallback_counts[klass] += 1
                if klass == "head":
                    y_pct = 6 + stack_n * 6   # top-down stack starting at 6%
                    x_pct = 92
                else:
                    y_pct = 94 - stack_n * 6  # bottom-up stack starting at 94%
                    x_pct = 92
                # Clamp to reasonable bounds so the stack doesn't walk off-slide
                y_pct = max(6, min(y_pct, 94))
                fallback_position = {"x_pct": x_pct, "y_pct": y_pct}
            else:
                log.warning(
                    "Finding #%d could not be matched to any slide (element=%r, section=%r). "
                    "Provide a --markers file for manual placement.",
                    idx, element_selector, section_slug,
                )

        mappings.append({
            "finding_index": idx,
            "burn_number": burn_number,
            "baton_element_index": baton_idx,
            "slide": slide,
            "match_method": match_method,
            "severity": severity,
            "fallback_role": fallback_role,
            "fallback_position": fallback_position,
        })

    return mappings


def compute_marker_positions(markers_mapping, baton_data):
    """Compute pixel positions for markers on screenshots."""
    elements = baton_data.get("elements", [])
    screenshots = baton_data.get("screenshots", [])
    sections = baton_data.get("sections", [])
    viewport = baton_data.get("viewport", {})
    dpr = viewport_dpr(viewport)
    element_coord_scale = _infer_element_coord_scale(elements, screenshots, viewport, dpr)
    # Fallback dimensions when viewport is missing — use canonical per-device
    # dimensions from contracts/device-semantics.md so a missing viewport
    # doesn't silently produce wrong-scale marker coordinates.
    _DEVICE_FALLBACKS = {
        "mobile": (390, 844, 3),
        "laptop": (1440, 900, 1),
        "desktop": (1920, 1080, 1),
    }
    device = (baton_data.get("device") or "laptop").lower()
    _fw, _fh, _fdpr = _DEVICE_FALLBACKS.get(device, _DEVICE_FALLBACKS["laptop"])
    try:
        default_nat_w = int(viewport.get("width") or _fw)
    except (ValueError, TypeError):
        default_nat_w = _fw
    try:
        default_nat_h = int(viewport.get("height") or _fh)
    except (ValueError, TypeError):
        default_nat_h = _fh

    slide_markers = {}

    for mapping in markers_mapping:
        finding_idx = mapping["finding_index"]
        # Number used by HTML hotspot overlays/callouts. Falls back to the
        # global index for legacy manual markers.json files.
        burn_number = mapping.get("burn_number") or finding_idx
        elem_idx = mapping.get("baton_element_index")
        slide = mapping.get("slide")
        if slide is None:
            # Unresolved mapping — skip marker placement
            continue
        severity = mapping.get("severity", "medium")

        if slide not in slide_markers:
            slide_markers[slide] = []

        # Fallback position from auto_map_markers (head-scoped / absence findings)
        fallback_pos = mapping.get("fallback_position")
        if fallback_pos is not None:
            # Compute pixel position from percentage for overlay placement.
            if isinstance(screenshots, list) and slide < len(screenshots):
                ss = screenshots[slide]
                nat_h = (
                    ss.get("naturalHeight")
                    or ss.get("height")
                    or default_nat_h
                ) if isinstance(ss, dict) else default_nat_h
                nat_w = (
                    ss.get("naturalWidth")
                    or ss.get("width")
                    or default_nat_w
                ) if isinstance(ss, dict) else default_nat_w
            else:
                nat_w, nat_h = default_nat_w, default_nat_h
            cx = int(nat_w * fallback_pos["x_pct"] / 100)
            cy = int(nat_h * fallback_pos["y_pct"] / 100)
            slide_markers[slide].append({
                "number": burn_number,
                "finding_index": finding_idx,
                "x": cx,
                "y": cy,
                "x_pct": fallback_pos["x_pct"],
                "y_pct": fallback_pos["y_pct"],
                "severity": severity,
                "fallback_role": mapping.get("fallback_role"),
            })
            continue

        if elem_idx is not None and elem_idx < len(elements):
            elem = elements[elem_idx]

            if isinstance(screenshots, list) and slide < len(screenshots):
                ss = screenshots[slide]
                scroll_y = ss.get("scrollY", 0) if isinstance(ss, dict) else 0
                nat_h = (
                    ss.get("naturalHeight")
                    or ss.get("height")
                    or default_nat_h
                ) if isinstance(ss, dict) else default_nat_h
                nat_w = (
                    ss.get("naturalWidth")
                    or ss.get("width")
                    or default_nat_w
                ) if isinstance(ss, dict) else default_nat_w
            else:
                scroll_y = 0
                nat_h = default_nat_h
                nat_w = default_nat_w

            try:
                viewport_w_css = float(viewport.get("width") or nat_w or 1)
            except (TypeError, ValueError):
                viewport_w_css = float(nat_w or 1)
            try:
                viewport_h_css = float(viewport.get("height") or nat_h or 1)
            except (TypeError, ValueError):
                viewport_h_css = float(nat_h or 1)

            sx = float(nat_w) / max(1.0, viewport_w_css)
            sy = float(nat_h) / max(1.0, viewport_h_css)

            rect_css = element_rect_css(elem, element_coord_scale) or {
                "x": 0.0,
                "y": 0.0,
                "width": 1.0,
                "height": 1.0,
            }
            abs_y_css = rect_css["y"]
            abs_x_css = rect_css["x"]
            elem_w_css = max(1.0, rect_css["width"])
            elem_h_css = max(1.0, rect_css["height"])

            rel_y = (abs_y_css - float(scroll_y)) * sy
            rel_x = abs_x_css * sx
            elem_w = max(1, int(round(elem_w_css * sx)))
            elem_h = max(1, int(round(elem_h_css * sy)))

            cx = int(round(rel_x + elem_w / 2))
            cy = int(round(rel_y + elem_h / 2))

            cx = max(30, min(cx, nat_w - 30))
            cy = max(30, min(cy, nat_h - 30))

            # Store both pixel coords AND percentage for CSS overlays
            x_pct = (cx / nat_w) * 100
            y_pct = (cy / nat_h) * 100

            # Zone rectangle (for v1.0 hotspot outlines). Clamp to slide bounds
            # so sticky-positioned elements like headers don't overflow.
            zone_left = max(0, min(rel_x, nat_w - 4))
            zone_top = max(0, min(rel_y, nat_h - 4))
            zone_w = max(12, min(elem_w, nat_w - zone_left))
            zone_h = max(12, min(elem_h, nat_h - zone_top))
            zone_left_pct = (zone_left / nat_w) * 100
            zone_top_pct = (zone_top / nat_h) * 100
            zone_w_pct = (zone_w / nat_w) * 100
            zone_h_pct = (zone_h / nat_h) * 100

            slide_markers[slide].append({
                "number": burn_number,
                "finding_index": finding_idx,
                "x": cx,
                "y": cy,
                "x_pct": x_pct,
                "y_pct": y_pct,
                "severity": severity,
                "zone": {
                    "left_pct": zone_left_pct,
                    "top_pct": zone_top_pct,
                    "w_pct": zone_w_pct,
                    "h_pct": zone_h_pct,
                },
            })
        else:
            if isinstance(sections, list) and slide < len(sections):
                sec = sections[slide]
                sec_h = sec.get("height", 400) if isinstance(sec, dict) else 400
                slide_markers[slide].append({
                    "number": burn_number,
                "finding_index": finding_idx,
                    "x": 100,
                    "y": sec_h // 2,
                    "x_pct": 10,
                    "y_pct": 50,
                    "severity": severity,
                })

    return slide_markers
