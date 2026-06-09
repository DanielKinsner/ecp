# Handoff — bloat prune + awdmods run-review fixes (2026-06-08)

> Session goal (operator): "cut the bloat, the redundancy, wire it up properly,
> commit + push to main in small chunks." Driven by two inputs: the
> `docs/2026-06-08-audit-run-review-awdmods.md` post-run review (claims to
> validate + implement) and a fresh repo-wide bloat/redundancy/dead-code audit.

## State at handoff

- Branch `main`, **11 commits pushed** (`988830e..4b72c13`). Net **−2,864 lines**
  (668 insertions, 3,532 deletions across 49 files).
- **Tests green both runners:** `python -m pytest tests/` → **1107 passed, 12
  skipped, 54 subtests** (baseline at session start was 1088 passed; +19 from new
  tests added this session). `python -m unittest discover -s tests` → **719 OK**.
- Every commit was gated by the relevant tests; full suite re-run green before this handoff.

## Method

1. Validated each run-review §8/§10 recommendation against ground truth with a
   read-only fan-out workflow (the review itself documented a correlated LLM
   false-positive in §11, so every claim was re-checked against the actual code,
   not taken on faith). Verdicts: **8 VALID, 3 PARTIAL** — none invalid.
2. Ran a separate bloat/redundancy/dead-code audit workflow; every DELETE was
   required to prove zero references with a deterministic grep before action.

---

## What shipped (this session)

### Run-review fixes
| Commit | Claim | What changed |
|---|---|---|
| `e97f169` | **C7b** | `generate-report.py` `--device`/`--plugin-root` now conditionally required (render path only); the state verbs (`--mark-reflection-complete` etc.) run with just `--engagement`. +2 tests. |
| `8cca301` | **C7c** | Trace-counter parser regex (`canary_checks._TRACE_COUNTER_RE`) tolerates trailing annotations (`: 12 (wave2 6+6)`, `← v2:…`) — was a silent FALSE reconcile failure. +2 tests, contract note. |
| `48f9eeb` | **C9** | `drift-check` auto-appends a `# DRIFT GATE` block (verdict + max_ratio + worst f_ref) to `audit-trace.log` every run, so FAIL→fix→re-PASS is reconstructable. +5 tests, contract + SKILL note. |
| `3b6d074` | **C1+C2 (+C8)** | `acquire_url.py`: `--allow-existing` + `_merge_meta` (merge into the lead's dir, lead fields win — no more clobbering meta.json/trace); `_upgrade_batons_to_v2` (acquisition auto-runs the v1→v2 conversion in place; desktop+mobile; idempotent; best-effort). +10 tests. acquire.md: never kill browsers by bare `chrome` process name (C8). |
| `07c1fd4` | **C7a** | Documented the `-v2` visual-report suffix the v2 renderer hardcodes (SKILL Artifact Contract + report-export.md table). |
| `fb6144a` | **C5** | Sanctioned a narrow, logged, **mechanical-only** normalize tier between autofix and re-dispatch (schema/placement only, never prose; must re-validate + log). SKILL + dispatch-contract. |

### Bloat / redundancy pruning
| Commit | What | Lines |
|---|---|---|
| `aac68a9` | Deleted `scripts/one_off/` (13 throwaway scripts) + orphan `scripts/normalize_lf.py` | ~3.3k |
| `e4af34d` | Deleted 3 hyphenated reference CLI shims; re-pointed generators + 3 generated docs to the underscored modules (collapsed dual-naming) | ~24 |
| `b2de02d` | Deleted legacy orphan `scripts/prep_synth_input.py` (crashes on v2; zero callers) | ~73 |
| `61d8d52` | Deduped `viewport_dpr`/`element_rect_raw` (re-export from `report.geometry`) and `levenshtein_distance` (new `assembly/_text_distance.py`; ratio wrappers kept separate — opposite semantics) | ~58 |
| `07c1fd4`, `4b72c13` | Doc truth-ups: removed dead file pointers (`docs/brainstorms/*`, `docs/plans/*`, `docs/redesign-v2-proposal.md`) from schemas + requirements.txt; fixed `<engagement_setup>` anchor; corrected README outputs + acquire.md "teammate" language; corrected SKILL.notes.md "specialists are teammates" (false since 2026-06-01); noted v2 path in package docstrings; surfaced `build_synthesizer_emission_fallback.py` in SKILL Recovery. | — |

`scripts/*.py` went from 26 → 21 files.

---

## Deferred — and WHY (do NOT treat as done)

These were deliberately NOT done because they're either (a) load-bearing and
risky to edit blind, (b) only verifiable against a live audit, or (c) net-additive
(the operator explicitly wanted subtraction, not more lines). Each has a precise
plan so the next pass is fast.

### 1. Category B — v1 / Agent-Teams contract-reword sweep  ⚠️ biggest remaining item
**Why deferred:** `skills/audit/SKILL.md` **loads these contracts at runtime**
(see its "Read these files" list + the phase load-table), so the stale content is
actively read by the audit lead — but precisely because they're load-bearing,
bulk-editing them blind risks breaking the next audit. Several need a real
decision, not a mechanical fix (e.g. *should SKILL stop loading `audit-assembly.md`
on a v2 run, or should the contract be rewritten to v2?*).

**Recommended approach:** one focused pass (ideally a workflow: one agent per
contract → reads the stale file + the canonical v2 source + how/where SKILL loads
it → proposes an exact diff + confidence) → human/lead reviews each diff → apply
high-confidence ones → run tests + (ideally) one live `--plugin-dir` audit.

Findings (file → what's stale, from the bloat audit; all verified):
- `workflows/audit.md` — describes the dead Agent-Teams **teammate** model (Step 1b "Team Huddle", MANDATORY SendMessage broadcasts, writes `cluster-*.md`). Loaded for the Specialist-audit phase. Either rewrite to the one-shot subagent model or stop loading it.
- `contracts/synthesizer-subagent.md` — "ONE synthesizer **per device**" + `assemble-audit.py --priority-path`; contradicts `synthesizer-v2.md` ("per engagement", emits `synthesizer-emission-v1.json` + both device md).
- `contracts/audit-reconciliation.md` — Step 0 reads `cluster-*.md` markdown + `validate-cluster-files.py`; v1 path.
- `contracts/audit-assembly.md` — the v1 `audit.md` template; SKILL still loads it for Assembly phase.
- `contracts/progress-comparison.md` — reads/writes `audit.md`; **no script implements it** (`grep progress_comparison scripts/` → none); v2 never writes `audit.md`.
- `contracts/priority-path-synthesis.md` — `assemble-audit.py` reconciliation + `SYNTHESIS_HINT:` (teammate-era).
- `contracts/dispatch-contract.md` — the v1 cluster-auditor teammate template (lines ~129-269) embeds MANDATORY huddle/handoff broadcasts pointing at the stale `workflows/audit.md §Step 1b`.
- `contracts/team-lifecycle.md` — full Agent-Teams lifecycle for `/ecp:audit|build|compare|resume`; migration note already says it's dead for audit.
- `contracts/flags.md`, `contracts/device-semantics.md`, `contracts/meta-schema.md`, `contracts/lead-discipline.md` — still claim support for frozen skills (`/ecp:build|compare|quick-scan|resume`) that don't exist in this build (only `/ecp:audit` ships).
- `contracts/cluster-routing.md` — references nonexistent SKILL anchors `<cluster_selection>` / `<domain_cluster_routing>`.
- `skills/audit/SKILL.notes.md` line ~24 already corrected this session; the routing-table rows for the dead phases could get the same legacy caveat.

### 2. C3 — native true-scrollable-height probe in the acquirer (run-review §3/§8-#1)
**Why deferred:** the acquirer-side scroll-to-end probe is only verifiable against
a **live** browser capture (the test suite can't exercise agent-browser), and the
inflation it fixes is cosmetic (the awdmods run proved output was fine — 0 unplaced
hotspots; it only cost investigation time). Shipping unverifiable scroll-timing
changes into the capture path is the churn risk to avoid.
**Plan (already scoped by validation):** add `_probe_doc_height()` to
`acquire_url.py` (scrollTo end → read scrollY, loop until stable within ~4px →
restore scrollTo(0)), persist `true_max_scroll_px` on the v1 baton; in
`baton_v1_to_v2.py:209` prefer it: `base = probed if probed>0 else el_bottom;
page_height = max(base, sec_bottom, vh)` (the `sec_bottom` floor makes it safe —
can't shrink below real captured content). Do BOTH halves or neither (a field
nothing writes is dead code). Verify with one live `--plugin-dir` mobile audit.

### 3. C4 — structured `*.normalizations.json` + consistency canary (run-review §8-#2, called #1 leverage)
**Why deferred:** genuinely **additive** (~150-250 lines: a new `normalize` CLI
verb in `test-specialist.py` as the write chokepoint + a `check_lead_normalizations_consistent`
canary in `canary_checks.py` + tests + bumping the canary-count assertions in
`tests/test_v2_canary_checks.py` / `test_g24_*`). The operator explicitly wanted
subtraction this session. The **policy half (C5) shipped** and points here.
**Plan:** mirror autofix's `run_autofix`/`*.repairs.json` shape exactly. `run_normalize`
writes `<emission>.normalizations.json` (`{finding_local_id, field, before, after,
reason, applied_at}`); the canary asserts every recorded `after` == the file's
current value (skip-pass when absent, mirroring the reflection canaries). This is
the enforcement that makes C5's sanction safe — worth doing, but it's a decision
to add machinery, so left for the operator to greenlight.

### 4. C6 — ghost-zone placement for absence/head-meta findings (run-review §8-#4) — PARTIAL, HIGH risk
**Why deferred:** HIGH-risk geometry (every audit's render path; expect 3-8 snapshot
re-baselines) AND validation confirmed it **won't even silence the `proxy_overload`
SOFT WARN** it targets (that counts non-exact *types*, not stacks). The soft-warn is
already correctly rationalized as benign for absence-heavy homepages. Exactly the
kind of risky churn to do deliberately, not blind.
**Plan (Phase 1 only, if pursued):** generalize `_distribute_stacked_section_markers`
(`report/v2_markers.py:~560`) — change the filter at ~570 from only
`proposed_anchor_section` to also `proposed_anchor_element` + `e_index_lookup`
(the two stack classes that actually fired: head-meta findings sharing the logo
element; multiple clusters citing one baton element). Add an `element_stacked_manual`
match-method and register it in `visual_evidence._MATCH_METHOD_TO_TYPE`,
`review_state._hotspot_confidence`/`_marker_source`. Re-baseline the live-render
fixture. Verify with a live render.

### 5. reflection_state.py ↔ report_state.py factory dedup (bloat audit, CONSOLIDATE, medium risk)
~70 mirrored LOC (two near-identical state machines). A `_meta_state_gate(field,
terminal, error_class, msg)` factory would collapse them, but both are tested by
parallel gates (G8 / G23) — medium risk, left for a focused refactor.

### 6. Minor KEEP-BUT-NOTE
- Note the `reference_*` family (link-check / lint / maintenance, ~640 LOC) in
  `docs/CONVENTIONS.md` as "operator maintenance, off the audit path" so future
  bloat audits don't keep re-flagging it.

---

## Verification caveat (read before trusting the acquire change)

`scripts/acquire_url.py`'s live capture path is **not** exercised end-to-end by the
test suite (needs `agent-browser` + a live URL). This session's acquire change
(`3b6d074`) is covered by unit tests on the **extracted pure helpers**
(`_prepare_engagement_dir`, `_merge_meta`, `_upgrade_batons_to_v2` — 10 tests) and
the converter's own 31 tests, and the helpers are guarded (the auto-convert is
best-effort: on failure it warns and keeps the v1 baton, so it can't regress
existing behavior). **Before the next client run, do one live
`--plugin-dir` `/ecp:audit` and confirm:** (a) the lead pre-creates the dir and the
acquirer accepts it with `--allow-existing` without wiping `meta.json`; (b)
`baton{,-mobile}.json` are v2-shape on disk after acquisition (with
`baton*.v1raw.json` backups present).

## Pointers
- Run-review (the source claims): `docs/2026-06-08-audit-run-review-awdmods.md`
- Validation workflow result + bloat audit result: this session's task outputs
  (`.../tasks/whtlc109h.output`, `.../tasks/wqpntlg92.output`) — ephemeral; the
  Category B evidence above is the durable copy.
- Env / launch: `CLAUDE.md` (always `--plugin-dir` against the working tree).
