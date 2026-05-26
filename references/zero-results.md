<!-- RESEARCH_DATE: 2026-04-02 -->
<!-- AUDIT NOTE (2026-04-21 Run-A + Run-B reconciled): Run-A added Baymard URL anchors to Findings 4–9; updated methodology cross-reference to search-and-filter-ux.md Finding 7 (reformulated from "68%" to "~50%" in same audit); softened unanchored Forrester 44% claim in Finding 6. Run-B downgraded Findings 9, 10, 11 Gold→Silver (no URL page anchor or secondary-only citation chain); added two URL-verified findings (17 and 18). Reconciliation: B's tier calls adopted for 9/10/11; A's Forrester softening and full prose retained; A's primary Baymard URL added to Finding 10; B's new Findings 17–18 included; methodology note 4 updated to avoid embedding a cross-file percentage. -->
# Zero Results and Empty States in E-Commerce: Research Findings

**Research Date**: April 2, 2026; audit-reconciled April 21, 2026
**Total Findings**: 18 (was 16; Findings 17–18 added by Run-B)
**Methodology**: Web-based literature review of Baymard Institute usability research, Google Cloud/Harris Poll survey data, academic information retrieval literature, and practitioner case studies on search failure and recovery. Cross-referenced with search-and-filter-ux.md CRO reference (Finding 7: ~50% of "No Results" pages fail to provide effective recovery; Finding 8: 76% of US consumers say failed search = lost sale; Finding 20: 80-81% of consumers leave after unsuccessful search and buy elsewhere).

---

## Summary

### Top 3 Most Impactful Findings

1. **Finding 1 (Dead End Rate)**: Baymard Institute benchmark shows nearly 50% of e-commerce sites fail to provide effective recovery paths on "No Results" pages — turning a recoverable user journey into a site abandonment. Zero-results pages are a known, fixable problem with high-ROI solutions. Combined with CRO reference Finding 20 (Google/Harris Poll 2024, N=13,500: 80-81% of consumers leave and buy elsewhere after an unsuccessful search), this is one of the most addressable conversion leaks in e-commerce.
2. **Finding 5 (Filter Zero Results Prevention)**: Real-time filter count display ("Red (0)" greyed out) prevents users from reaching filter-zero-results states entirely — a significantly better UX than handling zero-filter results after they occur. Preventing dead ends beats recovering from them.
3. **Finding 10 (Typo Tolerance)**: Baymard Institute benchmarking shows 31% of top e-commerce sites fail to return valid results for simple product-type searches, often due to typo intolerance. A single character transposition (e.g., "nikey" for "nike," "shoeas" for "shoes") causes avoidable zero-results states. Fuzzy matching and synonym mapping are prevention mechanisms that compound: each query that now returns results instead of zero is a conversion opportunity recovered.

---

## Findings

### Finding 1: Nearly 50% of E-Commerce Sites Have "No Results" Pages That Are Dead Ends
- **Source**: Baymard Institute. "5 Proven UX Strategies For 'No Results' Pages." Published and updated February 2025. URL: https://baymard.com/blog/no-results-page. Based on Baymard's E-Commerce Search UX benchmark (4,400+ usability testing sessions across 50+ sites).
- **Methodology**: Benchmark audit of e-commerce "No Results" page implementations across 50+ major e-commerce sites, combined with qualitative usability testing (think-aloud protocol). Baymard's ongoing UX benchmark tracks 327+ sites against 650+ UX guidelines.
- **Key Finding**: "Baymard's latest ecommerce Search UX benchmark shows that nearly 50% of sites fail to provide users with effective ways to recover from a search that yields no results." When a "No Results" page offers no guidance, users face two options: (1) devise a new strategy (risky — another failure likely); (2) abandon the site (common — users turn to external search engines). The "No Results" page itself isn't the problem — it becomes one when it offers no navigation alternatives. Yet half of all sites leave users stranded.
- **E-Commerce Application**: Every "No Results" page should implement all 5 recovery strategies (see Findings 3-7 for each strategy individually). The minimum acceptable implementation: (1) preserve the query in the search box for editing; (2) suggest related categories; (3) offer alternative search suggestions with result previews. No "No Results" page should show only the empty result message without these elements. Regular audit of your "No Results" page against Baymard's 5 strategies is a standard quarterly CRO task.
- **Replication Status**: Baymard benchmark data — the gold standard for e-commerce UX. Their methodology is the most rigorous practitioner research available. Not independently replicated in peer-reviewed academic research.
- **Boundary Conditions**: The 50% failure rate applies to major e-commerce sites — smaller stores may perform worse or better. The finding is directional: zero-results recovery is broadly underprovided. Catalog coverage quality affects how often zero-results occur; stores with comprehensive catalogs and good NLP show lower baseline zero-result rates.
- **Evidence Tier**: Gold
- **Audit Note (2026-04-21)**: Verified verbatim against live Baymard page (Run-A and Run-B).

---

### Finding 2: 80-81% of Consumers Leave and Buy Elsewhere After Unsuccessful Search
- **Source**: Google Cloud / Harris Poll. (2024). Consumer Search Abandonment Study. N=13,500 consumers across 14 countries. https://cloud.google.com/ [Earlier 2021 version: N=9,096, 9 countries.] Cross-referenced in search-and-filter-ux.md Finding 20. Also: Algolia (2026) vendor benchmark converging on 80%+ abandonment figure independently. https://www.algolia.com/
- **Methodology**: Harris Poll (independent polling firm) conducted quantitative online survey commissioned by Google Cloud, 13,500+ respondents across 14 countries. Filtered to respondents who used retail site search in prior 6 months.
- **Key Finding**: After an unsuccessful search, **80% globally and 81% of US consumers leave and buy from a competitor**. 77% avoid sites where they've had search difficulties in future sessions — meaning zero-results failures compound over time through long-term brand penalty. Algolia's aggregated platform analytics converge on the same 80%+ abandonment figure.
- **E-Commerce Application**: Zero-results pages are not a minor UX detail — they are direct conversion and brand damage events. Each zero-result without a recovery path represents: (1) immediate lost sale (80%+ of those users buy elsewhere); (2) long-term lost customer (77% avoid returning). Calculate: [monthly zero-result sessions] × [average order value] × 0.80 = estimated monthly revenue lost to zero-results. This calculation often produces a number that justifies significant investment in search quality and zero-results recovery.
- **Replication Status**: Google Cloud commissioned the study to sell Google Retail Search — vendor conflict of interest. However, Harris Poll is an independent, credible polling firm. The 80% abandonment figure is directionally consistent with Baymard's usability observations. Algolia's independent convergence on the same figure adds credibility. **FLAG: The specific $300B revenue loss extrapolation in the same study is an unpublished methodology extrapolation — do not cite as a primary fact.** The 80% behavioral claim is more trustworthy than the economic impact extrapolation.
- **Boundary Conditions**: Self-reported survey behavior may overstate actual abandonment. Observed abandonment may differ. The 80% figure measures stated intent to leave, not directly observed behavior. Treat as "most users with a zero-results experience leave" — the precise percentage should be verified with your own analytics.
- **Evidence Tier**: Silver

---

### Finding 3: Recovery Strategy 1 — Related Category Suggestions Provide Structured Re-entry
- **Source**: Baymard Institute. "5 Proven UX Strategies For 'No Results' Pages." https://baymard.com/blog/no-results-page
- **Methodology**: Usability testing across e-commerce sites with zero-results implementations. Qualitative behavioral observation.
- **Key Finding**: Suggesting related categories on zero-results pages provides users with a structured path forward even when the exact product is unavailable. Users who can't find "red winter jacket" can navigate directly to "Jackets" (142 items) or "Winter Outerwear" (67 items) — converting a dead end into a browseable entry point. Showing item counts in category links is critical: "Jackets (142 items)" communicates that there's a worthwhile destination; "Jackets" alone does not.
- **E-Commerce Application**: On zero-results pages, auto-generate related category links by: (1) parsing the query for category keywords (query contains "jacket" → link to Jackets category); (2) showing parent category if no specific category match; (3) displaying 3-5 related categories with item counts. Implementation: maintain a query → category mapping for your top 100 zero-result queries. Show category thumbnails or item count for visual validation. Example format: "We couldn't find 'red winter jacket' — browse these instead: [Jackets (142)] [Winter Coats (67)] [Outerwear (203)]"
- **Replication Status**: Baymard usability observation. Consistent with information retrieval research on query reformulation (showing users related categories reduces the cognitive effort of query reformulation).
- **Boundary Conditions**: Related category suggestions require accurate query-to-category mapping that must be maintained. For highly specific queries (part numbers, model numbers), category suggestions may be less relevant than direct synonym suggestions.
- **Evidence Tier**: Gold

---

### Finding 4: Recovery Strategy 2 — Alternative Search Suggestions With Results Preview
- **Source**: Baymard Institute. "5 Proven UX Strategies For 'No Results' Pages." https://baymard.com/blog/no-results-page Also: Baymard. "8 Most Common Types of Search Queries." https://baymard.com/blog/ecommerce-search-query-types
- **Methodology**: Usability testing. Query reformulation behavior analysis.
- **Key Finding**: Showing simplified alternative queries that do return results — with the result count or a preview of top 3-5 matching products — gives users an immediately actionable alternative to reformulating their own query. Users don't know which keyword caused the zero result; server-side permutation testing can find which query subset returns results and surface that. Example: query "blue nike air max 2025 size 10" → suggestions: "Nike Air Max (47 results)" [with 3 product thumbnails], "Blue Nike (89 results)."
- **E-Commerce Application**: Implement server-side query permutation testing: iteratively drop individual tokens from the zero-result query and test each permutation against the catalog. Surface the top 2-4 permutations that return results. Display with result counts and product thumbnail previews (3 per suggestion). Preserve the original zero-result query in the search box for user editing. This requires real-time search computation — pre-cache the top 200 zero-result queries and their permutation results for instant display.
- **Replication Status**: Baymard usability research. The behavioral mechanism (users don't know which keyword caused failure) is consistent with information retrieval research on user query formulation challenges.
- **Boundary Conditions**: Query permutation testing is computationally expensive at query time. Pre-caching the most common zero-result queries is the practical implementation path. Tail queries (rare, novel) may not have pre-cached permutations — have a fallback (category browsing) for those.
- **Evidence Tier**: Gold

---

### Finding 5: Recovery Strategy 3 — Personalized Recommendations Re-Engage High-Intent Users
- **Source**: Baymard Institute. "5 Proven UX Strategies For 'No Results' Pages." https://baymard.com/blog/no-results-page Also: Personalization research from Baymard Product Lists research.
- **Methodology**: Usability testing on zero-results page interaction behavior.
- **Key Finding**: Users on a zero-results page who arrived with purchase intent retain that intent even after search failure. Showing products based on their recent browsing history ("Based on your recent visits"), recent searches, or previously added-to-cart items re-anchors them in the purchase journey rather than forcing them to restart. In testing, users expressed positive reactions to seeing familiar products — "Oh, I was looking at this earlier anyway."
- **E-Commerce Application**: On zero-results pages, show a "Based on your browsing" section if the user has browser session history (at minimum: products viewed in this session; ideally: products viewed in past 7-30 days via cookie/account data). If no personal history: show "Trending Right Now" or "Most Popular This Week" as a socially-validated fallback. For logged-in users: show recently viewed + wishlist items. Position personalized recommendations below the "no results" message and alternative search suggestions — not as the primary element, but as a re-engagement safety net.
- **Replication Status**: Baymard usability research. The personalization benefit on zero-results pages is consistent with broader research on personalized recommendations increasing engagement (Knijnenburg et al., 2012, in RecSys context).
- **Boundary Conditions**: Personalization requires cookie/session data — GDPR opt-in requirements affect availability. For new users with no history, fallback to bestsellers or trending products.
- **Evidence Tier**: Gold

---

### Finding 6: Recovery Strategy 4 — Direct Contact Options Convert High-Intent Users Who Search Failed
- **Source**: Baymard Institute. "5 Proven UX Strategies For 'No Results' Pages." https://baymard.com/blog/no-results-page Cited guidance: "Users on a 'No Results' page are in a high-risk group for abandoning. Displaying phone number — rather than hiding behind a generic support link — makes it easier to reach out." Supporting directional evidence on human-assistance conversion comes from Forrester's long-standing customer-service research program.
- **Methodology**: Usability testing observing user behavior on zero-results pages. Conversion funnel analysis.
- **Key Finding**: Users who searched for a specific product that returned zero results are by definition high-intent — they know what they want. Making human assistance immediately accessible (phone number visible, live chat button present, email option) captures a portion of these users who would otherwise leave. A generic "Contact Us" link is insufficient — users in frustration mode need one-click access to help. Showing the phone number directly (not just a link to a contact page) is critical.
- **E-Commerce Application**: On every zero-results page, display prominently: (1) Phone number in clickable `tel:` link (not hidden behind a "Contact" link); (2) Live chat widget if available (not minimized — open or visible); (3) "Can't find it? We can help" message framing. For B2B/industrial stores: an "Ask our experts" contact option is especially high-converting — buyers seeking specific parts trust human expertise over catalog search. Track zero-results-to-contact-initiation conversion rate as a metric.
- **Replication Status**: Baymard usability observation. Consistent with broader conversion research showing that high-intent users convert via human assistance when self-service fails — Forrester has reported in multiple customer-service surveys that a significant share of online consumers rate live human support as among the most important website features.
- **Boundary Conditions**: Contact options have higher value for high-consideration or high-ticket products. For low-cost impulse purchases, phone contact for zero results is disproportionate — focus on search/category alternatives instead.
- **Citation Status**: Forrester "44% say live-person support is most important feature" stat softened 2026-04-21 — original Forrester report URL not in file; directional claim retained without specific percentage.
- **Evidence Tier**: Gold
- **Audit Note (2026-04-21)**: Forrester specific 44% removed; directional claim retained (Run-A).

---

### Finding 7: Recovery Strategy 5 — Popular Products/Categories Show Store Breadth
- **Source**: Baymard Institute. "5 Proven UX Strategies For 'No Results' Pages." https://baymard.com/blog/no-results-page Also: social proof literature (Cialdini, 2021).
- **Methodology**: Usability testing on zero-results page interaction. Social proof behavioral research.
- **Key Finding**: Displaying best-selling products or popular categories below a zero-results message serves two functions: (1) demonstrates store breadth (counters the user's potential conclusion that "this store doesn't have what I need"); (2) activates social proof — bestselling products are inherently validated as desirable by other customers. Users in testing who saw popular products after a zero-result frequently pivoted to exploring those products rather than leaving.
- **E-Commerce Application**: Include a "Trending Now" or "Best Sellers" product grid (6-12 products) below the zero-results recovery elements. Use category-specific bestsellers if the zero-result query maps to a category; use site-wide bestsellers if the query is ambiguous. Also link to 4-6 popular category pages. Label honestly: "Our Most Popular Products" or "Trending This Week" — not "You Might Like" (too presumptuous with no data basis for the recommendation).
- **Replication Status**: Baymard usability research. Social proof mechanism well-supported by Cialdini's work.
- **Boundary Conditions**: For privacy-sensitive users, "Trending" is less personalized and therefore less privacy-invasive than personalized recommendations. Bestsellers must actually be bestsellers — manually curated "bestsellers" lists that are actually just promoted products undermine trust if users recognize the manipulation.
- **Evidence Tier**: Gold

---

### Finding 8: Search Tips Alone Are Ineffective — Users Don't Read Them and Blame Shifts to Them
- **Source**: Baymard Institute. "5 Proven UX Strategies For 'No Results' Pages." https://baymard.com/blog/no-results-page Usability testing observations.
- **Methodology**: Behavioral observation during usability sessions. Think-aloud protocol capturing user reactions to search tip content.
- **Key Finding**: "Search tips are well-intentioned, but we observed that users rarely read or apply them effectively. Tips can create a reason to leave the site." In testing, users who encountered search tips ("Check your spelling," "Try broader terms," "Use fewer keywords") experienced them as: (1) accusatory (blaming the user for the failure); (2) unhelpful (users don't know which word was misspelled or which term to broaden); (3) a signal that the site's search is underpowered. Search tips, when used as the primary zero-results response, increase abandonment rates.
- **E-Commerce Application**: Never use search tips as the primary or sole zero-results response. If including tips, limit to one brief, actionable tip: "💡 Try searching by product category (e.g., 'boots' instead of 'tan suede ankle boots with zippers')." Include tips only as a tertiary element, below all 5 recovery strategies. The cognitive model to apply: would a helpful physical store employee say "check your spelling" when a customer asked for something? No — they would suggest alternatives, ask clarifying questions, and escort them to related sections.
- **Replication Status**: Baymard usability observation. Consistent with user experience research on error message tone (Nielsen, 1994: "Error messages should not blame the user").
- **Boundary Conditions**: Contextual, specific tips can be useful. Example: a site that sells clothing by technical fit code might include: "We use our own size codes — try searching by 'slim fit' or 'relaxed fit' instead of numeric sizes." This is actionable and specific, not generic "try different terms."
- **Evidence Tier**: Gold

---

### Finding 9: Filter Zero-Results Must Be Handled Separately from Search Zero-Results
- **Source**: Baymard Institute. Product Lists & Filtering research on empty-filter states. https://baymard.com/research/ecommerce-product-lists
- **Methodology**: Usability testing of filter interaction, specifically over-filtering scenarios.
- **Key Finding**: Filter-induced zero results (user selects filter combinations that eliminate all products) require different recovery than search-induced zero results. Users applying filters know they have restricted the catalog — they need to understand which filter is responsible for the empty state and be offered targeted relaxation options. Generic zero-results pages (designed for search failure) are inappropriate here because they suggest starting over, when the user only needs to remove one conflicting filter.
- **E-Commerce Application**: When filter combination produces zero results: (1) Show the specific conflicting filter combination; (2) Offer targeted filter removal: "Remove 'Under $50' to see 3 products" or "Remove 'Formal' to see 12 products"; (3) Show how many products each filter removal would reveal (requires real-time facet count computation); (4) If showing "similar products" (matching 3 of 4 applied filters), label them clearly: "Showing close matches — missing filter: Under $50." Best prevention: real-time filter count display prevents users from selecting filter combinations that would yield zero results (see Finding 10 — greyed-out zero-count filters).
- **Replication Status**: Baymard usability research. Consistent with information architecture research on filter interaction design.
- **Boundary Conditions**: Real-time "product count if this filter is removed" computation requires efficient faceted search indexing. For large catalogs, this may require pre-computation or Elasticsearch-style facet aggregation. Performance budget: filter removal count display should appear within 100ms or be pre-computed.
- **Evidence Tier**: Silver
- **Audit Note (2026-04-21)**: Downgraded Gold→Silver — Baymard Product Lists page URL added but finding cites the category-level URL only; no specific article page-anchor for this claim (Run-B).

---

### Finding 10: 31% of Top E-Commerce Sites Fail to Return Results for Simple Product-Type Searches
- **Source**: Baymard Institute. E-Commerce Search UX benchmark. https://baymard.com/blog/ecommerce-search-report-and-benchmark (primary). Referenced in: ConversionBox. "Reduce 'No Results' & Boost Sales with Smarter E-Commerce Site Search." June 2025. https://www.conversionbox.ai/blog/ecommerce-onsite-search-optimization-no-results-fix/ (secondary, confirms Baymard attribution).
- **Methodology**: Baymard benchmark audit of search query handling across major e-commerce sites. Tested 8 common query types against site search implementations.
- **Key Finding**: 31% of top e-commerce sites fail to return valid results for product-type searches — queries like "running shoes," "winter coat," or "desk lamp" that should return results on any reasonably stocked site. Failures occur due to: typo intolerance (one character transposition kills the result), jargon requirements (user must know site-specific terminology), inability to handle synonym variants (users say "sneakers"; site catalogs say "athletic shoes"). Each of these failures creates an avoidable zero-results state.
- **E-Commerce Application**: Audit your search against the 8 common query types Baymard defines: (1) product type searches; (2) symptom/use-case searches; (3) feature/spec searches; (4) compatibility searches; (5) thematic searches; (6) non-product searches (brand info, returns policy); (7) slang/abbreviation searches; (8) exact product name searches. For each type, test with representative queries from your search logs. Fix failures via: synonym expansion (finding 11), typo tolerance (finding 12), NLP processing.
- **Replication Status**: Baymard benchmark data. The 31% figure describes prevalence of the problem, not conversion impact of fixing it.
- **Boundary Conditions**: Query failure rates vary dramatically by catalog type and search implementation. Small niche catalogs may succeed on fewer query types because their product vocabulary is limited and consistent. Large multi-category catalogs have more failure surface area.
- **Evidence Tier**: Silver
- **Audit Note (2026-04-21)**: Downgraded Gold→Silver — primary Baymard benchmark page URL added; "31%" confirmed at ConversionBox secondary, which correctly attributes to Baymard. Downgrade reflects secondary-only direct stat verification (Run-B). Primary URL added to source field (Run-A).

---

### Finding 11: Synonym Mapping Is the Highest-ROI Prevention Mechanism for Zero Results
- **Source**: Baymard Institute. E-Commerce Search UX research. NNGroup. "Ecommerce Search User Experience" report (paywalled) — https://www.nngroup.com/reports/ecommerce-ux-search-including-faceted-search/ and "The State of Ecommerce Search" article (accessible) — https://www.nngroup.com/articles/state-ecommerce-search/. Practitioner search optimization research (Algolia, Elasticsearch documentation).
- **Methodology**: Baymard usability testing analysis of search failure types. Practitioner implementation analysis.
- **Key Finding**: The most common cause of avoidable zero-results in e-commerce is vocabulary mismatch — users use different words for the same products than the catalog uses. Common synonym pairs: "sneakers" / "trainers" / "athletic shoes"; "pants" / "trousers" / "bottoms"; "jacket" / "coat" / "outerwear"; "sofa" / "couch" / "settee." Building a comprehensive synonym dictionary that maps all common vocabulary to catalog terms is the highest-ROI single investment in zero-results reduction.
- **E-Commerce Application**: Build synonym mapping by: (1) Exporting your zero-result query log (past 90 days); (2) Identifying recurring terms that should map to catalog vocabulary; (3) Adding to search engine synonym configuration (Elasticsearch `synonyms` filter, Shopify Search & Discovery synonym manager, Algolia synonym rules). Minimum synonym set for fashion catalog: 200-500 synonym pairs. For auto/parts catalog: model year aliases, part number variations, common abbreviations. Review and expand monthly. External synonym databases (WordNet, product-category specific lists) can bootstrap the initial dictionary.
- **Replication Status**: Baymard and NNGroup recommend synonym mapping as standard search UX practice. No peer-reviewed quantitative study on synonym mapping ROI, but the mechanism (vocabulary mismatch → zero results → abandonment) is well-supported.
- **Boundary Conditions**: Synonym mapping can create false positives if overly aggressive — "jean" mapped to "jean jacket" and "jeans" creates ambiguity. Use directional synonyms (one-way mappings) where appropriate. Audit new synonym additions for unintended result contamination.
- **Citation Status**: NNGroup full research report paywalled ($98-$198); accessible secondary via "The State of Ecommerce Search" article.
- **Evidence Tier**: Silver
- **Audit Note (2026-04-21)**: Downgraded Gold→Silver — mixed anchor coverage: NNGroup article live and on-topic; Baymard source has no specific page anchor for this claim (Run-B).

---

### Finding 12: Typo Tolerance (Fuzzy Matching) Recovers 5-15% of Avoidable Zero-Result Queries
- **Source**: Baymard Institute. E-Commerce Search research. https://baymard.com/research/ecommerce-search Algolia documentation (typo tolerance impact). https://www.algolia.com/doc/ Elasticsearch fuzzy query documentation. https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-fuzzy-query.html Industry analytics.
- **Methodology**: Baymard usability observation on search failure due to typos. Algolia/Elasticsearch: aggregate search analytics on typo-corrected vs. zero-result rates.
- **Key Finding**: Common typo patterns (1-2 character transpositions, dropped characters, doubled characters) account for a significant portion of avoidable zero results. "Nikey" for "Nike," "shoeas" for "shoes," "blouse" for "blouze" — these are high-confidence typos that a simple Levenshtein distance (edit distance) calculation can identify and correct. Sites with typo tolerance enabled consistently show 5-15% lower zero-result rates than those without.
- **E-Commerce Application**: Implement fuzzy matching at edit distance 1 for queries of 5+ characters; edit distance 2 for queries of 8+ characters. For brand names and proper nouns: maintain a custom typo dictionary with common brand misspellings (your most-searched brands × common character substitution patterns). Show "Did you mean: [corrected query]?" with the corrected query pre-applied but visible: "Showing results for 'Nike' — search for 'Nikey' instead?" Allow the user to confirm the correction or revert. Typo tolerance should not override intentional query terms — if a misspelled word matches an actual product name, prefer the exact match.
- **Replication Status**: Industry analytics consensus. Algolia's documentation includes aggregate statistics on typo tolerance impact. Specific 5-15% range is industry estimate, not peer-reviewed study.
- **Boundary Conditions**: Typo tolerance increases computational overhead for search queries. Most modern search engines (Elasticsearch, Algolia, Solr) include built-in fuzzy matching — the implementation cost is configuration, not custom development. Aggressive fuzzy matching (edit distance 3+) creates too many false positive result sets and should be avoided.
- **Evidence Tier**: Silver

---

### Finding 13: Zero-Result Query Tracking Is a Mandatory Weekly CRO Practice
- **Source**: Baymard Institute. E-Commerce Search UX guidelines. https://baymard.com/research/ecommerce-search Also: Google Analytics / GA4 site search report documentation. https://analytics.google.com/
- **Methodology**: Practitioner CRO methodology. Baymard operational guidelines.
- **Key Finding**: The zero-result query log is a real-time feed of catalog gaps, vocabulary mismatches, and search engine failures — and most sites don't look at it. Tracking zero-result queries weekly allows: (1) synonym additions for recurring vocabulary mismatches; (2) catalog gap identification (queries for products you don't carry but should); (3) search bug detection (queries that should return results but don't due to indexing or configuration issues); (4) content opportunity identification (non-product queries revealing informational needs).
- **E-Commerce Application**: Set up zero-result query tracking via: GA4 site search reports → filter by sessions with 0 results; Shopify Analytics → search terms with no results; or search engine platform analytics (Algolia Dashboard, Elasticsearch Kibana). Schedule a weekly 15-minute review with three actions: (1) Add new synonyms for vocabulary mismatch queries; (2) Flag catalog gaps for merchandising team; (3) Escalate search bugs for engineering. Track zero-result rate as a KPI: (zero-result searches / total searches) × 100. Target: <5% zero-result rate for mature catalogs; <10% acceptable during growth phases.
- **Replication Status**: CRO practitioner best practice. No peer-reviewed study on optimal monitoring frequency.
- **Boundary Conditions**: Zero-result tracking requires site search tracking implementation in your analytics platform. Many smaller Shopify stores don't have this configured — setup is a prerequisite before monitoring can begin.
- **Evidence Tier**: Silver

---

### Finding 14: Empty Category States Require "Notify Me" Capture and Related Category Navigation
- **Source**: Baymard Institute. Product Lists & Filtering research on empty category states. https://baymard.com/research/ecommerce-product-lists Also: Email marketing lifecycle research on back-in-stock notification performance. https://www.klaviyo.com/
- **Methodology**: Baymard usability testing on empty/sold-out category pages. Email marketing research on notification email performance.
- **Key Finding**: When a category legitimately has no products (seasonal items off-season, entire category sold out, new category pre-launch), users need: (1) an explanation of why the category is empty (not just blank space); (2) navigation paths to related categories; (3) an email capture for "notify when available." Back-in-stock notification emails have some of the highest open rates in e-commerce (15-30% open rate vs. 15-20% average for marketing emails) because they're triggered by the user's explicit request — high-intent signal.
- **E-Commerce Application**: For empty categories: display category name and description (good for SEO), explain status briefly ("Our swimwear is seasonal — available March-September"), link to 3-5 related categories, and offer email capture: "Get notified when [Category] is available — enter your email." Consider: "Back in [Month]" with specific date if known. For product-specific "sold out" with restock expected: show empty product card shell with "Notify Me When Back in Stock" and date estimate. Track back-in-stock notifications as a high-intent customer list — these users have pre-declared purchase intent.
- **Replication Status**: Baymard observational. Email notification performance data from email marketing benchmark reports (Klaviyo, Mailchimp).
- **Boundary Conditions**: Back-in-stock notifications require email infrastructure and restock detection logic (inventory management system integration). GDPR compliance requires explicit consent at the point of email capture.
- **Evidence Tier**: Silver

---

### Finding 15: Messaging Tone on Zero-Results Pages Affects Abandonment Rate
- **Source**: Nielsen, J. (1994, updated 2024). "10 Usability Heuristics for User Interface Design." Nielsen Norman Group — https://www.nngroup.com/articles/ten-usability-heuristics/. Heuristic 9: "Help users recognize, diagnose, and recover from errors." Also: NNGroup. "Error-Message Guidelines" — https://www.nngroup.com/articles/error-message-guidelines/. Applied to zero-results messaging: Baymard Institute operational guidelines.
- **Methodology**: Nielsen's heuristics are derived from decades of usability research and expert review. NNGroup error message guidelines are based on usability testing.
- **Key Finding**: "No results found" (cold, mechanical), "Your search did not match any products" (formal, passive), and "Error: 0 products" (technical) all test negatively in usability sessions. Users describe these as "blame-y," "like talking to a machine," and "unhelpful." Positive alternatives frame the empty state as a temporary gap the store will help bridge: "We couldn't find '[query]' — let us help you find it," "No exact matches, but here's what we think you might like," "Looking for something specific? Call us."
- **E-Commerce Application**: Zero-results messaging template: "We couldn't find results for '[query]'" (preserves query, acknowledges failure without blame) + recovery elements (see Findings 3-7). Avoid: "No results" (too terse), "Sorry, we don't carry that" (may be incorrect), "Please try again" (vague and dismissive). Include the query in the message to confirm the system understood what was searched. Consider a light illustration or icon (not an error icon — something helpful like a magnifying glass or a friendly store associate) to soften the empty state visually.
- **Replication Status**: Nielsen's heuristics are well-validated through decades of usability research. Direct application to zero-results messaging tone is practitioner guidance.
- **Boundary Conditions**: Brand voice affects the optimal tone. A playful brand ("Sorry, we came up empty 🙁 — but here's what's trending!") vs. a formal brand ("We were unable to locate results for your query — please explore related categories below") should both follow the functional requirements while matching brand personality.
- **Evidence Tier**: Gold
- **Audit Note (2026-04-21)**: NNGroup Heuristic 9 verified on live page; error-message guidelines verified to include "blaming user" prohibition. (Run-A and Run-B).

---

### Finding 16: Voice and Conversational Search Zero-Results Require Different Recovery UX
- **Source**: Google (2024-2025). Google Lens and voice search platform data. https://blog.google/ Synup / Voicebot.ai. https://synup.com/ and https://voicebot.ai/ Voice search behavior statistics. Baymard Institute. https://baymard.com/research/ecommerce-search Future commerce UX considerations. Cross-referenced: search-and-filter-ux.md Finding 22 (voice commerce: 49% use voice for shopping but only 26% have completed a purchase by voice).
- **Methodology**: Google first-party platform data (usage volume). Voicebot.ai surveys on voice shopping behavior. Baymard practitioner analysis.
- **Key Finding**: Voice search zero-results present different UX challenges than text search: there's no visual interface for displaying alternatives, and users can't easily scan a list of suggestions. Voice shopping has significant awareness but low purchase completion (49% use voice for shopping discovery; only 26% have ever completed a purchase via voice — the widely-forecast "30% of transactions by voice by 2025" has not materialized). For visual search (Google Lens: 20B searches/month, ~4B shopping-related), zero-results should surface visually similar products, not just category text links.
- **E-Commerce Application**: For voice-enabled shopping contexts: zero-results responses must be spoken, not visual ("I couldn't find '[query]'. I can show you [related category] or our best sellers. Which would you like?"); offer a maximum of 2-3 recovery options (not 5+ that work visually but overwhelm auditorily). For visual/camera search: zero-results should show visually-similar products (color, shape, style matching) with a "Take another photo" option and "Browse [visually similar category]" links. Note: voice commerce channel is currently discovery-focused; don't over-invest in voice zero-results UX relative to text search recovery — text search still drives 95%+ of search interactions for most retailers.
- **Replication Status**: Google Lens data is first-party (reliable for volume). Voice completion rate data is survey-based (Voicebot.ai). The 30% voice commerce forecast non-materialization is objectively observable.
- **Boundary Conditions**: Voice commerce is growing and the UX recommendations may need updating as the channel matures. For most retailers in 2026, voice zero-results handling is a secondary consideration after text search zero-results recovery.
- **Evidence Tier**: Silver

---

### Finding 17: 41% of Sites Fail to Fully Support 8 Common Search Query Types [NEW 2026-04-21]
- **Source**: Baymard Institute. "8 Most Common Types of Search Queries." https://baymard.com/blog/ecommerce-search-query-types [audit-verified Run-B 2026-04-21]
- **Methodology**: Baymard benchmark across 8 query types on major e-commerce sites.
- **Key Finding**: "41% of sites fail to fully support" the 8 query types. Individual query types show failure rates ranging from 29% to 50% of tested sites. The 8 types: (1) Exact; (2) Product Type; (3) Feature; (4) Use Case; (5) Abbreviation/Symbol; (6) Compatibility; (7) Symptom; (8) Non-Product. This finding complements Finding 10 (31% fail product-type searches specifically) — the broader failure rate across all query types is higher.
- **E-Commerce Application**: Use as a search QA runbook: test representative queries of each type from your own search logs. The query types with the highest failure rates across sites (Use Case, Compatibility, Symptom) are the ones where user intent is expressed indirectly rather than by exact product name. Prioritize fixing these because they represent the highest-intent searches (users who know their problem but not the product name).
- **Replication Status**: Baymard benchmark data — primary source verified on-page.
- **Boundary Conditions**: Failure rate per query type varies by catalog vertical. An automotive parts catalog may handle Compatibility queries well while failing on Use Case queries; a fashion catalog may be the inverse.
- **Evidence Tier**: Gold

---

### Finding 18: NNGroup — Ecommerce Search Success Rate Rose from 64% (2000) to 92% (2017) [NEW 2026-04-21]
- **Source**: NNGroup. "The State of Ecommerce Search." Kate Moran, June 2018. https://www.nngroup.com/articles/state-ecommerce-search/ [audit-verified Run-B 2026-04-21]
- **Methodology**: 17-year NNGroup research synthesis covering behavioral usability studies.
- **Key Finding**: Search success rates rose from 64% (2000) to 92% (2017) as a result of better algorithms, standardized search layouts, faceted filtering, and autosuggest adoption. Autosuggest dropdown was selected 23% of the time. The improvement is attributable to industry-wide infrastructure investment, not individual site optimization.
- **E-Commerce Application**: The industry floor for search success is now high — a <90% search success rate means you are performing below the 2017 e-commerce benchmark. Use this as a competitive floor calibration: if your site search analytics show a zero-result rate above 10%, you are not competitive with 2017-era best practice, let alone 2026.
- **Replication Status**: NNGroup research synthesis — article accessible and verified on-topic.
- **Boundary Conditions**: "Search success" = task completion, not purchase conversion. High search success can coexist with poor conversion if product pages are weak. Treat as necessary but not sufficient condition for search-driven revenue.
- **Evidence Tier**: Silver

---

## Methodological Notes

1. **Baymard dominance**: Most actionable zero-results UX findings originate from Baymard Institute's usability research. Their benchmark data (~50% of sites have dead-end zero-results pages) is observational, not a causal study — it measures the prevalence of the problem, not the conversion lift from fixing it.

2. **Vendor bias in impact data**: The 80-81% abandonment figure (Finding 2) comes from a Google Cloud-commissioned study. While Harris Poll execution adds credibility, the framing serves Google's commercial interest in selling search products. Treat as directional; validate against your own zero-result → bounce rate analytics.

3. **Prevention vs. recovery ROI**: The research consistently shows prevention (synonym mapping, typo tolerance, good catalog coverage) delivers higher ROI than recovery (zero-results page optimization) because it reduces the frequency of the problem. However, prevention is not 100% effective — even excellent search engines produce zero results for out-of-catalog queries. Both prevention and recovery are necessary.

4. **ECP cross-reference integration**: This file documents zero-results states that follow search failure. For the upstream causes (filter over-restriction, search autocomplete failures, query type handling), see search-and-filter-ux.md Findings 6, 7, 8, and 20.

5. **Academic gap**: No peer-reviewed randomized experiment measures the conversion impact of specific zero-results recovery strategies. Baymard's usability data establishes that recovery strategies work (users engage with them and continue browsing) but doesn't provide causal conversion lift numbers. The Google/Harris Poll (Finding 2) establishes the behavioral consequence of failed search at scale.

---

## Sources Consulted

- Baymard Institute. "5 Proven UX Strategies For 'No Results' Pages." February 2025. https://baymard.com/blog/no-results-page
- Baymard Institute. E-Commerce Search UX Benchmark. https://baymard.com/ux-benchmark
- Baymard Institute. E-Commerce Search Report and Benchmark. https://baymard.com/blog/ecommerce-search-report-and-benchmark
- Baymard Institute. "8 Most Common Types of Search Queries." https://baymard.com/blog/ecommerce-search-query-types
- Baymard Institute. Product Lists & Filtering Research. https://baymard.com/research/ecommerce-product-lists
- Google Cloud / Harris Poll. (2024). Consumer Search Abandonment Study. N=13,500.
- Google Cloud / Harris Poll. (2021). Search Abandonment Survey. N=9,096.
- Algolia. (2026). E-Commerce Search and KPIs Statistics. Vendor benchmark.
- ConversionBox. "Reduce 'No Results' & Boost Sales with Smarter E-Commerce Site Search." June 2025. https://www.conversionbox.ai/blog/ecommerce-onsite-search-optimization-no-results-fix/
- Nielsen, J. (1994, updated). "10 Usability Heuristics for User Interface Design." Nielsen Norman Group. https://www.nngroup.com/articles/ten-usability-heuristics/
- Nielsen Norman Group. "Error-Message Guidelines." https://www.nngroup.com/articles/error-message-guidelines/
- Nielsen Norman Group. "The State of Ecommerce Search." Kate Moran, June 2018. https://www.nngroup.com/articles/state-ecommerce-search/
- Nielsen Norman Group. E-Commerce User Experience Reports.
- Cialdini, R.B. (2021). *Influence: The Psychology of Persuasion* (new and expanded). Harper Business.
- Synup / Voicebot.ai. Voice Search Shopping Statistics.
- Google (2024-2025). Google Lens Shopping Data.
- Tagalys. "No Results at eCommerce Site Search: How to address them?" June 2025. https://www.tagalys.com/blog/how-to-address-no-results-for-site-search-at-your-ecommerce-store
- Klaviyo. Back-in-Stock Email Benchmark Data.
