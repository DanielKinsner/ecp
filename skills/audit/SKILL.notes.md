# ECP Audit Skill Notes

This companion holds P3 context moved out of `SKILL.md` during the information architecture reset pilot on 2026-05-05. Runtime behavior belongs in `SKILL.md`, contracts, workflows, scripts, and references. This file explains why the router points where it points.

## Why The Router Exists

The former audit skill mixed live instructions, hard gates, v1/v2 migration notes, detailed examples, fallback procedures, and historical rationale in one always-on file. That made every rule look equally urgent and forced agents to reread long context even when the canonical behavior lived elsewhere.

The router keeps the active execution surface small and makes the source of truth explicit:

- lead discipline in `contracts/lead-discipline.md`
- dispatch shape in `contracts/dispatch-contract.md`
- flags in `contracts/flags.md`
- device semantics in `contracts/device-semantics.md`
- audit state in `contracts/audit-state-machine.md`
- cluster specialist instructions in `workflows/audit.md`
- acquisition instructions in `workflows/acquire.md`
- assembly and report contracts in `contracts/audit-assembly.md`, `contracts/synthesizer-v2.md`, and `contracts/report-export.md`

## v1 To v2 Dispatch Context

The old skill carried a long inline note from Phase H, dated 2026-04-28. The important context is that v2 flipped most roles from teammate dispatch to one-shot subagent dispatch. Cluster specialists stayed as teammates because they benefit from the shared engagement workspace.

The runtime rule now lives in `contracts/dispatch-contract.md`. When the old prose says "spawn the X teammate" for acquirer, ethics, or synthesizer, the v2 interpretation is a `Task` subagent. Cluster specialists remain `Agent` teammates.

## Acquisition And Device Context

The old skill explained why each device captures its own DOM: responsive ecommerce pages often render different sections, drawers, lazy-load states, and conditional markup at different viewport widths. Mobile-specific DOM prevents false negatives on elements that only exist at mobile widths.

That rationale is historical context. The runtime contract is in `contracts/device-semantics.md`, `workflows/acquire.md`, and `contracts/dom-preprocessor.md`.

## Lead Discipline Context

The strict no-shortcut language exists because prior runs could look successful even when the lead had silently done teammate work directly. The failure mode was a believable report without independent cluster coverage.

The live rule is not "use agents because it feels purist." The live rule is that the team architecture is the evidence contract. If a role fails, the run records the failure or follows an explicit fallback. It does not pretend the role ran.

Canonical source: `contracts/lead-discipline.md`.

## Deterministic Routing Context

The old skill contained a long note explaining the switch from LLM-emitted `baton.sections[].clusters` as primary routing to deterministic keyword routing in `scripts/dom_preprocess.py`. The reason was cross-device drift: the same template could receive different cluster arrays across desktop and mobile.

Canonical sources:

- `contracts/dom-preprocessor.md`
- `contracts/cluster-routing.md`
- `scripts/dom_preprocess.py`

## Priority Path Context

The former inline instruction "The lead writes the Priority Path into audit.md using scored candidates" is retired. It created broken F-ref links when lead-authored labels drifted from renderer-assigned cluster indices.

Canonical sources:

- `contracts/priority-path-synthesis.md`
- `contracts/synthesizer-subagent.md`
- `contracts/synthesizer-v2.md`
- `scripts/assembly/synthesizer_parser.py`

## Ethics Context

v2 added a dedicated ethics layer between cluster specialists and the synthesizer. This reduces per-cluster legal drift and gives the synthesizer one canonical ethics emission to integrate.

Ethics fidelity is not part of the prompt diet. Do not compress legal or source evidence. Load the full ethics gate where the workflow requires it.

Canonical sources:

- `references/ethics-gate.md`
- `contracts/ethics-subagent-v2.md`
- `contracts/synthesizer-v2.md`

## Fallback Context

Manual acquisition and WebFetch are degraded paths, not shortcuts. The old skill repeated this because it was easy for agents to treat fallback availability as permission to skip dispatch. The current router keeps only the hard gate; the full fallback procedure lives in `workflows/acquire.md`.

Cluster failure has a different recovery model: failed specialist work becomes SKIP output, not lead-authored substitute findings. That preserves truthfulness about coverage gaps.

## Old Section Map

| Former inline section | Current source |
| --- | --- |
| no_preflight_questions | `contracts/lead-discipline.md` |
| flags | `contracts/flags.md` |
| mode_detection | `contracts/url-validation.md`, `contracts/lead-discipline.md`, router mode section |
| device_selection | `contracts/device-semantics.md` |
| engagement_setup | `contracts/team-lifecycle.md`, `contracts/meta-schema.md` |
| audit_trace_assertion_header | `contracts/trace-assertion-canary.md` |
| cost_trace_heuristic | `contracts/trace-assertion-canary.md` |
| platform_detection | `contracts/platform-detection.md` |
| page_type_detection and page_pattern_detection | `contracts/page-detection.md` |
| cluster_selection and routing | `contracts/cluster-routing.md` |
| team_lifecycle | `contracts/team-lifecycle.md` |
| auditor_dispatch_template and phase_audit | `workflows/audit.md`, `contracts/specialist-prompt-v2.md` |
| finding_reconciliation | `contracts/audit-reconciliation.md` |
| priority_path_synthesis | `contracts/priority-path-synthesis.md`, `contracts/synthesizer-subagent.md` |
| dom_preprocessor | `contracts/dom-preprocessor.md` |
| phase_ethics_v2 | `contracts/ethics-subagent-v2.md` |
| phase_synthesize_v2 | `contracts/synthesizer-v2.md` |
| audit_assembly | `contracts/audit-assembly.md`, `scripts/assemble-audit.py` |
| progress_comparison | `contracts/progress-comparison.md` |
| report_export | `contracts/report-export.md` |
| ethics | `references/ethics-gate.md`, `contracts/ethics-subagent-v2.md` |
| reference_freshness | reference file `RESEARCH_DATE` watermarks and checkpoint warnings |

## Pilot Follow-up

Do not use this pilot as permission to rewrite every runtime file. Run at least one full audit cycle with the router first. If that cycle exposes missing instructions, add the missing runtime contract to the correct contract or workflow file, then keep `SKILL.md` as the router.
