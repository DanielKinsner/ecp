"""acquire.md Step 1d — configurator / fitment dual-state capture (canonical acquire helper).

When at least two required ``<select>`` elements exist and the primary CTA is disabled,
selects either the URL-pinned variant (``?variant=NNN`` / ``?sku=...``) or the first
valid option per select, waits for dynamic updates, and captures one
``{prefix}configured.jpg`` for the baton ``configured_state`` field.

C13 (workflows/acquire.md §311-323) — variant pinning. Pre-fix this module
always picked the first non-disabled option in each select and recorded no
``variant_id`` / ``variant_source``. In a dual-device run desktop and mobile
could (and did, awdmods 2026-05-18) capture different SKUs whenever the
default DOM order of options differed across viewports — every cross-device
pricing or CTA finding from those runs implicitly compared different
variants. The contract requires:

    1. If the source URL carries variant/sku/variantId/selected_variant,
       click THAT variant on every device (record variant_source="url-pinned").
    2. Otherwise, select first-available and record the RESOLVED identity
       so cross-device drift is at least detectable downstream
       (variant_source="first-available", variant_id=<resolved>).

The cross-device assertion lives lead-side; this module only owns the
per-device pin + record steps.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse

_DETECT_JS = r"""(function(){
  var selects = Array.from(document.querySelectorAll("select"));
  var required = selects.filter(function(s){
    return s.required || s.getAttribute("aria-required") === "true";
  });
  var btns = Array.from(document.querySelectorAll(
    'button[type="submit"],[class*="add-to-cart"],[name="add"],[aria-label*="Add to"],[aria-label*="add to"]'
  ));
  var cta = null;
  for (var b=0;b<btns.length;b++) {
    var r = btns[b].getBoundingClientRect();
    if (r.width>0 && r.height>0) { cta = btns[b]; break; }
  }
  if (!cta && btns[0]) cta = btns[0];
  return {
    requiredCount: required.length,
    ctaDisabled: cta ? !!cta.disabled : false,
    match: required.length >= 2 && cta && cta.disabled
  };
})()"""

# Pre-fix _APPLY_JS — kept for the first-available code path. Returns the
# RESOLVED variant identity from the page so we can record it on the baton
# even when no URL variant was supplied (workflows/acquire.md §317:
# "variant_id: '<resolved variant id from the selected option>'").
_APPLY_FIRST_AVAILABLE_JS = r"""(function(){
  var selects = Array.from(document.querySelectorAll("select")).filter(function(s){
    return s.required || s.getAttribute("aria-required") === "true";
  });
  for (var i=0;i<selects.length;i++) {
    var s = selects[i];
    var j = 0;
    for (var k=0;k<s.options.length;k++) {
      if (s.options[k].value && !s.options[k].disabled) { j = k; break; }
    }
    if (s.options.length > j) s.selectedIndex = j;
    else if (s.options.length) s.selectedIndex = 0;
    s.dispatchEvent(new Event("input", {bubbles: true}));
    s.dispatchEvent(new Event("change", {bubbles: true}));
  }
  /* Resolved-identity probe: read Shopify's live selectedVariantId first,
     then DOM attributes/options, with product.variants[0] only as a labeled
     last resort. Best-effort; null on non-Shopify sites is acceptable. */
  var resolved = null;
  var resolvedSource = null;
  try {
    var meta = window.ShopifyAnalytics && window.ShopifyAnalytics.meta;
    if (meta && meta.selectedVariantId != null) {
      resolved = String(meta.selectedVariantId);
      resolvedSource = 'shopify-selectedVariantId';
    }
    if (!resolved) {
      var dv = document.querySelector('[data-variant-id]');
      if (dv) {
        resolved = String(dv.getAttribute('data-variant-id') || '').trim() || null;
        if (resolved) resolvedSource = 'data-variant-id';
      }
    }
    if (!resolved && selects.length) {
      var last = selects[selects.length - 1];
      if (last && last.options && last.selectedIndex >= 0 && last.options[last.selectedIndex]) {
        resolved = String(last.options[last.selectedIndex].value || '').trim() || null;
        if (resolved) resolvedSource = 'selected-option-value';
      }
    }
    if (!resolved && meta && meta.product && meta.product.variants && meta.product.variants.length) {
      var first = meta.product.variants[0];
      if (first && first.id != null) {
        resolved = String(first.id);
        resolvedSource = 'shopify-product-first-variant';
      }
    }
  } catch (e) {}
  return {
    ok: true,
    n: selects.length,
    resolved_variant_id: resolved,
    resolved_variant_source: resolvedSource
  };
})()"""


def _build_apply_url_pinned_js(variant_id: str) -> str:
    """Build the JS payload that selects the URL-pinned variant on this page.

    Looks for the variant by these signals (in order, mirroring acquire.md §315):
    1. ``[data-variant-id="<id>"]`` swatches / radio inputs (Shopify Dawn default).
    2. ``input[name="id"][value="<id>"]`` (Shopify legacy radio form).
    3. ``select option[value="<id>"]`` (variant select dropdown).
    4. A ``window.ShopifyAnalytics.meta.product.variants[]`` match — when found,
       click the matching swatch/option by index.

    If the variant truly can't be located on this page (404'd ID, draft, or
    not a Shopify shape), the JS falls back to the first-available behavior
    and reports ``url_pinned: false`` so the caller records that honestly
    instead of lying about a pin.
    """
    # Defensively escape the variant id as a JS string literal.
    vid_lit = json.dumps(str(variant_id))
    return r"""(function(){
  var target = """ + vid_lit + r""";
  var found = false;
  var heuristicVariantIndex = null;

  /* 1. data-variant-id swatch / radio. */
  var dv = document.querySelector('[data-variant-id="' + target + '"]');
  if (dv) {
    try { dv.click(); found = true; } catch (e) {}
  }

  /* 2. Shopify legacy input[name="id"] radio. */
  if (!found) {
    var ri = document.querySelector('input[name="id"][value="' + target + '"]');
    if (ri) {
      try {
        ri.checked = true;
        ri.dispatchEvent(new Event('change', {bubbles: true}));
        ri.dispatchEvent(new Event('input', {bubbles: true}));
        found = true;
      } catch (e) {}
    }
  }

  /* 3. <select><option value="<id>"> variant select. */
  if (!found) {
    var sels = Array.from(document.querySelectorAll('select'));
    for (var si=0; si<sels.length; si++) {
      var s = sels[si];
      for (var oi=0; oi<s.options.length; oi++) {
        if (String(s.options[oi].value || '') === target) {
          s.selectedIndex = oi;
          s.dispatchEvent(new Event('input', {bubbles: true}));
          s.dispatchEvent(new Event('change', {bubbles: true}));
          found = true;
          break;
        }
      }
      if (found) break;
    }
  }

  /* 4. ShopifyAnalytics index match — heuristic only. The variant id
     matched the product list, but an index-based swatch click is not a
     verifiable URL pin because the swatch NodeList may not share that order. */
  if (!found) {
    try {
      var meta = window.ShopifyAnalytics && window.ShopifyAnalytics.meta;
      if (meta && meta.product && meta.product.variants) {
        for (var vi=0; vi<meta.product.variants.length; vi++) {
          if (String(meta.product.variants[vi].id) === target) {
            var swatches = document.querySelectorAll('[class*="swatch"], [class*="variant"] [role="button"], [class*="variant"] button');
            if (swatches.length > vi) {
              try {
                swatches[vi].click();
                heuristicVariantIndex = vi;
                break;
              } catch (e) {}
            }
          }
        }
      }
    } catch (e) {}
  }

  /* If the URL variant couldn't be located, fall back to first-available
     so we still produce a configured screenshot — but report it. */
  if (!found && heuristicVariantIndex === null) {
    var rsels = Array.from(document.querySelectorAll('select')).filter(function(s){
      return s.required || s.getAttribute('aria-required') === 'true';
    });
    for (var i=0;i<rsels.length;i++) {
      var ss = rsels[i];
      var j = 0;
      for (var k=0;k<ss.options.length;k++) {
        if (ss.options[k].value && !ss.options[k].disabled) { j = k; break; }
      }
      if (ss.options.length > j) ss.selectedIndex = j;
      ss.dispatchEvent(new Event('input', {bubbles: true}));
      ss.dispatchEvent(new Event('change', {bubbles: true}));
    }
  }
  return {
    url_pinned: !!found,
    target_variant_id: target,
    heuristic_variant_index: heuristicVariantIndex
  };
})()"""

_CTA_PRICE_JS = r"""(function(){
  var btns = Array.from(document.querySelectorAll(
    'button[type="submit"],[class*="add-to-cart"],[name="add"],[aria-label*="Add"]'
  ));
  var cta = btns[0] || null;
  var price = "";
  var el = document.querySelector("[class*='price'],[itemprop='price'],[data-product-price]");
  if (el) price = (el.textContent || "").trim().replace(/\s+/g, " ").slice(0, 120);
  return {
    ctaText: cta ? (cta.textContent || "").trim().replace(/\s+/g, " ").slice(0, 120) : "",
    ctaEnabled: cta ? !cta.disabled : null,
    price: price
  };
})()"""


_VARIANT_QUERY_KEYS = ("variant", "variantId", "variant_id", "sku", "selected_variant")


def extract_target_variant_from_url(url: str) -> str | None:
    """Return the URL-pinned variant id from the target URL, or ``None``.

    Checks (in order, per workflows/acquire.md §315):
      1. Query string keys: ``variant``, ``variantId``, ``variant_id``, ``sku``,
         ``selected_variant``.
      2. Shopify-style path tail ``/products/.../<variant-id>`` is NOT a real
         Shopify convention — Shopify uses query string only — so we don't
         try to mine the path. A clean ``?variant=NNN`` is the canonical
         signal and is what the awdmods 2026-05-18 case relied on.
    """
    if not isinstance(url, str) or not url:
        return None
    try:
        parsed = urlparse(url)
    except (ValueError, TypeError):
        return None
    q = parse_qs(parsed.query or "", keep_blank_values=False)
    for key in _VARIANT_QUERY_KEYS:
        vals = q.get(key)
        if not vals:
            continue
        v = (vals[0] or "").strip()
        if not v:
            continue
        # Defensive sanitization: Shopify variant ids are digits; SKUs can be
        # alnum + dash/underscore. Reject anything that looks like JS injection.
        if re.fullmatch(r"[A-Za-z0-9._\-]+", v):
            return v
    return None


def try_configured_state_capture(
    *,
    ev: Callable[[str], Any],
    scroll_to_y: Callable[[int], int],
    eng_dir: Path,
    shot_jpeg: Callable[[Path, int], tuple[Path, str, str | None, str]],
    file_prefix: str,
    target_url: str | None = None,
) -> dict[str, Any] | None:
    """Return ``configured_state`` dict for the baton or ``None`` if not applicable.

    Assumes default-state DOM is already saved; this mutates the live page.

    ``target_url`` (C13) is the URL the audit was dispatched against. When it
    carries a ``variant``/``sku``/``variant_id``/``selected_variant``/``variantId``
    query parameter, the matching variant is selected on every device
    (``variant_source="url-pinned"``); otherwise the first-available behavior
    runs and the RESOLVED identity is recorded so cross-device drift can be
    detected downstream (``variant_source="first-available"``).
    """
    scroll_to_y(0)
    time.sleep(0.4)
    det = ev("JSON.stringify(" + _DETECT_JS + ")")
    dct = _parse_obj(det) if not isinstance(det, dict) else det
    if not dct or not dct.get("match"):
        return None

    target_variant = extract_target_variant_from_url(target_url or "")
    variant_id: str | None = None
    variant_source: str = "first-available"
    variant_resolution_source: str | None = None
    try:
        if target_variant:
            url_pinned_raw = ev("JSON.stringify(" + _build_apply_url_pinned_js(target_variant) + ")")
            up = _parse_obj(url_pinned_raw) if not isinstance(url_pinned_raw, dict) else url_pinned_raw
            if up and up.get("url_pinned"):
                variant_id = str(up.get("target_variant_id") or target_variant)
                variant_source = "url-pinned"
            else:
                # URL variant couldn't be located on this page — the JS already
                # fell back to first-available, so record it honestly.
                variant_source = "first-available"
                if up and up.get("heuristic_variant_index") is not None:
                    variant_id = str(up.get("target_variant_id") or target_variant)
                    variant_resolution_source = "heuristic-variant-index"
        else:
            apply_raw = ev("JSON.stringify(" + _APPLY_FIRST_AVAILABLE_JS + ")")
            ap = _parse_obj(apply_raw) if not isinstance(apply_raw, dict) else apply_raw
            if ap:
                resolved = ap.get("resolved_variant_id")
                if isinstance(resolved, str) and resolved.strip():
                    variant_id = resolved.strip()
                resolved_source = ap.get("resolved_variant_source")
                if isinstance(resolved_source, str) and resolved_source.strip():
                    variant_resolution_source = resolved_source.strip()
    except (OSError, RuntimeError, TypeError, ValueError):
        return None
    time.sleep(1.5)
    try:
        cta_raw = ev("JSON.stringify(" + _CTA_PRICE_JS + ")")
        cta_info: Any = _parse_obj(cta_raw) if not isinstance(cta_raw, dict) else cta_raw
    except (OSError, RuntimeError, TypeError, ValueError):
        cta_info = {}
    rel = f"{file_prefix}configured.jpg" if file_prefix else "configured.jpg"
    out = eng_dir / rel
    try:
        path, _h, _f, _e = shot_jpeg(out, 80)
    except (OSError, RuntimeError) as exc:
        print(f"STATUS: PARTIAL - configurator screenshot failed: {exc}", flush=True)
        return None
    if not path.exists() or path.stat().st_size < 100:
        return None
    result: dict[str, Any] = {
        "screenshot": rel,
        "cta_text": str((cta_info or {}).get("ctaText") or ""),
        "cta_enabled": (cta_info or {}).get("ctaEnabled") if cta_info else None,
        "price": str((cta_info or {}).get("price") or ""),
        "variant_source": variant_source,
    }
    if variant_id:
        result["variant_id"] = variant_id
    if variant_resolution_source:
        result["variant_resolution_source"] = variant_resolution_source
    return result


def _parse_obj(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            o = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        if isinstance(o, str):
            try:
                return json.loads(o)
            except json.JSONDecodeError:
                return {}
        if isinstance(o, dict):
            return o
    return {}
