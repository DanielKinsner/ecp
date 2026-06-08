# Audit — AWDMods.com Homepage (mobile)

## Executive Summary

On a 390-wide phone the first screen jumps straight from the search bar into four stacked `Select Make / Model / Year / Trim` dropdowns, and the `FIND PARTS` button — the page's only conversion action — falls below the fold behind Year and Trim, undersized at ~40% width with a low-contrast grey label. There is no headline, no value statement, and the only way to browse by category in the first viewport is the unlabeled hamburger drawer. The store sells real products with prices and a few genuine 5.0 ratings, but the head carries only `OnlineStore` and `WebSite` JSON-LD, the title is `AWDMods – AWDMods`, and there is no meta description or `og:image`. Start with the hero: add a headline, surface category links above the fold, and make `FIND PARTS` a full-width, high-contrast, in-view button. Then gate the checkout-script prefetch off the homepage and close the structured-data and price-anchoring gaps.

## Ethics Gate

One ADJACENT finding, no BLOCK findings.

- **ethics F-16 — Privacy Policy Links to Staging Domain, Not Canonical Store** (MEDIUM, ADJACENT): the footer Privacy Policy link points to `https://e1520g-k3.myshopify.com/policies/privacy-policy` (a Shopify staging domain) instead of the canonical `awdmods.com` path. See the rendered finding below.

Remaining ethics checks (free-shipping disclosure, fabricated-urgency absence, genuine review counts, newsletter disclosure, CCPA opt-out link, US-only cookie-consent posture, decorative newsletter imagery) returned CLEAR and are not rendered here.

## Top Priorities

### Rebuild the first mobile screen: headline, in-view labeled button, and visible category links

The mobile hero asks the visitor to do the hardest task first and hides the reward. Above the fold there is no headline or value sentence — the search field, four `Select` dropdowns, and a `FIND PARTS` button are the only content, and the dropdown labels describe the tool, not the offer (visual-cta F-11). The `FIND PARTS` button itself spans only ~40% of the width while the dropdowns above it run nearly edge-to-edge, its label and icon render in muted grey rather than white, and Year, Trim, and the button all fall below the 844px first screen, so the core task requires four cold-start decisions plus a scroll before it can even be run (visual-cta F-12, performance-ux F-95). A browse-minded shopper who does not know their exact vehicle has no visible category path at all — the departments live entirely behind the unlabeled hamburger drawer and a carousel that only begins at the bottom edge of the screen (category-navigation F-50). Add a short headline and subhead above the selector, make `FIND PARTS` a full-width button with a white label, tighten the vertical rhythm so the button sits in view, and surface a compact row of named category links (Performance, Exterior, Interior, Handling, Electronics) directly beneath the selector.

### Keep the primary path reachable on scroll and stop prefetching checkout on the homepage

Two mobile-specific structural gaps compound each other. The header that holds search, cart, and menu scrolls away with the page and is not pinned, and once the hero `FIND PARTS` button scrolls off there is no sticky bar to return to it — a shopper who decides to act mid-page has to scroll all the way back to the top (performance-ux F-18, visual-cta F-67). Meanwhile the head fires 74 prefetch tags for the Shopify checkout bundle (polyfills, Google Pay, PayPal, address autocomplete) on a homepage where no one is checking out, while carrying no preload for any above-fold image — pure latency tax paid by every mobile visitor over cellular (performance-ux F-76). Pin a compact sticky bar (logo, search, cart, or a vehicle-selector entry point) so the primary path stays one tap away at any depth, gate the checkout-web prefetch to the cart and checkout routes, and add a `rel="preload" as="image" fetchpriority="high"` for the mobile LCP element.

### Add Product and AggregateRating structured data to the rated, priced featured products

The featured products display a 5.0-star rating and live prices ("From $135.99", "$49.00") on screen, but the page's structured data declares only `OnlineStore` and `WebSite` — there is no `Product`, `Offer`, or `AggregateRating` markup (content-seo F-62, trust-credibility F-15). The rating, price, and availability a customer can already see are not in a form Google Shopping, ChatGPT Shopping, or Perplexity can read, so the page cannot earn rating-star or price rich results for these items. A controlled test attributed roughly a 20% organic-traffic uplift to review schema alone. Add server-rendered JSON-LD on the product templates (and ideally an `ItemList` on this homepage) with `Product`/`Offer` (price, priceCurrency, availability) plus `AggregateRating` (ratingValue, ratingCount) mirroring exactly what the page displays, then validate with Google's Rich Results Test.

### Give the featured price a reference anchor and an installment line, and add product reassurance

The featured floor-mats card prices at a flat "FROM $135.99" with nothing to anchor it against — no MSRP strikethrough, no compare-at, no savings figure — and the neighboring card at $49.00 sets the only on-page comparison, which makes the $135.99 item read as the expensive option rather than the premium one (pricing F-43). The card also shows only the lump-sum price with no "pay in 4" or "as low as $34" line, even though Shop Pay sits in the footer payment row, so installment infrastructure almost certainly exists but is never surfaced where intent forms (pricing F-96). And there is no returns, guarantee, or warranty cue anywhere near the products — for a Made-to-Order $135.99 mat set, the shopper's live question is "what happens if this doesn't fit my car?" and the page answers it nowhere (trust-credibility F-27). Render an MSRP strikethrough or complete-the-set framing above the price, surface a Shop Pay Installments / Affirm line beneath it for items above ~$50, and add a one-line reassurance ("Fitment guaranteed or your money back", "Easy 30-day returns") near the card.

### Rewrite the head: descriptive title, meta description, and an Open Graph image

The homepage title is `AWDMods – AWDMods` — the brand name duplicated, ~17 characters, carrying no category or fitment keyword. There is no meta description (the only fallback is the single word `AWDMods`), no `og:image`, and the product images carry their CSS class list as alt text (content-seo F-32, content-seo F-75, content-seo F-76). Titles under 30 characters are rewritten by Google more than 95% of the time. Rewrite the title to front-load the offer and the cars ("Performance Parts for WRX, STI, Focus RS & ST | AWDMods"), add a ~150-character meta description and matching `og:description`, add a 1200x630 `og:image`, and set each product image's `alt` from the product title at the card component level so every card is corrected at once.

## Findings by Cluster

### visual-cta F-11 — No Hero Headline or Value Proposition Above the Vehicle Selector

**SECTION:** hero
**ELEMENT:** headline block (absent — proposed location: above the Select Make dropdown, before e74 at y=203 CSS px)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The top of the mobile homepage jumps straight from the search bar into four "Select Make / Model / Year / Trim" dropdowns and a "FIND PARTS" button, with no headline or value-proposition sentence anywhere above the fold. A first-time visitor who lands here in the first five seconds sees the brand name in the logo and a vehicle-lookup form, but nothing that states what AWDMods sells, who it is for, or why to buy here rather than a competitor. The dropdown labels do the page's only talking, and they describe the tool, not the offer.

**RECOMMENDATION:** Add a short headline and one supporting line in the empty band directly above the Select Make dropdown — for example a benefit-led headline naming the audience and category ("Performance and styling parts for your WRX, STI, and Focus RS/ST") with a one-line subhead on fitment confidence. Keep the headline to roughly two lines so it does not push the "FIND PARTS" button further down the first screen.

**Why this matters:** Within the first five seconds a visitor decides whether the page is relevant; with no headline answering "what is this and is it for me," shoppers who are not already sold on the brand bounce before they ever engage the vehicle selector, and the entire hero rests on a tool the visitor has no stated reason to use.

▸ hero-section-psychology.md, Finding 1: The 5-Second Test — Clarity Is the Foundational Hero Metric (Gold) [Gold]

### visual-cta F-12 — FIND PARTS Button Is Undersized, Not Full-Width, and Its Label Reads Low-Contrast Grey

**SECTION:** primary-cta
**ELEMENT:** `button` ("Find parts") at e84 (y=466, height=55 CSS px)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The "FIND PARTS" button is the single conversion action in the hero, yet it is the smallest interactive target on the first screen: it spans roughly 40 percent of the width while the four dropdowns above it are nearly full-width, and it sits left-aligned rather than anchored across the thumb zone. Its label and search icon render in a muted grey on the blue fill instead of white, so the button text is lower-contrast than the plain white dropdown labels directly above it — the most important action on the screen is visually quieter than the form fields that feed it.

**RECOMMENDATION:** Make "FIND PARTS" a full-width button matching the width of the dropdowns above it and set the label and icon to white for a strong contrast against the blue fill. Sizing the primary action at least as large as the inputs it submits keeps it the easiest target to tap and the clearest next step after the dropdowns are filled.

**Why this matters:** Larger, edge-anchored buttons are acquired faster and more reliably by thumbs, and a primary CTA that is smaller and lower-contrast than its own form fields signals it is a minor control; on mobile, where the selector is the main conversion path, a quiet undersized submit button costs completed lookups.

▸ cta-design-and-placement.md, Finding 4: Fitts's Law — Larger Buttons Are Faster and Easier to Acquire (Gold) [Gold]

### visual-cta F-67 — No Sticky CTA After the Find Parts Button Scrolls Out of View

**SECTION:** sticky-cta
**ELEMENT:** sticky CTA bar (absent — proposed location: viewport-bottom-sticky, appearing after the hero Find Parts button scrolls offscreen)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The mobile homepage runs roughly four screens deep — hero, category cards, Featured Collection, newsletter, footer — but the only conversion action, the hero "FIND PARTS" button, disappears after the first screen and nothing replaces it. As the visitor scrolls through the category carousel and featured products there is no pinned bar offering to jump back into the vehicle selector or to shop, so a shopper who decides to act mid-page has to scroll all the way back up to the hero or hunt for the search bar.

**RECOMMENDATION:** Add a compact sticky bottom bar that appears once the hero button scrolls off — surfacing either the vehicle-selector entry point or a "Shop All" action — so the primary path stays one tap away at any scroll depth. Keep the bar to roughly 50–60px tall so it does not crowd the content it floats over.

**Why this matters:** On multi-screen mobile pages the primary action scrolls out of view quickly, and persistent bottom CTAs recover conversions from shoppers who become ready to act below the fold; without one, intent that builds mid-page leaks away while the visitor reorients to find the next step.

▸ cta-design-and-placement.md, Finding 11: Sticky "Add to Cart" on Mobile — 5-37% Conversion Lift (Bronze) [Bronze]

### visual-cta F-46 — Top FREE SHIPPING / SHOP NOW Bar Sits in the Banner-Blindness Zone

**SECTION:** announcement-bar
**ELEMENT:** `div[class*="announce"]` (free-shipping bar) at e69 (y=0, height=41 CSS px)
**SOURCE:** BOTH
**PRIORITY:** LOW

**OBSERVATION:** The free-shipping message and its "SHOP NOW" link live in a full-width colored bar pinned above the logo — the exact slot users have learned to treat as a promotional banner and skip. The free-shipping threshold is a genuine reason-to-buy signal, but presenting it as a top promo strip with an embedded generic "SHOP NOW" link means a large share of visitors scan straight past both the offer and the link to the content below.

**RECOMMENDATION:** Surface the free-shipping threshold as plain text inside the content flow near the hero or the conversion path, not only in the top banner, and give the embedded link a destination-specific label instead of generic "SHOP NOW". Repeating the shipping promise where the eye actually lands keeps it working even when the banner is ignored.

**Why this matters:** Content styled as a top promotional banner is reliably skipped, so a real purchase incentive parked there does little work; pulling the free-shipping message into the content flow recovers a trust-and-value signal that is currently spent on a slot most shoppers' eyes route around.

▸ eye-tracking-and-scan-patterns.md, Finding 6: Banner Blindness — Users Ignore Ad-Like Content Across 3 Decades (Gold) [Gold]

### visual-cta F-16 — SHOP PERFORMANCE Category Card Button Is Clear and Well-Contrasted

**SECTION:** secondary-cta
**ELEMENT:** `div[class*="star"]` (Performance card) at e17 (y=571, height=278 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The category-card CTA gets the basics right: "SHOP PERFORMANCE" is a solid blue button with a crisp white label that names exactly where it goes, and it is the most contrasting element inside the dark card. The label is specific rather than a generic "Shop Now", so a scanning visitor understands the action at a glance.

**RECOMMENDATION:** Keep this treatment for the category-card CTAs and reuse the same solid-fill, white-label, destination-specific pattern for the hero's "FIND PARTS" button so the primary action reads at least as strongly as these secondary ones.

**Why this matters:** Specific, high-contrast button labels let scanning shoppers act without re-reading the surrounding card, which keeps the category carousel a working entry point into the catalog.

▸ cta-design-and-placement.md, Finding 14: Specific Labels Outperform Generic Labels (Gold) [Gold]

### trust-credibility F-13 — Featured Collection Cards Show 5.0/5.0 With No Review Count

**SECTION:** star-rating-widget
**ELEMENT:** `div[class*="rating"]` ("5.0 / 5.0") at e90 (y=1424, height=21 CSS px)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The Featured Collection cards display a perfect 5.0/5.0 star rating with no review count anywhere beside the stars, and the rating appears on some cards but not others in the same row. A bare 5.0 with no count gives a shopper nothing to weigh: they cannot tell whether the average rests on two ratings or two hundred, and a flawless 5.0 reads as less believable than a 4.4 backed by a visible count. Purchase likelihood peaks in the 4.0–4.7 range and declines as the average approaches 5.0, so a perfect score shown without the volume behind it works against the card rather than for it.

**RECOMMENDATION:** Render the review count next to every star row (for example "5.0 (8)" or "5.0 — 8 reviews") and show the rating on all cards consistently, not just some. If a product has fewer than five reviews, prioritize collecting more before featuring it, since the first five reviews carry the bulk of the conversion lift; if a product genuinely has only a handful of perfect ratings, showing the small count is more credible than showing a bare 5.0.

**Why this matters:** Products with five reviews convert at roughly 270% the rate of products with none, and that lift depends on the shopper seeing the volume; a perfect 5.0 shown with no count both withholds the volume signal and trips the "too good to be true" skepticism that suppresses click-through on featured products.

▸ social-proof-patterns.md, Finding 1: The 4.0-4.7 Star Rating Sweet Spot (Gold) [Gold]

### trust-credibility F-15 — Star Ratings Carry No AggregateRating Markup for Search Results

**SECTION:** review-schema-markup
**ELEMENT:** AggregateRating JSON-LD (absent — proposed location: on the product cards under the Featured Collection heading e86 at y=938 CSS px)
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** The product cards show a star rating on screen, but the page's structured data contains only store-level and website-level markup with no `AggregateRating` or `Review` schema behind those stars. That means the ratings are visible to a person scrolling the page but invisible to search engines, which cannot render star snippets in results for ratings they cannot read. A controlled split test found that adding `AggregateRating` markup alone lifted organic traffic by roughly 20%, so a rating that exists on the page but not in the markup leaves that lift on the table.

**RECOMMENDATION:** Add `AggregateRating` JSON-LD to each rated product (and to the product objects surfaced on the homepage) with `ratingValue` plus a real `ratingCount` or `reviewCount`, mirroring exactly what the page displays. If a review app is already collecting the ratings, enable its schema output rather than hand-coding; verify the result in Google's Rich Results Test so the values match the visible stars.

**Why this matters:** Star snippets in search results are one of the highest-ROI organic-visibility wins available, and a ~20% organic-traffic uplift was measured from review schema alone; without the markup the store earns the trust cost of displaying ratings while forfeiting the search visibility those same ratings could buy.

▸ ugc-reviews-seo.md, Finding 7: Review Schema (AggregateRating) Produces ~20% Organic Traffic Uplift (Gold) [Gold]

### trust-credibility F-27 — No Guarantee or Return-Policy Reassurance Near the Products

**SECTION:** guarantee-policy-block
**ELEMENT:** guarantee/returns cue (absent — proposed location: adjacent to the product price, after e89 at y=1406 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The homepage carries exactly two trust cues: a free-shipping bar pinned to the top and a payment-mark row buried in the footer. There is no money-back guarantee, no returns reassurance, and no warranty cue anywhere near the products themselves. For an automotive-parts store where a Made-to-Order floor mat set runs $135.99, the shopper's live question is "what happens if this doesn't fit my car?" and the page gives no answer at the point of consideration. A short returns or guarantee statement near the price answers that question where it is being asked.

**RECOMMENDATION:** Surface a one-line reassurance near the product cards and the Find Parts action (for example "Easy 30-day returns" or "Fitment guaranteed or your money back"). Frame it as a confident promise rather than a conditional escape clause, since positive framing converts better; keep the full policy linked from the footer as it is today.

**Why this matters:** Return-policy and guarantee visibility is one of the strongest purchase-decision factors for online shoppers and a documented driver of conversion lift; for fitment-sensitive automotive parts at this price point, the absence of any reassurance near the product leaves the shopper's biggest objection unanswered exactly when they would act.

▸ trust-and-credibility.md, Finding 15: Money-Back Guarantee Increased Sales by 21-26% (Bronze) [Bronze]

### trust-credibility F-28 — Payment Badges Sit Only in Footer, Far From Any Buying Decision

**SECTION:** footer
**ELEMENT:** `li[class*="payment"]` (PayPal badge) at e134 (y=2152, height=35 CSS px)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** Every recognized payment mark the store accepts is confined to one row at the bottom of the footer, below the copyright. The brands themselves are strong (PayPal carries the highest eye-tracking notice rate of the common seals, and Visa and Mastercard are universally recognized), so the asset is good, but placement is doing little work. A badge in the footer reads as decoration; a badge shown where the shopper is deciding to act reassures them at the exact moment the question "is this store legitimate and safe to pay?" arises. On this homepage the trust-anchoring moments are the Find Parts action and the Featured Collection cards, and neither carries a payment or security cue.

**RECOMMENDATION:** Mirror two or three of the strongest payment marks (PayPal, Visa, Mastercard) into a compact row near the Featured Collection cards or beneath the Find Parts action, while keeping the full set in the footer. Cap the surfaced set at two or three so the row reads as reassurance rather than clutter.

**Why this matters:** Shoppers form their judgment of whether a store is safe to buy from at the moment of action, not at the bottom of the page most never reach; payment marks placed only in the footer waste their strongest brands by showing them after the buying decision has already been made.

▸ trust-and-credibility.md, Finding 8: Trust Badge Proximity to CTA Matters More Than Presence (Silver) [Silver]

### trust-credibility F-31 — Recognized Payment Brands and Social Links Present in Footer

**SECTION:** footer
**ELEMENT:** `li[class*="payment"]` (Visa badge) at e136 (y=2186, height=35 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The footer leans on recognized, high-trust brands: the payment row carries Visa, Mastercard, PayPal, Apple Pay, Google Pay, Shop Pay, Discover, and Amex, and the social links point to real Facebook, Instagram, and YouTube profiles. These are exactly the marks shoppers recognize, and presenting the genuine accepted methods is a solid baseline trust foundation to build on.

**RECOMMENDATION:** Keep the recognized payment marks and the real social links in place; the strongest next step is to extend a trimmed version of this row higher up the page near the products.

**Why this matters:** Recognized payment and social brands are the trust signals shoppers respond to most, so having the genuine set already in the footer means the raw assets for a stronger trust presentation are present and only need better placement.

▸ trust-and-credibility.md, Finding 10: PayPal Seal Attracts Most Visual Attention (Silver) [Silver]

### content-seo F-32 — Title Tag Is Just the Brand Name Repeated Twice

**SECTION:** title-tag
**ELEMENT:** `<title>` (`AWDMods – AWDMods`) at e100 (head element near the logo at y=171 CSS px)
**SOURCE:** DOM
**PRIORITY:** HIGH

**OBSERVATION:** The homepage title tag reads "AWDMods – AWDMods" — the brand name repeated, 17 characters total, with the second half wasted on a duplicate. There is no product category, no vehicle fitment (Focus RS/ST, WRX/STI), and no keyword a shopper would type. Titles under 30 characters get rewritten by Google more than 95% of the time, so even this thin title is unlikely to survive into the search result. The 51–60 character range that earns the most clicks is left almost entirely empty.

**RECOMMENDATION:** Rewrite the title to front-load what AWDMods sells and which cars it fits, then close with the brand — for example "Focus RS/ST & WRX/STI Performance Parts | AWDMods" (around 49 characters). Keep the primary keyword in the first two to three words so it survives the F-pattern scan, and drop the duplicated brand name. This is a single-file change in the theme head.

**Why this matters:** The title tag is the single biggest CTR lever for a page that already ranks. A title that is just the brand name twice gives Google nothing to match against a buyer's query and forfeits the 51–60 character window that drives the most clicks.

▸ title-formulas-serp-psychology.md, Finding 4: Front-Loading the Primary Keyword Increases CTR (Gold) [Gold]

### content-seo F-62 — Star Ratings and Prices Shown but No Product Schema

**SECTION:** product-schema
**ELEMENT:** Product / AggregateRating JSON-LD (absent — proposed location: describing the priced, star-rated featured products, before e89 at y=1406 CSS px)
**SOURCE:** DOM
**PRIORITY:** HIGH

**OBSERVATION:** The featured products display a 5.0-star rating and live prices ("From $135.99", "$49.00") in the page, but the structured data only declares `OnlineStore` and `WebSite` — there is no `Product`, `Offer`, or `AggregateRating` markup. The rating, price, and availability that customers can already see are not expressed in a form Google Shopping, ChatGPT Shopping, or Perplexity can read, so the page cannot earn rating-star or price rich results for these items.

**RECOMMENDATION:** Add server-rendered JSON-LD on the product templates (and ideally an `ItemList` on this homepage) including `Product`/`Offer` with price, priceCurrency, and availability plus `AggregateRating` with ratingValue and ratingCount. `AggregateRating` must reflect real, unsuppressed review data. A controlled test found review schema alone lifted organic traffic about 20%.

**Why this matters:** Without `Product` and `AggregateRating` markup the store forfeits star and price rich results that materially raise click-through, and it stays invisible to AI shopping agents that match products by structured Schema.org data plus identifiers.

▸ schema-product-markup.md, Finding 10: Review Schema Alone Produces ~20% Organic Traffic Uplift (Gold) [Gold]

### content-seo F-76 — Featured Product Images Use CSS Class Names as Alt Text

**SECTION:** image-alt-text
**ELEMENT:** `img[alt]:not([alt=""])` (Velourtex floor-mats image) at e23 (y=1000, height=266 CSS px)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The Featured Collection product images carry their CSS class list ("card__image motion-reduce object-center object-contain") as their accessible name instead of descriptive alt text. A screen reader announces the class string, and Google Images and Google Lens have no readable subject for the image. Visually these are specific, identifiable products — the Velourtex fitted carpet floor mats and the wheel/stripe kit — so the absence of real alt text is both an accessibility gap and a lost visual-search opportunity. The same pattern repeats across the collection images (e23 through e31).

**RECOMMENDATION:** Set the alt attribute from the product title field so each image gets descriptive text following the [Product Name] [Key Attribute] [View] pattern — for example "Velourtex fitted carpet floor mats for Ford Focus RS / ST, set of 4, black with blue trim". Fixing it at the card component level corrects every card on the page at once.

**Why this matters:** Missing descriptive alt text is the most commonly cited WCAG 2.1 SC 1.1.1 violation in ADA web-accessibility lawsuits (3,948 US federal filings in 2025) and it makes product images invisible to Google Lens, which handles roughly 5 billion commercially-intentful visual searches a month.

▸ image-seo-alt-text.md, Finding 11: WCAG 2.1 SC 1.1.1 Is the Legally-Cited Alt Text Standard (Gold) [Gold]

### content-seo F-75 — Meta Description and Social Preview Are Placeholder Brand Text

**SECTION:** meta-description
**ELEMENT:** `meta[name="description"]` (absent; `og:description` = "AWDMods") at e100 (head element near the logo at y=171 CSS px)
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** The homepage has no meta description, its Open Graph description is just the word "AWDMods", and there is no Open Graph image. Search engines therefore generate a snippet from whatever fragment they find, social shares and AI shopping previews show no descriptive summary, and there is no thumbnail for an AI agent or messaging app to display. None of these surfaces is given a single sentence describing that this is a performance-parts store for WRX, STI, Focus RS, and ST vehicles.

**RECOMMENDATION:** Add a 140–155 character meta description and a matching `og:description` that name the catalog and audience — for example "Performance and styling parts for Subaru WRX/STI and Ford Focus RS/ST — shop by vehicle and find the right fit fast." Add an `og:image` (the logo on a branded background works) so previews and AI thumbnails render an image.

**Why this matters:** Descriptive metadata is what search snippets, social cards, and AI shopping previews show to qualify a click; leaving it null or as a bare brand word cedes that messaging to algorithms and removes the thumbnail that AI-referred traffic — which converts at higher intent — relies on.

▸ ai-search-agentic-discovery.md, Finding 4: AI-Referred Traffic Shows Higher Purchase Intent Signals (Silver) [Silver]

### content-seo F-87 — Homepage Has Almost No Descriptive or Benefit-First Copy

**SECTION:** description-block
**ELEMENT:** intro/value-proposition block (absent — proposed location: below the vehicle-selector hero, before the category cards)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The homepage carries almost no descriptive text. The hero is a search field plus four "Select Make/Model/Year/Trim" dropdowns and a FIND PARTS button with no headline or value statement; the lower page is category labels ("Performance", "Intakes", "Exhaust"), product cards, and a newsletter prompt. There is no sentence that tells a first-time visitor — or an AI shopping assistant — what the store specializes in, which vehicles it fits, or why to buy here. The one descriptive line on the page is the newsletter blurb naming Focus RS/ST and WRX/STI.

**RECOMMENDATION:** Add a short benefit-first intro block beneath the vehicle selector: one headline and two or three sentences naming the audience (WRX/STI, Focus RS/ST owners), the value (verified fitment, curated performance and styling parts), and what to do next. Lead with the outcome, then the specifics, so the copy both reassures shoppers and gives crawlers extractable content.

**Why this matters:** Insufficient on-page information drives roughly 20% of purchase task failures, and a homepage with no descriptive copy gives AI shopping agents nothing to extract when a shopper asks what the store sells, suppressing both human conversion and AI-referred discovery.

▸ benefit-first-descriptions.md, Finding 2: Information Incompleteness Causes 20% of Purchase Task Failures (Gold) [Gold]

### content-seo F-63 — Canonical and Mobile Viewport Tags Are Correctly Set

**SECTION:** canonical-url
**ELEMENT:** `link[rel="canonical"]` + `meta[name="viewport"]` at e100 (head element near the logo at y=171 CSS px)
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** The homepage declares a correct self-referencing canonical — "https://www.awdmods.com/", absolute, HTTPS, and lowercase — and a proper mobile viewport meta ("width=device-width, initial-scale=1"). The canonical consolidates signals to the preferred root URL and the viewport tag confirms the page is built to render correctly on the 390-wide mobile viewport.

**RECOMMENDATION:** Keep the self-referencing canonical and viewport meta as they are. When product and collection templates are reviewed, confirm they follow the same pattern — each canonical pointing to its own `/products/[handle]` URL rather than a collection-prefixed duplicate.

**Why this matters:** A correct canonical prevents duplicate-URL signal dilution, and the viewport meta is a precondition for mobile rendering and mobile-first indexing — both are foundational technical signals the rest of the SEO work builds on.

▸ canonical-duplicate-content.md, Finding 12: Self-Referencing Canonicals Are Best Practice (Silver) [Silver]

### performance-ux F-76 — No Above-Fold Image Preload; 74 Checkout Scripts Prefetched on Home Load

**SECTION:** third-party-scripts
**ELEMENT:** `div[class*="announce"]` (free-shipping bar) at e69 (y=0, height=41 CSS px)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The page head fires 74 prefetch tags for the Shopify checkout bundle (polyfills, OnePage, Google Pay, PayPal, address autocomplete, and dozens more) on the homepage, where no one is checking out yet. On a phone over cellular, that network contention competes with the assets the visitor actually needs to see and act on. At the same time the head carries no preload for any above-fold image, so the browser discovers and prioritizes the visible content late. The first mobile viewport is the free-shipping bar over a dark vehicle finder with no prioritized imagery to settle the layout quickly.

**RECOMMENDATION:** Gate the checkout-web bundle so it only fires on the cart and checkout routes, not the homepage. If a specific element is the mobile LCP target (the logo or the first category tile), add a matching `rel="preload" as="image"` with `fetchpriority="high"` in the head so the browser starts fetching it before it parses down to the markup.

**Why this matters:** Each 0.1s of mobile load time tracks to roughly 8% retail conversion, and prefetching the entire checkout codebase on a page no one is checking out from is pure latency tax paid by every mobile visitor. Slow first paint also reads as an untrustworthy store before the visitor has evaluated a single product.

▸ media-performance-optimization.md, Finding 1: Product Hero Image Is the LCP Element — Requires fetchpriority and Preload (Gold) [Gold]

### performance-ux F-18 — No Sticky Header or Cart Once the Visitor Scrolls Past the First Screen

**SECTION:** header-nav
**ELEMENT:** sticky header/cart bar (absent — proposed location: viewport-bottom-sticky, reachable in the thumb zone once the header scrolls away)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The header that holds search, the cart, and the menu sits at the top and scrolls away with the page — it is not pinned. Once a mobile visitor moves past the first screen into the category carousel and the Featured Collection, there is no persistent way to search, open the cart, or jump back to the vehicle finder without scrolling back to the very top. On a phone, where the natural easy-reach zone is the bottom of the screen, the most-used actions live in the hard-to-reach top corners and then disappear entirely.

**RECOMMENDATION:** Pin a compact sticky bar — logo, search, and cart — to the top or bottom of the mobile viewport so it stays reachable on scroll. A bottom bar keeps these actions in the natural thumb zone and shows a cart count badge for ongoing context.

**Why this matters:** Hidden or disappearing navigation consistently depresses engagement on mobile; when the cart and search vanish on scroll, every return trip costs the visitor a full-page scroll, which is exactly the friction that pushes phone shoppers to abandon.

▸ mobile-conversion.md, Finding 13: Mobile Navigation — Hamburger Menu vs. Bottom Navigation (Gold) [Gold]

### performance-ux F-95 — Vehicle Finder Pushes Two of Four Dropdowns and Find Parts Below the Fold

**SECTION:** fitment-guide
**ELEMENT:** `button` ("Find parts") at e84 (y=466, height=55 CSS px)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The vehicle finder is the page's primary task, but on a 390-wide phone its four sequential dropdowns (Make, Model, Year, Trim) plus the FIND PARTS button stack vertically and the action button lands below the first screen — Year, Trim, and the button are all flagged below the fold. The visitor has to make four ordered selections and scroll before they can run the search. None of the four dropdowns shows a pre-selected default, so every field is an active decision from a cold start.

**RECOMMENDATION:** Tighten the vertical rhythm so at least Make, Model, and the FIND PARTS button fit the first mobile screen, and pre-select the most common Make or collapse Year and Trim until Make and Model are chosen. Sequential disclosure (reveal Year only after Model is set) reduces the number of choices visible at once and keeps the action in view.

**Why this matters:** When the only action that starts the shopping journey sits below the fold behind four cold-start decisions, a share of mobile visitors never reach it; each added equally-weighted choice raises decision time and the odds of a silent bounce before the first product is ever seen.

▸ cognitive-load-management.md, Finding 1: Hick-Hyman Law (Gold) [Gold]

### performance-ux F-17 — Featured Collection Product Images Carry No Explicit Dimensions for CLS

**SECTION:** product-card-grid
**ELEMENT:** `img.card__image` at e23 (y=1000, height=266 CSS px)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The Featured Collection product images sit below the fold in a horizontally swipeable row and are lazy-loaded, which is correct for off-screen media. What is missing is the safeguard: if these card images do not carry explicit width and height (or a CSS `aspect-ratio` reserving their square footprint), the cards have no reserved space until each image arrives, so the row can reflow as a phone slowly pulls them in over cellular. On mobile the small screen absorbs layout shift poorly, and the orange quick-add badge overlapping each image is a tap target that can jump as the card settles.

**RECOMMENDATION:** Add explicit `width` and `height` attributes or a CSS `aspect-ratio` on the card image so the browser holds the space before the image loads. This keeps the Featured Collection row stable as the visitor swipes and prevents the quick-add badge from shifting under a thumb.

**Why this matters:** Cumulative layout shift causes misclicks and erodes trust, and its impact is proportionally larger on mobile because the screen has less room to absorb a reflow; a shifting product row at the moment a visitor reaches for the quick-add badge directly costs add-to-cart actions.

▸ media-performance-optimization.md, Finding 5: Explicit Width and Height Attributes Prevent CLS (Gold) [Gold]

### performance-ux F-13 — Header Tap Targets and Native Dropdowns Meet Mobile Sizing

**SECTION:** header-nav
**ELEMENT:** `summary.header__icon--menu` (hamburger) at e105 (y=54, height=46 CSS px)
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** The header icons (hamburger and cart) render at 46x46 CSS px and the vehicle-finder dropdowns and search field are 55px tall full-width controls — all comfortably above the WCAG 2.2 AA minimum and at the platform-recommended size, so the interactive elements are easy to hit on a phone.

**RECOMMENDATION:** Keep these control sizes as the storefront evolves; the only adjacency to watch is keeping the hamburger and the logo from crowding in the top-left corner.

**Why this matters:** Adequately sized, well-spaced tap targets keep mobile interaction error rates low and avoid the accidental taps that frustrate phone shoppers and add friction to every navigation step.

▸ mobile-conversion.md, Finding 6: Touch Target Sizing Research (Bronze) [Bronze]

### pricing F-43 — Featured "From $135.99" Price Carries No MSRP or Compare-At Anchor

**SECTION:** price-block
**ELEMENT:** `div[class*="price"]` ("From $135.99") at e89 (y=1406, height=28 CSS px)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The featured floor-mats listing prices at a flat "FROM $135.99" with nothing to anchor it against — no manufacturer MSRP, no strikethrough "regular price", and no stated savings. A shopper landing on the homepage sees a three-figure number for a floor mat with no reference point telling them whether that is a strong price or a steep one. The neighboring card ($49.00) sets the only on-page comparison, and it is roughly a third of the price, which makes the $135.99 item read as the expensive option rather than the premium one.

**RECOMMENDATION:** Render any manufacturer list price or documented prior selling price as a strikethrough above the live price (e.g. "MSRP $169.99 — From $135.99") and state the savings in both dollars and percent. If no defensible reference price exists, anchor the mat against a complete-the-set framing — show the per-pair price next to the full-vehicle kit price — so the $135.99 reads as the entry point into a higher-tier purchase rather than a bare number.

**Why this matters:** An advertised reference price raises the buyer's internal "normal" price for the item before they even calculate savings, lifting both perceived quality and deal attractiveness. Without one, a $135.99 part is judged against whatever the shopper last saw — here, a $49 item — and reads as expensive, suppressing click-through into the product page.

▸ price-anchoring.md, Finding 2: Advertised Reference Price Effects on Internal Reference Price Formation (Gold) [Gold]

### pricing F-96 — No Installment / Pay-in-4 Pricing Shown Beside the $135.99 Item

**SECTION:** price-block
**ELEMENT:** installment line (absent — proposed location: immediately below the live price on the product card, after e89 at y=1406 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The $135.99 floor-mat set sits squarely in the mid-ticket band ($50–$500) where installment messaging does the most work, yet the card shows only the lump-sum price. Shop Pay is present as a wallet icon in the footer, so installment infrastructure is almost certainly already available at checkout, but the shopper never sees a "pay in 4" or "as low as $34" line at the point where purchase intent forms. The decoupled installment figure is the number that makes a three-figure part feel affordable, and it is absent.

**RECOMMENDATION:** Surface the installment line on the product card and product page directly beneath the price — "or 4 interest-free payments of $34.00" with the provider logo. Gate it to items above ~$50 so the installment amount stays meaningful, and always keep the full price visible alongside it for disclosure.

**Why this matters:** Large-scale peer-reviewed retail data shows adding BNPL lifts basket size about 10% and purchase incidence about 9%, with the gain concentrated on mid-ticket items exactly like this one. Showing the installment price only at checkout forfeits that lift, because the affordability reframe has to land before the buy decision is made, not after.

▸ bnpl-payment.md, Finding 1: BNPL Increases Basket Size 10% — Large-Scale Peer-Reviewed Evidence (Gold) [Gold]

### pricing F-51 — Free-Shipping Threshold Stated as a Static Banner With No Progress Framing

**SECTION:** shipping-threshold
**ELEMENT:** `div[class*="announce"]` (free-shipping bar) at e69 (y=0, height=41 CSS px)
**SOURCE:** BOTH
**PRIORITY:** LOW

**OBSERVATION:** The store states its free-shipping threshold plainly in the top bar — "FREE SHIPPING on most orders $75+ — Contiguous US only" — which is the right disclosure and avoids cost-surprise later. What it does not do is convert that threshold into a moving target. The number is a static announcement; there is no progress framing such as "You are $18 away from free shipping" that updates as items are added, so the threshold informs but never actively pulls basket size upward.

**RECOMMENDATION:** Add a goal-gradient progress line that names the exact remaining amount — "You are $18.01 away from FREE shipping" — in the cart and mini-cart, updating live as items are added. Frame it from the shopper's current subtotal as a head start ("you have added $57 — $18 more for free shipping") rather than from zero, which sharpens the pull toward the threshold.

**Why this matters:** The goal-gradient effect — people accelerate effort as a goal comes into view — is the validated mechanism behind free-shipping progress bars, and specific remaining-amount framing measurably lifts average order value. A static threshold tells shoppers the rule; a live progress cue is what actually moves more carts past it.

▸ free-shipping.md, Finding 1: Goal-Gradient Effect — Scientific Foundation for Free Shipping Progress Bars (Gold) [Gold]

### pricing F-68 — Charm Pricing Used Correctly on Utilitarian Parts

**SECTION:** price-block
**ELEMENT:** `div[class*="price"]` ("From $135.99") at e89 (y=1406, height=28 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** Prices use .99 endings on utilitarian auto parts, which is the correct format for this value-positioned, non-luxury category — just-below pricing lifts purchase intent here without any quality-perception penalty. The featured prices ("From $135.99", "$49.00") follow this convention.

**RECOMMENDATION:** Keep .99 endings on functional parts. Reserve round pricing only for any genuinely premium or gift-style SKUs where round numbers read as more intentional.

**Why this matters:** Charm pricing is a low-cost micro-optimization that the meta-analytic evidence supports for non-luxury goods; using it correctly here means the page is not leaving the small but reliable just-below lift on the table.

▸ charm-pricing.md, Finding 1: Meta-Analytic Evidence for Just-Below Pricing Effects (Gold) [Gold]

### category-navigation F-50 — Only Category Path in First Viewport Is the Hidden Hamburger Drawer

**SECTION:** header-nav
**ELEMENT:** `summary` (hamburger menu trigger) at e105 (y=54, height=46 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** HIGH

**OBSERVATION:** A shopper who does not already know their exact vehicle has no visible way to browse the catalogue by category in the first screen. The departments — Performance, Handling & Brakes, Interior, Exterior, Electronics — live entirely inside the off-canvas drawer behind the hamburger icon, plus a card carousel that only starts at the bottom edge of the first viewport. Browse-oriented visitors must either tap an unlabeled hamburger or scroll past the entire fitment form before any category name appears.

**RECOMMENDATION:** Surface a compact row of named category links or tiles (Performance, Exterior, Interior, Handling, Electronics) directly beneath the fitment selector, above the fold. Keep the drawer as the exhaustive menu, but do not make it the only first-screen route into the catalogue.

**Why this matters:** Around 40% of shoppers fail to locate navigation that is hidden behind a non-obvious control; an auto-parts buyer who cannot find their category in the first screen concludes the store is hard to shop and leaves before reaching a product grid.

▸ search-and-filter-ux.md, Finding 3: 40% of Users Cannot Locate Filtering Options (Gold) [Gold]

### category-navigation F-63 — Category Carousel Reveals Roughly One Tile, Hiding Catalog Breadth

**SECTION:** subcategory-tiles
**ELEMENT:** `ul` (Performance category card list) at e15 (y=565, height=296 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The on-page category navigation is a horizontal carousel that displays one full card at a time — "Performance" dominates the viewport while only a thin edge of the next card peeks in. The five departments (Performance, Handling & Brakes, Interior, Exterior, Electronics) exist in the markup, but a shopper sees just one and must swipe blindly to discover the rest. The whole range never appears together, so the breadth of the catalogue is invisible on first view.

**RECOMMENDATION:** Replace the one-card-at-a-time carousel with a 2-column tile grid or a peeking carousel that shows at least two cards plus a visible slice of a third, so the eye registers that multiple categories exist. Label the scroll affordance or show all five tiles stacked to make the breadth explicit.

**Why this matters:** Position primacy means the first tile captures the bulk of attention and the rest are rarely reached; when a shopper cannot see that Interior, Exterior, and Electronics also exist, they assume the store is narrower than it is and self-route less effectively into the categories they actually want.

▸ merchandising-psychology.md, Finding 1: Products in First 1-2 Rows Receive 2-3x More Clicks (Silver) [Silver]

### category-navigation F-05 — Shop by Vehicle Drawer Lists Only Two Vehicles

**SECTION:** header-nav
**ELEMENT:** `summary` ("Shop by Vehicle" drawer submenu) at e36 (y=757, height=467 CSS px)
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** Inside the menu drawer, the "Shop by Vehicle" browse path expands to just two destinations — Subaru WRX / STI and Ford Focus RS / ST. The fitment selector on the same page presents a full Make / Model / Year / Trim cascade, so a shopper who chooses to browse by vehicle instead of using the dropdowns lands on a near-empty hub that contradicts the catalogue depth the selector promises.

**RECOMMENDATION:** Populate the Shop by Vehicle drawer with the full set of supported vehicle collections, or replace the static two-item list with a link into the dynamic fitment results. Either way, the by-vehicle browse path should reflect the same vehicle coverage the FIND PARTS selector implies.

**Why this matters:** A vehicle hub that lists only two platforms both wastes internal-linking value for the rest of the vehicle collections and tells browse-mode shoppers the store may not carry parts for their car, pushing them to leave rather than search.

▸ collection-page-architecture.md, Finding 2: Hub-and-Spoke Taxonomy Consolidates Topic Authority (Silver) [Silver]

### category-navigation F-88 — Search Box Is a Visible Full-Width Input at Page Top

**SECTION:** header-nav
**ELEMENT:** `input[type="search"]` (header search field) at e53 (y=110, height=55 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** Search is exposed as a real, full-width text input directly below the logo rather than hidden behind an icon-only toggle. The field spans the entire content width, so a typical multi-word query such as "focus rs cat back exhaust" stays visible while it is typed and edited.

**RECOMMENDATION:** Keep the open search input as the primary affordance. Confirm against your own search logs that the field width holds the 25–30 character queries most shoppers type, and that the predictive-search dropdown returns relevant matches for one-character misspellings and abbreviations like "cat-back".

**Why this matters:** An always-visible, wide search box is the single most reliable way for a high-intent visitor to reach a specific part fast; hiding it behind an icon or clipping the query both suppress the highest-converting traffic on the site.

▸ search-and-filter-ux.md, Finding 17: Search Box Width Must Accommodate the Typical Query (Gold) [Gold]

### category-navigation F-03 — Vehicle Fitment Selector Anchors the Compatibility Path

**SECTION:** fitment-guide
**ELEMENT:** `button` ("Find parts") at e84 (y=466, height=55 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** For an auto-parts catalogue, fitment is the primary conversion lever, and the homepage leads with it: a Make / Model / Year / Trim cascade resolving to a "FIND PARTS" button sits in the first viewport. This routes shoppers straight to compatible results instead of forcing them to guess part names in free-text search.

**RECOMMENDATION:** Keep the fitment selector in its top-of-page position. Ensure each dropdown disables impossible combinations as the prior field is chosen, and that the saved vehicle persists into category pages so the compatibility constraint carries through the whole browse, not just this entry point.

**Why this matters:** Sites selling compatibility-dependent products see roughly 65% task failure without a fitment filter; surfacing it on the homepage removes the dominant reason auto-parts shoppers abandon before they reach a product.

▸ search-and-filter-ux.md, Finding 5: Compatibility Filters — Only 35% Task Success (Gold) [Gold]

### ethics F-16 — Privacy Policy Links to Staging Domain, Not Canonical Store

**SECTION:** footer-policy-links
**ELEMENT:** `footer` (Information block, Privacy Policy link) at e4 (footer region, last block on the page)
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** The Privacy Policy footer link points to `https://e1520g-k3.myshopify.com/policies/privacy-policy` — a Shopify development/staging domain — rather than a canonical first-party URL on awdmods.com. A visitor clicking through to review the store's data practices lands on a page hosted under an unbranded third-party domain with no visible relationship to AWDMods. CCPA/CPRA (Cal. Civ. Code § 1798.100 et seq.) requires that the privacy notice be reasonably accessible and clearly attributable to the business collecting the data; a policy hosted on a staging domain does not clearly identify AWDMods as the data controller. The Terms and Conditions link correctly uses the canonical `/pages/terms-of-service` path, confirming this is a configuration oversight rather than intentional design.

**RECOMMENDATION:** Update the Privacy Policy footer link `href` from `https://e1520g-k3.myshopify.com/policies/privacy-policy` to the canonical first-party URL (`https://www.awdmods.com/policies/privacy-policy` or the relative path `/policies/privacy-policy`). In Shopify admin, navigate to Online Store → Navigation → Footer menu and update the link destination. Confirm the policy page loads correctly at the canonical URL before publishing.

**Why this matters:** A staging-domain URL breaks the chain of attribution — a consumer reading the policy sees `e1520g-k3.myshopify.com`, not AWDMods — and creates unnecessary exposure in the event of a CCPA enforcement inquiry or class action. The fix costs nothing and removes the ambiguity entirely.

▸ ethics-gate.md, PART 6: Cross-Cutting Regulatory Landscape — Regulatory Disclosure Chain (Gold) [Gold]

## Methodology Notes

Mobile audit at 390x844 (DPR 3). Findings scoped to this device render here; page-level findings (head signals, structured data, price anchoring, image alt text, the ethics privacy-policy link) render identically in the desktop audit. Coverage spans the vehicle-fitment selector, the category carousel and hamburger drawer, the Featured Collection cards, the page head, and the footer. PASS findings are included to document what the page already does correctly.
