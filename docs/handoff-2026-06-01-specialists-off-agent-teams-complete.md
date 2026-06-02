# Handoff — Cluster specialists migrated OFF Agent Teams → GA one-shot subagents (COMPLETE)

**Date:** 2026-06-01
**Status:** Implemented, verified, committed, and **pushed to `main`**. Test suite green.
**Decision record:** the prior handoff's §5b ("DECISION + EXECUTION: migrate cluster specialists OFF Agent Teams"), path #1 (GA parallel one-shot subagents).

---

## 1. TL;DR — what changed and where we are

The audit pipeline's **cluster specialists** (a.k.a. cluster auditors) used to be dispatched as **Agent-Teams teammates** — an experimental, never-GA feature with a documented shutdown bug (the "cannot cleanup team with N active members" hang) and a noisy idle-notification stream. This migration flips them to **GA parallel one-shot subagents** — the same dispatch shape the acquirer, ethics, and synthesizer roles already use. This was the **last** teammate role in the audit path, so the audit flow no longer creates a team at all.

The whole change is **safe** because the lead never relied on team state to collect specialist work: it finds completed clusters by **looking for their output files on disk** (a glob over the per-cluster emission filenames). That collection mechanism is transport-independent, so flipping the dispatch shape changes only two things — **how recovery is delivered** and **how concurrency is controlled**. Everything else in the lead loop is untouched.

**It is done and on `main`.** What remains is *runtime proof* (a live audit), not more editing — see §5.

---

## 2. What the migration actually did

**Transport flip.** Cluster specialists now dispatch as one-shot subagents via the Agent tool with `subagent_type="general-purpose"`, a short `description`, the model (`sonnet`, or `opus` with `--deep`), and the rendered prompt. **No team name, no teammate name, no team creation.** Every contract, skill, and rationale that described them as teammates was updated to say "one-shot subagent."

**Recovery change.** When a specialist's emission fails one of the lead's validation gates (format / voice / evidence-anchor), the old behavior bounced a correction message back to the still-alive teammate. Now the lead:
1. tries the automatic shape-repair (autofix) first,
2. if that still fails, generates a **retry prompt with the validation error embedded** (the split-mode harness has a `--write-retry-prompt` flag for this), and
3. **re-dispatches a brand-new one-shot subagent** with that prompt — the fresh subagent has no memory of the first attempt; it gets only the cluster content + the specific error.
4. On a **second** failure the cluster is marked `partial` and the run continues. No back-and-forth messaging with a long-lived agent.

**Concurrency change.** The old default was "spawn specialists in waves of ≤5" (a workaround for a server-side concurrent-spawn rate limit observed on 2026-05-27, where 8+ concurrent spawns failed at zero tokens). The new default is **full-parallel** — dispatch all requested clusters in one message. A new **`--max-concurrent N`** flag (default = unlimited) is the **escape hatch**: if the rate limit bites again, set `--max-concurrent 5` to restore batched waves. Full-parallel is the default; waves are recovery, not routine.

**Counter rename (with backwards compatibility).** The structural trace counter for specialists is now the canonical **`subagent_spawned_specialists`**. The two older names (`team_spawned_specialists` and the v1-era `team_spawned_auditors`) are **retained as accepted aliases — never remove them.** Old/archived trace files still validate.

**What was deliberately preserved (do NOT "finish migrating" these):**
- The **cancellation sentinel** (the cancel-flag protocol the lead checks at every layer boundary) — preserved verbatim apart from three terminology word-swaps.
- The **file-ownership / atomic-write / concurrent-audit-isolation** rules.
- **Multi-planner peers stay on Agent Teams.** They are the *one* role whose entire value is real-time peer-to-peer negotiation, which only teams provide. The Agent-Teams lifecycle reference was annotated "dead for the audit path, retained for a future multi-planner resume" — annotated, **not deleted**.

---

## 3. The runtime piece that made it actually work (important)

A green test suite proves the *edits* are correct. It does **not** prove specialists dispatch correctly at runtime, because the tests don't spawn live agents.

The single most important non-documentation change: the **audit-completion reconciliation canary** (the check that confirms "every role that should have run, ran") read the specialist count from a fixed tuple of counter names that only contained the *legacy* names. If left alone, a real v2 audit would write the *new* `subagent_spawned_specialists` counter, the canary would look for the old names, find zero, and **fail its own completion check** — falsely declaring "specialists never ran." Adding the canonical counter to that tuple is what lets a real run pass.

There are exactly **two** places in code that consume specialist counters, and **both** now accept the canonical name (one via alias-normalization, one via the canary tuple). That's the entire code surface — confirmed by searching the scripts directory for the counter names. So the code side is complete; the only thing untested is a real end-to-end run.

---

## 4. How it was built and verified

- **Method:** subagent-driven development — a fresh implementer agent per task, then independent spec + quality review, guard-tests-first (write the failing assertion, watch it fail, make the edit, watch it pass), and the **full suite green after every single commit**. One commit per task.
- **Consolidated guard tests:** all the new assertions live in one test module added for this migration (18 tests). They check the *contracts* — that the dispatch shapes, counters, recovery wording, and flag docs say what they should.
- **Final verification (actual output):** full suite **989 passed / 12 skipped**, the determinism-gate suite **37 passed**, the migration's guard module **18 passed**.
- **Notable things caught during execution** (worth knowing if you revisit the plan): three of the plan's own guard-test regexes were subtly wrong (they matched the wrong markdown-table column, or asserted "preserved" strings that actually lived inside the blocks being deleted); one task's prescribed replacement text contradicted its own guard test. Each was verified against the live files and corrected before landing. A few small internal contradictions the plan left behind (stale "teammate" cells in tables it was already editing) were fixed in the same commits.

---

## 5. Next steps (prioritized) — what's left to do

### 5.1 — Live audit smoke run (the real proof; highest priority)
Run a real audit against a live URL and confirm the migration behaves at runtime. Look for:
- **Zero team creation** — no team-create / team-delete calls anywhere in the run. The old shutdown-hang should be gone.
- **Specialists dispatched in one full-parallel batch** (all requested clusters at once), not in waves.
- The **`subagent_spawned_specialists`** trace counter is **non-zero** and matches the number of clusters dispatched.
- The per-cluster output files land on disk and the lead collects them by file presence.
- The **completion canary passes** (this exercises the §3 runtime change).
- **Exercise the recovery path at least once:** force or catch a validation failure on a cluster emission and confirm the lead generates a retry prompt and re-dispatches a *fresh* subagent (not a message bounce), and that a second failure marks the cluster `partial`.
- **Watch for the concurrent-spawn rate limit.** If you see spawns failing at zero tokens at high concurrency, that's the known server-side limit — set the new max-concurrent flag to 5 and re-run. If it recurs reliably, consider lowering the default, but only with that evidence.

A good target is a comprehensive run (all clusters, both devices) on a real store, since that's where the old waves-of-5 limit showed up.

### 5.2 — Regenerate the trace-log fixtures from a real audit
The test fixtures still contain **v1-legacy** trace logs (old counter names). That's intentional and fine — the alias normalization keeps them valid. But once you have a clean live v2 run (5.1), regenerate those fixtures **from the real audit output** (don't hand-edit them) so the fixtures reflect the new canonical counter going forward.

### 5.3 — Broad cosmetic tool-name cleanup (low priority, explicitly deferred)
Throughout the contracts, the unified spawn tool is referred to by both its current name and its legacy alias (the two are interchangeable). This migration **only** normalized the names on the cluster-specialist rows plus a single clarifying note; it deliberately did **not** sweep the other roles' contract text (acquirer / ethics / synthesizer / planner / reviewer / builder). Doing that broad rename later would also mop up the few residual "teammate"-flavored sentences left in the dispatch contract and the reconciliation contract (see §6). This is purely cosmetic — no behavior depends on it.

---

## 6. Known residuals (out of scope, intentionally left, documented)

These are stale-wording leftovers the migration deliberately did **not** chase, because the plan scoped terminology cleanups file-by-file and reserved the broad tool-name rename as a separate follow-up. None affect behavior; the tests are green:
- In the **dispatch contract**, the "subagent dispatch contract" subsection (about the *other* one-shot roles) still frames the spawn tool by its legacy name, and one sentence still references specialists needing "teammate shape." That subsection is the explicit out-of-scope area for the deferred rename.
- In the **reconciliation contract**, a few sentences around the validation gates still say "teammate," "two-attempt loop," and "third failure" — the surrounding recovery edits use the new "fresh re-dispatch / second failure" model, so these read slightly inconsistently. Worth aligning during the broad cleanup.
- The **anti-rogue lead rulebook** keeps two "teammate" mentions that are historical/illustrative (a "why this file exists" note and a verbatim quote of what a rogue lead *would* say) — correct to leave as-is.

If you do the 5.3 cleanup, knock these out at the same time.

---

## 7. How to verify on pickup (machine-agnostic)

From the repo root, after cloning on the new machine:

```
python -m pytest tests/ -q
```
Expect **989 passed, 12 skipped**. Then the two focused suites:
```
python -m pytest tests/test_v2_determinism_gate.py -q          # expect 37 passed
python -m pytest tests/test_specialist_subagent_dispatch.py -q  # expect 18 passed (this migration's guard module)
```

The full task-by-task record (commits, the controller interventions, and these follow-ups) lives in the migration plan's **"## Execution log"** section. The implementation plan and the original design doc sit alongside it in the docs directory.
