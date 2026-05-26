"""Shared geometry helpers for report and editor hotspot placement."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def viewport_dpr(viewport: dict[str, Any] | None) -> float:
    """Return effective DPR for legacy and v2 viewport shapes."""
    viewport = viewport or {}
    raw = (
        viewport.get("dpr_actual")
        or viewport.get("dpr")
        or viewport.get("dpr_requested")
        or 1
    )
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return 1.0
    return value if value > 0 else 1.0


def element_rect_raw(element: dict[str, Any] | None) -> dict[str, float] | None:
    """Return raw element geometry from v2 ``rect`` or legacy flat fields."""
    if not isinstance(element, dict):
        return None
    rect = element.get("rect") if isinstance(element.get("rect"), dict) else element
    try:
        return {
            "x": float(rect.get("x", 0) or 0),
            "y": float(rect.get("y", 0) or 0),
            "width": float(rect.get("width", 0) or 0),
            "height": float(rect.get("height", 0) or 0),
        }
    except (AttributeError, TypeError, ValueError):
        return None


def element_rect_css(element: dict[str, Any] | None, scale: float) -> dict[str, float] | None:
    """Return element geometry normalized to CSS page coordinates."""
    rect = element_rect_raw(element)
    if rect is None:
        return None
    safe_scale = scale if scale else 1.0
    return {
        "x": rect["x"] / safe_scale,
        "y": rect["y"] / safe_scale,
        "width": rect["width"] / safe_scale,
        "height": rect["height"] / safe_scale,
    }


def section_scroll_top(section: dict[str, Any] | None) -> float:
    """Return the CSS scroll top for a v2 section."""
    if not isinstance(section, dict):
        return 0.0
    raw = section.get("scroll_y_top")
    if raw is None:
        raw = section.get("scrollY", 0)
    try:
        return float(raw or 0)
    except (TypeError, ValueError):
        return 0.0


def section_scroll_bottom(section: dict[str, Any] | None, viewport_h: float = 0.0) -> float:
    """Return the CSS scroll bottom for a v2 section."""
    if not isinstance(section, dict):
        return 0.0
    raw = section.get("scroll_y_bottom")
    if raw is not None:
        try:
            return float(raw)
        except (TypeError, ValueError):
            pass
    height = section.get("height")
    try:
        h = float(height or viewport_h or 0)
    except (TypeError, ValueError):
        h = viewport_h or 0.0
    return section_scroll_top(section) + h


def css_page_envelope_height(
    screenshots: list[Any] | None,
    viewport: dict[str, Any] | None,
    sections: list[Any] | None = None,
) -> float:
    """Return the largest CSS page y covered by screenshots/sections."""
    viewport = viewport or {}
    try:
        viewport_h = float(viewport.get("height") or 0)
    except (TypeError, ValueError):
        viewport_h = 0.0

    max_bottom = viewport_h
    for screenshot in screenshots or []:
        if not isinstance(screenshot, dict):
            continue
        try:
            max_bottom = max(max_bottom, float(screenshot.get("scrollY", 0) or 0) + viewport_h)
        except (TypeError, ValueError):
            pass
    for section in sections or []:
        max_bottom = max(max_bottom, section_scroll_bottom(section, viewport_h))
    return max_bottom


def infer_element_coord_scale(
    elements: list[Any] | None,
    screenshots: list[Any] | None,
    viewport: dict[str, Any] | None,
    dpr: float | None = None,
    sections: list[Any] | None = None,
) -> float:
    """Infer whether element geometry is CSS px or DPR-scaled physical px."""
    viewport = viewport or {}
    effective_dpr = float(dpr or viewport_dpr(viewport) or 1.0)
    if effective_dpr <= 1:
        return 1.0

    try:
        viewport_w = float(viewport.get("width") or 0)
    except (TypeError, ValueError):
        viewport_w = 0.0

    css_h = css_page_envelope_height(screenshots, viewport, sections)
    if css_h <= 0:
        return 1.0

    rects = [rect for element in elements or [] if (rect := element_rect_raw(element)) is not None]
    if not rects:
        return 1.0

    y_max = max(r["y"] + max(0.0, r["height"]) for r in rects)
    x_max = max((r["x"] + max(0.0, r["width"]) for r in rects), default=0.0)

    css_y_fits = y_max <= css_h * 1.25
    dpr_y_fits = (y_max / effective_dpr) <= css_h * 1.25

    # Vertical page extent is the strongest signal for slide selection. If raw
    # y exceeds the CSS page envelope but normalizes cleanly by DPR, the baton
    # is physical-pixel based.
    if not css_y_fits and dpr_y_fits:
        return float(effective_dpr)

    # If vertical extent is inconclusive, use horizontal extent conservatively.
    # The DPR path requires a strong overflow beyond plausible off-canvas CSS.
    if viewport_w > 0:
        css_x_fits = x_max <= viewport_w * 1.35
        dpr_x_fits = (x_max / effective_dpr) <= viewport_w * 1.35
        strong_physical_x = x_max > viewport_w * 1.75
        if css_y_fits and not css_x_fits and dpr_x_fits and strong_physical_x:
            return float(effective_dpr)

    return 1.0


def image_dimensions(path: Path) -> tuple[int, int] | None:
    """Read image dimensions with Pillow when available."""
    try:
        from PIL import Image
    except Exception:
        return None
    try:
        with Image.open(path) as image:
            return int(image.width), int(image.height)
    except (OSError, ValueError):
        return None


def screenshot_natural_size(
    screenshot_ref: str | None,
    engagement_dir: Path | None,
    viewport: dict[str, Any] | None,
) -> tuple[int, int]:
    """Return screenshot natural pixel dimensions with honest fallbacks."""
    viewport = viewport or {}
    if screenshot_ref and engagement_dir is not None:
        actual = image_dimensions(engagement_dir / screenshot_ref)
        if actual:
            return actual

    dpr = viewport_dpr(viewport)
    try:
        width = int(float(viewport.get("width") or 1) * dpr)
    except (TypeError, ValueError):
        width = 1
    try:
        height = int(float(viewport.get("height") or 1) * dpr)
    except (TypeError, ValueError):
        height = 1
    return max(1, width), max(1, height)


def backfill_screenshots_from_sections(
    baton: dict[str, Any],
    engagement_dir: Path | None = None,
) -> None:
    """Populate v1-style screenshots[] from v2 sections[] when absent."""
    if baton.get("screenshots") or not baton.get("sections"):
        return
    viewport = baton.get("viewport") or {}
    screenshots: list[dict[str, Any]] = []
    for section in baton.get("sections") or []:
        if not isinstance(section, dict):
            continue
        ref = section.get("screenshot_ref")
        if not ref:
            continue
        natural_w, natural_h = screenshot_natural_size(ref, engagement_dir, viewport)
        screenshots.append({
            "path": ref,
            "label": section.get("label") or section.get("slug") or ref,
            "scrollY": section_scroll_top(section),
            "naturalWidth": natural_w,
            "naturalHeight": natural_h,
        })
    if screenshots:
        baton["screenshots"] = screenshots


def screenshot_ref_to_index(screenshots: list[Any] | None) -> dict[str, int]:
    """Map screenshot path/file refs to zero-based slide indices."""
    out: dict[str, int] = {}
    for i, screenshot in enumerate(screenshots or []):
        if not isinstance(screenshot, dict):
            continue
        ref = screenshot.get("path") or screenshot.get("file") or ""
        if ref:
            out[str(ref)] = i
    return out


def slide_for_css_y(
    scroll_y: float,
    viewport_h: float,
    screenshots: list[Any] | None,
    sections: list[Any] | None = None,
) -> int:
    """Pick the slide for a CSS page y, preferring section ownership."""
    ref_index = screenshot_ref_to_index(screenshots)
    for section in sections or []:
        if not isinstance(section, dict):
            continue
        top = section_scroll_top(section)
        bottom = section_scroll_bottom(section, viewport_h)
        if top <= scroll_y <= bottom:
            ref = section.get("screenshot_ref")
            if ref in ref_index:
                return ref_index[ref]

    best_slide = -1
    best_distance = float("inf")
    for i, screenshot in enumerate(screenshots or []):
        if not isinstance(screenshot, dict):
            continue
        try:
            ss_scroll = float(screenshot.get("scrollY", 0) or 0)
        except (TypeError, ValueError):
            ss_scroll = 0.0
        if ss_scroll <= scroll_y < ss_scroll + viewport_h:
            relative_y = scroll_y - ss_scroll
            distance = abs(relative_y - viewport_h / 2.0)
            if distance < best_distance:
                best_distance = distance
                best_slide = i

    if best_slide >= 0:
        return best_slide

    best_slide = 0
    best_distance = float("inf")
    for i, screenshot in enumerate(screenshots or []):
        if not isinstance(screenshot, dict):
            continue
        try:
            ss_scroll = float(screenshot.get("scrollY", 0) or 0)
        except (TypeError, ValueError):
            ss_scroll = 0.0
        distance = abs(ss_scroll - scroll_y)
        if distance < best_distance:
            best_distance = distance
            best_slide = i
    return best_slide
