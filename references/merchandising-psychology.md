<!-- RESEARCH_DATE: 2026-04-02 -->
<!-- RECONCILED: 2026-04-22 — Run A + Run B dual-run synthesis. F1/F4/F6 Gold→Silver, F2 reformulated (64% conflation corrected, diversity-Relevance framing), 3 new findings (F10 Joachims, F11 Huber decoy, F12 Simonson compromise), F5 ethics cross-ref added, dead URL removed. -->
# Merchandising Psychology: Research Findings

**Research Date**: April 2, 2026 (original); reconciled April 22, 2026
**Domain**: Category UX — Product Ordering and Merchandising Psychology
**Total Findings**: 12 (original 9 + 3 added in dual-run audit)
**Methodology Note**: Merchandising psychology research sits at the intersection of behavioral economics, attention research, and ecommerce UX. Baymard's position effect data (2–3× more clicks for top positions) is well-established qualitatively, with foundational primary-source grounding from Joachims et al. 2005 (Finding 10). Vendor claims for AI merchandising lift (5–15% revenue improvement) are flagged as commercial data requiring independent verification.

---

## Cross-Reference Notice

**ECP Reference Overlap**:
- No direct overlap for merchandising psychology specifically.
- eye-tracking-and-scan-patterns.md covers the F-pattern and above-fold attention data that explains why position effects exist.
- Decoy/compromise effects (Findings 11, 12) overlap with pricing-psychology / bundle-pricing clusters — cross-ref those for overlapping claims.

This file covers: position primacy effects, algorithmic vs. manual merchandising, hybrid approaches, badge psychology, out-of-stock handling, new product discovery, category header design, personalization cold-start, position-bias primary evidence (IR), decoy effect, compromise effect.

---

## Summary

### Top 3 Most Impactful Findings

1. **Finding 1 (First 1–2 Rows Get 2–3× More Clicks)**: Top positions in a product grid receive disproportionate attention and clicks. The merchandising decision of what appears first is among the most high-stakes configuration choices in ecommerce — it's worth treating with deliberate strategy.
2. **Finding 3 (Hybrid Algorithm + Manual Merchandising)**: Pure algorithm creates "rich get richer" dynamics; pure manual doesn't scale. The hybrid approach (algorithm fills positions, merchandisers pin/boost/bury) captures the efficiency of algorithms while preserving strategic control.
3. **Finding 5 (Social Proof Badges Increase Click-Through)**: Best Seller, New, and Sale badges applied to the right products with strict limits (1–2 per card) measurably increase click-through by reducing evaluation effort. The limit and automation rules prevent badge inflation that eliminates the signal.

---

## Findings

### Finding 1: Products in First 1–2 Rows Receive 2–3× More Clicks Than Later Positions

- **Source**: Baymard Institute. "Product List UX Research." https://baymard.com/research/ecommerce-product-lists Category page click pattern analysis. Cross-referenced with Hugo Jenkins UsabilityHub click heatmap data (2020) https://usabilityhub.com/. Foundational position-bias primary source: Joachims et al. 2005 SIGIR — see Finding 10.
- **Methodology**: Baymard qualitative usability testing with eye-tracking across 19+ major ecommerce sites. Jenkins: click heatmap analysis via UsabilityHub (n=150). NNGroup eye-tracking on product listing pages.
- **Key Finding**: Products in positions 1–8 (first 2 rows in a 4-column grid) receive 2–3× more clicks than products in positions 9+. Position 1 receives the most attention of any individual position. This "primacy effect" is driven by above-fold attention concentration (eye-tracking research shows 57% of viewing time above the fold per NNGroup) and F-pattern scanning (horizontal sweep across row 1, then row 2, then diminishing attention on subsequent rows). The effect compounds over time: products that rank high get more clicks → more sales data → algorithm keeps them ranked high. The underlying position-bias phenomenon is rigorously established by Joachims et al. 2005 (see Finding 10); the specific 2–3× ratio applied to ecommerce is Baymard practitioner synthesis.
- **E-Commerce Application**: Treat positions 1–20 as "prime real estate" requiring active management. Decisions about what appears in these positions should be conscious merchandising choices: (1) Which products represent the breadth and quality of the category? (2) Which products have strong margin AND strong conversion? (3) Which products need initial visibility to break into the algorithmic ranking cycle? Do not default-sort by "Product ID" or database order — the first 20 positions should reflect intentional merchandising strategy.
- **Replication Status**: Position primacy is one of the most stable findings in attention/click research, replicated across search engine results, ecommerce grids, and offline retail shelf positioning. See Finding 10 for the primary IR evidence base (Joachims 2005; Craswell 2008).
- **Boundary Conditions**: The 2–3× ratio is an average — specific magnitudes depend on page length, category size, and user intent. High-intent users (searching for a specific item) are less influenced by position than discovery browsers. Mobile users see fewer above-fold products (often 2–4 in a 2-column grid), making position 1 even more dominant.
- **Evidence Tier**: Silver *(the 2–3× ecommerce ratio is Baymard practitioner synthesis without a specific page anchor; the underlying position-bias phenomenon is Gold — documented at Finding 10)*

---

### Finding 2: Diversity-Based "Relevance" Default Sort Outperforms "Newest" Default

- **Source**: Baymard Institute. "Always Sort Product Lists by Diversity-Based 'Relevance' (24% Don't)." https://baymard.com/blog/default-sort-type. Large-scale usability testing and benchmark of sort option usage.
- **Methodology**: Baymard usability testing comparing default sort options across major ecommerce sites. Observation of user confusion and confidence levels with different default sorts.
- **Key Finding**: Baymard benchmark: 24% of desktop ecommerce sites fail to implement a diversity-based default sort (verified on cited URL). The recommended default is a diversity-based "Relevance" sort that ensures product types constituting >10% of a category appear within the first 20 positions on desktop (first 10 on mobile) — preventing a homogeneous top-of-list that misrepresents the category's breadth. "Newest First" as default caused confusion in Baymard usability testing — users who hadn't explicitly asked for new products were confused about why they were seeing recently added items, and questioned whether they were seeing the "best" or "most popular" products. One participant: *"They seem quite pricey, and just because their most expensive items pop up first, I would probably leave."* "Best Selling" default leverages the crowd wisdom heuristic: users trust that social proof from prior buyers validates quality. Plain "Best Selling" without the >10% diversity rule can still cause the category to feel narrow — the Baymard recommendation adds diversity as a secondary constraint.
- **E-Commerce Application**: Default sort by page type: (1) Standard category browsing → diversity-based "Relevance" or "Best Selling" with diversity rule applied (recommended); (2) Search results → "Relevance" (match to search intent); (3) New Arrivals section/page → "Newest" (explicit context makes this sensible); (4) Sale/clearance → "Best Selling" or "Highest Discount" (urgency + social proof); (5) After user applies sort → maintain their choice for the session; (6) Filtered views → maintain the sort order the user had before filtering.
- **Replication Status**: Consistent across Baymard usability testing rounds. The finding that "newest first" causes confusion is replicated qualitatively.
- **Boundary Conditions**: "Best Selling" default requires actual sales data to sort by. New stores without sales history must use "Featured" (manual curation) or "Newest" as interim defaults. Plain "Relevance" as a category page default (not search) is opaque to users unless diversity logic is applied and the result looks curated and representative.
- **Evidence Tier**: Gold

---

### Finding 3: Hybrid Algorithmic + Manual Merchandising Outperforms Either Approach Alone

- **Source**: Baymard Institute. Category page merchandising research. https://baymard.com/research/ecommerce-product-lists Cross-referenced with Constructor.io https://constructor.com/, Algolia https://www.algolia.com/, and Nosto merchandising platform documentation https://www.nosto.com/. **[Vendor flag for specific lift percentages.]**
- **Methodology**: Baymard qualitative research on algorithmic sorting effects. Vendor platforms report 5–15% revenue-per-visitor improvement from AI merchandising — methodology not independently verified.
- **Key Finding**: Pure algorithmic sorting creates "rich get richer" dynamics — high-converting products stay at the top, new products never get visible, category storytelling is lost, and seasonal/trend products may not surface despite business value. Pure manual merchandising doesn't scale (impossible to manage 10,000+ SKU positions manually) and is subject to human bias and update lag. Hybrid approach: algorithm fills all positions based on conversion/margin/recency signals; merchandisers apply boost/bury/pin rules on top; business logic rules enforce constraints (always bury discontinued products; new products get initial position boost; on-sale products get promoted).
- **E-Commerce Application**: Hybrid merchandising rule types: (1) Pin: fix specific products to exact positions (e.g., pin a launch product to position 1 for 30 days); (2) Boost: multiply ranking score for products meeting criteria (is_new × 1.5, is_high_margin × 1.2, is_featured × 2.0); (3) Bury: reduce ranking score (is_discontinued → last pages, is_low_margin → -30% score); (4) Category rules: products in specific collections always appear in category (e.g., all "Bestsellers" in top 20 of their parent category); (5) Inventory signals: low stock (≤5 units) may bury rather than promote — don't build discovery for products that will disappoint with OOS.
- **Replication Status**: The hybrid approach is industry consensus; specific lift percentages from vendor platforms lack independent verification.
- **Boundary Conditions**: Hybrid merchandising requires a merchandising rules engine — either a purpose-built tool (Constructor.io, Algolia, Searchspring) or custom implementation. Small stores (<500 products) can achieve hybrid outcomes through manual sort orders in their platform (Shopify collection sort, WooCommerce ordering) + new product badges without a dedicated tool.
- **Evidence Tier**: Silver

---

### Finding 4: Category Banner Height Maximum — Products Must Be Visible Without Scroll

- **Source**: Baymard Institute. Category page header usability research. https://baymard.com/research/ecommerce-product-lists Usability testing of category page layouts. (No free page-anchored URL with the specific 200–300px threshold.) Quantitative support: NNGroup above-fold data (57% viewing time) — see eye-tracking-and-scan-patterns.md.
- **Methodology**: Qualitative usability testing observing user frustration when scrolling is required to see any products on a category page.
- **Key Finding**: Users navigate to category pages for products, not content. Promotional banners, editorial content, or large visual headers that push all products below the fold cause immediate disorientation and elevated bounce rates in usability testing. The maximum usable above-products content height is approximately 200–300px on desktop (accounting for global navigation height), ensuring at least one full row of product cards is visible above the fold. On mobile: the above-fold product visibility threshold is even tighter — with a typical phone viewport of 667px and 60–80px of navigation, only 200px of category header content is acceptable.
- **E-Commerce Application**: Category page content hierarchy: (1) H1 category heading (always, important for SEO and accessibility): small, doesn't consume much space; (2) Short category description (optional, 1–2 lines max): only if it adds navigation value or is needed for SEO; (3) Promoted filter pills (optional but valuable): 48px row height; (4) Subcategory navigation tiles (optional): 60–80px if using text pills, 120–150px if using image tiles; (5) Promotional banner (only if there's a specific promotion): maximum 150–200px height; (6) Products begin here — at least one row visible above fold on both desktop and mobile. Test with DevTools device simulation: on a 375px mobile viewport with 60px navigation, what's the first product's top position? If >400px, the header is too tall.
- **Replication Status**: Consistent Baymard research finding. The principle that users come to category pages for products (not content) is stable.
- **Boundary Conditions**: Lifestyle/editorial brand pages (not standard category pages) intentionally use full-viewport imagery before product display — this is a different page type. "New Season" or campaign collection pages may justify more editorial space. The restriction applies specifically to standard product category pages.
- **Evidence Tier**: Silver *(the 200–300px pixel thresholds are practitioner-derived guidance; no free page-anchored Baymard URL provides this specific quantification)*

---

### Finding 5: Social Proof Badges (Best Seller, New, Sale) Increase Click-Through — Maximum 2 Per Card

- **Source**: Baymard Institute. Product list badge research. https://baymard.com/research/ecommerce-product-lists Cross-referenced with CRO social proof research (social-proof-patterns.md).
- **Methodology**: Qualitative usability testing of badge effect on product card click-through. Benchmark analysis of badge implementation across major ecommerce sites.
- **Key Finding**: Badges applied to product cards reduce evaluation friction by providing a quick signal about why a product is notable. Effect by badge type: "Best Seller" is the strongest social proof signal (crowd validation); "Sale/Discount" is a strong price motivation signal; "New" appeals to novelty seekers; "Low Stock" creates urgency (but must be honest); "Staff Pick" provides editorial authority. Maximum 2 badges per card — more than 2 creates visual clutter that reduces the effectiveness of individual badges and competes with the product image for attention. Automated badge application (from data rules) is preferred over manual — it ensures consistency and reduces maintenance overhead.
- **E-Commerce Application**: Badge automation rules: (1) Best Seller: products in top 10% of category by units sold in trailing 30 days; (2) Sale/Discount: `compare_at_price` > `price` — display percentage: "20% Off"; (3) New: `created_at` timestamp within 30 days; (4) Low Stock: inventory ≤ 5 units — display "Only X left" (only show if the number is accurate — don't fake scarcity); (5) Badge application: take the two highest-priority applicable badges per product. Display consistently at top-left of image. CSS: `position: absolute; top: 8px; left: 8px;`. Typography: 11–13px, bold, high contrast on the badge background color.
- **Replication Status**: Badge click-through effects are qualitatively consistent in Baymard testing. Specific CTR lift percentages depend on implementation and category — treat as directional.
- **Boundary Conditions**: Badge inflation (applying "Best Seller" to all products in a small catalog) eliminates the signal value. Only apply "Best Seller" if the product is genuinely among top sellers in its category — not just the top seller of a 10-product catalog. "Low Stock" must be truthful — users who add to cart and find the item available in unlimited quantity feel manipulated, which damages trust. → See ethics-gate.md §1.1 (urgency/scarcity rules) for the fabricated-scarcity guardrail.
- **Evidence Tier**: Silver

---

### Finding 6: Out-of-Stock Products Should Be Pushed to End of List — Not Hidden or Featured In-Position

- **Source**: Baymard Institute. Out-of-stock product handling research. https://baymard.com/research/ecommerce-product-lists Category page merchandising. (No free page-anchored URL.)
- **Methodology**: Usability testing of different OOS product display strategies.
- **Key Finding**: See also grid-layout.md Finding 6 for the full treatment. Summary: (1) Hiding OOS products entirely: causes confusion when users search for previously-seen products; SEO impact from URL removal; (2) OOS products in their algorithmic position: wastes prime real estate with unconvertable products; (3) OOS products pushed to end of category with indicator: best practice — product remains findable for "Notify Me" and reference, doesn't waste prime positions.
- **E-Commerce Application**: Implement as an algorithmic rule: products with inventory ≤ 0 receive a sorting penalty that moves them to the end of category page results. Apply in any category that uses algorithmic or manual sort. On individual product cards: show greyed image, "Out of Stock" badge, "Notify When Available" CTA. On category pages: consider filtering out OOS by default for categories with >20% OOS rate and providing "Include out of stock" toggle.
- **Replication Status**: Consistent Baymard recommendation.
- **Boundary Conditions**: See grid-layout.md Finding 6 for full boundary conditions.
- **Evidence Tier**: Silver *(no free page-anchored URL for this specific OOS merchandising rule)*

---

### Finding 7: New Product Discovery Requires Active Position Intervention — Algorithm Alone Fails

- **Source**: Baymard Institute. New product visibility research. https://baymard.com/research/ecommerce-product-lists Cross-referenced with merchandising platform documentation (Algolia https://www.algolia.com/, Constructor.io https://constructor.com/). See also grid-layout.md Finding 9.
- **Methodology**: Analysis of algorithmic ranking behavior for products without performance history. Qualitative usability research on new product discovery.
- **Key Finding**: New products have zero historical sales, click, and conversion data — algorithmic ranking based on performance signals places them last by default. Users never see them → they never develop data → they stay last. The discovery problem is self-reinforcing. Baymard usability testing shows that when users explicitly ask for "new" products, they use sort or filter — but natural category browsing rarely surfaces new products without algorithmic intervention.
- **E-Commerce Application**: New product visibility strategies: (1) Forced position: pin new products to positions 5–12 in category for 30 days (below bestsellers, above algorithmic tail); (2) New Arrivals section or subcategory page: dedicated "New This Month" entry point in navigation/on category page; (3) Position boost rule: new products (<30 days) receive a ranking multiplier (1.5–2.0×) in the merchandising algorithm; (4) "New" badge: visible indicator that a product is newly added (encourages "new arrival" scanners to click); (5) Email/notification: "New in [Category]" email to subscribers. Measure: compare click-through rate for new products with vs. without position intervention in A/B test.
- **Replication Status**: Algorithm bias against new products is a structural feature of performance-based ranking. Finding is based on algorithmic analysis, not user behavior experiment.
- **Boundary Conditions**: New products that have been given boosted position for 30 days and still don't convert indicate a product-market fit problem, not a visibility problem. Remove position boost after intervention period and let the algorithm reflect actual performance.
- **Evidence Tier**: Silver

---

### Finding 8: Subcategory Navigation Tiles Improve Discovery for Large Category Hierarchies

- **Source**: Baymard Institute. Category page navigation research. https://baymard.com/research/ecommerce-product-lists Collection page architecture findings.
- **Methodology**: Usability testing of category page navigation patterns for large-catalog ecommerce sites.
- **Key Finding**: For categories with meaningful subcategories (e.g., "Dresses" containing "Casual," "Formal," "Cocktail," "Wedding Guest"), presenting subcategory navigation tiles at the top of the category page dramatically improves discovery by helping users self-route to the right subcategory immediately, rather than browsing an undifferentiated mixed-category product grid. Subcategory tiles work when: the category has 4+ meaningful subcategories, each subcategory has 20+ products, and users arrive at the parent category with intent to navigate to a specific subcategory.
- **E-Commerce Application**: Subcategory navigation implementation: (1) Position above product grid (or alongside a truncated featured product selection in a split-layout); (2) Use either image tiles (with lifestyle image representing the subcategory) or text pills — image tiles are more engaging; text pills take less space; (3) Show subcategory name + product count: "Cocktail Dresses (47)"; (4) Keep to maximum 8 subcategory tiles before the grid — more creates scrolling before product discovery; (5) For very large categories (10+ subcategories): use a horizontal scrollable pill row rather than a wrapping grid of tiles. On mobile: horizontal scrolling pills work better than tile grids due to space constraints.
- **Replication Status**: Qualitative Baymard finding. Consistent recommendation for large-catalog category pages.
- **Boundary Conditions**: Subcategory navigation tiles add value only when the subcategories are meaningfully distinct and well-populated. For small catalogs (<200 products per category) or categories with only cosmetic subcategory distinctions, the tiles add navigation overhead without clarity benefit.
- **Evidence Tier**: Silver

---

### Finding 9: Personalized Product Ordering Requires Sufficient Data — Cold-Start Problem

- **Source**: Baymard Institute. Personalization research applied to category merchandising. https://baymard.com/research/ecommerce-product-lists Cross-referenced with personalization-psychology.md (if available in the psych-references set).
- **Methodology**: Qualitative and analytical research on personalized ranking systems and their data requirements. Industry practitioner evidence.
- **Key Finding**: Personalized category page ordering (showing products ordered by predicted user preference based on browse/purchase history) requires substantial user data to outperform well-configured non-personalized sorting. The "cold-start problem" means that: new users have no personal data → personalization performs worse than default; users with thin history (1–2 sessions) → personalization may produce worse results than bestsellers-based default. Personalization becomes meaningful when a user has 5+ product interactions or 2+ purchase sessions.
- **E-Commerce Application**: Personalization rollout strategy: (1) No personalization for new users (session 1 and 2): default to Best Selling; (2) Emerging personalization (sessions 3–5): incorporate browse history as a mild ranking signal; (3) Established personalization (5+ sessions or 1 purchase): personalized ordering as primary signal. For most ecommerce stores: focus on category-level and bestsellers-based merchandising first; personalized ordering is a later optimization requiring real ML infrastructure. Don't confuse personalized recommendations ("You might also like...") with personalized category ordering — the former is easier to implement and often higher ROI.
- **Replication Status**: Cold-start problem is well-established in recommendation systems research (academic literature: Lam et al. 2008, Schein et al. 2002).
- **Boundary Conditions**: Personalization effectiveness varies significantly by product catalog size and repeat purchase frequency. High-repeat-purchase categories (beauty, supplements, consumables) see stronger personalization lift than infrequent-purchase categories (furniture, appliances). B2B procurement contexts (repeat ordering from fixed catalog) are the strongest use case for personalized ordering.
- **Evidence Tier**: Silver

---

### Finding 10: Position Bias — Foundational IR Primary Evidence

- **Source**: Joachims, T., Granka, L., Pan, B., Hembrooke, H., & Gay, G. (2005). "Accurately Interpreting Clickthrough Data as Implicit Feedback." *Proceedings of SIGIR 2005*. <https://doi.org/10.1145/1076034.1076063> Craswell, N., Zoeter, O., Taylor, M., & Ramsey, B. (2008). "An Experimental Comparison of Click Position-Bias Models." *WSDM 2008*. <https://doi.org/10.1145/1341531.1341545>
- **Methodology**: Joachims: eye-tracking + randomized result-presentation experiments (Cornell; N=36 users across controlled conditions) measuring click rates by position independent of document relevance. Swapped result positions to isolate position bias from content quality. Craswell: large-scale click-log analysis comparing cascade, mixture, and position-discount click models.
- **Key Finding**: Users follow a "cascade" model — they evaluate ranked results top-down and make click decisions before exhaustively scanning deeper. Click probability decays roughly exponentially with position, independent of actual item relevance. Swapping the top two results in the Joachims experiment caused click rates to shift with position rather than content: position 1 consistently captured the majority of clicks regardless of what document was placed there. This is the foundational primary evidence for the position-bias phenomenon that Finding 1 applies to ecommerce grids.
- **E-Commerce Application**: The Joachims finding justifies treating positions 1–3 (or positions 1–8 in a multi-column grid) as an editorial/merchandising decision, not a neutral algorithmic output. Whatever you place at the top sells more — partly because it is there, not only because it is better. Use deliberately: place strategic merchandising picks, rotate "featured" positions to distribute exposure, and discount raw position-click data when training ranking models (use position-adjusted metrics such as Inverse Propensity Scoring).
- **Replication Status**: Extensively replicated across IR literature. Cascade and dependent click models (DCM) are standard baselines in click modeling. Applicable to ecommerce product rankings by analogy — the cognitive mechanism (top-down scanning) is the same domain as F-pattern behavior documented in eye-tracking-and-scan-patterns.md.
- **Boundary Conditions**: Joachims was conducted on web search results (text links). Applying to visual product grids requires interpolation: grids show items in parallel rows rather than a single vertical list, so position effects are 2D (row × column). Top-left position remains dominant in F-pattern scanning. The exponential decay curve from search results is directionally applicable but magnitudes differ in grid contexts.
- **Evidence Tier**: Gold (primary peer-reviewed; SIGIR is ACM flagship IR venue; DOIs verified)

---

### Finding 11: Decoy Effect — Asymmetric Dominance Shifts Product Choice

- **Source**: Huber, J., Payne, J. W., & Puto, C. (1982). "Adding Asymmetrically Dominated Alternatives: Violations of Regularity and the Similarity Hypothesis." *Journal of Consumer Research*, 9(1), 90–98. <https://doi.org/10.1086/208899>
- **Methodology**: Laboratory choice experiments with student participants. Subjects chose between pairs (A, B) and triples (A, B, A'), where decoy A' was inferior to target A on all dimensions but comparable to B. Measured choice-share shifts; violated the "regularity" axiom of rational choice theory.
- **Key Finding**: Adding a decoy option A' (asymmetrically dominated — worse than target A on every attribute, but close enough to B to serve as a comparison anchor) consistently shifts choice share from B toward A. Reported choice-share shifts of 5–15 percentage points; direction is robust across replications even when specific magnitudes vary. The mechanism: A' provides a clear "reason" to prefer A over B (A dominates A', A' is comparable to B → A must be better than B).
- **E-Commerce Application**: When presenting three tiers of similar products on a category page or product detail comparison, configure the middle or target tier with an asymmetrically dominated alternative to shift preference toward it. Concrete example: three subscription tiers where one is clearly inferior to the target on every meaningful dimension — shifts selection toward the intended tier. Cross-reference pricing-psychology cluster for overlapping coverage of this effect in pricing contexts.
- **Replication Status**: Widely replicated in consumer psychology and behavioral economics. Ariely (2008, *Predictably Irrational*) popularized the effect for marketing audiences. Magnitudes vary by context; direction is robust.
- **Boundary Conditions**: Decoy effect requires comparable attributes across options — weakens when options differ on incommensurable dimensions. Cultural effects exist; Western consumer samples show stronger effects than some Asian samples in cross-cultural replications. The decoy must be genuinely inferior to the target — if users perceive the decoy as a real option, the framing collapses.
- **Evidence Tier**: Gold (JCR primary; foundational behavioral-economics paper; DOI verified)

---

### Finding 12: Compromise Effect — Middle Option Preference in Three-Tier Product Sets

- **Source**: Simonson, I. (1989). "Choice Based on Reasons: The Case of Attraction and Compromise Effects." *Journal of Consumer Research*, 16(2), 158–174. <https://doi.org/10.1086/209205>
- **Methodology**: Laboratory choice experiments with consumer products. Subjects faced triples arranged on a single attribute dimension (low/medium/high price × quality). Measured how adding an "extreme" third option changed the share of the middle option.
- **Key Finding**: When three alternatives are arranged on a quality-price gradient (low-price/low-quality, mid-price/mid-quality, high-price/high-quality), the middle option is disproportionately selected — the compromise effect. Users justify their choice via "reasons" logic: the middle minimizes the risk of being wrong on either extreme. Adding an extreme option (above or below the prior pair) systematically increases selection of what was previously the extreme but is now the middle.
- **E-Commerce Application**: Surface three-tier product arrangements in top positions on category pages when the goal is to steer toward a margin-optimal middle SKU. Works best when the three tiers are genuinely differentiated (not cosmetic). In category pages with wide price ranges, adding a clearly premium "high" option can shift demand from the cheapest to the middle tier. Avoid "compromise for its own sake": users notice when tiers feel artificial. Cross-reference pricing-psychology cluster.
- **Replication Status**: Extensively replicated. Simonson & Tversky (1992, *JMR*) extended the effect to marketing contexts. Tversky & Simonson (1993) is the canonical context-dependence model. Works alongside decoy effect (Finding 11) — both exploit context-dependent evaluation.
- **Boundary Conditions**: Compromise effect weakens when users have strong pre-existing preferences or high category expertise. Most effective for unfamiliar categories where users lack a reference preference. The three tiers must be arranged on a perceptually legible attribute gradient — if users can't rank the options, the compromise heuristic doesn't fire.
- **Evidence Tier**: Gold (JCR primary; widely replicated; DOI verified)

---

## Methodological Notes

- Position primacy effects are among the most robustly replicated findings in retail and ecommerce research. The specific 2–3× ecommerce ratio is a Baymard practitioner estimate from usability observation; the underlying position-bias phenomenon is rigorously grounded in IR primary literature (Finding 10).
- AI merchandising vendor claims (5–15% revenue lift from algorithmic ordering) have not been independently replicated. These claims come from platforms with strong commercial interest in demonstrating value. Treat as directional upper bounds.
- Badge psychology is well-grounded in social proof theory (Cialdini), but specific CTR lifts from individual badge types lack rigorous controlled studies in ecommerce contexts.
- Decoy and compromise effects (Findings 11, 12) have strong primary-literature support (Huber 1982; Simonson 1989). Their specific ecommerce application is practitioner inference from strong laboratory foundations — direction is robust, magnitude depends on implementation.
- **Audit note (2026-04-22, dual-run reconciliation)**: F1, F4, F6 downgraded Gold → Silver (practitioner-derived specifics without page-anchored Baymard citations). F2 reformulated — original "64%" figure was from a different Baymard benchmark (sort-option availability) conflated with default-sort usage; replaced with Baymard's actual diversity-based Relevance recommendation. Findings 10–12 added from peer-reviewed primary sources (all Gold tier).

---

## Sources Consulted

1. Baymard Institute. Product Lists UX Research. https://baymard.com/research/ecommerce-product-lists
2. Baymard Institute. "Always Sort Product Lists by Diversity-Based 'Relevance' (24% Don't)." https://baymard.com/blog/default-sort-type
3. Baymard Research Hub (index). https://baymard.com/research
4. Jenkins, H. (2020). Click heatmap analysis. https://medium.com/insights-observations/size-and-layout-of-e-commerce-product-grids-a-user-research-case-study-8a8307cbd087
5. Constructor.io. "Ecommerce Merchandising." https://constructor.io/
6. Algolia. "AI Merchandising." https://www.algolia.com/products/ai-powered-search/merchandising-studio/
7. Nielsen Norman Group. "Above the Fold / Scrolling and Attention." https://www.nngroup.com/articles/scrolling-and-attention/
8. Joachims, T., Granka, L., Pan, B., Hembrooke, H., & Gay, G. (2005). "Accurately Interpreting Clickthrough Data as Implicit Feedback." *SIGIR 2005*. DOI: 10.1145/1076034.1076063
9. Craswell, N., Zoeter, O., Taylor, M., & Ramsey, B. (2008). "An Experimental Comparison of Click Position-Bias Models." *WSDM 2008*. DOI: 10.1145/1341531.1341545
10. Huber, J., Payne, J. W., & Puto, C. (1982). "Adding Asymmetrically Dominated Alternatives." *Journal of Consumer Research*, 9(1). DOI: 10.1086/208899
11. Simonson, I. (1989). "Choice Based on Reasons: The Case of Attraction and Compromise Effects." *Journal of Consumer Research*, 16(2). DOI: 10.1086/209205
<!-- REMOVED: https://baymard.com/research/category-navigation — returns 404 as of 2026-04-21 audit -->
