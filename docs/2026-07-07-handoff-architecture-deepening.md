# Handoff — architecture deepening pass (2026-07-07)

Session ran the `improve-codebase-architecture` review on ECP, then implemented
the safe wins in small commits **straight to `main`** (Dan's GitHub contribution
contest + he switched machines mid-way). This doc is the cross-machine resume
point — the full HTML review report was written to an OS-temp dir (ephemeral) and
the candidate roadmap also lives in this box's local `.claude` memory (does **not**
travel), so **this file is the source of truth on the other PC.**

## What landed on `main` (all both-runner green — pytest + unittest)

| Commit | Candidate | What | Verified |
|--------|-----------|------|----------|
| `a71288e` | **C4** | One home for the 85/70 giant-rectangle threshold. `assembly/visual_quality.py DEFAULT_GIANT_*` is canonical; `v2_markers` / `placement_audit` / `placement_repair` import it. Sync test broadened to pin all 4 consumers. | tests + import smoke |
| `b1422c8` | **C1 step 1** | Placement seam: new `scripts/report/placement.py` with typed `Placed \| Blank` + `decide_placement(finding, PlacementContext)`. `auto_map_markers_v2` is first consumer (byte-identical via `_to_mapping`). `parse_baton_index`/`_element_y`/`_element_height` moved there. | tests + byte-identical output |
| `ec8b619` | **C3** | **REAL BUG FIX.** `review_state._build_snap_targets` normalized snap-target Y by `section_h`; the section screenshot is a viewport-height capture, so snapped / placement-repaired markers landed low by `(1 − section_h/viewport_h)`. Fixed via pure `_element_snap_pct` (viewport_h). | tests + regenerated a real editor shows the correction (e24 95%→82%) |
| `fa9e5d1` | C3 hardening | End-to-end placement-Y coverage for `section_h != viewport_h` across multiple sections (the suite only had one-viewport fixtures, which hid the bug). Sibling-bug sweep of the section-height pattern came back clean. | tests |

Test baseline after this session (this work box, with local engagements):
**pytest 1490 passed / 11 skipped · unittest 1022 OK.** Runner-parity floor is 1312
(clean-clone-derived — don't re-floor from a box with local engagements).

## ⚠️ ACTION FOR DAN — hand-test the C3 fix

The C3 fix is **behavior-changing on the hotspot surface** and was pushed without a
hand-test (Dan was away). Verify before relying on it for a client report:

1. Regenerate an editor: `python scripts/generate-editor.py --engagement docs/ecp/<id> --plugin-root .`
   (pick an engagement whose early sections are shorter than a viewport — most are).
2. Open `editor.html`, use **snap-to-element** on an element near the **bottom** of the
   first/second section.
3. **Expected:** the marker snaps **onto** the element. **Before the fix** it landed
   ~135–177px *below*. Section 3 (where `section_h == viewport_h`) was already correct
   = control.

If it looks wrong, `git revert ec8b619` is clean — but the evidence (4 engagements'
`section-N.jpg` measured at viewport height; the renderer already normalizes by
viewport_h) is strong.

## Declined (do not re-suggest)

- **C7 — ValidationContext for `validate_business_rules`.** The silent-skip footgun is
  already closed at the runtime caller (`test-specialist.py:560` threads every kwarg incl.
  `anchor_candidates_sidecar`). The ~70 test callers use the optional-kwargs form
  intentionally (partial-context single-rule testing). A context object would force 70
  callers to build one to relocate 6 kwargs and **fails the deletion test**. Not worth it.

## Remaining candidates — each needs Dan's eyes (not safe to push blind)

Ordered by value. All touch the client deliverable or the live runtime path, which
pytest does not fully vouch for — that's why they were held.

- **C2 — one in-memory finding + `merge()`** carrying `reference_citations`, consumed by
  `dedup` / `pipeline` / `v2_loader`. **Dan's ruling: IN-MEMORY ONLY — do NOT change the
  on-disk finding schema (frozen §7).** Blocker: the 3 merge sites are at different
  representation levels (Finding dataclass vs raw dicts), so a true consolidation is a
  restructure of when Finding objects are built; the v2 merge path is driven by the live
  `/ecp:audit` runtime and can't be byte-identical-verified standalone.
- **C1 step 2+** — migrate `review_state` / `placement_audit` / `placement_repair` to
  consume the typed `Placed | Blank` (+ `Blank.reason`: absent / offslide / no_geometry /
  unresolved_baton_index) instead of re-deriving from `match_method` strings. Behavior-
  preserving but large surface (review_state ~1249 lines); marginal locality gain.
- **C5 — unify the two forked marker renderers** (`components.py` CSS-div vs
  `review_state.py` SVG). **Dan's ruling: KEEP the v1 render path (`markers.py`) — unify
  renderers only, do NOT delete v1.** Rendering-output change → needs visual hand-test.
- **C6 — make `scripts/` importable + rename `test-specialist.py`** (core runtime
  mis-named as a test; hyphenated files force `importlib` shims). Highest blast radius:
  ripples through `SKILL.md`, contracts, and the live `/ecp:audit` path that pytest can't
  verify.

## Checked and deliberately left alone (not shallow)

- `templates/css.py` (1620 lines) — one function `get_report_css(...)` behind it = **deep**,
  not shallow. Length is unfactored volume, not interface bloat.
- v1 vs v2 HTML builders — a **real seam** sharing machinery (`v2_html_builder` imports
  `html_builder` helpers), not a fork. The genuine forks are the marker resolver
  (`markers.py` vs `v2_markers.py`) and renderer (`components.py` vs `review_state.py`) — see C5.
- ~7 dead one-off `write_*`/`run_*`/`temp_*` scripts — already **gitignored/untracked**
  (`.gitignore` 43-49). Deleting them is working-tree hygiene, not a commit.

## Next steps

1. Dan: hand-test C3 (above). If good, C3 is fully done.
2. When at a hand-testable machine, tackle C2 / C5 / C6 with byte-identical or visual
   verification. Recommended order: C2 (highest value) → C5 → C6 (riskiest last).
