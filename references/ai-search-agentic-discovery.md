<!-- RESEARCH_DATE: 2026-04-02 -->
<!-- AUDIT_DATE: 2026-04-21 -->
<!-- RECONCILED_DATE: 2026-04-22 -->
# AI Search & Agentic Commerce Discovery

**Research Date:** 2026-04-02
**Total Findings:** 10
**Methodology:** Synthesis of OpenAI official product feed specification, Adobe Analytics traffic data (July 2025), Google AI Overview impact studies (GrowthSRC, Seer Interactive, BrightEdge), Gartner agentic AI predictions, and Google Search Central documentation. This is an emerging domain — specifications change rapidly, and evidence tiers are lower than established SEO fields.

> **Cross-Reference:** See SEO reference `schema-product-markup.md` for the Schema.org Product markup implementation that serves as the foundation for AI commerce discovery. The GTIN/product identifier requirements (schema-product-markup.md Finding 8) are the single most important technical step for AI commerce readiness.

---

## Summary

### Top 3 Most Impactful Findings

1. **Schema.org Product markup is the universal foundation for all AI commerce platforms** (Finding 10) — Google, OpenAI, and Perplexity all consume Schema.org Product markup. JSON-LD is the delivery format. One correct implementation serves all current and likely future AI shopping agents simultaneously.

2. **AI-referred traffic converts better — 27% lower bounce rate, 8–10% higher engagement** (Finding 4) — Adobe Analytics data: despite being a tiny fraction of total traffic, AI-referred shoppers show significantly higher purchase intent signals. Optimizing for AI discoverability is high-ROI because the traffic that arrives is better quality.

3. **GTIN/product identifiers are the cross-platform product matching key** (Finding 5) — Required by Google, required by OpenAI Product Feed, used by Perplexity's shopping indexing. Sites without populated GTINs are effectively invisible to AI shopping agents attempting cross-platform product matching.

---

## Coverage by Research Question

| Research Question | Findings | Evidence Quality |
|---|---|---|
| What is ChatGPT Shopping and how does it work? | 1, 2 | Gold (spec) |
| Do AI Overviews hurt organic CTR? | 3 | Gold |
| Is AI-referred traffic worth optimizing for? | 4 | Silver |
| Why are GTINs so critical for AI commerce? | 5 | Gold |
| Is there a universal AI shopping standard? | 6 | Silver |
| How big is Perplexity as a channel? | 7 | Bronze |
| Should descriptions be Q&A-structured for AI? | 8 | Silver |
| Are Gartner's agentic commerce predictions reliable? | 9 | Silver |
| What single thing delivers maximum AI readiness? | 10 | Gold |

---

## Findings

### Finding 1: ChatGPT Instant Checkout Launched September 29, 2025 — Shopify and Etsy First
- **Source**: OpenAI, "Buy it in ChatGPT: Instant Checkout and the Agentic Commerce Protocol" (Sept 29, 2025) — https://openai.com/index/buy-it-in-chatgpt/ (primary launch announcement, Gold). CNBC Sept 29 2025; Digital Commerce 360 Sept 30 2025; Stripe newsroom Sept 2025 (corroborating). OpenAI Help Center, "Shopping with ChatGPT Search" — https://help.openai.com/en/articles/11128490-shopping-with-chatgpt-search. Shopify partnership announcement. OpenAI Agentic Commerce Product Feed specification — https://developers.openai.com/commerce/specs/feed/ (replaces the retired platform.openai.com/docs/shopping path).
- **Methodology**: OpenAI official announcement and specification — not a study but authoritative documentation of feature launch and requirements.
- **Key Finding**: **ChatGPT Instant Checkout launched September 29, 2025** (not November 2025), enabling users to purchase products without leaving the ChatGPT interface. Etsy went live first; Shopify merchants were announced as "coming soon" at launch. Initial limitations: single-item purchases only in v1; US market initially; Shopify merchants have first-class native integration. Users can ask "find me a carbon fiber hood for a 2024 GR Supra" and ChatGPT surfaces matching products with purchase capability. Separately, **ChatGPT Shopping Research** (a reinforcement-trained GPT-5-mini variant for product research, distinct from Instant Checkout) launched **November 24, 2025** — see [Finding 12 / Methodological Notes] for the Shopping Research product details. The live file previously conflated these two separate OpenAI product launches under a single November 2025 date.
- **E-Commerce Application**: For Shopify stores: check your Shopify admin → Sales Channels to verify ChatGPT Shopping integration is enabled. For non-Shopify platforms: submit a product feed per OpenAI's specification. The integration prioritizes merchants with: accurate product data, populated GTINs, current inventory/pricing, complete return policy information. Note: by March 2026, ChatGPT's shopping experience had been significantly expanded (multi-item cart rollout per CNBC/MacRumors March 2026 — the "single-item only" limitation of v1 is now obsolete).
- **Replication Status**: Official OpenAI launch announcement (Gold) — factual. Business impact data limited given rapid product evolution.
- **Boundary Conditions**: Product has evolved significantly since September 2025 launch. Complex products requiring consultation/customization are not well-suited to this channel. The channel is relatively new and benchmarks are still emerging.
- **Evidence Tier**: Gold for launch facts (OpenAI official announcement live); Silver for current behavioral/business-impact claims (product has been revised since launch).
<!-- RECONCILED_NOTE: F1 corrected per Vera reconciled audit 2026-04-22. Launch date corrected from Nov 2025 → Sept 29, 2025 (Instant Checkout). Shopping Research (Nov 24, 2025) is a separate product — noted here and in Methodological Notes. -->

---

### Finding 2: OpenAI Product Feed Specification Requirements
- **Source**: OpenAI Agentic Commerce Product Feed specification — https://developers.openai.com/commerce/specs/feed/ (primary current spec; replaces the retired platform.openai.com/docs/shopping path). OpenAI Developers Agentic Commerce overview — https://developers.openai.com/commerce/product-feeds/. Agentic Commerce Protocol docs — https://agentic-commerce-protocol.com/docs/commerce/specs/feed.
- **Methodology**: OpenAI official specification — not a study; authoritative technical documentation.
- **Key Finding**: Required feed fields: `is_eligible_search` (boolean), `is_eligible_checkout` (boolean), `title` (≤150 characters), `description` (≤5,000 characters), `price` (with currency), `availability` (in stock/out of stock), `gtin` (required for product matching), `brand`, `images` (3–5 recommended). Feed push cadence per current ACP spec mirrors: **daily refresh is the baseline commitment; up to 15-minute push is supported for merchants who need real-time pricing and inventory accuracy** (recommended for Instant Checkout eligibility where pricing volatility requires it). The feed format substantially mirrors Google Merchant Center's format with additional ChatGPT-specific fields.
<!-- RECONCILED_NOTE: F2 cadence corrected per Vera reconciled audit 2026-04-22. Prior "every 15 minutes" framing was incomplete; daily is the baseline, 15-min is available for real-time needs. Both cadences confirmed in ACP spec mirrors. -->
- **E-Commerce Application**: If building for ChatGPT Shopping: (1) populate ALL required fields; (2) GTIN is critical — products without GTIN may not match in ChatGPT's knowledge graph; (3) description should answer conversational queries ("What fitment does this cover?", "Is this street legal?") within the 5,000-char limit — AI parses differently than traditional keyword search; (4) ensure pricing and availability update every 15 minutes for Instant Checkout accuracy.
- **Replication Status**: Official specification — applies to all ChatGPT Shopping integrations.
- **Boundary Conditions**: The 15-minute update frequency requirement assumes real-time inventory management infrastructure. Stores with weekly inventory cycles cannot meet this requirement without significant architecture changes — Instant Checkout eligibility may be limited.
- **Evidence Tier**: Gold — OpenAI official specification.

---

### Finding 3: AI Overviews Reduce Organic CTR 32–61% — But Ecommerce Is Partially Insulated
- **Source**: Ahrefs, "AI Overviews and Clicks — Updated Study" (Dec 2025, 300K keywords): https://ahrefs.com/blog/ai-overviews-reduce-clicks-update/. Seer Interactive, AI Overview CTR impact (Sept 2025): https://www.seerinteractive.com/insights/aio-impact-on-google-ctr-september-2025-update. GrowthSRC analysis (200,000+ keywords tracked): https://growthsrc.com/google-organic-ctr-study/. BrightEdge Research, February 2026: AI Overviews on approximately 48% of tracked queries.
- **Methodology**: Ahrefs: observational analysis of 300K keywords (Dec 2025). GrowthSRC: before/after CTR analysis for queries with AI Overview vs. without, across 200K+ keywords. Seer Interactive: client portfolio analysis. BrightEdge: prevalence tracking. All are observational analyses — not controlled experiments. Confounders (query type distribution, branded vs. non-branded mix) affect results.
- **Key Finding**: Ahrefs Dec 2025 (300K keywords): top-page CTR **58% lower** on queries with AI Overviews. Seer Interactive Sept 2025: organic CTR **61% lower** (1.76%→0.61%) on AIO queries; paid CTR **68% lower**. GrowthSRC: position-1 CTR **32% lower** on AIO queries. AI Overviews appear on approximately 48% of tracked queries (BrightEdge, Feb 2026). However: ecommerce transactional queries are partially insulated — Google Shopping widgets typically appear instead of AI Overviews for direct product purchase queries. Being cited within an AI Overview delivers approximately 35% higher CTR than non-cited brands on informational queries (GrowthSRC secondary finding).
- **E-Commerce Application**: (1) Prioritize keyword strategy around transactional queries where shopping widgets appear (search for your target keywords and observe what SERP features appear); (2) For informational/comparison content, optimize to be cited within AI Overviews — this requires authoritative, well-structured content that AI can directly quote or reference; (3) Monitor CTR trends in Search Console by query type to identify AI Overview impact on your specific queries.
- **Replication Status**: Multiple independent analyses confirm AI Overview CTR suppression for informational queries. The ecommerce insulation finding is consistent across analyses. The 35% CTR boost for cited sources is from GrowthSRC secondary analysis — single source.
- **Boundary Conditions**: AI Overview presence varies by query type. Shopping queries are most insulated. Branded queries are most insulated. Generic informational queries ("how to install a cold air intake") are most affected. The 48% prevalence figure may increase over time as Google expands AI Overview coverage.
- **Evidence Tier**: Silver — multiple independent large-n vendor analyses now exist (Ahrefs 300K keywords Dec 2025, GrowthSRC 200K+, Seer Interactive portfolio). Ahrefs' methodological rigor and dataset scale (300K keywords) materially strengthens the evidence base above single-vendor Bronze. Converging directional finding across independent sources.
<!-- RECONCILED_NOTE: F3 upgraded Bronze→Silver per Vera reconciled audit 2026-04-22. Ahrefs Dec 2025 study added as primary anchor; all three Ahrefs/Seer/GrowthSRC figures now cited explicitly. -->

---

### Finding 4: AI-Referred Traffic Shows Higher Purchase Intent Signals
- **Source**: Adobe Analytics, "Adobe Analytics 2025 Holiday Shopping Report" (Q4 2025 / Holiday 2025) — news.adobe.com/news/2026/01/adobe-holiday-shopping-season [Citation Status: URL pending human verification — Run B cites but reconciler did not fetch]. Earlier: Adobe Analytics, "AI and the Future of Commerce" report (July 2025), https://business.adobe.com/blog/perspectives/generative-ai-and-the-future-of-commerce. Adobe Analytics tracks ecommerce behavior across major retail sites.
- **Methodology**: Adobe Analytics: behavioral analysis of traffic from AI-referral sources vs. traditional organic and paid sources. Large dataset (Adobe Analytics covers a significant portion of major US ecommerce sites). Methodology: comparative analysis of engagement metrics (bounce rate, session depth, time on site) segmented by traffic source. Note: Adobe has acknowledged that specific percentages shift between reporting periods — treat as directional.
- **Key Finding**: Generative AI traffic to retail sites increased approximately 4,700% year-over-year (large base from near-zero, July 2025 report — historical snapshot). Q4 2025 / Holiday season update: AI-referred shoppers show **31–33% lower bounce rate**, **45% more time on-site**, and **13% more pages per visit** compared to other traffic sources (Adobe Q4 2025 data, cited in Run B). The July 2025 figures (8–10% higher engagement, 27% lower bounce) are superseded by Q4 2025 numbers which reflect a more mature traffic pattern. The interpretation remains consistent: users who arrive via AI assistant recommendation are further along in their decision process — the AI has already pre-qualified them.
- **E-Commerce Application**: AI-referred traffic is currently a small absolute volume but growing rapidly and showing higher conversion potential. Treat AI discoverability as a long-term channel investment. The quality of AI-referred traffic justifies optimizing for it even before volume is significant.
- **Replication Status**: Adobe Analytics data is from a large dataset but is vendor-published. The specific percentages (8% vs 10% engagement in different reports) vary — Adobe acknowledges this in their reporting. Treat directionally; the overall picture (AI-referred traffic has better engagement signals) is consistent.
- **Boundary Conditions**: "AI-referred traffic" is currently a small segment. A 4,700% increase from near-zero is still a small absolute number for most merchants. Don't over-invest in AI-specific optimization to the detriment of established channels. The referral source categorization may change as AI assistants evolve their referral behaviors.
- **Evidence Tier**: Silver — Adobe Analytics is a credible firm with access to large-scale ecommerce data, but numbers vary between reports and methodology is not fully published.

---

### Finding 5: GTIN/Product Identifiers Are Required for Cross-Platform AI Product Matching
- **Source**: Google Search Central, "Product identifiers," https://developers.google.com/search/docs/appearance/structured-data/product#product-identifiers. OpenAI Agentic Commerce Product Feed specification (GTIN listed as required field): https://developers.openai.com/commerce/specs/api/feeds [Note: OpenAI developer portal blocks automated fetches; field values confirmed via multiple independent spec mirrors — alhena.ai, lengow.com, agenticcommerce.pro]. Google Merchant Center product data specification, https://support.google.com/merchants/answer/7052112?hl=en.
- **Methodology**: Multiple official platform specifications — not a study but authoritative cross-platform requirement documentation.
- **Key Finding**: GTIN (Global Trade Item Number) is required by both Google Merchant Center (for Shopping eligibility) and the OpenAI Agentic Commerce Product Feed (for ChatGPT Shopping). Without GTIN, products cannot be reliably matched across databases — AI shopping agents that pull product data from multiple sources cannot confirm they're showing the same product from different retailers. GTIN is the single point of convergence for product identity across platforms. Google Merchant Center GTIN exemptions include: store-brand products, used/refurbished products, and customized products — these are the main product categories where GTIN is not required even for Google Shopping.
<!-- RECONCILED_NOTE: F5 — corrected OpenAI URL from platform.openai.com/docs/shopping (dead) to developers.openai.com/commerce/specs/api/feeds. Added Google Merchant Center GTIN exception list (store-brand, used, customized) per Run A addition. -->
- **E-Commerce Application**: For every product that has a manufacturer-assigned GTIN/UPC/EAN: populate it in schema and product feed. For aftermarket automotive parts: use manufacturer part number (MPN) as `mpn`. For custom/handmade products: use a consistent SKU as minimum identifier. For products that appear in multiple Google Shopping databases, GTIN enables price comparison features — visibility benefit and competitive feature.
- **Replication Status**: Official platform specifications — consistent requirement across Google and OpenAI.
- **Boundary Conditions**: Not all products have manufacturer-assigned GTINs. Handmade, custom, or one-of-a-kind products legitimately lack GTINs. In these cases, MPN or SKU is the fallback. Fabricating GTINs (using random numbers) is against both Google and OpenAI policies and will cause product disapproval.
- **Evidence Tier**: Gold — Google and OpenAI official specifications.

---

### Finding 6: No Dominant AI Shopping Feed Standard Yet — Schema.org Is the Stable Foundation
- **Source**: Industry analysis of AI shopping platform requirements (2025–2026). Google Merchant Center specification https://support.google.com/merchants/answer/7052112?hl=en, OpenAI Product Feed specification https://platform.openai.com/docs, Perplexity's stated indexing approach (web crawl) https://www.perplexity.ai/. Schema.org is referenced by all three platforms as the underlying ontology: https://schema.org/Product
- **Methodology**: Cross-platform specification analysis — not a study. Comparative analysis of requirements across Google, OpenAI, and Perplexity.
- **Key Finding**: Google Merchant Center, OpenAI Product Feed, and Perplexity's shopping indexing all have different specific requirements, update frequencies, and eligibility criteria. However: all three reference Schema.org Product as the underlying ontology. The convergence point is: Schema.org Product markup + product identifiers (GTIN/MPN) + accurate pricing/availability data. No single "universal AI shopping feed" standard exists, but Schema.org is the closest available.
- **E-Commerce Application**: Foundation strategy: implement comprehensive Schema.org Product markup first (see schema-product-markup.md). Then layer platform-specific feeds: (1) Google Merchant Center (required for Shopping visibility); (2) OpenAI Product Feed (for ChatGPT Shopping). Don't build proprietary integrations for emerging AI platforms — the standards will likely converge around Schema.org.
- **Replication Status**: Specification comparison — factual as of April 2026 but likely to evolve.
- **Boundary Conditions**: The AI shopping landscape is changing rapidly. **Emerging standard candidates**: (1) OpenAI's Agentic Commerce Protocol (ACP) — already an open spec with a GitHub-hosted reference implementation, growing toward a cross-merchant standard (see Finding 11 if added); (2) Google's Universal Commerce Protocol (UCP) — reported by industry coverage (ALM Corp, March 2026) as Google's competing protocol, though reconciler could not independently verify UCP from a primary Google source — retain as Bronze-tier mention. (3) llms.txt — a community-proposed convention for AI-readable site directories (similar to robots.txt), in proposal stage as of April 2026, no major platform has adopted it as a requirement. The Schema.org foundation advice is stable regardless of which standard wins.
- **Evidence Tier**: Silver — specification analysis; accurate as of research date but subject to rapid change.

---

### Finding 7: Perplexity Shopping — Growing Channel With Unverified Volume Claims
- **Source**: Perplexity CEO Aravind Srinivas at Bloomberg Tech Summit (May 2025, reported by TechCrunch) https://techcrunch.com/: 780 million queries/month. GoDataFeed report: 400% QoQ growth (methodology not published). https://www.godatafeed.com/
- **Methodology**: CEO public statement (Bloomberg Tech Summit): authoritative for volume figure. GoDataFeed: vendor analysis — methodology not published, financial interest in driving Perplexity adoption. The 400% QoQ growth is not independently verified.
- **Key Finding**: Perplexity handles approximately 780 million queries/month (CEO-confirmed, May 2025). A growing percentage include shopping intent with product recommendations. Perplexity indexes the open web — no feed submission required. Standard SEO best practices (crawlable pages, Schema.org markup, descriptive product content) make products discoverable on Perplexity without additional platform-specific work.
- **E-Commerce Application**: No special action required for Perplexity beyond excellent standard SEO: (1) crawlable product pages; (2) Schema.org Product markup; (3) descriptive, informative product descriptions that answer questions; (4) don't block Perplexity's crawler (PerplexityBot) in robots.txt. If you're blocking AI crawlers broadly, verify you're not blocking shopping-relevant AI discovery.
- **Replication Status**: CEO volume claim (780M/month) is an authoritative self-disclosure. Growth rate (400% QoQ) is from a vendor analysis not independently verified. Overall trend direction (Perplexity growing) is broadly confirmed.
- **Boundary Conditions**: Perplexity's shopping volume is still small compared to Google. Perplexity indexes the web rather than accepting direct feeds — you cannot "optimize" specifically for Perplexity beyond standard SEO practices. The 400% growth figure should not be cited without the GoDataFeed attribution and caveat.
- **Evidence Tier**: Bronze — CEO statement is directionally reliable; GoDataFeed growth rate is unverified vendor data.

---

### Finding 8: Q&A-Structured Content Improves AI Query Matching
- **Source**: Searchable.com, 2026 (vendor recommendation — not peer-reviewed). Supported by general understanding of how LLMs process structured vs. unstructured text and how conversational queries are formulated. Google's FAQ schema documentation: https://developers.google.com/search/docs/appearance/structured-data/faqpage.
- **Methodology**: Vendor recommendation with logical basis. No controlled study specifically measuring AI discovery lift from Q&A product descriptions. The structural logic: LLMs are trained on Q&A data and process explicitly-structured questions and answers efficiently.
- **Key Finding**: AI shopping assistants parse product descriptions differently from traditional keyword search. Conversational queries ("Will this fit my 2024 GR Supra?", "Is this easy to install?") match more easily against Q&A-structured content than against specification-dense paragraphs. FAQ sections make answers extractable for AI citation.
- **E-Commerce Application**: Include a FAQ section (5–10 questions) on product pages using natural customer question language: "Is this compatible with [Year] [Model]?", "What's included in the kit?", "How long does installation take?", "Is this street legal?" Answer concisely and accurately. Mark up with FAQPage schema (note: Google has restricted FAQ rich results for most sites, but the structured data still benefits internal AI search and AI assistant extraction).
- **Replication Status**: No independent controlled study. Structural logic is sound. The FAQ schema benefit for traditional SERPs has been restricted since 2023. AI extraction benefit is logical but unproven.
- **Boundary Conditions**: Google has restricted FAQ rich results since 2023. Per current Google FAQ documentation (verified 2026-04-08): FAQ rich results are shown only for *"well-known, authoritative websites that are government-focused or health-focused."* For most ecommerce sites, FAQPage schema will not produce visible FAQ rich results in Google SERPs. The structured data still benefits AI assistant extraction and on-site search — but merchants should not implement FAQPage schema expecting SERP rich result eligibility.
- **Evidence Tier**: Silver — logical basis is sound; Searchable.com is vendor-sourced; no controlled study.

---

### Finding 9: Gartner Agentic Commerce Predictions — Verified Claims and Unverified Claims
- **Source**: Gartner, "Predicts 2025: AI-Enabled Agents Will Drive Business Transformation" (2024). https://www.gartner.com/ Gartner Symposium/ITxpo 2024. Note: the specific "90% of B2B buying AI-intermediated by 2028" claim attributed to Gartner in some industry sources could NOT be located in Gartner's published documents — treat as possibly misattributed.
- **Methodology**: Gartner research and prediction reports — credible analyst firm, but predictions are inherently speculative. Gartner's prediction methodology involves analyst consensus and enterprise survey data.
- **Key Finding**: Verified from Gartner: "33% of enterprise software will include agentic AI by 2028" (confirmed). "40%+ of agentic AI projects will be canceled by end of 2027 due to complexity and cost overruns" (confirmed — Gartner has a history of noting hype cycle failures alongside adoption predictions). UNVERIFIED: "90% of B2B buying will be AI-intermediated" — this specific figure could not be located in Gartner publications; it may be misattributed or paraphrased out of context.
- **E-Commerce Application**: Agentic commerce (AI agents autonomously making purchases on behalf of users) is real but nascent. Prepare by ensuring machine-readable product data (Schema.org, GTINs, clear return policies, accurate pricing). Don't over-invest in speculative AI-specific platforms before standards stabilize. The fundamentals (clean schema, accurate product data, clear policies) serve both human and AI buyers.
- **Replication Status**: Gartner predictions are frequently cited but are inherently speculative. The "agentic AI project failures" counter-prediction is a useful reality check.
- **Boundary Conditions**: Gartner's predictions have mixed historical accuracy. 2028 predictions made in 2024 carry significant uncertainty. The specific B2B buying intermediation claim should not be cited without independent source verification.
- **Evidence Tier**: Silver — Gartner is a Silver-tier source; predictions are speculative by nature. The unverified "90%" claim should be flagged if used.

> **⚠️ Quality Flag**: The "90% of B2B buying AI-intermediated by 2028" statistic attributed to Gartner in some industry publications could NOT be independently verified in Gartner's published research. Do not cite this figure without independent verification of the original Gartner source.

---

### Finding 10: Schema.org Product Markup Is the Single Highest-ROI AI Commerce Action
- **Source**: Google Search Central https://developers.google.com/search, OpenAI Product Feed specification https://platform.openai.com/docs, Schema.org documentation https://schema.org/Product. Cross-platform analysis: Schema.org Product is referenced as the underlying ontology by Google, OpenAI, and Perplexity's stated approach.
- **Methodology**: Cross-platform specification analysis. The primacy of Schema.org is established by the convergence of all major AI shopping platforms around it.
- **Key Finding**: If an ecommerce site does ONE thing for AI commerce readiness: implement comprehensive Schema.org Product markup with JSON-LD. Core required types: `Product` with `Offer` (price, availability, URL), `AggregateRating` (if reviews exist), GTIN/MPN/SKU, `MerchantReturnPolicy`, `ShippingService`. This single implementation serves Google Shopping, ChatGPT Shopping, Perplexity shopping, and any future AI shopping agent simultaneously.
- **E-Commerce Application**: Implementation priority order: (1) Product + Offer (price, availability, URL) — enables Google Shopping; (2) AggregateRating — enables star ratings in SERPs (+20% organic traffic uplift per SearchPilot); (3) GTIN/MPN — enables cross-platform product matching; (4) MerchantReturnPolicy — enables AI trust comparison; (5) ShippingService — completes merchant information. After implementing all five, submit to Google Search Console for validation and to OpenAI Product Feed for ChatGPT Shopping. **Ethics/Legal**: Schema that surfaces in SERPs and AI commerce interfaces is subject to FTC 16 CFR 465 (Fake Reviews Rule), FTC 16 CFR 255 (Endorsement Guides), and Lanham Act §43(a) — AggregateRating markup with fabricated or gated reviews is potentially deceptive under FTC rules. See ethics-gate.md for full framework.
- **Replication Status**: The specification requirements are confirmed by Google and OpenAI. The compound effect of all five components together is not independently measured but is additive. Schema-retirement status (2025 audit of recommended types): all five recommended schema types (Product, Offer, AggregateRating, MerchantReturnPolicy, ShippingService) remain active and current in the Schema.org specification as of April 2026 — none have been deprecated or retired.
- **Boundary Conditions**: Schema.org markup must accurately reflect current product data — stale pricing, availability, or return policy information creates errors that can result in Shopping disapprovals.
- **Evidence Tier**: Gold — Google and OpenAI official specifications (the implementation requirement is documented); Silver for the compound ROI claim (logical but not independently measured).

---

## Methodological Notes and Caveats

1. **This is the most rapidly-changing reference file in the SEO library.** AI commerce platforms launched within the last 12 months; specifications are evolving. Verify all specification details against current official documentation before implementation.

2. **Two distinct OpenAI product launches are in scope for this file:** (1) **Instant Checkout** (Sept 29, 2025) — the ACP-based buy-in-ChatGPT feature. (2) **Shopping Research** (Nov 24, 2025) — a reinforcement-trained GPT-5-mini research tool for product discovery; a different product from Instant Checkout, launched nearly two months later (source: https://openai.com/index/chatgpt-shopping-research/; confirmed CNBC Nov 24, Retail Dive, Digital Commerce 360 Nov 25, PYMNTS). The live file historically conflated these; F1 has been corrected to reflect Instant Checkout (Sept 29); Shopping Research is noted in this Methodological Notes section pending a full Finding 12 addition.

3. **Adobe traffic data (Finding 4) uses shifting baselines.** The 4,700% YoY figure comes from a near-zero baseline — it reflects early growth from nothing, not a large absolute channel. Don't use this as a primary business case; AI traffic is still a small fraction of ecommerce traffic. Q4 2025 numbers (31-33% lower bounce, 45% more time-on-site) are more current and actionable.

4. **The Gartner "90% B2B" figure is unverified.** If referenced in presentations or strategy documents, require the presenter to cite the original Gartner source document.

5. **Perplexity statistics (Finding 7) are early-stage.** The 780M/month figure is CEO-stated (May 2025); it may have grown significantly by the time this reference is used. Run B adds 2026 projection range of 1.2–1.5B/month from unaudited analyst estimates — treat as directional projection only.

---

## Sources Consulted

- OpenAI Instant Checkout Launch (Sept 29, 2025): https://openai.com/index/buy-it-in-chatgpt/
- OpenAI Shopping Research Launch (Nov 24, 2025): https://openai.com/index/chatgpt-shopping-research/
- OpenAI Agentic Commerce Product Feed Specification (current): https://developers.openai.com/commerce/specs/api/feeds
- Ahrefs AI Overviews CTR Study (300K keywords, Dec 2025): https://ahrefs.com/blog/ai-overviews-reduce-clicks-update/
- Seer Interactive AIO CTR (Sept 2025): https://www.seerinteractive.com/insights/aio-impact-on-google-ctr-september-2025-update
- GrowthSRC AI Overviews CTR Study: https://growthsrc.com/google-organic-ctr-study/
- BrightEdge AI Overview Prevalence: https://www.brightedge.com/
- Adobe Analytics AI Commerce Report (July 2025): https://business.adobe.com/blog/perspectives/generative-ai-and-the-future-of-commerce
- Google Merchant Center Product Data Specification: https://support.google.com/merchants/answer/7052112?hl=en
- Google Search Central Product Identifiers: https://developers.google.com/search/docs/appearance/structured-data/product#product-identifiers
- Schema.org Product: https://schema.org/Product
- Gartner Agentic AI Predictions: https://www.gartner.com/en/newsroom/press-releases/2024-10-gartner-predicts
- Perplexity CEO Statement (Bloomberg Tech Summit, May 2025): via TechCrunch
