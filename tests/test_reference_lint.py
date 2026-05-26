"""Tests for reference-library hygiene linting."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from reference_lint import lint_reference_file  # noqa: E402


class ReferenceLintTests(unittest.TestCase):
    def _lint_text(self, text: str):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.md"
            path.write_text(text, encoding="utf-8")
            return lint_reference_file(path)

    def test_accepts_complete_finding(self):
        issues = self._lint_text(
            """# Sample

### Finding 1: Strong claim
- **Source**: Research paper. https://example.com/paper
- **Methodology**: Controlled test.
- **Key Finding**: The thing happened.
- **E-Commerce Application**: Use the thing carefully.
- **Replication Status**: Replicated.
- **Boundary Conditions**: Works in this condition.
- **Evidence Tier**: Gold
- **Audit Note**: Tier is Gold because the source is primary and replicated.
"""
        )

        self.assertEqual(issues, [])

    def test_flags_missing_audit_note_and_source_url(self):
        issues = self._lint_text(
            """# Sample

### Finding 1: Weak claim
- **Source**: Research paper without URL.
- **Methodology**: Controlled test.
- **Key Finding**: The thing happened.
- **E-Commerce Application**: Use the thing carefully.
- **Replication Status**: Replicated.
- **Boundary Conditions**: Works in this condition.
- **Evidence Tier**: Silver
"""
        )

        codes = {issue.code for issue in issues}
        self.assertIn("missing-audit-note", codes)
        self.assertIn("source-without-url", codes)

    def test_flags_unwrapped_doi(self):
        issues = self._lint_text(
            """# Sample

### Finding 1: DOI claim
- **Source**: Research paper. https://doi.org/10.1000/example
- **Methodology**: Controlled test.
- **Key Finding**: The thing happened.
- **E-Commerce Application**: Use the thing carefully.
- **Replication Status**: Replicated.
- **Boundary Conditions**: Works in this condition.
- **Evidence Tier**: Gold
- **Audit Note**: Tier is Gold because the source is primary and replicated.
"""
        )

        self.assertIn("doi-not-angle-wrapped", {issue.code for issue in issues})

    def test_accepts_angle_wrapped_legacy_sici_doi(self):
        issues = self._lint_text(
            """# Sample

### Finding 1: Legacy DOI claim
- **Source**: Research paper. <https://doi.org/10.1002/(SICI)1520-6793(200003)17:3<257::AID-MAR4>3.0.CO;2-P>
- **Methodology**: Controlled test.
- **Key Finding**: The thing happened.
- **E-Commerce Application**: Use the thing carefully.
- **Replication Status**: Replicated.
- **Boundary Conditions**: Works in this condition.
- **Evidence Tier**: Gold
- **Audit Note**: Tier is Gold because the source is primary and replicated.
"""
        )

        self.assertNotIn("doi-not-angle-wrapped", {issue.code for issue in issues})

    def test_accepts_qualified_key_finding_labels(self):
        issues = self._lint_text(
            """# Sample

### Finding 1: Current public page
- **Source**: Research page. https://example.com/page
- **Methodology**: Public documentation review.
- **Key Finding** (current wave): The thing happened.
- **E-Commerce Application**: Use the thing carefully.
- **Replication Status**: Replicated.
- **Boundary Conditions**: Works in this condition.
- **Evidence Tier**: Silver
- **Audit Note**: Tier is Silver because the source is current but observational.

### Finding 2: Historical claim
- **Source**: Research page. https://example.com/archive
- **Methodology**: Historical documentation review.
- **Key Finding (historical)**: The earlier thing happened.
- **E-Commerce Application**: Use the thing carefully.
- **Replication Status**: Not independently replicated.
- **Boundary Conditions**: Historical only.
- **Evidence Tier**: Bronze
- **Audit Note**: Tier is Bronze because the source is retained for context only.
"""
        )

        self.assertNotIn("missing-key-finding", {issue.code for issue in issues})

    def test_skips_removed_finding_blocks(self):
        issues = self._lint_text(
            """# Sample

### Finding 12: [REMOVED — duplicate topic]
> Prior version duplicated a neighboring finding, so this slot is intentionally empty.
"""
        )

        self.assertEqual(issues, [])

    def test_accepts_audit_note_between_field_label_and_value(self):
        issues = self._lint_text(
            """# Sample

### Finding 1: Audited claim
- **Source**: Research page. https://example.com/page
- **Methodology**: Public documentation review.
- **Key Finding** [**AUDIT 2026-04-22: quantitative claim removed**]: The thing happened.
- **E-Commerce Application**: Use the thing carefully.
- **Replication Status**: Replicated.
- **Boundary Conditions**: Works in this condition.
- **Evidence Tier**: Silver
- **Audit Note**: Tier is Silver because the source is current but observational.
"""
        )

        self.assertNotIn("missing-key-finding", {issue.code for issue in issues})


if __name__ == "__main__":
    unittest.main()
