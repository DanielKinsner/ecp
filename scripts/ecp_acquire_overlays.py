"""Browser-session helpers for `workflows/acquire.md` Step 1b (overlays) + 1c (timers).

These functions accept a callback ``eval_json(source: str) -> Any`` that should run
``agent-browser eval`` (or equivalent) and return parsed JSON.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Optional
from urllib.parse import urlparse

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

_DISMISS_ROUND = r"""
(function(){
  var sels = [
    '#onetrust-accept-btn-handler',
    'button#onetrust-accept-btn-handler',
    '#truste-consent-button',
    '[id*="onetrust"] button',
    'button[aria-label*="ccept" i]',
    'button[aria-label*="Agree" i]',
    'button[aria-label*="lose" i]',
    '.osano-cm-accept',
    '[class*="consent"] button',
    '[role="dialog"] button',
    '.modal button',
    '[class*="omnisend"] button',
    '[class*="klaviyo"] button',
    '[class*="mailchimp"] button'
  ];
  for (var i=0;i<sels.length;i++) {
    var el = document.querySelector(sels[i]);
    if (el) {
      var r = el.getBoundingClientRect();
      if (r.width<1 && r.height<1) continue;
      try { el.click(); return {clicked: true, sel: sels[i]}; } catch (e) {}
    }
  }
  var b = document.querySelector('a[role="button"], a.btn, button, [role="button"]');
  if (b) { var t = (b.innerText || '').trim().toLowerCase(); if (/accept|agree|got it|ok|dismiss|close|no thanks|decline/.test(t)) { try { b.click(); return {clicked: true, sel: 'text-match'}; } catch (e) {} } }
  return {clicked: false};
})()
"""

_FORCE_REMOVE = r"""
(function(){
  var sels = '[role="dialog"], .modal, [class*="consent"], [class*="newsletter"], [class*="omnisend"], [class*="overlay"], [class*="popup"]';
  var nodes = document.querySelectorAll(sels);
  var removed = 0;
  for (var i=0;i<nodes.length;i++) {
    var el = nodes[i];
    if (!el) continue;
    var r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    var vw = window.innerWidth, vh = window.innerHeight;
    var coverage = (Math.min(r.right, vw) - Math.max(r.left, 0)) * (Math.min(r.bottom, vh) - Math.max(r.top, 0));
    if (coverage > vw * vh * 0.1) {
      try { el.remove(); removed++; } catch (e) { try { el.style.display = 'none'; removed++; } catch (e2) {} }
    }
  }
  return {removed: removed};
})()
"""

_KEYDOWN_ESC = r"""
(function(){ try { document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', keyCode: 27, bubbles: true})); } catch (e) {} return true; })()
"""


def viewport_clear_eval_source() -> str:
    return _VIEWPORT_CHECK


def dismiss_overlays(eval_json: EvalJson, *, rounds: int = 6, pause_s: float = 1.0) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for _ in range(max(0, int(rounds))):
        r = eval_json("JSON.stringify(" + _DISMISS_ROUND + ")")
        if not isinstance(r, dict):
            break
        out.append(r)
        if r.get("clicked") is not True:
            # try escape once in case focus trap
            eval_json("JSON.stringify(" + _KEYDOWN_ESC + ")")
            time.sleep(0.25)
            r2 = eval_json("JSON.stringify(" + _DISMISS_ROUND + ")")
            if isinstance(r2, dict) and r2.get("clicked") is True:
                out.append(r2)
            else:
                break
        time.sleep(max(0.0, float(pause_s)))
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
    if a.scheme not in ("http", "https") or b.scheme not in ("http", "https"):
        return "Non-HTTP(S) final URL"
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
