"""Tiered HTML preprocessing for Cursor `acquire.md`-style URL capture (Python).

Mirrors the mandatory steps in `workflows/acquire.md` "Step 4: Extract and Preprocess DOM"
as closely as practical without adding third-party HTML tree libraries.

Returns processed HTML, ``dom_mode`` (``full`` | ``reduced`` | ``skeleton``), merged
JSON-LD structured data, and final byte size.
"""

from __future__ import annotations

import json
import re
from html import escape
from typing import Any

# Size tiers (UTF-8 bytes), per acquire.md
TIER_FULL_MAX = 300 * 1024
TIER_REDUCED_MAX = 500 * 1024


def _b(html: str) -> int:
    return len(html.encode("utf-8"))


def _extract_json_ld_blocks(html: str) -> tuple[str, list[Any]]:
    """Remove ``application/ld+json`` script blocks; parse JSON into a list (best-effort)."""
    out_ld: list[Any] = []
    out_parts: list[str] = []
    pos = 0
    for m in re.finditer(
        r'(?is)(<script\b[^>]*\btype\s*=\s*["\']application/ld\+json["\'][^>]*>)(?P<body>.*?)(</script>)',
        html,
    ):
        out_parts.append(html[pos : m.start()])
        pos = m.end()
        body = m.group("body")
        try:
            parsed: Any = json_loads_flexible(body.strip())
        except (json.JSONDecodeError, TypeError, ValueError):
            parsed = None
        if parsed is not None:
            out_ld.append(parsed)
    out_parts.append(html[pos:])
    return "".join(out_parts), out_ld


def json_loads_flexible(raw: str) -> Any:
    return json.loads(raw)


def _strip_all_scripts(html: str) -> str:
    return re.sub(r"(?is)<script\b[^>]*>.*?</script>", "", html)


def _strip_all_styles(html: str) -> str:
    return re.sub(r"(?is)<style\b[^>]*>.*?</style>", "", html)


def _strip_data_attributes(html: str) -> str:
    return re.sub(
        r'\sdata-[a-zA-Z0-9_-]+\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s>]+)',
        "",
        html,
    )


def _first_aria_label(svg_open_and_inner: str) -> str:
    m = re.search(r'(?is)\baria-label\s*=\s*"([^"]*)"', svg_open_and_inner[:2000])
    if m:
        return m.group(1)[:200]
    m = re.search(r'(?is)aria-label\s*=\s*\'([^\']*)\'', svg_open_and_inner[:2000])
    if m:
        return m.group(1)[:200]
    m = re.search(r'(?is)<title[^>]*>([^<]{1,120})', svg_open_and_inner)
    if m:
        return m.group(1).strip()[:200]
    return "svg"


def _replace_one_svg(html: str) -> tuple[str, bool]:
    m = re.search(r"(?is)<svg(\s[^>]*)?>", html)
    if not m:
        return html, False
    start = m.start()
    pos = m.end()
    lower = html.lower()
    depth = 1
    n = len(html)
    while pos < n and depth:
        a = lower.find("<svg", pos)
        b = lower.find("</svg>", pos)
        if b == -1:
            return html, False
        if a != -1 and a < b:
            depth += 1
            pos = a + 4
        else:
            depth -= 1
            if depth == 0:
                end = b + len("</svg>")
                chunk = html[m.start() : end]
                label = escape(_first_aria_label(chunk), quote=True)
                repl = f'<svg aria-label="{label}"/>'
                return html[:start] + repl + html[end:], True
            pos = b + len("</svg>")
    return html, False


def _strip_svg_innards(html: str) -> str:
    for _ in range(5000):
        html, changed = _replace_one_svg(html)
        if not changed:
            break
    return html


def _strip_html_comments_except_omission(html: str) -> str:
    def _sub(m: re.Match[str]) -> str:
        body = m.group(0)
        if "more items omitted" in body:
            return body
        return ""

    return re.sub(r"(?s)<!--.*?-->", _sub, html)


def _strip_sensitive_input_values(html: str) -> str:
    def _clean_tag(tag: str) -> str:
        t = tag
        t = re.sub(
            r'(?i)\bvalue\s*=\s*"(?:[^"]*)"(?=[^>]*\btype\s*=\s*"(?:password|hidden)"\b)',
            "",
            t,
        )
        t = re.sub(
            r'(?i)(<input\b[^>]*\btype\s*=\s*"(?:password|hidden)"[^>]*)\svalue\s*=\s*"[^"]*"',
            r"\1",
            t,
        )
        t = re.sub(
            r'(?i)(<input\b[^>]*\bautocomplete\s*=\s*"(?:[^"]*cc-[^"]*|new-password)"[^>]*)\svalue\s*=\s*"[^"]*"',
            r"\1",
            t,
        )
        return t

    return re.sub(r"(?is)<input\b[^>]+>", lambda m: _clean_tag(m.group(0)), html)


def _collapse_template_siblings(
    html: str,
    *,
    keep: int,
) -> str:
    """
    Heuristic: repeated identical *lines* of markup (10+) become one omission block.
    Mirrors the intent of acquire.md step 4 (template duplicate reduction) without a full DOM tree.
    """
    if keep < 1:
        keep = 1

    # Cheap global: repeated identical lines (common in SSR grids)
    lines = html.splitlines()
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        j = i + 1
        run = 1
        while j < n and lines[j] == line and len(line) > 40:
            run += 1
            j += 1
        if run >= 10 and line.strip().startswith("<"):
            keep_n = min(keep, run)
            for _k in range(keep_n):
                out.append(line)
            omitted = run - keep_n
            if omitted > 0:
                out.append(f"<!-- [{omitted}] more items omitted -->")
            i = j
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def _strip_inline_styles_except_important(html: str) -> str:
    keep_re = re.compile(
        r"(?is)<(button|a\b|h[1-6]\b|p\b|div\b|span\b|section\b|header\b|footer\b|label\b)[^>]*(class=\"[^\"]*("
        r"btn|price|trust|badge|cta|cart|checkout|omnisend|consent|rating|star|review"
        r")[^\"]*\"|role=\"(button|link)\"|type=\"(submit|button)\"|aria-[^=]*=)",
    )

    def _maybe_strip(m: re.Match[str]) -> str:
        tag = m.group(0)
        if keep_re.search(tag):
            return tag
        return re.sub(r'(?i)\sstyle\s*=\s*("[^"]*"|\'[^\']*\'|[^\s>]+)', "", tag)

    return re.sub(r"(?is)<[a-z][a-z0-9-]*\b[^>]+>", _maybe_strip, html)


def _skeleton_mode(html: str) -> str:
    """Extremely defensive extraction: headings, buttons, links, forms, key roles, $ text."""
    chunks: list[str] = []
    for pat in [
        r"(?is)<h[1-6][^>]*>.*?</h[1-6]>",
        r"(?is)<input\b[^>]+/>",
        r"(?is)<input\b[^>]+>",
        r"(?is)<button\b[^>]*>.*?</button>",
        r"(?is)<textarea\b[^>]*>.*?</textarea>",
        r"(?is)<select\b[^>]*>.*?</select>",
        r"(?is)<a[^>]+>[^<]{1,200}</a>",
        r"(?is)<img\b[^>]+/>",
        r'(?is)<(main|header|footer|nav|form)\b[^>]*>.*?</\1>',
        r'(?is)<[^>]*\brole="[^"]+"[^>]*>.*?</[a-z0-9-]+>',
    ]:
        for m in re.finditer(pat, html, re.DOTALL):
            s = m.group(0)
            if len(s) < 12_000:
                chunks.append(s)
    for m in re.finditer(r"(?i)[\$\u20ac\u00a3]\s?\d", html):
        a = max(0, m.start() - 80)
        b = min(len(html), m.end() + 80)
        safe = escape(html[a:b], quote=True)
        chunks.append(f'<p class="ecp-skeleton-currency">{safe}</p>')
    body = "\n".join(chunks[:2000])
    return (
        "<!DOCTYPE html><!-- SKELETON MODE: DOM exceeded 500KB, extracted structural elements only -->\n"
        "<html><head><meta charset='utf-8'/></head><body>"
        f"{body}</body></html>"
    )


def preprocess_acquisition_dom(
    raw_outer_html: str,
    *,
    existing_structured: Any = None,
) -> tuple[str, str, Any, int]:
    """
    Returns: ``(html_out, dom_mode, structured_data, size_bytes)``.

    ``structured_data`` is either a list of JSON-LD objects, a single dict, or ``None``.
    """
    structured: list[Any] = []
    if existing_structured is not None:
        if isinstance(existing_structured, list):
            structured.extend(existing_structured)
        else:
            structured.append(existing_structured)

    html, ld = _extract_json_ld_blocks(raw_outer_html)
    structured.extend(ld)

    html = _strip_all_scripts(html)
    html = _strip_all_styles(html)
    html = _strip_data_attributes(html)
    html = _strip_svg_innards(html)
    html = _strip_html_comments_except_omission(html)
    html = _strip_sensitive_input_values(html)
    # Template duplicate reduction (heuristic) — only meaningfully helps before tiering
    html = _collapse_template_siblings(html, keep=5)
    if _b(html) > TIER_FULL_MAX:
        html = _collapse_template_siblings(html, keep=2)

    dom_mode = "full"
    if _b(html) > TIER_REDUCED_MAX:
        html = _skeleton_mode(html)
        dom_mode = "skeleton"
    elif _b(html) > TIER_FULL_MAX:
        html = _strip_inline_styles_except_important(html)
        dom_mode = "reduced"
        html = _collapse_template_siblings(html, keep=2)
    size = _b(html)

    if len(structured) == 0:
        merged: Any = None
    elif len(structured) == 1:
        merged = structured[0]
    else:
        merged = structured

    return html, dom_mode, merged, size
