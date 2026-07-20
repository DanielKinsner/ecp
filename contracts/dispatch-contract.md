# Auditor dispatch contract

Canonical reference for spawning teammates and subagents across all ECP skill coordinators. Contains per-role model assignments, the explicit-model rule, the `--deep` escape hatch behavior, the **v2 dispatch shape policy** (Phase H, 2026-04-28: subagent vs teammate per role), the cluster-auditor (v1 / v2-cluster-specialist) prompt template, and the subagent dispatch contract for the v2-flipped roles.

**Why this file exists:** Prior to Round 12, the dispatch template + model selection rules lived inside `skills/audit/SKILL.md` and `/ecp:build`, `/ecp:compare`, and `/ecp:quick-scan` all deferred to "See `/ecp:audit` `<auditor_dispatch_template>`" for their own spawning logic. That meant those 3 sibling skills had to load the full audit skill (~1500 lines) just to read 100 lines of dispatch rules, AND any change to the rules had to propagate by hand. Round 5 added `--deep` to audit + build but missed compare + quick-scan until Round 9 caught the drift via the addendum review. This file resolves the coupling — dispatch is a first-class canonical reference, no skill owns it.

**Read this file when:** you are the coordinator (lead) of any `/ecp:*` skill that spawns teammates or subagents. That's audit, build, compare, and quick-scan. The audit lead reads this when spawning acquirer (subagent in v2), cluster specialists (subagent), ethics (subagent), synthesizer (subagent), planner/reviewer/builder (subagents in v2). Compare and quick-scan use the same shape per their skill-specific notes below.

**Do NOT read this file if you are a teammate or subagent.** They don't spawn sub-roles — they execute a single task. Workflow / specialist-prompt files contain their own instructions, not this dispatch contract.

---

## The explicit-model rule (MANDATORY)

You MUST pass the `model` parameter explicitly on every single `Agent` tool call. Do NOT rely on parent inheritance.

**Why explicit over inherited:**
- Parent inheritance is silent — if the parent is opus and the spawn doesn't specify, the teammate silently runs on opus even when the spec says sonnet.
- Explicit is auditable — `grep -n 'model: ' skills/ workflows/` gives you the complete dispatch ledger. Inherited is invisible.
- Explicit defends against Round 9's class of bug — where skills shipped with opus hardcoded as the default and nobody noticed until a review pass grepped for it.

**This rule has no exceptions.** Every Agent tool call in every skill passes `model: "sonnet"` or `model: "opus"` inline. If you find yourself reasoning "the parent is already X, it'll inherit," stop — pass it explicitly.

---

## Path resolution contract (MANDATORY)

The lead MUST ensure teammates receive **absolute paths** in their dispatched prompts. Claude Code does **NOT** expand `${CLAUDE_PLUGIN_ROOT}` inside spawned-teammate (Agent/Task) prompts — a teammate `Read` of a literal `${CLAUDE_PLUGIN_ROOT}/...` path returns "File does not exist" (B0). The variable is therefore expanded **at render time** by `scripts/test-specialist.py` (`render_prompt` / `render_synthesizer_prompt` substitute `${CLAUDE_PLUGIN_ROOT}` → repo root), so the rendered `docs/ecp/{id}/.prompts/specialist-*.txt` and `synthesizer.txt` carry real absolute paths. The lead dispatches that rendered `.txt` verbatim as the Agent/Task `prompt` and MUST NOT reintroduce the literal variable into a dispatched prompt.

---

## Per-role model + dispatch-shape assignments (canonical, Phase H 2026-04-28)

| Role | Default model | With `--deep` | v2 Dispatch shape | Rationale |
|------|--------------|---------------|-------------------|-----------|
| Acquirer | `sonnet` | `sonnet` (unchanged) | **subagent** (Task tool, no team_name) | Mechanical task — navigate, screenshot, extract DOM, write baton. No synthesis needed. No peer coordination. Subagent eliminates an idle-notification stream the lead never reads. |
| Cluster specialist (a.k.a. cluster auditor) | `sonnet` | `opus` | **subagent** (Agent tool, no team_name) | Coverage work — read reference files, apply principles to page, emit JSON-only emission. **Runs on `sonnet` (Sonnet 5) by default (2026-07-20):** Sonnet 5 clears the schema/format/voice bar the four reconciliation guardrails enforce, at lower latency and cost than opus. `--deep` upgrades specialists to `opus` for complex pages (the original pre-2026-06-02 escape hatch, restored). One-shot dispatch (no team_name); file-presence glob determines missing clusters at resume. v2 specialists do NOT peer-coordinate (no SendMessage, no huddles) — see `contracts/specialist-prompt-v2.md` "## No coordination" section. |
| Ethics subagent | `sonnet` | `opus` | **subagent** (Task tool, no team_name) | Layer 1.5 in v2 — runs after specialists, before synthesizer. Single-pass page-scope emission. No peer coordination, no shared workspace need beyond writing one JSON file. See `contracts/ethics-subagent-v2.md`. |
| Lead (coordinator) | `opus` | `opus` (unchanged) | n/a — IS the lead | Reconciliation, dedup, Priority Path synthesis, ethics gate processing. The synthesis brain stays on opus. |
| Synthesizer | `opus` | `opus` (unchanged) | **subagent** (Task tool, no team_name) | Layer 3 prose writer. Runs once per engagement, single dispatch with the full canonical-f_refs manifest + cluster emissions trimmed. No peer coordination. See `contracts/synthesizer-v2.md`. |
| Planner | `opus` | `opus` (unchanged) | **subagent** (Task tool, no team_name) | Strategic prioritization across 30+ findings is reasoning-heavy. Single-pass dispatch reading audit.md + plan template. SendMessage Q&A loop replaced by inline lead-presents-checkpoint flow in v2. |
| Reviewer | `opus` | `opus` (unchanged) | **subagent** (Task tool, no team_name) | Critical evaluation and blocking Q&A. Subagent shape with one-shot dispatch; lead surfaces any reviewer questions inline at checkpoint_review. **Do NOT downgrade model.** |
| Builder | `sonnet` | `opus` | **subagent** (Task tool, no team_name) | Code writing is mechanical for most changes. Use opus only on complex refactors or client-facing builds. Subagent shape; lead surfaces builder questions inline at checkpoint_build. |
| Multi-planner peers | `opus` each | `opus` (unchanged) | **teammate** (Agent + team_name) | Cross-cluster negotiation benefits from reasoning depth AND from peer-to-peer SendMessage during planning per `contracts/multi-planner-protocol.md`. Multi-planner is the ONLY non-specialist role that retains teammate status — the SendMessage peer negotiation is the entire point. |

**The `--deep` escape hatch:** `--deep` upgrades the **cluster specialists, ethics subagent, and builder** from `model: "sonnet"` to `model: "opus"`. Everything else stays on its default (acquirer stays sonnet; lead/planner/reviewer/synthesizer stay opus). The flag is a single decision point at the top of the skill — the lead reads `--deep` from the arguments and applies it uniformly. See `${CLAUDE_PLUGIN_ROOT}/contracts/flags.md` for the full `--deep` flag documentation.

---

## Why cluster specialists run on Sonnet 5 — and the guardrails that keep output honest

As of 2026-07-20, cluster specialists default to **`sonnet`** (Sonnet 5). Sonnet 5 clears the schema/format/voice bar with negligible drift, at lower latency and cost than opus, so it is the right default for routine coverage work. `--deep` upgrades specialists to **opus** for complex pages (a configurator, a heavily-designed landing page, a site a prior sonnet run missed subtle findings on) — the original pre-2026-06-02 escape hatch, restored. The **builder** also defaults to sonnet (and upgrades on `--deep`), so the guardrails below — built to make a sonnet specialist safe — remain in force for both roles.

Earlier in this release cycle (2026-04-07 awdmods test), an older Sonnet drifted on FINDING block format — 5 of 10 auditors wrote `### F-SEO-XX` headings instead of code-fenced blocks. That drift is caught by **four reinforcing guardrails**:

1. **Lead-as-validator format check** in `${CLAUDE_PLUGIN_ROOT}/contracts/audit-reconciliation.md` Step 0 — reads each cluster file as it arrives, bounces non-compliant files back via a fresh re-dispatch with corrective instructions.
2. **Lead-as-validator voice check** in `${CLAUDE_PLUGIN_ROOT}/contracts/audit-reconciliation.md` Step 0b (added in Round 14) — catches client-tone drift (jargon, compliance-speak, citation-only Why-this-matters) before reconciliation.
3. **Forensic assertion canary** — surfaces silent format failures in the numerical counters at audit completion. See `${CLAUDE_PLUGIN_ROOT}/contracts/trace-assertion-canary.md`.
4. **Explicit format examples in `workflows/audit.md` Step 4a + worked voice examples in Step 4b/4c** — the specialist follows concrete examples better than prose descriptions.

If a page needs the strongest reasoning signal, pass `--deep` to route specialists to opus; the guardrails above hold on either model.

---

## When to pass `--deep` / opus

Pass `--deep` (and therefore use opus for the **cluster specialists, ethics subagent, and builder**) when:

- **The page is complex** — configurator, multi-step checkout, heavily-designed landing page, React SPA with late hydration, a site you've already audited and sonnet missed subtle findings on.
- **The output will go directly to a client** and quality signal matters more than cost.
- **You're iterating on the spec** and want the strongest baseline for A/B comparison between runs.

Otherwise, omit `--deep`: the cluster specialists, ethics subagent, and builder run on sonnet (Sonnet 5). The lead, planner, reviewer, synthesizer, and multi-planner peers stay on opus either way.

See `${CLAUDE_PLUGIN_ROOT}/contracts/trace-assertion-canary.md` "Cost trace heuristic" for the exact per-role token multipliers that quantify the savings.

---

## v2 Dispatch shape policy (Phase H — 2026-04-28)

v2 flips the v1 default. **Most roles dispatch as one-shot subagents (Agent tool, no team_name); only multi-planner peers remain teammates** (Agent tool with team_name). Cluster specialists are one-shot subagents (no team_name).

### What changes for the lead

| Concern | v1 (teammate everywhere) | v2 (subagent default + teammate exceptions) |
|---|---|---|
| `idle_notification` stream | One per teammate per layer (~70 across acquire → specialists → ethics → synthesize → render) | One per remaining teammate (multi-planner peers only, and only during planning); **~0 in a standard audit** |
| Lead context tokens spent on idle pings | Significant — each idle ping is a context entry the lead reads through | Order-of-magnitude smaller |
| Peer coordination via SendMessage | Used in v1 cluster huddles + handoff broadcasts (now unused) | Used only by multi-planner peers per `contracts/multi-planner-protocol.md` |
| TaskCreate/TaskUpdate ledger | Every teammate claims + completes a task | Multi-planner peers only |
| Failure recovery | Lead re-spawns failed teammate via `SendMessage` retry, OR creates a new teammate name | Lead re-dispatches subagent via fresh Task call (no shared task state to clean up) |
| Output workspace | Cluster specialists share `docs/ecp/{engagement_id}/` and rely on deterministic `cluster-{cluster}-{device}.json` naming | Same — cluster specialists are one-shot subagents that still write to the shared engagement directory; the lead merges by deterministic file name |

### Why specialists are one-shot subagents

Cluster specialists share an engagement directory (`docs/ecp/{engagement_id}/`) and the lead merges their outputs by deterministic file name (`cluster-{cluster}-{device}.json`). One-shot subagent dispatch (no team_name) provides:

1. **Full-parallel fanout with concurrency control** (default = unlimited, fallback `--max-concurrent N` flag): the lead collects via filesystem glob and dispatches all missing clusters in one message. **Default behavior:** dispatch all requested cluster specialists in parallel (no artificial waves). **Rate-limit fallback:** if the dispatcher hits transient server-side rate limits ("not your usage limit"), the lead can re-dispatch in waves via `--max-concurrent N` (e.g., `--max-concurrent 5` to batch in waves of 5). The 2026-05-27 batch discovered this limit at 8+ concurrent spawns — Amazon engagement `0669899d` saw 7 of 8 spawns fail at 0 tokens; slingmods `4a0721e9` lost the entire first 20-way fanout and recovered via waves of ~5. Full-parallel is the default; the `--max-concurrent` flag exists for rate-limit recovery, not routine use. See `contracts/flags.md` for the `--max-concurrent` contract.
2. **Restart-friendly file-presence model.** If the lead resumes mid-run, it reads which `cluster-*-{device}.json` files are already on disk and re-dispatches only the missing ones. File presence is the truth; the subagent does not rely on a task-list record.
3. **No coordination ceremony.** v2 specialists do NOT SendMessage anyone, do NOT broadcast intent, do NOT propagate SYNTHESIS_HINT. See `contracts/specialist-prompt-v2.md` "## No coordination" section. One-shot subagent shape eliminates the idle-notification stream.

### Why multi-planner peers keep teammate status

Multi-planner is the one role where SendMessage peer negotiation is the WHOLE POINT — `contracts/multi-planner-protocol.md` describes peers reaching shared decisions in real time during planning. That coordination is impossible to replicate via subagent shape, so multi-planners stay teammates with active peer messaging.

### How to dispatch each role in v2

| Role | Template / prompt source | Tool call |
|---|---|---|
| Acquirer | `workflows/acquire.md` | `Task(subagent_type="general-purpose", model="sonnet", prompt=<acquire workflow>)` |
| Cluster specialist | `contracts/specialist-prompt-v2.md` (with per-cluster params from `contracts/specialists/{cluster}.md`) | `Agent(subagent_type="general-purpose", description="Audit {cluster} cluster", model="sonnet", prompt=<rendered template>)` |
| Ethics subagent | `contracts/ethics-subagent-v2.md` | `Task(subagent_type="general-purpose", model="sonnet", prompt=<rendered ethics template>)` |
| Synthesizer | `contracts/synthesizer-v2.md` | `Task(subagent_type="general-purpose", model="opus", prompt=<rendered synthesizer template with canonical_f_refs_manifest>)` |
| Multi-planner peer | `contracts/multi-planner-protocol.md` | `Agent(subagent_type="general-purpose", team_name="audit-{engagement_id}", name="planner-{cluster}", model="opus", prompt=<plan scope + multi-planner-protocol>)` |

> **Tool-name note (`Task` vs `Agent`):** `Task` is the v2.1.63 **legacy alias** for the unified `Agent` spawn tool — both names work and dispatch identically. This contract uses `Agent` as the canonical name. The broad cosmetic `Task`→`Agent` rename across the *other* one-shot roles' contract text (acquirer / ethics / synthesizer / planner / reviewer / builder) is **OUT OF SCOPE** for this migration; only the cluster-specialist rows and the intro line above are normalized here.

> **Single-planner / reviewer / builder note:** In this audit-only repo those roles dispatch as one-shot subagents per the per-role table and the "Subagent dispatch contract (v2 default)" section below. Their workflow prompt sources (`workflows/plan.md`, `workflows/review.md`, `workflows/build.md`) and the `/ecp:build` · `/ecp:compare` · `/ecp:quick-scan` sibling skills are not part of this repo, so they are intentionally omitted from this dispatch table.

### What stays the same

- **The explicit-model rule** (every dispatch passes `model: ...` inline; never inherit from parent).
- **Sonnet vs Opus assignment per role.** The flip is about *transport* (subagent vs teammate), not about model choice.
- **The `--deep` escape hatch** — affects model choice for the cluster specialists, ethics subagent, and builder (all sonnet by default, opus with `--deep`); dispatch shape is unchanged.
- **The forensic-trace assertion canary.** Counter names evolve to reflect the new shape; see "Assertion counter update on spawn" below for the v2 counter set.

---

## Auditor prompt template (removed in v1.2)

The v1 cluster-auditor teammate prompt template — including its `team_name`/`name`-bearing Agent invocation, its MANDATORY Step 1b intent huddle, its MANDATORY handoff broadcast, and the per-finding overlap-SendMessage — **was removed from this file in v1.2** as part of the prune pass for the frozen v1 markdown-emission path (product.md §5).

v2 specialists use [`contracts/specialist-prompt-v2.md`](specialist-prompt-v2.md) as the canonical prompt template. That template emits JSON-only against `schema/cluster-emission-v1.json`, dispatches as a one-shot subagent (no `team_name`, no `name`), and explicitly documents "## No coordination" (no SendMessage, no huddles, no SYNTHESIS_HINT propagation). The per-role and v2 dispatch tables above are the live contract; the cluster-specialist row carries `subagent_spawned_specialists` as its canonical counter (with `team_spawned_auditors` retained as the v1 alias).

If a v1 markdown-emission engagement ever needs replaying, the historical prompt template lives in git history alongside `scripts/assemble-audit.py` and `scripts/validate-cluster-files.py` — both of which are themselves frozen v1 tools per `skills/audit/SKILL.md` "Legacy v1 tools" note.

---

## Assertion counter update on spawn

**After every successful dispatch** (whether `Agent` for teammates or `Task` for subagents), the lead MUST increment the corresponding counter in `audit-trace.log`. The counter is the structural truth of the run; if you spawn N roles, the counter says N. If you don't spawn any, the counter says 0 — and the assertion self-check at audit completion will catch you.

### v2 counter set (Phase H — 2026-04-28)

The v2 dispatch flip introduces `subagent_spawned_*` counters alongside the existing `team_spawned_*` counters. The audit lead writes both:

| Role | Dispatch shape | Counter name to increment |
|---|---|---|
| Acquirer | subagent | `subagent_spawned_acquirers` |
| Cluster specialist | subagent | `subagent_spawned_specialists` (v1 backwards-compat alias `team_spawned_auditors` still accepted) |
| Ethics subagent | subagent | `subagent_spawned_ethics` |
| Synthesizer | subagent | `subagent_spawned_synthesizer` |
| Planner (single) | subagent | `subagent_spawned_planner` |
| Multi-planner peer | teammate | `team_spawned_planners` |
| Reviewer | subagent | `subagent_spawned_reviewer` |
| Builder | subagent | `subagent_spawned_builder` |

**Acquirer counter unit (per baton, not per Task).** `subagent_spawned_acquirers` counts **batons emitted** (1 per device captured), not Task dispatches. The canonical `scripts/acquire_url.py --both` is a single Task that emits two batons (`baton.json` + `baton-mobile.json`) and increments the counter by 2 — the `trace_counters_reconcile_with_artifacts` canary reconciles the counter against the on-disk batons, so a dual-device `--both` run correctly records 2, not 1. Spawning one Task per device by hand reaches the same count.

**Backwards compatibility:** v1 audit runs continue to increment `team_spawned_acquirers` and `team_spawned_auditors`. The audit-completion self-check accepts EITHER counter as valid evidence the role ran. v2 runs SHOULD use the new counter names; the assertion check treats `subagent_spawned_acquirers >= 1` and `team_spawned_acquirers >= 1` as equivalent for the purpose of "acquirer ran at least once."

See `${CLAUDE_PLUGIN_ROOT}/contracts/trace-assertion-canary.md` for the full counter contract and self-check rules, including the v2 header format.

---

## Subagent dispatch contract (v2 default)

For roles dispatched as one-shot subagents (acquirer, ethics, synthesizer, planner-single, reviewer, builder — and cluster specialists, per the v2 table above), the lead uses a one-shot spawn with **no `team_name`**. (`Task` and `Agent` are the same unified spawn tool — the legacy alias and its current name dispatch identically; the structural difference between subagent and teammate dispatch is the absence of `team_name`, not which tool name you type.)

### Tool-call shape

```
Task(
  subagent_type="general-purpose",
  description="<3-5 word imperative summary of the role's work>",
  model="<sonnet | opus per the per-role table above>",
  prompt=<rendered role-specific prompt template>
)
```

There is no `team_name` parameter (so the subagent does not join the team), no `name` parameter (so there's no per-role handle for SendMessage), and no shared task-list claim/complete cycle.

### Why subagents instead of teammates for these roles

1. **They don't peer-coordinate.** The roles flipped to subagent in v2 (acquirer, ethics, synthesizer, planner, reviewer, builder) never SendMessage another role at the same layer. v1 created teammates uniformly; v2 reserves teammate shape for the one role that genuinely needs real-time peer messaging (multi-planner peers). Cluster specialists share a workspace too, but through the engagement directory by deterministic filename — not teammate shape — so they dispatch as one-shot subagents like the rest.
2. **Idle notifications collapse.** A teammate that's idle pings the lead's mailbox until it gets a task or is dismissed. A subagent runs once, returns, and exits — no idle stream.
3. **Lead context shrinks.** Each idle notification is a context entry the lead reads through. ~70 idle pings (v1) → ~5-10 (v2).
4. **No team-state cleanup.** A subagent that fails leaves no zombie task on the team task list; the lead just dispatches a fresh subagent.

### Handling questions / clarifications from a subagent

A subagent can't SendMessage during execution. v1's reviewer/builder Q&A loops (relay-loop-protocol.md) used SendMessage during the teammate's run; v2 reviewer/builder pose questions in their final emission (a structured `questions[]` field). The lead surfaces them inline at `<checkpoint_review>` / `<checkpoint_build>` and re-dispatches a fresh subagent with the answers if the operator wants iteration. The relay-loop-protocol.md is preserved for v1 backwards compat but the v2 path doesn't need it.

### Failure recovery

If the subagent's prompt produces malformed output, validation failure, or no useful response:
1. **Retry once** — re-dispatch a fresh `Task` call with the same prompt plus an embedded validation error (e.g., "Your prior emission failed schema validation: <error>. Re-emit a single valid JSON object."). Increment a `subagent_retried_<role>` counter.
2. **On second failure** — either apply one logged **mechanical normalize** through the chokepoint command `scripts/test-specialist.py normalize` (schema/placement/shape metadata only, NEVER substantive prose; the command re-validates schema plus business rules before writing `<emission>.normalizations.json` — see `skills/audit/SKILL.md` Validation step 1), OR mark the role's output `status: "partial"` (or skip the layer with a SKIP marker) and continue. Document the reason in `audit-trace.log` and `lead-reflection.md`.

### Cancel.flag check

Before EACH subagent dispatch (and at every layer boundary in the audit pipeline), the lead checks `<engagement-dir>/cancel.flag`. If the file exists, the lead writes `engagement_status: cancelled_by_operator` to `audit-trace.log` and exits cleanly with partial artifacts preserved. See `contracts/lead-discipline.md` "Cancellation sentinel (cancel.flag)" section.

---

---

## Cross-references

- **`skills/audit/SKILL.md`** — the audit router defers to this file for dispatch shape.
- **`${CLAUDE_PLUGIN_ROOT}/contracts/flags.md`** — canonical `--deep` flag documentation.
- **`${CLAUDE_PLUGIN_ROOT}/contracts/trace-assertion-canary.md`** — spawn counter contract + cost trace heuristic.
- **`${CLAUDE_PLUGIN_ROOT}/contracts/audit-reconciliation.md`** — the format + voice validation guardrails the specialist emissions must clear.
- **`${CLAUDE_PLUGIN_ROOT}/contracts/specialist-prompt-v2.md`** — canonical v2 cluster-specialist prompt template (replaces the removed v1 teammate template above).
- **`${CLAUDE_PLUGIN_ROOT}/contracts/cluster-routing.md`** — source of truth for the per-cluster reference file list each v2 specialist receives.
- **`${CLAUDE_PLUGIN_ROOT}/contracts/device-semantics.md`** — dual-device session isolation and per-device path conventions.
- **`${CLAUDE_PLUGIN_ROOT}/references/ethics-gate.md`** — canonical ethics content the ethics subagent (`contracts/ethics-subagent-v2.md`) consumes.

When editing this file, grep `skills/audit/SKILL.md` + `workflows/acquire.md` + `workflows/audit.md` for any `model: "sonnet"` or `model: "opus"` literals and verify each still matches the per-role table above. Drift in model assignments is the highest-risk class of bug in the whole plugin because it silently changes cost and quality.
