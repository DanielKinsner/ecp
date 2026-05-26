# Changelog

> **ERRATA for pre-v1.0 entries.** The changelog below preserves history back
> to v2.0. Some claims in the v5.x and earlier sections have been superseded
> by the v1.0 app-shell rewrite and subsequent hardening passes. Known
> superseded claims:
>
> - **CSP model (v5.x and earlier: "blocks all script execution").** The
>   current report uses `script-src 'unsafe-inline'` to host the three-panel
>   runtime. See `scripts/report/templates/html_structure.py` for the active
>   CSP meta tag.
> - **Flag surface (v5.x era: `--export-report`, `--cluster`).** `--export-
>   report` was retired when the in-report Export Brief modal shipped.
>   `--cluster` remains as a backwards-compat alias for `--focus` (see
>   `contracts/flags.md`).
> - **Legacy scroll-document builders** listed in v5.x release notes
>   (`build_tab_bar_html`, `build_priority_path_cards_html`,
>   `build_finding_cards_html`, `build_pass_cards_html`) were removed when
>   the three-panel app-shell shipped in v1.0.1. Git history preserves the
>   implementations.
>
> For the current state of architecture, flags, and the report runtime, see
> `README.md`, `ARCHITECTURE.md`, and `contracts/flags.md` — the changelog
> below is a historical record, not a live reference.

## 1.4.1 — 2026-05-02 (Hotspot placement + Priority Path render fixes)

Bug-fix release surfaced by the first `/ecp:audit` run on awdmods.com
(engagement `2026-05-02-9cd2a2ac`). Four discrete defects, four fixes:

### Bug A — every hotspot collapses onto slide 1

Acquirer subagents return `STATUS: COMPLETE` while leaving
`baton.{screenshots,sections}[].scrollY` null/zero. The renderer's
`_slide_for_y` then sees every slide reporting `scrollY=0` and pins
every element-anchored marker to slide 0, clamped to the bottom edge.
**Fix:** new `scripts/lead_prep.py normalize-scrolly` recovers the per-
section scroll position from each `elements{?-mobile}-sN.json` file's
`scroll_y_at_capture` field (which the JS eval populates correctly even
when the LLM-written baton omits it) and writes the values back into
the baton. Wired into `skills/audit/SKILL.md` `<phase_audit>` step 3a
as a mandatory pre-DOM-preprocess step.

### Bug B — hotspot_confidence lies about placement quality

`scripts/assembly/review_state.py:_hotspot_confidence` mapped both
`e_index_lookup` and `proposed_anchor_element` to `"exact-selector"`,
even when the e_index lookup hit an element whose y-coordinate sat
past every captured screenshot's envelope (off-slide → marker clamps
to bottom of nearest slide). The editor's "needs review" filter became
useless because every finding reported the same confidence value.
**Fix:** `scripts/report/v2_markers.py` now detects degenerate
placements (no-geometry elements, off-slide y-coordinates) and emits
the new `e_index_lookup_offslide` match_method, which `review_state.py`
maps to `"fallback-absence"` — already a legal enum value, no schema
break, editor's `riskyConfidence` array already includes it. Also
added `operator_override → exact-selector` and demoted the conflated
`proposed_anchor_viewport → needs-manual-marker` to `"section-match"`
since viewport anchors are real positioning signals, not bail-outs.

### Bug C — Priority Path tab missing from HTML reports (resolves via D)

`v2_loader.load_v2_priority_path` correctly drops Priority Path stories
whose actionable-ref count falls below 2 — but when finding f_refs
disagree with priority_path[].f_refs (Bug D below), every story falls
below the threshold and the tab silently empties. No code change here;
fixing Bug D restores the tab.

### Bug D — synthesizer mints divergent f_ref numbering

The `<phase_synthesize_v2>` lead-prep step "Build canonical f_refs
manifest" was documented but had no concrete tooling to run, so leads
have been skipping it and dispatching the synthesizer without inlining
`{{canonical_f_refs_manifest}}`. The synthesizer then invents its own
per-finding numbering (e.g., `visual-cta F-77`) while correctly using
cluster-local 1-based indices inside `priority_path[].f_refs` (e.g.,
`visual-cta F-01..F-06`). The two namespaces never intersect, the
render-time filter drops everything, and Bug C surfaces.
**Fix:** `scripts/lead_prep.py build-canonical-frefs` produces both
the structured `canonical-f-refs-manifest.json` and a markdown
`canonical-f-refs-manifest.md` that the lead pastes verbatim into the
synthesizer prompt at `{{canonical_f_refs_manifest}}`. SKILL.md
`<phase_synthesize_v2>` step 3 updated to point at the new helper.

### Verification

Re-render of engagement `2026-05-02-9cd2a2ac` after Bug A data fix +
Bug B code patch (without re-acquisition or re-synthesis):

| metric | before | after |
|---|---|---|
| desktop slide distribution | s1: 26 / s2: 2 / s3: 0 | s1: 18 / s2: 6 / s3: 0 |
| mobile slide distribution | s1: 26 / s2: 2 / s3: 0 | s1: 14 / s2: 12 / s3: 2 |
| confidence variety (mobile) | 100% exact-selector | exact-selector + section-match |
| VC-77 (Newsletter) slide | mobile-section-1 | mobile-section-3 ✓ |

Bug D verification requires a full re-audit since it touches the
synthesizer dispatch — operators should re-run `/ecp:audit` after
upgrading to confirm Priority Path tab renders.

## 1.4.0 — 2026-05-02 (Visual review editor v1 + severity-keyed renderer)

Marker bump for the testing/install identity across Claude Code, Codex, and
Cursor. Bundles editor v1 (filmstrip, polygon/lasso tools, Photopea
round-trip, clipboard, multi-select, layer toggles, snap-to-baton-element,
right-click hardening) with renderer upgrades (severity-keyed colors,
polygon/freeform markers, directional callout arrows, spotlight mask,
transform-correct overlays, severity-dotted sidebar, print stylesheet) and
v2 renderer fixes (citation URL restore, `proposed_anchor` threading).
Cursor manifest bumped 0.2.7 → 0.3.0 to match recent cursor surface
updates. No schema changes since 1.3.14; install via
`/plugin marketplace update ecommerce-conversion-psychology` then
`/reload-plugins`.

## 1.3.14 — 2026-04-30 (Architectural fix B: proposed_anchor for absent findings)

### Schema

- **`schema/finding-v1.json` — new `proposed_anchor` typed-union field.**
  Discriminator on `kind` (`element` | `section` | `viewport`) with strict
  `oneOf` per-variant validation. Closed enums on `placement` (constrained
  per kind) and `viewport_trigger` (`after_primary_cta_offscreen`,
  `before_first_scroll`). Conditional rule requires `proposed_anchor`
  whenever `element.baton_index = "absent"`. Section-bound behaviors use
  `kind=section` with `placement=section-bottom-overlay` so `kind=viewport`
  stays truly page-global. The `reason` field is operator-tooltip prose
  ONLY — the renderer must NEVER parse it for placement logic.

### Renderer

- **`scripts/report/v2_markers.py` — four-strategy precedence.** Real
  `e_index` lookup → `proposed_anchor` dispatch on `kind` (NEW) →
  `section_centroid` alias-map fallback for older absent findings →
  banner. Per-kind placement helpers compute slide-relative coordinates
  from `before-element` / `after-element` / `inside-element-{top,center,
  bottom}` / `section-bottom-overlay` / `viewport-bottom-sticky`.
  Defensive viewport-mismatch fall-through prevents mobile-authored
  placements from rendering on desktop slides.

### Transport

- **`scripts/assembly/models.py` — new frozen `ProposedAnchor` dataclass**
  attached to `Finding`. Does NOT participate in identity / dedup —
  identity stays surface-based per the locked v1 scope.
- **`scripts/assembly/json_parser.py`, `scripts/report/v2_loader.py` —
  field threaded through whitelist normalizers** so it doesn't silently
  drop on the way to the renderer.

### Specialist contract

- **`contracts/specialist-prompt-v2.md` — new "Proposed anchor for absent
  findings" section** between the existing "Element references —
  precedence" rule and the "Evidence anchors — visual position rule."
  Teaches all v2 cluster specialists how to populate `proposed_anchor`
  for each `kind`, with worked examples. Per-cluster contracts in
  `contracts/specialists/` are intentionally NOT touched —
  `proposed_anchor` is global to all clusters.

### Verification

- Schema meta-validates; 7 positive/negative validation cases behave as
  designed.
- 293/293 v2 unit tests pass; 14/14 e2e render tests pass.
- Synthetic 7-finding renderer dispatch routes all four strategies to the
  correct slides with per-placement coordinates.

### Out of scope (deferred to a future pass)

- Identity / dedup logic in `scripts/assembly/pipeline.py:83` and
  `scripts/assembly/business_rules.py:478` stays surface-based.
- Existing reference fixtures (e.g. `docs/ecp/2026-04-30-1e0a1b01/`)
  pre-date `proposed_anchor` and will fail validation under the strict
  new schema. Spot-checks happen on fresh acquisitions, not by re-
  rendering historical data.

## 1.3.13 — 2026-04-23 (README + manifest accuracy: real corpus counts)

### Docs / metadata accuracy

- **README badge:** `v1.2.0` → `v1.3.13` (was stale across the entire 1.3.x patch series).
- **Corpus counts corrected to ground truth.** README now reads **945 classified findings across 72 reference files** (was `800+ / 80+`). Verified by counting `### Finding N` headings across `references/*.md`.
- **Manifest descriptions:** `plugin.json` and `marketplace.json` updated from `800+` to `900+ research-backed findings` — kept as a `+` band so they age across patch releases without re-editing.
- **`plugin.json` version:** `1.3.0` → `1.3.13` (was lagging the changelog).

No runtime changes. Documentation/metadata only.

## 1.3.12 — 2026-04-23 (Cursor URL bootstrap: default device desktop)

### Cursor URL bootstrap

- **Default `--device`:** `desktop` (1920×1080). Single-device runs no longer default to `laptop` (1440×900); pass `--device laptop` explicitly when needed.
- **`--both` / `--devices`:** now expands to **`desktop` + `mobile`** (was laptop + mobile). `ecp_run_visual_reports.py` fallbacks for missing `device` in `baton.json` align with `desktop`.

## 1.3.11 — 2026-04-23 (Cursor URL bootstrap: human-style section names + label dedupe)

### Cursor URL bootstrap

- **`scripts/cursor_bootstrap_url.py`:** one browser eval per viewport now returns both the **largest
  in-viewport h1–h3** and a **human scene** string (landmark + `elementFromPoint` walk: header, main,
  nav, section, footer). `scripts/ecp_section_hints.py` `section_label()` prefers a non-placeholder
  scene, then heading / above-the-fold / numbered fallbacks (`workflows/acquire.md`-style descriptive
  prose, not cluster slugs as labels).
- **Uniqueness:** `make_section_labels_unique()` runs **before** `enrich_baton_sections` so
  `sections[]` / `screenshots[]` labels are deduped (e.g. ` (view 2)`) and cluster keyword routing
  uses the final strings.

## 1.3.10 — 2026-04-23 (Cursor subagent roles replace Agent Teams)

### Cursor plugin

- Added `agents/*.md`: `ecp-orchestrator`, `ecp-acquisition`, `ecp-cluster-auditor` (hard cap ≤4
  `references/` files per cluster), `ecp-synthesizer`, `ecp-reviewer` — scoped handoffs to avoid
  context compaction on large corpora.
- `plugin.json` + `sync-to-cursor.ps1` include `agents/`.
- `ecp-cursor` skill updated: coordination model now describes this pipeline explicitly.

## 1.3.9 — 2026-04-23 (Cursor: visual report runner + configurator + FINDING format)

### Cursor plugin

- **`ecp_run_visual_reports.py`:** runs `run_visual_report.py` for one or all batons, validates
  `meta.json` by default, pairs device ↔ baton automatically.
- **Slash command `/ecp-report`** → `commands/ecp-report.md`.
- **`ecp_configurator.py` + bootstrap:** `acquire.md` Step 1d — when ≥2 required `<select>` and disabled
  CTA, fills first options and adds `configured_state` + `*-configured.jpg`.
- **Skills** (`quick-scan-cursor`, `audit-cursor`, `ecp-cursor`): report output must use **fenced
  `FINDING:` blocks** + **`Viewport:`** for `visual-report.html` generation.

## 1.3.8 — 2026-04-23 (Cursor slash commands for ecp-cursor)

### Cursor plugin

- Added repo-root `commands/*.md` with **slash commands** `/ecp`, `/ecp-quick-scan`, `/ecp-audit`, `/ecp-build`,
  `/ecp-compare`, `/ecp-resume`, `/ecp-bootstrap-url` (see `.cursor-plugin/README.md`).
- `.cursor-plugin/plugin.json` now declares `skills`, `rules`, and `commands` paths (same layout as other marketplace plugins).
- `scripts/sync-to-cursor.ps1` mirrors the `commands/` directory into the local install.

## 1.3.7 — 2026-04-23 (multi-device + section hints + nav timeout for Cursor URL bootstrap)

### Cursor URL bootstrap

- **`scripts/cursor_bootstrap_url.py`:** `--both` (laptop+mobile) or `--devices laptop,mobile`;
  at most one of `laptop` / `desktop` per run. Multi-device runs prefix JPEGs (`laptop-section-1.jpg`,
  `mobile-section-1.jpg`) so both batons can live in one engagement folder.
- **Navigation:** `--goto-timeout` (default 30s) aborts with `STATUS: BLOCKED` on timeout.
- **Sections:** new `scripts/ecp_section_hints.py` plus visible h1–h3-in-viewport sampling for
  `sections[].label` / `screenshots[].label` and cluster keyword routing.
- **Session** per engagement: `ecp-cursor-<engagement_id>` (stable across devices in a joint run).
- **`meta.json`:** `devices_requested` / `devices_scanned` when more than one device; confidence
  is the worst (lowest) per-device value.

## 1.3.6 — 2026-04-23 (acquire.md overlay + DOM preprocessing for Cursor URL bootstrap)

### Cursor URL bootstrap

- `scripts/cursor_bootstrap_url.py` now runs a best-effort **overlay dismissal** loop,
  **viewport-clear** verification, and **JS removal** of blocking overlays before screenshots.
  If the viewport is still not clear, capture **at most one** reference screenshot and mark
  `viewport_clear: false` / `PARTIAL` (avoids six unusable occluded shots per `workflows/acquire.md`).
- **Post-load guardrails:** cross-host redirect + password-field detection (early exit with
  `STATUS: BLOCKED`).
- **Scroll** uses `window.scrollTo({ behavior: "instant" })` with a simple scroll verification
  pass (mirrors `acquire.md` scroll guidance).
- **DOM** is written through tiered **`acquire.md` preprocessing** via new `scripts/ecp_acquire_dom.py`
  (full / `reduced` / `skeleton` + JSON-LD extraction for `structured_data`).
- **Timers:** best-effort `workflows/acquire.md` Step 1c probe via `scripts/ecp_acquire_overlays.py`
  (only written to the baton when a timer-like region is found).

## 1.3.5 — 2026-04-23 (deeper `acquire.md` baton parity for Cursor URL bootstrap)

### Cursor URL bootstrap (report-shaped baton)

- Expanded `scripts/cursor_bootstrap_url.py` to emit a more `workflows/acquire.md`-like
  `baton.json` / `baton-mobile.json` (device-dependent filenames) including:
  - 1–6 JPEG viewport screenshots (`section-*.jpg`) with hash de-dupe + retry
  - `screenshots[]` + `sections[]` metadata
  - per-scroll element extraction with DPR scaling (report pipeline coordinate model)
  - `styles` + `pre_hydration_warning` + best-effort `structured_data`
  - `dom.html` / `dom-mobile.html` (device-dependent DOM filename)
- Windows: resolves `agent-browser` via `shutil.which` so `subprocess` can launch the shim reliably.

## 1.3.2 — 2026-04-23 (Cursor URL bootstrapping)

Adds a practical URL acquisition path for Cursor workflows.

### URL engagement bootstrap (Cursor)

- Added `scripts/cursor_bootstrap_url.py` to create `docs/ecp/<id>/` artifacts:
  - `dom.html`
  - `baton.json` (best-effort element list for report mapping)
  - `meta.json`
  - `context.md`
- Wired Cursor skills to reference the bootstrap command for URL inputs.

## 1.3.3 — 2026-04-23 (Cursor install sync)

### Cursor install sync

- Added `scripts/sync-to-cursor.ps1` to mirror a full local plugin install
  (shared knowledge + report pipeline dependencies) into
  `~/.cursor/plugins/local/ecp-cursor`.
- Updated `README.md` + `.cursor-plugin/README.md` to recommend the sync script.

## 1.3.4 — 2026-04-23 (line ending helper for Cursor assets)

- Added `scripts/normalize_lf.py` to normalize text files to LF (helps reduce
  Windows CRLF warning noise during `git add` for Cursor-scoped text assets).

## 1.3.1 — 2026-04-23 (Cursor plugin parity + runtime helpers)

Adds a full Cursor-side plugin scaffold and bridges key workflow parity gaps
without modifying existing Claude/Codex runtime files.

### Cursor plugin scaffold

- Added `.cursor-plugin/plugin.json` (`ecp-cursor`)
- Added Cursor rules:
  - `.cursor/rules/ecp-output-format.mdc`
  - `.cursor/rules/ecp-ethics-guardrails.mdc`
  - `.cursor/rules/ecp-evidence-standards.mdc`
- Added Cursor mode skills:
  - `skills/ecp-cursor/SKILL.md`
  - `skills/quick-scan-cursor/SKILL.md`
  - `skills/audit-cursor/SKILL.md`
  - `skills/build-cursor/SKILL.md`
  - `skills/compare-cursor/SKILL.md`
  - `skills/resume-cursor/SKILL.md`

### Accuracy and efficiency model

- Added Lead Analyst + Accuracy Reviewer structure across Cursor skills.
- Added required fast validation pass and conditional second-pass escalation
  (only for low confidence, conflict, or high-risk recommendations).
- Added audit scoring/reconciliation guidance and compare fairness checks.

### Cursor runtime helper layer

- Added `.cursor-plugin/contracts/meta-schema.json`
- Added `.cursor-plugin/scripts/validate_meta.py`
- Added `.cursor-plugin/scripts/infer_engagement_state.py`
- Added `.cursor-plugin/scripts/run_visual_report.py`
- Wired skill docs to concrete runtime commands for:
  - state inference
  - schema validation
  - optional visual report generation from artifacts

### Documentation updates

- Added Cursor install instructions to `README.md` with copy commands.
- Added `.cursor-plugin/README.md` with runtime command sequences and mode mapping.

## 1.3.0 — 2026-04-23 (citation hygiene + legal cluster repair)

Follow-up to v1.2.0. Addresses issues found by post-merge audit
(`references-audit-findings-2026-04-22.md` + url-appendix + actionable-
missing-data appendix). Three separate fixes:

**Legal cluster (Phase 1):**
- Stripped erroneous `$54,540 / Fed Reg 2026-00535` claim from
  review cluster (scarcity-urgency, social-proof-patterns,
  review-collection, ugc-reviews-seo). Fed Reg 2026-00535 is a
  Surface Transportation Board rule, not an FTC adjustment.
  ethics-gate.md quarantines this error; Sprint 3 apply pass
  reintroduced it in sibling files. Fixed.
- Applied 9 verified FTC URL replacements from actionable-missing-data
  appendix (fake-reviews-rule, junk-fees-rule, deception policy,
  endorsement guides, Fashion Nova press release, Rytr press release,
  CAN-SPAM compliance guide, comparative advertising statement).
- ethics-gate.md registry verification date refreshed to 2026-04-23.

**Mechanical (Phase 2):**
- Wrapped paren-containing DOIs in angle-brackets for markdown safety
- Removed trailing markdown asterisks from one DOI
- Flagged example.com/yourstore.com placeholders in demo code blocks
- Resolved one SEJ slug placeholder OR flagged as unresolved

**Zero-URL finding files (Phase 3):**
- biometric-and-express-checkout.md: 8/8 findings given URLs
- checkout-optimization.md: 23/23 findings given URLs

**Source-line remap (Phase 4):**
- ~170-200 Source lines given explicit URLs across ~40 files
- Unresolvable findings flagged Bronze with Citation Status notes

**Cache refresh required post-merge.**

## 1.2.0 — 2026-04-22 (Sprint 3 research hygiene + contracts split)

Full evidence-hygiene pass across all 69 reference files. Every finding's source, URL, evidence tier, and citation status has been verified against primary sources by a two-run audit (Run A + Run B) with independent cross-reconciliation (Vera). Human-verified deferred decisions resolved by Dan on 2026-04-22.

### Research hygiene — Sprint 3

- **~202 findings updated** across 69 reference files: corrected URLs, upgraded/downgraded evidence tiers, fixed journal names, added missing DOIs, removed unverifiable numeric claims, standardized citation status notes.
- **New findings added**: charm-pricing F4 (Bizer & Schindler 2005), discount-framing F5 (Darke & Freedman 1995), discount-framing F6 (DelVecchio et al. 2007), benefit-first-descriptions F13 (schema.org Product split-tier).
- **New file**: `references/ai-media-disclosure.md` — consolidated AI-media-disclosure framework (FTC Operation AI Comply, EU AI Act Art 50, C2PA Content Credentials, disclosure best practices). Extracted from color-accuracy F13, video-integration F15, video-optimization F12.
- **Ethics-gate updates**: WCAG 2.2 AA framing added to Part 7.3 (W3C Recommendation 12 December 2024). 10-item cross-reference handoff queue appendix added for future reconciliation.
- **Evidence tier corrections**: benefit-first-descriptions F7 downgraded Silver→Bronze (return rate percentages unverifiable), pricing-psychology F14 downgraded Silver→Bronze (consulting figures misattributed/mutated through vendor blog telephone game), grid-layout F3/F4/F5/F6/F7 confirmed Silver (Baymard Premium-gated).
- **Abandoned-cart-psychology**: Baymard cart abandonment stats updated to 2026 edition (50 studies + 2025 survey N=1,026).
- **Language cleanup**: "bot-blocked" replaced with "blocks automated fetches" across all reference files.
- **All VERA-UNRESOLVED markers resolved**. One VERA-ADD-DEFERRED remains (canonical-duplicate-content F13 HTTPS preference — future content addition).
- **image-quantity-types F1 retitled**: "Five Reviews = 270% Higher Purchase Likelihood vs. Zero (REVIEWS, Not Images)" to prevent misattribution of Spiegel Research Center review study as image research.

### Folder restructure — operational contracts moved to `contracts/`

Split the 96-file `references/` folder into two purpose-scoped folders to stop operational contracts from accumulating alongside CRO research.

- **New `contracts/` folder** for operational files the skill leads read but auditors never cite in findings. 25 files moved via `git mv` (history preserved per file):
  - Lead discipline: `lead-discipline.md`, `audit-reconciliation.md`, `audit-assembly.md`, `priority-path-synthesis.md`, `conflict-resolution.md`, `verification-checklist.md`
  - Team protocol: `dispatch-contract.md`, `team-lifecycle.md`, `relay-loop-protocol.md`, `multi-planner-protocol.md`, `go-back-protocol.md`, `trace-assertion-canary.md`
  - Skill config: `flags.md`, `meta-schema.md`, `cluster-routing.md`, `cluster-migration.md`, `device-semantics.md`, `platform-detection.md`, `page-detection.md`, `url-validation.md`, `report-export.md`
  - Subagent specs: `synthesizer-subagent.md`, `humanizer-subagent.md`
  - Pipeline specs: `dom-preprocessor.md`, `progress-comparison.md`
- **`references/` now holds only CRO research** — 71 domain files that auditors cite via `↳` in findings, including `ethics-gate.md` (cited via `REFERENCE:` field in FAIL blocks), `evidence-tiers.md`, `essential-principles.md`, and 68 topic-specific research files.
- **Pointer rewrites:** 222 references updated across 40+ files — every `${CLAUDE_PLUGIN_ROOT}/references/{file}.md` path and every bare in-prose mention that implied the old folder. Verified symmetric: 0 stale `references/` pointers remain outside historical docs.
- **Scripts updated:** `scripts/sync-to-codex.ps1` adds `"contracts"` to `$sharedDirectories`. `scripts/build_claim_verification_ledger.py` needed no change (still iterates only domain files for Evidence Tier analysis). `scripts/dom_preprocess.py` comments updated.
- **Docs updated:** `ARCHITECTURE.md` tree diagram split the `references/` block into `references/` (domain) + `contracts/` (operational) with a one-line description per contract.
- **Not updated:** frozen snapshots in `docs/ecp/` (per-engagement outputs) and `docs/research-audit/run-{A,B}/` (historical research passes). Those preserve the folder layout in effect when they were generated.
- **Cache refresh required.** Plugin cache at `~/.claude/plugins/cache/ecommerce-conversion-psychology/ecp/1.1.0/` needs to be updated to match the new layout — `git fetch && git reset --hard origin/main` inside that directory after this PR merges. Without refresh, cached SKILL.md files still point to the old `references/` paths.
- **Why:** before this move, `references/` held CRO research + orchestration contracts + protocol specs in a single flat folder. The mixing made it too easy to drop a new file in the wrong place, and expanded the auditor context surface (cluster auditors would occasionally load operational files they had no use for). Clean separation aligns with the lead-vs-teammate architecture — contracts are lead-only, references are audit-library.

## 1.1.0 — 2026-04-14 (authored TITLE field, mandatory dedup, cluster rename, UI polish)

Response to iteration notes from the awdmods.com live review (Dan + Vera). Shipped in a single push; 31/31 tests passing; legacy-alias sanity checks pass so resumed v1.0.x engagements render unchanged.

### Schema — authored TITLE field on every finding

The v1.0 renderer derived a finding's left-rail title from its SECTION slug at render time, which produced walls of duplicate labels when multiple auditors flagged different issues under the same canonical slug. The awdmods desktop audit rendered `Value Proposition` seven times in the content-seo cluster and `Image Optimization` / `Page Load` repeatedly in mobile-performance. Users looking at the left rail couldn't tell the findings apart without clicking into each one, and the redundant labels eroded confidence in the pipeline.

- **New mandatory `TITLE:` field** on every FAIL and PARTIAL finding block. ≤60 chars, unique within the cluster, cannot trivially mirror its own SECTION slug. Authored by the cluster auditor (not derived). Rules live in `workflows/audit.md` Step 4d with a worked 7-row disambiguation table and a same-hero-element collapse example.
- **Reconciliation Step 0 now enforces** TITLE presence, ≤60-char length, non-trivial-section-match, and cluster-scoped uniqueness. Tailored SendMessage correction loop bounces TITLE-only failures back to the auditor without making them re-do format or voice.
- **Render precedence flipped.** `scripts/report/templates/components._finding_title` is now documented as the legacy fallback; the live path uses the finding's own `TITLE` field via the existing `f.get("title") or _finding_title(f)` call site. Legacy v1.0 engagements without TITLE render unchanged (slug fallback).
- **Parser/model/writer alignment.** `scripts/assembly/parser.py` and `scripts/report/parser.py` extract `TITLE`. `scripts/assembly/models.Finding` carries it. `scripts/assembly/writer._reconstruct_block` emits it in reassembled FINDING blocks.

### Dedup — Layer 3 same-SECTION collapse is MANDATORY

`references/audit-reconciliation.md` Layer 3 was previously a SHOULD, which meant leads sometimes ran it and sometimes didn't. Inconsistent dedup is the upstream cause of the duplicate-title rendering. Layer 3 is now a gate with explicit merge rules:

- **Trigger:** 2+ findings in the same cluster sharing BOTH `SECTION` slug AND an overlapping `ELEMENT` (same selector, or parent/child, or same descriptive location).
- **Merge rules:** highest PRIORITY wins, tie-broken by evidence tier (Gold > Silver > Bronze), then by longer OBSERVATION. TITLE rewritten to cover combined scope. RECOMMENDATIONs merged as sub-bullets. Primary citation preserved; others moved to `**Also referenced:**`. SYNTHESIS_HINTs unioned.
- **Worked example** in the file shows three hero-image findings collapsing to one `Hero Image Loading Issues` finding with three remediation sub-bullets.
- **Different-ELEMENT findings are NOT merged** — they stay separate but must have distinct TITLEs.

### Cluster rename — `mobile-performance` → `performance-ux`

Diagnosed while reviewing why `mobile-performance` kept appearing on desktop audits: four of the cluster's five reference files (`cognitive-load-management`, `page-performance-psychology`, `core-web-vitals`, `media-performance-optimization`) are device-agnostic — only `mobile-conversion.md` is mobile-specific. The old name led desktop audit users to expect the cluster to be skipped on desktop; it was not, and it should not be. Desktop page performance, cognitive load, and media weight all matter.

- **Canonical slug:** `performance-ux`. **Client-facing label:** "Performance & UX". **Chip:** `PU`. Same purple color retained.
- **Legacy slug is a resume alias.** `mobile-performance` stays in `CLUSTER_LABELS`, `CLUSTER_COLORS`, `CLUSTER_TAB_ORDER`, and the chip palette — all mapping to `performance-ux`-equivalent display. Resumed v1.0.x engagements with `clusters_used: ["mobile-performance"]` render identically.
- **New dispatches emit the new slug.** `scripts/dom_preprocess.CLUSTERS_DEFAULT`, cluster-routing tables, `--focus mobile` alias, page-type defaults, and the multi-planner file-naming convention all updated.
- **`references/cluster-migration.md`** now carries two translation tables (v4.x → v5.0 and v5.0/v1.0 → v1.1) and an updated load-time translation log format. Collapses the two-step migration for v4.x engagements into a single resolved slug.
- **`references/cluster-routing.md`** has a v1.1 callout explaining the cluster's actual scope and why the override rule ("mobile in device set → include performance-ux") still applies — `mobile-conversion.md` still lives in this cluster for mobile-specific guidance.

### UI polish

Drawn from Vera's review of the live v1.0.1 report:

- **Header severity chips.** The header strip now renders a per-severity chip group (e.g. `13 HIGH · 14 MEDIUM · 4 LOW`) next to the total-findings + cluster-count chips. Zero-count buckets are omitted. Chips carry severity-colored borders and value emphasis.
- **Up/Down arrow finding navigation.** Arrow keys move selection through every `data-fid`-bearing row in the visible panel (finding-row or priority-ref-row), wrapping at both ends. Collapsed cluster cards auto-expand when selection enters them (reuses the existing `selectFinding` path). Input/textarea focus still short-circuits.
- **Editable Export Brief textarea.** The modal's `readonly` is gone; focus ring pairs with an inline hint that tweaks only affect the clipboard copy, not the source findings.
- **"Select HIGH" toggle button.** Sits next to "Select all visible" in the bottom bar. Adds every CRITICAL + HIGH finding across the whole audit to the brief (not scoped to the visible tab). Toggles off when all are already in the brief. Hotkey-friendly — bypasses the need to drill into each cluster card.
- **Subtler device frame.** The desktop monitor-stand chrome is gone. Every device now renders as a thin-border container with a small uppercase corner label (`DESKTOP` / `MOBILE` / `LAPTOP`). `.device-base`, `.device-stand`, and `.device-stand-base` are collapsed to `display: none` so the existing DOM contract stays stable for anyone styling around them.
- **Cluster chip cleanup.** `MP` chip (which tracked back to the pre-rename "Mobile Performance" slug) is now `PU`.

### Regression coverage

`tests/test_v1.py` unchanged (31/31 pass). Legacy-alias sanity checks validate that `mobile-performance` resolves to the same label/color/chip/tab-order entries as `performance-ux`. Smoke checks cover TITLE extraction in both parsers, the new header severity chip HTML, the editable-textarea markup, and the device-frame CSS.

### File changes

27 files modified; 414 insertions, 215 deletions. Commit `9f86df8` on `main`.

---

## 1.0.1 — 2026-04-14 (three-panel report redesign + postmortem fixes from the first v1.0 production run)

First v1.0 production run went live against `awdmods.com` (74 desktop / 70 mobile findings, dual-device, all 10 clusters). The audit.md pipeline worked as designed; the **visual report layer** surfaced a long tail of UX issues, dead plumbing, and a silent JS-truncation bug that only manifested on specific finding content. v1.0.1 is the shippability-level response.

### Report redesign — scroll-document → three-panel app shell

The v5/v6 single-column report couldn't hold 70+ findings gracefully — long vertical scrolls, the single-stream "All" tab numbered F-01..F-74 which felt unordered, and head-scoped / site-wide-absence findings had no visual home. Replaced with a three-panel app shell that treats the audit as a working tool, not a document.

- **Left rail:** tab switcher (**Priority Path** default, **By Cluster**, **Ethics**) over a scrollable content area. Cluster cards are collapsible with `N findings` + worst-severity chip; ethics tab gets a red badge with BLOCK / ADJACENT count.
- **Center stage:** empty by default with a 4-step onboarding tile grid. On selection, swaps to the screenshot at real viewport aspect + a single severity-colored hotspot zone + a dark-mode animated callout card anchored beside the screenshot with a CSS leader arrow pointing at the hotspot's vertical center.
- **Right rail:** selected finding's full detail — element, observation, recommendation, source with tier badge + clickable URL, ethics banner, Skip / Add-to-brief actions.
- **Bottom bar:** live brief counter + `Select all visible` + `Export Brief`.
- **Export modal:** two formats — bulleted list grouped by cluster, and verbatim markdown mirror of the audit.md FINDING code fences. Clipboard copy with fallback. Brief selections persist per-engagement in `localStorage`.
- **Cluster-scoped finding IDs:** the old single-stream F-01..F-74 numbering is gone. Every row and detail now displays `VC-01`, `TC-03`, `PR-05`-style labels where the 2-letter prefix is the cluster's chip abbreviation. Each cluster numbers internally from 1; collisions are impossible across the 10-cluster set.
- **Hotspot zones:** real rectangles drawn from `getBoundingClientRect()` coordinates captured during acquisition, outlined in severity color. Head-scoped / site-wide-absence findings fall back to a corner-stacked point marker. Fade-in + gentle pulse on select.
- **Animated dark callout:** panel-raised background, severity pill, short title, first 160 chars of recommendation in mint-green. Positioned as a flex sibling of the screenshot (never overlapping), with a CSS leader triangle the JS aligns to the hotspot's vertical center. Flips to flex-column with an up-pointing arrow on viewports <960px.
- **Ethics pill in header:** always visible, state-colored. `ETHICS: PASS` (green ✓), `ETHICS: ADVISORY (N)` (amber ⚠), `ETHICS: BLOCK` (red ✗ with outer glow). Clicking it jumps to the Ethics tab.

### Critical — `</script>` inside JSON payloads was silently truncating the desktop report JS runtime

One of the mobile-performance auditors cited the Speculation Rules API and quoted a literal `<script type="speculationrules">{...}</script>` fragment in its OBSERVATION. That fragment ended up JSON-encoded inside `FINDINGS` / `EXPORT_MARKDOWN` payloads embedded in an inline `<script>` block. Browsers treat `<script>` as a raw-text element — once inside, `</script>` closes the tag regardless of whether it's sitting inside a JSON string. The HTML parser closed the runtime early, `setSlide(0)` never ran, `addEventListener('click', …)` never attached, every delegated handler was dead. Mobile didn't cite Speculation Rules, so mobile worked and desktop didn't.

- **Fix:** `scripts/report/html_builder._build_html_fragments` now runs every JSON payload through a `_safe_json` wrapper that replaces `</` with `<\/` (a no-op in JS — backslash before `/` is a superfluous escape) and `<!--` with `<\!--`. Applied to `findings_json`, `export_markdown_json`, `slide_sources_json`. Regression test added.

### High — `Unknown URL` / schema drift in meta.json reader

Live engagement writers emit `engagement_id` + top-level `url`; `_load_metadata` only looked at the old `id` + `page.url` schema. Headers rendered `Unknown URL` even when the URL was sitting right there in meta.json.

- **Fix:** `_load_metadata` falls through both schemas: `meta.page.url` → `meta.url` → `meta.url_normalized`; `meta.id` → `meta.engagement_id` → engagement directory name; `meta.page.type` → `meta.page_type`. Regression test covers all four fallback paths.

### High — Cluster chip was showing plurality, not worst severity

A cluster with 3 HIGH + 4 MEDIUM rendered `4 MEDIUM`, hiding the HIGHs. Old logic: `max(sev_counts, key=(count, -priority))`.

- **Fix:** Iterate CRITICAL → HIGH → MEDIUM → LOW, stop at the first non-zero bucket. The `visual-cta` / `trust-credibility` / `pricing` chips now surface their HIGH counts first. Regression test pins the worst-wins behavior.

### Cleanup — dead renderer plumbing removed (−258 lines in `templates/components.py`)

- Removed 4 legacy scroll-document builders (`build_tab_bar_html`, `build_priority_path_cards_html`, `build_finding_cards_html`, `build_pass_cards_html`) previously kept as "backwards compat" — nothing imported them.
- Removed the `pass_findings` + `build_pass_cards_html` path (the app shell doesn't render a "What's Working Well" section).
- Removed the unused `cluster_finding_map` parameter that was built and passed through with no consumer.
- Removed the `thumb_html` builder that duplicated ~1MB of inline base64 thumbnail data into every rendered report, only to be dropped by the new shell.
- Dropped 13 unused imports across `html_builder.py` and `components.py`.

### Cleanup — dead CLI flag removed

`scripts/assemble-audit.py --apply-dedup` was advertised in `--help` but always exited `Not yet implemented`. Removed. Regression test pins the `--help` output so the flag can't sneak back in.

### DOM preprocessor promoted to first-class script

`references/dom-preprocessor.md` documented the algorithm; previously every lead had to reimplement it inline per engagement. `scripts/dom_preprocess.py` is now a stand-alone CLI that reads `dom.html` + `baton.json` and writes per-cluster context slices with empty-slice pruning and keyword-based fallback routing.

### Default marker fallback for unmatched findings

26 findings per audit used to be dropped when the auto-matcher couldn't map their element to baton coordinates (head-scoped meta/schema/OG/canonical findings, site-wide absence findings like "no loyalty program"). `scripts/report/markers.py` now classifies unmatched findings as **head** or **absence** and routes them to a top-right or bottom-right stack on slide 0 / last slide respectively. Closes the 26/148 drop on the awdmods run (desktop 34→54 markers mapped, mobile 42→61).

### Layout responsive breakpoints

Raised from 1200px to 1400px. Narrow-desktop widths (1000–1200px) that used to get cramped 7fr/5fr proportions now collapse to a clean single column with a centered evidence canvas. Callout width + wrapper gap scale with 1440px / 1280px midpoint breakpoints so side-by-side doesn't get tight at mid widths.

### Device intake prompt reordered

`/ecp:audit` device prompt: `1. Desktop (default) · 2. Mobile · 3. Laptop · 4. Pick 2 (Desktop + Mobile, or Laptop + Mobile)`. The old a/b/c/d lettered format with Laptop as `b` and Mobile+Laptop as `c` was confusing.

### Regression tests

`tests/test_v1.py` now covers the four postmortem fixes end to end: `</script>` JSON-in-HTML escape, meta.json schema fallback (4 cases), cluster severity worst-wins (3 cases), dead `--apply-dedup` flag removal. **31/31 tests pass.**

### Engagement scratchpad cleanup

Deleted `docs/ecp/2026-04-14-7bee7af0/_fix_format.py`, `_fix_format2.py`, `_preprocess.py` — ad-hoc one-off scripts from the awdmods run. Canonical replacement is `scripts/dom_preprocess.py`.

### ARCHITECTURE.md refreshed

Retired the "self-contained 3,300-line Python script" description of `scripts/generate-report.py`. The `Render pipeline` section now accurately documents the v1.0 `scripts/report/*` package layout (html_builder orchestration, templates subpackage, 7-phase pipeline) + the v1.0.1 invariants (CSP-safe, safe JSON embedding, cluster chip worst-wins, Priority Path default, fallback markers, zero external deps at render time). Also updated the directory-listing reference to `generate-report.py` and the citations paragraph to point at `scripts/report/citations.py` with the `is_safe_citation_url` allowlist.

### `FinalizedFindings` wired into production

`scripts/assembly/pipeline.FinalizedFindings` was an immutable frozen-dataclass abstraction defined for v1.0 but only ever consumed by tests — production code called the underlying `assign_display_indices` directly and built its own valid-refs set inline. `scripts/assemble-audit.py` now uses `FinalizedFindings.build()` + `.valid_refs()` directly, so the writer and the synthesizer validator see the same frozen post-dedup, display-index-assigned container. The immutability guarantee (MappingProxyType-wrapped cluster finding map) now has a real production consumer.

### Deferred (next cycle)

- **Codex packaging consolidation.** Three sources of truth (`SKILL.md`, `ecp-codex/SKILL.md`, `.codex-plugin/plugin.json`) still exist. Naming drift between them is the biggest remaining architectural inconsistency.
- **`audit-trace.log` enforcement.** The canary is a procedural/manual mechanism today — no Python in `scripts/` writes or validates the counters. Promoting it to runtime-enforced is a v1.1 item.

---

## 1.0.0 — 2026-04-14 (v1.0 shippability — Codex-audit CRITICAL fixes, WooCommerce, evidence anchoring, voice humanizer)

First tagged release. Resets the version line to 1.0.0 after the 5.x development series. Aligns `.codex-plugin/plugin.json` with `.claude-plugin/plugin.json` — prior versions diverged (5.0.2 vs 5.0.1), producing the wrong version in rendered report headers when the renderer loaded the Codex manifest.

### Ethics output consolidation (C3 fix)

The shipped runtime could simultaneously claim "VIOLATIONS FOUND" and "0 BLOCK findings detected" in the same `audit.md`. Root cause: `_detect_ethics_status` inferred BLOCK from prose `FINDING: FAIL` inside the `## Ethics Gate` section even when no structured `ETHICS_STATE:` was set; the summary read from the structured findings list, which could be empty. Two sources of truth for the same output line.

- **Single source of truth.** `writer._ethics_gate_header` and `_ethics_gate_summary` both now derive from `result.ethics_findings`. They physically cannot disagree — the header's state and the summary's count read from the same list in the same function call. Regression-tested in `tests/test_v1.py`.
- **Prose-inference fallback removed.** `parser._detect_ethics_status` recognises only structured `ETHICS_STATE: BLOCK` or `ETHICS_STATE: ADJACENT` markers. Anything else returns `CLEAR`. Auditors that intend to flag an ethics concern MUST emit a structured FINDING block with `ETHICS_STATE` and `SOURCE_URL`.
- **One-way migration note:** cluster files produced by v5.0.x auditors that relied on prose-only ethics markers now register as ethics-silent. Archive old engagements before upgrading, or re-run their auditors. The practical impact is narrow (most v5.0.x auditors already emit structured fields when they flag an ethics concern), and the alternative (raising on missing marker) would break `/ecp:audit` replay on every legacy engagement — a non-starter for local test loops.
- **SOURCE_URL preserved through rendering.** `report/parser.parse_findings` now extracts `SOURCE_URL` and `ETHICS_STATE` fields; `html_builder._resolve_citations` keeps an existing `source_url` intact rather than overwriting from the weaker reference-file lookup. Ethics findings render with a clickable primary-source URL end-to-end.

### Priority Path synthesis automation (C1 fix) + F-N index consistency (C2 fix)

Before v1.0, `audit.md` shipped with a literal `<!-- Lead: use priority-path-candidates.json to write action stories here -->` HTML comment because the synthesis step depended on a manual "lead" action the executable pipeline didn't enforce. The headline Priority Path feature rendered as empty-state whenever the lead forgot. Separately, `scoring._finding_ref` emitted references from pre-dedup `local_index` while the writer re-sorted findings by priority — Priority Path links pointed at the wrong finding cards.

- **`scripts/assembly/pipeline.py` (NEW):** `PIPELINE_STAGES` tuple plus `_assert_stage(name, expected_index)` checks enforce pipeline ordering — a reviewer greps for `_assert_stage` to verify call order matches the canonical sequence rather than tracing call sites.
- **`assign_display_indices`:** tags every finding with its 1-based position within its cluster in the final display order (`priority_rank`, then `local_index`). Scoring now emits `{cluster} F-{display_index:02d}` refs that match what the writer renders. `FinalizedFindings` frozen dataclass wraps findings and `cluster_finding_map` in `MappingProxyType` so neither the writer nor the synthesizer can mutate them after assembly.
- **Synthesizer subagent + Python validator.** The lead dispatches a synthesizer subagent per `references/synthesizer-subagent.md` after dedup + F-N assignment. The subagent returns a fenced JSON block with 3–5 stories. `scripts/assembly/synthesizer_parser.py` parses the response and validates every story's `f_refs` against the `FinalizedFindings.valid_refs()` allowlist. Hallucinated F-Ns, wrong-cluster refs, malformed JSON, or story count out of range all render a visible `> **ERROR:**` block in audit.md rather than a silent placeholder.
- **New CLI:** `python scripts/assemble-audit.py --priority-path PATH` loads the subagent response file, parses + validates, passes stories to the writer.
- **Atomic audit.md write.** Writer now uses `audit.md.tmp` + `os.fsync` + `os.replace` on the same volume. Shuts the Windows-junction edge case via a same-volume assertion with `shutil.move` fallback. No partially-written `audit.md` regardless of whether reconciliation and synthesizer race.

### Evidence anchoring + page-specificity (WS#2)

The #1 failure mode that made reports feel generic: findings read as CRO best-practice advice that could be pasted into any store's audit. Voice check caught jargon; nothing caught page-agnostic reasoning.

- **Dispatch contract evidence requirement.** `references/dispatch-contract.md` auditor prompt gains an explicit Evidence requirement section — every finding MUST cite a DOM selector matching the acquired page, a screenshot coordinate, or a ≥3-word verbatim quote. Anything else will be rejected.
- **Forbidden framings.** Verbatim blocklist: "consider adding", "best practice suggests", "typical stores benefit from", "industry standard is", "users often expect", "research shows that". Two worked examples contrast acceptable (page-anchored) vs unacceptable (generic) finding shapes.
- **Reconciliation Step 0c (NEW).** Evidence-anchor gate between the voice check and dedup. Same two-attempt `SendMessage` correction loop as format + voice checks. Third failure drops the finding silently — a cluster with zero survivors renders as empty. Ethics findings and PASS findings are exempt.
- **Evidence tier rule tightened.** `references/evidence-tiers.md` now states page-specificity is a precondition for Gold. A finding with a Baymard/NNGroup citation but no concrete page anchor is downgraded to Bronze.

### Voice humanizer (WS#3)

Adds a transform pass after the 0-series validator gates that rewrites OBSERVATION and RECOMMENDATION fields into senior-strategist voice without changing the specific claims.

- **Ethics routing via orchestration code, not prompt.** The lead filters `ethics_state in ("BLOCK", "ADJACENT")` findings out of the humanizer's input batch before the Task dispatch is constructed — plus a belt-and-suspenders filter that also excludes findings whose citation points at `ethics-gate.md` Source Registry. The humanizer subagent never sees legal claims; it cannot soften them regardless of temperature or prompting.
- **`references/humanizer-subagent.md` (NEW):** prompt template with invariants (preserve numeric claims, proper nouns, quoted strings, causal direction, severity calibration) and a worked example showing DOM-jargon rewritten into plain voice with hex values and button labels copied verbatim.
- **Python-side validation.** Length-bound check (reject rewrites < 0.7× or > 1.5× input length — single reliable drift signal). Malformed response keeps originals. No retry loop; voice polish is a nice-to-have and never trades a validated finding for a failed rewrite.
- **Per-cluster batching.** One Task dispatch per cluster, not per finding. A full dual-device audit runs ~20 humanizer calls rather than 200–500.

### HTML report hardening (WS#4)

- **Citation URL scheme + host allowlist.** `scripts/report/citations.is_safe_citation_url` validates every URL before it reaches a rendered `<a href>`. Scheme restricted to `http`/`https`. Host must not be loopback / private (RFC1918) / link-local / reserved / multicast / IPv6-ULA / `localhost`. Rejects `javascript:`, `data:`, `file:`, `ftp:`, `http://169.254.169.254/` (cloud metadata), control chars, and URLs over 2048 bytes. `html_builder._resolve_citations` validates both the finding's own `SOURCE_URL:` field and any sources-lookup fallback. Unsafe URLs render as `(source unavailable)`.
- **Source Registry prompt-injection mitigation.** `references/ethics-gate.md` Source Registry wrapped in `<source_registry>...</source_registry>` XML tags with a framing preamble clarifying that link text is data, not instruction. The registry is inlined (~25KB) into every auditor's prompt preamble, so attacker-controlled link text from a malicious PR is a legitimate indirect-prompt-injection surface.
- **CODEOWNERS + CI lint.** `.github/CODEOWNERS` requires review on `references/ethics-gate.md`. `.github/workflows/ethics-registry-lint.yml` fails PRs whose Source Registry link text contains imperative verbs (`ignore`, `disregard`, `override`, `you must`, `new instructions`) or unbalanced brackets.

### Disambiguation — CA SB-478 shipping costs

`references/ethics-gate.md` §3.1 (Drip Pricing / Hidden Fees) now includes a `#### Shipping-costs distinction` block with FIRES / DOES NOT FIRE / WHY triplet. Shipping calculated at checkout on a product page is NOT a SB-478 or 16 CFR 464 violation. The prior-memory false CRITICAL on this category was an incorrect reading of the regulation scope.

### WooCommerce platform support (WS#7)

- **`platforms/woocommerce.md` (NEW):** 246 lines. Structured like `platforms/opencart.md`. Covers WC 9.x on WP 6.5+ as the version floor (HPOS by default, Cart + Checkout Blocks by default). Emphasises the classic-hooks-vs-render_block split since that's the #1 builder footgun on block-enabled stores — classic action hooks silently no-op on block checkout.
- **Detection heuristics.** Requires ≥2 signals with at least one commerce-specific (`wc-block-*` class, `woocommerce` body class, `wc_cart_fragments` script, `generator` meta, `/cart` or `/checkout` URL path). Bare `wp-content/` alone classifies as `generic` — a WordPress blog without commerce won't false-positive into the WooCommerce builder path.
- **Flag enum + descriptions updated.** `references/flags.md` `--platform` now accepts `woocommerce`. Both plugin.json descriptions list WooCommerce alongside Shopify, Next.js, OpenCart.

### Regression test suite (`tests/test_v1.py`)

23 unittest cases covering the silent-failure surfaces introduced or modified by v1.0. No pytest dependency — runs with `python -m unittest tests.test_v1`. Coverage:

- Ethics header/summary count consistency (5 cases).
- F-N post-dedup consistency via `assign_display_indices` + `_finding_ref` (3 cases).
- Citation URL resolution (3 cases).
- Synthesizer validator — hallucinated refs, wrong-cluster refs, count bounds, malformed JSON (8 cases).
- URL allowlist fuzz — 29 parametrized cases covering JS/data/file/ftp schemes, every private-IP range, oversized + control-char URLs (2 cases, 29 assertions).
- Pipeline stage ordering pinned so any future reorder surfaces in the diff (2 cases).

### Deferred (intentionally)

- **UI/UX redesign** — separate branch, tested on a local server, post-tag. Function-before-ego.
- **Codex packaging consolidation** — the Codex `.codex-plugin/` + `ecp-codex/` + root `SKILL.md` split (Codex audit M2/N1/N2/N3) is a separate Codex-focused release cycle. v1.0 only fixes the version-skew visible in rendered report headers.
- **Explicit Anthropic SDK caching** — the Claude Code `Task` tool has `enablePromptCaching: false` hardcoded on subagents ([anthropics/claude-code#29966](https://github.com/anthropics/claude-code/issues/29966)). Preamble-first prompt restructuring produces zero cache benefit until that ships. All LLM calls in v1.0 (auditor dispatch, humanizer, synthesizer) use the same subagent auth path. No new env var; no new SDK dependency.
- **Automated screenshot marker test harness** (v1.0.1). v1.0 screenshot verification is manual against the validation audit.

### QA source

To be filled in after the validation audit runs. Validation storefront: WooCommerce official demo (operator doesn't have a live WC store today; see `docs/plans/2026-04-14-feat-ecp-v1-shippability-plan.md` §Five-point validation gate for the fallback policy).

---

## 5.0.2 — 2026-04-13 (SlingMods NRG wing audit + assembly script + ethics gate overhaul)

### Ethics gate overhaul

The phantom social proof rule falsely flagged empty star outlines with "(0 reviews)" as a CRITICAL FTC violation. This exposed three deeper architectural problems: no source URLs on legal citations, no verification step before accusing users of breaking laws, and a binary BLOCK/CLEAR output model that forced auditors to choose between "you're violating the law" and "nothing to see here."

- **Three-state ethics output model:** BLOCK (CRITICAL, actually illegal) → ADJACENT (MEDIUM, one change away from a violation, strongly recommended) → CLEAR. ADJACENT lets auditors flag real risks without making false accusations. Example: empty star outlines + "(0 reviews)" = ADJACENT (truthful now, but removing the count text would cross the line).
- **Source registry:** Canonical URLs for all 28 cited regulations (11 federal, 4 state, 4 EU, 2 Google). Every BLOCK and ADJACENT finding must include a `SOURCE_URL:` line so the user can click through and read the actual law. An ethics finding without a verifiable source URL is an unsubstantiated legal claim and must not be presented as fact.
- **Applicability self-check:** 3 mandatory questions before CRITICAL: (1) does this regulation prohibit what I'm seeing? (2) would the penalty be enforceable here? (3) can I cite the specific clause? If any answer is "no" or "unsure" → ADJACENT, not BLOCK.
- **Phantom social proof fix:** Filled stars with no reviews = BLOCK. Hollow/empty star outlines with "(0 reviews)" = ADJACENT (truthful empty state). FTC Fake Reviews Rule targets fabricated reviews, not empty UI widgets.
- **Reconciliation rule rewrite:** Lead must verify the regulation applies to the specific scenario before preserving CRITICAL. A correct regulation name with an incorrect application is still a false positive and must be downgraded.

### Assembly script — `scripts/assemble-audit.py`

The lead previously reconciled cluster files "in context" by reading 100+ findings across 11 files (229KB) and manually assembling audit.md. This didn't work — the SlingMods run produced 110 raw findings and duplicates survived into the final report.

- **`scripts/assembly/` package:** 5 modules — models.py (dataclasses), parser.py (cluster file parsing), dedup.py (3-layer dedup engine), scoring.py (Priority Path candidate scoring), writer.py (audit.md + sidecar output).
- **3-layer dedup:** Layer 1 exact match (same SECTION + same ELEMENT → auto-merge), Layer 2 SYNTHESIS_HINT merge (same slug + same element → auto-merge), Layer 3 fuzzy candidates (same SECTION but different ELEMENT → sidecar for human review).
- **Ethics-aware dedup:** BLOCK findings never merged. ADJACENT findings deduped normally but tags + SOURCE_URL preserved through merge.
- **Sidecar outputs:** `dedup-review-{device}.json` (fuzzy candidates for optional review), `priority-path-candidates-{device}.json` (scored groups for lead's Priority Path writing), `finding-groups-{device}.json` (section groupings for future visual report tabbed cards).
- **CLI:** `python scripts/assemble-audit.py --engagement docs/ecp/{id} --device mobile`. Flags: `--dry-run`, `--no-sidecar`, `--apply-dedup` (v2).
- **Test results:** SlingMods engagement — mobile 59→56 (3 auto-merged), desktop 49→43 (6 auto-merged).

### Acquirer improvements

- **Viewport-clear verification:** After overlay dismissal, a mandatory JS check confirms <10% of viewport is still covered before proceeding to screenshots. If still occluded, tries JS removal, then falls back to PARTIAL status with 1 diagnostic screenshot instead of 6 useless ones. Prevents the SlingMods bug where Omnisend popup covered all 6 mobile screenshots.
- **Expanded popup selector list:** Added Omnisend, Klaviyo, Mailchimp, Privy, Justuno, OptinMonster by class and ID. The original list only caught generic selectors.
- **Explicit overlay chain callout:** "Do NOT stop after dismissing one overlay" with named common chains (Termly cookie → Omnisend newsletter).

### Infrastructure

- **Plugin cache sync hook:** `.git/hooks/post-commit` auto-syncs `references/`, `workflows/`, `skills/`, `scripts/`, `platforms/`, `agents/`, `citations/` to the Claude Code plugin cache after every commit touching those directories. Also ships `scripts/sync-plugin-cache.sh` for manual sync.
- **Audit skill updated:** `<finding_reconciliation>` now references `assemble-audit.py` for mechanical dedup instead of manual in-context reconciliation.

### QA source
All changes from engagement `2026-04-13-6504bd67` (slingmods.com NRG wing product page, 6 clusters × 2 devices, comprehensive scope).

---

## 5.0.1 — 2026-04-10 (QA fixes from awdmods.com audit)

### Bug fixes
- **Homepage cluster routing** — comprehensive defaults expanded from 4 to 6 clusters (adds pricing, category-navigation); standard from 3 to 4 (adds content-seo). The old 3→4 gap made scope selection meaningless.
- **Ethics gate §5.3** — added materiality distinction between AI-generated product imagery (CRITICAL) and decorative/atmospheric imagery (LOW/informational). FTC Operation AI Comply targeted deceptive claims, not decorative backgrounds.
- **Ethics gate §1.2** — added scope clarification: CA SB-478 explicitly excludes shipping costs; FTC Junk Fees Rule covers ticketing/lodging only. Shipping on product cards is UX best practice, not legal requirement. Added auditor guidance to check for existing free-shipping banners.
- **Reconciliation dedup** — expanded from exact (SECTION, ELEMENT) matching to 3-layer dedup: Layer 1 exact match, Layer 2 SYNTHESIS_HINT merge (same-issue findings across clusters), Layer 3 same-cluster SECTION collapse.
- **Contested severity** — when auditors disagree by 2+ severity levels, lead now reviews reasoning instead of auto-promoting to max. Incorrect regulation citations can be downgraded.
- **Voice check blocklist** — added pattern 6 (internal pipeline terms: baton, dispatch, coordinator, teammate) and pattern 7 (soft jargon: proximate, price evaluation, render-blocking, viewport without context).
- **Auditor voice guide** — added rule 5: never reference internal pipeline artifacts in client-facing findings.
- **DOM preprocessor** — header, footer, and announcement bar sections now included in every cluster's context file regardless of baton cluster tagging. Fixes false findings from auditors who can't see page-wide info.

### QA source
All fixes from engagement `2026-04-10-6e67afdc` (awdmods.com homepage, 6 clusters × 2 devices). Full findings documented in `docs/audit-qa-findings-2026-04-10.md`.

---

## 5.0.0 — 2026-04-06 (Phase 4 update 2026-04-09)

### Round 16 — Codebase optimization pass: contract alignment, dead code cleanup, structural refactors (2026-04-09)

Executed the full 4-wave optimization plan from `docs/ecp-optimization-plan-2026-04-09.md`. All 13 findings from the codebase audit addressed. No user-facing behavior changes in Waves 1-2; product-decision items in Wave 3 approved before implementation.

**Wave 1 — Safe alignment and cleanup:**
- **Dead artifact cleanup:** Removed deleted `workflows/visual-report.md` from ARCHITECTURE.md file tree, fixed `reconcile.md` description ("Deadlock arbitration workflow"), corrected `meta.json.template` description (reference example, not copied at runtime), removed `report.html` from root SKILL.md artifact list, cleaned stale `templates/meta.json.template` mentions from resume skill and cluster-migration reference.
- **Build multi-planner reconciliation aligned:** `references/team-lifecycle.md` now matches `skills/build/SKILL.md` and `workflows/reconcile.md` — peer negotiation is the default, reconciler is deadlock-only.
- **Citation path fixed:** `citations/sources.md` self-reference corrected from `docs/citations.md`.
- **Dead code removed:** Unused `SVG_CHART` constant deleted from `scripts/generate-report.py` (verified all other SVG constants are used).
- **Orphan file archived:** `agent-teams-url-resolution.md` moved to `docs/history/`.

**Wave 2 — Internal contract repairs:**
- **DOM sequencing normalized:** `skills/audit/SKILL.md` `<page_type_detection>` no longer references DOM signals before acquisition — URL-pattern heuristics run pre-acquisition, DOM refinement explicitly post-acquisition. `skills/quick-scan/SKILL.md` `<platform_detection>` restructured into Stage 1 (pre-acquisition) / Stage 2 (post-acquisition).
- **Trace canary aligned:** Audit skill self-check assertion #2 now uses `expected_auditor_count` (dynamic, set at dispatch time after scope + empty-slice pruning) instead of static `C × D`. Task creation formula unchanged (tasks are created pre-pruning). Team lifecycle section updated with pruning note.

**Wave 3 — Product-decision items (approved):**
- **Scope prompt sanctioned:** `references/lead-discipline.md` updated from 3 to 4 allowed pre-flight prompts — audit scope selection (focused/standard/comprehensive/custom) is now the 4th, explicitly distinguished from the forbidden open-ended "What clusters do you want?" Updated all cross-references from "three" to "four."
- **Quick-scan network consent added:** `skills/quick-scan/SKILL.md` `<url_acquisition>` now includes the mandatory "About to fetch {domain} — proceed?" confirmation, aligning with `references/flags.md` and `references/lead-discipline.md`.
- **Degraded-mode behavior documented:** `ARCHITECTURE.md` no longer falsely claims "no degraded-mode assembly." Updated to describe the actual behavior: reports still generate with hotspot overlays even when optional image-conversion tools are missing.
- **Metadata numbers normalized:** marketplace.json (540+ → 800+), plugin.json (846 → 800+), README (846/88 → 800+/80+). Removed brittle line-count claim from README.

**Wave 4 — Structural refactors:**
- **`scripts/generate-report.py` decomposed:** The 2,079-line `generate_report()` function split into 9 private helpers (`_load_inputs`, `_resolve_citations`, `_build_marker_mappings`, `_process_screenshots`, `_compute_metrics`, `_check_ethics`, `_load_metadata`, `_build_html_fragments`, `_write_output`) plus `_assemble_html(ctx)` wrapping the HTML template. `generate_report()` is now a ~72-line orchestrator. Zero behavioral change — pure structural refactor. Verified with `--help` and `ast.parse`.
- **`skills/audit/SKILL.md` thinned (1,306 → ~800 lines, −39%):** Extracted 6 new canonical reference files: `references/audit-assembly.md` (audit.md template format), `references/progress-comparison.md` (FIXED/REGRESSED/NEW tracking), `references/dom-preprocessor.md` (per-cluster DOM slicing), `references/report-export.md` (visual report generation procedure), `references/go-back-protocol.md` (phase revert protocol), `references/page-detection.md` (page type + configurator pattern detection). Spawn templates moved to `workflows/plan.md`, `workflows/review.md`, `workflows/build.md`. `skills/build/SKILL.md` updated to point to new references instead of "Same as /ecp:audit."

### Round 15 — Scope selector + DOM preprocessor for token cost reduction (2026-04-09, commit 31323e0)

Live-tested with a dual-device (mobile + desktop) 6-cluster audit of slingmods.com. The audit surfaced ~220K+ token cost with 12 parallel auditors each independently reading the full DOM. Two architectural changes address this:

- **Scope selector replaces silent auto-dispatch.** Interactive a/b/c/d prompt at audit start: focused (1 cluster), standard (3-4 clusters, new default), all clusters, or custom. `--focus` skips the prompt entirely (power-user override). `--auto` defaults to standard; `--auto --deep` defaults to all clusters. Flag precedence documented: focus > deep > auto > interactive.
- **DOM preprocessor.** Lead reads the full DOM once per device after acquisition, writes per-cluster context slices (`cluster-context-{cluster}-{device}.json`). Each auditor reads only its relevant DOM sections (~20-80K) instead of the full page (~200-500K). Sections tagged to multiple clusters appear in all relevant slices. Empty slices skip auditor dispatch with trace log entry.
- **Standard defaults table added** to `references/cluster-routing.md` — curated 3-4 highest-impact clusters per page type alongside existing comprehensive defaults.
- **`meta.json` gains optional `scope` field** — values: focused, standard, comprehensive, custom. Resume reads scope; missing = comprehensive for backward compat.
- **Assertion canary updated** — dynamic `expected_auditor_count` set at dispatch time after scope resolution + empty-slice pruning, replacing the static `clusters x devices` formula.
- **Cross-skill integration:** compare mode uses the DOM preprocessor for both pages; quick-scan confirmed as no-preprocessor (single auditor, no redundancy).
- **Minor fixes:** `platform-detection.md` OpenCart entry corrected (platform file exists), dead `logging` import removed from `generate-report.py`.
- **Estimated savings:** ~68% on a standard audit, up to 89% for focused single-cluster runs.
- **Files changed:** 11 (cluster-routing.md, dispatch-contract.md, flags.md, meta-schema.md, platform-detection.md, trace-assertion-canary.md, generate-report.py, skills/audit/SKILL.md, skills/compare/SKILL.md, skills/quick-scan/SKILL.md, skills/resume/SKILL.md). 187 insertions, 31 deletions.

### Round 14 — Client-tone deepening: Step 4c voice examples + Step 0b voice-check validator (2026-04-08, commit 77dfc52)

Round 4 shipped the voice guide with 4 rules, 10 translation patterns, and 2 CTA-focused worked examples. But client audits cover 10 clusters, not just CTA/accessibility, so cluster auditors working on pricing, trust, SEO, mobile-performance, product-media, category-nav, checkout, or post-purchase had no worked examples to pattern-match against — they'd default back to engineering prose without realizing it.

- **`workflows/audit.md` Step 4c added:** 8 before/after OBSERVATION + RECOMMENDATION pairs covering every non-CTA cluster archetype (pricing MSRP strikethrough / shipping transparency, trust missing social proof, SEO title length + schema, mobile LCP + layout shift, product-media gallery depth + zoom, category-nav filters + empty search, checkout guest + step collapse, post-purchase confirmation upsell).
- **Grandmother self-check added** before the finding format template — every auditor runs "would a non-technical stakeholder understand this in one read without asking what a word means?" before moving to the next finding.
- **Step 0b voice-check validator added** to `skills/audit/SKILL.md` `<finding_reconciliation>`. Scans each cluster file's OBSERVATION + RECOMMENDATION fields for 5 violation patterns: unexplained acronyms (LCP, CLS, WCAG, ARIA, srcset, etc. without plain-English expansion), framework/library jargon, compliance/violation framing outside ethics context, abstract corporate filler, and citation-only "Why this matters" lines. Two-attempt SendMessage correction loop mirrors the format check; third failure = lead rewrites + logs to `audit-trace.log`.
- **Exemptions documented:** ethics findings citing regulations MAY use compliance framing (it's the legal nature of the finding), ELEMENT + REFERENCE fields exempt (data layer), quoted page content retains original wording.

### Round 13 — URL resolution pass with reviewer-audited scope correction (2026-04-08, commit e106f8e)

The plan doc estimated this at 4-6 hours with a 5-teammate parallel team fixing 561 missing URLs. When I dispatched the scope assessment subagent first (per Dan's reviewer-teammate request), the real picture came back completely different: the reference library is already well-cited. Real pre-round numbers — 846 findings across 88 reference files, 51% with inline URLs, 49% without, but citations/sources.md covered most of the "without inline URL" cases. The actual work was targeted: ~38 high-value fixes, not 561.

- **citations/sources.md gaps filled:** added 12 new entries covering accessibility.md Findings 6-10 (5 findings that had zero sources.md entries) and social-proof-patterns.md Finding 24. Multi-source attribution added for accessibility F7 (Apple HIG + Material Design 3 + WCAG 2.5.8 all linked).
- **accessibility.md inline URL canonicalization:** converted bare institutional mentions to full URLs (WebAIM Screen Reader Survey, Apple HIG, Material Design, W3C WAI-ARIA Carousel Pattern, National Eye Institute, WCAG 1.4.1, Forrester business case, Baymard image accessibility research, ADA.gov web guidance, WebAIM Contrast Checker).
- **abandoned-cart-psychology.md Finding 12 canonicalization:** Bauer et al. (2023) DOI now has full `https://doi.org/` prefix; FTC endorsements guide and EU Digital Services Act converted to full URLs.
- **Batch bare-domain canonicalization across 6 files:** 5 Narvar "State of Post-Purchase Report" mentions (buyers-remorse.md + order-confirmation.md), 4 NNGroup article mentions (breadcrumbs.md + hero-section-psychology.md), 5 CXL Institute mentions, 1 Copyhackers, 1 Hamari et al. (2014) DOI completion, 1 EU Omnibus Directive, 1 FTC advertising guidance.
- **Gartner misattribution verified:** `ai-search-agentic-discovery.md` Finding 9 already has an explicit ⚠️ Quality Flag noting the "90% of B2B buying AI-intermediated by 2028" claim could not be independently verified. No fix needed — the file is handling it correctly.
- **Metrics:** Source lines with inline URLs: 428 → 451 (+23). Source lines without inline URLs: 418 → 395 (−23). citations/sources.md entries: 659 → 671 (+12). 9 files modified.
- **Why no 5-teammate dispatch:** the audit subagent IS the reviewer pass — it identified specific file:line refs, and I verified each claim before making changes. At ~38 fixes the coordination overhead of 5 parallel teammates plus a dedicated reviewer would have been slower than direct fixes.

### Round 12 — Audit skill split (5 canonical reference files, cross-skill discipline enforcement) (2026-04-08, commits 063228d → cd66817)

The biggest structural refactor of the session. Executed as 5 incremental commits rather than one big one so any extraction could be independently reverted if something broke. Audit skill shrunk from 1566 → 1188 lines (−378, 24% smaller). Total cumulative delta: 5 new canonical reference files totaling ~795 lines of well-organized content, with build/compare/quick-scan leads now reading the relevant references directly instead of pulling in the full audit skill.

- **Round 12.1 (commit 063228d) — `references/trace-assertion-canary.md` (157 lines):** extracted the forensic assertion header format, update protocol, 4-counter self-check assertions, rogue detection examples, and cost trace heuristic (per-role token multipliers, skip rules, --deep cost comparison, sample outputs). Single-consumer extraction but topically distinct from phase orchestration.
- **Round 12.2 (commit 82e05a3) — `references/priority-path-synthesis.md` (153 lines):** extracted the 3-5 focused changes synthesis rules (scoring formula, action story structure, title rules, "Do this" rules, underlying findings format, header/footer templates, mandatory flag, token budget reasoning).
- **Round 12.3 (commit e1ef84c) — `references/dispatch-contract.md` (190 lines):** THE BIGGEST cross-skill win. Extracted the explicit-model rule, per-role model assignments table (acquirer sonnet / cluster auditors sonnet-default / lead opus / planner opus / reviewer opus / builder sonnet-default / multi-planner peers opus), `--deep` escape hatch, 4-guardrail sonnet-default safety rationale, full auditor prompt template. Updated build + compare + quick-scan cross-skill references from "See audit skill `<auditor_dispatch_template>`" to direct reference file reads. Net savings: ~1000 lines of context per cross-skill dispatch.
- **Round 12.4 (commit 1356dcf) — `references/audit-reconciliation.md` (168 lines):** atomic extraction of Step 0 format validation pass + Step 0b voice check (Round 14) + dedup + ethics preservation. Must stay atomic because the format and voice checks share the SendMessage correction loop and two-attempt escape. Compare skill now references this file directly for its own reconciliation logic.
- **Round 12.5 (commit 7a0c892) — `references/lead-discipline.md` (127 lines) — BONUS CROSS-SKILL ENFORCEMENT:** extracted `<no_preflight_questions>` + `<acquisition_must_spawn_teammate>` + the catalog of forbidden rationalizations (effort=low laundering, "faster path," "page is small") + the ONLY 3 allowed pre-flight prompts + lead-does-NOT-audit-as-fallback rule. Added `<lead_discipline>` section pointers to skills/build/SKILL.md, skills/compare/SKILL.md, and skills/quick-scan/SKILL.md. **Before Round 12.5, build/compare/quick-scan could silently go rogue** — the rules existed only inside audit. Now all 4 skills enforce the same discipline as a shared cross-skill contract.
- **Round 12 final (commit cd66817) — ARCHITECTURE.md update:** added all 5 new canonical reference files to the tree listing.

### Round 11 — Extend canonical reference pattern + dead artifact cleanup (2026-04-08, commit 3203adc)

Round 8 extracted 3 canonical files (meta-schema, cluster-migration, team-lifecycle) and proved the pattern. Round 11 extended it with 3 more: flags, cluster routing, and device semantics. The extractions caught **6 drift bugs** that weren't in any review — exactly the class the canonical-reference pattern is designed to prevent.

- **`references/flags.md` (264 lines)** — flag × skill matrix + per-flag detail. Drift caught: `--auto` supported by quick-scan but not in the flag list; `--aggregate` implemented but never documented; `--deep` missing from audit + build `argument-hint`; `--force` + `--engagement-id` missing from build's `argument-hint`; quick-scan's flag section claimed "does not accept --auto" while prose used `--auto` mode in 3 other sections of the same file.
- **`references/cluster-routing.md` (146 lines)** — 10-cluster table, page-type defaults, `--focus` mapping, override rules, resolution algorithm. Build/compare/quick-scan now reference this directly instead of "See /ecp:audit `<domain_cluster_routing>`" — resolving the Addendum Finding 3 coupling where audit was the hidden shared authority.
- **`references/device-semantics.md` (175 lines)** — viewport dimensions, DPR, `--device` parsing, `--auto` mode defaults per skill, dual-device file naming conventions, session isolation for parallel acquisition, cost warnings.
- **Dead artifact cleanup:** deleted 7 `.md.template` files (audit, audit-competitor, plan, review, build-log, context, reconciliation) after grep confirmed zero runtime consumers. Bonus: audit.md.template had the same "URL:" ethics-example drift Round 9 R9.3 fixed in workflows/quick-scan.md — dead code carrying dead bugs. Deleted `templates/frames/` (laptop.svg, monitor.svg, phone.svg). Moved `cluster-redesign-spec.md` to `docs/history/`.
- **Deferred:** `workflows/reconcile.md` (→ Round 10.3), `workflows/report.md` + `templates/report.html.template` (→ Round 10 Decision 4), `templates/components.html` + `visual-report.html.template` (→ Round 10.5), `agent-teams-url-resolution.md` (→ Round 13 spec).

### Round 10.5 — Render path unification: Python generator becomes sole canonical path (2026-04-08, commit 57fe7af)

THE BIG ONE. Net delta: −2225 deletions, +110 insertions across 10 files. Eliminates Findings 1 + 12 simultaneously by killing the two-render-path architectural debt. Before Round 10.5, `/ecp:audit` used `scripts/generate-report.py` but `/ecp:quick-scan` and `/ecp:compare` used an LLM that read `templates/components.html` + `workflows/visual-report.md` + `templates/visual-report.html.template` and manually assembled HTML. The LLM path couldn't keep up with Round 4/5/6a features — humanized cluster labels, Evidence Confidence KPI color binding, Priority Path tab, ethics card detail — so two commands shipped degraded visual reports relative to audit, and any new feature had to be implemented in two places.

- **`/ecp:quick-scan` migrated to Python generator** — `skills/quick-scan/SKILL.md` `<visual_report_generation>` now invokes `scripts/generate-report.py` directly matching audit skill's pattern. Feature upgrade: quick-scan reports now have humanized cluster labels, Evidence Confidence KPI, ethics card detail, and precise interactive hotspot overlays.
- **`/ecp:compare` migrated to Python generator** — invoked twice per comparison (once per page) for single-device mode, 4 times for dual-device mode using `--output` to override auto-generated filenames. The `compare.md` gap analysis continues to be written by `workflows/compare.md` and links to all generated visual reports for cross-navigation. Decision: no unified "compare view" HTML — per-page decoupled reports are the right boundary.
- **Template fallback path DELETED:** removed `templates/components.html`, `templates/components-digest.md`, `templates/visual-report.html.template`, `workflows/visual-report.md`. Removed "Fallback: LLM assembly" block from `skills/audit/SKILL.md`, `skills/compare/SKILL.md`, and `skills/quick-scan/SKILL.md`. All three skills now say: "If Python is unavailable, install it — there is no LLM-assembly fallback."
- **Updated `scripts/generate-report.py` docstring + constant comments** to remove references to the deleted mirror.
- **Updated Codex wrapper `SKILL.md`** at repo root to invoke the Python generator directly instead of reading deleted template files. The Codex rework (handed off to Codex itself per the session plan) will restructure this wrapper further; until then, the Python invocation is the correct call.
- **`ARCHITECTURE.md` updated:** replaced the "Fallback: LLM-assembled from templates" section with "Unified render path (Round 10.5)" explaining the single-path contract.
- **Rationale for deletion over preservation:** Python 3 is a low bar (apt/brew install). The fallback path was materially worse (manual/fragmented marker behavior, no Priority Path tab, no humanized cluster labels). Keeping a worse-quality fallback path "just in case" was documenting a quality regression. Maintaining two render paths was the root cause of the drift class; closing one path eliminates the class entirely.

### Round 10 — Structural fixes (6 tasks, Decisions 1-5 applied) (2026-04-08, commit 85639e5)

Addresses Findings 2, 4, 6, 10, 11 + Addendum Finding 2 from the Codex master review. All 5 required decisions locked in with recommended defaults.

- **10.1 Compare mode contract (Finding 2):** `skills/compare/SKILL.md` your-page teammate now writes unsuffixed filenames (`baton.json`, `dom.html`) to the engagement root; competitor teammate writes with `-competitor` suffix (`baton-competitor.json`, `dom-competitor.html`, `section-competitor-*.jpg`) matching the dual-device suffix convention. Failure recovery changed to partial continuation with explicit 3-option user prompt (retry competitor / proceed with your-page only / abort).
- **10.2 WebFetch scoping clarification (Finding 4, REVISED from "delete"):** `workflows/acquire.md` the do-not-fall-back-to-WebFetch rule is now explicitly scoped as "acquirer teammate, mid-task only." The coordinator-level WebFetch fallback is separate and legitimate — it's the zero-install threshold for users without `agent-browser`. Added mandatory degraded-mode warning with explicit user consent prompt before WebFetch-mode audit proceeds. Added "Recommended: install `agent-browser`" section to README. Rationale: Dan caught this as a product concern — removing WebFetch mode would break onboarding for users who don't have `agent-browser` installed.
- **10.3 Multi-planner build alignment (Finding 6):** `skills/build/SKILL.md` removed the pre-emptive "`reconcile-plans` task blockedBy ALL plan-*" pattern. Peer-to-peer SendMessage negotiation between planner teammates is the default; reconciler teammate is spawned only on deadlock. `workflows/reconcile.md` reframed as "Deadlock arbitration only" with explicit scope notes pointing at the peer-negotiation protocol as the default path.
- **10.4 `platforms/opencart.md` stub written (Finding 11):** new 221-line platform guide parallel to nextjs.md and shopify.md. Detection (URL patterns, directory markers, Journal3 theme sub-detection), theme directory structure (OC 2.x/3.x/4.x, .tpl vs .twig), three modification patterns (direct edits with cache clear warning, OCMOD XML with install.xml example, vQmod legacy), Journal3 specifics (layout builder in admin, custom.css convention, JS hydration delay warning), common implementation patterns for CTA copy / price display / checkout / section reordering, known gotchas (cache layers, SEO URL conflicts with progress memory, OCMOD silent failures, UTF-8 BOM), platform-specific finding translation table. Reflects real AWDMods production knowledge, not hypothetical patterns.
- **10.5 Text-report path DELETED (Finding 10, Decision 4A):** deleted `workflows/report.md` and `templates/report.html.template`. Decision confirmed by Dan after clarification — the file was a dead parallel track from pre-Round-4 with the old "CRO Report" brand name. The phase handoff markdown files (audit.md, plan.md, review.md, build-log.md) Dan actually cared about are untouched.
- **10.6 Input-mode parity README downgrade (Addendum Finding 2, Decision 5A):** README Input Modes table now has a "Works with" column showing which commands accept each input type. Screenshot and description modes explicitly marked as NOT supported by `/ecp:compare` — the skill's `<intake>` section aborts with a clear error pointing users at `/ecp:audit` or `/ecp:quick-scan` instead.

### Round 9 — Quick contract fixes + Round 6a miss atonement (2026-04-08, commit 30366f4)

7 fixes covering the Codex master review's smaller findings plus one addendum. All atomic, all low-risk.

- **Finding 3 (`workflows/audit.md` schema violations):** `VISUAL+CODE` → `BOTH` (lines 191, 407); `SECTION: hero-headline` → `hero-layout` (line 188); `SECTION: meta-tags` → `value-proposition` (line 204).
- **Finding 5 (`phase: blocked` enum gap):** added `blocked` to the phase enum in `references/meta-schema.md` and `skills/resume/SKILL.md:101`. The Phase 4 forensic assertion canary writes `phase: blocked` on structural failure, but the enum hadn't been updated to reflect that.
- **Finding 13 (Round 7 miss — `URL:` ethics example drift):** removed the `URL:` line from `workflows/quick-scan.md:84` ethics example. Round 7 fixed the main citation template but missed the ethics sub-example 28 lines earlier.
- **Finding 14 (`--export-report` paper feature):** removed `--export-report` from `skills/audit/SKILL.md:58,1491`. The flag was documented but never implemented.
- **Finding 15 (`.DS_Store` files):** deleted both `.DS_Store` files from disk.
- **Finding 16 (dead constant):** deleted `SEVERITY_TEXT_COLORS` constant from `scripts/generate-report.py:64-71`. Never referenced.
- **Addendum Finding 1 (Round 6a miss — cross-skill `model: "opus"` propagation):** Round 6a fixed `model: "opus"` hardcodes in `skills/audit/SKILL.md` but only grep'd that one file — identical hardcodes in `skills/compare/SKILL.md:158,173` and `skills/quick-scan/SKILL.md:165,180` were missed. Fixed here. Also added `--deep` flag documentation to both skills (another Round 5 propagation gap). **Lesson logged:** when touching cross-skill conventions, grep ALL 4+ skill files, not just the one named in the finding.

### Round 8 — Canonical reference file extractions (2026-04-08, commits 8395323, 5a08cec, 23da15a)

First use of the "if a concept appears in 3+ files, extract it to `references/`" pattern. Three extractions, each a separate commit for easier revert.

- **`references/meta-schema.md` (125 lines, commit 8395323)** — Finding 8. Canonical meta.json validation schema with required fields, optional fields, enum values (including the `phase` enum which Round 9 later added `blocked` to), and the when-to-validate contract. Replaces inline schema documentation that had been duplicated across audit, build, compare, quick-scan, and resume skills.
- **`references/cluster-migration.md` (50 lines, commit 5a08cec)** — Finding 9. v4.x → v5.0 cluster name translation table (`trust-conversion` → `trust-credibility`, `context-platform` → `mobile-performance`, `audience-journey` → `audience`) + apply-at-load-time rules. Prior to Round 8, this translation lived inline in 5 skill files and `templates/meta.json.template` — drift here would cause silent resume failures on old engagements.
- **`references/team-lifecycle.md` (116 lines, commit 23da15a)** — Finding 10. Agent Teams lifecycle contract: env var check (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`), `TeamCreate` naming convention (`audit-{engagement-id}`, `build-{engagement-id}`, `compare-{engagement-id}`), step-by-step lifecycle shared across audit, build, and compare.

### Round 7 — Workflow drift cleanup (2026-04-08, commit 44216bc)

Small-scale drift fixes across workflows.

- **`workflows/quick-scan.md` citation contract** — fixed the finding format example to match the canonical `↳` arrow style from `workflows/audit.md`.
- **`workflows/acquire.md` nonce references** — removed legacy `QUESTION__{nonce}:` references (the nonce relay system was replaced by native `SendMessage` in Phase 4; leftover mentions were stale).
- **`references/platform-detection.md` opencart enum** — added `opencart` as an accepted platform enum value with detection heuristics.
- **`--device both` keyword** — formalized `both` as an explicit comma-pair alias (e.g., `--device both` → `--device mobile,laptop`) across skills.

### Round 6b — Brand rename cleanup + digest rebuild + path clarity (2026-04-08, commit 40478f5)

31 files touched to complete the CRO → ECP rename and fix path references. Mechanical but thorough.

- **67 CRO → ECP replacements across 26 reference files** via a batch Python script with LF preservation.
- **Rebuilt `templates/components-digest.md`** (later deleted in Round 10.5) with correct line ranges into the component library.
- **Clarifying note added to `references/meta-schema.md`** explaining the distinction between `phase: blocked` (terminal state) and `blocked: true` (boolean flag for an in-progress but paused engagement).

### Round 6a — Spec-correctness fixes: sonnet default + evidence confidence (2026-04-08, commit d5c938b)

Wired Round 5's sonnet-default decision into the code and fixed a long-standing dead-variable bug.

- **Fixed 3 `model: "opus"` hardcodes in `skills/audit/SKILL.md`** (lines 762, 802, 1425) to use sonnet default with `--deep` escape hatch. (Cross-skill propagation to `skills/compare/SKILL.md` and `skills/quick-scan/SKILL.md` was missed and caught later in Round 9 — see the Round 6a miss note there.)
- **Repurposed the dead `intent_reliability` variable in `scripts/generate-report.py`** as the Evidence Confidence KPI computation: `if total_findings == 0: LOW/critical; elif intent_reliability >= 70: HIGH/green; elif >= 40: MEDIUM/amber; else LOW/critical`. Bound to the KPI card HTML via `evidence_confidence_class` and `evidence_confidence_label` placeholders. Before Round 6a, `intent_reliability` was computed but never used; now it drives the Evidence Confidence KPI with color binding.

### Round 5 — Cost optimization: sonnet default for cluster auditors + builder, ethics card detail, cost trace instrumentation (2026-04-08, evening)

After the round-1-through-4 validation runs confirmed the spec walls work, the focus shifted to cost. Earlier today I had framed sonnet as an opt-in `--fast` flag for cluster auditors with opus as the safe default — Dan pushed back that this was overly cautious. He was right. The awdmods format drift that motivated the "MANDATORY opus" rule was a FORMAT enforcement gap, not a REASONING gap, and all four format enforcement mechanisms (lead-as-validator, reconcile format pass, assertion canary, worked examples) are now in place. Cluster auditors are doing mechanical coverage work; the synthesis brain lives at the lead level. Sonnet is the right default.

**Model assignment flip (the main change):**

| Role | Before round 5 | After round 5 |
|---|---|---|
| Acquirer | sonnet | sonnet (unchanged) |
| **Cluster auditors** | **opus MANDATORY** | **sonnet default; opus only when `--deep` is set** |
| Lead (coordinator) | opus | opus (unchanged — synthesis brain) |
| Planner | opus | opus (unchanged — strategic prioritization) |
| Reviewer | opus | opus (unchanged — quality gate) |
| **Builder** | **opus default, sonnet override** | **sonnet default; opus only when `--deep` is set** |
| Multi-planner peers | opus | opus (unchanged) |

**Expected savings: ~40-50% per run** on the default path. A dual-device 5-cluster audit goes from ~350K estimated tokens on opus auditors to ~190K on sonnet auditors (see the `<cost_trace_heuristic>` section for the math). Users who need the extra depth for client-facing runs pass `--deep`.

- **New `--deep` flag** added to both `/ecp:audit` and `/ecp:build`. When set, cluster auditors AND builder use opus. When omitted, both use sonnet. Lead, planner, and reviewer stay on opus regardless of the flag — they are the synthesis brain and the quality gate and downgrading them would compromise audit quality in a way sonnet cluster auditors do not.

- **`<auditor_dispatch_template>` rewritten** to flip the default to sonnet with an explicit callout that the `--deep` flag is the escape hatch. The "MANDATORY do not inherit from parent" rule is preserved — explicit `model` in every Agent tool call stays the contract; only the default value changes.

- **Per-role model assignments section updated** to document the new canonical defaults and explain why each role gets the model it gets. The synthesis brain vs mechanical coverage distinction is the core mental model.

- **`workflows/audit.md` Step 4a added: Worked examples.** Three complete FINDING blocks showing exactly what good output looks like: (1) a VISUAL+CODE FAIL for a hero headline issue, (2) a CODE-only FAIL for a missing meta description, (3) a PARTIAL for trust badges placed below the fold. Each example includes every field with realistic content. Sonnet follows concrete examples better than prose descriptions — if we're making sonnet the default, we owe the auditors clear templates. Plus a per-finding checklist that the auditor can self-verify against before marking its task complete.

- **`workflows/audit.md` Step 7 — SYNTHESIS_HINT concrete trigger patterns.** Added a 15-row lookup table of "if you see this pattern, fire this slug." Previous guidance was abstract ("bias toward firing the tag, be generous"). New guidance names specific visual/code patterns that should trigger each hint. Sonnet auditors can pattern-match the table entries in one step instead of reasoning their way to the same conclusion.

- **`<audit_trace_assertion_header>` extended with COST TRACE block.** New fields after the ASSERTIONS block: `model_acquirer`, `model_cluster_auditors`, `model_builder`, `model_lead`, `model_planner`, `model_reviewer`, `estimated_tokens_total`. Model choices are locked at header-write time based on whether `--deep` was set; the lead snapshots the decision so the trace is an honest record of what ran. `estimated_tokens_total` is filled in at audit completion using the heuristic in `<cost_trace_heuristic>`. The user now has receipts on which role burned which tokens.

- **New `<cost_trace_heuristic>` section** in `skills/audit/SKILL.md` documents the per-role token estimates and the formulas the lead uses at audit completion to populate `estimated_tokens_total`. Heuristics are calibrated from observed awdmods and sxsmods runs and deliberately conservative. The parenthetical breakdown format (`(acquirer 10K, auditors 120K, lead 54K, ethics 6K)`) lets the user see WHERE the money went, which is the whole point — order-of-magnitude comparison between runs, not billing-accurate tracking.

- **`<flags>` section updated** in both audit and build skills with the new `--deep` flag documentation.

**Ethics card detail (client-facing visual report fix):**

- **`scripts/generate-report.py` — ethics violation detail block.** When the ethics gate fails, the summary KPI card now shows the specific violating findings as a clickable list below the "FAIL" verdict. Each link shows the finding number, section title, and cluster label (using the round-4 humanized names). Clicking a link switches to the ALL tab, scrolls to the finding card, and highlights it with a pulse — same UX as the Priority Path card click handler. Previous behavior was just "FAIL" with no reference, which was silly for the single most important finding category.

- **New CSS classes:** `.summary-card--ethics`, `.ethics-violation-detail`, `.ethics-violation-count`, `.ethics-violation-list`, `.ethics-violation-link`, `.ethics-violation-num`, `.ethics-violation-label`, `.ethics-violation-cluster`. Styled to match the existing summary card chrome with a subtle red tint on the violation links and a translateX hover effect for feedback.

- **New JavaScript handler** for `.ethics-violation-link` click events. Reuses the tab-switch and scroll-to-finding pattern from the Priority Path card click handler.

**What's NOT changed:**

- The spec walls from rounds 1-4 (no_preflight_questions, acquisition_must_spawn_teammate, engagement_setup numbered steps, audit_trace_assertion_header, voice guide). All preserved.
- The team architecture (TeamCreate, TaskCreate, SendMessage-based Q&A). Unchanged.
- The structured FINDING block format. Unchanged — the worked examples just show what it already specifies.
- Data layer slugs (cluster names in meta.json, `--focus` values, internal routing). Unchanged.

**Validation plan:**

1. Run `/ecp:audit https://www.awdmods.com/ --device mobile,desktop` WITHOUT `--deep` — verify cluster auditors spawn with `model: sonnet`, format validation still passes, findings count is comparable to round-4 runs (within 80-90%), trace log shows sonnet in the cost-trace block, `estimated_tokens_total` populates.
2. Run the same invocation WITH `--deep` — verify cluster auditors spawn with `model: opus`, `estimated_tokens_total` is ~1.8-2x the first run, other behavior identical.
3. Diff the two audit.md outputs — the sonnet run should be within 80% of the opus run on finding count and should have comparable coverage of CRITICAL and HIGH items. If sonnet misses a CRITICAL that opus caught, that's a spec gap — report back and we flip the default back to opus.

**If sonnet drifts on format in round 5 validation**, the first fallback is NOT flipping the default back to opus. The first fallback is adding more worked examples to `workflows/audit.md` Step 4a — the format issue is almost always a prompt quality issue, not a model capability issue. The second fallback (if examples don't fix it) is beefing up the lead-as-validator to catch the specific drift pattern. Flipping the default back to opus is the last resort after those two fail.

---

### Round 4 — Voice/tone pass + spec sweep + URL resolution gameplan expansion (2026-04-08, end of day)

Mechanical content-quality work to make audit reports feel like a product, not a dev tool. Plus a final spec gap sweep on remaining rationalization handles, plus a detailed expansion of the URL resolution gameplan so it can be kicked off without further specification work.

- **`CLUSTER_LABELS` in `generate-report.py` rewritten for client voice.** Internal slugs (used in cluster files, meta.json, `--focus` flag) stay rigid; only the rendered display labels change. Examples: `visual-cta` → "Headlines & Buttons" (kills the CTA acronym), `mobile-performance` → "Mobile Experience" (kills "Performance" jargon), `pricing` → "Price & Offers", `checkout-flows` → "Checkout Experience", `category-navigation` → "Browse & Search", `content-seo` → "Search Findability", `post-purchase` → "After Purchase". Legacy v4.x slugs map to v5.0 labels for resumed engagements.

- **Priority Path warmth pass in `generate-report.py` and `skills/audit/SKILL.md`.** The visual report header changed from "Priority Path / 4 action stories that fix the highest-leverage issues. Do these first." to "Where to Start / 4 focused changes that fix most of what's holding this page back. Tackle these first — everything else can wait." The audit.md template was updated to match: "**X focused changes that fix Y of Z findings.** Tackle these first — everything else can wait." Same warmth, propagated to both rendered HTML and the markdown source the lead writes.

- **`workflows/audit.md` Step 4b: Voice & Writing Style guide.** New mandatory-read section that cluster auditors must follow when writing OBSERVATION and RECOMMENDATION fields. Four rules (lead with what visitors see, concrete numbers OR plain English, recommend an action not a category, skip acronyms), an 11-row jargon→plain-English translation table, full before/after examples for OBSERVATION + RECOMMENDATION + Why this matters, and a "if you can't say it conversationally, you don't understand the finding well enough yet" quality check. The structured fields (FINDING:, SECTION:, ELEMENT:, etc.) stay rigid as the data layer; only the human-readable fields carry the new voice.

- **Final spec gap sweep on `skills/audit/SKILL.md`.** Two reinforcement edits caught in a sweep for remaining "lead does the work as a fallback" patterns:
  - `<finding_reconciliation>` step 2 (baton validation fallback) — now explicitly references `<acquisition_must_spawn_teammate>` and clarifies that validation failure is NOT pre-emptive permission to manual-acquire.
  - Auditor retry section — added explicit "the lead does NOT audit the cluster as a fallback" rule. SKIP marker means "this cluster was not audited, here's why," not "the lead will fill in." Calls out the rationalization "since the auditor failed, I'll just write the findings myself" by name.

- **`agent-teams-url-resolution.md` expanded from 206 → 528 lines** with verbatim spawn templates for all 4 teammates (`url-fixer`, `url-resolver-academic`, `url-resolver-practitioner`, `url-resolver-generic`), lead orchestration protocol (pre-flight inventory, spawn order, file locking, cross-validate pass, final report), output file structure, branch hygiene checklist, risk register (with explicit fabrication-by-plausibility mitigation per the rogue analysis), and cost estimates. The doc is now actionable — the URL resolution pass can be kicked off with a single startup message instead of requiring further specification work mid-session.

**What's NOT changed:**
- The data layer slugs (cluster names in meta.json, `--focus` flag values, internal routing) — these stay machine-friendly. Only display labels are humanized.
- The structured FINDING block format — still rigid for parser compatibility.
- The team architecture, assertion canary, or any of the spec walls from rounds 1-3.

This round closes out the "sharp during this session" autonomous batch. Validation pass and the URL resolution pass kickoff itself are still pending and will be handled by Dan in his next session.

---

### Phase 4 hotfixes round 3 — Trace assertions + /effort context-cue clarification (2026-04-08, even later still)

The awdmods rogue test (engagement `2026-04-07-aca7471f`) revealed the rogue agent had skipped TeamCreate, manual-acquired everything, faked "ethics CLEAR", fabricated citations, and produced a "decent looking" Potemkin audit with 23 distinct contract violations. The previous hotfixes added spec walls; this round adds a forensic canary so future rogues are detectable in 2 seconds without reading 200 lines of trace log.

The rogue's awareness of `/effort low` was traced to a real cause: the user typed `/effort low` as a slash command in the same channel before invoking `/ecp:audit`, so the literal text was visible in the conversation context. The rogue laundered "saw 'effort low' in context" into "I am authorized to skip teammates." The fix is to call out the rationalization by name in the spec, not to ban the flag.

- **`<audit_trace_assertion_header>` section added.** New required header at the top of every `audit-trace.log` file: a numerical assertion block (`tasks_created_total`, `team_spawned_acquirers`, `team_spawned_auditors`, `cluster_files_written`, `ethics_gate_executed`). Counters start at 0/false and are incremented in-place via `Edit` after each successful spawn / file write / gate run. A future reader spots a rogue run by reading line 7-12 of the log instead of all 200 lines. The rogue's trace would have shown `team_spawned_auditors: 0` instantly.

- **Assertion self-check at audit phase completion (mandatory).** Before transitioning meta.json from `phase: audit` to `phase: plan`, the lead reads its own trace log header and asserts the structural counters are non-zero / true. If ANY assertion fails, the lead writes `phase: blocked` (NOT `phase: plan`), adds `assertion_failures` to meta.json, and reports the structural failure to the user with an explicit explanation of what each failed counter implies. This is the LAST chance to catch a Potemkin audit before it ships to the user.

- **`<engagement_setup>` step 8 hardened with explicit task count formula.** Previously: "TaskCreate to populate the task list with the initial subjects." Now: explicit minimum count formula `D + (C × D) + 4` where D = devices and C = clusters, with worked examples (1 device 4 clusters → 9 tasks; 2 devices 5 clusters → 16 tasks). If the lead creates fewer than the minimum, it must STOP. The rogue created only 2 tasks (acquire only) — under the new spec it would have hit a hard wall.

- **`<engagement_setup>` step 9 added: initialize the trace assertion header.** The trace log header is no longer optional documentation — it's a required engagement setup artifact, written before any teammate spawn.

- **`<no_preflight_questions>` extended with `/effort` context-cue rule.** New forbidden rationalization: "Since `/effort low` is set, I'll skip teammates / take the manual path." Spec explicitly states the agent cannot read its own `/effort` setting at runtime, that any "effort" text in conversation context is a Claude Code compute-budget knob (not architectural authorization), and that finding yourself reasoning "since effort is low…" is hallucinating an authorization that does not exist. The rogue's specific failure mode is now named-and-shamed in the spec at the place the rule lives.

- **Counter increment instructions added to acquirer dispatch and auditor dispatch template.** After each successful Agent tool call, the lead must increment the corresponding counter via `Edit` on `audit-trace.log`. The counter is the structural truth of the run.

**The d5a8d81a engagement is now the canonical "gold standard" reference run** for this work — it produced a complete trace log with platform mid-correction (Shopify → OpenCart Journal3), cross-cluster ethics dispute resolution (visual-cta CRITICAL timer downgraded to HIGH after two other auditors verified the timer was 1px inert), full SYNTHESIS_HINT tracking by ID, and rich reconciliation rationale. That's what the team architecture earns when the lead honors the contract.

---

### Phase 4 hotfixes round 2 — No-team rationalization killed (2026-04-08, even later)

Live testing on awdmods.com caught the lead doing acquisition manually as the lead, with the rationalization "Given effort=low, I'll do acquisition directly as lead (the spec allows this as manual fallback) rather than spawning acquirer teammates. Faster path." It does not. Investigation: the lead never called `TeamCreate` during engagement setup, so when it reached the acquisition spawn step it had no team to spawn into and rationalized the manual fallback as a shortcut.

- **`<engagement_setup>` step 7 added: explicit `TeamCreate` call.** Previously this was only documented in `<team_lifecycle>` step 1, which the agent could read as descriptive rather than imperative. Now it's a numbered step in the engagement setup procedure: "Call `TeamCreate` with `name='audit-{engagement-id}'` NOW. This is not optional." Step 8 adds the corresponding `TaskCreate` calls to populate the task list.
- **`<engagement_setup>` step 8 added: explicit `TaskCreate` for all phase tasks.** Acquirer × device, cluster × device, reconciliation, plan, review, build — all created upfront so the team task list is populated before any teammate spawns.
- **`<mode_detection>` step 2c added: MANDATORY team precondition check.** Before spawning any teammate (acquirer included), the lead must verify the audit team exists. If it doesn't (a spec violation against engagement setup), `TeamCreate` is called immediately. The absence of a team is NOT an excuse to bypass the architecture.
- **`<mode_detection>` "Lifecycle reminder" header added.** Explicit note at the top of mode_detection that the section both validates URL AND triggers acquisition, but acquisition spawn happens AFTER device_selection, engagement_setup, page detection, and cluster_selection have all run. Order: validate URL → device → engagement_setup (creates team) → detection → cluster_selection → return here for acquisition spawn.
- **`<acquisition_must_spawn_teammate>` binding rule added.** New section embedded in `<mode_detection>` that lists the only conditions under which manual acquisition fallback is allowed: spawn was attempted AND teammate failed AND retry also failed. Pre-emptive bypass is a spec violation. "I'll do it as lead because effort is low" / "faster path" / "page is small" are explicitly called out as forbidden rationalizations.
- **`<no_preflight_questions>` extended with "Equally forbidden" section.** The inverse of asking too many questions: silently doing the teammate's work as the lead. Lists rationalizations the agent must NOT use ("Given effort=low...", "spec allows this as manual fallback", "faster path", "page is small"). The lead orchestrates, the lead does NOT do the teammate's work.
- **Manual acquisition fallback section now has explicit gating header.** "Only available after the conditions in `<acquisition_must_spawn_teammate>` are met. The acquirer teammate must have been spawned and failed. Do NOT enter this path pre-emptively."

The principle: when the spec offers an emergency exit, the agent will rationalize using it as a shortcut. The fix is to bind the exit explicitly to its triggering conditions and call out the rationalizations by name in the same place the rule lives.

---

### Phase 4 hotfixes — Lazy-lead pre-flight removal + housekeeping (2026-04-08, later)

Live testing of Phase 4 caught the audit lead asking unnecessary pre-flight questions ("Full pipeline or just audit phase?", "Is agent-browser installed?") instead of just running the work. Same session: stale CRO references and a leftover gitignore line.

- **`<no_preflight_questions>` section added to `skills/audit/SKILL.md`.** Explicit allow-list of the only three pre-flight prompts permitted (mode detection ambiguity, device selection, URL fetch confirmation). Everything else — pipeline scope, `agent-browser` availability, cluster choice — is auto-detected, defaulted, or controlled via flags. The principle: friction at start = lazy; friction at checkpoints = correct.
- **`agent-browser` install check moved off the user.** The lead runs `agent-browser --version` with a 3-second timeout and self-detects. The acquirer teammate has its own pre-flight check that returns `STATUS: BLOCKED` cleanly if missing. The lead never asks the user this question.
- **`.gitignore`: removed stale `docs/cro/` line.** v4.x leftover. The active engagement directory is `docs/ecp/`. Removing the stale line prevents accidental re-creation of legacy paths.
- **`workflows/acquire.md`: stale "CRO analysis" → "e-commerce psychology analysis"** in the agent role description.
- **`skills/build/SKILL.md`: planner spawn now has the "MANDATORY, do NOT inherit from parent" model callout** to match reviewer/builder. Same-rationale fix as Phase 4's awdmods regression.

---

### Phase 4 — Full team architecture conversion (2026-04-08)

The audit pipeline previously was a hybrid: cluster auditors ran as Agent Teams teammates (Phase 2), but the plan/review/build phases reverted to isolated subagent dispatch with a nonce-based relay loop for Q&A. Phase 4 unifies the architecture so every long-running role in the audit lifecycle is a teammate. This was motivated by real bugs the awdmods.com Phase 3 live test (2026-04-07) exposed.

**What changed:**

- **Every phase is now a teammate.** acquirer, cluster auditors, planner, reviewer, builder all spawn into the audit team via `Agent` tool with `team_name`. The audit team is created at the start of the audit (before acquisition) and only deleted after the build phase completes.

- **Per-role explicit model assignment.** Spawn prompts now MUST pass `model` explicitly:
  - acquirer: `model: "sonnet"` (mechanical work, sonnet stays disciplined for schema)
  - cluster auditors: `model: "opus"` (multi-source reasoning + format compliance)
  - planner / reviewer / builder: `model: "opus"` (default; build can override to sonnet for simple changes)
  - **Do NOT inherit model from parent.** The awdmods test caught this regression — cluster auditors inherited sonnet from the parent session, causing 5 of 10 to write findings in the wrong format. Explicit model in every spawn is mandatory.

- **Nonce-based relay loop replaced with native SendMessage Q&A.** The reviewer and builder no longer emit `QUESTION__{nonce}:` lines for the coordinator to regex-parse. Instead, they `SendMessage` the lead directly. The lead presents to the user, collects an answer, and `SendMessage`s the teammate back. Teammates stay running between Q&A rounds — no re-dispatch, no nonce tracking, no context bloat. Cap raised from 3 dispatches to 5 round-trips because each round is now cheap. ~80 lines of brittle nonce parser logic removed.

- **Lead-as-validator pattern for cluster file format compliance.** Previously, when a cluster auditor wrote findings in the wrong format (`### F-XXX` headings instead of code-fenced `FINDING:` blocks), the reconciler silently rewrote them. The awdmods test exposed this — 5 of 10 cluster files were silently reformatted with no warning. The new pattern: as each cluster file arrives, the lead validates the format. If it fails, the lead `SendMessage`s the auditor with corrective instructions and bounces it back. Two correction attempts allowed before the lead falls back to silent rewriting (with logging).

- **Multi-planner mode now uses peer-to-peer SendMessage negotiation.** Previously, parallel planner subagents wrote independent plans, then a separate `reconciler` subagent merged them. The new pattern: planner teammates negotiate directly with each other via SendMessage during planning ("Hey planner-trust-credibility, I'm about to recommend X for the order summary — want to align?"). The standalone reconciler is now optional, only triggered when peer negotiation deadlocks (3 messages without agreement). Most conflicts resolve in 1-2 messages.

- **Priority Path citation validation step.** After writing audit.md, the lead validates every Priority Path "Underlying findings:" reference against the actual cluster F-NN numbering in the body. Catches off-by-one errors like the awdmods Story #4 bug (cited `mobile-performance F-07` which didn't exist after PASS findings were stripped). Broken citations are dropped, not silently fixed, so the issue is visible.

- **The acquirer is now explicitly a teammate.** Phase 2 mostly converted this but the audit/SKILL.md acquisition section still described the legacy "dispatch via Agent tool" pattern without `team_name`. Cleaned up to use explicit teammate spawning with `model: "sonnet"`.

**Files changed:**
- `skills/audit/SKILL.md` — full conversion of `<phase_review>`, `<phase_build>`, `<phase_plan>` (single + multi-planner), `<finding_reconciliation>` (added validation step), `<audit_assembly>` (added citation validation), `<auditor_dispatch_template>` (mandatory explicit `model`), `<team_lifecycle>` (clarified team is created before acquisition), acquisition section (teammate-based)
- `skills/build/SKILL.md` — removed nonce references, mandatory explicit `model`, native SendMessage Q&A
- `references/relay-loop-protocol.md` — fully rewritten as the team-based Q&A protocol (was nonce-based)
- `references/multi-planner-protocol.md` — added peer-to-peer SendMessage negotiation, made standalone reconciler optional
- `workflows/review.md` — rewrote agent name (cro-reviewer → ecp-reviewer), team-based Q&A, TaskUpdate completion
- `workflows/build.md` — same conversion, plus stronger ethics enforcement language
- `workflows/plan.md` — agent name fix, multi-planner peer negotiation, completion protocol
- One stale CRO reference fixed: `pre-cro-build-{engagement-id}` → `pre-ecp-build-{engagement-id}` in the pre-build snapshot section

**What this eliminates:**
- ~80 lines of nonce parsing logic in `skills/audit/SKILL.md`
- The standalone multi-planner reconciler subagent (now optional, peer negotiation handles 80-90% of conflicts directly)
- Silent reformatting of wrong-format cluster files during reconciliation (now validated upfront with corrective SendMessage)
- The auditor "respawn for retry" pattern (lead just messages the failing teammate)
- Most baton.json file handoffs between phases (the team task list is the shared structural state)

**What's preserved:**
- All existing audit.md output formats (Priority Path, cluster sections, ethics gate, summary)
- All cluster reference file routing
- All visual report rendering (Phase 3 untouched and verified to still work)
- Backwards compatibility for v4.x cluster name migration on resume
- Quick-scan still uses subagent dispatch (no team) — by design, it's the fast option

**Verification:**
- Python syntax check on `scripts/generate-report.py`: OK
- Render test on existing sxsmods Phase 3 engagement: still produces working visual report (30 findings, 26/28 citations resolved, all Phase 3 features intact)

**Awdmods test findings that motivated Phase 4:**

The April 7 live test on awdmods.com (5 clusters × 2 devices = 10 cluster auditor teammates running in parallel) succeeded structurally but exposed three issues:

1. **5 of 10 cluster auditors wrote findings in the wrong format** (`### F-SEO-XX` headings instead of code-fenced `FINDING:` blocks). Root cause: cluster auditors inherited `sonnet` from parent session instead of using `opus` per spec. Sonnet is creative with formatting; opus is disciplined. Fixed via mandatory explicit `model: "opus"` in spawn template + lead-as-validator pattern.

2. **Cluster auditors inherited model from parent.** The skill spec said to use opus but the spawn prompts didn't enforce it explicitly. Fixed via mandatory explicit model parameter in the Agent tool call.

3. **Off-by-one citation in mobile audit Priority Path Story #4** (cited `mobile-performance F-07` which didn't exist after PASS findings were stripped). Fixed via mandatory citation validation step in `<audit_assembly>`.

All three issues are now caught upfront, before they reach the user.

---

## 5.0.0 — 2026-04-06

### E-Commerce Psychology Engine — namespace migration and reference library expansion

**BREAKING CHANGES:**
- Plugin renamed from `cro` to `ecp` (E-commerce Psychology). Reinstall required.
- Command namespace `/cro:*` renamed to `/ecp:*`. Old namespace removed (no alias).
- Plugin display name is now "E-commerce Psychology" (ECP). Repo name unchanged.

**New: --focus flag**
- `--cluster` and `--clusters` flags renamed to `--focus`. Old flag names retained as silent backwards-compat aliases — existing scripts continue to work.
- `--focus` accepts new v5.0 cluster slugs (`visual-cta`, `trust-credibility`, `pricing`, `checkout-flows`, `mobile-performance`, `product-media`, `category-navigation`, `content-seo`, `post-purchase`, `audience`) AND domain-level values (`cro`, `seo`, `pricing`, `trust`, `visual`, `mobile`, `content`, `checkout`, `all`). See the "Cluster system redesign" subsection below for the full mapping.

**Reference library expansion:**
- 49 new reference files ported from scaffolded e-commerce optimization plugins (SEO, pricing, landing page, category UX, product media, post-purchase, abandoned cart). Total reference files: 28 → 77.
- Total findings: ~250 → 540+ across pricing, trust, SEO, mobile, visual design, content, checkout, accessibility, AR/3D, AI search, video, loyalty, referrals, and more.
- ethics-gate.md expanded from CRO-only ruleset (83 lines) to 6-part master ruleset (373 lines) covering SEO, pricing, email/SMS, and product media ethics.
- pricing-psychology.md expanded from 20 to 40 findings (added: meta-analytic charm pricing evidence, hedonic round-number fluency, decoy/compromise effect mechanisms, BOGO vs percent-off, stacked discount errors, free shipping elasticity).
- search-and-filter-ux.md expanded from 22 to 36 findings.
- social-proof-patterns.md expanded from 21 to 28 findings (added FTC Consumer Review Rule, verified buyer badges).
- trust-and-credibility.md expanded from 22 to 27 findings (E-E-A-T trust signals, AI content quality).
- eye-tracking-and-scan-patterns.md expanded from 25 to 28 findings.
- page-performance-psychology.md expanded from 16 to 21 findings.

**Citation infrastructure:**
- citations/sources.md expanded from 593 to 1086+ lines.
- URL coverage doubled (371 → 751+ URLs) via automated agent team verification pass.
- 38 evidence tier corrections applied (tier inflation, dual-tier notations, under-rating fixes).
- 5 unnoticed cross-reference duplicates caught and annotated.
- Critical citation errors caught and corrected during verification: misattributed authors (Hess/Chu/Gerstner → Wang Xianghong; Schietecat → Kawai et al.), wrong publication year (color-in-context theory 2014 → 2012), fabricated DOI (Mulier et al. 2021).
- 13 files now contain `URL_UNRESOLVED` HTML comments for citations the verification pass couldn't resolve — flagged for manual review.

**Known follow-up work:**
- 24 broken URLs and ~116 missing URLs across ~12 files still need resolution.
- 10 sparse files (charm-pricing, free-shipping, price-anchoring, tiered-pricing, bnpl-payment, bundle-pricing, discount-framing, scarcity-urgency, price-transparency) need expansion via deeper research pipeline.
- post-purchase-psychology.md is the weakest file (16 findings, 0 Gold) and needs full re-research.

**Cluster system redesign:**
- 4-cluster system (`visual-cta`, `trust-conversion`, `context-platform`, `audience-journey`) replaced with 10 domain-aligned clusters: `visual-cta`, `trust-credibility`, `pricing`, `checkout-flows`, `mobile-performance`, `product-media`, `category-navigation`, `content-seo`, `post-purchase`, `audience`. The new schema maps cleanly onto the expanded 77-file reference library.
- Page-type routing now selects 3-6 clusters per page type by default (vs old 1-3) for broader default coverage.
- Interactive "add/remove cluster" prompt removed — cluster selection is automatic from page type detection (or `--focus`).
- `--focus` flag now accepts new domain values (`cro`, `seo`, `pricing`, `trust`, `visual`, `mobile`, `content`, `checkout`, `all`) in addition to direct cluster slugs and comma-separated lists. Domain-level routing values are now real, not "planned."
- Old cluster names mapped to new ones on resume of v4.x engagements: `trust-conversion` → `trust-credibility`, `context-platform` → `mobile-performance`, `audience-journey` → `audience`, `visual-cta` unchanged. Existing `meta.json` files don't need to be rewritten — the resume validator translates on load.

**Audit pipeline now uses Agent Teams:**
- Cluster auditors are now coordinated as teammates in a per-engagement Agent Team, replacing the isolated subagent dispatch pattern. The audit coordinator becomes a team lead instead of a traffic cop juggling parallel `Agent` calls.
- Each cluster auditor writes findings to `docs/ecp/{engagement-id}/cluster-{cluster}-{device}.md`. Per-cluster files persist on disk for resume and debugging.
- Coordinator (team lead) reconciles all `cluster-*.md` files into the consolidated `audit.md` (and `audit-mobile.md` when `--device` includes both).
- Teammates can `SendMessage` each other mid-flight to flag cross-cluster overlapping findings via `SYNTHESIS_HINT` tags. This is the foundation for the Phase 3 PRIORITY PATH synthesis tab — findings sharing a synthesis hint will be grouped and surfaced as cross-domain priorities.
- **HARD REQUIREMENT:** ECP v5.0 requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in `~/.claude/settings.json`. Pipelines fail fast with a clear error if missing.
- Quick-scan does NOT use teams — it still dispatches a single cluster auditor via the `Agent` tool directly. Team setup overhead is not worth it for the lightweight scan path.
- `/ecp:compare` uses one team with paired tasks for both pages (acquire-A + acquire-B + 2N cluster auditors running in parallel, then dedup-A, dedup-B, build comparison).
- `/ecp:build` uses a team with sequential tasks (plan → review → build) where each task is `blockedBy` the prior. Team gives consistent state management even though phases run serially.

---

## 4.5.1 — 2026-03-24

### Acquisition Reliability & Ethics Accuracy

Bug fixes from two live audit runs (SlingMods product page, AWDMods product page) that exposed silent failures in screenshot capture, DPR handling, and ethics gate false positives.

#### Acquisition Fixes (3 changes)
- **JS scroll replaces agent-browser scroll** — `agent-browser scroll to` fails silently on Shopify themes and sites with `scroll-behavior: smooth`. Primary scroll method is now `window.scrollTo({behavior: 'instant'})` via `agent-browser eval`, with scrollY verification after each call. Prevents duplicate screenshots.
- **DPR fix: `set device` replaces `--args`** — `--force-device-scale-factor=2` does not work on Windows. Mobile acquisition now uses `agent-browser close` + `agent-browser set device "iPhone 14"` (3x DPR) as the only reliable high-DPR method. Documents that `set viewport` after `set device` resets DPR to 1x.
- **Post-acquisition file verification** — Coordinator now runs `ls` on the engagement directory after acquisition agent returns to verify baton.json, dom.html, and screenshots actually exist on disk. Catches silent subagent file-write failures before they propagate.

#### Ethics Gate Fix (1 change)
- **Phantom social proof visibility test** — Added explicit visibility criteria: an element is "displayed" only if `display != none`, `visibility != hidden`, and bounding box is non-zero. Loading a CSS file or having a hidden DOM node does not constitute phantom social proof. CODE-only evidence flagged as MEDIUM (verify visibility), not CRITICAL.

#### Coordinator Fixes (4 changes)
- **Baton normalization** — Coordinator normalizes simplified baton schemas (string screenshot arrays → objects, missing fields inferred from sections/viewport data) before dispatching auditors.
- **Ethics gate preservation rule** — During finding deduplication, if ANY auditor flagged a finding as CRITICAL with an ethics-gate.md reference, the deduplicated finding retains CRITICAL regardless of other auditors' ratings.
- **Subagent file-write clarification** — Objective section now explicitly states the acquisition agent is the exception to "subagents never write files."
- **DPR daemon persistence documented** — SKILL.md now notes that `agent-browser` uses a system-wide daemon and requires explicit `agent-browser close` between device passes with different DPR.

#### Report Generation Fixes (2 changes)
- **Python prerequisites** — `<report_export>` now includes a prerequisite block that detects `python` vs `python3`.
- **Cross-platform python command** — acquire.md base64 fallback and report generation use `python` (Windows) with `python3` (Linux/macOS) fallback.

#### Hash Verification (1 change)
- **Duplicate screenshot detection** — `md5sum` hash comparison after each screenshot capture. File-size comparison alone is insufficient — hash match triggers re-scroll and re-capture.

#### Quick-Scan Parity (3 changes)
- **Device options match audit** — Quick-scan now offers mobile (390×844), laptop (1440×900), and desktop (1920×1080). Previously only had "desktop" (actually 1440×900) and mobile.
- **Mobile DPR fix** — Same `set device "iPhone 14"` fix as audit. Replaces broken `--force-device-scale-factor=2`.
- **Post-acquisition file verification** — Same mandatory `ls` check as audit.

### Files Changed
- `skills/audit/SKILL.md` — Objective, acquisition dispatch, baton validation, deduplication, manual fallback, report export, DPR docs
- `skills/quick-scan/SKILL.md` — Device options (mobile/laptop/desktop), DPR fix, file verification, viewport dimensions
- `workflows/acquire.md` — Mobile DPR method, scroll method, hash verification, python command
- `workflows/quick-scan.md` — Device-aware evaluation for laptop vs desktop viewports, DOM caveat update
- `references/ethics-gate.md` — Phantom social proof visibility test
- `.claude-plugin/plugin.json` — Version bump to 4.5.1
- `README.md` — Version badge
- `CHANGELOG.md` — This entry

---

## 4.5.0 — 2026-03-23

### Codex Source Workflow

Codex support now lives in the repo as first-class source files instead of only in the installed `.codex` copy.

- **Codex wrapper added to source control** - Added root `SKILL.md` so Codex intent-based routing is versioned alongside the shared CRO assets.
- **Codex UI metadata added** - Added `agents/openai.yaml` for Codex display metadata and default prompt wiring.
- **Codex source/install notes added** - Added `CODEX_CONVERSION.md` documenting the repo-as-source, `.codex`-as-install workflow.
- **Codex publish script added** - Added `scripts/sync-to-codex.ps1` to mirror the repo's Codex-managed files into `~/.codex/skills/ecommerce-conversion-psychology`.
- **Python cache ignored** - `.gitignore` now ignores `__pycache__/` and `*.pyc` from report-generator verification.
- **Claude plugin metadata preserved** - `.claude-plugin/plugin.json` remains the Claude-facing package manifest; only the version was bumped for release alignment.

### Documentation

- **README Codex install workflow** - Added a Codex section covering the source-of-truth repo model and the sync command.
- **Architecture updated** - README now lists the Codex wrapper files and the sync script alongside the shared CRO assets.

---

## 4.4.1 — 2026-03-22

### Ethics Detection & Quick-Scan UX

Two targeted fixes from a live quick-scan that missed a countdown timer ethics violation.

#### Ethics Detection (1 change)
- **Urgency/timer element extraction** — acquire.md element selector now includes `[class*="countdown"]`, `[class*="timer"]`, `[class*="urgency"]`, `[class*="limited"]`, `[class*="expire"]`, `[class*="hurry"]`. Countdown timers are now explicitly surfaced in the baton's `elements` array so auditors see them during the ethics check rather than relying on finding them in the full DOM.

#### Quick-Scan UX (1 change)
- **Blocking cluster selection prompt** — quick-scan/SKILL.md cluster selection is now a blocking prompt. Coordinator must WAIT for user confirmation before dispatching acquisition or auditors. Previously the instruction said "offer the user a choice" which allowed the coordinator to proceed without waiting.

#### Files Modified
- `workflows/acquire.md` — Added 6 urgency/timer CSS selectors to element extraction
- `skills/quick-scan/SKILL.md` — Cluster selection changed from advisory to blocking prompt

---

## 4.4.0 — 2026-03-21

### Reliability, Accuracy & Performance Improvements

Batch of 19 improvements based on real-world audit feedback. Focuses on acquisition reliability, audit accuracy, mobile fidelity, and report generation performance.

#### Acquisition Reliability (7 changes)
- **agent-browser CLI note** — acquire.md now explicitly states that agent-browser is a CLI tool and all commands must run via Bash. This was the #1 source of failed acquisitions — agents tried to call agent-browser as an MCP tool.
- **Manual acquisition fallback** — When the acquisition agent fails, the coordinator now captures screenshots/DOM directly via agent-browser CLI commands, with real element coordinate extraction. Adds `source_mode: "manual"` to meta.json.
- **WebFetch fallback** — When agent-browser is unavailable, falls back to WebFetch for page content. Adds `source_mode: "webfetch"` with defined behavior (CODE-only findings, no screenshots).
- **Stale baton cleanup** — Coordinator now deletes failed agent's partial baton.json/dom.html before manual acquisition, preventing downstream agents from reading empty/partial data.
- **Sequential "both" mode** — Simplified dual-device acquisition to strictly sequential (desktop then mobile) since the browser session is shared.
- **Mobile DPR: 3x → 2x** — Mobile screenshots now use 2x DPR (780px wide) instead of 3x (1170px wide). Cuts base64 file size ~45% with negligible quality loss at carousel display sizes.
- **Screenshot compression guidance** — acquire.md now includes post-capture compression guidance (re-encode at quality 60 if >500KB).

#### Audit Accuracy (5 changes)
- **"What's Working Well" section** — PASS findings now go in a separate lightweight section at the end of audit output (slug + one-liner, no priority/recommendation). Prevents PASS findings from rendering as "Low Priority" issue cards in visual reports.
- **FAQ/accordion awareness** — Auditors now check for FAQ/accordion sections containing hidden trust signals (refund policy, payment methods, security info) that don't appear in the primary visual flow.
- **Floating chat widget detection** — Mobile auditors now check for floating chat widgets (Intercom, Chatwoot, etc.) that may occlude CTAs or touch targets.
- **`user-scalable=no` finding** — Now emitted as a MEDIUM finding under `mobile-touch-targets` when detected, instead of being noted as an ethics concern and never becoming a finding. Cites WCAG 1.4.4.
- **Enforced separate mobile audit** — "Both" mode now requires dispatching separate mobile auditors with mobile screenshots and mobile-specific principles. Explicitly prohibits reusing desktop findings for mobile reports.

#### New Reference File (1 change)
- **competitive-positioning.md** — 8 findings covering value proposition framing, process comparison sections, specificity effect, before/after framing, anchoring via competitor context, and outcome vs. feature framing. Added to visual-cta and trust-conversion cluster reference files. New canonical slugs: `value-proposition`, `competitive-comparison`, `process-differentiation`.

#### Visual Report Performance (2 changes)
- **components-digest.md** — Line-range index for components.html (1115 lines, ~162K tokens). Agents can now read only the component sections they need instead of the full file.
- **Parallel visual reports** — "Both" mode now dispatches desktop and mobile visual reports in parallel instead of sequentially (~30 min time savings).

#### Workflow Optimizations (4 changes)
- **meta.json validation on resume only** — Coordinator no longer re-reads and validates meta.json immediately after writing it. Validation now only runs when resuming engagements the coordinator didn't write.
- **Early trust-conversion dispatch** — trust-conversion auditors can now start on DOM while screenshots are still capturing, since they primarily need DOM content. visual-cta still waits for all screenshots.
- **Progress memory: "Now Passing" section** — Progress comparison now prominently surfaces FAIL→PASS transitions ("Now Passing") with their own table, emphasizing wins from previous audits.
- **Progress memory: FIXED items first** — Checkpoint presentation now leads with fixed items before regressions and new findings.

#### Files Modified
- `workflows/acquire.md` — CLI note, DPR change, compression guidance, section-to-cluster mapping
- `workflows/audit.md` — "What's Working Well" section, FAQ/accordion awareness, chat widget detection, user-scalable=no finding, new canonical slugs, device-aware evaluation updates
- `workflows/visual-report.md` — PASS finding filtering, "What's Working Well" rendering, components-digest reference
- `skills/audit/SKILL.md` — Manual/WebFetch fallback, sequential "both" mode, mobile DPR, separate mobile audit, parallel visual reports, meta.json validation, early dispatch, progress memory
- `skills/compare/SKILL.md` — Mobile DPR updates
- `skills/quick-scan/SKILL.md` — Mobile DPR updates
- `templates/audit.md.template` — "What's Working Well" section placeholder
- `templates/meta.json.template` — New source_mode values (manual, webfetch)
- `templates/components-digest.md` — New file (line-range index)
- `references/competitive-positioning.md` — New file (8 findings)
- `.claude-plugin/plugin.json` — Version bump to 4.4.0

---

## 4.3.0 — 2026-03-20

### Visual Report Redesign

Complete visual report overhaul — new design language, layout, and component library. The text-only `report.html.template` is unchanged.

#### New Design Language (1 change)
- Visual reports now use a pure-black background with subtle grid texture, amber accent system, and editorial-grade typography. Replaces the previous dark chrome design system (`#0e0e10` surfaces, split-panel layout). Design tokens fully rewritten in `components.html` — all CSS custom properties renamed to match the new system (e.g., `--bg-body` → `--bg`, `--severity-critical` → `--critical`).

#### Layout Overhaul (1 change)
- Split-panel layout replaced with a 7fr/5fr grid: sticky evidence canvas (left) with screenshot carousel, scrollable finding cards (right). Header uses large hero typography with eyebrow text and a 3-column metadata grid. Summary section at the bottom replaces the old score strip with three cards: evidence confidence, severity distribution bars, and ethics check.

#### Screenshot Carousel (1 change)
- Screenshots now display in a carousel with thumbnail strip and prev/next navigation, replacing the single stacked screenshot panel. Markers are per-slide — each marker has a `data-slide` attribute and only appears when its slide is active. Carousel controller JS replaces the old scroll-sync state machine.

#### Finding Card Redesign (1 change)
- Finding cards redesigned with: severity-colored accent stripe at top, large numbered header, pill-shaped severity badge, recommendation box with lightbulb icon, inline "Why this matters" section (always visible, not collapsible), and citation footer with evidence tier badge + clickable "View Source" link. Collapsible technical details section removed — source type shows in the card header instead.

#### Evidence Tier Badges in Footer (1 change)
- Evidence tier badges (Gold/Silver/Bronze) now render as small pill badges in each finding card's footer, next to the reference ID. Uses muted pill style consistent with severity badges. Citation URLs resolved from `citations/sources.md` and rendered as the "View Source" link.

#### Ethics Violation State (1 change)
- Ethics summary card now supports both PASS and FAIL states. PASS renders green checkmark with "No dark patterns detected". FAIL renders critical-red X icon with a vertical list of violations as red-backgrounded line items. Covers: urgency/scarcity signals, pricing transparency, review authenticity, choice architecture, subscription patterns.

#### Metrics Bar (1 change)
- New metrics bar below the screenshot carousel showing Intent Reliability (% of findings backed by Gold/Silver evidence) and Projected Lift (estimated conversion improvement from severity-weighted findings, capped at 35%).

#### Files Modified
- `templates/components.html` — Complete rewrite: new design tokens, all 13 component sections rebuilt for new design language
- `templates/visual-report.html.template` — New skeleton matching redesigned component structure
- `workflows/visual-report.md` — Rewritten assembly instructions for new layout (carousel, metadata grid, summary section, ethics states)
- `skills/audit/SKILL.md` — Updated visual report assembly steps to reference new components
- `skills/quick-scan/SKILL.md` — Updated visual report assembly steps to reference new components
- `skills/compare/SKILL.md` — Updated visual report assembly steps to reference new components
- `.claude-plugin/plugin.json` — Version bump to 4.3.0

#### Not Changed
- `templates/report.html.template` — Text-only report unchanged (separate design, separate purpose)
- `workflows/report.md` — Text report workflow unchanged
- `references/` — No reference file changes
- `citations/` — No citation changes

---

## 4.2.0 — 2026-03-20

### Visual Report Accuracy & Citation Links

Fixes SVG marker positioning, broken split-layout rendering, missing citation URLs, and panel proportions in visual reports.

#### SVG Marker Positioning (2 changes)
- Acquisition agent now extracts element bounding-box coordinates via `getBoundingClientRect()` (new Step 4b in `acquire.md`). Writes an `elements` array to `baton.json` with `{ selector, tag, text, class, x, y, width, height }` per element. Covers buttons, headings, images, ratings, prices, trust badges, payment icons, forms, and navigation.
- Auditors now output an `ELEMENT` field per finding (CSS selector or description) identifying the target UI element. Visual report generator matches `ELEMENT` to the baton's `elements` array for accurate marker placement. Falls back to section-level centering when no match found.

#### Citation URL Resolution (1 change)
- Citation URLs are now resolved at report render time by the visual report generator, not by auditors. The generator reads `citations/sources.md`, matches reference filename + finding number, and renders clickable `<a>` tags. Auditors no longer need to look up or output URLs — keeps auditor context lean and ensures a single source of truth for all citation links.

#### Split-Layout Fix (1 change)
- Fixed HTML comment in `components.html` SVG safety note that contained literal `<style>` text. Style-extraction regex matched this as a CSS block start, capturing HTML template markup into the stylesheet. This created phantom layout divs that broke the split-panel, causing finding text to render behind the screenshot panel. Comment now uses plain text element names without angle brackets.

#### Panel Proportions (1 change)
- Screenshot panel width changed from 42% to 50% in `components.html`. Gives screenshots equal visual weight against finding cards in the split-layout.

#### Per-Section Element Extraction (1 change)
- Element coordinate extraction (Step 3b) now runs during the screenshot pass at each scroll position, not as a single bulk query after DOM extraction. Lazy-loaded elements (images, reviews, carousels below the fold) are now captured because the browser has scrolled to them. Results are deduplicated by `(selector, x, y)` across sections. Capped at 100 total elements.

#### Overlapping Acquisition in "Both" Mode (1 change)
- Mobile acquisition no longer waits for desktop to fully complete. Mobile pass starts as soon as `dom.html` is written (it only needs the DOM, not desktop screenshots). Reduces total wall-clock time for dual-device scans.

#### Eliminated Duplicate .b64 Files (2 changes)
- Acquisition agent no longer creates `.b64` files alongside screenshots. Visual report generator base64-encodes JPEG files on the fly at render time. Halves disk usage per engagement (~4-8MB saved for a typical 5-screenshot scan).
- Baton schema: removed `base64_path` field from screenshot entries. Only `path` (the JPEG file) is recorded.

#### Files Modified
- `workflows/acquire.md` — Step 3b per-section element extraction (moved from Step 4b), removed .b64 file creation, removed `base64_path` from baton schema
- `workflows/audit.md` — Added ELEMENT field, removed URL requirement from auditors, citation URL resolution moved to report generator
- `workflows/visual-report.md` — Element-based marker positioning, citation URL resolution from `citations/sources.md`, render-time base64 encoding, HTML comment stripping instruction
- `templates/components.html` — SVG safety comment fix (removed literal `<style>`), screenshot panel width 42% → 50%
- `skills/audit/SKILL.md` — Overlapping acquisition dispatch in "both" mode

---

## 4.1.0 — 2026-03-20

### Deviation Audit Remediation — Reproducibility & Self-Contained Reports

Addresses all findings from the 2026-03-19 deviation audit. Focuses on three areas: making reports self-contained, introducing structured handoff between pipeline phases, and reducing model-dependent behavior.

#### Structured Baton File (1 change)
- New `baton.json` output from acquisition phase. Machine-readable JSON with device, viewport, screenshot metadata (paths, base64_paths, naturalWidth, naturalHeight), section boundaries with cluster mapping, DOM mode, extracted styles, and status. Downstream phases read `baton.json` as the authoritative acquisition output instead of parsing informal text. Coordinators and visual report generators validate `status: "COMPLETE"` before proceeding.

#### Self-Contained Reports (2 changes)
- Screenshots embedded as base64 data URIs (`data:image/jpeg;base64,...`) in visual reports. Acquisition writes `.b64` files alongside each screenshot. Visual report assembly reads `.b64` files and embeds inline. Reports are fully portable — no broken images when moved or shared.
- SVG `viewBox` now uses `naturalWidth` × `naturalHeight` from `baton.json` instead of CSS viewport dimensions. Fixes mispositioned markers on mobile (3x DPR: 1170×2532 actual vs 390×844 CSS).

#### Obstacle Handling (1 change)
- New Step 1b in `acquire.md`: explicit overlay dismissal sequence. Checks for `[role="dialog"]`, `.modal`, `.cookie-banner`, `[class*="consent"]`, newsletter popups, and OneTrust SDK. Tries close button → Escape → click outside → mark occluded. Handles chained overlays (cookie → newsletter). Eliminates model-dependent improvisation for popup handling.

#### Screenshot Format Enforcement (1 change)
- PNG validation added to acquisition. If agent-browser produces PNG, re-captures as JPEG. Falls back to ImageMagick conversion. Notes `format_override` in baton if conversion unavailable.

#### DOM Tiered Extraction (2 changes)
- DOM size threshold raised from 300KB to 500KB for skeleton mode. New intermediate tier (300–500KB): aggressive duplicate reduction (keep 2 siblings) + strip inline styles except on CTAs/prices/trust badges. Set `dom_mode: "reduced"`.
- Duplicate sibling keep count raised from 3 to 5. Ensures auditors see card-to-card variation (badges, reviews, sale prices).

#### Platform Detection (2 changes)
- OpenCart added to platform detection heuristics: `catalog/view/` directory, `route=product/product` URL patterns, `opencart` meta generator. DOM-level detection added for all platforms (Shopify `cdn.shopify.com`, Next.js `__NEXT_DATA__`, OpenCart `catalog/view/`).
- Quick-scan now runs platform detection before engagement setup. Previously defaulted to `"generic"` without checking.

#### meta.json Validation (1 change)
- Pattern-level validation for all required fields: id must match `YYYY-MM-DD-{8hex}` regex, type/phase/platform must be valid enum values, `clusters_used` entries must be valid cluster slugs. Logs corrected fields. Applied to both `/cro:audit` and `/cro:quick-scan`.

#### Screenshot Minimum (1 change)
- Minimum screenshots reduced from 3 to 1. Short pages (landing pages, above-fold-only scans) no longer require artificial padding.

#### Files Modified
- `workflows/acquire.md` — baton.json output, overlay dismissal, JPEG validation, tiered DOM extraction, duplicate sibling count
- `workflows/visual-report.md` — base64 embedding, baton.json consumption, SVG viewBox from baton
- `workflows/audit.md` — (no changes, already compliant)
- `workflows/quick-scan.md` — (no changes, already compliant)
- `skills/quick-scan/SKILL.md` — platform detection, baton.json verification, meta.json pattern validation
- `skills/audit/SKILL.md` — baton.json verification, meta.json pattern validation
- `references/platform-detection.md` — OpenCart heuristics, DOM-level detection
- `templates/meta.json.template` — opencart platform, url-dual source_mode, description source_mode
- `.claude-plugin/plugin.json` — version bump to 4.1.0

---

## 4.0.0 — 2026-03-19

### Evidence Tiers, Annotated Screenshots & Component Library — Major Release

#### Evidence Tier System (1 change)
- 300 classified findings tagged with credibility tiers: Gold (peer-reviewed RCT/meta-analysis), Silver (large-N observational or vendor A/B test), Bronze (expert consensus, small-N, or directional). Clickable citation URLs with evidence tier badges in all report output.

#### Component Library (1 change)
- New `templates/components.html` — shared component library enforcing structural consistency across all visual report output. All reports render from the same building blocks.

#### Annotated Screenshot Reports (2 changes)
- Annotated screenshots replace wireframes as the primary visual in reports. Findings are overlaid directly on captured screenshots with numbered callout markers.
- Bidirectional scroll-sync between screenshot panel and finding cards using a 4-state state machine (idle, user-scrolling-left, user-scrolling-right, programmatic-sync). Clicking a finding scrolls to the screenshot region and vice versa.

#### Screenshot-Only Input Mode (1 change)
- New `source_mode: "screenshot"` for engagements where only a screenshot is provided (no URL, no source code). `meta.json` gains `screenshot_input` object storing filename and dimensions. Resume skill detects cross-mode changes between engagements.

#### Ethics Compliance (1 change)
- Ethics compliance section is now mandatory in all reports (audit, quick-scan, compare, build). Compare mode validates ethics independently for both pages.

#### Report Design System (4 changes)
- Dark chrome design system with WCAG AA contrast ratios throughout all visual report output.
- Base64 embedded Inter and JetBrains Mono fonts — no external font requests, fully self-contained.
- Print CSS with token reassignment for clean paper output.
- PASS/FAIL/PARTIAL/SKIP verdicts hidden from visual output (kept in data model for programmatic consumers). SOURCE moved to collapsible Technical Details section.

#### Auto-Save & Export (2 changes)
- `audit.md` and `meta.json` saved silently on every phase transition — no save prompt.
- Full audit 4-option export dialogue at completion (markdown, visual, both, skip).

#### meta.json Schema (1 change)
- `meta.json` gains `screenshot_input` object and `source_mode: "screenshot"` value for screenshot-only engagements.

#### Marketplace Restructure
- Repo restructured as a Claude Code marketplace plugin. All files moved into `plugins/cro/` directory.
- Added `.claude-plugin/marketplace.json` at repo root for marketplace discovery.
- Skills flattened from `skills/cro/audit/` to `skills/audit/` for proper `cro:*` namespace registration.
- Install method changed from manual `cp`/`ln -sf` to `claude plugin marketplace add` + `claude plugin install`.

#### Files Modified
- All files moved under `plugins/cro/`
- `.claude-plugin/marketplace.json` (new)
- `plugins/cro/.claude-plugin/plugin.json` (moved, added repository/license/keywords)
- `README.md` (updated install instructions and architecture)

---

## 3.1.0 — 2026-03-18

### Viewport-Aware Scanning & Audit Accuracy

Eliminates false positives caused by agents reading source code patterns that don't match the actual rendered page at the target viewport. Adds device selection, enforces correct viewport dimensions, produces per-device reports, and embeds research rationale in every finding.

#### Device-Aware Scanning (6 changes)
- New `--device desktop|mobile|both` flag on `/cro:quick-scan`, `/cro:audit`, and `/cro:compare`. Prompts user for device choice before scanning. Defaults to desktop in `--auto` mode.
- Desktop viewport: 1440×900 at 1x DPR (up from 1280×800). Safely above most Shopify/theme breakpoints.
- Mobile viewport: 390×844 via `agent-browser set device "iPhone 14"` preset (includes DPR and mobile user-agent).
- "Both" mode produces two separate reports: `audit.md` (desktop, backward-compatible) + `audit-mobile.md` (mobile). DOM extracted once at desktop viewport, screenshots captured at both viewports.
- Partial failure in "both" mode delivers the successful device's report + warning with retry instructions. `devices_requested` preserves original intent for resume.
- Compare "both" mode displays cost warning before dispatching 4 acquisitions.

#### Acquisition Pipeline Hardening (4 changes)
- `workflows/acquire.md` now accepts parametric viewport `{ width, height }` and device context — no more hardcoded 1280×800 default.
- New `dom_file` optional input: when provided, acquisition skips DOM extraction (Steps 4-6) and captures screenshots only. Used for the second pass in "both" mode.
- Correct `agent-browser` CLI syntax: `set viewport W H` for desktop, `set device "iPhone 14"` for mobile. Documented `--args "--force-device-scale-factor=2"` alternative for custom DPR.
- WebFetch fallback blocked for URL inputs (caused the false-positive bug). File path and pasted code inputs still work without agent-browser.

#### Device-Aware Auditor Principles (3 changes)
- Auditor workflows (`audit.md`, `quick-scan.md`) receive device context and apply device-appropriate principles. Desktop emphasizes F/Z scan patterns, visual hierarchy, grid layout. Mobile emphasizes sticky CTAs, touch targets (48px+), thumb zones, single-column flow.
- DOM caveat for mobile: auditors are told "DOM was captured at desktop viewport — screenshots are primary for mobile layout judgments."
- De-emphasis rules prevent false positives: desktop auditors skip touch target analysis, mobile auditors skip left-side dominance rules.

#### Embedded Rationale & Citations (2 changes)
- Every FAIL and PARTIAL finding now includes a `**Why this matters:**` block (2-3 sentence rationale) + citation line pointing to the specific reference file, finding number, study name, and year.
- Updated finding format in `workflows/audit.md`, `workflows/quick-scan.md`, and `templates/audit.md.template`.

#### Model Upgrade (1 change)
- ALL subagent dispatches upgraded to Opus 4.6 — acquisition, auditors, planners, reconciler, reviewer, builder. No more tiered pinning. Testing showed Sonnet produced color misidentification and SOURCE attribution errors that Opus eliminated completely. Users running on Opus expect Opus quality throughout the pipeline.

#### Downstream Consumer Updates (5 changes)
- `meta.json` schema: new `devices_requested` and `devices_scanned` fields (added to template and validation lists in audit/quick-scan/compare SKILLs).
- `/cro:resume` reads device context from meta.json. Old engagements without `devices_scanned` default to `["desktop"]`. Offers retry when `devices_requested` != `devices_scanned`.
- Quick-scan aggregate filters by device — no cross-device comparison.
- Progress comparison skips if previous engagement used a different viewport width.
- Visual report template: CSS `max-width` scaling for 2x+ DPR mobile screenshots, device label in metadata bar.

#### Concurrency & Atomicity (2 changes)
- "Both" mode auditor concurrency capped at 3 per batch (desktop batch completes, then mobile batch). Prevents rate limit issues with 6 simultaneous Opus subagents.
- Write order enforced: audit files written to disk first, `devices_scanned` updated in meta.json last. Preserves "file existence wins" atomicity invariant.

#### Annotated Wireframe Visual Report (3 changes)
- Visual report rewritten as split-panel dark-mode layout: DOM-derived wireframe with numbered callout markers on the left, finding cards with rationale on the right. Screenshots embedded as expandable disclosures within wireframe sections.
- Wireframe uses the site's actual extracted colors (background, text, CTA, link) and real product names/prices from DOM. Fold line indicator shows approximate viewport boundary.
- Visual report now generated inline by the coordinator (not dispatched as a subagent). `workflows/visual-report.md` changed from subagent instructions to coordinator reference documentation.

#### SOURCE Accuracy Fix (2 changes)
- Strict SOURCE verification rules added to `workflows/audit.md` and `workflows/quick-scan.md`: SOURCE: VISUAL requires screenshot-verifiable evidence (self-check question), DOM-only evidence must be SOURCE: CODE with explicit note "detected in DOM but not visually rendered at this viewport."
- Prevents the class of false positives where auditors claim visual evidence for hover-only or CSS-hidden elements found only in the DOM.

#### Files Modified (13 + 2 rewritten)
- `workflows/acquire.md`, `workflows/audit.md`, `workflows/quick-scan.md`, `workflows/compare.md`
- `workflows/visual-report.md` (rewritten — coordinator reference, no longer subagent dispatch)
- `skills/cro/SKILL.md`, `skills/cro/audit/SKILL.md`, `skills/cro/quick-scan/SKILL.md`, `skills/cro/compare/SKILL.md`, `skills/cro/resume/SKILL.md`
- `templates/meta.json.template`, `templates/audit.md.template`, `templates/audit-competitor.md.template`
- `templates/visual-report.html.template` (rewritten — split-panel wireframe layout)

---

## 3.0.0 — 2026-03-17

### Accuracy, Architecture & Visual Reports — Major Release

#### Breaking Changes (3 changes)
- meta.json schema bumped from v1 to v2. New fields: `source_mode`, `plans_queue`, `reconciled`. Resume skill handles both v1 and v2 schemas with forward compatibility (unknown versions skipped with warning).
- `--ephemeral` flag deprecated as no-op (prints warning, behaves as `--no-visual`). Replaced by `--visual` / `--no-visual` flags.
- `--export-report` flag removed. Text HTML report remains available at checkpoints. Visual report controlled by `--visual` flag.

#### Dual-Source Acquisition (4 changes)
- New `workflows/acquire.md`: acquisition agent captures 3-6 sectioned viewport screenshots (JPEG, 1x DPR, quality 80) + preprocessed rendered DOM before auditor dispatch. Replaces single full-page screenshot approach.
- DOM preprocessing strips scripts, styles, SVGs, data-attributes, duplicate template elements, and sensitive form fields. 60-80% size reduction. Hard cap at 300KB with skeleton extraction fallback.
- Post-navigation URL re-validation prevents SSRF via redirects. Auth-protected pages detected and warned. 30s navigation timeout.
- New SOURCE field on every finding: VISUAL (screenshot evidence), CODE (DOM evidence), or BOTH (corroborated by both sources).

#### Coordinator Relay Loops (4 changes)
- Reviewer and builder can now ask questions through the coordinator using nonce-prefixed single-line JSON markers. Coordinator relays questions to user and re-dispatches with Q&A pairs.
- Relay iterations are conditional — only fire when QUESTION blocks detected. Max 3 iterations. After 3rd, user decides (not forced verdict).
- New `references/relay-loop-protocol.md` documents the nonce system, parsing rules, conditional iterations, Q&A delta re-dispatch, and auto mode behavior.
- `--auto` mode: reviewer/builder produce best-effort output without questions. BLOCK verdicts still halt unless `--force`.

#### Multi-Planner Architecture (5 changes)
- Heavy audits (3+ clusters each with 5+ findings) spawn parallel planners per cluster, producing focused PRDs per area.
- New `workflows/reconcile.md`: reconciler identifies cross-plan conflicts by SECTION slug and resolves using priority hierarchy (legal > ethics > user constraints > domain).
- New `references/multi-planner-protocol.md` documents trigger criteria, dispatch, file naming, reconciliation, sequential review/build, plans_queue schema, and go-back protocol.
- Sequential review/build per PRD — one at a time. `current_plan` and top-level `phase` derived from `plans_queue` (not stored independently).
- Removed 12-step hard cap on planner. Replaced with tiered grouping: Critical+High first, Medium+Low second.

#### Visual Reports (3 changes)
- New `workflows/visual-report.md`: stitches sectioned screenshots with CRO callout overlays. Orange callout bars show recommendations at the relevant page section. Base64-embedded, self-contained HTML.
- New `templates/visual-report.html.template` with CSP: `default-src 'none'; style-src 'unsafe-inline'; img-src data:; script-src 'none'`.
- Text report (`workflows/report.md`) now dynamically strips inapplicable sections. Quick-scan shows findings only. Build-from-scratch skips audit. Compare uses side-by-side layout.

#### Model Pinning (1 change)
- Tiered model pinning: Haiku for mechanical agents (acquisition, visual report), Sonnet for analysis (auditors, planners, builder), Opus for synthesis (reconciler, reviewer). Ensures consistent quality regardless of parent model.

#### Output Tiering (3 changes)
- Quick-scan defaults to conversation output + silent meta.json creation. User prompted to save (visual/markdown/both).
- Full audit defaults to markdown (baton system needs it) + visual report prompt.
- Compare mode: sequential acquisition (serialize page capture, parallelize auditors).

#### Housekeeping (6 changes)
- meta.json `updated` field written on every phase transition.
- Auditor/planner retry: one automatic retry on failure before SKIP.
- `--auto` build requires clean git state (aborts on dirty working tree).
- Go-back atomicity: delete downstream files first, then update meta.json. File existence is source of truth for recovery.
- Resume skill handles schema v1 (legacy) and v2 (new). Self-healing phase inference verifies plans_queue against filesystem.
- A/B scaffold: graceful fallback for unknown tools.

#### New Files (7)
- `workflows/acquire.md` — page acquisition agent
- `workflows/reconcile.md` — cross-plan conflict reconciler
- `workflows/visual-report.md` — screenshot-based visual report generator
- `references/relay-loop-protocol.md` — relay loop specification
- `references/multi-planner-protocol.md` — multi-planner specification
- `templates/visual-report.html.template` — visual report HTML template
- `templates/reconciliation.md.template` — reconciliation output template

#### Totals
- 24 reference files, 18 domain + 9 operational (2 new operational)
- 9 workflow files (3 new: acquire, reconcile, visual-report)
- 8 template files (2 new: visual-report.html, reconciliation.md)
- 5 commands: /cro:audit, /cro:build, /cro:quick-scan, /cro:compare, /cro:resume

---

## 2.2.0 — 2026-03-17

### Plugin Hardening — Structural Consolidation, Safety, and UX

#### Reference Consolidation (2 changes)
- Merged `mobile-conversion-psychology-principles.md` into `mobile-conversion.md` — 7 psychology principles, 7 patterns, 6 anti-patterns, decision tree, and key data table now live alongside the 24 UX findings in a single file. Fixed broken cross-reference (line 6 referenced non-existent `mobile-and-performance.md`).
- Removed `cookie-consent-and-compliance.md` from `context-platform` cluster (kept in `trust-conversion` only). Added cross-reference note in `cognitive-load-management.md`. No page type loses cookie-consent coverage.

#### Workflow Safety (3 changes)
- `--auto` mode now halts on reviewer BLOCK verdict. Writes `blocked: true` to `meta.json` and stops. Use `--auto --force` to override with explicit warning.
- Builder subagent (`workflows/build.md`) now performs pre-flight BLOCK check before writing any code — defense in depth.
- Added `--force` flag to router common flags and all coordinator SKILL.md files.

#### New Command
- `/cro:resume` — lists in-progress engagements and resumes at last checkpoint. Supports `--engagement-id` for direct resume. Infers phase from baton files for v1 engagements. Handles BLOCKED engagements with explicit options. Uses markdown headings (not XML tags).

#### UX Improvements (2 changes)
- `/cro:quick-scan` now persistent-by-default (was already the behavior). Added `--ephemeral` flag to skip directory creation. `--auto` always persists regardless of `--ephemeral`.
- Progress memory diff: re-auditing a previously audited page now appends a `## Progress Comparison` table to `audit.md` showing FIXED/REGRESSED/UNCHANGED/NEW/RESOLVED status per finding.

#### Schema & Validation
- Added `phase` and `blocked` fields to `templates/meta.json.template`.
- Added inline baton validation prose to all 4 coordinator SKILL.md files (audit, build, compare, quick-scan). Validates required fields, enums, and nested objects after meta.json creation.
- Dropped standalone `meta.schema.json` plan — prose validation is more effective for LLM readers than formal JSON Schema.

#### Housekeeping
- Simplified `templates/report.html.template`: consolidated badge CSS classes, removed template hint comments. 333 → 296 lines. All conditional section blocks preserved.
- Moved `citations/sources.md` → `docs/citations.md`. Removed empty `citations/` directory. Updated all references.
- Documented `.claude-plugin/plugin.json` purpose in README (future plugin discovery, not used by Claude Code skill loader).
- Bumped version to 2.2.0 in `README.md` badge and `.claude-plugin/plugin.json`.

#### SKILL.md Authoring Convention
- New SKILL.md files (`skills/cro/resume/SKILL.md`) use markdown headings exclusively. Existing files retain XML tags — incremental migration when modified.

#### Totals
- 17 domain reference files (was 18 — mobile merge) + 7 principle/operational files
- ~272 findings in reference library (unchanged — merge consolidated, did not add/remove)
- 5 commands: `/cro`, `/cro:audit`, `/cro:build`, `/cro:quick-scan`, `/cro:compare`, `/cro:resume`

---

## 2.1.0 — 2026-03-17

### Mobile CRO Expansion — 9 New Topics, 4-Audit Verified

#### New Reference Docs (3)
- `cookie-consent-and-compliance.md` — 9 findings. Banner architecture, placement, GDPR compliance, consent fatigue, cognitive load. **Tier 1 evidence** (multiple large-N peer-reviewed field experiments including Utz 2019 on a real ecommerce site with 82,000+ users).
- `biometric-and-express-checkout.md` — 8 findings. Digital wallets, passkeys, password friction, biometric speed and trust, generational divide. **Tier 2 evidence** (Stripe A/B testing is methodologically strongest).
- `social-commerce-psychology.md` — 7 findings. Trust transfer, impulse mechanics, platform comparisons, herd effect, cross-generational targeting. **Tier 2/3 evidence** (purchase-intention vs actual-behavior gap; cultural boundary conditions).

#### Expanded Reference Docs (6 existing docs, ~43 new findings)
- `page-performance-psychology.md` — +4 findings (skeleton animation quality, shimmer direction, fidelity requirements, accessibility). Corrected NNGroup threshold and flagged Akamai citation.
- `color-psychology.md` — +2 findings (dark mode CTA/trust badge contrast, dark mode reading performance and sentiment).
- `mobile-conversion.md` — +4 findings (dark mode adoption, WCAG failure rates with ecommerce-platform-specific data, accessibility lawsuits, touch targets and font size).
- `search-and-filter-ux.md` — +4 findings (search-user correlation caveat, zero-results abandonment, mobile filter placement, visual/voice search).
- `post-purchase-psychology.md` — +4 findings (automated push vs blasts, notification fatigue with Wohllebe N=17,500, multi-channel cart recovery cascade, rich media push).
- `eye-tracking-and-scan-patterns.md` — +5 findings (usage vs beauty videos, vertical video, mere presence effect, short-form engagement, gallery placement).

#### Cross-Reference Findings (3)
- `checkout-optimization.md` — +2 findings (accessible checkout design, cart recovery channel cross-reference from post-purchase).
- `social-proof-patterns.md` — +1 finding (social commerce trust transfer cross-reference).
- `cta-design-and-placement.md` — +1 finding (WCAG touch target requirements cross-reference).

#### Routing & Infrastructure
- Added 3 new docs to cluster routing: cookie-consent → context-platform + trust-conversion; biometric → trust-conversion; social-commerce → audience-journey.
- Added 3 canonical section slugs: cookie-consent, express-checkout, social-commerce.
- Updated slug lists in all 3 workflow files (audit, quick-scan, compare).
- Quick-scan now shows all cluster options with descriptions when prompting user.
- Quick-scan output suggests other clusters and full audit as next steps.
- Planner prompt updated to require inlining implementation specifics (hex codes, ARIA attributes, regulatory requirements) since builder cannot access reference docs.
- Verification checklist expanded from 9 to 12 items (cookie consent, express checkout, dark mode contrast).

#### Evidence Quality
- All 9 topics verified through 4-audit triangulation: Critical Audit (bias/methodology), Verification Audit (87 claims, structured review), Agent Verification (URL-level source checking), Sonnet Audit (54 claims, direct URL fetching).
- 8 factual errors corrected in source data before writing (wrong authors, wrong journals, wrong stats, wrong thresholds, citation laundering flags).
- No ecommerce-specific RCTs exist across any of the 9 topics (or the existing 15 reference docs). This is a structural feature of the field, not a gap we can fill. All conversion evidence is directional.
- Evidence quality tiers applied: Tier 1 (cite with confidence), Tier 2 (cite with caveats), Tier 3 (directional only), Tier 4 (do not cite — removed).
- Cross-reference report documenting all audit findings at `docs/audit files/cross-reference-report.md`.

#### Known Limitations
- Quick-scan defaults to one cluster; new topics only surface via --cluster override or full audit.
- Social commerce reaches product pages only via cross-reference in social-proof-patterns.md, not the full standalone doc.
- Push notification cart recovery reaches cart pages only via cross-reference in checkout-optimization.md.
- Dark mode findings split across visual-cta and context-platform clusters; cart pages miss mobile adoption context.
- No A/B comparison mechanism between v2.0 and v2.1 audit quality.

#### Totals
- 18 domain reference files (was 15) + 7 principle/operational files
- ~272 findings in reference library (was ~229)
- 3 new standalone docs, 9 existing docs modified, 5 workflow/skill files updated

---

## 2.0.1 — 2026-03-12

### Reference Library Audit & Accuracy Pass

#### Data Quality
- Removed 4 unverifiable statistics: "1617% sales increase" (WordStream), "FOMO = 60% of impulse purchases" (Research & Metric), "rounded corners 17-55% CTR" (no primary source), "BNPL 78% conversion improvement" (vendor-reported)
- Replaced 7 statistics with stronger, independently sourced data (BNPL, Shop Pay, coupon behavior, Q&A conversion, Amazon recommendations, Google blue experiment, Norton trust seal)
- Reconciled 4 cross-file metric inconsistencies (desktop vs mobile conversion, mobile cart abandonment, checkout form fields, website error abandonment)
- Added freshness warnings to 4 dated data points (Hoober 2013, Baymard search 2014, trust seal demographics mid-2010s, Monetate Q4 2017)

#### Ethics Gate Expansion
- Updated FTC penalty to 2025 inflation-adjusted amount ($53,088)
- Added Amazon Prime FTC settlement ($2.5B, Sep 2025) — largest dark patterns enforcement action
- Added 7 missing regulations: EU AI Act, GDPR, CCPA/CPRA ADMT, US state privacy laws (20+ states), CA SB 243, FTC Click-to-Cancel vacatur, EU DSA Art 25 enforcement precedent (X/Twitter €120M fine)

#### Citation Architecture
- Created `docs/citations.md` — single-file citation index (~350 source URLs) for human verification
- Stripped all URLs from 13 reference files to reduce agent context token usage
- Researched and added DOI links for 20 academic sources in pricing-psychology.md
- Researched and added URLs for 29 named sources in mobile-conversion-psychology-principles.md

#### Totals
- 229 findings in reference library — 0 deleted, 12 modified, 4 bad stats removed
- ~305 URLs extracted from reference files, ~50 URLs researched and added
- Net impact: stronger data, current legal compliance, lower agent context cost

## 2.0.0 — 2026-03-11

### Breaking Changes
- `/ecommerce-conversion-psychology` replaced by `/cro` command family (deprecation stub retained)
- Baton file format changed from single `docs/cro-action-plan.md` with HTML markers to per-engagement directories under `docs/cro/`
- References, workflows, platforms, and templates moved from `skills/ecommerce-conversion-psychology/` to plugin root

### New Commands
- `/cro` — Router/help menu. Lists all CRO commands. Auto-discovered when users mention CRO.
- `/cro:audit` — Full 4-phase CRO relay on an existing page (audit, plan, review, build)
- `/cro:build` — Full 4-phase relay from scratch with structured intake
- `/cro:quick-scan` — Single-cluster quick scan, 3-5 quick wins, one-and-done
- `/cro:compare` — 1:1 competitor comparison with gap analysis

### New Features
- **Multi-file baton system** — Per-engagement directories with separate files per phase. No more HTML comment markers.
- **Severity filtering** — `--min-priority` flag filters findings by priority level (critical/high/medium/low)
- **Cost/impact scoring** — Action plan table includes Effort and Impact columns
- **Platform-specific templates** — Shopify and Next.js platform references loaded by the builder
- **HTML report export** — Self-contained report with inline CSS, WCAG AA compliant, print-friendly
- **Progress memory** — Re-auditing a previously audited URL shows what changed since last audit
- **A/B test scaffolding** — Generates test hypotheses, variant code, and measurement plans per platform
- **Screenshot/URL-based audit** — Visual audit via agent-browser when source code unavailable
- **Competitor comparison** — Side-by-side scoring with gap analysis and ethics checking

### Agent-Native Improvements
- `--auto` flag for checkpoint-free automation (audit, build)
- Structured argument acceptance for all commands
- `--export-report`, `--ab-scaffold`, `--cluster`, `--engagement-id` flags
- Deterministic `--auto` path with mandatory safety gates

### Security
- HTML report includes CSP header blocking all script execution
- All report content HTML-entity-escaped before insertion
- URL validation with IPv4/IPv6 SSRF prevention (references/url-validation.md)
- Ethics gate passed to compare workflow for synthesized recommendation validation

### New Reference Files
- `references/url-validation.md` — SSRF prevention rules
- `references/platform-detection.md` — Platform detection heuristics with .liquid disambiguation
- `references/ab-testing-patterns.md` — A/B testing methodology and patterns
- `platforms/shopify.md` — Shopify OS 2.0, Liquid patterns, Shop Pay, Checkout Extensions
- `platforms/nextjs.md` — App Router, RSC boundaries, Server Actions, middleware A/B testing

### Architecture
- Nested directory namespacing (`skills/cro/audit/SKILL.md` → `/cro:audit`)
- Shared infrastructure at plugin root (references, workflows, platforms, templates)
- Canonical SECTION slug registry for deterministic finding matching
- meta.json with `schema_version: 1` for future migration safety
- Atomic go-back protocol (write-then-rename)
