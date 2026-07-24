"""Guards for the installed-plugin freshness gate (P0-13, 2026-07-24).

Root cause being pinned: the installed ecp plugin runs from a frozen
cache snapshot, and editing the repo does not refresh it — historically
letting token-expensive audits run silently-stale code, noticed (if at
all) only via the report's version badge after the spend. The gate in
``scripts/preflight_freshness.py`` compares the running plugin tree
against the dev repo recorded in ``known_marketplaces.json`` and blocks
BEFORE any audit spend. These tests pin every verdict path plus the
SKILL.md wiring that makes the gate actually run.

unittest.TestCase shape on purpose — both runners must see these
(tests/test_runner_parity_guard.py rationale).
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import preflight_freshness as pf  # noqa: E402


def _make_tree(root: Path) -> None:
    """Minimal runtime tree: one file per manifest-relevant top entry."""
    (root / "scripts").mkdir(parents=True)
    (root / "scripts" / "tool.py").write_text("print('v1')\n", encoding="utf-8")
    (root / "contracts").mkdir()
    (root / "contracts" / "flags.md").write_text("# flags\n", encoding="utf-8")
    (root / "product.md").write_text("# product\n", encoding="utf-8")


class PreflightFreshnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="ecp-preflight-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = self.tmp / "repo"
        _make_tree(self.repo)
        self.marketplaces = self.tmp / "known_marketplaces.json"
        self._register_repo(self.repo)

    def _register_repo(self, path: Path) -> None:
        self.marketplaces.write_text(
            json.dumps(
                {"ecp": {"source": {"source": "directory", "path": str(path)}}}
            ),
            encoding="utf-8",
        )

    def _clone_plugin(self) -> Path:
        plugin = self.tmp / "cache-copy"
        shutil.copytree(self.repo, plugin)
        return plugin

    # ---- verdict paths ----------------------------------------------------

    def test_fresh_when_plugin_root_is_the_repo(self):
        """--plugin-dir mode: same directory means no snapshot to distrust."""
        self.assertEqual(pf.run(self.repo, self.marketplaces), 0)

    def test_fresh_when_snapshot_matches_repo(self):
        self.assertEqual(pf.run(self._clone_plugin(), self.marketplaces), 0)

    def test_stale_when_a_runtime_file_differs(self):
        plugin = self._clone_plugin()
        (self.repo / "scripts" / "tool.py").write_text("print('v2')\n", encoding="utf-8")
        self.assertEqual(pf.run(plugin, self.marketplaces), pf.STALE_EXIT)

    def test_stale_when_repo_has_a_file_the_snapshot_lacks(self):
        plugin = self._clone_plugin()
        (self.repo / "scripts" / "new_tool.py").write_text("x = 1\n", encoding="utf-8")
        self.assertEqual(pf.run(plugin, self.marketplaces), pf.STALE_EXIT)

    def test_stale_when_repo_deleted_a_file_the_snapshot_kept(self):
        plugin = self._clone_plugin()
        (self.repo / "contracts" / "flags.md").unlink()
        self.assertEqual(pf.run(plugin, self.marketplaces), pf.STALE_EXIT)

    def test_pycache_noise_is_not_staleness(self):
        plugin = self._clone_plugin()
        cache_dir = plugin / "scripts" / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "tool.cpython-313.pyc").write_bytes(b"\x00\x01")
        self.assertEqual(pf.run(plugin, self.marketplaces), 0)

    def test_non_runtime_dirs_do_not_trigger_stale(self):
        """docs/tests/fixtures drift must not block an audit."""
        plugin = self._clone_plugin()
        (self.repo / "docs").mkdir()
        (self.repo / "docs" / "note.md").write_text("scratch\n", encoding="utf-8")
        self.assertEqual(pf.run(plugin, self.marketplaces), 0)

    # ---- SKIP degradation (never a false block off the dev boxes) ---------

    def test_skip_when_marketplaces_file_missing(self):
        self.assertEqual(
            pf.run(self._clone_plugin(), self.tmp / "nope.json"), 0
        )

    def test_skip_when_no_ecp_entry(self):
        self.marketplaces.write_text("{}", encoding="utf-8")
        self.assertEqual(pf.run(self._clone_plugin(), self.marketplaces), 0)

    def test_skip_when_registered_repo_dir_is_gone(self):
        self._register_repo(self.tmp / "deleted-checkout")
        self.assertEqual(pf.run(self._clone_plugin(), self.marketplaces), 0)

    def test_skip_when_marketplaces_json_is_corrupt(self):
        self.marketplaces.write_text("{not json", encoding="utf-8")
        self.assertEqual(pf.run(self._clone_plugin(), self.marketplaces), 0)

    # ---- wiring: the gate must actually run in the audit skill ------------

    def test_skill_md_wires_the_gate_as_p0(self):
        skill = (REPO_ROOT / "skills" / "audit" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("preflight_freshness.py", skill)
        self.assertIn("P0-13", skill)

    def test_real_repo_manifest_covers_the_load_order_surfaces(self):
        """The manifest must include the files the audit actually loads."""
        manifest = pf.build_manifest(REPO_ROOT)
        self.assertIn("skills/audit/SKILL.md", manifest)
        self.assertIn("contracts/lead-discipline.md", manifest)
        self.assertIn("scripts/preflight_freshness.py", manifest)
        self.assertIn("product.md", manifest)


if __name__ == "__main__":
    unittest.main()
