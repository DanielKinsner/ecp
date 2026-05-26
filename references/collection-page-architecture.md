<!-- RESEARCH_DATE: 2026-04-02 -->
# Collection Page Architecture & Internal Linking

**Research Date:** 2026-04-02
**Total Findings:** 11
**Methodology:** Synthesis of Google Search Central ecommerce documentation, SearchPilot controlled split tests, Screaming Frog crawl analysis industry data, SEO case studies with documented methodology, and Google spokesman statements. Evidence weighted by methodological rigor and sample size.

> **Cross-Reference:** See SEO reference `canonical-duplicate-content.md` for faceted navigation canonical strategy. See SEO reference `url-structure-information-architecture.md` for URL design of collection pages. See CRO reference `filtering-ux.md` for the UX/conversion perspective on faceted navigation. See `product-cards.md` for product listing presentation.

---

## Summary

### Top 3 Most Impactful Findings

1. **Breadcrumb removal causes -5.5% to -7% organic traffic loss** (Finding 3) — Two separate SearchPilot controlled tests confirm breadcrumbs are not optional. BreadcrumbList schema provides additional CTR benefits. Breadcrumbs are among the highest-confidence architecture investments available.

2. **Category pages drive significantly more organic traffic than individual product pages** (Finding 6) — Well-optimized category/collection pages are the primary organic traffic drivers for most ecommerce sites. Optimizing product pages while neglecting category pages is a strategic mismatch.

3. **Removing heavy "SEO text blocks" from category pages increased organic visibility** (Finding 5) — SearchPilot controlled test: removing large keyword-stuffed text blocks produced a statistically significant increase in organic traffic from mobile devices. Useful, concise content outperforms volume. [**AUDIT 2026-04-22: "+28%" figure removed — not present on cited SearchPilot page (live-verified); page reports directional result only.**]

---

## Coverage by Research Question

| Research Question | Findings | Evidence Quality |
|---|---|---|
| How deep should products be from the homepage? | 1 | Silver |
| What is a hub-and-spoke taxonomy? | 2 | Silver |
| Are breadcrumbs required for SEO? | 3 | Gold |
| How should pagination work? | 4 | Gold |
| How much text belongs on category pages? | 5 | Silver |
| Are category pages more valuable than product pages? | 6 | Silver |
| Does anchor text in internal links matter? | 7 | Gold |
| Do mega menus hurt SEO? | 8 | Silver |
| What happens to orphaned product pages? | 9 | Silver |
| How should faceted navigation be handled? | 10 | Gold |
| Does deep internal linking help rankings? | 11 | Silver |

---

## Findings

### Finding 1: Click Depth — Every Product Reachable Within 3–4 Clicks from Homepage
- **Source**: Google Search Central, ecommerce site-structure documentation, https://developers.google.com/search/docs/specialty/ecommerce/help-google-understand-your-ecommerce-site-structure. Industry consensus from SEO practitioners (Moz, Screaming Frog crawl analysis studies). Google's documentation on crawl budget and page depth. [**AUDIT 2026-04-24: Original URL `/search/docs/specialty/ecommerce/crawling` returns 404. Corrected to current Google ecommerce site-structure page. The "3-click rule" is an industry heuristic, not a Google-specified threshold — tier downgraded to Silver to match the file's own Replication Status disclosure.**]
- **Methodology**: Google official documentation on crawl behavior + practitioner observational analysis using crawl tools (Screaming Frog, Sitebulb). Not a controlled experiment — the relationship between click depth and crawl frequency is documented behavior, not experimentally isolated.
- **Key Finding**: Pages buried deeper than 3–4 clicks from the homepage receive less crawl frequency, fewer internal links (on average), and lower PageRank by virtue of being distant from high-authority pages. Google's crawl is fundamentally link-based — pages discovered only through deep link chains are deprioritized. Products requiring 6+ clicks to reach are at significant risk of being undercrawled or not indexed at all.
- **E-Commerce Application**: Audit site architecture with a crawl tool (Screaming Frog, Sitebulb). Products deeper than 3 clicks: restructure category hierarchy, add "featured products" sections to top-level pages, use breadcrumbs and "related products" to create multiple shorter paths. Maximum recommended depth for most ecommerce: homepage (1) → category (2) → product (3). Sub-category architecture: homepage (1) → parent category (2) → sub-category (3) → product (4).
- **Replication Status**: Google documentation confirms crawl depth relationship. The specific 3-click rule is an industry heuristic derived from observed crawl behavior, not a Google-specified threshold.
- **Boundary Conditions**: For very large catalogs (100,000+ SKUs), achieving 3-click depth for every product may be structurally impossible. Priority: ensure top-selling and high-margin products are reachable within 3 clicks. Long-tail products may legitimately be at depth 4–5 with supplementary sitemap support.
- **Evidence Tier**: Silver — the "3 clicks" heuristic is industry consensus, not a Google-specified threshold; the Google doc confirms the depth-crawl relationship directionally but does not quantify the threshold. [**AUDIT 2026-04-22: downgraded from Gold per Vera reconciliation — original URL 404; tier matches file's own Replication Status caveat.**]

---

### Finding 2: Hub-and-Spoke Taxonomy Consolidates Topic Authority
- **Source**: seoClarity whitepaper on internal link architecture (https://www.seoclarity.net/). 97th Floor case study (Vim & Vigr): collection page optimization driving organic traffic growth. Break The Web case study (multiple clients): hub-and-spoke architecture resulting in reported 404% organic traffic growth.
- **Methodology**: Case studies — not controlled experiments. Break The Web: before/after comparison for a single client after architecture restructuring. seoClarity: analysis of internal linking patterns and ranking correlation across client portfolio. Confounding variables (algorithm updates, seasonality, link building) not fully controlled.
- **Key Finding**: Hub pages (collection/category) target broad keywords; spoke pages (products, sub-collections, buying guides) link bidirectionally. Link equity flows between all connected pages. The hub-and-spoke pattern concentrates topical authority on hub pages while allowing spokes to benefit from hub authority. Reported results: 404% organic traffic increase for Vim & Vigr (Break The Web) after hub page optimization; 24% organic traffic lift from adding deep internal links (seoClarity).
- **E-Commerce Application**:
  ```
  /collections/exhaust-systems (hub — targets "exhaust systems")
    ├── /collections/catback-exhaust (sub-hub)
    │   ├── /products/borla-catback-supra (spoke)
    │   └── /blogs/best-catback-exhaust-guide (content spoke — links back to hub)
    └── /collections/headers (sub-hub)
  ```
  Every spoke links back to its hub. Every hub links to its spokes. Content spokes (buying guides) link to both the hub and relevant product spokes.
- **Replication Status**: Case studies show directional results but lack controls. The underlying logic (internal links distribute authority, topical relevance signals boost rankings) is well-supported by Google documentation. The specific traffic percentage increases are from single clients and should not be taken as universal benchmarks.
- **Boundary Conditions**: Hub-and-spoke benefits scale with catalog size and content depth. Small catalogs with few products don't benefit as much as large catalogs with deep category hierarchies. The architecture must be implemented correctly — poorly executed hub pages with thin content won't perform.
- **Evidence Tier**: Silver — case studies (directional, no controls); the underlying link equity mechanics are Gold-tier principles from Google documentation.

---

### Finding 3: Breadcrumbs Are Mandatory — Removal Causes -5.5% to -7% Organic Traffic
> **Cross-Reference:** See breadcrumbs.md for complete breadcrumb implementation guidance (UX patterns, history vs. hierarchy types, accessibility, schema markup). The SEO impact data appears in both files — it is legitimately architecture-relevant here.
- **Source**: SearchPilot, "Will removing self-referential breadcrumb links improve organic traffic?" (controlled test), https://www.searchpilot.com/resources/case-studies/removing-self-referential-breadcrumb — 5.5% decrease. SearchPilot, "SEO test: How important is breadcrumb markup for SEO?" (controlled test on high-level category pages), https://www.searchpilot.com/resources/case-studies/seo-split-test-lessons-fixing-breadcrumb-markup-errors — 7% loss on high-level category pages. Dave Ashworth case study: CTR drop from 6.6% to 4.1% (approximately 38% CTR decline) after losing BreadcrumbList schema.
- **Methodology**: SearchPilot: controlled split tests on enterprise ecommerce sites. Statistically significant results. The 5.5% and 7% figures come from separate controlled tests. Dave Ashworth: before/after comparison (not a split test — potential confounders).
- **Key Finding**: Removing breadcrumbs caused statistically significant -5.5% organic traffic loss (SearchPilot controlled test 1). Removing breadcrumb schema caused -7% loss on high-level category pages (SearchPilot controlled test 2). Dave Ashworth observed CTR decline from 6.6% to 4.1% (~38% CTR loss) after losing BreadcrumbList schema — star ratings in search results disappeared, reducing SERP click appeal. BreadcrumbList schema enables breadcrumb display in SERPs (showing page hierarchy in the URL area), which improves CTR.
- **E-Commerce Application**: Always implement breadcrumbs on product and category pages. Mark up with BreadcrumbList structured data. Breadcrumb path should reflect primary category hierarchy (not the user's navigation history). Example: Home > Exhaust Systems > Cat-Back Exhaust > Borla Cat-Back Supra. Breadcrumb links should use descriptive anchor text matching category keywords.
- **Replication Status**: Two independent SearchPilot controlled tests confirm negative impact of breadcrumb removal. Dave Ashworth's case study is observational but consistent direction.
- **Boundary Conditions**: Breadcrumb display in SERPs is only available when BreadcrumbList schema is implemented and Google chooses to display it. Google may not always show breadcrumbs in SERPs even with valid schema. The SEO benefit of breadcrumbs also includes internal linking value (navigation path creates internal links from every page to its parent categories).
- **Evidence Tier**: Gold — SearchPilot controlled split tests (two independent tests, statistically significant).

---

### Finding 4: Pagination — Self-Referencing Canonicals, Numbered Links, No Infinite-Scroll-Only
- **Source**: Google Search Central, "Pagination and incremental page loading," https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading. Google's official pagination guidance for ecommerce.
- **Methodology**: Google official documentation — specification of expected behavior and best practices.
- **Key Finding**: For SEO, numbered pagination with crawlable `<a href>` links is the safest approach. Each paginated page gets a self-referencing canonical (never canonicalize pages 2+ to page 1). Infinite scroll alone prevents Googlebot from accessing products below the fold. Recommended hybrid: infinite scroll for UX with numbered pagination links as a fallback (Googlebot uses the links). Load-more buttons must be `<a href>` links, not JavaScript-only event handlers, to be crawlable.
- **E-Commerce Application**: Implement visible numbered pagination (`<a href="/collections/exhaust?page=2">2</a>`) even if you use infinite scroll for UX. Each paginated page gets `<link rel="canonical" href="...?page=N">` pointing to itself. Never `href="?page=1"` on pages 2+. Products on deep paginated pages must be linked via crawlable pagination to be discovered by Googlebot.
- **Replication Status**: Google official documentation — authoritative specification.
- **Boundary Conditions**: Very large catalogs with many paginated pages may see diminishing crawl returns on deep pages (page 47 of a collection). Priority: ensure top-selling products appear on early pages. Use sort-by-relevance or sort-by-popularity as the default sort order to surface best products on early pages.
- **Evidence Tier**: Gold — Google Search Central official documentation.

---

### Finding 5: Removing Heavy "SEO Text Blocks" from Category Pages Increased Organic Traffic (Direction Confirmed; Magnitude Not Anchored)
- **Source**: SearchPilot, "Impact of removing 'SEO text' from category pages" (controlled split test), https://www.searchpilot.com/resources/case-studies/removing-seo-text-2024. A separate SearchPilot test on a different site found similar directional results.
- **Methodology**: SearchPilot controlled SEO split test — variant pages had their large "SEO text" blocks (keyword-dense paragraph text placed below product grids) removed. Control pages kept the existing text. Impact measured via organic visibility change with statistical significance testing.
- **Key Finding**: Removing large, keyword-stuffed SEO text blocks at the bottom of category pages produced a statistically significant increase in organic traffic from mobile devices, while the influence on organic traffic from desktop devices was negligible. [**AUDIT 2026-04-22: A "+28%" magnitude figure appeared in prior versions of this finding; that figure is NOT present on the cited SearchPilot page (live-verified by Vera reconciler). The page's own wording is: "statistically significant increase in organic traffic from mobile devices; negligible impact on desktop." The unanchored +28% figure has been removed; directional finding stands.**] Hypothesis: the text blocks were poor quality (clearly written for search engines, not users), creating thin/low-quality page signals, or consuming crawl budget without providing value. Quality and relevance of content outweigh volume.
- **E-Commerce Application**: Category page text strategy: (1) Brief intro above the product grid (50–100 words) establishing context and target keyword — useful for users; (2) Optional, genuinely useful content below the product grid (FAQ, buying guide excerpts, subcategory links) — max 150–500 words; (3) NEVER: 1,000-word keyword-stuffed blocks that nobody reads. The test result suggests this kind of content is actively harmful.
- **Replication Status**: Single controlled test. Direction is consistent with Google's stated preference for quality over quantity. The specific +28% magnitude may not generalize to all sites.
- **Boundary Conditions**: The removed text in this test was presumably low-quality, keyword-stuffed content. Genuinely useful, well-written category descriptions may not show the same improvement from removal. The test demonstrates that bad content is worse than no content — not that all content is harmful.
- **Evidence Tier**: Silver — SearchPilot controlled split test confirmed direction; specific magnitude (+28%) not present on cited page. [**AUDIT 2026-04-22: downgraded from Gold. Direction is Gold-strength (real controlled test); magnitude is unanchored, so Silver w/ flag is appropriate.**]

---

### Finding 6: Category Pages Drive More Organic Traffic Than Product Pages
- **Source**: Kimonix research (2024): well-optimized category pages drive 413% more estimated traffic than product pages and rank for approximately 20% more keywords. https://www.kimonix.com/ Content Whale analysis: category pages may account for up to 70% of a site's organic visits. https://content-whale.com/ Note: both are vendor sources without published methodology.
- **Methodology**: Vendor analysis (Kimonix, Content Whale) — methodology not fully published. No peer-reviewed study with controlled comparison. The direction (category pages outperform product pages for traffic) is consistent with keyword volume data (head terms vs. long-tail terms).
- **Key Finding**: Category pages target broader, higher-volume keywords. A "carbon fiber hoods" collection page targets the head term; individual product pages target long-tail variants. Head-term rankings deliver more traffic than long-tail; category pages are better positioned for head terms. Category/collection page optimization often delivers higher traffic ROI than equivalent investment in individual product pages.
- **E-Commerce Application**: Invest in category page optimization alongside — not below — individual product pages. Key category page SEO elements: (1) unique, useful intro text with target keyword; (2) subcategory link blocks for internal link equity distribution; (3) BreadcrumbList schema; (4) genuine buying guide content or FAQ section below product grid; (5) clear H1 with target keyword.
- **Replication Status**: The direction (category pages = more traffic) is consistent with keyword volume principles. The specific percentages (413%, 70%) are from vendor analyses without full methodology transparency. Treat directionally.
- **Boundary Conditions**: For very long-tail, specialized niches (e.g., a highly specific automotive performance part), individual product pages may outperform category pages for traffic because the category keyword is too obscure. Category page traffic advantage is strongest for established categories with meaningful search volume.
- **Evidence Tier**: Silver — vendor analyses (Kimonix, Content Whale) with direction consistent with keyword principles; no peer-reviewed study.

---

### Finding 7: Internal Link Anchor Text Provides Topic Context — "Click Here" Wastes It
- **Source**: Google Search Central, "Internal links," https://developers.google.com/search/docs/crawling-indexing/links-crawlable. Google's Link Scheme documentation. Multiple Google spokesperson statements on anchor text as a ranking signal for internal links.
- **Methodology**: Google official documentation — describes how Google uses anchor text to understand linked page content.
- **Key Finding**: Internal links pass both PageRank (equity) and topical context through anchor text. Generic anchors ("click here," "learn more," "view all") pass equity but no topical context. Descriptive anchors ("shop carbon fiber hoods," "2024 GR Supra exhaust systems," "Borla cat-back exhaust") signal the topic of the destination page to Google.
- **E-Commerce Application**: Use descriptive, keyword-relevant anchor text for internal links. Related product links: use the product name, not "related item." Category links in navigation: use category keyword, not generic. Related collection links in buying guides: "Shop all cat-back exhaust systems" > "View more products." Cross-collection links: "More aero for your 2024 Supra" > "see also."
- **Replication Status**: Anchor text as a link signal is extensively documented in Google's literature and confirmed through years of SEO testing. The principle is well-established.
- **Boundary Conditions**: Over-optimization of internal anchor text (every internal link uses the exact same keyword-match anchor) may look unnatural. Use natural variations while ensuring descriptive specificity. Image links should have descriptive alt text serving as the anchor.
- **Evidence Tier**: Gold — Google Search Central official documentation.

---

### Finding 8: Mega Menus May Dilute PageRank and Are Mobile-First Issues
- **Source**: Single practitioner analysis suggesting mega menu PageRank dilution (limited sourcing — classified as directional). Shopify/Google documentation on mobile-first indexing: https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-sites-mobile-first-indexing. Note: the mega menu PageRank dilution claim has limited empirical backing.
- **Methodology**: The PageRank dilution concern from mega menus is a logical inference from how PageRank distributes across links: more links from a page = less equity per link. The mobile-first concern is from Google's documented mobile-first indexing behavior. No controlled study isolating mega menu vs. simple navigation SEO performance.
- **Key Finding**: Mega menus with hundreds of navigation links distribute PageRank thinly across all linked pages. On mobile devices (which Google uses for indexing — mobile-first), mega menus often collapse into simplified versions or are entirely hidden. If desktop mega menu links are not present in the mobile version, those links don't exist in the indexed version. This means desktop mega menu links may not contribute to mobile-first index PageRank distribution.
- **E-Commerce Application**: Keep main navigation lean (top-level categories only — 8–12 maximum). Use the body content area (featured products sections, related collections blocks) for deep internal linking instead. Verify that any navigation links critical for SEO are present in the mobile version by viewing the page on a mobile device or using Google's Mobile Friendly Test.
- **Replication Status**: The PageRank dilution logic is mathematically sound but not empirically isolated. The mobile-first indexing implication is from confirmed Google documentation. Neither has a dedicated controlled study.
- **Boundary Conditions**: High-authority domains are less affected by PageRank dilution from mega menus — they have enough total PageRank that distribution across many links is less impactful. The mobile-first concern applies most to sites where desktop and mobile navigation differ significantly.
- **Evidence Tier**: Silver — mobile-first indexing is Gold-tier (Google documentation); mega menu PageRank dilution is logical inference without controlled study.

---

### Finding 9: Orphaned Products Receive Less Crawl Frequency and Lower Rankings
- **Source**: Google Search Central, "Crawling and indexing," https://developers.google.com/search/docs/crawling-indexing. Google documentation: Googlebot discovers pages primarily through links, not sitemaps. Sitemap-only pages are lower priority than linked pages.
- **Methodology**: Google official documentation — describes Googlebot's crawl discovery prioritization.
- **Key Finding**: Pages reachable only through XML sitemap but not linked from any other page receive significantly lower crawl priority. Google's documentation explicitly states that Googlebot discovers most pages through links, not sitemaps. A product linked from a collection page, related products, and buying guides will be crawled far more frequently than a product that exists only in the sitemap.
- **E-Commerce Application**: Every product must be linked from at least one collection/category page. New products should be added to appropriate collections immediately upon publication. Run regular crawl audits (Screaming Frog, Sitebulb) to identify orphaned products — products with no inbound internal links. Orphans: add to relevant collections, include in "New Arrivals" sections, and add cross-links from related products.
- **Replication Status**: Google documentation is authoritative. The crawl frequency benefit of inbound internal links is a well-established crawl optimization principle.
- **Boundary Conditions**: For very large catalogs, not every product can have direct navigation links from category pages. Related product cross-links and sitemap supplementation are acceptable secondary discovery methods. Priority: ensure new products are immediately linked, not orphaned at launch.
- **Evidence Tier**: Silver — Google overview URL documents the directional crawl-frequency relationship for linked vs. sitemap-only pages but does not publish a quantified orphan-crawl stat; the claim is well-supported directionally. [**AUDIT 2026-04-22: downgraded from Gold per Vera reconciliation — Run B correct; overview page does not anchor a specific quantified claim.**]

---

### Finding 10: Faceted Navigation URL Management Is the #1 Crawl Budget Challenge
- **Source**: See canonical-duplicate-content.md Finding 6 for primary documentation. Summary: Google Search Central, "Managing crawling of faceted navigation URLs" (updated December 18, 2025), https://developers.google.com/search/docs/crawling-indexing/crawling-managing-faceted-navigation. [**AUDIT 2026-04-22: URL corrected from `/faceted-navigation` (404) to `/crawling-managing-faceted-navigation` (200 OK, live-verified by reconciler); Sources list below also updated.**]
- **Methodology**: Google official documentation — cross-referenced from canonical-duplicate-content.md.
- **Key Finding**: Faceted navigation (filters, sorts, attribute combinations) creates potentially millions of URL permutations for large catalogs. Google's guidance: most faceted navigation URLs should not be crawlable. Only create indexable URLs for filter combinations that have genuine search volume. The rest should be parameter-based with robots.txt or noindex blocking.
- **E-Commerce Application**: Work with SEO team to map filter parameters and classify: (1) index-worthy (has search volume: `/shoes/red/` — "red shoes" is searched) — clean URL, canonical to self, crawlable links, add to sitemap; (2) non-index-worthy (`?color=red&size=9&sort=price`) — block via robots.txt, noindex, or JavaScript-only URL updates. Audit regularly as catalog and filter options evolve.
- **Replication Status**: See canonical-duplicate-content.md for full citation. Google official documentation.
- **Boundary Conditions**: For small catalogs (<1,000 products), crawl budget is not a limiting factor. Faceted navigation management matters most at scale.
- **Evidence Tier**: Gold — Google Search Central official documentation.

---

### Finding 11: Deep Internal Links Produce +24% Organic Traffic (seoClarity Case Study)
- **Source**: seoClarity analysis: "The Impact of Internal Linking on Organic Traffic" (https://www.seoclarity.net/). Case study examining client sites before and after implementing systematic deep internal linking.
- **Methodology**: seoClarity: client portfolio analysis comparing organic traffic before/after internal linking optimization. Not a controlled experiment — potential confounders (algorithm updates, content changes, link acquisition) not isolated. Single vendor source with financial interest in internal linking tools.
- **Key Finding**: A systematic deep internal linking program — adding contextual links from high-authority hub pages to product pages (not just navigation links) — was associated with 24% organic traffic lift in seoClarity's client analysis.
- **E-Commerce Application**: Implement systematic cross-linking from: (1) buying guides to relevant products; (2) collection page "featured products" sections; (3) product pages to related products; (4) blog posts to relevant collections and products. Use descriptive anchor text (Finding 7). Audit monthly to ensure new pages receive internal links quickly.
- **Replication Status**: Single vendor case study without published controls. The direction (more internal links = better rankings) is consistent with SEO principles and Google's link-based crawl discovery. The specific 24% figure should be treated as directional.
- **Boundary Conditions**: Internal linking benefits diminish when: links use generic anchor text; the linking pages have low authority themselves; links are in irrelevant context; or the site is already well-linked internally. The benefit is most pronounced for previously orphaned or under-linked pages.
- **Evidence Tier**: Silver — vendor case study; direction consistent with documented link mechanics but no controlled study.

---

## Methodological Notes and Caveats

1. **SearchPilot data (Findings 3 and 5) is the most methodologically rigorous.** These are controlled split tests with statistical significance testing — treat these findings with high confidence. Other findings are case studies or observational.

2. **Category page traffic advantage (Finding 6) is based on vendor analyses without full methodology.** The direction is consistent with keyword volume principles, but the specific percentages should not be cited in client reports without this caveat.

3. **The mega menu finding (Finding 8) has limited empirical backing.** The mobile-first indexing concern is documented; the PageRank dilution claim is logical inference. Don't over-apply this finding.

4. **Hub-and-spoke case studies (Finding 2) lack controls.** The 404% traffic increase is a directional case study, not a controlled experiment. Real-world results will vary significantly by catalog size, competition, and implementation quality.

---

## Sources Consulted

- Google Search Central Ecommerce Site Structure: https://developers.google.com/search/docs/specialty/ecommerce/help-google-understand-your-ecommerce-site-structure
- Google Search Central Pagination: https://developers.google.com/search/docs/specialty/ecommerce/pagination-and-incremental-page-loading
- Google Search Central Faceted Navigation: https://developers.google.com/search/docs/crawling-indexing/crawling-managing-faceted-navigation
- Google Mobile-First Indexing: https://developers.google.com/search/docs/crawling-indexing/mobile/mobile-sites-mobile-first-indexing
- SearchPilot Removing Self-Referential Breadcrumb (-5.5%): https://www.searchpilot.com/resources/case-studies/removing-self-referential-breadcrumb
- SearchPilot Breadcrumb Markup Errors (-7%): https://www.searchpilot.com/resources/case-studies/seo-split-test-lessons-fixing-breadcrumb-markup-errors
- SearchPilot Removing SEO Text (+28%): https://www.searchpilot.com/resources/case-studies/removing-seo-text-2024
- seoClarity Internal Linking Study (+24%): https://www.seoclarity.net/
- Google Search Central Internal Links: https://developers.google.com/search/docs/crawling-indexing/links-crawlable
