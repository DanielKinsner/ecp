#!/usr/bin/env python3
"""Normalize CRLF -> LF for text files (best-effort, utf-8)."""

from __future__ import annotations

import argparse
from pathlib import Path


TEXT_EXT = {
    ".md",
    ".mdc",
    ".json",
    ".py",
    ".ps1",
    ".yml",
    ".yaml",
    ".txt",
    ".sh",
}


def should_process(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXT:
        return True
    # extensionless files (rare) — skip
    return False


def normalize_file(path: Path) -> bool:
    data = path.read_bytes()
    if b"\r\n" not in data and b"\r" not in data:
        return False
    text = data.decode("utf-8", errors="strict")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    path.write_text(text, encoding="utf-8", newline="\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize CRLF to LF for text files under paths")
    parser.add_argument("paths", nargs="+", help="Files or directories to scan")
    args = parser.parse_args()

    changed = 0
    scanned = 0

    roots: list[Path] = [Path(p) for p in args.paths]
    for root in roots:
        if root.is_file():
            candidates = [root]
        else:
            candidates = [p for p in root.rglob("*") if p.is_file()]

        for path in candidates:
            if not should_process(path):
                continue
            scanned += 1
            try:
                if normalize_file(path):
                    changed += 1
            except OSError:
                continue

    print(f"OK scanned={scanned} changed={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
