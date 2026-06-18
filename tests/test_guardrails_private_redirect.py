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


if __name__ == "__main__":
    unittest.main()
