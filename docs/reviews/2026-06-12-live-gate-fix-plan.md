# Live-gate fix plan — post-`/ecp:audit` LV2–LV4 findings (2026-06-12)

> **Status: ✅ EXECUTED (2026-06-12 → 2026-06-13).** All LG1–LG16 + the Minor
> nits landed on `main` as tiny guard-test-first commits (`24c21bd..9fda9f8`):
> LG1–LG3 first (`98aa402`/`fa76b71`/`16f1505`), then LG4–LG16 (`43186fc..9fda9f8`).
> Suite green on BOTH runners — **1402 pytest passed / 12 skipped / 963 unittest**
> (this box); parity floor re-floored to **1366** (clean-clone 1396).
>
> **Per-item outcome (several plan claims were stale — verified against current code):**
> - **Code:** LG1 (hero decode-wait + srcset/fetchpriority/stepped-scroll), LG2
>   (device-scoped baton precedence), LG3 (edge-punct quote strip), LG4 part 1
>   (diagnose skip hidden markers) + part 2 (callout de-stack), LG5 (small exact
>   element → box), LG6 (`anchor_satisfies_numeric_predicate` business rule + contract),
>   LG7 (visual-qa requires `args.engagement`), LG8 (`--from-review` honors demotions).
> - **Doc/contract reconciliations:** LG9 (load-order repo-root anchor), LG10
>   (device-keyed baton naming), LG11 (`proposed_anchor` normalize example), LG12
>   (v2 loader doc + parser trap), LG13 (acquirer counter = per-baton), LG14
>   (two Placement-QA flavors), LG15 (full canary set), Minor (schema-axes + help string).
> - **Refuted / already-fixed (no code change needed):** LG4's "`-ai` duplicate in
>   render set" and "absence findings stack" were already fixed; LG9 was an
>   omission, not a wrong base header; LG12's v2 loader already exists
>   (`json_parser.parse_emission_file(s)`); **LG16** was already enforced (ADJACENT
>   hedge already covers `why_this_matters`) — pinned with a regression test.
> - **Operator follow-ups (not unit-testable):** LG1 — re-run the live awdmods
>   `--plugin-dir /ecp:audit … --visual` and confirm `section-1.jpg` renders the
>   hero + `diagnose` `CAPTURE_SUSPECT` → 0; LG4 part 2 — eyeball the editor's
>   fanned-out callouts on a same-element stack. `O1` (stale v1.4.1 plugin on the
>   work box) remains an operator action.
>
> ---
>
> _Original plan (as authored, OPEN) follows._ Authored by the reviewer terminal after the first
> live `--plugin-dir /ecp:audit https://awdmods.com/ --visual` run
> (engagement `2026-06-12-d662a8d3`, on disk for repro). The roadmap's live gate
> (`O3`) is **DONE**; this plan is the work that gate surfaced, merged with the
> roadmap items that were explicitly waiting on LV2–LV4 data.

## What the gate established (so we don't re-litigate it)

- **PASS — the deliverable-corrupting class is dead live.** Zero `(50,50)` phantom
  markers across all 4 rendered reports (V1/V2 confirmed fixed). LV1
  acquire/convert clean (valid v2 batons, `*.v1raw.json` preserved, meta merge
  intact). Pipeline ran end-to-end (12 specialists, ethics, synth, render,
  reflection); every subagent stall recovered, no data lost. The lead correctly
  held the factually-correct ethics anchors (`e166`=`<s>$1,847.99</s>`, `e20`) against
  a **buggy** validator (see LG2/LG3) — verified at the code level.
- **CAUGHT — placement + capture quality.** `diagnose_engagement.py` returns
  `DO NOT SHIP` both devices (this is the normal raw-draft baseline — the committed
  worked example `2026-06-08-8e46b1c8` gets the same verdict; the §6 editor pass is
  what finalizes placement). The *distribution* is the signal:
  desktop `CAPTURE_SUSPECT:10 STACKED:10 POINT_FOR_REGION:2 PREDICATE_MISMATCH:3 DUPLICATE:3 OK:3`;
  mobile `CAPTURE_SUSPECT:7 STACKED:11 POINT_FOR_REGION:4 PREDICATE_MISMATCH:1 DUPLICATE:4 OK:3`.

## ID space (avoid the 4-way collision)

New findings carry an **`LG`** prefix (Live-Gate, 2026-06-12). Each maps to its
legacy ID where it continues prior work: `S1`/`A8`/`hc-C6`/`PR-97` from
`2026-06-10-consolidated-findings-and-plan.md` and the V/S/U/O space in
`2026-06-10-post-roadmap-review-and-fix-plan.md`. Never cite a bare C-number.

## Execution rules (carry from prior waves)

Tiny per-behavior commits; **guard-test-FIRST** (failing test + fix in the SAME
commit); BOTH runners green before ff-merge (`pytest` + `unittest discover`);
re-floor `tests/test_runner_parity_guard.py` from a **clean-clone** count when the
suite grows (its docstring "Floor update rule" — do not floor from a box with
local `docs/ecp/` engagements); conventional commit messages carrying the `LG#`
ID; branch → `git merge --ff-only` → push → delete. `$env:PYTHONIOENCODING='utf-8'`
before non-ASCII scripts. Contribution contest is live → tiny real commits are a
feature; never squash.

---

## P0 — correctness & trust (do first)

### LG1 (= `S1` full scope) — Hero reveal capture: the false-finding cascade root cause
**The #1 finding. Dan observed it live on BOTH devices: the hero image never loaded
into the captured screenshots, and it drove a large share of the findings.**
- **Evidence:** `2026-06-12-d662a8d3` desktop `section-1.jpg` shows the hero band as a
  black void with only the vehicle-selector dropdowns floating in it. `diagnose`
  header: "above-fold captured flat/void (55% void rows) … hero likely UNRENDERED",
  10 desktop / 7 mobile `CAPTURE_SUSPECT`, some of them capture-induced **false**
  findings ("claims empty/blank region"). This is the VC-08/VC-24 cascade the
  `293d0ed` reveal fix was meant to kill — still partially alive.
- **Root cause (confirmed from the captured DOM, not a guess):** the hero is a
  Shopify `.banner.image-overlay … scroll-trigger animate--fade-in` element. The
  reveal pass (`scripts/acquire_url.py:816-854`, `_reveal_lazy_and_animations`,
  called at `:1139`) **did** fire — the element carries `scroll-trigger--active` —
  so the fade-in is NOT the blocker. The blocker is image paint: sitewide images use
  `srcset` + `loading` with essentially **no plain `src`** (25 `srcset` / 1 `src` /
  0 `<picture>` in `dom.html`). The reveal flips `loading=lazy→eager` and
  `data-src→src`, then waits a **flat `time.sleep(1.0)`** (`:1147`) and nudges
  IntersectionObserver with a single `scrollTo(0, innerHeight)`→back (`:836-839`) —
  too weak for a large CDN hero `<img srcset>` to download+decode before the
  above-fold screenshot fires.
- **Fix (diagnose-first with a live awdmods re-capture, then implement the smallest
  prong that fixes it; likely all three):**
  1. Replace the flat 1.0s with an **above-fold image-decode wait**: after the
     reveal, `await Promise.all([...aboveFoldImgs].map(i => i.decode().catch(()=>{})))`
     (or poll `img.complete && img.naturalWidth>0`) up to a bounded timeout, THEN
     capture. Highest-probability fix.
  2. Broaden eager coverage to `<img srcset>` with no `src` (force a source re-pick)
     and `<source srcset>`; set `fetchpriority="high"` on above-fold hero media.
  3. Make the IO-trigger a **stepped scroll-through** (increment through the full
     page to fire all scroll-triggers + IO image loads, then return to top) instead
     of a single viewport hop.
- **Guard test (first):** JS-level unit on the reveal helper via the existing
  eval-harness pattern — assert it (a) eager-triggers a `srcset`-only lazy `<img>`,
  and (b) the capture sequence waits on decode before screenshot (no flat-sleep-only
  path). Manual acceptance: re-run `/ecp:audit https://awdmods.com/ --visual`, confirm
  `section-1.jpg` shows the rendered hero and `diagnose` `CAPTURE_SUSPECT` drops
  toward 0 and "hero UNRENDERED" clears. Scope note: this completes `S1`, whose full
  reveal-pass rework was explicitly deferred in the backlog — it's now justified by
  live data.

### LG2 (NEW engine bug) — `_check_baton_precedence` pools desktop+mobile elements
- **Where:** `scripts/assembly/business_rules.py:927-934`.
- **Bug (verified):** when validating an emission against both batons, it flattens
  `desktop_baton.elements + mobile_baton.elements` into one list and builds
  `by_e_index = {el["e_index"]: el …}`. Desktop `e166` and mobile `e166` collide
  (last-baton-wins), and the "find any element where a quote matches" loop (`:945+`)
  scans across both devices — so a **correct** desktop anchor gets compared against a
  mobile element and flagged. This is the **same device-less-match family as `V3`**
  (fixed in `v2_loader` but never here). It produced 2 false-positive `validate`
  failures on the live ethics emission; the lead correctly refused to corrupt the
  data and overrode the gate with evidence.
- **Fix:** scope the precedence check per device — only compare a finding's anchor
  against the baton for that finding's device (`proposed_anchor.viewport`, or for
  page-scope ethics, check against each device baton independently and require the
  match to be device-consistent). **Guard test (first):** colliding `e_index` across
  desktop/mobile where the correct device's element matches the quote → assert NO
  violation; the cross-device collision case that currently false-fires → assert it
  no longer fires.

### LG3 (NEW engine bug) — `_VERBATIM_QUOTE_PATTERN` keeps trailing punctuation
- **Where:** `scripts/assembly/business_rules.py:65` (the regex) + the substring test
  at `:939-942`.
- **Bug (verified):** `re.compile(r'["“”]([^"“”]{2,80})["“”]')` captures inner
  punctuation, so prose ending a sentence with `"$1,847.99."` yields the quote
  `$1,847.99.`, which never substring-matches element text `$1,847.99` → the correct
  anchor (`e166`) is rejected and the check bounces to a wrong element. Compounds LG2.
- **Fix:** strip trailing/leading punctuation (`.`,`,`,`;`,`:`,`)`…) from each
  extracted quote before the substring comparison. **Guard test (first):** a finding
  whose prose quotes `"<text>."` with the period inside the quotes, correctly anchored
  → assert it validates clean.

---

## P1 — placement quality (the roadmap work LV3 was gating)

### LG4 (= `A8` / `hc-C6` ghost-zone — RE-OPEN) — de-stack collapsed markers
- **Trigger met:** the roadmap parked `A8` with "re-open only if LV3 vision-QA shows
  stacked-marker or region-as-point placement still hurting reports." LV3 shows
  10–11 `STACKED` + 3–4 `DUPLICATE` per device. Re-open.
- **Where:** `scripts/report/v2_markers.py` + `scripts/assembly/review_state.py`.
- **Work:** region findings → a box over the section rather than ≥3 points collapsing
  onto one section-bottom pixel; de-stack absence/head-meta findings; drop the `-ai`
  duplicate from the render set. **Guard test (first):** a review-state with 3 region
  findings resolving to one pixel → assert they render as distinct boxes / are
  de-stacked, not a single stack.

### LG5 (= region-as-point) — render region/banner findings as a box, not a point
- **Where:** same files as LG4 (`v2_markers.py` + `review_state.py`).
- **Bug:** `POINT_FOR_REGION` (2 desktop / 4 mobile) — a region/banner finding (e.g.
  ethics `F-66` on the strikethrough-price area) renders as a single point instead of
  a box over the area. **Guard test (first):** a region-shaped finding → assert a
  box geometry is emitted, not a centroid point.

### LG6 (= `PR-97` predicate-anchor tightening) — anchor predicate-bearing claims correctly
- **Where:** `contracts/specialist-prompt-v2.md` anchor rules.
- **Bug:** `PREDICATE_MISMATCH` (3 desktop / 1 mobile) — e.g. pricing `F-16` says
  "OVER $1,766" but anchors a `$135.99` element. The specialist must anchor a
  predicate-bearing claim (`over $X`, `cheapest`, …) to an element that **satisfies**
  the predicate, or to the section. **Guard:** extend the specialist anchor-rule
  canary / business-rule lint to flag a numeric-predicate finding whose anchored
  element text contradicts the predicate (pin behavior where it exists; if it needs a
  new rule, add it test-first).

---

## P2 — tooling & workflow

### LG7 (NEW) — `ecp-visual-qa` named-workflow arg plumbing + stale default engagement
- **Where:** `.claude/workflows/ecp-visual-qa.js` (and the doc invocation in
  `contracts/report-export.md:82`).
- **Bug:** `Workflow(name="ecp-visual-qa", args={engagement,device,tier})` did NOT
  forward `args` to the script's `args` global; it fell back to the hardcoded stale
  default engagement `2026-06-01-749a3c3d` and ran desktop both times. (Same flavor as
  the `O2` ROOT hardcode just fixed — the `ENG`/`DEVICE` defaults are stale literals
  too.) **Fix:** make named-workflow args plumb, or read `args` defensively and drop
  the stale default engagement (derive or require it). **Guard:** a test asserting the
  script has no hardcoded engagement-id literal and reads `args.engagement` first.

### LG8 (NEW) — `--from-review` should honor repaired confidence demotions
- **Where:** `--from-review` render path (`generate-report.py` / `report_state`).
- **Bug:** the lead observed `--from-review` didn't honor confidence demotions written
  by the repair pass (`review-state-*.repaired.json` exist in the engagement).
  **Fix + guard:** reproduce, then pin that a repaired-demoted finding renders at its
  demoted state.

---

## P3 — contract & doc reconciliation (cheap, high-clarity; from the lead's Q1 debrief)

- **LG9** — `skills/audit/SKILL.md` path-base header says base = `…/skills/audit`,
  but every Runtime-Load-Order path resolves against the **repo root** (the lead's
  first 6 Reads failed). Fix the header / clarify resolution.
- **LG10** — Dual-device naming contradiction: `contracts/device-semantics.md`
  ("first device = bare name, second = `-{device}`") vs `SKILL.md` Artifact Contract
  (`baton.json`=non-mobile, `baton-mobile.json`=mobile) — and the hardcoded
  `--desktop-baton-path`/`--mobile-baton-path`. Reconcile to the v2 convention.
- **LG11** — `SKILL.md` Validation step 1 lists "a stray-anchor removal" as a
  permitted **normalize**, but `evidence_anchors` is excluded from
  `NORMALIZE_ALLOWED_FIELDS` (`scripts/test-specialist.py`) — the one named example is
  impossible. Align the doc to the allowlist (the contract is right; the example is
  stale) or add the field with care.
- **LG12** — No v2 findings loader for the trim step: `synth_input.trim_baton_file`
  expects `Finding`s but the only loader (`assembly.parser.load_all_cluster_files`) is
  v1-markdown-only (raised `FileNotFoundError` on `cluster-*-{device}.md`). Add a v2
  JSON loader or document the direct-`e_index`-set trim path the lead improvised. Also
  note: `assembly/parser.py` is a legacy-v1 trap NOT named in the "do NOT run" list.
- **LG13** — Acquirer "one per device" (`dispatch-contract.md`/`SKILL` step 5) vs the
  deterministic `--both` single process (`workflows/acquire.md`), and the
  `trace_counters_reconcile_with_artifacts` canary expecting `acquirers ≥ 2` (it
  counts batons). Document `--both` = 1 acquirer = 2 batons and fix the counter
  semantics so no fudge is needed.
- **LG14** — Two "Placement QA" definitions: `generate-report.py` `weak_placements=0`
  vs `placement_audit.py` 18/22 weak on the same render (it also counts
  page_level/proxy/stacked). Reconcile the terminology in `contracts/report-export.md`.
- **LG15** — Canary set under-documented: `trace-assertion-canary.md` documents 3
  Phase-I canaries; `run_all_canaries` returns 12. Document the full set.
- **LG16** — Consider an ethics-specialist instruction to hedge `why_this_matters` on
  ADJACENT findings (mirror the observation/recommendation hedge rule).
- **Minor** — baton `schema_version: 1` inside a `schema_version: 3` engagement reads
  as a contradiction (acquire.md "Implementation note" wording); `prepare-synthesizer
  --help` says "10 specialists per device" (stale — standard scope is 6).

---

## Not a Codex code task (tracked elsewhere)

- **`O1`** — stale `ecp@…v1.4.1` plugin on the WORK box (`C:\Users\SM - Dan\…`) is an
  **operator** action (uninstall + marketplace remove + restart), not code. Still
  open; clear before the next live run on that machine. Home box is verified clean.
