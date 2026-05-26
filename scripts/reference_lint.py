"""Reference library hygiene checks.

The ECP reference files are part of the product surface: auditors cite them,
and reports inherit their evidence quality. This module keeps the mechanical
contract explicit so citation drift is visible before release.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


REQUIRED_FIELDS = (
    "Source",
    "Methodology",
    "Key Finding",
    "E-Commerce Application",
    "Replication Status",
    "Boundary Conditions",
    "Evidence Tier",
    "Audit Note",
)

VALID_TIERS = {"Gold", "Silver", "Bronze"}
URL_RE = re.compile(r"https?://[^\s)\]>'\"`|]+")
DOI_RE = re.compile(r"https://doi\.org/[^\s)\]>,;]+")
FINDING_RE = re.compile(r"^### Finding\s+\d+:", re.MULTILINE)


@dataclass(frozen=True)
class ReferenceIssue:
    path: str
    line: int
    code: str
    message: str


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _finding_blocks(text: str) -> Iterable[tuple[int, str]]:
    matches = list(FINDING_RE.finditer(text))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        yield match.start(), text[match.start():end]


def _field_line(block: str, field: str) -> tuple[int, str] | None:
    escaped_field = re.escape(field)
    pattern = re.compile(
        rf"^- \*\*{escaped_field}(?:\s*\([^*]*\))?\*\*(?:\s*\([^)]*\)|\s*\[[^\]]*\])*:\s*(.*)$",
        re.MULTILINE,
    )
    match = pattern.search(block)
    if not match:
        return None
    return block.count("\n", 0, match.start()) + 1, match.group(1).strip()


def _is_removed_finding(block: str) -> bool:
    first_line = block.splitlines()[0].lower()
    return "[removed" in first_line


def lint_reference_file(path: Path) -> list[ReferenceIssue]:
    text = path.read_text(encoding="utf-8")
    issues: list[ReferenceIssue] = []

    for start, block in _finding_blocks(text):
        if _is_removed_finding(block):
            continue

        base_line = _line_number(text, start)
        for field in REQUIRED_FIELDS:
            found = _field_line(block, field)
            if found is None:
                issues.append(
                    ReferenceIssue(
                        path=str(path),
                        line=base_line,
                        code=f"missing-{field.lower().replace(' ', '-')}",
                        message=f"Finding is missing required field: {field}",
                    )
                )

        source = _field_line(block, "Source")
        if source is not None:
            rel_line, value = source
            if not URL_RE.search(value):
                issues.append(
                    ReferenceIssue(
                        path=str(path),
                        line=base_line + rel_line - 1,
                        code="source-without-url",
                        message="Source field must include a direct URL on the Source line",
                    )
                )

        tier = _field_line(block, "Evidence Tier")
        if tier is not None:
            rel_line, value = tier
            tier_name = value.split()[0].strip(".,;:*") if value else ""
            if tier_name not in VALID_TIERS:
                issues.append(
                    ReferenceIssue(
                        path=str(path),
                        line=base_line + rel_line - 1,
                        code="invalid-evidence-tier",
                        message="Evidence Tier must start with Gold, Silver, or Bronze",
                    )
                )

    for match in DOI_RE.finditer(text):
        before = text[match.start() - 1] if match.start() > 0 else ""
        if before != "<":
            issues.append(
                ReferenceIssue(
                    path=str(path),
                    line=_line_number(text, match.start()),
                    code="doi-not-angle-wrapped",
                    message="DOI URLs must be wrapped in angle brackets",
                )
            )

    return issues


def lint_reference_dir(reference_dir: Path) -> list[ReferenceIssue]:
    issues: list[ReferenceIssue] = []
    for path in sorted(reference_dir.glob("*.md")):
        issues.extend(lint_reference_file(path))
    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ECP reference-library hygiene")
    parser.add_argument("path", nargs="?", default="references", help="Reference file or directory")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    target = Path(args.path)
    if target.is_dir():
        issues = lint_reference_dir(target)
    else:
        issues = lint_reference_file(target)

    if args.json:
        print(json.dumps([asdict(issue) for issue in issues], indent=2))
    else:
        for issue in issues:
            print(f"{issue.path}:{issue.line}: {issue.code}: {issue.message}")
        print(f"{len(issues)} issue(s)")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
