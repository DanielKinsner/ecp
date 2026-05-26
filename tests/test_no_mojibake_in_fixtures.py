"""Phase 7 hardening (2026-05-18) — pin that committed JSON/MD fixtures
stay free of double-encoded UTF-8 mojibake.

Codex caught a regression in commit f0656ff where my Phase 7 fixture
migration script wrote 3 ethics-findings.json files through a Python
process whose default encoding turned `§`, `—`, `©`, etc. into `Â§`,
`â€"`, `Â©` (double-encoded UTF-8 → cp1252). This test scans every
committed JSON/MD fixture under tests/fixtures/, docs/ecp/, contracts/,
schema/ for the specific marker characters that signal mojibake.

Catches the next time anyone edits these files through a cp1252-default
Python on Windows without explicit ``encoding='utf-8'`` + ``ensure_ascii=False``.

Run isolated: ``pytest tests/test_no_mojibake_in_fixtures.py``.
"""
from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# The exact byte sequences that indicate double-encoded UTF-8. Each of
# these is what you see when a UTF-8 byte stream containing 2- or 3-byte
# chars was once decoded as cp1252 (or Latin-1) and re-encoded as UTF-8.
MOJIBAKE_MARKERS = (
    # 'Â' alone or followed by another high-byte char — UTF-8 0xC2 prefix
    # leaked through as a stray char. Appears in: Â§ (section), Â© (copyright),
    # Â° (degree), Â® (registered), etc.
    "Â",
    # 'â€' is the cp1252 reading of UTF-8 0xE2 0x80, prefix for most
    # General Punctuation chars: â€" (em dash), â€" (en dash),
    # â€" (open quote), â€" (close quote), â€™ (right single quote),
    # â€¦ (ellipsis), etc.
    "â€",
    # 'Ã' is the cp1252 reading of UTF-8 0xC3, prefix for the next chunk
    # of Latin-1 supplement chars (À-ÿ): Ã© (é), Ã¨ (è), Ã¼ (ü), etc.
    # Common in mojibake from European-language strings.
    "Ã",
    # U+FFFD replacement character — appears when a decoder couldn't
    # represent a byte at all. Always a bug; never a real text payload.
    "�",
)

# Directories to scan. ``docs/ecp`` covers committed engagement
# evidence + the -fixed sister-runs. ``tests/fixtures`` covers
# synthetic test fixtures. ``contracts`` and ``schema`` cover plugin
# contract docs that may contain prose with em dashes etc.
SCAN_DIRS = (
    REPO_ROOT / "tests" / "fixtures",
    REPO_ROOT / "docs" / "ecp",
    REPO_ROOT / "contracts",
    REPO_ROOT / "schema",
)

# Extensions to scan. Limited to UTF-8 text formats — binary files
# (JPEG, PNG) are excluded.
SCAN_EXTENSIONS = (".json", ".md")

# Engagement folders we know contain pre-Phase-7 mojibake INTENTIONALLY
# preserved as broken evidence. Per the operator decision documented in
# the 2026-05-18 audit cycle, this folder stays in its as-shipped state.
KNOWN_BROKEN_EVIDENCE_DIRS = {
    # Original broken awdmods engagement — kept exactly as it was so
    # future readers can see the bug Codex caught + the inline-patched
    # workaround. The sister-run at 5ff7a91f-fixed/ is the cleaned copy
    # that other tests load from.
    REPO_ROOT / "docs" / "ecp" / "2026-05-18-5ff7a91f",
}


# File-name patterns that hold OUR-authored content (specialist
# emissions, contract docs, schemas, plan docs). These should never
# contain mojibake — if they do, a Python/git/editor in the chain
# misencoded our output.
#
# Acquisition-time outputs (baton.json, cluster-context-*.json,
# dom*.html, review-state-*.json, visual-report-*.html, editor.html)
# are intentionally EXCLUDED — those are scraped from live web pages
# whose source HTML may already contain mojibake from the page itself,
# and "cleaning" them would diverge the evidence from the source.
# Codex's 2026-05-18 review of f0656ff scoped the regression to
# "introduced by THIS phase"; this scope filter honors that.
INCLUDED_FILENAME_PATTERNS = (
    "ethics-findings.json",
    "synthesizer-emission-v1.json",
    "canonical-f-refs.json",
    "meta.json",
)
INCLUDED_PARENT_DIRS = ("contracts", "schema", "tests/fixtures")


def _files_to_scan() -> list[Path]:
    out: list[Path] = []
    for root in SCAN_DIRS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.suffix.lower() not in SCAN_EXTENSIONS:
                continue
            if not path.is_file():
                continue
            # Skip files under a known-broken-evidence root.
            try:
                if any(
                    path.is_relative_to(broken)
                    for broken in KNOWN_BROKEN_EVIDENCE_DIRS
                ):
                    continue
            except AttributeError:  # pragma: no cover — Python < 3.9
                if any(
                    str(broken) in str(path) for broken in KNOWN_BROKEN_EVIDENCE_DIRS
                ):
                    continue
            rel = path.relative_to(REPO_ROOT)
            rel_str = str(rel).replace("\\", "/")
            # Scope filter: include only files we author (not scraped
            # acquisition output). Either filename match OR parent-dir match.
            included = (
                path.name in INCLUDED_FILENAME_PATTERNS
                or any(rel_str.startswith(d + "/") for d in INCLUDED_PARENT_DIRS)
            )
            if not included:
                continue
            out.append(path)
    return sorted(out)


@pytest.mark.parametrize("path", _files_to_scan(), ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_committed_fixture_has_no_mojibake(path: Path) -> None:
    """Codex 2026-05-18 regression: f0656ff committed CLEAR ethics
    migrations through a cp1252-default Python on Windows, producing
    Â§, â€", Â©, etc. in the JSON. This test pins the absence of those
    markers across every UTF-8 fixture we scan, with an explicit
    exception list for known-broken-evidence engagement folders.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        pytest.fail(f"{path} is not valid UTF-8: {e}")
    hits: dict[str, int] = {}
    for marker in MOJIBAKE_MARKERS:
        count = text.count(marker)
        if count:
            hits[marker] = count
    if hits:
        # Find the first line containing the most common marker so the
        # failure message is actionable (operator sees the exact line
        # to fix, not just a count).
        most_common = max(hits, key=lambda m: hits[m])
        sample_line = ""
        for line in text.splitlines():
            if most_common in line:
                sample_line = line.strip()[:200]
                break
        pytest.fail(
            f"Mojibake detected in {path}:\n"
            f"  counts: {hits}\n"
            f"  first offending line: {sample_line!r}\n"
            f"  fix: re-read + re-write the file with explicit "
            f"encoding='utf-8' and ensure_ascii=False; see "
            f"docs/ecp/2026-05-18-* for the Phase 7 hardening commit "
            f"with the canonical repair script."
        )
