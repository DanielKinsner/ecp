"""Security guards for the hotspot-editor server (adversarial review 2026-07-08).

#14 — the loopback editor server had no Host/Origin validation, so a malicious
     page the operator is also visiting could DNS-rebind to 127.0.0.1 or fire a
     cross-origin POST (CSRF) to overwrite review-state / import assets.
#22 — /api/import-asset accepted any image/* including image/svg+xml, which the
     static server then served as image/svg+xml — an SVG with inline <script>
     was stored XSS in the editor origin.

Spawns the real Node server and drives it over HTTP. Gated on node + a committed
fixture (the server serves editor.html from the engagement dir).
"""
from __future__ import annotations

import base64
import json
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_FIXTURE = _REPO / "tests" / "fixtures" / "2026-05-02-9cd2a2ac"
_PORT = 8813

# Smallest valid 1x1 PNG (magic 89 50 4E 47).
_PNG_B64 = ("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4"
            "2mNk+M8AAAMBAQDJ/pLvAAAAAElFTkSuQmCC")


def _req(path_, *, method="GET", headers=None, data=None, port=_PORT):
    url = f"http://127.0.0.1:{port}{path_}"
    r = urllib.request.Request(url, method=method, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(r, timeout=5) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


@unittest.skipUnless(shutil.which("node") and _FIXTURE.exists(), "node + committed fixture required")
class EditorServerSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="ecp-editor-sec-"))
        cls.eng = cls.tmp / "e"
        shutil.copytree(_FIXTURE, cls.eng)
        cls.proc = subprocess.Popen(
            ["node", "scripts/serve-editor.cjs", "--engagement", str(cls.eng), "--port", str(_PORT)],
            cwd=str(_REPO), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        # Wait for readiness.
        for _ in range(60):
            try:
                _req("/editor.html")
                break
            except Exception:
                time.sleep(0.1)
        else:
            raise RuntimeError("editor server did not start")

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        try:
            cls.proc.wait(timeout=5)
        except Exception:
            cls.proc.kill()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    # ---- #14: Host / Origin -------------------------------------------------
    def test_correct_host_serves(self):
        status, _ = _req("/editor.html", headers={"Host": f"127.0.0.1:{_PORT}"})
        self.assertEqual(status, 200)

    def test_foreign_host_rejected_dns_rebinding(self):
        status, _ = _req("/editor.html", headers={"Host": "evil.example.com"})
        self.assertEqual(status, 403)

    def test_cross_site_post_rejected_csrf(self):
        body = json.dumps({"state": {"device": "desktop"}}).encode()
        status, text = _req(
            "/api/render-review", method="POST", data=body,
            headers={"Host": f"127.0.0.1:{_PORT}", "Origin": "https://evil.example.com",
                     "Content-Type": "application/json"},
        )
        self.assertEqual(status, 403)
        self.assertIn("cross-origin", text)

    def test_same_origin_post_not_blocked_by_csrf_guard(self):
        # Same-origin POST passes the CSRF guard (it may still 4xx/5xx on payload,
        # but must NOT be the 403 cross-origin refusal).
        body = json.dumps({}).encode()
        status, text = _req(
            "/api/render-review", method="POST", data=body,
            headers={"Host": f"127.0.0.1:{_PORT}", "Origin": f"http://127.0.0.1:{_PORT}",
                     "Content-Type": "application/json"},
        )
        self.assertNotEqual((status, "cross-origin" in text), (403, True))

    # ---- #22: SVG stored-XSS ------------------------------------------------
    def _import(self, mime, b64):
        body = json.dumps({
            "asset_id": "t", "filename": f"x.{mime.split('/')[-1]}",
            "mime_type": mime, "data_url": f"data:{mime};base64,{b64}",
        }).encode()
        return _req("/api/import-asset", method="POST", data=body,
                    headers={"Host": f"127.0.0.1:{_PORT}", "Origin": f"http://127.0.0.1:{_PORT}",
                             "Content-Type": "application/json"})

    def test_svg_import_rejected(self):
        svg = base64.b64encode(b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>").decode()
        status, text = self._import("image/svg+xml", svg)
        self.assertEqual(status, 500)  # saveImportedAsset throws -> 500 json error
        self.assertIn("JPEG, PNG, WebP, or GIF", text)

    def test_png_import_accepted(self):
        status, text = self._import("image/png", _PNG_B64)
        self.assertEqual(status, 200)
        self.assertIn('"ok": true'.replace(" ", ""), text.replace(" ", ""))
        # Extension derives from the sniffed mime, not the client filename.
        self.assertIn(".png", text)

    def test_png_bytes_relabeled_as_svg_still_stored_as_png(self):
        # Client lies (mime_type/filename say svg) but the bytes are PNG -> the
        # sniff wins, so it is stored as a .png raster, never an executable svg.
        status, text = self._import("image/svg+xml", _PNG_B64)
        self.assertEqual(status, 200)
        self.assertIn(".png", text)
        self.assertNotIn(".svg", text)


if __name__ == "__main__":
    unittest.main()
