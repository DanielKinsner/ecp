"""Installed-plugin freshness gate (P0-13, 2026-07-24).

The installed ecp plugin runs from a frozen cache snapshot under
``~/.claude/plugins/cache/ecp/...``. Editing the repo does NOT update that
snapshot until ``claude plugin update ecp@ecp`` runs — which historically
let long, token-expensive audits execute silently-stale code, discovered
only after the spend (the version badge in the report header is a
post-hoc check). This script is the pre-spend mechanical gate: the audit
skill runs it at invocation start and a STALE verdict BLOCKS the audit
before any acquisition happens.

How it resolves "the repo": ``known_marketplaces.json`` records the ecp
marketplace as a ``directory`` source pointing at the dev checkout. On a
machine without that registration (or without the repo), there is nothing
to compare against, so the gate degrades to SKIP — it must never falsely
block a machine that only has the plugin.

Verdicts (stdout is ASCII-only — Windows cp1252 console gotcha):
  FRESH - running tree matches the repo, or IS the repo (--plugin-dir mode)
  STALE - runtime files differ; exit 2; the fix commands are printed
  SKIP  - no repo to compare against; exit 0

Exit codes: 0 = FRESH or SKIP (proceed), 2 = STALE (block).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

# Directories/files that affect audit behavior at runtime. Deliberately
# excludes tests/, fixtures/, docs/, archive/, graphify-out/ — those can
# drift without changing what an audit executes.
RUNTIME_PATHS = [
    ".claude-plugin",
    "citations",
    "contracts",
    "product.md",
    "references",
    "schema",
    "scripts",
    "skills",
    "templates",
    "workflows",
]

# Noise that differs between copies without being a real code change.
IGNORED_DIR_NAMES = {"__pycache__", "node_modules", ".git"}
IGNORED_FILE_SUFFIXES = (".pyc", ".pyo")

STALE_EXIT = 2
SAMPLE_LIMIT = 10


def _iter_runtime_files(root: Path):
    for top in RUNTIME_PATHS:
        p = root / top
        if p.is_file():
            yield p
        elif p.is_dir():
            for dirpath, dirnames, filenames in os.walk(p):
                dirnames[:] = [d for d in dirnames if d not in IGNORED_DIR_NAMES]
                for name in sorted(filenames):
                    if name.endswith(IGNORED_FILE_SUFFIXES):
                        continue
                    yield Path(dirpath) / name


def build_manifest(root: Path) -> dict:
    """Map of posix-style relative path -> sha256 for every runtime file."""
    manifest = {}
    for f in _iter_runtime_files(root):
        rel = f.relative_to(root).as_posix()
        manifest[rel] = hashlib.sha256(f.read_bytes()).hexdigest()
    return manifest


def resolve_repo_path(marketplaces_file: Path):
    """Return the dev-checkout path recorded for the ecp marketplace, or
    None when it can't be resolved (SKIP semantics — never a false block)."""
    try:
        data = json.loads(marketplaces_file.read_text(encoding="utf-8"))
        entry = data.get("ecp") or {}
        source = entry.get("source") or {}
        if source.get("source") != "directory":
            return None
        path = Path(source.get("path", ""))
        return path if path.is_dir() else None
    except (OSError, ValueError):
        return None


def _same_dir(a: Path, b: Path) -> bool:
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(
        os.path.realpath(b)
    )


def run(plugin_root: Path, marketplaces_file: Path) -> int:
    repo = resolve_repo_path(marketplaces_file)
    if repo is None:
        print("SKIP: no ecp dev-repo registration found; nothing to compare against.")
        return 0
    if _same_dir(plugin_root, repo):
        print("FRESH: running live from the repo (--plugin-dir mode); no snapshot involved.")
        return 0

    repo_manifest = build_manifest(repo)
    plugin_manifest = build_manifest(plugin_root)
    missing = sorted(set(repo_manifest) - set(plugin_manifest))
    extra = sorted(set(plugin_manifest) - set(repo_manifest))
    changed = sorted(
        rel
        for rel in set(repo_manifest) & set(plugin_manifest)
        if repo_manifest[rel] != plugin_manifest[rel]
    )

    if not (missing or extra or changed):
        print(f"FRESH: installed plugin matches the repo ({len(plugin_manifest)} runtime files verified).")
        return 0

    print("STALE: the installed plugin does NOT match the repo. BLOCK the audit - it would run old code.")
    print(f"  changed: {len(changed)}  missing-from-plugin: {len(missing)}  removed-from-repo: {len(extra)}")
    for label, paths in (("changed", changed), ("missing", missing), ("removed", extra)):
        for rel in paths[:SAMPLE_LIMIT]:
            print(f"  {label}: {rel}")
        if len(paths) > SAMPLE_LIMIT:
            print(f"  {label}: ... and {len(paths) - SAMPLE_LIMIT} more")
    print("Fix, then re-run the audit in a NEW session:")
    print("  claude plugin update ecp@ecp")
    return STALE_EXIT


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--plugin-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Root of the plugin copy actually running (default: this script's repo/snapshot).",
    )
    parser.add_argument(
        "--marketplaces",
        type=Path,
        default=Path.home() / ".claude" / "plugins" / "known_marketplaces.json",
        help="known_marketplaces.json to resolve the dev repo from (test override).",
    )
    args = parser.parse_args(argv)
    return run(args.plugin_root, args.marketplaces)


if __name__ == "__main__":
    sys.exit(main())
