# ECP Product v1 Adversarial Audit Findings

Audit date: 2026-06-09
Scope: repository conformance to `product.md` Spec v1.0.
Mode: audit-only. No code, test, or spec changes were made.

## Executive summary

The test suite is green, but the repo is not cleanly conformed to `product.md`.
The highest-risk issues are not broken Python functions; they are active
contracts that still tell the audit lead to use frozen or superseded behavior.
The most serious presentation-layer issue is that the current schema, prompt,
autofix, and renderer intentionally auto-place absence findings, while the
product spec says absence findings must always be blank.

## Findings

### P0 - Active audit load order still imports frozen/v1 runbooks

`product.md` says the canonical audit produces findings, Priority Path, and a
visual report, then stops before plan, review, or build (`product.md:70`,
`product.md:77`). It also freezes `quick-scan`, `compare`, `build`, and `resume`
(`product.md:160`) and says frozen scope may not be invoked, marketed, or relied
on as canonical (`product.md:156`).

The active `/ecp:audit` router contradicts itself. It says audit stops before
plan/review/build (`skills/audit/SKILL.md:15`) and v2 uses JSON emissions
(`skills/audit/SKILL.md:123`, `skills/audit/SKILL.md:168`), but its runtime load
table still imports stale files: `contracts/team-lifecycle.md`,
`workflows/audit.md`, `contracts/synthesizer-subagent.md`,
`contracts/priority-path-synthesis.md`, `contracts/audit-assembly.md`,
`contracts/audit-reconciliation.md`, and `contracts/progress-comparison.md`
(`skills/audit/SKILL.md:41`, `skills/audit/SKILL.md:54`,
`skills/audit/SKILL.md:56`, `skills/audit/SKILL.md:58`,
`skills/audit/SKILL.md:59`).

Those loaded files still contain concrete old instructions:

- `/ecp:audit` as a full audit -> plan -> review -> build pipeline
  (`contracts/flags.md:42`, `contracts/lead-discipline.md:17`,
  `contracts/lead-discipline.md:26`).
- Agent Teams setup, `TeamCreate`, `team_name`, `TaskUpdate`, and `SendMessage`
  (`contracts/team-lifecycle.md:53`, `contracts/team-lifecycle.md:55`,
  `contracts/team-lifecycle.md:56`, `contracts/team-lifecycle.md:58`).
- Markdown cluster files and v1 validation (`workflows/audit.md:16`,
  `workflows/audit.md:142`, `workflows/audit.md:740`,
  `contracts/audit-reconciliation.md:56`).
- `assemble-audit.py` and per-device Priority Path synthesis paths
  (`contracts/synthesizer-subagent.md:3`,
  `contracts/priority-path-synthesis.md:12`,
  `contracts/priority-path-synthesis.md:14`).

Impact: a lead following the active load order can be pulled onto mutually
exclusive paths in the same run: v2 JSON/no-team from `skills/audit/SKILL.md`,
but v1 markdown/Agent-Teams/plan-build from the files it is told to load. That
is a product conformance failure because the operator cannot trust which
contract is canonical during a client audit.

Remediation direction: remove these stale files from the active load path or
rewrite them to the v2 audit-only contract. Keep frozen/build-family material in
archive or clearly dead reference docs that `/ecp:audit` never loads.

### P0 - Absence findings are auto-placed, despite the spec's always-blank rule

`product.md` is explicit: auto-place only at about 99.9% confidence; below that,
leave the hotspot blank (`product.md:140`). It then gives the harder rule:
absence findings recommending a missing element, such as "no sticky CTA", are
always blank (`product.md:144`).

The current pipeline makes the opposite behavior load-bearing:

- The finding schema says `baton_index: "absent"` should render with a
  section-level hotspot (`schema/finding-v1.json:91`).
- The schema requires `proposed_anchor` on absent findings
  (`schema/finding-v1.json:586`, `schema/finding-v1.json:599`).
- The specialist prompt tells agents to emit that `proposed_anchor` so the
  renderer knows where the missing thing should appear
  (`contracts/specialist-prompt-v2.md:295`,
  `contracts/specialist-prompt-v2.md:297`,
  `contracts/specialist-prompt-v2.md:373`).
- Autofix injects a default section-bottom-overlay anchor when a specialist
  omits it (`scripts/assembly/emission_autofix.py:292`,
  `scripts/assembly/emission_autofix.py:309`,
  `scripts/assembly/emission_autofix.py:326`).
- The v2 marker resolver turns absent `proposed_anchor` data into coordinates
  (`scripts/report/v2_markers.py:11`, `scripts/report/v2_markers.py:727`,
  `scripts/report/v2_markers.py:746`).

The tests confirm this is intentional behavior, not dead code. The blanking test
only covers an absent finding with no `proposed_anchor`
(`tests/test_g4_blank_below_confidence.py:58`,
`tests/test_g4_blank_below_confidence.py:73`,
`tests/test_g4_blank_below_confidence.py:74`). But the stack-distribution test
uses auto-injected absent anchors and asserts those markers still render
(`tests/test_fix3_hero_stack_distribute.py:4`,
`tests/test_fix3_hero_stack_distribute.py:12`,
`tests/test_fix3_hero_stack_distribute.py:75`,
`tests/test_fix3_hero_stack_distribute.py:79`).

Impact: the product's presentation invariant is unenforceable for the very
absence findings it calls out. A missing trust strip, sticky CTA, review block,
or head metadata element can receive an automatic ghost/section placement even
though the spec says the operator must place or decline it manually. This is the
exact class where wrong placement is worse than a blank.

Remediation direction: treat `proposed_anchor` as an editor hint only for absent
findings. The report renderer should emit a hidden/unplaced marker for
`baton_index: "absent"` unless an operator override exists. Update schema,
autofix, specialist prompt, visual-evidence mapping, and tests together so the
always-blank rule becomes executable.

### P1 - Default cluster routing undercuts the full-breadth moat

`product.md` says the audit spans the full cross-domain cluster set, and lists
all 10 clusters as canonical breadth (`product.md:57`). It says breadth is the
differentiator and no trust invariant is cluster-exempt (`product.md:58`).

The active routing contract makes reduced coverage the normal path. It defines
page-type "comprehensive" defaults as only relevant subsets and "standard" as
the highest-impact 3-4 clusters (`contracts/cluster-routing.md:34`,
`contracts/cluster-routing.md:49`, `contracts/cluster-routing.md:51`). The
`--auto` default for `/ecp:audit` is `standard` 3-4 clusters
(`contracts/flags.md:57`, `contracts/flags.md:299`). The meta schema also
normalizes `focused`, `standard`, `comprehensive`, `custom`, and `everything`,
with "everything" as a separate all-10 option (`contracts/meta-schema.md:81`,
`contracts/meta-schema.md:85`).

Impact: a normal automated audit can omit canonical clusters without an explicit
degraded-mode label. The client-facing claim "full cross-domain" is only true
when the operator knows to force `everything` / `--focus all`; it is not true by
default.

Remediation direction: either make the canonical audit default to all 10
clusters, or amend `product.md` through the Spec Change Log to say page-type
subset audits are canonical. If reduced scopes remain, label them as non-full or
operator-selected variants so client runs cannot silently ship as "full breadth."

### P1 - Frozen inputs and modes remain valid active contract states

`product.md` freezes screenshot-only and codebase inputs (`product.md:161`) and
freezes quick-scan, compare, build, and resume (`product.md:160`). The active
router correctly rejects non-URL audit inputs (`skills/audit/SKILL.md:68`), and
the README/router both say frozen modes are out of scope (`README.md:19`,
`skills/ecp/SKILL.md:29`).

However, active contracts still validate or document frozen states:

- `contracts/flags.md` lists frozen modes throughout the canonical flag matrix
  (`contracts/flags.md:13`, `contracts/flags.md:39`,
  `contracts/flags.md:101`, `contracts/flags.md:197`,
  `contracts/flags.md:244`).
- `/ecp:audit` still advertises `--ab-scaffold` / `--ab-tool`, which generate
  post-audit test scaffolding after plan work (`contracts/flags.md:217`,
  `contracts/flags.md:221`, `contracts/flags.md:223`,
  `contracts/flags.md:234`).
- `contracts/device-semantics.md` documents file, description, and screenshot
  modes as active source modes (`contracts/device-semantics.md:141`,
  `contracts/device-semantics.md:145`, `contracts/device-semantics.md:146`,
  `contracts/device-semantics.md:147`).
- `contracts/meta-schema.md` still accepts `build`, `quick-scan`, and `compare`
  as engagement types and accepts file, pasted-code, screenshot, and description
  source modes (`contracts/meta-schema.md:26`,
  `contracts/meta-schema.md:115`, `contracts/meta-schema.md:118`,
  `contracts/meta-schema.md:119`, `contracts/meta-schema.md:120`,
  `contracts/meta-schema.md:121`).

Impact: even if the only discoverable shipped skill is `/ecp:audit`, downstream
agents and validators still see frozen input/mode shapes as canonical. That
keeps the reserved seams warm enough to be accidentally used and makes "URL-only,
audit-only" a router convention instead of a repository-wide contract.

Remediation direction: split active audit schema from archived/future schema, or
explicitly mark these values legacy-read-only and impossible for newly-created
v2 audit engagements. Remove build-family flags from the active audit flag
matrix unless/until a Spec Change Log entry unfreezes them.

### P2 - `product.md` governance is internally version-inconsistent

The file header says the spec version is 1.0 and that the file is the single
source of truth (`product.md:3`, `product.md:5`). The same file's change log now
contains multiple 1.1 entries (`product.md:253`, `product.md:254`,
`product.md:255`, `product.md:256`), while the governance rule says changes
require dated, rationale'd Spec Change Log entries and frozen scope only unfreezes
through such entries (`product.md:226`).

Impact: agents can reasonably disagree about whether they are auditing against
Spec v1.0 or v1.1. The user's prompt for this audit named Spec v1.0, but the
canonical file contains post-v1.0 contract changes without a matching header
version. That weakens the "constitution" role of the file.

Remediation direction: either bump the header to the latest effective version,
or relabel the 1.1 rows as contract addenda that do not change the product spec
version. The point is not which version wins; it is that the answer must be
unambiguous.

## Positive controls

- The shipped plugin surface is mostly audit-only at the top level: README and
  router describe `/ecp:audit`, and build/compare/quick-scan/resume are not
  discoverable as active skills (`README.md:19`, `skills/ecp/SKILL.md:29`,
  `skills/audit/SKILL.md:15`).
- The draft -> client-ready gate is well represented in code and tests:
  `report_state` refuses automated promotion, and the audit router states
  generated reports remain draft (`contracts/meta-schema.md:93`,
  `contracts/meta-schema.md:96`, `skills/audit/SKILL.md:194`).
- Canonical f_ref validation is well covered: synthesizer prompts and parsers
  use allowlists to reject hallucinated refs (`contracts/synthesizer-v2.md:156`,
  `contracts/synthesizer-v2.md:452`,
  `scripts/assembly/synthesizer_parser.py:260`).

## Verification performed

- `python -m pytest tests/` -> 1124 passed, 12 skipped.
- `python -m unittest discover -s tests` -> 736 tests, OK.
- Targeted presentation-layer tests also passed:
  `tests/test_g4_blank_below_confidence.py`,
  `tests/test_fix3_hero_stack_distribute.py`,
  `tests/test_g15_emission_autofix.py`.

Not run: live `/ecp:audit --plugin-dir` against an external URL. That would
create a new engagement and depends on live browser/network state; the current
task was repository audit and one findings document only.
