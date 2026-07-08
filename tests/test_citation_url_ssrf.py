"""Regression (adversarial review 2026-07-08): is_safe_citation_url must not
accept non-canonical numeric IPv4 hosts that browsers/libc still resolve to a
loopback or cloud-metadata address.

``ipaddress.ip_address`` only accepts canonical dotted-quad / IPv6 literals, so
decimal (``2130706433``), hex (``0x7f000001``), octal (``0177.0.0.1``) and
short-dotted (``127.1``) notations fell through to the "plain hostname, accept"
branch — defeating the guard's documented loopback/link-local/metadata SSRF
block. The fix normalises those forms and range-checks the real address.

unittest-style for `python -m unittest discover` compatibility.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.citations import is_safe_citation_url  # noqa: E402


class TestCitationUrlSsrfNumericHosts(unittest.TestCase):
    # Each of these resolves to 127.0.0.1 or 169.254.169.254 in a browser.
    BYPASS_URLS = [
        "http://2130706433/x",       # decimal 127.0.0.1
        "http://0x7f000001/x",       # hex 127.0.0.1
        "http://0177.0.0.1/x",       # octal-dotted 127.0.0.1
        "http://127.1/x",            # short-dotted 127.0.0.1
        "http://0x7f.0.0.1/x",       # mixed hex label
        "http://2852039166/x",       # decimal 169.254.169.254 (AWS/GCP IMDS)
        "http://0xA9FEA9FE/x",       # hex 169.254.169.254
    ]
    # Canonical loopback/metadata already blocked pre-fix — must stay blocked.
    CANONICAL_BLOCKED = [
        "http://127.0.0.1/x",
        "http://169.254.169.254/x",
        "http://10.0.0.5/x",
        "http://192.168.1.1/x",
        "http://localhost/x",
    ]
    # Real citation hosts — must remain accepted (no false positives).
    LEGIT = [
        "http://example.com/x",
        "https://www.nngroup.com/articles/y",
        "https://baymard.com:443/z",
        "http://8.8.8.8/x",          # public IP literal
        "https://sub.domain.co.uk/p",
    ]

    def test_numeric_bypass_hosts_rejected(self):
        for u in self.BYPASS_URLS:
            with self.subTest(url=u):
                self.assertFalse(
                    is_safe_citation_url(u),
                    f"{u!r} resolves to a loopback/metadata IP and must be rejected.",
                )

    def test_canonical_private_still_rejected(self):
        for u in self.CANONICAL_BLOCKED:
            with self.subTest(url=u):
                self.assertFalse(is_safe_citation_url(u), f"{u!r} must stay blocked.")

    def test_legit_hosts_still_accepted(self):
        for u in self.LEGIT:
            with self.subTest(url=u):
                self.assertTrue(
                    is_safe_citation_url(u),
                    f"{u!r} is a legitimate citation host and must be accepted.",
                )


if __name__ == "__main__":
    unittest.main()
