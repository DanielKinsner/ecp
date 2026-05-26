"""Tests for reference live-link inventory helpers."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from reference_link_check import (  # noqa: E402
    extract_reference_urls,
    normalize_url,
    should_retry_get_after_head_error,
)


class ReferenceLinkCheckTests(unittest.TestCase):
    def test_normalizes_trailing_markdown_punctuation(self):
        self.assertEqual(
            normalize_url("https://example.com/source)."),
            "https://example.com/source",
        )
        self.assertEqual(
            normalize_url("https://doi.org/10.1002/(SICI)1520-6793(200003)17:3<257::AID-MAR4>3.0.CO;2-P>`"),
            "https://doi.org/10.1002/(SICI)1520-6793(200003)17:3<257::AID-MAR4>3.0.CO;2-P",
        )

    def test_extracts_unique_reference_urls_with_file_mentions(self):
        with tempfile.TemporaryDirectory() as tmp:
            reference_dir = Path(tmp) / "references"
            reference_dir.mkdir()
            (reference_dir / "a.md").write_text(
                "Source: https://example.com/a. DOI: <https://doi.org/10.1000/example>",
                encoding="utf-8",
            )
            (reference_dir / "b.md").write_text(
                "Source: https://example.com/a; and https://example.com/b",
                encoding="utf-8",
            )

            entries = extract_reference_urls(reference_dir)

        by_url = {entry.url: entry for entry in entries}
        self.assertEqual(sorted(by_url), [
            "https://doi.org/10.1000/example",
            "https://example.com/a",
            "https://example.com/b",
        ])
        self.assertEqual(by_url["https://example.com/a"].files, ("a.md", "b.md"))

    def test_ignores_hostless_url_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            reference_dir = Path(tmp) / "references"
            reference_dir.mkdir()
            (reference_dir / "a.md").write_text("Source URL: https://", encoding="utf-8")

            entries = extract_reference_urls(reference_dir)

        self.assertEqual(entries, [])

    def test_extracts_legacy_sici_doi_as_one_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            reference_dir = Path(tmp) / "references"
            reference_dir.mkdir()
            (reference_dir / "a.md").write_text(
                "Source: <https://doi.org/10.1002/(SICI)1520-6793(200003)17:3<257::AID-MAR4>3.0.CO;2-P>",
                encoding="utf-8",
            )

            entries = extract_reference_urls(reference_dir)

        self.assertEqual(
            [entry.url for entry in entries],
            ["https://doi.org/10.1002/(SICI)1520-6793(200003)17:3<257::AID-MAR4>3.0.CO;2-P"],
        )

    def test_retries_google_support_head_errors_with_get(self):
        self.assertTrue(
            should_retry_get_after_head_error(
                "https://support.google.com/merchants/answer/6324350?hl=en",
                404,
            )
        )
        self.assertFalse(
            should_retry_get_after_head_error(
                "https://example.com/missing",
                404,
            )
        )


if __name__ == "__main__":
    unittest.main()
