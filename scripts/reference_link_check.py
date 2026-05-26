"""Live-link checking for ECP reference sources."""

from __future__ import annotations

import argparse
import json
import re
import socket
import ssl
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse, urlsplit, urlunsplit
from urllib.request import Request, urlopen


URL_RE = re.compile(r"https?://[^\s<>'\"`|]+")
ANGLE_URL_RE = re.compile(r"<(https?://[^>\s]+)>")
SICI_DOI_RE = re.compile(r"https://doi\.org/10\.1002/\(SICI\)[^\s]+")
TRAILING_PUNCTUATION = ".,;:>`"
PLACEHOLDER_HOSTS = {
    "example.com",
    "www.example.com",
    "yourstore.com",
    "www.yourstore.com",
    "localhost",
    "127.0.0.1",
}
GET_FALLBACK_HOSTS = {
    "support.google.com",
}


@dataclass(frozen=True)
class UrlEntry:
    url: str
    files: tuple[str, ...]


@dataclass(frozen=True)
class LinkCheckResult:
    url: str
    files: tuple[str, ...]
    status: str
    status_code: int | None
    final_url: str | None
    error: str | None
    elapsed_ms: int


def normalize_url(url: str) -> str:
    url = url.strip()
    while url.startswith("<"):
        url = url[1:]
    while url and url[-1] in TRAILING_PUNCTUATION:
        url = url[:-1]
    while url.endswith(")") and url.count("(") < url.count(")"):
        url = url[:-1]
    while url.endswith("]") and url.count("[") < url.count("]"):
        url = url[:-1]
    return url


def _urls_in_text(text: str) -> Iterable[str]:
    sici_dois = {normalize_url(match.group(0)) for match in SICI_DOI_RE.finditer(text)}
    yield from sici_dois
    for match in ANGLE_URL_RE.finditer(text):
        url = normalize_url(match.group(1))
        if not any(url in sici_doi for sici_doi in sici_dois):
            yield url
    for match in URL_RE.finditer(text):
        url = normalize_url(match.group(0))
        if not any(url in sici_doi for sici_doi in sici_dois):
            yield url


def extract_reference_urls(reference_dir: Path) -> list[UrlEntry]:
    files_by_url: defaultdict[str, set[str]] = defaultdict(set)
    for path in sorted(reference_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for url in _urls_in_text(text):
            parsed = urlparse(url)
            if url and parsed.scheme and parsed.netloc:
                files_by_url[url].add(path.name)

    return [
        UrlEntry(url=url, files=tuple(sorted(files)))
        for url, files in sorted(files_by_url.items())
    ]


def _is_placeholder(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return host.lower() in PLACEHOLDER_HOSTS or "[" in url or "]" in url


def _status_from_code(code: int) -> str:
    if 200 <= code < 400:
        return "live"
    if code in {401, 403, 405, 429}:
        return "blocked-or-rate-limited"
    if code in {404, 410}:
        return "dead"
    if 500 <= code < 600:
        return "server-error"
    return "review"


def should_retry_get_after_head_error(url: str, status_code: int) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return status_code in {404, 410} and host in GET_FALLBACK_HOSTS


def _request_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            quote(parts.path, safe="/:%"),
            quote(parts.query, safe="=&?:/%"),
            quote(parts.fragment, safe=""),
        )
    )


def _request(url: str, method: str, timeout: float):
    request = Request(
        _request_url(url),
        method=method,
        headers={
            "User-Agent": "Mozilla/5.0 ECP reference link checker",
            "Accept": "text/html,application/xhtml+xml,application/pdf,*/*",
        },
    )
    return urlopen(request, timeout=timeout, context=ssl.create_default_context())


def check_url(entry: UrlEntry, timeout: float = 10.0) -> LinkCheckResult:
    start = time.monotonic()
    if _is_placeholder(entry.url):
        return LinkCheckResult(
            url=entry.url,
            files=entry.files,
            status="placeholder",
            status_code=None,
            final_url=None,
            error=None,
            elapsed_ms=0,
        )

    try:
        try:
            response = _request(entry.url, "HEAD", timeout)
        except HTTPError as exc:
            if exc.code == 405 or should_retry_get_after_head_error(entry.url, exc.code):
                response = _request(entry.url, "GET", timeout)
            else:
                raise
        with response:
            code = response.getcode()
            final_url = response.geturl()
        status = _status_from_code(code)
        error = None
    except HTTPError as exc:
        code = exc.code
        final_url = exc.geturl()
        status = _status_from_code(exc.code)
        error = str(exc.reason)
    except (URLError, TimeoutError, socket.timeout) as exc:
        code = None
        final_url = None
        status = "error"
        error = str(getattr(exc, "reason", exc))
    except Exception as exc:
        code = None
        final_url = None
        status = "error"
        error = str(exc)

    return LinkCheckResult(
        url=entry.url,
        files=entry.files,
        status=status,
        status_code=code,
        final_url=final_url,
        error=error,
        elapsed_ms=int((time.monotonic() - start) * 1000),
    )


def check_reference_links(
    reference_dir: Path,
    *,
    timeout: float = 10.0,
    workers: int = 16,
    retry_timeout: float | None = None,
    retry_workers: int = 6,
) -> list[LinkCheckResult]:
    entries = extract_reference_urls(reference_dir)
    results: list[LinkCheckResult] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(check_url, entry, timeout) for entry in entries]
        for future in as_completed(futures):
            results.append(future.result())

    if retry_timeout and retry_timeout > timeout:
        transient = [
            UrlEntry(url=result.url, files=result.files)
            for result in results
            if result.status in {"error", "server-error"}
        ]
        if transient:
            retried: dict[str, LinkCheckResult] = {}
            with ThreadPoolExecutor(max_workers=retry_workers) as pool:
                futures = [pool.submit(check_url, entry, retry_timeout) for entry in transient]
                for future in as_completed(futures):
                    result = future.result()
                    retried[result.url] = result
            results = [retried.get(result.url, result) for result in results]
    return sorted(results, key=lambda result: result.url)


def _table(headers: tuple[str, ...], rows: list[tuple[object, ...]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |")
    return "\n".join(lines)


def render_link_report(results: list[LinkCheckResult], as_of: str | None = None) -> str:
    as_of = as_of or date.today().isoformat()
    counts = Counter(result.status for result in results)
    action_statuses = {"dead", "server-error", "error", "review"}
    action_items = [result for result in results if result.status in action_statuses]
    blocked = [result for result in results if result.status == "blocked-or-rate-limited"]

    summary_rows = [
        ("Unique URLs checked", len(results)),
        ("Action-required URLs", len(action_items)),
        ("Blocked/rate-limited URLs", len(blocked)),
        ("Placeholder/example URLs", counts.get("placeholder", 0)),
    ]
    status_rows = [(status, count) for status, count in counts.most_common()]
    action_rows = [
        (
            result.status,
            result.status_code or "",
            ", ".join(result.files[:3]) + (" ..." if len(result.files) > 3 else ""),
            result.url,
        )
        for result in action_items[:120]
    ] or [("none", "", "", "")]

    return "\n".join(
        [
            "# Reference Live-Link Check",
            "",
            "Internal maintenance file. This is a live URL health pass, not a claim-content audit.",
            "",
            f"- Generated: {as_of}",
            "- Refresh command: `python3 scripts/check-reference-links.py`",
            "- Error/server-error URLs receive a slower retry before this report is written.",
            "- Treat 401/403/405/429 as reachable-but-blocked unless manual review shows otherwise.",
            "",
            "## Summary",
            "",
            _table(("Metric", "Value"), summary_rows),
            "",
            "## Status Mix",
            "",
            _table(("Status", "Count"), status_rows),
            "",
            "## Action Queue",
            "",
            _table(("Status", "HTTP", "Files", "URL"), action_rows),
            "",
            "## What This Does Not Prove",
            "",
            "- It does not prove the source still supports the claim.",
            "- It does not prove statistics are copied correctly.",
            "- It does not prove legal or platform guidance is current.",
            "- Use this report to choose manual source-verification batches.",
            "",
        ]
    )


def write_link_check(
    reference_dir: Path,
    output_dir: Path,
    *,
    as_of: str | None = None,
    timeout: float = 10.0,
    workers: int = 16,
    retry_timeout: float | None = 35.0,
    retry_workers: int = 6,
) -> list[LinkCheckResult]:
    results = check_reference_links(
        reference_dir,
        timeout=timeout,
        workers=workers,
        retry_timeout=retry_timeout,
        retry_workers=retry_workers,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "reference-live-links.json").write_text(
        json.dumps([asdict(result) for result in results], indent=2),
        encoding="utf-8",
    )
    (output_dir / "reference-live-links.md").write_text(
        render_link_report(results, as_of=as_of),
        encoding="utf-8",
    )
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check live URL health for ECP references")
    parser.add_argument("--references", default="references", help="Reference directory")
    parser.add_argument("--output", default="reference-maintenance", help="Report output directory")
    parser.add_argument("--as-of", default=None, help="Generation date override, YYYY-MM-DD")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds")
    parser.add_argument("--workers", type=int, default=16, help="Concurrent request workers")
    parser.add_argument(
        "--retry-timeout",
        type=float,
        default=35.0,
        help="Slower retry timeout for error/server-error URLs; set 0 to disable",
    )
    parser.add_argument("--retry-workers", type=int, default=6, help="Concurrent retry workers")
    args = parser.parse_args(argv)

    results = write_link_check(
        Path(args.references),
        Path(args.output),
        as_of=args.as_of,
        timeout=args.timeout,
        workers=args.workers,
        retry_timeout=args.retry_timeout or None,
        retry_workers=args.retry_workers,
    )
    counts = Counter(result.status for result in results)
    for status, count in counts.most_common():
        print(f"{status}: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
