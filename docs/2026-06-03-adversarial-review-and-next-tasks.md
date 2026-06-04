# Adversarial Review + Next Tasks — Hotspot-Accuracy Batch (2026-06-03)

**To:** the agent implementing the hotspot-accuracy program
**From:** adversarial review pass (manual deep-read + a 9-agent refutation/sweep workflow; every claim below is code-cited)
**Scope:** the 6 "latest commits" on `main` (`5634e18` → `31a2f2c`), the repo state as a whole, and whether `docs/2026-06-03-handoff-hotspot-accuracy.md` prescribed the right directions.

> **Method note.** This was a *refutation* pass: each finding the reviewer formed by hand was handed to an independent agent told to **disprove** it against the actual code. Findings here survived that. Confirmations ("this is correct") are listed too, so you know what you can build on. Severity is calibrated — a real correctness gap is HIGH; a wording/doc drift is NIT.

---

## ✅ LANDED (2026-06-04) — P0 trio + Fix#3, verified against a live audit

The three P0 HIGH themes and the P1 Fix#3 edge are fixed on `main` (TDD, suite green
**1105 passed / 12 skipped**). A live dual-device `/ecp:audit` of awdmods.com homepage
(engagement `2026-06-04-bf5f32e0`, v2 pipeline) was run first to ground the work.

| Task | Commit | What landed |
| --- | --- | --- |
| **P0-2** coverage tool desktop-blind | `fbddec1` | `capture_coverage compare` pairs batons by their real `device` field, emits per-device deltas, warns on a missing canonical device. Can no longer mislabel mobile as desktop. |
| **P0-1** RC#1 zero-sized `<select>` dropped | `ada9ec4` | `_build_elements_js` keeps zero-sized SELECT/INPUT/BUTTON by anchoring to the nearest sized ancestor rect. Real-chromium behavioral smoke test (`tests/acquire-element-capture-smoke.mjs`, pulls the canonical JS — no duplication) verified RED→GREEN; wired into `npm test`. |
| **P0-3** v1 Priority Path `(not found)` | `a10ce2e` | The masked defect reproduced (v1 body used positional F-NN vs content-hashed sidecar refs). `html_builder._attach_display_indices` stamps each parsed finding with its canonical index from `finding-groups.json`; the skipped e2e test is re-enabled and passes. (v2 render path was already clean — verified 0 `(not found)` in the live audit.) |
| **Fix#3** thin-hero re-collapse (P1-4) | `c9983c7` | `_distribute_stacked_section_markers` enforces an 8% min band so a thin hero (`y_pct ≤ floor`) no longer re-stacks at 15%. Thin-section regression test added; the motivating `y≈85` case is unchanged. |

**Note on P3 (verification audit):** effectively done — the awdmods run produced both markdown
audits + visual reports with **25/25 hotspots placed per device, 0 unplaced, 0 fallback banners**,
and all substantive canaries green. RC#1/RC#2 capture buckets can now be re-confirmed on mobile too
via the fixed `capture_coverage compare`.

**Still open:** P1-5 (Fix#4 fold-in — weak-placement/stack warnings into the renderer CLI summary +
determinism gate + `section_stacked_manual` in the match-method breakdown), P1-6 (wire the visual-QA
gate into `workflows/audit.md`), and the remaining P2 cleanup (§4).

---

## Bottom line up front

| Commit | What it claims | Verdict |
| --- | --- | --- |
| `5634e18` RC#1 — broaden acquirer selectors | Capture YMM `<select>`/submit/promo into `elements[]` | ⚠️ **Partial.** Submit/promo path plausible; the **native zero-sized `<select>` — the exact thing the diagnosis named — is still dropped.** Behaviorally unverified. |
| `882d1a0` capture-coverage tool | Verify RC#1 at the source | ⚠️ **Works for desktop only.** `compare` never shows the mobile baton, and can mislabel mobile as desktop. The tool the runbook leans on to prove RC#1 can't see the device RC#1 was worst on. |
| `764d726` RC#2 — contiguous mobile tiling | Gap-free mobile screenshots to page height | ✅ **Correct.** Math verified to the pixel: contiguous + bottom-covered for every `doc_h` ≤ 10,128px. Clean. |
| `de95dfa` Fix#3 — distribute + flag hero stack | Spread stacked section-fallbacks, flag for manual | ✅ **Mostly correct.** One reproduced edge case (re-collapse when `y_pct < 15`). Grouping/propagation/determinism all sound. |
| `fb4209e`/`31a2f2c` handoff docs | Status + runbook + next steps | ⚠️ **Mostly truthful, 3 corrections needed** (RC#1 "DONE" overstates; runbook RC#1 check is desktop-only; RC#2 residual mis-worded). Direction is sound but the **priority order is wrong** (see below). |

**Repo as a whole:** healthy. Suite **green: 1094 passed / 13 skipped** (handoff says 1085 — stale, harmless). Working tree clean, `docs/ecp/` correctly gitignored, zero `TODO/FIXME` in `scripts/`. The earlier placement-QA (24 findings) and type-review (30 bugs) batches were spot-checked and are **genuinely fixed** — no papered-over work. **One real latent defect surfaced** that is unrelated to these commits but matters (a skipped e2e test masks a live customer-facing `(not found)` bug — see §2).

**The single most important takeaway:** the handoff's #1 next step ("run the verification audit") is sequenced *before* the two things that make the audit meaningful. RC#1 may not actually capture the YMM gate, and even if it does, `capture_coverage compare` can't prove it on mobile. **Fix RC#1 and the coverage tool first, then the audit verifies something real.**

---

## 1. Per-commit findings (the latest batch)

### RC#1 `5634e18` — acquirer selector breadth · ⚠️ partial

- **[HIGH] The native zero-sized `<select>` is still dropped — Fix #1(a) is not actually met.**
  The diagnosis (`docs/2026-06-02-hotspot-placement-diagnosis.md:64`, `:101`) was explicit: the YMM `<select>`s render at `width:0/height:0/opacity:0` before JS enhancement, and the fix must "emit `<select>` controls **even when** inline style sets `width:0/height:0`." The commit adds `'select'` to the allowlist at `scripts/acquire_url.py:123` — but the extraction body still has `if (r.width === 0 || r.height === 0) return null;` at **`acquire_url.py:132`**. `querySelectorAll` returning the node does not bypass the per-element `.map` filter, so a zero-sized native select is allowlisted and then immediately discarded. The fix only lands the YMM gate if the *JS-enhanced custom widget* happens to match a new class/role/aria glob **and** renders non-zero-sized — which is unverified.
  → The commit message's "(native + JS-enhanced widgets)" overstates capability. The submit button and `$75` promo bar (which the diagnosis does **not** claim are zero-sized) plausibly work.

- **[MEDIUM] The locking test can't catch this.** `tests/test_acquire_element_selectors.py` only asserts the selector *strings* appear in the JS source; it never runs the JS, never builds a zero-sized element, never asserts a `<select>` reaches `elements[]`. So RC#1(a) has **zero behavioral coverage** and should be treated as *unverified*, not *fixed*.

- **[LOW, in your favor] The in-viewport guard at `acquire_url.py:133` is NOT a flat drop.** Element extraction runs *inside* the per-scroll loop (`_build_elements_js` re-eval at `acquire_url.py:1079`, accumulated at `:1105`), so an element off-screen at scroll 0 is still captured when scrolled into view. The durable blocker is purely the zero-**size** guard at `:132`, compounded on mobile by coverage (a separate axis, now fixed by RC#2).

- **[MEDIUM→low] `[aria-label]` breadth is bounded, not dangerous.** `.slice(0, 10)` caps it per-scroll; `_dedupe_elements_phys(..., cap=140)` sorts by **area descending** with a per-`(selector,x,y)` dedup key, so a small distinct YMM control is *not* evicted by many aria siblings. The only residual risk is a tiny enhanced widget ranking below 140 larger elements — only relevant once the guard above is fixed.

### capture-coverage tool `882d1a0` · ⚠️ desktop-blind

- **[HIGH] `compare` reports the desktop baton only.** `scripts/report/capture_coverage.py:110-111` reads `before["batons"][0]` / `after["batons"][0]`, and `report()` appends `baton.json` before `baton-mobile.json` (`:72`), so `batons[0]` is always desktop. The handoff runbook step 2 prescribes exactly this command to prove RC#1 — but RC#1's documented failure (`<select>`=0, `$75`=0) was on **both** devices, and was *worse* on mobile. **The mobile half of RC#1 cannot be substantiated by the prescribed check.**
- **[HIGH] It mislabels mobile as desktop.** If `baton.json` is absent (failed desktop capture) but `baton-mobile.json` exists, `batons[0]` is the mobile baton, yet `:112` unconditionally prints `(desktop baton)`. A failed desktop capture could read as a passing RC#1 result.
- **[MEDIUM] The tool is blind to the very mechanism it's verifying.** Because RC#1's zero-size guard (above) drops native zero-sized selects, the `dropdown` bucket can read `0` "after" the fix even when the fix "worked" for enhanced widgets. The instrument can't distinguish "fix failed" from "native select was zero-sized."
- **[LOW] No tests cover `compare`, the ordering, or the mislabel path** (`tests/test_capture_coverage.py` tests only `classify`/`coverage`).
- ✅ `classify()` bucket logic is correct: `$75` bar → `promo` via `shipping`, YMM gate → `dropdown` via select/combobox/listbox, submit → `submit_input`.

### RC#2 `764d726` — contiguous mobile tiling · ✅ correct

This one is solid — verified by re-running the math against `scripts/acquire_url.py:680-705` (`inner_h=844`, `overlap=1.1`, `cap=12`):

- **Contiguous + bottom-covered for every `doc_h` in `[845, 10128]`px**; the first 1px interior gap appears at `doc_h=10129`. The handoff's "~10,100px" / commit's "~10k px" are both accurate (12 × 844 = 10,128 is the exact ceiling).
- The **page bottom is always captured** — `ys` always includes `max_scroll` (the `i=n-1` term), `max_scroll = doc_h − inner_h` (`:905`). Even at `doc_h=20000`, `reaches_bottom=True`.
- **Both diagnosis sub-bugs are fixed:** the `min(6)` clamp is gone, and "even-spread across `max_scroll`" is no longer a defect because `n` now scales with page height, keeping `step = max_scroll/(n−1) ≤ inner_h` whenever the cap isn't binding.
- `--max-screenshots 0` → per-device cap flows through `main()` and the recovery pass (`:1360`), so recovery can't silently re-shrink mobile.
- **[LOW] `TestCliDefault` is a dead skip** — `tests/test_acquire_scroll_tiling.py:96-98` guards on `hasattr(acquire_url, 'build_arg_parser')`, which doesn't exist (the parser is built inline in `main()`), so the `default=0` assertion never runs. (One of the 13 skips.)
- **[LOW] Wording:** above ~10,128px the failure mode is **mid-page gaps reopening**, not tail-clipping — see §3.

### Fix#3 `de95dfa` — distribute + flag hero stack · ✅ mostly correct

- ✅ **Grouping is correct** (refutes the obvious concern): `fallback_position` carries the *resolved* per-section coordinate (populated at `v2_markers.py:735` from `_resolve_section_placement`, which "compute[s] y_pct dynamically from real geometry"), **not** `(0,0)`. Two findings on section 0 group; a finding on section 2 does not. No cross-section over-merge.
- ✅ Propagation is wired end-to-end: `section_stacked_manual` → `hotspot_confidence="needs-manual-marker"` (`review_state.py:1133`), marker `source="proposed_anchor_section"` (valid schema enum), `visual_evidence=("section_absence","low")`. Deterministic sort `(burn_number, f_ref)`; `n≥2` guaranteed so no div-by-zero. The test (`tests/test_fix3_hero_stack_distribute.py`) exercises the **real** `auto_map_markers_v2` path, not a synthetic mapping.
- **[MEDIUM] Re-collapse when `y_pct < 15` (reproduced).** At `v2_markers.py:586-590`, `bottom = max(15.0, y_pct)` and `top = 15.0`; when the resolved `y_pct < 15`, `bottom == top` and **every** marker gets `new_y = 15.0` — a full re-stack. Reachable for `section_index=0` when the captured hero band is short relative to the viewport (`scroll_y_bottom < viewport_h × 0.1667`, ~140px mobile). The 2026-06-02 baton (729/844 → y=77.7) does *not* hit it, so the fix works for the motivating engagement — but it's latent for thin-hero captures.
  → Fix: anchor `bottom` at the original `y_pct` and spread *around/below* it, or enforce a minimum span (`top = min(15, bottom − MIN_SPAN)`, clamp ≥0). Add a thin-`section_0` regression test.
- **[LOW] Deviation from the diagnosis's *preferred* option, by design.** The diagnosis preferred (a) force-unplaced (render nothing, queue for manual). The operator chose (b) distribute+flag, which **still renders markers at guessed pixels** — partially retaining the "pin on a pixel it didn't earn" problem, mitigated only by the `needs-manual-marker` flag. Defensible (keeps visual context) and documented, but worth a distinct dashed/ghost visual treatment so the editor reads "unverified position," not a confident pin.
- **[NIT] Producer-authored `visual_evidence` overrides the downgrade** (`visual_evidence.py:142-146`): a finding carrying `{exact_element, high}` keeps it even after relabel. Low risk — `hotspot_confidence` still becomes `needs-manual-marker` (derived from `match_method`, not evidence).
- **[NIT] `section_stacked_manual` falls out of the renderer summary breakdown.** `v2_html_builder.py:320-336` counts `proposed_anchor_section` etc. but not the new method, so distributed markers are counted in "Hotspots placed" yet appear in *no* match-method bucket. Folds into the Fix#4 work below.

---

## 2. Repo state as a whole

- ✅ **Suite green:** 1094 passed / 13 skipped / 0 failed (~21s). Run `pytest tests/`, not `unittest discover` (the latter skips bare pytest funcs — known blind spot).
- ✅ **Earlier batches are real.** Spot-checked `placement_repair.py` (finding-level confidence fix at `:196`; re-anchor fail-safe `section-match` at `:185`, verified `riskyConfidence` in `tools/editor/editor.js`; `source='e_index_lookup'` enum fix at `:180`; slide-locality wired), `geometry_validator.py` (wired into render at `v2_html_builder.py:210`), crash guards, and type-review coercions — all genuinely fixed, no false claims.
- ✅ **Hygiene:** working tree clean; `docs/ecp/` gitignored (0 tracked); no `TODO/FIXME/XXX/HACK` in `scripts/`; modules import cleanly (note `v2_markers` uses relative imports → import as `report.v2_markers`).
- **[HIGH — pre-existing, surfaced here] A skipped e2e test masks a live customer-facing defect.** `tests/test_e2e_render.py:630` is `@unittest.skip`'d; an agent neutralized the skip and **the test fails on `assertNotIn("(not found)", html)`**. The skip's own docstring documents the root cause: after "Phase L.D", the renderer body uses **positional** F-NN (`report/templates/components.py:assign_cluster_indices`) while the Priority Path sidecar uses **content-hashed** F-NN (`assembly/pipeline.py:assign_display_indices`), so Priority Path links resolve to `(not found)` in the rendered HTML. This predates the reviewed commits and was a deliberate "Phase M" deferral — **but it currently has zero active regression coverage and ships broken cross-references in any audit whose Priority Path references a finding the renderer renumbered.** Confirm with a live render, then prioritize.
- **[LOW] Green suite slightly overstates coverage:** 9 of the 13 skips are gated on gitignored engagement fixtures, so the render pipeline has no live CI coverage. Consider committing one tiny synthetic engagement fixture for `final_report_render` / `review_state_schema`.
- **[NIT] Two leaked `agent-browser` temp files at repo root** (correctly ignored) — delete in a housekeeping pass.

---

## 3. Handoff-direction corrections

The handoff (`docs/2026-06-03-handoff-hotspot-accuracy.md`) is mostly truthful and its Fix#2/#3/#4 status claims, runbook CLI commands, gate path, and baseline corpus all check out. Three corrections before anyone acts on it:

1. **[HIGH] RC#1 "DONE" / "both root causes fixed in code" overstates it.** Downgrade Fix#1 to **"DONE (code) / UNVERIFIED (behavioral)"** and add the `acquire_url.py:132` zero-size caveat. As written, the TL;DR reads as settled when the YMM-gate capture is exactly what's in doubt.
2. **[HIGH] Runbook step 2 verifies RC#1 on desktop only.** `capture_coverage.py compare` is desktop-blind (§1). Either note this and instruct also running `capture_coverage.py report --engagement <new>` and eyeballing `baton-mobile.json`'s buckets, **or** fix `compare` to diff both batons (preferred — task P0-2). The headline "one audit verifies both root causes" isn't true until then.
3. **[MEDIUM] RC#2 residual is mis-worded.** "Pages taller than ~10,100px still **clip** beyond 12 tiles" is empirically false — the bottom is always captured. The real failure mode is **mid-page coverage gaps reopening** across the whole page (the original RC#2 pathology, ~352px gap at 14k px). More dangerous than "clipping" implies, and plausible on a real Shopify PDP.
4. **[NIT]** Update "1085 passed" → "1094 passed", or just say "green."

✅ **Fix#4 "MOSTLY DONE" is honest** about scope — the `≥3-on-a-pixel` stack warning and weak-placement tally *are* built in `placement_audit.py` (`STACK_MIN=3` at `:50`, `score_marker` at `:54-79`), and the "remaining = fold into renderer summary/CI" is correctly scoped. The only nuance: "MOSTLY DONE" undersells how much value is in the *remaining* part — the diagnosis's stated goal ("catch Pattern-D **automatically** in CI/audit-trace") is precisely the unbuilt integration; today it's an opt-in tool nothing in the audit flow calls.

✅ **The next-step list is well-chosen** *content*-wise (audit, Fix#4 fold-in, gate-wiring, long-page) — but the **order is wrong** for the goal. See P0 below.

---

## 4. Suggested next-task list (prioritized)

> Re-sequenced from the handoff: the audit (its #A) is blocked on hardware **and** can't prove RC#1 until P0-1 and P0-2 land. Do the audit-independent correctness work first.

### P0 — correctness, audit-independent

1. **Make RC#1 actually capture the YMM gate.** In `_build_elements_js` (`acquire_url.py:~129-144`), special-case form controls: skip the `r.width===0 || r.height===0` drop when `el.tagName` ∈ {SELECT, INPUT, BUTTON} (or when an enhanced sibling/ancestor is visible) and emit the control's logical rect (parent/label or enhanced-widget rect) instead of the collapsed native rect. **Add a behavioral test** (zero-sized `<select>` + visible enhanced widget → an `elements[]` row) so the guard regression is caught. *Until this lands, treat RC#1(a) as unverified.*
2. **Fix `capture_coverage.py compare` to cover both devices.** Iterate `zip(before['batons'], after['batons'])`, label each by its real `baton` field (`baton.json`→desktop, `baton-mobile.json`→mobile), never assume `[0]`=desktop; warn when the desktop baton is absent. Add tests for ordering, the mobile delta, and the mislabel path. *This is what lets the verification audit actually prove RC#1 on mobile.*
3. **Surface/fix the live `(not found)` Priority Path defect** (§2). Confirm with a live `generate-report.py` render, then thread `display_index` from the validated priority-path sidecar into the renderer body's finding labels, and **re-enable `test_e2e_render.py:630`.** Customer-facing.

### P1 — hardening + honesty

4. **Fix#3 `y_pct < 15` re-collapse** (`v2_markers.py:586-590`): decouple `bottom` from the floor / enforce a minimum span; add a thin-`section_0` regression test.
5. **Fix#4 fold-in (the actual value):** add `weak_placements_count` + the `≥3-on-a-pixel` warning to the renderer's own CLI summary (`v2_html_builder.py:300-337`) **and** a `tests/test_v2_determinism_gate.py` assertion, and include `section_stacked_manual` in the match-method breakdown. Closes the "0 unplaced ≠ all correct" trap without an operator remembering to run the standalone tool.
6. **Wire the visual-QA gate into the audit flow** (handoff #C): a `free`-tier Tier-0 pass in `workflows/audit.md`; map `--visual` → `standard`/`deep`. The gate JS itself is clean (verified — tiers/caps/voting/cost-dial all match the handoff); it just isn't called by anything.

### P2 — docs + cleanup

7. Apply the three handoff corrections in §3 (RC#1 status + caveat, runbook step-2 note, RC#2 residual reword, test count).
8. Add a "LANDED" status table to `docs/2026-06-03-adversarial-placement-qa-findings.md` (all 24 are fixed; the doc still reads as proposed).
9. Housekeeping: extract a `build_arg_parser()` factory so `TestCliDefault` runs; commit one synthetic render fixture for live CI coverage; delete leaked agent-browser temps; consider forcing `section_absence/low` for `section_stacked_manual` regardless of producer evidence; consolidate the duplicate `backfill_screenshots_from_sections` helper between `geometry.py` and `geometry_validator.py`.

### P3 — blocked on agent-browser hardware

10. **Run the verification audit** (handoff #A) — but only *after* P0-1 and P0-2, so it can actually substantiate RC#1 on both devices. One `/ecp:audit … --visual` run then verifies RC#1 (capture buckets, now mobile too), RC#2 (mobile sections span to page bottom), and eyeballs the Fix#3 distributed hero column.

---

## What's solid (build on this)

- RC#2 contiguous tiling — verified to the pixel.
- Fix#3 grouping/propagation/determinism — only the `<15%` edge needs a guard.
- The visual-QA gate JS — tiers, MIX caps (8/40), 1-vs-3 voting, crop determinism, schema-valid repair output, cost-dial table — all accurate, no correctness bugs.
- The earlier placement-QA (24) and type-review (30) batches — genuinely fixed.
- Test discipline and hygiene across the repo.

**Severity tally across all findings:** 7 HIGH, 6 MEDIUM, 11 LOW, 7 NIT, plus 18 explicit "this is correct" confirmations. The HIGHs cluster into three real themes: **(A)** RC#1 isn't verified/complete, **(B)** the tool meant to verify it is desktop-blind, **(C)** a skipped test masks a live render defect. Everything else is hardening or polish.

---

*Generated by an adversarial review pass: a manual deep-read cross-checked by a 9-agent refutation+sweep workflow (4 seed-finding refuters over RC#1/RC#2/Fix#3/coverage-tool + 5 repo-wide sweepers over Fix#4/visual-QA-JS/handoff-directions/hygiene/earlier-batches). All findings are cited to file:line at HEAD `31a2f2c`.*
