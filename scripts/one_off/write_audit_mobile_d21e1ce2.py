"""One-off: write audit-mobile.md for engagement 2026-04-29-d21e1ce2.

Run from repo root:
    python scripts/one_off/write_audit_mobile_d21e1ce2.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "assembly"))

from atomic_write import atomic_write_text  # noqa: E402

ENGAGEMENT = "2026-04-29-d21e1ce2"
OUT = REPO_ROOT / "docs" / "ecp" / ENGAGEMENT / "audit-mobile.md"


CONTENT = """# Audit — SlingMods Can-Am Spyder F3-RT Handlebar End Weights PDP (mobile)

## Executive Summary

The mobile page is 3,297px tall — about four full viewports — and the only Add to Cart button sits at y≈860, gone after one swipe with no sticky bar to take its place. The H1 wraps to five lines and pushes the $59.95 price below the 844px fold on initial load. Trust and pricing signals are scattered: PayPal Pay Later renders inline at the price (good), but no MSRP anchor, no shipping line near the price, no sticky CTA, no risk-reversal microcopy under the Add to Cart, and no star distribution under the perfect-5.0 rating. The product video is buried below the buy zone, and the only customer photo (1 of 15 reviewers) is hidden behind a tab. Start with the sticky CTA bar and the buy-box concentration pass.

## Ethics Gate

CLEAR — no BLOCK or ADJACENT findings on this page. Seven ethics checks (urgency, schema-rating consistency, privacy URLs, Prop 65, cookie consent, subscription patterns, hidden-text SEO) all rendered CLEAR.

## Top Priorities

### Concentrate price, trust, and shipping signals into the buy-box

The $59.95 price block on this page does the work of one element when it should be doing the work of five. The price renders as a standalone number with no MSRP strikethrough or compare-at reference (`pricing F-01`), the $75 free-shipping threshold lives only in a footer footnote 1,600px below the price block (`pricing F-03`), the perfect 5.0 rating sits above the price with no star distribution to defuse skepticism (`trust-credibility F-02`), and the Add to Cart button has no risk-reversal microcopy adjacent to it — only an Add to Wishlist link (`visual-cta F-04`). Devs should pull these into a single price-block container above the ATC button: an MSRP or set-of-2 unit anchor, a 'Free shipping over $75' line near the price, a star-distribution bar under the aggregate rating, and a single 'Free shipping over $75 · 90-day returns' microcopy line under the ATC button. All four are template-level edits in one product-page partial.

### Restore CTA visibility on a 3,297px page — there is no sticky bar to replace the inline button

On mobile the inline Add to Cart sits at y=862 and is below the 844px fold even before the visitor swipes through the gallery (`visual-cta F-03`, `performance-ux F-03`). Once the visitor scrolls into the description or reviews, the only conversion action on the page is offscreen and there is no sticky bottom bar to take its place. A persistent compact bar showing product name (truncated), price ($59.95), and a full-width Add to Cart button — triggered via IntersectionObserver on the inline ATC — closes this gap. Multiple Shopify A/B tests on comparable scroll-depth pages document 7.9–33% conversion lift from this pattern. While in the same template, switch the button fill color from solid black to the brand red (or a saturated accent) so it stops reading as a continuation of the dark header bar (`visual-cta F-01`).

### Fix the four schema and SEO leaks that suppress rich results and AI commerce matching

Four search-channel issues sit in the same JSON-LD block on this page. The `<title>` reads 'Handlebar End Weights' while the H1 reads 'Handlebar End Caps' — Zyppy's Q1 2025 dataset of 81,000 titles attributes the 76% Google rewrite rate to exactly this kind of noun mismatch (`content-seo F-01`). The Offer's `priceValidUntil` is hard-coded to 2026-04-29, the audit date itself; Google flags expired validity dates as stale and revokes Shopping rich result eligibility (`content-seo F-03`). The Product schema in the mobile capture has an MPN but no GTIN — AI shopping agents use GTIN as the cross-platform matching key (`content-seo F-05`). And BreadcrumbList structured data is absent (`category-navigation F-02`); two SearchPilot controlled tests put the cost at 5–7% of organic traffic. Devs can resolve all four in one template pass: align the H1/title noun on whichever term Search Console traffic prefers, replace the static `priceValidUntil` with a server-computed rolling date 365 days out, populate `gtin12` if EvolutionR has a UPC for this SKU, and add a BreadcrumbList block listing Home > Spyder > Handlebar Accessories > [Product Name].

### Move the product video into the gallery and turn the lone install photo into UGC volume

The 'Can-Am Spyder Handlebar End Weights' YouTube embed sits below the Add to Cart button, below the product spec table, and outside the image gallery entirely (`product-media F-01`). Most mobile visitors never scroll that far. Reposition it as gallery item 2 with a play-button overlay so a single swipe surfaces it. While re-instrumenting the gallery, fix the thumbnail strip layout — currently every thumbnail fits fully visible with no partial-peek crop, giving visitors no swipe affordance (`product-media F-04`). And the lone customer install photo behind the Photos (1) tab — 6.7% of 15 reviews — should be promoted into the gallery as the final thumbnail labelled 'Customer Install Photo,' and the post-purchase review email should include a vehicle-specific photo prompt to lift the photo-to-review ratio (`trust-credibility F-05`). For an aftermarket bar-end where the buyer's primary anxiety is 'what will it look like on my Spyder,' real install footage is doing the heaviest lift available.

### Three buy-box edits that ship in one theme commit

Three of the highest-confidence findings on this page resolve with copy or HTML-attribute changes inside one product-page template. Add `fetchpriority="high"` and a matching `<link rel="preload" as="image">` to the hero product image — Google's Vodafone A/B test attributes 8% more online sales to a 31% LCP improvement, and this attribute is the lowest-cost path to that delta (`performance-ux F-02`). Disclose the schema-encoded shipping rate directly under the price as 'Free shipping over $75' (the schema records a $7.99 shipping rate as the under-threshold fallback) — Baymard data attributes 39% of actionable abandonment to shipping costs that surface only at checkout (`pricing F-03`). And surface the existing Reward Points program in the price block as 'Earn 60 points on this order' for logged-out visitors so the program is discoverable at the moment of purchase intent (`post-purchase F-01`).

## Findings by Cluster

### audience

#### audience F-01 — 15-Review Social Proof Count Not Framed for Audience Resonance

**SECTION:** product-info-buy-box
**ELEMENT:** `div[class*="rating"]` at e8 (y=773, height=30 CSS px)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The product carries 15 reviews at a 5-star average, rendered as '(15 reviews) In Stock' inline with the stock badge. For a niche accessory targeting Can-Am Spyder F3 and RT owners — a highly specific audience who needs fitment confidence before spending $59.95 — the social proof is not audience-anchored: it gives no indication that the 15 reviewers own the same model-year as the visitor, and no review snippet appears at the price decision point to signal what buyers found valuable.

**RECOMMENDATION:** If the review dataset includes model or trim data from purchasers, surface a one-line snippet adjacent to the star rating — for example, '15 Spyder owners verified fitment' or pull the top-voted review sentence that references the F3 or RT. If model data is unavailable, changing '(15 reviews)' to '15 verified buyers' adds specificity without fabricating audience claims. Either change is a copy edit to a single template file.

**Why this matters:** Social proof quantity drives purchase likelihood — products with reviews show substantially higher conversion than those without — but for high-specificity niche products the framing of who reviewed matters as much as the count. A Spyder F3 owner who sees '15 Spyder owners verified fitment' has materially more confidence than one who sees a raw parenthetical count.

▸ personalization-psychology.md, Finding 10 [Gold]

### category-navigation

#### category-navigation F-02 — No BreadcrumbList Schema on Product Page

**SECTION:** page-head
**ELEMENT:** `script[type="application/ld+json"]` (no `BreadcrumbList` type present in either device capture)
**SOURCE:** DOM
**PRIORITY:** HIGH

**OBSERVATION:** The page carries a Product JSON-LD block but no `BreadcrumbList` structured data. Without `BreadcrumbList`, Google cannot render a breadcrumb path in the search snippet for this product — the SERP shows a raw URL instead of a human-readable hierarchy such as Home > Spyder > Handlebar Accessories. Two independent SearchPilot controlled tests confirm breadcrumb removal causes statistically significant organic traffic declines: -5.5% in one test and -7% on category pages in a second test.

**RECOMMENDATION:** Add a `BreadcrumbList` JSON-LD block to the page head, listing at minimum two `ListItem` entries — the top-level vehicle category and the current product. Example path: Home > Spyder > Can-Am Spyder F3 & RT Handlebar End Weights (2024+). Align the schema path with the visible breadcrumb and ensure the intermediate vehicle category level is added to both the visible breadcrumb and the schema simultaneously, so markup and rendered content stay in sync.

**Why this matters:** Missing BreadcrumbList is a confirmed organic-traffic risk backed by two SearchPilot controlled tests: -5.5% to -7% traffic declines. On a specialty powersports accessories site where organic search drives acquisition, that traffic gap compounds against every category landing page and directly suppresses revenue.

▸ breadcrumbs.md, Finding 9 [Gold]

#### category-navigation F-04 — Breadcrumb Skips Category Level — Only Home to Product

**SECTION:** breadcrumb
**ELEMENT:** `nav.breadcrumb` (visible row below vehicle nav, scroll_y≈0)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The mobile breadcrumb trail reads Home > [product title], skipping the vehicle category (Spyder) and any sub-category (Handlebar Accessories or equivalent). A shopper landing from a Google search for Can-Am Spyder handlebar accessories has no one-tap path to browse the broader Spyder accessories catalog. Baymard documents that hierarchy breadcrumbs must answer the question of what category a product is in, and the correct path should reflect at minimum one intermediate level between Home and the product.

**RECOMMENDATION:** If the site navigation hierarchy is Home > [Vehicle Model] > [Part Category] > [Product], render all intermediate levels as live links in the breadcrumb. For this product: Home > Spyder > Handlebar Accessories > EvolutionR Handlebar End Weights. Keep the current-page element (product name) as non-clickable text. On a 390px mobile viewport, truncate the product name at roughly 40 characters if needed rather than hiding category levels — the H1 immediately below provides the full product title, so the breadcrumb's navigation value comes from the category links.

**Why this matters:** A breadcrumb that skips category levels eliminates cross-sell navigation for the large share of PDP visitors arriving via external search with no prior on-site browsing session. One extra category link converts an orientation dead-end into a live catalog exploration path for visitors evaluating whether Slingmods carries more compatible accessories.

▸ breadcrumbs.md, Finding 1 [Gold]

#### category-navigation F-05 — No History Breadcrumb for Filter-State Return

**SECTION:** breadcrumb
**ELEMENT:** `nav.breadcrumb` (no Back-to-results link visible at scroll_y≈0)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The page implements only a hierarchy breadcrumb with no history-type Back-to-results link. Baymard documents that 68% of ecommerce sites fail to implement both breadcrumb types, and that shoppers who navigate from a filtered category list to a PDP — then tap the hierarchy breadcrumb — lose all applied filters. On a specialist powersports accessories site where shoppers typically arrive via vehicle-filtered category pages (such as all 2024 Spyder F3 handlebar accessories), losing filter state on back-navigation removes the most valuable context for continuing a shopping session.

**RECOMMENDATION:** When a shopper arrives on this page from a filtered or sorted category listing, serialize the referrer state (category URL, active filters, sort order, scroll position) into session storage or a URL parameter and render a Back to [Category Name] ([N] items) link above the hierarchy breadcrumb. Suppress this link when the visitor arrived from an external search or direct URL with no on-site referrer session, so the element only appears when valid return state exists.

**Why this matters:** Shoppers who lose filter context on back-navigation either abandon entirely or must re-apply filters from scratch. For a specialty catalog where compatible-vehicle filtering is the primary discovery mechanism, filter-state loss directly reduces the add-to-cart rate from category browsing sessions.

▸ breadcrumbs.md, Finding 2 [Gold]

#### category-navigation F-07 — Vehicle Category Nav Bar Visible Above Fold

**SECTION:** header-nav
**ELEMENT:** `nav.vehicle-categories` (icons at e6 / e7, y=68)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The vehicle category navigation bar renders above the fold and immediately signals to first-time visitors that Slingmods organizes accessories by vehicle model. The vehicle icons alongside text labels support rapid recognition for returning customers switching between model lines.

**RECOMMENDATION:** The vehicle nav bar functions appropriately at its current above-fold position. If analytics show meaningful tap rates on Spyder from this PDP, consider adding a 'Shop more Spyder accessories' anchor link within the product description section as a reinforcing internal discovery path.

**Why this matters:** Clear vehicle-model navigation reduces bounce for visitors who arrive on a product that does not fit their specific vehicle, giving them an immediate path to the correct model line without leaving the site.

▸ collection-page-architecture.md, Finding 3 [Gold]

### checkout-flows

#### checkout-flows F-02 — No Express Checkout Buttons on Product Page

**SECTION:** product-info-buy-box
**ELEMENT:** `div.atc-zone` (no Apple Pay / Google Pay / Shop Pay buttons present); footer payment icons at e19
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The product detail page for the EvolutionR handlebar end weights shows a standard Add to Cart button and a PayPal Pay Later installment line, but offers no one-tap express checkout path. Apple Pay, Google Pay, and Amazon Pay logos appear only in the site footer (out of purchase context, at `e19` y=2417), not as actionable buttons near the Add to Cart interaction. A mobile shopper who has Apple Pay or Google Pay configured must navigate through the full cart-to-checkout funnel — typically 5-8 taps and two page loads — to complete a $59.95 purchase.

**RECOMMENDATION:** If the payment processor supports express checkout (PayPal, Stripe, or similar), add Apple Pay and Google Pay buttons directly below the Add to Cart button on the product page, above the PayPal Pay Later line. On mobile at 390px, these buttons should span the full content width. Label the group with a thin divider and the text '— or pay instantly with —' to distinguish express from cart-based checkout. Stripe placement data shows that wallet buttons at the top of the checkout flow — or on the product page itself — convert at approximately 2x the rate of buttons placed later in the funnel.

**Why this matters:** Shopify and Stripe A/B data attribute a 7-22% checkout conversion lift to express wallet buttons. On mobile, where typing addresses and card numbers is the primary friction point, the absence of a one-tap path disproportionately suppresses conversions from Apple Pay and Google Pay users — which represent the majority of mobile shoppers under 40.

▸ biometric-and-express-checkout.md, Finding 6 [Silver]

#### checkout-flows F-05 — PayPal Pay Later Installment Messaging Present

**SECTION:** product-info-buy-box
**ELEMENT:** `div[class*="pay"]` at e18 (y=862, height=37 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The page surfaces a PayPal Pay Later installment message — 'Pay in 4 interest-free payments of $14.99 with PayPal' — directly on the product page near the price (`e18`, y=862). This correctly reduces the perceived cost barrier for price-sensitive shoppers before they reach checkout.

**RECOMMENDATION:** The PayPal Pay Later message placement is effective — preserve it and ensure it remains above the Add to Cart button on mobile. If Affirm (already in the footer payment icon set) is also enabled at checkout, surface an Affirm monthly payment estimate on the PDP as well to cover shoppers who prefer Affirm over PayPal.

**Why this matters:** Displaying BNPL options on the product page rather than only at checkout reduces sticker-shock abandonment for payment-sensitive segments and surfaces the installment framing at the decision point where it does the most work.

▸ checkout-optimization.md, Finding 13 [Gold]

### content-seo

#### content-seo F-01 — Title Tag Uses 'End Weights'; H1 Uses 'End Caps'

**SECTION:** page-head
**ELEMENT:** `h1` at e3 (y=676, height=97 CSS px); `<title>` in page head
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The page title tag reads 'Can-Am Spyder F3 & RT Handlebar End Weights (2024+)' while the H1 reads 'EvolutionR Stainless Steel Weighted Handlebar End Caps for the Can-Am Spyder F3 & RT Models (Pair) (2024+)'. The product noun differs between the two: 'End Weights' in the title, 'End Caps' in the H1. Google's Q1 2025 analysis of 81,000 titles found that pages where title and H1 share the same key nouns have a title rewrite rate of approximately 20%; pages with misaligned titles are rewritten at the 76% population average. The video embed overlay also uses 'HANDLEBAR END WEIGHTS', making three surface-level keyword variants active on the same page.

**RECOMMENDATION:** If 'End Caps' is the preferred product noun (the H1 is typically the authoritative page element), update the title tag to 'Can-Am Spyder F3 & RT Handlebar End Caps (2024+)' and align the video thumbnail overlay text to match. If 'End Weights' better matches how target buyers search (verify via Google Search Console query data), update the H1 to use that phrasing instead. Either direction is acceptable — consistent use of one term across title, H1, and description heading is what matters.

**Why this matters:** Title rewrites at the 76% rate mean Google is replacing your optimized title with its own version for the majority of SERP impressions. When the rewritten title omits or changes the primary product noun, click-through rates drop and the page may rank for a different keyword than you intend. Aligning title and H1 is documented as the single highest-leverage action for reducing title rewrites.

▸ title-formulas-serp-psychology.md, Finding 12 [Silver]

#### content-seo F-03 — priceValidUntil Expired on Date of Capture

**SECTION:** page-head
**ELEMENT:** `script[type="application/ld+json"]` Offer.priceValidUntil = "2026-04-29"
**SOURCE:** DOM
**PRIORITY:** HIGH

**OBSERVATION:** The product's JSON-LD structured data sets `priceValidUntil` to '2026-04-29' — the date the page was captured. Google's product schema specification requires that this field contain a future date. An already-expired value signals to Google that pricing data is stale, which triggers re-evaluation for rich result eligibility. Google's documentation confirms that schema inaccuracies — including expired validity dates — can result in rich result removal, price display suppression in Shopping results, and Merchant Center disapproval if a feed is connected.

**RECOMMENDATION:** Update the `priceValidUntil` value in the product JSON-LD template to a rolling future date — either a date 12 months ahead that is updated annually, or a dynamic value generated server-side from today's date plus a fixed offset (e.g., 365 days). If the price changes frequently, tie this field to the actual promotion or pricing period end date. Never hardcode a static near-term date without a process to update it before expiry.

**Why this matters:** An expired priceValidUntil causes Google to treat the product's price as unverified, which strips star ratings and price display from SERP snippets. This directly reduces click-through rate for a product that has 15 reviews and would otherwise show rich results. The fix is a template change, not content work — the downside risk is disproportionate to the effort required.

▸ schema-product-markup.md, Finding 15 [Gold]

#### content-seo F-05 — No GTIN in Product Schema — AI Commerce Matching Blocked

**SECTION:** page-head
**ELEMENT:** `script[type="application/ld+json"]` Product schema (mpn present, gtin absent)
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** The product JSON-LD contains an MPN (`canam-spyder-handlebar-end-weights-evolutionr`) and internal product ID (22409) but no GTIN (UPC/EAN/ISBN). Google and OpenAI's ChatGPT Shopping both use GTIN as the primary cross-platform product matching key. Without it, AI shopping agents cannot reliably confirm this product matches a product in their knowledge base, which reduces the likelihood of surfacing in ChatGPT Shopping Research results and in Google Shopping's cross-retailer comparison features. For aftermarket automotive accessories like this one, if EvolutionR assigns a GTIN/UPC to this product, populating it would close this gap.

**RECOMMENDATION:** Check with the manufacturer (EvolutionR) whether a UPC or EAN is assigned to this SKU. If a manufacturer GTIN exists, add it to the JSON-LD as `gtin12` (for UPC) or `gtin13` (for EAN). If no manufacturer-assigned GTIN exists for this aftermarket part, the current MPN + brand combination is the documented fallback — no further action is needed. Do not fabricate a GTIN; that violates both Google and OpenAI policies.

**Why this matters:** ChatGPT Shopping Research and Google Shopping both use GTIN as the cross-platform identifier to match a product across multiple data sources. Products without GTINs are treated as unmatchable in AI shopping comparison flows, meaning competitors with GTINs populated appear in side-by-side AI recommendations while this product does not. For a niche aftermarket part with strong fitment specificity, GTIN-enabled AI commerce visibility could represent a meaningful incremental revenue channel.

▸ ai-search-agentic-discovery.md, Finding 5 [Gold]

#### content-seo F-06 — Canonical Tag Correctly Self-References Clean URL

**SECTION:** page-head
**ELEMENT:** `link[rel="canonical"]` (canonical = `https://www.slingmods.com/canam-spyder-f3-rt-handlebar-end-weights`)
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** The page head contains a self-referencing canonical tag pointing to `https://www.slingmods.com/canam-spyder-f3-rt-handlebar-end-weights` — a clean, lowercase, hyphen-separated URL with no collection prefix, no trailing slash, and no query parameters. This correctly prevents the Shopify dual-path duplicate (the `/collections/X/products/` variant) from splitting link equity.

**RECOMMENDATION:** No action required. Continue verifying canonical tag output after any theme update, as custom Shopify theme modifications are a known failure mode for canonical tag integrity.

**Why this matters:** A correctly implemented self-referencing canonical ensures all link equity consolidates to the preferred URL rather than being split across the Shopify collection-prefixed duplicate path.

▸ canonical-duplicate-content.md, Finding 1 [Gold]

#### content-seo F-08 — Product Description Uses Benefit-First FAB Structure

**SECTION:** description-tabs
**ELEMENT:** `section.product-description` (within description-reviews-tabs section, scroll_y≈1611)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The product description visible in the description tab leads with an outcome-first opening ('enhance rider comfort in just a few minutes'), explains the problem mechanism (handlebar vibration, tingling, fatigue), and follows with a 'Benefits and Features' bullet list covering fitment, weight spec (0.85 lb each, 8x heavier than stock), material (CNC-machined stainless steel, gloss black), and installation (direct bolt-on). This FAB structure — Benefit stated first, Feature and Advantage following — is well-executed for a consumer performance accessory.

**RECOMMENDATION:** No structural changes needed. As a freshness opportunity, the description could be extended with a short Q&A section addressing common pre-purchase questions: 'Will these fit my 2025 Spyder RT-L?', 'Do I need special tools?', and 'Do these affect balance at highway speeds?' — this Q&A content would also improve AI shopping assistant parsing of the page.

**Why this matters:** Benefit-first descriptions reduce the information gap that causes approximately 20% of purchase task failures. This page's current structure already clears that bar.

▸ benefit-first-descriptions.md, Finding 1 [Gold]

### performance-ux

#### performance-ux F-02 — Hero Product Image Lacks fetchpriority and Preload

**SECTION:** hero
**ELEMENT:** `img.product-hero` (above-fold image, no `fetchpriority` attribute or `<link rel="preload" as="image">` in head)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The main product photo of the EvolutionR handlebar end caps fills the entire viewport from the top of the gallery to around 660px scroll depth and is the largest above-fold element — meaning it is almost certainly the LCP element. Neither a `<link rel="preload" as="image">` in the page `<head>` nor a `fetchpriority="high"` attribute on the product image element is present. Without these signals, the browser places the hero image in its default network priority queue and begins fetching it only after parsing the full HTML, several render-blocking stylesheet requests (including a synchronous Google Fonts CSS call), and a TypeKit stylesheet. On a 4G mobile connection this ordering typically adds 300–600ms to the time before the hero image fetch begins — directly inflating LCP.

**RECOMMENDATION:** Add `fetchpriority="high"` to the primary product image element and add a matching `<link rel="preload" as="image" fetchpriority="high" href="[hero-image-url]">` in the `<head>` before any stylesheet links. For the `<picture>` format hierarchy, the preload should reference the WebP or AVIF source and use the `imagesrcset` / `imagesizes` attributes to match the responsive breakpoints. This is a template-level change to the product page layout file. After deploying, verify in Chrome DevTools that the LCP element resolves to Good (≤2.5s) on a simulated 4G connection.

**Why this matters:** Google's Vodafone A/B test showed a 31% LCP improvement produced 8% more online sales on a controlled 100K-click sample. The Google/Deloitte study across 37 brands found each 0.1s mobile speed improvement yields 8.4% more retail conversions. A missing fetchpriority on the LCP image is the single highest-leverage, lowest-cost fix available on this page — one HTML attribute change with measurable revenue upside.

▸ media-performance-optimization.md, Finding 1 [Gold]

#### performance-ux F-03 — No Sticky Add to Cart After Gallery Scroll

**SECTION:** product-info-buy-box
**ELEMENT:** `button.add-to-cart` (inline ATC at y≈862; no sticky bottom bar present)
**SOURCE:** VISUAL
**PRIORITY:** HIGH

**OBSERVATION:** Once a visitor scrolls below the product gallery and price block — which happens within the first swipe on a 390px viewport — the Add to Cart button at approximately y=862 scrolls off screen. There is no sticky bottom bar, no floating CTA, and no fixed action element that persists as the shopper reads the product description, fitment guide, or reviews. The baton confirms no sticky element exists with an add-to-cart role. On mobile, where one-handed thumb reach favors the bottom of the screen, the CTA is effectively inaccessible during the research phase of the visit.

**RECOMMENDATION:** Add a sticky bottom bar that appears once the inline Add to Cart scrolls out of view (use an `IntersectionObserver` on the existing Add to Cart button as the trigger). The sticky bar should show the product name shortened to one line, the price ($59.95), and a full-width 'Add to Cart' button at a minimum height of 56px. The trigger condition keeps the bar hidden while the inline CTA is visible, eliminating duplication. This is a component-level change to the PDP template; it overlaps with `visual-cta F-03` and resolves both findings simultaneously.

**Why this matters:** Mobile cart abandonment averages 78–80% vs. 70% on desktop. Baymard estimates a 35% conversion rate increase is recoverable through better mobile checkout access design. Removing friction from the moment a shopper decides to buy — by making the CTA accessible without scrolling back — is the most direct lever for closing the mobile conversion gap on this product type.

▸ mobile-conversion.md, Finding 4 [Gold]

#### performance-ux F-05 — Render-Blocking Google Fonts CSS Delays First Paint

**SECTION:** page-head
**ELEMENT:** `link[rel="stylesheet"][href*="fonts.googleapis.com"]` and `link[rel="stylesheet"][href*="use.typekit.net"]`
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** The page `<head>` loads two synchronous external CSS stylesheets from third-party domains: Google Fonts (`fonts.googleapis.com/css?family=Open+Sans...`) and Adobe TypeKit (`use.typekit.net/iji1kin.css`). Both are declared as standard `<link rel="stylesheet">` tags with no media query, `display=swap` workaround in the CSS call, or async loading strategy. The browser must fully download and parse both external CSS files before it can begin rendering any visible content — including the product title and hero image. A preconnect hint to fonts.gstatic.com is present, which helps with the subsequent font file fetch, but the blocking CSS call itself still stalls the render pipeline.

**RECOMMENDATION:** For the Google Fonts call, append `&display=swap` to the CSS URL if not already present, then load the stylesheet asynchronously: use `<link rel="preload" as="style" onload="this.onload=null;this.rel='stylesheet'">` with a `<noscript>` fallback. For TypeKit, switch to the async embed method (the JavaScript snippet Adobe provides) instead of the synchronous CSS link. Both changes eliminate the render-blocking behavior without removing the fonts. Test with Lighthouse before and after — First Contentful Paint and LCP should both improve.

**Why this matters:** Each external render-blocking stylesheet adds the full DNS + TCP + TLS + download round-trip latency before a single pixel renders. SpeedCurve testing found third-party scripts as a category can inflate LCP from under 1s to over 26s in worst cases. Even modest savings of 200–400ms here directly improve LCP and FCP — the two metrics most correlated with conversion via the Deloitte/Google 0.1s = 8.4% conversion relationship.

▸ core-web-vitals.md, Finding 8 [Silver]

### post-purchase

#### post-purchase F-01 — Reward Points Link Has No Value Framing or Enrollment Trigger

**SECTION:** footer
**ELEMENT:** `footer` at e19 (y=2417, height=880 CSS px) — Reward Points link in Information column
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The footer contains a 'Reward Points' link buried in the Information column alongside Privacy Policy and CARB Policy. There is no mention of the program anywhere on the product page — no points-earned preview, no enrollment prompt, no 'earn X points on this order' framing. Shoppers have no reason to know the program exists, much less what value it delivers.

**RECOMMENDATION:** Surface the loyalty program at the point of highest receptivity — on the product page near the price and add-to-cart area, and again at checkout confirmation. Minimum change: add a one-line 'Earn [X] Reward Points on this order' callout under the price block. The confirmation page should then show points earned from the order, the new total, and progress toward the next reward using endowed-progress framing: 'You earned 60 points — only 440 more to your first $5 reward.'

**Why this matters:** A loyalty program that shoppers never discover does not drive repeat purchases. The order confirmation moment is statistically the highest enrollment trigger (12-25% of buyers enroll when prompted immediately after purchase), and the endowed progress effect shows that pre-filled starting points lift program completion by 79%. Leaving this invisible costs repeat purchase revenue with zero implementation cost for the visibility fix.

▸ loyalty-programs.md, Finding 1 [Gold]

#### post-purchase F-03 — No Referral Program Surface on Product Page or Footer

**SECTION:** footer
**ELEMENT:** `footer .extras-column` (no Refer-a-Friend entry; absent at e19, y=2417)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** No referral program entry point exists anywhere on the page — not in the footer navigation, not on the product page, and not visible in any section. Slingmods serves a tight-knit community of Polaris Slingshot and Can-Am owners who actively share modifications; there is no mechanism to capture this organic advocacy through a structured referral reward.

**RECOMMENDATION:** Add a referral program entry point to the footer 'Extras' column ('Refer a Friend' link). The highest-value placement is on the order confirmation page, surfaced within 72 hours post-purchase when referral willingness peaks. Use double-sided framing: 'Give your fellow rider $15 off — you get $15 too when they buy.' For this PDP, a subtle 'Share with your riding crew' element near the product title would capture pre-purchase social sharing intent that seeds organic referrals.

**Why this matters:** Specialty vehicle accessory customers are community-driven — they discuss builds in forums, riding groups, and social media. A structured referral program with a double-sided incentive converts organic conversation into trackable rewarded acquisition. Referred customers show 16-25% higher lifetime value than marketing-acquired customers, and the 72-hour post-purchase window closes permanently without a prompt in place.

▸ referral-programs.md, Finding 3 [Bronze]

### pricing

#### pricing F-01 — Price Lacks MSRP Anchor or Compare-At Reference

**SECTION:** product-info-buy-box
**ELEMENT:** `div[class*="price"]` at e10 (y=823, height=77 CSS px)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The price block shows '$59.95' as a standalone number with no reference price alongside it — no MSRP strikethrough, no 'Compare at $X,' and no explicit savings line. Visitors evaluating this product have no external anchor to calibrate whether $59.95 is a strong price for weighted stainless-steel handlebar end caps. The schema markup confirms the product has a price of $59.95 but no advertised reference price has been set. Without a reference price, the advertised reference price effect (which independently elevates perceived quality and transaction value) cannot fire.

**RECOMMENDATION:** If EvolutionR publishes an MSRP for this SKU, display it as a strikethrough above the live price — for example, 'MSRP $79.95' struck through with '$59.95' below it, followed by a 'You save $20 (25%)' line in a contrasting color. If no manufacturer MSRP exists, a documented 'Regular Price' based on actual prior pricing achieves the same anchoring effect and satisfies FTC 16 CFR §233.1 requirements. The savings line should state both the dollar amount and the percentage to satisfy both acquisition-value and transaction-value channels simultaneously.

**Why this matters:** Displaying a credible reference price consistently lifts purchase intent and perceived value in peer-reviewed field studies. A $59.95 product with a visible $79.95 MSRP anchor reads as a good deal; the same $59.95 in isolation gives buyers no basis for judgment and defaults to feeling expensive against $0.

▸ price-anchoring.md, Finding 2 [Gold]

#### pricing F-03 — Free Shipping Not Communicated Near Price Decision

**SECTION:** product-info-buy-box
**ELEMENT:** `div.price-block` (no shipping line in price area; footer asterisk at e19, scroll_y=2417)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The price block at scroll_y 823 contains only the live price and a PayPal BNPL installment line. No free shipping message, threshold callout, or progress indicator appears anywhere near the price or Add to Cart button. The only shipping disclosure on the mobile page is a footnoted asterisk in the footer — roughly 1,600px below the purchase decision zone — reading '* Free Shipping Applies to Most Contiguous U.S. Orders - Some Items May Not Qualify.' A visitor deciding whether to add this $59.95 item to cart has no signal about shipping cost at the point of decision.

**RECOMMENDATION:** Add a 'Free shipping on this order' or 'Free standard shipping' line directly beneath the price element (between the price and the BNPL line, or immediately below it) if this product qualifies. If a threshold applies, surface the threshold message here: 'Free shipping on orders $X+.' The zero-price effect makes 'FREE' a qualitatively stronger signal than any equivalent dollar discount, so the word 'free' should be explicit rather than implied. If the schema-defined $7.99 shipping rate applies to this item, state that cost near the price instead — known shipping costs at decision time reduce the abandonment pressure that undisclosed fees create.

**Why this matters:** Shipping cost uncertainty at the price-evaluation stage contributes to cart abandonment regardless of whether shipping is ultimately free or paid. A visitor who cannot see shipping terms near the price must mentally budget a worst-case shipping cost, effectively anchoring against a higher total than the product warrants.

▸ free-shipping.md, Finding 2 [Gold]

### product-media

#### product-media F-01 — Product Video Buried Below Add-to-Cart

**SECTION:** gallery
**ELEMENT:** `iframe.youtube-embed` (placed below Add to Cart, around scroll_y≈900)
**SOURCE:** VISUAL
**PRIORITY:** HIGH

**OBSERVATION:** The product demonstration video sits beneath the Add to Cart button, beneath the product spec table, and outside the image gallery entirely. On mobile at this scroll position, a visitor must scroll past the price, PayPal Pay Later messaging, quantity selector, Add to Cart button, part number, and loyalty points notice before they reach the video. Baymard Institute found that 35% of major e-commerce sites make exactly this error — placing video where the majority of visitors never see it.

**RECOMMENDATION:** Move the video into the product image gallery as the second gallery item, immediately after the hero packshot. On mobile, the gallery swipe flow would then surface the video thumbnail at a single swipe, with a visible play-button overlay. The current below-ATC placement means the video's persuasion work is done after the conversion decision point has already passed.

**Why this matters:** A product video that 70%+ of mobile visitors never encounter provides zero conversion value regardless of production quality. Placing it in gallery position 2 is the single highest-leverage change available for this page's media setup.

▸ video-integration.md, Finding 8 [Gold]

#### product-media F-04 — Gallery Thumbnails Show No Depth Signal on Mobile

**SECTION:** gallery
**ELEMENT:** `.gallery-thumbnail-strip` (two complete rows, no partial-peek crop)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The mobile gallery thumbnail strip displays thumbnails in two complete rows with every thumbnail fully visible — no thumbnail is cropped at the edge. This layout provides no 'there are more images' affordance. Mobile users rely on a partial peek of the next thumbnail to understand they can swipe for additional views; when all thumbnails are fully visible simultaneously, users have no swipe incentive and may not discover all product angles. No image counter (e.g. '1 of 7') is visible in the gallery area.

**RECOMMENDATION:** Redesign the thumbnail strip so the rightmost thumbnail in each row is cropped at roughly 40–50% of its width. Use a container width calculated to show 3.5 thumbnails per row rather than a whole number. Pair this with CSS scroll-snap so the peek effect is smooth. If a full thumbnail-strip redesign is out of scope, add a '1 of 7' image counter overlay on the hero image instead — this satisfies the minimum viable depth signal.

**Why this matters:** Mobile visitors who do not realize additional product angles exist may skip images that show the product installed on a handlebar — exactly the contextual evidence that converts accessory buyers who are unsure about fit and appearance on their specific bike.

▸ gallery-ux.md, Finding 10 [Gold]

#### product-media F-05 — YouTube Embed Exposes Competitor Ads Post-Playback

**SECTION:** gallery
**ELEMENT:** `iframe[src*="youtube.com"]` (YouTube-hosted embed in product information zone)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The product video is embedded via YouTube, identifiable by the red YouTube icon in the section label 'Can-Am Spyder Handlebar End Weights.' YouTube embeds on product pages have four documented problems: after playback completes, YouTube surfaces a grid of related videos that frequently includes competitor products; YouTube may serve pre-roll ads (including competitor ads) before playback; YouTube URLs are blocked on some corporate and enterprise networks; and YouTube analytics do not attribute video-assisted purchases back to the product page session.

**RECOMMENDATION:** When migrating the video to gallery position 2 (per `product-media F-01`), host it through a dedicated video CDN such as Mux, Cloudflare Stream, or Vimeo Pro rather than YouTube embed. For a store at this price point and SKU count, a self-hosted solution eliminates post-play competitor recommendations at minimal monthly cost. If self-hosting is not immediately feasible, the YouTube embed is acceptable as an interim step — but apply the facade pattern (lightweight static thumbnail that loads the player only on tap) to protect Core Web Vitals.

**Why this matters:** A buyer who finishes watching this video and then clicks a YouTube recommendation to a competing product has left the purchase funnel — the video's persuasion investment just drove a competitor sale.

▸ video-schema.md, Finding 3 [Silver]

#### product-media F-07 — Image Set Covers Required Types for Hardware Accessory

**SECTION:** gallery
**ELEMENT:** `.gallery-thumbnails` (7 images covering packshot, detail, and install-context types)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The gallery provides 7 images covering the four core image types for a mechanical accessory: hero packshot showing the pair of end caps on a neutral background, close-up detail shots showing the machined stainless construction, and multiple installed-on-handlebar context shots that answer the buyer's primary question — 'will this look right on my bike?' The image count (7) exceeds the commodity-hardware minimum of 3–5 and is appropriate for a $59.95 parts accessory.

**RECOMMENDATION:** The current image set is well-suited to this product category. One enhancement to consider: an in-scale reference image showing the end caps next to the stock OEM units would help buyers confirm the size match before purchasing. This is an optional improvement, not a deficiency.

**Why this matters:** Adequate image coverage reduces 'not as pictured' returns for hardware accessories where buyers need to verify both visual fit and build quality before committing.

▸ image-quantity-types.md, Finding 3 [Gold]

### trust-credibility

#### trust-credibility F-02 — Perfect 5.0 Rating Triggers Purchase Skepticism

**SECTION:** product-info-buy-box
**ELEMENT:** `div[class*="rating"]` at e8 (y=773, height=30 CSS px)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The product rating displays as a perfect 5.0 out of 5 across 15 reviews, confirmed by both the visible filled stars and the page's structured data (`ratingValue: '5'`). Northwestern University's Spiegel Research Center found that purchase likelihood peaks in the 4.0-4.7 range and then decreases as ratings approach 5.0 — shoppers become skeptical that a perfect score is authentic. At 15 reviews with a 5.0 average, the rating sits precisely in the zone where potential buyers start questioning whether critical feedback has been filtered out.

**RECOMMENDATION:** Add a full star-distribution breakdown (percentage of 5-star through 1-star ratings) directly beneath the star widget. Showing the distribution — even if it is currently all 5s — gives shoppers the transparency to verify the score for themselves rather than suspecting gating. If the review collection flow pre-screens by satisfaction before sending requests, reconfigure it to send to all confirmed purchasers, which will naturally introduce rating variance over time and is also required under FTC 16 CFR §465.7 to avoid review-suppression liability.

**Why this matters:** A perfect 5.0 average with a moderate review count is one of the most common credibility-undermining patterns in e-commerce — shoppers have been trained by fake-review incidents to distrust it. Leaving this unaddressed on a $59.95 accessory purchase causes a meaningful share of comparison shoppers to discount the social proof entirely or seek external validation, reducing the page's ability to close the sale on the first visit.

▸ social-proof-patterns.md, Finding 1 [Gold]

#### trust-credibility F-04 — Review Text Behind Tab Not Indexed by Search Engines

**SECTION:** description-tabs
**ELEMENT:** `div.reviews-tab-panel` (review text loaded only on tab interaction; absent from initial HTML)
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** All 15 customer reviews are accessible only after clicking the 'Reviews (15)' tab. The review text is not present in the initial server HTML — it requires JavaScript interaction to surface. A SearchPilot controlled split test found that revealing previously hidden tab content produced approximately 7.4-7.5% organic session improvement. When review text is absent from the initial HTML, search engine crawls miss the keyword-rich natural language in those reviews, reducing the page's long-tail organic footprint and weakening the E-E-A-T Experience signal Google evaluates for product pages.

**RECOMMENDATION:** Render the first 3-5 reviews in the initial server HTML below the tab bar — keeping the tab UI intact for navigation — so that review text is present in the page source before any tab interaction. To verify the current state: view page source (not browser inspector) and search for a known phrase from any review; if it does not appear, the review content is not being indexed. If the review widget is delivered via a third-party JavaScript platform, check whether it supports server-side rendering options that place review text in the initial HTML while preserving the tab interface.

**Why this matters:** Review text is simultaneously a trust signal for live visitors, an SEO long-tail keyword asset (customers write naturally how buyers search: 'fits 2024 Spyder RT', 'bolt-on install'), and an E-E-A-T Experience signal for Google quality evaluation. Locking 15 genuine reviews behind a tab click means their full value — both for conversion and organic traffic — is only partially realized. The SearchPilot-measured 7.4% session improvement represents meaningful incremental traffic on a search-driven product page.

▸ ugc-reviews-seo.md, Finding 5 [Gold]

#### trust-credibility F-05 — Single Customer Photo Leaves UGC Gallery Underbuilt

**SECTION:** description-tabs
**ELEMENT:** `div.photos-tab` (Photos (1) tab — 1 photo against 15 reviews)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The Photos tab shows a count of 1 against 15 reviews — a 6.7% photo-to-review ratio. For a handlebar accessory where the primary purchase question is 'how will this look installed on my Spyder?', an owner-submitted install photo answers that question in a way the four professional studio images cannot replicate. Bazaarvoice data indicates 74% of shoppers say customer photos increase their purchase likelihood. With only one photo available, the page has the structural infrastructure for UGC but has not activated it at meaningful volume.

**RECOMMENDATION:** Add an explicit photo-upload prompt to the post-purchase review request email with a vehicle-specific hook such as 'Attach a photo of your Spyder with the bar ends installed.' For the 15 existing reviewers who submitted text without photos, a targeted follow-up email requesting an install photo can seed the gallery quickly. Once additional photos are collected, surface the customer photo in the main image carousel as the final thumbnail labeled 'Customer Install Photo' so it is visible without a tab click — this increases its trust impact for shoppers who never reach the Photos tab.

**Why this matters:** For a vehicle accessory purchase, a shopper's core unresolved question is whether the product will look right on their specific model. One real install photo from a fellow Spyder owner closes that gap immediately. With only one customer photo across 15 buyers, the page is leaving a high-value trust signal unrealized for the majority of its satisfied customers.

▸ social-proof-patterns.md, Finding 5 [Bronze]

#### trust-credibility F-08 — Footer Payment Icons and Address Implement Core Trust Signals

**SECTION:** footer
**ELEMENT:** `footer` at e19 (y=2417, height=880 CSS px)
**SOURCE:** BOTH
**PRIORITY:** LOW

**OBSERVATION:** The footer implements the core E-E-A-T Trustworthiness elements: a physical street address ('882 Patriot Dr. Suite G, Moorpark, CA 93021'), a toll-free phone number ('(800)211-1396'), eight recognizable payment method logos including PayPal, and a transparent brand-affiliation disclaimer ('not affiliated with or endorsed by Polaris / BRP'). These signals collectively address the 'Is this a real company?' anxiety for first-time visitors without overloading the footer with redundant badges.

**RECOMMENDATION:** The footer trust signals are well-structured. One incremental addition: a dedicated 'Returns' or 'Shipping Policy' link in the Information column would surface the return policy without requiring shoppers to navigate through the Terms page — return policy clarity is a documented purchase-decision factor, and making it one click away from the product page removes a friction point for first-time buyers.

**Why this matters:** Missing core footer trust signals — physical address, phone, recognized payment logos — creates a trust deficit that badge additions elsewhere cannot compensate for. The current implementation correctly covers these foundations.

▸ trust-and-credibility.md, Finding 23 [Gold]

### visual-cta

#### visual-cta F-01 — Add to Cart Button Uses Black — No Pop-Color Contrast Against White Page

**SECTION:** product-info-buy-box
**ELEMENT:** `button.add-to-cart` (solid black fill matching the dark header bar)
**SOURCE:** VISUAL
**PRIORITY:** HIGH

**OBSERVATION:** The 'Add to Cart' button uses a solid black fill (the same dark tone as the site's top navigation bar), so the button's visual weight matches the header rather than standing apart from the white content area beneath the product images. A shopper scanning this page perceives two similarly dark bands — the header and the CTA — without a clear chromatic signal that the button is the priority action. The Jackson's Art Supplies A/B test recorded an 18.4% conversion rate lift and a 66% increase in Add to Cart clicks for new visitors simply by giving the primary CTA a color that stood out from other interactive elements.

**RECOMMENDATION:** If the site's primary brand palette is black and red (as the SlingMods logo shows), introduce a high-contrast accent color — such as the brand red or a saturated orange — for the 'Add to Cart' fill on the product detail page. Keep the button full-width and the same height; only the fill color needs to change. Black can remain the color for secondary actions like the quantity selector controls, preserving hierarchy while making the primary CTA the most visually distinct element in the purchase zone.

**Why this matters:** The CTA's color is the shopper's visual cue that 'this is where to go next.' When it reads as a continuation of the header rather than a distinct call to act, mobile users who are scanning quickly — not reading — may not register it as the primary action, reducing spontaneous add-to-cart taps and the first-session conversion rate.

▸ cta-design-and-placement.md, Finding 3 [Bronze]

#### visual-cta F-03 — No Sticky Add-to-Cart Bar on Scroll — CTA Leaves Viewport During Content Review

**SECTION:** product-info-buy-box
**ELEMENT:** `button.add-to-cart` (inline ATC at y≈862; no persistent sticky bar at viewport bottom)
**SOURCE:** VISUAL
**PRIORITY:** HIGH

**OBSERVATION:** Once a shopper scrolls past the product title and price block — which happens as soon as they read the fitment guide or product description — the only path back to adding the item is to scroll back up. The page has 3,297px of total height and rich content (video, spec table, description, reviews tab). Multiple independent Shopify A/B tests document a 7.9–33% conversion lift from a sticky bottom CTA bar that keeps the 'Add to Cart' action accessible regardless of scroll position.

**RECOMMENDATION:** Implement a compact sticky CTA bar that appears once the primary 'Add to Cart' button scrolls out of view. The bar should display the product name (truncated), price ($59.95), and a full-width 'Add to Cart' button. Keep the bar height at 56–64px so it does not obscure body content. On pages with required variant selection, ensure the sticky bar triggers the variant selector if no option has been chosen yet rather than submitting an incomplete form.

**Why this matters:** Shoppers who read the fitment guide or watch the product video are demonstrating high purchase intent — they are doing pre-purchase research, not window shopping. Losing that shopper because they cannot convert in the moment they complete their evaluation (without a multi-second scroll back up) is one of the highest-leverage missed conversions on a mobile PDP.

▸ cta-design-and-placement.md, Finding 11 [Bronze]

#### visual-cta F-04 — No Risk-Reversal Microcopy Adjacent to the Add to Cart Button

**SECTION:** product-info-buy-box
**ELEMENT:** `button.add-to-cart` (no microcopy line below button; only Add to Wishlist link present)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The 'Add to Cart' button stands alone with only 'Add to Wishlist' below it. Baymard's checkout usability research identifies short trust-reinforcing microcopy placed directly adjacent to the CTA as a material friction-reducer at the moment of commitment. The footer carries a footnote about free shipping ('Free Shipping Applies to Most Contiguous U.S. Orders') and the page header mentions a 90-day return policy in the schema data, but neither surfaces within the CTA zone where purchase hesitation peaks.

**RECOMMENDATION:** Add a single line of microcopy directly below the 'Add to Cart' button summarizing the two highest-value reassurances: the free shipping threshold and the return window. For example: 'Free shipping on most US orders · 90-day returns.' Keep the text at 12–13px in a muted gray so it is visually subordinate to the button itself. If free shipping requires a minimum order, state the threshold; if it applies unconditionally to this SKU, 'Free shipping' alone is sufficient.

**Why this matters:** First-time visitors arriving from search have no prior relationship with SlingMods. A $59.95 specialty accessory purchase requires a moment of commitment; removing the two most common hesitations — 'what if it does not fit?' and 'what does shipping cost?' — at exactly the moment of decision directly reduces cart abandonment without any change to the product, pricing, or checkout flow.

▸ cta-design-and-placement.md, Finding 23 [Silver]

#### visual-cta F-05 — H1 Title Wraps to 5 Lines on Mobile, Delaying Price and CTA Visibility

**SECTION:** hero
**ELEMENT:** `h1` at e3 (y=676, height=97 CSS px) — 104 characters wrapping to 5 lines
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The product title is 104 characters and wraps to 5 lines at mobile viewport width, occupying 97px of vertical space below the already-tall image gallery. Baymard's mobile UX research establishes that on 375px-wide screens, headlines exceeding ~40 characters at standard heading size often push primary CTAs below the fold. On this page the price ($59.95) sits at y=823 in the baton — below the 844px mobile viewport height — meaning the purchase price is not visible on page load without scrolling. The title is accurate and contains SEO-critical model specifics, so this is a partial verdict rather than a fail.

**RECOMMENDATION:** If the full model compatibility string must remain in the H1 for SEO, wrap the secondary qualifier in a visually smaller span or move '(Pair) (2024+)' to a subtitle element displayed at a smaller weight below the main title. A shorter visible headline — for example, 'EvolutionR Weighted Handlebar End Caps — Can-Am Spyder F3 & RT' — would reduce wrapping to 2–3 lines and bring the price block above the viewport fold, improving the initial price-CTA visibility without changing URL structure or canonical content.

**Why this matters:** On mobile, every pixel of vertical height consumed by the title is a pixel that delays the shopper's view of the price and Add to Cart button. NNGroup's eye-tracking research shows mobile users assign 44% of their total viewing time to above-fold content; pushing the price below the fold on page load means the most conversion-critical element — price confirmation before committing to add — is in the attentionally deprioritized zone.

▸ eye-tracking-and-scan-patterns.md, Finding 27 [Gold]

#### visual-cta F-06 — Add to Cart Button Touch Target and Full-Width Sizing Meet Mobile Standards

**SECTION:** product-info-buy-box
**ELEMENT:** `button.add-to-cart` at e2 (full-width across 360px content column, ≈48–60px tall)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The 'Add to Cart' button is full-width across the content column, satisfying Apple's 44pt and Google's 48dp minimum touch target recommendations. The button includes a shopping cart icon for immediate recognition, clear CTA label text, and solid fill styling that distinguishes it from the ghost-link 'Add to Wishlist' below it — correct secondary CTA hierarchy.

**RECOMMENDATION:** No change needed for touch target sizing or visual affordance. The existing full-width, solid-fill treatment is a sound implementation of mobile CTA best practices for the tap target dimension. Color contrast (covered separately in `visual-cta F-01`) is the additional optimization to apply alongside this baseline.

**Why this matters:** A correctly sized, clearly labeled primary CTA reduces mis-taps and user frustration on mobile, contributing to a lower abandonment rate at the point of intent.

▸ cta-design-and-placement.md, Finding 5 [Silver]

## Methodology Notes

Single-shot dispatch (`dispatch_shape="single"`, `degraded_mode=false`). Cross-device finding independence is the expected outcome here: every canonical f_ref has `devices_present` length 1, so `scope_page_synchronized_refs` is intentionally empty. Findings rendered above appear only on the mobile audit; the desktop counterparts (where they exist) appear only in `audit-desktop.md`. Ethics gate is CLEAR — all seven canonical ethics findings rendered PASS/CLEAR and are not enumerated in this document by default (see synthesizer-emission-v1.json `humanized_findings` for the full ethics check list).
"""


def main() -> None:
    atomic_write_text(OUT, CONTENT)
    print(f"wrote: {OUT}")
    print(f"size: {OUT.stat().st_size} bytes")


if __name__ == "__main__":
    main()
