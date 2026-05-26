---
name: ecp-reconciler
context: fork
---

# E-Commerce Psychology Reconciler — Deadlock Arbitration Only

> **Frequency: RARE-PATH.** This workflow runs only during multi-planner deadlocks — a situation that arises in fewer than 10% of audit engagements. Most multi-planner runs resolve conflicts via peer SendMessage negotiation and never spawn a reconciler. If you are reading this file to understand the common audit flow, you are in the wrong place — see `contracts/audit-reconciliation.md` for the standard finding reconciliation process, or `contracts/multi-planner-protocol.md` for the peer-negotiation protocol.

**Scope:** This workflow is the **deadlock arbitration escape hatch** for multi-planner mode. It is NOT the default plan-merging flow.

**When this workflow runs:** Only when 2+ planner teammates flag an unresolvable conflict via SendMessage during the peer-to-peer negotiation phase of multi-planner planning. The audit/build coordinator spawns a `reconciler` teammate (`name="reconciler"`, `model: "opus"`) as the deadlock arbitrator, and that teammate reads this workflow as its task context.

**When this workflow does NOT run:** During normal multi-planner mode where planners successfully coordinate cross-cluster overlaps via peer SendMessage. In the common case, planners resolve conflicts themselves during planning and no reconciler is ever spawned. See `${CLAUDE_PLUGIN_ROOT}/contracts/multi-planner-protocol.md` for the canonical peer-negotiation protocol.

**You (the reconciler) receive multiple action plans (PRDs) that will be applied to the same page, plus the specific SendMessage exchanges that flagged the deadlock.** Your job is to arbitrate the flagged conflicts and resolve them so the plans can be implemented without contradictions.

## Input

The coordinator provides:
1. **PRD files** — 2-4 action plan files, each focused on a different domain cluster
2. **Audit findings** — the full audit.md so you understand WHY each planner made its decisions. Each finding includes the SECTION slug, SOURCE, and the principle that drove the recommendation.
3. **Ethics gate content** — non-negotiable rules
4. **Conflict resolution rules** — priority hierarchy for resolving conflicts
5. **Auto mode flag** — if true, resolve all conflicts deterministically (see Auto Mode)

## Process

### Step 1: Read All PRDs

Read every PRD file provided. For each plan step, note:
- The SECTION slug it targets
- The specific change proposed
- The priority level

### Step 2: Identify Conflicts

Identify any conflicts — places where plans contradict each other or make incompatible assumptions about the same page elements. Common conflict patterns:

- **Same element, different changes:** Two plans target the same SECTION slug with contradictory modifications (e.g., one says "make CTA orange" while another says "add green trust badge adjacent to CTA")
- **Style/color clashes:** Plans propose colors or styles that would clash visually when applied together
- **Layout assumptions:** One plan assumes an element is in position X while another plan moves it to position Y
- **Competing for space:** Two plans add content to the same limited area (e.g., both add elements above the fold)

### Step 3: Resolve Conflicts

For each conflict, resolve using this priority hierarchy:
1. **Legal/accessibility compliance** — WCAG AA, EU DSA, FTC, CA SB-478. Non-negotiable.
2. **Ethics gate** — No dark patterns, even if they "convert better."
3. **User-specified constraints** — Respect business context.
4. **Domain-specific guidance** — Higher-priority cluster wins ties.

When resolving, amend the lower-priority plan's step with a note:
```
[RECONCILED: adjusted from X to Y due to conflict with plan-{cluster-slug}]
```

### Step 4: Handle Irreconcilable Conflicts

If both conflicting steps are CRITICAL priority and cannot be reconciled without violating one:
- Flag for user decision with clear explanation of the tradeoff
- In `--auto` mode: apply tiebreaker using the cluster routing table order (the cluster listed first for the page type wins). Document as `[AUTO-RESOLVED: tiebreaker applied — {winning-cluster} takes precedence per routing table order]`

## Output Format

```
## Reconciliation Report

### Conflicts Found: [N]

#### Conflict 1: [SECTION slug]
- **Plan A** (plan-{slug}.md, step #): [what it proposes]
- **Plan B** (plan-{slug}.md, step #): [what it proposes]
- **Resolution:** [what was changed and why]
- **Priority rule applied:** [which level of the hierarchy decided this]

[Repeat for each conflict]

### Amended Plan Steps

[For each amended step, output the full updated step text with the [RECONCILED] tag]

### No-Conflict Verification

[List SECTION slugs that appear in multiple plans but are compatible — confirms you checked them]

RECONCILED: [N] conflicts resolved
```

If no conflicts found:
```
## Reconciliation Report

No cross-plan conflicts detected. All plans target distinct page areas or propose compatible changes.

NO_CONFLICTS: plans are compatible
```

## Output Rules

- Return the complete reconciliation report
- Every conflict must have a resolution with a cited priority rule
- Amended plan steps must include the full updated text (the coordinator will write them back to the PRD files)
- Do not modify steps that are not in conflict — preserve them exactly as written
- Never create new steps — only amend existing ones

## Quality Check

Before returning, verify:
- [ ] Every identified conflict has a resolution
- [ ] Every amended step includes the [RECONCILED] tag
- [ ] No new steps were created (only amendments)
- [ ] Ethics gate violations are never resolved in favor of the violating plan
- [ ] The reconciliation report is complete and self-contained

## Multi-PRD Conflict Resolution Logic

### How plans_queue Works in meta.json

When multi-planner mode is active, `meta.json` tracks each PRD's lifecycle:

```json
"plans_queue": [
  {
    "cluster": "visual-cta",
    "file": "plan-visual-cta.md",
    "phase": "plan",
    "steps": 8,
    "priority_breakdown": { "critical": 0, "high": 4, "medium": 3, "low": 1 },
    "reconciled": true,
    "amendments": 1
  },
  {
    "cluster": "trust-credibility",
    "file": "plan-trust-credibility.md",
    "phase": "plan",
    "steps": 6,
    "priority_breakdown": { "critical": 1, "high": 3, "medium": 2, "low": 0 },
    "reconciled": true,
    "amendments": 0
  },
  {
    "cluster": "pricing",
    "file": "plan-pricing.md",
    "phase": "plan",
    "steps": 5,
    "priority_breakdown": { "critical": 0, "high": 2, "medium": 3, "low": 0 },
    "reconciled": true,
    "amendments": 0
  }
]
```

Each entry tracks:
- `cluster` — which cluster this plan covers
- `file` — filename relative to engagement directory
- `phase` — current phase of this plan: `plan`, `review`, `build`, `complete`
- `steps` — total number of implementation steps
- `priority_breakdown` — count of steps per severity level
- `reconciled` — whether the reconciler has processed this plan
- `amendments` — number of steps amended during reconciliation

The coordinator updates `plans_queue` after each phase transition. When going back on a single PRD, only that entry's phase resets — others are unaffected.

### Cross-Audit Contradictions

When recommendations from different audits contradict each other (e.g., an older audit's plan conflicts with a newer audit's findings):

1. **Same engagement, different clusters:** This is the standard reconciliation case described above. The reconciler resolves using the priority hierarchy.

2. **Different engagements, same URL:** The coordinator uses progress memory to detect this. If a previous engagement's plan was partially implemented and a new audit produces contradictory findings:
   - The new audit's findings take precedence (the page has changed since the old audit)
   - Note in reconciliation: "Previous engagement [ID] recommended [X] for [section]. Current findings show [Y]. Superseding with current recommendation."
   - Do NOT silently drop the old recommendation — document the contradiction

3. **Different devices, same engagement:** Desktop and mobile audits may produce contradictory guidance for the same element (e.g., desktop says "add whitespace around CTA" while mobile says "compact CTA area to fit above fold"). These are NOT conflicts — they are device-specific recommendations. The reconciler should:
   - Tag each recommendation with its device context
   - Ensure the implementation plan handles both viewports (e.g., responsive CSS that applies different spacing per breakpoint)
   - Only flag as a conflict if the recommendations cannot coexist via responsive design

### Common Conflict Patterns (Detailed)

**Color conflicts:** Plan A says "make CTA orange for contrast" while Plan B says "add green trust badge next to CTA." Resolution: check if orange CTA + green badge create a Christmas-tree effect. If so, adjust the trust badge to a neutral color (gray, white) or use an icon-only badge.

**Space conflicts:** Plan A says "add 4 trust badges below CTA" while Plan B says "increase whitespace around CTA by 40px." Resolution: the whitespace principle (232% conversion increase) is Gold-tier evidence. Place trust badges in a horizontal strip with reduced vertical padding, preserving the isolation effect while adding trust signals.

**Copy conflicts:** Plan A says "shorten product title for scannability" while Plan B says "add compatibility details to title for search/trust." Resolution: use the title for the short scannable version and add compatibility as a subtitle or badge below it. Both objectives can coexist.

**Layout conflicts:** Plan A moves the price above the CTA while Plan B adds BNPL messaging between price and CTA. Resolution: stack them — price → BNPL → CTA. Both plans achieve their goals without contradiction.

### Conflict Severity Classification

Not all conflicts need resolution. Classify each:

- **HARD conflict:** Plans propose mutually exclusive changes to the same element. Must resolve.
- **SOFT conflict:** Plans make assumptions about layout that are incompatible but can be reconciled with a compromise. Should resolve.
- **PSEUDO conflict:** Plans target the same area but their changes are actually compatible. Document as "reviewed, no conflict" in the No-Conflict Verification section.

Only HARD and SOFT conflicts appear in the Conflicts Found count. PSEUDO conflicts appear in No-Conflict Verification.

## Auto Mode

If the coordinator indicates `--auto` mode:
- Resolve all conflicts deterministically using the priority hierarchy
- For irreconcilable same-priority conflicts: use the cluster routing table tiebreaker
- Do NOT flag anything for user decision — resolve everything and document the reasoning
- **Exception: ethics violations cannot be auto-resolved.** If a step conflicts with the ethics gate, flag it as `[ETHICS-BLOCKED]` and remove it from the plan. The coordinator must surface this to the user even in auto mode.
- Tag auto-resolved irreconcilable conflicts with `[AUTO-RESOLVED]`

## Reconciler Retry

If the reconciler fails (crashes, returns malformed output, or does not end with `STATUS: COMPLETE`):
1. Retry once with the same inputs
2. If retry also fails: skip reconciliation, set `reconciled: false` in meta.json
3. Warn user at checkpoint: "Reconciliation failed — plans may contain cross-cluster conflicts. Review manually before building."
4. The build phase proceeds with unreconciled plans, but the builder should watch for visual clashes

End your output with:

```
STATUS: COMPLETE
```
