# Audit State Machine (v2)

Canonical reference for `meta.json.engagement_status` values, their semantics, and the legal transition graph. The state machine is **per-engagement**, not per-session — once an engagement is created, its `engagement_status` is the single source of truth for what's been done, what's safe to retry, and what's mid-flight. Agents (the lead, resume logic, canaries, future MCP tools) read and write this field.

Authored 2026-04-27 as part of the v2 redesign (Phase A).

## Why the granular catalogue

Under quality-first framing, when something breaks the operator wants to know *exactly where* in the pipeline. A coarse enum like `running | complete | failed` collapses ten different failure modes into one "failed" bucket, forcing the operator to grep `audit-trace.log` for diagnosis. The granular catalogue (12 base states + a `failed_<phase>` family) means a single field read tells you what the next move is:

- `audit-state: specialists_complete, structuring_failed` → bug in deterministic Python; rerun structuring against the same JSON inputs
- `audit-state: synthesizing` for >5 min → Opus call wedged; check rate-limit state
- `audit-state: rendering` for >2 min → renderer issue, not LLM
- `audit-state: cancelled_by_operator` → operator dropped `cancel.flag`; partial artifacts preserved for replay

This matches Phase A's explicit goal: "the difference between `audit-state: running` and `audit-state: specialists_complete, structuring_failed` is the difference between an hour of grep and a five-minute fix."

## Enum values

### Initial / pre-dispatch

| Value | Written by | Meaning |
|---|---|---|
| `pending` | `skills/audit/SKILL.md` `<engagement_setup>` step 4 | Engagement directory created, `meta.json` written. Acquirer not yet dispatched. |

### Acquisition phase (Layer 0)

| Value | Written by | Meaning |
|---|---|---|
| `acquiring` | Lead, before dispatching acquirer subagents | Layer 0 in flight. Acquirer subagent(s) running. Wall-clock budget: 180s per device per `workflows/acquire.md` failure-mode section. |
| `acquired` | Lead, after both device acquirers complete cleanly | Layer 0 complete. Both batons (`baton.json` + `baton-mobile.json`) validate against `schema/baton-v1.json`. Downstream phases can proceed. |
| `partial_acquisition` | Lead, when acquirer returns `STATUS: PARTIAL` (e.g., overlay not dismissed, mobile DPR fallback to 1×, single device acquired but not the other) | Layer 0 completed with degradation. Downstream phases proceed but with degraded-state warnings surfaced to operator in render layer. |
| `acquisition_failed` | Lead, when acquirer returns `STATUS: BLOCKED` or `STATUS: TIMEOUT` (404, Cloudflare challenge, auth required, agent-browser unavailable, hard 180s wall-clock exceeded) | Terminal failure for this engagement. Downstream phases short-circuit. Operator must adjust input (different URL, supply DOM file, etc.) and create a new engagement. |

### Dispatch + parallel work (Layer 1 + 1.5)

| Value | Written by | Meaning |
|---|---|---|
| `ethics_dispatched` | Lead, immediately after dispatching the ethics subagent | Ethics subagent running. Single dispatch on union of mobile + desktop DOMs. Concurrent with specialist dispatch. |
| `specialists_dispatched` | Lead, immediately after dispatching the specialist auditors as a parallel batch | All N specialists (per scope) dispatched concurrently. Concurrent with ethics. |
| `ethics_complete` | Lead, after ethics subagent writes valid `ethics-findings.json` (cluster='ethics' emission validating against `schema/cluster-emission-v1.json`) | Layer 1.5 complete. Findings consumable by Layer 2 dedup and Layer 3 synthesizer. |
| `specialists_complete` | Lead, after all dispatched specialists have written valid `cluster-{cluster}-{device}.json` files (per `schema/cluster-emission-v1.json`) OR have been marked `status: partial` / `status: skipped` after retry exhausted | Layer 1 complete. Verified by `dispatched_specialists_emitted_count == expected_specialists_count` substantive canary. |

**Concurrency note:** `ethics_dispatched` and `specialists_dispatched` can both be written within the same lead turn (parallel-batch dispatch). Similarly, `ethics_complete` and `specialists_complete` can arrive in either order. The lead writes the *latter* of the two completions before transitioning to `structuring`.

### Sequential phases (Layer 2 → 3 → 4)

| Value | Written by | Meaning |
|---|---|---|
| `structuring` | Lead, when both `ethics_complete` and `specialists_complete` are recorded | Layer 2 deterministic Python pipeline running: jsonschema validation, SCOPE-aware dedup, candidate scoring, business-rules validation. No LLM in this phase. |
| `synthesizing` | Lead, after Layer 2 produces a valid candidates JSON | Layer 3 single Opus synthesizer dispatched. Reads all specialist JSON + screenshots + ethics-findings + page-type context; emits `audit-{device}.md` × 2 + `synthesizer-emission-v1.json`. May enter degraded mode (per Phase F.3); the `synthesizer-emission-v1.json` records `dispatch_shape: single \| per-device` and `degraded_mode: bool`. |
| `rendering` | Lead, after synthesizer emits valid markdown + JSON | Layer 4 Python render: `generate-report.py` reads JSON + synthesizer prose, produces visual HTML reports. Hotspots resolve via baton element index dictionary lookup — no fuzzy CSS-selector matching. |
| `complete` | Lead, after both visual HTML reports written successfully | Terminal success. Engagement is shippable. |

### Cancellation / failure

| Value | Written by | Meaning |
|---|---|---|
| `cancelled_by_operator` | Lead, when `<engagement-dir>/cancel.flag` is detected at any layer boundary | Operator (or another agent) dropped the sentinel file. Lead exits cleanly; partial artifacts preserved for replay. See Phase H.6 `cancel.flag` semantics. |
| `failed_<phase>` | Lead, when a phase fails irrecoverably after retries exhausted | `failed_acquisition` / `failed_ethics` / `failed_specialists` / `failed_structuring` / `failed_synthesis` / `failed_synthesis_drift` / `failed_render`. The canonical failure values; `audit-trace.log` carries the diagnostic detail. `failed_synthesis_drift` is the specific Phase F.3 failure where degraded-mode per-device dispatch ran but the cross-device Levenshtein assertion exceeded 10% on `scope='page'` rendering — the lead writes `lead-reflection.md` and the synthesizer-emission-v1.json records the per-finding ratios. Resume cannot recover from a `failed_<phase>` state — operator inspects, fixes input, creates a new engagement. |

## Legal transition graph

```
pending
  └─→ acquiring
        ├─→ acquired ──────────┐
        ├─→ partial_acquisition ┤
        └─→ acquisition_failed (terminal)

acquired / partial_acquisition
  └─→ ethics_dispatched ┐
                        ├─→ (concurrent)
  └─→ specialists_dispatched ┘

ethics_dispatched ──→ ethics_complete
                  └──→ failed_ethics (terminal)

specialists_dispatched ──→ specialists_complete
                       └──→ failed_specialists (terminal)

(both ethics_complete AND specialists_complete required)
  └─→ structuring
        ├─→ synthesizing
        │     ├─→ rendering
        │     │     ├─→ complete (terminal success)
        │     │     └─→ failed_render (terminal)
        │     ├─→ failed_synthesis (terminal — generic synth failure)
        │     └─→ failed_synthesis_drift (terminal — Phase F.3 Levenshtein drift abort)
        └─→ failed_structuring (terminal)

(any non-terminal state)
  └─→ cancelled_by_operator (terminal — partial artifacts preserved for replay)
```

## Read/write contract by phase

- **`skills/audit/SKILL.md`** writes `pending` at engagement creation; transitions through every state above.
- **Resume/replay** (out of scope in this build) would read `engagement_status` to route: `pending|acquiring` → restart acquisition; `acquired|partial_acquisition` → resume at ethics + specialists; `*_complete` → resume at next phase; `structuring|synthesizing|rendering` → re-run deterministically; `complete` → no-op; `failed_*` / `cancelled_by_operator` → not resumable.
- **`scripts/assembly/pipeline.py`** (Layer 2) reads `engagement_status` to verify `ethics_complete + specialists_complete` invariant; writes `structuring → synthesizing` transitions.
- **`generate-report.py`** (Layer 4) reads `engagement_status` to determine whether to render a "degraded" banner (when value is `partial_acquisition`) or a "cancelled" notice (when `cancelled_by_operator`).
- **Substantive canaries** (Phase I) verify `engagement_status` consistency: e.g., `dispatched_specialists_emitted_count == expected_specialists_count` is checked at the `specialists_dispatched → specialists_complete` transition.

## Sticky engine version

Per Phase L.3: an engagement's `meta.json.schema_version` (`1` legacy / `2` v1.5 / `3` v2) is sticky once set. v2 cannot retro-touch a v1 engagement — resume routes to the v1 path. v1 cannot resume a v2 engagement — schema_version mismatch fails with a clear error rather than silent data corruption.

This contract applies only to schema_version 3 (v2) engagements. v1 and v2-pre engagements use a coarser enum (`pending | audit | plan | review | build | complete | blocked`) per the legacy `phase` field.

## Cross-references

- [`schema/baton-v1.json`](../schema/baton-v1.json) — Layer 0 output that `acquired` requires
- [`schema/cluster-emission-v1.json`](../schema/cluster-emission-v1.json) — Layer 1 output that `specialists_complete` requires (also used by ethics emission with `cluster: ethics` + `device: page`)
- [`schema/synthesizer-emission-v1.json`](../schema/synthesizer-emission-v1.json) — Layer 3 output that `synthesizing → rendering` requires (shipped Phase F)
- [`contracts/synthesizer-v2.md`](synthesizer-v2.md) — synthesizer prompt template; sibling to specialist-prompt-v2.md (shipped Phase F)
- [`scripts/assembly/synth_input.py`](../scripts/assembly/synth_input.py) — Phase F.3 helpers (baton pre-trim, phrasing seeds, Levenshtein drift gate)
- [`contracts/meta-schema.md`](meta-schema.md) — full meta.json field reference; `engagement_status` enum values listed there mirror this document
- [`contracts/lead-discipline.md`](lead-discipline.md) — `cancel.flag` semantics, write-atomicity contract, concurrent-audit isolation rule
- [`contracts/trace-assertion-canary.md`](trace-assertion-canary.md) — substantive canaries that verify state-machine invariants (Phase I additions)

## Maintenance rule

When a new state is added to this document, update **all** of:
1. `templates/meta.json.template` — `engagement_status` field (if defaulted)
2. `contracts/meta-schema.md` — `engagement_status` enum value table
3. `skills/audit/SKILL.md` — phase transition write sites
4. `scripts/assembly/pipeline.py` and `generate-report.py` — readers
5. Substantive canaries in `contracts/trace-assertion-canary.md` if the state participates in invariant checks

Same-commit discipline: a state addition without all six site updates is a partial change that future-Claude or future-Dan will hit as inconsistency. Reviewer should reject partial state-machine changes.
