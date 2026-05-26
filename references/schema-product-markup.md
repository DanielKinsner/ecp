<!-- RESEARCH_DATE: 2026-04-21 (reconciled from run-A proposed + run-B proposed) -->
<!-- RECONCILER: Vera — 2026-04-22 -->
<!-- SOURCE_FILE: references/schema-product-markup.md (original research: 2026-04-02) -->
# Schema.org Product Markup & Agentic Commerce

**Research Date:** 2026-04-21 (reconciled audit revision of 2026-04-02 source)
**Total Findings:** 14 (was 13 — Finding 12 removed as duplicate of canonical-duplicate-content.md; Finding 14 added for FTC Fake Reviews Rule)
**Methodology:** Synthesis of Google Search Central official documentation (verified against live pages 2026-04-21), Google spokesperson statements (John Mueller, Martin Splitt), SearchPilot controlled split tests, OpenAI ChatGPT Shopping Research (launched Nov 24, 2025 — primary spec URL unverifiable as of 2026-04-21), and ecommerce platform behavior analysis. Evidence weighted by source authority and methodological rigor.

> **Cross-Reference:** See CRO references `ugc-integration.md` and `social-proof-patterns.md` for the consumer psychology behind reviews and ratings that schema markup surfaces in SERPs. See `ugc-reviews-seo.md` in this reference set for review-specific SEO implications. See `ethics-gate.md` Parts 2.2 (misleading structured data), 2.4 (fake reviews), and 7.4 (Lanham Act metadata scope) for FTC/Lanham compliance obligations on AggregateRating.

---

## Reconciliation Notes (2026-04-22)

**Run-A and Run-B were generally in agreement** on what needed fixing. Divergences resolved as follows:

- **F4 tier:** Both audits flagged that "not a ranking factor" does not appear verbatim in the current Google intro doc — it comes from Mueller public statements. B correctly downgrades to **Silver**; A kept Gold inconsistently. Silver adopted.
- **F6 required properties:** B correctly identifies the required triad as `applicableCountry` + `returnPolicyCategory` (Option A) OR `merchantReturnLink` (Option B). A's proposed missed `applicableCountry` from Option A. B's formulation confirmed against developers.google.com/search. B's version adopted.
- **F7 tier:** Both audits noted the "faster, less sophisticated Merchant Center crawler" is practitioner synthesis, not verbatim Google doc text. B downgrades to **Silver**; A kept Gold inconsistently. Silver adopted.
- **F8 tier:** Both audits note GTIN is "strongly recommended," not strictly required. B correctly downgrades to **Silver**. Adopted.
- **F10 retrospective citation:** B flags that SearchPilot's "Most Surprising Tests of 2025" ~20% figure refers to a DIFFERENT test (enriched content on nutrition pages), not the review schema test. This correction appears only in B and is important — the retrospective is removed as a primary citation for the ~20% claim.
- **F12:** B removes as duplicate of canonical-duplicate-content.md. Removal retained; stub placeholder kept for numbering continuity.
- **F13 tier:** A proposes Silver with Citation Status annotation; B proposes Bronze. The launch itself is confirmed by multiple tier-1 press sources (SiliconANGLE, Bloomberg, Retail Dive) — **Silver** is appropriate for the directional finding while field-level specifics remain Bronze pending primary re-host. A's Silver with citation annotation adopted.
- **F14 (FTC) and F15 (rich result revocability):** Both audits surface FTC material; B formalizes F14 as a standalone finding and adds F15. Both adopted.
- **Schema-type retirements (Nov 2025):** Run-B explicitly searched the Google blog 2025 archive and current search gallery and did NOT confirm the "7 retired schema types Nov 2025" claim. None of this file's recommended types are affected regardless. Not propagated.

---

## Summary

### Top 3 Most Impactful Findings

1. **Review schema alone produces ~20% organic traffic uplift** (Finding 10) — SearchPilot controlled test found review schema (without price) produced statistically significant ~20% organic traffic uplift. One of the highest-ROI schema implementations available.

2. **Merchant Center feed takes precedence over on-page schema** (Finding 3) — If Merchant Center feed shows a different price than on-page JSON-LD, the feed wins. Price mismatches between feed and schema cause rich result disapproval and stripped star ratings.

3. **AggregateRating schema is a live FTC liability surface** (Finding 14) — 16 CFR Part 465 (FTC Fake Reviews Rule, effective 2024-10-21) prohibits fake reviews, suppressing negative reviews, and material misrepresentations via aggregate ratings. Civil penalties up to $51,744 per violation. AggregateRating MUST reflect genuine, unsuppressed customer data.

---

## Coverage by Research Question

| Research Question | Findings | Evidence Quality |
|---|---|---|
| What schema format does Google prefer? | 1, 2 | Gold |
| Which data source wins when there are conflicts? | 3 | Gold |
| Does schema improve rankings directly? | 4 | Silver |
| How do I handle product variants? | 5 | Gold |
| Does return policy in schema matter? | 6 | Gold |
| Should schema be server-rendered? | 7 | Silver |
| Are product identifiers required? | 8 | Silver |
| Does price in rich results help or hurt? | 9 | Gold |
| What shipping schema options exist? | 11 | Silver |
| Do reviews in schema lift organic traffic? | 10 | Gold |
| How does schema serve AI/agentic commerce? | 13 | Silver |
| What are the FTC/Lanham legal risks of inflated ratings? | 14 (NEW) | Gold |
| Can rich result eligibility be revoked? | 15 (NEW) | Gold |

---

## Findings

### Finding 1: Two Markup Paths — Product Snippets vs. Merchant Listings
- **Source**: Google Search Central, "Product structured data" documentation (last updated 2025-12-10 UTC, verified 2026-04-21), https://developers.google.com/search/docs/appearance/structured-data/product.
- **Methodology**: Google's official specification — not a study but authoritative technical documentation describing Google's actual behavior and requirements.
- **Key Finding**: **Product Snippets** are for pages where users cannot directly purchase (editorial reviews, comparison articles). **Merchant Listings** are for pages where customers can actively purchase, and support additional properties: shipping, sizing, return policies, merchant-level data. Both use `@type: "Product"` but have different required and recommended properties.
- **E-Commerce Application**: Ecommerce product pages (PDPs) must use Merchant Listing markup. Editorial/review content about products uses Product Snippet markup. Never add `Offer` markup to editorial review pages where users cannot purchase — this misrepresents the page type.
- **Replication Status**: Google official specification — applies universally to all crawled content.
- **Boundary Conditions**: If a page is both an editorial review AND an ecommerce page (common for DTC brands that also publish reviews), use Merchant Listing with an editorial component. The presence of an `Offer` with price and `url` pointing to a cart/checkout path signals Merchant Listing intent.
- **Evidence Tier**: Gold — Google Search Central official documentation.
- **Audit Note (2026-04-21)**: Verified live against Google doc (last updated 2025-12-10 UTC). Content match confirmed. No changes.

---

### Finding 2: JSON-LD Is Google's Explicitly Preferred Schema Format
- **Source**: Google Search Central structured data documentation (verified 2026-04-21), https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data. Google's doc states: "Google recommends using JSON-LD for structured data if your site's setup allows it, as it's the easiest solution." The supported-formats table labels JSON-LD as "Recommended."
- **Methodology**: Google official documentation — authoritative specification.
- **Key Finding**: Google explicitly recommends JSON-LD over Microdata and RDFa. JSON-LD can be placed anywhere in HTML (typically `<head>` or before `</body>`), does not require modifying HTML structure, is easier to maintain, and is easier to generate server-side.
- **E-Commerce Application**: Always implement structured data as JSON-LD in a `<script type="application/ld+json">` block. Place in `<head>` for maximum parse reliability. Never mix JSON-LD and Microdata on the same page for the same entity — conflicting signals cause validation failures.
- **Replication Status**: Google's stated preference is consistent and unchanged since 2017.
- **Boundary Conditions**: Microdata still functions and Google will parse it. Legacy Microdata implementations don't need to be migrated immediately, but new implementations should use JSON-LD.
- **Evidence Tier**: Gold — Google official specification.
- **Audit Note (2026-04-21)**: Verified live. Prior version cited a "BrightonSEO 2025 ecommerce schema study (180 sites)" with a 60–73% JSON-LD adoption statistic — that study was not independently locatable in 2026-04-21 search. Statistic removed. Google's JSON-LD preference is independently Gold.

---

### Finding 3: Google Merchant Center Feed Takes Precedence Over On-Page Schema
- **Source**: Google Search Central, "Merchant Center and structured data" section (verified 2026-04-21), https://developers.google.com/search/docs/appearance/structured-data/product#merchant-center. Google Merchant Center Help documentation.
- **Methodology**: Google official documentation — describes the actual data source hierarchy Google uses when multiple data sources exist for the same product.
- **Key Finding**: Data source hierarchy: Product-level Merchant Center feed > Merchant Center Content API > on-page JSON-LD schema. If the Merchant Center feed shows price $99 and on-page schema shows $119, the feed wins in Google Shopping results. Price mismatches between Merchant Center and on-page schema cause rich result disapproval for the on-page version. Stars may be stripped from SERP appearance when data conflicts.
- **E-Commerce Application**: Always synchronize your Merchant Center feed and on-page schema from the same data source (your database/ERP). Automate both from a single truth. Any manual discrepancy creates rich result eligibility loss. Common failure mode: schema is updated manually but Merchant Center feed update is delayed.
- **Replication Status**: Google official documentation — applies universally. Merchant Center disapproval data confirms this in practice (visible in Merchant Center Diagnostics panel).
- **Boundary Conditions**: Applies only when a Merchant Center account is connected to the domain. Sites without a Merchant Center connection rely entirely on on-page schema. For sites with Merchant Center, on-page schema still matters for non-Shopping rich results (product rich snippets).
- **Evidence Tier**: Gold — Google Search Central official documentation.
- **Audit Note (2026-04-21)**: Verified live. No changes.

---

### Finding 4: Schema Is NOT a Direct Ranking Factor — CTR Effect Is Indirect
- **Source**: John Mueller (Google), multiple statements via Google Webmaster Central office hours and Twitter/X, 2019–2024. Google Search Central `intro-structured-data` documentation (verified 2026-04-21) does NOT contain the explicit written statement "Structured data is not a ranking factor" — this framing originates from Mueller's public statements, not the current written documentation. https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data https://www.youtube.com/@GoogleSearchCentral
- **Methodology**: Google spokesperson statements — authoritative but not in written documentation form.
- **Key Finding**: Schema markup does not directly improve rankings. The indirect path: schema → rich results → higher CTR → potentially better engagement signals → possible ranking reinforcement. John Mueller: "We don't use structured data for ranking in the sense that 'if you have structured data, you rank higher.'" Rich results are not guaranteed even with perfect schema.
- **E-Commerce Application**: Implement schema for CTR and discoverability benefits, not as a ranking signal. Do not deprioritize content quality in favor of schema optimization. Schema cannot compensate for thin content, low authority, or poor relevance.
- **Replication Status**: Consistent across Mueller/Illyes/Splitt statements over 5+ years.
- **Boundary Conditions**: For Google Shopping specifically, schema (or Merchant Center feed) is required for eligibility — no schema = no Shopping appearances. This is an eligibility gate, not a ranking signal.
- **Evidence Tier**: Silver — multiple Google spokesperson statements consistent over years; the "not a ranking factor" framing is not present in current written Google documentation. Prior Gold tier was overstated.
- **Audit Note (2026-04-21)**: Downgraded from Gold to Silver. The claim is well-supported by public Google spokesperson statements but is not explicitly present in the current live `intro-structured-data` doc text. Honest tier for this sourcing structure is Silver.

---

### Finding 5: ProductGroup with hasVariant for Multi-Variant Products
- **Source**: Google Search Central, "Product variants structured data" (last updated 2025-12-10, verified 2026-04-21), https://developers.google.com/search/docs/appearance/structured-data/product-variants. Shopify native ProductGroup support (confirmed in Shopify platform release notes).
- **Methodology**: Google official specification — describes the required and recommended schema structure for variant products.
- **Key Finding**: Multi-variant products (different colors, sizes, materials) should use `@type: "ProductGroup"` with `hasVariant` (array of Product objects). **Per current Google doc, the only strictly required property at the ProductGroup level is `name`.** Strongly recommended: `hasVariant`, `variesBy`, `productGroupID`, `aggregateRating`, `brand`, `description`, `url`. Prior version of this file listed hasVariant, variesBy, and productGroupID as "required" — this was incorrect per current spec. All are strongly recommended and functionally necessary for the variant pattern to produce rich results, but Google's spec marks only `name` as required.
- **E-Commerce Application**:
```json
{
  "@context": "https://schema.org",
  "@type": "ProductGroup",
  "name": "Carbon Fiber Hood - 2024 GR Supra",
  "productGroupID": "CF-HOOD-SUPRA-24",
  "variesBy": ["https://schema.org/color", "https://schema.org/material"],
  "hasVariant": [
    {
      "@type": "Product",
      "name": "Carbon Fiber Hood - Gloss Finish",
      "sku": "CF-HOOD-SUPRA-24-GLOSS",
      "color": "Gloss Black",
      "image": "https://example.com/images/hood-gloss.jpg",
      "offers": {
        "@type": "Offer",
        "price": "1299.99",
        "priceCurrency": "USD",
        "availability": "https://schema.org/InStock",
        "url": "https://example.com/products/cf-hood-supra?variant=gloss"
      }
    }
  ]
}
```
- **Replication Status**: Google specification is stable and documented. Shopify native support confirms broad platform adoption.
- **Boundary Conditions**: Each `hasVariant` Product must be a real, separately purchasable variant — not a color swatch that loads the same page. The variant's `url` must point to a page (or URL parameter) that loads that specific variant.
- **Evidence Tier**: Gold — Google Search Central official specification.
- **Audit Note (2026-04-21)**: Verified live (doc last updated 2025-12-10). Prior "launched February 2024" and "Shopify native support July 2024" launch dates removed — not on current Google doc and not independently locatable. Required/recommended split corrected.

---

### Finding 6: MerchantReturnPolicy Schema Is Critical for Agentic Commerce
- **Source**: Google Search Central, "MerchantReturnPolicy structured data" (last updated 2025-12-10, verified 2026-04-21), https://developers.google.com/search/docs/appearance/structured-data/return-policy. OpenAI ChatGPT Shopping Research (launched Nov 24, 2025) uses return policy data for merchant comparison — see Finding 13 for caveat on OpenAI source verifiability.
- **Methodology**: Google official documentation; OpenAI feature launch (third-party confirmed). Return policy data is required/strongly recommended across major AI commerce surfaces.
- **Key Finding**: Return policy markup enables Google's return policy rich result display. AI purchasing agents (ChatGPT Shopping Research, Google's AI shopping) use return policy data to compare merchants and inform purchase decisions. Missing return policy in schema is a competitive disadvantage when AI agents compare otherwise equivalent products.

  **Required properties (corrected 2026-04-21 against live Google spec):**
  - **Option A (inline):** `applicableCountry` + `returnPolicyCategory`
    - `returnPolicyCategory` accepted values: `MerchantReturnFiniteReturnWindow`, `MerchantReturnNotPermitted`, `MerchantReturnUnlimitedWindow`
    - `merchantReturnDays` becomes required when category = `MerchantReturnFiniteReturnWindow`
  - **Option B (link-out):** `merchantReturnLink` (single property, URL pointing to a human-readable policy page)
  - **Recommended (either option):** `returnMethod` (values: `ReturnByMail`, `ReturnInStore`, `ReturnAtKiosk`), `returnFees`

  Prior version of this file listed `returnPolicyCategory` + `merchantReturnDays` + `returnMethod` as a required triad. This was incorrect: `applicableCountry` was missing from Option A, `returnMethod` is recommended not required, and `merchantReturnDays` is conditionally required only under `MerchantReturnFiniteReturnWindow`.

- **E-Commerce Application**: Add `MerchantReturnPolicy` to every product page schema. If your policy is simple and standard, Option B (single `merchantReturnLink`) is sufficient. For richer Google return-policy rich results and AI agent data, use Option A with `applicableCountry`, `returnPolicyCategory`, and the recommended supporting properties. Keep policy data synchronized with your actual policy.
- **Replication Status**: Google specification is authoritative. AI agent behavior with return policy data is inferred from specification requirements, not independently studied.
- **Boundary Conditions**: Only matters if you have an ecommerce Merchant Listing (not editorial). Return policy must accurately reflect your actual policy — misrepresentation is a trust signal issue with both users and platforms.
- **Evidence Tier**: Gold — Google Search Central official specification.
- **Audit Note (2026-04-21)**: Required properties corrected against live Google spec. `applicableCountry` added to Option A. `returnMethod` correctly classified as recommended. `merchantReturnLink` Option B documented.

---

### Finding 7: JavaScript-Generated Schema Is Unreliable for Merchant Center Crawls
- **Source**: Google Search Central documentation, "Provide structured data" (verified 2026-04-21), https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data. John Mueller statements on JavaScript rendering for Shopping crawls (Google Webmaster Central Office Hours).
- **Methodology**: Google documentation and spokesperson statements. The specific "faster, less sophisticated Merchant Center crawler" framing is practitioner synthesis inferred from Google guidance and Mueller Q&A — not verbatim text from the cited page.
- **Key Finding**: JavaScript-dynamically-generated schema makes Shopping data updates less frequent and less reliable because Merchant Center's crawler may not execute JavaScript. Google explicitly recommends server-side rendering for schema markup. Schema must appear in the HTML returned from the server.
- **E-Commerce Application**: Schema must appear in the server-rendered HTML — not injected by JavaScript after page load. For Next.js/Nuxt/headless commerce: use SSR or SSG with schema embedded in rendered HTML. For Shopify: Liquid templates render server-side by default — schema in Liquid is safe. For React SPAs: ensure schema is in the SSR HTML payload, not a client-side hydration artifact.
- **Replication Status**: Consistent across Google's documentation and multiple developer Q&A sessions. JS rendering for Googlebot (for ranking) works but is slower.
- **Boundary Conditions**: Googlebot for organic search does render JavaScript, but with a delay. The issue is more acute for Merchant Center's higher-frequency crawls. Schema for organic rich results has more tolerance for JS rendering, but server-rendering is still best practice.
- **Evidence Tier**: Silver — Google's SSR recommendation for structured data is Gold; the "less sophisticated Merchant Center crawler" specific claim is practitioner synthesis from Mueller Q&A, not verbatim current doc. Downgraded from Gold.
- **Audit Note (2026-04-21)**: Downgraded from Gold to Silver. Core recommendation (use SSR for schema) is solidly supported. The Merchant-Center-specific framing is well-documented practitioner inference, not a current-doc verbatim statement.

---

### Finding 8: Product Identifiers (GTIN/MPN/SKU) Are the Universal Commerce Key
- **Source**: Google Search Central, "Product identifiers in structured data" (verified 2026-04-24), https://developers.google.com/search/docs/appearance/structured-data/product#product-identifiers. Google Merchant Center product data specification (verified 2026-04-24): https://support.google.com/merchants/answer/7052112?hl=en.
- **Methodology**: Google official specification. Cross-platform requirement analysis.
- **Key Finding**: Without GTIN/MPN/SKU, Google cannot match products to its Shopping Graph knowledge base. AI shopping agents (ChatGPT, Perplexity) cannot cross-reference products across data sources. **Corrected 2026-04-21**: Google Merchant Center describes GTIN as "**strongly recommended** for all products with a GTIN assigned by the manufacturer" — not unconditionally required. Products without any unique identifiers "may not be eligible for all Shopping programs or features." For store/private-label/custom products without manufacturer-assigned GTINs, the documented alternative is `brand` + `mpn`.
- **E-Commerce Application**: Populate `gtin` (preferred), `mpn`, or `sku` for every product — at minimum one. Use the manufacturer's GTIN/UPC/EAN when it exists. For custom/artisan products without manufacturer-assigned GTINs, use `mpn` + `brand`. For automotive: include OEM part numbers as `mpn`. Never fabricate GTINs for competitor products on comparison/review pages — Lanham Act § 43(a) false-designation risk.
- **Replication Status**: Consistent across Google Merchant Center specification.
- **Boundary Conditions**: Hand-crafted, one-of-a-kind, custom-made, used/vintage, and store-brand products may legitimately lack manufacturer GTINs. In these cases, use `mpn` + `brand` per Merchant Center documented exceptions.
- **Evidence Tier**: Silver — Google Merchant Center official documentation; GTIN is "strongly recommended," not strictly required across the board. Downgraded from Gold.
- **Audit Note (2026-04-21)**: Downgraded from Gold to Silver. Both audits independently flagged the "strongly recommended vs. required" distinction. Boundary conditions expanded to include store-brand/used/vintage product exceptions per Merchant Center Help.

---

### Finding 9: Price Exposure in Rich Results Has Mixed Effects — Evidence Is Controlled
- **Source**: SearchPilot, "Impact on SEO Performance of Price and Review Schema" (controlled split test, verified 2026-04-21), https://www.searchpilot.com/resources/case-studies/seo-split-test-lessons-adding-price-review-schema-product-pages.
- **Methodology**: SearchPilot controlled SEO A/B split test — variant pages received price + review schema; control pages received no schema. A second test compared review-only vs. no schema. Statistical significance confirmed.
- **Key Finding**: Test 1 (price + review schema together): inconclusive — "no detectable impact on organic traffic." SearchPilot's own analysis: "the price displayed in search results wasn't necessarily showing us in the best light compared to competitors due to different bundling and minimum order sizes." Test 2 (review schema alone): ~20% organic traffic uplift (statistically significant). Hypothesis: price visibility in SERPs can help or hurt depending on competitive pricing context.
- **E-Commerce Application**: Default recommendation: implement `AggregateRating` (stars) for all products with genuine reviews. For `Offer` (price in SERPs): implement for competitive/commodity-priced products where price is a winning factor; run your own test or omit for premium/luxury or bundled products where SERP price may not reflect true value. Never implement schema hoping to trick the algorithm — the data must be accurate.
- **Replication Status**: Single controlled test on one site. SearchPilot's methodology is rigorous, but results may not generalize across all price points and categories. This is the best available controlled data on this specific question.
- **Boundary Conditions**: The inconclusive result for price+review is context-specific (competitor pricing, bundling, minimum order size). Commodity/competitive-price retailers may see positive CTR impact from price exposure. Category-specific testing is recommended before site-wide deployment.
- **Evidence Tier**: Gold — SearchPilot controlled split test is the gold standard for SEO testing methodology.
- **Audit Note (2026-04-21)**: Verified live. Added SearchPilot's own explanation for why price+review was inconclusive. No tier change.

---

### Finding 10: Review Schema Alone Produces ~20% Organic Traffic Uplift
> **Cross-Reference:** See also ugc-reviews-seo.md Finding 7 for the full treatment of this study in the context of UGC/review SEO strategy.
- **Source**: SearchPilot, "Impact on SEO Performance of Price and Review Schema" (primary source, verified 2026-04-21), https://www.searchpilot.com/resources/case-studies/seo-split-test-lessons-adding-price-review-schema-product-pages. **Citation correction 2026-04-21**: SearchPilot's "Most Surprising Tests of 2025" retrospective (https://www.searchpilot.com/resources/case-studies/a-look-back-at-the-most-surprising-tests-of-2025) was previously cited as a second source for the ~20% figure — verified 2026-04-21, the ~20% figure in that retrospective refers to a DIFFERENT test (adding specification tables/related products to thin content pages), NOT the review schema test. The retrospective is NOT a confirming citation for this finding. The primary case-study page remains the sole verified source for the ~20% review-schema uplift.
- **Methodology**: Controlled SEO split test with statistical significance testing. Variant pages received `AggregateRating` schema; control pages had no schema. Impact measured via organic traffic change.
- **Key Finding**: Adding `AggregateRating` schema (without price) produced approximately 20% organic traffic uplift — statistically significant. This is one of the largest controlled-test uplifts in publicly available SEO test data.
- **E-Commerce Application**: Implement `AggregateRating` on every product page with genuine customer reviews. Required fields per Google spec: `ratingValue`, `ratingCount` (or `reviewCount`). Recommended: `bestRating` (5), `worstRating` (1). Schema must reflect actual, unsuppressed customer data — fabricated, inflated, or selectively filtered ratings violate multiple legal regimes: FTC Fake Reviews Rule (16 CFR Part 465, effective 2024-10-21); FTC Endorsement Guides (16 CFR Part 255 §§ 255.1 and 255.2(b)); and Lanham Act § 43(a) where inflated SERP-surfaced schema functions as false comparative advertising. Specific comparative superlatives surfaced in schema, meta titles, or descriptions ("#1 rated," "Best 2026," "Voted best") are NOT puffery and fall within Lanham Act metadata scope. See `references/ethics-gate.md` Parts 2.2, 2.4, and 7.4. See also Finding 14.
- **Replication Status**: Single controlled test. Direction (positive impact) consistent with theory and practitioner experience. The ~20% magnitude is specific to this test context.
- **Boundary Conditions**: Requires genuine reviews. Google's guidelines require a minimum number of reviews for star display in rich results. Effect likely stronger for categories where purchase confidence matters most.
- **Evidence Tier**: Gold — SearchPilot controlled split test.
- **Audit Note (2026-04-21)**: Verified live. Retrospective secondary citation corrected — the "Most Surprising Tests" ~20% refers to a different test and is removed as a confirming citation. FTC/Lanham clause-level citations added per researcher-ethics ethics-gate guidance.

---

### Finding 11: Organization-Level Shipping Schema via ShippingService
- **Source**: Google Search Central, "Merchant Shipping Policy (ShippingService) structured data" (last updated 2026-01-07, verified 2026-04-21), https://developers.google.com/search/docs/appearance/structured-data/shipping-policy. Google Search Central Blog, "More ways to share your shipping and returns policies with Google" (November 2025) — https://developers.google.com/search/blog — as announcement context.
- **Methodology**: Google official specification update.
- **Key Finding**: Shipping information can be specified at the `Organization` level via `ShippingService`, reducing the need to add shipping details to every individual product page when shipping is uniform across a catalog. Per-product `OfferShippingDetails` remains available for product-specific shipping costs.
- **E-Commerce Application**: If shipping policy is consistent across all products (e.g., free shipping on all orders over $50), implement `ShippingService` at Organization level once. If product-specific shipping applies (e.g., oversized items with freight charges), maintain `OfferShippingDetails` per product. Reduces schema maintenance burden significantly for large catalogs.
- **Replication Status**: Google specification is authoritative. No controlled studies yet on impact vs. per-product shipping schema.
- **Boundary Conditions**: Only appropriate when shipping is genuinely uniform. Misrepresenting per-product shipping costs at the Organization level creates inaccurate data and may result in Merchant Center disapprovals.
- **Evidence Tier**: Silver — Google official documentation; limited real-world validation data on ROI impact relative to per-product schema.
- **Audit Note (2026-04-21)**: Prior "available since November 2025" launch-date claim removed — current doc (updated 2026-01-07) does not provide that specific date. Nov 2025 Search Central Blog post added as announcement source. Silver tier retained.

---

### Finding 12: [REMOVED — duplicate topic]
> Prior version of this file (Finding 12) covered two-phase canonical evaluation for JavaScript sites. This was (a) a duplicate of canonical-duplicate-content.md Finding 7, which owns that topic, and (b) the specific "two-phase" framing was not verifiable against the current Google canonicalization page (verified 2026-04-21). Removed. See `canonical-duplicate-content.md` for canonical evaluation guidance and its verification status.

---

### Finding 13: OpenAI ChatGPT Shopping Research — Schema.org Foundation Applies
- **Source**: OpenAI announcement of ChatGPT Shopping Research (launched November 24, 2025) — launch confirmed by SiliconANGLE https://siliconangle.com/, Bloomberg https://www.bloomberg.com/, Retail Dive https://www.retaildive.com/, PYMNTS https://www.pymnts.com/, Digital Commerce 360 https://www.digitalcommerce360.com/ (Tier-1 business press). Shopify partnership confirmed in platform release notes. **Primary spec URL (`platform.openai.com/docs/shopping`) is not accessible as of 2026-04-21** — field-level specification details (character limits, push frequency) are NOT verified and are removed from this version pending primary re-host. OpenAI docs root: https://platform.openai.com/docs
- **Methodology**: Third-party-confirmed product launch. Field-level specification details pending direct verification against OpenAI developer documentation.
- **Key Finding**: ChatGPT Shopping Research (formerly described as "Instant Checkout" in pre-launch materials — correct name per Nov 24, 2025 launch is "Shopping Research") is a reinforcement-trained GPT-5 Mini variant that compares products and recommends purchases. Shopify merchants have first-class native integration. GTIN, accurate pricing/availability, and complete return-policy data are documented as critical for product matching and rich comparison experience. The Schema.org foundation (Findings 1–11 in this file) serves ChatGPT Shopping Research, Google Shopping, and Perplexity simultaneously.
- **E-Commerce Application**: For Shopify stores: verify your Shopify admin's Sales Channels settings for ChatGPT Shopping integration. For non-Shopify platforms: implement comprehensive Schema.org Product markup (Findings 1–11) with GTIN populated and current inventory/pricing/return-policy data. For field-level OpenAI-specific requirements (character limits, feed push cadence, `is_eligible_search` flag): verify directly against current OpenAI developer documentation before implementation.
- **Replication Status**: Launched November 24, 2025 — early adoption phase. Primary spec URL was 404/inaccessible as of 2026-04-21.
- **Boundary Conditions**: Verify against OpenAI's current public documentation before implementation. Available in US initially; international rollout ongoing.
- **Evidence Tier**: Silver — launch and core direction confirmed by multiple Tier-1 press sources; field-level specification details require direct verification against OpenAI developer documentation.
- **Citation Status**: Original OpenAI Product Feed spec URL (`platform.openai.com/docs/shopping`) dead/inaccessible as of 2026-04-21. Launch confirmed by multiple Tier-1 business press sources. Field-level specification (character limits, feed cadence, specific field names) removed pending primary re-host.
- **Audit Note (2026-04-21)**: "Instant Checkout" framing corrected to "ChatGPT Shopping Research" per Nov 24, 2025 launch materials. Downgraded from Gold. Field-level prescriptions removed pending primary spec re-host. Silver (not Bronze) because the launch and directional guidance are solidly confirmed by Tier-1 press sources; only the specification detail level is unverified.

---

### Finding 14 (NEW — 2026-04-21): FTC Fake Reviews Rule & Lanham Act § 43(a) Apply to AggregateRating Schema
- **Source**: FTC Final Rule on Consumer Reviews and Testimonials (16 CFR Part 465), Federal Register 89 FR 68034, effective 2024-10-21. FTC rulemaking page and rule text: https://www.ftc.gov/legal-library/browse/rules/rulemaking-use-consumer-reviews-testimonials. FTC Endorsement Guides (16 CFR Part 255), specifically § 255.1 (honest-opinion requirement) and § 255.2(b) (performance-claim substantiation when ratings function as endorsements). Lanham Act § 43(a) (15 U.S.C. § 1125(a)) — false advertising / false designation of origin.
- **Methodology**: Federal regulation and statutory citation. Not a study — live law.
- **Key Finding**: 16 CFR Part 465 prohibits:
  - Fake or AI-generated reviews attributed to real-seeming consumers
  - Buying positive reviews or suppressing negative reviews
  - Company insiders posing as independent reviewers
  - Material misrepresentations about reviews, including aggregate ratings that systematically exclude negative reviews
  Civil penalties: up to $51,744 per violation (2024 threshold, adjusted for inflation). Enforcement actions were filed under the rule in 2025.

  Lanham Act § 43(a) creates a private right of action for competitors harmed by false or misleading statements in commerce — including inflated `AggregateRating` values that surface in SERPs and function as comparative advertising. Estimated ~500 Lanham Act suits per year involving SERP-surfaced metadata claims. Puffery in product descriptions remains protected; specific comparative superlatives in schema, meta titles, or descriptions ("#1 rated," "Best 2026," "Voted best") are NOT puffery and fall within metadata scope.

- **E-Commerce Application**: `AggregateRating` schema MUST reflect genuine, unsuppressed customer review data. Specifically:
  - Do NOT exclude negative reviews from the pool that feeds `ratingValue` and `ratingCount`
  - Do NOT fabricate review counts to hit Google's star-display threshold
  - Do NOT use AI-generated reviews without clear FTC-compliant disclosure (and even with disclosure, check current FTC guidance)
  - If you display `AggregateRating` while systematically suppressing 1–2 star reviews, you face direct FTC enforcement AND Lanham Act claims from competitors
  See `references/ethics-gate.md` Parts 2.2 (misleading structured data), 2.4 (fake reviews), and 7.4 (Lanham Act metadata scope).
- **Replication Status**: Live federal rule. Enforcement actions already filed in 2025.
- **Boundary Conditions**: Directly applies to US commerce. EU merchants face parallel obligations under the Unfair Commercial Practices Directive (2005/29/EC) as amended by the Modernisation Directive (2019/2161), which explicitly covers fake reviews and misleading aggregate ratings.
- **Evidence Tier**: Gold — federal regulation and statutory citation.

---

### Finding 15 (NEW — 2026-04-21): Rich Result Eligibility Is Revocable — Monitor Actively
- **Source**: Google Search Central, structured data intro documentation (verified 2026-04-21), https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data. Google Search Console Rich Results Status and Manual Actions reports.
- **Methodology**: Google official documentation.
- **Key Finding**: Rich result eligibility can be revoked via Google manual action for spammy or manipulative structured data. Even accurate schema does not guarantee rich result display — Google evaluates page quality, content relevance, and schema accuracy holistically. Schema is necessary but not sufficient for rich results.
- **E-Commerce Application**: Monitor Google Search Console's Rich Results Status report and Manual Actions report regularly. If flagged: (a) identify and correct inaccurate or manipulative schema immediately, (b) request a manual action review after remediation, (c) do not use schema to misrepresent page content, prices, or reviews.
- **Replication Status**: Google documentation is authoritative.
- **Boundary Conditions**: Rich result eligibility also requires meeting content quality thresholds. A technically correct schema on a thin-content page may still not produce rich results.
- **Evidence Tier**: Gold — Google Search Central official documentation.

---

## Methodological Notes and Caveats

1. **Schema specifications evolve rapidly.** Google's structured data documentation is updated frequently. Always verify against the current specification at https://developers.google.com/search/docs/appearance/structured-data/product before implementation.

2. **Rich results are not guaranteed.** Even perfect schema implementation does not guarantee rich result display. Google evaluates page quality, content relevance, and schema accuracy holistically. Schema is necessary but not sufficient (see Finding 15).

3. **SearchPilot tests are the most reliable data available for SEO impact.** Where SearchPilot controlled test data exists (Findings 9, 10), it should be weighted heavily over correlational studies or practitioner consensus.

4. **AI commerce specifications are in rapid flux.** ChatGPT Shopping Research (Finding 13) should be treated as forward-looking. Build on Schema.org as the stable foundation; treat platform-specific feeds as additive. Verify OpenAI field-level requirements directly against current developer documentation.

5. **AggregateRating is a live FTC liability surface.** Any claim about review counts or ratings via structured data is a representation under 16 CFR Part 465. Treat schema as regulated advertising data, not "just SEO" (see Finding 14).

6. **Evidence tier corrections in this revision (2026-04-21):** Finding 4 (ranking factor) downgraded Gold → Silver; Finding 7 (JS/Merchant Center) downgraded Gold → Silver; Finding 8 (GTIN) downgraded Gold → Silver; Finding 13 (OpenAI) downgraded Gold → Silver. These corrections reflect honest sourcing — not weakening of the underlying guidance.

---

## Sources Consulted

- Google Search Central Product Structured Data: https://developers.google.com/search/docs/appearance/structured-data/product
- Google Search Central JSON-LD Introduction: https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data
- Google Search Central Product Variants (ProductGroup): https://developers.google.com/search/docs/appearance/structured-data/product-variants
- Google Search Central MerchantReturnPolicy: https://developers.google.com/search/docs/appearance/structured-data/return-policy
- Google Search Central ShippingService: https://developers.google.com/search/docs/appearance/structured-data/shipping-policy
- Google Search Central Canonicalization: https://developers.google.com/search/docs/crawling-indexing/canonicalization
- Google Merchant Center Product Data Specification: https://support.google.com/merchants/answer/7052112?hl=en
- SearchPilot Price + Review Schema Test: https://www.searchpilot.com/resources/case-studies/seo-split-test-lessons-adding-price-review-schema-product-pages
- SearchPilot Most Surprising Tests 2025 (corroborative — see Finding 10 citation correction): https://www.searchpilot.com/resources/case-studies/a-look-back-at-the-most-surprising-tests-of-2025
- OpenAI Product Feed Specification: https://platform.openai.com/docs/shopping (inaccessible 2026-04-21 — verify directly before implementation)
- Schema.org Product: https://schema.org/Product
- Schema.org MerchantReturnPolicy: https://schema.org/MerchantReturnPolicy
- FTC Fake Reviews Rule (16 CFR Part 465): https://www.ftc.gov/legal-library/browse/rules/rulemaking-use-consumer-reviews-testimonials
