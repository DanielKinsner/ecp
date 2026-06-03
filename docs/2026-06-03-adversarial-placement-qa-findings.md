# ECP — Adversarial Review: placement-audit / visual-QA feature (findings)

**Date:** 2026-06-03  ·  **Scope:** commits `133faab..d1a9a59` (HEAD), origin/main  ·  **Branch:** `main`

**Files reviewed (purely additive — 5 commits, +881 / −0):**
- `scripts/report/placement_audit.py` (Tier-0 analyzer + Tier-1 crop compositor)
- `scripts/report/placement_repair.py` (auto re-anchor + flag)
- `.claude/workflows/ecp-visual-qa.js` (tiered visual gate orchestration)
- `tests/test_placement_audit.py`, `tests/test_placement_repair.py`

**Method:** 5 dimension reviewers (audit-logic, repair-logic, workflow-seam, robustness, tests+claims) fanned over the changed files; each candidate finding was then run past **two independent skeptics** — a *reachability* lens ("can the bad input actually arrive given how this is invoked?") and a *code-accuracy* lens ("did the reviewer misread the code / is it already guarded?"). A completeness critic then hunted for what the dimensions missed. Finally the orchestrator re-verified the load-bearing claims against source.

**Tally:** 28 candidates → **22 confirmed** + 7 net-new from the completeness critic; **6 refuted**, several downgraded on reachability. Consolidated below to **24 findings** (duplicates merged) + 2 verified-good claims.

> **Status legend:** all findings are **proposed, not yet applied** — this doc is the review pass. Baseline today: **16/16 new tests pass**, feature is additive, no frozen-contract edits.

**Re-verified by orchestrator against source (not just agent-reported):**
- ✔ The editor confidence contract underpinning **[1]/[2]** — `editor.js` reads `f.hotspot_confidence` (finding-level) only, enum `["exact-selector","section-match","fallback-absence","needs-manual-marker"]` (`editor.js:16,252,266-271,284,463-464`; schema `review-state-v1.json:121-124`). `"low"` and marker-level confidence are inert; `placement_review_needed`/`repair_status` are not in the schema.
- ✔ The `_select_for_mix` cap math underpinning **[3]** (`n_weak = max(1, MIX-2)`).
- ✔ The "thresholds mirror visual_quality.py" claim **[V1]** (85/70 + identical `NON_EXACT_TYPES`).
- ✔ 16/16 tests green via `pytest tests/test_placement_audit.py tests/test_placement_repair.py`.

---

## Summary (by severity)

| # | Sev | File:Line | Category | Title | Verify |
|---|-----|-----------|----------|-------|--------|
| 1 | P1-high | `placement_repair.py:144-146` | dead-signal | FLAG branch writes `hotspot_confidence="low"`/`placement_review_needed` on the **marker**; editor reads finding-level enum → flag is a no-op | 2/2 + orch ✔ |
| 2 | P1-high | `placement_repair.py:135-138,154` + `ecp-visual-qa.js:146-161` | fail-unsafe | Re-anchor persisted UNVERIFIED with no editor-recognized flag; vision-reverted re-anchor stays on disk with wrong coords, renders "Likely OK" | 2/2 + orch ✔ |
| 3 | P1-high | `ecp-visual-qa.js:18` + `placement_audit.py:265-277` | silent-cap | Standard-tier `MIX=8` caps the gate at 6 weak markers; surplus weak placements are never verified/repaired but the report reads "verified" | critic + orch ✔ |
| 4 | P1-high | `ecp-visual-qa.js:140-159` | fail-unsafe | Re-anchor whose new slide has no screenshot is dropped from BOTH `fixed` and `reverted` → adopted unverified and unreported | critic |
| 5 | P1-high | `placement_audit.py:223` | crash | Corrupt/truncated screenshot crashes the entire `crops` command (no `try/except` around `Image.open`); missing-file path skips gracefully, this one aborts | 2/2 (finder P0) |
| 6 | P1-high | `placement_repair.py:107-160` | test-gap | `repair()` integration entirely untested — only `decide_match` covered; JS-consumed log/file shape unprotected | 2/2 |
| 7 | P2-medium | `placement_repair.py:60-62` + `placement_audit.py:259` | stale-data | `_query_tokens`/`make_crop` read `finding_title`, not `finding_title_override` → re-anchor/crop from pre-correction text | 2/2 |
| 8 | P2-medium | `placement_repair.py:66-71,83-104,135` | wrong-result | Re-anchor target chosen across ALL slides, no slide-locality constraint → confidently relocates a finding to the wrong section | critic |
| 9 | P2-medium | `placement_audit.py:238` | crash | `make_crop` PIL crop raises when marker coords are out of range (`x_pct>~111` → right<left); coords never clamped | 2/2 |
| 10 | P2-medium | `ecp-visual-qa.js:115` | logic | Vote attrition: `onTarget > v.length/2` divides by surviving votes → deep-mode 2-of-3 becomes unanimity when one verifier returns null | 2/2 |
| 11 | P2-medium | `placement_audit.py:114-115,296` + `placement_repair.py:111` | crash | Top-level review-state that isn't a dict → `AttributeError` on `.get()` (list elements guarded, root isn't) | 2/2 |
| 12 | P2-medium | `ecp-visual-qa.js:85` | crash | Triage agent result dereferenced with no null guard; the one un-guarded agent seam → null triage hard-fails the whole gate | 2/2 |
| 13 | P2-medium | `ecp-visual-qa.js:75-77,141-143` | brittleness | `<tmp_dir>` prose placeholders the agent must invent; two uncoordinated dirs, no cleanup (temp leak) | 2/2 |
| 14 | P2-medium | `placement_repair.py:115-116` | logic | `GIANT_W` filter can't catch offset full-bleed containers (`w_pct` clamped to `100-x_pct` upstream); partially backstopped by `GIANT_H` | 2/2 (1 lens uncertain) |
| 15 | P3-low | `placement_audit.py:75` | type-guard | Non-string `source` → `score_marker` `.startswith()` crash | 1/2 (unreachable on happy path) |
| 16 | P3-low | `placement_audit.py:245` | type-guard | Non-string `f_ref` → `make_crop` `.lower()` crash | 2/2 (malformed input) |
| 17 | P3-low | `placement_audit.py:246` | sanitize | `slide_id` interpolated raw into the crop filename (f_ref half IS slugged) → `/`/`..` escapes `out_dir` | critic |
| 18 | P3-low | `placement_audit.py:87` vs `:104,128` | consistency | `_dedup_by_fref` falls back to `id(m)`; `_find_stacks`/`analyze_device` fall back to `None` → id-less markers miss a real stack | 1/2 (unreachable, valid input) |
| 19 | P3-low | `placement_audit.py:245` | collision | Lossy f_ref slug can overwrite a PNG; unreachable for canonical f_refs (`^[a-z][a-z0-9-]*\s+F-\d{2}$`), real only for hand-edited ids | refuted→latent |
| 20 | P3-low | `placement_audit.py:197-204` | parse | `_screenshot_for` takes substring after last `-` as section N with no `isdigit` check → bogus `section-<text>.jpg` instead of clean None | critic |
| 21 | P3-low | `placement_repair.py:172` + `placement_audit.py:305` | seam-assumption | f_ref lists comma-joined across the JS→Python seam; an f_ref containing a comma splits into garbage tokens | critic |
| 22 | P3-low | `placement_repair.py:95-100` | diagnostic | `decide_match` empty-targets path emits "no baton element shares any subject text" when actually zero elements captured | 2/2 (phrasing) |
| 23 | P3-low | `placement_repair.py:121-151` | logic | Duplicate f_refs in `--misplaced` are double-processed (no dedup), inflating re_anchored/flagged counts | critic |
| 24 | P3-low | `placement_audit.py:240-242,280-323` | test-gap | `make_crop` resize-cap branch, `_cmd_audit`/`_cmd_crops` handlers, and the `make_crop(finding=None)` path have no tests | 2/2 |

**Verified-good (no defect):** [V1] threshold-sync claim TRUE; [V2] repair non-destructive + no frozen-contract edits TRUE.

**Refuted (considered, dropped):** stack-rounding pixel split (resolver writes byte-identical coords); slug collision for *valid* f_refs (grammar can't collide → downgraded to latent [19]); `skipped` f_refs vanishing (unreachable on the workflow path, still logged to disk); **unquoted space-bearing paths in the workflow** (these are `agent()` natural-language prompts, not `exec()` strings — a competent agent quotes spaced paths; the cited lines even contain `<tmp_dir>` placeholders that require interpretation); whole-workflow-untested (fail-safe glue, the risk-bearing `decide_match` core IS tested).

---

## P1-high — correctness / false-assurance

### 1. [P1-high] `placement_repair.py:144-146` — FLAG branch writes confidence the editor can't read
- **Symbol:** `repair` (flag branch)  ·  **Category:** dead-signal  ·  **Verification:** 2/2 skeptics confirmed + orchestrator re-verified `editor.js`/schema.
- **Trigger:** Any misplaced f_ref whose tokens find no/weak/ambiguous baton match → `decide_match` returns `action="flag"` (the common case per the module docstring). Runs via `ecp-visual-qa.js:131`.
- **Why it breaks:** The branch sets `marker["placement_review_needed"]=True` and `marker["hotspot_confidence"]="low"`. But the editor reads confidence **off the finding** (`f.hotspot_confidence`) and only recognizes `riskyConfidence = ["needs-manual-marker","fallback-absence","section-match"]` (`editor.js:16,463-464`). `"low"` is non-enum and lives on the wrong object, and `placement_review_needed`/`repair_status` aren't in `review-state-v1.json` at all. Net: a flagged finding renders as a plain "Review" item and **never enters the "Place manually" worklist** — the whole point of the FLAG path is inert downstream.
- **Proposed fix:** Set the flag on the **finding** with an enum value the editor consumes, e.g. `finding["hotspot_confidence"]="needs-manual-marker"`, and persist that finding into the repaired `rs`. Don't invent fields the schema/editor don't define.

### 2. [P1-high] `placement_repair.py:135-138,154` + `ecp-visual-qa.js:146-161` — re-anchor persisted UNVERIFIED with no fallback flag; reverted re-anchor stays on disk
- **Symbol:** `repair` (re-anchor branch) + workflow re-verify  ·  **Category:** fail-unsafe  ·  **Verification:** 2/2 confirmed (one lens called the "silent auto-adoption" framing slightly overstated — see below) + orchestrator re-verified the "Likely OK" render.
- **Trigger:** A finding whose anchor text lexically matches a baton element that is **not** the real subject (the "title vs description" case `decide_match`'s own docstring warns about). A live instance exists in the sample engagement (`content-seo F-64`, `docs/ecp/2026-06-01-749a3c3d`).
- **Why it breaks:** `marker.update(...)` writes the new box + `source="re_anchored"` + `repair_status="re_anchored_unverified"` and `repair()` flushes `.repaired.json` at line 154 — **before** any vision check, and with **no** editor-recognized low-confidence flag (unlike the FLAG branch). The workflow re-verifies and, on revert (`kept===false`), records it only in the in-memory return — it never rewrites `.repaired.json`. So a vision-rejected re-anchor stays on disk with the wrong coordinates; because the finding keeps its original `"exact-selector"`, the editor renders it **"Likely OK"** (`editor.js:271`). The docstring says the operator "adopts the repaired file," so the rejection is invisible there (it surfaces only in the ephemeral workflow JSON).
- **Caveat (honest):** the editor does not *auto-ingest* `.repaired.json`; adoption is an operator-gated manual swap, so "silently shipped to a client report" overstates it. Still a real footgun: nothing in the file distinguishes a vision-confirmed re-anchor from a rejected one.
- **Proposed fix:** Re-anchors must fail safe. Either (a) write an editor-recognized low-confidence flag on the finding when persisting an *unverified* re-anchor, so a skipped/reverted re-verify still queues it for manual review; and/or (b) have the workflow rewrite `.repaired.json` (or call a `repair.py --revert` mode) for reverted f_refs. The safe default belongs in the Python so it holds even if the JS re-verify is skipped.

### 3. [P1-high] `ecp-visual-qa.js:18` + `placement_audit.py:265-277` — the gate silently caps coverage at `MIX`
- **Symbol:** `MIX` const → `_select_for_mix`  ·  **Category:** silent-cap  ·  **Verification:** completeness critic + orchestrator re-verified the math.
- **Trigger:** Any engagement whose Tier-0 audit flags more than ~6 weak placements, run at standard tier (`MIX=8`).
- **Why it breaks:** `_select_for_mix` takes `n_weak = max(1, MIX-2)` weak markers (6 at standard) + up to 2 strong controls. Only those become `triage.crops`, and only crops are vision-verified and eligible for the misplaced→repair path. **Weak markers ranked below the cut are never verified and never repaired** — they pass the gate because the gate stopped looking. The audit summary still prints the true weak count (e.g. 30) while `totals.verified ≈ 8`, and nothing reconciles the gap, so the operator believes the page was fully QA'd. This is an emergent JS↔Python interaction no single-file reviewer would surface.
- **Proposed fix:** Either verify ALL flagged markers in standard tier (paginate the vision calls), or surface an explicit `"N weak placements NOT verified (MIX cap)"` line in the aggregate so the coverage hole is visible. Don't let a cost-control sample silently bound a pass/fail gate.

### 4. [P1-high] `ecp-visual-qa.js:140-159` — re-anchor to a screenshot-less slide is adopted unverified and unreported
- **Symbol:** repair re-verify pipeline  ·  **Category:** fail-unsafe  ·  **Verification:** completeness critic (not 2-lens; mechanically consistent with [2]).
- **Trigger:** A re-anchor that moves a marker to a different `slide_id` (see [8]) whose section screenshot is absent/corrupt.
- **Why it breaks:** `make_crop` returns `None` when `_screenshot_for` can't find the image (`placement_audit.py:220-221`), so that f_ref never appears in `recrop.crops`, and thus in neither `fixed` nor `reverted`. But `repair()` already persisted its new UNVERIFIED coordinates. Result: a re-anchor that was supposed to be vision-gated is silently adopted with no verification **and** no entry in the reverted list — strictly worse than [2] because it isn't even reported.
- **Proposed fix:** Reconcile `rep.re_anchored` against the reverify verdicts by `f_ref`; any re-anchor with no verdict must be force-flagged (`placement_review_needed`/enum confidence) and listed as unverified in the aggregate — never treated as fixed-by-omission.

### 5. [P1-high] `placement_audit.py:223` — corrupt screenshot crashes the entire `crops` command
- **Symbol:** `make_crop` / `_cmd_crops`  ·  **Category:** crash  ·  **Verification:** 2/2 confirmed + reproduced end-to-end. *(Finder rated P0; downgraded to P1-high — input-conditional, not happy-path.)*
- **Trigger:** A truncated/corrupt/placeholder `.jpg` in the engagement (realistic from a partial acquirer write; the test suite itself writes `b"x"` as a `.jpg`).
- **Why it breaks:** `_screenshot_for` only checks `cand.exists()` (line 204), then `Image.open(shot).convert("RGB")` runs with no `try/except` in `make_crop` or `_cmd_crops`. A file that exists but isn't a valid image raises `PIL.UnidentifiedImageError`, aborting the whole Tier-1 crop phase and losing the batch — whereas the missing-file path already returns `None` and skips that one marker.
- **Proposed fix:** Wrap `Image.open(...).convert(...)` in `try/except (UnidentifiedImageError, OSError): return None`, matching the existing `shot is None → return None` skip semantics so one bad screenshot degrades gracefully.

### 6. [P1-high] `placement_repair.py:107-160` — `repair()` integration is entirely untested
- **Symbol:** `repair`  ·  **Category:** test-gap  ·  **Verification:** 2/2 confirmed.
- **Trigger:** N/A (coverage gap). `test_placement_repair.py` imports only `decide_match, _overlap, _query_tokens`.
- **Why it matters:** `repair()` is the actual product entry the JS shells out to (`ecp-visual-qa.js:131`). The re-anchor mutation payload, the flag branch, the GIANT filter, the no-marker branch, and both file writes — including the **log/file shape the JS reads back** (`action:"re-anchored"/"flagged"`, the `.repaired.json` path) — are unexercised. A regression that renames a key (e.g. `snapped_baton_index`) or changes an action string ships green and only breaks at the JS boundary at runtime. (This test would also have caught [1].)
- **Proposed fix:** Add an integration test that monkeypatches `assembly.review_state._build_snap_targets` to return a fixed target dict, writes a temp `review-state-desktop.json`, calls `repair()`, and asserts (1) re_anchored/flagged counts, (2) the `.repaired.json` marker got `source="re_anchored"` + the target bbox, (3) the original file is byte-unchanged, (4) log entry shapes match what `ecp-visual-qa.js` reads.

---

## P2-medium — should fix

### 7. [P2-medium] `placement_repair.py:60-62` + `placement_audit.py:259` — query/crop text ignores the `*_override` title
- **Category:** stale-data  ·  **Verification:** 2/2 confirmed.
- **Trigger:** A finding whose title an editor corrected via `finding_title_override` (the title shown everywhere else), then re-run through repair.
- **Why it breaks:** `_query_tokens` iterates `("finding_title","callout_title","element")` and `make_crop` reads `finding_title or title` — neither reads the `_override`. Every other consumer prefers the override (`review_state.py:1102`, `editor.js:2846`). So repair builds its lexical query (and the crop label) from the **stale wrong subject**, biasing the match toward the wrong element. These two are the only `_override`-blind title readers in the codebase.
- **Proposed fix:** Prefer the override, mirroring `_display_title`: `finding.get("finding_title_override") or finding.get("finding_title")`, and `callout_title_override or callout_title`.

### 8. [P2-medium] `placement_repair.py:66-71,83-104,135` — re-anchor has no slide-locality constraint
- **Category:** wrong-result  ·  **Verification:** completeness critic (medium confidence on impact).
- **Trigger:** A page that repeats a label across sections (two "Add to Cart", footer-echoed nav, repeated "Buy Now") where the correct instance scores a hair lower or was filtered as oversized.
- **Why it breaks:** `_flatten_targets` pools every section's elements into one list; `decide_match` picks the global best label match with no requirement it lie on the finding's original slide, and `marker.update` rewrites `slide_id`. `MATCH_MARGIN` only guards when two near-equal scores survive — a single lexical twin on the wrong slide passes as "confident, unambiguous," producing a confidently-wrong cross-section placement.
- **Proposed fix:** Pass the marker's current `slide_id` into `decide_match`; prefer/limit candidates to that slide (or heavily penalize off-slide matches) unless there's positive evidence the original slide was wrong.

### 9. [P2-medium] `placement_audit.py:238` — `make_crop` crashes on out-of-range coords
- **Category:** crash  ·  **Verification:** 2/2 confirmed + reproduced (`x_pct=150` → PIL `right<left`). *(Secondary "resize-to-zero" claim refuted — the 220px margin floor prevents it.)*
- **Trigger:** A marker with `x_pct`/`y_pct` out of [0,100] — schema-valid (the upstream writer rounds without clamping) and reachable via the `--f-refs` override which bypasses `score_marker`.
- **Why it breaks:** `pct()` never clamps; an out-of-range left makes the crop box `left > right`, and PIL `Image.crop` raises `ValueError: Coordinate 'right' is less than 'left'`, aborting `_cmd_crops` mid-batch.
- **Proposed fix:** Clamp `pct()` output to [0,100] (or clamp the crop box so `x1>x0`, `y1>y0`) before `img.crop`.

### 10. [P2-medium] `ecp-visual-qa.js:115` — vote attrition raises the majority bar
- **Category:** logic  ·  **Verification:** 2/2 confirmed.
- **Trigger:** Deep tier (`VOTES=3`) when a verify agent returns null (the `.filter(Boolean)` exists precisely because they can).
- **Why it breaks:** `status = v.length && onTarget > v.length/2 ? 'on-target' : 'misplaced'` divides by *surviving* votes, not configured `VOTES`. One null → `v.length=2` → needs `onTarget>1` → **both** survivors must affirm (unanimity, stricter than 2-of-3); two nulls → a single vote decides. The reported denominator (`${VOTES}`) even disagrees with the decision denominator, masking the drift.
- **Proposed fix:** Compute against configured `VOTES` (e.g. `onTarget > VOTES/2` with a minimum-quorum check), or re-dispatch failed votes.

### 11. [P2-medium] `placement_audit.py:114-115,296` + `placement_repair.py:111` — non-dict root review-state crashes
- **Category:** crash  ·  **Verification:** 2/2 confirmed + reproduced (`[1,2,3]` → `AttributeError`).
- **Trigger:** A review-state file whose top-level JSON is a list/scalar (corrupt or hand-edited; `serve-editor` overwrites state from a POST payload).
- **Why it breaks:** `rs = json.loads(...)` then `rs.get("markers")` with no `isinstance(rs, dict)` check. The code already isinstance-guards list *elements* and `visual_evidence` but trusts the root — an asymmetric guard. Same in `_cmd_crops:296` and `repair:111`.
- **Proposed fix:** After `json.loads`, `if not isinstance(rs, dict): return None` (or raise a clear `ValueError`) in all three spots.

### 12. [P2-medium] `ecp-visual-qa.js:85` — triage result not null-guarded
- **Category:** crash  ·  **Verification:** 2/2 confirmed.
- **Trigger:** The single triage `agent()` returns null (schema mismatch / tool error). Every other call site uses `.filter(Boolean)`; this one doesn't.
- **Why it breaks:** `triage.crops.length` is dereferenced immediately (lines 85, 87) with no guard → `Cannot read properties of null`, hard-failing the whole gate before any verification, on every tier (free still dispatches triage). The sibling `ecp-report-qa.js:71` guards the analogous call — this seam diverges from the project's own convention.
- **Proposed fix:** `if (!triage || !Array.isArray(triage.crops)) return <error/empty report>`, consistent with the other sites.

### 13. [P2-medium] `ecp-visual-qa.js:75-77,141-143` — `<tmp_dir>` placeholder brittleness + temp-dir leak
- **Category:** brittleness  ·  **Verification:** 2/2 confirmed.
- **Trigger:** Every standard/deep run.
- **Why it breaks:** The crop `--out` dir is a prose placeholder (`<that_tmp_dir>`/`<tmp_dir>`) the agent must materialize and remember across the write and the manifest read; two independent agents (triage + recrop) each invent their own with no shared contract and no cleanup. `make_crop` writes `str(out_path)` (relative-or-absolute depending on what the agent passed), yet the schema then demands ABSOLUTE png paths, forcing agent post-processing. Happy-path works if the agent behaves; the leak is unconditional.
- **Proposed fix:** Compute a deterministic `mkdtemp` in JS and pass an explicit `--out` (and/or have `make_crop` emit absolute paths unconditionally); clean it up after.

### 14. [P2-medium] `placement_repair.py:115-116` — `GIANT_W` filter blind to offset full-bleed containers
- **Category:** logic  ·  **Verification:** 2/2 (one lens uncertain on impact).
- **Trigger:** A wide container whose left edge sits past ~15% of page width and whose right edge lands at/inside the page edge.
- **Why it breaks:** `_build_snap_targets` clamps `w_pct = min(100-x_pct, ...)` (`review_state.py:356`), so any element offset past 15% can never exceed `GIANT_W=85` regardless of true width — only the `x≈0` full-width case is caught. Such a container can survive the filter and win the lexical match (its `text_content` concatenates child text → high token overlap). **Mitigation:** the tall ones are still caught by `GIANT_H=70`; the residual cases are wide-but-short bands with less text, so impact is real but bounded.
- **Proposed fix:** Filter on geometric area or `(x_pct + w_pct)` reaching the right edge with large width, or compute the oversized flag from the unclamped element rect in `_build_snap_targets`.

---

## P3-low — hardening (mostly malformed/hand-edited input; one-liners)

The schema + canonical producer make most of these unreachable on the happy path, but they are the same "harden malformed input" class as the prior type-review batch, and the fixes are trivial.

### 15. [P3-low] `placement_audit.py:75` — non-string `source` crashes `score_marker`
`source = m.get("source") or ""` only normalizes falsy values; a truthy non-string (`123`) reaches `.startswith()` → `AttributeError`. `w_pct`/`h_pct` are isinstance-guarded; `source` isn't. **Reachability:** all producers + schema enum emit strings, so happy-path safe — latent. **Fix:** `source = s if isinstance(s := m.get("source"), str) else ""`.

### 16. [P3-low] `placement_audit.py:245` — non-string `f_ref` crashes `make_crop`
`fref = marker.get("f_ref") or "marker"` then `fref.lower()`; a truthy int f_ref → `AttributeError`, reproduced through the `crops --mix` CLI. Sibling code uses `str(f.get("f_ref"))`. **Fix:** `fref = str(marker.get("f_ref") or "marker")`.

### 17. [P3-low] `placement_audit.py:246` — `slide_id` unsanitized in the crop filename
`out_path = out_dir / f"{marker.get('slide_id','slide')}__{slug}.png"` — the f_ref half is regex-slugged but `slide_id` is interpolated raw, so a `/` or `..` escapes `out_dir` (path traversal / cross-dir scatter). **Fix:** slug `slide_id` with the same regex, or `os.path.basename` + reject components containing `os.sep`/`..`.

### 18. [P3-low] `placement_audit.py:87` vs `:104,128` — dedup vs stack-key fallback inconsistency
`_dedup_by_fref` falls back to `id(m)`; `_find_stacks`/`analyze_device` fall back to `None`. Markers lacking both `f_ref` and `marker_id` survive dedup (distinct `id`) but collapse to one `None` stack-key, so a real 3-stack is missed and `strong_frefs` get literal `None`s. **Reachability:** producer + schema always set both ids → latent. **Fix:** use one shared id helper (e.g. `... or f"_anon{id(m)}"`) in all three spots.

### 19. [P3-low] `placement_audit.py:245` — lossy f_ref slug can overwrite a PNG
Two f_refs that slug identically write the same filename; the second `crop.save` overwrites the first and the manifest points two entries at one image. **Reachability:** *refuted* for canonical f_refs — `^[a-z][a-z0-9-]*\s+F-\d{2}$` cannot slug-collide (verified across 1400 generated + all real engagements). Real only for hand-edited / non-ASCII ids → latent. **Fix:** append a short hash of the raw f_ref to the filename (also covers [17]).

### 20. [P3-low] `placement_audit.py:197-204` — `_screenshot_for` assumes a trailing integer
`n = slide_id.rsplit("-",1)[-1]` with no `isdigit` check → `desktop-hero` builds `section-hero.jpg` (silently maps to a nonexistent/colliding file rather than failing cleanly). Won't crash (falls through to `.exists()→None`) but masks malformed slide_ids. **Fix:** validate `r'-section-(\d+)$'` and return None on a mismatch.

### 21. [P3-low] `placement_repair.py:172` + `placement_audit.py:305` — comma is the sole f_ref delimiter
Both CLIs split `--misplaced`/`--f-refs` on comma, and the JS `join(',')`. An f_ref containing a comma splits into garbage tokens that resolve to no marker (silently dropped). Works today (`pricing F-65` has no comma) — unverified alphabet assumption across the seam. **Fix:** pass f_ref lists as JSON/newline-delimited, or document+enforce no-comma.

### 22. [P3-low] `placement_repair.py:95-100` — `decide_match` empty-targets reason is imprecise
With zero captured targets it emits "no baton element shares any subject text," implying elements existed and none matched. The failure-bucket (element-capture gap) is still correct — only the phrasing misleads the repair-log diagnostics. **Fix:** add an `if not targets:` branch with a distinct reason, + a test for the empty-targets case.

### 23. [P3-low] `placement_repair.py:121-151` — duplicate `--misplaced` f_refs double-processed
`misplaced` is split with no dedup; a repeated f_ref is processed twice (the second pass sees the already-mutated `source="re_anchored"` marker), inflating counts and emitting a contradictory log entry. Low impact today (workflow derives a unique set) but it's a public entry point. **Fix:** `dict.fromkeys(...)` at the top of `repair()`, and/or skip markers already `re_anchored`.

### 24. [P3-low] `placement_audit.py:240-242,280-323` — untested branches
The `make_crop` resize-cap (`>900px`), the `_cmd_audit`/`_cmd_crops` CLI handlers, `_select_for_mix`, and the `make_crop(finding=None)` path have no tests. No live defect (the scary resize-to-zero is unreachable), but a load-bearing surface. **Fix:** a `main(['crops', ...])` test over a temp engagement + a `section-N.jpg`, including an f_ref whose finding is absent and a `>900px` crop asserting `max(dims)<=900`.

---

## Verified-good (claims that hold)

### V1. Threshold-sync claim is TRUE — `placement_audit.py:38-44` vs `visual_quality.py:56-70`
`GIANT_WIDTH_PCT=85.0`/`GIANT_HEIGHT_PCT=70.0` and the 4-element `NON_EXACT_TYPES` are element-for-element identical to `visual_quality.py`. The docstring's "kept in sync by intent" is accurate today. **Residual risk:** the constants are duplicated literals with no shared import and no test asserting equality, so a future one-sided edit silently desyncs. **Suggested:** a one-line cross-module equality test (precedent exists at `test_g6_oversized_downrank.py:60-61`).

### V2. Repair is non-destructive + touches no frozen contract — `placement_repair.py:107-160`
The original `review-state-{device}.json` is read-only; the only two writes target `.repaired.json` and `placement-repair-log.json`. The lone frozen-code import is the read-only `_build_snap_targets`. `git show --stat 133faab..d1a9a59` confirms 5 files, +881/−0, no renderer/frozen edits. Claims hold.

---

## Suggested fix order (when you give the go)
1. **[1] + [6]** together — fix the editor confidence contract and land the `repair()` integration test that would have caught it.
2. **[2] + [4]** — make the re-anchor path fail safe (the highest operator-trust risk).
3. **[3]** — make the MIX coverage cap visible (or paginate).
4. **[5], [9], [11], [12]** — the crash guards (cheap, high-value).
5. **[7], [8], [10]** — the wrong-result logic fixes.
6. P3 cluster — batch the type-guards as one commit each per the prior review's cadence, each with a negative regression test.
