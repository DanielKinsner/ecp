<!-- RESEARCH_DATE: 2026-04-02 -->
<!-- RECONCILED: 2026-04-22 | Run-A (researcher-pricing) + Run-B (Opus 4.7 Pricing-B) -->
<!-- RECONCILER_NOTES: No conflicts between runs. F1/F2 VERIFIED both runs. F3 REFORMULATE both runs (A applied language fix; B incorporated same fix plus added Citation Status field). F4 NEW from Run B only — Gold JMR peer-reviewed field experiment, no objection from A (A proposed no expansion). Reconciled file = Run B proposed as base; all Run A F3 softening already present in Run B version. Both Methodological Notes 4 and 5 from Run B carried through — A had no competing notes. Header metadata updated to reflect 4 findings and reconciliation date. -->
<!-- NOTE: Key findings from this file have been merged into pricing-psychology.md. This file remains as supplementary reference with additional depth and context. -->
# Tiered Pricing: Decoy Effect, Compromise Effect, and Good-Better-Best Architecture

**Research Date**: April 2, 2026
**Last Audited**: April 21, 2026 (Run A + Run B)
**Reconciled**: April 22, 2026
**Total Findings**: 4 (new/extending); 2 partially covered by pricing-psychology.md
**Domain**: Tiered pricing, decoy effect, compromise effect, Good-Better-Best, pricing page design
**Methodology**: Web-based literature review; peer-reviewed journals; practitioner research

---

## ⚠️ OVERLAP NOTICE

The following findings are **partially covered** by `pricing-psychology.md` in ECP:

| Covered Topic | CRO Finding | What's Already There |
|---|---|---|
| Decoy effect replication challenges (11/91 reliable replications) | **Finding 5** | Meta-review; robust only in specific conditions; Bronze |
| Ariely's Economist decoy experiment (16%→84% shift) | **Finding 6** | Classroom demonstration; Bronze; not peer-reviewed |

**CRO Findings 5 and 6 cover the decoy effect with appropriate skepticism. This file adds the original foundational peer-reviewed decoy research (Huber et al. 1982), the compromise effect (Simonson 1989) which is a distinct and more reliable mechanism, the Good-Better-Best architecture framework (Mohammed 2018), and price-presentation order effects (Suk et al. 2012) — none of which are substantively covered in the CRO file.**

---

## Summary

### Top 3 Most Impactful New Findings

1. **Finding 2 (Simonson 1989 — Compromise Effect)**: The compromise effect — consumers prefer the middle option when uncertain — is more robust and reliable in real commerce than the decoy effect. Designing your target tier as the "reasonable middle" is more consistently effective than constructing a dominated decoy.
2. **Finding 1 (Huber, Payne & Puto 1982)**: The original peer-reviewed decoy effect paper establishing the foundational conditions under which asymmetric dominance reliably shifts preferences — providing the ground truth that allows practitioners to assess when decoy pricing will and won't work.
3. **Finding 4 (Suk, Lee & Lichtenstein 2012)**: Peer-reviewed field experiment showing price-presentation ORDER affects choice — descending price order (most expensive first) increases total sales vs. ascending order. Gold-tier support for ordering best practices.

---

## Findings

### Finding 1: Asymmetric Dominance (Decoy Effect) — Original Evidence and Conditions
- **Source**: Huber, J., Payne, J.W., & Puto, C. (1982). "Adding Asymmetrically Dominated Alternatives: Violations of Regularity and the Similarity Hypothesis." *Journal of Consumer Research*, 9(1), 90–98. <https://doi.org/10.1086/208899>
- **Methodology**: Multiple experiments at Duke University. Participants chose between sets of consumer products (beer, cars, restaurants, lotteries). In each case, a third "decoy" option was added that was dominated by one target option on at least one attribute but not clearly dominated by the other option. Choice shares were measured across conditions with and without the decoy. N = approximately 153 participants across experiments. Products were hypothetical choices but based on realistic attribute levels.
- **Key Finding**: Adding an asymmetrically dominated decoy — a third option that is clearly worse than the target on all relevant dimensions but not clearly worse than the competitor — reliably increased choice share for the target option (the one that dominates the decoy). Effect sizes ranged from 13% to 22% absolute choice share shift toward the target option across product categories. This violates the regularity condition of standard rational choice theory (adding a new option should never increase the relative share of an existing option). The effect was present across all tested product categories.
- **E-Commerce Application**: The decoy must be *asymmetrically* dominated — clearly worse than the target but not obviously dominated by all options. The classic SaaS application: if you want customers to choose the "Pro" ($99/mo, 15 users) tier over the "Basic" ($29/mo, 5 users), add a "Pro Lite" decoy ($89/mo, 10 users) that is clearly worse than Pro on price efficiency but makes Pro's value obvious by comparison. The decoy should not be the easiest or most intuitive choice — it exists only to make the target look better. However, see CRO Finding 5 for the replication context: this effect is real but requires precise conditions.
- **Replication Status**: The original paper has 1,500+ citations and has been replicated across dozens of studies — in lab settings. CRO Finding 5 provides the critical context: of 91 replication attempts reviewed by Frederick et al. (2014), only 11 were reliable. The effect is condition-dependent: it requires simple, comparable options (2–3 dimensions, no more); clearly dominated decoy; small choice sets. In complex real-world purchase decisions, the effect is unreliable.
- **Boundary Conditions**: See CRO Finding 5 for full boundary conditions. Key practical limits: (1) Choice set complexity — adding the decoy to a 6-tier pricing page eliminates the effect; (2) The decoy must be plausible — an obviously fake "straw man" tier is ignored; (3) High-involvement decisions where consumers deliberate carefully show smaller effects; (4) Real e-commerce data shows smaller effects than lab data due to noise, prior preferences, and external information sources.
- **Evidence Tier**: Gold (peer-reviewed JCR, foundational paper; but effect reliability in field settings is Silver — see CRO Finding 5)
- **Quality Note**: This is the foundational academic paper (Gold). CRO Finding 5 documents the replication crisis context. Both must be read together for accurate application.

---

### Finding 2: Compromise Effect — The Reliable Middle-Choice Mechanism
- **Source**: Simonson, I. (1989). "Choice Based on Reasons: The Case of Attraction and Compromise Effects." *Journal of Consumer Research*, 16(2), 158–174. <https://doi.org/10.1086/209205> — Extended by: Simonson, I., & Tversky, A. (1992). "Choice in Context: Tradeoff Contrast and Extremeness Aversion." *Journal of Marketing Research*, 29(3), 281–295. <https://doi.org/10.1177/002224379202900301>
- **Methodology**: Simonson (1989): Multiple lab experiments (N = 80–180 per study). Participants chose among product sets where a middle option was added or removed, or where the same product appeared as the middle of one set and an extreme of another. Tested cameras, microwave ovens, and other consumer durables. Simonson & Tversky (1992): Extended framework with field data from supermarket choices and lab studies, testing tradeoff contrast and extremeness aversion as separate mechanisms.
- **Key Finding**: When consumers face uncertainty about the best choice, they systematically favor compromise options — those in the middle of the range on price and attributes. This is driven by **extremeness aversion**: the psychological cost of choosing the cheapest option (fear of low quality) and the most expensive (fear of overpaying) both push consumers toward the middle. The effect is more robust and reliable than the decoy effect: it does not require an asymmetrically dominated option — any three-option set where one option is the middle generates preference for that middle. Simonson (1989) shows middle option selection rates of 45–55% vs. chance expectation of 33%.
- **E-Commerce Application**: The compromise effect is the primary reason three-tier pricing works in practice — more so than the decoy effect. For pricing pages: (1) Make your target tier the middle tier in *both* price and features; (2) Use the lowest tier to make the target look like a meaningful upgrade; (3) Use the highest tier to make the target look like reasonable value; (4) The "Most Popular" badge on the middle tier reinforces the compromise effect by providing social proof that the middle choice is indeed the modal choice. For SaaS: if your highest-margin tier is "Pro" at $79/mo, add a genuine "Enterprise" at $199/mo to make Pro feel like the sensible middle ground.
- **Replication Status**: Extensively replicated. Simonson (1989) has 1,900+ citations; Simonson & Tversky (1992) has 2,100+. The compromise effect replicates more consistently than the decoy effect — it was confirmed in cross-cultural studies (Simonson & Tversky tested US and Israeli samples), in supermarket field data, and in online choice experiments. More robust in the presence of consideration complexity than the decoy effect.
- **Boundary Conditions**: The compromise effect requires genuine uncertainty — expert consumers who have a strong prior preference are less susceptible. Effect is weaker when consumers have strong brand loyalty to a specific tier. In contexts where objective performance metrics are easy to compare (e.g., technical specs), consumers may not rely on compromise heuristics. The effect assumes a single quality dimension tradeoff — if different tiers serve genuinely different use cases, compromise logic doesn't apply (customers should choose the right tier, not the middle tier).
- **Evidence Tier**: Gold (peer-reviewed JCR + JMR, multiple studies, cross-cultural replication, field data)

---

### Finding 3: Good-Better-Best Architecture — Strategic Revenue Capture
- **Source**: Mohammed, R. (2018). "The Good-Better-Best Approach to Pricing." *Harvard Business Review*, September–October 2018. https://hbr.org/2018/09/the-good-better-best-approach-to-pricing — Supplemented by economic modeling literature: Mussa, M., & Rosen, S. (1978). "Monopoly and Product Quality." *Journal of Economic Theory*, 18(2), 301–317. <https://doi.org/10.1016/0022-0531(78)90085-6>
- **Methodology**: Mohammed (2018): HBR practitioner article synthesizing case studies from companies that implemented Good-Better-Best (GBB) pricing, with revenue outcome data. Companies analyzed include consumer goods, services, and SaaS firms. Case studies are proprietary/confidential but revenue lift range (25–40%) is derived from the aggregate of these implementations. Mussa & Rosen (1978): Foundational economic theory paper on second-degree price discrimination / vertical product differentiation — the theoretical basis for why tiered quality-price menus maximize revenue under heterogeneous willingness-to-pay.
- **Key Finding**: Mohammed (2018) **reports** that companies implementing Good-Better-Best tiered structures achieve revenue increases **in the 25–40% range** compared to single-price or two-price models. **Caveat**: this range is aggregated from practitioner case studies without full disclosure of methodology, sample selection, or counterfactual rigor; it should be treated as directional, not as a precise effect estimate. The strategic logic (which IS well-founded): single pricing captures only customers whose WTP exactly matches the price point; three tiers capture three bands of WTP. The "Good" tier prevents customer defection to competitors; the "Better" tier is the primary profit driver; the "Best" tier captures high-WTP customers who would have been under-charged at the "Better" price. Mussa & Rosen (1978): The economic proof that offering a menu of quality tiers with appropriate prices is always at least as profitable as offering a single quality level, given heterogeneous willingness-to-pay distributions.
- **E-Commerce Application**: Structure product offerings as explicit tiers (individual item, multi-pack, subscription; OR standard, plus, pro). Name tiers to communicate strategic purpose: "Good" should not be called "Basic" or "Starter" in a way that creates stigma; the "Better" tier is the anchor and should be named to signal the target customer ("Professional," "Plus," "Complete"). Price gaps between tiers: the "Good → Better" gap should feel like a meaningful upgrade for a reasonable incremental cost; the "Better → Best" gap can be larger to justify the premium segment. Do not set "Good" price so low it cannibalizes "Better" — the "Good" tier exists to prevent competitor defection, not to serve as the primary revenue driver.
- **Replication Status**: Mohammed's HBR framework has been widely adopted in SaaS, DTC, and enterprise software pricing. The revenue lift range (25–40%) comes from practitioner case studies synthesized by Mohammed (2018) without peer review. Mussa & Rosen's economic theory is foundational (500+ citations in economics). The conceptual case for tiered pricing is well-established; the specific revenue lift numbers are practitioner-grade estimates.
- **Boundary Conditions**: GBB architecture fails when: tiers are not genuinely differentiated (customers see through artificial feature gates); "Good" is too generous and cannibalizes "Better"; "Best" is priced so high it doesn't serve as a credible anchor (>4× the "Better" price typically fails as an anchor); product complexity prevents clear tier comparison (customers can't assess value differences). Category-specific: works best for subscription/recurring products; less effective for one-time purchase commodities with no natural tier structure.
- **Citation Status**: The Mohammed HBR article is behind a paywall; only the intro paragraph is publicly accessible. The specific 25–40% revenue lift range is widely repeated in practitioner/CRO literature attributing it to this article but could not be content-matched against the accessible portion at audit time. Treat the range as a practitioner synthesis figure, not a peer-validated number.
- **Evidence Tier**: Silver (Mohammed 2018: HBR practitioner research, case studies without full peer review; Mussa & Rosen 1978: Gold for theoretical foundation)

---

### Finding 4: Price-Presentation Order — Descending Price Increases Sales
- **Source**: Suk, K., Lee, J., & Lichtenstein, D.R. (2012). "The Influence of Price Presentation Order on Consumer Choice." *Journal of Marketing Research*, 49(5), 708–717. <https://doi.org/10.1509/jmr.11.0258>
- **Methodology**: Combined field experiment at a beer retailer with controlled laboratory studies. In the field study, beers were listed on menu in ascending order of price in one condition and descending order in another condition. Actual purchase data measured. Laboratory studies replicated with controlled product sets and tested anchoring mechanisms.
- **Key Finding**: Descending price order (highest price listed first) produced higher average transaction value than ascending price order. The mechanism: price-order-induced anchoring — the first price encountered serves as the reference anchor for subsequent options. When the highest price is first, middle and lower options appear reasonably priced. When the lowest price is first, middle and higher options appear expensive. This is the anchoring mechanism (Tversky & Kahneman 1974) applied specifically to price presentation sequence.
- **E-Commerce Application**: For pricing pages with 3 tiers, list them **most expensive → middle → cheapest** (i.e., highest-price tier on the left or top). This ordering (a) anchors on the highest price, making the middle tier feel like a compromise value; (b) pairs with the compromise effect (Finding 2) — when the middle tier is "the sensible middle" *AND* priced relative to a high anchor, selection rate on the middle tier increases. Counter-convention warning: many SaaS pricing pages show cheapest tier first (leftmost) based on reading-order intuition — this is a testable variable and the Suk et al. 2012 evidence supports reversing it. Caveat: reading order varies across cultures and platforms; always A/B test when changing established pricing page layouts.
- **Replication Status**: Single peer-reviewed paper with field + lab studies. Consistent with broader anchoring literature (Tversky & Kahneman 1974; Ariely, Loewenstein & Prelec 2003). Not yet replicated in SaaS subscription contexts specifically — most follow-up work has been in FMCG and consumer goods.
- **Boundary Conditions**: Effect is strongest when: (a) consumers are browsing without strong prior price reference; (b) product category has meaningful variation (not commodity); (c) presentation is genuinely sequential (not all-at-once grid). Effect weakens when: buyers know the market price range independently; layout is truly simultaneous (eye fixation patterns override presentation order); product complexity forces attribute-by-attribute comparison before price evaluation.
- **Evidence Tier**: Gold (peer-reviewed JMR; field experiment in real retail context + lab confirmation)
- **Added**: Run B audit, 2026-04-21

---

## Methodological Notes

1. **Decoy vs. Compromise in Practice**: The most practically important finding in this file is the reliability differential between the decoy effect (unreliable, condition-dependent) and the compromise effect (robust, widely replicable). Most practitioners trying to implement "decoy pricing" actually succeed through the compromise effect mechanism, not the decoy mechanism. You don't need a dominated "decoy" if you just have a well-designed three-tier structure where the middle option is clearly the value optimum.

2. **CRO Finding 5/6 Integration**: CRO Finding 6 (Ariely's Economist example, Bronze) is a classic illustration but not field evidence. The practical recommendation: in SaaS/subscription pricing page design, use the compromise effect as the primary mechanism (well-designed three tiers, target tier highlighted as "Most Popular") and only add a decoy tier if A/B testing confirms an uplift in your specific context. Don't assume the decoy effect will work; assume the compromise effect will work.

3. **Naming Matters**: Scaffolded material correctly notes tier naming as important. The Mohammed (2018) framework adds specificity: avoid names that stigmatize the entry tier ("Lite," "Basic," "Limited") because consumers then avoid the "Basic" tier even when it's appropriate for their needs, which is commercially suboptimal. "Essentials," "Standard," or "Starter" perform better than "Basic" or "Free" for paid entry tiers.

4. **Compound Stack**: Findings 2 (compromise) and 4 (descending-price order) compound — a middle tier that is BOTH structurally the compromise AND priced relative to a high-first anchor benefits from two independent mechanisms. Practitioners who implement only one mechanism are leaving lift on the table.

5. **HBR 25–40% Hedge**: Mohammed's 25–40% figure is an aggregated practitioner claim, not a peer-reviewed effect estimate. Use as directional evidence of GBB upside potential; do not forecast specific revenue lifts off this range for business cases.

---

## Sources Consulted

- Huber, J., Payne, J.W., & Puto, C. (1982). *Journal of Consumer Research*, 9(1), 90–98. <https://doi.org/10.1086/208899>
- Simonson, I. (1989). *Journal of Consumer Research*, 16(2), 158–174. <https://doi.org/10.1086/209205>
- Simonson, I., & Tversky, A. (1992). *Journal of Marketing Research*, 29(3), 281–295. <https://doi.org/10.1177/002224379202900301>
- Mohammed, R. (2018). *Harvard Business Review*, September–October 2018. https://hbr.org/2018/09/the-good-better-best-approach-to-pricing
- Mussa, M., & Rosen, S. (1978). *Journal of Economic Theory*, 18(2), 301–317. <https://doi.org/10.1016/0022-0531(78)90085-6>
- Suk, K., Lee, J., & Lichtenstein, D.R. (2012). *Journal of Marketing Research*, 49(5), 708–717. <https://doi.org/10.1509/jmr.11.0258>
- Frederick, S., Lee, L., & Baskin, E. (2014). [Decoy replication review — see pricing-psychology.md Finding 5]
- Ariely, D. (2008). *Predictably Irrational*. [pricing-psychology.md Finding 6]
