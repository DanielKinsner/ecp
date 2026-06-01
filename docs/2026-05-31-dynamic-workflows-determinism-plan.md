# Plan — Dynamic Workflows & the Non-Determinism Diagnosis (2026-05-31)

**Status:** Diagnostic + plan. No pipeline code was changed by this pass — only a
new read-only harness (`scripts/diagnostics/determinism_probe.py`) was added.
**Author:** Claude (Opus 4.8), max-effort autonomous pass for Dan.
**Audience:** the next agent (and Dan, on a different machine in the morning).
**How to read:** §1 is the answer. §2 is the diagnosis with tonight's evidence.
§3 is the dynamic-workflows verdict (how/why). §4 is the recommended sequence.
§5 is "where to look / how to independently re-diagnose." §6 is risks + what I did
NOT verify.

> Provenance note: line numbers are from the 2026-05-31 `main` tree
> (`DanielKinsner/ecp`). The repo lives under OneDrive and is worked on from
> multiple machines, so verify paths against `HEAD` before acting. The Glob tool
> was unreliable on the OneDrive path tonight (returned "no files found" for paths
> that exist); prefer `Get-ChildItem` / direct reads on this repo.

---

## 1. TL;DR — the answer to "would dynamic workflows help?"

**Qualified yes — but narrowly, and NOT as a fix for the non-determinism you're
seeing.** Three claims, in priority order:

1. **The non-determinism is mostly NOT an orchestration problem, so dynamic
   workflows do not "fix" it.** Tonight's empirical work shows your symptoms are
   driven by (a) the **live page changing between runs**, (b) **LLM word-choice in
   the specialists/synthesizer feeding the finding identifiers**, and (c) **a small
   number of concrete bugs in the supposedly-deterministic layers** — none of which
   a workflow touches. The deterministic Python itself is *clean* (proven below).

2. **Dynamic workflows ARE a strong, specific fit for ONE thing right now: the
   determinism gate.** `scripts/run-determinism-gate.py`'s own docstring says *"the
   lead is the orchestrator, this script is the coordinator."* Its documented loop —
   `for N in 1..n: prep → fan out ~20 specialists → barrier → ethics → build-frefs →
   synthesizer → validate → aggregate` — is a dynamic workflow being executed *by
   hand* across 5–12 hours. That is the textbook `pipeline()`/`parallel()` shape, and
   running it by hand means lead-orchestration drift contaminates the very
   measurement. This is also exactly your "audit the plugin with a dynamic workflow"
   idea — same artifact. **Build this first.**

3. **Dynamic workflows are a reasonable LATER fit for the production audit spine —
   but only after the bugs are fixed, and only as hardening, not as a determinism
   cure.** The `/ecp:audit` orchestration (an 8-command synth/render sequence + a
   "waves of ≤5" fan-out the lead runs by reading prose in `skills/audit/SKILL.md`)
   could become a saved workflow that makes validation + the drop-check *mandatory
   stages*. That converts "dispatch discipline held end-to-end (this run)" from a
   per-run hope into a guarantee and kills cross-machine orchestration drift. It does
   **not** make findings deterministic.

**Plugin-mechanics reality (confirmed):** a Claude Code *plugin* cannot ship or
auto-run a workflow — `workflows/` is not a plugin component. Workflows are a
user-side, opt-in primitive. Because you are the sole operator, the viable shape is
a **saved script in `.claude/workflows/` inside this repo** (project-scoped, version
controlled), invoked with the opt-in path. Details + sources in §3.4.

> **Addendum §7 (added 2026-06-01, on follow-up):** there is a *second*, product-facing
> use of workflows that is orthogonal to determinism and arguably higher direct value —
> an **agentic report-QA / verification workflow** that automates `product.md` §6's
> draft→client-ready trust gate (verify hotspots, citations, and claims; loop until
> clean). A PoC run tonight caught a **materially false finding** and a **mis-cited
> claim** in the slingmods fixture. See §7.

---

## 2. Diagnosis — why the reports/findings are non-deterministic

Think of it as four layers stacked from "unfixable physics" to "our bugs." Your
three reported symptoms (findings differ run-to-run, hotspots drift/drop, the HTML
itself varies) each have causes spread across these layers.

### L0 — The audited page is non-stationary (fundamental)
Every audit re-fetches a **live** URL. Dynamic content, the merchant's own A/B
tests, personalization, lazy-load, cookie/consent walls, and time-of-day changes
mean two captures yield different DOMs → different baton element ordering → different
`eN` indices → different `baton_index` on findings → different content-hash F-NN and
different hotspot targets. Re-captured **screenshots** alone guarantee the report
bytes differ run-to-run (different pixels → different base64 → different HTML). This
is why byte-identical reports across full re-runs are **impossible by construction**,
and why the team already defined the determinism gate's "Mode A" as *frozen-input
replay* (`run-determinism-gate.py` docstring). Working on multiple machines amplifies
this (env/timing/sync differences). **No code or workflow removes L0** — only
capture-once-replay does.

### L1 — LLM variance feeds the finding identifiers (dominant controllable cause)
The deterministic identifier scheme is only as stable as the **LLM-authored text it
hashes**. Two specific seams:

- **`_content_hash_for_finding`** (`scripts/assembly/pipeline.py:80`) computes the
  display index as `sha256(surface | baton_index | verdict)[:6] mod 99 + 1`. `surface`
  and `verdict` are written by the specialist. A one-word rephrase of `surface` moves
  the F-NN.
- **`cross_device_title_merge`** (`scripts/assembly/pipeline.py:295`) decides whether a
  desktop+mobile pair collapses into one finding by comparing
  `normalize_finding_title()` (`pipeline.py:258`) — the **first clause of the
  LLM-authored title**. Rephrasing the title can flip a merge, changing the finding
  *count*, the F-NN values, and the hotspots.
- The renderer only shows `verdict ∈ {FAIL, PARTIAL}` (`v2_loader.py:624`). A borderline
  finding the model flips to `PASS` on a re-run **disappears** from the report.

**Proven tonight** (real slingmods fixture, 76 findings): perturbing the `surface`
of one finding from `hero-pricing-paypal` → `hero-pricing-paypal-zone` moved it from
**`visual-cta F-84` → `visual-cta F-40`**. Nothing in the Python changed — only the
model's word. This is the engine of "findings differ / hotspots drift." The
content-hash scheme was a deliberate attempt to *stabilize* identifiers across runs
(see the `pipeline.py:80` docstring), and it does remove *positional* coincidence —
but it cannot stabilize against the model rephrasing its own `surface`/`verdict`/`title`.

### L2 — Real bugs in the "deterministic" layers + tooling (found tonight, fixable)
Good news first: **the dedup/hash/merge math is genuinely deterministic.** The probe
built the canonical view 5× in-process and across `PYTHONHASHSEED ∈ {0,1,12345}` and
got one identical fingerprint every time (76 real findings). The team's `sorted()` +
sha256 + frozen-dataclass discipline in `dedup.py` / `pipeline.py` holds. The defects
are all at the **boundaries**:

| ID | Bug | Where | Impact | Evidence tonight |
|----|-----|-------|--------|------------------|
| **B1** | **Silent finding-loss.** `build_canonical_view` drops an **entire cluster emission** if **any** finding fails schema; the **renderer discards `_drops`**. A single absent finding missing `proposed_anchor` voids the whole cluster from the report, with no error. | `scripts/report/v2_loader.py:588` and `:1151` discard `_drops`. The `proposed_anchor`-for-absent rule is `schema/finding-v1.json:585-601`. | High. "Findings/whole clusters vanish." Only caught if the lead ran `lead_prep build-canonical-frefs` (which *does* exit-4 on drops, `lead_prep.py:325`) before synth — i.e. **orchestration-gated**. | Repairing `proposed_anchor` on 44 absent findings took the canonical view **0 → 76 refs**. A 2nd emission (`ethics-findings.json`, `findings.6.effort.change_type`) still drops for an unrelated rule — so the silent-drop is **multi-cause**. |
| **B2** | **The determinism gate crashes.** `run_all_canaries → compute_visual_evidence_summary` raises `ModuleNotFoundError: No module named 'scripts'`. | `scripts/assembly/visual_quality.py:325` — `from scripts.report.visual_evidence import …`. This is the **only** `from scripts.` import in the whole tree (every sibling uses `from report.…`/`from assembly.…`). | High. The instrument that *measures* determinism is broken via its documented `dry-run`/`validate-run`/`aggregate` path. | `run-determinism-gate.py dry-run` traceback (full stack in §5). |
| **B3** | **Stale fixtures.** The checked-in fixtures pre-date the 2026-04-30 absent→`proposed_anchor` rule, so `build_canonical_view` returns **0 refs** on them today. Any test/gate built on them silently operates on an empty universe. | `fixtures/slingmods-pdp`, `fixtures/awdmods-homepage`. | Medium. Determinism gate + fixture-stability tests are effectively no-ops until refreshed. | Probe with no repair: 20/20 emissions dropped, `0` canonical refs. |
| **B4** | **Render embeds wall-clock date.** `_load_metadata` stamps `datetime.now()` into the report context (used by both v1 and v2 render paths). | `scripts/report/html_builder.py:673` (`generated_date`), reached via `v2_html_builder.generate_v2_report → v1._load_metadata`. | Low. Report bytes change by day even on identical inputs. | Confirmed by read. |
| **B5** | **Latent `id(f)` in a dedup key.** 'absent' findings are grouped under `(f"_absent_{id(f)}", …)`; `id()` is process-dependent. Washed out by a later sort except on exact ties. | `scripts/assembly/dedup.py:518`. | Very low (smell). | Read; not triggered in probe. |

### L3 — Orchestration drift (the lead executing prose)
`skills/audit/SKILL.md` is a 12-hard-gate, 15-step prose router. Its
"Validation, Synthesis, and Rendering" section is an **8-command sequence** the lead
runs by hand (validate every emission → `build-canonical-frefs` → trim batons →
dispatch synthesizer → validate synth → drift-check → canaries → render), plus a
specialist fan-out in **"waves of ≤5"** (phase 9, G-fanout cap). Because it is prose
the lead *interprets*, two runs (or two machines) can differ in: whether
`build-canonical-frefs` ran before synth (which is what catches B1), whether every
emission was validated, retry handling, command order, and environment (Windows
console encoding, Python/dep versions). The determinism gate's N-run loop is itself
hand-orchestrated, so today it measures **model drift + lead drift, confounded**.

**Already fixed — do not redo** (verified in the current tree): the 2026-05-26
handoff's **P0-1** (canonical-fref split-brain) is resolved — `lead_prep.build_canonical_frefs`
now calls `v2_loader.build_canonical_view` directly (`lead_prep.py:161-223`), single
source of truth. **P0-2** (router documented v1 tools for v2) is resolved — the SKILL
now marks the v1 tools "legacy" and lists the real v2 path. **G16** silent-drop
*surfacing* exists at `lead_prep` (exit-4). The gap B1 names is that the **renderer**
doesn't honor the same surfacing.

### Symptom → cause map
| Your symptom | Primary cause(s) |
|---|---|
| Findings differ run-to-run | **L1** (surface/verdict/title → F-NN, merges, PASS-filter) + **L0** (page changes) |
| Hotspots drift or drop | **L1** (F-NN + `baton_index` choice) + **L2/B1** (whole-cluster silent drop) + **L0** (eN re-index) |
| HTML itself varies | **L0** (re-captured screenshots → different base64 — guarantees byte diff) + **L2/B4** (date stamp) + everything upstream propagating |

---

## 3. The dynamic-workflows verdict (how & why)

### 3.1 What a workflow can and cannot touch
A Workflow orchestrates **subagents + JS control flow** (`agent()`, `pipeline()`,
`parallel()`). It operates at **L3 only**. It cannot make the live page stationary
(L0), cannot make the model pick the same `surface`/`verdict`/`title` (L1), and cannot
fix a Python boundary bug (L2). So **selling a workflow as "the determinism fix" would
be wrong** — and you specifically asked me not to do that. Its honest value is
*drift-proofing the orchestration* and *running multi-agent loops unattended and
identically.*

### 3.2 Fit #1 (build now): the determinism-gate harness — HIGH signal
This is the strongest, lowest-risk fit and doubles as your "diagnose the plugin with
a workflow" goal.

- **Why:** `run-determinism-gate.py` already *is* a hand-rolled workflow (its docstring
  says so). The Mode-A loop is `for N: parallel(20 specialists) → barrier → ethics →
  build-frefs → synth → validate-run`, then `aggregate` → TARr@N / TARa@N. Running it by
  hand across 5–12h is exactly what dynamic workflows exist to remove, and the manual
  loop injects lead-drift into the measurement the gate is trying to isolate.
- **What it buys:** (1) every run takes the *identical* dispatch path, so the gate
  measures **pure model drift** (its actual purpose); (2) it runs **unattended**;
  (3) code-guaranteed fan-out with the concurrency cap; (4) `validate-run`/`aggregate`
  become non-skippable stages.
- **Shape:** `.claude/workflows/ecp-determinism-gate.js` that takes `{fixture, n_runs}`
  in `args`, loops N times, `parallel()`-dispatches the specialists per run (reusing the
  existing specialist contract), then calls the existing Python coordinators
  (`prep-run`, `validate-run`, `aggregate`) via `agent()` steps that run bash. The Python
  stays the substrate; the workflow replaces the human loop.
- **Prerequisite:** fix **B2** and refresh **B3** first, or the gate can't produce a
  verdict.

### 3.3 Fit #2 (later, after L2 fixes): the production audit spine — MEDIUM signal
- **Why:** the `/ecp:audit` orchestration is the same fan-out + fixed sequence, today
  carried by prose the lead interprets (L3). A workflow encodes it.
- **What it buys:** makes per-emission validation + `build-canonical-frefs` + a
  **render-time drop-check** mandatory *stages* (closing **B1**'s orchestration-gating),
  code-guarantees the waves-of-5 fan-out, and can use structured-output schemas for
  dispatch. Converts "discipline held this run" into a guarantee and removes
  cross-machine L3 drift.
- **Caveats (be honest):** (a) it does **not** reduce L0/L1, which are the bulk of what
  you see; (b) it overlaps the existing Python orchestration — this is *re-platforming*,
  not new capability, so ROI is hardening; (c) sequence it **after** the L2 bug fixes,
  or you're just wrapping known bugs in a nicer loop.

### 3.4 Plugin mechanics (the constraint that shapes everything)
Confirmed against current Claude Code docs (changelog v2.1.154 GA'd dynamic workflows;
plugins reference component table):

- A **plugin cannot bundle a workflow.** Recognized plugin components are
  manifest/skills/commands/agents/output-styles/themes/hooks/MCP/LSP/monitors/bin/settings.
  There is **no `workflows/` plugin component.**
- Saved workflows live at **`.claude/workflows/<name>.js`** (project, in-repo) or
  `~/.claude/workflows/`. A saved script shows up as a `/<name>` command.
- Workflows are **opt-in**: the `workflow` keyword, `/effort ultracode`, a saved
  `/<name>` workflow, or no-prompt under `claude -p`/SDK/bypass mode. A SKILL can
  *instruct* the lead to author one but cannot bypass the consent step.
- **Because you are the sole operator (per `product.md` §1), this is fine:** keep
  `.claude/workflows/ecp-determinism-gate.js` (and later `ecp-audit.js`) in the repo,
  run via the opt-in path, "don't ask again" once. For unattended/scheduled runs
  (`claude -p`), opt-in is a no-op.
- **Reuse of ECP's own agents:** the Workflow `agent()` `agentType`/`subagent_type`
  option resolves from the same agent registry the `Agent` tool uses, so a workflow can
  likely dispatch ECP's specialist subagents by name. This is **lightly documented —
  verify with a 10-line spike** before architecting on it (it's the one thing the docs
  don't nail down).

---

## 4. Recommended sequence (prioritized; effort is relative, not calendar)

Fix the cheap, high-leverage bugs first; *measure* before re-platforming; adopt
workflows last and narrowly.

1. **(S) Fix B2** — change `scripts/assembly/visual_quality.py:325` to
   `from report.visual_evidence import ALL_CONFIDENCES, ALL_TYPES` (match the sibling
   convention). Unblocks the determinism gate. One line.
2. **(S) Fix B3** — refresh the two fixtures to the current schema (inject the now-required
   `proposed_anchor` on absent findings + the Phase-7 ethics `effort` shape), OR add a
   `--repair`/normalizer step. The harness's `--repair-absent-anchors` shows the exact
   transform; it resurrected 0→76 refs. Without this the gate runs on an empty universe.
3. **(M) Fix B1 (highest product value)** — make the **renderer** honor `_drops`: have
   `load_v2_findings` / `load_v2_engagement` (`v2_loader.py:588/1151`) surface a loud
   banner (and ideally hard-fail outside `--auto`) when `dropped_emissions` is non-empty,
   mirroring `lead_prep`'s exit-4. Consider **per-finding** drop granularity so one absent
   finding can't void 9 good ones in the same cluster. This directly attacks "findings
   vanish." (Respect `product.md` §4.2 — absence findings are a *feature*; the fix is to
   make their loss *visible*, not to suppress them.)
4. **(S) Fix B4/B5** — make `generated_date` inputs-derived (or drop it from the
   determinism surface); replace the `id(f)` key at `dedup.py:518` with a content key.
5. **(M) MEASURE** — with the gate working, run a real **Mode-A N≥5** determinism gate on
   a freshly-captured engagement and read TARr@N / TARa@N. *This number should drive
   everything after.* You cannot tune L1 without it.
6. **(M) Reduce L1 at the source** — constrain the hash inputs: `surface` is already a
   closed-ish enum (`finding-v1.json:66` + `business_rules._check_surface_in_vocabulary`);
   tighten enforcement so the model can't drift it. Consider a more structural
   cross-device merge key than the LLM title prefix (`pipeline.py:258`). Lower temperature
   is already intended (`cluster-emission-v1.json:74-79`); verify it's actually set on
   dispatch.
7. **(M) Workflow #1** — author `.claude/workflows/ecp-determinism-gate.js` (§3.2). Run
   the gate unattended; isolates pure model drift.
8. **(L, optional) Workflow #2** — `.claude/workflows/ecp-audit.js` (§3.3) once 1–6 land.

Anything touching a frozen contract (schemas, `meta.json` shape, the finding schema)
requires a `product.md` §9/§10 Spec Change Log entry — B1's renderer behavior and any
schema edit qualify.

---

## 5. Where the next agent looks / how to independently re-diagnose

**Run the harness I left (read-only, Windows-safe):**
```powershell
$env:PYTHONIOENCODING='utf-8'
python scripts/diagnostics/determinism_probe.py probe --fixture fixtures/slingmods-pdp
# then, to see the 76-ref universe + input-sensitivity proof:
python scripts/diagnostics/determinism_probe.py probe --fixture fixtures/slingmods-pdp --repair-absent-anchors
```
Expected: probes 1+2 STABLE; without repair, 0 refs / 20 dropped (B1+B3); with repair,
76 refs and a `surface` perturbation that moves `visual-cta F-84 → F-40` (L1).

**Reproduce B2 (gate crash):**
```powershell
python scripts/run-determinism-gate.py dry-run --fixture fixtures/slingmods-pdp --runs-root $env:TEMP\ecp-det --n-runs 3 --no-embeddings --force
# -> ModuleNotFoundError: No module named 'scripts'  at assembly/visual_quality.py:325
```

**Read, in this order:**
- `scripts/report/v2_loader.py` — `build_canonical_view` (`:289`), the two `_drops`-discard
  sites (`:588`, `:1151`), the verdict/ethics render filters (`:624`, `:634`).
- `scripts/assembly/pipeline.py` — `_content_hash_for_finding` (`:80`),
  `normalize_finding_title` (`:258`), `cross_device_title_merge` (`:295`).
- `scripts/assembly/dedup.py` — `deduplicate_v2` (`:344`); the `id(f)` key (`:518`).
- `scripts/report/html_builder.py:673` — the `datetime.now()` stamp.
- `scripts/assembly/visual_quality.py:325` — B2.
- `schema/finding-v1.json:585-601` — the absent→`proposed_anchor` rule (B1's trigger).
- `scripts/run-determinism-gate.py` + `scripts/assembly/determinism_gate.py` — the
  gate/TARr/TARa instrument (the thing to re-platform as Workflow #1).
- `skills/audit/SKILL.md` — the prose orchestration spine to encode as Workflow #2.
- Prior handoffs for context: `docs/2026-05-26-ecp-v2-run-observations-handoff.md`
  (P0-1/P0-2, now fixed) and the `docs/handoff-2026-05-2{7,8,9}-*.md` batch.

**To independently confirm the dynamic-workflows mechanics:** write a throwaway
`.claude/workflows/spike.js` that `agent()`-dispatches one ECP specialist by
`agentType` and confirm it routes (the one under-documented point, §3.4).

---

## 6. Risks & what I did NOT verify

- **I did not run a live audit or a real N-run gate.** L0/L1 magnitudes are argued +
  demonstrated at the unit level, not measured end-to-end. Step 5 is how you get the
  real number; treat my L1 claim as *mechanism proven, magnitude unmeasured*.
- **B1's live frequency is orchestration-dependent.** The fixtures prove the *mechanism*
  cleanly; how often it bites real runs depends on whether `build-canonical-frefs` ran
  before synth each time. That uncertainty is itself the argument for Workflow #2.
- **Probe scope:** the harness only exercises Layer-2 structuring (no LLM, no render, no
  acquisition). It deliberately cannot speak to L0/L1 magnitude — only to "is the Python
  deterministic" (yes) and "do LLM-text fields move identifiers" (yes).
- **`agentType` reuse of plugin agents** is the one workflow capability the public docs
  don't pin down — verify with a spike before building Workflow #2 around it.
- **Single-operator assumption:** §3.4's "saved `.claude/workflows/` script" path is clean
  for you alone. If ECP ever ships to other users, workflows become per-user setup
  friction and Fit #2 should stay Python-portable. (You chose single-operator for this
  pass.)
- I changed **no** pipeline code — only added `scripts/diagnostics/determinism_probe.py`.
  The B-series fixes are left for the next agent so they can be reviewed as deliberate,
  logged changes per `product.md` §9.

---

## 7. Addendum (2026-06-01) — Agentic report-QA / verification workflow

Added in response to the follow-up: *"what about fixing the poor output of the reports?
A workflow that sends out subagents, verifies URLs, verifies hotspots, verifies the
website… and doesn't stop until the goal is achieved and tests confirm it's true."*

**This is a different — and for the product, stronger — use of dynamic workflows than
§1–§6.** §1–§6 are about *determinism* (same input → same output). This is about
*correctness of a single report* (are the findings / hotspots / citations actually
right). They are orthogonal: a report can be perfectly stable and still ship a false
claim. Per `product.md` §0 ("Untrustworthy = unusable") that second failure is the more
fatal one — so this is high leverage, and the answer is **yes, it makes strong sense.**

### 7.1 Why it fits (and why "don't stop until verified" is the crux)
ECP already *defines* this gate but runs it by hand: `product.md` §6 (draft→client-ready:
re-check the live site, follow every citation link, finalize hotspots) and the §4.1/§4.2
trust invariants (no fabrication, no hallucinated reference, no wrong hotspot). A workflow
automates the *checking*:
- Verification is independent per finding / citation / hotspot → ideal `parallel()` /
  `pipeline()` fan-out.
- "Keep going until verified" is the **loop-until-clean + adversarial-verify** pattern the
  Workflow tool is built for: spawn skeptics that try to *refute* each finding, repair the
  failures, re-verify, and stop only when a quality bar is met (e.g. zero refuted findings
  on the Priority Path, or N consecutive clean passes).

### 7.2 Proof — a real PoC run, not theory
I ran `.claude/workflows/ecp-report-qa.js` (committed) against the frozen slingmods
fixture: sample 6 FAIL/PARTIAL findings → for each, fan out 3 verifiers in parallel
(anchor / citation / claim) → aggregate. **20 agents, ~700K tokens, ~144s.**

| Finding | Anchor | Citation | Claim |
|---|---|---|---|
| visual-cta F-01 | valid ✓ | supported ✓ | holds ✓ |
| visual-cta F-02 | absent_ok ✓ | supported ✓ | holds ✓ |
| pricing F-01 | valid ✓ | supported ✓ | holds ✓ |
| pricing F-02 | valid ✓ | supported ✓ | holds ✓ |
| **pricing F-05** | **not_found ⚠** | supported ✓ | **refuted ⚠** |
| **trust-credibility F-01** | valid ✓ | **weak_support ⚠** | holds ✓ |

Two real, client-blocking defects surfaced that determinism work would never catch:
- **pricing F-05 is materially false.** The finding claims no price-match guarantee
  appears above the fold ("buried in footer"). The claim-verifier found "PRICE MATCH
  GUARANTEE" in the top promo bar *directly above* the price and Add-to-Cart, and that the
  footer does **not** contain it. The anchor-verifier *independently* flagged the finding's
  `baton_index="absent"` as wrong (it should have anchored to the real promo element). Two
  verifiers, same finding — the adversarial-multi-lens payoff. A §4.1 fabrication-class
  defect that would have shipped.
- **trust-credibility F-01 is mis-cited.** The cited reference (Finding 1, missing alt text
  on `<img>`) does not substantiate the actual claim (star-rating icon-font `<i>` elements
  needing accessible names). A §4.1 over-applied-reference defect.

4 of 6 were clean — so the pass discriminates; it is not a rubber stamp.

### 7.3 The production shape (verify → repair → re-verify, loop until clean)
The PoC stops at "report." The full version adds the repair loop you described:
```
dirty = all_findings
while dirty and rounds < MAX:
  verdicts = parallel(verify(f) for f in dirty)   # anchor + citation + claim, N-of-M adversarial
  dirty = [f for f in dirty if verdicts[f].failed]
  if not dirty: break
  parallel(repair(f) for f in dirty)              # re-dispatch the OWNING specialist with the verifier's evidence
  rounds += 1
emit(verified_report + qa_checklist)              # the checklist IS the §6 evidence; a human still promotes
```
- **Deterministic checks first; LLM only for the irreducible part.** URL liveness (200 +
  content), `e_index`-exists-in-baton, hotspot-rect geometry, citation-file-exists,
  section-heading-present — all deterministic and **already in the repo**
  (`scripts/report/geometry_validator.py`, `scripts/reference_link_check.py` /
  `scripts/check-reference-links.py`, `scripts/assembly/canary_checks.py`). The workflow
  should run those as cheap stages and reserve LLM verifiers (with N-of-M voting) for the
  one thing code can't judge: "does this claim hold against the screenshot / DOM."
- **Verify against the frozen evidence** (the baton / DOM / screenshots the finding was made
  from) for reproducibility; re-hit the **live** site only for the §6 "did it change / is
  the URL alive" checks. Don't conflate — a live re-fetch reintroduces the L0 page-drift
  problem from §2.

### 7.4 Honest caveats
1. **§6 reserves client-ready for the human** ("automated/`--auto` execution can never mark
   a report client-ready"). The workflow yields a *verified draft + a pass/fail checklist*;
   the operator still signs off — unless you relax §6 via a §9 Spec Change Log entry. Keep
   the human gate for legal/ethics findings regardless (§3.3).
2. **Verifiers are LLMs and can be wrong** (rubber-stamp or false-refute). Mitigate with
   deterministic-first + N-of-M adversarial voting on the semantic checks; treat a single
   verifier as a signal, not ground truth.
3. **Cost is real.** The 6-finding PoC was ~700K tokens / 20 agents. A full 76-finding
   report at 3 verifiers each ≈ 228 agents and several M tokens — fine on Max-plan runtime,
   not free: budget it (verify the Priority Path + all CRITICAL/HIGH fully, sample the
   rest) and cap the repair loop.
4. **Repair can oscillate.** A re-dispatched specialist might "fix" a finding into a new
   defect; cap rounds and require the repaired finding to pass the *same* verifiers that
   failed it.

### 7.5 Where this sits in the plan
This is arguably the **highest direct-product-value** of the three workflow candidates,
because it improves the trustworthiness of *every* report (§0/§6) rather than measuring
infrastructure. Revision to §4: treat it as **Workflow #1 (product)** alongside the
determinism gate as **Workflow #1 (infra)** — both are independent of the audit-spine
re-platform (§3.3) and can land right after the B-series bug fixes. Note the synergy with
**B1**: a render-time drop-check (B1) stops findings *vanishing*; this QA loop stops wrong
findings *shipping*. Together they cover both halves of the §4.1 trust contract.

**Where the next agent looks:** `.claude/workflows/ecp-report-qa.js` (run it via
`Workflow({scriptPath, args:{root, engagement}})`, or save/`/ecp-report-qa` once opted in);
the deterministic checks to fold in as stages — `scripts/report/geometry_validator.py`,
`scripts/reference_link_check.py`, `scripts/assembly/canary_checks.py`; and `product.md`
§4.1 / §4.2 / §6 for the quality contract the loop enforces.
