<!-- RESEARCH_DATE: 2026-04-02 -->
<!-- PROPOSED (Run B1 audit 2026-04-21): 2 URL fixes, 3 tier downgrades (F4/F5/F6 Gold→Silver), 2 new findings (F11 Baymard 2024, F12 Google 2024 faceted nav). See per-file review for detail. -->
<!-- NOTE: Key findings from this file have been merged into search-and-filter-ux.md. This file remains as supplementary reference with additional depth on filtering UX implementation details: promoted filters above the grid, dual applied-filter display, price filter requirements, filter value counts, mobile filter panel design, URL state management, and multi-select logic. -->
# Filtering UX: Research Findings

**Research Date**: April 2, 2026 (original); audit-reviewed April 21, 2026
**Domain**: Category UX — Product Filtering and Faceted Navigation
**Total Findings**: 12 (original 10 + 2 added in audit)
**Methodology Note**: Baymard Institute is the definitive research source for ecommerce filtering UX, with 25+ rounds of qualitative usability testing and a benchmark of 327+ major ecommerce sites. The search-and-filter-ux.md file in ECP contains 36 findings on this topic with significant overlap. This file focuses on findings not already covered there, with cross-references where overlap exists.

---

## Cross-Reference Notice

**ECP Reference Overlap** — These findings are COVERED in search-and-filter-ux.md and NOT fully duplicated here:
- Finding 1 (only 16% of sites have good filtering UX) — search-and-filter-ux.md Finding 1
- Finding 2 (67–90% abandonment with mediocre filtering; 17–33% with optimization) — search-and-filter-ux.md Finding 2
- Finding 3 (40% of users can't locate filter options) — search-and-filter-ux.md Finding 3
- Finding 4 (thematic filters drive >50% engagement when available) — search-and-filter-ux.md Finding 4
- Finding 7 (no-results recovery) — covered in zero-results.md

This file extends the filtering research with: promoted filters above the grid, dual applied-filter display, mobile-specific filter patterns, price filter requirements, filter value counts, and URL state management.

---

## Summary

### Top 3 Most Impactful Findings

1. **Finding 1 (Five Essential Filters — Only 43% of Sites Offer All Five)**: Price, User Rating, Color, Size, and Brand are required by users universally. Missing any of these core filters causes users to assume the store doesn't support their evaluation needs and to abandon. This is a gap directly addressable in an afternoon.
2. **Finding 2 (Applied Filters Shown in Two Locations — Macy's Best Practice)**: Applied filter chips shown only in the sidebar OR only above the grid both create user errors. Dual-location display (sidebar checked + chips above grid) is the gold standard that dramatically reduces "I'm confused about what's filtered" failures.
3. **Finding 5 (Price Filter Must Have Input Fields, Not Just Slider)**: Range sliders without manual input fields are one of the most common and frustrating filter failures — users with specific budgets can't enter exact numbers, and accidental slider movement loses their selection.

---

## Findings

### Finding 1: Five Essential Filters Required by Users — Only 43% of Sites Offer All Five

- **Source**: Baymard Institute. "Filtering UX: 5 Essential Filter Types." https://baymard.com/blog/5-essential-filters. Large-scale mobile usability testing. Published via Smashing Magazine and Baymard research database. Cross-referenced with search-and-filter-ux.md (ECP).
- **Methodology**: Baymard large-scale usability testing across 19+ major ecommerce sites, 4,400+ test sessions. Observation of filter usage patterns and abandonment behavior when filters are unavailable.
- **Key Finding**: 80% of mobile users apply Price filters. 53% of sites don't offer User Rating filters. Only 43% of sites offer all five essential filters. The five: (1) Price — used by 80% of mobile users; (2) User Rating — used by majority of quality-focused shoppers; (3) Color — critical for apparel, home decor, accessories; (4) Size — essential for apparel, footwear; (5) Brand — essential for multi-brand stores. Per-filter adoption gaps: Price 12% missing; Color 10%; Size 15%; Brand 27%. Missing any of these causes the user to conclude: "this site can't help me find what I need" → abandonment.
- **E-Commerce Application**: Audit your current filter set against these five. Add any missing essential filters before adding category-specific or thematic filters. Priority order for implementation: Price (immediate if missing), Brand (if multi-brand), Size (if selling apparel/footwear), Color (if selling visual products), Rating (if reviews exist). Category-specific "thematic" filters (occasion, fit type, material, feature set) are the next tier after these five are in place.
- **Replication Status**: Consistent across multiple Baymard testing rounds. The 80% price filter usage figure has been replicated in Baymard mobile testing data.
- **Boundary Conditions**: Single-brand stores don't need a Brand filter. Non-apparel/footwear stores may not need a Size filter. Very small catalogs (<50 products) may not need the full five — filters are most valuable with 100+ products per category.
- **Evidence Tier**: Gold

---

### Finding 2: Applied Filters Must Be Shown in Two Locations Simultaneously

- **Source**: Baymard Institute. "7 Filtering Implementations That Make Macy's Best-in-Class." https://baymard.com/blog/macys-filtering-experience. 2023. Large-scale usability testing benchmark.
- **Methodology**: Comparative usability testing of sites with different applied-filter display implementations. Baymard identified Macy's as best-in-class specifically for dual-location applied filter display.
- **Key Finding**: Sites that displayed applied filters in two locations simultaneously — (1) as removable chips/tags above the product grid AND (2) as checked/highlighted options in the sidebar — had vastly lower rates of user errors compared to single-location display. Baymard reports "42% of e-commerce sites only display applied filter in one of these positions" (Macy's article, verified). Single-location display (sidebar only) causes users to lose track of active filters when they scroll the sidebar out of view. Grid-top chips only (without sidebar sync) cause users to not know what filter controls correspond to the chips.
- **E-Commerce Application**: Applied filter display requirements: (1) Above product grid: display each active filter as a chip with product label and × removal button — `Color: Blue ×` `Size: M ×` with a "Clear all filters" link; (2) In sidebar: keep the filter option checked/highlighted/filled with accent color so its selection state is evident without reading the chips; (3) Product count update: dynamically update the product count display ("142 products" → "23 products") when filters are applied; (4) Remove button on each chip removes only that filter, not all filters; "Clear all" removes all filters simultaneously.
- **Replication Status**: Consistent across multiple Baymard testing rounds. The Macy's best-practice designation has appeared in Baymard research for several years.
- **Boundary Conditions**: Dual-location display increases implementation complexity. For very simple filter UIs with 1–2 filters: single location may be acceptable. The benefit is most pronounced with 3+ filters where tracking active state becomes cognitively demanding.
- **Evidence Tier**: Gold

---

### Finding 3: Promoted Filters Above the Product Grid Increase Mobile Filter Engagement

- **Source**: Baymard Institute. "Consider Promoting Important Filters (61% Don't)." https://baymard.com/blog/promoting-product-filters. Published November 2023. Usability benchmark: 61% of sites don't promote filters above the product grid.
- **Methodology**: Baymard usability testing of mobile filter discovery and engagement. Benchmark of 327+ sites for filter promotion implementation.
- **Key Finding**: Mobile users frequently don't realize filtering is available because the filter panel is hidden behind a "Filter" button. 40% of usability test subjects couldn't locate filter options (see search-and-filter-ux.md Finding 3). Displaying 2–4 high-priority filters as visual pills or thumbnail buttons above the product grid significantly improves filter discovery and engagement on mobile. This is especially valuable for category-specific filters (e.g., furniture shape thumbnails, apparel style pills, electronics storage-size pills) that users with a specific need would apply immediately.
- **E-Commerce Application**: Promoted filter implementation: (1) Select 2–4 most commonly used filters for the category; (2) Display above product grid as pill buttons or image thumbnails with product count: `Casual (142)` `Formal (67)` `Athletic (89)`; (3) On click: apply filter AND sync with the standard filter panel (they should be the same filter, just two entry points); (4) Show active state on pill when selected; (5) Still maintain the standard filter panel for the full filter set. Mobile prioritization: promoted filters are especially high-impact on mobile where the full filter panel is hidden.
- **Replication Status**: Consistent across Baymard's 2023 research. 61% gap in sites offering this feature represents a clear competitive differentiator.
- **Boundary Conditions**: Promoted filters add visual complexity to the category page header. For simple catalogs with few filter options, promoted filters may create redundancy. The promoted filter selection (which 2–4 filters to promote) requires category-level analysis of actual filter usage data.
- **Evidence Tier**: Gold

---

### Finding 4: Filter Value Counts Must Be Displayed — Especially with Faceted Filtering

- **Source**: Baymard Institute. Filter value count research. Category page filtering usability testing. https://baymard.com/research/ecommerce-product-lists (No free page-anchored URL with the specific claim; consistent with Baymard's premium Product Lists & Filtering guideline set.)
- **Methodology**: Usability testing with think-aloud protocol observing decision-making when filter option counts are and are not displayed.
- **Key Finding**: Showing product counts next to each filter value — "Red (47)" "Blue (32)" "Green (4)" — provides users with critical information for filter decision-making: (1) Is this filter option worth applying? (4 results may not be enough); (2) Will combined filters produce zero results? (users can avoid dead-end combinations); (3) Which is the most popular/available option? Dynamic count updates when other filters are applied allow users to understand the combinatorial filter effect in real time without applying and discovering zero results.
- **E-Commerce Application**: Filter count implementation: (1) Display counts next to every filter value in parentheses: `Red (47)`; (2) Update counts dynamically when other filters are applied (requires server-side faceted search or client-side filtering); (3) Hide (or grey out and disable) filter values with count = 0 — don't make users click an option that will return zero results; (4) Consider "Show 5 more" with total count for long filter lists (more than 7–8 visible options). For performance: pre-compute filter counts on the server and include in the initial page response; real-time dynamic counts require careful caching strategy.
- **Replication Status**: Consistent Baymard recommendation across multiple research rounds.
- **Boundary Conditions**: Dynamic count updates with complex faceted filtering can be computationally expensive at scale. For large catalogs (100K+ products), approximate counts (rounded to nearest 10) may be acceptable. For small catalogs (<1000 products), exact real-time counts are achievable.
- **Evidence Tier**: Silver *(audit 2026-04-21: downgraded from Gold — no free page anchor with specific claim)*

---

### Finding 5: Price Filter Requires Both Slider AND Manual Input Fields

- **Source**: Baymard Institute. Price filter UX research. Large-scale usability testing. https://baymard.com/blog/price-filter (No free page-anchored URL with the specific claim; consistent with Baymard's premium guideline set.)
- **Methodology**: Usability testing of various price filter implementations. Think-aloud protocol capturing user frustration with slider-only implementations.
- **Key Finding**: Range sliders alone are problematic for price filters: (1) Fine-grained selection is difficult on mobile (finger imprecision); (2) Accidental slider movement loses the user's intended range; (3) Users with specific budgets ($200 max) can't enter exact values; (4) Slider handles on mobile are frequently too small to hit accurately (below 44px touch target). Providing both a slider (for range visualization) AND manual input fields (for exact values) satisfies all user needs.
- **E-Commerce Application**: Price filter implementation: (1) Display a slider for visual range selection with the range indicator; (2) Pair with minimum and maximum input fields that show and accept exact values; (3) Slider movement updates the input fields in real-time; (4) Input field changes update the slider position; (5) Apply filter on input field blur (leaving the field) or with an explicit "Apply" button for custom ranges; (6) Show current range prominently: "Showing results $50 – $150"; (7) Mobile: ensure slider handles are minimum 44×44px touch target size (the handle, including padding). Do NOT update results on every slider drag move — update on release (mouse up / touch end) to prevent excessive API calls.
- **Replication Status**: Consistent Baymard recommendation. The slider-without-input failure is one of the most-cited filter UX anti-patterns.
- **Boundary Conditions**: For predefined price ranges ("Under $25" / "$25–$50" / "$50–$100" / "$100+") as alternatives to custom ranges: these work well alongside a slider for quick range selection, but should still include a "custom range" input option for users with specific budgets outside the predefined brackets.
- **Evidence Tier**: Silver *(audit 2026-04-21: downgraded from Gold — no free page anchor)*

---

### Finding 6: Mobile Filter Panel Must Be Full-Screen with Sticky Apply Button

- **Source**: Baymard Institute. Mobile filter panel UX research, premium guideline set. Consistent with industry-standard mobile ecommerce filter patterns. https://baymard.com/research/mcommerce-usability (NOTE: audit 2026-04-21 — the previously cited URL `baymard.com/blog/mobile-ecommerce-search-and-navigation` is a 2015 mobile navigation overview and does NOT discuss full-screen filter panels or sticky Apply buttons; that citation was removed.)
- **Methodology**: Large-scale mobile usability testing across 20+ major mobile ecommerce sites. Task-based testing of filter selection and application flows.
- **Key Finding**: Mobile filter panels that appear as partial overlays (covering half the screen) create problems: (1) Users lose context of the product grid; (2) Small tap targets in partial overlays increase selection errors; (3) Scroll conflicts between overlay and background. Full-screen filter panels (covering the entire viewport) are the most usable mobile pattern: they have full space for filter groups, clear back/close navigation, and no scroll conflicts. A prominent sticky "Show [N] results" button at the bottom of the full-screen panel reduces the "how do I see the results?" confusion that causes filter abandonment.
- **E-Commerce Application**: Mobile filter panel requirements: (1) Full-screen modal/drawer (not partial overlay); (2) "×" close button top-right and/or back arrow top-left; (3) Filter groups in scrollable list (within the full-screen panel); (4) Sticky "Show [N] results" CTA at bottom, dynamically updating count as filters are selected; (5) Applied filters summary visible at top of panel: "3 filters applied"; (6) Filter count badge on the "Filter" button in the category page header: "Filter (3)". The filter count badge is critical — it signals to users who return to the category page that filters are active.
- **Replication Status**: Consistent across Baymard mobile research. Full-screen filter pattern is the industry standard on major mobile ecommerce sites.
- **Boundary Conditions**: Full-screen filter works for vertical scrolling filter lists. For horizontal filter strips (1–3 filters displayed as horizontal pills at top of page, not behind a button): partial overlay interaction is acceptable since only a few options are shown.
- **Evidence Tier**: Silver *(audit 2026-04-21: downgraded from Gold — URL mismatch removed; claim retained as industry-consensus Silver)*

---

### Finding 7: Filter URL State Management — Required for Shareability and SEO

- **Source**: Baymard Institute. URL state research for category pages. Cross-referenced with Google Search Central technical documentation: https://developers.google.com/search/docs/crawling-indexing/crawling-managing-faceted-navigation *(updated URL — previous path /faceted-navigation returns 404; replaced with current canonical as of 2024-12)*
- **Methodology**: Baymard usability testing of filter state persistence across navigation. Google technical guidance on crawlable faceted navigation.
- **Key Finding**: Filter selections that don't update the URL create three user-experience problems: (1) Sharing filtered views is impossible (link sends recipient to unfiltered category); (2) Refreshing the page loses all filter selections; (3) Bookmarking filtered views fails. Additionally, some filtered views have SEO value and should be crawlable (e.g., "Women's Blue Dresses" is a valid landing page); URL parameters allow selective crawling. Google's 2024 guidance: use `&` as parameter separator; return HTTP 404 for zero-result facet combinations (not empty 200); use `rel="canonical"` and `rel="nofollow"` to control crawl budget.
- **E-Commerce Application**: URL state implementation: (1) Update URL on every filter change using `history.pushState()` or `history.replaceState()` — use push for navigable history (users can browser-back through filter states) or replace for non-navigable (back button exits filtering entirely); (2) URL format: `/category/dresses?color=blue&size=m&sort=price-asc`; (3) Filter params should be parseable on page load to restore filter state; (4) For SEO: decide which filter combinations merit crawlable pages vs. noindex treatment — canonical tags and robots directives manage crawl budget. Consult collection-page-architecture.md (if available) for SEO-specific faceted navigation strategy.
- **Replication Status**: Usability finding consistent across Baymard research. URL state is also a technical requirement for shareable/bookmarkable filtered views.
- **Boundary Conditions**: URL-based filter state requires server-side or client-side rendering that can parse URL params to initialize filter UI state. For JavaScript-heavy SPAs: ensure URL updates happen before any API calls (not after receiving results) so that the URL represents intent, not just current state.
- **Evidence Tier**: Gold

---

### Finding 8: Multi-Select vs. Single-Select Filter Values — Correct Logic By Filter Type

- **Source**: Baymard Institute. Filtering logic research. Category page usability testing. https://baymard.com/research/ecommerce-product-lists
- **Methodology**: Usability testing observing user mental models for filter combination behavior.
- **Key Finding**: Users have consistent (often implicit) expectations for filter combination logic: Color filter: OR logic ("Red OR Blue") — users want to see products in any of their selected colors, not only products that are somehow both. Size filter: OR logic within the filter ("Size M OR L OR XL"). Brand filter: OR logic within the filter ("Nike OR Adidas"). Price filter: AND logic (range — both min AND max apply simultaneously). Between-filter logic: AND ("Color: Blue AND Size: M" = products that are blue AND size M). User Rating minimum: AND logic (≥4 stars = only show products rated 4+ stars).
- **E-Commerce Application**: Implementation of correct filter logic: (1) Color, Size, Brand: multi-select checkboxes, OR logic within filter group; (2) Price: range slider/input, implicit AND logic (both bounds apply); (3) Rating: radio buttons or single-select minimum threshold (OR logic doesn't make semantic sense for ratings); (4) Boolean filters (In Stock, On Sale): single checkbox, AND logic with other filters. Communicate the logic to users with clear UI: checkboxes imply multi-select/OR; radio buttons imply single-select/AND; the label copy matters: "Any of these colors" vs. "Colors."
- **Replication Status**: Qualitative finding from Baymard usability testing. User mental models for filter logic are consistent across their research rounds.
- **Boundary Conditions**: Some advanced users want AND logic for colors ("show me products available in both red AND blue") — this is a niche use case not supported by most filter implementations and not expected by typical shoppers. B2B catalog filtering (where "product must meet specification A AND specification B") may have different logic expectations than consumer ecommerce.
- **Evidence Tier**: Silver

---

### Finding 9: Instant Apply vs. Manual Apply — Context Determines Which Is Better

- **Source**: Baymard Institute. Filter interaction pattern research. Desktop and mobile usability testing. https://baymard.com/research/ecommerce-product-lists
- **Methodology**: Comparative usability testing of instant-apply (results update immediately on filter selection) vs. manual-apply ("Apply Filters" button required) patterns.
- **Key Finding**: Desktop instant-apply (results update immediately as each filter is selected): Preferred for desktop because users can see live results and adjust without committing. Requires fast filter API response (<500ms) or progressive loading to feel smooth. Desktop with slow filter response or complex products: manual apply is better — prevents multiple API calls mid-selection. Mobile manual apply: generally preferred because: (1) Users tend to select multiple filters before wanting to see results; (2) Each filter change triggering a page update on mobile creates disorienting reloads; (3) The full-screen filter panel pattern naturally lends itself to "select all, then apply" flow.
- **E-Commerce Application**: Decision rule: (1) Desktop + filter API response <500ms → instant apply; (2) Desktop + filter API response >500ms → debounce 300ms then apply, or use manual apply button; (3) Mobile → always use manual apply with sticky "Show [N] results" CTA button; (4) For progressive enhancement: start with manual apply (works everywhere), then enhance to instant apply on desktop when API performance is confirmed adequate.
- **Replication Status**: Consistent Baymard recommendation based on usability testing across both patterns.
- **Boundary Conditions**: The API response time threshold (500ms) is approximate — test with your actual filter API to determine what "feels instant" vs. "feels slow" for your specific implementation.
- **Evidence Tier**: Silver

---

### Finding 10: "Show More / Show Less" Pattern for Long Filter Value Lists

- **Source**: Baymard Institute. Filter list length usability research. Category page benchmark. https://baymard.com/research/ecommerce-product-lists
- **Methodology**: Usability testing of filter groups with varying numbers of visible options.
- **Key Finding**: Showing all filter values simultaneously in a long scrollable list (10+ values) causes users to miss options at the bottom and makes the filter panel feel overwhelming. Showing only the top 5–7 values by default with a "Show [N] more" expansion mechanism allows quick access to most-used values while providing access to the full list. The default 5–7 values should be ordered by product count (most results first) or by convention (size XS, S, M, L, XL, XXL in natural order). Search-within-filter is valuable for filters with 15+ values (e.g., 50-brand multi-brand store).
- **E-Commerce Application**: Filter group display rules: (1) 1–7 values: show all; (2) 8–12 values: show 5–6 with "Show [N] more" link; (3) 13+ values: show 5–6 with "Show [N] more" AND add search-within-filter input (`<input type="search" placeholder="Search brands...">`); (4) "Show more" should be expandable/collapsible in the same panel (not a modal or new page); (5) After "Show more" is clicked, add "Show less" to collapse back. For size filters: show sizes in natural order (XS, S, M, L, XL, XXL, 2XL) regardless of count — users look for their specific size, not the most common.
- **Replication Status**: Consistent Baymard recommendation. The 5–7 default visibility rule appears across multiple Baymard publications.
- **Boundary Conditions**: Category-specific filter value ordering may differ from generic best practice. For boot sizes (women's 5–12, half sizes): size-natural order is essential. For price filters: no "show more/less" needed as there are no discrete values to hide.
- **Evidence Tier**: Silver

---

### Finding 11: Baymard 2024 Product Finding Research — 1,000+ Issues Across 219 Sessions (NEW)

- **Source**: Baymard Institute. "2024 Product Finding Research Launch." https://baymard.com/blog/product-finding-2024-launch. Published September 17, 2024.
- **Methodology**: 5,550+ hours of moderated usability testing across 219 user sessions on 12 major retailers (Best Buy, Gap, H&M, Nordstrom, etc.). Produced 160+ new or significantly revised UX guidelines; only 3% of prior guidelines changed, confirming long-term stability.
- **Key Finding**: Baymard's 2024 research surfaced 1,000+ usability issues across product-finding surfaces (category navigation, filtering, sorting, search). Only 3% of previous recommendations changed materially, supporting the durability of the older (2014–2018) benchmark data cited throughout this file. Notable reversals: Quick View now recommended for visually-driven products (previously discouraged); pagination "acceptable under certain conditions" (previously broadly discouraged).
- **E-Commerce Application**: When implementing filter/sort/product-finding UX, reference 2024+ Baymard guidelines for current benchmark percentages. Core principles (dual-location applied filters, 5 essential filters, filter value counts) are unchanged.
- **Replication Status**: Single Baymard study; however the 97% stability rate across prior guidelines is the key replication signal.
- **Boundary Conditions**: Baymard Premium required for full research access; this launch post is freely accessible with quoted key findings.
- **Evidence Tier**: Gold

---

### Finding 12: Google 2024 Faceted-Nav Crawling Guidance — 404 for Empty Results (NEW)

- **Source**: Google Search Central. "Managing crawling of faceted navigation URLs." https://developers.google.com/search/docs/crawling-indexing/crawling-managing-faceted-navigation. Companion blog: https://developers.google.com/search/blog/2024/12/crawling-december-faceted-nav (December 2024).
- **Methodology**: Official Google documentation on crawl-budget handling for faceted navigation.
- **Key Finding**: Google's 2024 guidance for ecommerce faceted navigation: (1) use `&` as parameter separator (NOT `,` `;` or brackets — crawlers struggle to detect these); (2) maintain consistent filter order when using path-based URLs (`/products/fish/green/tiny`); (3) return **HTTP 404** for zero-result filter combinations (not empty 200 — empty 200 wastes crawl budget); (4) block unneeded faceted URLs via robots.txt or URL fragments; (5) use `rel="canonical"` and `rel="nofollow"` strategically to consolidate signals and limit low-value crawling.
- **E-Commerce Application**: Audit facet URL handling on your store. Most headless Shopify/Next.js implementations default to 200 with empty grid on zero-result filter combinations — this is suboptimal per Google's 2024 guidance. Implement explicit 404 responses when a facet combination returns zero products. Enforce consistent parameter ordering in generated canonical URLs.
- **Replication Status**: Google developer documentation; reflects Google's crawl-handling policy as of December 2024. Replaces prior 2014 "best and worst practices" blog post.
- **Boundary Conditions**: The 404-for-empty rule helps large catalogs; minor impact on small-catalog stores where filter combinations rarely produce empty results.
- **Evidence Tier**: Silver (Google Developers, accessible, specific guidance with page anchor)

---

## Methodological Notes

- Baymard Institute's filtering research is the most comprehensive in ecommerce UX — 25+ rounds of qualitative testing, 4,400+ test sessions, 327+ site benchmark. It represents the gold standard for filtering UX guidance.
- The ECP's search-and-filter-ux.md contains 36 findings with significant coverage of filtering research — this file deliberately focuses on findings not fully covered there (promoted filters, dual display, price filter mechanics, mobile panel, show-more pattern).
- Filtering UX failure rates (84% of sites failing to provide good filtering) make this one of the highest-ROI optimization areas in ecommerce — the gap between current industry standard and best practice is large and addressable.
- **Audit note (2026-04-21)**: Several claims in this file depend on paywalled Baymard Premium content. Where no free page anchor exists for a specific numeric claim, the tier was downgraded to Silver per the Run B1 rubric. The core guidance is still sound and defensible.

---

## Sources Consulted

1. Baymard Institute. "E-Commerce Product Lists & Filtering." Published via Smashing Magazine (2015, updated). https://www.smashingmagazine.com/2015/04/the-current-state-of-e-commerce-filtering/
2. Baymard Institute. "Consider Promoting Important Filters." https://baymard.com/blog/promoting-product-filters
3. Baymard Institute. "7 Filtering Implementations That Make Macy's Best-in-Class." https://baymard.com/blog/macys-filtering-experience
4. Baymard Institute. "5 Essential Filter Types." https://baymard.com/blog/5-essential-filters
5. Baymard Institute. "Product Finding 2024 Research Launch." https://baymard.com/blog/product-finding-2024-launch
6. Baymard Institute. Research Hub. https://baymard.com/research/ecommerce-product-lists
7. Google Search Central. "Managing crawling of faceted navigation URLs." https://developers.google.com/search/docs/crawling-indexing/crawling-managing-faceted-navigation
8. ECP. search-and-filter-ux.md. references/search-and-filter-ux.md
