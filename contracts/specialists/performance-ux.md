# Performance UX Specialist (v2)

Per-cluster parameter file for the **performance-ux** specialist. Combined with the shared template body in [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) and per-engagement variables (cluster-context path, baton path, screenshots), this file produces the final dispatch prompt.

Note on cluster scope: despite the legacy name, performance-ux covers **all viewports**, not just mobile. Four of the five reference files (cognitive-load-management, page-performance-psychology, core-web-vitals, media-performance-optimization) are device-agnostic. mobile-conversion.md carries mobile-specific patterns. Findings that apply cross-device should use `scope: "page"`; findings that apply only to one viewport use `scope: "device"`.

## Parameters

```yaml
cluster: performance-ux
references:
  - mobile-conversion
  - cognitive-load-management
  - page-performance-psychology
  - core-web-vitals
  - media-performance-optimization
surface_vocabulary:
  - lcp-element
  - cls-source
  - inp-interaction
  - third-party-scripts
  - hero-image
  - image-loading
  - cognitive-load-block
  - filter-panel
  - form-fields
  - mobile-touch-target
target_finding_count: 4-7
```

The 5 reference files are sourced from [`contracts/cluster-routing.md`](../cluster-routing.md) "The 10 clusters" table for the performance-ux row. All 5 live at `${CLAUDE_PLUGIN_ROOT}/references/<file>.md`.

## Cluster guidance

The block below renders into the template at the `{{cluster_guidance}}` slot. It surfaces patterns the specialist should bias toward and edge cases the template body does not cover.

```
## Cluster guidance — performance-ux

Performance-ux findings span two axes: (1) loading and rendering speed — measured, objective, tied to revenue via multiple industry studies; and (2) cognitive-load and interaction friction — harder to measure, but equally impactful on add-to-cart and checkout completion. Both axes apply on desktop and mobile. Flag `scope: "device"` only when the finding is genuinely viewport-specific; `scope: "page"` when the same technical cause affects all visitors regardless of device.

### Speed and Core Web Vitals

Bias toward these patterns from your reference set:

- **LCP threshold violations** — Good ≤2.5s, Needs Improvement 2.5–4.0s, Poor >4.0s (core-web-vitals.md Finding 1). The hero product image is the LCP element on most PDPs. Check whether the baton shows `fetchpriority="high"` absent on the first above-fold image element; absent `width`/`height` attributes on that element. A missing `fetchpriority` attribute on the hero image is "almost guaranteed going to have an impact on your LCP" (Martin Splitt / Google). Emit `scope: "device"` for mobile-only LCP failures; `scope: "page"` when the same missing attribute affects both device renderings.

- **Never lazy-load the LCP/hero image** — applying `loading="lazy"` to the hero product image is one of the most common and damaging single-attribute errors (media-performance-optimization.md Finding 5, core-web-vitals.md Finding 6). If the baton shows the primary product image carrying `loading="lazy"`, emit a HIGH-severity finding. This is a `scope: "page"` finding — the attribute is in the HTML served to all devices.

- **CLS — Cumulative Layout Shift** — Good ≤0.1, Needs Improvement 0.1–0.25, Poor >0.25 (core-web-vitals.md Finding 1). Common ecommerce causes: images without `width`/`height` attributes, dynamically injected promotional banners or variant-selector elements, late-loading review widgets. CLS causes misclicks (user taps a button that shifts during load) and trust erosion — Swappie reduced CLS 91% and saw 42% mobile revenue increase (core-web-vitals.md Finding 10). A `scope: "device"` CLS finding is appropriate when the shift is only observable at the mobile viewport (e.g., a desktop sidebar collapses to an injected element on mobile); otherwise `scope: "page"`.

- **INP — Interaction to Next Paint** — Good ≤200ms, Needs Improvement 200–500ms, Poor >500ms (core-web-vitals.md Finding 2). INP replaced FID in March 2024 and is harder to satisfy: it measures the worst interaction across the session, not just the first. High-frequency ecommerce interactions are the target surface: variant selector (color/size), add-to-cart, filter/sort controls, image gallery navigation. JavaScript-heavy variant selectors blocking the main thread are the primary cause. Use the baton's `interactions_captured[]` if present. INP failures are `scope: "page"` when JavaScript bundles cause the problem regardless of device; `scope: "device"` when a mobile-only carousel or touch handler is the cause.

- **Third-party script bloat** — SpeedCurve testing found a real ecommerce site went from <1s LCP to 26.82s with all third-party scripts enabled; each script adds ~34ms on average (core-web-vitals.md Finding 8). If the baton's `third_party_scripts[]` or the DOM slice shows 10+ third-party scripts loading on the product page, that is a finding. Note: scripts in the analytics/marketing/personalization category must fire only post-consent under ePrivacy Directive — do not render a judgment on whether this is the case; note the script count and categories observed, and let the ethics subagent handle consent-gate compliance.

- **0.1s = 8.4% retail conversion** — the Deloitte/Google "Milliseconds Make Millions" study (page-performance-psychology.md Finding 1, core-web-vitals.md Finding 4). Use this as the backing citation for why LCP findings are HIGH severity. Vodafone's controlled A/B test: 31% LCP improvement → 8% more sales (page-performance-psychology.md Finding 17 / core-web-vitals.md Finding 5) is the strongest single-study anchor for stakeholder framing in your `why_this_matters`.

- **Image format and lazy-load strategy** — hero/LCP image: `fetchpriority="high"`, no `loading="lazy"`. Gallery images 3+: `loading="lazy"`. Modern format hierarchy: AVIF (~94.9% browser support) > WebP (~96.4%) > JPEG (media-performance-optimization.md Findings 2, 3, 7). File size targets: hero <100KB, gallery <150KB, thumbnails <25KB. If the baton shows a hero image served as a large JPEG without a `<picture>` element, emit a finding. `scope: "page"` for format/compression findings — the HTML is served identically to all devices.

- **Speculation Rules API** — Ray-Ban A/B test: +101% mobile PDP conversion and +156% desktop PDP conversion after implementing prerendering on collection pages (core-web-vitals.md Finding 11). If the page is a collection/category page and no `<script type="speculationrules">` is present, note the opportunity in `notes[]` rather than emitting a FAIL — this is an advanced enhancement, not a baseline defect. Chrome-only caveat applies.

- **CrUX field data vs. Lighthouse lab data** — Google uses real Chrome User Experience Report (CrUX) data for ranking signals, not Lighthouse scores (core-web-vitals.md Finding 9). When evaluating CWV performance, cite the screenshot or baton's `crux_summary` if present; do not confuse a Lighthouse 100 with a passing CrUX profile. If the baton shows a `crux_summary` with any metric in Needs Improvement or Poor, that is credible evidence for a finding regardless of the Lighthouse score. Note: Chrome iOS users do not contribute to CrUX — Safari-heavy audiences may have different real-world profiles than CrUX implies.

- **CWV population pass rate** — in 2024, only 43% of web origins pass all three CWV on mobile and 54% on desktop (page-performance-psychology.md Finding 22 / Web Almanac 2024). This means the majority of ecommerce sites fail on mobile. When framing why a CWV finding matters, note that passing all three on mobile puts a store in the top 43% — a competitive positioning argument, not just a technical metric. Use `scope: "device"` when citing the mobile-specific 43% figure.

- **`fetchpriority` is Baseline-supported — no JS fallback needed** — `fetchpriority="high"` is now supported by Chrome 102+, Edge 102+, Firefox 132+, and Safari 17.2+ (media-performance-optimization.md Finding 12). If the DOM shows JavaScript-based priority detection wrapping `fetchpriority`, note in `notes[]` that the JS guard is unnecessary overhead and can be removed. The HTML attribute alone is sufficient.

- **Rakuten 24 multi-metric CWV improvement** — Rakuten 24's CWV optimization improved CLS by 92.7%, FID by 7.95%, FCP by 8.45%, and TTFB by 18.03%, yielding 33.13% conversion rate increase and 53.37% revenue-per-visitor increase (page-performance-psychology.md Finding 5 / core-web-vitals.md Finding 5 overlap note). Use this alongside the Vodafone study to demonstrate that compound CWV improvements have compounding revenue impact beyond any single metric.

- **CDN delivery** — images served from origin without a CDN add 100–300ms round-trip latency for geographically distant users (media-performance-optimization.md Finding 6). Shopify CDN is automatic; WooCommerce/custom platforms require explicit CDN setup. If the baton or DOM slice shows product images served from the origin domain rather than a CDN hostname, note this in `notes[]` — it is a platform-configuration finding rather than a template-level fix, and the effort score should reflect `change_type: "feature"` + `change_scope: "cross-cutting"`.

- **Progress indicators for checkout operations** — users shown a moving progress bar waited 3× longer than users with no indicator; determinate progress bars (percentage-based) outperform indeterminate (spinner) because they reduce uncertainty (page-performance-psychology.md Finding 3). For any checkout or search-filter operation over 1 second, absence of a progress indicator is a MEDIUM finding. `scope: "page"` — this is a UI pattern affecting both viewports.

### Cognitive load and interaction friction

- **Hick's Law and navigation choice count** — decision time increases logarithmically with number of choices (cognitive-load-management.md Finding 1). Navigation menus, variant selectors, and filter panels are the primary surfaces. Going from 4 to 8 equally-weighted options costs the same cognitive time as going from 2 to 4. If a variant selector shows 12+ swatches of equal visual weight with no promoted default, that is a MEDIUM finding. Note the Scheibehenne meta-analysis (Finding 4): choice overload has a near-zero mean effect across conditions — do not claim "too many options reduces sales" without contextual evidence from the page. Bias toward citing the moderators (preference uncertainty, task difficulty, option similarity) rather than raw option count.

- **Progressive disclosure** — above-fold content should be: product image, title, price, variant selector, Add to Cart CTA. Product description, full specs, reviews, shipping detail belong in accordions or tabs below (cognitive-load-management.md Finding 7). If the page has all specs rendered flat in a single block above the CTA, that is a finding. Use tabs for a few long sections, accordions for many short sections.

- **Scanning patterns: F-pattern vs. layer-cake** — in the absence of strong headings, users default to the F-pattern (cognitive-load-management.md Finding 6). Pages with clear, information-carrying headings shift users to the layer-cake pattern, which is more efficient (Finding 18). If the product page's information architecture uses weak heading text ("Details," "Info") or no headings at all, note it as a MEDIUM finding.

- **Chunking product attributes** — specifications should be grouped by category (Physical, Performance, Compatibility) rather than presented as a flat alphabetical list (cognitive-load-management.md Finding 16). Flat spec lists above 8–10 items are a cognitive-load finding.

- **Element density and working memory** — comparing more than 5–7 product attributes simultaneously is cognitively expensive (Miller's Law, cognitive-load-management.md Finding 5). For comparison tables or pricing tiers, more than 4 tiers or 12 feature rows is a finding (Finding 14). Note that Miller's Law does NOT apply to navigation menus where items remain visible on screen.

- **Animation duration** — optimal UI animation is 200–500ms; below 100ms is invisible, above 1s feels like a delay; animations must render at 60fps (page-performance-psychology.md Finding 10). If the baton or DOM slice shows CSS transitions explicitly set to >600ms on hover or add-to-cart interactions, emit a MEDIUM finding. Use `scope: "page"` — CSS animations affect all viewports.

- **Filter panel friction** — 61% of sites do not promote their most important filters; users confronted with 15+ filter types of equal visual weight experience scanning fatigue (cognitive-load-management.md Finding 19). If the category or collection page shows more than 10 equally-weighted filter options with no promoted subset, emit a MEDIUM finding. The recommended pattern is 3–5 key filters promoted horizontally above a collapsible "More Filters" section. `scope: "page"` — filter panels appear on both viewports, though the layout differs.

- **Baymard filtering defects checklist** — 32% of sites do not display applied-filter summaries; 62% fail to explain industry-specific filter terminology; 64% do not offer all four essential sort options (Price, Rating, Best-Selling, Newest) (cognitive-load-management.md Finding 8). Check the cluster-context DOM slice for: (1) presence of an applied-filters summary bar; (2) sort option count; (3) multi-select within filter categories. Missing applied-filter summary is a MEDIUM finding. Missing all four sort options is a LOW–MEDIUM finding.

- **Checkout form field count** — average checkout has 11.3 fields; 22% of users abandon specifically due to long/complicated checkout; the ideal is 7–8 fields (cognitive-load-management.md Finding 11, mobile-conversion.md Finding 16). If the checkout DOM slice shows more than 10 fields and does not include address autocomplete, emit a HIGH finding on mobile (abandonment amplified) or MEDIUM on desktop. `scope: "device"` if mobile-specific abandonment data drives the finding; `scope: "page"` if the form-field count is the same across both device renderings.

- **Default variant selection** — pre-selecting the highest-converting default variant (typically neutral/black colors) reduces active decisions required (cognitive-load-management.md Finding 12, Finding 13). If the product page loads with no variant pre-selected and the variant selector shows equal visual weight across all options, note it as a LOW finding. The ethical dimension of defaults (pre-checked add-ons) is out of scope for this cluster — describe what you observe and let the ethics subagent evaluate.

- **Mobile scanning: marking pattern vs. F-pattern** — on mobile, the "marking pattern" dominates: eyes remain relatively fixed while the thumb scrolls content past them, processing content sequentially rather than spatially (mobile-conversion.md Principle 2). This means critical conversion information must appear in scroll order, not positioned at spatial offsets. If the mobile DOM shows price or CTA displaced to a right column or floated sidebar rather than in the primary scroll flow, emit a MEDIUM `scope: "device"` finding.

- **Optimistic UI for add-to-cart** — showing add-to-cart success immediately (before server confirmation) moves the perceived latency from the 1s threshold to the 0.1s instantaneous threshold (page-performance-psychology.md Finding 8). If the DOM slice shows no optimistic state indicator (no immediate cart count update, no button feedback) on the add-to-cart element, note this as a LOW finding or in `notes[]`.

### Mobile-specific patterns (scope: device)

These findings apply only when `device == "mobile"`. Emit `scope: "device"` for all of them.

- **Thumb zone and sticky CTA** — 75% of mobile interactions are thumb-driven; the easy-reach zone is the bottom center of the screen (mobile-conversion.md Finding 1). Primary CTAs (Add to Cart, Buy Now) should be in the bottom third or in a sticky bottom bar. If the baton shows the Add to Cart button fixed at the top of the page or only inline with content near the fold, that is a MEDIUM finding. Sticky bottom bars that appear after the user scrolls past the inline CTA increase add-to-cart rate (Finding 18).

- **Bottom navigation vs. hamburger** — visible bottom navigation increases engagement 25–50%; 70% of users prefer it for essential functions (mobile-conversion.md Finding 13). If the mobile DOM shows a hamburger menu as the sole navigation pattern, that is a MEDIUM finding. Reserve the finding for cases where the hamburger genuinely hides the primary navigation (not a secondary overflow menu).

- **Touch target sizing** — WCAG 2.2 AA minimum is 24×24 CSS px (SC 2.5.8); platform best practice is 44×44+ (mobile-conversion.md Finding 6). For audit finding classification: targets below 24×24 with inadequate spacing are a WCAG AA failure; targets 24–44px meet AA but fall below platform best practice. Do not classify sub-24px targets as CRITICAL — that severity tier is reserved for ethics findings. Use HIGH for confirmed AA failures with clear legal exposure.

- **Font size and iOS auto-zoom** — inputs below 16px font size trigger iOS auto-zoom, disrupting checkout flow; 16px is the practical conversion floor for mobile form inputs (mobile-conversion.md Finding 24). If checkout or form inputs show `font-size` below 16px, emit a MEDIUM finding with `scope: "device"`.

- **Digital wallets and checkout friction** — one-click checkout (Apple Pay, Google Pay, Shop Pay) increases mobile spending 28.5%; mobile cart abandonment is 78–80% (mobile-conversion.md Findings 10, 17). If the checkout DOM shows no digital wallet option, emit a MEDIUM finding. `scope: "device"` — this is a mobile-checkout pattern.

- **Gallery thumbnails vs. dots** — 76% of mobile sites use only dot indicators; thumbnails provide information scent that drives more image exploration and higher add-to-cart rates (mobile-conversion.md Finding 20). If the mobile product image gallery shows only dots with no thumbnails, that is a LOW–MEDIUM finding.

- **Swipe and gesture support** — mobile users default to swipe for image galleries even with no affordance (mobile-conversion.md Finding 9). If the DOM slice shows no swipe handler on the gallery element, emit a MEDIUM finding. Check for partial-next-image "peek" as the swipeability affordance.

- **Autofill and input type optimization** — enabling HTML `autocomplete` attributes boosts form completion rates by 25% and speeds form filling by 30%; incorrect input types (using `type="text"` for phone or card number fields) force users to switch keyboards manually, adding 2–4 seconds per field (mobile-conversion.md Finding 14). If the checkout DOM shows form inputs without correct `type`, `inputmode`, or `autocomplete` attributes, emit a MEDIUM finding. Priority fields: shipping address, card number, email, phone. This is `scope: "device"` because the keyboard-switching penalty is mobile-specific.

- **Interrupt-driven mobile sessions require upfront value framing** — mobile shopping happens in fragmented, context-switched moments (commutes, queues, couch-scrolling). The most compelling value proposition must appear in the first viewport; users experiencing the "marking pattern" will not scroll for confirmation they should care (mobile-conversion.md Principle 1). If the mobile first viewport is dominated by a large hero image with no visible price or product name, and the CTA requires scrolling, emit a MEDIUM `scope: "device"` finding noting that the "front-load the purchase decision" pattern is not met.

- **Speed as a checkout trust signal** — 70% of consumers say page speed impacts willingness to buy; slow checkout pages specifically undermine trust at the critical conversion moment (page-performance-psychology.md Finding 7, Finding 19). If the page type is `checkout` and the baton or screenshots suggest slow rendering (above-fold checkout fields not visible in the first screenshot, or render-blocking scripts present in the checkout DOM), frame your `why_this_matters` around the trust dimension, not just the speed metric.

### PASS findings

A clean performance-ux setup on desktop shows: LCP hero image with `fetchpriority="high"` and explicit dimensions, no `loading="lazy"` on above-fold images, AVIF/WebP format via `<picture>`, no third-party script pile-up, progressive disclosure information architecture (image + price + CTA above fold, specs in accordions), appropriately sized touch targets, clear section headings. On mobile additionally: sticky bottom CTA bar, bottom navigation, 16px+ form inputs, visible thumbnails in gallery. Note what is working — the synthesizer uses PASS findings to balance the deliverable narrative.

### Edge cases

- **Headless / JS-rendered pages.** If the DOM slice is largely empty with hydration markers and the baton shows `rendering_type: "ssr-partial"` or `"csr"`, CLS and INP findings may not be inferable from static DOM alone. Note this in `notes[]` and emit what you can observe from the screenshot evidence plus baton element data. Do not force a CWV finding you cannot support with evidence.

- **Video on PDPs.** `<video>` elements without a `poster` attribute render as a black box until metadata loads — if the video is in position 1–2 of the gallery, the black box becomes the LCP element (media-performance-optimization.md Finding 10). Check `poster` attribute presence on any `<video>` element in the above-fold slice. `preload="metadata"` is the correct loading mode; `preload="auto"` is a performance finding.

- **Skeleton screens.** Skeleton screen benefit is highly implementation-dependent: a skeleton that doesn't match the final layout dimensions can actively increase perceived wait time worse than a spinner (page-performance-psychology.md Finding 2, Finding 15). If the DOM shows skeleton loading UI, check whether the skeleton dimensions are reserved to match final content size (presence of explicit `min-height` or `aspect-ratio` CSS). A mismatched skeleton is a MEDIUM finding.

- **Responsive images.** `sizes="100vw"` applied to all images regardless of layout column width negates the bandwidth savings of `srcset` — a 33%-column image getting the full-viewport-width srcset candidate on wide screens is a common hidden performance cost (media-performance-optimization.md Finding 11). If the baton shows product grid images with `sizes="100vw"`, emit a LOW finding.

- **Dark mode and product photography.** Survey data shows 70–82% of smartphone users have dark mode enabled at the OS level (mobile-conversion.md Finding 21). No ecommerce-specific RCT on dark mode conversion impact exists. Do not emit a dark-mode finding based on preference-enablement statistics alone. If the DOM slice shows product images with transparent backgrounds or white product photography that will render poorly on dark surfaces AND the page lacks `prefers-color-scheme` handling, note it in `notes[]` as an observation. Emit a finding only if the screenshot evidence shows visually broken product display in dark mode.

- **Accessibility lawsuits and ecommerce targets.** 95.9% of homepages fail WCAG automated checks; Shopify stores average 75.1 errors per page (mobile-conversion.md Finding 22). 69–77% of ADA digital lawsuits target ecommerce/retail (Finding 23). This context informs severity framing on touch-target and font-size findings — these are not merely UX recommendations but active legal exposure. Frame `why_this_matters` for touch-target and font-size findings accordingly.
```

## Reference file list (rendered into template)

For substitution into `{{reference_file_list}}`:

```
- `mobile-conversion.md` — mobile UX mechanics and conversion psychology: thumb zones, sticky CTAs, bottom navigation, touch target sizing, gesture expectations, mobile checkout friction, digital wallets, gallery thumbnails
- `cognitive-load-management.md` — Hick's Law, Miller's Law, progressive disclosure, F-pattern scanning, layer-cake scanning, chunking, choice overload moderators, filter and form field friction
- `page-performance-psychology.md` — perceived speed and conversion: 0.1s revenue effect, skeleton screens, progress indicators, response time thresholds, optimistic UI, animation duration, LCP-to-sales pipeline, speed-trust relationship
- `core-web-vitals.md` — LCP/INP/CLS thresholds and ranking signals, never-lazy-load rule, third-party script auditing, Speculation Rules API, CrUX field data vs. Lighthouse lab data
- `media-performance-optimization.md` — hero image fetchpriority and preload, lazy-load strategy, AVIF/WebP format hierarchy, responsive srcset and sizes accuracy, file size targets, CLS prevention via explicit dimensions, video poster frames
```

## Cross-references

- [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) — shared template body this file parametrizes
- [`contracts/cluster-routing.md`](../cluster-routing.md) — canonical reference list source and cluster scope definition
- [`schema/cluster-emission-v1.json`](../../schema/cluster-emission-v1.json) — output shape
- [`schema/finding-v1.json`](../../schema/finding-v1.json) — per-finding shape
- [`scripts/test-specialist.py`](../../scripts/test-specialist.py) — harness that combines this file + template + per-engagement vars
