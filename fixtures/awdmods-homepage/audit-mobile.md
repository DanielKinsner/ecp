# Audit — AWDMods Homepage (mobile)

## Executive Summary

On a 390×844 viewport, the AWDMods homepage opens to a dark hero photograph with four sequential vehicle-selector dropdowns and a `FIND PARTS` CTA — and zero text headline, zero trust signal, no above-fold value proposition. The entire site navigation (`Shop by Category`, `Shop by Vehicle`, Contact, My Account) lives behind a hamburger icon; primary destinations are invisible at scroll_y=0. Featured Collection product cards present a single image and a small unlabeled `+` quick-add overlay (~40×40px, below the WCAG 44×44 target) as the only purchase affordance — no labeled `Add to Cart`, no MSRP anchoring on the $135 floor mat, no BNPL on the $135+ products. The page head is empty of meaningful SEO signal: title is `AWDMods - AWDMods` (17 chars), `meta_description` is null, `og:description` is just `AWDMods`, `og:image` is absent, and only `OnlineStore`/`WebSite` schema exists — no `Product`, `Offer`, or `AggregateRating`. The cart drawer has no express checkout buttons (Apple Pay, Google Pay, Shop Pay are footer logos only) and no free-shipping progress indicator. Sequence: SEO head fixes first (single-template edit), then hero headline + trust signal, then the Featured Collection card template work to add MSRP anchors, BNPL widgets, labeled CTAs, and rating placeholders.

## Ethics Gate

One ADJACENT finding (HIGH severity, page-scope): the footer Privacy Policy link points to a Shopify staging subdomain rather than the canonical `awdmods.com` URL. See `ethics F-01` below — a one-field fix in Shopify admin that closes a fragile compliance posture. No BLOCK findings.

## Top Priorities

### Replace the icon-only quick-add with a labeled mobile-card CTA, then layer in the missing trust and pricing signals

Each mobile Featured Collection product card currently exposes only a small (~40×40px) orange `+` quick-add overlay as its purchase affordance — below the WCAG 2.2 AA 44×44 touch target and unlabeled. A visitor cannot tell whether tapping it adds to cart, opens a configurator, or navigates to the PDP. Add a clearly labeled, near-full-width CTA button beneath the price line on each card (`Add to Cart` for in-stock SKUs, `Choose Options` for `Made to Order` variants), at minimum 48px tall. In the same template change, layer in the missing pricing and trust signals: MSRP strikethrough above the selling price (only Borla currently shows this; the other eight cards do not), Shop Pay Installments line for products $200+, and a star-rating area that either displays the current rating or a `Be the first to review` placeholder so the highest-priced VelourTex card stops showing zero social proof. This single PR addresses `visual-cta F-03`, `pricing F-02`, `pricing F-04`, `trust-credibility F-02`, and the `category-navigation F-05` review-display gap.

[`visual-cta F-03`, `pricing F-02`, `pricing F-04`, `trust-credibility F-02`]

### Fix the page head: title, meta description, og:image, og:description, and H1

The homepage title is `AWDMods - AWDMods` (17 chars), the `meta_description` is null, the `og:description` contains only `AWDMods`, the `og:image` is absent, and there is no H1 element anywhere on the page. Zyppy's Q1 2025 analysis found titles under 30 characters are rewritten by Google more than 95% of the time, and H1/title alignment drops the rewrite rate from 76% to ~20%. All five fixes live inside `layout/theme.liquid` or `snippets/head-tags.liquid`. Set the title to `Performance Parts for Focus RS, WRX & STI | AWDMods` (51 chars), write a 140–155 character meta description that names categories and the $75 free-shipping threshold, mirror the same text into `og:description`, point `og:image` at a 1200×630 crop of the existing hero photograph, and add a visually prominent (or visually hidden) H1 above the vehicle selector with the same primary noun phrase as the title. Single-file edit, ships in under an hour.

[`content-seo F-02`, `content-seo F-04`, `content-seo F-07`, `content-seo F-09`, `content-seo F-11`]

### Surface primary navigation outside the hamburger; add bottom nav for mobile

The entire site navigation — `Shop by Category`, `Shop by Vehicle`, Contact, My Account — lives behind the hamburger icon in the top-left. NNGroup confirms hidden navigation consistently underperforms on discoverability; switching to visible bottom navigation increases engagement by 25–50% and reduces task completion time by 22%. Implement a persistent bottom navigation bar with 4–5 destinations: Home, Search, Shop by Vehicle (or Browse), Cart (with item-count badge), Account. Reserve the hamburger for the full secondary category tree. The current pattern makes both `Shop by Category` and `Shop by Vehicle` — AWDMods' two primary discovery modes — invisible at the zero-scroll state.

[`performance-ux F-02`, `category-navigation F-10`]

### Replace four sequential dropdowns with a single predictive vehicle search; persist the selection

The mobile hero presents four sequential dropdown selectors (Make → Model → Year → Trim) — the highest-friction input pattern on mobile, where each tap opens an OS-native picker that closes before the next dropdown can be used. Every additional mandatory decision in the funnel corresponds to measurable drop-off. Replace the four dropdowns with a single predictive search input (`Type your vehicle — e.g., 2018 Subaru WRX`) that resolves Make/Model/Year/Trim in one gesture. After submission, persist the vehicle selection in localStorage and surface a `Vehicle: 2018 Subaru WRX` chip below the sticky header so it follows the visitor into category pages. This addresses both the four-dropdown friction (`performance-ux F-05`) and the siloed-finder gap (`category-navigation F-03`) where the selector currently does not propagate to category-page filtering.

[`performance-ux F-05`, `category-navigation F-03`]

### Enable express checkout in the cart drawer and add a shipping-progress bar

The cart drawer is empty of express checkout entry points: no Apple Pay, no Google Pay, no Shop Pay buttons. Payment-method logos sit in the footer at scroll_y ~1629, far from any purchase action. The drawer also lacks a free-shipping progress indicator, so the announcement bar's $75 threshold is disconnected from the in-cart experience. Enable Shopify's `dynamic checkout buttons` setting on cart and product forms — this surfaces Apple Pay, Google Pay, or Shop Pay as a single-tap path above the standard `Checkout` button. Add a free-shipping progress bar to the cart drawer (`You're $23 away from free shipping`) that updates as items are added. On mobile, where 70%+ of Shop Pay transactions originate, this is the single highest-leverage checkout fix available.

[`checkout-flows F-01`, `checkout-flows F-05`, `checkout-flows F-03`]

## Findings by Cluster

### Visual CTA

#### visual-cta F-02 — No Above-Fold Headline or Value Proposition

**SECTION:** header-quick-filter
**ELEMENT:** `(absent — proposed location: above the vehicle selector dropdowns in the hero)`
**SOURCE:** VISUAL
**PRIORITY:** HIGH

**OBSERVATION:** The entire above-fold viewport on mobile (390×844px) contains no headline and no value proposition. A visitor arriving cold sees a dark car photograph, four unlabeled dropdown selectors, and a blue `FIND PARTS` button — but nothing that answers `What does this store sell?` or `Why should I choose AWDMods over a competitor?` The page title `AWDMods - AWDMods` appears only in the browser tab. Baymard and NNGroup research identifies a visible above-fold headline as a required element for landing pages receiving cold or paid traffic.

**RECOMMENDATION:** Add a single concise headline directly above or beside the vehicle-selector widget — `Performance Parts for Focus RS, Focus ST, WRX, and STI` — that identifies the store's product scope. If the brand positioning warrants differentiation, append `Expert-curated. Ships fast.` This can be a one-line `<h1>` or `<p>` element that sits above the selector dropdowns within the existing hero layout, costing zero additional viewport height if line-height is constrained.

**Why this matters:** Without a visible headline, every cold-traffic visitor must decode the page's purpose from visual cues alone. At mobile scroll speeds, many will bounce before the vehicle selector registers as a tool rather than a form to ignore. A single descriptive headline resolves the `Is this the right place?` question in under 2 seconds.

▸ hero-section-psychology.md, Finding 4 (Baymard) [Gold]

#### visual-cta F-03 — Product Cards Lack Visible Add-to-Cart CTA

**SECTION:** featured-collection
**ELEMENT:** `img` at e22 (y=3000, 798×798 device px) — the `+` overlay is a 40×40 device px circular icon at bottom-right
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The VelourTex Floor Mats card in the Featured Collection presents a product image, title, price (`FROM $135.99`), and a `Made to Order` badge — but the only purchasable action is a small (~40×40px) orange circular `+` icon at the bottom corner of the product image. This icon is below the WCAG 2.2 AA 44×44px touch target recommendation and is unlabeled — a visitor cannot tell by looking whether it adds to cart, opens a configurator, or navigates to the PDP. NNGroup research on CTA label clarity shows unlabeled or ambiguously-labeled primary actions produce lower engagement.

**RECOMMENDATION:** Add a clearly labeled, full-width or near-full-width CTA button beneath the price line on each product card — `Add to Cart` for in-stock products or `Choose Options` for products requiring configuration (the `Made to Order` floor mats). The button should use the same blue fill currently used on category CTAs, be at minimum 48px tall, and carry a text label visible at rest state without any hover or tap interaction. The small orange `+` can remain as a supplementary quick-add shortcut but should not be the only purchase affordance.

**Why this matters:** Product cards on a homepage Featured Collection are a direct revenue path — a visitor browsing with purchase intent should be able to initiate the cart action without navigating to a PDP first. An unlabeled icon button as the sole card-level CTA forces every interested visitor through an extra tap, adding friction at the highest-intent moment in the browse flow.

▸ cta-design-and-placement.md, Finding 14 (NNGroup) [Gold]

#### visual-cta F-05 — No Trust Signal in Above-Fold Hero

**SECTION:** header-quick-filter
**ELEMENT:** `(absent — proposed location: beneath the vehicle selector and above the FIND PARTS button)`
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The above-fold viewport at scroll_y=0 contains: free-shipping announcement bar (`FREE SHIPPING on most orders $75+`), AWDMods logo, hamburger menu, search bar, vehicle selector dropdowns, and FIND PARTS button. No aggregate review rating, no customer count, no media mention, and no satisfaction guarantee is visible. The free-shipping bar communicates a shipping policy but is not a credibility signal — it does not answer `Can I trust this merchant?` for a first-time visitor.

**RECOMMENDATION:** Add a compact trust signal directly within the hero section, beneath the vehicle selector and above the FIND PARTS button — for example, a one-line element showing `★★★★★ 4.8 · 3,200+ orders shipped` or `Trusted by WRX and Focus RS owners since [year]`. If aggregate review data is available from the Shopify store, a star rating aggregate with order count is the highest-credibility option and takes approximately 30px of vertical space.

**Why this matters:** For automotive parts — a considered purchase where fitment errors are costly and returns inconvenient — trust signals at the initial impression point are more important than in impulse categories. A first-time visitor encountering a dark, unfamiliar site with no credibility markers and a vehicle-configuration form as the primary UX has no signal that the merchant is reliable.

▸ hero-section-psychology.md, Finding 10 (Baymard) [Gold]

#### visual-cta F-07 — FIND PARTS CTA Button Visually Distinct on Dark Hero

**SECTION:** header-quick-filter
**ELEMENT:** FIND PARTS button (e14 area, y=0)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The FIND PARTS primary action button in the hero widget uses a blue solid fill that contrasts adequately against the dark hero background and the semi-transparent selector dropdown backgrounds. The button is the visually dominant interactive element within the vehicle selector widget, satisfying the contrast-over-color principle.

**RECOMMENDATION:** No change required for CTA button contrast in this element. If the overall hero receives a redesign per `visual-cta F-02` and `visual-cta F-05`, ensure the FIND PARTS button retains its current contrast advantage and is not overridden by added headline or trust signal elements.

**Why this matters:** Maintaining CTA visual dominance within the vehicle selector widget ensures that visitors who engage with the selector can identify and tap the conversion action without hunting for it.

▸ color-psychology.md, Finding 2 (CXL) [Silver]

#### visual-cta F-08 — Newsletter CTA Copy Is Audience-Specific

**SECTION:** newsletter-footer
**ELEMENT:** `section` at e29 (y=1629, content `Join Our Newsletter! New parts, new builds, exclusive deals...`)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The newsletter section copy names the store's core vehicle fitments by model (`Focus RS, Focus ST, WRX, or STI`) rather than using generic `new arrivals` language. This vehicle-specificity mirrors the store's audience segmentation and creates a relevance signal — a Focus RS owner reading `when something drops for your Focus RS` receives a targeted prompt.

**RECOMMENDATION:** No change required. This specificity pattern should be extended up-page: the vehicle model names that make the newsletter copy effective belong in the hero headline as well (`visual-cta F-02`).

**Why this matters:** Audience-specific copy in the newsletter section sets a positive pattern. Consistent application of vehicle-specific language throughout the page — especially above the fold — would reinforce relevance at the highest-attention viewport positions.

▸ headline-copywriting.md, Finding 1 (CXL) [Silver]

### Pricing

#### pricing F-02 — Featured Card Price Has No MSRP or Comparison Anchor

**SECTION:** featured-collection
**ELEMENT:** `span.price` at e27 (content `From $135.99`)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** Both visible featured-collection cards present bare selling prices with no reference anchor. The VelourTex floor mats show `FROM $135.99` — no MSRP strikethrough, no `was/now` framing, no savings percentage. The Revo Designs decal kit shows `$49.00` with identical absence of comparison context. Visitors land on these cards without a prior price signal; the advertised reference price mechanism (Grewal et al. 1998) that elevates perceived product value is entirely bypassed.

**RECOMMENDATION:** If either product has a manufacturer-suggested retail price above the selling price, render the MSRP as a grey strikethrough above the selling price and add a `Save $X (Y%)` line in the brand's accent color. Where a documented MSRP is unavailable, display a legitimate `regular price` based on actual prior pricing (FTC 16 CFR §233.1 requires the reference to reflect a bona fide prior offer). Liquid edit to the product card snippet that conditionally renders `compare_at_price` when populated.

**Why this matters:** Reference prices independently raise perceived product quality and transaction value before customers calculate savings — omitting them means $135.99 reads as expensive against nothing, suppressing click-through on the highest-ticket featured card.

▸ price-anchoring.md, Finding 2 (Grewal et al. 1998) [Gold]

#### pricing F-04 — No BNPL Option on $135+ Featured Product

**SECTION:** featured-collection
**ELEMENT:** `(absent — proposed location: below price line on each product card priced $100+)`
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** BNPL (Klarna, Afterpay, Affirm, or Shop Pay Installments) is absent throughout the site. The footer payment-icons row (e32) shows Amex, Apple Pay, Discover, Google Pay, Mastercard, PayPal, Shop Pay, Visa — no BNPL provider. The featured $135.99 floor mat falls within the $50–$500 range where BNPL generates its largest purchase-incidence and basket-size lift (Maesen & Ang 2025: ~9% purchase incidence increase, ~10% basket size increase). A `Made to Order` product requiring upfront commitment is precisely the scenario where installment framing reduces perceived affordability barriers.

**RECOMMENDATION:** Add Shopify's native Shop Pay Installments (no extra merchant cost on eligible orders) or connect Afterpay. Surface the installment price (`4 interest-free payments of $34.00`) directly beneath the selling price on product cards and PDPs. The installment amount, not the total, should be the psychologically salient figure while the full price remains visible for regulatory compliance.

**Why this matters:** Mid-ticket automotive accessories in the $100–$500 range are exactly where BNPL generates measurable conversion lift; leaving a $135 featured product without an installment option cedes that lift to competitors who display one.

▸ bnpl-payment.md, Finding 1 (Maesen & Ang 2025) [Gold]

#### pricing F-06 — Free Shipping Banner Uses Hedged Language That Dilutes Goal-Gradient Pull

**SECTION:** header-quick-filter
**ELEMENT:** `banner` at e14 (y=0, content `FREE SHIPPING on most orders $75+`)
**SOURCE:** BOTH
**PRIORITY:** LOW

**OBSERVATION:** The site-wide announcement bar reads `FREE SHIPPING on most orders $75+`. The $75 threshold is a concrete anchor — that part is strong. However, `on most orders` hedges the promise without explanation: visitors don't know whether their item type, size, or location excludes them. The goal-gradient effect requires a perceived achievable goal; ambiguous eligibility disrupts goal formation.

**RECOMMENDATION:** Replace `on most orders $75+` with a cleaner threshold statement. If all standard-size orders qualify, write `FREE SHIPPING on orders $75+` with no qualifier. If exclusions exist (oversized parts, freight items), list them specifically in a tooltip or a linked page rather than burying them in the headline copy. A progress bar in the cart drawer showing exact distance to $75 would further operationalize the threshold.

**Why this matters:** Vague threshold copy undermines the $75 goal as a conversion lever; clarifying it costs a single copy edit and directly reduces the 39% of cart abandoners who cite unexpected shipping costs as a primary reason.

▸ free-shipping.md, Finding 1 (Kivetz et al. 2006) [Gold]

#### pricing F-08 — Charm Pricing Applied Consistently Across Featured Cards

**SECTION:** featured-collection
**ELEMENT:** `span.price` at e27 (content `From $135.99`)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** $135.99 uses a .99 ending on a utilitarian accessory (floor mats), appropriate for the product type and brand positioning. Troll & Wieseke (2024) meta-analysis confirms just-below pricing produces a statistically reliable positive effect on purchase intentions (d = 0.11) for non-luxury goods. $49.00 for the decal kit uses a round ending — also defensible, as round prices on smaller-ticket items reduce cognitive friction without the charm-pricing benefit being material at that price level.

**RECOMMENDATION:** No change required. The .99 ending on $135.99 is well-calibrated. If future variants or bundles are priced above $199, maintain the .99 or .95 ending to preserve the left-digit effect.

**Why this matters:** Maintaining charm pricing on mid-ticket utilitarian products is a low-cost optimization that preserves a small but real purchase-intention advantage.

▸ charm-pricing.md, Finding 1 (Troll & Wieseke 2024) [Gold]

### Trust & Credibility

#### trust-credibility F-02 — Featured Product Has 2 Reviews at Perfect 5.0 — Below Threshold and Suspect Rating

**SECTION:** featured-collection
**ELEMENT:** `div.rating` at e26 (content `5.0 / 5.0 (2) 2 total reviews`)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The Revo Designs Rocker Stripes Decal Kit card displays a rating of 5.0 / 5.0 derived from exactly 2 reviews. This is below the 5-review threshold where purchase likelihood jumps 270% (Spiegel Research Center, Northwestern), and a perfect 5.0 rating is the precise configuration that triggers skepticism — Spiegel's research confirms purchase likelihood peaks at 4.0–4.7 and decreases as ratings approach 5.0. The VelourTex Carpet Floor Mats card (`From $135.99`) displays no rating or review count whatsoever, leaving a $135.99+ product with zero social proof on the homepage.

**RECOMMENDATION:** For the Revo Designs card: implement a post-purchase email review request triggered by delivery confirmation, sent 7–14 days post-delivery, targeting all buyers of this SKU. The goal is reaching 5 verified reviews — at that threshold the conversion lift is documented at 270%. Do not artificially inflate the rating by soliciting only satisfied customers; the 4.0–4.7 range converts better than 5.0. For the VelourTex card: this higher-AOV product receives a 380% conversion lift from reviews per Spiegel's price-segmented data — prioritize review collection for this SKU. If zero reviews exist, suppress the star widget entirely rather than showing an empty state.

**Why this matters:** Products under 5 reviews lose the majority of the conversion lift that social proof provides. On a homepage featuring only a handful of products, a 2-review card with a suspicious perfect score actively undermines the credibility AWDMods needs as an independent specialty retailer competing without Amazon's brand equity.

▸ trust-and-credibility.md, Finding 3 (Spiegel Research Center) [Gold]

#### trust-credibility F-03 — No Trust Badges Near Any CTA — Payment Icons Confined to Footer Only

**SECTION:** newsletter-footer
**ELEMENT:** `list` at e32 (y=1629, content `American Express Apple Pay Discover Google Pay Mastercard...`)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** Across all four page sections, payment-method icons appear exclusively in the footer (e32, scroll_y 1629+). No security seal, money-back guarantee, or return policy indicator is present near any product card, above-fold CTA, or add-to-cart action. Baymard's research confirms trust badges placed in headers or footers are perceived as generic and do not convey that the payment process specifically is secure — the proximity effect requires placement at the moment of purchasing anxiety. PayPal (67% eye-tracking notice rate, CXL Institute) is present in the footer icon row but receives no attention-driving placement where purchase decisions are made.

**RECOMMENDATION:** Add a compact trust bar — 2–3 badges maximum — directly beneath the product cards in the Featured Collection section, where a shopper's next action is clicking through to purchase. The bar should include PayPal (already accepted, highest recognition) and one additional signal: either a `Free Shipping $75+` reassurance badge or a `30-Day Returns` badge if that policy exists. Do not replicate the full footer payment grid; 2–3 well-chosen marks at the conversion point outperform a grid of 8 icons confined to the footer.

**Why this matters:** AWDMods is an independent specialty retailer without the brand recognition of Amazon or AutoZone. For this audience segment, trust signals must appear where purchase decisions occur. Footer-only placement means shoppers who do not scroll to the bottom — the majority on mobile — never encounter a trust signal before bouncing.

▸ trust-and-credibility.md, Finding 23 (Google Quality Rater Guidelines) [Gold]

#### trust-credibility F-06 — Return Policy Absent From Homepage — No Visible Link or Snippet in Any Section

**SECTION:** newsletter-footer
**ELEMENT:** `contentinfo` at e30 (y=1461, content `Information About Us`)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The footer's `Information` accordion is collapsed on mobile (e30, scroll_y 1461+), meaning any return or shipping policy links inside are invisible without a tap interaction. No return policy text, summary badge, or `Easy Returns` indicator appears in any of the four page sections. Google's Quality Rater Guidelines identify a clearly stated return policy linked from the product page as a required Trustworthiness element for high-Trust ratings.

**RECOMMENDATION:** If AWDMods offers returns, surface a one-line policy summary — `Free returns within 30 days` or equivalent — as a text line or small badge near the featured product cards. Add to the same trust bar recommended in `trust-credibility F-03`. Additionally, expand the footer Information accordion by default on mobile, or ensure return/shipping links appear as visible text rather than behind a collapsed interaction.

**Why this matters:** First-time visitors to an independent automotive parts retailer carry meaningful purchase risk anxiety — incorrect fitment or product dissatisfaction has no obvious resolution if no return policy is visible. Eliminating that anxiety before the click-through to a product page reduces friction at the highest-dropout stage of the funnel.

▸ trust-and-credibility.md, Finding 20 (Signifyd 2024) [Bronze]

#### trust-credibility F-07 — No Expert Editorial Content — Homepage Carries Only Category Navigation and Product Cards

**SECTION:** featured-collection
**ELEMENT:** `(absent — proposed location: 3-4 sentence expert-voice block beneath Featured Collection)`
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** Across all four page sections, no expert editorial content is present: no staff picks with fitment rationale, no `vehicles we know best` copy, no technical orientation for new visitors. The homepage communicates category breadth and a vehicle finder, but nothing that demonstrates AWDMods' deep platform knowledge of the Focus RS, Focus ST, WRX, or STI vehicles it explicitly names in the newsletter copy. Google's Quality Rater Guidelines identify expert editorial content — fitment compatibility notes, installation difficulty ratings, known issues the manufacturer omits — as a key Expertise signal that differentiates a focused retailer from a generic reseller.

**RECOMMENDATION:** Add a short expert-voice block beneath the Featured Collection section — 3–4 sentences establishing AWDMods' focus (`We specialize in Focus RS/ST and WRX/STI builds; every part we carry is one we've tested or installed ourselves`) alongside 1–2 staff-pick callouts for currently featured products that name a specific fitment or installation note. Copy change, not a UI redesign. For technically complex products (exhausts, intakes, suspension), brief fitment notes (`Fits Focus RS 2016–2018 with stock subframe`) are the clearest Expertise signal possible.

**Why this matters:** Without editorial voice, AWDMods looks identical to a generic drop-shipper aggregating the same catalog. Automotive performance shoppers research extensively and trust specialists over generalists — demonstrating domain knowledge on the homepage is the differentiator that earns the product-page click from a comparison shopper.

▸ trust-and-credibility.md, Finding 24 (Google Quality Rater Guidelines) [Gold]

#### trust-credibility F-08 — OnlineStore Schema Incomplete — Missing AggregateRating and Physical Address

**SECTION:** newsletter-footer
**ELEMENT:** `script[type="application/ld+json"]` (OnlineStore block; no address, telephone, contactPoint, AggregateRating)
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** The page head carries two JSON-LD blocks: an OnlineStore schema and a WebSite schema with SearchAction. The OnlineStore schema includes the site name, logo URL, and social `sameAs` links (Facebook, Instagram, YouTube), but omits a physical address, telephone, and email — three elements Google's Quality Rater Guidelines identify as required Trustworthiness signals for unknown brands. Several `sameAs` entries are empty strings (`''`), suggesting incomplete setup. No AggregateRating schema is present at the store or product level.

**RECOMMENDATION:** Complete the OnlineStore schema: add an `address` property with PostalAddress (streetAddress, addressLocality, addressRegion, postalCode, addressCountry), a `telephone` property, and a `contactPoint` or `email`. Remove the empty-string `sameAs` entries. On product pages, add AggregateRating schema once review counts meet the 5-review threshold. The SearchPilot controlled test cited in `ugc-reviews-seo.md` found ~20% organic traffic uplift from adding AggregateRating schema alone.

**Why this matters:** Schema markup makes existing trust signals machine-readable for Google. A physical address in structured data directly satisfies the Trustworthiness pillar that quality raters evaluate for unknown brands. Empty `sameAs` fields are a low-signal indicator that the schema was partially configured and abandoned.

▸ eeat-product-pages.md, Finding 9 (Google) [Gold]

#### trust-credibility F-11 — Product Images Carry Descriptive Alt Text — Accessibility Baseline Met

**SECTION:** featured-collection
**ELEMENT:** `img` at e22 (alt `VelourTex Fitted Carpet Floor Mats for the Ford Focus RS / ST (Set of 4)`)
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** All four featured product card images (e22–e25) carry descriptive alt text that names the product, compatible vehicle, and variant detail. This matches the recommended formula (`[Product Name] — [Variant/Context]`) and passes the WebAIM Million benchmark that 53.1% of pages fail.

**RECOMMENDATION:** Maintain this standard. As inventory expands, enforce the alt text template at the product data level so new SKUs inherit descriptive text automatically rather than requiring post-upload edits.

**Why this matters:** Descriptive alt text serves screen reader users, improves image SEO indexability, and is among the lowest-effort accessibility wins available.

▸ accessibility.md, Finding 1 (WebAIM) [Gold]


### Content & SEO

#### content-seo F-02 — Title Tag Is 16 Characters — Rewritten >95% of the Time

**SECTION:** page-head
**ELEMENT:** `<title>` (content `AWDMods - AWDMods`, 17 chars)
**SOURCE:** DOM
**PRIORITY:** HIGH

**OBSERVATION:** The page title is `AWDMods - AWDMods` — 17 characters and a duplicate of the brand name with no descriptive content. Zyppy's Q1 2025 study of 81,000 titles found that titles under 30 characters are rewritten by Google more than 95% of the time. The current title gives Google no usable signal about what the store sells, which categories are available, or who the target customer is.

**RECOMMENDATION:** Rewrite to the formula `[Store Type] - [Key Vehicle Coverage] | [Brand]`. Example: `Performance Parts for Focus RS, WRX & STI | AWDMods` (51 characters). Edit the home-template SEO snippet so the title is rendered server-side at first parse.

**Why this matters:** Google rewrites titles that are too short with whatever copy it finds most relevant on the page — often the H1 or a navigation link. A store with a 17-character title is surrendering complete control over how it appears in search results.

▸ title-formulas-serp-psychology.md, Finding 3 (Zyppy 2025) [Gold]

#### content-seo F-04 — No Meta Description — OG Description Is Also `AWDMods`

**SECTION:** page-head
**ELEMENT:** `meta[name="description"]` absent; `meta[property="og:description"]` content `AWDMods`
**SOURCE:** DOM
**PRIORITY:** HIGH

**OBSERVATION:** There is no `<meta name='description'>` tag on the page. The `og:description` property is present but contains only `AWDMods` — no store description, no vehicle coverage, no value proposition. Google will generate a snippet by extracting whatever text it finds most relevant, likely category navigation labels or the newsletter copy. The `og:description` also powers social share previews; `AWDMods` as a social preview description provides no context for click-through.

**RECOMMENDATION:** Write a meta description of 140–155 characters that names the store's vehicle coverage, product categories, and a single differentiator. Example: `Shop performance parts, exterior mods, and accessories for the Ford Focus RS, Focus ST, Subaru WRX, and STI. Free shipping on orders $75+.` (152 characters). Apply the same text to `og:description` for social sharing consistency.

**Why this matters:** Google auto-generates snippets for pages without meta descriptions, and auto-generated snippets often pull from navigation menus or boilerplate text. A well-written meta description acts as a free ad in the SERP.

▸ title-formulas-serp-psychology.md, Finding 1 (Backlinko) [Gold]

#### content-seo F-06 — No Product or Merchant Schema — Homepage Has Only OnlineStore and WebSite Types

**SECTION:** page-head
**ELEMENT:** `script[type="application/ld+json"]` (OnlineStore + WebSite blocks; no Product/Offer/AggregateRating/MerchantReturnPolicy)
**SOURCE:** DOM
**PRIORITY:** HIGH

**OBSERVATION:** The only structured data on the page is an OnlineStore block (brand identity) and a WebSite block (SearchAction). Product-level schema — `@type Product`, `Offer`, `AggregateRating`, `MerchantReturnPolicy` — is entirely absent. Featured product cards show products with prices and star ratings, but none of this data is exposed in JSON-LD. AWDMods is ineligible for Google Shopping rich results, star ratings in SERPs, ChatGPT Shopping (launched 2025-09-29), and Perplexity product cards on this page.

**RECOMMENDATION:** Add JSON-LD Product markup for the featured collection products surfaced on the homepage. Each featured product card should emit `@type Product` with `name`, `image`, `offers` (price, priceCurrency, availability, url), and `aggregateRating` where reviews exist. Add `MerchantReturnPolicy` to the OnlineStore block. For Shopify, update the homepage Liquid template to inject product schema for each featured_collection product in the section.

**Why this matters:** SearchPilot's controlled test found that adding `AggregateRating` schema alone produced approximately 20% organic traffic uplift. Without any Product schema, AWDMods cannot appear in Google Shopping carousels, cannot surface in ChatGPT Shopping comparisons, and loses every star-rating rich result opportunity.

▸ schema-product-markup.md, Finding 10 (SearchPilot) [Gold]

#### content-seo F-07 — No H1 on Homepage — Highest Heading Is H2

**SECTION:** page-heading-structure
**ELEMENT:** `(absent — H2s present at `Featured Collection`, `Join Our Newsletter!`, `Information`, `My Account`)`
**SOURCE:** DOM
**PRIORITY:** HIGH

**OBSERVATION:** The AWDMods homepage has no H1 element. The page jumps directly to H2 headings. Without an H1, there is no semantic anchor for Google to confirm what the page's primary topic is, and the H1/title alignment strategy — which reduces Google's title rewrite rate from 76% to approximately 20% — cannot be implemented.

**RECOMMENDATION:** Add a visually prominent H1 to the hero section that names the store's core value proposition and vehicle coverage. If the hero image cannot accommodate visible text, a visually hidden (CSS off-screen) H1 is acceptable for SEO purposes. Suggested text: `Performance Parts and Accessories for Ford Focus RS, Focus ST, Subaru WRX & STI`. This H1 then becomes the semantic anchor to align the title tag against, reducing rewrite risk on both.

**Why this matters:** Zyppy's Q1 2025 data shows H1 and title alignment is the single highest-leverage defense against Google title rewrites, dropping the rewrite rate from 76% to ~20%. Without any H1, the page has no alignment possible.

▸ title-formulas-serp-psychology.md, Finding 12 (Zyppy 2025) [Silver]

#### content-seo F-09 — No og:image — Social Shares and AI Thumbnails Will Be Blank

**SECTION:** page-head
**ELEMENT:** `meta[property="og:image"]` (absent)
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** The page has no `og:image` tag. When the AWDMods homepage is shared on Facebook, Twitter/X, iMessage, Slack, or LinkedIn, the preview will render with no image — a blank thumbnail or a platform-chosen fallback. AI shopping agents and browsers that generate link previews will also lack a visual anchor. The homepage contains high-quality photography (hero section showing a WRX in a cinematic night setting) that could serve as an effective `og:image`.

**RECOMMENDATION:** Add `<meta property="og:image" content="[absolute URL to the hero image]">` pointing to a 1200×630px crop of the homepage hero photograph. Also add `og:image:width` and `og:image:height` tags. For Twitter, add `<meta name="twitter:image">` with the same URL. The image should be pre-sized to exactly 1200×630 to prevent platform-side auto-cropping.

**Why this matters:** Pages without `og:image` lose the single highest-visibility element in social and messaging link previews. In automotive communities where enthusiasts share links in Discord servers, Facebook groups, and iMessage threads, a blank thumbnail dramatically reduces click-through on those shares.

▸ ai-search-agentic-discovery.md, Finding 10 (Google) [Gold]

#### content-seo F-11 — Homepage Has No Product Description Content — AI Agents Cannot Extract Answers

**SECTION:** page-description
**ELEMENT:** `(absent — no body copy or store description text)`
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The AWDMods homepage contains no store description, no brand positioning statement, and no body copy that explains what AWDMods sells, which vehicles it supports, or why a shopper should buy from AWDMods over a competitor. The only text content visible is: category navigation labels, featured product card titles, and the newsletter signup copy. AI shopping agents (ChatGPT Shopping Research, Perplexity) that crawl the page to answer `What does AWDMods sell?` will find no extractable answer.

**RECOMMENDATION:** Add a 2–3 sentence store description to the homepage, placed between the hero vehicle finder and the category carousel. The copy should answer: what product categories are available, which vehicles are supported, and what makes AWDMods the right choice. Example: `AWDMods specializes in performance, exterior, and interior upgrades for the Ford Focus RS, Focus ST, Subaru WRX, and WRX STI. Every part is fitment-tested for your platform — shop by vehicle to see only what fits your build.` This copy also becomes the source material for the meta description (`content-seo F-04`).

**Why this matters:** A homepage without any descriptive text is invisible to AI shopping agents attempting to qualify AWDMods as a vendor. As ChatGPT Shopping and Perplexity grow their share of product discovery queries, stores with extractable positioning copy will be surfaced over those without.

▸ benefit-first-descriptions.md, Finding 2 (CXL) [Gold]

#### content-seo F-12 — sameAs Array in OnlineStore Schema Contains Empty Strings

**SECTION:** page-head
**ELEMENT:** `script[type="application/ld+json"]` (OnlineStore.sameAs has 12 entries; 9 are empty strings)
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** The OnlineStore JSON-LD block has a `sameAs` array with 12 entries, 9 of which are empty strings (`''`) rather than valid URL values. Google's structured data validator will flag empty string values in `sameAs` as malformed — they are not valid URL format. The three legitimate entries (Facebook, Instagram, YouTube) are correct, but the empty entries create schema validation errors that may affect Google's confidence in the entire block.

**RECOMMENDATION:** Remove all empty string entries from the `sameAs` array, keeping only the three valid social profile URLs: `sameAs: ['https://www.facebook.com/awdmods', 'https://www.instagram.com/awdmods', 'https://www.youtube.com/@AWDMods']`. In Shopify Liquid, this is in the theme's layout or SEO snippet — remove empty entries from the template that generates the array.

**Why this matters:** Malformed structured data can trigger Google Search Console rich result validation errors and reduce confidence in the store's brand knowledge graph entity. Empty `sameAs` entries signal incomplete template implementation.

▸ schema-product-markup.md, Finding 15 (Google) [Gold]

#### content-seo F-15 — Canonical Tag Is Self-Referencing, HTTPS, and Lowercase

**SECTION:** page-head
**ELEMENT:** `link[rel="canonical"]` (href `https://www.awdmods.com/`)
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** The canonical tag is correctly implemented: absolute HTTPS URL, lowercase, self-referencing, and matches the captured page URL exactly. No trailing slash inconsistency.

**RECOMMENDATION:** No action required. Continue verifying canonical tags after any theme updates, as Shopify theme modifications can inadvertently break canonical implementation.

**Why this matters:** A correctly implemented self-referencing canonical prevents Google from selecting an alternate URL variant as the canonical, protecting link equity consolidation.

▸ canonical-duplicate-content.md, Finding 12 (CXL) [Silver]

#### content-seo F-17 — Viewport Meta Tag Present — Mobile-Ready Signal Confirmed

**SECTION:** page-head
**ELEMENT:** `meta[name="viewport"]` (content `width=device-width,initial-scale=1`)
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** The viewport meta tag is correctly implemented with `width=device-width,initial-scale=1`, confirming proper mobile viewport configuration. This is the prerequisite for Google's mobile-first indexing and prevents the double-tap-to-zoom behavior that degrades mobile conversion.

**RECOMMENDATION:** No action required.

**Why this matters:** Without a correct viewport meta tag, Google's mobile-first indexing treats the page as non-mobile-optimized, which can suppress rankings on mobile queries.

▸ title-formulas-serp-psychology.md, Finding 12 (Zyppy 2025) [Silver]

#### content-seo F-18 — Product Card Alt Text Is Descriptive and Follows [Product Name] Template

**SECTION:** featured-collection
**ELEMENT:** `img` at e22 (alt `VelourTex Fitted Carpet Floor Mats for the Ford Focus RS / ST (Set of 4)`)
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** All four featured collection product card images (e22–e25) carry descriptive alt text following the `[Brand] [Product Name] [Fitment]` template. Each alt text is informative, fitment-specific, and under 80 characters. No keyword stuffing detected.

**RECOMMENDATION:** No action required for the featured product card images. Maintain this alt text pattern for all product images site-wide.

**Why this matters:** Correctly described product images are indexed for Google Images and eligible for Google Lens visual search.

▸ image-seo-alt-text.md, Finding 2 (Google) [Gold]

### Checkout Flows

#### checkout-flows F-01 — No Express Checkout Buttons in Cart Drawer or Buy-Box

**SECTION:** cart-drawer
**ELEMENT:** `(absent — cart drawer e17 element exists in DOM but contains no wallet buttons)`
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The cart drawer element (e17) is present in the page DOM but was empty at capture — no Apple Pay, Google Pay, or Shop Pay buttons appear inside it. No express checkout buttons exist anywhere in the above-fold header area or on the product cards in the featured collection. On mobile, where 70%+ of Shop Pay transactions originate, the absence of wallet buttons means every buyer must navigate through the full checkout form.

**RECOMMENDATION:** Enable the `dynamic checkout buttons` setting on product forms and within the cart drawer in Shopify. This surfaces Apple Pay, Google Pay, or Shop Pay (whichever matches the shopper's device and configured wallets) as a single-tap payment path above the standard `Checkout` button. Place these buttons at the top of the cart drawer, before the email or address fields, so mobile visitors can complete purchase in 1-2 taps from any page.

**Why this matters:** Stripe's controlled A/B testing shows express checkout buttons placed at the top of the flow convert at approximately 2x the rate of buttons placed at the end. Apple Pay specifically delivers a +22.3% conversion lift. For a mobile-first automotive accessories store where the average visitor browses on a device with a digital wallet already configured, the missing express path is the single highest-leverage checkout fix available.

▸ biometric-and-express-checkout.md, Finding 6 (Stripe) [Silver]

#### checkout-flows F-03 — Payment Method Icons Footer-Only — Not Surfaced Pre-Cart

**SECTION:** newsletter-footer
**ELEMENT:** `list` at e32 (y=1629, content `American Express Apple Pay Discover Google Pay Mastercard...`)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The store lists 8 payment methods (American Express, Apple Pay, Discover, Google Pay, Mastercard, PayPal, Shop Pay, Visa) as icon badges in the footer at approximately scroll_y 1629 — visible only after the visitor has scrolled past the newsletter section. Payment variety is strong, meeting the 4-method minimum with significant margin, but the icons appear only after the fold. No payment method indicators appear near the product cards, in the cart drawer, or anywhere in the purchase path.

**RECOMMENDATION:** Add payment method icons or a brief `Accepts:` line near product-card buy buttons or within the cart drawer summary. On Shopify, this can be done by adding the payment-methods Liquid snippet to the cart drawer template. Showing familiar logos (especially PayPal and Shop Pay) close to the `Add to Cart` action reassures hesitant buyers before they commit to clicking through to checkout.

**Why this matters:** Stripe's testing found that surfacing at least one additional relevant payment method beyond cards drove a 7.4% conversion increase and 12% revenue increase on average. When a shopper cannot quickly confirm that PayPal or Shop Pay is available, they face a micro-uncertainty that adds friction to the decision to proceed.

▸ checkout-optimization.md, Finding 14 (Stripe) [Silver]

#### checkout-flows F-05 — Cart Drawer Lacks Shipping Progress and Subtotal Confirmation

**SECTION:** cart-drawer
**ELEMENT:** `cart-drawer` at e17 (custom element; empty at capture)
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** The cart drawer (e17) exists as a custom element in the page DOM but was empty at capture. The DOM does not reveal whether the open drawer displays a subtotal, a `free shipping progress` bar toward the $75 threshold, or a running estimated total. Without a shipping progress bar inside the drawer, the announcement bar's threshold message is disconnected from the in-cart experience.

**RECOMMENDATION:** Add a free-shipping progress bar to the cart drawer that shows the gap between the current cart subtotal and the $75 free shipping threshold (`You're $23 away from free shipping`). This is a native feature in several Shopify cart drawer apps and available as a Liquid/JavaScript addition. The bar should update dynamically as items are added or removed. Confirm the open drawer shows a clear subtotal before the `Checkout` button.

**Why this matters:** Baymard's research identifies 39-48% of actionable cart abandonment as cost-surprise driven. A real-time progress bar toward the free shipping threshold directly motivates shoppers to increase cart size while signaling that the final checkout cost will not surprise them.

▸ checkout-optimization.md, Finding 4 (Baymard) [Gold]

#### checkout-flows F-08 — Free Shipping Threshold Visible Above the Fold

**SECTION:** announcement-bar
**ELEMENT:** `banner` at e14 (y=0, content `FREE SHIPPING on most orders $75+`)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The page leads with a blue announcement bar reading `FREE SHIPPING on most orders $75+` visible at scroll_y=0 without any user interaction. Visitors understand the shipping cost structure before they add any product to cart, removing the primary trigger for late-funnel abandonment.

**RECOMMENDATION:** The current implementation is effective. If the store offers free shipping on all orders (not just `most`), updating the copy to remove the qualifying word `most` would eliminate residual uncertainty. If `most` reflects a genuine product exclusion (e.g., oversized exhaust systems), add a tooltip or link clarifying which items are excluded.

**Why this matters:** Baymard's multi-year research finds 39% of actionable cart abandonment is triggered by extra costs appearing late. Surfacing the shipping threshold on the first visible row is the single most direct treatment for this abandonment cause.

▸ checkout-optimization.md, Finding 1 (Baymard) [Gold]

### Performance & UX

#### performance-ux F-02 — Hamburger-Only Navigation Hides Primary Destinations

**SECTION:** header-quick-filter
**ELEMENT:** `button` at e3 (hamburger toggle, top-left of sticky header)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The entire site navigation — Shop by Category, Shop by Vehicle, Contact, and My Account — lives behind a hamburger menu icon in the top-left corner. No persistent bottom navigation bar is present. On a 390px mobile viewport, the primary discovery paths (category browsing, vehicle-specific shopping) are invisible until the user taps a small icon. NNGroup research confirms hidden navigation consistently underperforms on discoverability; switching to visible bottom navigation increases engagement by 25–50% and reduces task completion time by 22%.

**RECOMMENDATION:** Implement a persistent bottom navigation bar with 4–5 destinations: Home, Search, Shop by Category (or Browse), Cart, Account. Reserve the hamburger for the full secondary category tree. The bottom bar should remain visible during scroll and display a badge count on Cart.

**Why this matters:** 70% of users prefer bottom navigation over hamburger menus for essential functions. For a specialty parts store where vehicle compatibility is the primary filter, hiding `Shop by Vehicle` behind a hamburger creates an extra tap on every mobile session before a visitor can start shopping.

▸ mobile-conversion.md, Finding 13 (NNGroup) [Gold]

#### performance-ux F-05 — Hero Vehicle Selector Dropdowns — Four Sequential Decisions Before Finding Parts

**SECTION:** header-quick-filter
**ELEMENT:** `banner` at e14 (vehicle selector with 4 dropdowns: Make, Model, Year, Trim)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The mobile hero presents four sequential dropdown selectors — Select Make, Select Model, Select Year, Select your Trim — as the primary above-fold CTA. On mobile, dropdowns are the highest-friction input pattern: each tap opens an OS-native picker, the user makes a selection, and the picker closes before the next dropdown can be used. Four sequential decisions must be completed in order before the FIND PARTS button activates. Hick's Law confirms that each additional required decision adds logarithmically to response time and cognitive cost.

**RECOMMENDATION:** Replace the four sequential dropdowns with a single predictive search input (`Type your vehicle — e.g., 2018 Subaru WRX`) that resolves Make/Model/Year/Trim in one gesture. A single text input with autocomplete triggers one keyboard interaction versus four dropdown interactions. Alternatively, if the dropdown flow is retained, default the Make selector to the most-purchased vehicle to reduce active selections from 4 to 3 for the majority of visitors.

**Why this matters:** The vehicle selector is the first conversion step for new visitors — an unsuccessful or frustrating vehicle selection experience drops users before they see a single product. Every additional mandatory decision corresponds to measurable drop-off; reducing sequential steps directly improves the rate at which visitors reach vehicle-filtered product listings.

▸ cognitive-load-management.md, Finding 1 (Hick & Hyman) [Gold]

#### performance-ux F-07 — Carousel Swipe Handler and Scroll Indicator Present

**SECTION:** category-carousel
**ELEMENT:** `slider-component` at e8 area (scrollbar indicator strip below cards)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The category carousel implements a `<slider-component>` with the `slider--scroll-active` and `grid--peek` CSS classes, producing a partial-card peek of the next slide at the right edge. The screenshot confirms the Handling & Brakes card is partially visible, correctly signaling to users that the carousel is swipeable. A scrollbar indicator strip appears below the cards.

**RECOMMENDATION:** The swipe affordance implementation is sound. If conversion tracking shows low carousel engagement, the scrollbar indicator could be supplemented with higher-contrast dot indicators or numbered pagination (`1 of 5`) for users who miss the peek affordance.

**Why this matters:** Mobile users default to swiping for image and content carousels. When the swipe gesture expectation is confirmed by a visible peek affordance, users engage more with carousel content without confusion.

▸ mobile-conversion.md, Finding 9 (Baymard) [Gold]

#### performance-ux F-09 — Sticky Header Preserves Navigation Access on Scroll

**SECTION:** header-quick-filter
**ELEMENT:** `div` at e18 (`is_sticky: true`)
**SOURCE:** BOTH
**PRIORITY:** LOW

**OBSERVATION:** The sticky header element (e18) is confirmed sticky by both the captured element data and screenshots across sections 2, 3, and 4 — the header with logo, hamburger, account, and cart icons persists at the top of the viewport across all scroll positions. The cart icon (e6) is persistently accessible.

**RECOMMENDATION:** The sticky header is correctly implemented. The remaining gap — that the hamburger navigation is the only access point for category browsing — is addressed in `performance-ux F-02`.

**Why this matters:** Cart abandonment on mobile is 78–80%; maintaining persistent cart access reduces friction at the transition to checkout by keeping the cart icon visible at all times.

▸ mobile-conversion.md, Finding 1 (Baymard) [Bronze]

### Product Media

#### product-media F-01 — Category Carousel Uses JS Scroll Component — No CSS Scroll-Snap

**SECTION:** category-carousel
**ELEMENT:** `slider-component` at e9 area (class `slider--scroll-active`; no scroll-snap declarations)
**SOURCE:** DOM
**PRIORITY:** HIGH

**OBSERVATION:** The category swipe carousel is powered by a custom `<slider-component>` JavaScript element (Shopify Dawn-derived). The DOM contains no `scroll-snap-type` or `scroll-snap-align` declarations. The class `slider--scroll-active` confirms JavaScript intercepts scroll events to manage swipe. JS scroll interception on mobile creates friction when users attempt natural swipe gestures and produces less-smooth animation than hardware-accelerated CSS scroll-snap.

**RECOMMENDATION:** Replace the JS scroll-interception approach with CSS scroll-snap on the carousel list: add `scroll-snap-type: x mandatory` to the `<ul>` container and `scroll-snap-align: start` to each `<li>` slide. This hands swipe behavior to the browser compositor thread, eliminating JS scroll-conflict jank on iOS Safari and Android Chrome. The existing `slider-button` prev/next controls can remain as progressive enhancement.

**Why this matters:** Mobile users expect swipe gestures to work like native app behavior. JavaScript scroll interception is the most common cause of broken swipe patterns on mobile — it causes scroll-direction conflicts that result in accidental page scroll instead of card swipe. A broken swipe experience on the homepage category carousel creates an immediate negative first impression.

▸ thumbnail-design.md, Finding 5 (Baymard) [Gold]

#### product-media F-05 — All Category Card Background Images Have Empty Alt Text

**SECTION:** category-carousel
**ELEMENT:** `img` at e8 area (5 carousel cards; all alt="")
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** Every background image in the five category tiles (Performance, Handling & Brakes, Interior, Exterior, Electronics) carries `alt=""`. While empty alt is technically valid for decorative images, these images depict the product category content and serve as the primary visual anchor for each tile. Screen reader users navigating the carousel receive no image description — the card is announced solely by the heading text and subcategory list.

**RECOMMENDATION:** Add descriptive alt text to each category card image that describes the visual content shown, not just repeats the heading. For example: the Performance card image showing a turbocharger and intake manifold should read `alt="Turbocharger and cold air intake performance parts"` rather than `alt="Performance"` (which duplicates the heading). This passes WCAG 1.1.1 Non-text Content and provides useful context to users on slow connections.

**Why this matters:** WCAG 2.1 Level A requires informative images to have descriptive alt text. The EU European Accessibility Act (effective June 28, 2025) makes accessibility non-compliance a legal exposure for EU-facing merchants. Image alt text on category cards is also indexed by Google Image Search.

▸ gallery-ux.md, Finding 9 (W3C WCAG) [Gold]

### Category Navigation

#### category-navigation F-03 — Vehicle Compatibility Finder Siloed in Hero — Not Connected To Category Navigation

**SECTION:** header-quick-filter
**ELEMENT:** `button` at e5 (`Shop by Vehicle` hamburger drawer item; vehicle selector at e14 hero area)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** AWDMods sells vehicle-specific parts. A `Select Make / Model / Year / Trim` compatibility widget is embedded inside the homepage hero section, but it functions as a standalone search redirect — not as a persistent filter that follows visitors into category pages. Once a shopper selects their vehicle and lands on a collection, there is no visible `Showing parts for: Ford Focus RS` confirmation, no ability to re-filter by vehicle from within a category, and the hamburger `Shop by Vehicle` drawer requires re-entry of the vehicle context from scratch on every session.

**RECOMMENDATION:** If vehicle data can be persisted in a session cookie or localStorage after the FIND PARTS submission, surface a sticky `Vehicle: Ford Focus RS` chip below the site header that remains visible on all collection pages and can be changed or cleared. This confirmation chip serves three purposes: it reassures the visitor their fitment filter is active, it disambiguates results for cross-compatible parts, and it reduces repetitive vehicle re-selection. A secondary improvement is surfacing the compatibility finder as an inline filter within collection page headers.

**Why this matters:** Baymard research documents 65% task failure rates on automotive and electronics sites where compatibility filters are absent or disconnected from the browsing flow. Visitors who cannot confirm their selected vehicle is filtering results will either distrust the results or purchase an incompatible part — both outcomes are high-cost.

▸ search-and-filter-ux.md, Finding 5 (Baymard) [Gold]

#### category-navigation F-05 — Category Carousel Tiles Show No Product Counts

**SECTION:** category-carousel
**ELEMENT:** `div` at e8 (content `Performance ... Intakes Exhaust Cooling Drivetrain upgrades ... Shop Performance`)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The five category tiles in the horizontal swipe carousel each show a category name, 3–4 subcategory keyword lines, and a `Shop [Category]` CTA. No product count appears on any tile. The subcategory keywords are useful orientation signals, but a visitor cannot tell whether Performance has 12 products or 1,200 before tapping through.

**RECOMMENDATION:** Add a product count label to each category tile — `Performance (143 parts)` — sourced from the collection's product count in Shopify. The count requires no layout change beyond appending a small text line or badge to the existing tile structure.

**Why this matters:** Product counts on category tiles give visitors calibration before committing to a tap, reducing bounce when a category turns out to be smaller than expected.

▸ merchandising-psychology.md, Finding 8 (Baymard) [Silver]

#### category-navigation F-08 — Full-Width Inline Search Bar in Sticky Header

**SECTION:** header-quick-filter
**ELEMENT:** `search` at e15 (full-width input, sticky header, content placeholder `Search`)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The search field renders as a full-width visible input in the sticky header bar, present on every page scroll position without requiring an icon tap. The placeholder text reads `Search` and the field is immediately interactive on page load.

**RECOMMENDATION:** This pattern meets the mobile persistent search standard. No change required. Monitor that the search input remains visible at scroll_y=0 on all device sizes in the 390px viewport range.

**Why this matters:** A visible search entry point in the sticky header removes friction for visitors who know what part they need and arrive with a specific query.

▸ search-and-filter-ux.md, Finding 17 (NNGroup) [Gold]

#### category-navigation F-10 — Hamburger Drawer Navigation Lacks Category Product Preview

**SECTION:** header-quick-filter
**ELEMENT:** `button` at e4 (`Shop by Category` drawer item; reveals 9 text-only category links)
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** The `Shop by Category` submenu in the hamburger drawer reveals text-only links: Performance, Exterior, Interior, Handling, Drivetrain, Brakes, Cooling, Wheels, Accessories. Nine category links presented as a flat text list with no images, product counts, or subcategory hierarchy.

**RECOMMENDATION:** For the nine category items in the `Shop by Category` drawer, add a small category icon or thumbnail image (30–40px) to the left of each text label, and append the product count in a secondary text style. CSS and template change to the existing `<li>` items.

**Why this matters:** Text-only category lists in mobile drawers require users to parse each label sequentially, slowing navigation for first-time visitors who are not yet familiar with AWDMods' product taxonomy.

▸ merchandising-psychology.md, Finding 8 (Baymard) [Silver]

### Post-Purchase

#### post-purchase F-02 — No Loyalty Program Teaser on Homepage

**SECTION:** newsletter-footer
**ELEMENT:** `(absent — no loyalty teaser in newsletter; no Rewards entry in footer My Account accordion)`
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The AWDMods homepage carries no loyalty program signal anywhere — no points-teaser in the product area, no `Earn points on this purchase` copy in the newsletter section, no `Join Rewards` link in the footer `My Account` accordion. The footer accordion contains four links — My Account, Order History, Wish List, Track My Order — but no Rewards or Points entry.

**RECOMMENDATION:** If AWDMods has an active loyalty program, add an `Earn points on every order — join free` teaser to the newsletter section above the email input, and add a `Rewards` link to the footer `My Account` accordion. If no loyalty program exists yet, the newsletter section is the natural anchor for a `Join Rewards` enrollment CTA.

**Why this matters:** The confirmation page generates the highest loyalty enrollment rate (12-25% of new customers), but homepage awareness is what surfaces the program to returning visitors who missed the confirmation-page prompt. Without a loyalty signal on the homepage, repeat customers have no reminder that the program exists between orders.

▸ loyalty-programs.md, Finding 9 (Smile.io) [Bronze]

#### post-purchase F-03 — No Referral CTA in Footer or Newsletter Section

**SECTION:** newsletter-footer
**ELEMENT:** `(absent — no referral link in footer; no `Share with a friend` in newsletter)`
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** Neither the newsletter section nor the footer contains a referral program CTA. The footer `My Account` accordion links to My Account, Order History, Wish List, and Track My Order — but no referral or `Share with a friend` entry point. AWDMods has Facebook, Instagram, and YouTube social links in the footer, confirming social sharing infrastructure exists, but no mechanism connects that social presence to a structured referral incentive.

**RECOMMENDATION:** Add a referral link to the footer `My Account` accordion — `Refer a Friend, Earn $X` — pointing to a referral landing page. Frame the CTA in give-first language: `Give your friend $15 off. You get $15 too.` If a referral program does not exist, build one — the performance-mod community is highly word-of-mouth driven, and the 72-hour post-purchase window is where referral participation peaks.

**Why this matters:** Word-of-mouth referrals from existing customers in niche automotive enthusiast communities carry outsized credibility compared to paid acquisition — referred customers arrive pre-validated by a trusted peer.

▸ referral-programs.md, Finding 4 (Wharton) [Silver]

#### post-purchase F-06 — Order Tracking and Account Access Present in Footer

**SECTION:** newsletter-footer
**ELEMENT:** `heading` at e35 (`My Account` accordion in footer)
**SOURCE:** BOTH
**PRIORITY:** LOW

**OBSERVATION:** The footer `My Account` accordion includes `Track My Order` and `Order History` links, giving customers a persistent site-wide entry point to order status. This reduces WISMO (`Where Is My Order?`) friction for customers who return to the homepage after purchase.

**RECOMMENDATION:** The `Track My Order` link is a useful baseline. Surface it outside the collapsed accordion on mobile — a persistent `Track your order` text link above the footer would be immediately visible without requiring an accordion tap.

**Why this matters:** 96% of customers check order tracking at least once; providing a clear homepage-accessible path to tracking reduces support ticket volume and post-purchase anxiety for customers in the shipping window.

▸ order-confirmation.md, Finding 6 (Shopify) [Bronze]

### Audience

#### audience F-01 — Newsletter Framing Uses Vehicle Segments but Lacks Consent Clarity for Data Use

**SECTION:** newsletter-footer
**ELEMENT:** `section` at e29 (y=1629, content `Join Our Newsletter! New parts, new builds, exclusive deals...`)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The newsletter copy correctly names specific vehicle models (`Focus RS, Focus ST, WRX, or STI`), signaling segment-aware curation — this is effective audience framing. However, the form provides no indication of send frequency, content type beyond `parts and deals`, or what the subscriber is specifically agreeing to receive. The submit button has no visible accessible label beyond the arrow icon, and no inline description of what personal data is collected or how it is used. The `Your Privacy Choices` link exists in the footer but is three scroll interactions below the newsletter form.

**RECOMMENDATION:** Add a one-line sub-copy beneath the email field: `No spam — vehicle-specific parts drops and occasional deals only. Unsubscribe anytime.` This establishes the fair-value exchange that makes first-party data collection feel transparent rather than covert. Place a `Privacy Policy` inline link within one tap of the submit button so the consent context is visible at the moment of opt-in.

**Why this matters:** Consumers view first-party email opt-in as a fair trade — data for better experience — but only when the value exchange is explicit. Without frequency and content expectations set at signup, subscriber expectations go unmet, increasing unsubscribe rates and reducing the brand trust that makes email personalization effective.

▸ personalization-psychology.md, Finding 8 (CXL) [Silver]

#### audience F-02 — Domestic US Page Correctly Scoped — No Localization Defects

**SECTION:** header-quick-filter
**ELEMENT:** `(no hreflang tags; USD pricing; US-only payment methods)`
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** The page has no hreflang tags, a US-canonical URL (`awdmods.com`), USD pricing, and US-standard payment methods. No RTL content, no non-USD currency markers, no non-English copy. The page is correctly scoped as a domestic US storefront with no international presentation defects.

**RECOMMENDATION:** No cross-cultural changes required for the current domestic US presentation. If AWDMods expands to serve Canadian or international buyers, the first localization step should be local currency display and locally relevant payment methods.

**Why this matters:** Forcing cross-cultural localization requirements on a domestic US page would add unnecessary cost and complexity. The current setup is appropriate for the stated market.

▸ cross-cultural-considerations.md, Finding 5 (CXL) [Silver]

### Ethics

#### ethics F-01 — Privacy Policy Links to Staging Domain, Not Canonical Store

**SECTION:** footer-policy-links
**ELEMENT:** `contentinfo` at e30 (footer Information accordion; href `https://e1520g-k3.myshopify.com/policies/privacy-policy`)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The footer Privacy Policy link on both desktop and mobile points to `https://e1520g-k3.myshopify.com/policies/privacy-policy` — a `myshopify.com` staging subdomain — instead of a canonical first-party URL on `awdmods.com`. Every other footer link (About Us, Terms and Conditions, CARB Policy, Your Privacy Choices) correctly uses relative paths or the canonical domain. Only the Privacy Policy routes to the staging domain. The pattern is legally adjacent: GDPR Article 13 requires the controller to provide information `at the time personal data are obtained` via a clearly attributable notice; a privacy policy URL under a third-party domain (myshopify.com) rather than the merchant's own domain creates ambiguity about which entity controls the data and which policy governs the transaction. CCPA notice requirements similarly depend on visitors being able to identify the disclosing entity from the URL.

**RECOMMENDATION:** Update the Privacy Policy footer link to point to the canonical first-party URL. On Shopify, the standard path is `/policies/privacy-policy` (relative) or `https://www.awdmods.com/policies/privacy-policy` (absolute). In Shopify admin, navigate to Online Store > Navigation > footer menu, locate the Privacy Policy link, and replace the destination URL. Confirm the `Your Privacy Choices` page also links to the canonical policy rather than the staging domain.

**Why this matters:** A staging-domain privacy policy URL puts the site in a fragile compliance position. For any visitor from a GDPR-covered country (EU, UK, EEA) or California, the privacy policy is a legally required disclosure. If the staging domain is retired or access-restricted, visitors encounter a broken link at the exact moment they are trying to exercise their privacy rights — producing an active GDPR Art 13 and CCPA notice violation. The fix takes under two minutes in Shopify admin.

▸ ethics-gate.md, PART 6 — Regulatory Disclosure Chain (GDPR Art 13) [Gold]

## Methodology Notes

PASS findings (visual-cta F-07, visual-cta F-08, pricing F-08, trust-credibility F-11, content-seo F-15, content-seo F-17, content-seo F-18, checkout-flows F-08, performance-ux F-07, performance-ux F-09, category-navigation F-08, post-purchase F-06, audience F-02) are included in the per-section views above to confirm correct implementation. Six ethics CLEAR findings are recorded in the ethics-findings.json emission and not rendered into this document by default.
