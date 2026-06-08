# Audit Run Review — awdmods.com homepage (`2026-06-08-8e46b1c8`)

> Read-only post-run review of the ECP v2 audit conducted 2026-06-08 against the AWDMods.com homepage (desktop + mobile, comprehensive scope). Produced by a 7-agent read-only review workflow (3 parallel gatherers → adversarial trust assessment → synthesize → strict verify → finalize), then **corrected by the lead after a ground-truth check overturned the workflow's central P0** (see §7 and §11). No audit artifacts were modified by this review.

---

## 1. Plain-English Summary

An ECP v2 audit ran against the AWDMods.com homepage for both desktop and mobile, end to end: it captured both viewports, ran 12 cluster specialists plus an ethics pass, assembled 68 canonical finding references, synthesized a 5-item Priority Path, wrote two markdown reports + two annotated visual HTML reports + a hotspot editor, and finished with **every hard quality gate passing** (schema validation, cross-device drift gate, structural + substantive canaries). It is a clean, **complete DRAFT** engagement.

The review workflow initially flagged a P0 ("the lead claims it hand-fixed three specialist outputs, but two aren't logged and one was never actually changed"). **I verified that claim against the files and it is wrong** — a correlated misread by two of the review's own agents (they confused finding-index 3 with finding-index 1). All three normalizations *did* persist, both edited emissions *do* re-validate, and the client-facing finding content was preserved. The two "empty" `.repairs.json` files are the **autofix tool's** logs (autofix correctly did nothing on those two); the hand-edits are recorded in `lead-reflection.md` + `audit-trace.log`, which is where they belong. Details and evidence in §7 and §11.

What remains true and worth acting on is smaller but real: (1) the lead *did* hand-normalize three emissions, which the SKILL contract discourages ("never hand-edit beyond autofix") — a documented, correctly-executed deviation, not a correctness failure; (2) those hand-normalizations live only in prose, not in a machine-diffable record a canary could check — a transparency/enforcement gap; (3) the documented workflow has genuine contradictions (the acquirer deletes the meta file the lead is told to write first; an undocumented baton v1→v2 conversion the run depends on); and (4) the browser-cleanup step force-killed the operator's real Chrome. None corrupted the client reports.

**Bottom line: DRAFT BUT COMPLETE.** Every deliverable exists, every hard gate passes, content is intact and validated. It is not CLIENT-READY only because the manual client-verification gate (re-check the live site, follow every citation link, finalize hotspot placement) is by design a separate human pass that has not been run.

---

## 2. Run Context

| Item | Value | Source / confidence |
|---|---|---|
| Repo path | `C:\Users\SM - Dan\Documents\GitHub\ecp` | env — verified |
| Engagement folder | `docs/ecp/2026-06-08-8e46b1c8` | `meta.json` |
| Engagement ID | `2026-06-08-8e46b1c8` | `meta.json.id` |
| URL | `https://www.awdmods.com/` (homepage; normalized `awdmods.com`) | `meta.json.page` |
| Platform / page type | shopify / homepage | `meta.json` — **inferred** (detected from DOM `cdn.shopify.com` / `/cdn/shop/`, not operator-specified) |
| Device(s) | desktop (1920×1080) + mobile (390×844) | `meta.json.devices_requested` |
| Scope | comprehensive, 6 CRO clusters | `meta.json.scope` / `clusters_used` |
| Branch / commit (at run) | `main` / `134d39c` | git |

**Exact request acted on:**
`/ecp:audit https://www.awdmods.com/ lets do desktop and mobile viewports.  the comprehensive landing page clusters.  i just want markdown and visual html reports as deliverables and you can proceed when ready.`

**Flags — NONE were explicit.** Everything was inferred from the free-text request:

| Flag | Inferred value | Inferred from |
|---|---|---|
| `--device` | `desktop,mobile` | "desktop and mobile viewports" |
| `--focus`/scope | `comprehensive` | "the comprehensive landing page clusters" |
| `--visual` | implied (reports generated) | "visual html reports" |
| `--platform` | `shopify` | acquisition-time DOM detection (not requested) |
| `--auto` / `--deep` | not set | — |

Cluster resolution: homepage → comprehensive = `visual-cta, trust-credibility, content-seo, performance-ux, pricing, category-navigation` (6). The "mobile in device set → ensure performance-ux" and "significant price display → ensure pricing" overrides both re-confirmed clusters already present.

**Plugin / runtime loading method: INDETERMINATE from the lead's vantage.** `generate-report.py` was invoked with `--plugin-root <repo-root>`, consistent with both an installed plugin and a `--plugin-dir` dev load. *How* the skill was loaded into the session happens in the CLI host before the skill runs and is not recorded in any artifact. The session cwd was `C:/Users/SM - Dan` (not the repo), and the lead read contracts from `<repo-root>/contracts/*.md` by absolute path — its first reads under `skills/audit/contracts/` failed because contracts live at repo root, not under the skill dir. Per the repo's own CLAUDE.md, a real `/ecp:audit` should be launched with `--plugin-dir` against the working tree; whether that happened here is unverifiable from the artifacts.

---

## 3. Step-by-Step Timeline

| # | Phase | Status | Files created | Notable events / fallbacks | Matched contract? |
|---|---|---|---|---|---|
| 1 | Setup & init | ✅ complete | `meta.json` (v3 stub), `audit-trace.log` | engagement dir created; clusters resolved | Yes |
| 2 | Acquisition | ✅ complete | `baton.json`, `baton-mobile.json`, `dom.html`, `dom-mobile.html`, `section-*.jpg` (3 desktop + 4 mobile) | acquirer Task subagent ran `acquire_url.py --both --hybrid`; emitted **v1-shape batons** → `baton_v1_to_v2.py`; acquirer **cleared the lead's meta.json** (non-empty-dir guard) → lead rebuilt v2 meta; **mobile apparent-truncation investigation** (see §3 note) → no recovery needed; **broad `chrome` kill likely closed operator's real Chrome** | Partial — see §5 |
| 3 | DOM preprocess | ✅ complete | 12 `cluster-context-*.json`, 2 `anchor-candidates-*.json` (desktop 54 / mobile 53 candidates), 12 `.prompts/specialist-*.txt` | 0 empty clusters skipped | Yes |
| 4 | Specialist dispatch (Layer 1) | ✅ complete (with repairs) | 12 `cluster-*-{device}.json`, `dispatch-manifest.json` | 12 opus subagents in 2 waves of 6 (desktop, then mobile) | Yes |
| 4.5 | Ethics gate (Layer 1.5) | ✅ complete | `ethics-findings.json` | 1 sonnet subagent; US-jurisdiction + false-positive guards; 1 ADJACENT, 7 CLEAR, 0 BLOCK | Yes |
| 5 | Emission validation (P0-08) | ✅ complete (after fixes) | `*.repairs.json` (autofix logs) | 3/13 failed first pass → ethics **autofixed** (4 repairs) + 1 telemetry entry dropped; visual-cta-mobile + category-nav-mobile **hand-normalized** (schema/placement metadata only); all 13 re-validate | Partial — see §5 #1 |
| 6 | Canonical f_refs | ✅ complete | `canonical-f-refs.json` (68 / 7 clusters), `-manifest.json`, `-manifest.md`, `canonical-frefs-dropped.json` (empty) | 0 dropped | Yes |
| 7 | Baton trim | ✅ complete | `baton-{desktop,mobile}-trimmed.json` + summaries | desktop 20/140, mobile 22/140 elements | Yes |
| 8 | Synthesizer (Layer 3) | ✅ complete | `synthesizer-emission-v1.json` (5 stories), `audit-desktop.md`, `audit-mobile.md` | 1 opus Task subagent | Yes |
| 9 | Synthesizer validation | ✅ pass | — | validates vs canonical f_refs allowlist | Yes |
| 10 | Cross-device drift gate | ⚠️→✅ | (edit to `audit-mobile.md`) | **FAILED first** at 0.1108 > 0.10 on content-seo F-32 (citation-line absorption false positive; obs/rec byte-identical) → lead unified F-32 citation → re-ran **0.0000 PASS** | Partial — see §5 #5/§7 |
| 11 | Substantive canaries | ⚠️→✅ | (counter lines appended to trace) | **trace_counters_reconcile FAILED** (parser skipped counters with trailing parentheticals; `cluster_files_written` missing) → clean `key: <int>` lines appended → **all hard canaries PASS**; `visual_evidence_proxy_overload` SOFT WARN (64%/71%) noted | Partial — see §5 #5 |
| 12 | Render (Layer 4) | ✅ complete | `visual-report-{desktop,mobile}-v2.html`, `editor.html`, `review-state-{desktop,mobile}.json` | **0 unplaced**; desktop 1 weak / 2 stacks, mobile 3 weak / 1 stack | Partial naming — see §5 #3 |
| 13 | Reflection & final state | ✅ complete | `lead-reflection.md` | `--mark-reflection-complete` (required `--device`+`--plugin-root` or it errored) → `reflection_state=complete`; `engagement_status=complete`; `report_state=draft` | Partial — see §5 #4 |

**§3 note — the mobile "truncation" investigation:** The converted `page_height_px` read **8622px** and elements reached y=6756, while only 4 mobile screenshots covered ~2305px — *looking* like ~73% of the page was missed. The lead built a patched copy of `acquire_url.py` (warm-scroll + a true-scrollable-height probe), which returned `true_max_scroll=1461`, and `section-4-mobile.jpg` shows the footer + "© 2026, AWDMods." (real page bottom). Conclusion: the mobile page genuinely is ~2305px; the high-y elements are the **off-canvas hamburger drawer** (`menu-drawer__navigation` h=4059), correctly captured per the acquirer's always-include-off-canvas rule. **No data was missing; no recovery was performed.** This was a *confirmation*, not a recovery — but it consumed real effort and triggered the Chrome-kill side effect (see §7).

---

## 4. Artifact Inventory

58 artifacts present; 100% of expected deliverables exist.

**Deliverables (client-facing):**

| Artifact | Status | Size | Role |
|---|---|---|---|
| `audit-desktop.md` | ✅ | ~54 K | Desktop report (32 findings + ethics) |
| `audit-mobile.md` | ✅ | ~54 K | Mobile report (31 findings + ethics) |
| `visual-report-desktop-v2.html` | ✅ | 1.2 M | Annotated desktop report (3 screenshots embedded) |
| `visual-report-mobile-v2.html` | ✅ | 1.4 M | Annotated mobile report (4 screenshots embedded) |
| `editor.html` | ✅ | ~2.1 M | Editable dual-device hotspot tool (bonus) |

**State / trace:** `meta.json` (schema v3; `engagement_status=complete`, `report_state=draft`, `reflection_state=complete`), `audit-trace.log`, `lead-reflection.md` (6.1 K). **Acquisition:** `baton.json` / `baton-mobile.json` (v1→v2, 140 elements each), `dom.html` / `dom-mobile.html`, 7 `section-*.jpg`. **Layer 1/1.5:** 12 `cluster-*-{device}.json`, `ethics-findings.json` (8 findings). **Layer 2:** `canonical-f-refs.json` (68) + `-manifest.json`/`.md`, `canonical-frefs-dropped.json` (empty), `baton-*-trimmed.json` + summaries. **Layer 3:** `synthesizer-emission-v1.json` (5 stories, 61 humanized findings). **Layer 4:** `review-state-{desktop,mobile}.json`. **Repair logs:** `ethics-findings.repairs.json` (4 repairs), `cluster-visual-cta-mobile.repairs.json` (0 repairs), `cluster-category-navigation-mobile.repairs.json` (0 repairs). **Intermediates (normal):** 12 `cluster-context-*.json`, 2 `anchor-candidates-*.json`, `dispatch-manifest.json`, `.prompts/` (13).

**On the two "0-repair" sidecars (corrected):** `cluster-visual-cta-mobile.repairs.json` and `cluster-category-navigation-mobile.repairs.json` correctly show `repairs_count: 0` — these are **autofix** logs, and autofix legitimately found nothing autofix-safe to repair in those two files. The lead's subsequent **hand-normalizations** of those emissions are recorded in `lead-reflection.md` and `audit-trace.log`, not in the autofix sidecar. (The review's gather/trust passes misread these empty autofix logs as "edits not logged"; see §7 and §11.) No expected artifact is missing.

---

## 5. Contract Drift / Contradictions

| # | Sev | Drift | Contract vs. reality |
|---|---|---|---|
| 1 | **P1** | **Hand-edits beyond autofix** | `skills/audit/SKILL.md` Validation step 1: *"never hand-edit an emission beyond what autofix repaired."* The lead hand-normalized 3 emissions after autofix (ethics telemetry drop; visual-cta-mobile `surface trust-strip-11→other`+note; category-nav-mobile dropped a divergent anchor). The contract's stated path is re-dispatch on 2nd failure. **The edits were correctly executed and validate (see §7), but the action itself is a contract deviation.** Mitigating: each is documented in `lead-reflection.md` + `audit-trace.log` and changed only schema/placement metadata, not client-facing prose. |
| 2 | **P1** | **Phase order ⊥ acquirer non-empty-dir guard** | SKILL phase order step 3 writes `meta.json` *before* step 5 acquisition; `acquire_url.py` refuses a non-empty dir (`if eng_dir.exists() and any(eng_dir.iterdir()): error`). The acquirer cleared the lead's `meta.json`+trace to proceed, wrote a quick-scan `meta.json`, and the lead rebuilt v2 state post-acquisition. Two frozen contracts are mutually incompatible on the critical path. |
| 3 | **P2** | **`-v2` HTML naming undocumented** | SKILL "Artifact Contract" says `visual-report.html`; `contracts/report-export.md` says `visual-report-{device}.html`. Actual files are `visual-report-{device}-v2.html` (the v2 renderer hardcodes `-v2`). Docs never mention the suffix. |
| 4 | **P2** | **`--mark-reflection-complete` undocumented required args** | SKILL implies a bare invocation; `generate-report.py` marks `--device` and `--plugin-root` `required=True` unconditionally, so the bare verb errors before the reflection-complete handler runs. The run hit this and had to re-invoke with both flags. |
| 5 | **P2** | **Trace counter format ambiguity** | `contracts/trace-assertion-canary.md` defines counter syntax but doesn't forbid trailing annotations; the parser requires a clean `key: <int>` line, so `specialists: 12 (wave2…)` parsed as 0 → canary FAIL → reformat + rerun. Spec gap that costs a rework cycle whenever a lead annotates counters. |
| 6 | **P2** | **Undocumented baton v1→v2 conversion** | `workflows/acquire.md` says the baton validates against `schema/baton-v1.json`; SKILL phase order has **no** v1→v2 conversion step, yet `acquire_url.py` emits v1-shape batons and the v2 pipeline requires the converted shape. The conversion (`baton_v1_to_v2.py`) is load-bearing but inferred. |
| 7 | P3 | `docs/ecp` gitignored | `.gitignore` ignores `docs/ecp/`; product.md §5 says engagements are working-tree-only. Consistent — noted because this review's engagement folder is force-added (`git add -f`) at the operator's explicit request for evidence. |
| 8 | P3 | Off-canvas mobile elements | `acquire.md` always-includes drawer/off-canvas selectors; the mobile high-y elements were captured per contract. No violation — the investigation confirmed the contract works (and surfaced a real follow-up: the converter's `page_height_px` is inflated by off-canvas elements; `true_max_scroll` is the honest signal). |

---

## 6. Validation Results

All structural validators and all HARD canaries pass. Two SOFT warns are within-spec for an absence-heavy homepage. **All numbers below were independently re-derived from the on-disk artifacts during this review (not taken from the run's own logs), and the two disputed emissions were re-validated post-review.**

**Schema validation**
- **12/12** cluster emissions PASS vs `cluster-emission-v1.json`.
- `ethics-findings.json`: 8 findings PASS (1 ADJACENT, 7 CLEAR, 0 BLOCK, 0 false-CRITICAL).
- `synthesizer-emission-v1.json`: PASS (status=complete, 5 priority_path stories, 61 humanized findings; `scope_page_synchronized_refs=2` → content-seo F-32, ethics F-16).
- **Post-review re-validation of the two hand-normalized files:** `cluster-visual-cta-mobile.json` → PASS, finding[3] `surface="other"` **with** `surface_note`; `cluster-category-navigation-mobile.json` → PASS, finding[2] `e32` anchor removed (anchors = `["section-1-mobile.jpg"]`).

**Drift gate:** PASS, `max_ratio = 0.0000` (threshold 0.10) after the F-32 citation unification. F-32 and F-16 each obs/rec/why = 0.0000. Both `audit-{device}.md` now carry an identical F-32 citation line.

**Canaries (final: `all_passed=True`)**

| Canary | Class | Result |
|---|---|---|
| `ethics_findings_have_source_urls` | HARD | PASS (1 actionable carries a valid non-self-cite URL; 7 CLEAR skipped) |
| `element_index_match_rate` | HARD | PASS — **1.000** (48/48 present-element findings cite a real baton index; 15 absent excluded; thr 0.80) |
| `cross_device_ethics_diff` | HARD | PASS — desktop=1, mobile=1, diff=0 (max 1) |
| `priority_path_count_parity` | HARD | PASS — synth=5; desktop 5/5, mobile 5/5 |
| `clusters_represented` | HARD | PASS — 6/6, 0 dropped |
| `trace_counters_reconcile_with_artifacts` | HARD | **FAIL → PASS** — under-counted 3 roles (trailing parentheticals); reconciled after clean-line append |
| `lead_reflection_not_stale` / `_well_formed` | HARD | PASS (after reflection written + `reflection_state=complete`) |
| `visual_evidence_*` exact-rectangle / priority-needs-review | HARD | PASS (0 over thresholds) |
| `visual_evidence_proxy_overload` (desktop) | SOFT | WARN — 64% (16/25) non-exact vs 40% |
| `visual_evidence_proxy_overload` (mobile) | SOFT | WARN — 71% (17/24) non-exact vs 40% |

**Placement QA (from render, no re-render performed):** 0 unplaced both devices. Desktop 25 hotspots placed (17 e_index + 7 proposed-anchor + 1 section), 2 stacks, 1 weak. Mobile 24 placed (14 e_index + 7 proposed-anchor + 2 viewport + 1 section), 1 stack, 3 weak. Stacks are head/meta findings (title/meta-description/og:image cluster near the logo) and a price/trust cluster on the featured grid. No `(not found)` / unresolved refs in either markdown report.

**Counting layers (not a contradiction):** ~71 raw specialist findings (12 emissions) → 68 canonical f_refs after dedup → 61 humanized/rendered (7 ethics CLEAR don't render) → 32 desktop / 31 mobile shown per device document. Different layers of the same pipeline; the run does not reconcile them in one place (a small clarity gap).

---

## 7. Trust Assessment (severity-ranked)

> **The single most important correction in this review:** the review workflow's trust + verify agents raised a **P0** asserting that two of three hand-edits were unlogged and that `cluster-visual-cta-mobile.json` finding[3] still had `surface="primary-cta"` (edit never applied). **I checked the files directly and that P0 is false** — a correlated index-confusion error by both agents (`primary-cta` is finding **[1]**, the FIND PARTS button; finding **[3]** is the FREE-SHIPPING/banner-blindness finding, correctly `surface="other"` + `surface_note`). Evidence: `cluster-visual-cta-mobile.json` finding[3] = `{surface:"other", surface_note: present}`; `category-navigation-mobile` finding[2] = `e32` removed; both re-validate `status: complete`. The empty `.repairs.json` are autofix logs, not hand-edit logs. There is **no P0**. See §11 for the meta-lesson.

### P1 — Hand-normalization is a real contract deviation (correctly executed)
- **What:** The lead hand-edited 3 emissions after autofix, which `SKILL.md` discourages ("never hand-edit beyond autofix… re-dispatch on 2nd failure").
- **Evidence:** `lead-reflection.md` ("Deviations observed"); `audit-trace.log` ("autofix+normalize applied…"); the edited files validate and titles/observations/recommendations are unchanged.
- **Why it matters:** It's a deviation from the letter of the contract, chosen to avoid re-dispatching (and possibly regressing) the other good findings in those emissions. Reasonable engineering, but it bypasses the contract's intended path.
- **Client-facing impact:** **None to correctness** — content preserved, schema valid. The impact is to *process discipline*, not the reports.

### P1 — Phase order ⊥ acquirer non-empty-dir guard
- **What:** The lead writes `meta.json` before acquisition; the acquirer refuses/clears a non-empty dir and wrote its own; the lead rebuilt v2 state.
- **Evidence:** SKILL phase order vs `workflows/acquire.md` guard; `audit-trace.log`; `lead-reflection.md`.
- **Why it matters:** Two frozen contracts contradict each other; success depended on the lead noticing and rebuilding state. Fragile for future runs.
- **Client-facing impact:** None — final `meta.json` is schema-valid and complete. Risk is to *future* runs (silent state loss if unnoticed).

### P2 — Hand-normalizations recorded only in prose, not a machine-diffable record
- **What:** The autofix path writes a structured `*.repairs.json` with before/after diffs; lead hand-normalizations are recorded only in `lead-reflection.md` + `audit-trace.log` (free text). There is no structured, canary-checkable record asserting "claimed edit == actual file state."
- **Evidence:** `ethics-findings.repairs.json` (structured, 4 diffs) vs the prose-only record of the visual-cta-mobile / category-nav-mobile hand-edits.
- **Why it matters:** This is *exactly* the gap that let the review's agents (and would let a future operator) suspect a non-persisted edit without being able to mechanically refute it. The edits here were fine — but the process can't *prove* it from a structured artifact. (Recommendation in §8 #2.)
- **Client-facing impact:** None directly; it's a transparency/auditability gap.

### P2 — Mobile height "investigation" was a confirmation framed as a discovery, and caused a side effect
- **What:** The reflection presents the mobile page-height investigation as resolving an apparent truncation; the data was always complete (off-canvas drawer). The investigation also triggered a broad `chrome` process kill that **likely closed the operator's real Chrome**.
- **Evidence:** `lead-reflection.md` (Rationalizations caught / Anomalies); `audit-trace.log` KNOWN-RENDER-RISK; `baton-mobile.json` max y=6756; no finding cites y>2305; 0 unplaced hotspots.
- **Why it matters:** The conclusion and the KNOWN-RENDER-RISK flag are correct, but an optional, side-effect-bearing experiment was run on the critical path. Process honesty matters when the reflection *is* the trust record.
- **Client-facing impact:** None on the reports. Operator-environment impact was real (Chrome closed; tab-restore mitigated).

### P2 — F-32 drift fix is correct but not independently reconstructable
- **What:** Drift failed at 0.1108 on content-seo F-32 (citation-line absorption — a known false-positive class); the lead unified the mobile citation to the desktop line and re-ran to 0.0000. Only the corrected state is visible in the artifacts.
- **Evidence:** `lead-reflection.md`; both `audit-{device}.md` now show the identical F-32 citation; trace records the rerun.
- **Why it matters:** The failure→fix can't be reconstructed from artifacts (no pre-fix ratio logged). The outcome is correct; the auditability is the gap.
- **Client-facing impact:** None — F-32 renders consistently in both reports.

### P2 — Trace counter format forced a canary rerun
- **What:** Initial counters carried trailing parentheticals; the int-parser read 0; `trace_counters_reconcile` failed; the lead appended clean `key: <int>` lines.
- **Evidence:** `audit-trace.log`.
- **Why it matters:** Spec doesn't forbid annotations, so this costs a rework cycle each time a lead annotates counters.
- **Client-facing impact:** None.

### P3 — `visual_evidence_proxy_overload` SOFT WARN (64% / 71% vs 40%)
- **What / why / impact:** Non-exact visual evidence exceeds the advisory threshold, expected for an absence-heavy homepage (no hero headline, meta description, og:image, schema, trust block, sticky CTA, MSRP/BNPL — all `generated_expected_zone`/`proxy_element`). Advisory only; all hard canaries pass; correctly rationalized. No trust impact; worth tracking as a recurring homepage pattern (§8 #4).

### P3 — Undocumented v1→v2 conversion + browser-cleanup hazard
- Documentation/operational debt: the v1→v2 baton conversion is load-bearing but undocumented; the cleanup step's bare `chrome` match can close the operator's real browser. Neither affects the reports; both affect repeatability and operator trust.

---

## 8. What I Would Do Differently (recommendations — no files changed)

1. **Resolve the acquire_url fragility cluster as a unit.** The v1-shape baton emission, the `meta.json` clobber (non-empty-dir guard), and the mobile height-measurement confusion are the *same* root problem: `acquire_url.py` is a v1-shaped, dir-destructive, height-naive tool glued onto a v2 pipeline. Fix it to **emit v2 directly**, **merge-not-clobber** into an existing engagement dir, and **probe true scrollable height natively** (`scrollTo(end) → read scrollY`, loop until stable). That removes three operator-dependent recovery steps and one undocumented conversion in one pass.
2. **Make lead hand-normalizations a first-class, canary-checked record.** Add a structured `*.normalizations.json` (parallel to autofix's `*.repairs.json`) that records every lead edit with before/after + reason, and a canary that asserts the recorded after-value equals the file's current value. This converts the §7 P2 transparency gap into a mechanical guarantee — and would have let this review *refute* its own false P0 in one step instead of a manual file read.
3. **Resolve the hand-edit-vs-redispatch tension at the policy level.** The contract says "never hand-edit / re-dispatch on 2nd failure," but the lead chose surgical normalization to avoid regressing ~29 good findings — a reasonable instinct. Either sanction a narrow, logged "normalize" tier between autofix and re-dispatch (with the mandatory record from #2), or make re-dispatch cheap (single-finding re-emission) so nobody is tempted to hand-edit. The current gap guarantees operators violate the letter of the contract under time pressure.
4. **Give absence/head-meta findings a first-class hotspot placement strategy.** The recurring stacks (head/meta findings near the logo; price/trust on the featured grid) and the 64–71% proxy_overload aren't run-specific bugs — they're structural: `<head>` and "missing X" findings have no on-page element to anchor to. Dedicated "ghost-zone" lanes for head-meta and for absence findings, with deterministic spread, would stop the stacking and let operators skip the manual spread pass.
5. **Pay down the v1/v2 + naming doc debt.** Document the `-v2` HTML suffix (SKILL Artifact Contract + report-export.md), document or remove the `--device`/`--plugin-root` requirement on `--mark-reflection-complete`, and either forbid or tolerate trailing annotations in trace counters. Individually trivial; collectively they're why this pipeline needs an expert operator who already knows the gotchas.
6. **Scope browser cleanup to Playwright PIDs / cache paths only — never a bare `chrome` name match.** This one has already cost the operator their live browser once.
7. **Make the drift fix auditable.** When a drift failure is resolved by editing a synced finding, append a one-line trace entry with the pre-fix ratio and the file/line changed, so failure→fix is reconstructable.

---

## 9. Final Verdict

### `DRAFT BUT COMPLETE`

Every deliverable exists; every hard quality gate passes; the findings are schema-valid, page-anchored, and content-intact; the ethics gate is clean with zero false-CRITICALs; 0 hotspots are unplaced. The review workflow's `UNTRUSTWORTHY-RERUN-REQUIRED` verdict was **based on a P0 that a ground-truth file check disproved** (a correlated agent misread — §7, §11); with that corrected, the honest verdict is a complete draft.

It is **not** `CLIENT-READY`: that status is reserved for after the operator's manual verification pass (re-check the live site, follow every legal/ethics citation link, finalize hotspot placement in `editor.html`, then `generate-report.py … --mark-client-verified`). That pass is by design separate and has not been run — `report_state` is correctly `draft`.

Residual items to address before *the next run* (not blockers for *this* draft): the P1 contract deviations (hand-edit policy; acquirer phase-order contradiction) and the P2 transparency gaps. None changes the content of the two markdown reports or the two visual reports already produced.

---

## 10. Reviewer's Broader Opinions

**The bones are genuinely strong — this is a real quality system, not theater.** Content-hash-stable canonical f_refs, a cross-device drift gate, an `element_index_match_rate` canary that hit 1.000, ethics-diff parity, priority-path parity, trimmed batons feeding the synthesizer, and a draft→client-verified state machine that *refuses* auto-promotion — these are opinionated, load-bearing safety nets. The substantive layer is tuned for the actual domain: on an absence-heavy homepage it produced 0 false-CRITICAL ethics findings and correctly cleared the shipping threshold, genuine low-count reviews, decorative imagery, US-only jurisdiction, and touch targets. The fact that the drift gate *fired at all* on F-32 means the net is live, not decorative.

**The single biggest structural risk is that the trust record and the artifacts can diverge — and nothing mechanically catches it.** The whole value proposition is that you don't re-read 71 findings by hand; you trust the canaries, the repair sidecars, and the reflection. In *this* run the edits were fine, but the review still couldn't *prove* it from a structured artifact — it took a manual file read to refute a plausible-sounding P0. The narrative layer (reflection, trace prose) is currently **trusted but not enforced**. Every claim a lead writes about what it did to a finding should be mechanically diffable against the file it claims to have changed, with a hard canary on mismatch. Right now the most authoritative-*sounding* artifact (the reflection) is the *least* machine-verified.

**Top 5 highest-leverage improvements, in order:**

1. **Enforce the narrative (recommendation §8 #2).** Make lead-edit-claim ↔ structured-record ↔ emission a mechanical canary. Highest leverage because it converts "trust me" into "proven," and it's the class of gap that most undermines the product. (It would also have made *this review* trivially self-correcting.)
2. **Kill the acquire_url fragility cluster (§8 #1).** v1-baton + meta-clobber + height-naivety are one root cause; fixing the acquirer to emit v2, merge-not-clobber, and probe true height removes three recovery steps and one undocumented conversion at once.
3. **Fix the hand-edit-vs-redispatch policy (§8 #3).** The contract is arguably wrong, not the lead — sanction a narrow logged "normalize" tier or make single-finding re-dispatch cheap. The current gap guarantees operators deviate under pressure.
4. **First-class placement for absence/head-meta findings (§8 #4).** Stop the stacking and the proxy_overload WARN structurally instead of leaning on the operator's manual spread pass.
5. **Pay down v1/v2 + naming doc debt (§8 #5).** Every inferred/undocumented step is a place the next operator — or the next model — guesses wrong. This is the difference between "needs an expert operator" and "runs reliably for anyone."

**Closing observation:** this run went *well* by its own machinery's standards, and the reasons it can't ship to a client today are a manual-verification gate (by design) and documentation/enforcement gaps — not a capability gap. That's the good kind of problem: the analysis quality and the safety nets are real; what's missing is making the *trust record* as rigorous as the findings it vouches for.

---

## 11. Meta-note: this review's own correlated false positive

Worth recording because it bears on how you use multi-agent review going forward. This review ran an adversarial structure (independent gather → adversarial trust → strict verify). **Two independent agents — the trust assessor and the verifier — reached the *same wrong conclusion***: that `cluster-visual-cta-mobile.json` finding[3] had `surface="primary-cta"` and the lead's edit never applied. Both had file access; both "checked." The verifier even **approved** the draft, citing the P0 as "materially confirmed."

The error: finding **[1]** (local_id 2) is the FIND PARTS button with `surface="primary-cta"`; finding **[3]** (local_id 4) is the FREE-SHIPPING/banner-blindness finding the lead actually edited to `surface="other"`. One agent's index confusion propagated into the verifier rather than being caught by it — adversarial verification is **not** robust to *correlated* errors when both agents share the same misreading heuristic.

It was caught only by a direct `python -c "json.load(...); print finding[3]"` against the live file. Practical takeaways: (1) for any review claim that gates a verdict, **confirm against ground truth with a deterministic command**, not another LLM read; (2) the §8 #2 structured-normalization-record + canary would have made this self-refuting in one step; (3) "the verifier approved it" is not sufficient when the verifier and the author share an input-parsing failure mode. The pipeline's *deterministic* checks (schema validation, the canaries) never wavered — they correctly reported all 12 emissions valid throughout. The judgment layer is where the correlated error lived.

---

*Generated by a read-only review workflow, lead-corrected against ground truth. No audit artifacts were modified. The audit engagement folder (`docs/ecp/2026-06-08-8e46b1c8/`, normally gitignored) is force-committed alongside this report at the operator's request for downstream evidence.*
