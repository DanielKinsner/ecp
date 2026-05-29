"""Heuristic section labels + cluster slugs for URL acquisition batons.

Implements `workflows/acquire.md`-style **descriptive** section names (not cluster slugs) via
in-viewport landmarks + visible headings, plus a keyword → cluster map for routing. Labels are
**deduped** to stay unique, matching the baton contract.
"""

from __future__ import annotations

import re
from typing import Any

# Canonical v5 cluster slugs; keywords are intentionally broad (see acquire.md)
_CLUSTER_KEYWORDS: list[tuple[str, list[str]]] = [
    (
        "visual-cta",
        [
            "hero",
            "headline",
            "banner",
            "add to cart",
            "add-to-cart",
            "buy now",
            "shop now",
            "subscribe",
            "learn more",
        ],
    ),
    (
        "trust-credibility",
        [
            "review",
            "rating",
            "testimonial",
            "trust",
            "badge",
            "guarantee",
            "certified",
            "verified",
            "stars",
        ],
    ),
    (
        "pricing",
        [
            "price",
            "sale",
            "discount",
            "save",
            "shipping",
            "bnpl",
            "klarna",
            "afterpay",
            "bundle",
        ],
    ),
    (
        "checkout-flows",
        [
            "cart",
            "checkout",
            "basket",
            "payment",
            "billing",
            "paypal",
            "apple pay",
        ],
    ),
    (
        "product-media",
        [
            "gallery",
            "carousel",
            "thumbnail",
            "zoom",
            "video",
            "360",
            "image",
        ],
    ),
    (
        "category-navigation",
        [
            "search",
            "filter",
            "sort",
            "category",
            "collection",
            "breadcrumb",
        ],
    ),
    (
        "content-seo",
        [
            "h1",
            "blog",
            "read more",
            "description",
        ],
    ),
    (
        "post-purchase",
        [
            "order",
            "thank you",
            "thank-you",
            "loyalty",
            "refer",
        ],
    ),
    (
        "audience",
        [
            "personalize",
            "recommended",
            "for you",
        ],
    ),
    (
        "performance-ux",
        [
            "hamburger",
            "drawer",
            "sticky",
            "swipe",
            "mobile menu",
        ],
    ),
]

_DEVICE_HINTS: dict[str, str] = {
    "mobile": "Mobile layout: check sticky bars, touch targets, drawer nav.",
    "laptop": "Laptop: multi-column and hover-dependent UI may appear.",
    "desktop": "Desktop: wide layout, hover flyouts, mega-menus may appear.",
}


def clusters_for_text(*blobs: str) -> list[str]:
    s = " ".join(b for b in blobs if b)
    s = s.lower()
    s = re.sub(r"\s+", " ", s).strip()
    out: list[str] = []
    for slug, kws in _CLUSTER_KEYWORDS:
        for kw in kws:
            if kw in s:
                out.append(slug)
                break
    # De-dupe preserve order
    seen: set[str] = set()
    unique: list[str] = []
    for c in out:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique[:6]


def section_label(
    *,
    index: int,
    scroll_y: int,
    heading: str,
    page_title: str,
    device: str,
    human_scene: str = "",
) -> str:
    """Build a **human-style** label (acquire.md: unique prose, not a cluster slug)."""
    scene = (human_scene or "").strip()
    if len(scene) > 3 and not _looks_generic_placeholder(scene):
        return scene[:100]
    h = (heading or "").strip()
    if scroll_y < 6:
        if h:
            return f"Above the fold — {h[:85]}"
        return "Above the fold (hero, navigation, and primary CTA)"
    if h:
        return h[:100]
    if index <= 2:
        return f"Primary content block {index}"
    return f"Lower page section {index}"


def _looks_generic_placeholder(s: str) -> bool:
    t = s.lower().strip()
    return t in ("main content", "content block", "content section", "article content", "") or (
        t.startswith("content") and len(t) < 18
    )


def make_section_labels_unique(
    sections: list[dict[str, Any]], screenshots: list[dict[str, Any]] | None = None
) -> None:
    """Mutate `label` in place so every entry is unique (acquire.md contract)."""
    if not sections:
        return
    used: set[str] = set()
    for row in sections:
        if not isinstance(row, dict):
            continue
        base = str(row.get("label") or "").strip() or f"section-{row.get('screenshot_index', 0)}"
        final = base[:100]
        if final in used:
            n = 2
            while True:
                cand = f"{base} (view {n})"[:100]
                if cand not in used:
                    final = cand
                    break
                n += 1
                if n > 30:
                    final = f"{base[:70]} (alt)"[:100]
                    break
        used.add(final)
        row["label"] = final
    if screenshots is None:
        return
    # Sync screenshot labels to section by screenshot_index
    by_shot: dict[int, str] = {}
    for s in sections:
        if not isinstance(s, dict):
            continue
        try:
            si = int(s.get("screenshot_index", 0) or 0)
        except (TypeError, ValueError):
            continue
        if si and s.get("label"):
            by_shot[si] = str(s.get("label"))
    for sh in screenshots:
        if not isinstance(sh, dict):
            continue
        try:
            ix = int(sh.get("index", 0) or 0)
        except (TypeError, ValueError):
            continue
        if by_shot.get(ix):
            sh["label"] = by_shot[ix]


def enrich_baton_sections(sections: list[dict[str, Any]], page_title: str, device: str) -> list[dict[str, Any]]:
    for row in sections:
        if not isinstance(row, dict):
            continue
        lab = str(row.get("label", "") or "")
        clusters = clusters_for_text(lab, page_title, _DEVICE_HINTS.get(device, ""))
        if clusters and not row.get("clusters"):
            row["clusters"] = clusters
        elif not row.get("clusters"):
            row["clusters"] = clusters or ["visual-cta"]
    return sections


def enrich_screenshot_labels(
    screenshots: list[dict[str, Any]], sections: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_idx: dict[int, str] = {}
    for s in sections:
        if not isinstance(s, dict):
            continue
        try:
            si = int(s.get("screenshot_index", 0))
        except (TypeError, ValueError):
            continue
        if si and s.get("label"):
            by_idx[si] = str(s.get("label"))
    for sh in screenshots:
        if not isinstance(sh, dict):
            continue
        try:
            ix = int(sh.get("index", 0))
        except (TypeError, ValueError):
            continue
        if by_idx.get(ix):
            sh["label"] = by_idx[ix]
    return screenshots
