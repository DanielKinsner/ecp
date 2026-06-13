# Post-roadmap review — confirmed findings & fix plan (2026-06-10)

> ## ✅ Phase 1 DONE — V1–V3 fixed 2026-06-12; next gate item: the live LV2–LV4 session (O3)
> **V1–V3 landed on `main`** in `a5e5e95..671e245` (guard-test-first, tiny
> commits) plus review follow-ups `73ad205..f263fbf`: an end-to-end
> `--from-review` guard through the real CLI (`tests/test_v2_from_review_render_e2e.py`)
> and a point-fallback fix so legitimate 0% coordinates stop teleporting to the
> (92,10) default. Review-verified by running every new guard against the
> pre-fix code (they fail there). Suites after: **1355 pytest / 895 unittest,
> parity floor 1336, both green.**
> **Still open (not gate-blocking):** V4–V5 (Phase 2), S1–S3 (Phase 3), U1–U7
> (Phase 4, verify before fixing), and Phase 5's O1 (stale work-box plugin) +
> O2 (QA-workflow ROOT hardcoding), which must be cleared as part of running O3,
> the live session itself.
>
> *Original 2026-06-10 banner, for the record:* an 8-axis review of the executed
> roadmap (`959eaeb..b97d8d7`) found five adversarially-confirmed bugs (V1–V5),
> each independently reproduced by a verifier agent; V1–V3 corrupted the client
> deliverable. Spec-axis verdict on the roadmap: substantially honest — 31/33
> findings genuinely fixed at the code level; the gaps are S1–S3 below. Suites
> then: 1341 pytest / 889 unittest (`b97d8d7`).

**Provenance.** 2026-06-10 work-box session: 8 parallel review axes (standards,
spec-vs-roadmap, acquisition, report pipeline, placement/promotion, tests/guards,
plugin validation, repo state) over `git diff 959eaeb...HEAD`, with every
critical/high finding re-verified by an independent adversarial agent instructed
to refute it from the code on disk. The five doc/guard cleanups from the same
review already landed (`98e1856..b97d8d7`: parity floor 1322, CLAUDE.md
true-ups, gitignore comments, graphify-out promotion entry).

**⚠️ ID disambiguation (this doc adds a FOURTH space — read this first).**
This doc's findings are **`V1–V5`** (verified bugs), **`S1–S3`** (spec-claim
gaps), **`U1–U7`** (unverified single-reviewer mediums), **`O1–O3`**
(operational pre-gate items). Where a finding relates to a 2026-06-10 spec-audit
ID it is cited as e.g. "spec-audit C7" — never bare. The three pre-existing
colliding spaces are documented in
[2026-06-10-consolidated-findings-and-plan.md](2026-06-10-consolidated-findings-and-plan.md)
§"ID disambiguation".

**Execution rules** (carry from the executed roadmap): tiny per-task commits,
guard-test-FIRST (write the failing test, then the fix, same commit), both
runners green before ff-merge to `main`, re-floor
`tests/test_runner_parity_guard.py` in any wave that adds tests.

---

## Phase 1 — deliverable-corrupting bugs (BLOCKING, do first)

### V1 — Final `--from-review` v2 render draws hidden/unplaced markers at slide center
**The exact-tier-or-blank doctrine (rulings A1/A2) is bypassed in the one path
that produces the client deliverable.**
- **Where:** `_apply_review_state_to_slide_markers`,
  `scripts/report/v2_html_builder.py:558-588` (routed from
  `generate-report.py:248-271` for any v2 engagement with `--from-review`).
- **Bug (verified by live repro):** the marker loop (a) never checks
  `marker["hidden"]`, and (b) defaults missing coords to 50:
  `x=_review_float(marker.get("x_pct"), 50)`. `build_initial_review_state`
  always sets truthy `callout_position`/`callout_color`
  (`scripts/assembly/review_state.py:125-127`), so `_review_override_enabled`
  (`v2_html_builder.py:418-433`) is True for every finding → every non-hidden…
  i.e. every unplaced absence (post-`89f2b40`) and off-slide e_index
  (post-`a2e9e91`) renders a **phantom point marker at (50,50) on slide 0**,
  including findings promoted via the A9 "approved = deliberate blank" flow
  (`scripts/assembly/report_state.py:71-76`).
- **Fix:** in `_apply_review_state_to_slide_markers`, skip markers with
  `hidden: true` (and do NOT render a marker when no geometry fields are
  present, rather than defaulting to 50/50). Correct reference behavior already
  exists in the v1 fallback renderer `_render_marker_svg`
  (`scripts/assembly/review_state.py:698-700`).
- **Guard test (write first, must fail pre-fix):** call `generate_v2_report`
  with a review-state containing a hidden, coord-less marker (the
  `_unplaced_marker` shape, `review_state.py:608-637`) and assert NO marker
  HTML/SVG is emitted for it; positive control: a placed rect marker still
  renders. No test currently calls `generate_v2_report` with a hidden marker
  (`test_g4_blank_below_confidence.py` tests `_render_marker_svg` only).

### V2 — Operator point/ellipse/polygon placements collapse to (50,50) in the v2 final render
- **Where:** same function, `scripts/report/v2_html_builder.py:586-590`.
- **Bug (verified):** only `x_pct/y_pct/w_pct/h_pct` are read. The editor
  stores point markers as `cx_pct/cy_pct` (`tools/editor/editor.js:931`),
  ellipse as `cx/cy/rx/ry` (`:936`), polygon/freeform as `points[]` (`:946/:953`)
  — and promotes confidence to exact-selector on placement (`:980-981`). Those
  placements render at the 50/50 default while the gate and QA count them
  exact. Worse: default zone-less markers from `review_state.py:592-605` are
  point/`cx_pct` shaped too. (Pre-existing code, but `89f2b40` made manual
  placement THE mandated path for absences, so it is now load-bearing.)
- **Fix:** teach `_apply_review_state_to_slide_markers` (or a shared
  normalizer used by both render paths) to read all three geometry families
  from `schema/review-state-v1.json:155-158`. Mitigation note: rect and
  snap-to-element write `x/y/w/h` and are unaffected.
- **Guard test:** review-state fixtures with one point, one ellipse, one
  polygon marker → assert rendered geometry matches (not 50/50); plus V1's
  hidden case stays blank.

### V3 — spec-audit C7: merge metadata attaches to the wrong finding (device-less match)
- **Where:** `build_canonical_view` augmentation loop,
  `scripts/report/v2_loader.py:566-568`.
- **Bug (verified through the real pipeline):** the merge winner is matched by
  `(cluster, local_index)` only, though the producer emits `kept["device"]`
  (`scripts/assembly/dedup.py:386`) for exactly this purpose. `local_id`
  restarts per emission file, so desktop pricing#2 and mobile pricing#2 both
  surviving dedup is routine; the wrong one can receive
  `devices_present`/citations/tier — which then **leaks a single-device finding
  onto the other device's report** via the `device not in devices_present`
  filter (`v2_loader.py:736-738`), the exact class spec-audit C7 targeted.
  Secondary edge: chained merges (layer-1 winner later absorbed) silently skip
  attribution.
- **Fix:** one line — add `and f.device == kept.get("device")` to the match.
  Consider logging the chained-merge skip.
- **Guard test:** the existing C7 round-trip test uses `local_id=1` on both
  devices (`tests/test_phase3_c5_c7_c17.py:333-450`) so no collision occurs —
  add a case with colliding local_ids across devices where the merge keeps the
  later-sorted finding, assert metadata lands on the kept finding and the other
  device's report does NOT show the leaked finding.

## Phase 2 — evidence-quality bugs (fix before or shortly after the gate)

### V4 — spec-audit C15: DPR-fallback signal erased by the v1→v2 converter
**Status 2026-06-12:** FIXED `3c916c5`; legacy no-field behavior pinned `57c7c3e`.
- **Where:** `scripts/baton_v1_to_v2.py:360,364`.
- **Bug (verified):** acquire now writes `viewport.dpr_requested/dpr_actual/
  dpr_fallback` on the v1 baton (`acquire_url.py:616-642,1176-1180`), but the
  converter reconstructs from v1 `viewport.dpr` (set to the ACTUAL int) →
  mobile 3.0→1.0 fallback emits `dpr_requested=1.0, dpr_actual=1.0`. The
  schema's documented detection signal (`schema/baton-v1.json:47-66`,
  "dpr_actual != dpr_requested") never fires in the pipeline-visible v2 baton
  (`baton.json` is overwritten in place; truth survives only in
  `baton.v1raw.json`).
- **Fix:** converter prefers v1 `viewport.dpr_requested/dpr_actual` when
  present. **Guard test:** round-trip v1-with-fallback → v2 asserts
  requested=3.0/actual=1.0 (no round-trip test exists; the converter test
  fixture uses stale `viewport.dpr=3`).

### V5 — spec-audit C13: variant "pin" records a selection-independent constant on Shopify
**Status 2026-06-12:** FIXED `f2de7b0` and `f55530d`; JS regression guard `6f8f323`.
- **Where:** `_APPLY_FIRST_AVAILABLE_JS`, `scripts/ecp_configurator.py:81-96`.
- **Bug (verified):** resolves variant identity as
  `ShopifyAnalytics.meta.product.variants[0].id` — the product's FIRST variant,
  constant per product (the live field is `meta.selectedVariantId`, which
  appears nowhere in the repo); fallback 2 grabs the first `[data-variant-id]`
  element; the only honest fallback (3) is shadowed wherever ShopifyAnalytics
  exists. Both devices record the same id → the cross-device
  `variant_divergence` check (`contracts/trace-assertion-canary.md:237-252`)
  false-negatives on the awdmods 2026-05-18 class whenever the URL has no
  `?variant=`. Tests stub the JS so it is uncaught.
- **Fix:** read `meta.selectedVariantId` (post-select) with `variants[0].id`
  only as a labeled last resort (`variant_source` should say which). Related
  U-item: the swatch-by-variant-index branch records `url_pinned: true` for a
  heuristic click (`ecp_configurator.py:160-175`) — make it honest while in
  the file.

## Phase 3 — gaps in the EXECUTED claim (spec axis)

- **S1 — spec-audit C11 is half-done.** Recording is real; the reveal pass is
  unscoped (`acquire_url.py:825-833` still force-paints global selectors +
  kills all animation), the contract's `dom_state_modified` field is
  unemittable under the v2 schema (`workflows/acquire.md:243-268` vs
  `schema/baton-v1.json:83-109`), and **the reveal-pass placeholder is
  anchorable** — synthesized with `is_offscreen: False`
  (`baton_v1_to_v2.py:235`) so it enters hero cluster context as citable
  evidence (1×1 rect at origin), the §4.1 fabrication class. Minimum fix:
  flip the placeholder to `is_offscreen: True` + extend
  `test_acquire_capture_truth_phase4.py:533-568` to cover it; then reconcile
  the contract/schema on `dom_state_modified` or rewrite the contract to the
  presence-in-list convention.
- **S2 — the promised G21-style frozen-mode non-invokability guard was never
  built** (roadmap Phase 5 end-item; spec-audit M2 list "§5 frozen modes not
  invokable"). The test labeled as it guards a different property. Build: a
  test asserting `skills/` contains no build/compare/quick-scan/resume skill
  dirs and the plugin surface exposes only `/ecp:audit`.
- **S3 — spec-audit M2 is pins-partial.** Still test-free after the wave: §2.2
  URL-only-input rejection, §2.4 audit-stops (no plan/review artifact), §5
  frozen-inputs rejected, §4.1 fabrication self-skip
  (`scripts/assembly/business_rules.py` untouched in range). Pin or formally
  defer each.

## Phase 4 — unverified mediums (single-reviewer claims; verify before fixing)

| ID | Claim | Where |
|---|---|---|
| U1 | Overlay dismissal clicks unrelated UI on overlay-free pages, ≤6–10 rounds, no progress gate; substring selectors over-match | `scripts/ecp_acquire_overlays.py:134-208` |
| U2 | A9 gate fails open per-device: missing/corrupt review-state file silently exempts that device (corrupt-file weaker than no-file; pinned deliberate by `test_g8:279-294`) | `scripts/assembly/report_state.py:113-146` |
| U3 | normalize verb re-validates schema only — business rules (incl. anchor-registry for `element.baton_index`, a placement-bearing allowlisted field) never run at the chokepoint | `scripts/test-specialist.py:1016-1032` |
| U4 | normalize chokepoint is opt-in: SKILL.md:135 + dispatch-contract.md:196 still mandate the old hand-edit flow; canary skip-passes with no trail | `skills/audit/SKILL.md:135` |
| U5 | `_probe_doc_height` catch-list misses `subprocess.CalledProcessError` — new pre-capture crash point | `scripts/acquire_url.py:791-795` |
| U6 | hc-C3 unit conflation: `true_max_scroll_px` (a scrollY) used as `page_height_px` base → undercounts ~1 viewport in single-shot path; test pins the conflated value | `scripts/baton_v1_to_v2.py:321-327` |
| U7 | C6b ref validation runs before positional index assignment → legacy engagements (no sidecars) lose ALL Priority Path links; C5 residual renders false "applies on the other device" chip for PASS/CLEAR-filtered refs | `scripts/report/html_builder.py:165-182`, `scripts/report/v2_loader.py:1162-1167` |

Also recorded, info-tier, no action required: W2 `malformed_refs` has no render
surface; the hedge canary's token list is permissive (bare `may` matches the
month); duplicate local_ids silently share extras (first-wins is the pinned
contract).

## Phase 5 — operational pre-gate checklist

- **O1 — stale plugin on the work box (CONFIRMED 2026-06-10):** `claude plugin
  list` on `C:\Users\SM - Dan\...` shows `ecp@ecommerce-conversion-psychology
  v1.4.1` (failed-to-load state). Run the CLAUDE.md removal procedure
  (uninstall user+project scope, marketplace remove, restart) and re-verify
  before any live session there.
- **O2 — per-machine ROOT hardcoding in the QA workflows (CONFIRMED):**
  **Status 2026-06-12:** FIXED `88172cf` and `244cd0c`.
  `.claude/workflows/ecp-visual-qa.js:14` defaults to the work-box path,
  `ecp-report-qa.js:13` to the home-box path — each breaks on the other
  machine, and the canonical invocation (`contracts/report-export.md:82`)
  passes no root. Fix: derive ROOT from cwd or an env var; pre-existing but
  LV3 depends on it.
- **O3 — the live LV2–LV4 `--plugin-dir` `/ecp:audit` session** (the roadmap's
  one remaining gate) — run only after Phase 1 lands; the session doubles as
  live verification for V1/V2 (check the rendered report has zero (50,50)
  phantom markers).
