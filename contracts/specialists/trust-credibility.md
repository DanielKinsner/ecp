# Trust-Credibility Specialist (v2)

Per-cluster parameter file for the **trust-credibility** specialist. Combined with the shared template body in [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) and per-engagement variables (cluster-context path, baton path, screenshots), this file produces the final dispatch prompt.

## Parameters

```yaml
cluster: trust-credibility
references:
  - trust-and-credibility
  - social-proof-patterns
  - eeat-product-pages
  - review-collection
  - ugc-integration
  - ugc-reviews-seo
  - accessibility
surface_vocabulary:
  - review-block
  - star-rating-widget
  - verified-buyer-marker
  - ugc-gallery-photos
  - trust-badge-cluster
  - guarantee-policy-block
  - eeat-author-box
  - alt-text-layer
  - color-contrast-layer
  - review-schema-markup
target_finding_count: 4-7
```

The 7 reference files are sourced from [`contracts/cluster-routing.md`](../cluster-routing.md) "The 10 clusters" table for the trust-credibility row. All 7 live at `${CLAUDE_PLUGIN_ROOT}/references/<file>.md`. The specialist reads them all before auditing.

## Cluster guidance

The block below renders into the template at the `{{cluster_guidance}}` slot. It surfaces patterns the specialist should bias toward and edge cases the template body does not cover.

```
## Cluster guidance — trust-credibility

This cluster spans five interlocking surfaces: review display and collection, UGC integration,
E-E-A-T signals on product pages, trust badge placement, and accessibility compliance. Findings
are strongest when tied to specific, named elements on the page rather than to general-policy
observations. Bias toward these patterns:

**Review count and rating display**
- The 0→5 review threshold is the single highest-leverage intervention documented in the reference
  set (Spiegel Research Center, Northwestern, 2017: 270% purchase-likelihood lift). A product page
  with fewer than 5 reviews is a HIGH-severity finding. Products with zero reviews warrant FAIL;
  products with 1–4 reviews warrant PARTIAL (progress toward threshold but below it).
- The 4.0–4.7 star range is the conversion sweet spot. A displayed average of 5.0 stars triggers
  skepticism (Spiegel Gold). If the page shows 5.0 with fewer than 5 reviews, the combination is
  doubly suspect — emit as a single FAIL describing both the count gap and the perfect-rating signal.
- Star-rating display at the price block or above-fold is a distinct finding from star-rating display
  in the reviews section. If the rating widget is present only below the fold or behind a tab, the
  page is missing the above-fold trust anchor. Confirm scroll_y from the baton before claiming a
  position-based finding.

**Verified buyer badges and review authenticity signals**
- "Verified Purchase" or "Verified Buyer" labels on reviews add 15% purchase-likelihood lift
  (Spiegel Gold). If the review display omits these badges despite the site collecting order-verified
  reviews, emit a PARTIAL or FAIL depending on how complete the gap is.
- A full star-distribution breakdown (percentages for 1–5 stars) converts better than showing only
  the aggregate average. Its absence on a product with meaningful review volume is a MEDIUM finding.
- If negative reviews are suppressed or absent despite a review count that should have produced some
  (e.g., 200 reviews all rated 4–5 stars, zero 1-star), flag the pattern neutrally as a display
  design observation without invoking ethics terms — let the ethics subagent handle FTC Consumer
  Review Rule implications (16 CFR § 465.7 review-suppression prohibition).

**UGC photos at the price block and gallery**
- UGC photos integrated into the main gallery (positions 3–6 after professional images) outperform
  UGC placed only in the reviews section, where 40–60% of visitors never scroll (Baymard usability
  research). If customer photos exist in reviews but not in the gallery, emit a MEDIUM finding on
  placement.
- A "N customer photos" callout near the gallery increases both social proof signal and photo
  submission behavior (PowerReviews behavioral data). Its absence when 3+ UGC photos exist is a
  LOW-to-MEDIUM finding depending on catalog context.
- Verified-buyer UGC photos (badge applied to confirmed purchasers' images) are the strongest
  Experience signal for E-E-A-T (Google Quality Rater Guidelines, December 2025 edition). If the
  page shows customer photos with no "Verified Buyer Photo" label, note the gap.
- Gallery ratio guidance: 70% professional / 30% UGC is the practitioner-consensus balance
  (Baymard-derived). A gallery showing zero UGC despite the site having UGC is a notable gap.
  A gallery showing only UGC with no professional packshot is a separate quality concern.

**Trust badge placement and density**
- Placement at the moment of anxiety outperforms generic placement. Badges near the Add-to-Cart
  button and payment fields outperform badges in the header or footer (Baymard: "Customers Perceive
  Only Parts of a Checkout-page as Being Secure," Gold). If badges are present but placed in the
  footer and absent near the CTA, that is the finding — not the presence of badges generally.
- 2–3 badges per section is the practitioner-consensus maximum. Eight or more signals desperation
  rather than security. Count the visible badges in the baton near the CTA zone.
- Badge brand matters more than badge certification. PayPal (67% eye-tracking notice rate, CXL
  Institute) and recognized payment logos (Visa/Mastercard) outperform obscure security seals.
  Unknown seals adjacent to recognized ones borrow credibility from their neighbors. If the page
  carries only unrecognized seals, emit a MEDIUM finding.
- Money-back guarantee framing: positive framing ("We guarantee you'll love it") outperforms
  negative framing ("If unsatisfied, return for refund") by ~21–26% lift (Conversion Rate Experts
  Bronze). If a guarantee badge is present, note whether the copy uses positive or conditional
  framing as part of the observation.
- Return policy: 77% of European consumers base purchase decisions on return policy visibility
  (Signifyd 2024, Bronze); Baymard confirms it as a top checkout-abandonment reducer. If the return
  policy is absent from the product page or only linked from the footer, that is a MEDIUM finding.

**E-E-A-T signals: expertise and experience beyond manufacturer specs**
- Expert editorial content ("Our Expert Take," fitment notes for adjacent vehicle years, installation
  difficulty ratings, known issues the manufacturer does not mention) is documented in Google QRG
  December 2025 as an Expertise signal that also differentiates from competitors using identical
  manufacturer copy (Gold). Its absence on a technically complex or high-AOV product is a MEDIUM
  finding. Its absence on a commodity product is LOW.
- AI-generated product descriptions that are generic, template-uniform across the catalog, or
  factually shallow are an Expertise gap. Observe the description register: if it reads like
  unedited AI output, note this as a trust and E-E-A-T concern — framing it as "description lacks
  product-specific knowledge" rather than invoking AI explicitly in client-facing prose.
- Author attribution on buying guides and category descriptions strengthens the Expertise signal
  (Google QRG, Silver). Missing on editorial content is LOW unless the category is YMYL-adjacent
  (health, safety, finance), in which case treat as MEDIUM.
- Responding to reviews publicly signals active business presence (Proserpio & Zervas, 2017,
  Marketing Science Gold). If the page shows negative reviews with no brand responses, that is a
  LOW finding; if multiple negative reviews go unanswered, elevate to MEDIUM.

**Accessibility — WCAG 2.2 AA**
- WCAG 2.2 AA is the de facto legal standard under ADA Title III (US, 3,117 federal lawsuits in
  2025) and EU EAA (effective 2025-06-28). Findings here are non-optional compliance items.
- Product images missing alt text: 53.1% of web pages fail this requirement (WebAIM Million 2026).
  Formula for good alt text: "[Product Name] — [View/Angle] — [Key Feature or Context]." File-name
  alt text (e.g., "product-img-1234.jpg") is a FAIL. Absent alt text is a FAIL. Emitted severity:
  HIGH for missing alt text on hero or primary gallery images.
- Color contrast: 4.5:1 ratio required for normal text (WCAG 2.2 SC 1.4.3, AA). Common failures:
  light gray price text on white, sale-badge text on red without testing, dimmed "Out of Stock"
  overlays. If contrast is visually suspect, note it as requiring measurement; if clearly below
  threshold, emit as FAIL.
- Color swatches: each swatch must convey its name via aria-label (WCAG SC 1.4.1, Level A —
  color alone cannot be the sole information carrier). Missing aria-labels on color swatches are
  a FAIL, severity HIGH, because they also affect conversion for the ~8% of males with red-green
  color blindness.
- Touch targets: 44×44pt is the practitioner-consensus minimum (Apple HIG); WCAG 2.2 SC 2.5.8
  sets 24×24 CSS px as the legal floor. Gallery navigation arrows and color swatches are the most
  common failures. If screenshot evidence shows clearly undersized targets, emit FAIL at MEDIUM.
- Video captions: WCAG 2.2 SC 1.2.2 (Level A) requires captions for prerecorded video with
  audio. A product demonstration video with audio and no visible caption control is a FAIL at HIGH.
- ARIA gallery patterns: product galleries without proper aria-label, aria-roledescription="slide",
  and keyboard navigation emit as PARTIAL (technical depth is required here; do not emit FAIL
  without direct evidence of broken keyboard navigation from baton or screenshot).
- Reviews behind JavaScript tabs may not be indexed by Google (SearchPilot: ~7.4–7.5% organic
  session uplift from revealing hidden content). If the reviews section appears to be tab-gated,
  emit this as a MEDIUM finding combining SEO and E-E-A-T implications.

**PASS findings**
Emit a PASS when the page demonstrates: ≥5 reviews with a 4.0–4.7 average prominently displayed;
verified-buyer badges present; UGC photos integrated in the gallery; 2–3 trust badges placed near
the CTA; return policy or money-back guarantee visible; alt text present and descriptive on
primary images; adequate contrast on price elements. A clean trust setup is not common — when
you see it, name it. The synthesizer's Priority Path Bundle mode uses PASS findings to balance the
audit narrative.

**Edge cases**
- **New product with zero reviews by design (pre-launch or exclusive drop):** Emit PARTIAL with
  observation that the product page has not yet accumulated social proof and note the 0→5 review
  threshold as the immediate priority. Do not emit FAIL if the launch context makes zero reviews
  expected — but do note the conversion risk.
- **Quote-only or B2B configurator page:** If the page is structured as a quote request with no
  public reviews section, emit status: "skipped" with skip_reason explaining the absence. Trust
  signals for B2B quote pages are a different surface (company credentials, case studies) that may
  not match the review-centric cluster.
- **Multi-locale pages with hreflang signals:** FTC Consumer Review Rule implications are US-only;
  EU Omnibus Directive and DSA apply to EU-facing pages. Describe the trust surface without
  invoking jurisdictional legal conclusions — let the ethics subagent handle regulatory framing.
- **Third-party review widgets (Yotpo, Bazaarvoice, Trustpilot):** Review text delivered via
  client-side JavaScript is not reliably indexed by Google (SearchPilot Gold, ugc-reviews-seo.md
  Finding 5). If the baton shows a third-party widget and the DOM slice shows no review text in
  the initial HTML, emit a MEDIUM finding on indexability.
```

## Reference file list (rendered into template)

For substitution into `{{reference_file_list}}`:

```
- `trust-and-credibility.md` — trust signal placement, badge psychology, checkout abandonment, review-count thresholds, E-E-A-T trust dimension
- `social-proof-patterns.md` — review display patterns, star-rating sweet spot (4.0–4.7), scarcity effects, UGC conversion data, FTC Consumer Review Rule (16 CFR Part 465)
- `eeat-product-pages.md` — Google E-E-A-T framework for product pages, expert editorial signals, AI-content guidance, author attribution, accessibility-SEO overlap
- `review-collection.md` — review request timing and mechanics, photo/video solicitation, incentive compliance, FTC enforcement, negative-review handling
- `ugc-integration.md` — UGC photo placement strategy, gallery ratio, moderation standards, rights management, verified-buyer photo badging
- `ugc-reviews-seo.md` — review schema (AggregateRating), JS rendering risk for review text, long-tail keyword value of reviews, FTC daily-violation accrual
- `accessibility.md` — WCAG 2.2 AA requirements, alt text formulas, touch target standards, color contrast, ARIA gallery patterns, video captions, color-swatch labeling
```

## Cross-references

- [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) — shared template body this file parametrizes
- [`contracts/cluster-routing.md`](../cluster-routing.md) — canonical reference list source
- [`schema/cluster-emission-v1.json`](../../schema/cluster-emission-v1.json) — output shape
- [`schema/finding-v1.json`](../../schema/finding-v1.json) — per-finding shape
- [`scripts/test-specialist.py`](../../scripts/test-specialist.py) — harness that combines this file + template + per-engagement vars
