# Audit assembly

Canonical template for the consolidated `audit.md` file, including the finding format, summary recount, Priority Path citation validation, and the assertion self-check cross-reference.

**Why this file exists:** Prior to this extraction, the audit.md template structure lived inside `skills/audit/SKILL.md` where only the audit lead could reference it. But the Python renderer (`scripts/generate-report.py`), the reviewer, and the planner all consume audit.md — they deserve a canonical contract for its format.

**Read this file when:** you are the audit lead assembling the consolidated audit.md from cluster files, or you are any consumer of audit.md that needs to know its structure.

---

## Critical format requirement

Every FAIL and PARTIAL finding in audit.md **MUST** be wrapped in triple-backtick code fences. The visual report generator (`generate-report.py`) parses findings with a regex that matches code-fenced blocks. If findings are written as plain markdown (e.g., `**FINDING: FAIL**` without code fences), they will NOT appear in the DIAGNOSTIC INSIGHTS panel of the visual report — the report will show annotated screenshots with markers but zero finding cards.

**Correct finding format** (note the triple backticks on their own lines before and after):

    ```
    FINDING: FAIL
    SECTION: primary-cta
    ELEMENT: button.btn-cart
    SOURCE: VISUAL
    OBSERVATION: [observation text]
    RECOMMENDATION: [recommendation text]
    REFERENCE: [reference file and finding number]
    PRIORITY: HIGH
    **Why this matters:** [rationale]
    ↳ [citation] [Tier]
    ```

**Incorrect** (will cause zero findings in visual report):

    **FINDING: FAIL**
    SECTION: primary-cta
    ...

When assembling, copy each finding from the auditor output preserving its code fences. Do NOT reformat findings as plain markdown, bold text, or any other style. The auditors output code-fenced findings per `workflows/audit.md` — preserve that format exactly.

**Note on FINDING verdict:** Use only `FAIL` or `PARTIAL` as the verdict. `CRITICAL` is a PRIORITY value, not a verdict. A critical finding should be `FINDING: FAIL` with `PRIORITY: CRITICAL`.

---

## audit.md template structure

```
# E-Commerce Psychology Audit: {page_title} ({device_label})

**URL:** {url}
**Viewport:** {device} {width}×{height} @ {dpr}x DPR
**Platform:** {platform}
**Date:** {date}
**Engagement:** {engagement_id}
**Clusters audited:** {comma-separated cluster names}

---

## Ethics Gate: {CLEAR | VIOLATIONS FOUND}
{summary line or violation list}

---

## Priority Path

**{X} focused changes that fix {Y} of {Z} findings.** Tackle these first — everything else can wait.

### 1. {Action title} ({SEVERITY})
**Fixes {N} findings across {M} clusters** ({comma-separated cluster names})

{2-3 sentence description.}

**Do this:** {1-2 sentence concrete action.}

**Underlying findings:** {cluster} F-{NN}, {cluster} F-{NN}, ...

---

### 2. {Action title} ({SEVERITY})
{...}

---

{3-5 stories total per the priority_path_synthesis spec}

> **The remaining {R} findings** (smaller wins, edge cases, info-only items) are in the cluster sections below.

---

## Findings

### {cluster_name} cluster
{code-fenced findings ordered by priority: CRITICAL → HIGH → MEDIUM → LOW}

### {next_cluster_name} cluster
{code-fenced findings}

---

## Cross-Cluster Connections
{For each unique SYNTHESIS_HINT slug, list the related findings across clusters with a brief connection note. This is the raw data the Priority Path was built from. Keep both sections — Priority Path is the user-facing action plan, Cross-Cluster Connections is the underlying data for power users.}

Example:
- **order-summary-trust-pricing-overlap**: pricing F-04 (unexpected shipping reveal) + trust-credibility F-07 (missing trust badges near total) — both diagnose problems with the same DOM region. Fix together as one action.

---

## What's Working Well
{deduplicated PASS findings from all auditors, as bullet list}

---

## Summary
| Priority | Count |
|----------|-------|
| CRITICAL | {n} |
| HIGH | {n} |
| MEDIUM | {n} |
| LOW | {n} |
| **Total** | **{n}** |

**Top 5 actions by expected impact:**
1. {action}
```

---

## MANDATORY summary recount step

Before writing the Summary table, the lead MUST re-count findings from the actual code-fenced FINDING blocks just written into the audit.md body — NOT from any in-flight reconciliation arithmetic. The reconciliation logic involves dropping duplicates across multiple cluster files, and the running tally is easy to get wrong (off-by-one or off-by-two errors are typical). Recount procedure:

1. Read back the audit.md body (the Findings sections you just wrote — you can grep your own output buffer or re-read the file from disk).
2. Count occurrences of `^FINDING: ` (each one is one finding card).
3. For each finding card, parse the `PRIORITY:` line to bucket it into CRITICAL / HIGH / MEDIUM / LOW.
4. Use those counts in the Summary table. Do NOT trust intermediate arithmetic from the reconciliation step.

This protects against the "summary table says 26 but the cards add up to 28" class of bug.

---

## MANDATORY Priority Path citation validation step

After writing audit.md, the lead MUST validate every `**Underlying findings:**` reference in the `## Priority Path` section against the actual cluster F-NN numbering in the `## Findings` body. The Priority Path is drafted while findings are still being deduplicated and ordered, so it's easy to cite a finding that gets dropped or renumbered before audit.md ships. This step catches off-by-one citation errors before they reach the visual report.

Validation procedure:

1. **Build the cluster->max-N map.** For each cluster section in `## Findings`, count the code-fenced FINDING blocks. The result is `{cluster: max_finding_index}`. Example: `{trust-credibility: 7, visual-cta: 9, content-seo: 6, performance-ux: 8}`.

2. **For each Priority Path story, parse its `**Underlying findings:**` line** and extract every `{cluster} F-{NN}` reference.

3. **Validate each reference:**
   - Does the cluster exist in the cluster->max-N map? If not -> broken reference, drop it.
   - Is the local index N in range `[1, max_finding_index]`? If not -> broken reference (off-by-one or stale citation from before reconciliation dedup), drop it.

4. **If you find broken references:**
   - Drop the bad reference from the citation list
   - If the story now has zero valid underlying findings, replace its line with `**Underlying findings:** _none — this story was synthesized from thematic patterns and is not anchored to a specific cluster finding_`
   - Log every dropped reference in `audit-trace.log` (or print to lead's output): `Citation validation: dropped {cluster} F-{NN} from Priority Path story #{N} — {reason}`
   - Do NOT silently fix the number (e.g., do NOT change F-07 -> F-06 just because 6 is in range; the lead doesn't know which finding the story was actually trying to cite). Drop the bad reference and surface the issue.

5. **If a story loses >=2 references**, also re-evaluate whether it still belongs in the Priority Path. A story with 1 underlying finding has lost most of its leverage justification. Consider demoting it.

**Why this matters:** The awdmods.com live test (April 7, 2026) showed mobile audit Story #4 citing `performance-ux F-04, F-05, F-06, F-07` — but F-07 doesn't exist (only F-01..F-06 are written after 2 PASS findings were moved to "Working Well"). This was an off-by-one drafting error from referencing the original cluster numbering before the PASS-info findings were stripped during reconciliation. Without this validation step, broken hyperlinks slip through to the visual report and click into nothing.
