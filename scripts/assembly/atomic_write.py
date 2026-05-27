"""Atomic file-write helpers for v2 pipeline.

All v2 writers (baton, cluster-emission, ethics-findings, synthesizer-emission,
meta.json, lead-state.json, lead-reflection.md, audit.md) MUST use these helpers
to write to disk. The pattern is: write to <filename>.tmp, then os.replace() to
the canonical name. Partial writes are orphaned tempfiles that resume logic
ignores; the canonical file is either fully-written or unchanged — never
half-written.

Closes Kieran's filesystem-race / partial-write concern from the technical-review
pass. Documented in contracts/lead-discipline.md write-atomicity rule.

Authored 2026-04-27 as Phase A.3b deliverable of the v2 redesign.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write_json(path: str | Path, payload: Any, *, indent: int = 2) -> None:
    """Write a JSON-serializable payload to ``path`` atomically.

    Uses ``json.dumps(sort_keys=True, ensure_ascii=False)`` for determinism
    (closes deepen-pass item 10 — byte-identical output across runs requires
    sorted keys + UTF-8). Forces ``\\n`` line endings to keep behavior identical
    on Windows vs POSIX (operator's environment is Windows; Windows default
    ``\\r\\n`` would break byte-equality assertions in Phase J fixture testing).

    On any exception during write, the orphaned tempfile is removed and the
    exception re-raised. The canonical file at ``path`` is unchanged.
    """
    path = Path(path)
    parent = path.parent if path.parent != Path("") else Path(".")
    parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump(payload, f, sort_keys=True, ensure_ascii=False, indent=indent)
            f.write("\n")  # POSIX convention; trailing newline is expected.
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass  # best-effort cleanup; OS will reclaim eventually
        raise


def atomic_write_text(path: str | Path, content: str) -> None:
    """Write ``content`` to ``path`` atomically.

    Forces UTF-8 encoding and ``\\n`` line endings (see ``atomic_write_json``
    for rationale). Suitable for markdown audit documents, lead-reflection
    files, agent-behavior logs, and any other text artifact in v2.

    Trailing newline is added if not already present (POSIX convention).
    """
    path = Path(path)
    parent = path.parent if path.parent != Path("") else Path(".")
    parent.mkdir(parents=True, exist_ok=True)

    if not content.endswith("\n"):
        content = content + "\n"

    fd, tmp_path = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        raise


__all__ = ["atomic_write_json", "atomic_write_text"]
