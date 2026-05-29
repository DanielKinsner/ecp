"""Durable v1->v2 baton converter.

Maps an `acquire_url.py`-shape (v1) baton onto `schema/baton-v1.json` (v2): flat
x/y/width/height elements + scroll-slice sections become e_index/rect elements,
disjoint sections, a parsed page_head, and capture_state. Supersedes the
throwaway `adapt_v1_baton_to_v2.py` and the per-engagement
`convert_<eng>_batons.py` copies.

Faithful to the production acquirer: section labels + per-section clusters are
produced via the *same* `ecp_section_hints` helpers `acquire_url.py` itself uses
(lines 1094-1096), not a bespoke all-clusters stamp. Per-section clusters are
advisory downstream anyway — `dom_preprocess._route_clusters_for()` re-routes
authoritatively from labels (see docs/superpowers/specs/2026-05-29-durable-baton-
converter-design.md).

This module exposes a pure `convert_baton(...)` (no I/O) for testability; the
I/O wrapper and CLI live alongside it.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

import ecp_section_hints as sec_hints  # noqa: E402
from assembly.atomic_write import atomic_write_json  # noqa: E402
from jsonschema import Draft202012Validator  # noqa: E402

_SCHEMA_PATH = REPO / "schema" / "baton-v1.json"
_EID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[0-9a-f]{8}$")

IMPLICIT_ROLE = {
    "button": "button", "a": "link", "nav": "navigation", "header": "banner",
    "footer": "contentinfo", "main": "main", "h1": "heading", "h2": "heading",
    "h3": "heading", "h4": "heading", "h5": "heading", "h6": "heading",
    "img": "image", "form": "form", "input": "textbox", "select": "combobox",
}

_validator_cache: Draft202012Validator | None = None


class BatonConversionError(ValueError):
    """Raised when inputs are invalid or the converted baton fails schema validation."""


def _validator() -> Draft202012Validator:
    global _validator_cache
    if _validator_cache is None:
        schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
        _validator_cache = Draft202012Validator(schema)
    return _validator_cache


def _validate(v2: dict) -> None:
    errs = sorted(_validator().iter_errors(v2), key=lambda e: list(e.path))
    if errs:
        detail = "; ".join(f"{list(e.path)}: {e.message[:140]}" for e in errs[:8])
        raise BatonConversionError(f"converted baton failed schema validation: {detail}")


def _head_meta(dom_html: str) -> dict:
    """Extract page_head fields from the captured DOM <head>."""
    head_match = re.search(r"<head[^>]*>(.*?)</head>", dom_html, re.I | re.S)
    head = head_match.group(1) if head_match else dom_html[:20000]

    def meta(name: str) -> str | None:
        m = re.search(
            rf'<meta[^>]+(?:name|property)=["\']{re.escape(name)}["\'][^>]*>', head, re.I)
        if not m:
            return None
        c = re.search(r'content=["\'](.*?)["\']', m.group(0), re.I | re.S)
        return c.group(1).strip() if c else None

    canon = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*>', head, re.I)
    canon_href = None
    if canon:
        h = re.search(r'href=["\'](.*?)["\']', canon.group(0), re.I)
        canon_href = h.group(1).strip() if h else None

    hreflang = []
    for lk in re.findall(r'<link[^>]+rel=["\']alternate["\'][^>]*>', head, re.I):
        if "hreflang" in lk.lower():
            lang = re.search(r'hreflang=["\'](.*?)["\']', lk, re.I)
            href = re.search(r'href=["\'](.*?)["\']', lk, re.I)
            hreflang.append({"lang": lang.group(1) if lang else "",
                             "href": href.group(1) if href else ""})
    return {
        "canonical": canon_href,
        "meta_description": meta("description"),
        "viewport_meta": meta("viewport"),
        "og_image": meta("og:image"),
        "hreflang": hreflang,
    }


def _slugify(label: str, idx: int, seen: set[str]) -> str:
    raw = re.sub(r"[^a-z0-9-]", "", label.lower().replace(" ", "-").replace("_", "-"))
    raw = raw.strip("-")[:60]
    if not raw or not re.match(r"^[a-z]", raw):
        raw = f"section-{idx + 1}"
    slug, n = raw, 2
    while slug in seen:
        slug = f"{raw}-{n}"[:60]
        n += 1
    seen.add(slug)
    return slug


def _build_elements(v1: dict, vh: int) -> list[dict]:
    out = []
    for i, el in enumerate(v1.get("elements", []) or []):
        tag = ((el.get("tag") or "").lower() or "div")[:32]
        text = (el.get("text") or "")[:240]
        cls = (el.get("class") or "")[:240]
        y = max(0.0, float(el.get("y", 0)))
        out.append({
            "e_index": f"e{i}",
            "tag": tag,
            "selector": (el.get("selector") or tag)[:512],
            "rect": {
                "x": max(0.0, float(el.get("x", 0))),
                "y": y,
                "width": max(0.0, float(el.get("width", 0))),
                "height": max(0.0, float(el.get("height", 0))),
            },
            "scroll_y_at_capture": 0,
            "role": IMPLICIT_ROLE.get(tag, "group"),
            "accessible_name": (text or cls)[:240],
            "text_content": text,
            "is_above_fold": y < float(vh),
            "is_sticky": False,
            "is_offscreen": not bool(el.get("visible", True)),
        })
    return out


def _build_sections(v1: dict, device: str, page_height: int, page_title: str, vh: int) -> list[dict]:
    # Shallow-copy section rows so enrichment never mutates the caller's v1.
    raw = [dict(s) for s in sorted(v1.get("sections", []) or [],
                                   key=lambda s: int(s.get("scrollY", 0)))]
    # Mirror acquire_url.py: dedupe labels + route clusters via the same helpers.
    sec_hints.make_section_labels_unique(raw)
    sec_hints.enrich_baton_sections(raw, page_title, device)

    seen: set[str] = set()
    out = []
    for idx, s in enumerate(raw):
        label = (s.get("label") or f"Section {idx + 1}")[:120]
        top = int(s.get("scrollY", 0))
        raw_bot = top + int(s.get("height", vh))
        if idx + 1 < len(raw):
            raw_bot = min(raw_bot, int(raw[idx + 1].get("scrollY", 0)) - 1)
        else:
            raw_bot = min(raw_bot, page_height)
        bot = max(raw_bot, top + 1)
        shot_idx = int(s.get("screenshot_index", idx + 1))
        shot = (f"section-{shot_idx}.jpg" if device == "desktop"
                else f"section-{shot_idx}-mobile.jpg")
        out.append({
            "label": label,
            "slug": _slugify(label, idx, seen),
            "clusters": list(s.get("clusters") or ["visual-cta"]),
            "scroll_y_top": top,
            "scroll_y_bottom": bot,
            "screenshot_ref": shot,
        })
    return out


def convert_baton(
    v1: dict,
    dom_html: str,
    *,
    device: str,
    engagement_id: str,
    captured_at: str | None = None,
) -> dict:
    """Convert an acquire_url.py-shape v1 baton to a schema-valid v2 baton.

    Pure: no filesystem access. Raises BatonConversionError on invalid inputs or
    if the produced baton fails schema/baton-v1.json validation.
    """
    if not _EID_RE.match(engagement_id or ""):
        raise BatonConversionError(
            f"engagement_id {engagement_id!r} must match YYYY-MM-DD-<8 hex>")
    if device not in ("desktop", "mobile"):
        raise BatonConversionError(f"device must be 'desktop' or 'mobile', got {device!r}")

    vp = v1.get("viewport") or {}
    dpr = float(vp.get("dpr") or (3 if device == "mobile" else 1))
    vw = int(vp.get("width") or (390 if device == "mobile" else 1920))
    vh = int(vp.get("height") or (844 if device == "mobile" else 1080))

    page_title = (v1.get("title") or "").strip()
    elements = _build_elements(v1, vh)

    el_bottom = max((e["rect"]["y"] + e["rect"]["height"] for e in elements), default=0.0)
    sec_bottom = max(
        (int(s.get("scrollY", 0)) + int(s.get("height", 0)) for s in v1.get("sections", []) or []),
        default=0)
    page_height = int(max(el_bottom, sec_bottom, vh))

    sections = _build_sections(v1, device, page_height, page_title, vh)

    head = _head_meta(dom_html)
    page_head: dict[str, Any] = {
        "canonical": head["canonical"],
        "meta_description": head["meta_description"],
        "viewport_meta": head["viewport_meta"],
        "og_image": head["og_image"],
        "schema_jsonld": v1.get("structured_data") or [],
        "hreflang": head["hreflang"],
    }
    if page_title:
        page_head["title"] = page_title[:256]

    v2 = {
        "schema_version": 1,
        "engagement_id": engagement_id,
        "device": device,
        "url": (v1.get("url_final") or v1.get("url") or "")[:2048],
        "captured_at": captured_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "viewport": {
            "width": vw,
            "height": vh,
            "dpr_requested": dpr,
            # v1 'overlays' carry no element index, so we cannot emit a schema-valid
            # overlays_detected[].e_index; record dpr fallback instead and leave
            # overlays empty (see capture_state below).
            "dpr_actual": 1.0 if v1.get("dpr_fallback") else dpr,
        },
        "capture_state": {
            "hydration": "pre-hydration" if v1.get("pre_hydration_warning") else "post-hydration",
            # A v1 baton never records which element was the overlay, and the schema
            # requires overlays_detected[].e_index to match ^e[0-9]+$ — so the only
            # schema-valid, honest choice is an empty list (not {"e_index": None}).
            "overlays_detected": [],
            "page_height_px": page_height,
        },
        "elements": elements,
        "sections": sections,
        "page_head": page_head,
    }
    _validate(v2)
    return v2


def convert_engagement(
    engagement_dir: str | Path,
    *,
    devices: tuple[str, ...] = ("desktop", "mobile"),
    out_dir: str | Path | None = None,
    engagement_id: str | None = None,
    captured_at: str | None = None,
) -> dict[str, dict]:
    """Convert the v1 batons in an engagement dir to v2, in place (or to out_dir).

    In-place mode is non-destructive: each device's original v1 baton is preserved
    as ``baton{,-mobile}.v1raw.json`` and the conversion always reads from that
    immutable raw, so re-running is idempotent and never clobbers the v1 with a v2.
    With ``out_dir`` set, the source dir is left entirely untouched (no backup).
    """
    engagement_dir = Path(engagement_dir)
    eid = engagement_id or engagement_dir.name
    dest_dir = Path(out_dir) if out_dir is not None else engagement_dir
    results: dict[str, dict] = {}

    for device in devices:
        suffix = "" if device == "desktop" else "-mobile"
        baton_path = engagement_dir / f"baton{suffix}.json"
        dom_path = engagement_dir / f"dom{suffix}.html"
        v1raw_path = engagement_dir / f"baton{suffix}.v1raw.json"

        if not baton_path.exists():
            print(f"[{device}] skip - {baton_path.name} not found", file=sys.stderr)
            results[device] = {"status": "skipped", "reason": f"{baton_path.name} not found",
                               "output": None, "v1raw": None, "warnings": []}
            continue

        if out_dir is None:
            # Preserve the original v1 once; thereafter always convert from it.
            if not v1raw_path.exists():
                shutil.copy2(baton_path, v1raw_path)
            source_path = v1raw_path
        else:
            source_path = baton_path  # never mutate the source dir

        v1 = json.loads(source_path.read_text(encoding="utf-8"))
        warnings: list[str] = []
        if dom_path.exists():
            dom_html = dom_path.read_text(encoding="utf-8", errors="ignore")
        else:
            dom_html = ""
            warnings.append(f"{dom_path.name} not found - page_head fields will be null")

        v2 = convert_baton(v1, dom_html, device=device, engagement_id=eid, captured_at=captured_at)

        for s in v2["sections"]:
            if not (engagement_dir / s["screenshot_ref"]).exists():
                warnings.append(f"referenced screenshot missing: {s['screenshot_ref']}")

        out_path = dest_dir / f"baton{suffix}.json"
        atomic_write_json(out_path, v2)
        note = f" [{len(warnings)} warning(s)]" if warnings else ""
        print(f"[{device}] wrote {out_path.name} "
              f"({len(v2['elements'])} elements, {len(v2['sections'])} sections){note}",
              file=sys.stderr)
        results[device] = {
            "status": "written",
            "output": out_path,
            "v1raw": v1raw_path if out_dir is None else None,
            "warnings": warnings,
        }

    return results


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(
        description="Convert acquire_url.py-shape v1 batons to the v2 schema in an engagement dir.")
    p.add_argument("engagement_dir", type=Path,
                   help="Engagement directory (named YYYY-MM-DD-<8 hex>) holding baton{,-mobile}.json + dom{,-mobile}.html")
    p.add_argument("--device", choices=["both", "desktop", "mobile"], default="both")
    p.add_argument("--out-dir", type=Path, default=None,
                   help="Write converted batons here instead of in place (source dir untouched, no .v1raw backup)")
    p.add_argument("--engagement-id", default=None,
                   help="Override the engagement_id (defaults to the directory name)")
    args = p.parse_args(argv)

    devices = ("desktop", "mobile") if args.device == "both" else (args.device,)
    try:
        results = convert_engagement(
            args.engagement_dir, devices=devices, out_dir=args.out_dir,
            engagement_id=args.engagement_id)
    except BatonConversionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0 if any(r["status"] == "written" for r in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
