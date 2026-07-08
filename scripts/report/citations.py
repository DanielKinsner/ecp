"""Citation URL resolution and reference humanization."""

import ipaddress
import re
import string
from urllib.parse import urlparse


def _numeric_host_to_ip(host):
    """Normalize a non-standard but browser-resolvable numeric IPv4 host to an
    ``IPv4Address``, else return None for a genuine hostname.

    ``ipaddress.ip_address`` only accepts canonical dotted-quad / IPv6 forms,
    but browsers and libc ``inet_aton`` also resolve decimal (``2130706433``),
    hex (``0x7f000001``), octal (``0177.0.0.1``) and short-dotted (``127.1``)
    notations — all of which map to 127.0.0.1 / metadata IPs and are a classic
    SSRF bypass of a range check that only looks at the canonical form. We
    normalise those here (deterministically, without the platform-dependent
    ``socket.inet_aton``) so the caller can range-check the real address.
    IPv6 is untouched — ``ipaddress.ip_address`` already handles it upstream.
    """
    parts = host.split(".")
    if not 1 <= len(parts) <= 4:
        return None
    values = []
    for p in parts:
        if not p or len(p) > 11:
            return None
        try:
            if p[:2] in ("0x", "0X"):
                v = int(p, 16)
            elif p[0] == "0" and len(p) > 1:
                v = int(p, 8)
            elif p.isdigit():
                v = int(p, 10)
            else:
                return None  # contains a letter -> real hostname label
        except ValueError:
            return None
        if v < 0:
            return None
        values.append(v)
    # inet_aton "last part fills the remaining low-order bytes" rule.
    n = len(values)
    if n == 1:
        num = values[0]
    elif n == 2:
        if values[0] > 0xFF or values[1] > 0xFFFFFF:
            return None
        num = (values[0] << 24) | values[1]
    elif n == 3:
        if values[0] > 0xFF or values[1] > 0xFF or values[2] > 0xFFFF:
            return None
        num = (values[0] << 24) | (values[1] << 16) | values[2]
    else:
        if any(v > 0xFF for v in values):
            return None
        num = (values[0] << 24) | (values[1] << 16) | (values[2] << 8) | values[3]
    if not 0 <= num <= 0xFFFFFFFF:
        return None
    return ipaddress.ip_address(num)


def is_safe_citation_url(url):
    """Return True if `url` is safe to render as a clickable ``<a href>``.

    Rejects everything except http/https URLs whose host is a public
    domain name or a public IPv4/IPv6 address:

    - Non-http(s) schemes: ``javascript:``, ``data:``, ``file:``, ``ftp:``,
      blank, whitespace-only. Protects against XSS via ``javascript:``
      href and local-file exfil via ``file://`` href.
    - Private / loopback / link-local / reserved / multicast IPs, including
      cloud-metadata endpoints (AWS/GCP IMDS ``169.254.169.254``). Protects
      against SSRF if a citation URL is ever fetched server-side (the
      WS#1 HEAD-check is one such path).
    - ``localhost`` hostname.
    - URLs longer than 2048 bytes, or containing control chars outside
      ``string.printable`` (minus ``\\r``/``\\n``/``\\t``) which let an
      attacker splice HTML attributes or headers.

    Returns True only for URLs that pass every check. Failing URLs should
    render as ``(source unavailable)`` — existing fallback at
    ``scripts/report/templates/components.py``.
    """
    if not url or not isinstance(url, str):
        return False
    if len(url) > 2048:
        return False
    # Reject control characters — keep it to visible printable ASCII.
    # string.printable includes whitespace; a tab or newline inside a URL
    # is almost always malicious.
    if any(c not in string.printable for c in url):
        return False
    if any(c in "\r\n\t" for c in url):
        return False
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    host = parsed.hostname
    if not host:
        return False
    host = host.lower()
    if host == "localhost":
        return False
    # If the host parses as an IP literal, check its range.
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        # Not a *canonical* IP literal. Browsers still resolve decimal / hex /
        # octal / short-dotted IPv4 forms (e.g. 2130706433, 0x7f000001,
        # 0177.0.0.1, 127.1) to real addresses — normalise and range-check
        # those too, or a crafted citation URL slips a loopback/metadata host
        # past this guard (SSRF-bypass hardening, adversarial review 2026-07-08).
        ip = _numeric_host_to_ip(host)
        if ip is None:
            # Genuine hostname — accept.
            return True
    if ip.is_private or ip.is_loopback or ip.is_link_local:
        return False
    if ip.is_reserved or ip.is_multicast or ip.is_unspecified:
        return False
    return True


def resolve_citation_url(reference_str, sources_lookup):
    """Resolve a finding's REFERENCE or citation field to a URL.

    Auditors write references in many formats:
      "cta-design-and-placement.md — Finding 3"           (em-dash + Finding)
      "cta-design-and-placement.md, Finding 3"            (comma + Finding)
      "cta-design-and-placement.md Finding 3"             (whitespace + Finding)
      "cta-design-and-placement.md: Finding 3"            (colon + Finding)
      "cta-design-and-placement.md — Findings 6, 9, 18"   (multi-finding)
      "cta-design-and-placement.md § Primary CTA"         (section ref, no Finding number)
      "cta-design-and-placement.md"                       (bare file ref)
      "...md — Finding 3; ...md — Finding 2"              (multi-file, semicolon-separated)

    Resolution strategy:
      1. Try to extract filename + specific Finding number -> most specific URL
      2. If no Finding number found, fall back to ANY URL for that file
         (file-level link, accepting that we can't pinpoint the finding)
      3. Return None only if neither strategy yields a URL

    Returns the first matching URL, or None.
    """
    if not reference_str or not sources_lookup:
        return None

    # Split on semicolons for multi-file references
    parts = re.split(r";\s*", reference_str)

    # Strategy 1: filename + specific Finding number (most specific)
    # Separator class: comma, colon, hyphen, em-dash, en-dash, OR pure whitespace.
    # Using [\s,:\u2014\u2013\-]* (zero or more) lets us match:
    #   "file.md Finding N"   "file.md, Finding N"   "file.md — Finding N"   etc.
    for part in parts:
        match = re.match(
            r"([\w\-]+\.md)[\s,:\u2014\u2013\-]*Findings?\s*([\d,\s]+)",
            part.strip(),
        )
        if match:
            filename = match.group(1)
            nums = re.findall(r"\d+", match.group(2))
            for num in nums:
                key = f"{filename}:{num}"
                if key in sources_lookup:
                    return sources_lookup[key]

    # Strategy 2: filename only (file-level fallback)
    # Many references cite "filename.md § Section X.Y" or just "filename.md"
    # without a specific Finding number. Return ANY URL for that file —
    # users land on the right reference, just not the exact finding.
    for part in parts:
        match = re.match(r"([\w\-]+\.md)", part.strip())
        if match:
            filename = match.group(1)
            for key, url in sources_lookup.items():
                if key.startswith(f"{filename}:"):
                    return url

    return None


def humanize_reference(reference_str):
    """Convert a raw REFERENCE field into human-readable label(s).

    Auditors write references like:
      "schema-product-markup.md; ai-search-agentic-discovery.md"
      "title-formulas-serp-psychology.md Finding 6"
      "ethics-gate.md § 1.3 Reviews / Social Proof"
      "trust-and-credibility.md — trust badge placement"

    For client-facing reports, the raw filenames look like dev jargon. This
    helper:
      - Strips the .md extension
      - Replaces hyphens with spaces and title-cases the result
      - Drops finding numbers, section markers (§), and trailing notes
      - Joins multiple references with ", "

    Examples:
      "schema-product-markup.md; ai-search-agentic-discovery.md"
        -> "Schema Product Markup, AI Search Agentic Discovery"
      "title-formulas-serp-psychology.md Finding 6"
        -> "Title Formulas SERP Psychology"
      "ethics-gate.md § 1.3 Reviews / Social Proof"
        -> "Ethics Gate"
    """
    if not reference_str:
        return ""

    parts = re.split(r";\s*", reference_str)
    labels = []
    seen = set()
    for part in parts:
        match = re.match(r"([\w\-]+\.md)", part.strip())
        if not match:
            continue
        filename = match.group(1)
        slug = filename[:-3]  # strip .md
        # Special-case acronyms that title() butchers
        words = []
        for w in slug.split("-"):
            if w.lower() in ("seo", "serp", "ux", "ui", "ai", "ar", "cta", "url", "ugc", "eeat", "bnpl", "cwv", "lcp", "cls", "ftc", "dsa"):
                words.append(w.upper())
            else:
                words.append(w.title())
        label = " ".join(words)
        if label not in seen:
            seen.add(label)
            labels.append(label)
    return ", ".join(labels)
