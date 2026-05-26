#!/usr/bin/env python3
"""Pre-assembly validator for cluster audit files.

Runs over every ``cluster-{cluster}-{device}.md`` file in an engagement
directory and checks for the failure patterns observed in the
2026-04-21 awdmods engagement:

1. **Format contract violation** — cluster file uses markdown H3 pseudo-
   findings (``### CF-01 — Title``) instead of triple-backtick
   ``FINDING:`` code-fenced blocks. Downstream ``assemble-audit.py``
   parses zero findings from these files, silently losing entire clusters
   of work.
2. **Self-referential citation** — the ``↳`` citation tail points back
   at the cluster's own reference file as ``[Silver]`` filler (e.g.,
   ``↳ checkout-flows.md — cluster reference [Silver]``). This was
   sonnet's path of least resistance when it couldn't find an external
   source; it satisfies the format-contract requirement for a citation
   tail while providing zero external evidence.
3. **Ethics SOURCE_URL pointing at audited domain** — a finding marked
   ``ETHICS_STATE: ADJACENT`` or ``ETHICS_STATE: BLOCK`` cites the
   product URL as its source instead of the canonical regulation URL
   from ``references/ethics-gate.md``'s Source Registry.
4. **DPR-scaled pixel values in mobile titles** — mobile screenshot
   coordinates are DPR-scaled (e.g., y=2454 on an iPhone 14 where CSS
   y=818). Quoting those numbers in finding titles is meaningless to a
   store operator. Flag any title with a pixel value larger than 2x the
   CSS viewport width on mobile files.

Usage
-----

    # Lint one engagement, exit non-zero if any file fails
    python scripts/validate-cluster-files.py --engagement docs/ecp/{id}

    # Soft mode — warn but return 0
    python scripts/validate-cluster-files.py --engagement docs/ecp/{id} --warn-only

Returns exit code 0 if every cluster file passes. Exit code 1 if any
violation is found (unless ``--warn-only`` is passed). The lead
coordinator runs this between auditor-teammate completion and
``assemble-audit.py`` so structural issues surface as a signal to
``SendMessage`` the auditor for a corrective rewrite, rather than
silently parsing empty findings.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

# Regex for the only acceptable finding format — triple-backtick fenced
# ``FINDING:`` block. The renderer parser (scripts/report/parser.py)
# uses essentially the same pattern.
_FINDING_FENCE = re.compile(
    r"^```\s*$(?:\r?\n)FINDING:\s*(FAIL|PARTIAL)\s*$",
    re.MULTILINE,
)

# Pseudo-finding heading — common drift when sonnet defaults to a
# "report-style" markdown register instead of the code-fenced contract.
# Matches:
#   ``### CF-01 — Title``         (compact ID + dash)
#   ``### F-03: Title``           (compact F-ID + colon)
#   ``### Finding 5 - Title``     (verbose, H3)
#   ``## Finding CF-D-01: ...``   (verbose, H2 — observed 2026-04-24 awdmods)
#   ``## Finding 4 — ...``        (verbose H2 with em-dash)
_PSEUDO_FINDING_HEADING = re.compile(
    r"^#{2,3}[ \t]+(?:Finding[ \t]+)?(?:[A-Z]{1,4}-)?(?:F-)?[A-Z0-9]+(?:-[A-Z0-9]+)*[ \t]*[-—:][ \t]",
    re.MULTILINE | re.IGNORECASE,
)

# Meta-language voice leak — auditors quoting their own context-management
# work in client-facing OBSERVATION/RECOMMENDATION text. Observed
# 2026-04-24: "A thorough search of the full DOM (112,267 tokens) for
# cookie consent mechanisms..." propagated through audit.md into the
# visual report. None of these phrases describe page content; they
# describe the auditor's own scan effort and must not ship to a client.
_META_LANGUAGE_PATTERNS = [
    (re.compile(r"\(\s*\d[\d,]*\s+tokens?\s*\)", re.IGNORECASE), "token count"),
    (re.compile(r"\bfull DOM\s*\(\s*\d", re.IGNORECASE), "full DOM (N tokens)"),
    (re.compile(r"\bsearched the full DOM\b", re.IGNORECASE), "searched the full DOM"),
    (re.compile(r"\bcontext window\b", re.IGNORECASE), "context window"),
    (re.compile(r"\bI (scanned|searched|reviewed) the\b", re.IGNORECASE), "first-person scan"),
    (re.compile(r"\bmy (search|scan|review|analysis)\b", re.IGNORECASE), "first-person possessive"),
    (re.compile(r"\bin (this|the) prompt\b", re.IGNORECASE), "prompt reference"),
]

# Self-referential citation tail — the ``↳`` line points back at the
# cluster's own reference file as filler evidence. Matches
# ``↳ {cluster}.md — ...`` where ``{cluster}`` is the cluster whose
# file we are linting.
_CITATION_TAIL = re.compile(r"^↳\s*([\w-]+)\.md", re.MULTILINE)


def _find_fenced_findings(content: str) -> list[int]:
    """Return line numbers (1-based) of every FINDING code-fence opener."""
    hits = []
    for m in _FINDING_FENCE.finditer(content):
        hits.append(content[: m.start()].count("\n") + 1)
    return hits


def _find_pseudo_headings(content: str) -> list[tuple[int, str]]:
    hits = []
    for m in _PSEUDO_FINDING_HEADING.finditer(content):
        line_no = content[: m.start()].count("\n") + 1
        line = content[m.start() : content.find("\n", m.start())]
        hits.append((line_no, line.strip()))
    return hits


def _find_self_citations(content: str, cluster: str) -> list[tuple[int, str]]:
    """Return (line_no, line) tuples for ``↳ {cluster}.md`` tails.

    The rule is about the cluster's own file being cited as a source of
    evidence, not about every reference-file citation. We flag only
    when the cited reference filename equals the cluster slug — that is
    the filler pattern sonnet defaults to.

    Known non-issues that should NOT be flagged:
    - Citing a cluster-specific reference file (e.g., ``pricing F-01``
      citing ``bnpl-payment.md`` is fine; ``bnpl-payment`` is a
      reference, not the cluster slug)
    - Cross-cluster citations (``↳ ethics-gate.md``)
    """
    hits = []
    for m in _CITATION_TAIL.finditer(content):
        ref_filename = m.group(1)
        if ref_filename == cluster:
            line_no = content[: m.start()].count("\n") + 1
            line = content[m.start() : content.find("\n", m.start())]
            hits.append((line_no, line.strip()))
    return hits


def _find_ethics_misroute(content: str, page_netloc: str | None) -> list[tuple[int, str]]:
    """Return violations where an ethics finding's SOURCE_URL points at
    the audited domain."""
    hits = []
    if not page_netloc:
        return hits

    # Scan FINDING blocks for ETHICS_STATE: ADJACENT | BLOCK, then
    # inspect the SOURCE_URL field (if present) in the same block.
    block_pattern = re.compile(
        r"^```[\s\S]*?^FINDING:[\s\S]*?^```",
        re.MULTILINE,
    )
    for block_match in block_pattern.finditer(content):
        block = block_match.group(0)
        ethics_match = re.search(
            r"^ETHICS_STATE:\s*(ADJACENT|BLOCK)", block, re.MULTILINE
        )
        if not ethics_match:
            continue
        source_url_match = re.search(r"^SOURCE_URL:\s*(\S+)", block, re.MULTILINE)
        if not source_url_match:
            # Missing SOURCE_URL entirely — renderer will fall back to
            # the page URL, which is what we are trying to prevent.
            line_no = content[: block_match.start()].count("\n") + 1
            hits.append(
                (
                    line_no,
                    f"ethics finding ({ethics_match.group(1)}) has no SOURCE_URL; "
                    f"add canonical regulation URL from ethics-gate.md",
                )
            )
            continue
        src = source_url_match.group(1).strip().strip("<>")
        try:
            src_netloc = (urlparse(src).netloc or "").lower().lstrip("www.")
        except ValueError:
            continue
        if src_netloc == page_netloc:
            line_no = content[: source_url_match.start()].count("\n") + 1
            hits.append(
                (
                    line_no,
                    f"ethics finding cites the audited domain ({src_netloc}) as "
                    f"its SOURCE_URL; cite the regulation's canonical URL "
                    f"instead (see ethics-gate.md Source Registry)",
                )
            )
    return hits


def _find_meta_language(content: str) -> list[tuple[int, str]]:
    """Detect auditor meta-language leaks (token counts, first-person scan,
    context window references) inside FINDING blocks. Restricted to
    code-fenced blocks so prose preamble (e.g., "Why this matters" essays
    in the cluster file's intro) does not false-positive."""
    hits = []
    block_pattern = re.compile(
        r"^```[\s\S]*?^FINDING:[\s\S]*?^```",
        re.MULTILINE,
    )
    seen_lines: set[int] = set()
    for block_match in block_pattern.finditer(content):
        block = block_match.group(0)
        block_start = block_match.start()
        for pat, label in _META_LANGUAGE_PATTERNS:
            for hit in pat.finditer(block):
                line_no = content[: block_start + hit.start()].count("\n") + 1
                if line_no in seen_lines:
                    continue
                seen_lines.add(line_no)
                snippet = hit.group(0)[:80]
                hits.append(
                    (
                        line_no,
                        f"meta-language leak ({label}): {snippet!r}. "
                        f"Findings describe page content, not the auditor's "
                        f"scan effort. Rewrite without internal "
                        f"context-management language.",
                    )
                )
    return hits


def _find_dpr_titles(content: str, viewport_width: int | None) -> list[tuple[int, str]]:
    """Heuristic: on mobile, flag titles whose pixel value looks DPR-scaled.

    An iPhone 14 CSS viewport is 390 wide; DPR is 3. Any title with a
    pixel value greater than roughly 2× the CSS width is almost
    certainly quoting screenshot pixels rather than CSS pixels.
    """
    if not viewport_width:
        return []
    threshold = viewport_width * 2

    hits = []
    title_re = re.compile(r"^TITLE:\s*(.+)$", re.MULTILINE)
    for m in title_re.finditer(content):
        title = m.group(1)
        # Look for bare integer pixel values
        for num_match in re.finditer(r"(\d{3,5})\s*(?:px|pixel)", title, re.IGNORECASE):
            n = int(num_match.group(1))
            if n >= threshold:
                line_no = content[: m.start()].count("\n") + 1
                hits.append(
                    (
                        line_no,
                        f"TITLE references {n}px which is >= {threshold}px "
                        f"(2x CSS viewport width). Likely a DPR-scaled "
                        f"screenshot coordinate; restate in CSS pixels.",
                    )
                )
                break
    return hits


def _extract_cluster(filename: str) -> tuple[str, str] | None:
    """Parse ``cluster-{slug}-{device}.md`` → (slug, device)."""
    m = re.match(r"^cluster-([\w-]+)-(mobile|desktop|laptop)\.md$", filename)
    if not m:
        return None
    return m.group(1), m.group(2)


def _page_netloc_from_meta(engagement_dir: Path) -> str | None:
    meta_path = engagement_dir / "meta.json"
    if not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    page = meta.get("page") or {}
    url = page.get("url") or meta.get("url")
    if not url:
        return None
    try:
        return (urlparse(url).netloc or "").lower().lstrip("www.")
    except ValueError:
        return None


def _viewport_width_for_device(device: str) -> int | None:
    return {"mobile": 390, "laptop": 1440, "desktop": 1920}.get(device)


def validate_file(path: Path, page_netloc: str | None) -> list[str]:
    """Return a list of violation strings for this cluster file."""
    parsed = _extract_cluster(path.name)
    if not parsed:
        return []
    cluster, device = parsed

    content = path.read_text(encoding="utf-8", errors="replace")
    violations: list[str] = []

    fenced = _find_fenced_findings(content)
    pseudo = _find_pseudo_headings(content)

    if not fenced and pseudo:
        violations.append(
            f"FORMAT: no triple-backtick FINDING blocks found, but {len(pseudo)} "
            f"markdown-heading pseudo-findings detected (e.g., line {pseudo[0][0]}: "
            f"{pseudo[0][1]!r}). The assembler parses fenced blocks only — "
            f"rewrite each pseudo-finding in the code-fenced FINDING format "
            f"from workflows/audit.md §FORMAT CONTRACT."
        )
    elif pseudo and fenced:
        # Mixed — both present; flag anyway because the pseudo blocks
        # still won't parse.
        violations.append(
            f"FORMAT: {len(pseudo)} pseudo-finding H3 heading(s) alongside "
            f"{len(fenced)} fenced FINDING block(s). The H3 pseudo-findings "
            f"will be dropped by the assembler. First at line {pseudo[0][0]}: "
            f"{pseudo[0][1]!r}."
        )
    elif not fenced and not pseudo:
        violations.append(
            f"FORMAT: no FINDING blocks at all — neither fenced nor pseudo. "
            f"Cluster file is empty of findings."
        )

    self_cites = _find_self_citations(content, cluster)
    if self_cites:
        violations.append(
            f"SELF-CITATION: {len(self_cites)} finding(s) cite "
            f"↳ {cluster}.md as their source, which is the cluster's own "
            f"reference file. This is the 'filler citation' pattern — "
            f"either cite an external source (reference-file finding with "
            f"sources.md URL, regulation canonical URL, or inline study URL) "
            f"or strip REFERENCE/↳ entirely for pure DOM-fact observations. "
            f"First at line {self_cites[0][0]}."
        )

    ethics_issues = _find_ethics_misroute(content, page_netloc)
    for line_no, msg in ethics_issues:
        violations.append(f"ETHICS URL: line {line_no}: {msg}")

    dpr_issues = _find_dpr_titles(content, _viewport_width_for_device(device))
    for line_no, msg in dpr_issues:
        violations.append(f"DPR UNIT: line {line_no}: {msg}")

    voice_issues = _find_meta_language(content)
    for line_no, msg in voice_issues:
        violations.append(f"VOICE: line {line_no}: {msg}")

    return violations


def main() -> int:
    ap = argparse.ArgumentParser(description="Pre-assembly lint for cluster audit files.")
    ap.add_argument("--engagement", required=True, help="Path to engagement directory.")
    ap.add_argument(
        "--warn-only",
        action="store_true",
        help="Print warnings but exit 0 even if violations found.",
    )
    args = ap.parse_args()

    engagement = Path(args.engagement)
    if not engagement.is_dir():
        print(f"error: engagement directory not found: {engagement}", file=sys.stderr)
        return 2

    page_netloc = _page_netloc_from_meta(engagement)

    cluster_files = sorted(engagement.glob("cluster-*-*.md"))
    if not cluster_files:
        print(f"warning: no cluster-*-*.md files in {engagement}", file=sys.stderr)
        return 0

    total_violations = 0
    files_with_issues = 0

    for path in cluster_files:
        violations = validate_file(path, page_netloc)
        if not violations:
            print(f"  OK    {path.name}")
            continue
        files_with_issues += 1
        total_violations += len(violations)
        print(f"  FAIL  {path.name}")
        for v in violations:
            print(f"        * {v}")

    print()
    if total_violations:
        print(
            f"{files_with_issues} file(s) with {total_violations} violation(s). "
            f"Fix before running assemble-audit.py -- or re-dispatch the "
            f"offending auditor teammate(s) via SendMessage.",
            file=sys.stderr,
        )
        return 0 if args.warn_only else 1

    print(f"All {len(cluster_files)} cluster file(s) passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
