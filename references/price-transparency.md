<!-- RESEARCH_DATE: 2026-04-21 -->
<!-- RECONCILED: 2026-04-22 — see docs/research-audit/ecp-reconciled-FINAL-2026-04-22/RECONCILED/price-transparency.md for full audit log -->
# Price Transparency: Drip Pricing, Hidden Fees, and Trust Economics

**Research Date**: April 21, 2026 (original: April 2, 2026; revised at audit)
**Total Findings**: 7 (Findings 1–4 corrected/verified; Findings 5–7 regulatory additions)
**Domain**: Price transparency, drip pricing, hidden fees, cost disclosure timing, consumer trust
**Methodology**: Web-based literature review; academic economics; Baymard Institute; FTC + state + EU regulatory research

---

## ⚠️ OVERLAP NOTICE

Price transparency has **no direct overlap** with `pricing-psychology.md` findings. The CRO file addresses how to *present* prices (anchoring, charm, bundles); this file addresses *what costs to show, when, and how* to avoid abandonment from surprise fees.

**Adjacent overlaps to note:**
- Cart abandonment from extra costs is mentioned in CRO Finding 36 (same Baymard source) and CRO Finding 15/16 (free shipping). Do not cite all three files for the same recommendation — use this file as the primary reference for transparency mechanics.
- Loss aversion framing (CRO Finding 8) provides the mechanism for why hidden fees feel punitive — late-revealed costs trigger the loss aversion response at a moment when the customer is already emotionally committed.
- **Cross-file harmonization required**: `pricing-psychology.md` Finding 36 and `free-shipping.md` Finding 2 reference the same Baymard abandonment data. All three files should cite the same survey wave.

---

## Summary

### Top 3 Most Impactful New Findings

1. **Finding 1 (Baymard 2024 — Abandonment Causes)**: 39% of motivated shoppers abandon carts due to unexpected extra costs — the single largest controllable abandonment driver (prior wave showed 48%; direction and rank stable). This is the primary business case for full price transparency.
2. **Finding 2 (Morwitz, Greenleaf & Johnson 1998)**: Partitioned pricing reduces the recalled total price — but this is a double-edged sword: *transparent* early partitioning can raise perceived value, while *late-revealed* partitioning creates checkout shock and abandonment.
3. **Finding 3 (Hossain & Morgan 2006 — eBay Field Experiment)**: Revenue non-equivalence in online auctions: identical total prices produce different outcomes depending on how base price and shipping are split, because bidders treat them as separate mental accounts (bounded rationality). Note: the paper's causal direction is that high-shipping/low-base listings attracted MORE bidders and higher revenue — not fewer (see Audit Note).

---

## Findings

### Finding 1: Unexpected Costs as the Primary Controllable Abandonment Driver
- **Source**: Baymard Institute. (2024). "Cart Abandonment Rate Statistics." https://baymard.com/lists/cart-abandonment-rate — Also: Baymard Institute. "E-Commerce Checkout Usability: Benchmark." Premium research report (subscriber access). https://baymard.com/research
- **Methodology**: Ongoing large-scale consumer survey of US adult online shoppers who abandoned carts for reasons other than casual browsing. Supplemented by 4,400+ hours of qualitative usability testing on real checkout flows at 70+ major e-commerce sites. Meta-analysis of 50+ published studies yielding a 70.22% average abandonment rate baseline.
- **Key Finding (current wave, 2024)**: **39%** of non-browsing cart abandoners cite "extra costs too high" (shipping, tax, fees revealed late in checkout) as their primary reason — consistently #1 across Baymard survey waves. Secondary: **14%** couldn't calculate total cost up-front. Combined, more than half of non-browse abandonment is driven by cost visibility failures. Baymard estimates ~$260B recoverable revenue in the US+EU annually. *(Note: A prior Baymard wave, February 2024, showed 48% for extra costs and 17% for can't-see-total. Baymard updates headline figures across waves; specific percentages are wave-dependent. The directional finding — extra costs is the #1 controllable driver — is stable since 2010.)*
- **E-Commerce Application**: Every cost that will be charged to the customer must be visible at the earliest possible touchpoint: (1) **Shipping** — display exact amount or "Free shipping" on the product page, not at checkout. (2) **Tax** — display an estimate ("est. $X") on the product page or cart; exact calculation at checkout is acceptable if an estimate was shown earlier. (3) **Service fees, handling fees, processing fees** — never reveal at checkout; either include in base price or show prominently on product pages. Single highest-leverage fix for most e-commerce sites: add shipping estimate to product page.
- **Replication Status**: Baymard findings are consistent across multiple survey waves and directionally consistent with similar surveys from SaleCycle (~47% cite unexpected costs), Klaviyo (similar range), and Statista. The 70.22% average abandonment rate is a meta-analytic estimate across 50+ studies. Authoritative for e-commerce UX purposes.
- **Boundary Conditions**: B2B purchasers with expense accounts show lower shipping cost sensitivity. Mobile shoppers show higher overall abandonment but similar reason distributions. International shoppers show higher abandonment from tax/duty surprises.
- **Citation Status**: Current Baymard page (last updated ~Sept 2025) shows 39% for "extra costs too high." A February 2024 survey wave showed 48% per multiple secondary sources (eMarketer, Shopify, Contentsquare). **Cross-file harmonization required**: `pricing-psychology.md` Finding 36 and `free-shipping.md` Finding 2 must cite the same wave.
- **Evidence Tier**: Gold (Baymard Institute is the recognized methodological leader in e-commerce checkout research)

---

### Finding 2: Partitioned Pricing — The Psychological Double-Edged Sword
- **Source**: Morwitz, V.G., Greenleaf, E.A., & Johnson, E.J. (1998). "Divide and Prosper: Consumers' Reactions to Partitioned Prices." *Journal of Marketing Research*, 35(4), 453–463. <https://doi.org/10.1177/002224379803500404> — Extended by: Bertini, M., & Wathieu, L. (2008). "Attention Arousal Through Price Partitioning." *Marketing Science*, 27(2), 236–246. <https://doi.org/10.1287/mksc.1070.0295>
- **Methodology**: Morwitz et al.: Laboratory experiments (multiple studies, N ≈ 90–150 each) testing consumer responses to partitioned vs. combined pricing. Experiment 1: hotel room rate shown as (a) single total price, (b) room rate + resort fee. Measured recalled price, perceived value, and purchase intent. Additional studies varied fee salience and ordering. Product categories: hotel rooms, airline tickets, consumer electronics. Bertini & Wathieu: Extended the framework showing that partitioning focuses attention on the base-price component via an attention-arousal mechanism.
- **Key Finding**: Partitioned pricing (separating base price from surcharges) reduces the recalled total price — when the surcharge is presented separately, consumers focus on the base price as the "product cost" and underweight the surcharge. This selective attention increases purchase intent initially. HOWEVER: when the full cost is revealed at checkout (standard drip pricing pattern), the contrast between the expected cost (base price) and actual cost (base + fees) creates a sharp negative reaction — the fee is experienced as a *loss* relative to the adjusted reference price. The larger the gap, the stronger the abandonment reaction. Transparent partitioned pricing (showing all components early) can preserve the base-price salience benefit while avoiding checkout shock.
- **E-Commerce Application**: There is a legitimate use of partitioned pricing: showing shipping and tax as separate line items (vs. an all-in price) is transparent and helps customers understand what they're paying for. The problem is *late revelation* of components. The solution: show all components (base price, shipping, tax, any fees) as separate line items from the product page forward — not just at checkout. Cart should show a running estimated total including all known charges. This captures the cognitive advantage of itemization without the trust-destroying surprise.
- **Replication Status**: Morwitz et al. (1998) is a foundational paper with 1,200+ citations. The partitioned pricing effect has been extensively replicated — notably by Bertini & Wathieu (2008) on the attention mechanism, and by Hossain & Morgan (2006) in eBay auction data. Direction of finding is robust.
- **Boundary Conditions**: Partitioned pricing is only beneficial when the additional components are genuinely informative and valued by consumers. Artificial fee carving (inventing fees to partition) reduces trust and triggers FTC scrutiny. Effect is reversed when consumers actively shop for lowest total cost. EU Price Indication Directive mandates VAT-inclusive display, eliminating the partitioned pricing advantage for EU retailers in the tax component.
- **Evidence Tier**: Gold (peer-reviewed JMR, multiple studies, extensively replicated)

---

### Finding 3: Revenue Non-Equivalence from Shipping Partitioning — eBay Field Evidence
- **Source**: Hossain, T., & Morgan, J. (2006). "…Plus Shipping and Handling: Revenue (Non) Equivalence in Field Experiments on eBay." *B.E. Journal of Economic Analysis & Policy: Advances*, 6(2), Article 3. <https://doi.org/10.2202/1538-0637.1429> — Supplementary context: UK Office of Fair Trading (2010). "Advertising of Prices." OFT1291, summarized in GOV.UK/CMA online-choice-architecture evidence review: https://www.gov.uk/government/publications/online-choice-architecture-how-digital-design-can-harm-competition-and-consumers/evidence-review-of-online-choice-architecture-and-consumer-and-competition-harm.
- **Methodology**: Hossain & Morgan: Field experiment on eBay. Identical CDs and Xbox games listed as matched pairs with different starting bids and offsetting shipping costs (e.g., $1 start + $4 shipping vs. $5 start + free shipping). Measured final price, number of bidders, and total revenue. Total minimum cost to buyers was equalized across conditions. UK OFT: Market study including consumer survey (N = 3,000 UK consumers) and mystery shopping of 500+ websites.
- **Key Finding**: **Hossain & Morgan**: Despite economic equivalence in total cost, the two listing formats produced different outcomes. Their central result: high-shipping-cost / low-opening-price listings attracted **more bidders and higher revenues** than low-shipping / higher-base equivalents — contrary to the rational expectation that bidders would offset the shipping cost in their bids. They attribute this to bounded rationality: bidders treat base price and shipping as separate mental accounts, consistent with Morwitz et al. (1998). This means the shipping-partitioning effect (base-price salience) operated in sellers' favor in the eBay auction format. The boundary: the effect holds only when shipping charges are not excessive; unreasonably high shipping triggers backlash and reverses the pattern. **UK OFT**: 76% of surveyed consumers reported experiencing unexpected online charges; 34% reported abandoning a purchase as a direct result of hidden charges.
- **E-Commerce Application**: The Hossain & Morgan finding is more nuanced than "drip pricing always reduces conversions" — in an auction context, base-price salience combined with moderate itemized shipping can actually increase participation. For fixed-price retail e-commerce, the direct "drip pricing reduces conversion" evidence comes from Baymard survey data (Finding 1) and the partitioned-pricing literature (Morwitz 1998, Finding 2). The practical implication remains: make shipping visible early (product page, not checkout), keep shipping charges reasonable, and itemize components rather than hiding them in inflated base prices.
- **Replication Status**: Hossain & Morgan (2006) has 1,000+ citations. The bounded-rationality interpretation (bidders under-account for shipping) is well-supported by subsequent work. The UK OFT 2010 study is widely cited in drip-pricing secondary literature.
- **Boundary Conditions**: Hossain & Morgan's effect studied on eBay auction format specifically; does not directly generalize to fixed-price retail. In fixed-price e-commerce, late revelation of shipping triggers abandonment per Baymard data and partitioned-pricing theory. Excessive shipping charges break the auction effect — consumers recognize manipulation and reject listings.
- **Citation Status**: Kim, Natter & Spann (2009) was cited as a primary source in the original live file — **this was a miscitation**; that paper is about "Pay What You Want" pricing mechanisms, not drip pricing, and has been removed. UK OFT1291 URL returned 404 at audit (April 2026); the specific survey figures (76%, 34%, N=3,000) could not be content-matched at the cited URL. The OFT 2010 study is widely cited in secondary drip-pricing literature; treat as a supporting reference pending re-retrieval from UK National Archives (https://webarchive.nationalarchives.gov.uk/). Primary causal evidence for this finding is Hossain & Morgan (2006).
- **Audit Note (2026-04-22)**: The original live file stated that high-shipping/low-base-price listings attracted "14% fewer bidders" and "less total revenue" — **this reversed the actual Hossain & Morgan finding**. The paper documents the opposite: high-shipping/low-base listings attracted MORE bidders and MORE revenue, attributable to bounded rationality and separate mental accounts. The "14% fewer bidders" figure is unsupported and has been removed.
- **Evidence Tier**: Gold (Hossain & Morgan: peer-reviewed field experiment, B.E. Journal of Economic Analysis & Policy; OFT: government market study — figures pending re-verification)

---

### Finding 4: Price Guarantee Psychology — Trust Signal Without Operational Cost
- **Source**: Jain, S., & Srivastava, J. (2000). "An Experimental and Theoretical Analysis of Price-Matching Refund Policies." *Journal of Marketing Research*, 37(3), 351–362. https://journals.sagepub.com/doi/10.1509/jmkr.37.3.351 — Also: Moorthy, S., & Winter, R.A. (2006). "Price-Matching Guarantees." *RAND Journal of Economics*, 37(2), 449–465. <https://doi.org/10.1111/j.1756-2171.2006.tb00029.x>
- **Methodology**: Jain & Srivastava: Laboratory experiments (N = 150+, multiple studies) testing consumer responses to price-matching guarantees. Measured purchase intent, quality perception, and price sensitivity across conditions with and without price-match offers. Moorthy & Winter: Game-theoretic model with empirical support showing conditions under which price-matching guarantees emerge in competitive markets and their effect on equilibrium prices.
- **Key Finding**: Price-matching guarantees increase purchase intent and reduce price sensitivity even when consumers almost never invoke them. Mechanism: the guarantee signals that the seller is confident in their pricing competitiveness, reducing the consumer's perceived need to comparison shop. Moorthy & Winter find that price-match guarantees paradoxically *facilitate higher prices* in competitive markets because they reduce consumer search. For individual retailers, the trust and conversion benefit significantly outweighs the rare cost of actually matching a competitor's price.
- **E-Commerce Application**: Display a price-match guarantee prominently near the price/CTA on product pages. Frame it as: "Found it cheaper? We'll match it." The guarantee reduces comparison-shopping urgency in-session, increasing conversion. For DTC brands, it signals confidence in the value proposition. For marketplaces, it's less applicable since competitors are visible on the same page.
- **Replication Status**: The conversion benefit of price guarantees is well-documented in marketing literature. Jain & Srivastava's experimental evidence is supported by field studies of retailers who added/removed price guarantees. Moorthy & Winter's game-theoretic predictions are directionally confirmed in empirical work.
- **Boundary Conditions**: Price guarantees work best when (a) actual competitor pricing is not trivially easy to check, (b) the customer doesn't have a specific competitor in mind already, (c) the guarantee claiming process is perceived as easy. A complicated claiming process is counterproductive — it signals the offer is not genuine.
- **Citation Status**: Jain & Srivastava DOI (`10.1509/jmkr.37.3.351`) returned 404 in multiple audit attempts. The canonical SAGE URL above is proposed as an alternate; **verify this URL resolves before finalizing**. The paper is confirmed via Google Scholar and ResearchGate; accessible through those routes if the SAGE URL is also unstable.
- **Evidence Tier**: Gold (Jain & Srivastava: peer-reviewed JMR; Moorthy & Winter: peer-reviewed RAND Journal of Economics)

---

### Finding 5: California SB-478 — State-Level Ban on Hidden Fees (Effective July 1, 2024)
- **Source**: California Civil Code §§ 1770(a)(29), 1771.1 (added by SB-478, 2023; effective July 1, 2024). Bill text: https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202320240SB478 — Codified text: https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?lawCode=CIV&division=3.&title=1.5.&part=4.&chapter=&article=
- **Methodology**: California statute; enforced by California Attorney General and via Civil Code private right of action under the Consumers Legal Remedies Act (CLRA). Shipping carve-out: Cal. Civ. Code § 1770(a)(29)(B)(ii).
- **Key Finding**: SB-478 makes it a violation of the CLRA to advertise, display, or offer a price for a good or service that does not include all mandatory fees or charges, other than: (a) taxes or fees imposed by a government on the transaction, and (b) reasonable shipping costs actually charged to the consumer. The law targets mandatory non-governmental, non-shipping fees added at checkout. It does not require that shipping be free or that government taxes be pre-calculated into advertised prices.
- **E-Commerce Application**: US e-commerce sites serving California customers must include all mandatory non-government-tax, non-shipping fees in the headline advertised price. "Service fee," "convenience fee," "processing fee," mandatory handling fees — these must be in the displayed price, not added at checkout. Shipping and government sales tax remain permissible as separate line items. Effective July 1, 2024; multiple private suits and AG enforcement actions filed 2024–2025.
- **Replication Status**: Regulatory requirement; not a research finding. California is the most populous US state and a de facto national compliance floor for consumer-facing e-commerce.
- **Boundary Conditions**: Applies to consumer-facing (B2C) offerings for California customers. B2B transactions treated differently under the CLRA. Government-imposed taxes/fees and reasonable shipping remain permissible as separate line items. Genuinely optional fees (e.g., expedited shipping upgrade, optional gift wrapping) are not covered.
- **Evidence Tier**: Gold (primary regulatory source; currently enforced)
- **Added**: Vera reconciled audit, 2026-04-22

---

### Finding 6: FTC Junk Fees Rule (16 CFR Part 464) — Federal Drip-Pricing Rule for Tickets and Hotels
- **Source**: Federal Trade Commission. "Trade Regulation Rule on Unfair or Deceptive Fees." 90 Fed. Reg. 2066 (Jan. 10, 2025); codified at 16 CFR Part 464. Effective May 12, 2025. Press release: https://www.ftc.gov/news-events/news/press-releases/2024/12/federal-trade-commission-announces-bipartisan-rule-banning-junk-ticket-hotel-fees — Rulemaking: https://www.ftc.gov/legal-library/browse/rules/rulemaking-unfair-or-deceptive-fees
- **Methodology**: FTC rulemaking under the FTC Act; NPRM issued November 2022, final rule December 17, 2024, effective May 12, 2025. Final rule is narrower than the NPRM — applies ONLY to live-event ticketing and short-term lodging.
- **Key Finding**: The rule requires live-event ticketing and short-term lodging businesses to clearly and conspicuously disclose the true total price inclusive of all mandatory fees at the first point of price display. Civil penalties under FTC Act § 5(m), inflation-adjusted annually in the Federal Register — verify the current maximum in the most recent Federal Register notice before citing a specific dollar figure.
- **E-Commerce Application**: If your business sells live-event tickets or short-term lodging (including Airbnb/VRBO-style platforms), full-price disclosure is now required federally. For general e-commerce, this rule does **not** apply per-se — BUT: (a) drip pricing remains actionable under FTC Act § 5 deceptive-practices standard on a case-by-case basis, and (b) California SB-478 (Finding 5) imposes a general hidden-fees prohibition for California-facing commerce. Do not treat the narrowed federal rule as clearance for drip pricing in other industries.
- **Replication Status**: Regulatory rule; confirmed effective May 12, 2025 via multiple legal industry sources (Foley & Lardner, Morgan Lewis, National Law Review, JMBM Hotel Law blog).
- **Boundary Conditions**: Federal rule scope: live-event tickets + short-term lodging only. Hotels, motels, inns, short-term/vacation rentals (including Airbnb-style platforms) are covered. General retail e-commerce is NOT covered by this specific rule.
- **Evidence Tier**: Gold (primary regulatory source)
- **Added**: Vera reconciled audit, 2026-04-22

---

### Finding 7: EU Total-Price-Inclusive Display Requirements
- **Source**: EU Price Indication Directive 98/6/EC. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:31998L0006 — Amended and strengthened by: EU Omnibus Directive 2019/2161. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019L2161 (transposition deadline November 28, 2021; applied in Member States from May 28, 2022).
- **Methodology**: EU directive framework; transposed into national law in each Member State and enforced by national consumer protection authorities.
- **Key Finding**: EU retailers must display total B2C prices including all mandatory taxes (VAT) and charges. The Omnibus Directive 2019/2161 additionally requires: (a) **30-day prior price rule** — price reductions must reference the lowest price charged in the prior 30 days, not an inflated MSRP; (b) enhanced fake-review protections; (c) additional online-marketplace transparency requirements including disclosure of ranking parameters for search results.
- **E-Commerce Application**: EU e-commerce operators must include VAT and all mandatory fees in displayed prices for B2C customers. Strikethrough pricing for sales must reference the prior lowest price in the last 30 days — this is stricter than US 16 CFR § 233.1 reference-price rules and requires different display logic for EU-facing sites. Non-EU sellers marketing to EU consumers are generally subject to these requirements.
- **Replication Status**: Regulatory directive; applied across the EU since May 2022. National enforcement varies by Member State.
- **Boundary Conditions**: Applies to B2C transactions in the EU. B2B treated differently. The 30-day prior-price rule applies specifically when announcing a price reduction (not to all pricing generally).
- **Evidence Tier**: Gold (primary regulatory sources)
- **Added**: Vera reconciled audit, 2026-04-22

---

## Methodological Notes

1. **Baymard Stat Drift**: Baymard updates their abandonment survey periodically. All ECP files citing Baymard abandonment figures must be tagged with the survey wave. The 2024 published wave shows 39% extra-costs / 14% can't-see-total; a February 2024 wave showed 48% / 17%. Directional finding (extra costs = #1 controllable driver) is stable across waves. **Harmonize with `pricing-psychology.md` Finding 36 and `free-shipping.md` Finding 2.**

2. **Regulatory Stack (2024–2025)**: Price-transparency compliance now has three layers for US operators: (a) FTC Act § 5 deceptive-practices standard (general; case-by-case enforcement); (b) 16 CFR Part 464 FTC Junk Fees Rule (narrow — live-event tickets + short-term lodging only, effective May 12, 2025); (c) California SB-478 (general e-commerce into California; total price required excluding government taxes and reasonable shipping, effective July 1, 2024). For EU-facing sellers: Directive 98/6/EC + Omnibus Directive 2019/2161.

3. **Loss Aversion Mechanism**: The reason late fee revelation is so damaging is explained by CRO Finding 8 (Kahneman & Tversky 1979 prospect theory / Tversky & Kahneman 1991). When a customer has mentally committed to a purchase at price X and then discovers the real cost is X + $8 fee, they experience the $8 as a *loss* relative to their committed reference point — not just as "the price is $8 higher." Loss aversion (~2× gain) means the $8 surprise is psychologically equivalent to a $16–18 price increase.

---

## Sources Consulted

- Baymard Institute. (2024). Cart Abandonment Rate Statistics. https://baymard.com/lists/cart-abandonment-rate
- Morwitz, V.G., Greenleaf, E.A., & Johnson, E.J. (1998). *Journal of Marketing Research*, 35(4), 453–463. <https://doi.org/10.1177/002224379803500404>
- Bertini, M., & Wathieu, L. (2008). *Marketing Science*, 27(2), 236–246. <https://doi.org/10.1287/mksc.1070.0295>
- Hossain, T., & Morgan, J. (2006). *B.E. Journal of Economic Analysis & Policy: Advances*, 6(2), Article 3. <https://doi.org/10.2202/1538-0637.1429>
- Jain, S., & Srivastava, J. (2000). *Journal of Marketing Research*, 37(3), 351–362. https://journals.sagepub.com/doi/10.1509/jmkr.37.3.351 *(canonical SAGE URL — verify before finalizing)*
- Moorthy, S., & Winter, R.A. (2006). *RAND Journal of Economics*, 37(2), 449–465. <https://doi.org/10.1111/j.1756-2171.2006.tb00029.x>
- Office of Fair Trading (UK). (2010). Advertising of Prices. OFT1291. *(URL at gov.uk returned 404 at April 2026 audit; seek via UK National Archives)*
- Federal Trade Commission. (2024). Trade Regulation Rule on Unfair or Deceptive Fees, 16 CFR Part 464. 90 Fed. Reg. 2066 (Jan. 10, 2025). https://www.ftc.gov/legal-library/browse/rules/rulemaking-unfair-or-deceptive-fees
- California Civil Code §§ 1770(a)(29), 1771.1 (SB-478, 2023). https://leginfo.legislature.ca.gov/faces/billTextClient.xhtml?bill_id=202320240SB478
- EU Price Indication Directive 98/6/EC. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:31998L0006
- EU Omnibus Directive 2019/2161. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019L2161
- Tversky, A., & Kahneman, D. (1991). *Quarterly Journal of Economics*, 106(4), 1039–1061. <https://doi.org/10.2307/2937956> [pricing-psychology.md Finding 8 — mechanism reference]
