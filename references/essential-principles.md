# Essential Principles — Universal Rules (Summary/Fallback File)

> **⚠️ DO NOT CITE THIS FILE IN AUDIT FINDINGS.** This is a distilled summary of principles drawn from other reference files. It does NOT carry local citations, methodology notes, or Evidence Tiers. Auditor citations (↳ footer on findings) MUST point to the primary reference file where the principle originates (e.g., `cta-design-and-placement.md` for CTA principles, `trust-and-credibility.md` for social proof, `mobile-conversion.md` for touch target standards). This file exists as a quick-reference companion for `/ecp:build` when no domain cluster refs are loaded and for orientation only.
>
> **Integration note:** `/ecp:build` loads this file as a fallback when no domain-specific cluster references are loaded. For cluster auditors, the domain-specific reference files contain the same principles with full evidence, citations, and worked examples — those are the primary references.

These provide meaningful guidance even when no domain-specific reference files are loaded. Each is distilled from the strongest evidence across all domains. For full evidence, citations, and boundary conditions, consult the primary reference file noted in each section.

## Visual Hierarchy & CTA

1. **Contrast drives CTA performance, not color.** No specific color "converts better." The highest-contrast element on the page gets clicked. (VWO meta-analysis; HubSpot red/green test = 21% lift was contrast, not hue)
2. **One primary CTA per viewport.** Multiple competing CTAs reduce conversion. Secondary actions must be visually subordinate.
3. **CTA labels must be specific and honest.** "Add to Cart — $49" outperforms "Submit." Personalized CTAs convert 202% better than generic (HubSpot, 330K CTAs).

## Trust & Social Proof

4. **Place trust signals near conversion points, not in the footer.** Trust badges near Add to Cart or payment form reduce anxiety at the decision moment. 2-3 badges outperform 8+.
5. **Five reviews = 270% conversion lift.** The first 5 reviews matter most. Optimal displayed rating is 4.0-4.7 stars — perfect 5.0 triggers skepticism. (Spiegel/Northwestern)
6. **Specific social proof beats vague claims.** "Sarah from Denver bought this 2 hours ago" converts ~58% better than "Customers love this product." UGC converts 3-5x vs professional photography.

## Pricing

7. **Show the highest price first (anchoring).** The first number seen becomes the reference point. Show original price, then discount. (Kahneman & Tversky; replicated extensively)
8. **Charm pricing works below $100.** $X.99 triggers left-digit effect. Above $100, round numbers signal quality. Luxury brands should avoid charm pricing.
9. **Total cost transparency prevents abandonment.** 39-48% of abandoners cite unexpected costs. Show shipping, tax, and fees as early as possible.

## Layout & Cognitive Load

10. **Users scan, they don't read.** F-pattern for text-heavy pages, Z-pattern for minimal layouts. Place critical content in the first two fixation points.
11. **Limit simultaneous choices to 3 or fewer (Hick's Law).** More options increase decision time logarithmically. Choice overload is real but context-dependent — expertise and preference clarity moderate the effect.
12. **57% of viewing time is above the fold.** The most important content and CTA must be visible without scrolling.

## Performance & Mobile

13. **Every 0.1s of load time improvement lifts conversion measurably.** 0.1s = 8.4% retail conversion lift (Google/Deloitte). 3 seconds is the abandonment threshold for 53% of mobile users.
14. **Thumb zone placement is critical on mobile.** Bottom-center of screen is the natural thumb resting area. Place primary CTAs there. **Touch-target standards (see `mobile-conversion.md` F6 for full detail):** WCAG 2.2 SC 2.5.8 Level AA requires 24×24 CSS px minimum (with spacing exception); WCAG 2.2 SC 2.5.5 Level AAA requires 44×44 px (not legally required in US private ecommerce). Apple HIG recommends 44pt; Google Material 3 recommends 48dp. **Targets under 24×24 without adequate spacing = legal-risk BLOCK; 24×24 to 44×44 = platform-practice ADJACENT; ≥44×44 = PASS.** Do not conflate the AAA/platform recommendations with the AA legal floor.

## Post-Purchase & Personalization

15. **66% of shoppers feel post-purchase anxiety** (Narvar 2025 State of Post-Purchase Report, 3,461 US consumers). Confirmation emails historically reported >100% open rates (multiple opens per recipient for order-tracking), though that figure is now unreliable post–Apple Mail Privacy Protection — refresh against current-year ESP data before citing a specific percentage. Use confirmation emails for reassurance, not just receipts. Post-checkout upsells convert 3-8% with zero abandonment risk (vendor-aggregate data from Shopify post-purchase apps).
16. **Personalization works when covert, backfires when overt.** "Because you viewed X" triggers creepiness. "Popular in your area" feels like service. Once triggered, creepiness is irreversible — the customer doesn't return.
