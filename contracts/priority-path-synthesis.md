<!-- RESEARCH_DATE: 2026-04-14 -->
# Priority Path synthesis

Canonical rules for the lead's Priority Path synthesis step — the one the audit lead runs after finding reconciliation and before writing the final `audit.md` summary.

## v1.0 orchestration contract

**Before:** the lead manually wrote action stories into `audit.md` by reading `priority-path-candidates-{device}.json`. When the lead forgot, `audit.md` shipped with a literal `<!-- Lead: ... -->` HTML comment and the report's Priority Path card fell back to empty-state (Codex audit C1).

**v1.0:** the synthesis step is an explicit subagent dispatch with deterministic Python validation.

1. `scripts/assemble-audit.py` runs reconciliation → dedup → `pipeline.assign_display_indices` → `score_groups` → `write_audit_md` (with `priority_path_stories=None`, which renders a clear pointer to Step 2).
2. The lead dispatches the synthesizer subagent per `${CLAUDE_PLUGIN_ROOT}/contracts/synthesizer-subagent.md`, inlining the finalized `valid_refs` allowlist, the scoring candidates, and a compact findings digest. The subagent returns a fenced JSON code block.
3. The lead writes the subagent response text to a file (e.g. `priority-path-synthesis-{device}.txt` in the engagement directory) and re-runs `assemble-audit.py --priority-path PATH`.
4. `assemble-audit.py` parses + validates the response with `scripts/assembly/synthesizer_parser.py`. Validation failures (no fenced block, malformed JSON, hallucinated F-N, story count out of range, etc.) render a visible ERROR block in `audit.md` instead of silent placeholder. The operator sees the failure.
5. On validation pass, stories are passed to the writer and rendered as real `### N. Title (SEVERITY)` blocks with action paragraphs and Underlying findings F-N references. All F-Ns are guaranteed to resolve because the allowlist was built from `FinalizedFindings.cluster_finding_map`.

**F-N references use post-dedup display order.** `assign_display_indices` tags every finding with `display_index` before scoring runs; `scoring._finding_ref` emits refs in the form `{cluster} F-{display_index:02d}`; the writer renders findings in the same order the display indices were assigned. Before v1.0, scoring emitted refs based on pre-dedup `local_index` while the writer re-sorted by priority — links pointed at the wrong cards (C2). The single-source ordering guarantee removes the drift.

**Retry protocol.** If validation fails, the lead may dispatch the synthesizer subagent ONE more time with a correction turn including the validation error message. If the retry also fails, the lead proceeds without `--priority-path` and the writer renders the ERROR block. No third attempt — elaborate retry loops defend a failure mode we have not observed, and graceful degradation is sufficient.



**Why this file exists:** The Priority Path is the headline UX feature of the v5.0 visual report — it collapses 20-30 raw findings into 3-5 concrete "focused changes" the user can actually act on. The synthesis rules are substantial (scoring formula, action story format, voice rules, header/footer templates) and prior to Round 12 they lived inline in `skills/audit/SKILL.md` where they interrupted the phase orchestration flow. This file extracts them so the audit lead can load the synthesis rules only when running the synthesis step, and so the reasoning behind Priority Path is discoverable from `references/` as a first-class concept.

**Read this file when:** you are the audit lead and you are running the Priority Path synthesis step, which happens after `<finding_reconciliation>` (format validation + voice check + dedup + ethics preservation) is complete and before `<audit_assembly>` writes the final `audit.md`.

---

## Purpose

After dedup completes, the lead synthesizes the deduplicated findings into a **Priority Path** — 3 to 5 prioritized "action stories" that group interconnected findings into single, actionable fixes.

**Why this step exists:**
A reconciled audit produces 20-30+ findings. Users staring at 30 findings feel paralyzed and do nothing. The Priority Path collapses that long list into 3-5 concrete actions, each of which fixes multiple underlying findings:

- "Fix the newsletter popup" → resolves 4 findings across 3 clusters
- "Replace the demo testimonials" → resolves 2 findings + closes an FTC violation
- "Unify the hero CTA story" → resolves 3 findings in the visual-cta cluster

The user gets ONE coherent action plan instead of a scattershot list.

**Priority Path is mandatory.** Every `audit.md` MUST have a `## Priority Path` section. Even on small audits with only 5-10 findings, write at least 1 action story (could be a single CRITICAL finding presented as its own story). Never skip this section. Never write "Priority Path: none" or similar.

---

## Process

### Step 1 — Group findings by SYNTHESIS_HINT slug

During reconciliation you collected the `SYNTHESIS_HINT: <slug>` tags from each finding. Bucket findings sharing a slug into one group. Each bucket becomes a candidate action story.

Findings without a `SYNTHESIS_HINT` tag are candidates for manual grouping in Step 2.

### Step 2 — Add ungrouped findings as candidates

Findings without a synthesis hint that share an `ELEMENT`, `SECTION`, or DOM region with another finding can be grouped manually. Use your reasoning here — you have all the findings in front of you and you know which ones diagnose the same underlying issue.

Examples of valid manual groupings:
- Two findings both targeting `section.hero` — one about headline visibility, one about CTA contrast → single "Fix the hero" story.
- Three findings on the checkout page — one about guest checkout, one about step count, one about zip autofill → single "Fix the checkout flow" story.
- One CRITICAL ethics finding + one HIGH trust finding both about fake testimonials → single "Replace the demo testimonials" story that closes the FTC violation AND the trust gap.

### Step 3 — Score each candidate group by impact

Scoring formula:

- **+10** per CRITICAL finding in the group
- **+5** per HIGH finding
- **+2** per MEDIUM finding
- **+1** per LOW finding
- **+3** per cluster spanned (cross-cluster groups are higher leverage)
- **+2** if the group touches the LCP element, hero, or first-fold area

**Tiebreaker:** groups with ethics-gate violations always rank above groups without, regardless of raw score. Ethics findings are non-negotiable and must surface prominently.

### Step 4 — Pick the top 3-5 groups

Aim for **3 minimum, 5 maximum.** If you have fewer than 3 cross-cluster groups, fill with the highest-priority single-cluster findings (a CRITICAL finding alone is still a valid action story).

### Step 5 — Write one action story per chosen group

Use this exact structure:

```markdown
### {N}. {Action title} ({SEVERITY})
**Fixes {X} findings across {Y} clusters** ({comma-separated cluster names})

{2-3 sentence description of what the issue is and why it matters. Cite specific evidence from the underlying findings.}

**Do this:** {1-2 sentence concrete action. ONE thing the user should do. Not a checklist — a single decision.}

**Underlying findings:** {cluster} F-{NN}, {cluster} F-{NN}, ...
```

---

## Rules for the action title

- It MUST be an action ("Fix the newsletter popup", NOT "Newsletter popup choice asymmetry")
- Lead with a verb when possible: "Replace", "Remove", "Optimize", "Fix", "Add", "Unify", "Shorten", "Reorder"
- Severity in parens at end: `(CRITICAL)`, `(HIGH)`, `(MEDIUM)`, `(LOW)`. Use the highest severity from the underlying findings.
- Numbered `1.`, `2.`, `3.`, ... in priority order (story 1 is the most important action).

---

## Rules for the "Do this" line

- **Concrete action, not a category.** "Add `loading='lazy'` to all below-fold images" not "Optimize images".
- **ONE decision the user makes.** If you find yourself writing "first do X, then do Y, then check Z" — that's a phase/plan output, not a Priority Path output. Pick the most important one and state it. The planner phase will break it into implementation steps.
- **Plain English, not jargon.** "Remove the testimonials section" not "Excise the placeholder UGC module". The Priority Path is the part a non-technical stakeholder reads first — it HAS to be jargon-free.

The voice rules from `${CLAUDE_PLUGIN_ROOT}/workflows/audit.md` Step 4b + 4c apply here too. Run the grandmother test on each "Do this" line before finalizing.

---

## Rules for `Underlying findings`

- **Format:** `{cluster-slug} F-{NN}` where `NN` is the finding's index within its cluster (1-based, in order they appear in the cluster section).
- **Comma-separated** on a single line.
- **Include all findings in the group**, not just the headliner. This is the link target for the visual report — the PRIORITY PATH tab will hyperlink each citation to the corresponding finding card in the cluster tab.
- The lead runs a validation pass during `<audit_assembly>` ("Priority Path citation validation step") that cross-checks every `{cluster} F-{NN}` reference against the actual cluster F-NN numbering in the audit.md. Bad references get dropped with a trace log entry.

---

## Remaining findings line

After the action story cards, add this line:

> **The remaining {N} findings** (smaller wins, edge cases, info-only items) are in the cluster sections below.

Where `N = total findings − count covered by Priority Path stories`. If Priority Path stories cover ALL findings (rare on small audits with high overlap), say "All findings are covered by the Priority Path above."

---

## Header line

Above the action stories, add:

> **{X} focused changes that fix {Y} of {Z} findings.** Tackle these first — everything else can wait.

Where:
- `X` = number of stories (3-5)
- `Y` = total findings covered by those stories
- `Z` = total findings in the audit

---

## Voice note

"Focused changes" reads warmer than "action stories" for a client report. Use **"changes"** for the count word, not "stories" or "items" — it implies the user is going to actually do something, not read about something.

"Tackle these first — everything else can wait" is a deliberate permission to defer the other 15-25 findings. Without it, users feel obligated to read every finding card and do nothing.

---

## Token budget

This synthesis takes ~5-10 thousand tokens of opus reasoning. It is **NOT optional** for cost reasons. The Priority Path is the primary user-facing artifact of the audit — the cluster sections are reference material, the Priority Path is the action plan. Cutting this to save tokens defeats the purpose of the audit.

See `${CLAUDE_PLUGIN_ROOT}/contracts/trace-assertion-canary.md` "Cost trace heuristic" for the `lead_cost` formula that already budgets for Priority Path synthesis overhead (the per-finding +$0.0004 component).

---

## Cross-references

- **`skills/audit/SKILL.md`** — `<priority_path_synthesis>` defers to this file. Audit lead reads this file during the synthesis step.
- **`${CLAUDE_PLUGIN_ROOT}/contracts/audit-reconciliation.md`** — the step immediately before synthesis. Produces the deduplicated finding set + SYNTHESIS_HINT groupings that this file consumes.
- **`${CLAUDE_PLUGIN_ROOT}/workflows/audit.md`** — cluster auditors write the `SYNTHESIS_HINT:` line on individual findings per Step 4 finding format. Auditors don't compute groupings; the lead does during synthesis.
- **`skills/audit/SKILL.md`** `<audit_assembly>` — runs the Priority Path citation validation step after synthesis: cross-checks every `{cluster} F-{NN}` reference against the actual cluster numbering and drops bad refs with a trace log entry.

When editing this file, the audit skill's `<priority_path_synthesis>` pointer stub should reference this file as the source of truth.
