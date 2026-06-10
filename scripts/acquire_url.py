#!/usr/bin/env python3
"""Acquire an ECP engagement folder for URL analysis (canonical acquirer).

This is the canonical deterministic acquirer for the Claude `/ecp:audit` path:
the acquirer subagent runs this script (see `skills/audit/SKILL.md`
§ "Dispatch Shape" and `workflows/acquire.md`).

Implements a report-compatible subset of `workflows/acquire.md`:
- resolves `agent-browser` in a Windows-friendly way (`shutil.which`)
- sets device/viewport
- navigates + settles
- captures viewport screenshots tiled to page height — up to 6 (desktop) / 12 (mobile)
  by default, contiguous with slight overlap (hash de-dupe + one retry on duplicates)
- extracts per-scroll element boxes and applies DPR scaling to match screenshot pixels
- captures basic computed style metadata
- writes DOM to `dom.html` (laptop/desktop) or `dom-mobile.html` (mobile)
- writes `baton.json` (laptop/desktop) or `baton-mobile.json` (mobile) for the report pipeline
- best-effort overlay dismissal + viewport-clear check before screenshots; tiered DOM preprocessing

When fitment / required `<select>` + disabled CTA is detected, an extra **configured** JPEG and
`configured_state` in the baton are written per `acquire.md` Step 1d. Section labels and cluster
slugs use `ecp_section_hints.py` (headings + keyword map). Some acquire steps (true parallel
named sessions, human section naming) remain Claude-side; URL evidence is still report-compatible.

Examples:
  python scripts/acquire_url.py --url "https://example.com"
  python scripts/acquire_url.py --url "https://example.com" --hybrid
  python scripts/acquire_url.py --url "https://example.com" --device laptop
  python scripts/acquire_url.py --url "https://example.com" --both
  python scripts/acquire_url.py --url "https://example.com" --devices desktop,mobile --goto-timeout 45
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import math
import shutil
import struct
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent


def _load_script_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _build_elements_js(expected_hostname: str) -> str:
    """Build the per-section element-extraction JS with a hard hostname
    guard baked in.

    The 2026-05-27 four-concurrent-audits batch revealed cross-engagement
    session contamination: while a slingmods.com audit was extracting
    elements, the headless browser session drifted to amazon.com (a
    concurrent audit's destination) and the slingmods mobile baton
    captured 51 Amazon "Sponsored" elements with 0 SlingMods elements.
    The contamination only surfaced because the ethics + content-seo
    specialists independently flagged "baton elements look like Amazon"
    — there was no acquisition-side guard.

    Post-fix: the eval payload checks ``window.location.hostname`` on
    every call and short-circuits to a structured contamination report
    instead of returning element rows. The Python side
    (``_check_for_contamination``) detects the sentinel and aborts the
    acquisition with a loud STATUS line. Re-running the acquirer in a
    fresh session is the documented recovery path.

    ``expected_hostname`` is inlined as a JS string literal — single
    quotes are escaped defensively even though valid hostnames cannot
    contain them.
    """
    # JSON-encode to inline as a safe string literal (handles any oddly-
    # named hostname characters that would otherwise break the JS string).
    expected_literal = json.dumps(expected_hostname)
    return (
        r"""
(function(){
  /* G16-followup (2026-05-27): cross-engagement contamination guard.
     Aborts and reports if the session drifted off the validated origin. */
  var __expected = """ + expected_literal + r""";
  var __actual = (window.location && window.location.hostname) || '';
  if (__actual !== __expected) {
    return {
      __contamination_detected: true,
      expected_hostname: __expected,
      actual_hostname: __actual,
      actual_href: (window.location && window.location.href) || ''
    };
  }
  return ['button', '[role="button"]', '.btn', 'a.btn',
   'h1', 'h2', 'h3',
   'img[alt]:not([alt=""])',
   '[class*="rating"]', '[class*="star"]', '[class*="review"]',
   '[class*="price"]', '[class*="trust"]', '[class*="badge"]',
   '[class*="cart"]', '[class*="checkout"]',
   'input[type="search"]', '[class*="search"]',
   '[class*="shipping"]', '[class*="guarantee"]',
   'form', 'nav', 'header', 'footer',
   '[class*="newsletter"]', '[class*="subscribe"]',
   '[class*="payment"]', '[class*="pay"]',
   '[class*="countdown"]', '[class*="timer"]', '[class*="urgency"]',
   '[class*="limited"]', '[class*="expire"]', '[class*="hurry"]',
   /* targeted additions (2026-06-03): hero controls the fixed allowlist missed —
      YMM dropdowns (native + JS-enhanced widgets), submit buttons, promo/announce
      bars, gallery thumbnails, and accessible-named controls. */
   'select', '[role="combobox"]', '[role="listbox"]',
   'input[type="submit"]', 'input[type="button"]',
   '[class*="dropdown"]', '[class*="gallery"]', '[class*="thumb"]',
   '[class*="announce"]', '[class*="promo"]', '[aria-label]'
  ].flatMap(function(sel) {
    try {
      return Array.from(document.querySelectorAll(sel)).slice(0, 10).map(function(el) {
        let r = el.getBoundingClientRect();
        const scrollY = window.scrollY || document.documentElement.scrollTop;
        const tag = el.tagName.toLowerCase();
        /* Native form controls (the YMM <select>, submit <input>, <button>)
           routinely render at width:0/height:0/opacity:0 before JS enhancement.
           Dropping them on size discards the exact control the hotspot needs
           (2026-06-02 hotspot diagnosis RC#1). Keep a zero-sized form control by
           anchoring it to its nearest sized ancestor (label/wrapper/enhanced
           widget rect); only fall through to the drop when no sized ancestor
           exists within 4 levels (truly invisible, nothing to pin). */
        const isFormControl = (tag === 'select' || tag === 'input' || tag === 'button');
        if (r.width === 0 || r.height === 0) {
          if (!isFormControl) return null;
          let anc = el.parentElement, ar = null, depth = 0;
          while (anc && depth < 4) {
            const pr = anc.getBoundingClientRect();
            if (pr.width > 0 && pr.height > 0) { ar = pr; break; }
            anc = anc.parentElement; depth++;
          }
          if (!ar) return null;
          r = ar;
        }
        if (r.bottom < 0 || r.top > window.innerHeight) return null;
        /* C10 (workflows/acquire.md §558-563): drop elements that exist in DOM
           but are not visible — display:none / visibility:hidden / aria-hidden=true.
           Before this guard, an opacity:0 or visibility:hidden element entered the
           baton as visible evidence and specialists cited it. _reveal_lazy_and_animations
           runs BEFORE extraction (acquire_url.py:958) and sets style.visibility='visible'
           on scroll-trigger / animate--* elements, so revealed heroes survive this filter. */
        try {
          const cs = window.getComputedStyle(el);
          if (cs && (cs.display === 'none' || cs.visibility === 'hidden')) return null;
          if (el.getAttribute && el.getAttribute('aria-hidden') === 'true') return null;
        } catch(_) {}
        return {
          selector: sel,
          tag: tag,
          text: (el.textContent || '').trim().slice(0, 60),
          class: (el.className || '').toString().slice(0, 80),
          x: Math.max(0, Math.round(r.left)),
          y: Math.max(0, Math.round(r.top + scrollY)),
          width: Math.round(r.width),
          height: Math.round(r.height)
        };
      }).filter(Boolean);
    } catch(e) { return []; }
  });
})()
"""
    )


def _check_for_contamination(ev: Any) -> dict | None:
    """Detect the contamination sentinel returned by ``_build_elements_js``
    when the session drifted off the validated origin.

    Returns the sentinel dict (with keys ``expected_hostname``,
    ``actual_hostname``, ``actual_href``) when contamination is detected;
    otherwise None.

    The eval CAN double-encode the response (agent-browser wraps a JSON
    string around already-JSON content); both ``isinstance(ev, dict)`` and
    pre-unwrapped variants are handled by the caller's ``_eval_json_object``
    helper before this check runs.
    """
    if isinstance(ev, dict) and ev.get("__contamination_detected") is True:
        return ev
    return None

# In-viewport h1–h3 (largest) + human-readable scene (landmark / elementFromPoint walk) for section labels.
_SECTION_VIEW_JS = r"""(function(){
  var sy = (window.pageYOffset != null) ? window.pageYOffset : (document.documentElement && document.documentElement.scrollTop) || 0;
  var ih = window.innerHeight, iw = window.innerWidth;
  var cx = Math.min(iw / 2, 400);
  function bestHeading() {
    var nodes = document.querySelectorAll("h1,h2,h3");
    var best = "", bestA = 0;
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i], r = el.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) continue;
      if (r.bottom < 0 || r.top > ih) continue;
      var t = (el.textContent || "").trim().replace(/\s+/g, " ").slice(0, 100);
      if (!t) continue;
      var a = r.width * r.height;
      if (a > bestA) { bestA = a; best = t; }
    }
    return best;
  }
  function sceneFromPoint() {
    var pts = [ih * 0.2, ih * 0.45, ih * 0.65];
    var el = null;
    for (var p = 0; p < pts.length; p++) {
      try { el = document.elementFromPoint(cx, pts[p]); } catch (e) { el = null; }
      if (el) break;
    }
    if (!el) return "Main content";
    var n = 0, cur = el;
    while (cur && n++ < 15) {
      var t = (cur.tagName || "").toLowerCase();
      var role = (cur.getAttribute("role") || "").toLowerCase();
      var r = cur.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) { cur = cur.parentElement; continue; }
      if (t === "footer" || role === "contentinfo") return "Footer and site information";
      if (t === "header" || role === "banner") return "Site header and top navigation";
      if (t === "nav" || role === "navigation") return "Navigation and category links";
      if (t === "aside") return "Sidebar and supporting content";
      if (t === "main" || role === "main") {
        var hm = cur.querySelector("h1,h2,h3");
        if (hm) {
          var tx = (hm.textContent || "").trim().replace(/\s+/g, " ").slice(0, 75);
          if (tx) return "Main \u2014 " + tx;
        }
        return "Main content area";
      }
      if (t === "section" || t === "article") {
        var h2 = cur.querySelector("h1,h2,h3");
        var al = (cur.getAttribute("aria-label") || "").trim();
        if (h2) {
          var tt = (h2.textContent || "").trim().replace(/\s+/g, " ").slice(0, 85);
          if (tt) return tt;
        }
        if (al) return al.slice(0, 85);
        return t === "article" ? "Article body" : "Content section";
      }
      cur = cur.parentElement;
    }
    return "Content block";
  }
  var h = bestHeading();
  var line = sceneFromPoint();
  if (sy < 10) {
    if (h) {
      return { heading: h, scene: "Above the fold \u2014 " + (h.length > 70 ? h.slice(0, 67) + "..." : h) };
    }
    return { heading: h, scene: "Above the fold (hero, navigation, and primary CTA)" };
  }
  if (h && line && h.toLowerCase() !== line.toLowerCase() && line.indexOf(h) < 0) {
    return { heading: h, scene: (line + " \u2014 " + h).replace(/\s+/g, " ").trim().slice(0, 100) };
  }
  if (h) return { heading: h, scene: h.slice(0, 100) };
  return { heading: "", scene: (line || "").slice(0, 100) };
})()"""

_STYLES_JS = r"""
(function(){
  function rgbToHex(c){
    if (!c) return null;
    c = String(c);
    if (c.startsWith('#')) {
      if (c.length === 4) {
        return ('#' + c[1]+c[1] + c[2]+c[2] + c[3]+c[3]).toLowerCase();
      }
      return c;
    }
    const m = c.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const parts = m[1].split(',').map(function(s){ return s.trim(); });
    if (parts.length < 3) return null;
    const r = parseInt(parts[0], 10), g = parseInt(parts[1], 10), b = parseInt(parts[2], 10);
    if (isNaN(r) || isNaN(g) || isNaN(b)) return null;
    return '#' + [r,g,b].map(function(n){
      return ('0' + n.toString(16)).slice(-2);
    }).join('');
  }
  const bodyBg = rgbToHex(getComputedStyle(document.body).backgroundColor) || '#ffffff';
  const p = document.querySelector('p');
  const h1 = document.querySelector('h1');
  const tEl = p || h1 || document.body;
  const text = rgbToHex(getComputedStyle(tEl).color) || '#000000';
  const btn = document.querySelector('button, [role="button"], .btn');
  const ctaBg = btn ? rgbToHex(getComputedStyle(btn).backgroundColor) : null;
  const a = document.querySelector('a');
  const link = a ? rgbToHex(getComputedStyle(a).color) : null;
  const main = document.querySelector('main');
  const container = main && main.firstElementChild ? main.firstElementChild : document.body.firstElementChild;
  const containerBg = container ? rgbToHex(getComputedStyle(container).backgroundColor) : null;
  return { bg: bodyBg, container_bg: containerBg || bodyBg, text: text, cta_bg: ctaBg, link: link };
})()
"""

_PRE_HYDRATION_JS = r"""
(function(){
  function countVisibleTextNodes(node){
    if (!node) return 0;
    if (node.nodeType === 3) {
      const t = (node.textContent || '').replace(/\s+/g, ' ').trim();
      if (!t) return 0;
      let p = node.parentNode;
      while (p) {
        const tag = (p.nodeName || '').toLowerCase();
        if (tag === 'script' || tag === 'style' || tag === 'noscript') return 0;
        p = p.parentNode;
      }
      return 1;
    }
    let total = 0;
    for (const c of node.childNodes) total += countVisibleTextNodes(c);
    return total;
  }
  return { count: countVisibleTextNodes(document.body) };
})()
"""

def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run(cmd: list[str], *, check: bool) -> int:
    p = subprocess.run(cmd, check=False, text=True)
    if check and p.returncode != 0:
        raise subprocess.CalledProcessError(p.returncode, cmd, output=p.stdout, stderr=p.stderr)
    return p.returncode


def _run_ab(
    agent_browser: str,
    sub: list[str],
    *,
    session: str | None,
    check: bool,
    timeout: float | None = None,
) -> int:
    cmd = _ab_bin(agent_browser, sub, session=session)
    try:
        p = subprocess.run(cmd, check=False, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("agent-browser command timed out") from exc
    if check and p.returncode != 0:
        raise RuntimeError(
            f"agent-browser failed ({p.returncode}): {' '.join(sub[:3])}… stderr={getattr(p, 'stderr', '')!r}"
        )
    return p.returncode


def _run_capture(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True, encoding="utf-8", errors="replace", shell=False)


@dataclass
class Viewport:
    width: int
    height: int
    dpr: float
    use_device: str | None  # e.g. "iPhone 14" for high-DPR mobile path


def device_profile(device: str) -> Viewport:
    d = device.lower()
    if d == "laptop":
        return Viewport(1440, 900, 1.0, None)
    if d == "desktop":
        return Viewport(1920, 1080, 1.0, None)
    if d == "mobile":
        return Viewport(390, 844, 3.0, "iPhone 14")
    raise SystemExit(f"Unknown device: {device}")


def section_screenshot_name(index: int, device: str) -> str:
    """Canonical per-section screenshot filename.

    Contract (single source of truth, shared with the validator and the
    converter):
      - desktop / laptop -> ``section-{index}.jpg``
      - mobile           -> ``section-{index}-mobile.jpg``

    This MUST match scripts/assembly/business_rules.py ``_SCREENSHOT_PATTERN``
    (``^section-[0-9]+(-mobile)?\\.jpg$``) and scripts/baton_v1_to_v2.py's
    ``screenshot_ref`` derivation. The name MUST NOT vary with single- vs
    multi-device runs: mobile-vs-non-mobile is the only axis, mirroring
    baton{,-mobile}.json and dom{,-mobile}.html. The historic ``{device}-``
    prefix in multi-device runs emitted e.g. ``desktop-section-1.jpg``, which
    the validator/converter rejected.
    """
    suffix = "-mobile" if str(device).lower() == "mobile" else ""
    return f"section-{int(index)}{suffix}.jpg"


def _resolve_agent_browser() -> str:
    ab = shutil.which("agent-browser")
    if not ab:
        raise SystemExit(
            "agent-browser is required for URL bootstrapping.\n"
            "Install:\n"
            "  npm install -g agent-browser && agent-browser install"
        )
    return ab


def _ensure_agent_browser() -> str:
    ab = _resolve_agent_browser()
    try:
        _ = _run_capture([ab, "--version"]).strip()
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            "agent-browser is present on PATH but failed to run.\n"
            f"Tried: {ab}\n"
            f"Details: {exc}"
        ) from exc
    return ab


def _ab_bin(agent_browser: str, args: list[str], *, session: str | None) -> list[str]:
    if session:
        return [agent_browser, "--session", session, *args]
    return [agent_browser, *args]


def _eval_args(source: str) -> list[str]:
    """Return `eval` args with the JS base64-encoded.

    On Windows, `agent-browser` resolves to a .ps1/.cmd npm shim that re-parses
    argv through PowerShell/cmd. JS payloads containing double-quotes or shell
    metacharacters (`"`, `(`, `)`, `{`, `}`, `>`, `&&`, `|`) get mangled or
    truncated by the shim's parser (PowerShell does not treat CMD-style `\\"` as an
    escape, so it ends the string early), producing `SyntaxError: Unexpected end of
    input` in the browser. base64 is metacharacter-free, so it round-trips intact;
    agent-browser decodes it via `-b/--base64`.
    """
    b64 = base64.b64encode(source.encode("utf-8")).decode("ascii")
    return ["eval", "-b", b64]


def _parse_trailing_json(stdout: str) -> Any:
    s = stdout.strip()
    if not s:
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
    for line in reversed(lines):
        if not line.startswith("{") and not line.startswith("["):
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return None


def _unwrap_eval(value: Any) -> Any:
    """Unwrap agent-browser's JSON-encoded eval result.

    agent-browser JSON-encodes the value an `eval` returns. Our JS wraps payloads
    in `JSON.stringify(...)`, so results arrive double-encoded: a JSON string whose
    content is itself JSON. Decode the inner layer when present; leave plain,
    non-JSON strings and already-decoded structures untouched. Safe whether
    agent-browser single- or double-encodes.
    """
    if isinstance(value, str) and value.strip():
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _parse_eval_json_string(stdout: str) -> str:
    payload = _unwrap_eval(_parse_trailing_json(stdout))
    return payload if isinstance(payload, str) else ""


def _eval_json_object(agent_browser: str, session: str | None, source: str) -> Any:
    source = " ".join(str(source).split())
    out = _run_capture(_ab_bin(agent_browser, _eval_args(source), session=session))
    return _unwrap_eval(_parse_trailing_json(out))


def _file_md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _jpeg_size(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()
    if len(data) < 2 or data[0:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 1 < len(data) and i < 20_000_000:
        if data[i] != 0xFF:
            i += 1
            continue
        while i < len(data) and data[i] == 0xFF:
            i += 1
        if i >= len(data):
            return None
        marker = data[i]
        i += 1
        if marker in (0xD8, 0xD9):
            continue
        if i + 1 >= len(data):
            return None
        seg_len = struct.unpack(">H", data[i : i + 2])[0]
        if seg_len < 2 or i + seg_len > len(data):
            return None
        if marker in (0xC0, 0xC1, 0xC2):
            if seg_len < 8:
                return None
            h, w = struct.unpack(">HH", data[i + 5 : i + 9])
            return int(w), int(h)
        i += seg_len
    return None


def _read_image_natural_size(path: Path) -> tuple[int, int]:
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        wh = _jpeg_size(path)
        if wh is not None:
            return wh
    if path.suffix.lower() == ".png":
        wh = _png_size(path)
        if wh is not None:
            return wh
    return (0, 0)


def _png_size(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()
    # PNG signature + IHDR chunk
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    if data[12:16] != b"IHDR":
        return None
    w = struct.unpack(">I", data[16:20])[0]
    h = struct.unpack(">I", data[20:24])[0]
    if w <= 0 or h <= 0:
        return None
    return int(w), int(h)


def _to_jpg_inplace(path: Path, *, quality: int) -> Path:
    """Return a .jpg path next to `path`, converting with system tools if available."""
    if path.suffix.lower() in {".jpg", ".jpeg"}:
        return path
    out = path.with_suffix(".jpg")

    # macOS native converter
    if shutil.which("sips"):
        cmd = [
            "sips", "-s", "format", "jpeg",
            "-s", "formatOptions", str(max(0, min(100, quality))),
            str(path), "--out", str(out),
        ]
        p = subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if p.returncode == 0 and out.exists():
            try:
                path.unlink()
            except OSError:
                pass
            return out

    # ImageMagick fallback
    if shutil.which("magick"):
        cmd = ["magick", str(path), "-quality", str(max(0, min(100, quality))), str(out)]
        p = subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if p.returncode == 0 and out.exists():
            try:
                path.unlink()
            except OSError:
                pass
            return out

    # No converter available; keep original format and record format_override.
    return path


def _build_viewport_dpr_fields(
    *, inner_w: int, inner_h: int, dpr_requested: float, dpr_actual: float
) -> dict[str, Any]:
    """C15 (schema/baton-v1.json viewport.dpr_requested/dpr_actual): assemble the
    viewport sub-object with the full request-vs-actual DPR split so the
    chromium_headless_shell silent-1x-on-mobile fallback surfaces in the baton
    instead of being collapsed to a single ``dpr`` value.

    Pre-fix the acquirer wrote only ``viewport.dpr`` (the observed value), which
    meant a mobile capture that fell back to 1x DPR looked identical to a true
    1x desktop capture; specialists making contrast/text-size claims had no way
    to know the screenshots were undersampled. The schema (v2 deepen-plan
    architecture, validated by scripts/baton_v1_to_v2.py) requires both
    ``dpr_requested`` and ``dpr_actual``; ``dpr_fallback`` is the convenience
    boolean the v1->v2 converter reads (baton_v1_to_v2.py:246). ``dpr`` is kept
    set to ``dpr_actual`` so existing readers (scripts/report/geometry.py's
    ``viewport_dpr`` fallback chain) keep returning the actual scaling factor.
    """
    fallback = abs(float(dpr_actual) - float(dpr_requested)) > 0.05
    return {
        "width": int(inner_w),
        "height": int(inner_h),
        "dpr": _dpr_int_from(float(dpr_actual)),
        "dpr_requested": float(dpr_requested),
        "dpr_actual": float(dpr_actual),
        "dpr_fallback": bool(fallback),
    }


def _section_occluded_from_viewport_state(state: Any, *, threshold_pct: float = 30.0) -> bool:
    """C14 (workflows/acquire.md §363): a section is occluded when an overlay
    covers > ``threshold_pct`` % of the viewport at that scroll position.

    ``state`` is the dict returned by ``ecp_acquire_overlays.read_viewport_state``
    (``{clear: bool, blocking: [{coverage: <percent int>}, ...]}``). The
    ``blocking`` entries carry per-overlay viewport coverage in integer percent;
    we treat the section as occluded only when any single overlay exceeds the
    contract threshold (default 30 %). On a non-dict / missing-blocking state we
    fall back to ``not state.get('clear')`` so a totally-broken probe still
    surfaces as occluded (fail loud, not silent).
    """
    if not isinstance(state, dict):
        return False
    blocking = state.get("blocking")
    if isinstance(blocking, list):
        for b in blocking:
            if not isinstance(b, dict):
                continue
            try:
                cov = float(b.get("coverage") or 0)
            except (TypeError, ValueError):
                cov = 0.0
            if cov > float(threshold_pct):
                return True
        return False
    return not bool(state.get("clear"))


def _dpr_int_from(dpr: float) -> int:
    # `scripts/report/*` uses int() on viewport.dpr — keep to sane integer steps.
    if dpr <= 0:
        return 1
    r = float(dpr)
    if abs(r - round(r)) < 0.05:
        return max(1, int(round(r)))
    return max(1, int(round(r)))


def _dpr_scale_element_css_to_phys(el: dict[str, Any], dpr: int) -> dict[str, Any]:
    out = dict(el)
    for k in ("x", "y", "width", "height"):
        v = int(out.get(k, 0) or 0)
        # Clamp to >=0: off-canvas elements yield negative getBoundingClientRect
        # coords, which schema/baton-v1.json (rect.* minimum: 0) rejects.
        out[k] = max(0, int(round(v * dpr)))
    return out


def _dedupe_elements_phys(rows: list[dict[str, Any]], cap: int) -> list[dict[str, Any]]:
    best: dict[tuple[str, int, int], dict[str, Any]] = {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        sel = str(r.get("selector", ""))
        x = int(r.get("x", 0) or 0)
        y = int(r.get("y", 0) or 0)
        w = int(r.get("width", 0) or 0)
        h = int(r.get("height", 0) or 0)
        area = max(0, w) * max(0, h)
        key = (sel, x, y)
        cur = best.get(key)
        if cur is None or area > int(cur.get("_area", 0) or 0):
            rr = dict(r)
            rr["visible"] = True
            rr["_area"] = area
            best[key] = rr
    out = list(best.values())
    out.sort(key=lambda e: int(e.get("_area", 0) or 0), reverse=True)
    for e in out:
        e.pop("_area", None)
    return out[:cap]


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _metrics(agent_browser: str, session: str | None) -> dict[str, Any]:
    m = _eval_json_object(
        agent_browser,
        session,
        "JSON.stringify({"
        "innerW: window.innerWidth,"
        "innerH: window.innerHeight,"
        "dpr: window.devicePixelRatio || 1,"
        "docH: Math.max("
        "  document.documentElement ? document.documentElement.scrollHeight : 0,"
        "  document.body ? document.body.scrollHeight : 0"
        ")}"
        ")",
    )
    return m if isinstance(m, dict) else {}


def _count_visible_text(agent_browser: str, session: str | None) -> int:
    c = _eval_json_object(agent_browser, session, f"JSON.stringify({_PRE_HYDRATION_JS})")
    if not isinstance(c, dict):
        return 0
    try:
        return int(c.get("count") or 0)
    except (TypeError, ValueError):
        return 0


# Pre-capture reveal: many themes (notably Shopify Dawn + its derivatives) hide
# above-fold content behind scroll-triggered reveal animations (`.scroll-trigger
# .animate--fade-in`, `opacity:0` until an IntersectionObserver fires) and behind
# lazy-loaded images / background media. A cold headless capture at scroll-y=0
# catches these UNPAINTED, so the hero renders as a black/empty void and its
# elements (heading, image) are filtered as `opacity:0` -> not visible. That
# produced the awdmods 2026-06-08 false "empty hero" finding cascade. Firing the
# reveals + eager-loading lazy media BEFORE capture is the root-cause fix.
_REVEAL_LAZY_AND_ANIMATIONS_JS = """JSON.stringify((function(){
  var r={lazy_imgs:0, reveal_els:0, error:null};
  try {
    document.querySelectorAll('img[loading="lazy"]').forEach(function(img){ img.loading='eager'; r.lazy_imgs++; });
    document.querySelectorAll('img[data-src],img[data-srcset],source[data-srcset]').forEach(function(el){
      if(el.dataset.src && !el.getAttribute('src')) el.setAttribute('src', el.dataset.src);
      if(el.dataset.srcset && !el.getAttribute('srcset')) el.setAttribute('srcset', el.dataset.srcset);
      r.lazy_imgs++;
    });
    document.querySelectorAll('.scroll-trigger,[class*="animate--"],[data-cascade]').forEach(function(el){
      el.classList.remove('scroll-trigger--offscreen');
      el.classList.add('scroll-trigger--active');
      el.style.opacity='1'; el.style.transform='none'; el.style.visibility='visible';
      r.reveal_els++;
    });
    var s=document.createElement('style');
    s.setAttribute('data-ecp-reveal','1');
    s.textContent='.scroll-trigger,[class*="animate--"]{opacity:1!important;transform:none!important;visibility:visible!important;}*{animation-duration:0s!important;transition-duration:0s!important;}';
    (document.head||document.documentElement).appendChild(s);
    var y=window.scrollY||0;
    window.scrollTo(0, Math.min((document.body?document.body.scrollHeight:0)||0, window.innerHeight));
    window.dispatchEvent(new Event('scroll'));
    window.scrollTo(0, y);
    window.dispatchEvent(new Event('scroll'));
  } catch(e){ r.error=String((e&&e.message)||e); }
  return r;
})())"""


def _reveal_lazy_and_animations(ev) -> dict[str, Any]:
    """Force scroll-trigger reveal animations visible and eager-load lazy media
    before capture, so above-fold heroes/banners paint. Best-effort: any failure
    is swallowed (a non-revealing page captures as before). Returns a small report
    (counts) for the trace. ``ev`` is the engagement's JSON-eval callable."""
    try:
        out = ev(_REVEAL_LAZY_AND_ANIMATIONS_JS)
        return out if isinstance(out, dict) else {}
    except (OSError, RuntimeError, ValueError, TypeError):
        return {}


def _outer_html(agent_browser: str, session: str | None) -> str:
    out = _run_capture(
        _ab_bin(
            agent_browser,
            _eval_args(
                "(function(){"
                "  var el = document.documentElement;"
                "  if (!el) return JSON.stringify('');"
                "  return JSON.stringify(el.outerHTML || '');"
                "})()"
            ),
            session=session,
        )
    )
    return _parse_eval_json_string(out)


# Per-device viewport-screenshot caps. Mobile PDPs (390x844 CSS px) run far
# taller than desktop, so a universal cap of 6 left ~700px gaps between evenly
# spaced shots and stranded most of the page with no section image to anchor
# hotspots to (Root Cause #2 of docs/2026-06-02-hotspot-placement-diagnosis.md).
# Mobile now tiles contiguously up to MAX_SCREENSHOTS_MOBILE; both caps bound
# audit cost. SCROLL_OVERLAP_FACTOR adds a small per-tile overlap so an element
# straddling a viewport boundary still lands whole inside one shot.
MAX_SCREENSHOTS_DESKTOP = 6
MAX_SCREENSHOTS_MOBILE = 12
SCROLL_OVERLAP_FACTOR = 1.1


def _device_screenshot_cap(device: str) -> int:
    return MAX_SCREENSHOTS_MOBILE if str(device).lower() == "mobile" else MAX_SCREENSHOTS_DESKTOP


def _plan_scroll_ys(
    *,
    max_scroll: int,
    inner_h: int,
    doc_h: int,
    max_shots: int,
    overlap: float = SCROLL_OVERLAP_FACTOR,
) -> list[int]:
    max_shots = max(1, int(max_shots))
    n_by_page = max(1, int(math.ceil((doc_h / max(1, inner_h)) * max(1.0, float(overlap)))))
    n = min(max_shots, n_by_page)
    if n == 1:
        ys = [0]
    elif max_scroll <= 0:
        ys = [0] * n
    else:
        ys = [int(round((i * max_scroll) / (n - 1))) for i in range(n)]
    ys = [max(0, min(int(y), max_scroll)) for y in ys]

    out: list[int] = []
    seen: set[int] = set()
    for y in ys:
        if y not in seen:
            out.append(y)
            seen.add(y)
    return out if out else [0]


_CONF_ORDER = {"Low": 0, "Medium": 1, "High": 2}


def _worse_confidence(a: str, b: str) -> str:
    ca = _CONF_ORDER.get(a, 1)
    cb = _CONF_ORDER.get(b, 1)
    return a if ca < cb else b


@dataclass
class _DeviceRunInfo:
    device: str
    baton_name: str
    dom_name: str
    inner_w: int
    inner_h: int
    dpr_i: int
    n_shots: int
    n_sections: int
    dom_size: int
    dom_mode: str
    status: str
    page_href: str
    page_title: str | None
    confidence: str
    url_arg: str
    n_elements: int
    occluded_sections: int
    scroll_failed_sections: int
    pre_hydration_warning: bool
    blockers_count: int
    recovery_pass: bool = False


def _hybrid_gate_reasons(info: _DeviceRunInfo) -> list[str]:
    """Return quality-gate failures for fast-pass URL bootstrap output."""
    reasons: list[str] = []
    if info.status != "COMPLETE":
        reasons.append(f"status={info.status}")
    if info.n_sections < 3:
        reasons.append(f"sections<{3} ({info.n_sections})")
    if info.n_elements < 12:
        reasons.append(f"elements<{12} ({info.n_elements})")
    if info.occluded_sections > 0:
        reasons.append(f"occluded_sections={info.occluded_sections}")
    if info.scroll_failed_sections > 1:
        reasons.append(f"scroll_failed_sections>{1} ({info.scroll_failed_sections})")
    if info.pre_hydration_warning:
        reasons.append("pre_hydration_warning=true")
    return reasons


def _parse_devices(ns: argparse.Namespace) -> list[str]:
    if getattr(ns, "both", False):
        return ["desktop", "mobile"]
    raw = (getattr(ns, "devices", None) or "").strip()
    if raw:
        parts = [p.strip().lower() for p in raw.split(",") if p.strip()]
        valid = {"laptop", "desktop", "mobile"}
        for p in parts:
            if p not in valid:
                raise SystemExit(f"Invalid device in --devices: {p} (use laptop, desktop, mobile)")
        return parts
    d = (ns.device or "desktop").strip().lower()
    if d not in {"laptop", "desktop", "mobile"}:
        raise SystemExit(f"Invalid --device: {d}")
    return [d]


def _run_one_device(
    *,
    device: str,
    file_prefix: str,
    url: str,
    engagement_id: str,
    eng_dir: Path,
    agent_browser: str,
    ecp_dom: Any,
    ecp_ov: Any,
    sec_hints: Any,
    ecp_cfg: Any,
    max_screenshots: int,
    settle_seconds: float,
    post_scroll_wait: float,
    goto_timeout: float,
    overlay_rounds: int = 6,
    overlay_pause_s: float = 1.0,
    recovery_pass: bool = False,
) -> tuple[int, _DeviceRunInfo | None]:
    preprocess_acquisition_dom = ecp_dom.preprocess_acquisition_dom
    prof = device_profile(device)
    session = f"ecp-cursor-{engagement_id}"
    baton_name = "baton-mobile.json" if device == "mobile" else "baton.json"
    dom_name = "dom-mobile.html" if device == "mobile" else "dom.html"

    # G16-followup (2026-05-27): derive the expected hostname from the input
    # URL so the per-section element extraction can guard against cross-
    # engagement session contamination (a concurrent acquirer navigating
    # to a different domain in the shared headless browser session). The
    # validated hostname is what the elements JS checks `window.location.
    # hostname` against on every call; mismatch aborts the run. Refined
    # from the actual landed hostname below (after goto + redirect resolve)
    # so www-vs-no-www and trailing-slash redirects don't false-trigger.
    from urllib.parse import urlparse as _urlparse
    expected_hostname = (_urlparse(url).hostname or "").lower()

    _run(_ab_bin(agent_browser, ["close"], session=session), check=False)
    if prof.use_device:
        _run(_ab_bin(agent_browser, ["set", "device", prof.use_device], session=session), check=True)
    else:
        _run(
            _ab_bin(
                agent_browser, ["set", "viewport", str(prof.width), str(prof.height)], session=session
            ),
            check=True,
        )
    try:
        _run_ab(
            agent_browser, ["goto", url], session=session, check=True, timeout=goto_timeout
        )
    except (RuntimeError, OSError) as exc:
        msg = str(exc).lower()
        if "timed out" in msg or "timeout" in msg:
            print("STATUS: BLOCKED - navigation timed out", file=sys.stderr)
            return 2, None
        print(f"ERROR: navigation failed: {exc}", file=sys.stderr)
        return 1, None

    time.sleep(max(0.0, float(settle_seconds)))

    def _ev(src: str) -> Any:
        return _eval_json_object(agent_browser, session, src)

    loc0 = _ev("JSON.stringify({href: String(location.href || ''), title: String(document.title || '')})")
    if not isinstance(loc0, dict):
        loc0 = {}
    page_href_early = str(loc0.get("href") or "")
    page_title_early = str(loc0.get("title") or "")

    # G16-followup (2026-05-27): refine the contamination-guard hostname
    # baseline using the actual LANDED hostname (after any www-vs-no-www
    # or trailing-slash redirects), so the per-section guard doesn't
    # false-trigger on a benign redirect target. The guardrails check
    # below already accepts cross-subdomain landings on the SAME
    # registrable domain — this guard mirrors that intent and only
    # fires on a true cross-engagement drift (e.g. slingmods → amazon).
    _landed_hostname = (_urlparse(page_href_early).hostname or "").lower()
    if _landed_hostname:
        expected_hostname = _landed_hostname

    g_reason = ecp_ov.guardrails_fail_reason(request_url=url, final_href=page_href_early or url)
    if g_reason:
        print(f"STATUS: BLOCKED - {g_reason}", file=sys.stderr)
        return 2, None
    pwd = _ev('JSON.stringify(!!document.querySelector(\'input[type="password"]\'))')
    if str(pwd).strip().lower() == "true":
        print("STATUS: BLOCKED - page requires authentication (password field).", file=sys.stderr)
        return 2, None

    if _count_visible_text(agent_browser, session) < 10:
        time.sleep(3.0)

    ecp_ov.dismiss_overlays(
        lambda s: _ev(s),
        rounds=max(1, int(overlay_rounds)),
        pause_s=max(0.1, float(overlay_pause_s)),
    )
    ecp_ov.force_remove_blocking_overlays(lambda s: _ev(s))
    time.sleep(0.5)
    ecp_ov.force_remove_blocking_overlays(lambda s: _ev(s))
    time.sleep(0.5)
    vp0 = ecp_ov.read_viewport_state(lambda s: _ev(s))
    viewport_ok = bool(vp0.get("clear")) if isinstance(vp0, dict) else False
    blockers: list[Any] = []
    if isinstance(vp0, dict) and isinstance(vp0.get("blocking"), list):
        blockers = list(vp0.get("blocking") or [])

    timer_baton: dict[str, Any] | None = ecp_ov.verify_timers(lambda s: _ev(s), sleep_s=10.0)

    # Reveal scroll-trigger animations + eager-load lazy media BEFORE capture so
    # above-fold heroes/banners actually paint (root-cause fix for the black-hero
    # false-finding cascade). Then give images a beat to decode.
    reveal = _reveal_lazy_and_animations(_ev)
    if reveal:
        print(
            f"REVEAL: forced {reveal.get('reveal_els', 0)} scroll-trigger/animation "
            f"elements visible, eager-loaded {reveal.get('lazy_imgs', 0)} lazy images"
            + (f" (error: {reveal['error']})" if reveal.get("error") else ""),
            file=sys.stderr,
        )
        time.sleep(1.0)

    m0 = _metrics(agent_browser, session)
    inner_w = int(m0.get("innerW") or prof.width)
    inner_h = int(m0.get("innerH") or prof.height)
    doc_h = int(m0.get("docH") or inner_h)
    # C15 (schema/baton-v1.json viewport.dpr_requested/dpr_actual): record the
    # full request-vs-actual split so the downstream v1->v2 converter
    # (scripts/baton_v1_to_v2.py:246 reads `dpr_fallback`) can surface the
    # chromium_headless_shell silent-1x-on-mobile downgrade instead of papering
    # over it with a single observed dpr.
    dpr_requested = float(prof.dpr)
    dpr_actual = float(m0.get("dpr") or prof.dpr)
    dpr = dpr_actual
    dpr_i = _dpr_int_from(dpr)
    dpr_fallback = abs(dpr_actual - dpr_requested) > 0.05

    _req_shots = int(max_screenshots)
    # 0 (the default) = auto per-device cap; an explicit nonzero value overrides it.
    max_shots_eff = _device_screenshot_cap(device) if _req_shots <= 0 else _req_shots
    if not viewport_ok:
        max_shots_eff = 1
        print(
            "STATUS: PARTIAL - viewport not clear after overlay handling; "
            f"capturing {max_shots_eff} reference screenshot(s) only (see `workflows/acquire.md` Step 1b).",
            file=sys.stderr,
        )

    max_scroll = max(0, doc_h - inner_h)
    scroll_ys = _plan_scroll_ys(
        max_scroll=max_scroll, inner_h=inner_h, doc_h=doc_h, max_shots=max_shots_eff
    )

    def _scroll_to_y(target_y: int) -> int:
        src = (
            "JSON.stringify((function(t){"
            "window.scrollTo({top: t, behavior: 'instant'});"
            "return {t: t, y: window.scrollY};"
            f"}})({int(target_y)}))"
        )
        r = _ev(src)
        y_used = int(target_y)
        if isinstance(r, dict):
            try:
                y_used = int(float(r.get("y", target_y)))
            except (TypeError, ValueError):
                y_used = int(target_y)
        if abs(y_used - int(target_y)) > 50:
            time.sleep(1.0)
            r2 = _ev(src)
            if isinstance(r2, dict):
                try:
                    y_used = int(float(r2.get("y", y_used)))
                except (TypeError, ValueError):
                    pass
        time.sleep(max(0.0, float(post_scroll_wait)))
        return y_used

    def _cfg_shot(out_path: Path, quality: int) -> tuple[Path, str, str | None, str]:
        _run_capture(
            _ab_bin(
                agent_browser,
                [
                    "screenshot",
                    "--json",
                    "--screenshot-format",
                    "jpeg",
                    "--screenshot-quality",
                    str(quality),
                    str(out_path),
                ],
                session=session,
            )
        )
        if not out_path.exists():
            raise RuntimeError(f"screenshot not written: {out_path}")
        p = _to_jpg_inplace(out_path, quality=max(60, int(quality)))
        fmt = None
        if p.suffix.lower() not in {".jpg", ".jpeg"}:
            fmt = p.suffix.lstrip(".") or "bin"
        h = _file_md5(p)
        if p != out_path and p.resolve() != out_path.resolve():
            out_path.parent.mkdir(parents=True, exist_ok=True)
            p.replace(out_path)
        return out_path, h, fmt, out_path.suffix.lower()

    seen_hashes: set[str] = set()
    screenshots: list[dict[str, Any]] = []
    section_rows: list[dict[str, Any]] = []
    element_rows: list[dict[str, Any]] = []

    for i, y in enumerate(scroll_ys, start=1):
        y_used = _scroll_to_y(int(y))
        try:
            hout = _run_capture(
                _ab_bin(
                    agent_browser, _eval_args(f"JSON.stringify({_SECTION_VIEW_JS})"), session=session
                )
            )
            v = _parse_trailing_json(hout)
        except (OSError, RuntimeError, subprocess.CalledProcessError):
            v = None
        if isinstance(v, dict):
            ht = str(v.get("heading") or "").strip()
            scene = str(v.get("scene") or "").strip()
        else:
            ht, scene = "", ""
        rel_name = section_screenshot_name(i, device)
        out_path = eng_dir / rel_name
        label_guess = sec_hints.section_label(
            index=i,
            scroll_y=y_used,
            heading=ht,
            page_title=page_title_early,
            device=device,
            human_scene=scene,
        )

        def _shot(quality: int) -> tuple[Path, str, str | None, str]:
            _run_capture(
                _ab_bin(
                    agent_browser,
                    [
                        "screenshot",
                        "--json",
                        "--screenshot-format",
                        "jpeg",
                        "--screenshot-quality",
                        str(quality),
                        str(out_path),
                    ],
                    session=session,
                )
            )
            if not out_path.exists():
                raise RuntimeError(f"screenshot not written: {out_path}")
            p = _to_jpg_inplace(out_path, quality=max(60, int(quality)))
            fmt = None
            if p.suffix.lower() not in {".jpg", ".jpeg"}:
                fmt = p.suffix.lstrip(".") or "bin"
            h = _file_md5(p)
            if p != out_path:
                if p.resolve() != out_path.resolve():
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    p.replace(out_path)
            return out_path, h, fmt, out_path.suffix.lower()

        path, hsh, fmt_override, _ext = _shot(80)

        if hsh in seen_hashes and i > 1:
            bump = max(1, min(50, inner_h // 20))
            y_try = int(min(max_scroll, y_used + bump))
            if y_try != y_used:
                y_used = _scroll_to_y(y_try)
                path, hsh, fmt_override, _ext = _shot(80)

        scroll_failed = hsh in seen_hashes
        if not scroll_failed:
            seen_hashes.add(hsh)
        if path.stat().st_size > 500_000:
            y_used = _scroll_to_y(y_used)
            path, hsh, fmt_override, _ext = _shot(60)
            if not scroll_failed and hsh not in seen_hashes:
                seen_hashes.add(hsh)

        nat_w, nat_h = _read_image_natural_size(path)
        if nat_w == 0 or nat_h == 0:
            print(f"ERROR: could not read screenshot dimensions: {path}", file=sys.stderr)
            return 1, None

        screenshots.append(
            {
                "index": i,
                "label": label_guess,
                "scrollY": y_used,
                "path": rel_name,
                "naturalWidth": int(nat_w),
                "naturalHeight": int(nat_h),
                "format_override": fmt_override,
            }
        )

        if i < len(scroll_ys):
            nxt = int(scroll_ys[i])
            hgt = max(0, nxt - y_used)
            hgt = min(inner_h, hgt)
        else:
            hgt = min(inner_h, max(0, doc_h - y_used))
        # C14 (workflows/acquire.md §363): re-probe occlusion at THIS scroll
        # position. Pre-fix the probe ran once at scroll_y=0 and that single
        # boolean was copied to every section row, so an overlay that appeared
        # mid-page (sticky chat widget, in-line video modal) silently went
        # un-flagged. Per-position values now land on the section they describe.
        vp_here = ecp_ov.read_viewport_state(lambda s: _ev(s))
        section_occluded = _section_occluded_from_viewport_state(vp_here)
        section_rows.append(
            {
                "label": label_guess,
                "heading": ht or None,
                "scrollY": y_used,
                "height": int(hgt),
                "clusters": [],
                "occluded": bool(section_occluded),
                "overlay_dismissed": bool(viewport_ok),
                "screenshot_index": i,
                "scroll_failed": bool(scroll_failed),
            }
        )

        ev = _eval_json_object(agent_browser, session, f"JSON.stringify({_build_elements_js(expected_hostname)})")
        contamination = _check_for_contamination(ev)
        if contamination is not None:
            # G16-followup (2026-05-27): the session drifted off the
            # validated origin mid-capture (almost certainly because a
            # concurrent acquirer in another engagement called `goto`
            # on a different URL — the headless browser global state
            # is shared). Abort loudly rather than silently capture
            # elements from the wrong page; the operator's recovery
            # is to re-run acquisition in a fresh session.
            print(
                f"ERROR: cross-engagement session contamination detected "
                f"during element extraction at scroll_y={y_used}. "
                f"Expected hostname={contamination.get('expected_hostname')!r}, "
                f"actual hostname={contamination.get('actual_hostname')!r} "
                f"(href={contamination.get('actual_href')!r}). "
                f"Re-acquire this engagement in a fresh agent-browser "
                f"session before proceeding.",
                file=sys.stderr,
            )
            return 1, None
        if not isinstance(ev, list):
            ev = []
        for item in ev:
            if not isinstance(item, dict):
                continue
            element_rows.append(_dpr_scale_element_css_to_phys(item, dpr_i))

    elements = _dedupe_elements_phys(element_rows, cap=140)

    styles_obj = _eval_json_object(agent_browser, session, f"JSON.stringify({_STYLES_JS})")
    if not isinstance(styles_obj, dict):
        styles_obj = {}

    c0 = _count_visible_text(agent_browser, session)
    if c0 < 5:
        time.sleep(5.0)
    c1 = _count_visible_text(agent_browser, session)
    pre_hydration = bool(c0 < 5 and c1 < 5)

    dom_text_raw = _outer_html(agent_browser, session)
    if not dom_text_raw.strip():
        print("ERROR: failed to read DOM HTML from page", file=sys.stderr)
        return 1, None

    dom_processed, dom_mode, structured, _ = preprocess_acquisition_dom(dom_text_raw)
    dom_path = eng_dir / dom_name
    _write_text(dom_path, dom_processed)

    # acquire.md Step 1d: optional second screenshot after choosing fitment / required options
    # (page mutates; default-state DOM is already on disk)
    configured_state: dict[str, Any] | None = None
    try:
        configured_state = ecp_cfg.try_configured_state_capture(
            ev=_ev,
            scroll_to_y=_scroll_to_y,
            eng_dir=eng_dir,
            shot_jpeg=_cfg_shot,
            file_prefix=file_prefix,
        )
    except (OSError, RuntimeError, TypeError, ValueError):
        configured_state = None

    loc = _ev("JSON.stringify({href: String(location.href), title: String(document.title || '')})")
    if not isinstance(loc, dict):
        loc = {}
    page_href = str(loc.get("href") or page_href_early)
    page_title = str(loc.get("title") or page_title_early)
    sec_hints.make_section_labels_unique(section_rows, screenshots)
    sec_hints.enrich_baton_sections(section_rows, page_title, device)
    sec_hints.enrich_screenshot_labels(screenshots, section_rows)

    status = "PARTIAL"
    if viewport_ok and bool(screenshots) and not pre_hydration:
        status = "COMPLETE"

    confidence = "Medium" if elements else "Low"
    if pre_hydration or not viewport_ok:
        confidence = "Low"

    baton: dict[str, Any] = {
        "status": status,
        "engagement_id": engagement_id,
        "device": device,
        "dpr": dpr_i,
        "dpr_fallback": bool(dpr_fallback),
        "viewport": _build_viewport_dpr_fields(
            inner_w=inner_w,
            inner_h=inner_h,
            dpr_requested=dpr_requested,
            dpr_actual=dpr_actual,
        ),
        "viewport_clear": viewport_ok,
        "screenshots": screenshots,
        "sections": section_rows,
        "url": url,
        "url_final": page_href or None,
        "title": page_title or None,
        "dom_file": dom_name,
        "dom_mode": dom_mode,
        "dom_size_bytes": dom_path.stat().st_size,
        "styles": {
            "bg": str(styles_obj.get("bg") or "#ffffff"),
            "container_bg": str(styles_obj.get("container_bg") or "#ffffff"),
            "text": str(styles_obj.get("text") or "#000000"),
            "cta_bg": str(styles_obj.get("cta_bg") or "#cccccc"),
            "link": str(styles_obj.get("link") or "#0000ee"),
        },
        "elements": elements,
        "pre_hydration_warning": pre_hydration,
        "structured_data": structured,
        "source_mode": "url",
    }
    if not viewport_ok and blockers:
        baton["viewport_blockers"] = blockers[:30]
    if timer_baton is not None:
        baton["timers"] = timer_baton
    if configured_state:
        baton["configured_state"] = configured_state

    _write_text(eng_dir / baton_name, json.dumps(baton, indent=2) + "\n")
    occluded_sections = sum(1 for s in section_rows if bool(s.get("occluded")))
    scroll_failed_sections = sum(1 for s in section_rows if bool(s.get("scroll_failed")))
    return (
        0,
        _DeviceRunInfo(
            device=device,
            baton_name=baton_name,
            dom_name=dom_name,
            inner_w=inner_w,
            inner_h=inner_h,
            dpr_i=dpr_i,
            n_shots=len(screenshots),
            n_sections=len(section_rows),
            dom_size=dom_path.stat().st_size,
            dom_mode=dom_mode,
            status=status,
            page_href=page_href or url,
            page_title=page_title or None,
            confidence=confidence,
            url_arg=url,
            n_elements=len(elements),
            occluded_sections=int(occluded_sections),
            scroll_failed_sections=int(scroll_failed_sections),
            pre_hydration_warning=bool(pre_hydration),
            blockers_count=len(blockers),
            recovery_pass=bool(recovery_pass),
        ),
    )


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI arg parser. Extracted from ``main`` so the default
    contract (e.g. ``--max-screenshots`` auto-sentinel = 0) is unit-testable
    without invoking acquisition (adversarial review 2026-06-03 §1, un-skips
    tests/test_acquire_scroll_tiling.py::TestCliDefault)."""
    parser = argparse.ArgumentParser(description="Bootstrap docs/ecp engagement for URL input (Cursor).")
    parser.add_argument("--url", required=True, help="https URL to load")
    parser.add_argument(
        "--engagement-id",
        default="",
        help="Engagement folder name under docs/ecp. Default: auto-generated",
    )
    parser.add_argument(
        "--device",
        default="desktop",
        choices=["laptop", "desktop", "mobile"],
        help="Device profile (used when --devices and --both are not set; default: desktop 1920×1080)",
    )
    parser.add_argument(
        "--devices",
        default="",
        help="Comma-separated devices for one engagement (e.g. desktop,mobile). At most one of laptop+desktop.",
    )
    parser.add_argument(
        "--both",
        action="store_true",
        help="Shorthand: capture desktop and mobile in the same folder (same as --devices desktop,mobile)",
    )
    parser.add_argument(
        "--goto-timeout",
        type=float,
        default=30.0,
        help="Timeout in seconds for agent-browser navigation (default: 30)",
    )
    parser.add_argument(
        "--max-screenshots",
        type=int,
        default=0,
        help=(
            "Max viewport screenshots per device; 0 = auto per-device cap "
            f"(desktop {MAX_SCREENSHOTS_DESKTOP}, mobile {MAX_SCREENSHOTS_MOBILE}). "
            "Pass a nonzero value to override for all devices."
        ),
    )
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=3.0,
        help="Seconds to wait after navigation before capture",
    )
    parser.add_argument(
        "--post-scroll-wait",
        type=float,
        default=0.75,
        help="Seconds to wait after scrolling before screenshot/element extraction",
    )
    parser.add_argument(
        "--hybrid",
        action="store_true",
        help=(
            "Fast-first with auto-recovery: run once, evaluate quality gates, "
            "then rerun one stricter acquisition pass per failing device."
        ),
    )
    parser.add_argument(
        "--allow-existing",
        action="store_true",
        help=(
            "Merge into an existing (non-empty) engagement dir instead of "
            "refusing it. Required when the audit lead pre-creates the dir with "
            "meta.json + audit-trace.log per SKILL phase order: lead-authored "
            "meta.json fields are preserved (merge, not clobber)."
        ),
    )
    return parser


def _prepare_engagement_dir(eng_dir: Path, allow_existing: bool) -> int | None:
    """Create the engagement dir. Return an exit code to ABORT, or None to proceed.

    By default a non-empty dir is refused (a fresh quick-scan must not stomp a
    prior engagement). With ``allow_existing`` the lead's pre-created dir — SKILL
    phase order writes ``meta.json`` + ``audit-trace.log`` BEFORE acquisition — is
    accepted so the acquirer can merge into it rather than being forced to wipe it
    (run-review C2: the two frozen contracts collided on the critical path).
    """
    if eng_dir.exists() and any(eng_dir.iterdir()) and not allow_existing:
        print(f"ERROR: engagement directory already exists and is not empty: {eng_dir}")
        print("  (pass --allow-existing to merge into a lead-created engagement dir)")
        return 1
    eng_dir.mkdir(parents=True, exist_ok=True)
    return None


def _merge_meta(eng_dir: Path, acquirer_meta: dict[str, Any]) -> dict[str, Any]:
    """Merge the acquirer's quick-scan meta into any lead-authored meta.json.

    Lead-authored fields WIN — the acquirer only fills gaps it owns — so a
    pre-existing engagement's ``engagement_status`` / ``report_state`` /
    ``reflection_state`` / ``clusters`` are never destroyed by acquisition
    (run-review C2: the acquirer was clobbering the lead's meta.json + trace to
    get past the non-empty-dir guard). On a fresh standalone quick-scan there is
    no existing meta.json yet, so the acquirer's own meta is written unchanged.
    """
    existing_path = eng_dir / "meta.json"
    if existing_path.exists():
        try:
            existing = json.loads(existing_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            existing = None
        if isinstance(existing, dict) and existing:
            return {**acquirer_meta, **existing}
    return acquirer_meta


def _upgrade_batons_to_v2(eng_dir: Path, devices, engagement_id: str) -> None:
    """Upgrade the freshly-written v1 batons to the v2 schema the downstream
    pipeline (validate / synthesize / render) consumes.

    Previously this conversion was an undocumented manual step the lead ran by
    hand; wiring it into acquisition removes that gap (run-review C1). Desktop +
    mobile only — the v2 baton schema covers those two device shapes; a laptop
    capture keeps its v1 baton. Idempotent (``baton_v1_to_v2.convert_engagement``
    preserves ``baton{,-mobile}.v1raw.json``) and best-effort: acquisition has
    already succeeded, so a conversion failure — e.g. a non-schema engagement id
    on a standalone quick-scan — only warns and leaves the v1 baton in place.
    """
    convertible = tuple(d for d in devices if d in ("desktop", "mobile"))
    if not convertible:
        return
    try:
        converter = _load_script_module(
            "baton_v1_to_v2", SCRIPTS_DIR / "baton_v1_to_v2.py")
        converter.convert_engagement(
            eng_dir, devices=convertible, engagement_id=engagement_id)
    except Exception as exc:  # noqa: BLE001 — never fail acquisition on conversion
        print(f"WARNING: v1->v2 baton conversion skipped ({exc}); v1 baton kept on disk.",
              file=sys.stderr)
        print(f"  Convert manually: python scripts/baton_v1_to_v2.py {eng_dir}",
              file=sys.stderr)


def main() -> int:
    args = build_arg_parser().parse_args()

    devices = _parse_devices(args)
    non_mobile = [d for d in devices if d in ("laptop", "desktop")]
    if len(non_mobile) > 1:
        print(
            "ERROR: at most one of laptop or desktop is allowed in a single run. "
            "Use laptop+mobile or desktop+mobile.",
            file=sys.stderr,
        )
        return 1

    engagement_id = args.engagement_id.strip() or f"ecp-cursor-{uuid.uuid4().hex[:10]}"
    eng_dir = REPO_ROOT / "docs" / "ecp" / engagement_id
    _abort = _prepare_engagement_dir(eng_dir, args.allow_existing)
    if _abort is not None:
        return _abort

    agent_browser = _ensure_agent_browser()
    ecp_dom = _load_script_module("ecp_acquire_dom", SCRIPTS_DIR / "ecp_acquire_dom.py")
    ecp_ov = _load_script_module("ecp_acquire_overlays", SCRIPTS_DIR / "ecp_acquire_overlays.py")
    sec_hints = _load_script_module("ecp_section_hints", SCRIPTS_DIR / "ecp_section_hints.py")
    ecp_cfg = _load_script_module("ecp_configurator", SCRIPTS_DIR / "ecp_configurator.py")

    multi = len(devices) > 1
    file_prefix = "{device}-" if multi else ""
    results: list[_DeviceRunInfo] = []
    combined_confidence = "High"
    for device in devices:
        prefix = file_prefix.format(device=device) if multi else ""
        code, info = _run_one_device(
            device=device,
            file_prefix=prefix,
            url=args.url,
            engagement_id=engagement_id,
            eng_dir=eng_dir,
            agent_browser=agent_browser,
            ecp_dom=ecp_dom,
            ecp_ov=ecp_ov,
            sec_hints=sec_hints,
            ecp_cfg=ecp_cfg,
            max_screenshots=int(args.max_screenshots),
            settle_seconds=float(args.settle_seconds),
            post_scroll_wait=float(args.post_scroll_wait),
            goto_timeout=float(args.goto_timeout),
            overlay_rounds=6,
            overlay_pause_s=1.0,
            recovery_pass=False,
        )
        if code != 0 or info is None:
            return code

        if args.hybrid:
            reasons = _hybrid_gate_reasons(info)
            if reasons:
                print(
                    f"HYBRID: quality gates failed for {device} ({', '.join(reasons)}); "
                    "running one recovery pass with stricter capture settings...",
                    file=sys.stderr,
                )
                r_code, r_info = _run_one_device(
                    device=device,
                    file_prefix=prefix,
                    url=args.url,
                    engagement_id=engagement_id,
                    eng_dir=eng_dir,
                    agent_browser=agent_browser,
                    ecp_dom=ecp_dom,
                    ecp_ov=ecp_ov,
                    sec_hints=sec_hints,
                    ecp_cfg=ecp_cfg,
                    max_screenshots=0,
                    settle_seconds=max(float(args.settle_seconds), 5.0),
                    post_scroll_wait=max(float(args.post_scroll_wait), 1.25),
                    goto_timeout=max(float(args.goto_timeout), 45.0),
                    overlay_rounds=10,
                    overlay_pause_s=1.2,
                    recovery_pass=True,
                )
                if r_code == 0 and r_info is not None:
                    info = r_info
                else:
                    print(
                        f"HYBRID: recovery pass failed for {device}; keeping first-pass artifacts.",
                        file=sys.stderr,
                    )

        results.append(info)
        combined_confidence = _worse_confidence(combined_confidence, info.confidence)

    primary = devices[0]
    page_href = results[-1].page_href
    page_title = results[-1].page_title

    meta: dict[str, Any] = {
        "engagement_id": engagement_id,
        "mode": "quick-scan",
        "status": "in_progress",
        "updated_at": _now_iso(),
        "confidence": combined_confidence,
        "device": primary,
        "url": page_href or args.url,
        "page": {"url": page_href or args.url, "title": page_title},
        "source_mode": "url",
    }
    if multi:
        meta["devices_requested"] = list(devices)
        meta["devices_scanned"] = [r.device for r in results]

    _write_text(eng_dir / "meta.json", json.dumps(_merge_meta(eng_dir, meta), indent=2) + "\n")
    if multi:
        lines = [
            f"# Engagement {engagement_id}",
            "",
            f"- URL: `{args.url}`",
            f"- Devices: `{', '.join(devices)}` (multi capture)",
            f"- Page title: `{page_title or ''}`",
            "",
        ]
        for r in results:
            lines.extend(
                [
                    f"## {r.device}",
                    f"- Baton: `{r.baton_name}`",
                    f"- DOM: `{r.dom_name}`",
                    f"- Viewport: {r.inner_w}x{r.inner_h} @ {r.dpr_i}x",
                    f"- Capture mode: {'hybrid-recovery' if r.recovery_pass else 'fast-first'}",
                    "",
                ]
            )
        lines.append(
            "This folder was created by `scripts/acquire_url.py` for the ECP URL acquire pipeline. "
            "Run the visual report per device using the matching baton file."
        )
        lines.append("")
        _write_text(eng_dir / "context.md", "\n".join(lines) + "\n")
    else:
        r0 = results[0]
        _write_text(
            eng_dir / "context.md",
            "\n".join(
                [
                    f"# Engagement {engagement_id}",
                    "",
                    f"- URL: `{args.url}`",
                    f"- Device: `{r0.device}`",
                    f"- Baton: `{r0.baton_name}`",
                    f"- DOM: `{r0.dom_name}`",
                    f"- Capture mode: {'hybrid-recovery' if r0.recovery_pass else 'fast-first'}",
                    f"- Page title: `{page_title or ''}`",
                    "",
                    "This folder was created by `scripts/acquire_url.py` for the ECP URL acquire pipeline.",
                    "Next: write `quick-scan.md` or `audit.md` findings, then run the visual report wrapper if needed.",
                    "",
                ]
            )
            + "\n",
        )

    # Upgrade the v1-shape batons just written to the v2 schema the rest of the
    # pipeline reads (previously an undocumented manual lead step — run-review C1).
    _upgrade_batons_to_v2(eng_dir, devices, engagement_id)

    print("OK")
    print(f"engagement_dir={eng_dir}")
    for r in results:
        print(
            f"---\n"
            f"DEVICE: {r.device}\n"
            f"VIEWPORT: {r.inner_w}x{r.inner_h} @ {r.dpr_i}x\n"
            f"SCREENSHOTS: {r.n_shots} captured\n"
            f"SECTIONS: {r.n_sections} recorded\n"
            f"DOM_SIZE: {r.dom_size} ({r.dom_mode})\n"
            f"DOM: docs/ecp/{engagement_id}/{r.dom_name}\n"
            f"BATON: docs/ecp/{engagement_id}/{r.baton_name}\n"
            f"STATUS: {r.status}\n"
            f"CONFIDENCE: {r.confidence}\n"
            f"ELEMENTS: {r.n_elements}\n"
            f"OCCLUDED_SECTIONS: {r.occluded_sections}\n"
            f"SCROLL_FAILED_SECTIONS: {r.scroll_failed_sections}\n"
            f"PRE_HYDRATION_WARNING: {str(r.pre_hydration_warning).lower()}\n"
            f"HYBRID_RECOVERY: {str(r.recovery_pass).lower()}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
