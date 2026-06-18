"""Pin the atomic-write invariant: never leave a half-written deliverable.

Stabilization guard for the repo-wide-review D8 finding (2026-06-18). Every v2
writer routes through atomic_write_json / atomic_write_text so the canonical file
is either fully written or unchanged — never half-written (contracts/
lead-discipline.md write-atomicity rule; product.md export-integrity intent).
The helpers were unprotected by any test. This pins the two load-bearing
guarantees so a future edit to the temp+rename pattern can't silently regress:

  1. A write that fails mid-way leaves a pre-existing canonical file byte-identical
     and unchanged, and leaves no orphaned .tmp file behind.
  2. A successful write produces deterministic, LF-terminated output.

Run:
    python -m pytest tests/test_atomic_write_invariant.py
    python -m unittest tests.test_atomic_write_invariant
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.atomic_write import atomic_write_json, atomic_write_text  # noqa: E402


def _orphan_tmps(d: Path) -> list[str]:
    return [p.name for p in d.iterdir() if p.name.endswith(".tmp")]


class AtomicWriteInvariant(unittest.TestCase):
    def test_json_success_is_deterministic_and_lf_terminated(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "meta.json"
            atomic_write_json(path, {"b": 2, "a": 1})
            raw = path.read_bytes()
            # sorted keys + trailing newline + LF (no CRLF even on Windows)
            self.assertEqual(raw, b'{\n  "a": 1,\n  "b": 2\n}\n')
            self.assertNotIn(b"\r\n", raw)
            self.assertEqual(_orphan_tmps(Path(d)), [])

    def test_json_failure_preserves_canonical_and_leaves_no_orphan(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "review-state.json"
            atomic_write_json(path, {"ok": True})
            before = path.read_bytes()

            # A set is not JSON-serializable -> json.dump raises mid-write.
            with self.assertRaises(TypeError):
                atomic_write_json(path, {"bad": {1, 2, 3}})

            self.assertEqual(path.read_bytes(), before, "canonical file must be unchanged")
            self.assertEqual(_orphan_tmps(Path(d)), [], "no .tmp orphan may remain")

    def test_replace_failure_preserves_canonical_and_leaves_no_orphan(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "audit.md"
            atomic_write_text(path, "original")
            before = path.read_bytes()

            real_replace = os.replace

            def boom(src, dst):
                raise OSError("simulated rename failure")

            os.replace = boom
            try:
                with self.assertRaises(OSError):
                    atomic_write_text(path, "new content that must not land")
            finally:
                os.replace = real_replace

            self.assertEqual(path.read_bytes(), before, "canonical file must be unchanged")
            self.assertEqual(_orphan_tmps(Path(d)), [], "no .tmp orphan may remain")

    def test_text_success_forces_lf_and_trailing_newline(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "lead-reflection.md"
            atomic_write_text(path, "line1\nline2")  # no trailing newline supplied
            raw = path.read_bytes()
            self.assertTrue(raw.endswith(b"\n"))
            self.assertNotIn(b"\r\n", raw)


if __name__ == "__main__":
    unittest.main()
