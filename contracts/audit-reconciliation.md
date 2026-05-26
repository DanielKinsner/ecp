# Audit reconciliation

Canonical reference for the lead's reconciliation phase — format validation (Step 0), voice check (Step 0b, added in Round 14), deduplication, ethics preservation, and consolidated audit.md assembly. Runs after cluster auditors complete their tasks and before Priority Path synthesis.

**Why this file exists:** The reconciliation phase is the quality gate between cluster auditor output and the final audit.md. It contains three distinct enforcement layers (format, voice, dedup+ethics) that all live in the reconciliation step but serve different quality concerns. Prior to Round 12, these 120+ lines sat inline in `skills/audit/SKILL.md` where they interrupted the phase flow. Round 14 added the voice check (Step 0b) on top of the existing format check (Step 0), making the section even heavier. Extracting the whole reconciliation block as an **atomic unit** into this canonical file keeps all three enforcement layers together (they share the same SendMessage correction loop, same two-attempt escape, same audit-trace.log logging) while giving the audit lead a cleaner orchestration narrative.

**Atomic extraction rule:** Step 0 + Step 0b + the reconciliation process MUST stay in one file. Do not split the format check from the voice check — they share the correction loop. Do not split the validation passes from the dedup logic — the dedup logic assumes validation passed. This file is the canonical home for the entire reconciliation phase.

**Read this file when:** you are the audit lead (or compare lead — same logic applies to both pages) and all cluster auditor teammates have marked their tasks complete. You're about to validate and reconcile their findings into the consolidated `audit.md`.

---

## Overview

After all cluster auditor teammates have marked their tasks complete, the lead validates and reconciles their findings into the consolidated `audit.md`. The validation happens in two sequential passes (format, then voice), each with a two-attempt correction loop via SendMessage. Only after both passes clear does dedup + ethics preservation + assembly run.

Sequence of operations:

1. **Step 0 — Format validation pass** (per cluster file, as each one arrives, don't wait)
2. **Step 0b — Voice check pass** (after format check passes)
3. **Reconciliation process** (dedup + ethics preservation + SYNTHESIS_HINT grouping + final ordering)
4. **Handoff to `<priority_path_synthesis>`** — runs next, see `${CLAUDE_PLUGIN_ROOT}/contracts/priority-path-synthesis.md`

---

## Step 0 — Format validation pass (MANDATORY, do this BEFORE reconciliation)

For each cluster file as it arrives (don't wait for all of them — validate per arrival), the lead must check format compliance:

### Source of truth — the linter regex is authoritative

The format spec lives in **two places** that MUST stay in lockstep: this contract's prose (human-readable mirror) and `scripts/validate-cluster-files.py` (executable definition). When they disagree, **the regex wins**. Coordinators deriving format-correction templates for SendMessage bounces MUST copy the fence + first-line shape from the regex below, not paraphrase from the prose.

**Authoritative regex (verbatim from `scripts/validate-cluster-files.py:57-60`):**

```python
_FINDING_FENCE = re.compile(
    r"^```\s*$(?:\r?\n)FINDING:\s*(FAIL|PARTIAL)\s*$",
    re.MULTILINE,
)
```

A FINDING block is recognized when:

1. A triple-backtick fence opens on its own line (no language tag, no trailing characters), immediately followed by
2. `FINDING:` and either `FAIL` or `PARTIAL`, on its own line — this is the **first line inside the fence**, not the second or fifth.

The remaining fields (`TITLE:`, `SECTION:`, `ELEMENT:`, etc.) are required by the format example below but are not part of the fence-opener regex. The regex is the gate; the field list is the contract.

**Why this section exists (added 2026-04-27 from §24.2 #1):** A live engagement (slingmods.com PDP, 2026-04-27) had its format-correction loop fail because the lead synthesized a bounce-back template from this contract's prose without checking the regex. The lead's template put `SECTION:` first and `VERDICT:` at the end; auditors faithfully followed the wrong template; 5 of 7 second-round files still failed validation. The single-source-of-truth fix is to inline the regex here so coordinator and linter cite the same authority.

**Maintenance rule:** any edit to `_FINDING_FENCE` in `validate-cluster-files.py` MUST update this section in the same commit, and vice versa. CI should grep both files in the same diff or fail.

### Procedure

1. Read `docs/ecp/{engagement-id}/cluster-{cluster}-{device}.md`
2. Run a format check. The cluster file MUST contain code-fenced FINDING blocks of the form:
   ```
   ```
   FINDING: FAIL
   TITLE: ...
   SECTION: ...
   ELEMENT: ...
   SOURCE: ...
   OBSERVATION: ...
   RECOMMENDATION: ...
   REFERENCE: ...
   PRIORITY: ...
   **Why this matters:** ...
   ↳ {citation} [Tier]
   ```
   ```
3. **Format violations to detect:**
   - File contains `### F-XXX` headings instead of code-fenced blocks → REJECT
   - Findings use `[TAG]` blocks inside code fences instead of `FINDING:` prefix → REJECT
   - Findings use `### Finding 1:` or `### F1.` headings → REJECT
   - File uses `## Finding N` sections instead of code-fenced blocks → REJECT
   - Code-fenced blocks present but missing `FINDING:` line at the top → REJECT
   - Any FAIL or PARTIAL finding missing a `TITLE:` line → REJECT (see TITLE sub-checks below)
   - Any `TITLE:` value longer than 60 characters → REJECT
   - Any `TITLE:` value that trivially matches its SECTION slug (e.g., SECTION `value-proposition` + TITLE `Value Proposition`, case-insensitive, ignoring hyphens/spaces) → REJECT — the TITLE exists specifically to differentiate findings that share a SECTION
   - Two or more findings in the cluster file sharing an identical TITLE (case-insensitive, whitespace-normalized) → REJECT
   - All findings code-fenced AND each starts with `FINDING: FAIL` or `FINDING: PARTIAL` AND TITLE rules above satisfied → ACCEPT

4. **If REJECTED, send the auditor back via SendMessage:**
   ```
   SendMessage to "auditor-{cluster}-{device}":
   "Your cluster file at docs/ecp/{engagement-id}/cluster-{cluster}-{device}.md
    does not use the required format. Findings MUST be wrapped in triple-backtick
    code fences with `FINDING: FAIL` or `FINDING: PARTIAL` as the first line of
    each block. Your file currently uses [describe what they did wrong].
    Please rewrite the file in the canonical format documented in
    workflows/audit.md Step 4a 'Worked Examples' and Step 4d 'TITLE field rules'.
    The reconciler depends on this format, and the visual report generator
    parses code-fenced blocks via regex.
    Reformatting in place is acceptable — keep your observations and
    recommendations verbatim, only change the wrapper structure.
    Mark your task in_progress again while you rewrite, then back to completed
    when done."
   ```

   **For TITLE-specific rejections, use this tailored message instead:**
   ```
   SendMessage to "auditor-{cluster}-{device}":
   "Your cluster file at docs/ecp/{engagement-id}/cluster-{cluster}-{device}.md
    cleared the block-format check but failed TITLE validation. Specific issues:

    - [List each offending finding by its current TITLE or block position, e.g.,
      'Finding #3 is missing a TITLE: line entirely',
      'Findings #2 and #5 both have TITLE: Value Proposition — must be unique within this cluster',
      'Finding #7 has TITLE: Trust Badges which matches its SECTION slug trust-badges — too generic',
      'Finding #4 TITLE is 74 chars — must be ≤60'].

    Please re-read workflows/audit.md Step 4d 'TITLE field rules' and rewrite the
    offending TITLE lines only. Keep every other field (SECTION, ELEMENT, OBSERVATION,
    RECOMMENDATION, PRIORITY, REFERENCE, citation) verbatim. Rename titles to name
    the specific element or sub-issue (e.g., 'Homepage Hero Lacks Value Prop',
    'Product Cards Generic Copy'). Two findings in the same cluster cannot share an
    identical TITLE.

    Mark your task in_progress again while you rewrite, then back to completed
    when done."
   ```
5. Wait for the corrected file (the teammate will message you when done) and re-validate. **Two corrections max** — if the teammate still produces wrong format on the second attempt, the lead reformats in place AND logs the failure in `audit-trace.log` for follow-up. Do NOT silently reformat without going through this two-attempt loop first.

**Why the format check matters:** A live test on awdmods.com (April 7, 2026) showed 5 of 10 cluster auditors writing in the wrong format. Previous behavior was for the reconciler to silently reformat them during audit.md assembly, which "worked" but hid the problem and added unaccounted reconciler work. The new lead-as-validator pattern fails fast at the right layer, gives the auditor a chance to fix its own output, and only falls back to silent rewriting if the teammate genuinely can't produce the right format. This is exactly the kind of mid-flight coordination that subagents couldn't do but teammates can.

---

## Step 0b — Voice check pass (MANDATORY, runs after format check passes)

After the format check accepts a cluster file, the lead runs a voice check against the OBSERVATION and RECOMMENDATION fields of each finding. The voice guide in `${CLAUDE_PLUGIN_ROOT}/workflows/audit.md` Step 4b + Step 4c is the canonical reference — this check enforces it at the reconciliation layer so clients never see raw jargon output.

**Voice check — scan each finding's OBSERVATION and RECOMMENDATION fields for these violation patterns:**

1. **Unexplained acronyms/abbreviations** (reject if present without plain-English expansion in the same sentence): `LCP`, `FID`, `CLS`, `TBT`, `TTFB`, `CWV`, `WCAG` (without "accessibility" context), `ARIA` (without "screen reader" context), `SERP`, `OCMOD`, `LTV`, `DPR`, `SSR`, `CSR`, `CMS`, `DOM`, `CSS` (acceptable in CODE findings only), `srcset`, `rel=preload`, `rel=canonical`, `h1/h2/h3`, `sr-only`, `aria-hidden`, `role=`, `viewport meta`. If the acronym appears only in the structured fields (ELEMENT, REFERENCE), that's OK — the check is on narrative prose only.
2. **Framework/library jargon without context:** `React`, `Shopify Liquid`, `Next.js` (OK in platform-specific notes, not in client narrative), `schema.org`, `hydration`, `SPA`, `hook`, `component`, `event listener`.
3. **Compliance/violation framing instead of outcome framing:** look for the words `violation`, `compliance`, `conformance`, `mandates`, `required by spec` — these read as audit-speak. The only legitimate places for these words are ETHICS findings (ethics-gate references) and legal compliance findings (EU DSA, FTC, WCAG AA requirements on accessibility pages). Elsewhere, reject and ask the teammate to rewrite using the voice guide's "what we found / what to do" pattern.
4. **Abstract nouns without referents:** `optimize`, `enhance`, `leverage`, `synergy`, `best practice`, `industry standard`, `thought leadership` — empty corporate filler that doesn't tell the visitor what actually changes on the page.
5. **Citation-only "Why this matters":** if the `**Why this matters:**` line is ONLY a research citation (e.g., "Per Baymard (2024), CTA contrast affects conversion by 8-12%.") without the "for a store doing X orders/month, that's Y" or equivalent business translation, reject.
6. **Internal pipeline terminology:** References to ECP pipeline artifacts that expose the multi-agent architecture to the client. Reject if the OBSERVATION or RECOMMENDATION contains: `baton`, `dispatch`, `dispatch brief`, `coordinator`, `teammate`, `cluster file`, `cluster context`, `engagement directory`, `acquirer`, `trace log`, `reconciliation`, `auditor-`, `team-lead`, `SendMessage`, `TaskUpdate`. The client should not know the audit was produced by a multi-agent pipeline — write as if you examined the page directly.
7. **Soft jargon that passes the acronym check but fails the grandmother test:** `proximate` (use "near" or "next to"), `at the point of [noun]` (use "when [verb]"), `price evaluation` (use "looking at prices"), `render-blocking` (use "slows down the page"), `viewport` without context (use "screen" or "what visitors see"), `above-fold` without explanation (use "the part of the page visitors see before scrolling"), `DOM` in non-CODE findings (use "the page" or "the page source"), `element` when referring to visible things (use the actual name — "the button", "the banner", "the price tag"). These terms are common in developer documentation but opaque to business owners.

**If REJECTED on voice check, send the auditor back via SendMessage:**
```
SendMessage to "auditor-{cluster}-{device}":
"Your cluster file at docs/ecp/{engagement-id}/cluster-{cluster}-{device}.md
 passed format validation but failed the voice check. The following findings
 use jargon or framing that won't translate for a client reader:

 - Finding at SECTION [slug]: uses [specific jargon term] without plain-English
   equivalent.
 - Finding at SECTION [slug]: uses 'violation'/'compliance' framing instead
   of 'what we found / what to do'.
 - Finding at SECTION [slug]: 'Why this matters' is citation-only without
   business outcome translation.

 Please rewrite these findings using the voice guide in
 workflows/audit.md Step 4b and the cluster-specific worked examples
 in Step 4c. Keep the SECTION, ELEMENT, PRIORITY, SOURCE, and REFERENCE
 fields exactly as you had them — only rewrite OBSERVATION, RECOMMENDATION,
 and **Why this matters** in plain English. The grandmother test applies:
 if a small business owner or a store manager wouldn't understand what
 you wrote in one read, simplify.

 Mark your task in_progress again while you rewrite, then back to completed
 when done."
```

Same two-attempt loop as the format check. On third failure, the lead rewrites in place using the voice guide's translation patterns AND logs the voice failure in `audit-trace.log` for follow-up. Do NOT silently pass jargon-laden findings through to the client.

**Exemptions from the voice check:**
- Ethics findings citing regulations (EU DSA, FTC Fake Reviews Rule, CA SB-478, GDPR) MAY use compliance-framing because that's the legal nature of the finding.
- The `ELEMENT` field may use CSS selectors (`button.btn-cart`) — this is the data layer, not the narrative layer.
- The `REFERENCE` field may use technical filenames — this is the data layer.
- Quoted page content (if the auditor quotes the page's actual copy) retains the page's original wording, even if it contains jargon.

**Why this check is mandatory:** The whole value of ECP is that it speaks to clients the way a consultant would, not the way an engineer would. If even one finding in the output slips into compliance-speak or unexplained acronyms, it breaks the trust the rest of the report is trying to build. The Round 4 voice guide gave auditors the rules; Round 14's voice check enforces them at the reconciliation layer so slips never reach the visual report.

---

## Step 0c — Evidence-anchor gate (MANDATORY, runs after voice check passes)

After format and voice checks both pass, the lead runs an evidence-anchor check against every finding in the cluster file. A finding fails this gate if its OBSERVATION and RECOMMENDATION fields contain no concrete evidence anchor tying the finding to the page under audit. Anchors are the same three types enumerated in `${CLAUDE_PLUGIN_ROOT}/contracts/dispatch-contract.md` Evidence requirement section:

1. **DOM selector** that matches an element present in the cluster-context JSON for this engagement (e.g., `button.add-to-cart-hero`, `div[data-reviews="0"]`, `.wc-block-product-price`).
2. **Screenshot region** referenced by approximate coordinate (e.g., "top-right quadrant of mobile hero", "~340×220 at 0,120").
3. **Verbatim quoted copy** of ≥3 consecutive words from the acquired DOM text (e.g., `"free shipping over $75"`, `"only 3 left in stock"`).

**Fail signals — any of these mark a finding as generic, no-anchor:**
- The ELEMENT field is blank, `(unspecified)`, or a placeholder like `hero`/`page`/`site` without a CSS selector or data attribute.
- OBSERVATION contains any forbidden framing listed in contracts/dispatch-contract.md ("consider adding", "best practice suggests", "typical stores benefit from", "industry standard is", "users often expect", "research shows that") AND no quoted copy or measured value appears elsewhere in the block.
- RECOMMENDATION describes an abstract pattern ("strengthen the CTA", "improve trust signals", "add urgency") without naming a specific page element or location to apply the change.

**If REJECTED on evidence-anchor gate, send the auditor back via SendMessage:**
```
SendMessage to "auditor-{cluster}-{device}":
"Your cluster file at docs/ecp/{engagement-id}/cluster-{cluster}-{device}.md
 passed format and voice checks but failed the evidence-anchor gate. The
 following findings read as generic CRO advice — they could be pasted into
 any audit of any store because they don't reference THIS page:

 - Finding at SECTION [slug]: no DOM element named; OBSERVATION uses
   [specific forbidden framing]. Add a CSS selector or data attribute
   from the cluster-context JSON, OR quote the specific copy you observed,
   OR describe a screenshot coordinate.
 - Finding at SECTION [slug]: RECOMMENDATION is abstract ('strengthen the
   CTA'). Name the actual button/link on the page and describe the specific
   change (color, copy, placement).

 Please rewrite with a concrete evidence anchor — see contracts/dispatch-contract.md
 'Evidence requirement' section and the 'acceptable' worked example. If you
 genuinely can't identify an anchor for a finding after examining the
 cluster-context JSON and the screenshots, drop the finding rather than
 emit it generic.

 Mark your task in_progress again, rewrite, then back to completed."
```

Same two-attempt loop as format and voice checks. On third failure, the lead **drops the finding silently** (no special marker, no placeholder) — a cluster that lands with zero surviving findings after Step 0c is rendered in the audit as an empty cluster. Generic advice never reaches the client.

**Exemptions from the evidence-anchor gate:**
- Ethics findings (ETHICS_STATE: BLOCK or ADJACENT) are exempt — their evidence anchor is the cited regulation, not the page. Ethics findings already carry SOURCE_URL linking to the primary source.
- PASS findings (`FINDING: PASS`) are exempt — they describe what the page is doing well, and may legitimately reference generic patterns being correctly implemented.

**Why this check is mandatory:** The #1 failure mode that makes rendered reports feel robotic and generic is page-agnostic CRO advice dressed up as findings. The voice check catches jargon; this check catches the deeper problem of findings that don't actually describe the page under audit. Combined with dispatch-contract's Evidence requirement section (telling auditors upfront to produce anchored findings) and evidence-tiers.md (downgrading unanchored findings to Bronze regardless of citation quality), the three layers make page-specificity non-optional.

---

## Step 1 — Voice humanizer rewrite (runs after 0-series gates pass)

After Step 0, 0b, and 0c all pass for a cluster, the lead dispatches the humanizer subagent to rewrite the OBSERVATION and RECOMMENDATION fields of eligible findings into senior-strategist voice. This is NOT a validator gate — it is a transform pass. 0-series stages share the SendMessage correction loop and the validator semantics; Step 1 is a one-shot dispatch that either polishes voice or fails gracefully.

**Pre-dispatch filter (lead-orchestrated, not prompt-driven):**

Before constructing the humanizer prompt, the lead splits each cluster's findings into two lists:

- `passthrough` — any finding where `ethics_state in ("BLOCK", "ADJACENT")` OR the finding's `SOURCE_URL:` / `REFERENCE:` points at a `references/ethics-gate.md` Source Registry URL. These findings are EXCLUDED from the humanizer's input batch. Their original voice-checked text is kept verbatim. The humanizer never sees them and cannot soften a legal claim.
- `to_humanize` — everything else in the cluster. These are sent to the humanizer subagent as a JSON array.

This is a routing decision in code, NOT an instruction in the humanizer's prompt. Never rely on the LLM to self-skip ethics findings. Filter first; dispatch second.

**Dispatch:** one `Task` call per cluster. `subagent_type: general-purpose`. Prompt body lives in `${CLAUDE_PLUGIN_ROOT}/contracts/humanizer-subagent.md` — the lead interpolates `{{cluster}}`, `{{engagement_id}}`, and `{{findings_json}}`. The subagent returns one fenced JSON code block containing a `rewrites` array.

**Post-response validation (Python-side, lightweight):**

For each rewrite returned:

- If `finding_id` is not in the input batch → reject that rewrite, keep the original voice-checked text.
- If `len(new_observation) < 0.7 * len(original_observation)` OR `> 1.5 * len(original_observation)` → reject that rewrite, keep original. Same check on `recommendation`. Length drift is the single reliable signal of truncation or padding.
- If the response has no fenced JSON block OR the JSON is malformed OR `rewrites` is missing → reject the ENTIRE cluster's response, keep all originals. Log the failure in `audit-trace.log` with the first ~200 chars of the response text for diagnosis.

**No retry loop.** One humanizer dispatch per cluster per run. Failure keeps original voice-checked text — which already passed Step 0b's blocklist gate, so it ships at acceptable quality, just without polish. Voice humanization is a nice-to-have; never trade a validated finding for a failed rewrite. Elaborate retry-with-correction loops defend a failure mode we have not observed.

**Why this runs here:** the voice check in Step 0b is a REJECTOR — it bounces findings with hard-banned terms (baton, dispatch brief, DOM, render-blocking, etc.). Step 1's humanizer is a REWRITER — it takes findings that already cleared Step 0b's blocklist but still carry residual softer jargon ("proximate", "price evaluation", "above-fold") and polishes them into the senior-strategist register. Step 0b owns "kill the obvious jargon"; Step 1 owns "polish the voice of what's left." The pre-dispatch ethics filter means Step 1 cannot soften a BLOCK or ADJACENT finding — those skip the rewriter entirely.

**Model rationale:** humanizer subagent is dispatched asking for Opus-tier reasoning in the prompt body. Sonnet reads more robotic for voice/copy work — operator preference. Cost tradeoff could revisit in v1.1.

---

## Reconciliation process per device

Only run AFTER format validation AND voice check pass for all cluster files.

1. List all `cluster-{cluster}-{device}.md` files in the engagement directory.
2. Read each file. Parse FINDING blocks (each wrapped in triple-backtick code fences per the existing finding format).
3. For each finding, extract: `TITLE`, `SECTION` slug, `ELEMENT`, `SOURCE`, `PRIORITY`, `OBSERVATION`, `RECOMMENDATION`, `REFERENCE`, citations, and any `SYNTHESIS_HINT` tag. TITLE must have cleared the format gate — any finding reaching this step without a unique-within-cluster TITLE is a gate-escape bug; log and bounce back to Step 0.
4. **Apply deduplication (three layers):**

   **Layer 1 — Exact match:** Two findings are duplicates if they share the same `SECTION` slug AND target the same `ELEMENT` (or substantially overlapping elements). When duplicates are found, keep the finding with the higher `PRIORITY`. If equal, keep the one with the stronger evidence tier (Gold > Silver > Bronze — see `${CLAUDE_PLUGIN_ROOT}/references/evidence-tiers.md`). Append to the kept finding's observation: `Also identified by {other_cluster} cluster.`

   **Layer 2 — SYNTHESIS_HINT merge:** Findings sharing the same `SYNTHESIS_HINT: <slug>` value that describe the **same underlying issue** (not just related issues) should be merged into a single finding. Keep the finding with the most complete observation, merge unique details from other findings, and list all source clusters. This prevents the same issue (e.g., "AI-generated hero image") from appearing as 3 separate finding cards from 3 different clusters.

   **Layer 3 — Same-cluster SECTION collapse (MANDATORY):** When a single cluster produces 2+ findings that share **both** the same `SECTION` slug AND an overlapping `ELEMENT` (same CSS selector, or one selector is a clear parent/child of the other, or both point at the same descriptive location such as "hero area"), the lead MUST collapse them into 1 combined finding with sub-points. This is a gate, not a suggestion — unresolved overlaps inflate the finding count and produce the duplicate-title problem in the rendered left rail.

   **How to collapse:**

   1. Pick the finding with the highest PRIORITY as the kept finding. Ties broken by Gold > Silver > Bronze evidence tier, then by the longer OBSERVATION (richer evidence).
   2. Rewrite the kept finding's `TITLE` to cover the combined scope — e.g., three hero-image findings with titles `"Hero Image 2.4MB"`, `"Hero Image No srcset"`, `"Hero Image No Explicit Dimensions"` collapse to one finding titled `"Hero Image Loading Issues"`.
   3. Merge the RECOMMENDATION fields as a sub-bulleted list, preserving each discrete action. Preserve the highest-value citation + tier from the source findings; other citations go into a `**Also referenced:**` line appended to `**Why this matters:**`.
   4. Merge unique evidence from each OBSERVATION. If the merged OBSERVATION would exceed ~4 sentences, prefer the strongest evidence sentence and drop redundant framing.
   5. Collapse the `REFERENCE:` line to the kept finding's primary reference; drop the others.
   6. The combined finding carries the `SECTION`, `ELEMENT`, `SOURCE`, and `PRIORITY` of the kept finding. If the other collapsed findings had `SYNTHESIS_HINT` values the kept finding lacked, append them (comma-separated).

   **Worked example — input (3 findings, same SECTION, same ELEMENT scope):**

   ```
   FINDING: FAIL
   TITLE: Hero Image Weight 2.4MB
   SECTION: image-optimization
   ELEMENT: section.hero img.hero-photo
   OBSERVATION: The hero image is a 2.4MB JPEG shipped at full resolution to every device...
   RECOMMENDATION: Export the hero at three widths and serve via srcset.
   PRIORITY: HIGH
   ```

   ```
   FINDING: FAIL
   TITLE: Hero Image No srcset
   SECTION: image-optimization
   ELEMENT: section.hero img.hero-photo
   OBSERVATION: The hero <img> has no srcset attribute, so mobile browsers download the 1920-wide variant...
   RECOMMENDATION: Add a srcset with 480w, 960w, and 1920w variants.
   PRIORITY: HIGH
   ```

   ```
   FINDING: FAIL
   TITLE: Hero Image Missing Dimensions
   SECTION: image-optimization
   ELEMENT: section.hero img.hero-photo
   OBSERVATION: The hero <img> tag has no width or height attributes, so the browser can't reserve space...
   RECOMMENDATION: Add width="1920" height="900" to the img tag.
   PRIORITY: MEDIUM
   ```

   **Output (1 collapsed finding):**

   ```
   FINDING: FAIL
   TITLE: Hero Image Loading Issues
   SECTION: image-optimization
   ELEMENT: section.hero img.hero-photo
   OBSERVATION: The hero image is a 2.4MB JPEG shipped at full resolution to every device, with no srcset for responsive delivery and no width/height attributes. On mobile, the browser downloads the full 1920-wide image and then reflows the page when it arrives.
   RECOMMENDATION:
   - Export the hero at three widths (480w, 960w, 1920w) and wire them via srcset so each device gets an appropriately sized image.
   - Add explicit width="1920" height="900" (or the aspect-ratio CSS equivalent) so the browser reserves layout space before the image loads.
   PRIORITY: HIGH
   ```

   **What NOT to dedup:** Findings that share a `SECTION` slug but target genuinely different elements (e.g., `SECTION: trust-badges` appearing on `footer .payment-icons` and again on `section.hero .trust-strip` — these are two distinct trust-badge problems at two locations, keep both but ensure their TITLEs are distinct). Cross-cluster findings tagged with the same SYNTHESIS_HINT that describe **related but distinct** issues (e.g., pricing and trust aspects of the same order summary) — these stay separate but are grouped in the Cross-Cluster Connections section.

   **If Layer 3 leaves 2+ findings with identical TITLEs after collapse:** treat this as a format-gate failure and SendMessage the auditor to rename the remaining titles for uniqueness. The client-facing report cannot ship with duplicate left-rail labels.

5. **Contested severity handling:**
   When 2+ auditors flag the **same underlying issue** (same SYNTHESIS_HINT or same SECTION+ELEMENT) at **different** severity levels:
   - If the spread is 1 level (e.g., HIGH vs MEDIUM): keep the higher severity. Normal disagreement.
   - If the spread is 2+ levels (e.g., CRITICAL vs MEDIUM): this is a **contested finding**. The lead MUST read the reasoning from both findings before choosing a severity. Do NOT auto-promote to the highest severity — the highest-severity finding may have weaker reasoning or cite an inapplicable regulation.
   - For contested CRITICAL findings that cite specific regulations (ethics-gate references): verify the regulation actually applies to the specific scenario. If the citation is incorrect (e.g., citing FTC Operation AI Comply for decorative imagery, or CA SB-478 for shipping costs), downgrade to the severity supported by the correct legal analysis.
   - Log contested findings and the lead's resolution in `audit-trace.log`.

6. **Ethics gate preservation rule:** If ANY teammate flagged a finding as `PRIORITY: CRITICAL` with a reference to `ethics-gate.md`, the lead MUST verify that the cited regulation **actually applies to the specific scenario on this page** before preserving CRITICAL. A correct regulation name with an incorrect application is still a false positive. Verification means:
   - Check the regulation's source URL (see ethics-gate.md Source Registry) to confirm the specific section cited covers this conduct
   - Check whether the auditor passed the three-question Applicability Self-Check (ethics-gate.md)
   - If the finding has `APPLICABILITY_UNCERTAIN: true`, the lead MUST independently verify before preserving CRITICAL
   - If verification confirms the regulation applies: retain `PRIORITY: CRITICAL`. The finding cannot be downgraded.
   - If verification shows the regulation doesn't apply to this scenario: downgrade to the severity supported by the correct legal analysis and log the reason in `audit-trace.log`
   - **Ethics violations with incorrect or inapplicable citations MUST be downgraded.** Presenting a false legal accusation to the user is worse than missing a finding.

7. **Synthesis hint grouping:** After dedup, remaining findings sharing the same `SYNTHESIS_HINT: <slug>` value are tagged as a synthesis group for the Cross-Cluster Connections section and for Priority Path story construction.

8. Order findings by `PRIORITY` (CRITICAL → HIGH → MEDIUM → LOW), then by cluster (per the order in `clusters_used` from `meta.json`).

9. Write the consolidated `audit.md` per the `<audit_assembly>` format in `skills/audit/SKILL.md`.

---

## Cluster file lifecycle

- Cluster files (`cluster-{cluster}-{device}.md`) are intermediate artifacts. They persist after reconciliation for debugging and re-reconciliation.
- They are NOT consumed by the visual report generator — only `audit.md` (and `audit-{device}.md` for the second device in dual-device mode) are.
- They CAN be re-read on resume if reconciliation needs to be re-run (e.g., after a single cluster is re-audited and the lead wants to re-integrate the corrected findings without re-running the other clusters).

---

## Expected reduction

30-60 raw findings (across 6 clusters × 2 devices) typically deduplicate to 18-30 unique findings per device. The 10-cluster system produces more raw findings than the old 4-cluster system (v4.x), but cross-cluster overlap is also higher (more deduping). The ratio holds because the new clusters carve up the reference library more finely, not because they add new findings — same total content, better routed.

---

## Cross-references

- **`skills/audit/SKILL.md`** — `<finding_reconciliation>` defers to this file. Audit lead reads this file after all cluster auditor tasks complete.
- *(Compare mode — reconciling two pages — is out of scope in this build; see `product.md`.)*
- **`${CLAUDE_PLUGIN_ROOT}/contracts/priority-path-synthesis.md`** — the phase immediately after reconciliation. Consumes the deduplicated finding set + SYNTHESIS_HINT groupings.
- **`${CLAUDE_PLUGIN_ROOT}/contracts/trace-assertion-canary.md`** — after reconciliation completes, the lead increments `cluster_files_written` (one per file that passed both validation passes) and eventually runs the self-check at audit completion.
- **`${CLAUDE_PLUGIN_ROOT}/workflows/audit.md`** Step 4 / 4a / 4b / 4c — the canonical format + voice guide the cluster auditors are supposed to follow. The validation passes in this file enforce conformance.
- **`${CLAUDE_PLUGIN_ROOT}/references/evidence-tiers.md`** — Gold/Silver/Bronze tie-breaker rules for the dedup step.
- **`${CLAUDE_PLUGIN_ROOT}/references/ethics-gate.md`** — source of the CRITICAL preservation rule.

When editing this file, the audit skill's `<finding_reconciliation>` pointer stub should reference this file as the source of truth. The compare skill can reference this file directly without deferring through audit — that's a bonus side-effect of Round 12.4 being clean.
