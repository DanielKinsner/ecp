# Handoff — Hotspot-Accuracy Program (2026-06-03)

**North star:** the HTML report's hotspot overlays land on the element each finding
is about — and we can *verify that visually* without a human eyeballing every box.
Everything below serves that one goal.

This is the rolling handoff for the placement/acquirer arc. For the broader AMS-style
chain see the project memory; this file is ECP-specific.

---

## TL;DR

- **Both upstream root causes of hotspot misplacement are now fixed in code** and on `main`.
  - Root Cause #1 — acquirer dropped the hero controls (YMM dropdowns, submit buttons,
    promo bars, gallery thumbs) → no `eN` to anchor to. **Fixed** (`5634e18`).
  - Root Cause #2 — mobile captured only ~27% of the page in non-contiguous bands →
    most of the page had no section image for a hotspot to anchor to. **Fixed** (`764d726`).
- **The verification side is built**: a tiered visual-QA gate (vision agents look at each
  suspect hotspot crop and judge on-target/misplaced) + a deterministic Tier-0 analyzer +
  an auto-reanchor/flag repair loop with a diagnostic log.
- **All four diagnosis fixes (#1–#4) are now in code.** #3 (hero-stack distribute + flag)
  shipped this session as `de95dfa`; #4 is substantially covered by the placement_audit tool.
- **One thing is blocked:** behavioral confirmation needs a single live `/ecp:audit`
  (~45 min, needs an agent-browser machine). That **one audit verifies both root causes** (and
  lets you eyeball the Fix #3 distributed hero column) — see the runbook below.
- **The best audit-independent next step is folding Fix #4's `weak_placements_count` into the
  renderer summary / CI**, then wiring the visual-QA gate into the audit flow.

---

## The two-sided model

| Side | Question | Status |
| --- | --- | --- |
| **Capture** (acquirer) | Did we grab the element + a screenshot band it lives in? | RC#1 + RC#2 fixed |
| **Verify** (renderer + QA) | Does the rendered box actually sit on that element? | gate built; Fix #3/#4 pending |

The 2026-06-02 diagnosis (`docs/2026-06-02-hotspot-placement-diagnosis.md`) prescribed **four**
fixes. #1 and #2 are the durable upstream answer (now done). #3 and #4 are renderer-side guards
that contain the symptom and prevent silent recurrence.

| Fix | What | Status |
| --- | --- | --- |
| #1 | Capture hero controls into `elements[]` / anchor candidates | **DONE** `5634e18` |
| #2 | Mobile coverage tracks page height (contiguous tiling) | **DONE** `764d726` |
| #3 | Hero absent-finding stack: distribute up the band + flag for manual review (operator chose "distribute + flag" over pure force-unplaced) | **DONE** `de95dfa` |
| #4 | Surface placement confidence in the render summary so "0 unplaced" ≠ "all correct" | **MOSTLY DONE** via `placement_audit.py` + visual-QA gate; remaining = fold the signal into the renderer's own summary/CI |

**All four diagnosis fixes are now in code.** The only thing left before a confident
"hotspots are accurate" claim is the single live verification audit (runbook below).

---

## What shipped this session

Placement/acquirer arc on `main` (newest first):

```
764d726 fix(acquirer): contiguous mobile screenshot tiling (Root Cause #2)
882d1a0 feat(capture-coverage): control-coverage verification tool for the acquirer fix
5634e18 fix(acquirer): broaden element-capture selectors for hero controls (Root Cause #1)
74ffef4 fix(placement): P3 hardening batch + threshold-sync test
e5d33db fix(visual-qa): vote math vs configured VOTES + deterministic crop dirs
6d35f02 fix(placement): clamp crop coords + catch offset full-bleed targets
5c31442 fix(placement-repair): prefer *_override text + slide-locality on re-anchor
8471e2a fix(visual-qa): triage null guard + surface MIX coverage gap
0e6c908 fix(placement): crash guards — corrupt screenshot + non-dict root
5bc2bb6 fix(visual-qa): persist re-verify verdicts + reconcile no-verdict re-anchors
873d901 fix(placement-repair): editor-readable confidence + valid source enum
d1a9a59 feat(visual-qa): fold repair + re-verify into the workflow (one command)
2f48779 feat(placement-repair): auto re-anchor + flag + diagnostic log
20f8192 feat(workflow): ecp-visual-qa — tiered visual hotspot-placement gate
13a14a3 feat(placement-audit): crop compositor for vision verification
133faab feat(placement-audit): Tier-0 hotspot-placement confidence analyzer
```

Plus the adversarial type-review batch that preceded it (30 type bugs + cross-OS
`force_utf8_io()`; see `docs/2026-06-03-adversarial-type-review-findings.md`).

Suite: **1085 passed, 13 skipped** (`python -m pytest tests/`). Run pytest, not
`unittest discover` — the latter skips bare pytest-style funcs.

---

## Root Cause #2 — what the fix actually does (for the record)

The mobile cliff was **two** compounding bugs, not one:

1. `_plan_scroll_ys` hard-clamped *every* device to `min(6, …)` shots.
2. It then spread those shots **evenly across `max_scroll`**, which only tiles correctly when
   the shot count ≈ `ceil(doc_h / inner_h)`. On an 8622-px mobile page (390×844 viewport) that
   meant 6 windows spaced ~1556px apart, each only 844px tall → **~712px dead zones between
   every captured window.** Elements in the gaps were never screenshotted, so their hotspots
   had no section image to land on.

Fix (`scripts/acquire_url.py`):
- Per-device caps: `MAX_SCREENSHOTS_DESKTOP = 6`, `MAX_SCREENSHOTS_MOBILE = 12`.
- `_plan_scroll_ys` drops the `min(6)` clamp and tiles to
  `ceil(doc_h / inner_h × SCROLL_OVERLAP_FACTOR)` (1.1 overlap), bounded by the device cap.
- `--max-screenshots` default is now `0` = auto per-device cap; a nonzero value still overrides.
- The hybrid recovery pass uses the device cap too, so it can't silently re-shrink mobile.

**Cost:** ~+6 mobile screenshots per audit (12 vs 6). Bounded and tunable via the two module
constants — if 45 min creeps up, lower `MAX_SCREENSHOTS_MOBILE`, no code surgery.

**Known residual:** mobile pages taller than ~10,100px (12 × 844) still clip beyond 12 tiles —
the documented cost cap. If a real PDP exceeds that, options are (a) bump the constant or
(b) a future full-page stitched capture. Not a blocker for typical Shopify PDPs.

---

## THE verification runbook (one audit verifies both root causes)

**Blocked on:** an agent-browser machine + interactive `/ecp:audit` (~45 min). When you can run it:

1. **Run a fresh audit on a YMM/PDP page** (the canonical reproducer is a Shopify PDP with a
   Make/Model/Year gate — e.g. awdmods or slingmods):
   ```
   /ecp:audit https://www.awdmods.com/ --visual
   ```
   Give me the new engagement id (the `docs/ecp/<date>-<hash>/` folder).

2. **Root Cause #1 — capture coverage (control buckets):**
   ```
   python scripts/report/capture_coverage.py compare --before docs/ecp/2026-06-01-749a3c3d --after docs/ecp/<new>
   ```
   **Baseline (old code, all 12 existing engagements):** dropdown / submit_input / gallery /
   promo / aria_named ≈ **0**. **Success = any of these go 0 → non-zero** in the new audit,
   especially a Make/Model/Year `<select>` and the `FIND PARTS`/submit button.

3. **Root Cause #2 — mobile coverage:**
   - `baton-mobile.json` should show **~11–12 sections** on a tall PDP (was ~3–6), spanning
     to the page bottom (last `sections[].scroll_y_bottom` ≈ `page_height_px`, not ~27% of it).
   - `python scripts/report/placement_audit.py audit --engagement docs/ecp/<new> --device mobile`
     should show **fewer weak/stacked** markers than the mobile baseline (10 hero findings
     collapsed onto one pixel in `2026-06-02-4f121e87`).

4. **End-to-end visual proof — the gate:**
   ```
   # via the dynamic workflow (Claude Code v2.1.154+):
   #   .claude/workflows/ecp-visual-qa.js  args: { engagement: "<new>", device: "mobile", tier: "deep" }
   ```
   Success = vision agents confirm the hero hotspots are **on-target**, and the repair loop's
   diagnostic log shows **fewer "element-capture gap" reasons** than before.

**One audit covers all four checks.** Don't burn two.

---

## What's next (prioritized)

**A. Run the verification audit** (runbook above) — the one remaining blocker on a confident
"hotspots are accurate" claim. Verifies RC#1 + RC#2 in a single ~45-min run. Also eyeball that
the hero stack now renders as a distributed, manual-flagged column (Fix #3) rather than one pin.

**B. Diagnosis Fix #4 — placement confidence in the render summary.**
Largely already built (`placement_audit.py` counts weak placements + flags ≥3-on-a-pixel
stacks). Remaining: fold `weak_placements_count` into the renderer's own summary output / CI
trace so "0 unplaced" can never read as "all correct" without running the gate. Audit-independent;
the next knockable.

**C. Wire the visual-QA gate into the audit flow.** Today it's standalone
(`.claude/workflows/ecp-visual-qa.js`); `workflows/audit.md` doesn't call it. Folding a
`free`-tier Tier-0 pass into the audit (and `--visual` → `standard`/`deep`) makes placement
QA automatic instead of a remembered manual step.

**D. Residual long-mobile-page coverage** (>~10k px) — see RC#2 note. Low priority.

**Fix #3 — how it landed (for the verification eyeball).** Absent findings that share the
auto-injected `(section_index=0, section-bottom-overlay)` anchor are now spread up the section
band by ordinal (`scripts/report/v2_markers.py:_distribute_stacked_section_markers`), relabeled
`match_method="section_stacked_manual"` → finding `hotspot_confidence="needs-manual-marker"`
(editor "Place manually" queue) with a valid `proposed_anchor_section` source. Markers still
render at their distributed positions; nothing disappears. In the new audit, the hero band that
used to show one stacked pin should show a vertical column of manual-flagged markers.

---

## Cost dial (the thing that was holding us back)

The gate is tiered so you only pay for vision when you want it:

| Tier | What runs | Cost |
| --- | --- | --- |
| `free` | Tier-0 deterministic triage only (no vision) | $0 |
| `standard` | + 1 vision verifier on flagged crops (MIX cap 8) | low |
| `deep` | + 3-verifier majority on flagged crops (MIX cap 40) | higher |

Default is `standard`. Use `free` in CI for a zero-cost regression signal, `deep` for the
one verification audit above. The acquirer's +6 mobile shots add to acquire time/tokens but
not to the gate cost.

---

## Reference index

- Diagnosis (the source of truth for the 4 fixes): `docs/2026-06-02-hotspot-placement-diagnosis.md`
- Placement-QA review (validated + fixed): `docs/2026-06-03-adversarial-placement-qa-findings.md`
- Type-review batch: `docs/2026-06-03-adversarial-type-review-findings.md`
- Acquirer: `scripts/acquire_url.py` (`_build_elements_js`, `_plan_scroll_ys`, `_device_screenshot_cap`)
- Capture-coverage instrument (RC#1): `scripts/report/capture_coverage.py`
- Tier-0 analyzer: `scripts/report/placement_audit.py`
- Repair loop + diagnostic log: `scripts/report/placement_repair.py`
- The gate: `.claude/workflows/ecp-visual-qa.js`
- Audit runbook the skill follows: `workflows/audit.md`; skill: `skills/audit/SKILL.md`
- Baseline corpus: 12 engagements under `docs/ecp/` (all pre-fix acquirer code)
```
