---
name: ecp:audit
description: >-
  Runs a full e-commerce psychology audit of an existing ecommerce page via
  four-phase relay (audit, plan, review, build). Covers product pages, checkout
  flows, carts, pricing, landing pages, category pages, and SEO using
  research-backed findings across pricing, trust, mobile, content, and visual
  design.
disable-model-invocation: true
argument-hint: "[url-or-file-path] [--auto] [--force] [--deep] [--min-priority critical|high|medium|low] [--platform shopify|nextjs|opencart] [--device mobile|laptop|desktop] [--focus cluster1,cluster2] [--visual] [--no-visual] [--ab-scaffold] [--ab-tool tool-name] [--engagement-id id]"
---

# ECP Audit Router

This skill is the runtime router for the full ECP audit relay. Keep it lean: load the contracts and workflows named below, run the phases in order, enforce the hard gates, and leave historical rationale in `SKILL.notes.md`.

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
8. P0-08: Cluster files MUST pass `scripts/validate-cluster-files.py` before assembly.
9. P0-09: Priority Path synthesis MUST use the protocol and subagent path; inline lead-authored stories are FORBIDDEN.
10. P0-10: Structural assertions in `contracts/trace-assertion-canary.md` MUST run before the audit checkpoint; assertion failure BLOCKS phase progression.
11. P0-11: v2 JSON and state writes MUST use atomic write helpers or scripts that own their output.
12. P0-12: Cancellation sentinel checks MUST happen at layer boundaries; when `cancel.flag` is present, no further dispatches happen.

## Runtime Load Order

Read these files at invocation start:

1. `contracts/lead-discipline.md`
2. `contracts/flags.md`
3. `contracts/audit-state-machine.md`
4. `contracts/dispatch-contract.md`
5. `contracts/device-semantics.md`
6. `contracts/meta-schema.md`

Then load phase-specific files only when that phase is reached.

| Phase | Load when needed |
| --- | --- |
| Input and setup | `contracts/url-validation.md`, `contracts/team-lifecycle.md`, `contracts/platform-detection.md`, `contracts/page-detection.md`, `contracts/cluster-routing.md` |
| Acquisition | `workflows/acquire.md`, `contracts/dom-preprocessor.md` |
| Specialist audit | `workflows/audit.md`, `contracts/specialist-prompt-v2.md`, relevant `references/**` files |
| Ethics | `contracts/ethics-subagent-v2.md`, `references/ethics-gate.md` |
| Synthesis | `contracts/synthesizer-v2.md`, `contracts/synthesizer-subagent.md`, `contracts/priority-path-synthesis.md` |
| Assembly and canaries | `contracts/audit-assembly.md`, `contracts/audit-reconciliation.md`, `contracts/trace-assertion-canary.md`, `contracts/progress-comparison.md` |
| Plan | `workflows/plan.md`, `contracts/multi-planner-protocol.md`, `contracts/conflict-resolution.md` |
| Review | `workflows/review.md`, `contracts/relay-loop-protocol.md` |
| Build | `workflows/build.md`, platform file under `platforms/{platform}.md` when detected |
| Export | `contracts/report-export.md`, `workflows/ab-scaffold.md` when requested |

## Mode Selection

`$ARGUMENTS` should contain a URL, file path, or description:

- URL mode: starts with `http://` or `https://`.
- File mode: points to an existing local file.
- Description mode: user describes what to audit or build and no URL/file is available.

Allowed pre-flight prompts are limited by `contracts/lead-discipline.md`: mode ambiguity, URL fetch confirmation, device selection, and audit scope selection. `--auto` uses the audit defaults from `contracts/flags.md`.

## Phase Order

Run this sequence:

1. Parse flags and choose mode.
2. Select device(s) per `contracts/device-semantics.md`.
3. Create or resume `docs/ecp/{engagement-id}` and write/update `meta.json`.
4. Create the audit team per `contracts/team-lifecycle.md`.
5. Detect platform, page type, page pattern, and cluster scope.
6. Dispatch acquisition for each requested device.
7. Verify acquisition artifacts on disk.
8. Preprocess DOM per device when DOM exists.
9. Dispatch cluster specialists for each selected cluster and device.
10. Dispatch ethics v2 after specialist emissions are present.
11. Dispatch synthesizer v2 after ethics completes or records partial status.
12. Validate cluster files, assemble audit markdown, and run structural plus substantive canaries.
13. Present the audit checkpoint unless `--auto`.
14. Dispatch planner, reviewer, and builder phases as requested or as `--auto` requires.
15. Export markdown, visual report, or A/B scaffold when requested.
16. Update `meta.json`, write `lead-reflection.md`, and clean up the team at completion.

## Dispatch Shape

Default to v2 dispatch:

- Acquirer: `Task` subagent, one per device.
- Cluster specialists: `Agent` teammates in the audit team.
- Ethics: `Task` subagent.
- Synthesizer: `Task` subagent.
- Single planner: `Task` subagent.
- Multi-planner peers: `Agent` teammates.
- Reviewer: `Task` subagent.
- Builder: `Task` subagent.

Record dispatch counters in `audit-trace.log` using `contracts/trace-assertion-canary.md`. Legacy v1 counter aliases may be accepted only where that contract explicitly says they are accepted.

## Artifact Contract

Write audit artifacts inside `docs/ecp/{engagement-id}/`:

- `meta.json`
- `audit-trace.log`
- acquisition artifacts: `baton.json` / `dom.html` for non-mobile, `baton-mobile.json` / `dom-mobile.html` for mobile
- cluster emissions: `cluster-{cluster}-{device}.md` or v2 JSON emissions as specified by the loaded workflow
- ethics emission: `ethics-findings.json`
- synthesizer emission: `synthesizer-emission-v1.json`
- audit markdown: `audit-{device}.md` for v2 device output; preserve legacy `audit.md` behavior where the current scripts require it
- `priority-path-stories.json` when priority path sidecar output is produced
- `lead-reflection.md`
- plan, review, build, report, and scaffold outputs for later phases

Use the path and field names from `contracts/meta-schema.md`, `contracts/audit-state-machine.md`, and the relevant workflow. Do not invent alternate artifact names.

## Validation And Recovery

Before audit assembly:

```powershell
python scripts/validate-cluster-files.py --engagement docs/ecp/{engagement-id}
```

Then assemble using the device and priority-path arguments required by the current workflow:

```powershell
python scripts/assemble-audit.py --engagement docs/ecp/{engagement-id} --device {device}
```

Run substantive canaries with `scripts.assembly.canary_checks.run_all_canaries` as documented in `contracts/trace-assertion-canary.md`, append summaries to `audit-trace.log`, and record anomalies in `lead-reflection.md`.

If acquisition fails after the required dispatch and correction attempt, use the manual acquisition fallback from `workflows/acquire.md` and log the degraded path. If cluster specialists fail, write an honest SKIP marker; do not replace specialist work with lead-authored findings.

## Checkpoints

Use checkpoint wording and options from the loaded workflow:

- Audit checkpoint: summary, key highlights, progress comparison when available, export options.
- Plan checkpoint: single-planner or multi-planner format.
- Review checkpoint: verdict and questions.
- Build checkpoint: build summary, export/scaffold options, done.

`--auto` skips interactive checkpoints where the workflow allows it. `--force` only overrides review BLOCK behavior where `workflows/review.md` and this skill's flags permit it.

## Exit Criteria

An audit phase can move forward only when:

- acquisition artifacts for requested devices have been verified;
- selected cluster emissions exist or skipped clusters are explicitly recorded;
- ethics has run or has a logged partial status after allowed retry;
- synthesis has produced expected v2 outputs or has a logged failure path;
- pre-assembly validation and assembly have run;
- structural assertions have passed;
- substantive canary results and lead reflection are written.

The full relay is complete when audit, plan, review, build or build-skip, exports requested by the user, `meta.json`, `audit-trace.log`, and `lead-reflection.md` all reflect the final state.
