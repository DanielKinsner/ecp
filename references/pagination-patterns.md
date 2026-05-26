<!-- PRODUCTION FILE FOLLOWS — apply all decisions above -->

# Pagination Patterns in E-Commerce: Research Findings

<!-- RESEARCH_DATE: 2026-04-02 -->
<!-- RECONCILED: 2026-04-21. Auditors: Run A (researcher-navigation) + Run B (opus-4.7). Reconciler: opus-4.7-reconciler. -->
<!-- CHANGES: F3 dates fixed (NNGroup Sep 2022, Deque Oct 2019); F3 Nike.com ref removed; F4 Gold→Silver; F5 URL + stat fix; F8 NNGroup 2023 added; F9 Gold→Silver; F11 rel=prev/next deprecated; F12 Gold→Silver; F15 new (Nunes & Dreze); F16 new (Baymard 2024). -->

**Research Date**: April 2, 2026; reconciled April 21, 2026
**Total Findings**: 16 (original 14 + 2 added in audit)
**Methodology**: Web-based literature review of Baymard Institute usability testing, Nielsen Norman Group research, academic studies on loading patterns, and practitioner case studies. Cross-referenced against CRO/search-filter reference data.

---

## Summary

### Top 3 Most Impactful Findings

1. **Finding 1 (Baymard Load More)**: "Load More" + progressive lazy-loading outperforms both pure pagination and pure infinite scroll on e-commerce category pages. Users browse more products than with pagination, evaluate individual items more carefully than with infinite scroll, and the footer remains accessible — addressing three distinct failure modes in a single pattern.
2. **Finding 5 (Search Results Infinite Scroll)**: Infinite scroll on search results pages is specifically harmful, not merely suboptimal. Because search results are relevance-sorted, scrolling mindlessly through degrading results is the wrong user behavior to encourage. Users should refine queries, not exhaust them.
3. **Finding 9 (Scroll Position Preservation)**: Failure to preserve scroll position on back navigation is one of the most consistently cited e-commerce UX failures across both NNGroup and Baymard research programs. Users who navigate to a product detail page and return to find themselves at page top — with products reloaded — abandon browsing sessions. The state management investment is non-negotiable.

---

## Findings

### Finding 1: Load More + Lazy-Loading Outperforms Both Pagination and Infinite Scroll
- **Source**: Baymard Institute. "Infinite Scrolling, Pagination Or 'Load More' Buttons? Usability Findings In eCommerce." Published as guest post on Smashing Magazine, March 2016. https://www.smashingmagazine.com/2016/03/pagination-infinite-scrolling-load-more-buttons/ Based on Baymard's Product Lists & Filtering research study.
- **Methodology**: Large-scale usability testing across 50+ e-commerce sites, multi-year study program. Qualitative usability sessions with think-aloud protocol. Supplemented by quantitative benchmarking of leading e-commerce sites across hundreds of UX guidelines.
- **Key Finding**: "Load More" buttons combined with lazy-loading produce the most seamless user experience for e-commerce category pages. Users browse more products than with pagination (lower friction to see more), focus more on individual items than with infinite scroll (natural pause points), and retain access to the footer (no blocking content stream). Specific benchmarks from the Smashing 2016 article: only **8% of the top 50 US e-commerce sites** use the Load More approach; **>90% of sites** that do use Load More get back-button navigation wrong; test subjects with infinite scroll scrolled through **more than twice as many products** as with pagination on mobile.
- **E-Commerce Application**: Implement a hybrid pattern: (1) Load 15-30 products initially; (2) Lazy-load an additional batch as the user scrolls; (3) Display a "Load More" button after a threshold (50-100 products); (4) On click, load the next batch and resume lazy-loading. Cycle repeats. This maximizes product exposure without the attention-diffusion problems of pure infinite scroll.
- **Replication Status**: Baymard has re-benchmarked multiple times (2016, 2019, 2022+) with consistent findings. NNGroup independently recommends against infinite scroll for e-commerce (see Finding 3). This is strong practitioner consensus, though not independently replicated in a peer-reviewed academic setting. See Finding 16 for Baymard's 2024 update, which refines (but does not reverse) this finding.
- **Boundary Conditions**: Recommendation applies specifically to category/collection pages with browsing intent. Search results pages require a different pattern (see Finding 5). Small catalogs (<30 products) don't need lazy-loading at all. B2B catalogs with known-item purchase intent may benefit from traditional pagination.
- **Evidence Tier**: Gold

---

### Finding 2: Traditional Pagination Causes Users to Browse Significantly Less of the Catalog
- **Source**: Baymard Institute, same study as Finding 1. Published via Smashing Magazine, March 2016. URL: https://www.smashingmagazine.com/2016/03/pagination-infinite-scrolling-load-more-buttons/
- **Methodology**: Usability testing with behavioral observation. Users were observed during product-finding tasks across sites with different pagination implementations.
- **Key Finding**: Users browsed significantly fewer products with traditional pagination than with infinite scroll or "Load More" patterns. More than a handful of pagination links visually discouraged continued browsing. Users spent more time evaluating page 1 results (deeper evaluation, less catalog exposure). Clicking "page 2" felt like a significant effort compared to scrolling.
- **E-Commerce Application**: Traditional pagination should not be the primary browsing mechanism for category pages with discovery intent. Its appropriate use cases are: (1) SEO-critical pages that need unique crawlable URLs at each page level; (2) catalogs where users need precise position tracking (e.g., "I was on page 3"); (3) B2B product sheets with predictable re-purchase behavior. When using pagination for SEO reasons, layer a progressive disclosure UI on top for users (see Finding 11). Note: Baymard's 2024 research (see Finding 16) revised pagination from "broadly discouraged" to "acceptable under certain conditions" — the use cases above align with the 2024 guidance.
- **Replication Status**: Consistent with Baymard's multi-year testing and NNGroup's independent usability research on scrolling vs. pagination. No peer-reviewed academic replication with controlled effect size measurement.
- **Boundary Conditions**: Pagination may actually perform better for goal-oriented known-item searches. The penalty is specifically in exploratory, discovery-mode browsing. Desktop vs. mobile effects differ — pagination is relatively less harmful on desktop where clicking feels more natural.
- **Evidence Tier**: Gold

---

### Finding 3: Infinite Scroll Creates Inaccessible Footers and Screen-Reader Failures
- **Source**: Nielsen Norman Group. "Infinite Scrolling: When to Use It, When to Avoid It." Published **September 4, 2022** *(audit correction: previously cited as "January 2024" — not supported on live page)*. URL: https://www.nngroup.com/articles/infinite-scrolling-tips/ Also: Deque. "Infinite Scrolling & Role=Feed Accessibility Issues." Published **October 2, 2019** *(audit correction: previously cited as "December 2025" — Deque article date verified)*. URL: https://www.deque.com/blog/infinite-scrolling-rolefeed-accessibility-issues/
- **Methodology**: NNGroup usability testing and expert review. Deque accessibility auditing across real-world web implementations.
- **Key Finding**: Infinite scroll prevents users from reaching footer content — contact information, return policies, help links, cross-navigation. The constant stream of new items pushes the footer below practical reach. Additionally, screen reader users in browse/reading mode may not recognize when they've exhausted a finite feed and may miss the footer region entirely. The Deque article identifies specific populations harmed by infinite scroll implementations: keyboard-only users, speech recognition users, less experienced screen reader users, switch-device users, low-vision users, cognitive-disability users, and mobile users. Most implementations do not correctly apply ARIA `role="feed"`, which is the designated accessibility mechanism for infinite feeds.
- **E-Commerce Application**: Infinite scroll fails e-commerce categorically because: (1) Footer inaccessibility blocks critical support/return pathways; (2) Screen reader accessibility requires ARIA `role="feed"` implementation plus supplementary patterns that most teams don't execute correctly; (3) Back-navigation state preservation is complex. Reserve infinite scroll for: social feeds (Twitter/X, Instagram), news articles, and content-browsing contexts where footer access is unimportant and content is temporally ordered.
- **Replication Status**: Consistent across NNGroup, Deque, Baymard, and practitioner research. No peer-reviewed quantitative study, but the accessibility failures are objectively verifiable via WCAG audit.
- **Boundary Conditions**: If infinite scroll is architecturally mandated, mitigation requires: sticky footer access (persistent bottom bar), `role="feed"` implementation plus a toggle to disable infinite scroll, explicit keyboard focus management on new content injection. This adds substantial engineering overhead that negates the simplicity argument for infinite scroll.
- **Evidence Tier**: Gold

---

### Finding 4: Infinite Scroll Increases Scanning Rate, Decreasing Per-Product Evaluation Quality
- **Source**: Baymard Institute, Product Lists & Filtering research. Referenced in multiple Baymard publications (2016-2022); directionally supported by https://www.smashingmagazine.com/2016/03/pagination-infinite-scrolling-load-more-buttons/ The specific eye-tracking and attention-diffusion claim originates in Baymard's paywalled research study and does not have a verbatim free URL anchor.
- **Methodology**: Eye-tracking and behavioral observation across e-commerce usability sessions.
- **Key Finding**: Infinite scroll caused users to scan products more rapidly and superficially compared to pagination or "Load More" patterns. First products still received relatively high attention, but the absence of pause points meant users never stopped to compare, evaluate, or form clear preferences. In contrast, pagination's page-break forces an evaluation decision (scroll on, or click to next page), and "Load More" provides optional explicit pause points.
- **E-Commerce Application**: For high-consideration products (electronics, appliances, apparel where fit matters), the per-product evaluation quality drop with infinite scroll is a conversion threat. For low-consideration products (consumables, commodities with pure price competition), infinite scroll's higher breadth exposure may be acceptable. Apply "Load More" pattern to all but the lowest-consideration categories.
- **Replication Status**: Consistent across Baymard's testing rounds. The attention-diffusion finding aligns with general attention research on continuous vs. discrete content streams.
- **Boundary Conditions**: The evaluation quality gap depends heavily on product complexity. Simple products (one attribute, obvious quality signals) are less affected. Complex products with many differentiating attributes (technical specs, fit requirements) are most affected.
- **Evidence Tier**: Silver *(audit 2026-04-21: downgraded from Gold — specific eye-tracking claim lacks free page anchor; Smashing 2016 URL supports directional finding only)*

---

### Finding 5: Infinite Scroll on Search Results Pages Is Specifically Harmful
- **Source**: Baymard Institute. Multiple publications on Search UX. Primary reference: "Infinite Scrolling, Pagination Or 'Load More' Buttons?" Smashing Magazine, March 2016. https://www.smashingmagazine.com/2016/03/pagination-infinite-scrolling-load-more-buttons/ Quote verified: "infinite scrolling should never be used for search results." Article also cites Etsy's A/B test that "documented a significant hit to the search experience" from infinite scroll on search.
- **Methodology**: Large-scale usability testing specifically on search results page interaction patterns.
- **Key Finding**: Baymard characterizes infinite scroll on search results pages as "downright harmful to usability — in particular, for search results and on mobile." The reason: search results are relevance-sorted — earlier results are better matches than later ones. Infinite scroll encourages users to mindlessly scroll through degrading results rather than refining their query. This is the behavioral opposite of what leads to conversion: a refined, specific query that returns high-relevance results.
- **E-Commerce Application**: Search results pages must use a different pattern from category pages: (1) Load 25-75 products initially (enough to establish relevance, not so many as to replace refinement); (2) NO lazy-loading; (3) "Load More" button only — never auto-load; (4) Prominently show result count ("Showing 48 of 2,847 results") to anchor the user's sense of how much there is; (5) Filter/refine controls should be visually dominant — the right next action is refinement, not scrolling. Cross-reference: search-and-filter-ux.md Finding 7 (~50% of "No Results" pages fail to provide effective recovery pathways) — search UX failures compound each other.
- **Replication Status**: Strong Baymard consensus. Directionally consistent with information retrieval research showing that users who refine queries find relevant items faster. Etsy A/B test cited as real-world corroboration in the Smashing article.
- **Boundary Conditions**: Sites with small catalogs (<200 searchable items) may not see this pattern manifest — if all results fit on one page, the distinction is moot. The harm scales with catalog size and result count.
- **Evidence Tier**: Gold

---

### Finding 6: Scroll Bar Position Is Used as a Progress Indicator — Lazy-Loading Breaks This
- **Source**: Baymard Institute. Product Lists & Filtering research. Also: Friedman, V. "Infinite Scroll UX Done Right: Guidelines and Best Practices." Smashing Magazine, March 30, 2022. https://www.smashingmagazine.com/2022/03/designing-better-infinite-scroll/ (discusses scrollbar reliability as an infinite-scroll UX problem and recommends scrollbar enhancements as mitigation).
- **Methodology**: Usability testing with behavioral observation and think-aloud protocol. Practitioner synthesis (Friedman 2022) for scrollbar-specific discussion.
- **Key Finding**: Users use the browser scroll bar as a proxy for how far they've browsed through a list. When lazy-loading dynamically extends page height, the scroll bar "jumps" — the position the user thought was 70% through the catalog suddenly becomes 40%. This is disorienting and breaks the mental model of progress. Additionally, footers briefly appear and then get pushed back down as new content loads, confusing users. Friedman (Smashing 2022) recommends "scrollbar enhancements" including dynamic position labels as mitigation.
- **E-Commerce Application**: Reserve total expected page height in advance: calculate (remaining_products × estimated_row_height) and set a min-height on the grid container via JavaScript. Content fills the reserved space as it loads, keeping the scroll bar accurate throughout. This is a non-obvious but critical detail for implementing lazy-loading without disorienting users.
- **Replication Status**: Observational finding from Baymard usability sessions. Not independently quantified with effect sizes, but consistent across sessions and corroborated by Friedman's 2022 practitioner synthesis.
- **Boundary Conditions**: If total product count is unknown (e.g., cursor-based pagination API), approximate the height estimate. Even a rough approximation is better than dynamic jumping. On mobile, the scroll bar is often invisible anyway — the impact is reduced but the footer-exposure problem persists.
- **Evidence Tier**: Silver

---

### Finding 7: Initial Product Count Should Vary by Product Complexity
- **Source**: Baymard Institute. Product Lists & Filtering research. https://baymard.com/research/ecommerce-product-lists Ranges referenced in Smashing 2016 article (10-30 initial products; "Load More" after 50-100 items). https://www.smashingmagazine.com/
- **Methodology**: Cross-category usability testing observations on optimal initial loads across product types.
- **Key Finding**: No single initial product count is optimal across all product types. Visual/apparel products tolerate faster scanning and benefit from larger initial grids (20-30 products). Spec-driven products (electronics, appliances) require more per-item evaluation time and benefit from smaller initial loads (10-20 products) that invite comparison. Mixed catalogs fall in between (15-24 products).
- **E-Commerce Application**: Set initial load count by category type, not site-wide. Use a 3-column grid for apparel/home (24-30 products), 2-column for electronics/high-consideration (12-18 products). Include product count in the UI ("Showing 24 of 142 products") so users calibrate their expectations. Update count dynamically as more products load.
- **Replication Status**: Practitioner guideline synthesized from Baymard testing, with ranges directionally reflected in Smashing 2016. Not independently validated with quantitative conversion measurements.
- **Boundary Conditions**: Mobile initial loads should always be at the lower end of the range — 10-20 products — due to smaller viewport and higher data-cost sensitivity. The ranges apply to desktop.
- **Evidence Tier**: Silver

---

### Finding 8: Skeleton Screens Improve Perceived Load Performance vs. Spinners
- **Source**: Luke Wroblewski's industry publication on skeleton screens, 2015 (original). Also: Kovacs, G., Mejtoft, T., & Söderström, U. (2018). "The effect of skeleton screens: Users' perception of speed and ease of navigation." ACM / ResearchGate. https://www.researchgate.net/publication/326858669 *(HTTP 403 — paywalled, but paper metadata verifiable; DOI available via ACM)*. Also: Nielsen Norman Group. "Skeleton Screens 101." Published June 4, 2023. https://www.nngroup.com/articles/skeleton-screens/
- **Methodology**: Crowdsourced studies comparing spinner vs. skeleton screen vs. "false front page" representations of loading states. Behavioral and attitudinal measures.
- **Key Finding**: Skeleton screens (greyed-out layout placeholders matching the eventual content structure) are perceived as faster than equivalent loading times with spinners or blank pages. Users remain oriented about what's loading and where, reducing uncertainty and frustration. NNGroup 2023 guidance adds nuance: "Spinners are typically best used on a single module loading within a page; skeleton screens are better when the full screen is loading." For waits under 10 seconds, either can work; for waits over 10 seconds, progress bars are preferred over either. Note: The commonly cited 20-30% perceived-speed improvement figure is practitioner synthesis, not a specific claim in either the NNGroup 2023 or Kovacs 2018 publications.
- **E-Commerce Application**: During initial page load AND during "Load More" product loading, use skeleton product cards rather than spinners. Match the skeleton shape to your actual product card dimensions (same aspect ratio, same grid columns). Animate with a shimmer/wave effect (left-to-right gradient) to signal active loading. Do not use spinners as the primary loading indicator in the product grid.
- **Replication Status**: The Kovacs et al. (2018) study provides empirical support. The 20-30% perception improvement figure is practitioner synthesis rather than a single rigorous RCT. NNGroup endorses skeleton screens as a best practice with the nuance described above.
- **Boundary Conditions**: Skeleton screens are most valuable for structured, repeated-element UIs (product grids, list views). They are less valuable for freeform or unpredictable layouts. The perception benefit diminishes if actual load time exceeds ~3 seconds — at that point, users need more informative progress feedback (progress bars for >10s per NNGroup 2023).
- **Citation Status**: ResearchGate URL returns HTTP 403 (paywalled) — Kovacs 2018 primary verifiable via paper metadata and ACM DOI.
- **Evidence Tier**: Silver

---

### Finding 9: Failure to Preserve Back-Navigation Scroll Position Is a Major Conversion Killer
- **Source**: Nielsen Norman Group. Usability research on back-navigation behavior in e-commerce. Referenced in NNGroup's E-Commerce UX report series (13 volumes, 1,073 design guidelines — paywalled). Baymard Institute: Mobile and desktop product list navigation research. https://baymard.com/research/ecommerce-product-lists *(research landing page; specific "top-10 failure" framing is from paywalled Baymard study)*.
- **Methodology**: Usability testing and expert review of back-button behavior across e-commerce implementations.
- **Key Finding**: Users who navigate from a category page to a product detail page and then press Back expect to return to exactly their previous scroll position, with previously loaded products still visible. When the category page reloads from scratch — starting at the top, losing the loaded products, resetting filters — users experience significant frustration and frequently abandon browsing. This is especially severe for "Load More" implementations where 60+ products had been loaded before the PDP visit.
- **E-Commerce Application**: Use the Browser History API to save full state before PDP navigation: scroll position, loaded product count, applied filters, active sort order. On popstate (back navigation), restore all four parameters without a server round-trip. For SPA implementations, this is typically handled by router-level scroll restoration configuration. For multi-page apps, use sessionStorage to persist state across page loads. Test specifically: browse → load more products × 2 → click product → back → verify scroll position and product count preserved.
- **Replication Status**: Consistent finding across both NNGroup and Baymard research programs, and is one of the most consistently cited e-commerce UX failures. Behaviorally intuitive — users have a strong expectation of positional continuity.
- **Boundary Conditions**: Some mobile browsers (Safari on iOS) handle scroll restoration differently and may require additional handling. The complexity increases with server-side rendering approaches. Ensure the solution works for the specific tech stack (Shopify, Next.js, Nuxt, etc. each have different implications).
- **Evidence Tier**: Silver *(audit 2026-04-21: downgraded from Gold — specific "top-10 most-cited" framing lacks free URL verification; underlying finding is well-supported but the ranking claim is from paywalled sources)*

---

### Finding 10: Progress Indicators ("Showing X of Y") Reduce Abandonment During Browse Sessions
- **Source**: Baymard Institute. Product Lists & Filtering research. https://baymard.com/research/ecommerce-product-lists Behavioral-psychology primary: Nunes & Dreze (2006) — see Finding 15 for full citation and methodology.
- **Methodology**: Baymard usability observations combined with broader behavioral psychology literature on goal-gradient effects.
- **Key Finding**: Showing users their progress through a catalog ("Showing 24 of 142 products") anchors their mental model and motivates continued browsing. Users who don't know how many products exist don't know whether they've seen a representative sample or a tiny fraction. The goal-gradient effect predicts that users near the "end" of a defined set will accelerate their evaluation (see Finding 15 for the foundational field-experiment evidence). Undefined-length sets (pure infinite scroll) don't create this motivational gradient.
- **E-Commerce Application**: Always display current count and total: "Showing [N] of [Total] products." Update dynamically as more products load. On the "Load More" button itself, show the next increment: "Load 24 more (118 remaining)." On the progress bar (optional), visually represent how much of the catalog has been seen. This single element serves double duty: expectation-setting AND motivation to continue browsing.
- **Replication Status**: The goal-gradient effect is well-established in behavioral psychology (Nunes & Dreze, 2006: Journal of Consumer Research — Finding 15). Its direct application to product list browsing is via Baymard's observational research, not a controlled experiment.
- **Boundary Conditions**: Works best when the total product count is known in advance and relatively small (<500). Very large result sets (2,000+ products) may actually discourage browsing by making the task feel endless — in that case, pair with strong filter promotion to help users narrow to a manageable set.
- **Evidence Tier**: Silver

---

### Finding 11: SEO-Safe Implementation Requires Paginated URL Structure Behind Progressive UX
- **Source**: Nielsen Norman Group. "Infinite Scrolling: When to Use It, When to Avoid It." Published September 4, 2022. https://www.nngroup.com/articles/infinite-scrolling-tips/ Google Search Central: "Managing crawling of faceted navigation URLs." https://developers.google.com/search/docs/crawling-indexing/crawling-managing-faceted-navigation *(current canonical as of December 2024)*.
- **Methodology**: SEO analysis and Google Search Central documentation review. NNGroup UX guideline synthesis.
- **Key Finding**: Search engine crawlers cannot reliably access content revealed via JavaScript lazy-loading or infinite scroll. Content that is not present in the initial HTML response or accessible via paginated URLs may not be indexed. The solution: maintain a paginated URL structure (`/category/shoes`, `/category/shoes?page=2`) as the canonical structure that crawlers can follow, while layering a progressive/lazy-loading UX on top for human users. **Note on `rel="prev"` / `rel="next"`: Google announced in March 2019 that these link relations are no longer used for indexing or ranking. They may still serve user-agent and screen-reader navigation in some implementations, but they should not be relied upon as SEO signals.** Google's current guidance recommends returning HTTP 404 for zero-result facet combinations and using `&` as the URL parameter separator.
- **E-Commerce Application**: Implement dual-layer architecture: (1) Server renders initial 24-30 products at page load (crawlable); (2) Server provides paginated next-page URLs accessible as anchor tags when JavaScript is disabled (crawlable); (3) JavaScript enhances the experience with lazy-loading and "Load More" (user-facing). Use self-referencing canonical tags on each paginated URL (each page has unique content and its own canonical). On filtered/sorted variants, canonical points to the unfiltered base URL. Do **not** rely on `rel="prev"` / `rel="next"` for SEO. Test: disable JavaScript in browser → all products should still be accessible via pagination.
- **Replication Status**: SEO behavior is documented by Google Search Central. The dual-layer recommendation is practitioner consensus. The `rel=prev/next` deprecation was announced by Google in March 2019.
- **Boundary Conditions**: Google has improved its JavaScript crawling capability over time, but paginated fallback remains the safest approach. This adds backend complexity and is particularly important for category pages where SEO traffic is significant. Pure SPAs (no SSR) should use dynamic rendering or SSR to solve this.
- **Evidence Tier**: Gold
- **Audit Note (2026-04-21)**: Updated to reflect Google's 2019 deprecation of `rel=prev/next` as indexing signals. Previous version recommended these tags as active SEO signals.

---

### Finding 12: Mobile Initial Loads Should Be Smaller Than Desktop
- **Source**: Baymard Institute. Mobile Commerce UX research (4,400+ usability testing sessions). Directionally supported by: https://baymard.com/blog/mobile-ecommerce-search-and-navigation *(specific 10-20 / 20-30 product count thresholds are from Baymard's paywalled Product Lists study; the blog URL supports the general mobile-smaller principle)*.
- **Methodology**: Large-scale moderated mobile usability testing with behavioral observation and think-aloud protocol.
- **Key Finding**: Mobile users are more sensitive to initial page load time than desktop users (higher data cost sensitivity, lower battery, intermittent connectivity). Mobile viewport shows fewer products per screenful (typically 1-2 columns vs. 3-4 on desktop). Recommendation: start with 10-20 products on mobile (vs. 20-30 on desktop), load smaller batches (10-20 per lazy-load or "Load More"), and show progress prominently. The "Load More" button must be visually prominent on mobile — easily tappable (44px+ touch target) and not hidden below many products.
- **E-Commerce Application**: Implement device-specific initial loads via server-side user-agent detection or responsive configuration. Sticky "Showing X of Y" counter helps mobile users track progress during longer browse sessions. "Back to top" button becomes critical for mobile sessions with 50+ loaded products.
- **Replication Status**: Consistent with Baymard's mobile commerce research program. Directionally aligned with Web Vitals guidance on mobile performance.
- **Boundary Conditions**: Device detection based on user agent is imprecise (tablets, fold phones). Screen width breakpoints may be a more reliable proxy for initial load sizing.
- **Evidence Tier**: Silver *(audit 2026-04-21: downgraded from Gold — specific product-count thresholds lack free URL verification; directional claim well-supported)*

---

### Finding 13: "Load More" Button Text and Design Affects Click Rate
- **Source**: Practitioner research synthesis from CRO case studies. Referenced in multiple conversion optimization reviews (2021-2024). Original Baymard Product Lists guidelines on "Load More" button implementation. https://baymard.com/research/ecommerce-product-lists
- **Methodology**: A/B testing case studies across e-commerce implementations. Practitioner meta-analysis.
- **Key Finding**: "Load More" button performance improves when: (1) the button shows how many more products will load ("Load 24 More Products"); (2) it appears at a natural browsing pause point (after the user has seen enough to want more, not too soon); (3) it is visually distinct from product cards but not visually overwhelming; (4) remaining count is shown ("118 more to explore"). "Show More" and "Load More" both test well; "Next Page" underperforms (implies pagination, not continuation).
- **E-Commerce Application**: Use: "Load [N] More Products ([X] Remaining)" or "Show More ([X] Left)." Position after the 3rd grid row initially, then after each additional grid section. Do not make the button sticky (it interferes with product browsing). Style with secondary button treatment — present but not dominant.
- **Replication Status**: Synthesized from practitioner A/B testing reports. No single peer-reviewed study. Effect sizes vary by site, product type, and initial load configuration.
- **Boundary Conditions**: Optimal button text varies by catalog personality. Fashion sites may prefer "Discover More." Utilitarian sites may prefer "Load More." Test in context.
- **Evidence Tier**: Bronze

---

### Finding 14: Auto-Load Threshold Should Account for Product Grid Row Height
- **Source**: Baymard Institute. Product Lists & Filtering — implementation guidelines. https://baymard.com/research/ecommerce-product-lists Engineering best practices synthesis.
- **Methodology**: Practitioner guidance derived from usability observations about scroll behavior.
- **Key Finding**: Lazy-loading should trigger before the user reaches the current bottom of loaded content, not at the bottom itself. Optimal auto-load trigger: when the user is 1-2 product rows from the current bottom of the loaded grid. This creates a seamless experience where new products appear just before the user needs them. Triggering too early (half-page up) wastes bandwidth on products the user may not reach; triggering too late (at the bottom) creates a jarring pause before content appears.
- **E-Commerce Application**: Implement using IntersectionObserver API targeting a sentinel element placed 2 grid rows above the current grid bottom. Calculate trigger distance: (grid_row_height × 2) pixels from bottom of loaded content. This typically works out to 400-600px on desktop, 200-400px on mobile.
- **Replication Status**: Engineering best practice derived from Baymard implementation guidelines. No independent quantitative validation.
- **Boundary Conditions**: Network latency affects optimal trigger distance — slow connections need an earlier trigger (further from bottom). For 3G/4G mobile connections, trigger at 3-4 rows from bottom.
- **Evidence Tier**: Bronze

---

### Finding 15: Nunes & Dreze Endowed-Progress Effect — Foundational Primary for Finding 10 (NEW)
- **Source**: Nunes, J. C., & Dreze, X. (2006). "The Endowed Progress Effect: How Artificial Advancement Increases Effort." *Journal of Consumer Research*, 32(4), 504–512. <https://doi.org/10.1086/500480>
- **Methodology**: Field experiment at a car wash with loyalty-card stamp programs. Two conditions: (A) 8-stamp card with 0 stamps filled vs. (B) 10-stamp card with 2 stamps pre-filled — identical 8 stamps required to earn the reward. N=300+ customers. Measured redemption rate and time-to-redemption.
- **Key Finding**: Customers given the "pre-filled" 10-stamp card (endowed with artificial progress toward the same goal) redeemed at **34%** vs. **19%** for the 0-of-8 card — nearly double the redemption rate despite identical objective effort required. Customers with the endowed-progress card also completed it faster. This is the foundational evidence for the goal-gradient / endowed-progress effect: perceived proximity to a goal increases effort allocation, even when objective distance is unchanged.
- **E-Commerce Application**: Finding 10's "Showing X of Y" pattern leverages this effect — showing "12 of 142 products" quietly anchors users against the total and motivates continued browsing. Stronger framings that emphasize progress ("You've seen 12 of 142 — 130 more to explore") may intensify the endowed-progress pull. The mechanism applies broadly: onboarding completion meters, loyalty-point visualization, checkout step counters, and filter progress indicators all activate the same effect.
- **Replication Status**: Published in Journal of Consumer Research (peer-reviewed). The goal-gradient concept originates with Hull (1932) and has been extensively studied in behavioral economics and psychology. Nunes & Dreze provide the most-cited modern field-experiment evidence.
- **Boundary Conditions**: The effect requires a credible goal. Gamed or manipulative progress indicators that users detect as artificial can backfire through reactance. For very large product sets (2,000+ products), the goal may feel unreachably far even with "X of Y" framing — see Finding 10 boundary condition for mitigation (pair with filter promotion).
- **Evidence Tier**: Gold *(Journal of Consumer Research primary; peer-reviewed field experiment; DOI verified)*

---

### Finding 16: Baymard 2024 Product Finding Research — Pagination Stance Revised (NEW)
- **Source**: Baymard Institute. "2024 Product Finding Research Launch." https://baymard.com/blog/product-finding-2024-launch Published September 17, 2024.
- **Methodology**: 5,550+ hours of moderated usability testing across 219 user sessions on 12 major retailers (Best Buy, Gap, H&M, Nordstrom, and others). Produced 160+ new/revised UX guidelines. 97% of prior guidelines were confirmed stable; 3% changed materially.
- **Key Finding**: Baymard's 2024 research revised prior pagination guidance: pagination is now considered **"acceptable under certain conditions"** — a material softening from the earlier stance that broadly discouraged it for category pages. The 2024 update also reversed Quick View guidance (now recommended for visually-driven product categories). The 97% guideline-stability rate across Baymard's multi-year study program is itself evidence of durability: the core finding (Load More preferred for discovery browsing) holds; pagination's acceptable conditions now include SEO-critical deep catalogs, spec-driven comparison browsing, and B2B repeat-purchase flows.
- **E-Commerce Application**: When choosing pagination pattern for a specific page type, reference 2024+ Baymard guidance rather than the 2016 Smashing article alone. The 2024 revision does not eliminate the Load More recommendation for consumer discovery browsing — it narrows the set of cases where pagination is categorically wrong. Use this finding alongside F2 and F1.
- **Replication Status**: Single Baymard study; the high guideline-stability rate (97% unchanged) is the key internal consistency signal. Full research is paywalled (Baymard Premium); the launch blog post is freely accessible and contains specific quoted findings.
- **Boundary Conditions**: Full methodology and detailed guidelines require Baymard Premium access. The launch post covers key reversals; edge cases and fine-grained implementation detail require the full study.
- **Evidence Tier**: Gold

---

## Methodological Notes

1. **Baymard dominance**: Most pagination UX findings originate from Baymard Institute, whose methodology (large-scale usability testing, 4,400+ sessions across 50+ sites) is the gold standard for e-commerce UX research. Baymard findings are observational, not causal A/B test results — they identify friction, not quantify conversion lift from fixing it.

2. **Selection bias in "Load More" recommendations**: The recommendation toward Load More + lazy-loading is based on task completion and browsing behavior metrics, not conversion rate. It's possible that deeper product browsing doesn't directly translate to higher conversion in all categories. Individual A/B testing of pagination patterns on your specific site is the gold standard.

3. **Academic gap**: No peer-reviewed controlled experiment directly measures the conversion impact of pagination pattern choice in e-commerce. All quantitative recommendations are from practitioner research with vendor or self-interest risks. Finding 15 adds foundational behavioral-economics primary grounding (Nunes & Dreze 2006) for the goal-gradient mechanism underlying Finding 10.

4. **Skeleton screen research quality**: The Kovacs et al. (2018) study exists but uses limited sample sizes and non-e-commerce contexts. The 20-30% perception improvement number is a practitioner synthesis, not a specific claim in the NNGroup 2023 or Kovacs 2018 publications. NNGroup 2023 provides updated, more nuanced guidance on when skeleton screens outperform spinners.

5. **ECP cross-reference**: Pagination patterns interact with filter UX (search-and-filter-ux.md Finding 3: 40% of users can't find filters; Finding 21: horizontal filter bars fail with 6+ types). Product discovery via scrolling is directly dependent on filtering quality — if filters work, users browse fewer pages and convert faster.

6. **Audit note (2026-04-21)**: F3 dates corrected (NNGroup Sep 2022 not Jan 2024; Deque Oct 2 2019 not Dec 2025). F4 and F9 downgraded Gold→Silver (no free page anchors). F12 downgraded Gold→Silver (specific thresholds unverifiable free). F11 updated to reflect Google's 2019 rel=prev/next deprecation. F15 (Nunes & Dreze JCR primary) and F16 (Baymard 2024) added.

---

## Sources Consulted

- Baymard Institute. "Infinite Scrolling, Pagination Or 'Load More' Buttons? Usability Findings In eCommerce." Smashing Magazine, March 2016. https://www.smashingmagazine.com/2016/03/pagination-infinite-scrolling-load-more-buttons/
- Baymard Institute. Product Lists & Filtering Research Study (ongoing). https://baymard.com/research/ecommerce-product-lists
- Baymard Institute. Mobile Commerce Usability Research. https://baymard.com/blog/mobile-ecommerce-search-and-navigation
- Baymard Institute. "2024 Product Finding Research Launch." September 17, 2024. https://baymard.com/blog/product-finding-2024-launch
- Nielsen Norman Group. "Infinite Scrolling: When to Use It, When to Avoid It." Published September 4, 2022. https://www.nngroup.com/articles/infinite-scrolling-tips/
- Nielsen Norman Group. "Skeleton Screens 101." Published June 4, 2023. https://www.nngroup.com/articles/skeleton-screens/
- Nielsen Norman Group. E-Commerce User Experience Reports (13 volumes, 1,073 guidelines).
- Deque. "Infinite Scrolling & Role=Feed Accessibility Issues." Published October 2, 2019. https://www.deque.com/blog/infinite-scrolling-rolefeed-accessibility-issues/
- Kovacs, G., Mejtoft, T., & Söderström, U. (2018). "The effect of skeleton screens: Users' perception of speed and ease of navigation." ACM / ResearchGate. https://www.researchgate.net/publication/326858669 *(HTTP 403 — paywalled; paper metadata verifiable)*
- Nunes, J. C., & Dreze, X. (2006). "The Endowed Progress Effect: How Artificial Advancement Increases Effort." *Journal of Consumer Research*, 32(4), 504–512. DOI: 10.1086/500480
- Google Search Central. "Managing crawling of faceted navigation URLs." https://developers.google.com/search/docs/crawling-indexing/crawling-managing-faceted-navigation
- Smashing Magazine. Friedman, V. "Infinite Scroll UX Done Right: Guidelines and Best Practices." March 30, 2022. https://www.smashingmagazine.com/2022/03/designing-better-infinite-scroll/
