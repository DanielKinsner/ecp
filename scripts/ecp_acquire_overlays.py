"""Browser-session helpers for `workflows/acquire.md` Step 1b (overlays) + 1c (timers).

These functions accept a callback ``eval_json(source: str) -> Any`` that should run
``agent-browser eval`` (or equivalent) and return parsed JSON.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Optional
from urllib.parse import urlparse

try:
    from url_validation import validate_url
except ImportError:  # pragma: no cover - ensure the sibling scripts/ dir is importable
    import sys as _sys
    from pathlib import Path as _Path
    _sys.path.insert(0, str(_Path(__file__).resolve().parent))
    from url_validation import validate_url

EvalJson = Callable[[str], Any]

_VIEWPORT_CHECK = r"""
JSON.stringify((function() {
  var sel = (
    '[role="dialog"], .modal, [class*="popup"], [class*="overlay"], ' +
    '[class*="newsletter"], [class*="subscribe"], [class*="omnisend"], [class*="klaviyo"], ' +
    '[class*="consent"], [id*="onetrust"], .cc-window, [id*="omnisend"]'
  );
  var overlays = document.querySelectorAll(sel);
  var blocking = [];
  for (var i=0;i<overlays.length;i++) {
    var el = overlays[i];
    if (!el) continue;
    var st = window.getComputedStyle ? window.getComputedStyle(el) : {display: 'block'};
    if (st && st.display === 'none') continue;
    var r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    var vw = window.innerWidth, vh = window.innerHeight;
    var coverage = (Math.min(r.right, vw) - Math.max(r.left, 0)) * (Math.min(r.bottom, vh) - Math.max(r.top, 0));
    if (coverage > vw * vh * 0.1) {
      var cn = (el.className && el.className.toString) ? el.className.toString() : "";
      blocking.push({tag: (el.tagName||'').toLowerCase(), class: cn.slice(0,80), id: (el.id||'').slice(0, 60), coverage: Math.round(coverage/(vw*vh)*100)});
    }
  }
  return {clear: blocking.length === 0, blocking: blocking, vw: window.innerWidth, vh: window.innerHeight};
})())
"""

"""C12 (workflows/acquire.md §222-228) — overlay dismissal must be semantic.

Pre-fix the round had two phases: (1) try a list of "container" selectors like
``[role="dialog"] button``, ``.modal button``, ``[class*="omnisend"] button``
and click the FIRST match unconditionally; (2) only AFTER all containers
missed, fall back to a text-constrained ``button`` scan. In an Omnisend
newsletter popup the FIRST button is "Subscribe", so the pre-fix happily
subscribed the operator's session to the brand's mailing list before any
"no thanks" text match ran.

Fix: semantic close-targeting (aria-label close/dismiss, ×/✕/close-class) runs
on EVERY round, paired with a hard subscribe/sign-up/submit/accept BLOCKLIST
that vetoes a click on any button whose accessible text matches those
patterns — regardless of which selector matched it. The accept-list (for
cookie/consent banners specifically) is preserved but is now whitelisted by
text too, so a "subscribe" button in a ``[class*="consent"] button`` selector
can never sneak through as "accept."

The contract reference is ``workflows/acquire.md`` ~222-228 (the
``aria-label*="close"`` / ``aria-label*="dismiss"`` / ``.close`` /
``button:has-text("×")`` / ``button:has-text("No thanks")`` enumeration).
"""

_DISMISS_ROUND = r"""
(function(){
  /* C12: subscribe/sign-up patterns. ANY candidate whose accessible text
     matches one of these is BLOCKED from clicking — newsletter popups
     consistently put "Subscribe" / "Sign up" / "Get 10% off" as the
     first button in the dialog. The blocklist runs on every round. */
  var BLOCK_TXT = /(subscribe|sign\s*up|signup|join|register|submit|continue|get\s+\d+|10%\s*off|claim|yes please|tell me|count me in|notify me|remind me|gift|buy|add to (cart|bag)|reveal)/i;
  var BLOCK_ARIA = /(subscribe|sign|register|submit|join)/i;

  /* Semantic close-set: matches the workflows/acquire.md ~222-228 contract
     (aria-label close/dismiss, .close/.dismiss classes, × / ✕ / X glyphs,
     "no thanks" / "decline" / "close" text). */
  var CLOSE_ARIA = /(close|dismiss|cancel|skip|reject|decline)/i;
  var CLOSE_TXT = /^(?:close|dismiss|cancel|skip|no thanks|no thank you|maybe later|not now|reject|decline|continue without|x|×|✕|✖|⨯)$/i;
  /* Accept-list (cookie/consent banners). NEVER applied to popups where the
     accept text would mean "subscribe me" — paired with BLOCK_TXT below. */
  var ACCEPT_TXT = /^(?:accept(?: all| cookies)?|agree(?: and continue)?|got it|ok|okay|allow(?: all)?|i accept|consent|confirm)$/i;

  function txt(el){ return ((el.innerText || el.textContent || '').trim().slice(0, 80)); }
  function aria(el){ return ((el.getAttribute && el.getAttribute('aria-label')) || '').trim().slice(0, 80); }
  function visible(el){
    if (!el) return false;
    var r = el.getBoundingClientRect();
    if (r.width < 2 && r.height < 2) return false;
    var cs = (window.getComputedStyle ? window.getComputedStyle(el) : null);
    if (cs && (cs.display === 'none' || cs.visibility === 'hidden')) return false;
    return true;
  }
  /* The single per-button safety check — applies to EVERY click attempt in
     EVERY phase. Returns true if the button is safe to dismiss with.
     Close semantics WIN over the block-list: "Continue without accepting"
     is a decline even though bare "continue" is a BLOCK_TXT token. */
  function isCloseSemantic(el){
    var t = txt(el), a = aria(el);
    return CLOSE_TXT.test(t) || CLOSE_ARIA.test(a) || /^continue without\b/i.test(t);
  }
  function safeToClick(el){
    if (!visible(el)) return false;
    if (isCloseSemantic(el)) return true;
    var t = txt(el), a = aria(el);
    if (BLOCK_TXT.test(t) || BLOCK_TXT.test(a)) return false;
    if (BLOCK_ARIA.test(a) && !CLOSE_ARIA.test(a)) return false;
    return true;
  }

  /* Phase 1 — known cookie/consent OK-button selectors (semantically safe
     because the IDs/classes are operator-specific and well-known). The
     subscribe blocklist still vetoes if the matched element is mis-named. */
  var sels = [
    '#onetrust-accept-btn-handler',
    'button#onetrust-accept-btn-handler',
    '#truste-consent-button',
    '[id*="onetrust"] button',
    'button[aria-label*="ccept" i]',
    'button[aria-label*="Agree" i]',
    '.osano-cm-accept'
  ];
  for (var i=0;i<sels.length;i++) {
    var el = document.querySelector(sels[i]);
    if (el && safeToClick(el)) {
      try { el.click(); return {clicked: true, sel: sels[i], phase: 'accept'}; } catch (e) {}
    }
  }

  /* Phase 2 — close-semantic targeting on EVERY round (this is the C12 fix).
     The pre-fix ran this only as a final text-fallback AFTER container
     selectors had already happily clicked the first button in a dialog.
     Now: walk dialogs/popups and look for an aria-label/class/text that
     matches the close-set. */
  var CLOSE_SEL = [
    '[aria-label*="close" i]',
    '[aria-label*="dismiss" i]',
    '[aria-label*="cancel" i]',
    '[aria-label*="skip" i]',
    'button.close',
    'button.dismiss',
    '[class*="close-button"]',
    '[class*="dismiss-button"]',
    '[class*="popup-close"]',
    '[class*="modal-close"]',
    '[class*="newsletter"] [class*="close"]',
    '[class*="omnisend"] [class*="close"]',
    '[class*="klaviyo"] [class*="close"]',
    '[role="dialog"] [aria-label*="close" i]',
    '[role="dialog"] [aria-label*="dismiss" i]',
    '.modal [aria-label*="close" i]'
  ];
  for (var ci=0; ci<CLOSE_SEL.length; ci++) {
    var ce = document.querySelectorAll(CLOSE_SEL[ci]);
    for (var cj=0; cj<ce.length; cj++) {
      if (safeToClick(ce[cj])) {
        try { ce[cj].click(); return {clicked: true, sel: CLOSE_SEL[ci], phase: 'close-semantic'}; } catch (e) {}
      }
    }
  }

  /* Phase 3 — scan buttons inside the known overlay containers, but ONLY
     click ones whose text / aria-label matches a close-set or a true
     consent-accept (cookie banner) AND survives the blocklist. The
     pre-fix clicked the first button unconditionally here — the root
     cause of the Subscribe regression. */
  var CONTAINERS = [
    '[role="dialog"]',
    '[aria-modal="true"]',
    '.modal',
    '[class*="popup"]',
    '[class*="overlay"]',
    '[class*="consent"]',
    '[class*="omnisend"]',
    '[class*="klaviyo"]',
    '[class*="mailchimp"]',
    '[class*="newsletter"]',
    '[class*="subscribe"]'
  ];
  for (var k=0; k<CONTAINERS.length; k++) {
    var nodes = document.querySelectorAll(CONTAINERS[k]);
    for (var n=0; n<nodes.length; n++) {
      var btns = nodes[n].querySelectorAll('button, [role="button"], a.btn, a[role="button"]');
      for (var bi=0; bi<btns.length; bi++) {
        var bel = btns[bi];
        if (!safeToClick(bel)) continue;
        var bt = txt(bel), ba = aria(bel);
        var isClose = CLOSE_TXT.test(bt) || CLOSE_ARIA.test(ba);
        var isAccept = ACCEPT_TXT.test(bt);
        if (!isClose && !isAccept) continue;
        try {
          bel.click();
          return {clicked: true, sel: CONTAINERS[k]+' button', phase: isClose ? 'close-text' : 'accept-text', text: bt};
        } catch (e) {}
      }
    }
  }

  /* Phase 4 — final text-match fallback over the whole document (preserved
     from pre-fix behavior; gated by safeToClick + close/accept patterns). */
  var any = document.querySelectorAll('a[role="button"], a.btn, button, [role="button"]');
  for (var ai=0; ai<any.length; ai++) {
    var ael = any[ai];
    if (!safeToClick(ael)) continue;
    var at = txt(ael);
    if (CLOSE_TXT.test(at) || ACCEPT_TXT.test(at)) {
      try { ael.click(); return {clicked: true, sel: 'text-match', phase: 'global-text', text: at}; } catch (e) {}
    }
  }
  return {clicked: false};
})()
"""

"""C11 (workflows/acquire.md §253-268) — per-overlay removal records.

Pre-fix this function returned only a count, then the converter wrote
``overlays_detected: []`` unconditionally, so the contract's
"DOM was edited during capture" caveat banner could never fire even when
three auto-open overlays had been force-dismissed via JS style override
(the awdmods 2026-05-18 mobile run is the documented case).

Fix: capture per-overlay identity (tag / id / class / aria-label /
coverage percent / dismissal method = ``js-remove`` or
``js-style-display-none``) on EVERY removal, return them as a list, and
let the Python wrapper and v1→v2 converter thread them onto the baton's
``capture_state.overlays_detected[]`` so downstream renderers can surface
the caveat.
"""

_FORCE_REMOVE = r"""
(function(){
  var sels = '[role="dialog"], .modal, [class*="consent"], [class*="newsletter"], [class*="omnisend"], [class*="overlay"], [class*="popup"]';
  var nodes = document.querySelectorAll(sels);
  var removed = 0;
  var records = [];
  function typeFromClasses(cls, id) {
    var s = ((cls||'') + ' ' + (id||'')).toLowerCase();
    if (/consent|onetrust|osano|cookie|privacy/.test(s)) return 'cookie-consent';
    if (/newsletter|subscribe|omnisend|klaviyo|mailchimp/.test(s)) return 'newsletter-modal';
    if (/age[-_ ]?gate/.test(s)) return 'age-gate';
    if (/promo|popup/.test(s)) return 'promo-popup';
    if (/geo|region|country/.test(s)) return 'geo-router';
    return 'other';
  }
  for (var i=0;i<nodes.length;i++) {
    var el = nodes[i];
    if (!el) continue;
    var r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    var vw = window.innerWidth, vh = window.innerHeight;
    var coverage = (Math.min(r.right, vw) - Math.max(r.left, 0)) * (Math.min(r.bottom, vh) - Math.max(r.top, 0));
    if (coverage > vw * vh * 0.1) {
      var clsRaw = (el.className && el.className.toString) ? el.className.toString() : '';
      var idRaw = (el.id || '');
      var rec = {
        tag: (el.tagName||'').toLowerCase(),
        id: String(idRaw).slice(0, 64),
        class: clsRaw.slice(0, 120),
        aria_label: ((el.getAttribute && el.getAttribute('aria-label')) || '').slice(0, 120),
        coverage_pct: Math.round(coverage/(vw*vh)*100),
        type: typeFromClasses(clsRaw, idRaw),
        method: 'js-remove'
      };
      try {
        el.remove();
        removed++;
      } catch (e) {
        try {
          el.style.display = 'none';
          rec.method = 'js-style-display-none';
          removed++;
        } catch (e2) {
          rec.method = 'failed';
        }
      }
      records.push(rec);
    }
  }
  return {removed: removed, records: records};
})()
"""

_KEYDOWN_ESC = r"""
(function(){ try { document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', keyCode: 27, bubbles: true})); } catch (e) {} return true; })()
"""


def viewport_clear_eval_source() -> str:
    return _VIEWPORT_CHECK


def _blocking_signature(state: dict[str, Any]) -> tuple[tuple[str, str, str, str], ...]:
    blocking = state.get("blocking")
    if not isinstance(blocking, list):
        return ()
    sig: list[tuple[str, str, str, str]] = []
    for item in blocking:
        if not isinstance(item, dict):
            continue
        sig.append(
            (
                str(item.get("tag") or ""),
                str(item.get("id") or ""),
                str(item.get("class") or ""),
                str(item.get("coverage") or ""),
            )
        )
    return tuple(sig)


def dismiss_overlays(eval_json: EvalJson, *, rounds: int = 6, pause_s: float = 1.0) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for _ in range(max(0, int(rounds))):
        before = read_viewport_state(eval_json)
        if before.get("clear") is True:
            break
        before_sig = _blocking_signature(before)

        r = eval_json("JSON.stringify(" + _DISMISS_ROUND + ")")
        if not isinstance(r, dict):
            break
        out.append(r)
        clicked = r.get("clicked") is True
        if r.get("clicked") is not True:
            # try escape once in case focus trap
            eval_json("JSON.stringify(" + _KEYDOWN_ESC + ")")
            time.sleep(0.25)
            r2 = eval_json("JSON.stringify(" + _DISMISS_ROUND + ")")
            if isinstance(r2, dict) and r2.get("clicked") is True:
                out.append(r2)
                clicked = True
            else:
                break
        time.sleep(max(0.0, float(pause_s)))
        if clicked:
            after = read_viewport_state(eval_json)
            if after.get("clear") is True:
                break
            if before_sig and _blocking_signature(after) == before_sig:
                break
    return out


def read_viewport_state(eval_json: EvalJson) -> dict[str, Any]:
    v = eval_json(_VIEWPORT_CHECK.strip())
    return v if isinstance(v, dict) else {}


def force_remove_blocking_overlays(eval_json: EvalJson) -> dict[str, Any]:
    r = eval_json("JSON.stringify(" + _FORCE_REMOVE + ")")
    return r if isinstance(r, dict) else {}


def verify_timers(eval_json: EvalJson, *, sleep_s: float = 10.0) -> Optional[dict[str, Any]]:
    _snap = r"""(function(){
  var nodes = document.querySelectorAll("[class*='timer'], [class*='countdown'], [class*='expire']");
  if (!nodes.length) return {found: 0, texts: []};
  var texts = [];
  for (var i=0;i<nodes.length;i++) texts.push((nodes[i].textContent||'').trim().slice(0, 160));
  return {found: nodes.length, texts: texts};
})()"""
    t0 = eval_json("JSON.stringify(" + _snap + ")")
    if not isinstance(t0, dict) or int(t0.get("found") or 0) <= 0:
        return None
    time.sleep(max(0.0, float(sleep_s)))
    t1 = eval_json("JSON.stringify(" + _snap + ")")
    if not isinstance(t1, dict):
        return {"timer_probe": t0, "error": "second_snap_failed"}
    t0a = t0.get("texts")
    t1a = t1.get("texts")
    t0a = t0a if isinstance(t0a, list) else []
    t1a = t1a if isinstance(t1a, list) else []
    return {
        "timer_live": t0a != t1a,
        "timer_static": t0a == t1a and len(t0a) > 0,
    }


def guardrails_fail_reason(*, request_url: str, final_href: str) -> str | None:
    """Return a human message if URL acquisition should block, else None."""
    try:
        a = urlparse(request_url)
        b = urlparse(final_href)
    except (ValueError, TypeError):
        return "URL parse error"
    # Deterministic per-URL validation (scheme + private/reserved IP ranges +
    # encoding bypass) on BOTH the request and the post-redirect final URL, so a
    # same-host redirect to a private/metadata IP is caught too — not just a
    # cross-host redirect. See contracts/url-validation.md / scripts/url_validation.py.
    for label, candidate in (("request", request_url), ("final", final_href)):
        reason = validate_url(candidate)
        if reason:
            return f"{reason} ({label} URL)"
    an = (a.netloc or "").lower()
    bn = (b.netloc or "").lower()
    an2 = an[4:] if an.startswith("www.") else an
    bn2 = bn[4:] if bn.startswith("www.") else bn
    if an2 and bn2 and an2 != bn2:
        return f"Redirected to a different host ({b.netloc!r} vs {a.netloc!r})"
    path = (b.path or "").lower()
    if "password" in path or "/login" in path or "/signin" in path or "/auth" in path:
        return "Auth/login path detected in final URL"
    return None
