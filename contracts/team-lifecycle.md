# Agent Teams lifecycle

Canonical lifecycle contract for every ECP v5.0 skill that uses Claude Code's experimental Agent Teams feature (`/ecp:audit`, `/ecp:build`, `/ecp:compare`, `/ecp:resume`). `/ecp:quick-scan` intentionally does NOT use teams — it runs as a single-agent dispatch because quick-scan's value proposition is speed and quick-scan only ever has one auditor, so the team overhead would not pay for itself.

Prior to ECP v5.0.x this lifecycle prose was duplicated across four skill files with the hard-requirement env var check, the `TeamCreate` naming convention, and the create/populate/spawn/coordinate/cleanup step list all copy-pasted. This reference is the single source of truth.

## Hard requirement

Every skill that uses teams MUST check for the experimental env var at the start of every engagement:

```
If the TeamCreate tool is unavailable:
  Print: "ECP v5.0 requires the experimental Agent Teams feature.
          Add this to your ~/.claude/settings.json:
            \"env\": { \"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS\": \"1\" }
          Then restart Claude Code and try again."
  Abort.
```

This check happens at engagement setup, BEFORE any team operations. The absence of `TeamCreate` on the tool roster is the signal — don't rely on reading the env var directly from `settings.json`, check the tool availability itself.

## Team naming convention

| Skill | Team name | Example |
|---|---|---|
| `/ecp:audit` | `audit-{engagement-id}` | `audit-2026-04-08-a3f7b1c2` |
| `/ecp:build` | `build-{engagement-id}` | `build-2026-04-08-a3f7b1c2` |
| `/ecp:compare` | `compare-{engagement-id}` | `compare-2026-04-08-a3f7b1c2` |

On resume, the coordinator recreates the team using the same naming convention — see the Resume section below.

## Generic lifecycle (audit, build, compare)

Every team-based engagement follows this pattern. Skill-specific steps (which teammates to spawn, in what order, with what blocking) are documented in each skill's `<phase_*>` sections.

1. **Create** — Call `TeamCreate` at the start of the engagement, **immediately after engagement setup and BEFORE any teammate is spawned**. The first teammate (acquirer for audit/compare, planner for build) requires the team to exist. For `/ecp:audit` this is the hard wall enforced by `<acquisition_must_spawn_teammate>`: no team = `TeamCreate` now, not "no team = give up and do it yourself."
2. **Populate task list** — `TaskCreate` for every phase task upfront, not just the first phase. Audit: acquirer × devices, cluster × devices, reconcile, plan, review, build. Build: plan → review → build with `blockedBy` dependencies. Compare: paired per-page auditors + reconcile + compare. Upfront creation matters — an empty `audit-*` task slot is a missing teammate commitment, not a "to-do later" note. See skill-specific `<engagement_setup>` for the exact task count formula.
3. **Spawn teammates** — Use the `Agent` tool with explicit `team_name`, `name`, and `model` parameters. **Model MUST be explicit on every spawn; do NOT inherit from parent.** See `skills/audit/SKILL.md` `<auditor_dispatch_template>` for the canonical dispatch contract and per-role model assignments (sonnet default for mechanical work, opus for synthesis/review, `--deep` flag to upgrade cluster auditors + builder to opus).
4. **Coordinate** — Teammates self-claim their task via `TaskUpdate` on startup and mark it complete when done. Teammates can `SendMessage` each other for cross-cluster synthesis hints, peer planner negotiation, or Q&A routed through the lead. The legacy nonce relay loop is gone — there are no nonces, no `QUESTION__{nonce}:` regex parsing, no stdout markers. Messages arrive natively through the team mailbox. See `contracts/relay-loop-protocol.md` for the old-vs-new comparison.
5. **Lead waits** — The team-lead waits for task completion notifications, which arrive automatically through the team mailbox. No polling loop. No stdout watching.
6. **Validate / Reconcile** — As each cluster file arrives, the lead runs format validation (audit) or paired reconciliation (compare). Non-compliant files bounce back to the teammate via `SendMessage`. See `<finding_reconciliation>` in the audit skill.
7. **Phase transitions** — For sequential phases (plan → review → build), the lead waits for each phase's task to complete before spawning the next phase's teammate. Phase tasks are created upfront in step 2 with `blockedBy` dependencies, so the lead just watches for the current phase to unblock the next.
8. **Cleanup** — After the entire engagement lifecycle completes AND all checkpoints are accepted, call `TeamDelete` to remove the team metadata. The engagement directory in `docs/ecp/{engagement-id}/` and all its artifacts persist — only the transient team state is cleaned up.

## Skill-specific notes

### `/ecp:audit`

The audit pipeline is the most complex consumer of teams. Cluster auditors spawn in parallel (up to 12 at once for dual-device 6-cluster runs), reconciliation is file-based with lead-as-validator, and the forensic audit-trace.log assertions make rogue runs detectable in 2 seconds. See `<team_lifecycle>` in `skills/audit/SKILL.md` for the full steps list with every cross-reference to other sections. The assertion counters (`team_spawned_acquirers`, `team_spawned_auditors`, `cluster_files_written`, `ethics_gate_executed`) are the contract — they must be non-zero at audit completion or the run is structurally invalid.

### `/ecp:build`

Build is inherently serial (plan → review → build), so the team's value is consistent state management and a clear task list, not parallelism. Phase tasks are created upfront with `blockedBy` dependencies. For multi-planner mode, the `plan` task expands into parallel `plan-{cluster}` tasks; peer-to-peer negotiation between planner teammates (via SendMessage) handles cross-cluster overlaps during planning. A reconciler teammate is spawned only if peer negotiation deadlocks — see `skills/build/SKILL.md` `<phase_plan>` and `contracts/multi-planner-protocol.md` for the canonical protocol.

### `/ecp:compare`

Compare runs paired audit tasks for two pages inside a single team. Cluster auditors for both pages run in parallel (4 clusters × 2 pages × 1 device = 8 auditor teammates; double for dual-device). Per-cluster synthesis hints can cross page boundaries via `SendMessage`. After both pages' cluster files are reconciled into per-page `audit.md` files, the lead runs the compare workflow against both reconciled audits.

### `/ecp:quick-scan`

Quick-scan intentionally does NOT use teams. It's a single-agent dispatch for a single-cluster 3-5 finding scan — the team setup/teardown overhead would exceed the actual work. Quick-scan is the one ECP v5.0 command that runs without `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` set.

## Resume (team recreation from filesystem state)

v4.x engagements have no team state on disk (teams didn't exist in v4.x). On resume, the coordinator:

1. **Verifies Agent Teams is enabled** per the hard requirement above. Abort with the same error if not.
2. **Recreates the team** with the same naming convention as the original engagement (`audit-{id}`, `build-{id}`, `compare-{id}`).
3. **Rebuilds the task list from filesystem state**:
   - Mark phases with existing output files as `complete` (e.g., `audit.md` exists → audit phase done).
   - Mark the next phase's task as `pending` and ready to spawn its teammate.
   - For audit engagements with partial cluster coverage: read which `cluster-{cluster}-{device}.md` files exist; mark those tasks complete; mark missing ones as pending and re-spawn auditors for them only.
   - For multi-planner build engagements: rebuild per-cluster plan tasks based on `plans_queue` state (post-cluster-migration translation).
4. **Resumes from the last incomplete task.** If the last phase ended at a checkpoint (e.g., audit complete awaiting plan confirmation), present the checkpoint to the user before spawning the next phase's teammate.

v4.x resume-time engagements also need cluster name translation applied before any filesystem lookups — see `contracts/cluster-migration.md`.

## Why teams (not isolated subagents)

The Phase 4 conversion replaced isolated-subagent dispatch with team-based dispatch for four reasons:

1. **Shared task list** — the user sees progress across phases as a unified list rather than "which subagent am I waiting on right now?"
2. **Shared state** — `~/.claude/teams/{team}/config.json` persists across teammate spawns, so restartable
3. **Native Q&A** — `SendMessage` replaces the legacy nonce relay loop (`QUESTION__{nonce}:` stdout regex parsing), eliminating ~80 lines of brittle parser code and the entire class of nonce mismatch bugs
4. **Parallel synthesis** — cluster auditors can send `SYNTHESIS_HINT` messages to peers across clusters, something isolated subagents couldn't do without round-tripping through the lead

The tradeoff is the hard requirement on the experimental env var. Quick-scan intentionally opts out to preserve its "works without team setup" simplicity.
