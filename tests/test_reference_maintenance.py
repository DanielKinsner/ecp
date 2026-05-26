"""Tests for reference maintenance dashboard generation."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from reference_maintenance import (  # noqa: E402
    collect_reference_inventory,
    render_freshness_markdown,
    render_validation_markdown,
)


class ReferenceMaintenanceTests(unittest.TestCase):
    def _reference_dir(self, files: dict[str, str]) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        reference_dir = root / "references"
        reference_dir.mkdir()
        for name, text in files.items():
            (reference_dir / name).write_text(text, encoding="utf-8")
        return reference_dir

    def test_validation_markdown_summarizes_current_lint_issues(self):
        reference_dir = self._reference_dir(
            {
                "cookie-consent.md": """# Cookie Consent

### Finding 1: Consent rule
- **Source**: FTC rule. https://www.ftc.gov/example
- **Methodology**: Regulatory review.
- **Key Finding**: Consent must be valid.
- **E-Commerce Application**: Audit consent flows.
- **Replication Status**: Primary source.
- **Boundary Conditions**: US enforcement only.
- **Evidence Tier**: Gold
""",
            }
        )

        inventory = collect_reference_inventory(reference_dir)
        markdown = render_validation_markdown(inventory, as_of="2026-04-24")

        self.assertIn("missing-audit-note", markdown)
        self.assertIn("Internal maintenance file", markdown)
        self.assertIn("cookie-consent.md", markdown)

    def test_freshness_markdown_marks_legal_sources_as_fast_changing(self):
        reference_dir = self._reference_dir(
            {
                "cookie-consent.md": """# Cookie Consent

### Finding 1: Consent rule
- **Source**: FTC rule. https://www.ftc.gov/example
- **Methodology**: Regulatory review.
- **Key Finding**: Consent must be valid.
- **E-Commerce Application**: Audit consent flows.
- **Replication Status**: Primary source.
- **Boundary Conditions**: US enforcement only.
- **Evidence Tier**: Gold
- **Audit Note**: Tier is Gold because this is primary regulatory guidance.
""",
                "pricing.md": """# Pricing

### Finding 1: Price study
- **Source**: Academic paper. <https://doi.org/10.1000/example>
- **Methodology**: Controlled experiment.
- **Key Finding**: Price framing changes behavior.
- **E-Commerce Application**: Test price framing.
- **Replication Status**: Replicated.
- **Boundary Conditions**: Consumer retail.
- **Evidence Tier**: Gold
- **Audit Note**: Tier is Gold because this is replicated peer-reviewed evidence.
""",
            }
        )

        inventory = collect_reference_inventory(reference_dir)
        markdown = render_freshness_markdown(inventory, as_of="2026-04-24")

        self.assertIn("cookie-consent.md", markdown)
        self.assertIn("30-90 days", markdown)
        self.assertIn("legal/regulatory", markdown)
        self.assertIn("pricing.md", markdown)


if __name__ == "__main__":
    unittest.main()
