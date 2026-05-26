# Engagement Context — 2026-04-28-1909a7d0

**Purpose:** Phase J primary golden fixture capture for the v2 ECP audit pipeline. This engagement runs the full v2 dispatch chain (acquirer subagent + 20 cluster specialist teammates + ethics subagent + synthesizer subagent + render) end-to-end against the awdmods.com homepage and freezes the outputs as the golden fixture for v2 stability validation.

**Operator:** dannytownkins (online during dispatch)
**Lead model:** opus (claude-opus-4-7)
**Pipeline:** v2 (Phase H dispatch shape policy)

## Target

- **URL:** https://awdmods.com/
- **Domain:** awdmods.com
- **Page type:** homepage (a customer-facing storefront homepage operated by Dan)
- **Devices:** desktop (1920×1080) + mobile (iPhone 14, 390×844 @ 3× DPR)

## Scope

- **Clusters:** all 10 (visual-cta, trust-credibility, pricing, checkout-flows, performance-ux, product-media, category-navigation, content-seo, post-purchase, audience)
- **Specialist dispatches:** 20 (10 clusters × 2 devices)
- **Plan / Review / Build:** SKIPPED (Phase J scope is audit-only fixture freeze)

## Phase J fixture deliverables

After audit completion, the following artifacts are copied verbatim to `fixtures/awdmods-homepage/`:

- `dom.html` and `dom-mobile.html`
- `section-N.jpg` (desktop) and `section-N-mobile.jpg` (mobile)
- `baton.json` and `baton-mobile.json`
- `cluster-{cluster}-{device}.json` × 20
- `ethics-findings.json`
- `synthesizer-emission-v1.json`
- `audit-desktop.md` and `audit-mobile.md`
- `visual-report-desktop-v2.html` and `visual-report-mobile-v2.html`
- `meta.json`
- `lead-reflection.md`
- `audit-trace.log`

## Locked decisions

- `--auto` mode active (no mid-run checkpoint prompts).
- Operator Checkpoint #5 fires at fixture freeze, not mid-audit.
- Substantive canaries (`run_all_canaries`) MUST PASS green for fixture acceptance per the Phase J handoff (`element_index_match_rate >= 0.8` is the operator-visible bar; failure prompts a re-dispatch decision before freeze).
- `cancel.flag` checked at every layer boundary per `contracts/lead-discipline.md` "Cancellation sentinel".

## References

- Phase J handoff: `docs/plans/2026-04-27-phase-j-handoff.md`
- Canonical plan Phase J section: `docs/plans/2026-04-27-feat-ecp-v2-redesign-plan.md`
- Trace assertion canary: `contracts/trace-assertion-canary.md`
- Substantive canaries module: `scripts/assembly/canary_checks.py`
