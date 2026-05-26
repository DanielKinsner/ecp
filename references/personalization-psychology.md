<!-- RESEARCH_DATE: 2026-03-09 -->
<!-- AUDIT_DATE: 2026-04-21 -->
<!-- RECONCILED_DATE: 2026-04-22 -->
# Personalization Psychology in E-Commerce — Relevance, Creepiness, and Recommendation Framing

**Total Findings**: 16
**Research Date**: 2026-03-09

## Executive Summary

Personalization drives 10-15% revenue lift on average (McKinsey), but carries significant psychological risks. The central tension: 71% of consumers expect personalized experiences, yet personalization triggers "creepiness" responses when it reveals data collection consumers didn't consent to or weren't aware of. The key moderators are **transparency of data collection** (overt vs. covert), **trust in the brand**, **data source** (first-party vs. third-party), and **timing** (how recently the consumer interacted). Personalized pricing is almost universally perceived as unfair regardless of whether the consumer benefits. The research converges on a clear principle: personalization works best when it feels like attentive service rather than surveillance.

> **⚠️ Legal Constraint Layer (Non-Optional):** Four regulatory regimes directly constrain personalization implementation: (1) CCPA/CPRA ADMT regulations (CA, eff. Jan 1, 2026) require opt-out rights for automated decision-making based on sensitive inferences; (2) GDPR Article 22 (EU) prohibits solely automated decisions with legal/significant effects without human review, explicit consent, or contractual necessity; (3) EU AI Act Article 5(1)(a) (eff. Feb 2, 2025) prohibits AI systems deploying subliminal or manipulative techniques to distort behavior; (4) FTC Surveillance Pricing study (Jan 2025) signals active federal scrutiny of AI-driven price personalization. These are not optional ethical guidelines — they are active law. See Findings 13-16 and ethics-gate.md Parts 6.1 and 6.3 before deployment.

---

### Finding 1: The Personalization Paradox — Covert Data Collection Destroys Click-Through

- **Source**: Aguirre, E., Mahr, D., Grewal, D., de Ruyter, K., & Wetzels, M. (2015). "Unraveling the Personalization Paradox: The Effect of Information Collection and Trust-Building Strategies on Online Advertisement Effectiveness." *Journal of Retailing*, 91(1), 34-49. <https://doi.org/10.1016/j.jretai.2014.09.005> (ScienceDirect: https://www.sciencedirect.com/science/article/abs/pii/S0022435914000669; open PDF: https://openaccess.city.ac.uk/id/eprint/15747/1/AGUIRRE%20et%20al%20%202015%20(2).pdf)
- **Methodology**: Three controlled experiments manipulating information collection strategies (overt vs. covert) and personalization levels.
- **Key Finding**: When firms collect data **overtly**, higher personalization increases click-through intentions. When data collection is **covert**, personalization increases feelings of vulnerability and **decreases** adoption rates. The effect is mediated by perceived vulnerability, not privacy concern per se. Trust-building strategies (e.g., trust seals, transferring trust from known partners) can offset the negative effect of covert collection.
- **E-Commerce Application**: Always make data collection visible. Use preference centers, explicit "because you told us you like X" framing, and trust signals alongside personalized content. Avoid surfacing recommendations that reveal tracking the user didn't explicitly agree to.
- **Replication Status**: Canonical study with 570+ citations. Core finding (overt > covert) replicated across multiple contexts.
- **Boundary Conditions**: Trust-building interventions can neutralize vulnerability. Effect strongest for consumers with high privacy sensitivity.
- **Evidence Tier**: Gold

---

### Finding 2: Trust Moderates Personalization Effectiveness — 27% CTR Lift for Trusted Retailers

- **Source**: Bleier, A. & Eisenbeiss, M. (2015). "The Importance of Trust for Personalized Online Advertising." *Journal of Retailing*, 91(3), 390-409. <https://doi.org/10.1016/j.jretai.2015.04.001> (ScienceDirect: https://www.sciencedirect.com/science/article/abs/pii/S0022435915000263)
- **Methodology**: Large-scale field study combined with lab experiments examining personalized retargeting banner ads across retailers with varying trust levels.
- **Key Finding**: For the **more trusted retailer**, personalized banner click-through rates increased by **27%**. Trust significantly increased positive responses (perceived usefulness) and reduced negative responses (reactance, privacy concerns). Consumers preferred banners showing **one** item they had viewed rather than **all** items — showing everything felt surveillance-like.
- **E-Commerce Application**: Build brand trust before ramping up personalization intensity. Show a single relevant item rather than exposing the full browsing history. New or low-trust brands should use lighter personalization (category-level, not item-level).
- **Replication Status**: Replicated in companion study (Bleier & Eisenbeiss, 2015, Marketing Science). Consistent with Aguirre et al. trust-building findings.
- **Boundary Conditions**: Effect diminishes for low-trust retailers. Showing too many tracked items triggers reactance even for trusted brands.
- **Evidence Tier**: Gold

---

### Finding 3: Personalization Timing Decay — High Personalization Loses Effectiveness Quickly

- **Source**: Bleier, A. & Eisenbeiss, M. (2015). "Personalized Online Advertising Effectiveness: The Interplay of What, When, and Where." *Marketing Science*, 34(5), 669-688. <https://doi.org/10.1287/mksc.2015.0930> (INFORMS: https://pubsonline.informs.org/doi/10.1287/mksc.2015.0930)
- **Methodology**: Two large-scale field experiments and two lab experiments examining depth of content personalization (DCP) and timing.
- **Key Finding**: High-DCP banners (showing exact viewed products) are most effective **immediately after** a consumer visits the store, but lose effectiveness rapidly as time passes. Medium-DCP banners (category-level personalization) are initially less effective but **more persistent**, eventually outperforming high-DCP banners after a delay. This means the optimal personalization strategy shifts over time.
- **E-Commerce Application**: Use exact-product retargeting within 24-48 hours of a visit. After that window, shift to category-level or style-level recommendations. Avoid showing "you viewed this exact item" ads a week later — that triggers creepiness rather than relevance.
- **Replication Status**: Well-cited (200+ citations). Timing effect is robust across product categories.
- **Boundary Conditions**: Decay rate likely varies by purchase cycle length (faster for impulse goods, slower for considered purchases).
- **Evidence Tier**: Gold — INFORMS (Marketing Science, Management Science) is explicitly listed in the Gold publisher list per evidence-tiers.md. [Upgraded Bronze→Gold per reconciled audit 2026-04-22; prior Bronze was a misapplication of publisher tier rules]

---

### Finding 4: The Creepiness Threshold — 41% Find Location-Based Personalization Creepy

- **Source**: Accenture (2018). "Personalization Pulse Check" — Accenture Interactive. Press release (live, verbatim-confirmed): https://newsroom.accenture.com/news/2018/widening-gap-between-consumer-expectations-and-reality-in-personalization-signals-warning-for-brands-accenture-interactive-research-finds [Note: the full report PDF at accenture.com/content/dam/accenture/final/a-com-migration/pdf/pdf-83/accenture-making-personal.pdf redirects to Accenture Song and is no longer accessible — remove this PDF URL; press release is the live authoritative source with all key statistics verbatim-confirmed]
- **Methodology**: Large-scale consumer survey (8,000 consumers across multiple countries).
- **Key Finding**: **41%** find it creepy to receive a text as they walk by a store. **40%** find mobile notifications after passing a store creepy. **35%** find social media ads for browsed items creepy. However, **73%** said no brand had communicated in a way that felt "too personal." Among the 27% who did feel it was too personal, **64%** were uncomfortable because the brand used data the consumer **didn't willingly provide**. **48%** of consumers left a brand's site and purchased elsewhere due to a poorly-curated experience (up from 40% the prior year).
- **E-Commerce Application**: Avoid location-triggered push notifications unless the consumer explicitly opted in. Cross-site retargeting (showing ads for browsed items on social media) is at the creepiness boundary for 1 in 3 consumers. The safest personalization uses data the consumer knowingly provided.
- **Replication Status**: Annual survey; creepiness thresholds consistent across multiple years of Accenture research.
- **Boundary Conditions**: Younger demographics (Gen Z) show slightly higher tolerance. Creepiness perception lower when value exchange is clear (e.g., discount offered alongside the personalized notification).
- **Evidence Tier**: Silver

---

### Finding 5: Creepiness Cannot Be "Fixed" Once Triggered

- **Source**: Petrova, P. (2026). "The Phenomenon of Creepiness in a Digital Marketing World." *Psychology & Marketing*, Wiley. DOI: 10.1002/mar.70089 (direct Wiley DOI page: https://onlinelibrary.wiley.com/doi/10.1002/mar.70089 — returns 403 paywall, confirmed as live article per Run A DOI verification; not a dead URL). [Note: the 30% and 60% statistics from this paper carry Citation Status DEFER — paywalled, specific figures accepted under peer-review trust assumption given confirmed journal and author list; flag for institutional access check]
- **Methodology**: Multi-study research examining creepiness as a distinct emotional response to digital personalization, including intervention tests.
- **Key Finding**: Creepiness emerges when personalized ads are appraised as **ambiguous and intrusively surveilling**, triggering uneasiness and reactance. Critically, **"you can't fight the feeling of creepiness"** once triggered — even interventions like transparency messages or discounts failed to neutralize the response. Creepiness is amplified by two consumer traits: **skepticism** and **technological paranoia**. **30%** of consumers unsubscribe due to creepiness. **60%** report discomfort with AI-driven personalization.
- **E-Commerce Application**: Prevention is the only viable strategy. Once a consumer perceives personalization as creepy, no amount of explanation or incentive recovers the relationship. Design personalization to stay well below the creepiness threshold rather than trying to optimize at the boundary.
- **Replication Status**: Recent publication building on established creepiness literature. Consistent with Aguirre et al. vulnerability findings. Supporting prior art: Moore, R., Moore, M.L., & Capella, M. (2005) on perceived intrusiveness of direct marketing; Tene, O., & Polonetsky, J. (2014) "A Theory of Creepy: Technology, Privacy and Shifting Social Norms," *Yale Law & Policy Review*, 32(2) — both corroborate the creepiness-as-distinct-emotional-response framing. [Run B supporting literature]
- **Boundary Conditions**: Skepticism and technological paranoia are amplifiers — high-trust consumers are more resilient. The "irreversibility" finding needs further replication across contexts.
- **Evidence Tier**: Gold — Wiley (Psychology & Marketing) is in the Gold publisher list; DOI confirmed at live Wiley paywall.

---

### Finding 6: 71% of Consumers Expect Personalization, 76% Get Frustrated Without It

- **Source**: McKinsey & Company (2021/2023). "The Value of Getting Personalization Right—or Wrong—Is Multiplying" — Next in Personalization Report. https://www.mckinsey.com/capabilities/growth-marketing-and-sales/our-insights/the-value-of-getting-personalization-right-or-wrong-is-multiplying
- **Methodology**: Large-scale consumer survey and cross-industry analysis of personalization revenue impact.
- **Key Finding**: **71%** of consumers expect personalized interactions. **76%** get frustrated when personalization is absent. Companies excelling at personalization generate **40% more revenue** from those activities than average players. Personalization drives **10-15% revenue lift** on average, with company-specific results spanning 5-25% depending on sector and execution quality. Shifting to top-quartile personalization performance would generate over **$1 trillion** in value across US industries.
- **E-Commerce Application**: Personalization is no longer optional — it's baseline expectation. The revenue case is strong (10-15% lift), but the risk of getting it wrong (frustration, abandonment) is equally significant. Invest in execution quality, not just personalization technology.
- **Replication Status**: Consistent with Salesforce, Accenture, and Epsilon research. Revenue lift figures validated across multiple McKinsey analyses.
- **Boundary Conditions**: Revenue lift varies significantly by sector (5-25% range). B2B personalization expectations are catching up to B2C but still lag.
- **Evidence Tier**: Silver

---

### Finding 7: Personalized Pricing Reduces Fairness Perception Regardless of Consumer Benefit

- **Source**: Ohlwein, M. & Bruno, P. (2025). "Algorithms of (un)fairness — Is personalized pricing fair game or foul play?" *International Journal of Market Research*, SAGE. Direct DOI: <https://doi.org/10.1177/14707853251338579> (SAGE journals DOI; 403 = live paywall, not dead); Richards, T., Liaukonyte, J., & Streletskaya, N. (2016). "Personalized Pricing and Price Fairness." *International Journal of Industrial Organization*, 44, 138-153. <https://doi.org/10.1016/j.ijindorg.2015.11.004> (Cornell repository: https://hdl.handle.net/1813/76283)
- **Methodology**: Ohlwein & Bruno: experimental study manipulating pricing strategies and measuring fairness perceptions. Richards et al.: economic modeling with consumer data.
- **Key Finding**: Personalized pricing reduces perceived price fairness **regardless of whether the consumer personally benefits** from the individualized price. The mechanism is violation of social norms — consumers expect equal treatment. Negative outcomes include reduced purchase intention, switching behavior, negative word-of-mouth, and loss of trust. The effect is driven by **suspicion** (cognitive) and **negative moral emotions** (affective). Even consumers who receive a lower personalized price perceive the practice as unfair when they learn others pay different amounts.
- **E-Commerce Application**: Avoid personalized pricing or keep it invisible. If dynamic pricing is used, frame it as universal mechanisms (sales, promotions, loyalty rewards) rather than individual price discrimination. Loyalty-based tiered pricing is more acceptable than algorithmic individual pricing. Never let consumers discover that another customer paid a different price for the same item.
- **Replication Status**: Consistent across multiple studies (Ohlwein & Bruno 2025, Richards et al. 2016, Weisstein et al. 2013). Robust finding.
- **Boundary Conditions**: Loyalty-tier pricing and volume discounts are perceived as fairer than algorithmic personalized pricing. Transparency about pricing criteria can partially mitigate unfairness perceptions but does not eliminate them.
- **Evidence Tier**: Gold

---

### Finding 8: First-Party Data Personalization is Accepted; Third-Party Data Triggers Distrust

- **Source**: Accenture (2018), "Personalization Pulse Check" — Press release (live): https://newsroom.accenture.com/news/2018/widening-gap-between-consumer-expectations-and-reality-in-personalization-signals-warning-for-brands-accenture-interactive-research-finds; Wunderkind consumer survey — [Citation Status: Retail Systems URL https://www.retail-systems.com/rs/Wunderkind_70_Percent_Believe_Advertisers_Dont_Respect_Digital_Experience.php is dead (URL_DEAD_2026-04-21); Wunderkind survey existence confirmed via secondary sources but primary URL unavailable — retain with Citation Status note per evidence-tiers.md Do-Not-Cite Rule 2 (only citation for specific stat)]
- **Methodology**: Consumer surveys measuring comfort with different data sources powering personalization.
- **Key Finding**: Among consumers who felt personalization was "too personal" (27% of respondents), **64%** were uncomfortable because the brand used **data they didn't willingly provide** — typically cross-site tracking or third-party data purchases. **70%** of consumers believe advertisers don't respect their digital experience (Wunderkind), with **95%** reporting being bothered by intrusive ads. Consumers view first-party data sharing as a **fair trade** — data for better experience. Third-party data feels like **surveillance**.
- **E-Commerce Application**: Build personalization on first-party and zero-party data (preferences, on-site behavior, explicit surveys). Avoid basing visible recommendations on third-party data sources. If using third-party data, don't surface it in ways that reveal cross-site tracking. Preference centers and quizzes are high-trust data collection methods.
- **Replication Status**: Consistent across Accenture, Salesforce, and GDPR-era consumer research. The first-party vs. third-party distinction is well-established.
- **Boundary Conditions**: Younger demographics are slightly more tolerant of cross-platform data use. Category matters — health and financial data have much lower tolerance than shopping preferences.
- **Evidence Tier**: Silver

---

### Finding 9: 90-98% of E-Commerce Traffic is Anonymous — Personalization Strategy Must Account for This

- **Source**: Nacelle, "Maximizing Ecommerce Personalization: Solve the Anonymous Visitor Gap" (2024) — https://nacelle.com/blog/maximizing-ecommerce-personalization-solve-the-anonymous-visitor-gap [WebFetch-verified live; exact quote: "90-98% of your website visitors are completely anonymous"]; Braze consumer study — https://www.braze.com/resources/reports-and-guides/global-customer-engagement-review [Citation Status: Braze URL not directly verified via fetch; retained as corroborating Bronze-tier source]
- **Methodology**: Analysis of e-commerce traffic patterns and personalization platform data across 1,000+ companies and 5+ billion users.
- **Key Finding**: **90-98%** of e-commerce traffic is anonymous (not logged in). **57%** of new users are anonymous, and of those, **80%** never receive any marketing messaging. Yet the majority of personalization budget and resources are focused on known visitors. Netflix-style 1:1 personalization is inappropriate for anonymous visitors. Behavioral segmentation (session-level clustering based on browse patterns) is the most effective approach for anonymous users, with progressive profile enrichment as interactions accumulate.
- **E-Commerce Application**: Design a two-tier personalization strategy: (1) segment-level personalization for anonymous visitors based on session behavior, referral source, and device context; (2) individual-level personalization for logged-in users. Don't waste sophisticated 1:1 personalization on anonymous traffic — it can't work and may trigger creepiness. Use contextual signals (time of day, category browsing, geographic region) for anonymous personalization.
- **Replication Status**: Traffic anonymity rates are consistent across industry analyses. The 90%+ figure is well-established.
- **Boundary Conditions**: Subscription-based and B2B e-commerce have much higher login rates, making individual personalization more viable. Mobile app users are more likely to be logged in than mobile web users.
- **Evidence Tier**: Bronze

---

### Finding 10: Social Proof Framing Outperforms Algorithmic Framing — 270% Purchase Lift with Reviews

- **Source**: Spiegel Research Center (Northwestern, 2017), "How Online Reviews Influence Sales" — https://spiegel.medill.northwestern.edu/how-online-reviews-influence-sales/ (full report PDF: https://spiegel.medill.northwestern.edu/wp-content/uploads/sites/2/2021/04/Spiegel_Online-Review_eBook_Jun2017_FINAL.pdf); CXL, "Social Proof in Conversion Optimization" — https://cxl.com/blog/is-social-proof-really-that-important/; The Good, "Social proof tactics for ecommerce" — https://thegood.com/insights/social-proof-ecommerce/; Genesys Growth — https://www.genesysgrowth.com/blog
- **Methodology**: Field experiments, A/B tests, and meta-analyses of social proof elements in e-commerce.
- **Key Finding**: Products with reviews show **270% higher purchase likelihood** than products without (Spiegel Research Center, WebFetch-verified verbatim). An apparel A/B test adding a review carousel to PDP delivered **4.21% conversion rate increase**, **8.77% revenue per visitor increase**, and **7.41% increase in products per visitor** (CXL/The Good secondary sources — Bronze tier, directional). Real-time social proof notifications ("X people purchased in the last 24 hours") boost conversions by **98%** compared to static pages [Citation Status DEFER: this figure traces to CXL/The Good secondary sources but is not on the Spiegel page — likely from a vendor report; retain with Citation Status note; do not attribute to Spiegel]. Note: a "93% of consumers say online reviews impact purchase decisions" figure has been removed — it was not found on the Spiegel source URL and has no confirmed primary attribution (probable source: Podium/BrightLocal/Trustpilot). Social proof framing ("customers also bought") leverages conformity bias and reduces perceived risk, while algorithmic framing ("recommended for you") can trigger personalization reactance.
- **E-Commerce Application**: Frame recommendations using social proof language ("Popular with customers who viewed this," "Trending in this category") rather than algorithmic language ("Our algorithm thinks you'll like this"). Social proof framing converts better because it provides both relevance and social validation without triggering surveillance concerns. Use real-time purchase/view counts where possible.
- **Replication Status**: Social proof effects are among the most replicated findings in consumer psychology. Specific conversion numbers vary by implementation.
- **Boundary Conditions**: Social proof is less effective for unique/luxury items where exclusivity matters. "Customers also bought" can backfire if the associations seem random or irrelevant.
- **Evidence Tier**: Gold

---

### Finding 11: Salesforce — 80% Say Experience Matters as Much as Product, 65% Expect Cross-Touchpoint Personalization

- **Source**: Salesforce (2023). "State of the Connected Customer" 6th Edition — https://www.salesforce.com/news/stories/customer-engagement-research-2023/ (full report PDF: https://a.sfdcstatic.com/content/dam/www/ocms/assets/pdf/service-cloud/state-of-connected-customer.pdf)
- **Methodology**: Global survey of thousands of consumers and business buyers.
- **Key Finding**: **80%** of customers say the experience a company provides is as important as its products/services. **65%** of consumers expect companies to adapt experiences to their changing needs. **61%** feel companies treat them as a number rather than an individual. **70%** say service agents' awareness of prior sales interactions is "very important" to keeping their business. Nearly **75%** of B2B buyers expect vendors to personalize to their needs.
- **E-Commerce Application**: Cross-channel consistency is now a baseline expectation. A customer who interacts via chat, email, and on-site expects continuity. The 61% who feel treated "as a number" represents an opportunity — basic recognition (name, past purchases, preferences) significantly differentiates. B2B e-commerce must catch up to B2C personalization standards.
- **Replication Status**: Annual survey, 6th edition. Trends are directionally consistent year over year with increasing expectations.
- **Boundary Conditions**: B2B expectations lag B2C but are converging. Expectations highest among high-spending, digitally native segments.
- **Evidence Tier**: Silver

---

### Finding 12: Algorithmic Transparency Has Mixed Effects — Explanation Quality Is Critical

- **Source**: Center for Democracy & Technology (CDT, 2022), "This is Transparency to Me: User Insights into Recommendation Algorithm Reporting" — https://cdt.org/insights/this-is-transparency-to-me-user-insights-into-recommendation-algorithm-reporting/; Wang et al. (2024), "How transparency affects algorithmic advice utilization: The mediating roles of trusting beliefs," *Decision Support Systems* — https://www.sciencedirect.com/science/article/abs/pii/S0167923624001064 (DOI: <https://doi.org/10.1016/j.dss.2024.114263)>
- **Methodology**: CDT: Qualitative user research on algorithmic transparency UX. Wang et al.: Experimental study on transparency and trust in algorithmic advice.
- **Key Finding**: Transparency about recommendation algorithms has **mixed effects** on conversion. Low-quality or overly technical explanations **backfire** by highlighting algorithmic complexity and amplifying perceptions of inscrutability. Some users bypass algorithmic feeds entirely after receiving transparency disclosures due to privacy or fairness concerns. However, transparency **increases trust** when explanations are simple, benefit-focused, and framed around the user's interest ("We noticed you like running gear" vs. "Our collaborative filtering algorithm matched your behavioral profile"). Individual differences in digital literacy significantly moderate the effect.
- **E-Commerce Application**: If explaining recommendations, use simple benefit-focused language: "Based on your recent searches" or "Popular in your area." Avoid technical framing like "personalized by our AI" or "algorithmically selected." Test whether explanation labels increase or decrease click-through for your specific audience — the effect is not universally positive.
- **Replication Status**: Mixed results across studies reflect genuine context-dependence rather than methodological issues.
- **Boundary Conditions**: Digitally sophisticated users respond better to transparency. Privacy-sensitive users may react negatively to any acknowledgment of data use. Benefit-focused framing is safer than mechanism-focused framing.
- **Evidence Tier**: Bronze

---

## Cross-Cutting Synthesis

| Dimension | Safe Zone | Danger Zone |
|---|---|---|
| **Data source** | First-party, zero-party, on-site behavior | Third-party, cross-site tracking, purchased data |
| **Transparency** | "Because you searched for X" | "Our AI analyzed your behavior" |
| **Timing** | Within 24-48 hours of interaction | Weeks after a single browse |
| **Depth** | Category-level, single-item | Full browsing history displayed |
| **Framing** | Social proof ("others also bought") | Algorithmic ("recommended for you") |
| **Pricing** | Universal promotions, loyalty tiers | Individual dynamic pricing |
| **Channel** | On-site, email (opted in) | Push notifications, location-triggered |
| **Recovery** | Not possible once creepiness triggers | Prevention is the only strategy |
| **Legal constraint** | First-party data, opted-in, with human review for high-stakes decisions | ADMT without opt-out (CA), solely automated significant decisions (GDPR Art. 22), subliminal manipulation (EU AI Act Art. 5), surveillance pricing (FTC scrutiny) |

## Key Takeaway for Implementation

The optimal personalization strategy operates **just below the creepiness threshold** using first-party data, social-proof framing, and transparent data sourcing. The paradox is real: consumers want personalization but react negatively when they notice the mechanism. The solution is personalization that feels like attentive service ("a good shopkeeper who remembers you") rather than surveillance ("a camera that follows you around the store").

---

---

### Finding 13 (NEW): CCPA/CPRA ADMT Regulations — Automated Decision-Making Technology Opt-Out (CA, eff. Jan 1, 2026)
- **Source**: California Privacy Protection Agency (CPPA), Final ADMT Regulations (OAL-approved 2025-09-22, effective 2026-01-01) — https://cppa.ca.gov/regulations/; CPRA (California Privacy Rights Act, Cal. Civ. Code § 1798.185(a)(16)). **Cross-ref**: ethics-gate.md Part 6.3.
- **Methodology**: Regulatory primary statute and final agency regulations.
- **Key Finding**: Effective January 1, 2026, California's CPPA ADMT regulations require: (1) consumers have the right to **opt out** of automated decision-making technology used for decisions with **significant effects** (employment, education, financial services, healthcare — but also expressly: targeting content and advertising); (2) businesses must provide pre-use notices disclosing what ADMT is used and for what purpose; (3) consumers have the right to access information about ADMT decisions and, in some cases, to obtain human review. For e-commerce personalization: product recommendation engines, dynamic pricing systems, and audience segmentation algorithms using sensitive inferences all fall within scope if they affect a California resident's access to goods or services.
- **E-Commerce Application**: Before January 1, 2026 (or immediately if past that date): audit personalization systems for ADMT triggers; add opt-out controls for significant-effect automated decisions involving California users; update privacy notices to disclose ADMT use. The CPPA interprets "significant effect" broadly — consult legal counsel on whether recommendation engines for pricing decisions qualify.
- **Evidence Tier**: Gold (regulatory primary — final CPPA regulations, OAL-approved 2025-09-22)

---

### Finding 14 (NEW): GDPR Article 22 — Right Not to Be Subject to Solely Automated Decisions
- **Source**: Regulation (EU) 2016/679 (GDPR) Article 22 — https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:02016R0679-20160504; EDPB (European Data Protection Board), Guidelines on Automated Individual Decision-Making and Profiling (WP251rev.01) — https://ec.europa.eu/newsroom/article29/items/612053. **Cross-ref**: ethics-gate.md Part 6.1.
- **Methodology**: Primary EU regulatory text + EDPB interpretive guidelines.
- **Key Finding**: GDPR Article 22 prohibits automated-only decisions "that produce legal effects concerning [the data subject] or similarly significantly affect [them]" unless: (a) the decision is necessary for the performance of a contract, (b) the data subject has given explicit consent, or (c) the decision is authorized by EU/Member State law. When exemptions apply, the data subject must retain the right to human review, to express their point of view, and to contest the decision. For e-commerce: dynamic pricing based on inferred characteristics, credit scoring for BNPL, and automated fraud decisions likely trigger Article 22. Product recommendations with no purchase-blocking effect likely do not.
- **E-Commerce Application**: Map all automated decision points in your personalization stack. For decisions affecting price, access to services, or credit: ensure one of the three lawful bases applies and implement human review mechanisms. Document decisions made by automated means and how they are explained to users.
- **Evidence Tier**: Gold (primary EU regulatory text + EDPB official interpretive guidelines)

---

### Finding 15 (NEW): EU AI Act Article 5(1)(a) — Prohibition on Subliminal/Manipulative AI Techniques
- **Source**: Regulation (EU) 2024/1689 (EU AI Act), Article 5(1)(a) — https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689 (prohibitions effective 2025-02-02). **Cross-ref**: ethics-gate.md.
- **Methodology**: Primary EU regulatory text.
- **Key Finding**: Article 5(1)(a) of the EU AI Act prohibits AI systems that *"deploy subliminal techniques beyond a person's consciousness or purposefully manipulative or deceptive techniques, with the objective, or the effect, of materially distorting the behaviour of a person…in a manner that causes or is reasonably likely to cause that person or another person significant harm."* This prohibition became effective **February 2, 2025**. For e-commerce personalization: AI-driven urgency messaging, scarcity indicators based on inferred consumer psychology profiles, and manipulation of decision environments using psychological vulnerabilities (dark patterns powered by AI) are at risk of falling within this prohibition.
- **E-Commerce Application**: Audit personalization interventions for subliminal or manipulative intent. Legitimate personalization (showing relevant products to users who have expressed interest) is not targeted by Art. 5(1)(a); psychological profiling used to exploit specific vulnerabilities (financial anxiety, impulsivity scores) is. The "significant harm" threshold limits scope but FINES are substantial (up to 3-6% of global annual turnover).
- **Evidence Tier**: Gold (primary EU regulatory text; prohibition provisions effective Feb 2, 2025)

---

### Finding 16 (NEW): FTC Surveillance Pricing Study — January 2025 Federal Scrutiny Signal
- **Source**: FTC, "Surveillance Pricing Study: A Report of the Federal Trade Commission" — released 2025-01-17 under FTC Act § 6(b) authority — https://www.ftc.gov/news-events/news/press-releases [specific press release URL for FTC Surveillance Pricing Study, Jan 2025; marked Citation Status: pending exact URL anchor from ftc.gov/news-events]. **Cross-ref**: ethics-gate.md.
- **Methodology**: FTC regulatory study / staff perspective (not a formal rule, but an authoritative signal of enforcement intent).
- **Key Finding**: In January 2025, the FTC released a study examining "surveillance pricing" — the use of extensive consumer data (location, browsing behavior, device data, biometrics) combined with AI to set individually optimized prices. The FTC expressed concern about harms to consumers, competitive distortion, and transparency failures. While not a rule, FTC § 6(b) studies historically precede enforcement actions and rulemaking. The study signals that AI-driven individualized pricing using behavioral/psychological profiling data is an active FTC priority.
- **E-Commerce Application**: If your personalization system influences pricing based on individual behavioral profiles (not just market demand), review your implementation against FTC surveillance pricing concerns. Universal dynamic pricing (price changes based on demand, time, or inventory) is generally lower risk; individual-targeted pricing based on inferred willingness-to-pay is higher risk. Document the data inputs and decision logic for any pricing algorithm.
- **Evidence Tier**: Gold (FTC official study released under FTC Act § 6(b) authority, January 2025)

---

*Research compiled: March 2026, reconciled April 2026. 16 findings (12 original + 4 legal/regulatory additions) from 20+ sources across academic research, industry surveys, field experiments, and regulatory primary sources.*
