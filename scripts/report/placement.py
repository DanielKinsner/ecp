"""The place-or-blank decision — one seam for product.md §4.2.

Whether a finding's hotspot is auto-placed on a screenshot or left blank for
the manual queue is the product's #1 trust rule (§4.2 v1.2, rulings A1+A2):
auto-place ONLY at exact-tier confidence (a baton_index that resolves to a
real, on-slide element with concrete geometry); every weaker signal leaves the
hotspot blank. Wrong / wrong-page placement is a hard violation, worse than a
blank.

That decision used to live only inside ``v2_markers.auto_map_markers_v2`` as a
loop that emitted ``match_method`` strings, and the consumers downstream
(``review_state`` confidence labels, ``placement_audit`` weak-scoring,
``placement_repair`` re-anchoring) each re-inferred the outcome from those
strings and the resulting pixel boxes. This module gives the decision one
owning interface — ``decide_placement(finding, ctx) -> Placed | Blank`` — so it
can be exercised in isolation and consumed as a typed result instead of
re-derived.

Step 1 of the C1 deepening: the seam is introduced and ``auto_map_markers_v2``
becomes its first consumer (it converts the typed result straight back into the
legacy mapping dict, so output is byte-identical). Later steps migrate the other
consumers off ``match_method`` strings onto ``Placed | Blank``.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .geometry import (
    element_rect_raw,
    infer_element_coord_scale,
    slide_for_css_y,
    viewport_dpr,
)

_E_INDEX_RE = re.compile(r"^e(\d+)$")


# ---------------------------------------------------------------------------
# Result types — the typed outcome of the place-or-blank decision
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Placed:
    """An exact-tier placement: the finding resolved to a real on-slide element.

    Carries everything ``auto_map_markers_v2`` needs to emit an
    ``e_index_lookup`` mapping. Corresponds to product.md §4.2 Strategy 1 (the
    only auto-placement path).
    """

    finding_index: int | None
    f_ref: str | None
    burn_number: object
    baton_element_index: int
    slide: int
    severity: str
    scope: str


@dataclass(frozen=True)
class Blank:
    """A left-blank hotspot: no exact-tier signal, so it goes to the manual queue.

    ``reason`` is the diagnostic the legacy ``match_method="unplaced"`` string
    threw away — the caller renders every Blank identically (no marker), but a
    typed reason lets a maintainer (and later consumers) tell an absent finding
    from an off-slide element from a geometry-less one without re-deriving it.
    """

    finding_index: int | None
    f_ref: str | None
    burn_number: object
    severity: str
    scope: str
    reason: str  # one of REASONS


# Why a finding was left blank. Descriptive only; all render as no marker.
REASON_ABSENT = "absent"  # baton_index="absent" or missing (ruling A1)
REASON_UNRESOLVED_BATON_INDEX = "unresolved_baton_index"  # eN out of element range
REASON_NO_GEOMETRY = "no_geometry"  # element has no usable rect
REASON_OFFSLIDE = "offslide"  # element sits outside every captured slide's band
REASON_OFFVIEWPORT = "offviewport"  # element is horizontally outside the captured viewport
REASONS = frozenset(
    {
        REASON_ABSENT,
        REASON_UNRESOLVED_BATON_INDEX,
        REASON_NO_GEOMETRY,
        REASON_OFFSLIDE,
        REASON_OFFVIEWPORT,
    }
)


# ---------------------------------------------------------------------------
# Placement context — baton-derived facts, computed once per report
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PlacementContext:
    """The baton-derived facts ``decide_placement`` needs, computed once.

    ``element_coord_scale`` (the CSS-px vs device-px inference) is O(elements),
    so it is resolved once here rather than per finding.
    """

    elements: list
    sections: list
    screenshots: list
    viewport_w: float
    viewport_h: float
    element_coord_scale: float

    @classmethod
    def from_baton(cls, baton: dict) -> "PlacementContext":
        elements = baton.get("elements", [])
        sections = baton.get("sections", [])
        screenshots = baton.get("screenshots", [])
        viewport = baton.get("viewport", {})
        viewport_w = float(viewport.get("width", 390) or 390)
        viewport_h = float(viewport.get("height", 844) or 844)
        dpr = viewport_dpr(viewport)
        element_coord_scale = infer_element_coord_scale(
            elements, screenshots, viewport, dpr, sections
        )
        return cls(
            elements,
            sections,
            screenshots,
            viewport_w,
            viewport_h,
            element_coord_scale,
        )


# ---------------------------------------------------------------------------
# Element helpers (relocated verbatim from v2_markers — only callers were here)
# ---------------------------------------------------------------------------


def parse_baton_index(baton_index: str | None) -> int | None:
    """Convert a baton e_index ('e5') to its 0-based array position.

    Returns None for None input or 'absent'. Returns None for malformed
    strings rather than raising — the caller falls through to the blank handler.
    """
    if not baton_index or baton_index == "absent":
        return None
    m = _E_INDEX_RE.match(baton_index)
    if not m:
        return None
    return int(m.group(1))


def _element_y(elem: dict) -> float:
    """Return absolute scroll_y of an element, accommodating v1 and v2 baton shapes."""
    rect = element_rect_raw(elem)
    return rect["y"] if rect else 0.0


def _element_height(elem: dict) -> float:
    """Return element height (CSS px), 0 when unavailable."""
    rect = element_rect_raw(elem)
    return rect["height"] if rect else 0.0


# ---------------------------------------------------------------------------
# The decision
# ---------------------------------------------------------------------------


def decide_placement(finding: dict, ctx: PlacementContext) -> Placed | Blank:
    """Decide whether ``finding``'s hotspot auto-places (Placed) or blanks (Blank).

    Exact-tier-or-blank ladder (product.md §4.2 v1.2):

    * Strategy 1 — the finding's ``baton_index`` resolves to an element that has
      usable geometry AND sits inside a captured screenshot's viewport band:
      ``Placed`` on that slide.
    * Otherwise (absent, unresolved index, no geometry, or off-slide):
      ``Blank`` with the reason — never auto-place a guess, never pin onto the
      wrong slide.
    """
    finding_idx = finding.get("index")
    f_ref = finding.get("f_ref")
    baton_index_str = finding.get("baton_index")
    scope = finding.get("scope") or "device"
    severity = (finding.get("priority") or "MEDIUM").lower()
    burn_number = finding.get("cluster_index") or finding_idx

    def _blank(reason: str) -> Blank:
        return Blank(finding_idx, f_ref, burn_number, severity, scope, reason)

    # Strategy 1: e_index lookup — the ONLY auto-placement path.
    elem_idx = parse_baton_index(baton_index_str)
    if elem_idx is None:
        return _blank(REASON_ABSENT)
    if not (0 <= elem_idx < len(ctx.elements)):
        return _blank(REASON_UNRESOLVED_BATON_INDEX)

    elem = ctx.elements[elem_idx]
    rect = element_rect_raw(elem)
    elem_y_raw = rect["y"] if rect else 0.0
    elem_h_raw = rect["height"] if rect else 0.0
    scale = ctx.element_coord_scale
    elem_y_css = elem_y_raw / scale if scale else elem_y_raw
    elem_h_css = elem_h_raw / scale if scale else elem_h_raw

    # An element with no usable rect must not be pinned onto an arbitrary slide.
    if elem_y_raw <= 0 and elem_h_raw <= 0:
        return _blank(REASON_NO_GEOMETRY)

    # Horizontal carousels keep non-visible cards in the DOM with exact rects
    # far beyond the viewport. Those are exact elements but not exact visual
    # evidence: clamping their x coordinate to 100% creates a convincing marker
    # on the wrong pixels. Only auto-place elements that intersect the captured
    # viewport horizontally; otherwise leave them for manual placement.
    elem_x_raw = rect["x"] if rect else 0.0
    elem_w_raw = rect["width"] if rect else 0.0
    elem_x_css = elem_x_raw / scale if scale else elem_x_raw
    elem_w_css = elem_w_raw / scale if scale else elem_w_raw
    if elem_x_css + elem_w_css <= 0 or elem_x_css >= ctx.viewport_w:
        return _blank(REASON_OFFVIEWPORT)

    # Pick the slide by element CENTER (tall elements spanning slides bias toward
    # the wrong slide if picked by top).
    slide_pick_y = elem_y_css + elem_h_css / 2.0
    slide = slide_for_css_y(slide_pick_y, ctx.viewport_h, ctx.screenshots, ctx.sections)

    offslide = True
    if 0 <= slide < len(ctx.screenshots):
        ss = ctx.screenshots[slide] if isinstance(ctx.screenshots[slide], dict) else {}
        ss_scroll = float(ss.get("scrollY", 0) or 0)
        if ss_scroll <= slide_pick_y < ss_scroll + ctx.viewport_h:
            offslide = False
    if offslide:
        # Never auto-place on the wrong slide (product.md §4.2 — wrong-page
        # placement is worse than blank).
        return _blank(REASON_OFFSLIDE)

    return Placed(
        finding_index=finding_idx,
        f_ref=f_ref,
        burn_number=burn_number,
        baton_element_index=elem_idx,
        slide=slide,
        severity=severity,
        scope=scope,
    )


# ---------------------------------------------------------------------------
# Cross-finding de-collision — one box per element (§4.2 precision over recall)
# ---------------------------------------------------------------------------

# Mirrors assembly.finding_stability.severity_rank, kept local so the live
# render path (review_state) doesn't import that optional-heavy module.
# Unknown / empty severity -> 0, so it only ever loses a tie-break.
_COPLACE_SEVERITY_RANK = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}


def coplaced_blanks(placements):
    """f_refs to blank when >1 finding auto-places on the SAME element (§4.2).

    ``placements`` is an iterable of ``(f_ref, slide_id, element_index,
    severity)`` for every finding that DID auto-place on a concrete baton
    element. When two or more share a ``(slide_id, element_index)`` their
    marker rects stack pixel-for-pixel — the operator sees one blob and
    ``diagnose_engagement.py`` flags STACKED / DUPLICATE. Precision over recall
    (§4.2): keep the single highest-severity box on the element and blank the
    rest into the manual-placement queue (they stay findings, just unplaced).

    Deterministic: a coord-less ``element_index`` of ``None`` never collides,
    and severity ties resolve to the first finding in input order.
    """
    groups: dict = {}
    for f_ref, slide_id, element_index, severity in placements:
        if element_index is None:
            continue
        groups.setdefault((slide_id, element_index), []).append((f_ref, severity))
    losers: set = set()
    for members in groups.values():
        if len(members) < 2:
            continue
        winner = max(
            members,
            key=lambda m: _COPLACE_SEVERITY_RANK.get((m[1] or "").upper(), 0),
        )[0]
        losers.update(f_ref for f_ref, _ in members if f_ref != winner)
    return losers
