"""Guard: the acquisition redirect guard blocks private/metadata IP hosts.

Regression for the repo-wide-review D3 finding #6 (2026-06-18). guardrails_fail_reason
only blocked cross-HOST redirects, so a same-host redirect to a private/loopback/
metadata IP — or an initial request URL that is itself such an IP — passed. It now
routes both the request and the post-redirect final URL through validate_url, while
preserving the existing cross-host and auth-path checks.

Run:
    python -m pytest tests/test_guardrails_private_redirect.py
    python -m unittest tests.test_guardrails_private_redirect
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts"))

from ecp_acquire_overlays import guardrails_fail_reason  # noqa: E402


class GuardrailsPrivateRedirect(unittest.TestCase):
    def test_same_host_redirect_to_private_ip_blocked(self):
        # The bug: host is unchanged conceptually but the final URL is a private IP.
        reason = guardrails_fail_reason(
            request_url="https://shop.example.com/p", final_href="http://10.0.0.5/admin")
        self.assertIsNotNone(reason)
        self.assertIn("private", reason.lower())

    def test_redirect_to_cloud_metadata_blocked(self):
        reason = guardrails_fail_reason(
            request_url="https://shop.example.com/p",
            final_href="http://169.254.169.254/latest/meta-data/")
        self.assertIsNotNone(reason)

    def test_request_url_that_is_private_ip_blocked(self):
        reason = guardrails_fail_reason(
            request_url="http://127.0.0.1:8080/", final_href="http://127.0.0.1:8080/")
        self.assertIsNotNone(reason)
        self.assertIn("request", reason.lower())

    def test_encoding_bypass_blocked(self):
        reason = guardrails_fail_reason(
            request_url="https://shop.example.com/p", final_href="http://2130706433/")
        self.assertIsNotNone(reason)

    def test_normal_same_host_redirect_allowed(self):
        self.assertIsNone(guardrails_fail_reason(
            request_url="https://shop.example.com/p",
            final_href="https://shop.example.com/p?ref=hero"))

    def test_cross_host_still_blocked(self):
        reason = guardrails_fail_reason(
            request_url="https://shop.example.com/p", final_href="https://evil.example.org/p")
        self.assertIsNotNone(reason)

    def test_auth_path_still_blocked(self):
        reason = guardrails_fail_reason(
            request_url="https://shop.example.com/p", final_href="https://shop.example.com/login")
        self.assertIsNotNone(reason)


class GuardrailsRedirectHostEquality(unittest.TestCase):
    """Regression (adversarial review 2026-07-08 finding #4): the same-site
    redirect guard must compare the registrable domain (port-stripped), not the
    raw netloc, so legitimate redirects don't abort the whole audit."""

    def _allowed(self, req, fin):
        self.assertIsNone(
            guardrails_fail_reason(request_url=req, final_href=fin),
            f"{req} -> {fin} should be allowed",
        )

    def _blocked(self, req, fin):
        self.assertIsNotNone(
            guardrails_fail_reason(request_url=req, final_href=fin),
            f"{req} -> {fin} should be blocked",
        )

    def test_port_normalization_allowed(self):
        self._allowed("https://store.com/p", "https://store.com:443/p")

    def test_apex_to_subdomain_allowed(self):
        self._allowed("https://example.com/p", "https://shop.example.com/p")

    def test_subdomain_to_apex_allowed(self):
        self._allowed("https://shop.example.com/p", "https://example.com/p")

    def test_cross_subdomain_same_parent_allowed(self):
        self._allowed("https://shop.example.com/p", "https://secure.example.com/p")

    def test_geo_subdomain_allowed(self):
        self._allowed("https://brand.com/p", "https://us.brand.com/p")

    def test_www_to_apex_allowed(self):
        self._allowed("https://www.example.com/p", "https://example.com/p")

    def test_different_registrable_domain_blocked(self):
        self._blocked("https://shop.example.com/p", "https://evil.example.org/p")


class GuardrailsAuthPathSegments(unittest.TestCase):
    """Regression (adversarial review 2026-07-08 finding #18): auth-path
    detection must match whole path SEGMENTS, not raw substrings, so ordinary
    ecommerce/blog URLs aren't false-classified as login pages and blocked."""

    def _allowed(self, path):
        self.assertIsNone(
            guardrails_fail_reason(
                request_url="https://store.com/p", final_href=f"https://store.com{path}"),
            f"path {path} should NOT be treated as an auth page",
        )

    def _blocked(self, path):
        self.assertIsNotNone(
            guardrails_fail_reason(
                request_url="https://store.com/p", final_href=f"https://store.com{path}"),
            f"path {path} should be treated as an auth page",
        )

    def test_password_product_slug_allowed(self):
        self._allowed("/products/1password-case")

    def test_authors_blog_path_allowed(self):
        self._allowed("/authors/jane-doe")

    def test_login_segment_blocked(self):
        self._blocked("/login")

    def test_nested_login_segment_blocked(self):
        self._blocked("/account/login")

    def test_auth_segment_blocked(self):
        self._blocked("/auth/callback")


if __name__ == "__main__":
    unittest.main()
