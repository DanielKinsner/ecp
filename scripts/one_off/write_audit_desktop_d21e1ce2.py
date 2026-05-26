"""One-off: write audit-desktop.md for engagement 2026-04-29-d21e1ce2.

Run from repo root:
    python scripts/one_off/write_audit_desktop_d21e1ce2.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "assembly"))

from atomic_write import atomic_write_text  # noqa: E402

ENGAGEMENT = "2026-04-29-d21e1ce2"
OUT = REPO_ROOT / "docs" / "ecp" / ENGAGEMENT / "audit-desktop.md"


CONTENT = """# Audit — SlingMods Can-Am Spyder F3-RT Handlebar End Weights PDP (desktop)

## Executive Summary

The $59.95 price renders without an MSRP anchor, the Add to Cart button has no trust badges or risk-reversal microcopy beside it, and the Add to Cart action disappears entirely once the visitor scrolls past about y=520 on a 1,661px-tall page. Four search-channel issues sit in the same JSON-LD block (H1/title noun mismatch on End Caps vs End Weights, expired priceValidUntil, missing GTIN/MPN, missing BreadcrumbList). The product video is parked in the right-rail outside the gallery where most visitors never see it. Start with the buy-box concentration pass and the schema/SEO repairs — both are template-level edits that ship in a single commit.

## Ethics Gate

CLEAR — no BLOCK or ADJACENT findings on this page. Seven ethics checks (urgency, schema-rating consistency, privacy URLs, Prop 65, cookie consent, subscription patterns, hidden-text SEO) all rendered CLEAR.

## Top Priorities

### Concentrate price, trust, and shipping signals into the buy-box

The $59.95 price block on this page does the work of one element when it should be doing the work of five. The price renders as a standalone number with no MSRP strikethrough or compare-at reference (`pricing F-02`), the $75 free-shipping threshold is announced at the top of the page but the $15.05 gap is invisible at the price decision point (`pricing F-04`), the perfect 5.0 rating sits above the price with no star distribution to defuse skepticism (`trust-credibility F-01`), and the Add to Cart button has no payment-security or guarantee badges adjacent to it (`trust-credibility F-03`). Devs should pull these into a single price-block container above the ATC button: MSRP or set-of-2 unit anchor, free-shipping proximity prompt stating the $15.05 gap with a 'You might also need' widget showing 1–3 small accessories priced $15–$25, a star-distribution bar under the aggregate rating, and a compact three-element trust badge row directly below the ATC. All four are template-level edits in one product-page partial.

### Restore CTA visibility on long scrolls — the page is 1,661px tall and the only sticky elements sit off-screen

The Add to Cart button sits at roughly y=470 in the right column and disappears once the visitor scrolls into the fitment guide and product description (`visual-cta F-02`). The only sticky elements present (`e10` and `e17`) are positioned at x=1835 in a 1920px viewport — 256px wide, extending 171px past the right edge — and carry no purchase copy. Visitors reading through the full description and the Spyder model fitment table have no visible purchase path without scrolling back to the top. A persistent compact bar showing product name (truncated), price ($59.95), and an Add to Cart button — triggered via IntersectionObserver on the inline ATC — would close this gap. Multiple Shopify A/B tests on comparable scroll-depth pages document 7–10% conversion lift from this pattern.

### Fix the four schema and SEO leaks that suppress rich results and AI commerce matching

Four search-channel issues sit in the same JSON-LD block on this page. The `<title>` reads 'Can-Am Spyder F3 & RT Handlebar End Weights (2024+)' while the H1 reads 'EvolutionR Stainless Steel Weighted Handlebar End Caps...' — Zyppy's Q1 2025 dataset of 81,000 titles attributes the 76% Google rewrite rate to exactly this kind of noun mismatch. The Offer's `priceValidUntil` is hard-coded to 2026-04-29, the audit date itself; Google flags expired validity dates as stale and revokes Shopping rich result eligibility. The Product schema in the desktop capture has no `gtin` or `mpn` (`content-seo F-02`), and BreadcrumbList structured data is absent — the breadcrumb on the rendered page reads only 'Home > [product]' (`category-navigation F-01`). Devs can resolve all of these in one template pass: align the H1 and `<title>` noun on whichever term Search Console traffic prefers, replace the static `priceValidUntil` with a server-computed rolling date 365 days out, add `mpn: "SM-22490"` to the Product JSON-LD, and add a BreadcrumbList block listing Home > Spyder > Handlebar Accessories > [Product Name] with matching visible breadcrumb levels.

### Move the product video into the gallery

The 'Can-Am Spyder Handlebar End Weights' YouTube embed sits outside the gallery, in the right-rail product-info column alongside specs and fitment data, with no video thumbnail in the main thumbnail strip (`product-media F-02`). Baymard's 2019 benchmark identified this exact placement in 35% of e-commerce sites where video does almost no purchase-intent work. For a vibration-reduction product where the mechanism — weighted bar ends absorbing handlebar resonance — is not self-evident from a static photo, a 30–60 second installation or ride-quality demonstration video in gallery position 2 or 3 is the highest-leverage media asset available. While re-instrumenting the gallery, add at least one in-scale reference image showing the bar end held in a hand or mounted on an actual handlebar to address the missing scale signal (`product-media F-03`).

### Three buy-box edits that ship in one theme commit

Three of the highest-confidence findings on this page resolve with copy or HTML-attribute changes inside one product-page template. Add `fetchpriority="high"` and a matching `<link rel="preload" as="image">` to the hero product image — Google's Vodafone A/B test attributes 8% more online sales to a 31% LCP improvement, and this attribute is the lowest-cost path to that delta (`performance-ux F-01`). Disclose the schema-encoded shipping rate directly under the price as 'Free shipping over $75 · $7.99 under threshold' — Baymard data attributes 39% of actionable abandonment to shipping costs that surface only at checkout (`checkout-flows F-01`). And surface the existing Reward Points program in the price block as 'Earn 60 points on this order' for logged-out visitors so the program is discoverable at the moment of purchase intent (`post-purchase F-04`).

## Findings by Cluster

### audience

#### audience F-02 — Vehicle Navigation Tab Shows No Active-Model State

**SECTION:** header-nav
**ELEMENT:** `nav#modelmenu` at e13 (y=137, height=36 CSS px)
**SOURCE:** BOTH
**PRIORITY:** LOW

**OBSERVATION:** The vehicle-model navigation bar (SLINGSHOT / SPYDER / RYKER / CANYON) is above the fold at y=138 on every page. On this Spyder product page, the SPYDER tab has no visual active state — no highlight, underline, or contrast change distinguishing it from the other vehicle tabs. The URL, product title, and fitment table all confirm the current context is Spyder, but the navigation does not reflect that. A visitor who arrived via search or a direct link has no visual confirmation from the navigation that they are in the correct vehicle section.

**RECOMMENDATION:** Apply an active-state CSS class to the corresponding vehicle tab when the current vehicle context can be inferred from the URL path or product category. This is a CSS-only change requiring no behavioral personalization or new data collection. If the platform supports a My Garage vehicle preference (the My Garage link is present in the desktop header), use that stored preference to persist the active vehicle context across the session.

**Why this matters:** When the navigation visually confirms the visitor's vehicle context, it reinforces that they are in the right section of the store and reduces the cognitive check of re-evaluating whether they navigated correctly. For a multi-vehicle brand, unclear vehicle context is a quiet abandonment driver that never surfaces as an obvious exit point.

▸ personalization-psychology.md, Finding 1 [Gold]

### category-navigation

#### category-navigation F-01 — Breadcrumb Skips Category Path — Home Jumps Directly to Product

**SECTION:** breadcrumb
**ELEMENT:** `nav.breadcrumb` (absent — proposed location: above the H1 at y≈118)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The breadcrumb on this page reads 'Home > EvolutionR Stainless Steel Weighted Handlebar End Caps for the Can-Am Spyder F3 & RT Models (Pair) (2024+)' — a single step from the homepage directly to the product. There is no intermediate category level such as 'Can-Am Spyder > Handlebars & Controls > Bar Ends' or equivalent. Visitors who arrive from organic search have no visual signal for what category this product belongs to, what else the store carries nearby, or how to browse related products. Additionally, no `BreadcrumbList` structured data appears in the page's JSON-LD — the schema block contains only Product markup — so Google cannot display a breadcrumb trail in search result snippets for this page.

**RECOMMENDATION:** Expand the breadcrumb to reflect the canonical category path: 'Home > Can-Am Spyder > Handlebars & Controls > Bar Ends & End Weights > [Product Name]'. Each intermediate level should link to its category page. If the product belongs to a single primary collection, use that collection's path consistently. Once the visible breadcrumb is in place, add a matching `BreadcrumbList` JSON-LD block to the page's head — the `itemListElement` array should mirror the visible hierarchy with a position integer and item URL for each level.

**Why this matters:** Baymard's benchmark of 327+ ecommerce sites found 68% fail to provide the correct breadcrumb depth. A two-hop 'Home > Product' trail gives search-entry visitors no context for the store's catalog structure and no one-click path to browse related accessories. The SearchPilot controlled test confirmed breadcrumb removal causes a statistically significant -5.5% organic traffic decline; a flat breadcrumb that fails to signal category relevance carries a comparable SEO cost.

▸ breadcrumbs.md, Finding 1 [Gold]

#### category-navigation F-03 — No 'Back to Results' History Breadcrumb for Filter-State Return

**SECTION:** breadcrumb
**ELEMENT:** `nav.breadcrumb` (absent — proposed location: above the hierarchy breadcrumb at y≈118)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The page has only a hierarchy breadcrumb. There is no history-style 'Back to [category]' link that would return a shopper to their filtered category list with sort order and scroll position intact. A customer who filtered 'Can-Am Spyder accessories by handlebar type,' landed on this PDP, and wants to resume browsing has no shortcut — clicking the hierarchy 'Home' link abandons their filtered context entirely.

**RECOMMENDATION:** When a visitor arrives at this page from a filtered category or search results page, render a 'Back to [Category Name] ([N] results)' link immediately above the hierarchy breadcrumb. Encode the `returnTo` URL — including active filter params and scroll position — in the PDP URL when generating the link from the category page so that clicking 'Back to results' restores the exact filtered view. For direct-URL arrivals with no referrer session state, suppress the history breadcrumb rather than showing a broken or generic link.

**Why this matters:** When shoppers lose their filtered context on the way back from a product page, they face re-applying all filters from scratch — a friction point Baymard's usability research identifies as among the most frustration-generating failures in category navigation. Shoppers who abandon rather than re-filter represent a measurable loss of category-level browse conversion.

▸ breadcrumbs.md, Finding 2 [Gold]

#### category-navigation F-06 — Vehicle Model Menu Provides Fitment-First Navigation Above Fold

**SECTION:** header-nav
**ELEMENT:** `nav#modelmenu` at e13 (y=137, height=36 CSS px)
**SOURCE:** BOTH
**PRIORITY:** LOW

**OBSERVATION:** The vehicle model navigation bar (SLINGSHOT / SPYDER / RYKER / CANYON / RIDING GEAR) sits at y=137, fully above fold on a 1080px desktop viewport. For a fitment-specific accessory store, this vehicle-first navigation layer correctly orients visitors by platform before they browse by category.

**RECOMMENDATION:** No change required. The model-first navigation row is well-positioned. If any model tabs are added or renamed in future catalog updates, verify that the active model tab receives a distinct visual state so the current product's fitment context is immediately clear (see `audience F-02`).

**Why this matters:** Fitment-first navigation reduces wrong-vehicle purchases and support contacts — a structural strength worth preserving as the catalog expands.

▸ collection-page-architecture.md, Finding 3 [Gold]

### checkout-flows

#### checkout-flows F-01 — No Shipping Cost Estimate Before Checkout

**SECTION:** product-info-buy-box
**ELEMENT:** `div.price-box` at e8 (y=403, height=64 CSS px) — proposed location for shipping callout
**SOURCE:** VISUAL
**PRIORITY:** HIGH

**OBSERVATION:** The product page for the $59.95 EvolutionR Handlebar End Caps shows no shipping cost estimate, no ZIP-code shipping calculator, and no free-shipping threshold indicator alongside the price. A shopper who adds this item to cart will not learn the shipping cost until the checkout flow — after they have already invested time evaluating the product and deciding to buy. Baymard Institute data (50-study aggregate, annually replicated) identifies extra costs revealed late in checkout as the single largest actionable abandonment trigger, cited by 39% of all non-browsing abandoners.

**RECOMMENDATION:** Add a shipping callout directly in the price block. If this product qualifies for the free shipping threshold shown in the top navigation bar ('Free Shipping on Most Orders Over $75*'), display 'Free shipping over $75 · $7.99 flat rate below threshold' so both states are visible. The schema-encoded shipping rate is already present in the page head (`OfferShippingDetails.shippingRate.value="7.99"`) and can be surfaced server-side without a new API call. If shipping is calculated by ZIP code, add an inline shipping estimator (ZIP input + Estimate shipping link) adjacent to the price.

**Why this matters:** Shoppers who reach checkout and see a shipping charge they did not expect are the most likely segment to abandon — Baymard data shows 39% of actionable abandoners cite this exact trigger. For a specialty accessory at $59.95, even a $7.99 shipping charge appearing late can flip a decided buyer into an abandoner.

▸ checkout-optimization.md, Finding 1 [Gold]

#### checkout-flows F-03 — Apple Pay and Google Pay Absent from Product Page

**SECTION:** product-info-buy-box
**ELEMENT:** `footer` at e18 (y=1345, footer-only payment icons; absent from buy-box)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The footer confirms this store accepts Apple Pay and Google Pay — both logos appear in the payment strip at the bottom of the page (`e18`, scroll_y 581+). However, neither an Apple Pay button nor a Google Pay button appears in the product hero where the Add to Cart action lives. The only express payment option near the price is the PayPal Pay Later widget (`e16`, y=442). Stripe controlled A/B holdback testing found that express checkout buttons placed at the beginning of the purchase flow convert at approximately 2x the rate compared to buttons placed at the payment step or relegated to footers.

**RECOMMENDATION:** Add Apple Pay and Google Pay express checkout buttons directly in the add-to-cart area of the product hero, positioned either above or immediately below the Add to Cart button with a visual separator labeled 'Or pay with.' These should be rendered as native payment request buttons (not icon-only payment logos) so clicking them initiates the express checkout flow. The footer payment icons can remain as trust signals, but they do not function as checkout accelerators from their current position.

**Why this matters:** Desktop shoppers with Apple Pay or Google Pay configured can complete a purchase from the product page in two clicks when express buttons are present — bypassing form entry entirely. Keeping these options visible only in the footer means most shoppers will never see them as a purchase path, and the store forfeits the conversion lift that Stripe large-sample testing attributes to early wallet placement.

▸ biometric-and-express-checkout.md, Finding 6 [Silver]

#### checkout-flows F-04 — PayPal Pay Later Surfaced at Price Point

**SECTION:** product-info-buy-box
**ELEMENT:** `div.pay-later-message` at e16 (y=442, height=24 CSS px)
**SOURCE:** BOTH
**PRIORITY:** LOW

**OBSERVATION:** The PayPal Pay Later widget (`e16`) renders immediately below the $59.95 price block, above the fold at y=442, showing 4 interest-free payments of $14.99 with PayPal. BNPL messaging at the price point is correctly positioned — the shopper sees the installment option at the moment they are evaluating affordability, not after reaching checkout.

**RECOMMENDATION:** No change required for the PayPal Pay Later widget placement. To reinforce this pattern, evaluate whether Affirm (which appears in the footer payment logos and has a dedicated information page linked in the footer) can also be surfaced near the price — see `pricing F-05`.

**Why this matters:** BNPL messaging at the price point reduces the effective perceived price and can recover shoppers who would otherwise abandon due to the upfront cost — this widget is working correctly and should be preserved through any future template changes.

▸ checkout-optimization.md, Finding 13 [Gold]

### content-seo

#### content-seo F-02 — Product Schema Missing GTIN and MPN Identifiers

**SECTION:** page-head
**ELEMENT:** `script[type="application/ld+json"]` (Product schema; absent — no `gtin` / `mpn` / `sku` fields in desktop capture)
**SOURCE:** DOM
**PRIORITY:** HIGH

**OBSERVATION:** The page's JSON-LD Product schema in the desktop capture contains `name`, `image`, `brand`, `aggregateRating`, and `offers` but omits every product identifier: no `gtin`, no `mpn`, no `sku`. The on-page copy displays part number SM-22490, confirming a manufacturer identifier exists but has not been added to structured data. Without a product identifier, Google Merchant Center cannot reliably match this SKU to its Shopping Graph knowledge base, and ChatGPT's Instant Checkout cannot cross-reference this product across data sources. Google Merchant Center describes GTIN as strongly recommended for products with a manufacturer-assigned identifier; for aftermarket automotive products without a universal GTIN, brand + mpn is the documented alternative.

**RECOMMENDATION:** Add the manufacturer part number as `mpn` in the JSON-LD: `"mpn": "SM-22490"`. If EvolutionR has a UPC or EAN assigned to this SKU, populate `gtin` instead or in addition. For aftermarket automotive parts, `mpn` is the correct identifier field. This is a single JSON-LD property addition requiring no structural page changes.

**Why this matters:** Products without identifiers are not matchable by AI shopping agents performing cross-platform product comparisons. Google Shopping, ChatGPT Shopping, and Perplexity all use GTIN or MPN as the convergence point for product identity across databases. Missing identifiers reduce Google Merchant Center Shopping eligibility and eliminate price-comparison features where this product would otherwise appear.

▸ ai-search-agentic-discovery.md, Finding 5 [Gold]

#### content-seo F-04 — MerchantReturnPolicy Absent from Product Schema

**SECTION:** page-head
**ELEMENT:** `script[type="application/ld+json"]` (Product schema — no `hasMerchantReturnPolicy` in desktop capture)
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** The product JSON-LD in the desktop capture does not include a `MerchantReturnPolicy` object. SlingMods.com has a return policy (the footer links to relevant pages) but that policy is not expressed in structured data on this device's page response. AI shopping agents — including ChatGPT Shopping Research and Google's AI-powered shopping surfaces — use return policy schema to compare merchants when evaluating otherwise equivalent products. Without it, SlingMods is invisible on this comparison dimension at exactly the moment a buyer is evaluating competing vendors.

**RECOMMENDATION:** Add a `MerchantReturnPolicy` block to the Product schema. The minimum viable path uses a link-out: `"hasMerchantReturnPolicy": {"@type": "MerchantReturnPolicy", "applicableCountry": "US", "merchantReturnLink": "https://www.slingmods.com/terms"}`. For richer Google rich result display, use the inline option with `returnPolicyCategory`, `merchantReturnDays`, and `returnMethod` fields set to match the actual policy terms. Note: the mobile capture's schema block already includes a complete `hasMerchantReturnPolicy` object — verify why the desktop response omits it and align both device responses.

**Why this matters:** Return policy transparency is a documented differentiator in AI commerce comparison flows. ChatGPT Shopping Research and Google Shopping both surface return policy data when comparing merchants. A competitor with complete return policy schema wins this comparison signal by default against a merchant whose policy exists but is invisible in structured data.

▸ schema-product-markup.md, Finding 6 [Gold]

#### content-seo F-07 — Canonical Tag Self-Referencing and Correctly Formed

**SECTION:** page-head
**ELEMENT:** `link[rel="canonical"]` (canonical = `https://www.slingmods.com/canam-spyder-f3-rt-handlebar-end-weights`)
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** The page head contains a self-referencing canonical tag pointing to `https://www.slingmods.com/canam-spyder-f3-rt-handlebar-end-weights` — a clean, hyphenated, lowercase product URL with no collection-path prefix.

**RECOMMENDATION:** No action required. Re-verify the canonical tag output after any Shopify or platform theme updates, as custom theme modifications are the most common cause of canonical regressions.

**Why this matters:** A correct self-referencing canonical consolidates ranking signals to the preferred URL and prevents Shopify-style dual-path behavior from splitting link equity between the `/products/` URL and the `/collections/.../products/` duplicate path.

▸ canonical-duplicate-content.md, Finding 1 [Silver]

### performance-ux

#### performance-ux F-01 — Hero Product Image Missing fetchpriority and Preload

**SECTION:** hero
**ELEMENT:** `img.product-hero` (absent in baton — referenced via Product schema `image` URL)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The primary product image — the EvolutionR handlebar end caps — loads without a `fetchpriority="high"` attribute or a matching `<link rel="preload" as="image">` in the page head. The page head loads nine CSS stylesheets before the browser begins parsing the main content. Without a priority hint, the browser queues the hero image behind those stylesheet requests, which delays the Largest Contentful Paint measurement — the metric Google uses as a ranking signal and the one most directly tied to conversion.

**RECOMMENDATION:** Add `fetchpriority="high"` directly to the hero product `<img>` element and add a matching `<link rel="preload" as="image" fetchpriority="high" href="[hero-image-url]">` in the head before the CSS stylesheet declarations. Do not add `loading="lazy"` to this image. Gallery images at scroll positions below the first viewport should use `loading="lazy"` with `fetchpriority="low"`.

**Why this matters:** A controlled A/B test at Vodafone showed a 31% LCP improvement produced 8% more online sales. The hero image is the LCP element on the majority of product pages — a single missing attribute change on this one element is the highest-leverage performance fix available on this page.

▸ media-performance-optimization.md, Finding 1 [Gold]

#### performance-ux F-04 — Logo Image Missing Width and Height — CLS Source

**SECTION:** header
**ELEMENT:** `img.logo` (referenced from `header` at e15, y=35, height=102 CSS px)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The SlingMods logo in the header (`/image/catalog/slingmods-logo-main.png`) has no `width` or `height` attributes. When the browser parses the HTML it cannot reserve the correct space for the logo, so the entire header layout — including the phone number, search field, cart button, and the two navigation rows below — shifts downward when the logo image loads. This shift scores against the Cumulative Layout Shift (CLS) Core Web Vital, which requires a score of 0.1 or better for the Good threshold.

**RECOMMENDATION:** Add `width` and `height` attributes to the logo `<img>` element matching the image's rendered CSS dimensions (inspect in DevTools to confirm the px values). Also ensure `max-width: 100%; height: auto;` is set in CSS so the logo scales responsively without overriding the declared aspect ratio. This is a one-line HTML change that eliminates this CLS source entirely.

**Why this matters:** Swappie's 91% CLS reduction contributed to a 42% mobile revenue increase. CLS at the very top of the page — in the header — affects every scroll position because the shift is visible before any content loads. Visitors see the page jump before they can read the product name or price.

▸ media-performance-optimization.md, Finding 5 [Gold]

#### performance-ux F-06 — brainyfilter.css Loaded Twice — Duplicate Render-Blocking Stylesheet

**SECTION:** page-head
**ELEMENT:** `link[rel="stylesheet"][href*="brainyfilter.css"]` (two consecutive identical entries)
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** The file `brainyfilter.css?v=1.4` appears twice in succession in the page head as identical `link rel="stylesheet"` entries. This causes the browser to make two blocking network requests for the same CSS file on every page load. Each duplicate is a render-blocking resource — the browser must download and parse both before it can begin painting visible content.

**RECOMMENDATION:** Remove one of the two duplicate `brainyfilter.css` entries from the template file where these stylesheets are declared. If the duplication comes from two separate includes (such as a layout template and a module template both including the filter CSS), consolidate to a single include point. After removing the duplicate, verify that filter functionality still renders correctly.

**Why this matters:** Every additional render-blocking stylesheet delays the point at which the browser can paint content. The Deloitte and Google study across 37 brands found a 0.1-second improvement in load time increases retail conversion by 8.4%. Eliminating a duplicate stylesheet is a zero-risk, zero-downside fix.

▸ page-performance-psychology.md, Finding 1 [Silver]

### post-purchase

#### post-purchase F-02 — Referral Program Has No PDP or Footer Presence

**SECTION:** footer
**ELEMENT:** `footer` at e18 (y=1345, height=296 CSS px) — proposed location for new referral entry
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The footer contains four content columns — Information, Year/Model Charts, Extras, and My Account — and none includes a referral program link, give-get CTA, or share prompt. The Extras column links to Gift Cards, Dealers, Price Match Guarantee, and Sell Your Products on SlingMods, but carries no referral entry. Slingmods has a Reward Points program (linked in the Information column), yet no complementary referral surface exists anywhere on the page. A buyer completing a $59.95 purchase is in peak referral-readiness during the 72-hour post-purchase window, but the page provides no pathway to share or refer.

**RECOMMENDATION:** Add a footer link in the Extras column alongside Gift Cards — 'Refer a Friend — Give $15, Get $15.' For the order confirmation page specifically, embed a referral block below the order details using give-first framing: 'Give your friend $15 off their first Slingmods order. You get $15 too when they buy.' Use one-click copy for the referral link. The footer placement captures browsing visitors; the confirmation page captures peak post-purchase excitement.

**Why this matters:** Customers who just purchased are at peak excitement and social sharing impulse. Referred customers show 16-25% higher LTV than paid-acquisition customers, and a referral program costs a fraction of equivalent paid traffic. Every order that ships without a referral prompt is a missed acquisition window that closes within 72 hours.

▸ referral-programs.md, Finding 3 [Bronze]

#### post-purchase F-04 — Reward Points Footer Link Carries No Enrollment Context

**SECTION:** footer
**ELEMENT:** `footer a[href*="rewards"]` (within `footer` at e18, y=1345)
**SOURCE:** BOTH
**PRIORITY:** LOW

**OBSERVATION:** The footer Information column contains a 'Reward Points' link pointing to slingmods.com/rewards. It is styled identically to adjacent utility links (About Us, Privacy Policy, CARB Policy) — plain text, no earning rate, no points-per-dollar value, no 'Earn X points on this order' hook. Visitors with purchase intent who reach the footer have no signal that buying this item earns them 60 points toward a reward. The product hero area separately shows 'Login & Earn 60 Points when purchasing this item' for authenticated users, but that message is absent for unauthenticated visitors who see only the footer.

**RECOMMENDATION:** Augment the footer link with a brief inline callout: change 'Reward Points' to 'Reward Points — Earn on every order.' For the PDP, add a small loyalty badge below the price block for non-logged-in visitors: 'Free to join — earn 60 points on this purchase toward your next reward.' The enrollment prompt belongs at the moment of purchase intent. Framing the offer as 'You earned 60 points from this order' rather than 'You have 0 points' activates the endowed progress effect, which Nunes and Dreze (2006, Journal of Consumer Research) found increases program completion by 79%.

**Why this matters:** Loyalty programs with visible enrollment prompts at the moment of purchase enroll 12-25% of new customers immediately post-checkout. A footer link with no value framing converts below 2%. Every purchase by an unenrolled customer is a missed opportunity to start the loyalty flywheel that drives 2-3x LTV versus non-members.

▸ loyalty-programs.md, Finding 1 [Gold]

#### post-purchase F-05 — Order Tracking and Account Self-Service Links Present

**SECTION:** footer
**ELEMENT:** `footer .my-account-column` (within `footer` at e18, y=1345)
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** The footer My Account column provides Track My Order, Order History, and My Account links — covering the core post-purchase self-service needs that reduce WISMO support volume.

**RECOMMENDATION:** No change required for this element. To increase impact, surface the same Track My Order link more prominently on order confirmation pages and in transactional emails so customers find it before they resort to a support inquiry.

**Why this matters:** Basic order-tracking access in the footer reduces inbound support tickets and gives post-purchase visitors a direct path to order status without contacting support.

▸ post-purchase-psychology.md, Finding 6 [Bronze]

### pricing

#### pricing F-02 — Price Block Has No MSRP or Compare-At Anchor

**SECTION:** product-info-buy-box
**ELEMENT:** `div[class*="price"]` at e8 (y=403, height=64 CSS px)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The price block on this product page displays a single number — '$59.95' — with no MSRP strikethrough, no 'compare at' figure, and no savings amount stated in dollars or percentage. A visitor landing on this page sees a price in isolation, with no signal about whether $59.95 represents strong value, a fair price, or an overpriced option. The h2 element and the price div both confirm the bare single-number presentation (`e5` at y=403 and `e8` at y=403).

**RECOMMENDATION:** If the EvolutionR Stainless Steel Handlebar End Caps carry a manufacturer's suggested retail price higher than $59.95, add the MSRP as a struck-through figure above or beside the selling price — for example, 'MSRP $79.95' in grey struck-through text, followed by 'Your Price $59.95' in the primary price color. Additionally, state the savings explicitly: 'You save $20.00 (25%)' as a visually distinct callout beneath the price pair. The reference price must reflect a price at which the product has genuinely been sold or listed; a fabricated inflate-and-discount MSRP undermines customer trust and FTC compliance (16 CFR §233.1).

**Why this matters:** Without a reference price, $59.95 anchors against nothing — the visitor defaults to whatever comparison came before, likely a cheaper product in search results. Grewal et al. (1998) show that a credible advertised reference price simultaneously sets an internal reference price, signals product quality, and makes the current price feel like a genuine deal. Retailers that add credible strikethrough anchoring typically see 5–15% conversion lifts on product pages that previously showed no reference price.

▸ price-anchoring.md, Finding 1 (Grewal et al. 1998) [Gold]

#### pricing F-04 — Free Shipping Threshold Exceeds Product Price With No Proximity Prompt

**SECTION:** product-info-buy-box
**ELEMENT:** `nav.free-shipping-banner` at e12 (y=0, height=35 CSS px) — banner; price block at e8 lacks proximity prompt
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The site-wide banner correctly announces free shipping on orders over $75 (`e12`, scroll_y=0, above fold). This product is priced at $59.95 — $15.05 short of the threshold. No inline progress message, no 'you need $15.05 more for free shipping' copy, and no recommended add-on product appears near the price block or add-to-cart button to motivate basket-building. The only free-shipping signal is the banner; the price block itself provides no goal-proximity framing.

**RECOMMENDATION:** Add a goal-proximity message in the price block or immediately below the Add to Cart button: 'Add $15.05 more to your order for FREE shipping.' If the visitor has already added an item to cart and returns to this page, update the message dynamically to reflect the remaining distance. Pair this with a 'You might also need' product widget showing 1–3 accessories or consumables priced $15–$25. Kivetz et al. (2006) show that framing the existing cart value as a head start — 'You already have $59.95 in your cart — just $15.05 more for FREE' — outperforms a message that ignores what the customer has already committed.

**Why this matters:** A visitor who sees a $59.95 product and a $75 threshold has a $15.05 gap that is easily closable — but only if the page makes the gap visible and actionable. Without proximity framing, most visitors will proceed to checkout rather than voluntarily basket-build. The goal-gradient effect shows that purchase acceleration is highest when the remaining distance is small and salient; the zero-price effect shows that reaching the threshold delivers a 'FREE' signal worth more than its monetary equivalent. This page suppresses both mechanisms by presenting the threshold only as a header banner, not as a product-specific prompt.

▸ free-shipping.md, Finding 1 [Gold]

#### pricing F-05 — BNPL Coverage Incomplete: Affirm Absent from Price Block

**SECTION:** product-info-buy-box
**ELEMENT:** `div.pay-later-message` at e16 (y=442, height=24 CSS px); footer Affirm link at e18
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** PayPal Pay Later is displayed inline in the price block at $14.99 × 4 (`e16`, above fold, y=442). This is correctly positioned. However, the site also carries an Affirm relationship — Affirm appears in the footer payment icons and has a dedicated footer navigation link ('Affirm Monthly Payments'). Affirm is not displayed in the price block. For a $59.95 product, Affirm's monthly installment framing (typically 3–6 monthly payments) presents a different and complementary message to PayPal's 4-bi-weekly structure, reaching visitors who prefer or specifically recognize Affirm.

**RECOMMENDATION:** If Affirm is active on this product, add the Affirm inline widget to the price block alongside or below the PayPal Pay Later message. The Affirm widget typically renders as a single line: 'As low as $X/mo with Affirm. Learn more.' Showing both options signals broader payment flexibility. First verify the Affirm widget has not been intentionally suppressed in theme settings for this product category — if suppression was deliberate, this finding does not apply.

**Why this matters:** BNPL awareness must be established on the product page before the purchase decision is formed (Maesen & Ang 2025). Visitors who rely on Affirm for mid-ticket purchases will not see their preferred payment option and may perceive the checkout as less flexible than it actually is, reducing the payment-decoupling benefit that BNPL provides for this price range.

▸ bnpl-payment.md, Finding 1 [Gold]

#### pricing F-06 — Charm Pricing Correctly Applied at Left-Digit Boundary

**SECTION:** product-info-buy-box
**ELEMENT:** `span[class*="price"]` at e9 (y=402, height=30 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The product is priced at $59.95, which crosses the $60 left-digit boundary. This is a correctly deployed charm price — the leftmost digit reads '5' rather than '6', activating the encoding advantage documented in the peer-reviewed literature.

**RECOMMENDATION:** No change needed. The .95 ending produces the maximum left-digit benefit because the leftmost digit changes from 6 to 5. Maintain this pricing format.

**Why this matters:** Charm pricing at left-digit boundaries is one of the lowest-cost micro-optimizations available. Troll and Wieseke's 2024 meta-analysis of 144 effect sizes confirms a statistically reliable purchase-intention lift for just-below prices at left-digit crossings, with no negative effect on perceived quality for non-luxury goods.

▸ charm-pricing.md, Finding 1 (Troll & Wieseke 2024) [Gold]

### product-media

#### product-media F-02 — Product Video Outside Gallery — Tab Placement Hides It

**SECTION:** gallery
**ELEMENT:** `iframe.youtube-embed` (placed in right-rail product-info column, not in gallery thumbnail strip)
**SOURCE:** VISUAL
**PRIORITY:** HIGH

**OBSERVATION:** The EvolutionR handlebar end weights page includes a YouTube embed titled 'Can-Am Spyder Handlebar End Weights' but places it outside the main product image gallery — it sits in the product-info column alongside specs and fitment data, not as a gallery thumbnail. The primary gallery carousel contains photo-only thumbnails with no video item mixed in. Baymard found that 35% of e-commerce sites place product video this way, making the video effectively invisible: visitors scanning the gallery never encounter it, and visitors who need the video to confirm fit or installation context must locate it separately.

**RECOMMENDATION:** Move the YouTube video to gallery position 2 or 3 — immediately after the hero packshot. Add a thumbnail image with a play-button overlay so the video is discoverable inside the gallery strip alongside the photo thumbnails. Visitors who recognize the play icon will opt in; those who only want photos can continue swiping past it.

**Why this matters:** Baymard's 2019 benchmark confirmed that videos placed outside the gallery are overlooked by the majority of visitors. For a handlebar vibration-reduction product where the mechanism of action — weighted bar ends absorbing resonance — is not self-evident from a static photo, a 30–60 second installation or ride-quality demonstration video in gallery position 2–3 is one of the highest-leverage media assets available. Burying it in a side column means it does almost no purchase-intent work.

▸ video-integration.md, Finding 8 [Gold]

#### product-media F-03 — No In-Scale Reference Image in Gallery

**SECTION:** gallery
**ELEMENT:** `.gallery-thumbnails` (proposed location for new in-scale image)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** All visible gallery thumbnails show the handlebar end cap against studio backgrounds from multiple angles. None of the ~7-8 gallery images places the product next to a recognizable size reference — no hand holding the bar end, no side-by-side with a handlebar or common object, no ruler. The weight spec (0.85 lbs, 8x heavier than stock) appears in the text panel but text dimensions alone do not resolve the perceptual size question: visitors new to the Spyder F3/RT platform cannot judge whether this cap is the size of a golf ball or a soda can without a reference image. Baymard benchmarked 28% of major e-commerce sites as missing in-scale images; this gallery fits that pattern.

**RECOMMENDATION:** Add at least one gallery image showing the EvolutionR bar-end cap held in a gloved or bare hand, or mounted on an actual Can-Am Spyder handlebar with the grip visible for context. For a pair product, showing both units side-by-side in hand communicates scale and pairing at once. If a lifestyle or install shot already exists showing fitment on the bike, promote it into the gallery — it doubles as a scale reference.

**Why this matters:** Baymard observed that 42% of shoppers attempt to judge product size from images. When no scale reference is available, size-mismatch anxiety triggers hesitation or post-purchase disappointment. For a fitment-critical aftermarket part whose compatibility is defined by a specific year-model-trim range, a scale reference image also signals that this is a real product tested on actual hardware, reinforcing trust in the fitment guide alongside it.

▸ image-quantity-types.md, Finding 4 [Gold]

#### product-media F-06 — Hero Image Missing fetchpriority="high" for LCP

**SECTION:** hero
**ELEMENT:** `img.product-hero` (referenced via Product schema `image` URL)
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** The product hero image (`canam-spyder-handlebar-end-weights-2024-up-gradient-main.jpg`, confirmed via Product schema JSON-LD) is the primary above-fold visual and the probable LCP element at desktop viewport. The page head preloads font assets (Teko woff2 and Font Awesome woff) but contains no `link rel="preload" as="image"` for the hero product image, and no `fetchpriority="high"` attribute is visible in the page source for the hero `<img>` element. Google recommends `fetchpriority="high"` for likely LCP images; gallery images at position 2+ should be lazy-loaded, but the hero must be treated as a priority resource.

**RECOMMENDATION:** Add `fetchpriority="high"` to the hero gallery image element that renders `canam-spyder-handlebar-end-weights-2024-up-gradient-main.jpg`. Pair this with explicit `width` and `height` attributes on the same element to prevent Cumulative Layout Shift. Remove any `loading="lazy"` attribute that may be applied globally to all images. This is a single HTML attribute change to one element in the product template; it overlaps with `performance-ux F-01` and resolves both findings simultaneously.

**Why this matters:** LCP is a Core Web Vitals ranking factor in Google Search since 2021. The product hero image on a standard e-commerce PDP is the most common LCP element. Treating it identically to lazy-loaded below-fold gallery images delays the browser fetch and directly degrades the LCP score, which affects both search visibility and the perceived responsiveness of the page for first-time visitors arriving from paid or organic search.

▸ image-quantity-types.md, Finding 11 [Gold]

### trust-credibility

#### trust-credibility F-01 — Perfect 5.0 Rating Triggers Skepticism — No Distribution Shown

**SECTION:** product-info-buy-box
**ELEMENT:** `div[class*="rating"]` at e6 (y=353, height=30 CSS px); star icons at e7 (y=354)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The rating widget displays five fully-filled stars with '(15 reviews)' and no star distribution breakdown. The structured data (JSON-LD) confirms the aggregate rating is a perfect 5.0 across all 15 reviews. A perfect score with 15 reviews does not match the credibility sweet spot: purchase likelihood peaks for products rated 4.0-4.7 and declines as ratings approach 5.0, because shoppers interpret perfect scores as curated or gated rather than authentic. There is no rating distribution bar showing how many 1-star through 5-star reviews exist, which is the display pattern that allows shoppers to verify authenticity.

**RECOMMENDATION:** If the product genuinely holds a 5.0 average, display the full star distribution breakdown (percentage of 5-star, 4-star, 3-star, 2-star, and 1-star reviews) immediately below the aggregate score. A visible distribution — even one that shows 14 five-stars and 1 four-star — signals that reviews have not been filtered and converts skeptical shoppers better than a bare perfect score. Do not suppress or filter reviews to maintain the 5.0; the review solicitation policy should invite all purchasers regardless of satisfaction level (FTC 16 CFR §465.7 also requires this).

**Why this matters:** A page-wide 5.0 with no distribution breakdown reads as suspicious to evaluative shoppers — the same audience most likely to purchase a $59.95 specialty accessory. Spiegel Research Center data confirms that purchase likelihood decreases as ratings approach 5.0, and that verified-authentic imperfection outconverts curated perfection.

▸ social-proof-patterns.md, Finding 1 [Gold]

#### trust-credibility F-03 — Payment Trust Badges Absent Near Add-to-Cart CTA

**SECTION:** product-info-buy-box
**ELEMENT:** `div.atc-zone` (no badge row present); footer `e18` carries the only badges
**SOURCE:** VISUAL
**PRIORITY:** HIGH

**OBSERVATION:** The page's full payment badge row — Visa, Mastercard, Amex, Discover, Google Pay, Apple Pay, PayPal, Amazon Pay, and Affirm — appears exclusively in the footer (scroll position 581+, element `e18`). The Add to Cart zone in the product info column has no security badge, guarantee icon, or payment method indicator adjacent to it. The PayPal Pay Later widget (`e16`, y=442) is the only trust-adjacent element in the CTA zone, and it surfaces a financing offer rather than a security assurance. Baymard's behavioral research shows that users perceive security cues as locally relevant: a badge in the footer does not register as applying to the purchase action above.

**RECOMMENDATION:** Add a compact trust badge row immediately below the Add to Cart button — three elements is the recommended maximum per section. A reasonable set for this store: the PayPal Verified mark (highest visual attention and recognition), a money-back guarantee badge citing the return policy, and a free-shipping confirmation. If a Norton or SSL seal is available, substitute it for one of these. The footer badge row can remain as-is; the CTA-adjacent row is additive.

**Why this matters:** 19% of shoppers abandon a recent checkout citing credit-card trust concerns (Baymard). Trust badges answer that anxiety only when placed at the moment of decision — beside the CTA — not in a footer users rarely reach on a single-product page.

▸ trust-and-credibility.md, Finding 23 [Gold]

#### trust-credibility F-06 — No Verified Buyer Signal in Above-Fold Review Summary

**SECTION:** product-info-buy-box
**ELEMENT:** `i.star-icon` at e7 (y=354, height=18 CSS px); review count at e6 (y=353)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The above-fold review summary shows star icons and '(15 reviews)' count with no accompanying 'Verified Buyer' indicator visible in the hero zone. Whether verified-buyer badges appear on individual reviews inside the tab panel cannot be confirmed from the above-fold capture alone, so this is scored as PARTIAL rather than FAIL. The aggregate rating display — the element most shoppers see before deciding whether to scroll — does not communicate that these reviews are from confirmed purchasers.

**RECOMMENDATION:** If your review platform records purchase verification (order-matched reviews), add a 'Verified Buyers' label to the aggregate rating display — for example '(15 reviews — Verified Buyers)' or a shield/checkmark icon adjacent to the review count. This surfaces the verification signal at the point where most visitors make their trust assessment, rather than requiring them to scroll into the tab panel.

**Why this matters:** Spiegel Research Center data shows a 15% increase in purchase likelihood when shoppers see verified-buyer status versus anonymous reviews of the same rating. For a $59.95 specialty part where purchase confidence hinges on fitment trust, that signal is load-bearing.

▸ trust-and-credibility.md, Finding 12 [Gold]

#### trust-credibility F-07 — Phone Number and Contact Link Prominent Above Fold

**SECTION:** header
**ELEMENT:** `header` at e15 (y=35, height=102 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The phone number `(800)211-1396` and a Message Us link are placed in the header (`e15`, y=35), visible above fold on initial page load with no scrolling required. A real, accessible phone number at the top of a specialty aftermarket product page is a meaningful trust signal for shoppers with pre-purchase fitment questions.

**RECOMMENDATION:** No change required. The current placement is effective for this surface. Maintain the visible phone number and contact link in the header through future template revisions.

**Why this matters:** Visible contact information is one of the core E-E-A-T Trustworthiness signals; its absence on a specialty parts page would create meaningful doubt about business legitimacy.

▸ trust-and-credibility.md, Finding 23 [Gold]

#### trust-credibility F-09 — Fitment Guide Displays Model-Specific Compatibility Above Fold

**SECTION:** fitment-guide
**ELEMENT:** `table.fitment-guide` (visible in right column of product hero, scroll_y≈293)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** A year-and-model fitment matrix (2024-2026 Spyder F3-L / F3-S / F3-T / RT / RTL) is displayed in the right column adjacent to the product imagery, above fold. This directly addresses the primary purchase anxiety for this product type: fitment compatibility. Showing exact model codes rather than a generic compatibility statement demonstrates genuine product knowledge.

**RECOMMENDATION:** No change required. Maintaining and expanding this fitment grid for all product years as the vehicle lineup evolves is the highest-leverage trust action for this catalog.

**Why this matters:** Incorrect fitment is the leading reason for returns on aftermarket parts. A clearly displayed fitment guide reduces purchase hesitation, return rates, and the customer-service burden of fitment questions.

▸ trust-and-credibility.md, Finding 23 [Gold]

### visual-cta

#### visual-cta F-02 — No Sticky Add to Cart on 1,661px Page

**SECTION:** product-info-buy-box
**ELEMENT:** `[class*="badge"]` at e10 (y=1006, height=60 CSS px) and e17 (y=1587) — both at x=1835, off-screen on standard widths
**SOURCE:** VISUAL
**PRIORITY:** HIGH

**OBSERVATION:** The page is 1,661px tall. Once a visitor scrolls past approximately 520px, the Add to Cart button and $59.95 price disappear from view. The only sticky elements present — `e17` at x=1835 and `e10` at x=1835 — sit 1,835px from the left edge of a 1,920px viewport and carry no purchase copy. Visitors reading the product description and Can-Am Spyder fitment guide in the second viewport have no visible purchase path without scrolling back to the top of the page.

**RECOMMENDATION:** When the visitor scrolls past the initial Add to Cart button (approximately scroll_y 520 on desktop), display a sticky bar fixed to the viewport top or bottom. The bar should show the product name (truncated), price ($59.95), and an Add to Cart button. Trigger it only after the primary CTA scrolls out of view, and dismiss it when the user scrolls back up to the original CTA zone.

**Why this matters:** Content-engaged shoppers who read through the full product description and fitment chart represent high-intent visitors. Removing the purchase path while they are consuming that content converts motivated readers into bouncers. Multiple independent A/B tests on product pages of comparable scroll depth show persistent CTAs lift completed orders by 7-10%.

▸ cta-design-and-placement.md, Finding 11 [Bronze]

## Methodology Notes

Single-shot dispatch (`dispatch_shape="single"`, `degraded_mode=false`). Cross-device finding independence is the expected outcome here: every canonical f_ref has `devices_present` length 1, so `scope_page_synchronized_refs` is intentionally empty. Findings rendered above appear only on the desktop audit; the mobile counterparts (where they exist) appear only in `audit-mobile.md`. Ethics gate is CLEAR — all seven canonical ethics findings rendered PASS/CLEAR and are not enumerated in this document by default (see synthesizer-emission-v1.json `humanized_findings` for the full ethics check list).

Note for dev verification: the desktop baton's Product schema lacks `mpn` and `hasMerchantReturnPolicy`, while the mobile baton's schema includes both. Verify the production server's response on both devices and align the schema output before shipping the `content-seo F-02` and `content-seo F-04` fixes.
"""


def main() -> None:
    atomic_write_text(OUT, CONTENT)
    print(f"wrote: {OUT}")
    print(f"size: {OUT.stat().st_size} bytes")


if __name__ == "__main__":
    main()
