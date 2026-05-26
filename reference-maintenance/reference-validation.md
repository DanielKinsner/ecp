# Reference Validation Maintenance

Internal maintenance file. Do not load this during normal customer-facing ECP audits unless the task is reference upkeep.

- Generated: 2026-04-24
- Refresh command: `python3 scripts/build-reference-maintenance.py`
- Source of truth: `references/*.md` plus `scripts/reference_lint.py`

## Summary

| Metric | Value |
| --- | --- |
| Reference files scanned | 72 |
| Finding blocks scanned | 916 |
| Validator issues | 808 |
| Non-audit-note issues | 0 |

## Validator Issue Mix

| Issue | Count |
| --- | --- |
| missing-audit-note | 808 |

## Non-Audit Blockers

No structural/source/DOI/tier blockers are currently open.

## Largest Open Backlogs

| File | Open issues |
| --- | --- |
| pricing-psychology.md | 33 |
| eye-tracking-and-scan-patterns.md | 30 |
| trust-and-credibility.md | 27 |
| color-psychology.md | 24 |
| cta-design-and-placement.md | 24 |
| mobile-conversion.md | 24 |
| checkout-optimization.md | 23 |
| page-performance-psychology.md | 22 |
| cognitive-load-management.md | 21 |
| search-and-filter-ux.md | 21 |
| abandoned-cart-psychology.md | 19 |
| headline-copywriting.md | 16 |
| post-purchase-psychology.md | 16 |
| video-integration.md | 16 |
| pagination-patterns.md | 15 |
| product-cards.md | 15 |
| benefit-first-descriptions.md | 13 |
| core-web-vitals.md | 13 |
| hero-section-psychology.md | 13 |
| order-confirmation.md | 13 |

## Agent Use

- Use this file to choose maintenance batches.
- Keep normal audit agents on the lean `references/*.md` files only.
- Prefer small commits grouped by issue type: DOI/source/tier/parser/audit-note.
- After edits, refresh this file with the command above.
