"""Path safety helpers — ensure operator-supplied and baton-supplied paths
stay inside their intended base directory.

Rationale: ``generate-report.py`` and ``assemble-audit.py`` accept path
inputs from operators (``--markers``, ``--priority-path``) and from
trusted-looking but potentially crafted data files (``baton.json``'s
screenshot paths). A path traversal like ``../../Windows/win.ini`` in a
baton could base64-embed arbitrary local files into a customer-facing
HTML report. ``resolve_within_base`` rejects those paths with a clear
``ValueError`` before any file read reaches the renderer.

Typical failure modes this guards against:

- A malicious baton with ``"path": "../../../../etc/passwd"`` for a
  screenshot entry. Without containment, the renderer would embed the
  passwd file as base64 into the HTML.
- A carelessly-set ``--markers`` path pointing at a system file or at
  another engagement's data.
- A synthesizer response file path written by an automation that
  doesn't sanitize the suggested filename.

Not a guard against:

- The operator explicitly choosing to write output to an arbitrary path
  (``--output``). Write destinations can't embed external content into
  the report; they just decide where the report lands. Normalization is
  still useful but containment is too restrictive for legitimate
  redirect workflows.
- Actively malicious operators running the CLI with full shell access.
  The guard raises the bar against accidents and untrusted data, not
  against a determined adversary with arbitrary-code-execution.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union


PathLike = Union[str, Path]


def resolve_within_base(path: PathLike, base: PathLike) -> Path:
    """Resolve ``path`` (relative or absolute) and assert it stays inside ``base``.

    Returns a fully resolved ``Path`` when containment holds. Raises
    ``ValueError`` when the path escapes the base via ``..`` components,
    symlinks to outside locations, or an absolute path that points
    elsewhere.

    Resolution rules:

    - Relative paths are joined with ``base`` BEFORE resolve, so
      ``resolve_within_base("foo.jpg", "/eng")`` checks ``/eng/foo.jpg``.
    - Absolute paths are resolved directly and must land inside ``base``.
    - ``..`` components are canonicalized by ``Path.resolve()``.
    - Symlinks are followed (the real target is what gets checked).

    Platform notes:

    - On Windows, junctions and symlinks resolve through, so an attacker
      who plants a junction inside ``base`` pointing outside it will
      still fail containment because the resolved real path escapes.
    - ``Path.resolve()`` with the default ``strict=False`` resolves
      non-existent paths by concatenation. Containment check works on
      non-existent targets; callers check existence separately.
    """
    p = Path(path)
    if not p.is_absolute():
        p = Path(base) / p
    resolved = p.resolve()
    base_resolved = Path(base).resolve()
    try:
        resolved.relative_to(base_resolved)
    except ValueError as exc:
        raise ValueError(
            f"Path {str(path)!r} escapes base directory {str(base)!r} "
            f"(resolved to {resolved})"
        ) from exc
    return resolved
