<!-- RESEARCH_DATE: 2026-04-02 -->
<!-- AUDIT_DATE: 2026-04-22 (Reconciled from Run A + Run B, 2026-04-21) -->
<!-- AUDIT_CHANGES: F1 — softened unverifiable 82% figures; added Columbia CBS accessible datapoint and open-access PDF URL. F2 — updated primary Baymard figure from 48% (prior wave) to 39% (current live page, verified 2026-04-22); prior-wave 48% preserved as disclosure note; added wave hygiene note. F3 — added paywall-access caveat on 14.8%. F4 — new (regulatory: drip-pricing FTC/CA/EU risk). F5 — new (Shampanier et al. 2007 zero-price effect). Methodological notes 4 and 5 added. -->
<!-- NOTE: Key findings from this file have been merged into pricing-psychology.md. This file remains as supplementary reference with additional depth and context. -->
# Free Shipping: Goal-Gradient Psychology, Threshold Optimization, and Cart Abandonment

**Research Date**: April 2, 2026
**Last Audited**: April 22, 2026 (Reconciled — Run A + Run B)
**Total Findings**: 5 (new/extending); 2 covered by pricing-psychology.md
**Domain**: Free shipping thresholds, goal-gradient effect, cart abandonment, progress indicators, regulatory compliance
**Methodology**: Web-based literature review; academic papers; Baymard Institute research; industry data; regulatory primary sources

---

## ⚠️ OVERLAP NOTICE

The following findings are **already covered** by `pricing-psychology.md` in ECP:

| Covered Topic | CRO Finding | Summary |
|---|---|---|
| NuFace A/B test — free shipping threshold increased orders 90% | **Finding 15** | Red Door Interactive / VWO case study |
| Free shipping threshold industry data (58% add items; 15–25% AOV lift) | **Finding 16** | FedEx survey, Cartly Pro, Intelligems merchant data |

**Do not re-implement CRO Findings 15 or 16. Reference them directly.**

| Covered Topic | Other File | Summary |
|---|---|---|
| Unexpected costs as #1 controllable abandonment cause (Baymard) | `price-transparency.md` **Finding 1** | Same Baymard data — do not cite both |
| Unexpected costs as #1 controllable abandonment cause (Baymard) | `pricing-psychology.md` **Finding 36** | Canonical version in the CRO file |

---

## Summary

### Top 3 Most Impactful New Findings

1. **Finding 1 (Kivetz, Urminsky & Zheng 2006)**: The goal-gradient hypothesis — people accelerate effort as they approach a goal — is empirically validated in a loyalty card field experiment showing substantial purchase acceleration in the final stages of goal pursuit and a significant positive effect of "illusionary head start" framing. This is the scientific foundation underlying free shipping progress bars.
2. **Finding 2 (Baymard Institute — current wave)**: 39% of US shoppers who abandon carts cite "extra costs too high" (shipping, tax, fees) as a primary controllable reason (current Baymard public page, verified 2026-04-22). Earlier Feb 2024 wave reported 48% — see wave disclosure note. Baymard is the gold-standard source on cart abandonment behavior.
3. **Finding 3 (Lewis 2006)**: The first field experiment in e-commerce specifically testing free shipping against paid shipping found that free shipping increased demand by approximately 14.8% but reduced revenue per order — establishing the tradeoff that proper threshold setting is designed to solve.

---

## Findings

### Finding 1: Goal-Gradient Effect — Scientific Foundation for Free Shipping Progress Bars
- **Source**: Kivetz, R., Urminsky, O., & Zheng, Y. (2006). "The Goal-Gradient Hypothesis Resurrected: Purchase Acceleration, Illusionary Goal Progress, and Customer Retention." *Journal of Marketing Research*, 43(1), 39–58. <https://doi.org/10.1509/jmkr.43.1.39> — Open-access PDF: https://home.uchicago.edu/ourminsky/Goal-Gradient_Illusionary_Goal_Progress.pdf
- **Methodology**: Multi-study field experiment and laboratory design. Field experiment 1: real coffee stamp loyalty card program (N = 900+ customers). Customers received cards requiring 10 stamps for a free coffee reward; researchers measured inter-purchase time as customers approached the 10th stamp. Study 2: "illusionary head start" manipulation — some cards started with 2 stamps already marked on a 12-stamp card vs. a fresh 10-stamp card; both required 10 additional stamps for reward. Studies 3–5: laboratory replications with real-incentive tasks, including an internet music-rating website. Original Hull (1932) rat maze studies provide the behaviorism foundation.
- **Key Finding**: Purchase frequency accelerated substantially as customers approached the reward threshold — café customers purchased coffee more frequently as they got closer to earning a free coffee; internet users visited the rating website more often, rated more songs per visit, and were less likely to terminate a session as they approached the incentive threshold. The illusionary head-start card led to meaningfully faster completion than the fresh 10-stamp card control — the Columbia Business School summary of the paper notes median completion times of approximately 10 days (head-start group) vs. 15 days (control), driven purely by perceived proximity to the goal rather than any difference in actual remaining effort. The effect is driven by perceived proximity to the goal, not the absolute number of actions remaining.
  - **Audit note (2026-04-22)**: The prior file version cited "82% faster purchase acceleration" and "82% completion rate lift" as specific figures. These specific percentages could not be content-matched against any accessible paper summary and should not be asserted as definite numbers. The Columbia Business School summary (10 vs. 15 days) is the best accessible concrete datapoint. The directional finding — substantial acceleration and significant head-start effect — is fully supported.
- **E-Commerce Application**: Free shipping progress bars work because of the goal-gradient effect — showing "You're $18 away from free shipping!" creates a mental goal state that accelerates purchase behavior as the customer approaches the threshold. The "head start" finding suggests pre-loading perceived progress: "You already qualify for standard shipping — add $18 more for FREE shipping" outperforms a blank progress bar starting from zero. Use specific dollar amounts ("$18 away") not round numbers ("about $20 away") — specificity increases goal salience. Update the progress bar in real-time on item add.
- **Replication Status**: One of the most-cited goal-gradient papers in marketing (1,800+ Google Scholar citations). Replicated in loyalty program, e-commerce, and gamification contexts. The foundational Hull (1932) animal learning result has been replicated hundreds of times. Robust finding.
- **Boundary Conditions**: Effect requires customers to be actively engaged in goal pursuit — passive browsers don't exhibit goal-gradient acceleration. Goal must be perceived as achievable: if the threshold is too far away, the goal feels unattainable and the gradient disappears. Effect is strongest when: (a) the goal is meaningful to the customer, (b) progress is visually salient, (c) the remaining distance is small relative to total journey. Illusionary progress is ethically acceptable when based on real baseline activity; fake pre-loaded progress bars unrelated to actual behavior are manipulative.
- **Evidence Tier**: Gold (peer-reviewed JMR, field experiment with real purchases, extensively replicated)

---

### Finding 2: Unexpected Costs as a Top Controllable Abandonment Cause
- **Source**: Baymard Institute. (Ongoing). "Cart Abandonment Rate Statistics." https://baymard.com/lists/cart-abandonment-rate — Primary methodology: Meta-analysis of 50+ published studies on cart abandonment rate, supplemented by in-house usability testing of 4,400+ hours with real shoppers across checkout flows.
- **Methodology**: Baymard's abandonment reason data comes from a proprietary large-scale survey of US online shoppers. Participants select reasons for their most recent cart abandonment from a multi-select list. Figures reported are from the subset who abandoned for reasons other than "just browsing / not ready to buy." Survey waves are updated periodically; the live page does not always show an explicit wave date.
- **Key Finding** (current Baymard public page, verified 2026-04-22): **39%** of US online shoppers cite "Extra costs too high (shipping, tax, fees)" as a reason for cart abandonment — the #1 controllable reason. Top abandonment reasons from the current page: 39% extra costs too high; 21% delivery too slow; 19% didn't trust site with credit card; 19% site required account creation; 18% checkout process too long/complicated; 15% returns policy unsatisfactory; 15% website errors/crashes; 14% couldn't see/calculate total cost upfront; 10% insufficient payment methods; 8% credit card declined. Baymard estimates **$260 billion** in potentially recoverable revenue in US+EU annually if checkout UX were best-practice (verbatim confirmed on live page).
  - **Prior-wave disclosure**: An earlier Baymard survey wave (Feb 2024, N = 2,058 US shoppers) reported **48%** for "extra costs too high" among motivated-shopper abandoners. The 48% figure is defensible when cited with explicit wave-year attribution. The current live page shows 39% with no wave date displayed. **This file now uses 39% as the primary figure.** See also: cross-file consistency note in Decisions — this same stat appears in `price-transparency.md` Finding 1 and `pricing-psychology.md` Finding 36; all three files should adopt the same wave-year choice in a coordinated pass.
- **E-Commerce Application**: The business case for a free shipping threshold is direct: a large share of motivated shoppers are abandoning because of cost surprise, and free shipping thresholds (a) reduce the cost itself or (b) make the cost feel earned. Implement: (1) free shipping threshold clearly communicated in site-wide header, (2) progress bar in cart showing distance to threshold, (3) product recommendations in cart for items that would qualify the order. Also address the "account creation required" and "couldn't see total cost upfront" reasons — they are close seconds and often cheaper to fix than changing shipping economics.
- **Replication Status**: Baymard is the authoritative source on e-commerce checkout usability. Their survey data has been published consistently since 2010 with stable findings. The #1-controllable-reason status of "extra costs too high" is stable across waves; specific percentages vary between waves (48% in one wave, 39% in the current). Consistent with similar surveys from Statista, SaleCycle, and Klaviyo.
- **Boundary Conditions**: Percentages are from US shoppers; EU and international data varies. Later Baymard waves may report different specific percentages — always verify against the live page and note the wave. Mobile shoppers show higher abandonment overall but similar reason distributions. B2B shoppers with expense accounts show less shipping cost sensitivity. For products where shipping cost is inherently high (oversized furniture, heavy equipment), threshold strategies are less effective than flat-rate or included shipping.
- **Evidence Tier**: Gold (Baymard Institute meets Gold tier criteria as recognized industry research authority; methodology is transparent and peer-comparable in scope)

---

### Finding 3: Free vs. Paid Shipping Demand Elasticity — The Cost-Revenue Tradeoff
- **Source**: Lewis, M. (2006). "The Effect of Shipping Fees on Customer Acquisition, Customer Retention, and Purchase Quantities." *Journal of Retailing*, 82(1), 13–23. <https://doi.org/10.1016/j.jretai.2005.11.005>
- **Methodology**: Field experiment using natural variation in shipping fee structures across a major online grocery retailer's customer base. Analyzed 38,000+ transactions over multiple periods with different shipping fee schedules ($0 free shipping vs. flat fee vs. variable fee). Controlled for customer tenure, purchase frequency, basket size, and product category. Abstract confirms: "shipping fees greatly influence order incidence rates and graduated shipping fees significantly affect average expenditures."
- **Key Finding**: Free shipping increased order incidence by approximately 14.8% compared to flat-fee shipping (figure from full paper; not visible in public abstract — preserved on good-faith citation of peer-reviewed source). However, free shipping *reduced* revenue per order because customers who previously paid shipping fees no longer needed to justify those fees with larger baskets. The net effect on revenue was positive only when combined with a minimum order threshold — threshold-based free shipping captured the demand increase while preserving or growing basket size. Flat free shipping (no threshold) is a value transfer, not a revenue strategy. Paper's abstract framing: "customer acquisition is more sensitive to order size incentives while retention is more influenced by base shipping fee levels."
- **E-Commerce Application**: This study directly establishes *why* thresholds matter. Free shipping with no threshold is a customer acquisition tool that trades margin for volume. Free shipping with a well-set threshold converts the cost into an AOV driver. The 15–25% above AOV rule (CRO Finding 16) reflects this economics: set the threshold high enough that reaching it requires basket-building, but low enough that the goal is achievable. Lewis's demand elasticity finding is the demand-side estimate; the AOV lift from threshold-reaching behavior (15–30% per CRO Finding 16) is the supply-side offset.
- **Replication Status**: Single field experiment with a large real-transaction dataset. The direction of findings (free shipping increases orders, threshold preserves margin) has been replicated in subsequent e-commerce research and is consistent with economic theory. Specific elasticity numbers are context-specific.
- **Boundary Conditions**: Study was conducted on grocery/subscription-type purchases with high repurchase frequency. Demand elasticity for free shipping varies substantially by product category: commodity goods show higher elasticity; high-consideration goods (furniture, electronics) show lower elasticity because customers have already decided to buy and are less influenced by shipping terms at the margin. Highly price-sensitive segments show greater shipping elasticity.
- **Evidence Tier**: Gold (peer-reviewed Journal of Retailing, large real-transaction field experiment)

---

### Finding 4 (NEW — 2026-04-22): Drip-Pricing Legal Risk — FTC Section 5, CA SB-478, and EU UCPD
- **Source**: (1) FTC Act Section 5 (15 U.S.C. § 45) — https://www.law.cornell.edu/uscode/text/15/45; (2) FTC Rule on Unfair or Deceptive Fees, 16 CFR Part 464 (effective May 12, 2025) — https://www.ftc.gov/news-events/news/press-releases/2025/05/ftc-rule-unfair-or-deceptive-fees-take-effect-may-12-2025; (3) California SB-478 Honest Pricing Law, Cal. Civ. Code § 1770(a)(29) (effective July 1, 2024) — https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=202320240SB478
- **Methodology**: Regulatory-document tracing from primary federal and state sources. California SB-478 text verified verbatim via leginfo.legislature.ca.gov. FTC Junk Fees Rule scope verified via May 2025 FTC press release.
- **Key Finding**: Hiding shipping fees until final checkout ("drip pricing") is a documented dark pattern with meaningful legal risk, but the legal landscape in 2026 is more nuanced than often represented:
  1. **FTC Junk Fees Rule (16 CFR 464)**, effective May 12, 2025: applies to **live-event ticketing and short-term lodging ONLY**. Does NOT currently cover general e-commerce shipping.
  2. **FTC Act Section 5 (15 U.S.C. § 45)**: applies broadly to "unfair or deceptive acts or practices" in e-commerce. Has been used against drip-pricing tactics generally. Shipping-cost suppression until final checkout is potentially within Section 5 deception scope; no specific e-commerce shipping enforcement case confirmed as of 2026-04-22.
  3. **California SB-478 (Civ. Code § 1770(a)(29))**: requires all-in pricing for goods and services but contains an explicit carve-out at subsection (B)(ii): "postage or carriage charges that will be reasonably and actually incurred to ship the physical good to the consumer" are **excluded** from the mandatory all-in-price requirement. California does NOT require shipping to be included in the displayed price. California AG UCL penalty: **$2,500 per violation**.
  4. **EU UCPD Article 7** (misleading omissions) plus Annex I prohibit material information omissions in invitations to purchase. Shipping costs not disclosed before checkout commitment are potentially within scope in EU markets.
- **E-Commerce Application**: "Free shipping is legally required" claims are **FALSE** — no federal or California law mandates free shipping. However, deliberate suppression of shipping costs until the final confirmation step can expose merchants to FTC Section 5 deception claims (US) and EU UCPD Article 7 claims (EU). Best practice: (a) disclose shipping cost or "free above $X" threshold in site-wide header; (b) compute and show shipping in cart (pre-checkout) whenever zip code is known; (c) never hide a non-zero shipping fee behind a "Get Quote" step if an estimate can be provided; (d) the regulatory trajectory (FTC attention on drip pricing, CA SB-478 all-in pricing principle) suggests expanded scope may come even if general e-commerce shipping is not yet covered by the Junk Fees Rule.
- **Replication Status**: Regulatory-source finding. CA SB-478 carve-out is verbatim-confirmed. FTC Junk Fees Rule scope confirmed. This is a compliance finding, not a behavioral-experiment finding — "replication" is not the applicable standard.
- **Boundary Conditions**: Currently no federal e-commerce shipping-specific rule beyond generic Section 5. State UDAP exposure varies — CA, CO, NY are active enforcers. EU authority is stronger with UCPD. The behavioral evidence for drip-pricing harm (39% abandonment due to extra costs, Finding 2) independently motivates early disclosure independent of legal risk.
- **Evidence Tier**: Silver (primary regulatory sources; clear legal authority established; no specific named enforcement case against a general e-commerce shipping drip-pricer confirmed as of 2026-04-22)

---

### Finding 5 (NEW — 2026-04-22): Zero-Price Effect — Why "Free" Shipping Is Worth More Than Its Monetary Value
- **Source**: Shampanier, K., Mazar, N., & Ariely, D. (2007). "Zero as a Special Price: The True Value of Free Products." *Marketing Science*, 26(6), 742–757. <https://doi.org/10.1287/mksc.1060.0254>
- **Methodology**: Series of field and laboratory experiments at MIT. Experiment 1: participants chose between Hershey's Kiss and Lindt Truffle at various price points. At market prices, most chose Lindt. When both prices were reduced by an equal absolute amount — Hershey's from 1¢ to FREE and Lindt from 14¢ to 13¢ — choice shifted dramatically toward Hershey's. Standard economic theory predicts no choice change (relative value difference is identical); observed behavior violates this prediction. Additional experiments varied products and price scales; bundled-offer experiments directly relevant to shipping framing.
- **Key Finding**: "Zero" is not merely the lowest price — it is a psychologically distinct category that triggers a positive affect response independent of the rational value calculation. When an option becomes FREE, its perceived value increases disproportionately beyond what the monetary saving would predict. The effect applies to bundled offers: "buy X, shipping FREE" is perceived as meaningfully better than "buy X, shipping $2" even when the item price is raised by $2 to produce an equivalent total cost. Replicated across multiple experiments and product types.
- **E-Commerce Application**: The zero-price effect is the deeper psychological mechanism explaining why free-shipping offers frequently outperform equivalent discounts. Implications: (1) Absorbing shipping cost into product price and calling it "free shipping" can outperform displaying "Product + low shipping" at an identical total — provided margin allows and consumers do not suspect the reframe; (2) "Free shipping with $50 order" framing outperforms "Save $6.99 shipping with $50 order" even when dollar impact is identical; (3) Never charge a trivial shipping fee ($1.99) if elimination is feasible — the psychological transition from ">$0" to "$0" is worth far more than the $1.99 revenue recovery; (4) This applies across product categories but is strongest for lower-priced items where shipping is a larger percentage of total cost.
- **Replication Status**: Foundational paper in the psychology of pricing, 2,500+ Google Scholar citations. Replicated across fast food, online retail, and other contexts (e.g., Kamins et al.). "Zero price effect" is one of the more robust findings in consumer behavior research.
- **Boundary Conditions**: Effect is strongest for: (a) low-to-mid-priced items where absolute savings are small but percentage-of-total impact is large; (b) contexts where the "free" option is genuine and unbundled (no hidden conditions); (c) consumer purchasing — B2B buyers with expense accounts show weaker zero-price preference because the decision is delegated to reimbursement. Effect weakens when consumers suspect the "free" option is subsidized by inflated item prices.
- **Evidence Tier**: Gold (INFORMS Marketing Science peer-reviewed; foundational paper; extensively replicated)

---

## Methodological Notes

1. **The NuFace 90% Lift Caveat**: CRO Finding 15 notes the 90% order lift partly reflected revealing a previously-hidden free shipping offer, not purely adding free shipping. Lewis (2006, Finding 3 here) provides a more conservative and generalizable demand estimate for adding free shipping — use this as a realistic baseline expectation; the NuFace number is an outlier ceiling.

2. **Threshold Calculation**: The scaffolded file's "AOV × 1.15 to 1.25" formula is practical and defensible. Lewis's finding adds: set the threshold such that *most orders that would naturally qualify anyway* still qualify, but a meaningful portion of near-qualifying orders are motivated to add items. Baymard data (CRO Finding 16: 58% of shoppers add items to reach threshold) suggests the threshold is being set in the right range when more than half of non-qualifying orders result in basket-building behavior.

3. **Goal-Gradient Practical Implementation**: Kivetz et al. (Finding 1) show the head-start effect is powerful. In e-commerce: "You've already added $45 in items — just $30 more for free shipping" uses the customer's existing basket as an established baseline, creating a head-start framing. This outperforms "Add $30 more for free shipping" which treats the basket as empty. The reframe is a single copy change with meaningful conversion impact.

4. **Zero-Price + Goal-Gradient Combined Effect**: Findings 1 (goal gradient) and 5 (zero-price effect) compound in threshold-based free shipping. The progress bar frames the threshold as a goal (triggering gradient acceleration as the customer approaches), and reaching the threshold delivers "FREE" (triggering the zero-price affect response). Together they explain why threshold-based free shipping frequently outperforms equivalent flat discounts — the mechanism is both behavioral-economic and psychological.

5. **Baymard Wave Hygiene**: The Baymard cart abandonment percentage for "extra costs too high" has varied across survey waves — 48% in an earlier wave (Feb 2024), 39% on the current live page (verified 2026-04-22). Always verify the figure against the live page at time of use and note the wave or verification date in citations. Three files in this plugin share this stat (free-shipping F2, price-transparency F1, pricing-psychology F36); coordinate wave-year decisions across all three.

---

## Sources Consulted

- Kivetz, R., Urminsky, O., & Zheng, Y. (2006). *Journal of Marketing Research*, 43(1), 39–58. <https://doi.org/10.1509/jmkr.43.1.39> (Open-access PDF: https://home.uchicago.edu/ourminsky/Goal-Gradient_Illusionary_Goal_Progress.pdf)
- Baymard Institute. (Ongoing). Cart abandonment rate statistics. https://baymard.com/lists/cart-abandonment-rate (Live page verified 2026-04-22; current figure: 39%)
- Lewis, M. (2006). *Journal of Retailing*, 82(1), 13–23. <https://doi.org/10.1016/j.jretai.2005.11.005>
- Shampanier, K., Mazar, N., & Ariely, D. (2007). *Marketing Science*, 26(6), 742–757. <https://doi.org/10.1287/mksc.1060.0254>
- FTC Act Section 5. 15 U.S.C. § 45. https://www.law.cornell.edu/uscode/text/15/45
- FTC Rule on Unfair or Deceptive Fees. 16 CFR Part 464 (effective May 12, 2025). https://www.ftc.gov/news-events/news/press-releases/2025/05/ftc-rule-unfair-or-deceptive-fees-take-effect-may-12-2025
- California SB-478 Honest Pricing Law. Cal. Civ. Code § 1770(a)(29). https://leginfo.legislature.ca.gov/faces/billNavClient.xhtml?bill_id=202320240SB478
- Hull, C.L. (1932). "The goal-gradient hypothesis and maze learning." *Psychological Review*, 39(1), 25–43. [Foundational behaviorism reference]
- NuFace/VWO/Red Door Interactive case study. [pricing-psychology.md Finding 15 — do not re-research]
- FedEx, Cartly Pro, Intelligems merchant data. [pricing-psychology.md Finding 16 — do not re-research]
