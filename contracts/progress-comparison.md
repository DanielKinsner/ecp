# Progress comparison

Algorithm for comparing current audit findings against a previous engagement's findings on the same URL, producing a delta summary (fixed, regressed, new, unchanged, resolved).

**Why this file exists:** The progress comparison algorithm is reusable across any skill that produces audit.md files and wants to show what changed since the last engagement. Extracting it from the audit skill makes it available to compare and quick-scan skills without loading the full audit orchestration spec.

**Read this file when:** you are the audit lead writing audit.md and want to append a `## Progress Comparison` section, or you are any skill coordinator that compares findings across engagements.

---

## When to run

After writing audit.md but before presenting the checkpoint.

## Algorithm

1. **Determine if a previous engagement exists:**
   a. If `--engagement-id` was provided, look up that engagement's audit.md directly
   b. Otherwise, scan `docs/ecp/*/meta.json` for a matching `url_normalized` (exclude the current engagement and quick-scan engagements)
   c. If multiple matches, use the most recent by date
   d. If no match found, skip this section entirely
   e. **Device-aware matching:** Only compare same-device reports. Desktop `audit.md` compares to previous `audit.md`. Mobile `audit-mobile.md` compares to previous `audit-mobile.md`. If the previous engagement used a different viewport width (e.g., old 1280px vs new 1440px), skip comparison and note: "Previous scan used a different viewport width; comparison skipped."

2. **Read the previous engagement's audit.md.** Parse each finding block, extracting:
   - SECTION slug (the canonical slug)
   - FINDING verdict (PASS, FAIL, PARTIAL, SKIP)

3. **Parse the current audit.md the same way.**

4. **Compare by SECTION slug and classify each:**
   - **FIXED:** was FAIL or PARTIAL in previous, now PASS in current — this is a win, highlight it
   - **REGRESSED:** was PASS in previous, now FAIL or PARTIAL in current
   - **UNCHANGED:** same verdict in both
   - **NEW:** present in current but not in previous
   - **RESOLVED:** present in previous but not in current (section no longer evaluated)

5. **Append a `## Progress Comparison` section to the current engagement's audit.md:**

```markdown
## Progress Comparison

Compared against engagement `{previous-id}` ({date}).

### Now Passing
<!-- List FIXED items prominently — these represent implemented improvements -->
| Section | Previous | Current |
|---------|----------|---------|
| {slug} | FAIL | PASS |

### Regressions
| Section | Previous | Current |
|---------|----------|---------|
| {slug} | PASS | FAIL |

### New Findings
| Section | Current |
|---------|---------|
| {slug} | {verdict} |

Summary: X FIXED, Y REGRESSED, Z UNCHANGED, W NEW, V RESOLVED
```

6. **Use the summary counts when presenting the checkpoint message.** Emphasize FIXED items — these are the user's wins. Present them first: "X issues from your last audit are now passing: [list slugs]." This gives users concrete feedback that their changes worked.
