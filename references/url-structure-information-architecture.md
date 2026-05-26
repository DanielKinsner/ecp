<!-- RESEARCH_DATE: 2026-04-02 -->
<!-- RECONCILED: 2026-04-22 — Run B proposed adopted as base; Run A URL fixes integrated; no conflicts -->
# URL Structure & Information Architecture

**Research Date:** 2026-04-02
**Audit Date:** 2026-04-21
**Reconciled:** 2026-04-22
**Total Findings:** 11 (was 9 — added Finding 10: infinite URL spaces; Finding 11: URL case consistency)
**Methodology:** Synthesis of Google Search Central official ecommerce URL documentation (verified 2026-04-21), Google spokesperson statements (John Mueller, Matt Cutts), Shopify platform documentation, and platform-specific technical analysis. Evidence weighted by source authority and documentation rigor.

> **Cross-Reference:** See SEO reference `canonical-duplicate-content.md` for URL canonicalization strategy. See `collection-page-architecture.md` for how URL architecture connects to internal linking and crawl efficiency.

---

## Summary

### Top 3 Most Impactful Findings

1. **Never change URLs without 301 redirects for every old URL** (Finding 3) — URL changes break existing backlinks, bookmarks, and indexed pages. Accumulated link equity takes time to transfer via 301. URL restructuring for SEO reasons rarely delivers enough benefit to justify the migration risk.

2. **Hyphens, not underscores** (Finding 7) — Google treats hyphens as word separators; underscores as word joiners. `carbon-fiber-hood` = three indexed words. `carbon_fiber_hood` = one word. This is a binary, simple rule with broad application.

3. **Shopify's URL constraints are fixed — optimize the handle** (Finding 4) — Shopify enforces specific URL patterns and you cannot override them. Focus optimization energy on the handle (slug) portion, not the path prefix. Verify canonical tag behavior after any theme modification.

---

## Coverage by Research Question

| Research Question | Findings | Evidence Quality |
|---|---|---|
| Flat vs. deep URL structures — which is better? | 1 | Gold |
| What does Google's official guidance say about URLs? | 2 | Gold |
| How critical is URL permanence? | 3 | Gold |
| What are Shopify's URL constraints? | 4 | Silver |
| How do URL parameters affect crawl budget? | 5 | Gold |
| Do trailing slashes matter? | 6 | Silver |
| Hyphens vs. underscores — does it matter? | 7 | Gold |
| How should international/multilingual URLs work? | 8 | Silver |
| Do descriptive URLs improve CTR? | 9 | Silver |
| Infinite URL spaces (calendars, session IDs, additive filters)? | 10 (NEW) | Gold |
| URL case consistency? | 11 (NEW) | Gold |

---

## Findings

### Finding 1: Flat URL Structures Are Preferred Over Deeply Nested Paths
- **Source**: Google Search Central, "Designing a URL structure for ecommerce websites" (last updated 2025-12-10), https://developers.google.com/search/docs/specialty/ecommerce/designing-a-url-structure-for-ecommerce-sites. Moz Whiteboard Friday on URL structure (practitioner consensus). John Mueller has stated URL depth is "not a ranking factor."
- **Audit Note (2026-04-21)**: Replaced dead URL `/specialty/ecommerce/creating-discoverable-urls` (404) with successor live URL `/specialty/ecommerce/designing-a-url-structure-for-ecommerce-sites` (last updated 2025-12-10). Content match confirmed by both auditors.
- **Methodology**: Google official documentation + spokesperson statements. The link equity relationship (pages closer to root receive more links on average) is a structural observation from crawl analysis, not an experimentally isolated causal finding.
- **Key Finding**: Google has explicitly stated that URL depth is NOT a direct ranking factor. However: pages closer to the root domain tend to have stronger internal link equity (structural advantage, not algorithmic preference). Deep URLs (`/shop/automotive/exterior/hoods/carbon-fiber/toyota/supra/2024/gloss-finish`) are harder to share, harder to remember, create longer indexable strings, and may signal thin niche content to Google.
- **E-Commerce Application**:
  - **Best practice**: `/products/carbon-fiber-hood-supra-2024` (flat, Shopify-style)
  - **Acceptable**: `/exhaust/catback/borla-catback-supra` (two category levels)
  - **Avoid**: `/shop/automotive/exterior/hoods/carbon-fiber/toyota/supra/2024/gloss-finish` (unnecessary depth)
  - Maximum recommended depth for products: 3 path segments beyond the domain.
- **Replication Status**: Google documentation is authoritative. Mueller's "URL depth is not a ranking factor" statement is consistent across multiple sessions. The structural link equity relationship is observed, not experimentally isolated.
- **Boundary Conditions**: Very large ecommerce sites with complex taxonomies may require 3–4 category levels to organize their catalog logically. In these cases, the categorical clarity and user navigation benefit outweighs the marginal URL depth consideration. Don't sacrifice logical structure for flat URLs.
- **Evidence Tier**: Gold — Google Search Central documentation + John Mueller statements.

---

### Finding 2: Google's Official Ecommerce URL Guidance
- **Source**: Google Search Central, "Designing a URL structure for ecommerce websites" (last updated 2025-12-10), https://developers.google.com/search/docs/specialty/ecommerce/designing-a-url-structure-for-ecommerce-sites. Google's most current ecommerce-specific URL guidance. Additional: Google Search Central URL structure doc: https://developers.google.com/search/docs/crawling-indexing/url-structure (2025-12-10).
- **Audit Note (2026-04-21)**: Replaced dead URL `/specialty/ecommerce/creating-discoverable-urls` (404) with successor. Added variant canonical note, case-consistency note, and hyphens-over-underscores directive per live Google doc content.
- **Methodology**: Google official documentation — specification of URL best practices for ecommerce.
- **Key Finding**: Google's official URL guidance for ecommerce: (1) Minimize alternative URLs returning the same content; (2) Use descriptive words in URLs (`/product/black-t-shirt` > `/product/3243`); (3) Use `?key=value` parameters (not `?value` alone); (4) Fragment identifiers (`#section`) are entirely ignored by Googlebot — never use them for product content; (5) Avoid URL parameters that don't change page content (tracking parameters, session IDs); (6) For product variants: use query parameters with the parameter-omitted URL as canonical; (7) Treat URL capitalization consistently.
- **E-Commerce Application**: Default URL pattern: `/products/[descriptive-slug]`. Descriptive slug should include: product type + key differentiator + brand or fitment. Examples: `carbon-fiber-hood-toyota-gr-supra`, `borla-s-type-cat-back-exhaust-2024-supra`. Avoid: numeric-only slugs (`/products/3847`), keyword-stuffed slugs (`/products/best-cheap-carbon-fiber-hood-toyota-supra-buy-now`), URL parameters for content that should have clean URLs (`/products/hood?color=black&size=large` → better as `/products/hood-black`).
- **Replication Status**: Google official documentation — authoritative and current.
- **Boundary Conditions**: For large catalogs with many variants, clean URL per variant may create many indexed pages. See canonical-duplicate-content.md for variant canonical strategy. Fragment identifiers are completely ignored by Googlebot — if you use anchor-based navigation (`#specifications`), those sections are not separately indexable.
- **Evidence Tier**: Gold — Google Search Central official documentation.

---

### Finding 3: URL Permanence Is Critical — Change URLs Only When Current Structure Is Harmful
- **Source**: Google Search Central, "Best practices for URL structure" (last updated 2025-12-10), https://developers.google.com/search/docs/crawling-indexing/url-structure. Multiple John Mueller statements on URL migration costs. Industry evidence from URL migration case studies.
- **Audit Note (2026-04-21)**: Softened "90–99% equity transfer" claim — this specific percentage does not appear in Google's current documentation. Both auditors flagged it; corrected to "most, but not immediate."
- **Methodology**: Google documentation + Mueller statements. URL migration impact is observable in Search Console data post-migration. Equity transfer via 301 redirect is documented in Google's official documentation.
- **Key Finding**: Every URL change breaks: (1) existing backlinks pointing to the old URL, (2) bookmarks and direct traffic, (3) indexed pages. Google transfers most page equity via 301 redirect, but the transfer is not immediate — it can take weeks to months. During the transition, rankings may fluctuate. Changing URLs for cosmetic SEO improvement rarely delivers enough benefit to justify this cost.
- **E-Commerce Application**: Decision rule: change URLs ONLY when the current structure is actively harmful (e.g., keyword-stuffed, confusing, creating massive duplicate content). Not for: minor optimization (adding one keyword to a slug), cosmetic preference, rebranding that doesn't affect product names. When URLs must change: (1) implement 301 redirect for EVERY old URL to its new equivalent — no exceptions; (2) update all internal links to use new URLs; (3) update XML sitemap; (4) submit for recrawl in Search Console.
- **Replication Status**: The cost of URL changes is well-documented through many industry case studies. Google's documented behavior on 301 equity transfer is consistent across Mueller statements.
- **Boundary Conditions**: Platform migrations (e.g., Magento to Shopify) often require URL structure changes. In these cases, URL changes are unavoidable — focus on implementing 301 redirects comprehensively. Even with perfect redirects, expect 2–3 months of ranking fluctuation post-migration.
- **Evidence Tier**: Gold — Google documentation and multiple consistent Mueller statements.

---

### Finding 4: Shopify URL Constraints Are Fixed — Optimize the Handle Only
- **Source**: Shopify Help documentation, "URL structure in Shopify," https://help.shopify.com/en/manual/online-store/search-engine-optimization/seo-support. Shopify developer documentation on URL routing.
- **Audit Note (2026-04-21)**: Shopify Help page returns 403 to automated fetching (bot protection); page is reachable for human users. Platform behavior is factual and unchanged — both auditors confirmed.
- **Methodology**: Platform technical analysis — Shopify's routing system is documented and deterministic. No study required; it's factual platform behavior.
- **Key Finding**: Shopify enforces these URL patterns: `/products/[handle]` (products), `/collections/[handle]` (collections/categories), `/pages/[handle]` (static pages), `/blogs/[blog-handle]/[article-handle]` (blog articles). You cannot create custom URL structures beyond these patterns. Products are also accessible at `/collections/[collection-handle]/products/[handle]` — this is a known duplicate path that Shopify handles via canonical tags pointing to `/products/`.
- **E-Commerce Application**: (1) Accept Shopify's URL patterns — they are adequate for SEO; (2) Optimize the `handle` (slug) portion: descriptive, keyword-rich, hyphenated, lowercase; (3) Ensure handle is set correctly at product creation — changing it later requires a redirect; (4) Verify canonical tags point to `/products/` URL, not the collection-prefixed duplicate; (5) After any theme update, re-verify canonical tag behavior with `curl -s [URL] | grep canonical`.
- **Replication Status**: Shopify platform behavior — consistent across all Shopify stores. Not a study that requires replication.
- **Boundary Conditions**: Shopify Plus offers headless commerce options that allow custom URL structures, but this requires significant development investment. Standard Shopify is limited to the fixed patterns. Headless/custom solutions must implement their own canonical tag management.
- **Evidence Tier**: Silver — Shopify enterprise documentation (Silver per publisher list). Verifiable platform behavior.

---

### Finding 5: URL Parameters and Crawl Budget — Ecommerce-Specific Concerns
- **Source**: Google Search Central, "Designing a URL structure for ecommerce websites," https://developers.google.com/search/docs/specialty/ecommerce/designing-a-url-structure-for-ecommerce-sites (URL parameter guidance for ecommerce). Google faceted-navigation doc: https://developers.google.com/search/docs/crawling-indexing/crawling-managing-faceted-navigation (2025-12-18). Google Search Console URL Parameters tool was deprecated — current guidance is to use robots.txt, noindex, or canonical tags instead.
- **Audit Note (2026-04-21)**: Prior file cited `/specialty/ecommerce/url-structure-for-ecommerce` which returns 404. Run B identified this; updated to current live source URLs.
- **Methodology**: Google official documentation — describes parameter classification and recommended handling.
- **Key Finding**: URL parameters in ecommerce create crawl budget challenges when they generate unique URLs for the same or similar content. Parameter types: (1) content-changing parameters (`?page=2` — changes content, keep crawlable); (2) presentation parameters (`?sort=price` — doesn't change content, block from indexing); (3) filter parameters (`?color=red` — may or may not merit indexing based on search volume for that combination). The deprecated Google Search Console URL Parameters tool has been replaced by manual management via robots.txt, noindex, and canonical tags.
- **E-Commerce Application**: Audit every parameter your site generates. Map each to: (a) index (has search volume, unique content), (b) noindex (minor or no search volume), (c) block via robots.txt (completely prevent crawling). Sort parameters: always noindex/block. Session ID parameters: always block (they create infinite URL spaces). Pagination parameters: keep crawlable with self-referencing canonicals.
- **Replication Status**: Google documentation is authoritative. The parameter management approach is well-established in ecommerce SEO practice.
- **Boundary Conditions**: Small ecommerce sites (< 1,000 products) may not need parameter management — Google's crawl budget is rarely exhausted. Parameter management becomes critical at 10,000+ product scale where filter combinations can create millions of URLs.
- **Evidence Tier**: Gold — Google Search Central official documentation.

---

### Finding 6: Trailing Slashes — Choose One, Be Consistent, Redirect the Other
- **Source**: John Mueller, multiple Search Central office hours and Twitter/X statements (2019–2023): "Google treats `/products/hood` and `/products/hood/` as different URLs." Google Search Central URL structure documentation. https://developers.google.com/search/docs/crawling-indexing/url-structure https://www.youtube.com/@GoogleSearchCentral
- **Methodology**: Google spokesperson statements + documentation. Not a study — factual URL behavior description.
- **Key Finding**: Google treats URLs with and without trailing slashes as different pages. `/products/hood` and `/products/hood/` are two separate URLs — both accessible, both indexable, both potentially creating duplicate content. Most platforms have a consistent pattern — Shopify does not use trailing slashes; WordPress/WooCommerce typically does. The choice between styles doesn't matter for ranking; consistency and redirect implementation are what matter.
- **E-Commerce Application**: (1) Determine your platform's default trailing slash behavior; (2) Ensure both versions (with and without slash) don't return 200 OK simultaneously — implement a redirect from the non-preferred to the preferred version; (3) Use the canonical URL format (with or without slash) consistently in all internal links, sitemaps, and structured data.
- **Replication Status**: Google spokesperson statements — consistent. The behavior is verifiable by directly comparing response codes for `/products/hood` vs. `/products/hood/`.
- **Boundary Conditions**: Most modern platforms handle trailing slash redirects automatically. Custom-built platforms and some server configurations may not. Verify with server-level response code testing.
- **Evidence Tier**: Silver — Google spokesperson statements (consistent); classified Silver as there's no formal study on the ranking impact of trailing slash inconsistency (the issue is primarily duplicate content management).

---

### Finding 7: Hyphens vs. Underscores — Hyphens Are Word Separators, Underscores Are Not
- **Source**: Matt Cutts (former Google head of Webspam), "Dashes vs. Underscores" video (Google Webmaster Tools, 2011), https://www.youtube.com/watch?v=AQcSFsQyct8. Google Search Central URL structure doc (last updated 2025-12-10): "we recommend using hyphens (`-`) instead of underscores (`_`) to separate words in your URLs, as it helps users and search engines better identify concepts in the URL." John Mueller has confirmed this behavior remains consistent.
- **Audit Note (2026-04-21)**: Double-sourced — added verbatim quote from current live Google URL structure doc (2025-12-10) in addition to the 2011 Matt Cutts video. Both auditors verified.
- **Methodology**: Google official statement (Matt Cutts, recorded video demonstration) + current Google URL documentation.
- **Key Finding**: Google treats hyphens (`-`) as word separators. `carbon-fiber-hood` is indexed as three separate words: "carbon," "fiber," "hood." Google treats underscores (`_`) as word joiners. `carbon_fiber_hood` is treated as one word: "carbon_fiber_hood." This means underscore-separated URLs do not get individual word indexing for each component — they behave as if the entire slug is one concatenated keyword.
- **E-Commerce Application**: Always use hyphens in URL slugs, image filenames, and any URL-visible strings. Never use underscores. Also: lowercase only (mixed-case URLs create duplicate content risk), no spaces (encode as `%20` which is ugly — use hyphens), no special characters except hyphens.
- **Replication Status**: Google official statement from Matt Cutts (video). Consistent across many years, confirmed by John Mueller, and documented in current live Google URL structure doc (2025-12-10).
- **Boundary Conditions**: This specifically applies to URLs and URL slugs. In filenames served via URLs (images, PDFs), the same rule applies. Underscores in CSS class names or JavaScript variables don't affect SEO.
- **Evidence Tier**: Gold — direct Google spokesperson statement (Matt Cutts video, John Mueller confirmation); documented in current Google URL structure doc.

---

### Finding 8: International URL Structure — Subdirectories, Subdomains, and ccTLDs Are Neutral Options
- **Source**: Google Search Central, "Multi-regional and multilingual sites" (last updated 2025-12-10), https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites. Google's official guidance on international targeting options.
- **Audit Note (2026-04-21)**: Both auditors independently flagged that the prior file's "Google recommends subdirectories for ecommerce" framing overstates Google's current position. The live doc presents all three options (ccTLDs, subdirectories, subdomains) with trade-offs rather than prescribing one. Framing and Evidence Tier corrected accordingly (Gold → Silver: the guidance is authoritative but the prior claim attributed a preference to Google that the doc does not make).
- **Methodology**: Google official documentation — specification of expected behavior for three URL patterns for international ecommerce.
- **Key Finding**: Three URL patterns for multi-market ecommerce: (1) **ccTLDs** (`example.de`) — strongest geographic signal, requires separate domain management; (2) **subdirectories** (`example.com/de/`) — "Easy to set up," "Low maintenance"; consolidated authority on a single domain; single server location is a drawback; (3) **subdomains** (`de.example.com`) — treated by Google as separate sites, may split domain authority. Google does NOT state a universal preference among these three. Each localized version requires: hreflang tags pointing to all alternates (including x-default), self-referencing canonical in the correct locale's format.
- **E-Commerce Application**: Choose based on operational trade-offs: ccTLDs for strongest local geographic signal + budget for separate domain management; subdirectories for consolidated authority + easier management; subdomains rarely chosen for ecommerce. For Shopify: Shopify Markets handles hreflang automatically. Whichever structure you choose, canonical for each locale should be the locale-specific URL, not the default language URL. Example: German product page canonical = `https://example.com/de/products/carbon-hood` (not `https://example.com/products/carbon-hood`).
- **Replication Status**: Google official documentation — authoritative guidance.
- **Boundary Conditions**: For very small international reach (1–2 markets, small catalog), the complexity of hreflang implementation may not justify the benefit over a simpler geotargeting approach.
- **Evidence Tier**: Silver — Google Search Central documentation is authoritative, but downgraded from Gold because the prior "subdirectories recommended for ecommerce" claim overstated the doc's actual neutrality on the topic.

---

### Finding 9: Descriptive URLs May Improve CTR — User Expectation Setting
- **Source**: Industry consensus and UX research on URL readability. Google Search Central documentation noting descriptive URLs help users understand page content before visiting. https://developers.google.com/search/docs/crawling-indexing/url-structure No controlled study specifically isolating CTR impact of descriptive vs. numeric URLs in SERPs.
- **Methodology**: No controlled study. Google documentation notes user benefit of descriptive URLs. Logical inference: users can read the URL in the SERP breadcrumb and form expectations about the page.
- **Key Finding**: Descriptive URLs (`/products/carbon-fiber-hood-supra-2024`) help users understand what they'll find before clicking — setting accurate expectations. Numeric/opaque URLs (`/products/3847`) provide no context. While no controlled study isolates URL descriptiveness as a CTR variable, descriptive URLs are consistently recommended across Google's documentation and UX literature.
- **E-Commerce Application**: Use descriptive slugs that include product category, key attribute, and relevant identifiers. The SERP breadcrumb (showing URL path structure) is read by users — make it informative. Avoid: numeric-only slugs, random strings, excessive abbreviations.
- **Replication Status**: No controlled study specifically on URL descriptiveness vs. CTR. The user expectation benefit is logical and consistent with UX research on URL readability.
- **Boundary Conditions**: Extremely long descriptive URLs may be truncated in SERP display, reducing the readability benefit. Keep descriptive slugs concise (3–6 words) while covering the essential identifying information.
- **Evidence Tier**: Silver — industry consensus and Google documentation support; no controlled study.

---

### Finding 10 (NEW — 2026-04-21): Avoid Infinite URL Spaces — Calendars, Session IDs, Additive Filters
- **Source**: Google Search Central URL structure doc: https://developers.google.com/search/docs/crawling-indexing/url-structure (2025-12-10, verified 2026-04-21). Google faceted-navigation doc: https://developers.google.com/search/docs/crawling-indexing/crawling-managing-faceted-navigation (2025-12-18, verified 2026-04-21).
- **Methodology**: Google official documentation — explicit anti-patterns flagged in current docs.
- **Key Finding**: Google explicitly flags several URL anti-patterns that create infinite or near-infinite URL spaces, wasting crawl budget: (1) **infinite calendar links** (each day links to the next day's calendar — never terminates); (2) **session IDs** in URLs (every session creates a new unique URL); (3) **additive filter URLs** (every combination of filters creates a new URL — N! combinations possible); (4) **irrelevant parameters** that don't change page content.
- **E-Commerce Application**: Audit for: (1) calendar widgets with crawlable "next month/next day" links; (2) session-based URLs; (3) additive filter URLs (`?color=red&color=blue&size=M&size=L` where order matters creates factorial combinations). Remediation: remove server-side URL generation for these patterns, block via robots.txt, or use URL fragments (`#filter`) instead of query parameters for presentation-only state.
- **Replication Status**: Google official documentation.
- **Boundary Conditions**: Most applicable to sites with calendar/booking widgets, complex product filters, or legacy session-based architectures. Well-architected Shopify stores rarely generate these issues by default.
- **Evidence Tier**: Gold — Google Search Central official documentation.

---

### Finding 11 (NEW — 2026-04-21): URL Case Consistency — Enforce Lowercase Uniformly
- **Source**: Google Search Central URL structure doc: https://developers.google.com/search/docs/crawling-indexing/url-structure (2025-12-10, verified 2026-04-21).
- **Methodology**: Google official documentation.
- **Key Finding**: Google's URL structure doc recommends consistent case handling to avoid duplicate content from case variants. `/Products/Hood` and `/products/hood` are technically different URLs — Google may crawl and index both separately, diluting signals. The doc recommends treating URL case consistently.
- **E-Commerce Application**: Enforce lowercase URLs platform-wide. 301 redirect mixed-case variants to lowercase. Configure web server (nginx, Apache, Cloudflare) to do automatic case-normalization where supported. For Shopify: handles are automatically lowercase; case issues typically arise with legacy URL patterns or custom routes in headless setups.
- **Replication Status**: Google official documentation.
- **Boundary Conditions**: Case sensitivity is a server-configuration issue; some servers treat URLs as case-insensitive by default, which masks the problem but may allow mixed-case URLs to resolve and fragment crawl equity.
- **Evidence Tier**: Gold — Google Search Central official documentation.

---

## Decision Tree: URL Structure

```
Starting a new site?
├── YES → Design URL structure before building
│   ├── Products: /products/[descriptive-slug]
│   ├── Collections: /collections/[category-slug]
│   ├── Blog: /blog/[post-slug]
│   ├── All slugs: lowercase, hyphens, descriptive words
│   └── Pick trailing slash style → redirect the other
└── NO → Migrating or restructuring?
    ├── Current URLs have equity? → Keep them
    │   └── URL optimization rarely worth migration risk
    ├── Current URLs are actively harmful?
    │   → Restructure WITH comprehensive 301 redirects
    │   → Map every single old URL to new equivalent
    └── Platform migration (e.g., Magento → Shopify)?
        → Match old URL patterns where platform allows
        → 301 redirect every old URL, no exceptions

What platform?
├── Shopify → Accept /products/, /collections/, /pages/ patterns
│   → Optimize handle/slug portion only
│   → Verify canonical tags after any theme change
├── Next.js / headless → Full control
│   → Implement /products/[slug] routing
│   → Ensure SSR canonical tags
│   → Enforce lowercase normalization server-side
├── WordPress/WooCommerce → Configure permalink structure
│   → /product/[slug]/ or /shop/[category]/[slug]/
└── Custom → SEO-first URL architecture
    → Document URL structure in technical spec before build
```

---

## Methodological Notes and Caveats

1. **URL structure has direct SEO impact through crawl efficiency and duplicate content management, not through URL "signals" per se.** Google has explicitly said URL structure is not a direct ranking factor. The indirect effects (internal link equity, crawl efficiency, duplicate content) are real.

2. **Never restructure URLs for marginal SEO benefit.** The cost (broken links, equity transfer time, redirect chain risk) almost always exceeds the benefit. The only valid reason to change URLs is when the current structure is actively harmful (creating massive duplication or crawl waste).

3. **Shopify's URL constraints are not SEO limitations.** The `/products/` and `/collections/` pattern is perfectly adequate for ranking. Don't let Shopify's fixed URL structure be a concern — focus optimization energy on content and authority.

4. **International URL choice is neutral per Google (Finding 8, corrected 2026-04-21).** The prior file overstated Google's stated preference for subdirectories. Google's current documentation presents ccTLDs, subdirectories, and subdomains as options with trade-offs. Subdirectories are a common and adequate default; they are not explicitly recommended over the others.

---

## Audit Change Log (2026-04-21)

| Change | Type | Auditors |
|---|---|---|
| Finding 1: Dead URL `/creating-discoverable-urls` → `/designing-a-url-structure-for-ecommerce-sites` | URL fix | A + B |
| Finding 2: Same dead URL fix; added variant canonical note and case-consistency note from live doc | URL fix + content | A + B |
| Finding 3: Softened "90–99% equity transfer" to "most, but not immediate" (figure not in current Google doc) | Claim softening | B (A did not flag) |
| Finding 5: Dead URL `/url-structure-for-ecommerce` → `/designing-a-url-structure-for-ecommerce-sites` + faceted-nav doc | URL fix | B (A did not flag) |
| Finding 7: Added verbatim quote from current Google URL structure doc as second source | Strengthening | A + B |
| Finding 8: Softened "Google recommends subdirectories for ecommerce" framing; tier Gold → Silver | Claim softening + tier | A + B |
| Finding 10: Added — Avoid infinite URL spaces (calendars, session IDs, additive filters) | New finding | B |
| Finding 11: Added — URL case consistency | New finding | B |

**Conflict resolution:** Run A's proposed file was accurate and internally consistent but did not catch the Finding 5 dead URL or the "90–99%" softening, and did not add Findings 10–11. Run B caught all of the above. No conflicts between the two runs — B's proposed adopted as the base with no overrides required.

---

## Sources Consulted

- Google Search Central Designing a URL Structure for Ecommerce: https://developers.google.com/search/docs/specialty/ecommerce/designing-a-url-structure-for-ecommerce-sites (2025-12-10)
- Google Search Central URL Structure Best Practices: https://developers.google.com/search/docs/crawling-indexing/url-structure (2025-12-10)
- Google Search Central Multi-regional and Multilingual: https://developers.google.com/search/docs/specialty/international/managing-multi-regional-sites (2025-12-10)
- Google Search Central Faceted Navigation: https://developers.google.com/search/docs/crawling-indexing/crawling-managing-faceted-navigation (2025-12-18)
- Matt Cutts Hyphens vs. Underscores (2011): https://www.youtube.com/watch?v=AQcSFsQyct8
- Shopify SEO Support Documentation: https://help.shopify.com/en/manual/online-store/search-engine-optimization/seo-support
