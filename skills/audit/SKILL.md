---
name: ecp:audit
description: >-
  Runs an e-commerce psychology audit of an existing ecommerce page: cited,
  element-anchored findings, a prioritized Priority Path, and an annotated
  visual report. Covers product pages, checkout flows, carts, pricing, landing
  pages, category pages, and SEO using research-backed findings across pricing,
  trust, mobile, content, and visual design.
disable-model-invocation: true
argument-hint: "[url] [--auto] [--deep] [--min-priority critical|high|medium|low] [--platform shopify|nextjs|opencart] [--device mobile|laptop|desktop] [--focus cluster1,cluster2] [--visual] [--no-visual] [--engagement-id id]"
---

# ECP Audit Router

This skill is the runtime router for the ECP audit. It produces cited, element-anchored findings, a prioritized Priority Path, and an annotated visual report, then stops — plan, review, and build are out of scope per `product.md` §2.4. Keep it lean: load the contracts and workflows named below, run the phases in order, enforce the hard gates, and leave historical rationale in `SKILL.notes.md`.

## Priority Key

- P0 Hard gate: blocks output or phase progression when violated.
- P1 Contract: required for product correctness, with an explicit recovery path where available.
- P2 Guidance: preferred behavior that improves quality or consistency.
- P3 Context: history, rationale, migration notes, and examples; see `SKILL.notes.md`.

## P0 Hard Gates

1. P0-01: The lead MUST follow `contracts/lead-discipline.md` before phase work begins.
2. P0-02: URL mode MUST validate the URL and get fetch confirmation unless `--auto` is set.
3. P0-03: Acquisition MUST dispatch acquirer subagent(s) before any manual fallback.
4. P0-04: The lead MUST verify expected acquisition files exist on disk before reading them or proceeding.
5. P0-05: Dual-device runs MUST keep each device's DOM, baton, screenshots, and audit outputs separated.
6. P0-06: Cluster audit work MUST be dispatched to cluster specialists; the lead NEVER audits a failed cluster as fallback.
7. P0-07: Ethics gate MUST execute before synthesis; BLOCK or ADJACENT ethics findings require real source URLs.
8. P0-08: Every cluster + ethics emission MUST pass validation before synthesis — `scripts/test-specialist.py validate --schema cluster-emission` for v2 JSON emissions (`scripts/validate-cluster-files.py` is legacy v1 markdown only).
9. P0-09: Priority Path synthesis MUST use the protocol and subagent path; inline lead-authored stories are FORBIDDEN.
10. P0-10: Structural assertions in `contracts/trace-assertion-canary.md` MUST run before the audit checkpoint; assertion failure BLOCKS phase progression.
11. P0-11: v2 JSON and state writes MUST use atomic write helpers or scripts that own their output.
12. P0-12: Cancellation sentinel checks MUST happen at layer boundaries; when `cancel.flag` is present, no further dispatches happen.

## Runtime Load Order

Read these files at invocation start (all paths in this section and the table below resolve from the **repo root** — the same anchor as the shell commands under "Validation, Synthesis, and Rendering", NOT relative to `skills/audit/`):

1. `contracts/lead-discipline.md`
2. `contracts/flags.md`
3. `contracts/audit-state-machine.md`
4. `contracts/dispatch-contract.md`
5. `contracts/device-semantics.md`
6. `contracts/meta-schema.md`

Then load phase-specific files only when that phase is reached.

| Phase | Load when needed |
| --- | --- |
| Input and setup | `contracts/url-validation.md`, `contracts/platform-detection.md`, `contracts/page-detection.md`, `contracts/cluster-routing.md` |
| Acquisition | `workflows/acquire.md`, `contracts/dom-preprocessor.md` |
| Specialist audit | `contracts/specialist-prompt-v2.md`, relevant `references/**` files |
| Ethics | `contracts/ethics-subagent-v2.md`, `references/ethics-gate.md` |
| Synthesis | `contracts/synthesizer-v2.md`, `contracts/priority-path-synthesis.md` (only the line-15 visible-ERROR-block rule is live; rest is v1-historical — v2 scoring is in `synthesizer-v2.md`) |
| Assembly and canaries | `contracts/audit-reconciliation.md`, `contracts/trace-assertion-canary.md` |
| Export | `contracts/report-export.md` |

> **Do NOT load these legacy files for an audit run** — they describe pre-v2 mechanics that contradict the v2 contracts above and each carries a dead/frozen header explaining why: `workflows/audit.md` (v1 Agent-Teams teammate model — SendMessage huddles, `SYNTHESIS_HINT` peer messaging, markdown emission); `contracts/synthesizer-subagent.md` (v1 per-device synthesizer post-`assemble-audit.py` flow — superseded by `contracts/synthesizer-v2.md`); `contracts/audit-assembly.md` (v1 `audit.md` template — v2 emits `audit-{device}.md` from the synthesizer directly); `contracts/progress-comparison.md` (frozen per §5, compare family); `contracts/team-lifecycle.md` (dead for the audit path since the 2026-06-01 §10 migration; retained as a §7 interface contract for the frozen multi-planner family).

## Mode Selection

`$ARGUMENTS` must contain a **URL** — the only canonical input (`product.md` §2.2):

- URL mode: starts with `http://` or `https://`.

URL is the sole supported audit input. Screenshot-only and codebase/file inputs are frozen (`product.md` §5) and are not accepted here; if `$ARGUMENTS` is not a URL, ask for one per `contracts/lead-discipline.md`.

Allowed pre-flight prompts are limited by `contracts/lead-discipline.md`: URL detection, URL fetch confirmation, device selection, and audit scope selection. `--auto` uses the audit defaults from `contracts/flags.md`.

## Phase Order

Run this sequence:

1. Parse flags and choose mode.
2. Select device(s) per `contracts/device-semantics.md`.
3. Create or resume `docs/ecp/{engagement-id}` and write/update `meta.json`.
4. Detect platform, page type, page pattern, and cluster scope.
5. Dispatch acquisition for each requested device. The acquirer invocation MUST pass `--allow-existing` (step 3 already created the dir): acquisition **merges** its quick-scan fields into the lead's `meta.json` — lead-authored fields win, so `engagement_status`/`report_state`/`reflection_state`/`clusters` survive — instead of clobbering it, and **auto-upgrades** each v1-shape baton to the v2 schema in place (`baton{,-mobile}.json` become v2; the raw v1 is preserved as `baton{,-mobile}.v1raw.json`). No separate `baton_v1_to_v2.py` step is needed on the happy path — run it manually only to recover a v1 baton.
6. Verify acquisition artifacts on disk (the on-disk `baton{,-mobile}.json` are already v2-shape — that is what validation, synthesis, and render consume).
7. Preprocess DOM per device when DOM exists.
8. Dispatch cluster specialists for each selected cluster and device — **full-parallel by default** (spawn all requested clusters in one message). Concurrency is capped server-side; if transient rate limits appear, use the `--max-concurrent N` flag to batch spawns into waves (documented in `contracts/flags.md`). The flag defaults to unlimited (all clusters at once). Wait for each batch's file-presence signal (via glob `cluster-{cluster}-{device}.json`) before proceeding to the next phase layer. See `contracts/dispatch-contract.md` §"Why specialists are one-shot subagents" point 1 for the transport-shape rationale.
9. Dispatch ethics v2 after specialist emissions are present.
10. Validate every specialist + ethics emission, build the canonical f_refs manifest, and trim each device baton, then dispatch synthesizer v2 (after ethics completes or records partial status).
11. Validate the synthesizer emission, run the cross-device drift gate, and run structural plus substantive canaries (see "Validation, Synthesis, and Rendering").
12. Present the audit checkpoint with export options.
13. Export the audit markdown and the annotated visual report when requested.
14. Update `meta.json`, write `lead-reflection.md`, run `generate-report.py --mark-reflection-complete` to flip `meta.json` `reflection_state` from `draft` to `complete` (G23, 2026-05-28). Do NOT clean up any team at completion (no team was created in audit v2 flow).

## Dispatch Shape

Default to v2 dispatch:

- Acquirer: one `Task` subagent per engagement — `scripts/acquire_url.py --both` captures both devices in a single Task (the canonical path), or one Task per device if the lead fans out by hand. The acquirer counter increments **per baton emitted** (1 per device captured), NOT per Task call, so a `--both` run records `subagent_spawned_acquirers: 2` (see `contracts/trace-assertion-canary.md`).
- Cluster specialists: one-shot subagent (`Agent` tool, no `team_name`).
- Ethics: `Task` subagent.
- Synthesizer: `Task` subagent.

All dispatch targets the **inline subagent contracts** via the Agent/Task tools — the acquirer runs `scripts/acquire_url.py` (the canonical deterministic acquirer), specialists use `contracts/specialist-prompt-v2.md`, ethics uses `contracts/ethics-subagent-v2.md`, synthesizer uses `contracts/synthesizer-v2.md`. The lead NEVER delegates to an `ecp-*` agent file. Any `ecp-orchestrator` / `ecp-acquisition` / `ecp-cluster-auditor` / `ecp-reviewer` / `ecp-synthesizer` agent that the Agent tool's type list may surface is a **frozen Cursor archive** (product.md §5/§8, now relocated to `archive/cursor-agents/`) and must not be selected as a delegation target — the "orchestrator" role is just this audit lead under a Cursor-era name.

Record dispatch counters in `audit-trace.log` using `contracts/trace-assertion-canary.md`. Legacy v1 counter aliases may be accepted only where that contract explicitly says they are accepted.

## Artifact Contract

Write audit artifacts inside `docs/ecp/{engagement-id}/`:

- `meta.json`
- `audit-trace.log`
- acquisition artifacts: `baton.json` / `dom.html` for non-mobile, `baton-mobile.json` / `dom-mobile.html` for mobile
- cluster emissions: `cluster-{cluster}-{device}.json` (v2 — live); the v1 `cluster-{cluster}-{device}.md` markdown form is legacy, not produced by a v2 run
- ethics emission: `ethics-findings.json`
- synthesizer emission: `synthesizer-emission-v1.json`
- audit markdown: `audit-{device}.md` for v2 device output; preserve legacy `audit.md` behavior where the current scripts require it
- `priority-path-stories.json` when priority path sidecar output is produced
- `lead-reflection.md`
- `visual-report-{device}-v2.html` when a visual report is requested (v2 renderer; laptop is just `visual-report-v2.html`). The legacy v1 renderer writes `visual-report.html` / `visual-report-{device}.html` with no `-v2` suffix.

Use the path and field names from `contracts/meta-schema.md`, `contracts/audit-state-machine.md`, and the relevant workflow. Do not invent alternate artifact names.

## Validation, Synthesis, and Rendering

This skill runs the **v2 JSON-emission pipeline**: specialists, ethics, and the synthesizer emit structured JSON (`cluster-{cluster}-{device}.json`, `ethics-findings.json`, `synthesizer-emission-v1.json`) and hotspots resolve by `e_index` lookup. Run these steps in order once specialist and ethics emissions exist. Commands run from the repo root; substitute `{id}`, `{cluster}`, `{device}`, and `{plugin-root}`. The exact synthesizer dispatch wiring (canonical-f_refs file plumbing, prompt placeholders) lives in the Synthesis-phase contracts (`contracts/synthesizer-v2.md`, `contracts/priority-path-synthesis.md`); the steps below are the orchestration spine and the commands that are stable regardless of that wiring.

1. **Validate every specialist + ethics emission** (P0-08), one call per emission:
   ```powershell
   python scripts/test-specialist.py validate --emission-path docs/ecp/{id}/cluster-{cluster}-{device}.json --schema cluster-emission --baton-path docs/ecp/{id}/baton.json
   ```
   Validate the ethics emission against both batons (`--schema cluster-emission --desktop-baton-path ... --mobile-baton-path ...`). On failure, **first try autofix** (G15 P1-3) for known-safe shape traps catalogued from live runs (path-form telemetry, duplicate finding tuples, overlong `proposed_anchor.reason`, missing `proposed_anchor` on absent findings):
   ```powershell
   python scripts/test-specialist.py autofix --emission-path docs/ecp/{id}/cluster-{cluster}-{device}.json --in-place
   ```
   Re-run `validate` against the autofixed emission. If validation now passes, proceed (the `--in-place` repairs were semantically conservative and the repairs log is at `<emission>.repairs.json`). If validation still fails, use `scripts/test-specialist.py --write-retry-prompt <path>` to generate a fresh-dispatch prompt with the validation error embedded, then re-dispatch a **fresh one-shot subagent** via `Agent(subagent_type="general-purpose", description="...", model="opus", prompt=<retry-prompt>)`. On second validation failure, you MAY apply one narrow **normalize** edit IF AND ONLY IF it is mechanical/schema/placement-only — e.g. a surface-field correction, a stray `proposed_anchor` removal (via the `<delete>` sentinel; `evidence_anchors` is NOT normalizable), a telemetry-prefix strip, a null→empty-string coercion. The only supported writer is `scripts/test-specialist.py normalize`; pass the same validation context you would pass to `validate` (for example `--baton-path`, `--desktop-baton-path`, `--mobile-baton-path`, and/or `--anchor-candidates-path`) so schema and business-rule validation both run before any write:
   ```powershell
   python scripts/test-specialist.py normalize --emission-path docs/ecp/{id}/cluster-{cluster}-{device}.json --field <field> --new-value <json-or-string> --finding-local-id <n> --reason "<one-line reason>" --baton-path docs/ecp/{id}/baton.json --in-place
   ```
   A normalize edit is permitted only when ALL of these hold: (a) it changes ONLY schema/placement/shape metadata, NEVER substantive client-facing prose (title, observation, recommendation, why-this-matters, citation, or any source URL — those are NEVER normalizable and force a re-dispatch or a `partial` skip); (b) the `normalize` command exits 0 after schema plus business-rule validation; and (c) the emitted `<emission>.normalizations.json` sidecar records the field, before/after values, reason, and timestamp. Also record the operator-facing reason in `audit-trace.log` and `lead-reflection.md` "Deviations observed". If the failure cannot be fixed by such a mechanical normalize, mark the cluster "partial" and continue. Do NOT otherwise hand-edit an emission beyond what autofix repaired.

2. **Build the canonical f_refs manifest** (after all specialists + ethics validate):
   ```powershell
   python scripts/lead_prep.py build-canonical-frefs --engagement docs/ecp/{id}
   ```
   Writes `canonical-f-refs.json` (`{valid_refs, by_canonical_ref}` — the shape steps 4-5 consume) plus `canonical-f-refs-manifest.json` + `.md` (tooling + the markdown the synthesizer prompt inlines). All three are serialized from one `report/v2_loader.build_canonical_view` call, so they are exactly the renderer's allowlist and cannot drift. These are the canonical f_refs the synthesizer must cite.

3. **Trim each device baton to referenced elements** before synthesizer dispatch (mandatory — prevents 1M-context overflow). Use `scripts/assembly/synth_input.trim_baton_file`, which writes a trimmed baton plus a `baton-{device}-trimmed-summary.json` sidecar. Feed it Findings from the **v2 JSON loader** `assembly.json_parser.parse_emission_files(cluster_paths).findings` (the same loader `lead_prep.py build-canonical-frefs` already uses) — NOT `assembly.parser.load_all_cluster_files`, which is the v1 markdown loader and raises `FileNotFoundError` on a v2 engagement (see "do NOT run" below). The synthesizer prompt points at the trimmed batons.

4. **Prepare and dispatch the synthesizer** (Task subagent) per `contracts/synthesizer-v2.md`, feeding it the cluster emissions, ethics findings, the trimmed batons (step 3), and the canonical f_refs (step 2):
   ```powershell
   python scripts/test-specialist.py prepare-synthesizer --engagement-id {id} --cluster-emission docs/ecp/{id}/cluster-{cluster}-{device}.json --ethics-findings-path docs/ecp/{id}/ethics-findings.json --desktop-baton-path <trimmed-desktop-baton> --mobile-baton-path <trimmed-mobile-baton> --canonical-f-refs-path docs/ecp/{id}/canonical-f-refs.json --out docs/ecp/{id}/.prompts/synthesizer.txt
   ```
   (`--cluster-emission` is repeated once per emission.) The synthesizer emits `synthesizer-emission-v1.json` plus `audit-desktop.md` / `audit-mobile.md`.

5. **Validate the synthesizer emission** (Phase F.4) against the canonical f_refs allowlist:
   ```powershell
   python scripts/test-specialist.py validate --emission-path docs/ecp/{id}/synthesizer-emission-v1.json --schema synthesizer-emission --finalized-findings docs/ecp/{id}/canonical-f-refs.json
   ```

6. **Run the cross-device drift gate** (Phase F.3):
   ```powershell
   python scripts/test-specialist.py drift-check --desktop-md docs/ecp/{id}/audit-desktop.md --mobile-md docs/ecp/{id}/audit-mobile.md --synthesizer-emission docs/ecp/{id}/synthesizer-emission-v1.json
   ```
   This auto-appends a `# DRIFT GATE` block (verdict + `max_ratio` + worst f_ref) to `audit-trace.log` on every run — you do **not** need to mirror the ratio into the trace by hand. If it FAILs and you resolve it by editing a synced finding, just re-run: the second block records the re-PASS, so the failure→fix is reconstructable from the two adjacent blocks (`contracts/trace-assertion-canary.md` "DRIFT GATE block").

7. **Run substantive canaries** with `scripts.assembly.canary_checks.run_all_canaries` as documented in `contracts/trace-assertion-canary.md`; append summaries to `audit-trace.log` and record anomalies in `lead-reflection.md`.

8. **Render the visual report** (v2 is auto-detected from `synthesizer-emission-v1.json`; `--v2` forces it), one call per device:
   ```powershell
   python scripts/generate-report.py --v2 --engagement docs/ecp/{id} --device {device} --plugin-root {plugin-root} --audit audit-{device}.md
   ```
   The render prints a deterministic **Placement QA** line (`weak_placements` + `≥3-on-a-pixel` stacks) — the free Tier-0 signal. Surface a non-zero count at the checkpoint. When `--visual` is set, escalate per device to the `ecp-visual-qa` vision gate at the flag-mapped tier (`standard`, or `deep` with `--deep`; `--auto` stays `free`). See `contracts/report-export.md` "Post-render placement QA".

**Legacy v1 tools — do NOT run on a v2 engagement.** `scripts/validate-cluster-files.py`, `scripts/assemble-audit.py`, and `scripts/assembly/parser.py` (the `load_all_cluster_files` loader, re-exported from `scripts/assembly/__init__.py` so an import auto-complete can land on it) parse v1 `cluster-{cluster}-{device}.md` markdown. On a v2 JSON engagement they find zero findings or raise `FileNotFoundError` on the missing `.md` files; they exist only for replaying archived v1 markdown engagements. For v2 JSON, use `scripts/assembly/json_parser.py` `parse_emission_file(s)` instead. The v1 `audit.md` template lives in `contracts/audit-assembly.md`.

**Recovery.** If acquisition fails after the required dispatch and correction attempt, use the manual acquisition fallback from `workflows/acquire.md` and log the degraded path. If cluster specialists fail, write an honest SKIP marker; do not replace specialist work with lead-authored findings. If the synthesizer truncates or emits an unparseable `synthesizer-emission-v1.json`, `scripts/build_synthesizer_emission_fallback.py` rebuilds a valid emission from the cluster + canonical-f_refs inputs (Phase J emergency tooling; covered by `tests/test_synth_emission_fallback.py`) — it is a recovery aid, not a normal pipeline step.

## Checkpoints

Use checkpoint wording and options from the loaded workflow:

- Audit checkpoint: summary, key highlights, progress comparison when available, export options.

`--auto` runs straight through to the report without pausing at the audit checkpoint.

## Exit Criteria

An audit phase can move forward only when:

- acquisition artifacts for requested devices have been verified;
- selected cluster emissions exist or skipped clusters are explicitly recorded;
- ethics has run or has a logged partial status after allowed retry;
- synthesis has produced expected v2 outputs or has a logged failure path;
- pre-assembly validation and assembly have run;
- structural assertions have passed;
- substantive canary results and lead reflection are written.

The audit is complete when findings, the Priority Path, any requested exports (audit markdown + visual report), `meta.json`, `audit-trace.log`, and `lead-reflection.md` all reflect the final state.

The generated report always ships as a **DRAFT** (`meta.json` `report_state: "draft"`, per `contracts/meta-schema.md` / product.md §6). Never write `report_state: "client-verified"` from the audit flow — and never under `--auto`. Client-ready promotion is the operator's manual verification pass (re-check the live site, follow every legal/ethics citation link, finalize hotspot placement), run separately via `generate-report.py --engagement <dir> --mark-client-verified`.

The `lead-reflection.md` narrative ALSO ships as a **DRAFT** (`meta.json` `reflection_state: "draft"`, per `contracts/meta-schema.md` / G23, 2026-05-28). After the canaries pass and the reflection narrative has been written/refreshed against the actually-completed on-disk state, the lead invokes `generate-report.py --engagement <dir> --mark-reflection-complete` to attest that the narrative matches the pipeline's actual end-state. This is the explicit verb the G23 state machine gates on; **never write `reflection_state: "complete"` directly or under `--auto`.** Premature reflection writes (e.g. an agent acting on a stale-partial pipeline view) leave the state at `draft`, so the operator knows at a glance whether the narrative is finalized.
