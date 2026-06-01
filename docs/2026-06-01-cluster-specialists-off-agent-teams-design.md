# Design — Migrate cluster specialists OFF Agent Teams (→ GA one-shot subagents)

- **Date:** 2026-06-01
- **Status:** DRAFT — design for review (precedes the implementation plan)
- **Decision provenance:** `docs/handoff-2026-06-01-migration-fixes-and-post-audit.md` §5b
  ("a decision, not a menu" — execute, don't re-litigate). Runtime path chosen this
  session: **#1 GA parallel one-shot subagents**.
- **Discovery basis:** read-only surface-map workflow `wf_e372b1ab-ec8` (5 Explore
  readers + synthesis) + dispatch-signature verification against
  `code.claude.com/docs` (sub-agents, tools-reference, v2.1.63 changelog).
- **Scope decision:** **Surgical + adjacent-correct** (flip + preserved loop +
  recovery change + counters/tests + spec-log + the 2 adjacent template-bug fixes;
  dead team machinery retained-and-annotated, not deleted).

---

## 1. Problem & why now

Cluster specialists are the **only remaining Agent-Teams teammate role in this
audit-only repo** (`skills/ecp/SKILL.md:29` confirms build/compare/quick-scan/resume
are out of scope; glob found only `skills/ecp/SKILL.md` + `skills/audit/SKILL.md`).
Agent Teams is an experimental feature (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`,
never GA) whose documented shutdown limitation is the `TeamDelete` "Cannot cleanup
team with N active members" hang we hit live, plus an idle-stream token cost. B0
fixed the *path-resolution symptom inside* teams; the feature itself stays fragile
and may not track the Opus 4.8 architecture. Removing it from the audit path retires
a standing reliability + cost liability that affects **every** audit run.

### Two findings that make this low-risk

1. **Subagent parity for specialists was already empirically validated.**
   `scripts/test-cluster-specialist-parity.py` (a Phase-H deliverable, 2026-04-28)
   diffed the *same* specialist prompt dispatched as subagent vs. teammate and
   classified output drift (PASS / PARTIAL / FAIL). The riskiest unknown — "do
   specialists degrade as subagents?" — is already answered.
2. **The one-shot infrastructure already exists and is tested for every other role.**
   `contracts/dispatch-contract.md` already defines a "Subagent dispatch contract
   (v2 default)" governing acquirer/ethics/synthesizer/planner/reviewer/builder, with
   failure-recovery-via-re-dispatch and `subagent_spawned_*` counters (+ backwards-
   compat aliases). Specialists were deliberately kept as the **lone teammate
   exception**. This migration = **remove the last exception**, reusing built machinery.

## 2. The verified dispatch signature

Tool name is **`Agent`** (renamed from `Task` in v2.1.63; `Task` remains a working
alias). It is the unified spawn tool — **omitting `team_name` yields an isolated
one-shot subagent** (fresh context, no mailbox, runs once, exits); passing `team_name`
(+ the experimental env flag) joins a persistent team. One-shot dispatch is **GA, no
env flag**. Concurrency = **multiple `Agent` calls in a single message**.

**Specialist dispatch — before → after:**

```
# BEFORE (teammate)
Agent(subagent_type="general-purpose", team_name="audit-{engagement-id}",
      name="specialist-{cluster}-{device}", model="sonnet", prompt=<rendered>)

# AFTER (GA one-shot subagent — same shape acquirer/ethics/synthesizer already use)
Agent(subagent_type="general-purpose", description="audit {cluster} {device}",
      model="sonnet", prompt=<rendered specialist-*.txt, absolute paths per B0>)
#  ↑ no team_name, no name. ALL requested clusters in one message (full-parallel default; see §3.2.1).
```

The rendered prompt is **unchanged** (B0 absolute-path expansion in
`scripts/test-specialist.py` already applies); only the wrapping tool-call params drop.

## 3. Design, by concern

### 3.1 Transport flip (core)
Specialists move from teammate → one-shot subagent, joining the existing "Subagent
dispatch contract" section rather than getting new dispatch prose. The per-role table
row flips; the now-obsolete "Why cluster specialists keep teammate status" rationale
is **rewritten** to "why specialists are one-shot subagents" (stateless, JSON-only,
zero peer coordination), explicitly **preserving** the file-presence
mechanics (transport-independent) while making concurrency caller-controlled
(§3.2.1). `skills/audit/SKILL.md` Phase-Order
**"Create team" step is deleted** for the audit path.

### 3.2 Preserved verbatim (the lead loop keys off files, not team state)
File-presence collection (`glob cluster-{cluster}-{device}.json`) ·
validate→autofix→re-dispatch · the prompt's JSON-only emission, "No coordination",
and write-scope · B0 absolute-path rendering · `cancel.flag` boundary + per-dispatch
checks · atomic writes (`scripts/assembly/atomic_write.py`) · `scripts/lead_prep.py`
build-canonical-frefs. **None of these depend on team transport** — they read/write
files on disk, which is exactly why the flip is safe. (Concurrency is the one loop
parameter that *changes* — see §3.2.1.)

### 3.2.1 Concurrency — full-parallel by default (CHANGED from wave-of-≤5)
**Decision (2026-06-01):** dispatch **all requested clusters at once** in a single
message by default, replacing the historical waves of ≤5. The cap addressed a failure
mode *separate* from Agent Teams, and it is cheap to retain as a fallback:

- **Two distinct historical failures, not one.** (a) The Agent-Teams shutdown hang
  (`TeamDelete` "cannot cleanup … active members") — the feature, now removed. (b) A
  **server-side concurrent-spawn rate limit** ("not your usage limit", spawns failing
  at 0 tokens at 8+ concurrent) that sank a 20-way fanout on slingmods `4a0721e9`
  (`dispatch-contract.md:96`, which itself calls the 5-cap **"operational, not
  architectural"**). The cap was about *spawn count*, not *teams* — so it could in
  principle still bite ~20 concurrent **subagents**.
- **Why full-parallel anyway:** that evidence is from 2026-05-27 and such limits drift;
  subagents may throttle differently; and the risk **scales with run size** — small
  test runs (a few clusters) are almost certainly fine, only big 10×2 ≈ 20-way
  comprehensive runs are exposed. Default-fast is the better dev-loop default.
- **Fallback knob (zero new speculative code):** the wave-batching logic already exists
  in the lead loop; retain it behind a **`--max-concurrent N` control, default =
  unlimited (all at once)**, documented like `--deep` in `contracts/flags.md`. If a run
  hits the throttle, `--max-concurrent 5` restores batched waves. "If it doesn't work
  out" is then a one-line default flip, not a re-architecture.
- **Workflow-forward:** concurrency is decided by the *caller*; specialists stay
  stateless + concurrency-agnostic. A future Dynamic Workflow wrapper (§8) would own
  concurrency via `pipeline()`/`parallel()` (cap ~16, queue the rest) with no specialist
  redesign.

### 3.3 The one real behavioral change — recovery delivery
Today a validation failure `SendMessage`s the still-alive teammate to fix in place.
A one-shot subagent has **already exited**, so recovery becomes **re-dispatch a fresh
subagent with the validation error embedded in the prompt** — the pattern the
synthesizer already uses (`--write-retry-prompt`) and that the "Subagent dispatch
contract → Failure recovery" section already specifies (retry once with error
embedded, then mark `partial`).

- `contracts/audit-reconciliation.md` Steps 0/0b/0c keep their **validation logic**
  (format / voice / evidence-anchor) and swap only the **delivery mechanism**
  (SendMessage bounce → fresh re-dispatch).
- **Decision (retry-prompt design):** reuse `specialist-prompt-v2.md` + add a
  `--write-retry-prompt <path>` flag to `scripts/test-specialist.py` mirroring the
  synthesizer's. **No new template.**
- **Semantic note:** the v1 "two-attempt SendMessage correction loop" collapses to
  "one autofix at validation → one fresh re-dispatch with error → `partial`". This is
  an intentional contract change, recorded here and in the spec-change-log.

### 3.4 Counters, determinism gate, tests
- Specialists increment **`subagent_spawned_specialists`**; `team_spawned_specialists`
  (and its v1 alias `team_spawned_auditors`) stay accepted as backwards-compat aliases.
  Both the counter and the alias rules **already exist** in
  `contracts/trace-assertion-canary.md`.
- `scripts/assembly/determinism_gate.py:parse_trace_assertions` gets the
  `subagent_spawned_specialists ↔ team_spawned_specialists` normalization so the
  structural canary accepts either as "specialists ran".
- **Tests — update:** `tests/test_v2_determinism_gate.py` and
  `tests/test_g24_trace_counters_reconcile.py` hardcode `team_spawned_specialists`;
  update to accept the subagent counter (via the alias normalization).
- **Tests — add-new:** (a) specialists dispatch as subagents (assert no `team_name`,
  `subagent_spawned_specialists ≥ expected`); (b) the `--max-concurrent` control is
  honored — default dispatches all requested clusters, `--max-concurrent N` caps the
  batch; (c) re-dispatch-with-error recovery works.
- **Tests — unchanged (stay green):** `test_b0_prompt_resolution.py`,
  `test_specialist_write_scope.py`, `test_prompt_template_completeness.py`,
  `test_lead_reflection_ownership_canary.py` — all transport-agnostic.
- **`scripts/test-cluster-specialist-parity.py`:** its job is done (parity proven);
  retain as archived historical evidence with a header note (don't delete, don't run
  in the gate).

### 3.5 Fixtures — alias-fallback, not hand-editing
The `audit-trace.log` fixtures (`fixtures/slingmods-pdp/`, `fixtures/awdmods-homepage/`,
`fixtures/2026-05-02-9cd2a2ac/`) encode `team_spawned_specialists`. **Decision:** keep
them as v1-legacy and rely on the backwards-compat alias (the canary already supports
this). **Regenerate from the next real audit**, not by hand-editing a trace (a
hand-edited trace would be fiction). This keeps archived traces readable and avoids
fabricating evidence.

### 3.6 Dead team machinery — annotate, don't delete
`contracts/team-lifecycle.md` (env-var hard-requirement + Resume team-recreation) goes
dead for the audit path but is **retained and clearly tagged** "audit-path dead
post-migration; live only for future multi-planner," because (a) multi-planner needs it
verbatim if it returns, and (b) it's a shared reference cited by the out-of-scope
build/compare/resume skills. The v1 `workflows/audit.md` huddle/handoff ceremony and the
v1 markdown auditor template in `dispatch-contract.md` stay as already-marked v1-legacy.

### 3.7 Adjacent template-bug fixes (folded in per scope decision)
`contracts/ethics-subagent-v2.md:16` and `contracts/synthesizer-v2.md:16` say "dispatch
via Agent tool" while the canonical `dispatch-contract.md` table marks them one-shot
subagents. These are pre-existing inconsistencies **in the exact class we're fixing**;
correct both to match the canonical contract (2 small edits).

### 3.8 Spec-change-log + docs
Touches the dispatch contract → a `product.md` §10 spec-change-log entry (B0/P1/#26
format) + a handoff note. Decision record already exists (handoff §5b).

## 4. File-change inventory (design altitude; exact lines pinned in the impl plan)

| File | Change | Class |
|---|---|---|
| `contracts/dispatch-contract.md` | Flip specialist row in per-role table + "How to dispatch" table; **rewrite** "Why specialists keep teammate status"; canonical counter → `subagent_spawned_specialists` (alias retained); full-parallel default + `--max-concurrent` fallback (supersedes the wave-of-5 cap text) | change |
| `contracts/specialist-prompt-v2.md` | Dispatch-shape line (~19): `Agent`+`team_name`+`name` → one-shot `Agent` (no team_name/name). "No coordination" stays | change |
| `skills/audit/SKILL.md` | Dispatch-Shape section: specialists = one-shot subagent; **delete** "Create team" Phase-Order step; dispatch default = all clusters at once, `--max-concurrent` fallback batching (supersedes hardcoded wave-of-5) | change |
| `contracts/audit-reconciliation.md` | Steps 0/0b/0c: SendMessage bounce → fresh re-dispatch with embedded error (validation logic unchanged) | change |
| `contracts/lead-discipline.md` | Acquisition/recovery prose: `Agent`+`SendMessage retry` → one-shot + fresh re-dispatch | change |
| `contracts/ethics-subagent-v2.md` | Line ~16 "Agent tool" → one-shot subagent (template-bug fix) | change |
| `contracts/synthesizer-v2.md` | Line ~16 "Agent tool" → one-shot subagent (template-bug fix) | change |
| `scripts/assembly/determinism_gate.py` | `parse_trace_assertions`: add `subagent_spawned_specialists ↔ team_spawned_specialists` normalization | change |
| `scripts/test-specialist.py` | Add `--write-retry-prompt`; docstring "Agent dispatch" wording | change |
| `contracts/flags.md` | Document `--max-concurrent N` (default = all), like `--deep` | change |
| `tests/test_v2_determinism_gate.py` | Accept subagent counter; + new subagent-dispatch guard | change / add |
| `tests/test_g24_trace_counters_reconcile.py` | Synthetic fixtures accept subagent counter | change |
| `contracts/team-lifecycle.md` | Annotate hard-requirement + Resume as "audit-path dead; multi-planner only" | annotate |
| `scripts/test-cluster-specialist-parity.py` | Archive header note (retain, don't run) | annotate |
| `product.md` §10 + handoff | Spec-change-log entry | doc |
| `test_b0_prompt_resolution.py`, `test_specialist_write_scope.py`, `test_prompt_template_completeness.py`, `lead_prep.py`, `atomic_write.py`, `multi-planner-protocol.md`, `relay-loop-protocol.md`, `cluster-migration.md` | **No change** (transport-agnostic / future-only) | preserve |

## 5. Test & verification plan

1. **Static:** `grep` confirms no `team_name`/`name=` in the specialist dispatch path;
   ethics/synthesizer templates match the canonical contract.
2. **Suite:** `python -m pytest tests/ -q` stays green (baseline 966) + the new guards.
3. **Determinism gate:** `python -m pytest tests/test_v2_determinism_gate.py -q` (37)
   green with the counter normalization.
4. **Live smoke (field test, may be a follow-up run):** a real `/ecp:audit` shows all
   requested specialists dispatched in one full-parallel batch, `subagent_spawned_specialists`
   non-zero, **zero** team creation / `TeamDelete`, `cluster-*-{device}.json` written, and
   validate→autofix→re-dispatch exercising the fresh-re-dispatch path. Confirms specialists
   no longer retry on *reference reads* — and surfaces the concurrent-spawn throttle early
   if it still exists (→ set `--max-concurrent 5`).

## 6. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Full-parallel default re-hits the server-side concurrent-spawn throttle on big ~20-way runs | `--max-concurrent N` fallback restores batched waves (one-line flip); risk scales with run size (small test runs unaffected); revisit the default if it recurs |
| Recovery path silently no-ops (SendMessage to a dead subagent) | Reconciliation rewrite routes failures to fresh re-dispatch; new recovery test |
| Archived/v1 traces fail validation | Backwards-compat alias retained indefinitely; canary already supports it |
| Accidentally flipping multi-planner to subagent | Keep the multi-planner teammate exception crystal-clear in the per-role table; it is the one role that *needs* `team_name` |
| Deleting team-lifecycle.md breaks future multi-planner / sibling skills | Retain-and-annotate (do not delete) |

## 7. Resolved questions (provisional → decided)

- **Dispatch signature:** `Agent`, no `team_name`/`name`, GA — *verified*.
- **Concurrency:** full-parallel by default; wave-batching retained behind
  `--max-concurrent N` (default = all) as the throttle fallback.
- **Fixtures:** alias-fallback now; regenerate from next live audit.
- **team-lifecycle.md:** retain + annotate.
- **Retry prompt:** reuse `specialist-prompt-v2.md` + `--write-retry-prompt`; no new template.
- **Resume coordinator:** none exists in this repo; audit resume is file-presence based — no breakage.
- **Multi-planner:** unchanged; keeps `Agent`+`team_name`; the env flag survives for it.

## 8. Out of scope (explicit) + future paths

**Out of scope now:** Live determinism N≥5 gate (handoff §C); regenerating fixtures via a
live run; the broad cosmetic `Task`→`Agent` rename across *other* roles' contract text;
migrating the out-of-repo build/compare/resume skills.

**Documented future path (build nothing now; don't fight it):** wrap specialist dispatch
in a **Dynamic Workflow** — a `pipeline()` fans out specialists and runs
validate→autofix→re-dispatch as stages with native concurrency, result caching, and
resume. The full-parallel + stateless-specialist design above is deliberately
workflow-ready: the wrapper would own concurrency with no specialist or contract
redesign. Dan wants to try this for the plugin, just **not in this migration**.
