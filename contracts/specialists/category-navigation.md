# Category Navigation Specialist (v2)

Per-cluster parameter file for the **category-navigation** specialist. Combined with the shared template body in [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) and per-engagement variables (cluster-context path, baton path, screenshots), this file produces the final dispatch prompt.

Audit scope: collection and category pages as the primary surface, plus search bar, breadcrumbs, and recommended-category widgets wherever they appear — including PDPs and the homepage.

## Parameters

```yaml
cluster: category-navigation
references:
  - search-and-filter-ux
  - filtering-ux
  - grid-layout
  - merchandising-psychology
  - pagination-patterns
  - product-cards
  - sorting-psychology
  - zero-results
  - breadcrumbs
  - collection-page-architecture
surface_vocabulary:
  - search-bar
  - filter-panel
  - sort-control
  - product-grid
  - product-card
  - breadcrumb
  - pagination
  - zero-results
  - subcategory-tiles
  - applied-filters
target_finding_count: 4-7
```

The 10 reference files are sourced from [`contracts/cluster-routing.md`](../cluster-routing.md) "The 10 clusters" table for the category-navigation row. All 10 live at `${CLAUDE_PLUGIN_ROOT}/references/<file>.md`.

## Cluster guidance

The block below renders into the template at the `{{cluster_guidance}}` slot.

```
## Cluster guidance — category-navigation

Your audit surface is everything that helps a visitor find, navigate, and evaluate products at the category level: collection pages, search results pages, filter and sort controls, the product grid, product cards within that grid, breadcrumbs, zero-results states, and pagination or infinite-scroll loading mechanics. Bias toward the patterns below.

### Search bar placement and design

- The search box must be visible at page top, not hidden behind an icon-only toggle on any site with more than 50 products (search-and-filter-ux.md Finding 17 — NNGroup Gold). Check width against typical query length: a box that clips after 15 characters fails users editing queries.
- On mobile, a persistent or sticky search entry point is the standard pattern. Audit whether scrolling the category page hides the search bar entirely.
- Autocomplete quality matters as much as presence. Baymard benchmarking shows 36% of autocomplete implementations do more harm than good (search-and-filter-ux.md Finding 6). Check whether suggestions are relevant, tolerant of one-character misspellings, and visually clear.

### Filter availability and placement

- The five essential filters (Price, User Rating, Color, Size, Brand) must all be present when applicable. Only 43% of sites offer all five — missing any causes users to conclude the store cannot help them (filtering-ux.md Finding 1, Gold). Audit each category: if the page sells visual products, Color is non-optional; if it sells apparel or footwear, Size is non-optional.
- 40% of users cannot locate filter options at all (search-and-filter-ux.md Finding 3, Gold). On desktop, verify the filter panel is in the left sidebar and visually prominent. On mobile, check that the "Filter" button is labeled clearly and carries a badge ("Filter (3)") when filters are active.
- Promoted filters above the product grid — 2–4 pill buttons for the most-used filters in that category — increase mobile filter engagement. 61% of sites don't offer this (filtering-ux.md Finding 3, Gold). Check whether the category page surfaces any promoted filter pills or thumbnail buttons above the grid.
- Applied filters must be shown in two locations simultaneously: as removable chips above the product grid AND as checked/highlighted options in the filter panel. 42% of sites display applied filters in only one location (filtering-ux.md Finding 2, Gold). Evaluate both locations; note if either is missing or out of sync.
- Filter value counts ("Red (47)") reduce the risk of dead-end filter combinations. Absence is a Silver-tier finding especially when the catalog is large (filtering-ux.md Finding 4).
- Price filter requires both a slider and manual input fields. Slider-only implementations frustrate mobile users who need to enter exact budgets (filtering-ux.md Finding 5, Silver).
- On mobile, the filter panel should be full-screen with a sticky "Show [N] results" button at the bottom (filtering-ux.md Finding 6, Silver). Partial-overlay filter panels on mobile are a common failure.
- Multi-select filter logic must be correct: Color/Size/Brand use OR logic (any selected values show); Price uses AND logic (both bounds apply simultaneously) (filtering-ux.md Finding 8, Silver).

### Sorting

- The default sort must be a diversity-based "Relevance" or curated "Featured" that samples across price points and product types. 24% of sites fail this by defaulting to Highest Price, Newest, or arbitrary order — causing premature abandonment when first visible products misrepresent the category (sorting-psychology.md Finding 1, Gold; also verified in merchandising-psychology.md Finding 2).
- Sort and filter controls must be visually and spatially separated. Users routinely confuse them in testing, using filters as a sort proxy (sorting-psychology.md Finding 6, Gold). The sort control should be a single-select dropdown on the right side of the results header; filter controls should be in the sidebar (desktop) or behind a dedicated button (mobile).
- "Bestselling" as a default activates the conformity heuristic and is appropriate for sale pages and high-homogeneity categories. "Newest First" as a default is a finding when used on broad category pages where it misrepresents catalog breadth (sorting-psychology.md Findings 2–3).
- Price sort must use the effective (sale) price, not original price. Mis-sorted price results cause immediate distrust (sorting-psychology.md Finding 5, Silver).
- "Biggest Discount" sort should be present on sale and clearance pages. Its absence on a promotional page is a medium finding (sorting-psychology.md Finding 14, Silver).

### Product grid layout

- Desktop column count: 3–4 columns with a visible filter sidebar; never exceed 5. Scanning time increases 35% going from 4 to 5 columns (grid-layout.md Finding 1, Silver — Jenkins 2020). On mobile, the standard is 2 columns for visual products; 1 column only for spec-heavy items that require wide text areas.
- Product cards must have consistent heights per row. Inconsistent aspect ratios from varying image sizes or badge combinations disrupt scanning rhythm. The image container must use a fixed aspect ratio (1:1 or 3:4) with `object-fit: cover` (grid-layout.md Finding 5, Silver).
- Category page header content must not push all products below the fold. Maximum above-grid content height: ~300px desktop, ~200px mobile, accounting for global navigation. If zero product cards are visible above the fold on mobile, the header is excessive (grid-layout.md Finding 7, Silver; merchandising-psychology.md Finding 4, Silver).
- NNGroup eye-tracking: 57% of page-viewing time is spent above the fold. At least one full row of product cards must render within the initial viewport (grid-layout.md Finding 10, Gold).
- Out-of-stock products should appear at the end of the grid with a visual indicator, not in their algorithmic position (grid-layout.md Finding 6, Silver). Check for greyed-out images and "Notify Me" CTAs on OOS cards.

### Product cards

- Review rating and review count must be visible on cards. 270% higher purchase likelihood with even 5 reviews vs. 0 (product-cards.md Finding 1, Gold — Spiegel/Northwestern). Display format: star graphic + numeric rating + count, e.g., "★★★★☆ 4.6 (128 reviews)."
- Price is a pass/fail decision made within 1–2 seconds. The effective price must be the primary visible number; sale framing should show original price with strikethrough (product-cards.md Finding 4, Silver).
- Touch targets for interactive card elements (wishlist icon, color swatches, quick-add) must meet 44×44pt (Apple HIG) minimum on mobile. Most mobile cards fail this (product-cards.md Finding 8, Gold; also WCAG 2.2 SC 2.5.8 minimum 24×24px).
- Color swatches on cards must update the card image when tapped. Unsynced swatches that require a PDP visit to see the color are a medium finding (product-cards.md Finding 9, Silver).
- Social proof badges ("Best Seller," "New," "Sale") increase click-through but must be limited to 1–2 per card. More than 2 badges eliminate the signal (product-cards.md Finding 7, Silver; merchandising-psychology.md Finding 5, Silver). Audit whether badge placement is consistent (top-left of image, typically) and data-driven (not inflated).

### Merchandising and position effects

- Products in the first 1–2 grid rows receive 2–3× more clicks than later positions (merchandising-psychology.md Finding 1, Silver; position-bias primary: Joachims et al. 2005, Gold). Treat the first 8–20 positions as editorial merchandising decisions, not neutral algorithm outputs. Evaluate whether the visible first row represents the category's breadth or is homogeneous/dominated by a single product type or price point.
- New products need a position boost or explicit intervention to escape algorithm suppression (merchandising-psychology.md Finding 7, Silver). Check whether new arrivals appear in the first two scrollable sections or are buried.
- If three product tiers appear at top positions, evaluate for compromise-effect framing: does the middle tier naturally draw the eye? (merchandising-psychology.md Findings 11–12, Gold — Huber 1982, Simonson 1989).
- Subcategory navigation tiles above the grid help users self-route on large categories (4+ distinct subcategories, 20+ products each). Their absence on a large parent-category page is a medium finding (merchandising-psychology.md Finding 8, Silver).

### Pagination and loading

- "Load More" + progressive lazy-loading outperforms both pure pagination and pure infinite scroll for browsing category pages (pagination-patterns.md Finding 1, Gold — Baymard Smashing 2016). Evaluate which pattern the page uses and whether it matches the guidance.
- Infinite scroll on a search results page is a specific harm, not merely suboptimal: it encourages mindless scrolling through degrading relevance rather than query refinement (pagination-patterns.md Finding 5, Gold). Note the page type — this finding applies to search results, not category browse.
- Infinite scroll that blocks footer access is an accessibility failure (pagination-patterns.md Finding 3, Gold — NNGroup/Deque). Check whether the footer is reachable without disabling JavaScript.
- Scroll position must be preserved on back navigation from PDP. Users who browse a filtered category, click a product, and return to find themselves at page top with all loaded products lost will abandon. This is one of the most consistently cited e-commerce UX failures (pagination-patterns.md Finding 9, Silver; breadcrumbs.md Finding 3, Silver).
- "Showing [N] of [Total] products" progress indicators reduce abandonment and should appear on the page (pagination-patterns.md Finding 10, Silver — goal-gradient effect, Nunes & Dreze 2006, Gold).
- SEO-critical: numbered pagination must use crawlable `<a href>` links even when infinite scroll or "Load More" is used for the UX layer. Googlebot cannot reliably access JavaScript-only loaded content (collection-page-architecture.md Finding 4, Gold).

### Zero-results states

- Nearly 50% of e-commerce sites fail to provide effective recovery paths on zero-results pages (zero-results.md Finding 1, Gold). When the page has a search bar, test a nonsense query to check what the zero-results page shows. Minimum acceptable: preserved query in search box, related categories, alternative product suggestions.
- Filter-induced zero results need a different treatment than search-induced zero results. Users who over-filter need targeted filter relaxation options ("Remove 'Under $50' to see 3 products"), not a generic empty-state page (zero-results.md Finding 9, Silver).
- Zero-results messaging tone matters. Cold mechanical messages ("No results found") test negatively. Client-framed messages ("We couldn't find [query] — let us help") reduce abandonment (zero-results.md Finding 15, Gold — NNGroup heuristics).
- "Search tips" as the primary or sole zero-results response are a finding — they test as accusatory and unhelpful (zero-results.md Finding 8, Gold).

### Breadcrumbs

- Ecommerce requires two breadcrumb types simultaneously: hierarchy ("Home > Women > Dresses") and history ("← Back to Cocktail Dresses (47)"). 68% of sites fail to implement both (breadcrumbs.md Finding 1, Gold). Check on PDPs: is the hierarchy breadcrumb present? Is a "Back to results" link preserving the filter state the user arrived with?
- History breadcrumbs must preserve filters, sort order, and scroll position. Clicking a hierarchy breadcrumb that resets all applied filters is among the most frustration-generating failures in category navigation testing (breadcrumbs.md Finding 2, Gold).
- BreadcrumbList schema markup is a functional SEO element. Two independent SearchPilot controlled tests confirm that removing breadcrumbs costs -5.5% to -7% organic traffic (breadcrumbs.md Findings 9–10, Gold). Check source for JSON-LD markup or equivalent.
- On mobile, a single "← [Parent Category]" pattern is the most usable for PDPs. Full hierarchy trails must use horizontal scrolling with 44px+ touch targets on each level, or a collapsed "..." expander (breadcrumbs.md Finding 5, Silver).

### Edge cases

- **PDPs and homepages:** Search bar, breadcrumbs, and recommended-category navigation widgets are in scope for this cluster wherever they appear on the page — not only on collection pages. A PDP missing both breadcrumb types is an in-scope finding. A homepage with a hidden search icon instead of a visible input is an in-scope finding.
- **Single-brand or small-catalog stores.** A Brand filter is not needed on a single-brand store. Fewer than 50 products may not justify autocomplete or a dedicated "Load More" button. Calibrate severity accordingly — skip Brand filter as a finding when the store is single-brand, and suppress pagination findings if total products fit on a single load.
- **Sale or clearance pages.** "Best Selling" or "Biggest Discount" sort defaults are appropriate here. A diversity-based "Relevance" default finding does not apply to a page where the page's commercial model is discount-first.
- **Search results pages vs. category browse pages.** Infinite scroll is a FAIL on search results but only a PARTIAL on category browse. Label which page type you are evaluating and apply the correct failure criterion.
- **Compatibility-dependent catalogs (auto parts, electronics accessories).** Compatibility filters are the primary conversion lever when products require fitment data. Their absence is a HIGH severity finding, not MEDIUM (search-and-filter-ux.md Finding 5, Gold — 65% task failure without compatibility filters).
- **B2B and quote-only pages.** Standard consumer filter/sort guidance is relaxed; alphabetical sort and list-view defaults are appropriate; discovery-browse findings may not apply. Emit `status: "skipped"` or note the B2B context in your findings if the page is clearly trade/procurement oriented.

### When to emit PASS findings

A clean category-navigation setup is one where: the search bar is visible and wide enough for real queries; all five essential filters are present and discoverable; applied filters display in both the sidebar and chips above the grid; the default sort showcases category breadth; the product grid defaults to 3–4 columns on desktop and 2 on mobile with consistent card heights; at least one product row is visible above the fold; breadcrumbs implement both hierarchy and history types; and the zero-results page provides at least three recovery paths. Emit PASS findings naming the specific elements that work — the synthesizer uses them in the Priority Path Bundle narrative.
```

## Reference file list (rendered into template)

For substitution into `{{reference_file_list}}`:

```
- `search-and-filter-ux.md` — overarching filter/search UX quality benchmarks, choice overload, autocomplete, and merged sort/filter psychology findings
- `filtering-ux.md` — five essential filters, dual applied-filter display, promoted filters above grid, price filter mechanics, mobile full-screen panel, multi-select logic
- `grid-layout.md` — column count and scanning speed, card size effects, mobile 2-column standard, above-fold product visibility, skeleton loading, CLS
- `merchandising-psychology.md` — position primacy effects, default sort diversity, hybrid algorithmic + manual merchandising, badge psychology, decoy/compromise effects, subcategory tiles
- `pagination-patterns.md` — Load More vs. infinite scroll vs. pagination, search-results-specific scroll harm, accessibility failures, scroll position preservation, progress indicators, SEO-safe dual-layer architecture
- `product-cards.md` — review display, price formatting, touch target requirements, color swatches, badge limits, card height consistency, wishlist buttons
- `sorting-psychology.md` — default sort diversity, position bias, price sort correctness, sort/filter visual separation, rating sort weighting, bestselling social proof, discount-percentage sort
- `zero-results.md` — recovery strategies (related categories, alternative suggestions, personalized recs, contact options, popular products), filter-induced vs. search-induced zero results, messaging tone, search tips as harmful response
- `breadcrumbs.md` — two breadcrumb types (hierarchy + history), filter-state preservation, browser back-button behavior, mobile patterns, BreadcrumbList schema, SEO impact controlled tests
- `collection-page-architecture.md` — click depth, hub-and-spoke taxonomy, breadcrumb SEO impact, pagination crawlability, SEO text strategy, category vs. product page traffic, anchor text, faceted navigation URL management
```

## Cross-references

- [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) — shared template body this file parametrizes
- [`contracts/cluster-routing.md`](../cluster-routing.md) — canonical reference list source for this cluster's row
- [`schema/cluster-emission-v1.json`](../../schema/cluster-emission-v1.json) — output shape
- [`schema/finding-v1.json`](../../schema/finding-v1.json) — per-finding shape
- [`scripts/test-specialist.py`](../../scripts/test-specialist.py) — harness that combines this file + template + per-engagement vars
