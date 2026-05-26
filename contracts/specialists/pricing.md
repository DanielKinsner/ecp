# Pricing Specialist (v2)

Per-cluster parameter file for the **pricing** specialist. Combined with the shared template body in [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) and per-engagement variables (cluster-context path, baton path, screenshots), this file produces the final dispatch prompt.

Phase B authors this as the proof-of-concept cluster. Phase C will add `contracts/specialists/{visual-cta,trust-credibility,checkout-flows,performance-ux,product-media,category-navigation,content-seo,post-purchase,audience}.md` following the same shape.

## Parameters

```yaml
cluster: pricing
references:
  - pricing-psychology
  - charm-pricing
  - price-anchoring
  - bundle-pricing
  - discount-framing
  - free-shipping
  - tiered-pricing
  - bnpl-payment
  - price-transparency
  - scarcity-urgency
  - competitive-positioning
surface_vocabulary:
  - price-block
  - msrp-anchor
  - discount-banner
  - bundle-block
  - bnpl-marker
  - shipping-threshold
  - tier-table
  - scarcity-marker
  - cost-breakdown
  - comparison-block
target_finding_count: 3-6
```

The 11 reference files are sourced from [`contracts/cluster-routing.md`](../cluster-routing.md) "The 10 clusters" table for the pricing row. All 11 live at `${CLAUDE_PLUGIN_ROOT}/references/<file>.md`. The specialist reads them all — sonnet at 1M context handles the full pricing pack without context pressure, and the v2 attention-bandwidth argument (§5.3 of the brainstorm) is exactly that cognitive concentration on a focused reference set beats spread attention across all 10 cluster packs.

## Cluster guidance

The block below renders into the template at the `{{cluster_guidance}}` slot. It surfaces patterns the specialist should bias toward and edge cases the template body does not cover.

```
## Cluster guidance — pricing

Pricing findings are strongest when the page surfaces specific number / framing patterns the references address. Bias toward these:

- **Charm pricing** ($X.99 vs $X.00) — character-count effect, left-digit bias. If the price ends in .99 or .95, that's a deliberate pattern; note it as observed-as-deliberate or critique it if the brand context suggests rounded pricing would read more premium.
- **MSRP anchoring** — strikethrough above the live price, "compare at" framing, "was/now" treatments. Absence of any anchor on a SKU >$50 is a high-leverage finding (price reads as expensive in isolation).
- **Bundle anchors** — complete-the-build kits, "frequently bought together," tiered SKU presentation. A bare single-SKU page in a category that typically bundles is missing leverage.
- **BNPL markers** — Klarna, Afterpay, Affirm, Shop Pay Installments. Presence at the price block lifts conversion on $100+ items; absence on a higher-ticket SKU is a finding.
- **Free-shipping framing** — threshold-with-progress ("$12 from free shipping") vs naked threshold ("Free shipping over $99") vs implicit ("Free shipping" with no condition). The framing pattern matters more than whether shipping is actually free.
- **Scarcity / urgency tied to price** — "X left at this price," countdown timers on discounts, "limited inventory" on the price element. Honest scarcity (real stock counter) is fine; fabricated countdowns that reset on reload are an ethics-adjacent finding the ethics subagent will surface separately — describe the urgency framing in your finding without invoking ethics terms.
- **Tiered pricing visibility** — quantity discounts, volume tiers, member pricing. If tiered offers exist but aren't surfaced at the primary price block, that's a finding.
- **Price transparency** — total cost (price + shipping + tax) visible before checkout, vs surprise costs at the cart drawer. Hidden costs are a high-conversion-impact finding.

Edge cases:

- **Quote-only pages (B2B, custom configurators).** No price displayed by design. Emit `status: "skipped"` with `skip_reason: "Page is quote-request driven; no price displayed for pricing cluster to evaluate."` Do not force a finding on price absence when the absence is the page's commercial model.
- **Variant-driven pricing.** If price changes with variant selection (e.g., "$69.95 — $129.95" range or dynamic update on color/size), evaluate the default-state price (what visitors see before configuring). The configurator capture is in `baton.configured_state` if present; cite both states if relevant.
- **Promotional overlays.** If a discount banner / free-shipping bar / promo modal is present in the baton's `capture_state.overlays_detected[]`, treat the underlying price as the canonical price and the overlay framing as a separate finding. Don't double-count — a "30% OFF" banner above a strikethrough price is one anchoring framing, not two.
- **Multi-currency / non-Western markets.** If `page_head.hreflang[]` or visible currency markers (₹, ¥, ₩, R$, etc.) suggest a non-Western market, the `audience` cluster will likely surface localization findings. Stay in your pricing lane: charm-pricing rules differ by locale (e.g., .99 conventions are weaker in JP/KR), so cite locale-aware references when relevant.

When emitting PASS findings: a clean pricing setup is one with strong anchoring (MSRP or bundle), present BNPL or transparent shipping framing, charm-or-rounded pricing applied deliberately. Note what's working — the synthesizer's Priority Path Bundle mode uses PASS findings to balance the deliverable narrative.
```

## Reference file list (rendered into template)

For substitution into `{{reference_file_list}}`:

```
- `pricing-psychology.md` — overarching pricing-decision framing
- `charm-pricing.md` — $X.99 / $X.95 / .00 patterns
- `price-anchoring.md` — MSRP strikethrough, comparison framing
- `bundle-pricing.md` — kit anchoring, complete-the-build
- `discount-framing.md` — sale presentation, "was/now"
- `free-shipping.md` — threshold framing, progress bars
- `tiered-pricing.md` — quantity discounts, member tiers
- `bnpl-payment.md` — Klarna / Afterpay / Affirm presence
- `price-transparency.md` — total-cost visibility, surprise-cost framing
- `scarcity-urgency.md` — limited-stock, countdown framing tied to price
- `competitive-positioning.md` — comparable-product framing
```

## Cross-references

- [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) — shared template body this file parametrizes
- [`contracts/cluster-routing.md`](../cluster-routing.md) — canonical reference list source
- [`schema/cluster-emission-v1.json`](../../schema/cluster-emission-v1.json) — output shape
- [`schema/finding-v1.json`](../../schema/finding-v1.json) — per-finding shape
- [`scripts/test-specialist.py`](../../scripts/test-specialist.py) — harness that combines this file + template + per-engagement vars
