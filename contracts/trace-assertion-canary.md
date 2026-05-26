# Audit trace assertion canary + cost trace heuristic

Canonical reference for the forensic assertion header that makes rogue audit runs detectable in 2 seconds, and the cost-trace heuristic that gives the user receipts on where token cost went.

**Why this file exists:** Prior to Round 12, these two load-bearing orchestration contracts lived inline in `skills/audit/SKILL.md`. They're read by the audit lead only (single consumer), but they're topically distinct from the phase flow and deserve their own reference file for clarity and future cross-skill extension (compare lead may adopt the same canary pattern in a later round).

**Read this file when:** you are the audit lead (coordinator) and you are writing the initial `audit-trace.log` header after engagement setup, OR running the self-check assertion at audit completion, OR computing estimated token cost for the trace log.

---

## Purpose of the assertion canary

Make rogue runs detectable in 2 seconds by writing the structural commitments to the top of `audit-trace.log` as numerical assertions. A future reader (or you on resume) should not need to read 200 lines to know whether the team architecture was honored.

**Rogue detection examples:**
- A rogue run that skipped all teammates shows `team_spawned_acquirers: 0` and `team_spawned_auditors: 0` at the top of its trace log. Two seconds to spot.
- A run that spawned acquirers but skipped cluster auditors shows `team_spawned_auditors: 0` while `team_spawned_acquirers: 2`. Same — instant.
- A run that spawned everything but never wrote cluster files (impossible if the auditors actually ran) shows `cluster_files_written: 0` while `team_spawned_auditors: 8`. Tells you the auditors crashed before writing.
- A run that "declared ethics CLEAR" without actually running the gate shows `ethics_gate_executed: false`. Fabrication detected.

**This is the rogue-detection canary.** It does not prevent the rogue, but it makes the rogue visible to itself and to the user immediately, so neither party is fooled by a Potemkin audit.

---

## Required header format

Write this as the FIRST ~30 lines of `docs/ecp/{engagement-id}/audit-trace.log` immediately after engagement setup completes. **Phase H — 2026-04-28** added the v2 dispatch-shape counters (`subagent_spawned_*` for acquirer/ethics/synthesizer/planner/reviewer/builder; `team_spawned_specialists` replaces `team_spawned_auditors`). v1 audits emit only the v1 counter subset; v2 audits emit the full v2 set. The self-check accepts both naming styles (alias rules below).

### v2 header (Phase H 2026-04-28 — default for v2 engagements):

```
# ECP Audit Forensic Trace
# Engagement: {engagement-id}
# Target: {url-or-file-path}
# Started: {iso-8601-timestamp}
# Pipeline: v2                           ← v1 | v2; gates which counter set is asserted
# Devices: {device-list}
# Clusters: {cluster-list}
# Flags: {space-separated list of flags actually set — e.g., "--deep --focus all" or empty}
# Scope: {scope}                         ← focused, standard, comprehensive, or custom
# ASSERTIONS (must all be > 0 / true at audit completion):
#   tasks_created_total: {N}              ← v1 only; v2 sets to the count of TaskCreate calls (specialists + multi-planners)
#   expected_specialist_count: {N}        ← set at dispatch time after scope resolution + empty-slice pruning (v2 alias of v1 expected_auditor_count)
#   subagent_spawned_acquirers: 0         ← v2: incremented after each Task call dispatching an acquirer
#   team_spawned_specialists: 0           ← v2: incremented after each Agent call dispatching a cluster specialist (teammate dispatch retained)
#   subagent_spawned_ethics: 0            ← v2: incremented after the Layer 1.5 ethics subagent dispatch
#   subagent_spawned_synthesizer: 0       ← v2: incremented after the Layer 3 synthesizer subagent dispatch
#   subagent_spawned_planner: 0           ← v2: single-planner subagent (multi-planner peers count via team_spawned_planners instead)
#   team_spawned_planners: 0              ← v2: multi-planner peers (teammate dispatch — peer SendMessage negotiation)
#   subagent_spawned_reviewer: 0          ← v2: incremented after each Task call dispatching the reviewer
#   subagent_spawned_builder: 0           ← v2: incremented after each Task call dispatching the builder
#   subagent_retried_<role>: 0            ← v2: incremented when a subagent's emission failed validation and the lead re-dispatched
#   cluster_files_written: 0              ← incremented after each cluster-{cluster}-{device}.json is verified on disk (both v1 and v2)
#   ethics_gate_executed: false           ← set true after ethics processing completes (v2: subagent_spawned_ethics >= 1 AND ethics-findings.json validated)
#   idle_notification_total: 0            ← v2: incremented per idle_notification observed; >10 from non-specialists triggers a soft warning
# COST TRACE (model choices locked at dispatch time; estimated_tokens_total filled at completion):
#   model_acquirer: sonnet                ← always sonnet per spec (mechanical work)
#   model_cluster_specialists: sonnet     ← sonnet by default; "opus" when --deep is set (v2 alias of v1 model_cluster_auditors)
#   model_ethics: sonnet                  ← v2: sonnet by default; "opus" when --deep is set
#   model_synthesizer: opus               ← v2: always opus (synthesis brain)
#   model_planner: opus                   ← always opus (strategic prioritization)
#   model_reviewer: opus                  ← always opus (quality gate)
#   model_builder: sonnet                 ← sonnet by default; "opus" when --deep is set
#   model_lead: opus                      ← synthesis brain — always opus
#   estimated_tokens_total: ~0            ← filled in at audit completion via the heuristic below
```

### v1 header (legacy — for v1 audits run via the v1 path):

```
# ECP Audit Forensic Trace
# Engagement: {engagement-id}
# Target: {url-or-file-path}
# Started: {iso-8601-timestamp}
# Pipeline: v1                           ← optional but preferred for new v1 runs; absent = legacy v1
# Devices: {device-list}
# Clusters: {cluster-list}
# Flags: {space-separated list of flags actually set — e.g., "--deep --focus all" or empty}
# Scope: {scope}                         ← focused, standard, comprehensive, or custom
# ASSERTIONS (must all be > 0 / true at audit completion):
#   tasks_created_total: {N}              ← from engagement setup step 8 minimum count
#   expected_auditor_count: {N}           ← set at dispatch time after scope resolution + empty-slice pruning
#   team_spawned_acquirers: 0             ← incremented after each Agent tool call to spawn an acquirer
#   team_spawned_auditors: 0              ← incremented after each Agent tool call to spawn a cluster auditor
#   cluster_files_written: 0              ← incremented after each cluster-{cluster}-{device}.md is verified on disk
#   ethics_gate_executed: false           ← set true after the lead reads ethics-gate.md AND processes auditor ethics outputs
# COST TRACE (model choices locked at spawn time; estimated_tokens_total filled at completion):
#   model_acquirer: sonnet                ← always sonnet per spec (mechanical work)
#   model_cluster_auditors: sonnet        ← sonnet by default; "opus" when --deep is set
#   model_builder: sonnet                 ← sonnet by default; "opus" when --deep is set
#   model_lead: opus                      ← synthesis brain — always opus
#   model_planner: opus                   ← always opus (strategic prioritization)
#   model_reviewer: opus                  ← always opus (quality gate)
#   estimated_tokens_total: ~0            ← filled in at audit completion via the heuristic below
```

### Counter alias rules (Phase H 2026-04-28)

The audit-completion self-check accepts either naming style for backwards compatibility. When a counter has a v1 name and a v2 alias, satisfying EITHER counter at the threshold passes the assertion:

| Assertion | v1 counter | v2 counter |
|---|---|---|
| Acquirer ran | `team_spawned_acquirers >= D` | `subagent_spawned_acquirers >= D` |
| Cluster specialists ran | `team_spawned_auditors >= expected_auditor_count` | `team_spawned_specialists >= expected_specialist_count` |
| Cluster files on disk | `cluster_files_written == team_spawned_auditors` | `cluster_files_written == team_spawned_specialists` |
| Ethics gate executed | `ethics_gate_executed == true` | same (v2 also implies `subagent_spawned_ethics >= 1`) |

**v2-only assertions (no v1 equivalent):**
- `subagent_spawned_synthesizer >= 1` — Layer 3 synthesizer dispatched (v1 lead writes audit.md inline; no subagent counter)
- `idle_notification_total <= 10 + (specialist_count × 1)` — soft warning if exceeded

**Substantive canaries (Phase I — 2026-04-28):** the structural counter assertions above check whether ROLES ran. Substantive canaries check whether their OUTPUTS hold up. The audit lead invokes `scripts.assembly.canary_checks.run_all_canaries(engagement_dir)` at audit completion and writes the three results to `audit-trace.log`. See "Substantive canaries" section below for the full contract.

---

## Substantive canaries (Phase I — 2026-04-28)

Three load-bearing canaries check the SUBSTANCE of the audit output, not just whether roles ran. The audit lead invokes them at audit completion, writes results to `audit-trace.log`, and writes any failures (and any deliberate operator-injected deviations) to `lead-reflection.md` per `contracts/lead-discipline.md` "Lead reflection (lead-reflection.md)" section.

Implementation: `scripts/assembly/canary_checks.py`. Pure functions; no LLM dispatch; safe to run on every engagement at completion.

### Canary 1 — ethics_findings_have_source_urls

**Asserts:** every ethics finding with `ethics_state` ∈ {BLOCK, ADJACENT} carries a non-empty `source_url` field, AND the `source_url` does NOT contain the audited domain (preventing self-cite filler).

**Why:** v2 ethics emissions are the legal-exposure surface; a BLOCK finding without a regulation/research source URL is unshippable to a client. The v1 reconciliation gate (`contracts/audit-reconciliation.md`) already rejects self-cite filler at the reconciliation step; this canary catches the regression where a future change weakens that gate.

**How to compute:** read `<engagement-dir>/ethics-findings.json`. For each finding with `ethics_state` ∈ {BLOCK, ADJACENT}: verify `source_url` non-empty AND extract host; reject if host equals the audited domain (or is a subdomain of it). CLEAR findings skipped (informational).

**Pass criterion:** 100% — any actionable finding without valid `source_url` fails the canary. Pass result is recorded as `canary_ethics_source_urls: pass` in audit-trace.log; fail is recorded with the failing f_refs.

**Failure handling:** the lead does NOT phase-block on canary failure (the audit still completes). Instead, the lead writes `canary_ethics_source_urls: fail` to audit-trace.log AND documents the failure in `lead-reflection.md` under "Anomalies". Operator decides at `<checkpoint_audit>` whether to proceed or re-dispatch ethics.

### Canary 2 — element_index_match_rate

**Asserts:** at least 80% of `**ELEMENT:**` lines in `audit-{device}.md` cite a baton element index (e.g., `at e23`). Excludes absent-element lines from the denominator (those findings correctly omit baton_index because the element doesn't exist on the page or isn't captured in the baton).

**Why:** Phase A locked specialists emitting `baton_index` directly per `contracts/specialist-prompt-v2.md` "Element references — the e<int> rule". The synthesizer renders the locked ELEMENT format (`{selector-or-tag} at e{baton_index}`) per `contracts/synthesizer-v2.md` "Per-finding rendering format" spec. This canary surfaces drift where specialists or synthesizer regress to fuzzy CSS-selector descriptions OR omit the baton index reference.

**How to compute:** read `audit-desktop.md` and `audit-mobile.md`. Count `**ELEMENT:**` lines (denominator) and the subset matching `at e\d+` (numerator). Exclude lines marked absent (`(absent — proposed location: ...)`, `(absent from baton)`, `(not in baton)`, `(no baton entry)`) from the denominator — those are correct off-baton renderings.

**Pass criterion:** rate ≥ 0.8. Per the canonical plan: "effectively 100% post-Phase A; canary catches regression."

**Failure handling:** soft canary — does NOT phase-block. Lead writes `canary_element_index_match_rate: {rate}` to audit-trace.log and documents the rate in `lead-reflection.md` under "Anomalies". Slingmods baseline (2026-04-28) scores ~0.63 due to known synthesizer ELEMENT-format drift; Phase J fixture refresh should bring this to ~1.0 on the awdmods golden.

### Canary 3 — cross_device_ethics_diff

**Asserts:** the count of actionable ethics findings (BLOCK + ADJACENT) rendered into `audit-desktop.md` differs from the count rendered into `audit-mobile.md` by at most 1.

**Why:** v2 ethics is a single page-scope emission (one `ethics-findings.json`, no per-device variants). The synthesizer renders the actionable findings into both audit documents. Asymmetric rendering means either the synthesizer dropped ethics findings on one device (rendering bug) or the canonical-merge step misclassified them (Layer-2.5 bug). Either way, the canary surfaces it.

**How to compute:** read `audit-desktop.md` and `audit-mobile.md`. Count `### ethics F-NN` and `#### ethics F-NN` headings in each. Compute `abs(desktop_count - mobile_count)`.

**Pass criterion:** diff ≤ 1. The 1-finding tolerance accommodates edge cases where a BLOCK is rendered into one device's section because of per-device evidence framing.

**Failure handling:** soft canary — does NOT phase-block. Lead writes `canary_cross_device_ethics_diff: {diff}` to audit-trace.log; if failed, also lists the asymmetric refs (refs in one but not the other) in `lead-reflection.md` under "Anomalies". Operator decides whether to investigate.

### How the lead invokes the canaries

After `<phase_synthesize_v2>` completes (or the v1 audit_assembly self-check runs), the lead invokes:

```python
from scripts.assembly.canary_checks import run_all_canaries

result = run_all_canaries(
    engagement_dir=Path("docs/ecp/{engagement-id}"),
    audited_domain="slingmods.com",  # extracted from meta.json or baton.json
    element_threshold=0.8,
    ethics_max_diff=1,
)
```

The result dict contains `all_passed` (bool) and `results` (list of three CanaryResult dicts). The lead writes each canary's `summary` to audit-trace.log under a new "SUBSTANTIVE CANARIES" section:

```
# SUBSTANTIVE CANARIES (Phase I — soft assertions, do NOT phase-block on failure):
#   canary_ethics_source_urls: pass (5 actionable; 0 missing source_url; 0 self-cite)
#   canary_element_index_match_rate: 0.927 pass (132/142 present-element findings cite baton index; 8 absent excluded)
#   canary_cross_device_ethics_diff: 0 pass (desktop=2, mobile=2)
```

Failed canaries are also documented in `lead-reflection.md` (see `contracts/lead-discipline.md` "Lead reflection" section) with the specific failing refs / counts / drifts.

### Why these are SOFT canaries

The structural counter assertions (`team_spawned_specialists >= expected_count`, `cluster_files_written == team_spawned_specialists`, etc.) phase-block on failure because they detect rogue runs that didn't honor the team architecture contract. The substantive canaries detect QUALITY issues that the operator may want to know about but shouldn't auto-block the run for. Slingmods' element_index_match_rate score of 0.63 is a real drift surface — but blocking the audit prevents the operator from seeing the audit at all. Better to surface the drift in lead-reflection.md and let the operator decide.

A future v2.1 enhancement could add a `--strict-canaries` flag that promotes these to phase-blocking. For v2.0 they're advisory.

---

## Observability sections (Phase 5 — 2026-05-18)

Beyond the structural counters and substantive canaries above, the audit trace carries three observability sections. These don't gate phase progression; they exist so a future operator (or another Codex/Claude pass) can diagnose a completed run without re-executing it. Closes Phase 5.4 of `docs/ecp/2026-05-18-report-accuracy-and-hotspot-remediation-plan.md`.

### BATON TRIM SUMMARY block

Written by the lead immediately after the pre-synthesizer baton trim step. One block per device.

```
# BATON TRIM SUMMARY (Phase 5.1 — informational):
#   desktop: input=24 elements -> output=13 (trim_ratio=0.54)
#     summary_sidecar: baton-desktop-trimmed-summary.json
#     kept_by_role:    button=2, image=4, navigation=1, text=6
#     removed_by_role: image=4, navigation=2, link=5
#   mobile:  input=31 elements -> output=14 (trim_ratio=0.45)
#     summary_sidecar: baton-mobile-trimmed-summary.json
#     kept_by_role:    button=3, image=2, navigation=1, text=8
#     removed_by_role: button=1, image=8, navigation=4, link=4
```

The `summary_sidecar` field points at the per-device `baton-{device}-trimmed-summary.json` written by `scripts/assembly/synth_input.build_trim_summary` — that file has the full per-element removed list, kept e_index set, and per-role counts. The trace block carries only the summary lines to keep audit-trace.log human-scannable.

**Implementation:** call `trim_baton_file(..., summary_path=eng_dir / f"baton-{device}-trimmed-summary.json")` instead of the 3-arg form. The returned dict's `summary_path` field is what the lead writes into the trace block.

### OVERLAY DISMISSAL LOG block

Written by the lead aggregating `capture_state.overlays_detected[]` from each device's baton. One block per device. Empty when the page had no auto-open overlays.

```
# OVERLAY DISMISSAL LOG (Phase 5.2 — informational):
#   desktop: 0 overlays dismissed (clean entry)
#   mobile:  3 overlays dismissed; dom_state_modified: true
#     overlay-1: type=cart-drawer       selector=.cart-drawer       method=js-style-display-none
#       before=overlay-1-before.jpg after=overlay-1-after.jpg
#     overlay-2: type=media-modal       selector=.product-media-modal method=js-style-display-none
#       before=overlay-2-before.jpg after=overlay-2-after.jpg
#     overlay-3: type=nav-drawer        selector=.mobile-nav-drawer  method=js-style-display-none
#       before=overlay-3-before.jpg after=overlay-3-after.jpg
```

`dom_state_modified: true` on any device signals that the captured DOM differs from a normal user's view. The visual report MUST surface this as a caveat banner; the synthesizer SHOULD mention it in the page summary so findings about layout/cognitive load have the right framing. The awdmods 2026-05-18 mobile run is the documented case where this flag should have fired but didn't (the workflow didn't require structured logging yet).

### VARIANT PIN STATE block

Written by the lead after both device acquirers complete. One block per engagement (cross-device).

```
# VARIANT PIN STATE (Phase 5.3 — informational):
#   url_variant_param: 43915856805953   (or "none" when URL has no variant)
#   desktop: variant_id=43915856805953 source=url-pinned   price="$399.50" cta_enabled=true
#   mobile:  variant_id=43915856805953 source=url-pinned   price="$399.50" cta_enabled=true
#   variant_divergence: false
```

When `variant_divergence: true`, the synthesizer prompt template MUST include a "Cross-device variant differs" note so it knows to caveat any cross-device price/CTA finding. The lead also writes this flag to `meta.json.variant_divergence` so resume logic and downstream tools can read it without re-parsing the trace.

**Update protocol additions:**
- Trim summary block: write once, after the pre-synth trim step. Source of truth: `scripts/assembly/synth_input.trim_baton_file(..., summary_path=...)` return dict.
- Overlay log block: write once, after all device acquirers complete and their batons are verified on disk. Source of truth: each baton's `capture_state.overlays_detected[]`.
- Variant pin block: write once, same checkpoint as overlay log. Source of truth: each baton's `configured_state.{variant_id, variant_source}`. Compute `variant_divergence` cross-device.

These three blocks land BEFORE the SUBSTANTIVE CANARIES block in the trace file so the diagnostic context precedes the canary verdicts.

---

---

## Update protocol

- The lead writes the initial header (with all counters at 0 / false) immediately after `<engagement_setup>` completes.
- The `Flags` line is locked at header-write time — record the flags actually present in `$ARGUMENTS`. Do NOT update this line later; it's a snapshot of how the run was invoked.
- The cost-trace `model_*` lines are locked at header-write time based on whether `--deep` was set. Do NOT update these later either; they record the model decision for this run.
- After EACH `Agent` tool call that spawns a teammate, the lead UPDATES the corresponding counter line in-place via `Edit` (not append a new line — overwrite the assertion line).
- After cluster file format validation passes for each cluster file, increment `cluster_files_written`.
- After the ethics gate processing step in `<audit_assembly>`, set `ethics_gate_executed: true`.
- At audit completion (before phase → plan), the lead updates `estimated_tokens_total` using the heuristic below.

---

## Self-check at audit completion (MANDATORY)

Before writing `phase: complete` to `meta.json`, the lead reads its own `audit-trace.log` header and asserts:

**v1 path (Pipeline: v1 or absent):**
- `team_spawned_acquirers >= 1` (or `>= 2` for dual-device)
- `team_spawned_auditors >= expected_auditor_count` (dynamic count set at dispatch time — see below)
- `cluster_files_written == team_spawned_auditors` (every spawned auditor produced a file)
- `ethics_gate_executed == true`

**v2 path (Pipeline: v2 — Phase H 2026-04-28):**
- `subagent_spawned_acquirers >= 1` (or `>= 2` for dual-device) — OR v1 alias `team_spawned_acquirers`
- `team_spawned_specialists >= expected_specialist_count` — OR v1 alias `team_spawned_auditors`
- `cluster_files_written == team_spawned_specialists` (cluster specialists keep teammate dispatch in v2)
- `subagent_spawned_ethics >= 1` AND `ethics_gate_executed == true` (Layer 1.5 fired and produced valid ethics-findings.json)
- `subagent_spawned_synthesizer >= 1` (Layer 3 fired and produced audit-{device}.md + synthesizer-emission-v1.json)
- `idle_notification_total` from non-specialist roles SHOULD be <= 10 (soft warning if exceeded — possible teammate dispatch leak)

**Dynamic `expected_auditor_count`:** The expected auditor count is no longer a static `clusters × devices` formula. With the scope selector and DOM preprocessor, the actual count depends on:
1. The scope selected (focused = 1, standard = 3-4, comprehensive = 5-6, custom = variable)
2. Empty-slice pruning from the DOM preprocessor (clusters with no DOM sections routed to them are skipped)
3. Number of devices

The lead writes `expected_auditor_count` to the trace log header at dispatch time (after scope resolution and empty-slice pruning, immediately before spawning auditors). This is the number of auditors that WILL be spawned, not the theoretical maximum. The assertion checks against this dynamic value.

**If ANY assertion fails:** this is a structural failure of the run. Do NOT mark `phase: complete`. Instead:

1. Log the failure to the trace: append `ASSERTION FAILURE — {field}: expected {N}, got {M}. Audit phase did NOT honor the team architecture contract.`
2. Set `phase: blocked` in `meta.json` (see `${CLAUDE_PLUGIN_ROOT}/contracts/meta-schema.md` for the phase enum — `blocked` is the canonical terminal state for structural failures).
3. Write the failed assertions to `meta.json` under a new `assertion_failures` field.
4. Report to the user: "This audit run did not honor the team architecture contract — {specific assertion that failed}. The output is present but the structural commitments were not met. Resume from `phase: blocked` to retry with corrections."

The run produced output but did NOT honor the contract. Marking it complete would be a lie.

---

## Cost trace heuristic

**Purpose:** Give the user receipts on where token cost went after each audit run, so optimization decisions are grounded in real numbers instead of guesses. This is instrumentation, not enforcement — it affects nothing about how the audit runs, it just reports what happened.

**When to compute:** At audit phase completion, immediately before the assertion self-check. The lead writes `estimated_tokens_total` into the trace log header cost-trace block, overwriting the `~0` placeholder.

**Heuristic formula** (rough — good enough for relative comparison between runs):

```
acquirer_cost       = acquirer_count * 5000                      (~5K tokens per acquirer teammate)
auditor_cost_sonnet = auditor_count * 12000                      (~12K tokens per sonnet cluster auditor)
auditor_cost_opus   = auditor_count * 28000                      (~28K tokens per opus cluster auditor, ~2.3x sonnet)
lead_cost           = 25000 + (finding_count * 400)              (~25K base + per-finding reconciliation overhead)
planner_cost        = 12000 + (finding_count * 300)              (~12K base + per-finding prioritization)
reviewer_cost       = 10000 + (finding_count * 250)              (~10K base + per-finding review)
builder_cost_sonnet = plan_step_count * 3000                     (~3K tokens per plan step on sonnet)
builder_cost_opus   = plan_step_count * 7000                     (~7K tokens per plan step on opus)
```

**Note:** these are per-model token counts, NOT input/output splits. They conflate read + write for simplicity. The goal is **order-of-magnitude comparison**, not billing-accurate tracking.

---

## Write format for estimated_tokens_total

```
#   estimated_tokens_total: ~125000 (acquirer 10K + auditors 120K + lead 45K + ethics-only audit, no plan/review/build)
```

The parenthetical breakdown is optional but helpful — it tells the user WHICH role burned the tokens. Format: comma-separated `role XXK` entries summing to the total.

---

## What to skip when computing cost

- If only the audit phase ran (user stopped at `checkpoint_audit`), the cost should exclude `planner_cost`, `reviewer_cost`, `builder_cost` entirely.
- If the run used `--deep`, use `auditor_cost_opus` and `builder_cost_opus`. Otherwise use the sonnet costs.
- If the run is audit-only (no plan steps generated), `builder_cost` is 0.

---

## Why heuristic, not actual

Claude Code's subprocess token accounting is not exposed to the lead agent in a reliable way. A heuristic with published multipliers is better than either (a) guessing silently or (b) asking the user for API billing dumps. The multipliers are calibrated from observed runs on awdmods and sxsmods and may drift as model behavior evolves — update them when you find the estimates are 2x+ off from actual billing.

---

## Sample outputs

**Dual-device 5-cluster audit on sonnet auditors, audit-only:**
```
#   estimated_tokens_total: ~190000 (acquirer 10K, auditors 120K, lead 54K, ethics 6K)
```

**Same run on opus auditors (`--deep`):**
```
#   estimated_tokens_total: ~350000 (acquirer 10K, auditors 280K, lead 54K, ethics 6K)
```

The difference between those two numbers (~160K tokens) is the cost of `--deep` on a typical homepage audit. For a simple page, that's real money; for a client-facing run, it may be worth it. **The trace gives the user the numbers to make that decision for next time.**

---

## Cross-references

- **`skills/audit/SKILL.md`** — `<audit_trace_assertion_header>` and `<cost_trace_heuristic>` defer to this file. The audit lead reads this file when writing the initial trace header and when running the self-check at audit completion.
- **`${CLAUDE_PLUGIN_ROOT}/contracts/meta-schema.md`** — the canonical `phase` enum includes `blocked` for assertion-failure terminal state.
- **`${CLAUDE_PLUGIN_ROOT}/contracts/dispatch-contract.md`** — per-role model assignments and the `--deep` escape hatch rules (the cost trace's `model_*` lines and `--deep` cost multipliers derive from this).
- **`${CLAUDE_PLUGIN_ROOT}/contracts/lead-discipline.md`** — anti-rogue rules that the canary is designed to catch slips against.

When editing this file, the audit skill's pointer stubs in `<audit_trace_assertion_header>` and `<cost_trace_heuristic>` should reference this file as the source of truth.
