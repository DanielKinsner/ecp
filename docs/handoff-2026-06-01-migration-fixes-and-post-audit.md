# Handoff — Migration fixes + post-audit state (2026-06-01)

Audience: the next agent (and Dan) picking up ECP. This is a pointer document —
read `product.md` (constitution) and the referenced docs rather than re-deriving.

## 1. TL;DR — where things stand

The Cursor→Claude Code migration left a class of bugs that made cluster
specialists fail/retry during audits. Those are now **fixed and verified**:

- **The specialist-retry root cause was B0:** Claude Code does NOT expand
  `${CLAUDE_PLUGIN_ROOT}` inside spawned-teammate prompts (Cursor did), so
  teammates received literal `${CLAUDE_PLUGIN_ROOT}/references/...` paths, their
  reference reads 404'd, and they died after ~5 tool calls → retry. Fixed by
  expanding the variable to an absolute path at render time
  (`scripts/test-specialist.py`).
- **Empirically confirmed in a live audit** (`docs/ecp/2026-06-01-749a3c3d`):
  the rendered `specialist-*.txt` prompts contain **0** literal
  `${CLAUDE_PLUGIN_ROOT}` and read from the absolute `…/ecp/references/`.
- **11 bite-size commits on `main`** (see §3); **full backend suite 966 passed /
  0 failed**; a 7-file, 80-case **regression net** guards every fix.

**Important nuance:** the live audit STILL had **3 specialist retries** — but these
are the *normal, pre-existing* validation self-healing loop (schema-nesting drift),
**not** the migration regression. The archive proved pre-migration runs retried
too. B0 fixed the *read-failure* retries; the *validation* re-dispatches are
expected and auto-resolve. Reducing their frequency is a quality-of-life
improvement (§4), not a bug.

## 2. Evidence: the 749a3c3d live audit

- **B0 held:** rendered specialist prompt → absolute reference paths, zero literal vars.
- **#26 held:** screenshots on disk are `section-N.jpg` / `section-N-mobile.jpg`
  (no `{device}-` prefix); the acquire naming fix worked.
- **3 validation retries (all auto-resolved, 12/12 emissions validate):**
  - `visual-cta-mobile` — PASS finding declared Silver tier but omitted required `reference_citations`.
  - `content-seo-mobile` — 4 findings vs the 5–8 band → re-dispatched, returned 6.
  - `performance-ux-mobile` — `template_id` under `observed_anchor` + `e50` outside the candidate registry + **`expected_overlay` at finding level instead of nested in `visual_evidence`** (2 corrective messages). This nesting drift recurs across runs.
- **New issues the live run surfaced** (from `lead-reflection.md`, NOT yet fixed unless noted):
  - **Converter JSON-LD bug:** `baton_v1_to_v2.py` set `page_head.schema_jsonld = structured_data or []`, but a single-object (dict) `structured_data` fails schema (must be array). Required a manual normalize+rerun. **(Fixed this session — see §3 if the `fix(converter)` commit is present.)**
  - **Acquirer emits v1-shape batons** → always needs `baton_v1_to_v2.py`. Should emit v2 directly.
  - **Mobile screenshot coverage:** deterministic acquirer captured only ~top 27% of an 8640px mobile page (anchoring unaffected — full DOM/element list — but screenshot evidence is top-weighted).
  - **Ethics enum near-miss:** `effort.change_scope: "element"` (invalid) needed manual normalize to `"single-file"`; autofix could learn this.

## 3. What landed on `main` (commits, newest first)

```
31d916a  test: regression guardrails locking in the migration fixes (80 cases)
17c0078  docs(spec-log): B0 path-resolution, P1 dispatch-contract, #26 naming
778b725  fix(P1): restore dropped multi-planner/relay dispatch structure
fcaa8ae  fix(#26): acquire_url emits unified section-N(-mobile).jpg
21e8827  chore(windows): ASCII-safe print in determinism_probe
e72b631  fix(B0): expand ${CLAUDE_PLUGIN_ROOT} to absolute at render  ← the retry fix
cf98d97  fix(B3): refresh stale fixtures (0->83 / 12->96 canonical refs)
1595b12  fix(B5): content-derived key for absent-finding dedup (drop id(f))
8804233  fix(B4): generated_date from engagement inputs, not wall clock
e40a178  fix(B2): visual_quality.py `from report.` not `from scripts.`
904eb68  docs: measure-twice migration reinvestigation report (decision record)
```

(Plus any `fix(converter)` commit added in §2.) Spec-change-log entries for the
contract-touching fixes (B0, P1, #26) are in `product.md` §10 (v1.1).

## 4. Next steps (prioritized; breadth)

**A. Concrete bugs surfaced by the live run (highest signal — real, scoped):**
1. **Harden `baton_v1_to_v2.py`** — coerce a non-list `structured_data` to a list before assigning `schema_jsonld`. (Done this session if `fix(converter)` is in the log; otherwise do it first — it caused a manual workaround in 749a3c3d.)
2. **Make `acquire_url.py` emit v2 (baton-v1.json) batons directly** — eliminates the v1→v2 conversion step and the JSON-LD class of bug. Bigger change; check `project_ecp_acquire_url_v1_baton`.
3. **Full-height mobile screenshot sampler** — current acquirer top-weights tall mobile pages.

**B. Reduce validation re-dispatches (quality-of-life, not bugs):** the 3 recurring retry classes are citation-on-PASS-Silver, finding-count-band, and `expected_overlay`/`observed_anchor` nesting. Tighten the worked examples in `contracts/specialist-prompt-v2.md` and/or extend `scripts/test-specialist.py autofix` to repair these near-misses (incl. ethics `change_scope: "element" -> "single-file"`). The schema/prompt are correct; sonnet just drifts on the complex `visual_evidence` nesting.

**C. Empirical determinism:** run a live **Mode-A N≥5** gate on a freshly-captured engagement for a real TARr/TARa. The gate infra is verified working (`tests/test_v2_determinism_gate.py` 37 passed; probe stable at 83/96 refs); this is the live-LLM number.

**D. Documented backlog (deferred, low-priority):** dedup v1 `sorted()` hygiene at the five v1 sites; `ecp_configurator.py` `{device}-configured.jpg` prefix (not a section screenshot, doesn't violate the contract today); gitignore the scratch `determinism-probe-report.json`.

**E. Housekeeping:** several **locked workflow worktrees** under `.claude/worktrees/wf_*` persist (harness scratch from this session's dynamic-workflow runs). They're separate checkouts, not main-tree files; the runtime should reclaim them, or `git worktree remove --force` once unlocked.

## 5. Dynamic workflows as a path forward

This session used ad-hoc **dynamic workflows** heavily and successfully — broad
discovery, an adversarial "measure-twice" review (50 agents) that corrected wrong
diagnoses, parallel fix implementation, and the guardrail-test net. That pattern
(fan-out → adversarial verify → synthesize; implement-in-worktrees → apply+commit)
is a good template for future batches.

**See `docs/2026-05-31-dynamic-workflows-determinism-plan.md`** for the deeper plan.
Status update against it:
- Its **§2 "concrete bugs" (B1–B5 class)** are now largely addressed (B2/B4/B5 fixed;
  B0 was the real one; the L2 boundary bugs it named are closed or guarded).
- Its **determinism-gate workflow (Fit #1)** is lower urgency now that the gate runs
  green — but a `.claude/workflows/ecp-determinism-gate.js` that runs Mode-A N≥5
  unattended (step C above) is still the clean way to get the real number.
- Its **§7 report-QA / verification workflow** (verify hotspots, citations, claims;
  loop until clean) remains the **highest direct product value** — it targets report
  *correctness* (`product.md` §6 draft→client-ready), orthogonal to the determinism
  work just completed. A PoC (`.claude/workflows/ecp-report-qa.js`) already exists.
- **B1 (renderer honoring `_drops`)** from that plan is NOT done and is still worth
  doing (make finding-loss loud at render time, not just at `lead_prep`).

## 5b. Vendor-backed: migrate specialists OFF Agent Teams (highest-leverage)

Research (2026-06-01) against current `code.claude.com/docs` confirms + extends this
session's findings:

- **Agent Teams is still experimental** (disabled by default; needs
  `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`; min v2.1.32; no GA). Docs ship it under a
  `<Warning>` with known limitations in session resumption, task coordination, and
  **shutdown behavior**.
- **The `TeamDelete` "Cannot cleanup team with N active members" we hit is that
  documented shutdown limitation — NOT an ECP bug.** Specialists ack the shutdown and
  go idle instead of exiting.
- **Vendor guidance:** stateless "read → analyze → write one JSON → exit, no peer
  messaging" workers (= v2 cluster specialists) should be **parallel one-shot
  subagents, NOT Agent Teams.** Teams are for teammates that share findings / challenge
  / coordinate — which v2 specialists never do.
- **B0 fixed the path-resolution symptom *inside* teams; this removes the fragility.**

**Options (ranked for ECP):**
1. **Parallel one-shot subagents** — `Agent` tool (renamed from `Task` in v2.1.63), GA/stable; fresh context each; `background: true` for concurrency; ~3× cheaper than teams; no teardown, no idle stream. **Minimal change** (swap the cluster-specialist dispatch shape; keep the lead's wave-of-≤5 + validate→autofix→re-dispatch logic). Removes the shutdown bug + idle noise directly.
2. **Dynamic Workflow** (v2.1.154+) — best *structural* fit: a `pipeline()` fans out specialists and runs validate→autofix→re-dispatch as stages with the concurrency cap, result caching, and **resume** built in; deletes the idle-notification interpretation + manual `ls cluster-*.json` polling. Maps ~1:1 onto the current dispatch contract. Research-preview.
3. **Multiagent Sessions** (Claude Agent SDK, beta) — only relevant if ECP moves off the CLI.

**Keep multi-planner on teams** if/when it returns — peer `SendMessage` negotiation is
the one thing only teams provide (this is why the P1 restoration kept multi-planner as
the sole teammate role).

Two concrete entry points when picking this up: (a) **low-effort** — a focused diff to
`contracts/dispatch-contract.md` + the `skills/audit/SKILL.md` dispatch step swapping the
cluster-specialist row from `Agent`-teammate to parallel one-shot subagent; or
(b) **high-leverage** — a prototype `pipeline()` workflow running the
specialist→validate→re-dispatch loop end-to-end. Either is a **spec-change-log** entry
(touches the dispatch contract). Sources: `code.claude.com/docs` sub-agents, workflows,
agent-sdk/subagents, changelog.

## 6. Key reference docs

- `docs/2026-06-01-migration-reinvestigation-measure-twice.md` — the decision record (what was confirmed/refuted; 20 refuted false leads not to re-chase).
- `docs/2026-05-31-dynamic-workflows-determinism-plan.md` — determinism + workflows plan.
- `product.md` §10 — Spec Change Log (v1.1 entries for B0/P1/#26).
- `contracts/dispatch-contract.md` — the "Path resolution contract" (B0) + restored multi-planner/relay structure; `contracts/relay-loop-protocol.md`, `contracts/multi-planner-protocol.md` (restored).
- `tests/test_b0_prompt_resolution.py` + the other 6 guardrail tests — what protects the fixes.

## 7. How to verify on pickup

```powershell
cd "C:\Users\SM - Dan\Documents\GitHub\ecp"
python -m pytest tests/ -q                              # expect 966 passed
python -m pytest tests/test_v2_determinism_gate.py -q   # determinism gate (37)
# B0 spot-check: render a specialist prompt, confirm 0 literal vars
python scripts/test-specialist.py prepare --cluster pricing --device desktop --engagement-id slingmods-pdp --cluster-context-path fixtures/slingmods-pdp/cluster-context-pricing-desktop.json --baton-path fixtures/slingmods-pdp/baton.json --viewport-width 1440 --viewport-height 900 --out $env:TEMP\chk.txt
# then: Select-String $env:TEMP\chk.txt -Pattern 'CLAUDE_PLUGIN_ROOT'  → 0 matches
```

The ultimate field test: **run a real audit** and confirm specialists no longer
retry on *reference reads* (validation re-dispatches may still occur and are fine).
</content>
