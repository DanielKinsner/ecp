"""Guard: acquire_url rejects bad URLs BEFORE launching the browser.

Regression for the repo-wide-review D3 finding #7 (2026-06-18). The pre-navigation
gate in acquire_url.main() runs validate_url on args.url right after arg parsing —
before _ensure_agent_browser() or any disk write — and returns exit code 2 on a
disallowed scheme / private-or-reserved IP / IP-encoding bypass.

Run:
    python -m pytest tests/test_acquire_url_pre_nav_gate.py
    python -m unittest tests.test_acquire_url_pre_nav_gate
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts"))

import acquire_url  # noqa: E402


class PreNavigationGate(unittest.TestCase):
    def _main_with_url(self, url: str) -> int:
        argv = ["acquire_url.py", "--url", url, "--engagement-id", "zz-prenav-unit-test"]
        old = sys.argv
        sys.argv = argv
        try:
            return acquire_url.main()
        finally:
            sys.argv = old

    def test_disallowed_scheme_returns_2(self):
        self.assertEqual(self._main_with_url("file:///etc/passwd"), 2)

    def test_private_ip_returns_2(self):
        self.assertEqual(self._main_with_url("http://10.0.0.5/"), 2)

    def test_metadata_ip_returns_2(self):
        self.assertEqual(self._main_with_url("http://169.254.169.254/latest/meta-data/"), 2)

    def test_encoding_bypass_returns_2(self):
        self.assertEqual(self._main_with_url("http://2130706433/"), 2)

    def test_no_engagement_dir_created_for_bad_url(self):
        eng = _REPO / "docs" / "ecp" / "zz-prenav-unit-test"
        self._main_with_url("javascript:alert(1)")
        self.assertFalse(eng.exists(), "bad URL must fail before any disk write")


if __name__ == "__main__":
    unittest.main()
