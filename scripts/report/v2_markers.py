"""v2 hotspot resolution (Phase G deliverable 2 + 3, simplified 2026-06-10).

Replaces the v1 5-tier fuzzy resolver in ``markers.py`` with a strict
exact-tier-or-blank ladder tied to v2's baton_index contract. Per
product.md §4.2 v1.2 (Phase-0 rulings A1+A2), confidence is categorical:
only methods that prove the marker lands on the right element
(e_index_lookup on a real on-slide element, operator overrides) auto-
place; every weaker strategy leaves the hotspot blank for the manual
queue. Absence findings (``baton_index="absent"``) ALWAYS go blank —
the operator places or declines them in the editor — because wrong /
wrong-page placement is a hard §4.2 violation, worse than blank.

    Strategy 1 — e_index_lookup (the only auto-placement path)
        Finding has ``baton_index = "eN"``. Look up baton.elements[N] by
        array position. Use rect.x / rect.y / rect.width / rect.height
        (v2-format baton) OR direct x/y/width/height (v1-format baton).
        Bypassed when the rect has no usable geometry or the element
        sits outside every captured screenshot's viewport band (C3 fix
        2026-06-10) — wrong-slide pinning is worse than blank.

    Strategy 4 — unplaced (everything else)
        Emit the finding with NO hotspot position. The finding still
        ships and is queued into the editor's manual-placement list
        (review_state marks it hotspot_confidence="needs-manual-marker"
        with a hidden, coord-less marker); the renderer draws nothing.

Pruned 2026-06-10 (Phase-0 ruling A1/A2):

    Strategy 2 — proposed_anchor dispatch (fix B, 2026-04-30). Auto-
    placed absent findings from a typed ``proposed_anchor`` (element,
    section-bottom-overlay, viewport-bottom-sticky). All three were
    BELOW exact-tier — pinning happened without the renderer ever
    proving the marker landed on the right element — so per §4.2 v1.2
    they were the wrong-hotspot class the rulings are aimed at.

    Strategy 3 — section_centroid (alias-map fallback for findings that
    pre-dated fix B). Surface-string substring match against
    baton.sections[].slug then a section-midpoint pin. Same issue.

    Auto-injection of a default proposed_anchor on absent findings (the
    old emission_autofix repair 4). Without auto-placement, no
    injection is needed.

    Distributed-stack relabel (``section_stacked_manual``, diagnosis
    Fix #3 2026-06-03). Existed to spread N absence findings the
    auto-inject default had collapsed onto one section bottom. With
    absences always blank, no stack forms.

``proposed_anchor`` itself stays in the schema as an OPTIONAL editor
hint — review_state threads it into ``finding.raw.proposed_anchor`` so
the editor's "Place manually" queue can show the specialist's
suggestion to the operator without the renderer pinning anything from
it. The schema's old "required when baton_index='absent'" rule is also
gone (a finding may now ship with ``baton_index="absent"`` and no
``proposed_anchor``).

Markers loader merge (deliverable 3): ``merge_markers`` takes the
Strategy-1 output and an operator overrides JSON. Operator entries WIN
on matching f_ref or finding_index — operator placement is exact-tier
by definition (the human looked at the screenshot and clicked) — and
fill the "manual queue resolved" path.

Authored Phase G (2026-04-28); fix B added 2026-04-30; pruned to the
exact-tier-or-blank shape 2026-06-10 (Phase-0 rulings A1+A2).
"""
from __future__ import annotations

from typing import Sequence

from .geometry import (
    element_rect_css,
    infer_element_coord_scale,
    viewport_dpr,
)

# The place-or-blank decision (product.md §4.2) lives behind the placement seam;
# auto_map_markers_v2 is its first consumer. parse_baton_index / _element_y /
# _element_height moved there with it — they had no other callers.
from .placement import (
    Blank,
    Placed,
    PlacementContext,
    decide_placement,
)

# The giant-rectangle threshold has one home — the giant_exact_rectangles gate
# in assembly/visual_quality.py. Importing it (a dependency-light, jsonschema-free
# leaf) keeps the down-rank here and that gate from ever drifting apart.
from assembly.visual_quality import (
    DEFAULT_GIANT_HEIGHT_PCT,
    DEFAULT_GIANT_WIDTH_PCT,
    is_giant_exact_rect,
)


# G6 (product.md §4.2 precision-first) — an exact_element hotspot whose baton
# rect is BOTH very wide AND very tall is almost always anchored to a parent
# container (full header/drawer/body), not the subject element. Such markers are
# auto-down-ranked to proxy_element so they render as approximate (dashed)
# markers instead of misleading solid "exact" rects. A full-width but SHORT strip
# (nav/footer/CTA/price row) is a precise anchor and stays exact — the wide-AND-
# tall test lives in is_giant_exact_rect. The threshold IS the
# giant_exact_rectangles gate threshold, imported above from its one home in
# assembly/visual_quality.py so the down-rank and the gate cannot drift.
GIANT_EXACT_WIDTH_PCT = DEFAULT_GIANT_WIDTH_PCT
GIANT_EXACT_HEIGHT_PCT = DEFAULT_GIANT_HEIGHT_PCT

# LG5 (2026-06-12): the minimum visible size of a rectangle hotspot zone, as a
# percent of the slide. An exactly-resolved element thinner than this in one
# dimension (e.g. a strikethrough price: ~2.9%w x ~1.9%h) used to fall through
# to a single point; we expand the sub-minimum dimension up to this floor,
# centered on the element, so a region renders as a box.
MIN_VISIBLE_ZONE_PCT = 2.0


def _coerce_pct(value: object, default: float = 50.0) -> float:
    """Coerce an operator-supplied percentage to a float; default on bad input.

    Operator ``--markers`` override entries are merged verbatim with no
    per-field schema validation, so ``x_pct``/``y_pct`` may be missing or
    non-numeric strings.
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def auto_map_markers_v2(
    findings: Sequence[dict],
    baton: dict,
) -> list[dict]:
    """Build the per-finding marker mapping using v2's exact-tier-or-blank ladder.

    Returns a list of mapping dicts compatible with v1's
    compute_marker_positions, plus an extra 'match_method' value for
    diagnostics:

        e_index_lookup    Strategy 1 succeeded — baton_index resolves to a
                          baton element with on-slide rect coords.
        unplaced          Strategy 4 — absent finding, off-slide element, or
                          unusable e_index; emitted with NO position
                          (fallback_position=None). The renderer draws
                          nothing and review_state queues it for manual
                          placement (product.md §4.2 v1.2 rulings A1+A2).

    Every finding still gets a mapping entry, but ``unplaced`` entries carry
    no position — compute_marker_positions_v2 deliberately renders nothing
    for them, and review_state surfaces them in the manual-placement queue.

    Absence findings (``baton_index="absent"``) ALWAYS land in ``unplaced``
    regardless of any ``proposed_anchor`` hint on the finding (ruling A1) —
    proposed_anchor still flows through to the editor's manual queue via
    review_state's per-finding ``raw`` block.
    """
    # The place-or-blank decision (Strategy 1 e_index_lookup, else Strategy 4
    # unplaced — product.md §4.2 v1.2) lives behind the placement seam. Each
    # typed Placed | Blank is converted straight back into the legacy mapping
    # dict here, so this function's output stays byte-identical while the
    # decision becomes independently testable and typed for later consumers.
    ctx = PlacementContext.from_baton(baton)

    mappings: list[dict] = []
    for f in findings:
        mappings.append(_to_mapping(decide_placement(f, ctx)))

    # Augment each mapping with visual_evidence so downstream
    # consumers (review-state writer, HTML builder, Phase 3 quality gates)
    # have a stable typed contract instead of having to interpret
    # match_method strings. Source priority: producer-authored
    # finding.visual_evidence > derived from match_method/proposed_anchor.
    # See scripts/report/visual_evidence.py for the derivation rules.
    from .visual_evidence import derive_visual_evidence
    findings_by_index: dict[int, dict] = {
        f.get("index"): f for f in findings if f.get("index") is not None
    }
    viewport = baton.get("viewport", {})
    for m in mappings:
        f = findings_by_index.get(m.get("finding_index"))
        if f is None:
            m["visual_evidence"] = derive_visual_evidence(
                match_method=m.get("match_method"),
                baton_index=None,
                proposed_anchor=None,
            )
            continue
        m["visual_evidence"] = derive_visual_evidence(
            f,
            match_method=m.get("match_method"),
        )
        # G6: down-rank an oversized exact_element marker to an approximate
        # proxy_element (renders dashed) so it stops claiming pixel-precise
        # placement it doesn't have, and the giant_exact_rectangles gate passes.
        _downrank_oversized_exact(m, ctx.elements, viewport, ctx.element_coord_scale)

    return mappings


def _downrank_oversized_exact(
    mapping: dict,
    elements: list,
    viewport: dict,
    element_coord_scale: float,
) -> None:
    """Down-rank an exact_element mapping to proxy_element when its baton rect is
    giant (product.md §4.2 precision-first). Mutates ``mapping['visual_evidence']``
    in place; no-op for non-exact types or normally-sized elements.

    The size test uses element-width-as-percent-of-viewport, which equals the
    slide-relative zone w/h pct the renderer computes (zone.w_pct =
    element_width_css / viewport_width_css * 100), so the threshold here matches
    exactly what the giant_exact_rectangles gate measures on the rendered marker.
    """
    ve = mapping.get("visual_evidence") or {}
    if ve.get("type") != "exact_element":
        return
    eidx = mapping.get("baton_element_index")
    if not isinstance(eidx, int) or eidx < 0 or eidx >= len(elements):
        return
    rect = element_rect_css(elements[eidx], element_coord_scale)
    if not rect:
        return
    try:
        vw = float(viewport.get("width") or 0)
        vh = float(viewport.get("height") or 0)
    except (TypeError, ValueError):
        return
    if vw <= 0 or vh <= 0:
        return
    w_pct = rect["width"] / vw * 100.0
    h_pct = rect["height"] / vh * 100.0
    if is_giant_exact_rect(
        w_pct, h_pct,
        max_width_pct=GIANT_EXACT_WIDTH_PCT,
        max_height_pct=GIANT_EXACT_HEIGHT_PCT,
    ):
        mapping["visual_evidence"] = {
            "type": "proxy_element",
            "confidence": "low",
            "reason": (
                f"Auto-down-ranked from exact_element: baton rect is "
                f"{w_pct:.0f}%w/{h_pct:.0f}%h of the viewport (wider than "
                f"{GIANT_EXACT_WIDTH_PCT:.0f}%w AND taller than "
                f"{GIANT_EXACT_HEIGHT_PCT:.0f}%h) — likely a parent container, "
                f"not the subject element (product.md §4.2 precision-first)."
            ),
        }


def _to_mapping(result: Placed | Blank) -> dict:
    """Convert a typed placement decision back into the legacy mapping dict.

    Keeps ``auto_map_markers_v2``'s output byte-identical while the decision
    itself lives behind the placement seam. ``Placed`` -> an ``e_index_lookup``
    mapping; ``Blank`` -> the ``unplaced`` mapping (``slide=0`` is a nominal
    anchor only; ``compute_marker_positions_v2`` draws nothing for it). All
    blanks render identically, so ``Blank.reason`` is not emitted here —
    consumers that want it read the typed result directly.
    """
    if isinstance(result, Placed):
        return {
            "finding_index": result.finding_index,
            "f_ref": result.f_ref,
            "burn_number": result.burn_number,
            "baton_element_index": result.baton_element_index,
            "slide": result.slide,
            "match_method": "e_index_lookup",
            "severity": result.severity,
            "fallback_role": None,
            "fallback_position": None,
            "scope": result.scope,
        }
    return {
        "finding_index": result.finding_index,
        "f_ref": result.f_ref,
        "burn_number": result.burn_number,
        "baton_element_index": None,
        "slide": 0,
        "match_method": "unplaced",
        "severity": result.severity,
        "fallback_role": "absent_unplaced",
        "fallback_position": None,
        "scope": result.scope,
    }


def merge_markers(
    auto_mapped: list[dict],
    operator_overrides: list[dict] | None,
) -> list[dict]:
    """Merge operator-supplied overrides with the auto-mapped result.

    Operator entries win on matching ``f_ref`` (preferred v2 key) or
    ``finding_index`` (v1 fallback). Auto-mapped entries fill any gap. v1
    behavior was REPLACE — operator file overrode the whole list. v2
    behavior is MERGE so an operator pinning two findings doesn't accidentally
    drop the auto-mapping for the other 40+ findings.

    Closes Phase G deliverable 3. Resolves §23.3 #3 / §24.5 #2.
    """
    if not operator_overrides:
        return list(auto_mapped)

    by_key: dict = {}  # key = (f_ref or finding_index)
    for m in auto_mapped:
        key = m.get("f_ref") or ("idx", m.get("finding_index"))
        by_key[key] = dict(m)

    for ov in operator_overrides:
        key = ov.get("f_ref") or ("idx", ov.get("finding_index"))
        # Operator wins; preserve any auto-mapped fields the override didn't set.
        if key in by_key:
            merged = dict(by_key[key])
            merged.update(ov)
            merged["match_method"] = "operator_override"
            by_key[key] = merged
        else:
            entry = dict(ov)
            entry.setdefault("match_method", "operator_override")
            by_key[key] = entry

    # Preserve original auto_mapped order for stability; append operator-only
    # entries at the end.
    out: list[dict] = []
    seen: set = set()
    for m in auto_mapped:
        key = m.get("f_ref") or ("idx", m.get("finding_index"))
        if key in by_key and key not in seen:
            out.append(by_key[key])
            seen.add(key)
    for ov in operator_overrides:
        key = ov.get("f_ref") or ("idx", ov.get("finding_index"))
        if key not in seen:
            out.append(by_key[key])
            seen.add(key)
    return out


def compute_marker_positions_v2(
    markers_mapping: list[dict],
    baton: dict,
) -> dict:
    """Compute pixel positions for v2 markers on screenshots.

    Mirrors v1's compute_marker_positions semantics so the rest of the
    renderer pipeline (hotspot overlays, click handlers) doesn't need to
    change. Difference from v1: handles both element.rect.{x,y,...} (v2
    baton) and element.{x,y,...} (v1 baton) shapes.
    """
    elements = baton.get("elements", [])
    screenshots = baton.get("screenshots", [])
    viewport = baton.get("viewport", {})
    dpr = viewport_dpr(viewport)
    element_coord_scale = infer_element_coord_scale(
        elements,
        screenshots,
        viewport,
        dpr,
        baton.get("sections") or [],
    )

    # Default natural dimensions per device per contracts/device-semantics.md.
    _DEVICE_FALLBACKS = {
        "mobile": (390, 844, 3),
        "laptop": (1440, 900, 1),
        "desktop": (1920, 1080, 1),
    }
    device = (baton.get("device") or "laptop").lower()
    _fw, _fh, _fdpr = _DEVICE_FALLBACKS.get(device, _DEVICE_FALLBACKS["laptop"])
    try:
        default_nat_w = int(viewport.get("width") or _fw)
    except (ValueError, TypeError):
        default_nat_w = _fw
    try:
        default_nat_h = int(viewport.get("height") or _fh)
    except (ValueError, TypeError):
        default_nat_h = _fh

    slide_markers: dict = {}
    for mapping in markers_mapping:
        slide = mapping.get("slide")
        if slide is None:
            continue
        try:
            slide = int(slide)
        except (TypeError, ValueError):
            continue
        if slide not in slide_markers:
            slide_markers[slide] = []

        finding_idx = mapping.get("finding_index")
        burn_number = mapping.get("burn_number") or finding_idx
        severity = mapping.get("severity", "medium")
        elem_idx = mapping.get("baton_element_index")
        fallback_pos = mapping.get("fallback_position")

        # Slide natural dimensions
        if isinstance(screenshots, list) and slide < len(screenshots):
            ss = screenshots[slide] if isinstance(screenshots[slide], dict) else {}
            nat_h = int(ss.get("naturalHeight") or ss.get("height") or default_nat_h)
            nat_w = int(ss.get("naturalWidth") or ss.get("width") or default_nat_w)
            scroll_y = float(ss.get("scrollY", 0) or 0)
        else:
            ss = {}
            nat_h = default_nat_h
            nat_w = default_nat_w
            scroll_y = 0.0

        if isinstance(fallback_pos, dict):
            fx = _coerce_pct(fallback_pos.get("x_pct"))
            fy = _coerce_pct(fallback_pos.get("y_pct"))
            cx = int(nat_w * fx / 100)
            cy = int(nat_h * fy / 100)
            slide_markers[slide].append({
                "number": burn_number,
                "finding_index": finding_idx,
                "f_ref": mapping.get("f_ref"),
                "x": cx,
                "y": cy,
                "x_pct": fx,
                "y_pct": fy,
                "severity": severity,
                "fallback_role": mapping.get("fallback_role"),
                "match_method": mapping.get("match_method"),
                "visual_evidence": mapping.get("visual_evidence"),
            })
            continue

        if elem_idx is None or elem_idx >= len(elements):
            continue

        elem = elements[elem_idx]
        rect_css = element_rect_css(elem, element_coord_scale) or {
            "x": 0.0,
            "y": 0.0,
            "width": 0.0,
            "height": 0.0,
        }
        ex = rect_css["x"]
        ey = rect_css["y"]
        ew = rect_css["width"]
        eh = rect_css["height"]

        # Convert absolute coords to slide-relative coords.
        # Element y is absolute scroll_y from page top. Slide.scrollY is the
        # scroll position when the slide's screenshot was captured. So slide-
        # relative y = elem_y - scroll_y, then scaled to natural dimensions.
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

        # Relative to slide
        rel_x_css = ex
        rel_y_css = ey - scroll_y

        cx = int(rel_x_css * sx + (ew * sx) / 2)
        cy = int(rel_y_css * sy + (eh * sy) / 2)

        # Clamp inside slide bounds — defensive.
        cx = max(0, min(cx, nat_w))
        cy = max(0, min(cy, nat_h))

        x_pct = (cx / max(1, nat_w)) * 100
        y_pct = (cy / max(1, nat_h)) * 100

        # Build zone (percentages) for rectangle hotspot overlays. The
        # renderer's build_hotspot_overlays_html reads m["zone"] with
        # left_pct/top_pct/w_pct/h_pct; falls through to circle when zone
        # is missing or too small. Phase G deliverable: precise element
        # rectangles instead of circle markers (Dan's Operator Checkpoint
        # #4 feedback — rectangles outline the element directly, like the
        # v1 baseline's red-outlined searchbar shot).
        rect_left_pct = (rel_x_css * sx) / max(1, nat_w) * 100
        rect_top_pct = (rel_y_css * sy) / max(1, nat_h) * 100
        rect_w_pct = (ew * sx) / max(1, nat_w) * 100
        rect_h_pct = (eh * sy) / max(1, nat_h) * 100
        # Clamp inside slide bounds and require minimum visible size.
        rect_left_pct = max(0.0, min(rect_left_pct, 100.0))
        rect_top_pct = max(0.0, min(rect_top_pct, 100.0))
        rect_w_pct = max(0.0, min(rect_w_pct, 100.0 - rect_left_pct))
        rect_h_pct = max(0.0, min(rect_h_pct, 100.0 - rect_top_pct))

        # LG5: emit a rectangle for any non-degenerate element rect. When one
        # dimension is below the minimum visible size (a thin strikethrough
        # price, ~1.9%h), expand THAT dimension up to the floor, centered on the
        # element, so a region renders as a box instead of a single point. The
        # element center is preserved; a zero-area rect stays a point (None).
        zone = None
        if rect_w_pct > 0.0 and rect_h_pct > 0.0:
            z_left, z_top = rect_left_pct, rect_top_pct
            z_w, z_h = rect_w_pct, rect_h_pct
            if z_w < MIN_VISIBLE_ZONE_PCT:
                z_left = max(0.0, z_left - (MIN_VISIBLE_ZONE_PCT - z_w) / 2)
                z_w = min(MIN_VISIBLE_ZONE_PCT, 100.0 - z_left)
            if z_h < MIN_VISIBLE_ZONE_PCT:
                z_top = max(0.0, z_top - (MIN_VISIBLE_ZONE_PCT - z_h) / 2)
                z_h = min(MIN_VISIBLE_ZONE_PCT, 100.0 - z_top)
            zone = {
                "left_pct": z_left,
                "top_pct": z_top,
                "w_pct": z_w,
                "h_pct": z_h,
            }

        slide_markers[slide].append({
            "number": burn_number,
            "finding_index": finding_idx,
            "f_ref": mapping.get("f_ref"),
            "x": cx,
            "y": cy,
            "x_pct": x_pct,
            "y_pct": y_pct,
            "severity": severity,
            "fallback_role": None,
            "match_method": mapping.get("match_method"),
            "visual_evidence": mapping.get("visual_evidence"),
            "zone": zone,
            # Element bounding box (in slide pixels) for diagnostic / future renderers.
            "rect": {
                "x": int(rel_x_css * sx),
                "y": int(rel_y_css * sy),
                "width": int(ew * sx),
                "height": int(eh * sy),
            },
        })

    return slide_markers
