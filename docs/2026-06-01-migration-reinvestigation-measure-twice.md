# ECP Migration Reinvestigation — Measure Twice (2026-06-01)

> **📜 HISTORICAL — banner added 2026-06-12.** Point-in-time investigation (2026-06-01); the migration it de-risked **shipped**. Superseded as a work pointer by the consolidated 2026-06-09/10 roadmap ([reviews/2026-06-10-consolidated-findings-and-plan.md](reviews/2026-06-10-consolidated-findings-and-plan.md), EXECUTED) and its post-roadmap fix plan ([reviews/2026-06-10-post-roadmap-review-and-fix-plan.md](reviews/2026-06-10-post-roadmap-review-and-fix-plan.md)). Re-triage anything that still looks undone against the current chain — CLAUDE.md §"Start here" is the live pointer.

> Produced by the `ecp-measure-twice` workflow: 7-lens discovery + adversarial
> verification (50 agents) diffing the current repo against the known-good
> pre-migration archive (`ecommerce-conversion-psychology-archive`). 38 raw
> findings → 40 verified → **2 confirmed migration regressions, 20 refuted.**

## 1. Executive summary

Only **one** issue is a true migration regression that needs action:
`dispatch-contract.md` lost ~46 lines of structure plus two referenced protocol
files (`relay-loop-protocol.md`, `multi-planner-protocol.md`) during the
prune-and-re-root, leaving a dangling reference and an internally contradictory
v2 multi-planner spec. A second item (skip-guarded render tests + dropped
engagement fixtures) is a deliberate, documented migration change rather than a
defect. **The headline B0 symptom (`${CLAUDE_PLUGIN_ROOT}` not expanded,
specialist early-death) is confirmed pre-existing and identical in the archive —
not caused by the migration** — and so are the determinism-hygiene bugs in
`dedup.py`. The "missing" agents/commands/skills/Cursor artifacts and frozen
workflow files are all intentional, spec-backed scope reductions (product.md
§5/§8) and should not be chased.

## 2. CONFIRMED migration regressions (P1, P2)

- **P1 — `dispatch-contract.md` dropped multi-planner/relay structure + 2 protocol files.**
  Line 69 says "multi-planner peers remain teammates" but the per-role table
  rows, the "How to dispatch each role in v2" table, and the multi-planner
  subsections are gone. `multi-planner-protocol.md` (0 refs here vs 4 in
  archive) and `relay-loop-protocol.md` are MISSING from `contracts/`. File is
  330 lines vs archive 376. **Fix:** restore both protocol files + the missing
  sections from the archive; resolve the line-69 contradiction. **Spec-log: yes.**
- **P2 — render/review-state tests converted to `pytest.skip()` + engagement
  fixture `docs/ecp/2026-05-01-d5ebb62c` dropped.** Intentional per commit
  `05c9883`. **No code change** — correct tracker attribution to "intentional
  migration change" and document the local fixture need. **Spec-log: yes.**

## 3. Confirmed PRE-EXISTING issues (NOT migration-caused — byte-identical in archive)

- **P1 — B3: stale fixtures missing `proposed_anchor` → 0 canonical refs.**
  Highest-value real defect. Inject `proposed_anchor` into 44 absent findings
  across `slingmods-pdp` + `awdmods-homepage`; fix 6 CLEAR ethics findings'
  effort fields to `not_applicable`. Verify: probe → 76 refs. **No spec-log.**
- **P2 — B0: `${CLAUDE_PLUGIN_ROOT}` not expanded for CC teammates (the
  specialist early-death symptom).** Real but pre-existing and NOT blocking
  (handoff: "runtime works today — leads inject preambles per-spawn"). The
  single-file `test-specialist.py` patch is **incomplete** (injects a local path
  into a remote prompt). Actionable slice = a documentation contract (below).
- **P2 — Path-resolution contract undocumented.** Add a "Path resolution
  contract" section to `dispatch-contract.md`: the lead MUST expand
  `${CLAUDE_PLUGIN_ROOT}` to absolute paths before dispatch. Docs only. **Spec-log: yes.**
- **P2 — `acquire_url.py` multi-device screenshot naming.** `acquire_url.py`
  emits `{device}-section-N.jpg` when `len(devices)>1`; `baton_v1_to_v2.py:165-166`
  hardcodes `section-N.jpg`; validation then warns "missing". **Fix in
  `acquire_url.py`** (Option A: unified `section-N(-mobile).jpg` even multi-device).
  Do NOT patch the converter. **Spec-log: yes** (naming contract).
- **P2 — `dedup.py` `id(f)` key + unsorted dict iteration.** Output is re-sorted
  downstream so deterministic today; only logging/auto-merge order varies. Code
  hygiene only — apply `sorted(...)` to the five v1 sites + replace `id(f)`.
- **P3 — smaller pre-existing items.** `html_builder.py` `datetime.now()` (HTML
  excluded from determinism gate); v1-only template placeholder; `pipeline.py`
  `id(f)` (stable in-process); deferred Phase-M test. Address with owning phase.

## 4. Refuted / uncertain (DO NOT chase)

- **#26 attributed to converter/validator** — REFUTED. Converter + validator are
  correct and pass tests; the real surface is `acquire_url.py` naming (§3).
- **B0 as a migration regression / `render_prompt()` must expand it** — REFUTED
  as a regression (identical in archive); the local-path fix is incorrect.
- **Missing plan/review/build/compare/quick-scan/reconcile workflows & contracts;
  missing `agents/`, `commands/`, Cursor suite, plugin.json properties** —
  REFUTED. Intentional frozen scope (product.md §2.4/§5/§8/§9; G21 `a0e6aba`;
  preserved in `archive/cursor-agents/`).
- **Missing `.claude/settings.local.json` / `launch.json`** — git-ignored, never
  tracked; archive `launch.json` was already broken.
- **`build_canonical_f_refs.py` dropped** — consolidated into `lead_prep.py`.
- **G15 autofix as a cause of bounces** — fixed `84cd4a4`, predates migration.
- (~20 candidates total refuted; see workflow transcript for the rest.)

## 5. Recommended "cut once" sequence

1. **B0 actionable slice + P1 dispatch-contract regression (batch — both edit
   `contracts/`, both need a spec-log entry).** Add the Path-resolution contract
   section; restore `relay-loop-protocol.md` + `multi-planner-protocol.md` and
   the deleted sections; fix the line-69 contradiction. Do NOT ship the
   incomplete `test-specialist.py` patch.
2. **B3 fixtures (highest-value functional defect; parallelizable).** Inject
   `proposed_anchor` + fix CLEAR effort fields; verify 76 refs. No spec-log.
3. **`acquire_url.py` multi-device naming.** Unify filenames; add
   `test_converter_screenshot_naming()`. Spec-log: yes.
4. **render/review-state skip-guard attribution** (docs only; fold into step 1's log).
5. **`dedup.py` determinism hygiene** (last; lowest risk; no functional impact today).

Spec-change-log entries required for steps 1, 3, 4.

## 6. Open gaps (the real "measure-twice" follow-ups)

- **TOP: No integration test proving `${CLAUDE_PLUGIN_ROOT}` + `{{...}}` are both
  resolved in a dispatched prompt AND that the teammate can actually read the
  referenced files.** This is the ONLY way to *prove* B0's runtime status rather
  than infer it. Settles the specialist-retry question empirically.
- No canary tests guarding the already-fixed determinism bugs (wire
  `determinism_probe.py` into the suite; add "no `id()` keys / sorted iteration"
  assertions).
- Fixture schema-evolution test (archive-era + new fixtures both carry valid
  `proposed_anchor`).
- Synthesizer f_refs manifest contract test (empty / >5 clusters / ambiguous scope).
- `render_prompt()` template-completeness test (no unresolved tokens ship).
- Engagement-folder retention: confirm pre-2026-05-26 engagements were pruned
  intentionally vs lost (`git log --all -- docs/ecp/`).
</content>
