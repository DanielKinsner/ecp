<!-- RESEARCH_DATE: 2026-04-02 -->
<!-- AUDIT_RECONCILED: 2026-04-22 (Run-A + Run-B; Vera reconciler) -->
# Product Grid Layout: Research Findings

**Research Date**: April 2, 2026 (original); audit-reviewed April 21, 2026
**Domain**: Category UX — Product Grid Layout and Visual Hierarchy
**Total Findings**: 12 (original 9 + 3 added in audit)
**Methodology Note**: Product grid research draws from Hugo Jenkins' UsabilityHub study (2020, n=150 — small but frequently cited) and Baymard Institute's qualitative benchmarking. Eye-tracking findings from Nielsen Norman Group and Baymard that overlap with this domain are in eye-tracking-and-scan-patterns.md (ECP) — this file focuses on grid-specific layout decisions.

---

## Cross-Reference Notice

**ECP Reference Overlap**:
- eye-tracking-and-scan-patterns.md Finding 2 (F-pattern scanning) — directly affects grid layout attention distribution, covered there
- eye-tracking-and-scan-patterns.md Finding 4 (57% viewing time above fold) — covered there (also now added as Finding 10 here for grid-specific framing)
- eye-tracking-and-scan-patterns.md Finding 5 (80% fixations on left half) — covered there

This file covers: column count by viewport, card size effects on scanning speed, grid vs. list view, visual hierarchy within product cards, responsive breakpoints, and skeleton loading for grids.

---

## Summary

### Top 3 Most Impactful Findings

1. **Finding 1 (4-Column Maximum with Sidebar; 34% Slower Scanning at 5 Columns)**: Hugo Jenkins' UsabilityHub study found that going from 4 to 5 columns increases per-row scanning time by 34% (4.61s → 6.26s). The cognitive cost of evaluating more products per row is non-linear — 5 columns is a measurable degradation.
2. **Finding 2 (Larger Cards = 19% Faster Scanning)**: Scaling up card size (larger images, larger text) reduced per-row scanning time from 4.45s to 3.61s — a 19% improvement. Image size is the dominant factor in product evaluation speed.
3. **Finding 4 (Mobile: 2-Column Standard, 1-Column for Complex Products)**: 2-column grids are the mobile standard for visual products. 1-column for spec-heavy products (electronics, automotive parts) where per-item evaluation requires more space.

---

## Findings

### Finding 1: Never Exceed 4–5 Columns; Each Additional Column Beyond 4 Slows Scanning 34%+

- **Source**: Jenkins, H. (2020). "Size and layout of e-commerce product grids: a user research case study." Medium. https://medium.com/insights-observations/size-and-layout-of-e-commerce-product-grids-a-user-research-case-study-8a8307cbd087 (mirror if Medium consent-wall: https://prototypr.io/news/size-and-layout-of-e-commerce-product-grids-a-user-research-case-study-if-youre-in-e-commerce-the). UsabilityHub click testing, n=150.
- **Methodology**: Multi-variate click test on UsabilityHub platform with 150 participants (25 unique per variation across 6 tests). Tested 3, 4, and 5 column layouts at various card sizes. Measured average scanning time per row to find a specific product.
- **Key Finding**: Scanning time per row by column count: 3-column: 4.45s; 4-column: 4.61s (+3.6% vs. 3-col); 5-column: 6.26s (+35.7% vs. 4-col). The jump from 4 to 5 columns is the critical inflection point — a 35% increase in per-row scan time represents a disproportionate cognitive cost for a marginal space gain. The 5-column jump is worse than the 3-to-4 jump because smaller thumbnails at 5-column widths approach the minimum threshold for confident product evaluation.
- **E-Commerce Application**: Desktop with sidebar (filters visible): use 3–4 columns. Desktop without sidebar (full-width browse or search results): use 4–5 columns maximum, 4 preferred. Never use 6+ columns at any viewport width. Wide viewport (>1440px): use 4–5 columns with a defined maximum container width rather than allowing the grid to scale indefinitely. Provide a user-selectable 2-column "large view" option as an accessibility accommodation — some users need larger images for confident evaluation.
- **Replication Status**: Jenkins study n=150 is small; directional finding is consistent with Baymard's qualitative research on grid column guidelines. Not replicated by an independent large-scale study.
- **Boundary Conditions**: The optimal column count depends on image quality and card information density. High-quality, large images support 4 columns more effectively than low-quality small images. Categories requiring dense attribute comparison (e.g., industrial components) may benefit from a list-view default rather than pushing column count.
- **Evidence Tier**: Silver (UsabilityHub study, n=150; directionally consistent with Baymard)

---

### Finding 2: Larger Product Cards (Bigger Images) Reduce Scanning Time by 19%

- **Source**: Jenkins, H. (2020). Same UsabilityHub study as Finding 1. https://usabilityhub.com/
- **Methodology**: Scaling up product card size (larger images, larger text, more whitespace) vs. compact card layout. Measured scanning time per row at same column count (3-column).
- **Key Finding**: Larger card size (scaling up from compact to generous) reduced average scanning time from 4.45s to 3.61s — an 18.9% improvement. The scanning speed benefit from larger cards exceeds the benefit from reducing column count — a 3-column grid with large cards outperforms a 4-column grid with compact cards. The primary driver of the improvement is image size: users evaluate products through images, and larger images reduce the cognitive effort required per evaluation.
- **E-Commerce Application**: Prioritize image size within the grid over showing more products per row. Minimum recommended image display size: 250px wide on desktop (for 3–4 column grids on 1200px+ viewports). On mobile: 150px minimum for 2-column grids. Provide adequate whitespace between cards (minimum 12px gutter on mobile, 16–24px on desktop) — cramped grids negate the benefit of individual large images. If traffic data shows high bounce rate from category pages: first test image size (increase card size by 15–20%) before testing column count.
- **Replication Status**: Same study as Finding 1 — small n=150. Directional finding consistent with UI design principles (larger targets reduce cognitive load).
- **Boundary Conditions**: There is a practical upper limit — a 2-column grid on a large desktop monitor shows so few products per screen that discovery efficiency suffers despite per-item evaluation ease. The optimal is a balance: large enough to evaluate confidently, small enough to see multiple items for comparison.
- **Evidence Tier**: Silver

---

### Finding 3: Grid View Is Always Preferred for Visual Products; List View Adds Value for Spec-Heavy Products

- **Source**: Baymard Institute. Product list UX research on grid-vs-list view selection. Related (separate) finding: "2 Key Design Principles for Product Listing Information (64% Get at Least 1 Wrong)." https://baymard.com/blog/list-item-design-ecommerce — this page verifies the 64% attribute-consistency statistic but does NOT discuss grid vs. list view. The grid-vs-list preference finding is Baymard practitioner consensus without a single free page anchor.
- **Methodology**: Usability testing comparing grid and list view across different product categories. Analysis of user preference and task performance with view toggle.
- **Key Finding**: Grid view (image-dominant, cards in rows) is the universally preferred layout for visual products (apparel, furniture, home decor, jewelry) where appearance is the primary evaluation criterion. List view (horizontal product rows with larger text content area) adds value for spec-heavy products (electronics, auto parts, tools) where attribute comparison is the primary task. Offering a view toggle increases user satisfaction for mixed-catalog sites; defaulting to grid with a list option available is the correct pattern. On mobile: always default to grid; list view is rarely beneficial on small screens. Related Baymard stat: 64% of e-commerce sites fail to consistently display product list-item attributes across similar products, leading to abandonment (verified on cited URL).
- **E-Commerce Application**: View toggle implementation: (1) Default to grid for all categories; (2) Offer grid/list toggle for electronics, tools, automotive, and other spec-heavy categories; (3) Remember user preference in `localStorage` (persist within-session at minimum, persist cross-session if possible); (4) List view minimum requirements: small product image (100–150px), full product title, key specs (3–5), price, rating, add-to-cart button — in a horizontal row per product; (5) Mobile: suppress list view option or hide it — show grid toggle instead.
- **Replication Status**: Consistent across Baymard research rounds. Grid vs. list preference by product type is a stable finding.
- **Boundary Conditions**: B2B procurement catalogs with professional buyers who know exactly what they want often prefer list view as default — the use case differs from consumer discovery browsing. Reorder/repurchase scenarios favor list view. First-time discovery favors grid.
- **Evidence Tier**: Silver *(audit 2026-04-21: downgraded from Gold — the grid-vs-list claim does not have a dedicated free page anchor; the cited URL supports the separate 64% attribute-consistency stat)*

---

### Finding 4: Mobile Grid: 2 Columns Standard; 1 Column for Complex Products

- **Source**: Baymard Institute. Mobile product list UX research. https://baymard.com/research/mcommerce-usability Cross-referenced with Hugo Jenkins UsabilityHub study (mobile data). https://usabilityhub.com/ (No free page-anchored URL with the specific 2-column recommendation.)
- **Methodology**: Mobile-specific usability testing across multiple ecommerce sites. Observation of mobile product grid interaction patterns.
- **Key Finding**: 2-column mobile grid is the standard for visual consumer products — it provides images large enough for confident evaluation (~150–180px wide on a 375px viewport) while showing enough products per screen for discovery efficiency. 1-column mobile layout is appropriate for: (1) Complex spec products requiring wide text areas; (2) Very large product images where 2-column images are too small to evaluate (some jewelry, detailed accessories); (3) Accessibility-heavy contexts where larger tap targets are essential. Never use 3+ column mobile grids for products requiring image evaluation — the images are too small.
- **E-Commerce Application**: Mobile grid configuration: (1) Default: 2 columns with 12px gutter; (2) Image size in 2-column: approximately 160–180px on 375px viewport (accounting for padding and gutter); (3) Mobile 1-column: reserve for complex/tech products or if product has very high visual complexity requiring larger images; (4) Provide a mobile grid density toggle (2-column / 1-column) for user preference on sites where this distinction matters. CSS: `grid-template-columns: repeat(2, 1fr)` with appropriate gap.
- **Replication Status**: Consistent across Baymard mobile research. 2-column mobile is industry standard across major ecommerce platforms.
- **Boundary Conditions**: Tablet breakpoint (768–1024px): 3 columns with sidebar or 2 without sidebar is typical. Portrait tablet can use 2–3 columns; landscape tablet can use 3–4 columns. Test on actual devices at each breakpoint — viewport-based CSS doesn't account for device-specific rendering differences.
- **Evidence Tier**: Silver *(audit 2026-04-21: downgraded from Gold — no free page anchor)*

---

### Finding 5: Consistent Card Heights Across Grid Rows Prevent Visual Confusion

- **Source**: Baymard Institute. Product list visual consistency research. CSS Grid spec: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout (MDN — W3C-adjacent).
- **Methodology**: Qualitative usability research on grid visual consistency. CSS technical specification for behavior.
- **Key Finding**: Inconsistent card heights (caused by varying product title length, different badge combinations, or inconsistent image aspect ratios) break grid row alignment, creating a "ragged" visual pattern that disrupts scanning rhythm. CSS Grid's `align-items: stretch` forces equal height cards within rows; flexbox requires `align-items: stretch` on the row container. The product image must be the fixed-height element that anchors card consistency — all variable-length text elements (titles, descriptions) must be truncated to a maximum line count.
- **E-Commerce Application**: Consistent card height implementation: (1) Fixed-height image container: `aspect-ratio: 1/1` (square) or `aspect-ratio: 3/4` (portrait for apparel) with `object-fit: cover`; (2) Product title: `display: -webkit-box; -webkit-line-clamp: 2; overflow: hidden;` (2-line max, CSS line clamp); (3) Price area: fixed height, accommodate original + sale price in same space; (4) Badge area: fixed height (1 badge maximum visible height); (5) CSS Grid container: `display: grid; align-items: stretch;` — grid rows align all cards to tallest card in row automatically; (6) Do NOT use JavaScript height equalization — CSS Grid handles this natively.
- **Replication Status**: Technical and qualitative combined finding. CSS Grid consistency behavior is technically validated.
- **Boundary Conditions**: `object-fit: cover` crops images to fill the container — ensure product images are photographed with sufficient padding from the subject edges to prevent unacceptable cropping on different aspect ratio products. For products where full-product visibility is critical (jewelry, small accessories): use `object-fit: contain` with consistent background color, accepting the letterbox appearance for full product visibility.
- **Evidence Tier**: Silver *(audit 2026-04-21: downgraded from Gold — no Baymard free page anchor for the visual-consistency claim; MDN supports the CSS mechanics but not the usability finding)*

---

### Finding 6: Out-of-Stock Products Should Appear Last in Grid, Not Hidden or First

- **Source**: Baymard Institute. Out-of-stock product placement research. Category page merchandising usability testing. https://baymard.com/research/ecommerce-product-lists (No free page-anchored URL with the specific claim.)
- **Methodology**: Usability testing observing user reactions to out-of-stock product placement strategies.
- **Key Finding**: Three strategies tested for out-of-stock products: (1) Hide completely: users feel products have disappeared; those with bookmarks are confused; SEO implications of URL removal; (2) In-position with out-of-stock badge: maintains context but wastes prime grid real estate with unconvertable products; (3) Moved to end of list with out-of-stock indicator: the recommended strategy — maintains product visibility for "notify me" functionality and user reference while preserving prime positions for in-stock products. A fourth pattern (in-position but dimmed, greyed out) is acceptable if "Notify Me" functionality is present.
- **E-Commerce Application**: Out-of-stock product display: (1) Algorithmically push OOS products to end of category page product list (after all in-stock products); (2) Display with "Out of Stock" badge overlay; (3) Dim the product image to 60–70% opacity (visual signal that it's unavailable); (4) Show "Notify Me When Available" button instead of "Add to Cart"; (5) Do NOT hide entirely — users reference products they've seen before; (6) For products returning to stock: remove OOS treatment immediately on restock trigger. For low-stock (1–5 units): display in normal position with "Only X left" badge to signal scarcity authentically.
- **Replication Status**: Consistent Baymard recommendation. The "end of list" pattern is the industry standard on major ecommerce platforms.
- **Boundary Conditions**: For categories with high OOS rates (>30% of products OOS): consider filtering out OOS by default with a toggle to "Include out of stock" — when the majority of visible products are OOS, the grid looks sparse and unconvincing. For product types where the OOS product remains a valid reference (finding a comparable in-stock product): keep OOS visible.
- **Evidence Tier**: Silver *(audit 2026-04-21: downgraded from Gold — no free page anchor)*

---

### Finding 7: Category Page Above-Content Area Must Not Push Products Below Fold

- **Source**: Baymard Institute. Category page header UX research. Usability testing of above-product-grid content. https://baymard.com/research/ecommerce-product-lists (No free page-anchored URL with the specific 300px/200px thresholds.) Quantitative support via NNGroup above-fold attention data — see Finding 10 below.
- **Methodology**: Usability testing with eye-tracking observing user behavior when products are pushed below the fold by category headers.
- **Key Finding**: Users come to category pages to see products. Content above the product grid (category description, promotional banners, subcategory navigation tiles, editorial content) that pushes all products below the fold causes disorientation and high bounce rates in usability testing. Users expect to see products immediately on category page load. The recommended maximum above-grid content height is approximately 300px on desktop, 200px on mobile — enough for a brief title, optional small promotional element, and subcategory pills, but not a full editorial banner. NNGroup data: 57% of viewing time is spent above the fold (see Finding 10) — content there is disproportionately valuable.
- **E-Commerce Application**: Category page above-grid content limits: (1) Category h1 heading: always; (2) Short category description (1–2 lines, optional): for SEO value, keep it brief; (3) Promoted filter pills (2–4): yes, these help; (4) Small promotional banner (max 200–250px height on desktop): only if there's a strong business reason; (5) Subcategory navigation pills: yes if the category has meaningful subcategories. Never: hero-image-style full-viewport category banners on category pages; long editorial copy above products; multiple stacked promotional elements. Test the "above-fold position" for products on your actual category pages using DevTools device simulation at 375px mobile — if zero products are visible above fold on mobile, the above-grid content is excessive.
- **Replication Status**: Consistent Baymard research finding across multiple benchmark rounds. Supported by NNGroup above-fold data.
- **Boundary Conditions**: "New Arrivals" or editorial collection pages with an intentional browse-and-inspire format may appropriately place lifestyle imagery above products — this is a different page type from a standard category page. Standard category/collection pages should prioritize immediate product visibility.
- **Evidence Tier**: Silver *(audit 2026-04-21: downgraded from Gold — no page anchor for specific 300/200 thresholds)*

---

### Finding 8: Skeleton Loading for Product Grids Reduces Perceived Wait Time and Prevents Layout Shift

- **Source**: Nielsen Norman Group. "Skeleton Screens 101." https://www.nngroup.com/articles/skeleton-screens/. Published June 4, 2023. Cross-referenced with Google Core Web Vitals CLS guidance.
- **Methodology**: NNGroup synthesis of prior skeleton vs. spinner research. NNG article: "spinners are typically best used on a single module, like a video or a card... Skeleton screens are better when the full screen is loading." For waits <10s either works; progress bars needed for >10s.
- **Key Finding**: For category page grid initial load: skeleton cards (card-shaped placeholders with shimmer animation) prevent layout shift and signal to users that products are loading rather than the page being broken. The skeleton cards must match the final grid card structure: image area (correct aspect ratio), 2-line title placeholder, price placeholder. Skeletons that don't match final card layout create layout shift when real content loads — potentially worsening perceived performance rather than improving it. (Note: the oft-cited "20–30% perceived speed improvement" figure is practitioner synthesis, NOT from the NNG article itself.)
- **E-Commerce Application**: Grid skeleton loading: (1) Generate N skeleton cards (where N = products per initial page load) with correct dimensions when a page loads; (2) Skeleton image area: same aspect ratio as real product cards; (3) Shimmer animation: `@keyframes shimmer { from { background-position: -200% 0; } to { background-position: 200% 0; } }` with `background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%)` — this is more effective than static grey; (4) Replace skeleton cards with real product cards as they load, using opacity transition (no layout shift if dimensions match); (5) For filtering state changes (applying a filter): show skeleton for the product grid area while new results load.
- **Replication Status**: NNGroup synthesis resolves contradictory prior studies. The key insight (fidelity to final layout is the determining factor, not skeleton vs. spinner choice) is well-supported.
- **Boundary Conditions**: Skeleton benefit is strongest when load time is 1–4 seconds. For sub-second loads, no loading state is needed. For loads >5 seconds: supplement skeleton with a progress indicator or count ("Loading 48 of 142 products"). For SSR/SSG pages: the grid renders with real content from the server — skeleton loading is not needed.
- **Evidence Tier**: Silver

---

### Finding 9: New Product Discovery Requires Algorithmic Intervention — Position Bias Suppresses New Arrivals

- **Source**: Baymard Institute. Category page merchandising research. https://baymard.com/research/ecommerce-product-lists Cross-referenced with merchandising-psychology.md.
- **Methodology**: Analysis of algorithmic sorting behavior and its effect on new product visibility. Cross-reference with industry merchandising platform documentation (Algolia, Constructor.io).
- **Key Finding**: Pure algorithmic sorting (by sales velocity, conversion rate) systematically buries new products because they lack historical performance data. Position 1–20 in a category receive 2–3× more clicks than positions 21+, meaning new products buried in position 50+ receive negligible organic discovery. Without intervention, new products can be trapped in a discovery vacuum: no position → no clicks → no sales data → always poor position.
- **E-Commerce Application**: New product discovery mechanisms: (1) "New Arrivals" section on category page (highlighted subsection or separate filter/sort option); (2) Algorithm rule: products added within last 30 days receive a fixed position boost to positions 5–15 (above fold on desktop, visible within first scroll on mobile); (3) Featured/pinned positions: manually fix 2–4 strategically important products in top positions via merchandising rules; (4) "New" badge on products within 30 days of catalog addition (automated via `created_at` timestamp); (5) Rotate "New Arrivals" spotlight: on page refresh or next visit, show different new products in featured positions to maximize exposure across visits. Measure: track click-through rate and conversion rate for new products at week 1, 2, 4 post-addition. If position is suppressing discovery, adjust boost rules.
- **Replication Status**: Position bias in click-through is well-established (Google search, ecommerce studies). Algorithm suppression of new products is a known failure mode documented by merchandising platform providers.
- **Boundary Conditions**: Position boosting for new products should be time-limited (30–60 days) to prevent perpetual occupation of top positions by products that don't convert after adequate exposure. If a new product receives boosted position for 30 days and still doesn't convert, the product may not resonate with your audience — position intervention doesn't fix a product-market fit problem.
- **Evidence Tier**: Silver

---

### Finding 10: NNGroup Above-Fold Attention — 57% of Viewing Time (NEW)

- **Source**: Nielsen Norman Group. "Scrolling and Attention." https://www.nngroup.com/articles/scrolling-and-attention/. Eye-tracking and scroll-behavior research.
- **Methodology**: NNGroup eye-tracking research synthesizing studies across years.
- **Key Finding**: Users spend **57% of page-viewing time above the fold** (down from 80% in 2010 as page designs lengthened); 74% within the first two screenfuls. There is a "sharp decrease in attention following the fold" — content below the fold gets seen but is materially less attended to.
- **E-Commerce Application**: Quantifies the structural rationale for Finding 7. Ensure at least the first row of product cards renders within the initial viewport on both desktop and mobile. For a 1080×1920 desktop with 80px global nav: products must begin before y=600px. For a 375×812 iPhone viewport with 60px nav: products must begin before y=350px.
- **Replication Status**: NNG's eye-tracking research is widely cited. The 57% figure is from 2018 NNG data; the downward trend from 80% (2010) is consistent with longer page design norms.
- **Boundary Conditions**: The above-fold percentage depends on page type and scroll behavior expectations. Category pages with clear "products below" affordances can pull more attention below the fold than marketing pages with unclear content structure.
- **Evidence Tier**: Gold

---

### Finding 11: Touch Targets — 44×44pt (Apple) / 48×48dp (Material) Minimum for Tappable Card Elements (NEW)

- **Source**: Apple Human Interface Guidelines — Layout. https://developer.apple.com/design/human-interface-guidelines/layout. Google Material Design — Accessibility. https://m3.material.io/foundations/accessible-design/accessibility-basics. WCAG 2.2 Success Criterion 2.5.8 (Target Size, Minimum) — absolute floor at 24×24 CSS pixels.
- **Methodology**: Platform vendor guidelines for touch-target sizing; WCAG AA baseline requirement.
- **Key Finding**: Interactive elements within product cards (favorite/heart, quick-view button, size-pill selector, add-to-cart CTA, color swatch) must meet platform-minimum tappable sizes: Apple HIG = 44×44 points; Material Design = 48×48 dp. WCAG 2.2 AA requires a 24×24 CSS-pixel floor. Undersized tap targets generate mistaken taps on the adjacent product card (navigating the user away from the grid unexpectedly) and frustrate thumb-based mobile browsing.
- **E-Commerce Application**: Audit every interactive element in product cards on actual mobile devices. "Quick Add" buttons that look clickable at 32px will generate phantom card-clicks. Color swatches at 20px are effectively untappable on mobile — bump to 32–40px minimum with sufficient spacing. Include invisible padding around small visual elements to reach minimum tap target: a 20px heart icon with 12px padding on each side meets the 44pt Apple minimum.
- **Replication Status**: Official platform vendor documentation. WCAG 2.2 Success Criteria are W3C-ratified.
- **Boundary Conditions**: The 44pt / 48dp guidelines are mobile-specific. Desktop with precise cursor targeting can use smaller targets (though WCAG AA 24px still applies). Dense grid designs must reserve sufficient whitespace between cards to prevent mistap even when individual targets meet minimum size.
- **Evidence Tier**: Silver (Apple/Google developer docs + W3C WCAG — all accessible, specific, with page anchors)

---

### Finding 12: Core Web Vitals CLS ≤0.1 — Grid Card Dimensions Must Be Pre-Reserved (NEW)

- **Source**: web.dev. "Cumulative Layout Shift (CLS)." https://web.dev/cls/ (verified 2026-04-21). Google Core Web Vitals: https://web.dev/vitals/.
- **Methodology**: Google Core Web Vitals specification; CrUX field data.
- **Key Finding**: "Good" CLS per Core Web Vitals is **0.1 or less**; poor is >0.25. Product grids that load images without reserved dimensions (missing `aspect-ratio` CSS or explicit `width`/`height` attributes) produce visible layout shifts as images replace unset placeholders. CLS is one of three Core Web Vitals directly tied to Google ranking signals.
- **E-Commerce Application**: Implementation: (1) Every product card image must declare `aspect-ratio` CSS OR explicit `width`/`height` HTML attributes; (2) Skeleton placeholders (Finding 8) must reserve identical dimensions to final content; (3) Lazy-loaded images (`loading="lazy"`) still need dimension reservation; (4) Measure CLS via CrUX (field data) in Google Search Console, not only Lab via Lighthouse — field data reflects real user experience across devices and network conditions; (5) Dynamically inserted badges, price strikethroughs, or stock messages must also reserve space or be animated within their own layout-isolated box (CSS `contain`).
- **Replication Status**: Google's Core Web Vitals thresholds are platform policy. The 0.1 threshold is based on Chrome UX Report data aggregation across millions of real pages.
- **Boundary Conditions**: CLS applies primarily to initial page load and user-unexpected shifts. User-initiated layout shifts (e.g., clicking "Show more" to expand a description) are exempt from the metric if they occur within 500ms of a discrete user action.
- **Evidence Tier**: Silver (web.dev is Google Developers tier per rubric; URL verified, specific numeric threshold)

---

## Methodological Notes

- Hugo Jenkins' UsabilityHub study (2020) is small (n=150) but is the only controlled study specifically measuring column count effect on scanning time. Treat the specific numbers as directionally reliable rather than precisely accurate.
- Baymard's qualitative research provides the strongest grid layout guidance through usability observation across 4,400+ test sessions. However, many specific Baymard guideline thresholds (200–300px max header, 2-column mobile default) do not have free page-anchored URLs — they live in paywalled Baymard Premium guideline content. Per the Run B1 rubric, these findings have been downgraded to Silver.
- Eye-tracking findings that affect grid layout attention distribution are covered in ECP's eye-tracking-and-scan-patterns.md — specifically F-pattern scanning, left-side attention bias, and above-fold attention concentration. These are critical complements to the structural grid findings here. Finding 10 brings the 57% above-fold figure into this file for direct grid-layout framing.

---

## Sources Consulted

1. Jenkins, H. (2020). "Size and layout of e-commerce product grids: a user research case study." Medium. https://medium.com/insights-observations/size-and-layout-of-e-commerce-product-grids-a-user-research-case-study-8a8307cbd087
2. Baymard Institute. Product Lists UX Research Hub. https://baymard.com/research/ecommerce-product-lists
3. Baymard Institute. "2 Key Design Principles for Product Listing Information." https://baymard.com/blog/list-item-design-ecommerce
4. Nielsen Norman Group. "Mobile Navigation: Image Grids or Text Lists?" https://www.nngroup.com/articles/image-vs-list-mobile-navigation/
5. Nielsen Norman Group. "Skeleton Screens 101." https://www.nngroup.com/articles/skeleton-screens/
6. Nielsen Norman Group. "Scrolling and Attention." https://www.nngroup.com/articles/scrolling-and-attention/
7. web.dev. "Cumulative Layout Shift (CLS)." https://web.dev/cls/
8. Apple Human Interface Guidelines — Layout. https://developer.apple.com/design/human-interface-guidelines/layout
9. Google Material Design — Accessibility. https://m3.material.io/foundations/accessible-design/accessibility-basics
10. MDN. CSS Grid Layout. https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout
11. ECP. eye-tracking-and-scan-patterns.md. references/eye-tracking-and-scan-patterns.md
