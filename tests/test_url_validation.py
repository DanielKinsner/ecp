"""Guard tests for the deterministic URL validator (url_validation.validate_url).

Code-pins contracts/url-validation.md §1-§4. Closes the repo-wide-review D3
finding (2026-06-18): URL validation was enforcement-by-prose with no
deterministic guard, unlike the eval channel.

Run:
    python -m pytest tests/test_url_validation.py
    python -m unittest tests.test_url_validation
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts"))

from url_validation import validate_url, is_url_allowed  # noqa: E402


class AllowedUrls(unittest.TestCase):
    def test_normal_public_sites_pass(self):
        for url in (
            "https://example.com",
            "http://example.com/product?id=1#frag",
            "https://shop.example.co.uk/p/123",
            "https://www.slingmods.com/",
            "http://8.8.8.8/",  # public IP literal is allowed (not private/reserved)
        ):
            self.assertIsNone(validate_url(url), url)
            self.assertTrue(is_url_allowed(url), url)


class SchemeRejection(unittest.TestCase):
    def test_non_http_schemes_blocked(self):
        for url in (
            "file:///etc/passwd",
            "data:text/html,<script>alert(1)</script>",
            "javascript:alert(1)",
            "ftp://example.com/x",
            "blob:https://example.com/uuid",
        ):
            self.assertIsNotNone(validate_url(url), url)


class PrivateIpv4Rejection(unittest.TestCase):
    def test_private_and_reserved_ranges_blocked(self):
        for url in (
            "http://127.0.0.1/",
            "http://127.0.0.1:8080/",
            "http://10.0.0.5/",
            "http://172.16.0.1/",
            "http://192.168.1.1/",
            "http://169.254.169.254/latest/meta-data/",  # cloud metadata
            "http://0.0.0.0/",
        ):
            self.assertEqual(validate_url(url),
                             "Cannot fetch private or internal network addresses.", url)

    def test_localhost_blocked(self):
        for url in ("http://localhost/", "http://localhost:3000/", "https://api.localhost/"):
            self.assertIsNotNone(validate_url(url), url)


class Ipv6Rejection(unittest.TestCase):
    def test_loopback_and_local_ipv6_blocked(self):
        for url in (
            "http://[::1]/",
            "http://[fc00::1]/",
            "http://[fe80::1]/",
            "http://[::ffff:127.0.0.1]/",  # IPv4-mapped loopback
        ):
            self.assertIsNotNone(validate_url(url), url)


class EncodingBypassRejection(unittest.TestCase):
    def test_alternate_ip_encodings_blocked(self):
        # All of these decode to 127.0.0.1; the contract rejects the *encoding*.
        for url in (
            "http://0x7f000001/",   # hex
            "http://0177.0.0.1/",   # octal
            "http://127.1/",        # abbreviated
            "http://2130706433/",   # decimal
        ):
            self.assertEqual(validate_url(url),
                             "IP address encoding not supported. Use standard dotted notation.", url)


class Malformed(unittest.TestCase):
    def test_empty_and_hostless(self):
        self.assertIsNotNone(validate_url(""))
        self.assertIsNotNone(validate_url(None))  # type: ignore[arg-type]
        self.assertIsNotNone(validate_url("https://"))


if __name__ == "__main__":
    unittest.main()
