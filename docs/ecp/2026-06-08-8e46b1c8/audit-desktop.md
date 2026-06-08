# Audit — AWDMods.com Homepage (desktop)

## Executive Summary

The opening screen at 1920x1080 is an almost-empty black band: the only content above the category tiles is a four-step vehicle-fitment selector floating in dead space, with no headline, value proposition, hero image, or labeled primary button. The page sells real products with real prices and a few genuine 5.0 ratings, but none of that surfaces above the fold and none of it is expressed in machine-readable markup — the head carries only `OnlineStore` and `WebSite` JSON-LD, the title is `AWDMods – AWDMods`, and there is no meta description or `og:image`. Start with the hero: add a headline, fill the black band, and turn the icon-only `Find parts` magnifier into a labeled button. Then close the structured-data and price-anchoring gaps that cost both search visibility and on-page conversion.

## Ethics Gate

One ADJACENT finding, no BLOCK findings.

- **ethics F-16 — Privacy Policy Links to Staging Domain, Not Canonical Store** (MEDIUM, ADJACENT): the footer Privacy Policy link points to `https://e1520g-k3.myshopify.com/policies/privacy-policy` (a Shopify staging domain) instead of the canonical `awdmods.com` path. See the rendered finding below.

Remaining ethics checks (free-shipping disclosure, fabricated-urgency absence, genuine review counts, newsletter disclosure, CCPA opt-out link, US-only cookie-consent posture, decorative newsletter imagery) returned CLEAR and are not rendered here.

## Top Priorities

### Fill the empty above-fold band with a headline, supporting media, and a labeled primary button

The single most valuable screen on the site is doing almost no selling. From the bottom of the navigation row (~y=160) down to the category tiles (y=544), the desktop viewport is a flat black band whose only occupants are four `Select Make / Model / Year / Trim` dropdowns floating mid-screen at y=308 and a 59x59px magnifier button at the far right. There is no headline, no value statement, no product, and no supporting image — a first-time visitor scanning the top-left in the natural F-pattern lands on empty space and cannot answer what AWDMods sells or why to buy here (visual-cta F-24, performance-ux F-83, category-navigation F-52). The de-facto primary action, the `Find parts` submit, is an unlabeled search icon that visually duplicates the separate top-of-page site search, so the page's main conversion control reads as a generic search affordance rather than a commit button (visual-cta F-13, category-navigation F-46). Add a concrete headline above the selector ("Performance parts for your Subaru WRX/STI and Ford Focus RS/ST") with a one-line subhead, set an on-brand hero image or product-in-use shot behind the selector to fill the void (visual-cta F-08), pull the category tiles up so they sit above the fold, and render the selector's submit as a full, solid, labeled "Find My Parts" button. These are template-level edits to the hero section; no backend work is required.

### Add Product and AggregateRating structured data to the rated, priced featured products

The Featured Collection grid lists named products with brands (Borla, Injen, Magnaflow, Tufskinz, Lloyd Mats), live prices, and visible 5.0-star ratings with counts — yet the page exposes none of this in structured data. The only JSON-LD blocks in the head are `OnlineStore` and `WebSite`, so the stars a shopper can see cannot become rich-result stars in Google, and AI shopping agents have no machine-readable product data to match or recommend (content-seo F-61, trust-credibility F-15 on mobile mirrors this). A controlled test attributed roughly a 20% organic-traffic uplift to review schema alone. Add `ItemList` JSON-LD wrapping each featured product as a `Product` with `offers` (price, priceCurrency, availability, url) and `AggregateRating` (ratingValue, ratingCount) drawn from the same fields already rendered on the cards, render it server-side, and validate with Google's Rich Results Test. `AggregateRating` values must mirror the real review data shown on the cards.

### Give every featured price a reference anchor and an installment line

Across the Featured Collection, prices render as a single bare number — `FROM $135.99`, `$437.91`, `$1,766.00` — with no MSRP strikethrough, no compare-at, and no installment framing on items well over $1,000 (pricing F-98, pricing F-97, pricing F-23). The Borla exhaust card on the same row proves the theme already supports a reference price: it shows `FROM $1,649.99` over a struck-through `$1,847.99`. So the capability exists and is used on exactly one of eight cards, which teaches shoppers to expect an anchor and then withholds it everywhere else. Populate the compare-at field on discounted SKUs so the theme renders the struck-through reference price uniformly, lead higher-ticket items with the saving stated explicitly ("Save $198"), and surface a Shop Pay Installments / Affirm line beneath each live price for items roughly $150 and up (the store already supports Shop Pay — its mark is in the footer payment row). A four-figure exhaust reads very differently as "$1,766" against nothing versus "$1,847.99 → $1,766.00, as low as $147/mo."

### Rewrite the head: descriptive title, meta description, and an Open Graph image

The homepage title is `AWDMods – AWDMods` — the brand name duplicated with an en-dash, 17 characters, carrying no category or fitment keyword. There is no meta description (the only fallback is the single word `AWDMods`), and the head requests a large-image social card (`twitter:card='summary_large_image'`) but supplies no `og:image` to fill it (content-seo F-32, content-seo F-74, content-seo F-60). Titles under 30 characters are rewritten by Google more than 95% of the time, so even this thin title rarely survives into the result. Rewrite the title to front-load the offer and the cars ("Focus RS/ST & WRX/STI Performance Parts | AWDMods", ~49 characters), add a ~150-character meta description naming the catalog and vehicles, and add a 1200x630 `og:image`. All three are single-file head edits.

### Add a trust block and surface social proof above the fold

The homepage answers "what do you sell" but never answers "why trust you." The only above-fold trust-adjacent element is the free-shipping bar, which speaks to delivery cost, not credibility; there is no guarantee, returns promise, customer count, press mention, or aggregate-rating figure anywhere on the page (visual-cta F-27, trust-credibility F-10). Compounding this, most featured cards carry zero reviews, and the cards that do rate show a flawless 5.0 on just two or three reviews — a perfect average on a tiny count reads as "too good to be true" rather than reassuring (trust-credibility F-23, trust-credibility F-09). Add a compact trust strip below the hero (guarantee, easy returns, a real customers-served or aggregate-rating figure, a visible support number), keep collecting reviews from every buyer so featured products cross five reviews and the average settles into the trusted 4.0–4.7 band, and prefer featuring products that already carry reviews so the grid leads with proof instead of bare prices.

## Findings by Cluster

### visual-cta F-24 — Hero Band Has No Headline or Value Proposition

**SECTION:** hero
**ELEMENT:** `button` ("Find parts") at e117 (absent headline — proposed location: above the vehicle selector, before e117 at y=308)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The first thing a visitor sees is a black hero band holding nothing but the four-field vehicle selector. There is no headline and no value proposition, so a first-time visitor cannot answer what the store sells or why to buy here in the opening seconds. The brand name `AWDMods` and the tiny "Car parts, simplified." line by the garage icon are the only clues, and neither sits in the hero as a clear promise. The minimum-viable hero needs a headline plus a supporting line; both are absent above the fold.

**RECOMMENDATION:** Add a concrete headline directly above the selector that names the offer and the audience — for example "Performance parts for your Subaru WRX/STI and Ford Focus RS/ST" — with a one-line subheadline stating the differentiator (fitment guarantee, free shipping over $75, fast dispatch). Keep the headline to 6–12 words so it scans in the opening seconds. This is a copy addition in the hero section template.

**Why this matters:** Visitors form a stay-or-leave judgment within the first seconds on visual clarity; a hero with no headline or value proposition fails that test and pushes cold traffic to bounce before they ever reach the category grid.

▸ hero-section-psychology.md, Finding 1: The 5-Second Test (Gold) [Gold]

### visual-cta F-13 — Hero's Only CTA Is a 59px Icon-Only 'Find parts' Button

**SECTION:** primary-cta
**ELEMENT:** `button[aria-label='Find parts']` at e117 (y=308, height=59 CSS px)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The hero offers no full-width, clearly-worded primary button. The only actionable control is a 59x59px magnifier button whose accessible name is "Find parts" but which visually reads as a search icon, not a primary action. At that size it is an icon target rather than a conversion button, and an icon-only control gives a scanning visitor no read on what happens when they click it. The de-facto primary action on the page is therefore small, label-less, and easy to overlook.

**RECOMMENDATION:** Render the selector's submit as a full, solid, labeled button alongside the dropdowns, with text such as "Find My Parts" on a high-contrast fill sized to match the 59px dropdown height. Naming the action and outcome on a button-shaped control, rather than a bare magnifier icon, makes the primary path unmistakable. Style it distinctly from the top-of-page site-search icon so the two findability tools are not confused.

**Why this matters:** When the page's main action is an unlabeled icon, visitors who scan rather than read cannot find the path forward, and a smaller target is also slower to acquire; both suppress the share of visitors who engage the selector at all.

▸ cta-design-and-placement.md, Finding 14: Specific Labels Outperform Generic Labels (Gold) [Gold]

### visual-cta F-08 — Hero Band Is Empty Black Space With No Supporting Media

**SECTION:** hero
**ELEMENT:** `button` ("Find parts") at e117 (absent hero media — proposed location: behind the vehicle selector, before e117 at y=308)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The hero has no supporting image or video; it is a plain black band with the vehicle selector centered in empty space. A product-in-use or build-context visual is one of the minimum hero elements and is the single strongest first-fixation driver; here that slot is blank. The empty band also wastes roughly 280px of the most-viewed real estate on the page, real estate that currently communicates nothing about the products. The first real imagery (the category-card photos) does not begin until y~430.

**RECOMMENDATION:** Set a strong on-brand image as the hero background behind the vehicle selector — a tuned WRX/STI or Focus RS in context, or a hero shot of installed parts — and keep the selector legible with an overlay. A single high-quality in-context photo fills the dead space and gives the opening view a concrete subject instead of a black void.

**Why this matters:** The hero occupies the highest-attention zone on the page; leaving it as empty black space forfeits the first-fixation moment that authentic product imagery is proven to capture, weakening first impressions for every visitor.

▸ hero-section-psychology.md, Finding 7: Hero Image Types (Gold) [Gold]

### visual-cta F-38 — Five Identical 'SHOP' Category CTAs Compete With No Primary

**SECTION:** subcategory-tiles
**ELEMENT:** `div` (Performance category card) at e29 (y=544, height=302 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** Because the hero contributes no headline or CTA, the first real call to action a visitor meets is the row of five category cards, and all five buttons — "SHOP PERFORMANCE", "SHOP HANDLING", "SHOP INTERIOR", "SHOP EXTERIOR", "SHOP ELECTRONICS" — share the same blue fill, same size, and same weight. Nothing in this row claims to be the primary path; the visitor has to evaluate all five equally, which adds choice friction at the exact moment the page should be pointing them somewhere.

**RECOMMENDATION:** If one category drives the most revenue or matches the most common landing intent, give that card's CTA a heavier treatment (larger, or a distinct accent) and let the other four read as secondary. If all five are genuinely equal, anchor the row with a single dominant action above it — a "Find My Parts" selector CTA or a "Shop All" button — so the eye has one clear primary before the category split.

**Why this matters:** Differentiating the primary action from look-alike siblings is a low-effort change with measured add-to-cart and conversion-rate lift; five equal-weight CTAs leave the visitor to resolve the hierarchy themselves, which costs attention and engagement.

▸ cta-design-and-placement.md, Finding 3: CTA Color Differentiation Lifted Conversion 18.4% (Bronze) [Bronze]

### visual-cta F-27 — Only Above-Fold Trust Element Is a Shipping Promo, Not Credibility

**SECTION:** trust-signal-strip
**ELEMENT:** `div[class*="announce"]` (free-shipping bar) at e34 (y=0, height=41 CSS px)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The opening view carries one trust-adjacent line, the free-shipping announcement bar reading "FREE SHIPPING on most orders $75+ — Contiguous US only", so the page is not entirely bare of reassurance. But a shipping promo answers how much delivery will cost, not whether the store can be trusted. There is no review aggregate, star rating, customer count, or guarantee in the hero — the credibility signal a cold visitor evaluating an unfamiliar parts retailer needs first. Product cards lower down show star ratings, but none of that proof surfaces above the fold.

**RECOMMENDATION:** Surface a compact aggregate near the top of the page — a star rating with review count beside the logo or under the vehicle selector. Pair it with the existing free-shipping bar so the opening view carries both a logistics reassurance and a credibility signal.

**Why this matters:** A single visible credibility signal in the hero measurably reduces the "is this store real" hesitation that drives cold-traffic bounce; relying on a shipping promo alone leaves that skepticism unanswered at the moment it forms.

▸ hero-section-psychology.md, Finding 10: Trust Signal in Hero (Gold) [Gold]

### visual-cta F-55 — Category 'SHOP' Buttons Use High-Contrast Blue Against Dark Cards

**SECTION:** primary-cta
**ELEMENT:** `div[class*="announce"]` (CTA palette) at e34 (y=0, height=41 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The category-card buttons get the color choice right: a saturated blue fill that contrasts cleanly with the dark photographic cards and the dark page chrome, so each button reads unmistakably as a clickable action rather than blending into the background.

**RECOMMENDATION:** Keep the contrasting blue CTA fill as the action color and reserve it for primary actions. When a single primary CTA is introduced in the hero, draw it from this same blue so the action color stays consistent across the page.

**Why this matters:** A CTA color that contrasts with the surrounding page is the most reliable lever for making buttons noticeable, and this page already satisfies it — worth preserving as other hierarchy fixes are made.

▸ color-psychology.md, Finding 2: Contrast and Visual Hierarchy Drive CTA Performance (Silver) [Silver]

### trust-credibility F-23 — Most Featured Collection Cards Carry Zero Reviews

**SECTION:** product-card-grid
**ELEMENT:** `div[class*="price"]` (Lloyd Mats price block) at e104 (y=1346, height=26 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** HIGH

**OBSERVATION:** The majority of cards in the Featured Collection display a price and a "Made to Order" tag but carry no stars and no review count whatsoever — the Lloyd Mats Velourtex mats at "FROM $135.99", the Injen intake at "$437.91", the Borla exhaust, the Magnaflow exhaust, and the Lloyd Mats trunk mat. These are the products the homepage chose to feature, yet they show no social proof at the exact moment a shopper is deciding whether the store and the part are credible. The higher-priced items here (a $437.91 intake, a four-figure exhaust) are where that gap costs the most.

**RECOMMENDATION:** Run a post-purchase review request triggered by delivery confirmation and prioritize the highest-priced SKUs first, where the review lift is largest. Until each featured card crosses five reviews, feature products that already have reviews so the homepage grid leads with social proof instead of bare prices.

**Why this matters:** Products with five reviews convert at roughly 270% the rate of products with zero, and the effect is strongest on higher-priced items; featuring review-less parts on the homepage spends prime real estate on cards that give a first-time visitor no reason to trust either the part or the store.

▸ social-proof-patterns.md, Finding 3: Five Reviews = 270% Conversion Lift (Gold) [Gold]

### trust-credibility F-09 — Featured Collection Cards Show Perfect 5.0/5.0 on Only 2-3 Reviews

**SECTION:** star-rating-widget
**ELEMENT:** `div[class*="rating"]` ("5.0 / 5.0") at e105 (y=1362, height=21 CSS px)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** Every rated card in the Featured Collection shows a flawless 5.0 out of 5.0, and the review counts beside them are tiny: "(2)" on the Revo Designs decal kit and "(3)" on both Tufskinz cards. A perfect average built on two or three reviews reads as "too good to be true" to a shopper, who has no critical review to weigh against the praise. Purchase likelihood peaks when the displayed average sits in the 4.0–4.7 range; a uniform 5.0 across the grid suppresses that confidence, and the very low counts compound the doubt because the rating could swing on a single new review.

**RECOMMENDATION:** Keep collecting reviews from every buyer (not just satisfied ones) so the average settles into the trusted 4.0–4.7 band and the count climbs past five, where most of the conversion lift lands. Display the actual review count prominently next to the stars and surface a star-distribution breakdown so the rating reads as earned rather than curated.

**Why this matters:** A clean 5.0 on two or three reviews converts worse than a 4.4 on twenty: shoppers discount perfect ratings as manipulated, and on an automotive store where parts carry real fitment risk, that skepticism directly suppresses add-to-cart on the highest-intent visitors who actually read the stars.

▸ social-proof-patterns.md, Finding 1: The 4.0-4.7 Star Rating Sweet Spot (Gold) [Gold]

### trust-credibility F-10 — Homepage Has No Company-Credibility or Aggregate Trust Block

**SECTION:** trust-badge-cluster
**ELEMENT:** trust strip (absent — proposed location: in the gap below the hero and category band, before the product grid)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The homepage answers "what do you sell" well but never answers "why should I trust you". Aside from the "FREE SHIPPING on most orders $75+" bar, there is no money-back guarantee, no returns promise, no "as seen in" or press mention, no total-customers-served or aggregate-reviews figure, and no prominent "why buy from us" block — and the footer offers link columns and payment icons but no customer-service phone number. For a specialty automotive store competing without the brand equity of a major retailer, the browsing-stage anxiety is squarely "is this a real company that will stand behind these parts", and nothing on the page addresses it.

**RECOMMENDATION:** Surface a compact trust strip below the hero and category band: a money-back or fitment guarantee, a returns promise, a total-orders or aggregate-rating figure, and a visible support phone number. Lead with the strongest genuine claim rather than stacking generic seals.

**Why this matters:** Trust signals lift conversion most for stores without established brand recognition; a homepage that shows products but no company credibility leaves first-time visitors to resolve "is this legit" on their own, and many resolve it by leaving.

▸ trust-and-credibility.md, Finding 18: Unknown Brands Need More Trust Signals Than Established Brands (Gold) [Gold]

### trust-credibility F-62 — Recognized Payment Badges Present in Footer

**SECTION:** footer
**ELEMENT:** `ul[class*="payment"]` (payment-badge row) at e81 (y=2841, height=35 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The footer carries a clean row of widely recognized payment marks — Amex, Apple Pay, Discover, Google Pay, Mastercard, PayPal, Shop Pay, and Visa. These are consumer-familiar brands (PayPal and the card networks carry the strongest trust-by-recognition effect), and they signal accepted, legitimate payment without resorting to obscure security seals.

**RECOMMENDATION:** Keep these recognized marks. When you build out a checkout or purchase zone, repeat the strongest of them (PayPal and the card networks) adjacent to the pay button, where proximity to the moment of payment anxiety adds the most reassurance.

**Why this matters:** Familiar payment logos reassure shoppers that payment is safe and routine; retaining them protects a trust signal the store already gets right.

▸ trust-and-credibility.md, Finding 10: PayPal Seal Attracts Most Visual Attention (Silver) [Silver]

### content-seo F-32 — Title Tag Is Just the Brand Name Repeated Twice

**SECTION:** title-tag
**ELEMENT:** `<title>` (`AWDMods – AWDMods`) at e113 (head element near the logo at y=56)
**SOURCE:** DOM
**PRIORITY:** HIGH

**OBSERVATION:** The homepage title tag reads "AWDMods – AWDMods" — the brand name repeated, 17 characters total, with the second half wasted on a duplicate. There is no product category, no vehicle fitment (Focus RS/ST, WRX/STI), and no keyword a shopper would type. Titles under 30 characters get rewritten by Google more than 95% of the time, so even this thin title is unlikely to survive into the search result. The 51–60 character range that earns the most clicks is left almost entirely empty.

**RECOMMENDATION:** Rewrite the title to front-load what AWDMods sells and which cars it fits, then close with the brand — for example "Focus RS/ST & WRX/STI Performance Parts | AWDMods" (around 49 characters). Keep the primary keyword in the first two to three words so it survives the F-pattern scan, and drop the duplicated brand name. This is a single-file change in the theme head.

**Why this matters:** The title tag is the single biggest CTR lever for a page that already ranks. A title that is just the brand name twice gives Google nothing to match against a buyer's query and forfeits the 51–60 character window that drives the most clicks.

▸ title-formulas-serp-psychology.md, Finding 4: Front-Loading the Primary Keyword Increases CTR (Gold) [Gold]

### content-seo F-74 — Homepage Has No Meta Description At All

**SECTION:** meta-description
**ELEMENT:** `meta[name="description"]` (absent — proposed location: head, near the brand mark e113 at y=56)
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** There is no meta description on the homepage, and the only fallback — `og:description` — is the single word "AWDMods". When Google builds the search snippet it will scrape whatever text it can find on a page that is almost entirely navigation and product thumbnails, which tends to produce a disjointed, low-CTR snippet. The store has no control over how its most important page is summarized in the result.

**RECOMMENDATION:** Add a meta description of roughly 150 characters that names the catalog and the vehicles it covers — for example "Performance, exterior, and interior parts for the Ford Focus RS/ST and Subaru WRX/STI. Free shipping on most orders $75+ in the contiguous US." Write it as a sentence a shopper would read, not a keyword list.

**Why this matters:** The meta description is the store's pitch in the search result. Leaving it blank hands snippet control to Google's auto-extraction, which on a thumbnail-heavy homepage routinely produces a weak summary that suppresses click-through.

▸ title-formulas-serp-psychology.md, Finding 1: Position #1 Gets 27.6% CTR (Gold) [Gold]

### content-seo F-60 — No Open Graph Image for Social and AI Previews

**SECTION:** og-image
**ELEMENT:** `meta[property="og:image"]` (absent — proposed location: head, near the brand mark e113 at y=56)
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** The head requests a large-image social card (`twitter:card='summary_large_image'`) but never provides an image to fill it — there is no `og:image` and no `twitter:image`. `og:title` and `og:description` are both just "AWDMods". When the homepage is shared on Facebook, sent in a message, or surfaced by an AI assistant building a preview, there is no thumbnail to show, so the link renders as a bare title-and-URL card next to competitors that show a branded image.

**RECOMMENDATION:** Add an `og:image` (and a matching `twitter:image`) pointing to a 1200x630 branded preview — the AWDMods logo over a hero build shot works well. Because the card type is already set to `summary_large_image`, supplying the image is the only missing step.

**Why this matters:** Shared and AI-surfaced links with a strong preview image are clicked far more than bare text cards. A declared image card with no image is the worst of both worlds — it reserves the large slot and then leaves it empty.

▸ image-seo-alt-text.md, Finding 4: Google Lens Processes ~20 Billion Visual Searches/Month (Gold) [Gold]

### content-seo F-61 — Featured Products Carry No Product or Rating Schema

**SECTION:** product-schema
**ELEMENT:** Product / ItemList / AggregateRating JSON-LD (absent — proposed location: describing the Featured Collection grid, anchored on its heading e79 at y=906)
**SOURCE:** DOM
**PRIORITY:** HIGH

**OBSERVATION:** The Featured Collection grid lists named products with brands (Borla, Injen, Magnaflow, Tufskinz, Lloyd Mats), live prices, and visible 5.0-star ratings with review counts, yet the page exposes none of this in structured data — the only JSON-LD blocks are `OnlineStore` and `WebSite`. With no `Product`, `ItemList`, or `AggregateRating` markup, Google cannot surface star ratings or price for these items, and AI shopping agents (ChatGPT Shopping, Perplexity) have no machine-readable product data to match or recommend.

**RECOMMENDATION:** Add `ItemList` JSON-LD wrapping each featured product as a `Product` with `name`, `offers` (price, priceCurrency, availability, url), and `AggregateRating` (ratingValue, ratingCount) drawn from the same fields already rendered on the cards. Render the markup server-side so Merchant Center and AI crawlers see it without executing JavaScript. `AggregateRating` must mirror only real, unsuppressed review data.

**Why this matters:** Adding `AggregateRating` schema alone produced roughly a 20% organic traffic uplift in a controlled test, and the same `Product` markup is what feeds Google Shopping and AI shopping agents. Leaving real, rated products undescribed forfeits both the star-rating rich result and AI commerce visibility.

▸ schema-product-markup.md, Finding 10: Review Schema Alone Produces ~20% Organic Traffic Uplift (Gold) [Gold]

### content-seo F-27 — Product Card Images Use CSS Class Names as Alt Text

**SECTION:** image-alt-text
**ELEMENT:** `img.card__image` at e35 (y=989, height=271 CSS px)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** Every product image in the Featured Collection carries an alt value of "card__image motion-reduce object-center object-contain" — the image's CSS class list bled into the alt attribute instead of a real description. A screen reader announces that string verbatim, and Google has nothing meaningful to read for the photo. These are clearly identifiable products (floor mats, a cold air intake, a cat-back exhaust, a gauge accent kit), so the alt text should name them. The same non-descriptive alt repeats across every card (e35–e44).

**RECOMMENDATION:** Set each alt attribute from the product feed to the product name plus a key attribute — for example "Borla cat-back ATAK exhaust for the Ford Focus RS" — following a [Product Name] [Key Attribute] pattern under about 125 characters. The fix is at the card component template, so it corrects every card at once.

**Why this matters:** Descriptive alt text is both the WCAG 2.1 SC 1.1.1 standard plaintiffs cite (3,948 federal ADA web suits were filed in 2025) and the signal Google and Google Lens use to surface product images in visual search. CSS class names as alt text fail on accessibility and discoverability simultaneously.

▸ image-seo-alt-text.md, Finding 11: WCAG 2.1 SC 1.1.1 Is the Legally-Cited Alt Text Standard (Gold) [Gold]

### content-seo F-64 — Self-Referencing HTTPS Canonical on the Homepage

**SECTION:** canonical-url
**ELEMENT:** `link[rel="canonical"]` (`https://www.awdmods.com/`) at e113 (head element near the brand mark at y=56)
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** The homepage canonical is "https://www.awdmods.com/" — absolute, HTTPS, lowercase, and self-referencing, matching the live URL exactly. This is exactly what Google wants and avoids the trailing-slash and www-variant duplication that trips up many stores.

**RECOMMENDATION:** Keep this as-is. When extending to product and collection templates, hold the same standard: a self-referencing, absolute, lowercase canonical that resolves to the `/products/[handle]` path rather than any collection-prefixed duplicate.

**Why this matters:** A correct self-referencing canonical consolidates ranking signals onto the preferred URL and prevents tracking-parameter and slash variants from fragmenting equity — a clean foundation worth preserving as the catalog grows.

▸ canonical-duplicate-content.md, Finding 12: Self-Referencing Canonicals Are Best Practice (Silver) [Silver]

### performance-ux F-37 — No Above-Fold Image Preload; Category Tile Is an Unprioritized LCP Element

**SECTION:** lcp-element
**ELEMENT:** `img.card__image` (Performance category tile) at e35 (y=989, height=271 CSS px)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** The opening viewport carries no preloaded above-fold image. The head preloads two web fonts with `fetchpriority="high"` but issues no `<link rel="preload" as="image">` for any visual element. The largest paint in the first screen is the row of five full-bleed category tile photos at y=544; without a `fetchpriority` signal or a preload, the browser discovers and ranks those images at default priority, behind the font and stylesheet requests it already prioritized. On a page whose first screen is otherwise a flat black band, those tiles are the Largest Contentful Paint, and they are the slowest thing the browser has been told to care about.

**RECOMMENDATION:** Add a `<link rel="preload" as="image" fetchpriority="high">` in the head for the first (left-most) tile image and set `fetchpriority="high"` on that tile's `<img>`. Serve the tile art through a `<picture>` element offering AVIF then WebP so the LCP byte cost drops 30–50 percent. Leave the remaining four tiles at default priority so they do not compete with the first paint.

**Why this matters:** Vodafone's controlled A/B test tied a 31 percent LCP improvement to 8 percent more sales, and Deloitte measured 8.4 percent higher retail conversion per 0.1s of mobile speed. When the LCP element loads at default priority behind fonts, every visitor waits longer for the first screen to feel finished, which compounds directly into lost add-to-cart starts.

▸ media-performance-optimization.md, Finding 1: Product Hero Image Is the LCP Element — Requires fetchpriority and Preload (Gold) [Gold]

### performance-ux F-83 — Empty Black Band Wastes the Entire Above-Fold Zone on Desktop

**SECTION:** hero
**ELEMENT:** `select` ("Select Year") at e88 (y=308, height=59 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** HIGH

**OBSERVATION:** At 1920x1080 the opening viewport is almost entirely a black void. Below the navigation row and above the category tiles, the band from roughly y=160 to y=544 holds nothing except the four Make/Model/Year/Trim dropdowns floating in the middle at y=308. A visitor scanning the top-left in the natural F-pattern lands on empty space — there is no store headline, no merchandising, no proof, and no product until they scroll past the fold to reach the tiles and the Featured Collection. The single most valuable screen on the site is doing almost no selling.

**RECOMMENDATION:** Fill the black band with a compact value line above the selector (a one-line headline plus the free-shipping proof that already exists in the announcement bar) and pull the category tiles or a featured build up into the first viewport so the screen carries merchandising. Reduce the vertical black padding so the selector and the first tile row both sit above the fold.

**Why this matters:** Users form a credibility judgment in the first seconds and scan the top-left first; a screen that shows only an empty band signals nothing to buy and gives the F-pattern nothing to catch. Above-fold emptiness on the highest-traffic screen suppresses engagement before the shopper ever reaches a product.

▸ cognitive-load-management.md, Finding 6: The F-Pattern — How Users Scan Product Pages (Gold) [Gold]

### performance-ux F-91 — Vehicle Finder Stacks Four Sequential Native Dropdowns With No Default

**SECTION:** fitment-guide
**ELEMENT:** `select` ("Select Make") at e86 (y=308, height=59 CSS px)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The vehicle finder is the primary action in the opening screen and it asks the visitor to complete four sequential native dropdowns — Make, then Model, then Year, then Trim — before it will return anything. Each select opens its own long option list, and none carries a sensible default or recently-used state, so a returning shopper repeats the full four-step sequence every visit. Native selects are the slowest of the available input patterns and the four-step gate stands between the visitor and every fitment-filtered result.

**RECOMMENDATION:** Persist the visitor's last vehicle (the header already exposes a clear-saved-vehicle control, so the state exists) and pre-fill the selects on return so repeat shoppers skip the gate. Where an attribute has a dominant value, default to it and let the shopper change it, which removes one or more of the four decisions from the common path.

**Why this matters:** Decision time rises with each added choice step, and a four-select gate in front of the catalog is friction every fitment shopper pays before seeing a single part; persisting the vehicle and defaulting common values shortens the path to relevant products and recovers shoppers who would otherwise abandon the finder.

▸ cognitive-load-management.md, Finding 1: Hick-Hyman Law — Decision Time Scales Logarithmically with Choices (Gold) [Gold]

### performance-ux F-24 — Featured Collection Product Images Show No Reserved Aspect Ratio

**SECTION:** product-card-grid
**ELEMENT:** `img.card__image` at e40 (y=942, height=271 CSS px)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The Featured Collection product images sit above the brand, title, and price text in each card. Where an image area is not given a reserved aspect ratio or matching width and height before it loads, the text below it is pushed down as each photo paints, and the price and surrounding elements shift under the cursor. The category tiles and the product grid both rely on full-bleed photography, which is exactly the content type that reflows the layout when dimensions are not declared.

**RECOMMENDATION:** Add explicit `width` and `height` attributes (or a CSS `aspect-ratio` on the image container) matching each photo's rendered ratio so the browser holds the space before the image arrives. Pair this with the lazy-load already appropriate for the below-fold grid so the reserved box and the deferred fetch work together.

**Why this matters:** Layout shift causes misclicks and erodes trust as content jumps during load; Swappie cut CLS by 91 percent and saw a 42 percent mobile revenue increase. Unreserved image boxes in a product grid shift the price and title under the shopper at the moment they are deciding to click, which is the costliest moment to move the target.

▸ media-performance-optimization.md, Finding 5: Explicit Width and Height Attributes Prevent CLS (Gold) [Gold]

### performance-ux F-52 — Fonts Preloaded and Logo Eager-Loaded in the Head

**SECTION:** image-loading
**ELEMENT:** `img` (header logo) at e113 (y=56, height=45 CSS px)
**SOURCE:** DOM
**PRIORITY:** LOW

**OBSERVATION:** The critical web fonts are correctly preloaded with `fetchpriority="high"` and `crossorigin` in the head, and the header logo is eager-loaded with a responsive `srcset` rather than lazy-loaded — the brand mark paints without deferral.

**RECOMMENDATION:** Keep the font preloads and the eager logo as they are. Extend the same preload discipline to the first above-fold image so the visible LCP element gets the same head-start the fonts already enjoy.

**Why this matters:** Preloaded fonts avoid a flash of unstyled text that would itself shift layout, and an eager logo paints the brand immediately — both reduce the perceived time to a finished first screen, which supports the speed-trust relationship at first impression.

▸ media-performance-optimization.md, Finding 12: fetchpriority Is Baseline-Supported (Gold) [Gold]

### pricing F-98 — Featured Collection Prices Run With No Reference Anchor

**SECTION:** price-block
**ELEMENT:** `div[class*="price"]` ("From $135.99") at e104 (y=1346, height=26 CSS px)
**SOURCE:** BOTH
**PRIORITY:** HIGH

**OBSERVATION:** Across the Featured Collection grid, prices appear as a single number with no reference price beside them — "FROM $135.99", "$437.91", "$1,766.00", and the rest show no MSRP strikethrough, no "compare at", and no "was/now" pair. A visitor evaluating $437.91 or $1,766.00 in isolation has nothing to measure the number against, so the price anchors against whatever they last saw rather than against the product's market value. The Borla exhaust on the same row proves the theme already supports a reference price (it shows "FROM $1,649.99" over a struck-through "$1,847.99"), so this is unused capability rather than a platform limit.

**RECOMMENDATION:** Populate the compare-at field on any SKU with a manufacturer MSRP or documented prior selling price so the theme renders the reference price struck through above the live price, exactly as the Borla card already does. Apply it first to the higher-ticket items ($135.99 and up) where the absolute savings figure carries the most weight, and state the saving explicitly ("Save $198") so the deal magnitude is unmissable.

**Why this matters:** An advertised reference price raises the shopper's internal sense of the product's normal value before they even calculate the discount, lifting both perceived quality and deal attractiveness; without it a $1,766 part reads as expensive against nothing, suppressing click-through from the homepage into the product page.

▸ price-anchoring.md, Finding 2: Advertised Reference Price Effects on Internal Reference Price Formation (Gold) [Gold]

### pricing F-97 — No Installment Pricing On Items Over $1,000

**SECTION:** price-block
**ELEMENT:** installment line (absent — proposed location: immediately under each live price in the collection grid, after e104 at y=1346)
**SOURCE:** VISUAL
**PRIORITY:** HIGH

**OBSERVATION:** Several products in the Featured Collection sit well above $1,000 — the Borla exhaust at "FROM $1,649.99" and the Magnaflow cat-back at "$1,766.00" — yet no price carries an installment option such as "as low as $146/mo" or "pay in 4". The store clearly supports Shop Pay (its mark sits in the footer payment row next to Visa and PayPal), so the installment rail exists but is never surfaced where the buying decision is forming. Shoppers see the full four-figure number with no smaller, more approachable framing beside it.

**RECOMMENDATION:** Render the per-installment amount directly beneath each live price for items roughly $150 and up, with the provider logo for trust transfer. Lead with the installment figure and keep the full price visible in the same block, so a $1,766 part also reads as a manageable monthly commitment at the moment the shopper is weighing it.

**Why this matters:** A large-scale field study found installment availability raises purchase amounts by about 10% and purchase incidence by about 9%, with the effect concentrated on mid-to-high-ticket items; surfacing installments only at the footer instead of at the price forfeits that lift precisely on the four-figure parts where the immediate cost is the biggest barrier.

▸ bnpl-payment.md, Finding 1: BNPL Increases Basket Size 10% — Large-Scale Peer-Reviewed Evidence (Gold) [Gold]

### pricing F-23 — Was/Now Anchor Shown On One Product But Not The Grid

**SECTION:** price-block
**ELEMENT:** `div[class*="price"]` (grid price block) at e104 (y=1346, height=26 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** MEDIUM

**OBSERVATION:** The Borla exhaust card does the anchoring job well: it pairs a live "FROM $1,649.99" against a struck-through "$1,847.99", which signals both the product's worth and the quality of the deal. The problem is consistency — that treatment appears on exactly one of eight visible products, so the same grid teaches shoppers to expect a reference price and then withholds it everywhere else. A discount shown on one tile and absent on the next reads as arbitrary rather than as a coherent value story across the collection.

**RECOMMENDATION:** Surface the was/now pair on every genuinely discounted SKU the same way the Borla card does, so the savings framing is uniform across the grid. Where a product is not on sale, lead instead with a credible MSRP reference rather than leaving the price bare, so every card communicates value on the same footing.

**Why this matters:** Comparative price framing works through two channels — the product's perceived worth and the perceived quality of the deal — and both require a credible reference price; a grid that anchors one product and not its neighbors leaves most of that conversion lift on the table and makes the lone discount look less believable.

▸ price-anchoring.md, Finding 1: Comparative Price Advertising — Acquisition Value vs. Transaction Value (Gold) [Gold]

### pricing F-16 — Free Shipping Bar States Threshold Without Progress Cue

**SECTION:** shipping-threshold
**ELEMENT:** `div[class*="announce"]` (free-shipping bar) at e34 (y=0, height=41 CSS px)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The store communicates its free-shipping offer up front — "FREE SHIPPING on most orders $75+ — Contiguous US only" sits in the persistent top bar, which correctly puts the offer in front of shoppers early. What is missing is any sense of progress toward it: the $75 figure is a flat statement, not a goal the shopper can see themselves approaching, and once items are in the cart there is no "you're $18 away from free shipping" cue to convert the threshold into a basket-building target.

**RECOMMENDATION:** Add a dynamic progress message that names the specific remaining amount ("You're $18 away from FREE shipping") and updates as items are added, rather than only stating the flat $75 condition. Keep the existing header bar so the offer stays visible early, and pair it with add-on suggestions that would carry a near-qualifying order over the line.

**Why this matters:** The goal-gradient effect shows shoppers accelerate spend as they see themselves nearing a reward, and "free" itself carries disproportionate pull beyond its dollar value; a naked threshold surfaces the offer but captures none of that basket-building motion that a live progress cue would convert into higher average order value.

▸ free-shipping.md, Finding 1: Goal-Gradient Effect — Scientific Foundation for Free Shipping Progress Bars (Gold) [Gold]

### category-navigation F-46 — Vehicle Selector Submit Is an Icon-Only Square With No Label

**SECTION:** fitment-guide
**ELEMENT:** `button` (fitment submit, magnifier icon) at e117 (y=308, height=59 CSS px)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The vehicle fitment tool, the primary way a shopper narrows this auto-parts catalog to their car, ends in a magnifying-glass icon with no text. After a visitor sets Make, Model, Year, and Trim, the action that returns their compatible parts looks like a generic search icon rather than a labeled commit button. The reused magnifying glass also visually duplicates the separate site-search box at the top of the page, so the two distinct actions (free-text search vs. run-my-fitment) read as the same control.

**RECOMMENDATION:** Give the fitment submit control a visible text label such as "Find Parts" or "Show My Parts" instead of a bare magnifying glass, and style it distinctly from the top-of-page site-search icon so the two findability tools are not confused.

**Why this matters:** Compatibility-driven catalogs live or die on the fitment flow; Baymard found only 35% of shoppers successfully find a compatible product when compatibility filtering is unclear. An unlabeled commit button at the end of a four-step selection is the exact friction point where a high-intent shopper hesitates and abandons.

▸ search-and-filter-ux.md, Finding 5: Compatibility Filters — Only 35% Task Success (Gold) [Gold]

### category-navigation F-52 — Fitment Selector Floats in an Empty Black Band Above the Fold

**SECTION:** fitment-guide
**ELEMENT:** `select` ("Select Make", leftmost fitment dropdown) at e86 (y=308, height=59 CSS px)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The vehicle fitment selector is the single most valuable findability control on this page, but it is dropped into the middle of a large empty black band with nothing around it and a wide gap of dead space both above and below the dropdown row. The result is that the most attention-rich zone of the page — the area above the fold where 57% of viewing time is spent — is mostly empty, while the category cards that communicate what the store actually sells do not start until y=544.

**RECOMMENDATION:** Tighten the empty band around the selector: add a short directive headline above the dropdowns (for example "Find parts that fit your car") and reduce the vertical dead space so the selector and the first row of category cards both occupy the above-fold zone instead of leaving it largely blank.

**Why this matters:** Above-the-fold space is the most-attended real estate on the page; leaving it as an empty black band wastes the prime opportunity to orient a first-time visitor and pushes the breadth-signaling category cards into lower-attention territory, slowing the visitor's read of what the store carries.

▸ grid-layout.md, Finding 10: NNGroup Above-Fold Attention — 57% of Viewing Time (Gold) [Gold]

### category-navigation F-45 — Category Cards Don't Match the Shop-by-Category Menu Taxonomy

**SECTION:** subcategory-tiles
**ELEMENT:** `div` (Electronics category card) at e33 (y=544, height=302 CSS px)
**SOURCE:** BOTH
**PRIORITY:** MEDIUM

**OBSERVATION:** The five large category cards (Performance, Handling & Brakes, Interior, Exterior, Electronics) present themselves as the store's primary category map, but they do not line up with the "Shop by Category" menu, which lists Performance, Exterior, Interior, Handling, Drivetrain, Brakes, Cooling, Wheels, and Accessories. The "Electronics" card points to a category the top menu never offers, while Drivetrain, Cooling, Wheels, and Accessories exist in the menu but are invisible on the homepage. A shopper who navigates by the cards and a shopper who navigates by the menu are working from two different taxonomies.

**RECOMMENDATION:** Reconcile the cards and the menu to one taxonomy: either add cards for the menu categories that are currently homepage-invisible (Drivetrain, Cooling, Wheels, Accessories) or fold "Electronics" into the menu so the two surfaces name the same set of collections and use matching anchor text.

**Why this matters:** When the homepage cards and the navigation menu disagree on the category structure, shoppers cannot form a reliable mental model of how the catalog is organized, and the mismatched anchor text also dilutes the internal-linking signals that help category pages rank and pass authority.

▸ collection-page-architecture.md, Finding 7: Internal Link Anchor Text Provides Topic Context (Gold) [Gold]

### category-navigation F-99 — Site Search Is Prominent, Wide, and Top-Positioned

**SECTION:** header-nav
**ELEMENT:** `input[type="search"]` (header search field) at e58 (y=51, height=55 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The site search is an always-visible open input at the top of the page, about 929px wide, rather than hidden behind an icon-only toggle. The field is wide enough to hold long auto-parts queries (brand plus model plus part type) without truncation, and it sits in the most expected location at the top of the header.

**RECOMMENDATION:** Keep the open, full-width search field. As a small enhancement, replace the generic "Search" placeholder with a scope cue such as "Search parts, brands, or part numbers" so the field signals what the catalog can match.

**Why this matters:** A visible, generously sized search box is the baseline that lets high-intent shoppers self-serve; keeping it open and wide protects the single highest-intent findability path on the page.

▸ search-and-filter-ux.md, Finding 17: Search Box Width Must Accommodate the Typical Query (Gold) [Gold]

### category-navigation F-29 — Category Cards Expose Subcategories Plus Dedicated CTAs

**SECTION:** subcategory-tiles
**ELEMENT:** `div` (Performance category card) at e29 (y=544, height=302 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The homepage category cards do more than name a category: each one lists its key subcategories (Performance shows Intakes, Exhaust, Cooling, Drivetrain upgrades) and carries a dedicated "SHOP PERFORMANCE" style CTA. That lets a shopper self-route either to the broad category or to a specific subcategory directly from the tile.

**RECOMMENDATION:** Keep the subcategory-in-tile pattern with dedicated CTAs. If the listed subcategories are not individually clickable yet, make each one a direct link so the discovery depth the cards advertise is also navigable in one click.

**Why this matters:** Subcategory tiles let shoppers self-route to the right part of a deep auto-parts catalog instead of wading through an undifferentiated grid, which shortens the path from homepage to a relevant collection.

▸ merchandising-psychology.md, Finding 8: Subcategory Navigation Tiles Improve Discovery (Silver) [Silver]

### category-navigation F-41 — Top Navigation Is Lean and Clearly Labeled

**SECTION:** header-nav
**ELEMENT:** `nav` (primary top navigation bar) at e28 (y=115, height=47 CSS px)
**SOURCE:** VISUAL
**PRIORITY:** LOW

**OBSERVATION:** The main navigation keeps to four legible top-level entries (Shop All, Shop by Category, Shop by Vehicle, Contact) with two of them opening category and vehicle dropdowns. This is a lean top-level structure rather than a sprawling mega menu, which keeps the catalog's two natural browse paths, by category and by vehicle, obvious from the header.

**RECOMMENDATION:** Keep the lean four-item navigation. As noted in the taxonomy finding, ensure the Shop-by-Category dropdown lists the same category set the homepage cards advertise so both browse paths resolve to one consistent structure.

**Why this matters:** A small, clearly labeled top-level navigation gives shoppers the two browse paths (by category, by vehicle) without overwhelming them, and a lean link set keeps internal authority concentrated on the category pages that drive organic traffic.

▸ collection-page-architecture.md, Finding 8: Mega Menus May Dilute PageRank (Silver) [Silver]

### ethics F-16 — Privacy Policy Links to Staging Domain, Not Canonical Store

**SECTION:** footer-policy-links
**ELEMENT:** `footer` (Information block, Privacy Policy link) at e4 (y=2585, height=310 CSS px)
**SOURCE:** DOM
**PRIORITY:** MEDIUM

**OBSERVATION:** The Privacy Policy footer link points to `https://e1520g-k3.myshopify.com/policies/privacy-policy` — a Shopify development/staging domain — rather than a canonical first-party URL on awdmods.com. A visitor clicking through to review the store's data practices lands on a page hosted under an unbranded third-party domain with no visible relationship to AWDMods. CCPA/CPRA (Cal. Civ. Code § 1798.100 et seq.) requires that the privacy notice be reasonably accessible and clearly attributable to the business collecting the data; a policy hosted on a staging domain does not clearly identify AWDMods as the data controller. The Terms and Conditions link correctly uses the canonical `/pages/terms-of-service` path, confirming this is a configuration oversight rather than intentional design.

**RECOMMENDATION:** Update the Privacy Policy footer link `href` from `https://e1520g-k3.myshopify.com/policies/privacy-policy` to the canonical first-party URL (`https://www.awdmods.com/policies/privacy-policy` or the relative path `/policies/privacy-policy`). In Shopify admin, navigate to Online Store → Navigation → Footer menu and update the link destination. Confirm the policy page loads correctly at the canonical URL before publishing.

**Why this matters:** A staging-domain URL breaks the chain of attribution — a consumer reading the policy sees `e1520g-k3.myshopify.com`, not AWDMods — and creates unnecessary exposure in the event of a CCPA enforcement inquiry or class action. The fix costs nothing and removes the ambiguity entirely.

▸ ethics-gate.md, PART 6: Cross-Cutting Regulatory Landscape — Regulatory Disclosure Chain (Gold) [Gold]

## Methodology Notes

Desktop audit at 1920x1080. Findings scoped to this device render here; page-level findings (head signals, structured data, price anchoring, image alt text, the ethics privacy-policy link) render identically in the mobile audit. Coverage spans the vehicle-fitment selector, the category-card row, the Featured Collection grid, the page head, and the footer. PASS findings are included to document what the page already does correctly.
