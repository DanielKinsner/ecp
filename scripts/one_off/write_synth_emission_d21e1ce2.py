"""One-off: write synthesizer-emission-v1.json for engagement 2026-04-29-d21e1ce2.

Run from repo root:
    python scripts/one_off/write_synth_emission_d21e1ce2.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "assembly"))

from atomic_write import atomic_write_json  # noqa: E402

ENGAGEMENT = "2026-04-29-d21e1ce2"
OUT = REPO_ROOT / "docs" / "ecp" / ENGAGEMENT / "synthesizer-emission-v1.json"


def main() -> None:
    payload = {
        "schema_version": 1,
        "engagement_id": ENGAGEMENT,
        "synthesizer_model": {
            "family": "opus",
            "version": "4.7",
            "context_window": "1M",
        },
        "started_at": "2026-04-29T16:50:00.000Z",
        "completed_at": "2026-04-29T17:35:00.000Z",
        "status": "complete",
        "dispatch_shape": "single",
        "degraded_mode": False,
        "audit_documents": {
            "desktop": f"docs/ecp/{ENGAGEMENT}/audit-desktop.md",
            "mobile": f"docs/ecp/{ENGAGEMENT}/audit-mobile.md",
        },
        "priority_path": [
            {
                "mode": "bundle",
                "title": "Concentrate price, trust, and shipping signals into the buy-box",
                "severity": "HIGH",
                "narrative": (
                    "The $59.95 price renders as a standalone number in both device captures with no MSRP "
                    "strikethrough, no free-shipping line near the price, no trust badges adjacent to the "
                    "Add to Cart button, and no MerchantReturnPolicy callout — even though the schema "
                    "encodes a $7.99 shipping rate and the announcement bar carries a $75 free-shipping "
                    "threshold. The visitor evaluating this aftermarket part has to assemble the value "
                    "story from scattered signals: PayPal Pay Later renders inline at the price, but the "
                    "$15.05-to-free-shipping gap is invisible, the perfect 5.0 rating sits above without "
                    "a star distribution to defuse skepticism, and the Add to Cart button has no "
                    "risk-reversal microcopy alongside it. Devs should pull these into a single price-block "
                    "container above the ATC: MSRP or set-of-2 unit anchor, free-shipping proximity prompt "
                    "stating the $15.05 gap, a star-distribution bar under the aggregate rating, the $7.99 "
                    "shipping line surfaced from schema.org/OfferShippingDetails, and a 'Free shipping over "
                    "$75 · 90-day returns' microcopy line under the ATC button. All five are template-level "
                    "edits in one product-page partial."
                ),
                "f_refs": [
                    "pricing F-02",
                    "pricing F-04",
                    "trust-credibility F-01",
                    "trust-credibility F-03",
                    "visual-cta F-04",
                ],
            },
            {
                "mode": "severity",
                "title": "Restore CTA visibility on long scrolls — desktop and mobile both leave shoppers without a buy path",
                "severity": "HIGH",
                "narrative": (
                    "The page is 1,661px tall on desktop and 3,297px tall on mobile. On desktop the Add to "
                    "Cart button sits at roughly y=470 and disappears once the visitor scrolls into the "
                    "fitment guide and product description; the only sticky elements on the page are at "
                    "x=1835 (a 1920px viewport — they sit 171px past the right edge) and carry no purchase "
                    "copy. On mobile the inline ATC sits at roughly y=860 and is below the 844px fold even "
                    "before the visitor swipes through the gallery — and there is no sticky bottom bar to "
                    "take its place when it scrolls away. A persistent compact bar showing product name, "
                    "$59.95, and a full-width Add to Cart button — triggered via IntersectionObserver on "
                    "the inline ATC — closes both device gaps in one component. Multiple Shopify A/B tests "
                    "on comparable scroll-depth pages document 7.9–33% conversion lift from this pattern."
                ),
                "f_refs": [
                    "visual-cta F-02",
                    "visual-cta F-03",
                    "performance-ux F-03",
                ],
            },
            {
                "mode": "bundle",
                "title": "Fix the four schema and SEO leaks that suppress rich results and AI commerce matching",
                "severity": "HIGH",
                "narrative": (
                    "Four search-channel issues sit in the same JSON-LD block on this page. The H1 reads "
                    "'End Caps' while the title tag and meta description read 'End Weights' — Zyppy's Q1 "
                    "2025 dataset of 81,000 titles attributes the 76% Google rewrite rate to exactly this "
                    "kind of noun mismatch. The Offer's `priceValidUntil` is hard-coded to 2026-04-29, the "
                    "audit date itself; Google flags expired validity dates as stale and revokes Shopping "
                    "rich result eligibility. The Product schema in the desktop capture has no GTIN or MPN, "
                    "and BreadcrumbList structured data is absent across both captures. Devs can resolve "
                    "all four in one template pass: align the H1/title noun on whichever term Search "
                    "Console traffic prefers; replace the static priceValidUntil with a server-computed "
                    "rolling date 365 days out; add `mpn: \"SM-22490\"` to the Product JSON-LD; and add a "
                    "BreadcrumbList block listing Home > Spyder > Handlebar Accessories > Product Name "
                    "with matching visible breadcrumb levels."
                ),
                "f_refs": [
                    "content-seo F-01",
                    "content-seo F-02",
                    "content-seo F-03",
                    "category-navigation F-02",
                ],
            },
            {
                "mode": "severity",
                "title": "Move the product video into the gallery and turn the lone install photo into UGC volume",
                "severity": "HIGH",
                "narrative": (
                    "The 'Can-Am Spyder Handlebar End Weights' YouTube embed sits outside the gallery — in "
                    "the desktop right-rail and below the mobile Add to Cart button — exactly the placement "
                    "Baymard's 2019 benchmark identified in 35% of e-commerce sites where video does almost "
                    "no purchase-intent work because shoppers scanning the gallery never encounter it. "
                    "Reposition it as gallery item 2 with a play-button overlay so a single swipe surfaces "
                    "it. While re-instrumenting the gallery, the lone customer install photo behind the "
                    "Photos (1) tab — 6.7% of 15 reviews — should be promoted into the gallery as the final "
                    "thumbnail labelled 'Customer Install Photo,' and the post-purchase review email should "
                    "include a vehicle-specific photo prompt to lift the photo-to-review ratio. For an "
                    "aftermarket bar-end where the buyer's primary anxiety is 'what will it look like on "
                    "my Spyder,' real install footage and an in-scale reference image are doing the heaviest "
                    "lift available."
                ),
                "f_refs": [
                    "product-media F-01",
                    "product-media F-02",
                    "product-media F-03",
                    "trust-credibility F-05",
                ],
            },
            {
                "mode": "quick-wins",
                "title": "Three buy-box edits that ship in one theme commit",
                "severity": "MEDIUM",
                "narrative": (
                    "Three of the highest-confidence findings on this page resolve with copy or "
                    "HTML-attribute changes inside one product-page template. Add `fetchpriority=\"high\"` "
                    "and a matching `<link rel=\"preload\" as=\"image\">` to the hero product image — "
                    "Google's Vodafone A/B test attributes 8% more online sales to a 31% LCP improvement, "
                    "and this attribute is the lowest-cost path to that delta. Disclose the $7.99 shipping "
                    "rate (already in OfferShippingDetails) directly under the price as 'Free shipping "
                    "over $75 · $7.99 flat under threshold' — Baymard data attributes 39% of actionable "
                    "abandonment to shipping costs that surface only at checkout. And surface the existing "
                    "Reward Points program in the price block as 'Earn 60 points on this order' for "
                    "logged-out visitors so the program is discoverable at the moment of purchase intent. "
                    "All three are single-template edits with no backend or schema changes."
                ),
                "f_refs": [
                    "performance-ux F-01",
                    "checkout-flows F-01",
                    "post-purchase F-04",
                ],
            },
        ],
        "quick_wins_manifest": [
            "audience F-01",
            "audience F-02",
            "category-navigation F-01",
            "category-navigation F-02",
            "category-navigation F-04",
            "category-navigation F-06",
            "category-navigation F-07",
            "checkout-flows F-04",
            "checkout-flows F-05",
            "content-seo F-01",
            "content-seo F-02",
            "content-seo F-03",
            "content-seo F-04",
            "content-seo F-05",
            "content-seo F-06",
            "content-seo F-07",
            "content-seo F-08",
            "performance-ux F-01",
            "performance-ux F-02",
            "performance-ux F-04",
            "performance-ux F-05",
            "performance-ux F-06",
            "post-purchase F-04",
            "post-purchase F-05",
            "pricing F-01",
            "pricing F-02",
            "pricing F-03",
            "pricing F-06",
            "product-media F-04",
            "product-media F-06",
            "product-media F-07",
            "trust-credibility F-02",
            "trust-credibility F-07",
            "trust-credibility F-08",
            "trust-credibility F-09",
            "visual-cta F-01",
            "visual-cta F-04",
            "visual-cta F-05",
            "visual-cta F-06",
        ],
        "severity_manifest": [
            "category-navigation F-01",
            "category-navigation F-02",
            "checkout-flows F-01",
            "checkout-flows F-02",
            "checkout-flows F-03",
            "content-seo F-01",
            "content-seo F-02",
            "performance-ux F-01",
            "performance-ux F-02",
            "performance-ux F-03",
            "post-purchase F-01",
            "pricing F-01",
            "pricing F-02",
            "product-media F-01",
            "product-media F-02",
            "trust-credibility F-01",
            "trust-credibility F-02",
            "trust-credibility F-03",
            "visual-cta F-01",
            "visual-cta F-02",
            "visual-cta F-03",
            "category-navigation F-03",
            "category-navigation F-04",
            "category-navigation F-05",
            "content-seo F-03",
            "content-seo F-04",
            "content-seo F-05",
            "performance-ux F-04",
            "performance-ux F-05",
            "post-purchase F-02",
            "post-purchase F-03",
            "pricing F-04",
            "pricing F-05",
            "product-media F-03",
            "product-media F-04",
            "product-media F-05",
            "product-media F-06",
            "trust-credibility F-04",
            "trust-credibility F-05",
            "trust-credibility F-06",
            "visual-cta F-04",
            "visual-cta F-05",
            "audience F-01",
            "pricing F-03",
            "performance-ux F-06",
            "audience F-02",
            "category-navigation F-06",
            "category-navigation F-07",
            "checkout-flows F-04",
            "checkout-flows F-05",
            "content-seo F-06",
            "content-seo F-07",
            "content-seo F-08",
            "post-purchase F-04",
            "post-purchase F-05",
            "pricing F-06",
            "product-media F-07",
            "trust-credibility F-07",
            "trust-credibility F-08",
            "trust-credibility F-09",
            "visual-cta F-06",
        ],
        "scope_page_synchronized_refs": [],
        "humanized_findings": [
            {
                "f_ref": "audience F-01",
                "plain_english_summary": (
                    "The mobile page shows '(15 reviews)' next to the star rating with no framing that ties "
                    "those reviewers to Spyder F3 or RT owners. A buyer worried about whether the product "
                    "fits their specific bike sees a number, not validation from people in the same "
                    "situation."
                ),
                "plain_english_action": (
                    "Replace '(15 reviews)' with '15 verified buyers' or '15 Spyder owners' once review "
                    "metadata is available, so the count anchors to the audience."
                ),
            },
            {
                "f_ref": "audience F-02",
                "plain_english_summary": (
                    "The desktop site has a vehicle nav row (Slingshot, Spyder, Ryker, Canyon) at the top "
                    "of every page, but on this Spyder product page the SPYDER tab gets no highlight. "
                    "Visitors arriving from search have no visual confirmation they are in the right "
                    "vehicle section of the store."
                ),
                "plain_english_action": (
                    "Apply an active-state highlight to the SPYDER tab on Spyder pages — a CSS-only change "
                    "that takes a few minutes."
                ),
            },
            {
                "f_ref": "category-navigation F-01",
                "plain_english_summary": (
                    "On desktop the breadcrumb reads 'Home > [product name]' and skips every category "
                    "level in between. Search visitors landing here have no one-click path to browse other "
                    "Spyder accessories or related handlebar parts, and Google snippets show a raw URL "
                    "instead of a category trail."
                ),
                "plain_english_action": (
                    "Expand the breadcrumb to 'Home > Spyder > Handlebar Accessories > Product Name' with "
                    "each intermediate level linked to its category page."
                ),
            },
            {
                "f_ref": "category-navigation F-02",
                "plain_english_summary": (
                    "The product page has no BreadcrumbList structured data. Google's search snippets "
                    "render the bare URL instead of a readable category path, and two SearchPilot "
                    "controlled tests put the cost at roughly 5–7% of organic traffic. On a search-driven "
                    "specialty store, that compounds across every product page."
                ),
                "plain_english_action": (
                    "Add a BreadcrumbList JSON-LD block to the page head that mirrors the visible "
                    "breadcrumb levels."
                ),
            },
            {
                "f_ref": "category-navigation F-03",
                "plain_english_summary": (
                    "Desktop visitors who arrive from a filtered category list (say, all 2024 Spyder F3 "
                    "handlebar parts) and click through to this product have no 'Back to results' link. "
                    "Tapping the breadcrumb 'Home' wipes their filters; many shoppers abandon rather than "
                    "re-applying them from scratch."
                ),
                "plain_english_action": (
                    "Add a 'Back to [Category] (N results)' link above the breadcrumb when the visitor "
                    "arrived from a filtered list."
                ),
            },
            {
                "f_ref": "category-navigation F-04",
                "plain_english_summary": (
                    "Same gap as desktop, on mobile: the breadcrumb jumps straight from Home to the "
                    "product, skipping the vehicle category and any handlebar-accessories subcategory. "
                    "Cross-sell navigation for organic-search visitors is effectively absent."
                ),
                "plain_english_action": (
                    "Add the Spyder and Handlebar Accessories levels to the visible breadcrumb on mobile "
                    "as well."
                ),
            },
            {
                "f_ref": "category-navigation F-05",
                "plain_english_summary": (
                    "The mobile breadcrumb has no 'Back to results' shortcut. A shopper who filtered to "
                    "their bike's compatible accessories and tapped through to this page cannot return to "
                    "those filters with a single tap."
                ),
                "plain_english_action": (
                    "Add a referrer-aware 'Back to [Category]' link above the breadcrumb that preserves "
                    "filter and scroll state."
                ),
            },
            {
                "f_ref": "category-navigation F-06",
                "plain_english_summary": (
                    "The desktop vehicle navigation row (Slingshot, Spyder, Ryker, Canyon, Riding Gear) "
                    "sits above the fold on every page — exactly the right position for a fitment-first "
                    "store. This is working well and worth preserving."
                ),
                "plain_english_action": (
                    "No change needed. If the catalog adds new vehicle lines, keep the row at this "
                    "position and give the active model a distinct visual state."
                ),
            },
            {
                "f_ref": "category-navigation F-07",
                "plain_english_summary": (
                    "The mobile vehicle category strip is also above the fold. New visitors instantly see "
                    "that the store is organized by vehicle model — the right structural choice for an "
                    "audience that filters by their bike first."
                ),
                "plain_english_action": (
                    "No change needed. Consider adding a 'Shop more Spyder accessories' anchor inside the "
                    "product description if analytics show meaningful taps."
                ),
            },
            {
                "f_ref": "checkout-flows F-01",
                "plain_english_summary": (
                    "The desktop product page never shows the shipping cost. The schema records a $7.99 "
                    "shipping rate, but the visitor only learns about it after starting checkout — when "
                    "Baymard data shows surprise shipping is the single largest abandonment driver."
                ),
                "plain_english_action": (
                    "Add a shipping line directly under the price: 'Free shipping over $75 · $7.99 under "
                    "threshold.'"
                ),
            },
            {
                "f_ref": "checkout-flows F-02",
                "plain_english_summary": (
                    "On mobile, the page has only the standard Add to Cart button — no Apple Pay, Google "
                    "Pay, or Shop Pay tap-to-buy options. The footer shows those payment logos but they "
                    "are static images, not actionable buttons. Mobile shoppers with wallets configured "
                    "have to type address and card details manually for a $59.95 purchase."
                ),
                "plain_english_action": (
                    "Add Apple Pay and Google Pay express buttons directly under the Add to Cart button."
                ),
            },
            {
                "f_ref": "checkout-flows F-03",
                "plain_english_summary": (
                    "The desktop product page is missing the same one-click wallet buttons. Apple Pay and "
                    "Google Pay logos are in the footer but never shown as actionable buttons in the "
                    "purchase area."
                ),
                "plain_english_action": (
                    "Add Apple Pay and Google Pay express checkout buttons in the buy box, labelled 'Or "
                    "pay with' to distinguish them from the main Add to Cart action."
                ),
            },
            {
                "f_ref": "checkout-flows F-04",
                "plain_english_summary": (
                    "The PayPal Pay Later widget renders directly under the price on desktop, showing "
                    "'4 interest-free payments of $14.99.' That is exactly where installment messaging "
                    "should sit — right at the moment a buyer is evaluating affordability."
                ),
                "plain_english_action": (
                    "No change needed. If Affirm is also live for this SKU, surface its monthly-payment "
                    "estimate alongside the PayPal widget."
                ),
            },
            {
                "f_ref": "checkout-flows F-05",
                "plain_english_summary": (
                    "Mobile carries the same PayPal Pay Later message above the Add to Cart button. The "
                    "installment framing reduces sticker shock at the price decision point — keep this "
                    "implementation."
                ),
                "plain_english_action": (
                    "No change needed for this widget. Add an Affirm monthly-payment estimate if Affirm "
                    "is enabled at checkout."
                ),
            },
            {
                "f_ref": "content-seo F-01",
                "plain_english_summary": (
                    "The mobile page title says 'End Weights' but the H1 says 'End Caps,' so search "
                    "engines see two different product nouns describing the same item. Google rewrites the "
                    "title on roughly 76% of pages with this kind of mismatch — the store loses control of "
                    "how its listing appears in search."
                ),
                "plain_english_action": (
                    "Pick whichever term — 'End Weights' or 'End Caps' — actual buyers search for, and use "
                    "it consistently across the title, H1, and meta description."
                ),
            },
            {
                "f_ref": "content-seo F-02",
                "plain_english_summary": (
                    "The desktop page's structured product data has no GTIN or MPN identifier. Google "
                    "Shopping and AI shopping agents (ChatGPT, Perplexity) use these IDs to match a "
                    "product across data sources. Without them, this SKU effectively does not exist in "
                    "cross-retailer comparisons."
                ),
                "plain_english_action": (
                    "Add the existing part number SM-22490 to the product schema as the MPN field."
                ),
            },
            {
                "f_ref": "content-seo F-03",
                "plain_english_summary": (
                    "The product schema's price-valid-until date is hard-coded to today's audit date. "
                    "Google treats expired validity dates as stale pricing and removes the product from "
                    "Shopping rich results."
                ),
                "plain_english_action": (
                    "Replace the static date with a server-side rolling value — typically today plus 365 "
                    "days — that updates automatically."
                ),
            },
            {
                "f_ref": "content-seo F-04",
                "plain_english_summary": (
                    "The desktop product schema does not declare a return policy. AI shopping agents and "
                    "Google compare merchants on return policy terms when buyers are picking between "
                    "vendors; without this data, the store loses that comparison silently."
                ),
                "plain_english_action": (
                    "Add a MerchantReturnPolicy block to the product schema declaring the actual 90-day "
                    "return window and method."
                ),
            },
            {
                "f_ref": "content-seo F-05",
                "plain_english_summary": (
                    "The mobile page schema includes an MPN but no GTIN. Without a GTIN (UPC/EAN), AI "
                    "commerce agents cannot reliably match this product across data sources for "
                    "cross-retailer comparisons."
                ),
                "plain_english_action": (
                    "If EvolutionR has a UPC assigned to this SKU, add it as a `gtin12` field in the "
                    "product schema. If no manufacturer GTIN exists, the current MPN+brand fallback is "
                    "acceptable."
                ),
            },
            {
                "f_ref": "content-seo F-06",
                "plain_english_summary": (
                    "The mobile page's canonical tag points to the clean product URL with no collection "
                    "prefix. This consolidates ranking signals correctly and prevents Shopify-style dual "
                    "URL paths from splitting link equity."
                ),
                "plain_english_action": (
                    "No change needed. Re-verify after any theme update."
                ),
            },
            {
                "f_ref": "content-seo F-07",
                "plain_english_summary": (
                    "Same on desktop: the canonical tag self-references the clean URL correctly."
                ),
                "plain_english_action": (
                    "No change needed. Re-verify the canonical output after any theme update."
                ),
            },
            {
                "f_ref": "content-seo F-08",
                "plain_english_summary": (
                    "The product description leads with the rider outcome — vibration reduction and "
                    "comfort — before listing material, weight, and install method. That benefit-first "
                    "structure is exactly what reduces 'I cannot tell what this does for me' purchase "
                    "abandonment."
                ),
                "plain_english_action": (
                    "No change needed. Consider extending with a short Q&A section covering common "
                    "fitment questions."
                ),
            },
            {
                "f_ref": "performance-ux F-01",
                "plain_english_summary": (
                    "The hero product image on desktop has no priority hint, and the page head loads nine "
                    "stylesheets before the browser starts fetching it. The biggest visible image — the "
                    "metric Google measures for ranking — is queued behind every CSS file."
                ),
                "plain_english_action": (
                    "Add `fetchpriority='high'` to the hero image and a matching preload tag in the page "
                    "head."
                ),
            },
            {
                "f_ref": "performance-ux F-02",
                "plain_english_summary": (
                    "Same gap on mobile: the hero product image has no preload and no priority hint. On a "
                    "4G connection that adds 300–600ms to the time before the image starts downloading, "
                    "directly hurting Largest Contentful Paint."
                ),
                "plain_english_action": (
                    "Add `fetchpriority='high'` and a preload tag for the mobile hero image as well."
                ),
            },
            {
                "f_ref": "performance-ux F-03",
                "plain_english_summary": (
                    "On mobile, once the visitor swipes past the gallery, the Add to Cart button is gone "
                    "and there is nothing pinned to the bottom of the screen. They have to scroll all the "
                    "way back up to buy."
                ),
                "plain_english_action": (
                    "Add a sticky bottom bar with product name, price, and a full-width Add to Cart "
                    "button. Trigger it via IntersectionObserver when the inline button leaves the "
                    "viewport."
                ),
            },
            {
                "f_ref": "performance-ux F-04",
                "plain_english_summary": (
                    "The Slingmods logo image has no width or height attributes. The browser cannot "
                    "reserve space for it, so when it loads the entire header — phone number, navigation, "
                    "vehicle tabs — jumps down. That visible shift drags the Cumulative Layout Shift "
                    "score below Google's 'Good' threshold."
                ),
                "plain_english_action": (
                    "Add `width` and `height` attributes to the logo image element matching its rendered "
                    "size."
                ),
            },
            {
                "f_ref": "performance-ux F-05",
                "plain_english_summary": (
                    "The mobile page loads two external CSS files — Google Fonts and Adobe TypeKit — "
                    "synchronously in the page head. The browser cannot draw anything until both finish "
                    "downloading and parsing, which adds a full network round-trip to first paint."
                ),
                "plain_english_action": (
                    "Load Google Fonts with `display=swap` and the preload-then-stylesheet pattern. "
                    "Switch the TypeKit embed to its async JavaScript variant."
                ),
            },
            {
                "f_ref": "performance-ux F-06",
                "plain_english_summary": (
                    "The brainyfilter.css stylesheet is included twice in the desktop page head as "
                    "back-to-back identical link tags. The browser makes two separate render-blocking "
                    "requests for the same file on every page load."
                ),
                "plain_english_action": (
                    "Find the duplicate include and remove one of the two entries."
                ),
            },
            {
                "f_ref": "post-purchase F-01",
                "plain_english_summary": (
                    "On mobile the only mention of the Reward Points program is a plain text link buried "
                    "in the footer alongside Privacy Policy and CARB Policy. Shoppers have no idea the "
                    "program exists, what they earn, or how to enroll — so a known retention lever is "
                    "effectively invisible."
                ),
                "plain_english_action": (
                    "Add a one-line callout under the price: 'Earn 60 points on this order toward your "
                    "next reward.'"
                ),
            },
            {
                "f_ref": "post-purchase F-02",
                "plain_english_summary": (
                    "There is no referral program anywhere on the desktop page or its footer. Slingmods' "
                    "audience is community-driven — Spyder and Slingshot owners share modifications "
                    "constantly — and that organic advocacy is going untracked and unrewarded."
                ),
                "plain_english_action": (
                    "Add a 'Refer a Friend — Give $15, Get $15' entry in the Extras footer column and a "
                    "post-purchase referral block on the order confirmation page."
                ),
            },
            {
                "f_ref": "post-purchase F-03",
                "plain_english_summary": (
                    "Same gap on mobile: no referral program surface anywhere on the page. The 72-hour "
                    "post-purchase window where referral willingness peaks closes without a prompt."
                ),
                "plain_english_action": (
                    "Add a referral entry point to the mobile footer and a referral block to the order "
                    "confirmation page."
                ),
            },
            {
                "f_ref": "post-purchase F-04",
                "plain_english_summary": (
                    "On desktop, the Reward Points footer link is a plain utility link with no earning "
                    "rate or value framing. Visitors with purchase intent see no signal that buying this "
                    "item earns them progress toward a reward."
                ),
                "plain_english_action": (
                    "Update the footer link to 'Reward Points — Earn on every order' and add an "
                    "'Earn 60 points on this purchase' callout under the price for logged-out visitors."
                ),
            },
            {
                "f_ref": "post-purchase F-05",
                "plain_english_summary": (
                    "The footer's My Account column has Track My Order, Order History, and account "
                    "self-service links — the basic post-purchase navigation customers need to find "
                    "without contacting support."
                ),
                "plain_english_action": (
                    "No change needed. Surface the same links more prominently on order confirmation "
                    "pages and in transactional emails."
                ),
            },
            {
                "f_ref": "pricing F-01",
                "plain_english_summary": (
                    "On mobile the price displays as '$59.95' with no MSRP strikethrough or compare-at "
                    "reference. Buyers have no anchor for whether $59.95 is a strong price for weighted "
                    "stainless-steel bar ends, so it defaults to feeling expensive against zero."
                ),
                "plain_english_action": (
                    "Add a manufacturer MSRP strikethrough above the price (e.g., 'MSRP $79.95') with a "
                    "'You save $20' line in a contrasting color."
                ),
            },
            {
                "f_ref": "pricing F-02",
                "plain_english_summary": (
                    "Desktop has the same gap: $59.95 stands alone with no reference price. A shopper "
                    "evaluating this against alternatives has no internal benchmark, so the price reads "
                    "as a plain number rather than a deal."
                ),
                "plain_english_action": (
                    "Display the manufacturer MSRP as a strikethrough above the live price, with the "
                    "savings amount and percentage stated explicitly."
                ),
            },
            {
                "f_ref": "pricing F-03",
                "plain_english_summary": (
                    "On mobile, the price block has no shipping line nearby. The free-shipping disclosure "
                    "lives in a footer footnote 1,600px below the purchase decision — far too late to "
                    "factor into the shopper's mental math."
                ),
                "plain_english_action": (
                    "Add a 'Free shipping over $75' line directly under the price."
                ),
            },
            {
                "f_ref": "pricing F-04",
                "plain_english_summary": (
                    "Free shipping kicks in at $75 but this product is $59.95 — a $15.05 gap. The page "
                    "shows neither the gap nor a recommended add-on to close it. Most visitors check out "
                    "rather than basket-build because the threshold is invisible at the price decision "
                    "point."
                ),
                "plain_english_action": (
                    "Add a goal-proximity message: 'Add $15.05 more for FREE shipping' with a "
                    "'You might also need' widget showing 1–3 small accessories priced $15–$25."
                ),
            },
            {
                "f_ref": "pricing F-05",
                "plain_english_summary": (
                    "The desktop price block carries the PayPal Pay Later widget but no Affirm option, "
                    "even though Affirm is in the footer payment row and has a dedicated 'Affirm Monthly "
                    "Payments' footer link. Shoppers who specifically prefer Affirm see only PayPal."
                ),
                "plain_english_action": (
                    "Add the Affirm inline widget to the price block alongside or below PayPal Pay Later."
                ),
            },
            {
                "f_ref": "pricing F-06",
                "plain_english_summary": (
                    "The price uses a .95 ending at $59.95, which crosses the $60 left-digit boundary. "
                    "That is the maximum-impact placement for the charm-pricing effect — keep it."
                ),
                "plain_english_action": (
                    "No change needed. Maintain the .95 ending at left-digit boundaries."
                ),
            },
            {
                "f_ref": "product-media F-01",
                "plain_english_summary": (
                    "On mobile, the product video sits below the Add to Cart button, below the spec "
                    "table, and outside the gallery entirely. By the time most shoppers reach it, they "
                    "have already passed the conversion decision point — so the video does almost no "
                    "purchase-intent work."
                ),
                "plain_english_action": (
                    "Move the video into the gallery as the second item, right after the hero shot, with "
                    "a play-button overlay so a single swipe surfaces it."
                ),
            },
            {
                "f_ref": "product-media F-02",
                "plain_english_summary": (
                    "Desktop has the same problem: the YouTube video sits in a side column, separate from "
                    "the gallery thumbnail strip. Visitors scanning the gallery never encounter it."
                ),
                "plain_english_action": (
                    "Inject the video as gallery position 2 with a play-button thumbnail so it shows up "
                    "alongside the photos."
                ),
            },
            {
                "f_ref": "product-media F-03",
                "plain_english_summary": (
                    "Every gallery shot is a studio image of the bar-end against a clean background. "
                    "Nothing shows the product held in a hand, mounted on an actual handlebar, or sized "
                    "next to a familiar object. New buyers cannot judge whether the cap is golf-ball-sized "
                    "or soda-can-sized."
                ),
                "plain_english_action": (
                    "Add at least one in-scale image — bar-end held in a gloved hand, or mounted on an "
                    "actual Spyder handlebar with the grip visible for context."
                ),
            },
            {
                "f_ref": "product-media F-04",
                "plain_english_summary": (
                    "The mobile thumbnail strip shows all seven thumbnails fully visible in two complete "
                    "rows. There is no partial peek of an off-screen image — so visitors get no signal to "
                    "swipe and may miss installed-on-bike shots that would close the deal."
                ),
                "plain_english_action": (
                    "Crop the rightmost thumbnail at 40–50% width so a partial peek signals more images "
                    "exist. Pair with CSS scroll-snap for a clean swipe."
                ),
            },
            {
                "f_ref": "product-media F-05",
                "plain_english_summary": (
                    "The product video is a YouTube embed. After playback ends, YouTube's recommended-"
                    "videos grid often surfaces competitor products — sending the buyer who just watched "
                    "your video straight to a competing seller's listing."
                ),
                "plain_english_action": (
                    "Migrate the video to a self-hosted video CDN like Mux, Cloudflare Stream, or Vimeo "
                    "Pro. As an interim, use the YouTube facade pattern (static thumbnail that loads the "
                    "player only on tap)."
                ),
            },
            {
                "f_ref": "product-media F-06",
                "plain_english_summary": (
                    "On desktop, the largest above-fold image is the hero product shot, but it is loaded "
                    "without a priority hint — Google's recommended attribute for the page's biggest "
                    "image. That hurts the Core Web Vitals LCP score."
                ),
                "plain_english_action": (
                    "Add `fetchpriority='high'` and explicit `width`/`height` attributes to the hero "
                    "image element."
                ),
            },
            {
                "f_ref": "product-media F-07",
                "plain_english_summary": (
                    "On mobile the gallery covers the four image types Baymard recommends for hardware "
                    "accessories: hero packshot, close-up detail, and multiple installed-on-bike shots. "
                    "Seven images total — well above the minimum for this category."
                ),
                "plain_english_action": (
                    "No change needed. Adding an in-scale next-to-stock-OEM shot would be a useful "
                    "enhancement."
                ),
            },
            {
                "f_ref": "trust-credibility F-01",
                "plain_english_summary": (
                    "Desktop shows a perfect 5.0 rating across 15 reviews with no star distribution "
                    "breakdown. Northwestern's Spiegel research found purchase likelihood actually "
                    "decreases as ratings approach 5.0 because shoppers suspect curation. With no "
                    "distribution to verify against, the perfect score reads suspicious instead of "
                    "reassuring."
                ),
                "plain_english_action": (
                    "Display a star-distribution bar (% of 5-star, 4-star, 3-star, etc.) under the "
                    "aggregate rating."
                ),
            },
            {
                "f_ref": "trust-credibility F-02",
                "plain_english_summary": (
                    "Same problem on mobile: 5.0 across 15 reviews with no breakdown. The unblemished "
                    "score triggers the same skepticism."
                ),
                "plain_english_action": (
                    "Add the star-distribution bar on mobile too. If the review collection flow filters "
                    "by satisfaction before sending requests, send to all confirmed purchasers instead — "
                    "FTC 16 CFR §465.7 also requires this."
                ),
            },
            {
                "f_ref": "trust-credibility F-03",
                "plain_english_summary": (
                    "Desktop has trust badges (Visa, PayPal, Amex, Apple Pay, etc.) but they live only in "
                    "the footer. The Add to Cart zone has no security or guarantee badges. Baymard's "
                    "research shows trust signals only register as relevant when they sit beside the "
                    "purchase action, not 1,500px away."
                ),
                "plain_english_action": (
                    "Add a compact trust-badge row directly under the Add to Cart button — three badges "
                    "max (PayPal Verified, money-back guarantee, free-shipping confirmation)."
                ),
            },
            {
                "f_ref": "trust-credibility F-04",
                "plain_english_summary": (
                    "All 15 reviews are loaded only after the visitor taps the Reviews tab. The actual "
                    "review text never appears in the initial page HTML, so search engines cannot index "
                    "those keyword-rich first-hand accounts."
                ),
                "plain_english_action": (
                    "Render the first 3–5 reviews server-side under the tab bar so review text is in the "
                    "page source from the start, while keeping the tab UI for the rest."
                ),
            },
            {
                "f_ref": "trust-credibility F-05",
                "plain_english_summary": (
                    "The Photos tab shows 1 photo against 15 reviews — about 7%. For a vehicle accessory "
                    "where buyers are asking 'how will this look on my bike,' a single install photo is "
                    "doing the work that a small UGC gallery should be doing."
                ),
                "plain_english_action": (
                    "Add an explicit photo prompt to the post-purchase review request email and surface "
                    "the customer install photo in the main image gallery as the final thumbnail."
                ),
            },
            {
                "f_ref": "trust-credibility F-06",
                "plain_english_summary": (
                    "Above-fold on desktop, the rating shows stars and '(15 reviews)' with no 'Verified "
                    "Buyers' label. Spiegel research attributes a 15% purchase-likelihood lift to that "
                    "single signal — and it is missing right where most shoppers form their trust "
                    "judgement."
                ),
                "plain_english_action": (
                    "Add a 'Verified Buyers' shield or label adjacent to the review count if the review "
                    "platform records purchase verification."
                ),
            },
            {
                "f_ref": "trust-credibility F-07",
                "plain_english_summary": (
                    "The desktop header shows 'Call Us: (800)211-1396 | Message Us' above the navigation "
                    "bar. A real, callable phone number on a specialty parts site is a meaningful trust "
                    "signal for buyers with fitment questions."
                ),
                "plain_english_action": (
                    "No change needed. Keep the contact link in the same prominent above-fold position."
                ),
            },
            {
                "f_ref": "trust-credibility F-08",
                "plain_english_summary": (
                    "The mobile footer carries the basics that establish Slingmods is a real business: "
                    "physical address, toll-free phone, recognizable payment logos, and a 'not affiliated "
                    "with Polaris/BRP' disclaimer. These are the foundational E-E-A-T signals."
                ),
                "plain_english_action": (
                    "No change needed. A direct 'Returns' or 'Shipping Policy' link in the Information "
                    "column would surface those terms one click sooner."
                ),
            },
            {
                "f_ref": "trust-credibility F-09",
                "plain_english_summary": (
                    "The Can-Am Spyder Fitment Guide table sits in the right column above the fold on "
                    "desktop, listing 2024–2026 model years for F3-L, F3-S, F3-T, RT, and RT-L. Showing "
                    "exact model codes — instead of a generic 'Compatible with Spyder' line — is the "
                    "single most reassuring trust signal on the page for fitment-anxious buyers."
                ),
                "plain_english_action": (
                    "No change needed. Maintain and expand this grid as the vehicle lineup evolves."
                ),
            },
            {
                "f_ref": "visual-cta F-01",
                "plain_english_summary": (
                    "The mobile Add to Cart button uses solid black — the same color as the dark header "
                    "bar at the top of the screen. A shopper scanning the page perceives two dark bands "
                    "without a clear pop-color signal that the button is the priority action."
                ),
                "plain_english_action": (
                    "Switch the Add to Cart fill to a saturated brand color (red or orange) so it stands "
                    "apart from the header. Keep secondary buttons in the existing dark tone."
                ),
            },
            {
                "f_ref": "visual-cta F-02",
                "plain_english_summary": (
                    "On the 1,661px desktop page, once the visitor scrolls past about 520px the Add to "
                    "Cart button is gone — and nothing replaces it. Visitors reading the description and "
                    "fitment guide have no visible way to buy without scrolling all the way back up."
                ),
                "plain_english_action": (
                    "Show a sticky top or bottom bar with product name, price, and Add to Cart once the "
                    "primary button scrolls out of view."
                ),
            },
            {
                "f_ref": "visual-cta F-03",
                "plain_english_summary": (
                    "On mobile the page is 3,297px tall and the only Add to Cart button sits around "
                    "y=860 — gone after one swipe. There is no sticky bottom bar, so the most engaged "
                    "visitors (the ones reading the full description and reviews) lose access to the "
                    "purchase action exactly when they are ready to buy."
                ),
                "plain_english_action": (
                    "Add a 56–64px sticky bottom bar that appears once the inline button scrolls off "
                    "screen, showing product name, price, and a full-width Add to Cart."
                ),
            },
            {
                "f_ref": "visual-cta F-04",
                "plain_english_summary": (
                    "The mobile Add to Cart button stands alone with only an Add to Wishlist link below "
                    "it. No reassurance — no 'Free shipping,' no '90-day returns,' no fitment guarantee — "
                    "appears within reading distance of the button at the moment of commitment."
                ),
                "plain_english_action": (
                    "Add a single line of microcopy under the Add to Cart button: "
                    "'Free shipping over $75 · 90-day returns.'"
                ),
            },
            {
                "f_ref": "visual-cta F-05",
                "plain_english_summary": (
                    "The H1 product title is 104 characters and wraps to five full lines on mobile, "
                    "consuming most of the second viewport. The price ($59.95) ends up below the 844px "
                    "fold on page load — so buyers cannot see the price without scrolling."
                ),
                "plain_english_action": (
                    "Trim the visible H1 to roughly 60 characters with the model qualifier '(Pair) "
                    "(2024+)' demoted to a smaller subtitle line. SEO content stays intact in the page "
                    "source."
                ),
            },
            {
                "f_ref": "visual-cta F-06",
                "plain_english_summary": (
                    "The mobile Add to Cart button is full-width and tall enough to satisfy Apple's 44pt "
                    "and Google's 48dp touch-target minimums. It also includes a cart icon and clear "
                    "label — correct mobile CTA mechanics."
                ),
                "plain_english_action": (
                    "No change needed for sizing. Color contrast is the separate issue covered above."
                ),
            },
            {
                "f_ref": "ethics F-01",
                "plain_english_summary": (
                    "No countdown timers, sale-end clocks, or fabricated urgency language on the page. "
                    "Both device captures show the price as a straight $59.95 with no artificial time "
                    "pressure."
                ),
                "plain_english_action": (
                    "Maintain this practice. Any future genuine sale countdown should be tied to a real "
                    "server-side end timestamp, not a client-side resetting timer."
                ),
            },
            {
                "f_ref": "ethics F-02",
                "plain_english_summary": (
                    "The schema's aggregate rating (5.0 across 15 reviews) matches the on-page review "
                    "count exactly. No inflation, no misrepresentation — schema and visible content "
                    "agree."
                ),
                "plain_english_action": (
                    "Maintain consistency as review count grows. If reviews paginate, ensure the schema "
                    "reflects the total across all pages."
                ),
            },
            {
                "f_ref": "ethics F-03",
                "plain_english_summary": (
                    "The Privacy Policy and Terms & Conditions links point to canonical first-party URLs "
                    "on slingmods.com — not a staging domain or third-party host. The disclosure chain "
                    "is intact."
                ),
                "plain_english_action": (
                    "Maintain canonical first-party policy URLs through any future platform migrations."
                ),
            },
            {
                "f_ref": "ethics F-04",
                "plain_english_summary": (
                    "The product description tab includes the California Prop 65 motor-vehicle-parts "
                    "safe-harbor warning and links to the official p65warnings.ca.gov URL. For a "
                    "stainless-steel automotive part, this disclosure is required and correctly "
                    "implemented."
                ),
                "plain_english_action": (
                    "Maintain the current disclosure format. Verify safe-harbor language if the catalog "
                    "expands to other chemical categories."
                ),
            },
            {
                "f_ref": "ethics F-05",
                "plain_english_summary": (
                    "A Termly cookie consent manager is deployed and a floating preferences button "
                    "remains visible after dismissal so visitors can revisit their choices. The site is "
                    "US-targeted (no hreflang tags, US-only shipping language), so EU ePrivacy rules do "
                    "not directly apply."
                ),
                "plain_english_action": (
                    "If expanding to EU traffic, verify the Termly configuration provides an equally "
                    "prominent 'Reject All' button and that analytics scripts do not fire before consent."
                ),
            },
            {
                "f_ref": "ethics F-06",
                "plain_english_summary": (
                    "This is a one-time-purchase product with no subscription, no auto-renewal, no free "
                    "trial, and no negative-option enrollment patterns. The standard add-to-cart flow "
                    "carries no ROSCA exposure."
                ),
                "plain_english_action": (
                    "No action needed. If subscription products are introduced later, ROSCA requires "
                    "clear material-terms disclosure before billing-information collection."
                ),
            },
            {
                "f_ref": "ethics F-07",
                "plain_english_summary": (
                    "No hidden text, keyword-stuffed divs, or cloaking patterns detected. Meta keywords "
                    "are concise and non-repetitive; product description content is substantive and "
                    "human-readable."
                ),
                "plain_english_action": (
                    "No action needed. Maintain the current natural-density keyword usage."
                ),
            },
        ],
        "telemetry": {
            "scope_page_count": 39,
            "scope_device_desktop_count": 9,
            "scope_device_mobile_count": 11,
            "ethics_findings_count": 7,
            "baton_elements_kept_after_trim": 31,
            "dispatch_run": "run-02-retry",
        },
        "notes": [
            (
                "scope_page_synchronized_refs is empty by design: the canonical f_refs manifest groups "
                "every finding to a single device (devices_present length 1 across all 60 actionable "
                "f_refs and 7 ethics f_refs). Cross-device finding independence is the expected outcome "
                "for this engagement — desktop and mobile specialists surfaced different finding sets "
                "even where the underlying issue is server-side, which is the correct handling per the "
                "Phase F.checkpoint LOCKED rule."
            ),
            (
                "Schema-data inconsistency between device batons noted: the desktop baton schema_jsonld "
                "lacks both `mpn` and `MerchantReturnPolicy`, while the mobile baton schema_jsonld "
                "includes `mpn: 'canam-spyder-handlebar-end-weights-evolutionr'` and a complete "
                "`hasMerchantReturnPolicy` block. The desktop content-seo specialist findings (F-02 GTIN "
                "and MPN missing; F-04 MerchantReturnPolicy absent) are accurate against the desktop "
                "capture but may not reflect the production server response in real time. The mobile "
                "content-seo F-05 (no GTIN) is accurate against both captures."
            ),
        ],
    }
    atomic_write_json(OUT, payload)
    print(f"wrote: {OUT}")
    print(f"size: {OUT.stat().st_size} bytes")


if __name__ == "__main__":
    main()
