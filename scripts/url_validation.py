"""Deterministic URL validation for acquisition.

Code-pins the string/parse-level rules of ``contracts/url-validation.md``
(§1 scheme, §2 IPv4 private/reserved, §3 IPv6, §4 encoding-bypass). Before this,
those rules were enforcement-by-prose only — unlike the eval channel, which is
code-pinned. ``validate_url`` is the single deterministic guard used at both the
pre-navigation gate and the post-redirect check.

Out of scope here (inherently runtime / agent concerns, see the contract):
  §5 DNS-rebinding — must re-check the RESOLVED IP at fetch time, which the
     browser does; a pure validator can't resolve deterministically.
  §6 per-domain user confirmation — agent/operator behavior, not a string rule.
"""
from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urlparse

_ALLOWED_SCHEMES = ("http", "https")
_PRIVATE_MSG = "Cannot fetch private or internal network addresses."
_ENCODING_MSG = "IP address encoding not supported. Use standard dotted notation."

_STRICT_DOTTED_QUAD = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")


def _reserved_ip_reason(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> str | None:
    """Reject loopback / private / link-local / reserved / unspecified / multicast."""
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        mapped = _reserved_ip_reason(ip.ipv4_mapped)  # e.g. ::ffff:127.0.0.1
        if mapped:
            return mapped
    if (ip.is_loopback or ip.is_private or ip.is_link_local
            or ip.is_reserved or ip.is_unspecified or ip.is_multicast):
        return _PRIVATE_MSG
    return None


def _is_standard_ipv4(host: str) -> bool:
    """True only for canonical dotted-quad (4 octets, 0-255, no leading zeros)."""
    if not _STRICT_DOTTED_QUAD.match(host):
        return False
    for octet in host.split("."):
        if len(octet) > 1 and octet[0] == "0":
            return False  # leading zero == octal encoding, not standard
        if int(octet) > 255:
            return False
    return True


def _is_alternate_ip_encoding(host: str) -> bool:
    """True for decimal / hex / octal / abbreviated IPv4 forms (bypass attempts)."""
    if re.fullmatch(r"0[xX][0-9a-fA-F]+", host):  # bare hex, e.g. 0x7f000001
        return True
    try:
        socket.inet_aton(host)  # accepts dotted, decimal, hex, octal, abbreviated
        return True             # standard dotted-quad already handled by the caller
    except OSError:
        return False


def _host_ip_reason(host: str) -> str | None:
    """If host is (or encodes) an IP literal, return a block reason, else None."""
    # IPv6 literal (urlparse strips the [...] brackets, so it appears bare).
    try:
        return _reserved_ip_reason(ipaddress.IPv6Address(host))
    except ValueError:
        pass
    if _is_standard_ipv4(host):
        try:
            return _reserved_ip_reason(ipaddress.IPv4Address(host))
        except ValueError:
            return _PRIVATE_MSG
    if _is_alternate_ip_encoding(host):
        return _ENCODING_MSG
    return None  # ordinary hostname — DNS-rebinding (§5) is re-checked at fetch time


def validate_url(url: str) -> str | None:
    """Return a human-readable block reason for ``url``, or None if it is allowed.

    Enforces contracts/url-validation.md §1-§4 deterministically.
    """
    if not url or not isinstance(url, str):
        return "Empty or non-string URL."

    # Shell-injection hardening (adversarial review 2026-07-08 #13): the URL is
    # passed as an argv to the agent-browser `goto` subcommand, which on Windows
    # resolves to an npm .cmd/.ps1 shim that re-parses argv through cmd.exe /
    # PowerShell (the eval channel dodges this via base64; goto cannot). Reject
    # characters that never appear UNENCODED in a valid URL (RFC 3986 excluded /
    # "unwise") but ARE shell/quote breakouts: C0/C1 controls, whitespace,
    # double-quote, backtick, angle brackets. This is zero-false-positive — a
    # real URL percent-encodes all of these.
    # NOTE (residual): cmd/PowerShell command separators that ARE legal in a URL
    # (`&` in query strings, `;` `(` `)` `|`) are NOT rejected here — that would
    # bounce legitimate URLs. Fully closing those requires invoking agent-browser
    # without the shim's argv reparse (resolve the real node entry, not the
    # .cmd), a tracked Windows follow-up.
    if any(ord(c) < 0x20 or ord(c) == 0x7F for c in url):
        return "URL contains control characters."
    if any(c in url for c in '" `<>\t\n\r'):
        return "URL must percent-encode spaces, quotes, backticks, and angle brackets."

    try:
        parsed = urlparse(url.strip())
    except (ValueError, TypeError):
        return "URL parse error."

    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        return "Only http:// and https:// URLs are supported."

    host = (parsed.hostname or "").lower()
    if not host:
        return "URL has no host."
    if host == "localhost" or host.endswith(".localhost"):
        return _PRIVATE_MSG

    return _host_ip_reason(host)


def is_url_allowed(url: str) -> bool:
    """Convenience boolean wrapper around ``validate_url``."""
    return validate_url(url) is None
