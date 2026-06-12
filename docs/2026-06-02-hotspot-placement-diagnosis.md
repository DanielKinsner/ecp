# Hotspot Placement Diagnosis — awdmods.com homepage audit (2026-06-02)

> **📜 HISTORICAL — banner added 2026-06-12.** Point-in-time diagnosis (2026-06-02). Placement is now exact-tier-or-blank with absences always manual (spec v1.2), and the live triage tool is `scripts/diagnose_engagement.py` (see [2026-06-08-hotspot-diagnosis-protocol.md](2026-06-08-hotspot-diagnosis-protocol.md)). Superseded as a work pointer by the consolidated 2026-06-09/10 roadmap ([reviews/2026-06-10-consolidated-findings-and-plan.md](reviews/2026-06-10-consolidated-findings-and-plan.md), EXECUTED) and its post-roadmap fix plan ([reviews/2026-06-10-post-roadmap-review-and-fix-plan.md](reviews/2026-06-10-post-roadmap-review-and-fix-plan.md)). CLAUDE.md §"Start here" is the live pointer.

| Field | Value |
| --- | --- |
| Engagement ID | `2026-06-02-4f121e87` |
| Page | https://www.awdmods.com/ |
| Scope | Comprehensive, dual-device (desktop + mobile) |
| Author | ECP audit lead (multi-agent diagnosis workflow) |
| Artifacts | Live under `docs/ecp/2026-06-02-4f121e87/` (gitignored — paths referenced, not committed) |

## Executive summary

Element-anchored hotspots (`source=e_index_lookup` or `source=proposed_anchor_element` against a real `eN`) placed correctly on both devices (confirmed). Every misplacement in this engagement is an "absent" finding that fell through to section-level placement — concretely, 17 findings resolved to a single `(kind=section, placement=section-bottom-overlay, section_index=0)` point per device (confirmed: 6 desktop + 10 mobile + 1 ethics out of 40 absent findings). The upstream cause is acquirer element-capture gaps (the hero's `FIND PARTS` submit, the four YMM `<select>`s, and the `$75` free-shipping bar are all missing from `elements[]` on both devices) plus a mobile coverage cliff (sections cover 2305 / 8622 px = 26.73 %) — not specialist discipline (confirmed). The renderer's "0 unplaced" status means *every* finding received coordinates via the 4-strategy resolver, not that the coordinates are subject-accurate (confirmed); a placement-confidence signal would have flagged this run.

## What went wrong (symptoms)

- **Total emissions:** 80 findings across 13 files — 36 desktop, 36 mobile, 8 page-scoped ethics (confirmed).
- **Element-anchor vs absent split:** desktop 18/18, mobile 17/19, ethics 5/3 (confirmed). No finding had a null/missing `element.baton_index`.
- **Post-audit verification result (this engagement, `verification-report.md`):** desktop **23 of 28** unique findings placed correctly (5 misplaced); mobile **~22 of 31** (the absent-hero collapse below). Element-anchored markers were accurate on both devices; the misses are entirely section fallbacks (confirmed).
- **Collapse point:** 17 findings — across 5 of 6 clusters plus ethics — share `(kind=section, placement=section-bottom-overlay, section_index=0)` and therefore resolve to the same `(slide, x_pct, y_pct)` per device (confirmed). Verified examples on the same desktop pixel: visual-cta F-24 (hero missing primary CTA), trust-credibility F-10 (no above-fold trust signal), performance-ux F-05 (empty black hero zone), performance-ux F-70 (vehicle-selector gate), performance-ux F-21 (50+ checkout-bundle prefetches), pricing F-41 (free-ship threshold without progress).
- **Mobile cluster of absent-hero findings collapsing to one point:** the 8 unique mobile findings carrying `section-bottom-overlay/section_index=0` on `slide_id=mobile-section-1` (incl. content-seo F-32 title-tag, content-seo missing meta description, content-seo missing `og:image`, content-seo F-62 missing schema, performance-ux F-04 empty mobile hero, performance-ux F-69 four-dropdown gate, performance-ux F-20 checkout prefetches, category-navigation F-33 missing category tiles) all render to `(50.0, 77.737)` (confirmed: `review-state-mobile.json` lists 16 `proposed_anchor_section` markers on slide-1 = 8 unique f_refs × AI-twin; the literal `(50.0, 77.737)` is computed by the renderer at HTML build — the raw review-state stores `x_pct=0/y_pct=0` and the % is derived from section geometry, see Mechanism).
- **AI-twin double-counting:** this engagement emits each `f_ref` twice with a `-ai` twin at identical coordinates (confirmed: desktop 58 marker rows / 29 unique f_refs; mobile 62 / 31). Twins inflate raw marker counts but never introduce a *new* misplacement; treat per-unique-`f_ref` tallies as the source of truth.

## Mechanism: section-bottom-overlay stacking

The renderer (`scripts/report/v2_markers.py`, `_resolve_section_placement`) computes `section-bottom-overlay` coordinates as:

```
target_y_page = section_top + (effective_bottom - section_top) * 0.90
y_pct         = (target_y_page - slide.scrollY) / viewport.height * 100
x_pct         = _SECTION_BOTTOM_OVERLAY_X_PCT   # 50.0, constant
```

Both axes are functions of `baton.sections[section_index]` geometry plus the device viewport — there is **no per-finding input** (confirmed; source line ~375, constants at line ~116). Consequently every finding that resolves to the same `(device, section_index)` lands on the exact same pixel.

For this engagement's mobile baton (`baton-mobile.json`: `sections[0].scroll_y_top=0`, `scroll_y_bottom=729`, `viewport.height=844`, `page_height_px=8622`):

```
eff_bot       = min(729, sections[1].top - 1, 8622) = 729
target_y_page = 0 + (729 - 0) * 0.90              = 656.1
y_pct         = 656.1 / 844 * 100                  = 77.73696682…
```

Result: the 16 mobile `proposed_anchor_section` slide-1 markers (8 unique f_refs × AI-twin) all stack at `(50.0, 77.737)`, source `proposed_anchor_section`, `snapped_baton_index=null` (confirmed). Desktop shows the homologous 12-marker stack (6 unique f_refs × AI-twin) on `desktop-section-1` (confirmed).

Two non-pathological fallback paths exist and behave correctly:
- `viewport-bottom-sticky` at `(50.0, 92.0)` — correctly typed for sticky-bar absence claims; only the 2 mobile sticky-bar findings use it here (visual-cta F-67, performance-ux F-18 — 4 marker rows with twins) (confirmed).
- `after-section` pins at `next_section.top - 12` — gap-between-sections semantics, distinct from `section-bottom-overlay`; used by 2 desktop findings only (confirmed).

The G6 oversized-exact downranker (`_downrank_oversized_exact`, thresholds 85 % width / 70 % height) demotes giant parent-container `e_index_lookup` matches to `visual_evidence=proxy_element / confidence=low / dashed` (confirmed). This run shows no evidence that the G6 path is contributing to the stacking — the stacked markers were never `exact_element` to begin with.

## Root cause 1: acquirer hero element-capture gaps

The CAPTURE baton starves downstream findings of any way to anchor to the hero. On both devices, the hero's load-bearing controls are missing from `elements[]` despite being present in `dom.html` (confirmed):

| Hero control | In `dom.html`? | In desktop `elements[]`? | In mobile `elements[]`? |
| --- | --- | --- | --- |
| `FIND PARTS` submit button | Yes (quick-filter form) | 0 hits | 0 hits |
| YMM `<select>` dropdowns (Make/Model/Year/Trim) | Yes | 0 `<select>` tags | 0 `<select>` tags |
| `FREE SHIPPING on most orders $75+` bar | Yes | 0 hits | 0 hits |

What *did* make `elements[]` on desktop (100 elements) and mobile (82 elements): search `<input>`s, drawer close/back buttons, a newsletter button, and several `"What are you looking for?"` placeholders (confirmed). No hero CTA, no nav links, no announcement bar. `anchor-candidates-{desktop,mobile}.json` corroborate — zero references to `FIND PARTS`, a Make/Year select, or `$75`; the lone `"free shipping"` hit is a generic vocabulary description, not a page-derived anchor (confirmed).

Likely extractor mechanism (likely): the YMM `<select>`s render with inline `width:0/height:0/opacity:0` before the storefront JS enhances them into custom widgets, so a visibility-gated extractor drops them. The announcement bar uses responsive-visibility classes which may also be filtered. (Separately corroborated this run: the `pricing-mobile` specialist flagged in its `notes[]` that the `$75` free-ship bar is visible in `section-1-mobile.jpg` but absent from the element index.)

Effect on findings: any hero-level finding has no `e_index`/selector to point at and **must** degrade to section-level fallback (confirmed). This is a forcing function on the specialist, not a discipline failure.

## Root cause 2: mobile screenshot/section coverage

Capture caps sections at 3 per device regardless of page length (confirmed: 6 screenshot files total — `section-{1,2,3}{,-mobile}.jpg`).

| Metric | Desktop | Mobile |
| --- | --- | --- |
| `capture_state.page_height_px` | 3240 | 8622 |
| Last `sections[].scroll_y_bottom` | 2895 | 2305 |
| Coverage | 2895 / 3240 = **89.35 %** | 2305 / 8622 = **26.73 %** |
| Uncovered tail | 345 px (10.65 %) | **6 317 px (73.27 %)** |
| Section labels | generic, viewport-sliced ("Above the fold (hero, navigation, primary CTA)" / "Primary content block 2" / "Lower page section 3"), `id=None` on every section (confirmed) |

Mobile section 0 spans `0..729` — ~8.5 % of the actual page — and is the only mobile band any hero-absent finding can fall into. At the desktop slice cadence, mobile would need ~12 sections to cover its 8622 px page. The combination of (a) hero element-capture gaps and (b) a single mobile hero band covering <9 % of the page is what concentrates the mobile absent-hero findings onto one pixel.

The sections are not semantic — they are viewport-sliced bands with generic labels and `id=None` (confirmed). Even with perfect specialist discipline, "anchor to the hero section" cannot mean anything more precise than "land somewhere in the 0..729 band."

## Why desktop fared better

Two structural reasons, both confirmed against the artifacts:

1. **Coverage ratio.** Desktop captured 89.35 % of `page_height_px`; mobile captured 26.73 %. The mobile collapse-band absorbs more "hero-ish" findings than the desktop one because there is nowhere else for them to land.
2. **Absent-finding fallback mix.** Desktop's 18 absent findings spread across multiple placements — 6 section-bottom-overlay/sec0, 5 element/before-element, 3 element/after-element, 2 section/after-section/sec1, 2 section-bottom-overlay/sec1, 0 viewport (confirmed). Mobile's 19 split far more narrowly — 10 section-bottom-overlay/sec0, 5 element/after-element, 2 element/before-element, 2 viewport/viewport-bottom-sticky, **0 after-section, 0 sec1 overlay** (confirmed). Mobile concentrates risk because the specialist has fewer usable section indices and no `e_index` to anchor to for the hero.

## The through-line + known prior occurrence

This is the same defect class documented for the **2026-05-01 awdmods run** in `contracts/specialist-prompt-v2.md` (and recapped in the sibling `docs/2026-06-02-awdmods-audit-qa-investigation.md` as "Pattern D — canned section-bottom-overlay on slide-1") (confirmed). In that prior engagement, `section-bottom-overlay` on `section_index=0` rendered onto category-card screenshots because the next section's geometry overlapped; `_effective_section_bottom` now clamps the overlap, but the *anchor-choice* defect is unchanged.

The prose guidance in `contracts/specialist-prompt-v2.md` — "use `kind:element` against `FIND PARTS`" — cannot be followed when `FIND PARTS` is not in `elements[]` (confirmed: 0 hits both devices). The specialist did the right thing within the constraints it was given: when the only available anchors are generic viewport-sliced sections, `section-bottom-overlay` is a defensible choice. **This is an acquirer-coverage problem upstream of any specialist-discipline rule.**

## Recommended fixes (hunches, prioritized)

| # | Fix | Layer | Expected impact | Confidence |
| --- | --- | --- | --- | --- |
| 1 | **Capture the hero CTA / YMM dropdowns / promo bar into `elements[]` and anchor-candidates.** (a) Emit `<select>` controls even when inline style sets `width:0/height:0/opacity:0` before JS enhancement (custom-widget pattern); (b) emit announcement-bar text nodes regardless of responsive-visibility classes; (c) emit the form submit button (`FIND PARTS`). Re-test that the candidate list contains `FIND PARTS`, a Make/Model/Year/Trim select, and the `$75` free-ship string on both devices. | Acquirer | Removes the *forcing function* behind ~13 of the 17 stacked findings (each hero-CTA / promo-bar / YMM-gate concern gets a real `eN`). | hunch (high confidence the path works; medium on exact uplift) |
| 2 | **Lift the mobile section/screenshot cap so coverage tracks `page_height_px`.** Today: 3 sections fixed. Proposed: tile to `ceil(page_height_px / viewport.height * overlap_factor)` so an 8622-px mobile page gets ~12 sections; cap by absolute screenshot count for cost. | Acquirer | Mobile coverage 26.73 % → ~95 %+. Even when fallback fires it lands in the *right* band. | hunch |
| 3 | **Renderer/business-rule guard: reject `(section-bottom-overlay, section_index=0)` for hero "absent" findings.** Either (a) force an element anchor (return `unplaced` if none — Strategy 4 already does this safely) or (b) place at a finding-aware hero-band coordinate (distribute stacked findings across the band by ordinal rather than collapsing to `y=77.737`). Prefer (a) — Strategy 4 was designed to surface manual-placement decisions instead of guessing. | Renderer | Removes the visible stack even when Root Causes 1+2 lag. Trades "wrong-coordinate marker" for "no marker, editor flags for manual." | likely |
| 4 | **Add a placement-confidence signal to the renderer summary** so "0 unplaced" cannot read as "all correct." Count `(source=proposed_anchor_section, snapped_baton_index=null)` markers as `weak_placements_count`; warn when ≥3 markers share identical `(slide, x_pct, y_pct)`. | Renderer + observability | Catches Pattern-D recurrences automatically in CI / audit-trace; matches the G6 "make low-confidence visible" philosophy. | likely |

Fixes 1 + 2 address the upstream root causes and are the durable answer. Fixes 3 + 4 are renderer-side guards that contain the symptom and prevent silent recurrences — ship them in parallel since neither blocks the acquirer work.

---

*Generated by a 5-agent diagnosis workflow (4 grounded investigators — anchor strategy, acquirer coverage, renderer geometry, device differential — + synthesizer). Numbers verified against engagement `2026-06-02-4f121e87` artifacts and `scripts/report/v2_markers.py`; cross-engagement claims from the workflow's first pass were corrected to this engagement's data before commit.*
