<!-- RESEARCH_DATE: 2026-04-02 -->
<!-- AUDIT_DATE: 2026-04-21 -->
<!-- RECONCILED_DATE: 2026-04-22 -->
# Content Freshness Signals

**Research Date:** 2026-04-02
**Total Findings:** 11
**Methodology:** Synthesis of Google spokesperson statements (Amit Singhal, Matt Cutts, John Mueller, Gary Illyes), Google patents on document freshness evaluation, Google core algorithm update documentation (2011 Freshness Update), and industry analyses. Evidence weighted by source authority and documentation quality.

> **Cross-Reference:** See SEO reference `ugc-reviews-seo.md` for review-driven freshness (the most scalable freshness strategy for large catalogs). See CRO reference `ugc-integration.md` for the conversion benefits of fresh review content.

---

## Summary

### Top 3 Most Impactful Findings

1. **Review solicitation is the most scalable freshness strategy — no editorial effort required** (Finding 4) — Each new customer review adds fresh, keyword-rich, unique content without editorial work. Active post-purchase review solicitation (7–14 days post-delivery) provides continuous freshness signals across the entire catalog simultaneously.

2. **Manipulating lastmod dates destroys Google's trust in your entire sitemap** (Finding 3) — Gary Illyes: Google operates on binary trust for lastmod — either trusts ALL your dates or ignores ALL of them. One false lastmod poisons the well for every URL in your sitemap.

3. **Freshness is NOT universally beneficial — evergreen product pages don't benefit** (Finding 2) — John Mueller: "If it's evergreen, you don't need to change it." Updating descriptions on established, unchanged products wastes effort and may destabilize rankings without any freshness benefit.

---

## Coverage by Research Question

| Research Question | Findings | Evidence Quality |
|---|---|---|
| What is Query Deserves Freshness (QDF)? | 1 | Gold |
| Does freshness help evergreen product pages? | 2 | Gold |
| Do fake lastmod date updates help? | 3 | Gold |
| Can reviews provide freshness signals? | 4 | Gold |
| How does Google technically evaluate freshness? | 5 | Silver |
| Which product types benefit from freshness? | 6 | Gold |
| What content updates count as substantive? | 7 | Gold |
| Do fresh buying guides help product page rankings? | 8 | Silver |
| Is the "90-day content update" rule valid? | 9 | Gold (debunked) |
| Does March 2024 HCU integration change freshness strategy? | 10 | Gold |
| What does lastmod actually signal to Google? | 11 | Gold |

---

## Findings

### Finding 1: Query Deserves Freshness (QDF) — Google's Freshness Re-Ranking Algorithm
- **Source**: Google Freshness Update, November 2011 (primary): https://googleblog.blogspot.com/2011/11/giving-you-fresher-more-recent-search.html — the canonical source for the "35% of search results" figure and the QDF framework. Amit Singhal (then Google Fellow and SVP), description of QDF algorithm, referenced in: New York Times, 2007 (paywalled secondary): https://www.nytimes.com/2007/06/03/technology/03google.html. Search Engine Journal QDF analysis: https://www.searchenginejournal.com/google-algorithm-history/freshness-algorithm/.
- **Methodology**: Google official announcement (2011 Freshness Update, primary) + Singhal's 2007 description of QDF algorithm. Not an empirical study — authoritative disclosure of Google algorithm behavior.
- **Key Finding**: QDF (Query Deserves Freshness) is a re-ranking function that boosts fresh content for queries where recency is important. Singhal described it as: if Google sees a spike in query volume around a topic, it infers that topic is "hot" and promotes fresh content. The November 2011 Freshness Update extended QDF to impact approximately **35% of search results** (this is a historical figure from the 2011 Google announcement — Google has not updated or re-issued this specific percentage since 2011; treat as directional rather than a current precise measurement). QDF-eligible query types: (1) recent events and hot topics, (2) regularly recurring events (annual product launches, seasonal sales), (3) frequently-updating information (product pricing, specifications).
<!-- RECONCILED_NOTE: F1 reformulated per Vera reconciled audit 2026-04-22. 2011 Google blog promoted to primary (NYT is paywalled secondary). "Historical 35% figure" caveat added per Run B. -->
- **E-Commerce Application**: QDF matters for: new product launches, trending items, "best X 2026" queries, seasonal/holiday product searches. QDF does NOT meaningfully affect: commodity products, evergreen product categories, navigational queries, stable product specifications. Identify which products in your catalog are seasonally/annually searched — these benefit from freshness investment.
- **Replication Status**: Google official announcement — algorithm behavior is documented. The 35% impact figure is from Google's own announcement of the 2011 update.
- **Boundary Conditions**: QDF is a re-ranking signal for fresh content, not a blanket freshness boost. Old, high-quality content on evergreen topics still outranks fresh content on those same topics — freshness only helps where freshness is relevant to the query.
- **Evidence Tier**: Gold — Google official announcement and Google Fellow spokesperson statement.

---

### Finding 2: Freshness Is NOT Universally Beneficial — Evergreen Products Don't Need Updates
- **Source**: Matt Cutts (former Google head of Webspam), SXSW 2013 and multiple Webmaster Q&A sessions: "Not every query deserves freshness." John Mueller, Google Search Central office hours (2020, recorded): "If it's evergreen, you don't need to change it." Search Engine Land summary: https://searchengineland.com/guide/query-deserves-freshness-qdf.
- **Methodology**: Direct Google spokesperson statements. Not a study — authoritative clarification of algorithm behavior.
- **Key Finding**: Google explicitly distinguishes between queries that deserve freshness (QDF-eligible, as in Finding 1) and queries where freshness is irrelevant. For stable, evergreen product pages (a kitchen knife that hasn't changed in 5 years, a standard mechanical part), freshness signals provide no ranking benefit. John Mueller has specifically said "if it's evergreen, you don't need to change it" in response to questions about updating old content.
- **E-Commerce Application**: Do NOT update product descriptions for the sake of appearing fresh if the product hasn't changed. This wastes editorial effort and may actually destabilize rankings temporarily (re-indexing can cause brief fluctuations). Update product pages when: (1) actual product information has changed, (2) you have new data or features to add, (3) the product category is genuinely trending, (4) content is incomplete or inaccurate.
- **Replication Status**: Consistent across multiple Google spokesperson statements. The "QDF applies only where freshness is relevant" principle is unambiguous and consistently communicated.
- **Boundary Conditions**: Even for evergreen products, adding genuinely useful new information (new compatibility data, new customer use cases, new FAQs based on customer questions) is beneficial — not because of freshness signals, but because of content improvement.
- **Evidence Tier**: Gold — multiple Google spokesperson statements (Matt Cutts, John Mueller); consistent over many years.

---

### Finding 3: Manipulating lastmod Dates Destroys Sitemap Trust
- **Source**: John Mueller, Reddit AMA (April 2025): "Setting today's date in a sitemap file isn't going to help anyone. It's just lazy." Coverage: Search Engine Journal (2025) — https://www.searchenginejournal.com/googles-john-mueller-updating-xml-sitemap-dates-doesnt-help-seo/545547/ . John Mueller, Twitter/X (2022): changing date without changes is "just noise and useless." Gary Illyes, Search Off the Record podcast (multiple episodes): Google operates on binary trust for lastmod — either trusts ALL or ignores ALL. Confirmed on Google Search Central YouTube channel.
- **Methodology**: Multiple direct Google spokesperson statements. Consistent across Mueller and Illyes statements.
- **Key Finding**: Setting lastmod to today's date across all sitemap URLs without actual content changes provides zero benefit AND actively harms trust. Gary Illyes: Google's trust in lastmod is binary — if your sitemap consistently has accurate lastmod dates, Google trusts all of them for crawl scheduling. If you consistently set false dates, Google ignores all your lastmod dates. One systematic false lastmod practice poisons every URL in your sitemap. The 35% impact of the 2011 Freshness Update does not apply to fake lastmod gaming.
- **E-Commerce Application**: Only update lastmod when substantive content changes occur — new product specifications, updated pricing, added compatibility data, new FAQ sections, new editorial content. Do NOT update lastmod when: re-deploying unchanged content, changing theme/layout, updating metadata without content change, adding tracking pixels.
- **Replication Status**: Consistent across multiple Google spokesperson statements. Mueller's April 2025 Reddit AMA explicitly addresses this exact practice.
- **Boundary Conditions**: Legitimate automation that updates lastmod when actual content management system changes are committed is fine — the issue is mass-setting all dates to today as an SEO tactic.
- **Evidence Tier**: Gold — direct Google spokesperson statements (Mueller, Illyes); multiple sources, consistent.

---

### Finding 4: Customer Reviews Provide Natural, Scalable Freshness Signals
- **Source**: Multiple SEO publications synthesizing Google's Quality Rater Guidelines and freshness algorithm behavior. GatherUp, "Review Statistics: The Impact of Online Reviews" (2024 edition), https://gatherup.com/blog/online-review-statistics/. Google QRG on dynamic review content receiving freshness weighting.
- **Methodology**: GatherUp: consumer survey data (methodology: online survey, sample not published). Google QRG: official framework. The freshness signal from reviews is an inferred effect from Google's documented freshness evaluation criteria (Finding 5).
- **Key Finding**: New customer reviews continuously add: fresh, unique text content; keyword variations matching real customer language; recency signals visible to both users and algorithms; and increased word count on the page — all without editorial effort. Google's quality rater guidelines specifically note that pages with recent reviews demonstrate active, living product pages. GatherUp consumer survey data: **67% of consumers sort reviews to see which ones are most recent** — indicating strong recency-seeking behavior in review-reading. Note: the GatherUp source describes review-sorting behavior, not a direct measurement of "recency as most influential factor" — the latter phrasing overstates what the survey measures.
<!-- RECONCILED_NOTE: F4 reformulated per Vera reconciled audit 2026-04-22. The 67% claim re-worded to match actual GatherUp source language ("sort reviews to see which are most recent" vs. "recency is most influential factor"). Tier for the 67% stat: Silver (vendor consumer survey with unpublished sample size, specific to sorting behavior). -->
- **E-Commerce Application**: Active review solicitation is the most scalable freshness strategy for large ecommerce catalogs. Implementation: (1) post-purchase email sequence requesting review (7–14 days after delivery confirmation); (2) SMS follow-up for mobile customers; (3) review reminder if no review submitted within 30 days; (4) make photo/video upload easy in review flow (photos increase review value for both SEO and conversion).
- **Replication Status**: The freshness benefit of reviews is structurally sound (new content = freshness signal) and consistent with Google's documented algorithm behavior. The 67% consumer recency preference is GatherUp survey data — directionally reliable but not peer-reviewed.
- **Boundary Conditions**: Review freshness benefits are most significant for products with query activity — products that are actively searched. Products with no search volume get no QDF benefit from fresh reviews. Reviews must comply with FTC Consumer Review Rule (see ugc-reviews-seo.md) — manufactured or incentivized reviews without disclosure are illegal.
- **Evidence Tier**: Gold for the freshness mechanism (structural logic supported by Google documentation); Silver for the GatherUp 67% statistic (vendor consumer survey, unpublished sample size, specific to sorting behavior — directionally reliable but not peer-reviewed).

---

### Finding 5: Google's Technical Freshness Evaluation — Patent Documentation
- **Source**: Google US Patents: US8549014B2 ("Modifying search result ranking based on implicit user feedback"), US8832088B1 ("Determining document age for search results"), US9081857B1. Google API leak (May 2024) — internal attribute names revealed: bylineDate, syntacticDate, semanticDate, lastSignificantUpdate, FreshnessTwiddler. SparkToro analysis of leaked API documentation: https://sparktoro.com/blog/a-critical-examination-of-the-google-search-api-document-leak/.
- **Methodology**: Patent documentation: public US Patent Office filings. API leak: accidental publication of internal Google API documentation (confirmed as real by Google spokespeople, though Google noted the API may not reflect current ranking systems). Both provide directional insight into Google's freshness evaluation criteria.
- **Key Finding**: Based on patent documentation and the May 2024 API leak, Google evaluates document freshness through multiple attributes: document inception date (when content was first discovered), change frequency (how often the document changes), change magnitude (how much content changed), and "lastSignificantUpdate" (a specific attribute distinguishing meaningful updates from superficial changes). The FreshnessTwiddler attribute is a named ranking adjustment for freshness. Google can distinguish between meaningful content updates and trivial changes.
- **E-Commerce Application**: Only substantive updates count toward freshness. Adding a new specification section, incorporating customer Q&A answers, updating compatibility data with a new model year, or adding installation notes — these are substantive. Changing punctuation, updating dates, or minor formatting changes — these are not meaningful freshness signals and may be ignored.
- **Replication Status**: Patent documentation is public record but may not reflect current Google implementation. The API leak provides directional insight but Google noted these attributes may be internal/experimental. Both sources should be treated as directional.
- **Boundary Conditions**: Patents describe patented approaches; Google may not implement every patented approach. The API leak attributes are interesting directional evidence but not definitive proof of how freshness is currently implemented.
- **Evidence Tier**: Silver — patent documentation (public but not confirmed as current implementation); API leak (directional evidence with caveats).

---

### Finding 6: Seasonal and Model-Year Products DO Benefit from Annual Freshness Updates
- **Source**: Google QDF mechanics (Finding 1) applied to product category research. Consistent with Singhal's description of QDF: "regularly recurring events" explicitly qualify for freshness boosts. https://blog.google/products/search/our-latest-quality-improvements-search/ Industry practitioner consensus on model-year content strategy.
- **Methodology**: Logical application of documented QDF algorithm (Gold-tier, Finding 1) to specific product categories. Practitioner consensus confirms seasonal patterns in keyword volume. No controlled study specifically isolating seasonal freshness update effects on rankings.
- **Key Finding**: Queries explicitly tied to model years, seasons, or annual events trigger QDF. "Best running shoes 2026," "2024 GR Supra mods," "Christmas gift guide electronics" — these are QDF-eligible. Products tied to model years, seasonal demand, or annual purchasing cycles benefit from content updated to reflect the current year's information, comparisons, and specifications.
- **E-Commerce Application**: For model-year products: (1) update content annually with the current year's specifications and compatibility; (2) update comparisons and competitor analysis for the current year; (3) include the current year in titles and descriptions (see title-formulas-serp-psychology.md Finding 11). For seasonal products: (1) create or update buying guides in the pre-season window (6–8 weeks before peak demand); (2) update product descriptions with seasonal use-case context.
- **Replication Status**: Structural application of documented QDF algorithm. The seasonal pattern in search behavior is observable in keyword research tools (Google Trends). No controlled study specifically on seasonal description updates.
- **Boundary Conditions**: Year modifiers only help when the product genuinely has model-year relevance. Adding "2026" to an unchanged commodity product misleads users and may be flagged as a quality issue.
- **Evidence Tier**: Gold — based on documented QDF algorithm mechanics; the specific seasonal application is practitioner consensus but the underlying mechanism is well-documented.

---

### Finding 7: Google Distinguishes Meaningful Updates from Superficial Changes
- **Source**: John Mueller, Google Search Central office hours (multiple sessions, 2020–2024) https://www.youtube.com/@GoogleSearchCentral; Gary Illyes, Search Off the Record podcast (multiple episodes) https://developers.google.com/search/podcasts/search-off-the-record. Consistent with Google patent documentation (Finding 5).
- **Methodology**: Direct Google spokesperson statements. Not a study.
- **Key Finding**: John Mueller has stated (multiple sessions) that changing a word or date without substantive content improvement is "just noise" from Google's perspective. Gary Illyes confirmed Google can evaluate whether a change represents meaningful new information vs. cosmetic modification. Google applies the "lastSignificantUpdate" concept (visible in API leak) — only substantive updates affect freshness evaluation.
- **E-Commerce Application**: Freshness-triggering updates must be substantive. Valid freshness updates for product pages: adding a compatibility table for new vehicle years, incorporating common customer questions as a new FAQ section, adding an installation guide section, updating specifications with newly-released variant information, adding expert editorial commentary. Not valid: updating a date in the text, changing "available in 3 colors" to "available in 3 color options," reformatting existing content.
- **Replication Status**: Consistent across multiple Google spokesperson statements over multiple years.
- **Boundary Conditions**: The threshold for "substantive" is not precisely defined by Google. A useful heuristic: would a genuine user notice that this page is more helpful than before? If yes, the update is substantive.
- **Evidence Tier**: Gold — multiple Google spokesperson statements (Mueller, Illyes); consistent over years.

---

### Finding 8: Fresh Buying Guides and Blog Content Can Transfer Freshness to Product Pages
- **Source**: Practitioner consensus on hub-and-spoke content architecture (see collection-page-architecture.md). Industry analysis on internal link equity flow and freshness signal transfer. Google Search Central ecommerce site-structure guidance: https://developers.google.com/search/docs/specialty/ecommerce/help-google-understand-your-ecommerce-site-structure. No peer-reviewed study; multiple SEO practitioners report this pattern.
- **Methodology**: Practitioner consensus based on observational experience with hub-and-spoke content models. The freshness transfer via internal links is a logical inference from Google's documented link equity flow mechanics. Not a controlled study.
- **Key Finding**: A freshly-published or updated buying guide that links to a product page may pass freshness signals (or at minimum, crawling priority) to the linked product pages via internal links. Google discovers new/updated content primarily through links — a freshly-updated buying guide signals to Googlebot that linked pages are relevant and worth re-evaluating.
- **E-Commerce Application**: Maintain a content calendar for buying guides and comparison articles. Update annually for model-year or seasonal categories. Link aggressively to product pages from fresh content (specific product anchors, not "click here" links). This compounds freshness signals from content pages to products while also building topical authority.
- **Replication Status**: Not independently studied with controlled methodology. Directionally plausible based on link equity mechanics and how Googlebot prioritizes crawling.
- **Boundary Conditions**: The freshness transfer, if it exists, is a secondary signal — it won't rescue poorly-structured or thin product pages. The primary benefit of fresh buying guides is their own ranking for informational queries; product page freshness benefit is supplementary.
- **Evidence Tier**: Silver — practitioner consensus with logical basis; no controlled study.

---

### Finding 9: REJECTED — "Content Updated Every 90–120 Days Maintains Rankings 4.2 Positions Higher"
- **Source**: Ocula Technologies blog (vendor marketing content). https://www.oculatechnologies.com/ Claimed a specific 4.2-position ranking advantage from 90–120 day content updates.
- **Methodology**: No published methodology. No sample size disclosed. Highly specific number (4.2 positions) with no supporting data. Single vendor source with direct financial interest in content management tools. This claim was identified in the scaffolded SEO reference files.
- **Key Finding**: **THIS FINDING IS REJECTED.** The claim lacks: published methodology, sample size, controls for confounding variables, and independent replication. The suspiciously precise number (4.2 positions) from a vendor with direct financial interest in content management solutions is a classic pattern of inflated marketing statistics. This contradicts Google's own guidance that evergreen content doesn't need regular updates.
- **E-Commerce Application**: Do not use this statistic. Do not schedule content updates based on this claim. Follow Google's own guidance: update content when it genuinely needs improvement or when product information changes — not on a calendar schedule.
- **Replication Status**: Not replicated. Contradicts Google spokesperson statements.
- **Boundary Conditions**: N/A — finding is rejected.
- **Evidence Tier**: Bronze (rejected — vendor marketing claim, no methodology).

> **⚠️ Quality Flag**: This finding was in the original scaffolded file. It has been **explicitly rejected** due to: no published methodology, vendor financial interest, suspiciously precise number, and direct contradiction of Google's documented position on evergreen content. Do not cite this statistic.

---

---

### Finding 10: March 2024 Helpful Content Integration — Superficial "Freshness Refreshes" Now Carry Downside Risk (NEW)
- **Source**: Google Search Central Blog, "March 2024 core update and spam policies update," https://developers.google.com/search/blog/2024/03/core-update-spam-policies (verified 200; prior B-audit URL `/2024/03/core-update` returns 404 — use corrected URL). Evidence: Google's official announcement of March 2024 core update.
- **Methodology**: Google official announcement — authoritative description of algorithm change.
- **Key Finding**: In March 2024, Google integrated the Helpful Content signals into the core ranking system, deprecating the separate Helpful Content Update. This integration means that superficial "freshness refreshes" — updating content cosmetically without substantive improvement — now carry **downside demotion risk** rather than just being wasted editorial effort. Prior to this integration, unhelpful content updated frequently might receive freshness signals; after integration, the Helpful Content classifier runs as part of core ranking and can actively demote pages that are updated but remain unhelpful.
- **E-Commerce Application**: When updating product pages for freshness purposes, ensure the update adds genuine value — new specifications, new FAQs, improved compatibility information, richer editorial content. Cosmetic updates (changing dates, reformatting existing text) may now work against you by triggering re-evaluation under the Helpful Content classifier. The principle from Finding 7 (meaningful vs. superficial updates) is now more consequential than before March 2024.
- **Replication Status**: Google official announcement — well-documented in industry coverage. The integration is confirmed; the specific causal mechanism (freshness update → HCU penalty) is an inferred practical consequence that aligns with Google's stated goal.
- **Boundary Conditions**: The Helpful Content integration primarily affects pages Google perceives as created primarily for search engines rather than users. Well-crafted, informative product pages are unlikely to be affected by routine content updates.
- **Evidence Tier**: Gold — Google Search Central official announcement (March 2024 core update).

---

### Finding 11: `lastmod` Is a Crawl-Scheduling Hint, Not a Direct Ranking Signal (NEW)
- **Source (primary — Google docs)**: Google Search Central, "Build and submit a sitemap," https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap. Official docs state Google uses `lastmod` when it is "consistently and verifiably accurate." Official docs also state: Google **explicitly ignores** `<priority>` and `<changefreq>` elements entirely. **Source (spokesperson — Gold)**: Gary Illyes, "Search Off the Record" podcast (multiple episodes 2023–2025): characterized `lastmod` as influencing crawl scheduling (when Googlebot revisits a URL) rather than directly affecting ranking weight.
- **Methodology**: Official Google documentation + Gary Illyes spokesperson statements. Illyes's characterization of lastmod as "crawl scheduling" is an interpretation attributable to him, not verbatim text from the official sitemap docs.
- **Key Finding**: Official Google sitemap docs establish: (1) Google uses `lastmod` only when it is consistently and verifiably accurate; (2) `<priority>` and `<changefreq>` are explicitly ignored by Google. Gary Illyes has characterized `lastmod` as influencing *when* Googlebot revisits a URL (crawl scheduling), not the ranking weight of the URL. Even accurate `lastmod` does not by itself boost rankings — its value is ensuring prompt re-crawl of genuinely-updated content. The crawl-scheduling framing is Illyes's interpretation, not a verbatim statement in the official sitemap docs; do not attribute "not a ranking signal" directly to the sitemap documentation.
- **E-Commerce Application**: Use `lastmod` accurately for genuinely updated pages (see Finding 3 for consequences of false dates). Do not populate `<priority>` or `<changefreq>` — Google ignores both. The payoff for accurate `lastmod` is faster re-crawl after substantive content updates, not a ranking boost.
- **Replication Status**: Official docs are authoritative. Illyes podcast statements are spokesperson-level Gold (consistent, attributable, on-record).
- **Boundary Conditions**: Accurate `lastmod` is valuable only when combined with genuinely updated, crawl-worthy content. For low-priority pages (thin, duplicate, noindexed), prompt re-crawl has no SEO benefit regardless of `lastmod` accuracy.
- **Evidence Tier**: Gold for what the official docs say (Google uses lastmod when accurate; ignores priority/changefreq); Gold for Illyes spokesperson framing (crawl-scheduling characterization). Note: the "not a ranking signal" claim is Illyes's characterization, not official doc text — cite accordingly.

---

## Methodological Notes and Caveats

1. **QDF is not directly observable.** No tool directly shows whether a query has QDF applied. Infer from keyword research patterns — queries where recent results dominate the SERPs are likely QDF-eligible.

2. **The API leak (Finding 5) is directional evidence, not authoritative.** Google acknowledged the leaked document was real but noted the API may be internal/experimental and not reflective of current production systems. Use directionally.

3. **Review freshness strategy (Finding 4) depends on compliance with FTC Consumer Review Rule.** Review gating, suppression, or fabrication is illegal under regulations effective October 2024. See ugc-reviews-seo.md for full legal framework.

---

## Sources Consulted

- Google Freshness Update Announcement (November 2011, primary): https://googleblog.blogspot.com/2011/11/giving-you-fresher-more-recent-search.html
- Amit Singhal / New York Times QDF Origin (2007, paywalled secondary): https://www.nytimes.com/2007/06/03/technology/03google.html
- Google Search Central Blog, March 2024 Core Update (F10): https://developers.google.com/search/blog/2024/03/core-update-spam-policies
- Google Search Central Build a Sitemap (F11): https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- John Mueller Reddit AMA (April 2025) on lastmod gaming
- Gary Illyes Search Off the Record Podcast (Google Podcasts)
- Search Engine Land QDF Guide: https://searchengineland.com/guide/query-deserves-freshness-qdf
- Google US Patent US8832088B1: https://patents.google.com/patent/US8832088B1
- SparkToro API Leak Analysis (May 2024): https://sparktoro.com/blog/a-critical-examination-of-the-google-search-api-document-leak/
- GatherUp Review Recency Statistics: https://gatherup.com/blog/online-review-statistics/
- Search Engine Journal Freshness Algorithm History: https://www.searchenginejournal.com/google-algorithm-history/freshness-algorithm/
