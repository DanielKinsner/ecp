# Go-back protocol

Procedure for reverting to a previous phase when the user chooses "go back" at a checkpoint.

**Why this file exists:** The go-back protocol is shared across `/ecp:audit` and `/ecp:build`. Prior to extraction, the audit skill owned the procedure and the build skill referenced it via "Same as /ecp:audit". This file is the single canonical source.

**Read this file when:** you are any `/ecp:*` skill coordinator and the user chooses to go back to a previous phase at a checkpoint.

---

## Atomicity rule

**Delete files FIRST, then update meta.json.** If deletion fails partway, meta.json still reflects the previous (correct) phase. Resume can detect and self-heal from inconsistent state.

## Single-planner mode

1. Delete downstream phase files (e.g., going back to audit deletes plan.md, review.md, build-log.md)
2. Update meta.json: phase -> target phase, updated -> current ISO timestamp
3. If builder has modified files: warn user about code divergence, suggest git restore
4. Re-dispatch target phase with fresh agents

## Multi-planner mode

- **Active PRD** = the `plans_queue` entry whose phase is furthest along (review > plan > pending). If multiple PRDs share the same phase, the one whose `file` was most recently modified is active. When the user says "go back" without specifying, operate on the active PRD.
- Going back on active PRD: delete only that PRD's downstream files (review-{slug}.md, build-log-{slug}.md). Verify file paths are children of the engagement directory before deletion. Reset that entry's phase in plans_queue.
- Going back to audit: delete ALL plan-*.md, review-*.md, build-log-*.md, and reconciliation.md. Reset plans_queue to empty. Update meta.json phase.
- See `${CLAUDE_PLUGIN_ROOT}/contracts/multi-planner-protocol.md` for details.

## Invariant

If meta.json phase and file existence disagree, file existence wins. This is how resume self-heals.
