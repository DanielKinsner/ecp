# Multi-Planner Protocol (Team-Based Peer Negotiation)

When an audit produces findings that are numerous and naturally cluster into distinct areas, the lead spawns parallel planner teammates — one per cluster — instead of a single planner. Phase 4 (April 2026) replaced the previous architecture (parallel subagents + standalone reconciler) with peer-to-peer SendMessage negotiation between planner teammates. The reconciler role is now optional and only triggered when peer negotiation deadlocks.

## Trigger Criteria

Use multi-planner mode when findings meet BOTH conditions:
- **3 or more clusters** produced findings (clusters are from the 10-cluster system: visual-cta, trust-credibility, pricing, checkout-flows, performance-ux, product-media, category-navigation, content-seo, post-purchase, audience)
- **Each cluster has 5+ findings** of its own

If either condition is not met, use single-planner mode (one planner teammate receives all findings).

This is guidance, not a rigid rule. If findings are numerous but all concentrated in one cluster, a single planner is more appropriate regardless of total count.

## Dispatch

1. Group audit findings by the source cluster that produced them
2. **Create one task per cluster** on the team task list:
   ```
   TaskCreate:
     subject: "Plan phase — {cluster} cluster"
     description: "Produce focused plan for {cluster} findings, negotiate cross-cluster overlaps with peer planners via SendMessage"
   ```
3. **Spawn N parallel planner teammates IN PARALLEL** (single message, multiple Agent tool calls):
   - Name: `planner-{cluster}` (e.g., `planner-pricing`, `planner-trust-credibility`)
   - `team_name`: `audit-{engagement-id}` (the existing audit team)
   - `model: "opus"` (mandatory, explicit, do NOT inherit from parent)
   - Each planner receives: its cluster's findings only + ethics gate + conflict resolution rules + context.md + contracts/multi-planner-protocol.md (this file) + the list of peer planner names from the team config
4. Each planner writes its output to `plan-{cluster-slug}.md` (e.g., `plan-visual-cta.md`, `plan-trust-credibility.md`)

**Planner retry:** If a planner fails (TaskUpdate with status note FAILED), the lead SendMessages it with corrective input and asks for a retry. If a second attempt also fails, proceed without that cluster's plan and note the gap at the checkpoint. Do NOT respawn a fresh teammate — message the existing one.

## Peer-to-Peer Negotiation (replaces standalone reconciler)

Cross-cluster conflicts and overlaps are resolved DURING planning by direct messaging between planner teammates. No separate reconciler agent is dispatched in the common case.

**When to send a peer message:**

A planner sends a SendMessage to a peer when its plan is about to recommend a change that touches the same DOM region or element as another cluster's likely concern. Example:

```
SendMessage to "planner-trust-credibility":
"Hey planner-trust-credibility, I (planner-pricing) am about to recommend
showing the shipping cost in the cart drawer for finding F-04 (unexpected
cost reveal). The cart drawer is also where trust badges + payment-method
icons live, so this overlaps your territory. Want to align on a single
combined recommendation? My current draft is: [X]. What's your draft?"
```

**The receiving peer:**

1. Reads the message
2. Checks if its draft plan touches the same area
3. Either:
   - Replies "I agree, your version covers it. I'll drop my standalone version and reference yours."
   - Replies "I have a different angle — here's mine: [Y]. Let's merge into [Z]."
   - Replies "These are independent — I'm flagging the trust badges, you're flagging the cost reveal. Two separate recommendations is correct."
4. Both peers update their drafts based on the agreement and continue

**Negotiation cap:** Maximum 3 messages per peer pair per session. If three rounds don't reach agreement, declare deadlock and flag for the optional reconciler step (see below). Most conflicts resolve in 1-2 messages.

**Async safety:** Peer messages may arrive while a planner is mid-thought. The receiving teammate should finish its current sentence/section before responding to the message. Don't interrupt your own reasoning to handle a message — finish the current item, then check the inbox.

## Optional Reconciler (deadlock resolution only)

The standalone `reconciler` teammate is only spawned when peer negotiation fails to resolve a conflict. Trigger conditions:

- 2+ planners reach the 3-message cap on a peer pair without agreement, OR
- A planner SendMessages the lead with `RECONCILER NEEDED: {description}` when it detects an irreducible conflict

When triggered, the lead:

1. Creates a `Reconciliation` task on the team task list
2. Spawns a `reconciler` teammate (`model: "opus"`)
3. Reconciler reads ALL plan-{cluster}.md files + audit.md + ethics-gate.md + contracts/conflict-resolution.md + the deadlock summary
4. Reconciler writes amended plan steps back to the affected plan-{cluster}.md files
5. Reconciler writes `reconciliation.md` to the engagement directory documenting what was changed and why
6. Reconciler TaskUpdate completed, SendMessages lead

**In the common case, no reconciler runs.** Peer negotiation handles 80-90% of conflicts directly. The reconciler is the safety net for the hard 10%.

If reconciler is also unsuccessful (or fails entirely): plans proceed unreconciled. Warn user at the checkpoint with a list of unresolved conflicts.

## Checkpoint

Present the multi-planner checkpoint:

```
Your audit produced [N] findings across [M] areas. Separate action plans created:
1. [Cluster Name] ([N] steps) — [priority breakdown]
2. [Cluster Name] ([N] steps) — [priority breakdown]
3. [Cluster Name] ([N] steps) — [priority breakdown]

[If reconciler amended steps: "Reconciler resolved N cross-plan conflicts. See reconciliation.md for details."]

Options:
1. Build all sequentially (recommended order: [priority-sorted list])
2. Pick one to start
3. Deepen a specific plan
4. Save all and resume later
```

**If --auto:** select option 1 (build all in recommended priority order). Skip checkpoint.

## Sequential Review/Build

After the user picks an order (or --auto selects priority order):

1. Set `current_plan` in meta.json to the first cluster slug
2. Run the full review → build cycle for that PRD using **per-PRD reviewer and builder teammates**:
   - Spawn reviewer teammate named `reviewer-{cluster}` (e.g., `reviewer-pricing`) with `model: "opus"`
   - Reviewer receives only that PRD's plan + audit findings + context
   - Reviewer uses the team-based Q&A protocol (see contracts/relay-loop-protocol.md) — SendMessage for questions, no nonces
   - After review, spawn builder teammate named `builder-{cluster}` with `model: "opus"`
   - Builder receives only that PRD's plan + review notes + context
   - Builder uses the team-based Q&A protocol
3. After build completes, update that PRD's entry in `plans_queue` to `phase: "complete"`
4. Present a mini-checkpoint: "PRD [cluster] complete. Continue to next, or stop here?"
5. If --auto: continue to next PRD automatically
6. Repeat for each PRD in order

**Reuse vs respawn:** Each PRD gets its OWN reviewer and builder teammate (named with the cluster suffix). Do NOT reuse a single `reviewer` teammate across multiple PRDs — each teammate's context is scoped to one cluster's plan, and reusing would leak context between PRDs.

## File Naming

Multi-planner mode uses `{phase}-{cluster-slug}` naming. Cluster slugs come from the 10-cluster system (v5.0+):

```
plan-visual-cta.md
plan-trust-credibility.md
plan-pricing.md
plan-checkout-flows.md
plan-performance-ux.md
plan-product-media.md
plan-category-navigation.md
plan-content-seo.md
plan-post-purchase.md
plan-audience.md
reconciliation.md
review-visual-cta.md        (written during that PRD's review cycle)
build-log-visual-cta.md     (written during that PRD's build cycle)
```

The suffixed variants share the same format as their unsuffixed parents — differing only in filename. The canonical format lives in `${CLAUDE_PLUGIN_ROOT}/workflows/plan.md`, `${CLAUDE_PLUGIN_ROOT}/workflows/review.md`, and `${CLAUDE_PLUGIN_ROOT}/workflows/build.md` respectively.

## meta.json State

Multi-planner adds these fields:

```json
{
  "plans_queue": [
    {"cluster": "visual-cta", "file": "plan-visual-cta.md", "phase": "complete"},
    {"cluster": "trust-credibility", "file": "plan-trust-credibility.md", "phase": "reviewing"},
    {"cluster": "pricing", "file": "plan-pricing.md", "phase": "pending"},
    {"cluster": "performance-ux", "file": "plan-performance-ux.md", "phase": "pending"}
  ],
  "reconciled": true
}
```

Valid phases per entry: `pending`, `reviewing`, `building`, `complete`, `failed`

**Derived fields (not stored, computed at read time):**
- `current_plan` = first entry whose phase is not `pending` or `complete`
- Top-level `phase` = derived from queue state (e.g., if any entry is `reviewing`, top-level is `review`)

**Self-healing:** If `plans_queue` phase and file existence disagree, file existence wins. Resume and go-back protocols should verify filesystem state.

## Go-Back Protocol

- **Going back on active PRD:** delete only that PRD's downstream files (e.g., `review-{slug}.md`, `build-log-{slug}.md`). Verify file paths are children of the engagement directory before deletion. Reset that entry's phase in `plans_queue`.
- **Going back to audit:** delete ALL PRD files, reconciliation.md, and all downstream files. Reset plans_queue to empty. Re-run audit.
- **Order:** delete files FIRST, then update meta.json. If deletion fails partway, meta.json still reflects the previous (correct) state.
