# Visual CTA Specialist (v2)

Per-cluster parameter file for the **visual-cta** specialist. Combined with the shared template body in [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) and per-engagement variables (cluster-context path, baton path, screenshots), this file produces the final dispatch prompt.

The visual-cta cluster audits the visual and compositional layer of conversion-oriented page surfaces: hero section layout, CTA button design and placement, headline copy and value proposition clarity, color and contrast on interactive elements, eye-tracking scan-path alignment, and page-length/scroll-depth decisions. It does not audit checkout flows (separate cluster) or product image quality (product-media cluster).

## Parameters

```yaml
cluster: visual-cta
references:
  - cta-design-and-placement
  - color-psychology
  - eye-tracking-and-scan-patterns
  - hero-section-psychology
  - headline-copywriting
  - page-length-strategy
surface_vocabulary:
  - hero
  - headline-block
  - subheadline
  - primary-cta
  - secondary-cta
  - sticky-cta
  - trust-signal-strip
  - hero-media
  - cta-microcopy
  - page-scroll-structure
target_finding_count: 4-7
```

The 6 reference files are sourced from [`contracts/cluster-routing.md`](../cluster-routing.md) "The 10 clusters" table for the visual-cta row. All 6 live at `${CLAUDE_PLUGIN_ROOT}/references/<file>.md`.

## Cluster guidance

The block below renders into the template at the `{{cluster_guidance}}` slot. It surfaces patterns the specialist should bias toward and edge cases the template body does not cover.

```
## Cluster guidance — visual-cta

Visual-CTA findings are strongest when grounded in specific observable signals: contrast ratios, scroll positions, character counts, button dimensions, viewport-relative element positions, headline word counts, and named scan-pattern violations. Bias toward these patterns:

**CTA button design**

- Primary CTA contrast: the button must be visually distinct from its surrounding background. The principle is contrast, not color — any high-contrast complementary color works; the brand's own dominant color used for the CTA blends in (Verizon gray-vs-red result; CXL meta-analysis). If you can measure or estimate the contrast ratio from the DOM/screenshot, cite it against the WCAG 4.5:1 text threshold and 3:1 UI-component threshold (WCAG 2.2 SC 1.4.3 and 1.4.11).
- Primary vs secondary CTA differentiation: the primary CTA must have a filled solid background; secondary actions (wishlist, compare, share) must be visually subordinate via ghost/outline or text-link styling. If secondary buttons match the primary in size and fill, flag it — the Jackson's Art Supplies test showed +18.4% conversion rate from differentiating the primary CTA alone.
- Touch target size on mobile: primary CTAs must be at minimum 48px tall; 60px is preferred for "Add to Cart" and equivalent primary conversion buttons. WCAG 2.2 SC 2.5.8 sets 24px as the legal floor — above that floor, Apple HIG (44pt) and Google Material Design (48dp) are the UX minimums. Measure from the baton's element height if available; otherwise estimate from the screenshot.
- CTA copy: name the action and outcome. "Add to Cart" beats "Buy" beats "Go." "Start my free trial" outperforms "Get started." Generic verbs (Submit, Continue, Go, Learn More) are a finding when used as the primary CTA on a product page or hero. Cite NNGroup "'Get Started' Stops Users" for the verb-specificity principle. Check for "my" vs "your" framing on commitment CTAs — first-person framing has a directional advantage though it is context-dependent.
- Disabled CTA states: if the baton shows a disabled "Add to Cart" (e.g., no variant selected), check whether the gating condition is communicated. Baymard found 40-60% of users do not understand why a grayed-out button is unclickable.
- Microcopy adjacent to CTA: a one-line trust statement directly beneath the primary CTA ("Free shipping · 30-day returns") reduces friction at the commitment point. Its absence on a high-consideration product page is a MEDIUM finding.
- Sticky CTA on mobile: if the primary CTA is above-fold only and the page is long enough to require scrolling, the absence of a sticky bottom CTA bar on mobile is a finding. Multiple independent Shopify A/B tests show 5-37% conversion lift; GrowthRock found +7.9% completed orders at 99% statistical significance.

**Color and visual hierarchy**

- Color-blindness rule: if stock/availability, error/success, or sale/urgency state is communicated by color alone (red vs green without text labels or icons), that is a finding. 8% of males of Northern European descent have red-green color deficiency (NIH/NEI). The WCAG SC 1.4.1 "use of color" requirement is the citation.
- Warm vs cool color congruence: warm accent colors (red, orange) increase arousal and suit hedonic/impulse products; cool colors (blue, green) suit utilitarian/considered purchases (Wilms & Oberfeld 2018). When the color temperature of a CTA or hero background appears mismatched with product category, note it — but keep the finding specific to what you can observe on the page.
- Background color and price sensitivity: red or high-brightness backgrounds increase price scrutiny; blue/low-brightness backgrounds reduce it (Hsieh et al., 2018 Journal of Interactive Marketing). If a high-ticket SKU ($200+) is presented on an aggressive red-accent background, note it as a color-pricing mismatch.
- Saturation signals: high saturation reads as potent/effective (strong for cleaning, performance, or functional products); low saturation reads as luxury/sophisticated (correct for premium positioning). Mismatches are findings.
- Dark mode adaptation: if the page has a dark background, check whether CTA button colors and trust badge assets have been adapted. Green "Add to Cart" buttons that pop on white may become muted against dark surfaces. Cite color-psychology.md Finding 21.

**Eye-tracking and scan-path alignment**

- F-pattern vs Z-pattern: text-heavy pages (category listings, search results, PDPs with long descriptions) exhibit F-pattern scanning — the top-left of each content block must contain the key information. Hero-only or minimal-content landing pages exhibit Z-pattern — logo top-left, value proposition top-right or center, CTA at the bottom-right terminal area (Gutenberg terminal area). Flag violations of the expected scan pattern for the page type you are auditing.
- Left-side dominance: product images belong on the left, description on the right (80% of fixations land on the left half — NNGroup). On desktop, a layout that places the product image on the right and text on the left fights the dominant scan direction. On mobile single-column this is not applicable.
- Above-fold attention: 57% of viewing time is above the fold on desktop (NNGroup 2018). The five elements that must be above the fold on a landing page hero: headline (primary value proposition), subheadline, primary CTA, supporting image or video, and at least one trust signal (aggregate review rating or customer count). The trust signal is the most commonly missing of the five. Check whether all five are above the fold on the dominant viewport for the device you are auditing. Use the baton's `is_above_fold` and `scroll_y_at_capture` fields as the source of truth for scroll position claims — do not infer from the screenshot alone.
- Mobile above-fold: on mobile only 44% of viewing time is above the fold vs 57% on desktop (NNGroup). The dominant mobile hero failure is an oversized hero image pushing the CTA below the fold. Check hero image height in the baton and flag if the CTA element's `is_above_fold` is false on a mobile engagement. This is a HIGH severity finding when confirmed.
- Gaze direction in hero images: if a human face or model in the hero image faces toward the camera rather than toward the headline or CTA, that steals attention from the conversion elements (Breeze 2009 eye-tracking, 106 participants). This is a zero-cost optimization — image selection or cropping. Note it as LOW severity unless the hero is the primary above-fold element.
- Banner blindness risk: promotional banners, sale badges, and featured-product carousels that resemble advertising are ignored — Benway & Lane 1998 found 86% of users missed information in ad-like formatting. If the page's primary conversion surface looks like an ad unit (bright borders, animation, standard banner dimensions), flag it.
- Carousel auto-rotation: auto-rotating carousels receive lower engagement than static layouts. Flag auto-rotation on hero carousels as a finding citing the banner-blindness and low-engagement mechanisms.

**Hero section composition**

- 5-second clarity: the primary test for a hero section — can a visitor answer "What does this company sell?" and "Why should I care?" within 5 seconds? If the hero headline is generic (could be placed on a competitor's page with the logo swapped), that is a MEDIUM-HIGH finding. Apply the "could a competitor copy this verbatim?" test.
- Squint test for hierarchy: if you squint at the hero section screenshot until details blur, exactly one element should dominate (headline or CTA button). If two or more elements have equal visual weight, hierarchy is broken. Mention this as a visual hierarchy finding with the squint test as your reasoning.
- Five minimum above-fold elements: headline, subheadline, primary CTA, supporting image/video, trust signal (see above). Missing any single element is a finding at the appropriate severity (trust signal = MEDIUM; missing CTA = HIGH; missing headline = CRITICAL-adjacent / HIGH).
- Hero image type: product-in-use or in-context photography outperforms studio white-background in hero positions (NNGroup authentic vs stock research). Generic stock images (people shaking hands, diverse team smiling at laptop) are treated as decorative noise — NNGroup eyetracking confirms. Flag generic stock imagery in hero positions as a LOW-MEDIUM finding.
- Hero image gaze direction (see eye-tracking section above).
- Background video in hero: hero background video only earns its place when motion communicates something a static image cannot. Check whether a poster image fallback is present, whether the video is muted and uses `playsinline`, and whether the video is compressed adequately. A hero video that is the LCP element and is not given `fetchpriority="high"` is a performance-conversion finding.
- Mobile hero text budget: hero headlines exceeding 40 characters wrap to 3+ lines on 375px-wide devices and push the CTA below the fold. Flag oversized mobile headlines when confirmed by the baton's mobile screenshot data.

**Headline and copy**

- Specificity over vagueness: quantified headlines ("Save 10 hours/week") outperform vague claims ("Save time") consistently across practitioner A/B tests. Flag headlines that use only generic modifiers (fast, easy, great, premium, best) without quantification or specific differentiators. This is a copy change — effort `change_type: "copy"`.
- Benefit-before-feature: the headline should communicate the outcome, not the specification. "Sleep better tonight" beats "Memory foam mattress." Apply the "So What?" test to visible headlines: if the headline states a feature, does the subheadline translate it to a benefit? If not, that is a finding.
- Value proposition completeness: a complete value proposition has relevance (what problem does it solve), quantified value (how much better), and differentiation (why this vs competitors). A headline failing to differentiate from competitors is the most common gap. Cite headline-copywriting.md Finding 3.
- Headline length: 6-12 words is the practitioner-validated sweet spot for above-fold headlines (Outbrain/Chartbeat 2M headline analysis). Shorter headlines often lack sufficient information; longer ones exceed easy scanning range. Apply to the observed headline character and word count.
- Subheadline function: each subheadline should serve exactly one of four functions — mechanism, differentiator, risk reversal, or authority/specificity. A subheadline that repeats the headline in different words adds no conversion value. Flag it.
- CTA verb quality: strong action verbs (Get, Start, Try, Claim, Download, Join) outperform weak verbs (Submit, Go, Click Here, Learn More, Continue). Cite NNGroup "'Get Started' Stops Users" and "Better Link Labels."
- CTA label honesty: the CTA label must accurately describe what happens next. If "Add to Cart" triggers a subscription modal, a survey, or a redirect to a different flow, that is a deceptive-experience finding within your cluster's frame. Cite Baymard Institute Finding 13 — 73% of users were surprised and 41% voiced frustration when a generic CTA led to an unexpected flow.

**Page length and scroll strategy**

- Consideration-level matching: page length should match purchase risk. A $20 impulse product needs 1-2 screenfuls; a $200+ considered purchase needs as many screenfuls as it takes to address all real buyer objections. Flag pages that appear truncated relative to product price and complexity — this is a "page too short for consideration level" finding. Cite page-length-strategy.md Finding 1.
- CTA cadence on long pages: for pages exceeding 3 screenfuls of content, there should be a CTA opportunity at least every 2 screenfuls (Unbounce/Oli Gardner practitioner rule). Check the baton's element list for CTA occurrences and flag pages where the CTA density is too sparse relative to page length. Use baton element types and scroll positions to estimate cadence.
- Scroll depth decay: 74% of viewing time is in the first two screenfuls (NNGroup 2018). Content appearing at screen 8+ is seen by fewer than 10% of visitors. This informs finding severity — a trust signal buried below screen 6 is effectively invisible to most visitors and should be surfaced earlier. Cite page-length-strategy.md Finding 3.
- Narrative arc: a long landing page should follow problem → solution → proof → CTA structure. A page that opens with a feature list before establishing the problem the product solves will underperform even if the individual elements are good. Note arc violations as a MEDIUM structural finding.
- Pattern interrupts: on long pages where all sections share the same visual layout (same background, same text/image ratio throughout), attention decays faster. If the screenshot sequence shows a visually monotonous page, note the absence of pattern interrupts (alternating layouts, color-band sections, pull quotes). Cite page-length-strategy.md Finding 6.

**Edge cases**

- Homepage hero vs PDP: the five-element above-fold rule applies most strictly to dedicated landing pages and PDPs receiving cold or paid traffic. A homepage hero for an established brand with strong repeat traffic has different constraints — the navigation provides brand context that a standalone landing page lacks. Note the page type in your findings.
- Single-product vs category pages: the CTA hierarchy rules (primary solid-fill, secondary ghost) apply most strictly to PDPs. Category pages legitimately have many equal-weight CTAs (product cards) — flag visual hierarchy issues at the product-card level only if the page's primary CTA (e.g., a featured product or hero unit) lacks differentiation.
- No headline or CTA present: if the page routed to this cluster has no above-fold headline or no CTA at all (e.g., a brand page, a contact page, a purely editorial page), emit `status: "skipped"` with `skip_reason` explaining the absence. Do not force CTA findings onto a page whose commercial model does not include a direct purchase CTA.
- Quote-only or B2B configurator pages: if the page has a "Request a Quote" or "Contact Sales" CTA instead of "Add to Cart," evaluate the CTA design principles as they apply to that model — contrast, copy specificity, above-fold visibility — but do not cite "Add to Cart"-specific benchmarks. Adapt the finding to the actual CTA present.
- Mobile vs desktop device: many above-fold findings are device-specific. A CTA that is above the fold on desktop but below the fold on mobile should be flagged with `scope: "device"` and include the baton's `scroll_y_at_capture` for the mobile element to satisfy the visual-position-finding schema rule. Never make an above/below-fold claim without citing a `scroll_y` anchor.

**When to emit PASS findings**

Emit a PASS finding when:
- The primary CTA is clearly differentiated (filled, high-contrast color, visually dominant over secondary actions).
- The hero headline is specific, benefit-led, and contains a measurable claim or named differentiator.
- All five above-fold elements are present and confirmed above-fold by the baton's element data.
- On mobile, the primary CTA is confirmed above-fold or a sticky CTA mechanism is present.
- Color usage respects WCAG contrast thresholds and does not use color as the sole state indicator.
PASS findings should name the specific pattern that is working, not just state "this is good." A clean visual-CTA setup enables the synthesizer's Priority Path Bundle mode to build a balanced deliverable narrative.
```

## Reference file list (rendered into template)

For substitution into `{{reference_file_list}}`:

```
- `cta-design-and-placement.md` — CTA button design, copy, placement, touch targets, sticky CTAs, and A/B test evidence
- `color-psychology.md` — contrast vs color myths, brand-color congruence, saturation, cultural associations, WCAG color requirements
- `eye-tracking-and-scan-patterns.md` — F-pattern, Z-pattern, Gutenberg terminal area, above-fold attention distribution, left-side dominance, banner blindness, scan patterns by page type
- `hero-section-psychology.md` — 5-second test, value proposition clarity, above-fold element requirements, hero image types, gaze direction, mobile hero sizing
- `headline-copywriting.md` — headline specificity, benefit-before-feature, value proposition completeness, CTA copy verbs, subheadline functions, readability
- `page-length-strategy.md` — consideration-level framework, scroll depth decay, CTA cadence on long pages, narrative arc structure, pattern interrupts
```

## Cross-references

- [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) — shared template body this file parametrizes
- [`contracts/cluster-routing.md`](../cluster-routing.md) — canonical reference list source for the visual-cta row
- [`schema/cluster-emission-v1.json`](../../schema/cluster-emission-v1.json) — output shape
- [`schema/finding-v1.json`](../../schema/finding-v1.json) — per-finding shape
- [`scripts/test-specialist.py`](../../scripts/test-specialist.py) — harness that combines this file + template + per-engagement vars
