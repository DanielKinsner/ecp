"""Build internal reference maintenance dashboards.

These dashboards are for upkeep agents, not normal report generation. They keep
freshness and validation concerns outside the reference files so ordinary audits
do not pay a context cost for maintenance bookkeeping.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from reference_lint import ReferenceIssue, lint_reference_dir


URL_RE = re.compile(r"https?://[^\s)\]>'\"`|]+")
FINDING_RE = re.compile(r"^### Finding\s+\d+:(?!.*\[REMOVED)", re.MULTILINE)
SOURCE_RE = re.compile(r"^- \*\*Sources?\b", re.MULTILINE)

LEGAL_DOMAINS = (
    "ftc.gov",
    "federalregister.gov",
    "ec.europa.eu",
    "eur-lex.europa.eu",
    "cnil.fr",
    "dataprotectionauthority.be",
    "gegevensbeschermingsautoriteit.be",
    "ico.org.uk",
    "gov.uk",
    "leginfo.legislature.ca.gov",
    "law.cornell.edu",
    "edpb.europa.eu",
)
PLATFORM_DOMAINS = (
    "developers.google.com",
    "support.google.com",
    "search.google.com",
    "web.dev",
    "schema.org",
    "openai.com",
    "perplexity.ai",
    "iabeurope.eu",
    "iabtechlab.com",
    "github.com/InteractiveAdvertisingBureau",
)
PRACTITIONER_DOMAINS = (
    "baymard.com",
    "nngroup.com",
    "stripe.com",
    "shopify.com",
    "klaviyo.com",
    "omnisend.com",
    "ahrefs.com",
    "searchenginejournal.com",
    "searchengineland.com",
    "semrush.com",
)
ACADEMIC_DOMAINS = (
    "doi.org",
    "ncbi.nlm.nih.gov",
    "acm.org",
    "springer.com",
    "sciencedirect.com",
    "wiley.com",
    "tandfonline.com",
    "jstor.org",
)

FILENAME_RISK_HINTS = {
    "legal/regulatory": (
        "consent",
        "cookie",
        "ethics",
        "scarcity",
        "urgency",
        "review",
        "price-transparency",
        "ai-media-disclosure",
    ),
    "platform/search/AI": (
        "ai-search",
        "schema",
        "seo",
        "canonical",
        "core-web-vitals",
        "content-freshness",
        "image-seo",
    ),
}

CADENCE_BY_CATEGORY = {
    "legal/regulatory": "30-90 days",
    "platform/search/AI": "90 days",
    "vendor/practitioner": "180 days",
    "academic/stable": "24 months",
    "mixed/unknown": "12 months",
}
CADENCE_PRIORITY = {
    "30-90 days": 0,
    "90 days": 1,
    "180 days": 2,
    "12 months": 3,
    "24 months": 4,
}
CATEGORY_PRIORITY = {
    "legal/regulatory": 0,
    "platform/search/AI": 1,
    "vendor/practitioner": 2,
    "mixed/unknown": 3,
    "academic/stable": 4,
}


@dataclass(frozen=True)
class ReferenceFileStats:
    path: str
    findings: int
    source_lines: int
    urls: int
    categories: tuple[str, ...]
    cadence: str


@dataclass(frozen=True)
class ReferenceInventory:
    reference_dir: Path
    files: tuple[ReferenceFileStats, ...]
    issues: tuple[ReferenceIssue, ...]


def _domain_matches(text: str, domains: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(domain.lower() in lowered for domain in domains)


def _filename_hint(path: Path, category: str) -> bool:
    lowered = path.name.lower()
    return any(hint in lowered for hint in FILENAME_RISK_HINTS.get(category, ()))


def _categories(path: Path, text: str) -> tuple[str, ...]:
    categories: list[str] = []
    if _domain_matches(text, LEGAL_DOMAINS) or _filename_hint(path, "legal/regulatory"):
        categories.append("legal/regulatory")
    if _domain_matches(text, PLATFORM_DOMAINS) or _filename_hint(path, "platform/search/AI"):
        categories.append("platform/search/AI")
    if _domain_matches(text, PRACTITIONER_DOMAINS):
        categories.append("vendor/practitioner")
    if _domain_matches(text, ACADEMIC_DOMAINS):
        categories.append("academic/stable")
    return tuple(categories or ("mixed/unknown",))


def _cadence(categories: tuple[str, ...]) -> str:
    ranked = sorted(categories, key=lambda category: CATEGORY_PRIORITY[category])
    return CADENCE_BY_CATEGORY[ranked[0]]


def collect_reference_inventory(reference_dir: Path) -> ReferenceInventory:
    files: list[ReferenceFileStats] = []
    for path in sorted(reference_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        categories = _categories(path, text)
        files.append(
            ReferenceFileStats(
                path=path.name,
                findings=len(FINDING_RE.findall(text)),
                source_lines=len(SOURCE_RE.findall(text)),
                urls=len(URL_RE.findall(text)),
                categories=categories,
                cadence=_cadence(categories),
            )
        )
    return ReferenceInventory(
        reference_dir=reference_dir,
        files=tuple(files),
        issues=tuple(lint_reference_dir(reference_dir)),
    )


def _table(headers: tuple[str, ...], rows: list[tuple[object, ...]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def _issue_counts_by_file(issues: tuple[ReferenceIssue, ...]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for issue in issues:
        counts[Path(issue.path).name] += 1
    return counts


def render_validation_markdown(inventory: ReferenceInventory, as_of: str | None = None) -> str:
    as_of = as_of or date.today().isoformat()
    issue_counts = Counter(issue.code for issue in inventory.issues)
    by_file = _issue_counts_by_file(inventory.issues)
    non_audit = [issue for issue in inventory.issues if issue.code != "missing-audit-note"]

    summary_rows = [
        ("Reference files scanned", len(inventory.files)),
        ("Finding blocks scanned", sum(file.findings for file in inventory.files)),
        ("Validator issues", len(inventory.issues)),
        ("Non-audit-note issues", len(non_audit)),
    ]
    issue_rows = [(code, count) for code, count in issue_counts.most_common()] or [("none", 0)]
    backlog_rows = [
        (path, count)
        for path, count in by_file.most_common(20)
        if count > 0
    ] or [("none", 0)]

    if non_audit:
        blocker_rows = [
            (Path(issue.path).name, issue.line, issue.code, issue.message)
            for issue in non_audit[:30]
        ]
        blocker_section = _table(("File", "Line", "Issue", "Message"), blocker_rows)
    else:
        blocker_section = "No structural/source/DOI/tier blockers are currently open."

    return "\n".join(
        [
            "# Reference Validation Maintenance",
            "",
            "Internal maintenance file. Do not load this during normal customer-facing ECP audits unless the task is reference upkeep.",
            "",
            f"- Generated: {as_of}",
            "- Refresh command: `python3 scripts/build-reference-maintenance.py`",
            "- Source of truth: `references/*.md` plus `scripts/reference_lint.py`",
            "",
            "## Summary",
            "",
            _table(("Metric", "Value"), summary_rows),
            "",
            "## Validator Issue Mix",
            "",
            _table(("Issue", "Count"), issue_rows),
            "",
            "## Non-Audit Blockers",
            "",
            blocker_section,
            "",
            "## Largest Open Backlogs",
            "",
            _table(("File", "Open issues"), backlog_rows),
            "",
            "## Agent Use",
            "",
            "- Use this file to choose maintenance batches.",
            "- Keep normal audit agents on the lean `references/*.md` files only.",
            "- Prefer small commits grouped by issue type: DOI/source/tier/parser/audit-note.",
            "- After edits, refresh this file with the command above.",
            "",
        ]
    )


def render_freshness_markdown(inventory: ReferenceInventory, as_of: str | None = None) -> str:
    as_of = as_of or date.today().isoformat()
    category_counts: defaultdict[str, int] = defaultdict(int)
    for file in inventory.files:
        for category in file.categories:
            category_counts[category] += 1

    sorted_files = sorted(
        inventory.files,
        key=lambda file: (
            CADENCE_PRIORITY[file.cadence],
            -file.urls,
            file.path,
        ),
    )
    fast_changing_rows = [
        (
            file.path,
            file.cadence,
            ", ".join(file.categories),
            file.findings,
            file.urls,
        )
        for file in sorted_files[:25]
    ]
    full_index_rows = [
        (
            file.path,
            file.cadence,
            ", ".join(file.categories),
            file.findings,
            file.urls,
        )
        for file in sorted_files
    ]

    return "\n".join(
        [
            "# Reference Freshness Maintenance",
            "",
            "Internal maintenance file. This is a recheck queue for source freshness, not public report copy.",
            "",
            f"- Generated: {as_of}",
            "- Refresh command: `python3 scripts/build-reference-maintenance.py`",
            "- Public reports should expose only compact evidence-confidence labels, not this maintenance ledger.",
            "",
            "## Cadence Rules",
            "",
            _table(
                ("Source type", "Suggested recheck cadence"),
                [
                    ("legal/regulatory", "30-90 days"),
                    ("platform/search/AI", "90 days"),
                    ("vendor/practitioner", "180 days"),
                    ("mixed/unknown", "12 months"),
                    ("academic/stable", "24 months"),
                ],
            ),
            "",
            "## Source-Type Mix",
            "",
            _table(
                ("Source type", "Files"),
                sorted(category_counts.items(), key=lambda row: CATEGORY_PRIORITY[row[0]]),
            ),
            "",
            "## Fastest-Moving Recheck Queue",
            "",
            _table(
                ("File", "Cadence", "Risk signals", "Findings", "URLs"),
                fast_changing_rows,
            ),
            "",
            "## Full File Index",
            "",
            _table(
                ("File", "Cadence", "Risk signals", "Findings", "URLs"),
                full_index_rows,
            ),
            "",
            "## Agent Use",
            "",
            "- Start with 30-90 day and 90 day files when doing freshness upkeep.",
            "- Prefer official replacements for legal, standards, and platform documentation.",
            "- Treat practitioner benchmark numbers as volatile unless the source publishes methodology and date.",
            "- Do not add long audit prose to `references/*.md`; keep detailed upkeep here or in per-run audit artifacts.",
            "",
        ]
    )


def write_maintenance_files(reference_dir: Path, output_dir: Path, as_of: str | None = None) -> None:
    inventory = collect_reference_inventory(reference_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "reference-validation.md").write_text(
        render_validation_markdown(inventory, as_of=as_of),
        encoding="utf-8",
    )
    (output_dir / "reference-freshness.md").write_text(
        render_freshness_markdown(inventory, as_of=as_of),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build internal reference maintenance dashboards")
    parser.add_argument("--references", default="references", help="Reference directory")
    parser.add_argument("--output", default="reference-maintenance", help="Dashboard output directory")
    parser.add_argument("--as-of", default=None, help="Generation date override, YYYY-MM-DD")
    args = parser.parse_args(argv)

    write_maintenance_files(Path(args.references), Path(args.output), as_of=args.as_of)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
