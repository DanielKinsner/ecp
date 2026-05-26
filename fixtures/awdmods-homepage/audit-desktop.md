# Audit — AWDMods Homepage (desktop)

## Executive Summary

The AWDMods homepage is a Shopify storefront serving a tightly defined niche — Ford Focus RS/ST and Subaru WRX/STI performance parts — but the homepage architecture leaves most of the brand's natural conversion advantages on the table. Above the fold, there is no headline, no value proposition, no trust signal, and no H1; the four-dropdown vehicle selector functions as both navigation and CTA but has no surrounding copy. The `<title>` is `AWDMods - AWDMods` (18 characters) and `meta_description` is null, so Google rewrites the SERP listing on every transactional query. The Featured Collection grid carries eight of nine products with bare prices (no MSRP anchor) and most cards display zero reviews on $400–$1,800 high-AOV exhausts and intakes. Schema markup is limited to `OnlineStore` and `WebSite` types — no `Product`, `Offer`, `AggregateRating`, or `MerchantReturnPolicy` blocks, blocking ChatGPT Shopping and Google Shopping rich result eligibility. Start with the SEO head fixes (title, meta description, og:image, H1) since they are single-template edits that compound with the structural gaps, then sequence the trust and pricing concentration work into the Featured Collection card template.

## Ethics Gate

One ADJACENT finding (HIGH severity, page-scope): the footer Privacy Policy link points to a Shopify staging subdomain rather than the canonical `awdmods.com` URL. See `ethics F-01` below — a one-field fix in Shopify admin that closes a fragile compliance posture. No BLOCK findings.

## Top Priorities

### Concentrate trust signals into the Featured Collection card template

The Featured Collection product cards are the highest-traffic conversion surface below the fold but they are missing four trust-credibility signals that are individually cheap to add and that compound when surfaced together: MSRP strikethroughs (eight of nine cards display bare prices), star ratings on the highest-AOV cards (the $1,649 Borla, $1,766 Magnaflow, and $405 Injen all display no rating widget), payment-method icons or a return-policy line near the price, and BNPL installment messaging on items above $200. Every signal exists somewhere on the site — Borla already shows the correct strikethrough format, payment icons live in the footer at scroll_y ~2841, the free-shipping threshold sits in the announcement bar, and Shopify supports Shop Pay Installments natively. Pull each into the product-card Liquid snippet so the entire row reads as a value statement rather than nine isolated prices. This is one template-level change that lands `pricing F-01`, `pricing F-03`, `trust-credibility F-04`, and `trust-credibility F-05` in a single PR.

[`pricing F-01`, `pricing F-03`, `pricing F-05`, `trust-credibility F-04`, `trust-credibility F-05`]

### Fix the page head: title, meta description, og:image, and H1

The homepage title is `AWDMods - AWDMods` (18 characters), the meta_description is null, the og:image is absent, and there is no H1 element anywhere on the page. Zyppy's Q1 2025 analysis found titles under 30 characters are rewritten by Google more than 95% of the time, and H1/title alignment drops the rewrite rate from 76% to ~20%. All four fixes live inside `layout/theme.liquid` or `snippets/head-tags.liquid`. Set the title to a 51–60 character formula that names the vehicle coverage (`Performance Parts for Ford Focus RS, ST & WRX | AWDMods`), write a 140–155 character meta description that names the categories and the $75 free-shipping threshold, point og:image at a 1200×630 crop of the existing hero photograph, and add a visually prominent H1 above the vehicle selector with the same primary noun phrase as the title. This is a single-file edit that ships in under an hour and corrects the SERP messaging on every branded and transactional query.

[`content-seo F-01`, `content-seo F-03`, `content-seo F-08`, `content-seo F-10`]

### Add Product, Offer, and AggregateRating JSON-LD to the Featured Collection

Schema markup is currently limited to `OnlineStore` and `WebSite` blocks. There is no `Product` block, no `Offer`, no `AggregateRating`, and no `MerchantReturnPolicy` — meaning the page is ineligible for Google Shopping rich results, star-rating SERP snippets, ChatGPT Shopping (launched 2025-09-29), and Perplexity product cards. SearchPilot's controlled split test found that adding `AggregateRating` schema alone produced approximately 20% organic traffic uplift. For each Featured Collection product, emit a `Product` JSON-LD block with `name`, `image`, `offers` (price, priceCurrency, availability, url), `aggregateRating` where reviews exist, and `gtin`/`mpn` where available. Add `MerchantReturnPolicy` to the `OnlineStore` block as Option B (`merchantReturnLink` pointing to the policy page). Implement in the Shopify section template that renders the featured collection — output the Liquid loop's product data as JSON-LD before closing the section's wrapper.

[`content-seo F-05`, `content-seo F-12`, `trust-credibility F-08`]

### Hero needs a headline and an above-fold trust signal

The full 1920×1080 above-fold viewport currently shows: navigation header, hero car image, vehicle selector dropdowns, and category tiles — with zero text headline and zero trust signal. The phrase `Car parts, simplified.` sits as an 11px secondary line inside the vehicle-selector utility widget; it is not a hero headline and any competitor could use the same phrase verbatim. Add a `<h1>` layer above the vehicle selector with the vehicle coverage written explicitly (`Performance Parts for the Ford Focus RS, Focus ST, WRX & STI`). Add a compact trust signal in the same band — a review aggregate (`5.0 from verified buyers`) or a customer-count line (`Parts shipped to 10,000+ AWD enthusiasts`). Both sit in the same hero section template; both are copy-only changes to the theme's hero section partial.

[`visual-cta F-01`, `visual-cta F-04`, `content-seo F-10`]

### Connect the vehicle selector to category navigation and add product counts

The hero vehicle selector (Make / Model / Year / Trim) collects fitment data but does not appear to pass it to the five category tile CTAs below. A visitor who selects `2018 Subaru WRX` and clicks `Shop Performance` lands on a generic Performance collection with no fitment filter applied and no `Showing parts for: 2018 Subaru WRX` confirmation. Wire the selector submission to set a session cookie or URL parameter that the category tile CTAs append to their target URLs, then render a persistent `Showing parts for: [vehicle]` chip on every collection page. Simultaneously add product counts to each tile heading (`Performance (143 parts)` or, post-vehicle-selection, `Performance (38 parts for your WRX)`) — these are queryable from the Shopify collection product count and require only a Liquid template change. Together these close the largest fitment-confidence gap on the homepage: visitors with a selected vehicle currently get no signal that their fitment is filtering anything.

[`category-navigation F-02`, `category-navigation F-04`]

## Findings by Cluster

### Visual CTA

#### visual-cta F-01 — Hero Section Has No Headline or Value Proposition

**SECTION:** hero-nav
**ELEMENT:** `(absent — proposed location: above the vehicle selector dropdowns in the hero section)`
**SOURCE:** VISUAL
**PRIORITY:** HIGH

**OBSERVATION:** The hero section displays a full-width dark car photograph with a vehicle year/make/model/trim selector overlay, but contains no headline, no subheadline, and no explicit value proposition copy. The phrase `Car parts, simplified.` appears only as an 11px secondary line inside the vehicle-selector utility widget at the top right — not as a hero headline. A first-time visitor arriving from paid or organic traffic cannot answer `What does AWDMods offer that competitors do not?` within 5 seconds. Baymard and NNGroup research identifies the hero headline as the first of five required above-fold elements for cold-traffic landing pages.

**RECOMMENDATION:** Add a headline layer to the hero containing a specific, differentiated value proposition that names the vehicles served — for example `Performance Parts for the Ford Focus RS, Focus ST, WRX & STI`. Place the headline at a readable size (40px minimum) in the upper-left or center of the hero, above the vehicle selector widget. If the vehicle selector is intended to remain the primary visual anchor, add a one-line benefit statement directly above the selector dropdowns to anchor context.

**Why this matters:** Visitors without a headline to anchor context bounce faster than visitors who receive an immediate relevance signal. The 5-second-test standard holds that if visitors cannot identify what a site sells before the first scroll, a significant share will leave before engaging the category tiles or featured collection.

▸ hero-section-psychology.md, Finding 4 (Baymard) [Gold]

#### visual-cta F-04 — No Trust Signal Visible Above the Fold

**SECTION:** hero-nav
**ELEMENT:** `(absent — proposed location: directly beneath the vehicle selector widget)`
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The full above-fold viewport on desktop (1920×1080) contains no trust signal of any kind — no star rating, no review count, no customer count, no recognized media mention, no satisfaction guarantee. The free-shipping announcement bar at the very top (`FREE SHIPPING on most orders $75+ — Contiguous US only SHOP NOW`) is the only policy signal present, but it is not a credibility indicator for an unknown brand. The Featured Collection h2 and product cards with review stars appear at scroll_y 906 and below — outside the above-fold zone for a 1080px viewport.

**RECOMMENDATION:** Add one compact trust signal directly in the hero or immediately beneath the vehicle selector widget. Minimum viable: a review aggregate pulled from the existing product reviews (`5.0 from verified buyers`) or a customer count (`Parts shipped to 10,000+ AWD enthusiasts`). Position it at the same vertical level as the vehicle selector dropdowns, left- or center-aligned. If aggregate site-level reviews are unavailable, a media mention or a strong brand qualifier (`Focused exclusively on Focus RS/ST and WRX/STI — no generic parts catalog`) serves the same credibility-anchoring function.

**Why this matters:** Stanford credibility research (Fogg et al., 2002) found users assess website credibility within seconds, primarily on first-impression cues. An automotive parts site selling $135–$1,766 products to enthusiasts faces a high trust bar; the absence of any above-fold credibility signal means every first-time visitor must scroll into the featured collection before encountering social proof.

▸ hero-section-psychology.md, Finding 10 (Baymard) [Gold]

#### visual-cta F-06 — Newsletter Subscribe Button Is Icon-Only With No Text Label

**SECTION:** newsletter-footer
**ELEMENT:** `button` at e36 (y=2302, height=49 CSS px)
**SOURCE:** BOTH
**PRIORITY:** LOW

**OBSERVATION:** The newsletter subscribe button at scroll_y 2302 renders as a 46×49px icon-only button containing a right-arrow icon and no text. NNGroup research establishes that generic or absent CTA labels reduce click-through because users scan without context; an arrow icon alone provides no benefit statement and forces the user to infer the action from the adjacent input field. The newsletter section copy itself (`New parts, new builds, exclusive deals. Be the first to know when something drops for your Focus RS, Focus ST, WRX, or STI.`) is well-written and audience-specific — the icon button undercuts the surrounding copy.

**RECOMMENDATION:** Replace the arrow-icon-only button with a text CTA: `Subscribe` at minimum, or a benefit-led variant such as `Get First Access` or `Keep Me Posted`. The button is already 49px tall (meets accessibility minimum) but needs to widen to accommodate 2–4 words of label text. Keep the existing newsletter copy.

**Why this matters:** The newsletter section is the last primary conversion surface before the footer. Icon-only submit buttons introduce ambiguity at the commitment point — a text label costs nothing to add and eliminates the interpretive step users must take when they see a bare arrow.

▸ cta-design-and-placement.md, Finding 14 (NNGroup) [Gold]

#### visual-cta F-09 — Newsletter Section Copy Is Specific and Audience-Named

**SECTION:** newsletter-footer
**ELEMENT:** `section` at e35 (y=2073)
**SOURCE:** BOTH
**PRIORITY:** LOW

**OBSERVATION:** The newsletter section copy names the exact vehicles served (Focus RS, Focus ST, WRX, STI) and the specific benefit of subscribing. This specificity — naming the audience by vehicle — is a strong application of the specificity principle: a Focus RS owner reading `something drops for your Focus RS` experiences immediate personal relevance.

**RECOMMENDATION:** Maintain the vehicle-named specificity. When future vehicle models are added to the catalog, update the newsletter copy to include them. Extend the same vehicle-naming pattern up-page to the hero headline.

**Why this matters:** Audience-specific copy increases opt-in rates by reducing the ambiguity of what subscribers will receive. The current copy sets an appropriate expectation and qualifies the subscriber at the point of sign-up.

▸ headline-copywriting.md, Finding 1 (CXL) [Silver]

### Pricing

#### pricing F-01 — Most Featured Products Lack Price Anchoring

**SECTION:** featured-collection-top
**ELEMENT:** `span.price` at e25 (y=1000, content `From $135.99`)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** Eight of the nine product cards in the Featured Collection display prices as bare numbers with no MSRP strikethrough, no compare-at framing, no `was/now` treatment. The lone exception is the Borla Cat-Back exhaust, which correctly shows `$1,847.99` struck through above `$1,649.99`. For the remaining cards — including the $405.48 Injen cold air intake, the $1,766.00 Magnaflow exhaust, and the `From $135.99` VelourTex floor mats — visitors see a single price with no reference point. Grewal, Monroe & Krishnan (1998) established that an advertised reference price simultaneously elevates the buyer's internal reference price, perceived product quality, and transaction value; without one, the selling price defaults to being evaluated against the shopper's last-seen price, which on this homepage may be a cheaper aftermarket part from a competitor site.

**RECOMMENDATION:** For each product whose manufacturer publishes an MSRP, render that MSRP as a struck-through price above the selling price on the product card. For made-to-order or branded exclusives without a published MSRP, introduce a `Regular price` / `Compare at` value documented from the prior selling price, ensuring it meets the FTC 16 CFR §233.1 bona-fide-price requirement. The Borla card's current execution — red current price with grey strikethrough MSRP — is the correct template; apply it across the full Featured Collection. This is a Liquid edit to the product card snippet that surfaces `compare_at_price` when populated.

**Why this matters:** Without a reference anchor, high-ticket items like the $405 intake and $1,766 exhaust are evaluated in isolation against the shopper's worst-case mental reference. Real-world A/B tests on reference-price addition report 5–15% conversion lifts on pages that previously displayed no anchor.

▸ price-anchoring.md, Finding 2 (Grewal et al. 1998) [Gold]

#### pricing F-03 — No BNPL Markers on High-Ticket Products

**SECTION:** featured-collection-top
**ELEMENT:** `(absent — proposed location: below the price line on each product card priced $200+)`
**SOURCE:** VISUAL
**PRIORITY:** HIGH

**OBSERVATION:** The Featured Collection includes three products priced above $400: an Injen cold air intake at $405.48, a Borla exhaust at $1,649.99, and a Magnaflow exhaust at $1,766.00. None of the product cards display a BNPL installment callout. The footer payment-method list (e37/e38) shows AmEx, Apple Pay, Discover, Google Pay, Mastercard, PayPal, Shop Pay, Visa — no Klarna, Afterpay, or Affirm logo, confirming BNPL is not configured site-wide. Maesen & Ang (2025) — the first peer-reviewed large-scale field study on BNPL in retail — found BNPL availability produces a ~9% increase in purchase incidence and a ~10% increase in basket size, with the effect concentrated in the $50–$500 range and above.

**RECOMMENDATION:** Enable Shopify's native Shop Pay Installments (no extra merchant cost on eligible orders) or connect a third-party BNPL provider such as Afterpay or Klarna. Surface the installment price (`or 4 interest-free payments of $X with Klarna/Afterpay`) directly beneath the selling price on product cards for items priced $100 and above. For the $1,649 Borla and $1,766 Magnaflow, the installment reframe (`4 payments of $412.50`) reduces the perceived immediate cost and is expected to lift purchase incidence on these high-consideration SKUs.

**Why this matters:** Performance automotive modifications in the $400–$2,000 range sit squarely in the zone where payment-decoupling has the largest measurable effect on conversion. A customer evaluating a $1,766 exhaust as a lump sum faces a much higher psychological barrier than one seeing `4 payments of $441.50`, even though the total cost is identical.

▸ bnpl-payment.md, Finding 1 (Maesen & Ang 2025, Journal of Marketing) [Gold]

#### pricing F-05 — No Free-Shipping Signal at Product Card Level

**SECTION:** featured-collection-top
**ELEMENT:** `(absent — proposed location: sub-label below price on cards qualifying for free shipping)`
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** None of the product cards in the Featured Collection carry any shipping signal — no `Free shipping`, no `Shipping from $X`, no threshold callout. The site-wide `FREE SHIPPING on most orders $75+` announcement bar at scroll_y 0 communicates the policy, but the per-card disclosure that converts the policy into an item-level value signal is missing. Baymard Institute (2024) data shows 39% of motivated US shoppers cite unexpected extra costs as the #1 reason for cart abandonment.

**RECOMMENDATION:** Annotate product cards for items that qualify for free shipping with a `Free shipping` sub-label below the price — Shopify themes support this as a metafield, tag-driven conditional, or product property check against the threshold. The Shampanier, Mazar & Ariely (2007) zero-price effect confirms that `Free shipping` is psychologically more compelling than a shipping discount of equivalent dollar value.

**Why this matters:** Shipping cost ambiguity at the product stage is a top-ranked abandonment driver; resolving it at the card level converts a potential cart-stage surprise into a conversion advantage on every Featured Collection impression.

▸ free-shipping.md, Finding 2 (Baymard 2024) [Gold]

#### pricing F-07 — Borla Exhaust Uses Correct MSRP Strikethrough Anchoring

**SECTION:** featured-collection-top
**ELEMENT:** `div.price-box` at e24 (y=1000, height ~60 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The Borla Cat-Back ATAK Exhaust for the Ford Focus RS correctly displays a strikethrough MSRP of $1,847.99 alongside the selling price of $1,649.99, using the visual treatment recommended by Grewal et al. (1998): higher reference price establishes transaction value, lower selling price establishes acquisition value. Savings of $198 are implicit from the two-price display.

**RECOMMENDATION:** This card's price anchoring execution is the template for the rest of the Featured Collection. Extend the same format — grey strikethrough MSRP above, styled selling price below — to all other products whose brands publish a manufacturer's suggested retail price.

**Why this matters:** Consistent MSRP anchoring across the collection signals price legitimacy and deal quality on every card, not just the promoted exhaust.

▸ price-anchoring.md, Finding 1 (Grewal et al. 1998) [Gold]

#### pricing F-09 — Charm Pricing Applied Inconsistently Across Product Cards

**SECTION:** featured-collection-top
**ELEMENT:** `span.price` at e25 (y=1000)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** Price endings across the Featured Collection are inconsistent: $135.99, $19.99, $59.99, $64.99, and $1,649.99 use .99 charm pricing; $49.00 and $1,766.00 use round pricing; $405.48 uses an irregular non-round ending that is neither a standard .99/.95 nor a clean round number. Troll & Wieseke's 2024 pre-registered meta-analysis (Journal of Consumer Psychology, 144 effect sizes) confirms .99 endings lift purchase intentions (d = 0.11) without harming quality perception for non-luxury goods. The $405.48 is the outlier: a mid-digit ending produces no charm benefit (the left digit does not change vs. $405.00) and does not read as a round, premium-positioning price either.

**RECOMMENDATION:** Standardize price endings across the collection. For utilitarian performance parts, .99 endings are appropriate. Resolve the anomalous $405.48 to either $405.99 (charm, left-digit unchanged — minimal benefit; consider $399.99 if pricing flexibility exists) or $405.00 (round). Update the SKU pricing in the Shopify product catalog rather than via theme template.

**Why this matters:** The $405.48 irregular ending creates a suboptimal price perception with no upside: it neither benefits from the .99 charm effect nor from round-number fluency. Standardizing removes a minor friction point.

▸ charm-pricing.md, Finding 1 (Troll & Wieseke 2024) [Gold]

### Trust & Credibility

#### trust-credibility F-01 — 5.0 Stars on 2 Reviews — Skepticism Trigger

**SECTION:** featured-collection-top
**ELEMENT:** `div.rating` at e21 (y=466, content `5.0 / 5.0 (2) 2 total reviews`)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The Revo Designs Rocker Stripes Decal Kit card on the featured collection shows a perfect 5.0 out of 5.0 average based on only 2 reviews. This combination is doubly damaging: the 4.0–4.7 range is the documented conversion sweet spot (Spiegel Research Center, 2017), and perfect 5.0 ratings trigger consumer skepticism about authenticity; at 2 reviews, the page is also below the 5-review threshold where 270% purchase-likelihood lift is realised.

**RECOMMENDATION:** Prioritise post-purchase review collection for this product to move from 2 to at least 5 reviews. Implement an automated post-purchase email triggered by delivery confirmation, sent 7–14 days post-delivery, targeting all buyers of this SKU. Do not artificially inflate the rating by soliciting only satisfied customers — the 4.0–4.7 range converts better than 5.0. Until the 5-review threshold is reached, add a `Be the first to share your experience` prompt to the product page rather than displaying a thin perfect score.

**Why this matters:** The 0-to-5 review threshold delivers the single highest-leverage trust lift in e-commerce — a 270% purchase likelihood increase. A perfect 5.0 on 2 reviews simultaneously signals inauthenticity, negating the trust benefit of any rating. At an AOV above $49, buyers apply higher scrutiny.

▸ social-proof-patterns.md, Finding 1 (Spiegel Research Center 2017) [Gold]

#### trust-credibility F-04 — Most Featured Products Have Zero Reviews

**SECTION:** featured-collection-top
**ELEMENT:** `(absent — proposed location: below product title on cards currently showing no rating widget)`
**SOURCE:** VISUAL
**PRIORITY:** HIGH

**OBSERVATION:** Of the nine distinct product cards visible across the featured collection, the majority display no reviews at all. The highest-AOV products on the page — Borla cat-back exhaust at $1,649.99, Magnaflow Competition cat-back at $1,766, and Injen cold air intake at $405.48 — show no star rating widget. The Spiegel Research Center study established that products with zero reviews have 270% lower purchase likelihood than products with 5 reviews, with the lift increasing to 380% for higher-priced items.

**RECOMMENDATION:** Treat the Featured Collection as a curated trust showcase: only feature products that have reached the 5-review threshold, or implement a post-purchase email campaign targeting buyers of the zero-review products to seed initial reviews. For the Borla and Magnaflow exhaust systems, even 5 genuine reviews would yield a documented 380% purchase-likelihood uplift. If products must be featured before review thresholds are met, add a `New arrival` or `Be the first to review` callout rather than displaying an empty star field.

**Why this matters:** The majority of the Featured Collection's highest-AOV products have no social proof. For buyers making $400–$1,800 discretionary performance upgrade decisions, the absence of any peer validation is the single most significant trust barrier on the page.

▸ trust-and-credibility.md, Finding 4 (Spiegel Research Center) [Gold]

#### trust-credibility F-05 — No Trust Badges Near Featured Product CTAs

**SECTION:** featured-collection-top
**ELEMENT:** `(absent — proposed location: trust strip below Featured Collection or merged into card template)`
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The homepage Featured Collection carries no trust signals at the product-card level: no return policy snippet, no money-back guarantee badge, no security seal. Payment method icons (AmEx, Apple Pay, Discover, Google Pay, Mastercard, PayPal, Shop Pay, Visa) appear only in the footer at scroll_y ~2841 — roughly 2,000 pixels below the first featured product cards. Baymard usability research establishes that trust badges function only when placed at the moment of purchase anxiety; footer placement is perceived as generic branding, not as security assurance for the specific product a visitor is considering.

**RECOMMENDATION:** Add a compact trust strip below the Featured Collection section or integrate 2–3 trust signals into the product card template: (1) a return policy indicator such as `Free returns within 30 days` or a link to the returns page; (2) a single recognized payment badge (PayPal achieves the highest notice rate at 67% in CXL eye-tracking research); (3) a money-back guarantee with positive framing (`Love it or return it`) near the Add to Cart area.

**Why this matters:** Payment icons visible only in the footer provide no trust lift at the point of intent. For an automotive-parts audience evaluating `Made to Order` products at $49–$1,766, the absence of a visible return path and payment reassurance at the product level forces visitors to evaluate risk without the information needed to commit.

▸ trust-and-credibility.md, Finding 8 (Baymard) [Silver]

#### trust-credibility F-09 — Payment Icons in Footer Only — No Return Policy on Product Cards

**SECTION:** newsletter-footer
**ELEMENT:** `contentinfo` at e34 (y=2585)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The footer `Information` column lists About Us, Privacy Choices, Privacy Policy, Terms and Conditions, and CARB Policy — but no Return Policy, Shipping Policy, or equivalent customer-assurance link is visible in the footer DOM slice. A return policy link is one of the explicit Trustworthiness elements in Google's Quality Rater Guidelines for product pages, and Signifyd's 2024 European consumer survey found 77% of shoppers base purchase decisions on return policy visibility.

**RECOMMENDATION:** Add a `Returns & Shipping` or `Return Policy` link to the footer Information column as an immediate fix. For higher impact, surface a brief return policy statement (`Free returns within 30 days on most orders`) on the Featured Collection section or in a global trust bar below the navigation.

**Why this matters:** Visitors evaluating `Made to Order` performance parts at $49–$1,766 face genuine return uncertainty — custom-made or special-order items often have different return rules. Without a visible return policy, that uncertainty resolves to `probably non-refundable`, which suppresses purchase intent for first-time visitors.

▸ trust-and-credibility.md, Finding 23 (Google Quality Rater Guidelines) [Gold]

#### trust-credibility F-10 — Product Images Have Descriptive Alt Text

**SECTION:** featured-collection-top
**ELEMENT:** `img` at e10 (y=989, alt `VelourTex Fitted Carpet Floor Mats for the Ford Focus RS / ST (Set of 4)`)
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** The featured collection product images carry full descriptive alt text: e10 (`VelourTex Fitted Carpet Floor Mats for the Ford Focus RS / ST (Set of 4)`) and e11 (`Revo Designs Rocker Stripes Decal Kit for the Ford Focus RS / ST (Set of 2)`) both match the product name and describe the item adequately for screen-reader users. This meets WCAG 2.2 SC 1.1.1 requirements.

**RECOMMENDATION:** Maintain this standard across all product images. For images added via new products or bulk imports, confirm Shopify's product title is automatically populating alt text for gallery images.

**Why this matters:** Descriptive alt text on product images is required for WCAG 2.2 AA compliance (ADA Title III / EU EAA effective 2025-06-28), improves screen reader accessibility, and supports Google Image indexing.

▸ accessibility.md, Finding 1 (WebAIM) [Gold]

### Content & SEO

#### content-seo F-01 — Title Tag Is 18 Characters and Duplicates Brand Name

**SECTION:** page-head
**ELEMENT:** `<title>` (content `AWDMods - AWDMods`, 18 chars)
**SOURCE:** DOM
**PRIORITY:** HIGH

**OBSERVATION:** The HTML title tag reads `AWDMods - AWDMods` — 18 characters total, with the brand name repeated on both sides of the separator. Zyppy's Q1 2025 analysis of 81,000 titles found that titles under 30 characters are rewritten by Google more than 95% of the time. The title contains zero product-category or keyword content: no mention of Ford Focus RS, Focus ST, WRX/STI, performance parts, or automotive accessories. For a shopper searching `Ford Focus RS performance parts` or `WRX STI exhaust`, this title provides no signal that AWDMods is relevant.

**RECOMMENDATION:** Rewrite the homepage title to the formula `[Primary Category] - [Key Differentiator] | [Brand]`, targeting 51–60 characters. Example: `Performance Parts for Ford Focus RS, ST & WRX | AWDMods` (54 chars). Front-load the product category since AWDMods is not yet brand-dominant for its target queries. Edit `layout/theme.liquid` or the SEO snippet that emits the title tag; ensure the home template overrides any default Shopify title pattern.

**Why this matters:** A title rewritten by Google to something generic eliminates AWDMods' control over its first-impression messaging in search results. Every transactional query where the title fails to signal relevance is a lost click to better-titled competitors.

▸ title-formulas-serp-psychology.md, Finding 3 (Zyppy 2025) [Gold]

#### content-seo F-03 — Meta Description Is Absent — Homepage Has No SERP Snippet Copy

**SECTION:** page-head
**ELEMENT:** `meta[name="description"]` (absent)
**SOURCE:** DOM
**PRIORITY:** HIGH

**OBSERVATION:** The homepage has no meta description tag. When a meta description is absent, Google auto-generates snippet text by extracting sentences from the page body — typically resulting in navigation labels, footer link text, or newsletter copy rather than a persuasive value proposition. For awdmods.com, Google is likely generating something from the category tile labels (`Performance Intakes Exhaust Cooling Drivetrain upgrades Shop Performance`) or the newsletter paragraph.

**RECOMMENDATION:** Add a meta description between 140–155 characters that leads with the primary customer benefit and names the key vehicle fitments: `Shop performance parts, exhaust systems, and exterior upgrades for the Ford Focus RS, Focus ST, WRX, and STI. Free shipping on most orders over $75.` Edit the home-template SEO snippet so the meta description is rendered server-side at first parse, not injected by client-side JS.

**Why this matters:** The homepage meta description controls first-impression copy for all branded and category queries where the site ranks. Auto-generated snippets drawn from navigation or footer text consistently underperform hand-written descriptions.

▸ title-formulas-serp-psychology.md, Finding 1 (Backlinko) [Gold]

#### content-seo F-05 — Homepage JSON-LD Lacks Product, Offer, AggregateRating, and GTIN Schema

**SECTION:** page-head
**ELEMENT:** `script[type="application/ld+json"]` (only OnlineStore + WebSite types present)
**SOURCE:** DOM
**PRIORITY:** HIGH

**OBSERVATION:** The page's structured data consists of two schema blocks: `@type OnlineStore` (with name, logo, sameAs social links, url) and `@type WebSite` (with SearchAction). Neither block contains `Product`, `Offer`, `AggregateRating`, `MerchantReturnPolicy`, or any product identifier (GTIN, MPN, SKU). The Featured Collection displays ten products with prices and two products with visible star ratings — element e21 shows `5.0 / 5.0 (2) 2 total reviews` — but this review data is invisible to Google's structured data parser. SearchPilot's controlled split test found that adding `AggregateRating` schema alone produces approximately 20% organic traffic uplift. Without GTIN fields, AWDMods products cannot be matched in Google Shopping's knowledge graph or in ChatGPT Instant Checkout.

**RECOMMENDATION:** For each Featured Collection product, emit a JSON-LD `Product` block with: `name`, `url`, `offers` (price, priceCurrency, availability), `aggregateRating` (ratingValue, ratingCount) for products with reviews, and `gtin`/`mpn` where available. Implement in the Shopify section template using a Liquid loop over `featured_collection.products` that outputs the JSON-LD before closing the section wrapper. Add `MerchantReturnPolicy` to the `OnlineStore` block using Option B (`merchantReturnLink` pointing to the existing return policy page).

**Why this matters:** Missing AggregateRating schema is a direct forfeit of the star-rating SERP display that drives 20% organic traffic uplift in controlled testing. Missing GTIN data blocks AWDMods products from appearing in Google Shopping rich results and ChatGPT Instant Checkout product matching.

▸ schema-product-markup.md, Finding 10 (SearchPilot) [Gold]

#### content-seo F-08 — No Open Graph Image — Social and AI Thumbnail Sharing Is Unbranded

**SECTION:** page-head
**ELEMENT:** `meta[property="og:image"]` (absent)
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** The page has no `og:image` meta tag. When the homepage URL is shared on social platforms (Facebook, LinkedIn, iMessage link previews) or surfaced by AI shopping agents that use Open Graph data for thumbnail rendering, no image is provided. The site has a high-quality hero image of a Subaru WRX STI in a cinematic low-light setting (visible at scroll_y 0) that would make an effective `og:image`.

**RECOMMENDATION:** Add `og:image`, `og:title`, `og:description`, and `og:url` meta tags to the homepage. Use the existing hero vehicle lifestyle image (resized to at least 1200×630px per Open Graph specification) as the `og:image`. The `og:title` and `og:description` should mirror the recommended page title and meta description copy. Add `twitter:image` with the same URL. Edit `layout/theme.liquid` or `snippets/head-tags.liquid`.

**Why this matters:** Unbranded or missing social thumbnails reduce link-share click-through and present an unpolished appearance when the store URL surfaces in Slack, Discord, social posts, or AI-summarized shopping recommendations — channels that drive a growing share of enthusiast automotive community traffic.

▸ ai-search-agentic-discovery.md, Finding 10 (Google) [Gold]

#### content-seo F-10 — No H1 Tag on Homepage — Title/H1 Alignment Impossible

**SECTION:** hero-nav
**ELEMENT:** `(absent — proposed location: above the vehicle selector dropdowns)`
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** The homepage has no H1 element. All heading elements in the document are H2 (`Featured Collection`, `Join Our Newsletter!`) or H3 (category labels: Performance, Exterior, Interior, Handling and Brakes). Zyppy's Q1 2025 analysis found that H1/title alignment is the single highest-leverage action against Google title rewrites — pages where H1 and title share the same primary noun phrase see rewrite rates drop from 76% to approximately 20.6%. Without an H1, this alignment is structurally impossible.

**RECOMMENDATION:** Add an H1 to the homepage hero section whose primary noun phrase matches the recommended title. If the title becomes `Performance Parts for Ford Focus RS, ST & WRX | AWDMods`, an appropriate H1 is `Performance Parts for the Ford Focus RS, Focus ST, WRX & STI`, visually prominent over or near the vehicle selector widget. The H1 can be styled to integrate with the hero design; its presence in the HTML source is what matters for Google's heading-to-title alignment check.

**Why this matters:** The absence of an H1, combined with the current 18-character brand-only title, means Google is generating its own title for this page in search results with near certainty.

▸ title-formulas-serp-psychology.md, Finding 12 (Zyppy 2025) [Silver]

#### content-seo F-13 — Product Card Image Alt Text Relies on Full Product Titles — Descriptive but Not Optimized

**SECTION:** featured-collection-top
**ELEMENT:** `img` at e10 (alt `VelourTex Fitted Carpet Floor Mats for the Ford Focus RS / ST (Set of 4)`, 71 chars)
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** Product card images use proper `<img>` elements (not CSS background-image), which makes them indexable by Google Images and discoverable via Google Lens. The alt text for the captured product images uses the full product title as the accessible name — descriptive and including fitment, but not following the recommended `[Product Name] [Key Attribute] [Angle/View/Context]` format. There is no view angle, color, or visual context appended (e.g., `front overhead view, installed in black interior`), which limits Google Lens match quality.

**RECOMMENDATION:** Continue using `<img>` elements. Enhance the alt-text template to append a view angle and visual context after the product title: format as `[Product Title] — [angle/view], [key visual attribute]`. For the floor mat: `VelourTex Fitted Carpet Floor Mats Ford Focus RS ST Set of 4 — overhead view, custom-fit black velour`. Template change in the product card Liquid snippet propagates across all collection-grid cards.

**Why this matters:** Google Lens processes approximately 20 billion visual searches per month, with 1 in 4 carrying commercial intent. Automotive accessory products are visually distinctive and naturally match visual search behavior. Richer alt text improves both Google Images relevance and Lens match confidence.

▸ image-seo-alt-text.md, Finding 4 (Google) [Gold]

#### content-seo F-14 — Canonical Tag Is Self-Referencing, HTTPS, and Correctly Structured

**SECTION:** page-head
**ELEMENT:** `link[rel="canonical"]` (href `https://www.awdmods.com/`)
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** The homepage canonical tag reads `https://www.awdmods.com/` — absolute URL with HTTPS scheme, www subdomain, lowercase path, trailing slash consistent with the site's root URL format. This self-referencing canonical correctly signals to Google that the homepage is the preferred URL.

**RECOMMENDATION:** No action required. Monitor canonical output after any theme modification — Shopify custom theme changes are the most common vector for canonical regressions.

**Why this matters:** A correct canonical at the homepage level prevents any www/non-www or trailing-slash variant from competing with the primary URL for link equity consolidation.

▸ canonical-duplicate-content.md, Finding 12 (CXL) [Silver]

#### content-seo F-16 — Homepage URL Is Clean, Lowercase, and Correctly Structured

**SECTION:** url
**ELEMENT:** page URL `https://awdmods.com/`
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** The homepage URL is the root domain with no path segments, parameters, or structural issues. No URL-level findings apply at the homepage root.

**RECOMMENDATION:** No action required at the homepage level. Prioritize URL audit work at the `/products/` and `/collections/` path levels where slug descriptiveness and hyphen-vs-underscore compliance are actionable.

**Why this matters:** A clean root URL ensures all homepage link equity consolidates correctly and no indexable duplicates exist at the domain root level.

▸ url-structure-information-architecture.md, Finding 2 (Google) [Gold]

### Checkout Flows

#### checkout-flows F-02 — No Express Checkout Buttons on Homepage Buy Path

**SECTION:** hero-nav
**ELEMENT:** `(absent — proposed location: cart drawer above the standard Checkout button)`
**SOURCE:** VISUAL
**PRIORITY:** HIGH

**OBSERVATION:** Apple Pay, Google Pay, and Shop Pay buttons are entirely absent from the homepage buy path. The footer lists these payment methods as small brand icons at scroll_y ~2841, but they are static logo images with no checkout action. There are no express checkout buttons in the cart icon area, no cart-drawer with an express option, and no quick-add-to-cart flow on the featured product cards.

**RECOMMENDATION:** Enable the `dynamic checkout buttons` setting in Shopify and surface Shop Pay, Apple Pay, and Google Pay buttons in the cart drawer above the standard `Checkout` button. For the checkout page, position wallet buttons at the top of the flow above the email/login field, per Stripe's controlled A/B data showing ~2x conversion at top-of-flow versus end-of-flow placement. This is a Shopify Payments setting, not a custom development task.

**Why this matters:** Apple Pay alone delivers +22.3% conversion lift (Stripe controlled A/B). Shop Pay converts approximately 9% higher across all checkouts. For a specialty performance parts store with AOV in the $135–$1,766 range, the incremental revenue from a 9–22% conversion lift on wallet-enabled visitors is material.

▸ biometric-and-express-checkout.md, Finding 6 (Stripe) [Silver]

#### checkout-flows F-04 — No BNPL Option for High-AOV Products

**SECTION:** newsletter-footer
**ELEMENT:** `list` at e37 (y=2841, content `American Express Apple Pay Discover Google Pay Mastercard...`)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The footer lists 8 accepted payment methods: American Express, Apple Pay, Discover, Google Pay, Mastercard, PayPal, Shop Pay, Visa. No buy-now-pay-later option (Afterpay, Klarna, or Affirm) is present. The featured product catalog includes items ranging from $19.99 to $1,766 — the Borla Cat-Back exhaust at $1,649.99 and the Magnaflow Competition exhaust at $1,766 are visible.

**RECOMMENDATION:** Enable Shop Pay Installments in Shopify Payments or integrate Afterpay/Klarna. For products above $200, display `Pay in 4 installments of $X with Afterpay` on the product page and in the cart. Prioritize BNPL rollout for the highest-AOV SKUs (exhaust systems, intake kits).

**Why this matters:** 10% of shoppers abandon because there are not enough payment methods (Baymard). For a store where a meaningful portion of catalog items exceed $300, installment payment options convert price-sensitive shoppers who would otherwise defect to a competitor that offers BNPL.

▸ checkout-optimization.md, Finding 13 (Baymard) [Gold]

#### checkout-flows F-07 — Free Shipping Threshold Visible Above Fold

**SECTION:** hero-nav
**ELEMENT:** `banner` at e19 (y=0, content `FREE SHIPPING on most orders $75+ — Contiguous US only`)
**SOURCE:** BOTH
**PRIORITY:** LOW

**OBSERVATION:** The free-shipping threshold ($75+) is disclosed in a persistent announcement bar at the very top of the page, above the header, at scroll position y=0. Shoppers see this before engaging with any product — the earliest possible disclosure point in the funnel.

**RECOMMENDATION:** The threshold is correctly placed. Add a cart-level threshold progress indicator (`Add $X more for free shipping`) to the cart drawer once items are present. Tighten the copy: replace `on most orders` with either `on orders $75+` (if all standard-size orders qualify) or a specific exclusion link.

**Why this matters:** Shipping cost revealed late is the single largest actionable abandonment driver (39–48% of abandoning shoppers, Baymard). Early disclosure at the top of the homepage prevents this trigger from firing at checkout.

▸ checkout-optimization.md, Finding 4 (Baymard) [Gold]

#### checkout-flows F-09 — Payment Method Breadth Meets Minimum Threshold

**SECTION:** newsletter-footer
**ELEMENT:** `list` at e37 (y=2841)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** Eight payment methods are shown in the footer: American Express, Apple Pay, Discover, Google Pay, Mastercard, PayPal, Shop Pay, Visa. This exceeds the 4-method minimum (cards, PayPal, Apple Pay, Google Pay) that Baymard identifies as the floor for avoiding payment-method-driven abandonment.

**RECOMMENDATION:** The payment method breadth is sufficient. The actionable gap is that these methods need to be surfaced as live express checkout buttons in the cart drawer and checkout flow (see `checkout-flows F-02`), not only as static brand logos in the footer.

**Why this matters:** Meeting the minimum payment method threshold removes the 10% payment-method abandonment trigger. Surfacing these methods actively at the cart converts the passive footer assurance into an active conversion lift.

▸ checkout-optimization.md, Finding 13 (Baymard) [Gold]

#### checkout-flows F-06 — Cart Icon Has No Item Count Badge or Drawer Preview

**SECTION:** hero-nav
**ELEMENT:** `button` at e2 (x=1616, y=51, role=button)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The header cart icon (e2, position x=1616, y=51) links to `/cart` and shows the text `Cart` to screen readers but displays no item count badge, no running subtotal, and no mini-cart drawer when clicked. When a shopper adds a product and continues browsing, there is no visible confirmation that their cart has items or what the current cart value is.

**RECOMMENDATION:** Enable a cart item count badge on the icon and configure a slide-out cart drawer on click (Shopify's native Dawn theme supports this via the cart drawer section). The drawer should show line items with images, quantities, individual prices, subtotal, and — once express checkout buttons are enabled — Shop Pay / Apple Pay / Google Pay buttons above the main `Checkout` button.

**Why this matters:** A cart with no visible state creates a disconnect between the shopper's mental model and the actual cart contents. Shoppers who cannot confirm items are in their cart are more likely to abandon or re-browse, adding friction to a funnel that already lacks express checkout acceleration.

▸ checkout-optimization.md, Finding 18 (Baymard) [Bronze]

### Performance & UX

#### performance-ux F-01 — Hero Car Image Implemented as CSS Background — Not LCP-Optimizable

**SECTION:** hero-nav
**ELEMENT:** `(CSS background on hero container; no img tag)` at e19 area
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The hero section displays a full-width car photograph spanning the entire 1920×1080 viewport. This image is implemented as a CSS background rather than an HTML `<img>` element — the header/hero DOM slice contains zero `<img>` tags for the large car photograph, and the page `<head>` contains no `<link rel="preload" as="image">` for it. CSS background images cannot carry `fetchpriority="high"`, cannot be described in a `<picture>` element for AVIF/WebP format negotiation, and are invisible to the browser's preload scanner.

**RECOMMENDATION:** Replace the CSS background with a `<picture>` element carrying `fetchpriority="high"`, explicit width and height attributes, and `<source>` entries offering AVIF and WebP before a JPEG fallback. Add `<link rel="preload" as="image" fetchpriority="high">` for the hero image URL in the `<head>`. This is a Shopify theme change to the hero section template — replace the CSS background-image with a Liquid-rendered `<img>` using Shopify's `image_url` filter.

**Why this matters:** On most product and collection pages, the hero image is the Largest Contentful Paint element. Vodafone's controlled A/B test found a 31% LCP improvement yielded 8% more online sales. A CSS background hero cannot be preloaded and cannot use modern AVIF format, leaving 30–50% potential file size reduction and an unknown but material LCP delay on the table.

▸ media-performance-optimization.md, Finding 1 (Google) [Gold]

#### performance-ux F-03 — Logo Image Missing fetchpriority — No Image Preload in Page Head

**SECTION:** hero-nav
**ELEMENT:** `img` at e9 (y=56, height=45 CSS px, alt `AWDMods`)
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** The AWDMods logo (e9) at the top of the page carries `loading="eager"` — correctly preventing lazy-load deferral — but omits `fetchpriority="high"`. The page `<head>` contains two font preload hints (Roboto Condensed and Open Sans Condensed) but no `<link rel="preload" as="image">` for any above-fold image. `fetchpriority="high"` is now Baseline-supported across Chrome 102+, Edge 102+, Firefox 132+, and Safari 17.2+.

**RECOMMENDATION:** Add `fetchpriority="high"` to the logo `<img>` element in the Shopify header template. If the hero image is converted to an `<img>` element per `performance-ux F-01`, the hero image should receive `fetchpriority="high"` and the logo drops to `auto`. Do not add `fetchpriority="high"` to more than one or two images.

**Why this matters:** `fetchpriority="high"` on the above-fold logo ensures it loads in the same high-priority network tier as render-blocking CSS, rather than queueing behind it. The priority signal affects when the browser starts the fetch — influencing the First Contentful Paint moment.

▸ media-performance-optimization.md, Finding 12 (Google) [Gold]

#### performance-ux F-04 — No AVIF/WebP Format Negotiation — Zero <picture> Elements Sitewide

**SECTION:** hero-nav
**ELEMENT:** `(absent — no picture elements anywhere in the document)`
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** The AWDMods logo is served as a PNG with a srcset of multiple PNG-format variants (no WebP or AVIF alternatives). The DOM contains zero `<picture>` elements across all sections. Shopify's CDN supports automatic WebP format negotiation via `image_url` Liquid filter with the format parameter, but this capability is not being leveraged. AVIF is supported by ~94.9% of browsers and reduces file size 50% vs JPEG; WebP achieves ~96.4% support at 25–34% reduction.

**RECOMMENDATION:** For the logo and all product images, switch to Shopify's Liquid `image_url` filter with `format: 'webp'` (or use `image_tag` which handles format negotiation). Wrap product images in `<picture>` elements with `<source type="image/avif">` and `<source type="image/webp">` before the JPEG/PNG fallback. Template-level change to image rendering partials in the Shopify Ignite theme.

**Why this matters:** Serving PNG instead of WebP or AVIF wastes 25–50% of image bandwidth on every page load. For a homepage with a large hero image and product card grid, the difference between JPEG and AVIF can exceed 500KB in total page image weight. Deloitte/Google found every 0.1s improvement in page load yields 8.4% higher retail conversion.

▸ media-performance-optimization.md, Finding 3 (Google) [Gold]

#### performance-ux F-06 — Navigation Information Architecture — Well-Chunked Category Tiles

**SECTION:** category-grid
**ELEMENT:** `nav` at e18 (content `Shop All`)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The five-category tile grid (Performance, Handling & Brakes, Interior, Exterior, Electronics) presents a well-structured progressive disclosure architecture: top-level category labels, 4–5 supporting sub-items per tile, and a single `Shop [Category]` CTA. Five options is within the cognitively comfortable scanning range, each tile is visually distinct with product photography, and the sub-item text lists provide information scent without overwhelming detail.

**RECOMMENDATION:** No change needed on the category grid layout. If the catalog expands, consider whether a sixth or seventh tile would warrant promoting the top 5 to a primary row with a collapsible secondary row.

**Why this matters:** Progressive disclosure at the category navigation level reduces the number of active decisions a first-time visitor must make before reaching a product — a direct contributor to lower bounce rates from the homepage.

▸ cognitive-load-management.md, Finding 7 (NNGroup) [Gold]

#### performance-ux F-08 — Speculation Rules API Absent — No Prerendering on Collection Navigation

**SECTION:** hero-nav
**ELEMENT:** `(absent — no script[type="speculationrules"] in document)`
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** The page head contains no `<script type="speculationrules">` element. The homepage presents five high-confidence next-navigation candidates (the five category CTAs) and a Featured Collection product grid with 9 product links visible. The Ray-Ban A/B test found the Speculation Rules API produced +156% desktop PDP conversion and +101% mobile PDP conversion on collection-to-PDP navigation.

**RECOMMENDATION:** Implement Speculation Rules on the homepage targeting the five category collection URLs and the Featured Collection product URLs. Use `eagerness: 'moderate'` to trigger prerendering on link hover, limiting bandwidth cost. Chrome-only — Firefox and Safari users see no change.

**Why this matters:** The Speculation Rules API eliminates perceived navigation latency entirely for Chrome users by rendering the next page in the background before the click. For a homepage that functions primarily as a navigation layer to category and product pages, this is an exceptionally well-matched pattern.

▸ core-web-vitals.md, Finding 11 (SearchPilot Ray-Ban case) [Silver]

### Product Media

#### product-media F-02 — No Hover Image Swap on Featured Collection Cards

**SECTION:** featured-collection-top
**ELEMENT:** `img` at e10 (y=989, 271×271 CSS px)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The Featured Collection grid presents every product card with a single static image and no hover interaction. Mousing over a card produces no image swap, no secondary angle, no quick-action overlay. 76% of sites fail to implement synchronized hover effects per Baymard's 50-site benchmark.

**RECOMMENDATION:** For each product card, implement a CSS opacity-transition hover swap (150–200ms ease) that replaces the primary product image with a secondary angle or lifestyle image on `mouseenter`. Preload the secondary image for above-fold cards. For automotive accessories, an installed/in-context shot is the highest-ROI secondary. Add a quick-add or `View Details` CTA visible on hover.

**Why this matters:** Desktop hover interactions drive click-through on category pages without requiring full PDP navigation. Baymard's benchmark identifies this as the highest single-interaction ROI enhancement for desktop product listings.

▸ thumbnail-design.md, Finding 2 (Baymard) [Gold]

#### product-media F-03 — Product Cards Expose Only One Image — No Multi-Image Access or Count Signal

**SECTION:** featured-collection-top
**ELEMENT:** `img` at e11 (y=989, 271×271 CSS px)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** Every product card across both rows of the Featured Collection presents exactly one image with no mechanism to access additional angles. There are no thumbnail strips, no dot indicators, no `N of N` counter, and no hover carousel. Baymard benchmarks require a minimum of 3 accessible images per listing card.

**RECOMMENDATION:** Add a hover carousel to each product card that reveals at least 2 additional images (3 total accessible) on desktop. Sequence: (1) primary packshot or hero image, (2) installed/lifestyle context shot, (3) detail close-up showing finish or material. Display a persistent `N of N` counter or thumbnail dots above or below the card image.

**Why this matters:** Shoppers evaluating automotive accessories need to see installation context, fitment evidence, and product detail before committing to a click. When all of that requires navigating to a PDP, a meaningful share of category-page visitors will not make the additional click.

▸ image-quantity-types.md, Finding 6 (Baymard) [Gold]

#### product-media F-04 — Featured Collection Cards Lack Unified Hit Area

**SECTION:** featured-collection-top
**ELEMENT:** `(card wrapping anchor absent — img and title rendered as separate elements)`
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** Product card images (e10, e11) are captured as standalone `img` elements and brand/title text as separate elements below, with no wrapping anchor element spanning the full card surface. This is a split hit-area pattern — Baymard identifies it at 76% of sites and characterizes it as a consistent source of misclicks and confusion.

**RECOMMENDATION:** Wrap each product card's full surface — image, brand name, product title, price, badge, and rating — in a single `<a>` element pointing to the PDP. Position any interactive elements that must remain separate (wishlist icon, quick-add button) using absolute positioning with higher z-index above the card link layer. Test with keyboard navigation to confirm Tab reaches each card and Enter navigates correctly.

**Why this matters:** Split hit areas on product cards cause misclicks that interrupt the browse flow and create a perception of a low-quality storefront. For a homepage Featured Collection, clickability friction at this stage directly suppresses downstream click-through and add-to-cart rates.

▸ thumbnail-design.md, Finding 3 (Baymard) [Gold]

### Category Navigation

#### category-navigation F-01 — Search Input Is Icon-Toggle Only — No Visible Text Box

**SECTION:** hero-nav
**ELEMENT:** `button` at e1 (x=1246, y=56, 44×44 CSS px); expanded `combobox` at e17 (929 CSS px wide)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The search entry point in the AWDMods header is a 44×44px icon button (accessible name `What are you looking for?`) rather than a persistently visible text input. NNGroup's guidance is explicit that on sites with more than 50 products, hiding search behind an icon-only toggle reduces findability — users who don't recognize the icon as a search trigger skip it entirely. The full-width combobox input (929px, e17) only appears after the icon is activated.

**RECOMMENDATION:** Render the search bar input as a persistently visible text field in the header rather than requiring an icon click to reveal it. The existing 929px input is already the right width for typical automotive parts queries — expose it by default so users see the `What are you looking for?` placeholder text on every page load.

**Why this matters:** Automotive parts shoppers have highly specific queries (part numbers, vehicle fitment, brand+model combinations). Hiding the search entry point behind an icon adds friction at the exact moment users are most ready to search; 40% of users fail to locate filtering/search options when they are not immediately visible.

▸ search-and-filter-ux.md, Finding 17 (NNGroup) [Gold]

#### category-navigation F-02 — No Compatibility Filter in Primary Navigation or Category Tiles

**SECTION:** category-grid
**ELEMENT:** `(absent — vehicle selector exists in hero but does not propagate to category tile CTAs)`
**SOURCE:** VISUAL
**PRIORITY:** HIGH

**OBSERVATION:** AWDMods sells compatibility-dependent products. The homepage hero includes a vehicle selector (Make / Model / Year / Trim), but it is visually buried in the hero image and disconnected from the five category tiles below. Once a visitor selects their vehicle and clicks `Shop Performance`, there is no visible confirmation that search results will be filtered to their fitment. Baymard's compatibility filter research shows 65% of users fail to find the correct product when compatibility filtering is absent or unclear.

**RECOMMENDATION:** Connect the homepage vehicle selector to the category tile CTAs so that clicking `Shop Performance` (or any tile) passes the selected vehicle as a URL parameter and renders the target collection page pre-filtered to that fitment. Display a persistent `Showing parts for: [Year] [Make] [Model]` chip at the top of every collection page when a vehicle has been selected. If the selector is not yet wired to filtering, add a prominent `Select your vehicle` prompt above the category tiles.

**Why this matters:** When compatibility filtering is absent or invisible, customers click through to collection pages, scroll past incompatible parts, and abandon — often buying from a competitor whose site surfaces fitment-specific results immediately. For a performance parts store serving Focus RS, WRX, and STI owners, fitment confidence is the highest-leverage conversion lever at the category navigation level.

▸ search-and-filter-ux.md, Finding 5 (Baymard) [Gold]

#### category-navigation F-04 — Category Navigation Tiles Missing Product Counts

**SECTION:** category-grid
**ELEMENT:** `div` at e12 (y=544, content `Performance Intakes Exhaust Cooling Drivetrain upgrades Shop Performance`)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The five `Shop by Category` tiles list subcategory names beneath each tile heading but show no product counts. Visitors cannot gauge whether a given category has enough relevant parts to justify clicking through. Baymard's filter-value-count research shows that displaying counts alongside category options lets users make better routing decisions and avoids dead-end navigations.

**RECOMMENDATION:** Add a product count beneath each category tile heading — `Performance (143 parts)` or, if the vehicle selector is connected, `Performance (38 parts for your WRX STI)`. Render server-side at page build time or fetch dynamically when a vehicle is selected. Even a static total-catalog count adds navigational value.

**Why this matters:** Without product counts, category tiles function as blind links — visitors have no signal for which categories are well-stocked for their build. Low-inventory categories that look equally prominent as deep ones will disappoint after click-through.

▸ search-and-filter-ux.md, Finding 25 (Baymard) [Gold]

#### category-navigation F-06 — Breadcrumbs Absent on Homepage — No Hierarchy or History Type Present

**SECTION:** hero-nav
**ELEMENT:** `(absent — no BreadcrumbList in JSON-LD; no breadcrumb component below nav)`
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** No breadcrumb navigation is present on the AWDMods homepage in any form — neither a hierarchy type (`Home > Performance`) nor a history type (`← Back to results`). The page's schema JSON-LD contains OnlineStore and WebSite types but no BreadcrumbList markup. While breadcrumbs are typically most critical on PDPs and collection pages, their absence from the Shopify theme means they are likely missing across the site. Two SearchPilot controlled tests found removing breadcrumbs caused -5.5% and -7% organic traffic loss respectively.

**RECOMMENDATION:** Implement BreadcrumbList JSON-LD schema across all collection and product pages. For collection pages, the hierarchy breadcrumb should render as `Home > [Category]` with crawlable anchor links. For PDPs, add both a hierarchy breadcrumb (`Home > Performance > Intakes > [Product Name]`) and a history-type `Back to [Collection] ([N] items)` link that preserves the visitor's filter and sort state.

**Why this matters:** Breadcrumb absence costs organic traffic directly (-5.5% to -7% in two controlled tests) and degrades navigation confidence for users stepping back up the category hierarchy. For an SEO-dependent store competing on automotive parts keywords, this is a structurally avoidable traffic loss.

▸ breadcrumbs.md, Finding 1 (SearchPilot) [Gold]

#### category-navigation F-07 — Featured Collection Grid Uses 5-Column Layout — Exceeds Recommended Maximum

**SECTION:** featured-collection-top
**ELEMENT:** `img` at e10 (y=989, 271 CSS px wide); cards at x=240, 528 confirm 5-col grid
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The Featured Collection on the homepage renders 5 product cards per row at 1920×1080 desktop. Element measurements confirm card widths of 271px with approximately 17px gutters across a 1905px container, accounting for 5 columns. Hugo Jenkins' UsabilityHub study found scanning time per row increases 35.7% going from 4 to 5 columns (4.61s → 6.26s).

**RECOMMENDATION:** Cap the grid at 4 columns by setting a maximum card width or using `grid-template-columns: repeat(4, 1fr)` with a defined max container width. A 4-column layout at this viewport yields roughly 450px card widths — larger images that reduce per-card evaluation time and compensate for showing one fewer product per row.

**Why this matters:** Automotive parts shoppers evaluate products through images. Narrower cards at 5 columns compress the visual evaluation signal, increasing time-on-page without increasing click confidence.

▸ grid-layout.md, Finding 1 (UsabilityHub Jenkins 2020) [Silver]

#### category-navigation F-09 — Vehicle Selector Widget Present Above the Fold on Homepage

**SECTION:** hero-nav
**ELEMENT:** `button` at e3 (x=795, y=116, content `Shop by Category`)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** AWDMods correctly surfaces a four-field vehicle selector (Make / Model / Year / Trim) in the hero banner, visible above the fold at page load. This addresses the core compatibility navigation need for automotive parts shoppers and positions fitment-first navigation prominently.

**RECOMMENDATION:** The vehicle selector placement is correct. Wire the submit button to pass vehicle parameters to collection page URLs so filter state persists across navigation. See `category-navigation F-02` for the gap in how selector results connect to category tile CTAs.

**Why this matters:** Automotive parts stores that surface vehicle compatibility filtering above the fold see higher engagement from returning customers who bookmark their vehicle configuration.

▸ search-and-filter-ux.md, Finding 5 (Baymard) [Gold]

#### category-navigation F-11 — Category Tiles Provide Clear Subcategory Hierarchy for Five Major Segments

**SECTION:** category-grid
**ELEMENT:** `div` at e13 (y=544, content `Handling and Brakes Suspension Wheels Brake kits Chassis control Shop Handling`)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The `Shop by Category` tile grid correctly surfaces all five major product segments (Performance, Handling & Brakes, Interior, Exterior, Electronics) with subcategory context text beneath each heading. This matches Baymard's subcategory navigation tile guidance for large-catalog parent categories.

**RECOMMENDATION:** The tile structure is sound. Priority improvements are connecting the vehicle selector to tile CTAs (`category-navigation F-02`) and adding product counts to tile labels (`category-navigation F-04`).

**Why this matters:** Category tiles that clearly segment a broad catalog reduce the number of unnecessary page views visitors must take before reaching relevant products.

▸ merchandising-psychology.md, Finding 8 (Baymard) [Silver]

### Post-Purchase

#### post-purchase F-01 — No Loyalty Program Signal on Repeat-Purchase Platform

**SECTION:** newsletter-footer
**ELEMENT:** `(absent — no loyalty entry point in newsletter, footer, or My Account column)`
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The homepage newsletter section and footer carry zero loyalty program signal: no rewards enrollment invitation, no points-per-purchase teaser, and no `join rewards` link in the footer navigation. The My Account column lists only Order History, Wish List, and Track My Order. AWDMods sells high-consideration performance parts to a customer base that builds vehicles over multiple purchases across months or years — a textbook fit for loyalty.

**RECOMMENDATION:** If AWDMods has an active loyalty program, add an `Earn rewards on every build` entry point to the footer My Account column alongside Order History. Add a one-line loyalty teaser beneath the newsletter headline: `Plus earn points on every part you add to your build — redeem for store credit.` If no loyalty program exists, the newsletter section and order confirmation page are the two highest-leverage locations to introduce one.

**Why this matters:** Loyalty program enrollment rates reach 12-25% of new customers when the prompt appears at or near the purchase confirmation moment. For a specialty auto parts store where a single customer may spend thousands across a year of modifications, a program that converts even one additional purchase from 15% of subscribers meaningfully outperforms most paid acquisition channels.

▸ loyalty-programs.md, Finding 9 (Smile.io) [Bronze]

#### post-purchase F-04 — Newsletter Value Proposition Frames Signup as News Delivery, Not Subscriber Benefit

**SECTION:** newsletter-footer
**ELEMENT:** `section` at e35 (y=2073, content `Join Our Newsletter! New parts, new builds, exclusive deals...`)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The newsletter section carries the heading `Join Our Newsletter!` and body copy: `New parts, new builds, exclusive deals. Be the first to know when something drops for your Focus RS, Focus ST, WRX, or STI.` This frames the newsletter as a broadcast channel for store announcements. For a customer who just purchased a performance part, this copy offers no post-purchase relationship value — no build guidance content, no owner tips, no reassurance framing, no community membership angle.

**RECOMMENDATION:** Rewrite the newsletter subheadline to lead with subscriber benefit rather than product announcements. Example: `Get exclusive build guides, early access to new parts, and subscriber-only discounts for your Focus RS, Focus ST, WRX, or STI build.` If AWDMods sends how-to content, installation tips, or owner spotlights, name those benefits explicitly.

**Why this matters:** The Post-Purchase Hug content framework shows that value-delivering content during the shipping window reduces cognitive dissonance and builds loyalty. The newsletter is the primary vehicle for delivering this content, but only if subscribers understand they will receive something worth opening.

▸ buyers-remorse.md, Finding 6 (Kumar et al. 2014) [Silver]

#### post-purchase F-05 — No Referral Program CTA for High-Advocacy Enthusiast Audience

**SECTION:** newsletter-footer
**ELEMENT:** `(absent — no referral link in footer Information or My Account columns)`
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The footer and newsletter section contain no referral program entry point. Performance car modification is an intensely social, word-of-mouth category: owners share builds on Instagram, YouTube, and at events. The 72-hour post-purchase window is the peak referral opportunity, and a customer returning to check order status finds no referral mechanism.

**RECOMMENDATION:** Add a `Refer a Friend` link to the footer My Account or Information column pointing to a referral program landing page. For the newsletter section, add a one-line prompt beneath the email field: `Already a customer? Share AWDMods with a fellow RS or WRX owner — give them $15 off their first order, get $15 back.` Use give-first framing — it outperforms get-first framing.

**Why this matters:** Referred customers from genuine peer recommendations show 16-25% higher profit margin over three years and 37% higher retention than non-referred customers. For a niche performance parts brand, peer referrals carry outsized trust.

▸ referral-programs.md, Finding 1 (Wharton Schmitt et al.) [Bronze]

### Ethics

#### ethics F-01 — Privacy Policy Links to Staging Domain, Not Canonical Store

**SECTION:** footer-policy-links
**ELEMENT:** `contentinfo` at e34 (footer Information column; href `https://e1520g-k3.myshopify.com/policies/privacy-policy`)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The footer Privacy Policy link on both desktop and mobile points to `https://e1520g-k3.myshopify.com/policies/privacy-policy` — a `myshopify.com` staging subdomain — instead of a canonical first-party URL on `awdmods.com`. Every other footer link (About Us, Terms and Conditions, CARB Policy, Your Privacy Choices) correctly uses relative paths or the canonical domain. Only the Privacy Policy routes to the staging domain. The pattern is legally adjacent: GDPR Article 13 requires the controller to provide information `at the time personal data are obtained` via a clearly attributable notice; a privacy policy URL under a third-party domain (myshopify.com) rather than the merchant's own domain creates ambiguity about which entity controls the data and which policy governs the transaction. CCPA notice requirements similarly depend on visitors being able to identify the disclosing entity from the URL.

**RECOMMENDATION:** Update the Privacy Policy footer link to point to the canonical first-party URL. On Shopify, the standard path is `/policies/privacy-policy` (relative) or `https://www.awdmods.com/policies/privacy-policy` (absolute). In Shopify admin, navigate to Online Store > Navigation > footer menu, locate the Privacy Policy link, and replace the destination URL. Confirm the `Your Privacy Choices` page also links to the canonical policy rather than the staging domain.

**Why this matters:** A staging-domain privacy policy URL puts the site in a fragile compliance position. For any visitor from a GDPR-covered country (EU, UK, EEA) or California, the privacy policy is a legally required disclosure. If the staging domain is retired or access-restricted, visitors encounter a broken link at the exact moment they are trying to exercise their privacy rights — producing an active GDPR Art 13 and CCPA notice violation. The fix takes under two minutes in Shopify admin.

▸ ethics-gate.md, PART 6 — Regulatory Disclosure Chain (GDPR Art 13) [Gold]

## Methodology Notes

PASS findings (visual-cta F-09, pricing F-07, trust-credibility F-10, content-seo F-14, content-seo F-16, checkout-flows F-07, checkout-flows F-09, performance-ux F-06, category-navigation F-09, category-navigation F-11) are included in the per-section views above to confirm correct implementation. Six ethics CLEAR findings are recorded in the ethics-findings.json emission and not rendered into this document by default.
