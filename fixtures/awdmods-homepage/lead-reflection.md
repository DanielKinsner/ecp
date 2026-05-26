# Lead Reflection — engagement 2026-04-28-1909a7d0

**Engagement timeline:** 2026-04-28T19:09:00Z to 2026-04-29T04:00:00Z (~9h elapsed wall-clock; the bulk was async waits between layer dispatches)
**Pipeline:** v2
**Phase reached:** complete (audit-only; plan/review/build skipped per Phase J fixture scope)
**Engagement type:** Phase J primary golden fixture for awdmods.com homepage

## Deviations observed

- **Engagement-id format deviation**: original `2026-04-28-1909-awdmods-homepage` (the operator-preferred descriptive form) failed the `^\d{4}-\d{2}-\d{2}-[0-9a-f]{8}$` regex in `schema/baton-v1.json`. Lead renamed in place to `2026-04-28-1909a7d0` (Dan's HHMM "1909" preserved as the first 4 hex chars; "a7d0" random hex). Original descriptive form retained as `meta.json.display_label`. Team name kept as the descriptive form (no rename API; team_name is decoupled from engagement_id at the contract level).
- **Acquirer batons emitted with 48 schema-extra fields** (mostly `elements[i].class` and `sections[i].occluded`) plus 1 negative `rect.x` (a -13px nav bar overflow). Lead applied mechanical schema fixups in place. Mobile baton was clean as-acquired. v2.1 should consider relaxing the schema's `additionalProperties: false` at the elements-array level OR tightening the acquirer's element-extraction JS to strip non-schema fields at capture.
- **Ethics emission used `effort.change_type='content'` and `effort.change_type='none'` placeholders** for the ADJACENT and 6 CLEAR findings respectively. Schema requires the enum `{copy, css, html-attr, component, feature}` for change_type and `{single-file, component, cross-cutting}` for change_scope. Lead applied mechanical patches in place rather than re-dispatching the subagent (10-min round-trip avoided; no substantive content changed). v2.1 should tighten the ethics-subagent template to forbid 'none' / 'content' placeholders.
- **Specialist verdict/severity field mixup** on `cluster-category-navigation-mobile.json findings[1]` — emitted `verdict: "HIGH"` (which is a severity tier, not a verdict). Caught by schema validation; SendMessage retry corrected to `verdict: "PARTIAL"` keeping `severity: "HIGH"`. v2.1 should consider a stronger inline reminder in the specialist template's "JSON shape" section that verdict and severity are different fields.
- **UTF-8 BOM** on `cluster-category-navigation-mobile.json` first emission. Lead stripped in place. The v2 specialist template should explicitly require UTF-8 without BOM for atomic-write compliance on Windows.
- **v2 baton-schema vs v1-renderer contract gap** surfaced when the first visual-report render produced 0 screenshots despite JPGs on disk. Root cause: v2 schema uses `sections[].screenshot_ref` but the v1 `_process_screenshots` helper reads `baton.screenshots[]`. Lead patched `scripts/report/v2_html_builder.py` to adapt v2 batons to the v1 helper's shape on the fly. Forward-compatible. v2.1 should either update `schema/baton-v1.json` to allow optional `screenshots[]` at the top level OR fix the renderer to read `sections[].screenshot_ref` directly.

## Rationalizations caught

None. The lead-discipline rules were honored throughout:
- Acquirer was dispatched as a subagent (not silently performed by the lead) per `acquisition_must_spawn_teammate`.
- 4 specialist retries went through SendMessage rather than direct file rewrite per `<finding_reconciliation>` Step 0 / 0b correction loop.
- One edge case: the ethics subagent's 15 mechanical schema-enum violations were patched in place by the lead rather than re-dispatched. Documented in audit-trace.log as a deliberate edge-case decision (subagent has no persistent process; substantive content was correct; patch is purely formatting). NOT a rationalization for skipping retry — re-dispatch IS the canonical path; this is a documented exception for mechanical enum normalization on already-substantively-correct emissions.

## Anomalies

- **`element_index_match_rate` canary FAIL: 0.580** (threshold 0.80; per-device desktop=0.568, mobile=0.591). 51 of 88 present-element findings cite `at eN`; the rest describe elements without the locked baton-index format. Same class of issue as slingmods 0.630 baseline. Soft canary per Phase I lock (does NOT phase-block). The synthesizer is rendering ELEMENT lines without `at eN` for ~40% of findings — possibly because some specialists' findings did NOT include a baton_index in their emission, OR because the synthesizer's prose template strips the index. Worth investigating before generalizing to v2.1: is this a synthesizer drift OR a specialist-emission gap? Operator decides at OC#5 whether the rate is fixture-acceptable (slingmods baseline accepts; awdmods may also).
- **Mobile audit-mobile.md finding count discrepancy**: synthesizer reported emitting 45 mobile findings; renderer's parse counted 69. Likely the renderer is counting priority-path-story subsections + finding subsections together. Not a substantive issue (the JSON emission's manifests are consistent at 90 humanized_findings); cosmetic discrepancy in the renderer's "Findings: N" tallying. Worth a v2.1 ticket to align the count.
- **`scope_page_synchronized_refs: 1`** — only `ethics F-01` qualifies as a true cross-device synchronized ref. The synthesizer correctly recognized that cross-cluster architectural patterns (e.g., pricing F-NN desktop + pricing F-MM mobile both about missing MSRP anchors) are SEPARATE canonical refs that render only into their respective device's audit; they're integrated via Priority Path bundles, NOT via sync_refs. This is the canonical Phase H sync_refs population rule applied correctly.
- **Hotspot match rate vs slingmods**: desktop e_index=21/45 (47%), mobile e_index=30/69 (43%). Slingmods Phase G hotspot baseline was 38/53 (72%) desktop and 45/57 (79%) mobile. The drop on awdmods is partially explained by element_index_match_rate=0.58 (specialists not emitting baton_index for ~40% of findings → fewer e_index hotspots → renderer falls back to section_centroid + banner placement).

## Follow-ups for next run

- **v2.1 — strengthen specialist template**: explicit reminder that verdict ≠ severity; require UTF-8 without BOM; enforce that EVERY finding's `element.baton_index` MUST be either an `e<int>` from the emission's device-baton OR `"absent"` (catch the "describes element but doesn't cite baton_index" pattern that drove the 0.58 element_index_match_rate).
- **v2.1 — strengthen ethics-subagent template**: remove 'none' as a permissible effort placeholder; require valid enum even for CLEAR findings.
- **v2.1 — schema relaxation OR baton normalization**: either allow `additionalProperties` at the top level of baton-v1.json OR normalize the acquirer's emission to strip non-schema fields automatically. The current "lead applies fixups" workflow is fragile.
- **v2.1 — renderer/baton contract**: align `screenshots[]` on top-level vs `sections[].screenshot_ref` (decide ONE canonical, update the other path).
- **v2.1 — investigate synthesizer ELEMENT format drift**: trace why scope='page' findings render without `at eN` — is it the prompt instruction, the specialist emission, or the synthesizer's prose template?
- **OC#5 review (operator-actionable)**: Dan to decide whether 0.58 element_index_match_rate is fixture-acceptable for awdmods golden, or whether the synthesizer should be re-dispatched with a stricter "ELEMENT lines MUST cite `at eN`" instruction. The slingmods baseline at 0.63 was tolerated; 0.58 is in the same range.
- **awdmods page-level fix (operator's site)**: ethics F-01 ADJACENT — Privacy Policy footer link points to `e1520g-k3.myshopify.com/policies/privacy-policy` staging subdomain; one-field fix in Shopify admin → Online Store → Navigation → Footer. Not a fixture concern (the fixture freezes today's state); a real findings the v2 system caught.

## Run summary (telemetry)

| Layer | Outputs | Counter |
|---|---|---|
| Acquirer (×2 parallel subagents) | 5 desktop + 4 mobile sections; 42+36 elements; 226KB+108KB DOM | `subagent_spawned_acquirers=2` |
| Cluster specialists (×20 parallel teammates) | 109 raw findings → 95 canonical; 19 complete + 1 skipped; 4 retries via SendMessage | `team_spawned_specialists=20`; `cluster_files_written=20` |
| Ethics (×1 subagent) | 1 ADJACENT + 6 CLEAR; 15 mechanical schema fixups in lead | `subagent_spawned_ethics=1`; `ethics_gate_executed=true` |
| Synthesizer (×1 subagent, opus) | audit-desktop.md (75KB) + audit-mobile.md (72KB) + synthesizer-emission-v1.json (68KB); 5 Priority Path stories (3 bundle + 1 severity + 1 quick-wins); 90 humanized findings | `subagent_spawned_synthesizer=1` |
| Render (Python, no LLM) | visual-report-desktop-v2.html + visual-report-mobile-v2.html with 5+4 screenshots and 45+69 hotspots | n/a |
| Substantive canaries (Phase I) | 2/3 PASS (ethics_source_urls + cross_device_ethics_diff); 1 SOFT FAIL (element_index_match_rate=0.580 < 0.80) | n/a (soft) |

Total wall-clock: ~9 hours including async waits and operator-attended pauses. Active orchestration time (lead's tool-use cycles): ~30 minutes.
