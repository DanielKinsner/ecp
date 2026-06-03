"""Cross-platform stdio hardening for ECP CLI entry points.

Why this exists: the ECP CLIs print non-ASCII characters (em dash ``—``,
multiplication sign ``×``, check marks) into status/notice messages on
stdout/stderr. On Windows, a piped stdio stream defaults to the legacy ANSI
code page (cp1252), so those characters are emitted as cp1252 bytes (e.g.
``—`` -> ``0x97``, ``×`` -> ``0xd7``). Any caller that reads the pipe as UTF-8
— the E2E test harness, the Node ``serve-editor`` layer, a shell redirect —
then crashes its reader with ``UnicodeDecodeError`` and loses the output
entirely (``subprocess.run`` returns ``stdout=None``).

The fix is launcher-independent: each CLI forces its own stdout/stderr to
UTF-8 at startup, so the process is correct whether it is spawned by the Node
tooling, run directly by the operator, or driven by the test suite. UTF-8 can
encode every Unicode code point, so the output side never needs an error
handler.
"""

from __future__ import annotations

import sys


def force_utf8_io() -> None:
    """Reconfigure stdout/stderr to UTF-8 regardless of platform locale.

    Idempotent and safe to call first thing in ``main()``. Streams that do not
    support ``reconfigure`` (already detached, replaced by a non-text capture
    buffer, etc.) are skipped rather than raising — hardening output encoding
    must never itself crash the CLI.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            # Stream is detached/closed or otherwise refuses re-encoding;
            # leaving its existing encoding in place is the safe fallback.
            pass
