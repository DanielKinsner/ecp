# Handoff — role-map re-anchoring in placement repair (2026-07-21)

Autonomous session (Dan at lunch: "make this work better"). Executed the one measured,
untouched opportunity the 2026-07-08 handoff left on the table: **teach
`placement_repair.py` to consult the semantic `anchor-candidates` role map** when its
lexical matcher fails. Hotspot accuracy is the #1 blocker to selling reports; the repair
tool is the pipeline's self-healing pass for gate-flagged misplaced hotspots.

## Why the lexical matcher fails (root cause, plain English)

Finding titles describe **problems** ("Star Rating Touch Target Is 12px"), element
labels are the element's **text** ("4.7 out of 5 stars"). Token overlap between the two
is ~0.0, so the repair gave up and dumped the finding into the manual queue — even
though the anchor-candidates sidecar already *knows* which element is the reviews
widget (`reviews-widget-1 → e10`).

## What landed

`scripts/report/placement_repair.py` + `tests/test_placement_repair_rolemap.py`:

- `infer_roles(finding, marker)` — role intent from (1) an explicit
  `observed_anchor.candidate_id` prefix (strongest — the specialist's own citation),
  else (2) conservative keyword inference over TITLE+element only (the anchor
  text_quote is deliberately excluded — it may come from the wrong anchor).
- **False-friend guards** — the handoff's named trap is pinned by test: "Title Tag" /
  "Meta Title" / "Page Title" SEO findings never grab the visible product-title
  heading (guard tokens: tag/meta/seo/alt/page).
- `decide_match(..., desired_roles=, e_to_roles=, current_e_index=)` — role fallback
  fires ONLY after the lexical path fails, and refuses on every ambiguity: multi-role
  intent, >1 same-slide candidate of the role, off-slide-only candidates, and the
  marker's CURRENT anchor (the gate said it's wrong there — re-asserting it would be
  a no-op repair claiming success).
- Same fail-safe as before: every role rescue lands `section-match` ("Check
  placement") + `re_anchored_unverified`; the `ecp-visual-qa` workflow's vision
  re-verify still decides confirm-vs-revert. Log entries gain an additive
  `via: "role-map" | "lexical"` provenance field (the QA workflow filters on
  `action` only — verified untouched).
- Missing sidecar → behavior identical to before (pure lexical). Present-but-broken
  sidecar → fail-loud `SidecarLoadError` per the canonical loader convention.

## Measured (corpus replay, all 24 engagements × device, deduped per finding)

| | auto re-anchor | flagged to manual |
|---|---|---|
| before (lexical only) | 46 | 734 |
| after (+ role map) | **138 (3×)** | 642 |

Zero regressions: no lexical re-anchor was lost. Sample rescues read correctly
("No MSRP Anchor on $135.99 Floor Mat Price" → element "From $135.99"; "Star Rating
Touch Target" → "4.7 out of 5 stars"; "Search Placeholder Gives No Query Guidance" →
"Search our store"). Replay was read-only — no engagement files were modified.

Suite after change: **1630 pytest passed / 11 skipped; 1137 unittest OK** (both
runners, work box 2026-07-21 — includes local-engagement mojibake cases on top of the
clean-clone floor).

## What this does NOT do

- Does not touch initial placement (`auto_map_markers_v2`) — only the repair pass.
- Does not change any schema, editor contract, or render path — nothing to hand-test
  visually; the effect shows up as fewer "Place manually" items after the next live
  audit's repair phase.
- The 2026-07-08 corpus defect numbers (13% residual) are unchanged by design — those
  are graded from stored review-states, and repair only runs inside a live QA pass.

## Still open (unchanged)

The live `/ecp:audit` gate (CLAUDE.md ⛔ CURRENT TASK), C5 renderer-decision
unification (wants Dan present for visual hand-test), C2/C1-step2/C6, and the §4.2
`generated_expected_zone` render-vs-blank ruling (Dan's call). Next live audit will
exercise this change for real via `ecp-visual-qa`'s repair phase.
