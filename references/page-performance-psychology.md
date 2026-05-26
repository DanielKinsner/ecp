<!-- RESEARCH_DATE: 2026-03-09 -->
<!-- MERGE NOTE: Findings 17+ merged from SEO (core-web-vitals.md) and Product Media (media-performance-optimization.md) domain refs (April 2, 2026). Original findings 1-16 unchanged. Only performance PSYCHOLOGY findings (user perception of speed, abandonment thresholds, business impact of latency) were merged; purely technical implementation details (image compression algorithms, CDN config) remain in their source files. -->
# Page Performance Psychology: Perceived Speed, Loading Patterns, and Conversion

**Research Date:** 2026-03-09
**Domain:** E-commerce page performance and its psychological impact on users
**Total Findings:** 22 cited findings with specific data points

## Executive Summary

Page performance psychology reveals that **perceived speed often matters more than actual speed** for conversion outcomes. The evidence supports several actionable conclusions

1. **Every 0.1s counts financially.** The Deloitte/Google study across 37 brands found a 0.1-second improvement yields 8-10% conversion lifts in retail and travel.
2. **Skeleton screens are not a silver bullet.** Research is contradictory -- Bill Chung (2020) found marginal benefits over spinners, while Viget (2017) found skeletons *increased* perceived wait time. Implementation quality matters more than the pattern itself.
3. **Core Web Vitals directly predict revenue.** Rakuten 24 saw 53% revenue-per-visitor increase and 33% conversion increase from CWV improvements. LCP is the strongest single predictor.
4. **The 3-second rule is real but aging.** Google's original 53% mobile abandonment stat is from 2016-era data. The threshold is likely lower now as expectations have risen.
5. **Optimistic UI is underused and high-impact.** Showing success before server confirmation (Instagram's approach) eliminates perceived latency for interactions entirely.
6. **Above-the-fold text should render first.** Text renders faster than images and satisfies LCP; hero images and CTAs should follow immediately, with below-fold content lazy-loaded.
7. **Speed is a trust signal.** 70% of consumers say page speed impacts willingness to buy. Slow sites are unconsciously associated with unreliable businesses.
8. **Animation quality matters more than skeleton-vs-spinner choice.** Wang et al. (2025, N=1,409) found dynamic animation significantly reduces perceived wait time vs static. The debate over skeletons vs spinners misses the point — how you animate matters more than what you animate. (See Finding 13, which refines Finding 2.)

---

## Findings

### Finding 1: The 0.1-Second Revenue Effect

- **Source**: Google/Deloitte, 2020, "Milliseconds Make Millions" https://www.deloitte.com/ie/en/services/consulting/research/milliseconds-make-millions.html
- **Methodology**: Analysis of 37 European and American brand sites, 30+ million user sessions, mobile load times monitored hourly for 30 days (late 2019).
- **Key Finding**: A 0.1-second improvement in mobile load time increased retail conversions by **8.4%** and average order value by **9.2%**. Travel conversions increased by **10.1%**. Luxury brand page views per session increased by **8.6%**.
- **E-Commerce Application**: Even micro-optimizations (eliminating one render-blocking resource, optimizing a single image) can produce measurable revenue impact. Prioritize the fastest wins.
- **Replication Status**: Strong -- based on real production data across multiple verticals and geographies. One of the most robust performance-to-revenue studies available.
- **Boundary Conditions**: Study focused on mobile. Desktop users may be less sensitive. Diminishing returns likely exist below ~1s load times.
- **Evidence Tier**: Silver

### Finding 2: Skeleton Screens -- Contradictory Evidence

- **Source**: (a) Viget, 2017, "A Bone to Pick with Skeleton Screens" https://www.viget.com/; (b) Bill Chung, 2020, UX Collective https://uxdesign.cc/
- **Methodology**: (a) Viget: 136 mobile users randomly shown spinner, skeleton, or blank screen via animated GIFs, then asked to evaluate wait time. (b) Chung: Physical mobile device testing with participants in "half-focused" state in downtown Vancouver.
- **Key Finding**: **Viget found skeletons performed worst** -- users perceived longer wait times with skeletons than with spinners or blank screens. **Chung found skeletons performed best**, but only marginally shorter perceived duration vs. spinner and blank screen.
- **E-Commerce Application**: Do not blindly adopt skeleton screens. Test them against your specific content type. Skeletons work best when they closely match the final layout (reducing layout shift). Poorly designed skeletons that don't match final content may increase perceived wait time by setting expectations that are then violated. **Note:** Finding 13 refines this finding — animation quality matters more than the skeleton-vs-spinner pattern choice. NNGroup (2023) recommends skeletons for full-page loads under 10 seconds and spinners for individual module loads under 10 seconds. The differentiator is use case (full-page vs module), not duration.
- **Replication Status**: Contradictory. No large-scale definitive study exists. Both studies had small sample sizes.
- **Boundary Conditions**: Skeleton fidelity matters enormously. A skeleton that closely mirrors final content likely outperforms a generic gray-box skeleton. Context (content-heavy pages vs. simple pages) likely moderates the effect.
- **Citation Status**: Bill Chung (2020) UX Collective URL currently returns 403 (access wall). The directional claim is supported independently by Viget 2017 (this finding) and by Wang et al. 2025 peer-reviewed N=1,409 (Finding 13), which supersedes both practitioner studies as the stronger modern primary.
- **Evidence Tier**: Bronze

### Finding 3: Progress Indicators and Willingness to Wait

- **Source**: Nielsen Norman Group, "Progress Indicators Make a Slow System Less Insufferable." https://www.nngroup.com/articles/progress-indicators/
- **Methodology**: UX research synthesis across multiple studies on progress indicator design.
- **Key Finding**: Users shown a **moving progress bar** experienced higher satisfaction and were willing to wait **3x longer** than users shown no indicator. Determinate progress bars (showing percentage) outperform indeterminate ones (spinning/pulsing) because they reduce uncertainty.
- **E-Commerce Application**: For any operation over 1 second (checkout processing, search filtering, page transitions), show a determinate progress indicator. For operations under 1 second, no indicator needed. Between 0.1-1s, a subtle animation suffices.
- **Replication Status**: Well-established. Rooted in decades of HCI research dating to Miller, R.B. (1968), "Response Time in Man-Computer Conversational Transactions," *AFIPS '68 Fall Joint Computer Conference*, <https://doi.org/10.1145/1476589.1476628> and Card, S.K., Moran, T.P. & Newell, A. (1983), *The Psychology of Human-Computer Interaction*, Lawrence Erlbaum (https://www.taylorfrancis.com/books/mono/10.1201/9780203736166/psychology-human-computer-interaction-stuart-card).
- **Boundary Conditions**: Progress bars that stall or move non-linearly can increase frustration. The bar must honestly reflect progress or use carefully designed easing curves.
- **Evidence Tier**: Gold

### Finding 4: The Three Response Time Thresholds

- **Source**: Jakob Nielsen / NNGroup, "Response Times: The 3 Important Limits." https://www.nngroup.com/articles/response-times-3-important-limits/
- **Methodology**: Literature synthesis from Miller, R.B. (1968), "Response Time in Man-Computer Conversational Transactions," *AFIPS '68*, <https://doi.org/10.1145/1476589.1476628> ; Card, Moran & Newell (1983), *The Psychology of Human-Computer Interaction* (Erlbaum); and Nielsen's own research.
- **Key Finding**: Three critical thresholds: **0.1 seconds** -- feels instantaneous, user feels they caused the result. **1 second** -- user notices delay but stays in flow, feels in control. **10 seconds** -- user loses attention entirely, may abandon.
- **E-Commerce Application**: Target 0.1s for micro-interactions (add-to-cart, filter toggles, UI state changes). Target under 1s for page transitions and search results. Never exceed 10s for any operation without a progress indicator and the option to cancel.
- **Replication Status**: Foundational HCI research, replicated extensively over 50+ years. Thresholds are rooted in human cognitive processing limits.
- **Boundary Conditions**: These are perceptual thresholds, not conversion thresholds. A page can load in 0.9s and still lose conversions if the content order is wrong.
- **Evidence Tier**: Gold

### Finding 5: Core Web Vitals and Conversion -- The Rakuten 24 Case

- **Source**: web.dev / Rakuten, 2021, "How Rakuten 24's investment in Core Web Vitals increased revenue per visitor by 53.37%" https://web.dev/case-studies/rakuten-24
- **Methodology**: A/B test on high-traffic landing page, 50/50 traffic split between optimized (version A) and original (version B). Measured CWV alongside conversion and revenue.
- **Key Finding**: Optimized version improved CLS by **92.72%**, FID by **7.95%**, FCP by **8.45%**, TTFB by **18.03%**. Business results: conversion rate up **33.13%**, revenue per visitor up **53.37%**. Separately, good LCP correlated with up to **61.13%** conversion rate increase and **26.09%** revenue per visitor increase.
- **E-Commerce Application**: CLS is the most underrated metric -- layout shifts during loading erode trust and cause misclicks. Prioritize: (1) fix CLS by reserving space for images/ads, (2) improve LCP by optimizing hero content, (3) reduce INP for interactive elements.
- **Replication Status**: Corroborated by Vodafone (8% sales increase from LCP improvement), Pinterest (15% sign-up increase), Renault (13% conversion increase).
- **Boundary Conditions**: Rakuten 24 is a Japanese market ecommerce site. Cultural differences in patience/expectations may apply. Results this dramatic suggest the baseline was quite poor.
- **Evidence Tier**: Silver

### Finding 6: The "3-Second Rule" -- Origin and Current Validity

- **Source**: Google/SOASTA, 2016-2017 https://www.thinkwithgoogle.com/; Akamai, 2010-2016 https://www.akamai.com/
- **Methodology**: Google/SOASTA analyzed mobile sessions. Akamai tracked abandonment across CDN-served sites. Earlier Akamai studies (2006, 2010) tracked evolving expectations.
- **Key Finding**: Google found **53% of mobile visits abandoned** if page took >3 seconds. Akamai's peak conversion rate of **4.75%** occurred at **3.3 seconds** load time; one additional second dropped conversion to **3.52%** (a **26% drop**). [CITATION LAUNDERED: The widely-cited Akamai '1 second = 7% conversion reduction' statistic traces to reports from 2006 and 2014 with varying methodologies. No auditable primary study exists for the specific 7% figure. The 53% Google/SOASTA figure is from 2016-era 3G network data — directionally correct but not current. Akamai primary URL (`developer.akamai.com/blog/2016/09/14/...`) returns 403 and redirects to `community.akamai.com`.] The 2010 Akamai study found **57% abandonment** at 3 seconds, up from lower thresholds in 2006.
- **E-Commerce Application**: The 3-second threshold remains a useful engineering target, but expectations are tightening. Aim for under 2 seconds on mobile. The trend shows users becoming less patient over time, not more.
- **Replication Status**: Widely cited but the original Google/SOASTA data is from 2016. The directional finding is robust, but the exact 53% figure is dated (**DATED 2016 — measured on 3G-era networks; thresholds are likely more demanding in 2025-2026**).
- **Boundary Conditions**: Varies by context. Users will wait longer for complex tasks (booking flights) than simple ones (browsing products). Wi-Fi vs. cellular also matters. Desktop thresholds are more forgiving.
- **Evidence Tier**: Silver

### Finding 7: Speed as a Trust Signal

- **Source**: Multiple: Unbounce Page Speed Report https://unbounce.com/; Queue-it ecommerce speed statistics https://queue-it.com/
- **Methodology**: Consumer surveys and behavioral analysis across ecommerce sites.
- **Key Finding**: **70% of consumers** say page speed impacts their willingness to buy from an online retailer. **78% of consumers** report negative emotions from slow/unreliable websites. Sites loading in 1 second convert **3x more** than those loading in 5 seconds, and **5x more** than those loading in 10 seconds.
- **E-Commerce Application**: Speed is not just a UX metric -- it is a brand trust signal. Customers unconsciously associate website speed with business reliability. A slow checkout page specifically undermines trust at the critical conversion moment.
- **Replication Status**: Consistent across multiple surveys and studies. The directional finding is robust.
- **Boundary Conditions**: Brand strength can buffer speed penalties. Amazon or Apple can get away with slightly more than an unknown brand. But even strong brands see measurable conversion drops from speed regressions.
- **Evidence Tier**: Bronze

### Finding 8: Optimistic UI and Perceived Instantaneity

- **Source**: Simon Hearne, 2021, "Optimistic UI Patterns for Improved Perceived Performance" https://simonhearne.com/; Smashing Magazine, 2016 https://www.smashingmagazine.com/
- **Methodology**: Analysis of optimistic UI implementations (Instagram, Facebook, Twitter) and their impact on perceived responsiveness.
- **Key Finding**: Optimistic UI eliminates perceived latency for discrete actions by showing the result immediately and rolling back only on failure. Instagram (pioneered by Mike Krieger) shows heart animation instantly while server communication happens in background. The pattern moves interactions from the 1-second threshold to the 0.1-second (instantaneous) threshold.
- **E-Commerce Application**: Apply to: add-to-cart (show item in cart immediately), wishlist/favorites, quantity changes, filter selections. Do NOT apply to: payment processing, order placement, or any action where false success has real consequences.
- **Replication Status**: Widely adopted by major platforms. No controlled A/B study with conversion data found, but the psychological mechanism (0.1s vs 1s threshold) is well-established.
- **Boundary Conditions**: Failure rate must be very low (<1%) for optimistic UI to work. If the server rejects the action frequently, the rollback experience is worse than waiting. Also inappropriate for irreversible or high-stakes actions.
- **Evidence Tier**: Bronze

### Finding 9: Above-the-Fold Content Loading Priority

- **Source**: web.dev Fetch Priority API documentation https://web.dev/articles/fetch-priority; Smashing Magazine, 2022 https://www.smashingmagazine.com/
- **Methodology**: Web performance best practices synthesis and browser rendering pipeline analysis.
- **Key Finding**: Text renders fastest and should be the LCP element when possible. Above-the-fold images should use `fetchpriority="high"` and never be lazy-loaded. In carousels, only the first visible image needs high priority. A 1-second delay in above-fold content visibility results in a **7% conversion reduction**.
- **E-Commerce Application**: Optimal loading order for a product page: (1) Product title + price text, (2) Primary product image (high priority, not lazy-loaded), (3) Add-to-cart CTA, (4) Product description, (5) Secondary images (lazy-loaded), (6) Reviews and recommendations. Never lazy-load hero or primary product images.
- **Replication Status**: Consistent with Google's LCP guidance and multiple performance case studies.
- **Boundary Conditions**: The "right" order depends on page type. Category/listing pages may prioritize grid images; checkout pages should prioritize form fields and trust badges.
- **Citation Status**: *Note: The cited "7% conversion reduction for 1-second above-fold delay" is not explicitly sourced in the Smashing Magazine or web.dev Fetch Priority docs. This figure likely traces to the same Akamai/SOASTA 2016 data referenced in Finding 6 and Finding 20 — treat as directional, not primary.*
- **Evidence Tier**: Silver

### Finding 10: Animation Duration Sweet Spot

- **Source**: NNGroup, "Executing UX Animations: Duration and Motion Characteristics" https://www.nngroup.com/
- **Methodology**: UX research synthesis on animation timing and user perception.
- **Key Finding**: Optimal UI animation duration is **200-500ms**. Below 100ms, animation is invisible. Above 1 second, it feels like a delay. Web-specific interactions should target **150-200ms**. Animations must render at **60fps** or users notice jank, which hurts perceived quality more than no animation at all.
- **E-Commerce Application**: Use 150-200ms transitions for hover states, button feedback, and micro-interactions. Use 300-500ms for page transitions, modal openings, and accordion expansions. Remove or reduce animations on low-powered devices and when `prefers-reduced-motion` is set. Never animate anything that blocks the user from their goal.
- **Replication Status**: Well-established in HCI literature.
- **Boundary Conditions**: Animation that communicates spatial relationships (e.g., where a modal came from) can justify slightly longer durations. Decorative animation should always be faster or eliminated.
- **Evidence Tier**: Gold

### Finding 11: Lazy Loading and Product Image Perception

- **Source**: Cloud Four, "Stop Lazy Loading Product and Hero Images" https://cloudfour.com/; ImageKit lazy loading guide https://imagekit.io/blog/
- **Methodology**: Performance analysis and UX assessment of lazy loading implementations across ecommerce sites.
- **Key Finding**: Lazy loading above-the-fold product images **hurts LCP** and perceived speed. Using blurred low-resolution placeholders or dominant-color placeholders creates a fluid transition that maintains perceived quality. However, low-resolution placeholder images that look pixelated can make products seem lower quality.
- **E-Commerce Application**: Never lazy-load the primary product image or hero images. For product grids below the fold, use LQIP (Low Quality Image Placeholder) with blur-up technique -- the dominant color or a tiny blurred version loads instantly, then the full image fades in. This maintains perceived quality while improving initial load.
- **Replication Status**: Consistent with Core Web Vitals guidance. The perceptual quality concern is logical but lacks controlled experimental data.
- **Boundary Conditions**: On very fast connections, lazy loading provides minimal benefit and adds complexity. The technique is most impactful on mobile/slow connections where bandwidth is constrained.
- **Evidence Tier**: Bronze

### Finding 12: Vodafone and the LCP-to-Sales Pipeline

- **Source**: web.dev, "The business impact of Core Web Vitals" https://web.dev/case-studies/vitals-business-impact
- **Methodology**: Real-world A/B testing and production metric correlation across multiple brands.
- **Key Finding**: Vodafone's **31% improvement in LCP** led to **8% more sales**, a **15% improvement** in cart-to-visit rate, and **11% more organic traffic**. This demonstrates the full chain: speed improvement -> better engagement -> higher conversion -> more revenue, compounded by SEO benefits from better CWV scores.
- **E-Commerce Application**: LCP improvements have a compounding effect -- they improve both direct conversion (users experience faster pages) and indirect acquisition (Google ranks faster pages higher, sending more traffic). Prioritize LCP as the single highest-ROI performance metric.
- **Replication Status**: Corroborated by Rakuten (Finding 5), Pinterest, and Renault case studies on web.dev.
- **Boundary Conditions**: Vodafone is a high-traffic brand; smaller sites may see proportionally different results. The SEO compounding effect depends on competitive landscape.
- **Evidence Tier**: Silver

### Finding 13: Animation Type Matters More Than Skeleton vs Spinner

- **Source**: (a) Wang et al., 2025, MDPI Journal of Theoretical and Applied Electronic Commerce Research https://www.mdpi.com/journal/jtaer; (b) Harrison, Yeo & Hudson, 2010, ACM CHI https://dl.acm.org/
- **Methodology**: (a) Wang: 4 online experiments (N=198, 411, 400, 400; total N=1,409) comparing dynamic vs static loading animations using Attentional Gate Theory. (b) Harrison: Controlled lab experiment testing ribbed, backward-decelerating progress bars at CMU.
- **Key Finding**: (a) Dynamic/animated loading indicators significantly reduced perceived wait time compared to static indicators. (b) Backward-decelerating ribbed progress bars reduced perceived duration by **~11-12%** (p<0.001). The pattern of the loading indicator (skeleton vs spinner) is less important than the quality of its animation.
- **E-Commerce Application**: Use subtle motion and shimmer on loading placeholders. Use accelerating-feel or backward-decelerating progress bars for determinate waits (checkout processing, payment). Avoid static loading indicators entirely.
- **Replication Status**: Wang 2025 is peer-reviewed with large total N=1,409. Harrison 2010 is peer-reviewed ACM CHI. Both are non-ecommerce contexts (general UI/loading tasks). No direct ecommerce conversion measurement.
- **Boundary Conditions**: Studies measured perception (perceived wait time), not purchase conversion. Wang's sample was ages 20-29 only. Ecommerce-specific replication is needed but the underlying perceptual mechanism is well-established.
- **Evidence Tier**: Bronze
- **Quality Flag**: Primary source (Wang et al.) is peer-reviewed with N=1,409; secondary source (Harrison et al.) is ACM CHI peer-reviewed. MDPI not in Gold publisher list but methodology exceeds Bronze norm.

### Finding 14: Shimmer Direction and Multi-Stage Loading Patterns

- **Source**: (a) Bill Chung, 2017, UX Collective https://uxdesign.cc/; (b) Erwin Hofman, practitioner study https://www.erwinhofman.com/; (c) Yin et al., 2025, MDPI Applied Sciences https://www.mdpi.com/journal/applsci
- **Methodology**: (a) Chung: Street-intercept testing, ~20 participants, compared wave/shimmer vs pulse vs static. (b) Hofman: Independent practitioner A/B comparison, ~20 participants. (c) Yin: Lab experiment, N=90, ages 20-29, repeated-measures ANOVA, 4-second constant wait.
- **Key Finding**: (a,b) Slow left-to-right shimmer animation was perceived as having the **shortest loading duration** compared to pulse and static alternatives. Two independent practitioner studies converge on the same direction. (c) Multi-stage loading patterns (e.g., spinner transitioning to skeleton) showed context-dependent results — some sequences outperformed single-stage, but blank+spinner often performed best.
- **E-Commerce Application**: Use slow left-to-right shimmer (the Facebook/Google pattern) for skeleton placeholders. For category/search pages with filter loading, consider multi-stage patterns (spinner for initial response, skeleton for content layout). Test multi-stage patterns rather than assuming they outperform single-stage.
- **Replication Status**: Shimmer direction confirmed by two independent practitioner studies (~20 each). Multi-stage is a single peer-reviewed study with small N. All non-ecommerce.
- **Boundary Conditions**: All sample sizes are very small (~20 for shimmer, N=90 for multi-stage). The shimmer finding is practitioner-level evidence, not peer-reviewed. Multi-stage results were context-specific — the "best" sequence varied by scenario.
- **Citation Status**: Bill Chung 2017 (UX Collective) URL returns 403 (access wall). The directional shimmer claim is supported independently by Erwin Hofman's practitioner study (separate source). Finding 13 (Wang et al. 2025, N=1,409) is the stronger modern primary for loading animation effects.
- **Evidence Tier**: Bronze

### Finding 15: Skeleton Fidelity — Match the Final Layout or Don't Use Them

- **Source**: (a) Tim Kadlec, 2020, web performance consultant https://timkadlec.com/; (b) NNGroup, 2023, "Skeleton Screens 101" https://www.nngroup.com/
- **Methodology**: (a) Kadlec: Expert practitioner analysis of skeleton screen implementations across production sites. (b) NNGroup: Expert synthesis and usability review.
- **Key Finding**: Skeleton screens convert passive waiting into active scanning — but **only when the skeleton closely matches the final layout structure**. A skeleton that doesn't match creates jarring "content shift" that actively harms perception, potentially worse than showing no skeleton at all. NNGroup independently warns against "frame-display" skeletons that don't show content structure. Both sources emphasize that **poorly matched skeletons are worse than spinners**.
- **E-Commerce Application**: Skeleton shapes must match product card dimensions, image aspect ratios, and text line heights. On product listing pages, the skeleton grid must match the final grid exactly. If you cannot match the layout, use a spinner instead. Reserve space for all dynamic elements to prevent Cumulative Layout Shift (CLS).
- **Replication Status**: Two independent expert sources (Kadlec and NNGroup) converge on the same conclusion. No peer-reviewed study on skeleton fidelity exists.
- **Boundary Conditions**: Expert guidance, not empirical conversion data. The mechanism is logical (layout shift = violated expectations) and consistent with CLS research (Finding 5), but the specific conversion impact of skeleton fidelity is unmeasured.
- **Evidence Tier**: Bronze

### Finding 16: Skeleton Screen Accessibility Requirements

- **Source**: Adrian Roselli, 2020, "More Accessible Skeletons" https://adrianroselli.com/
- **Methodology**: Accessibility expert analysis of skeleton screen implementations and screen reader behavior.
- **Key Finding**: Skeleton screen implementations without ARIA attributes create **accessibility barriers for screen reader users**. Recommended implementation: use `aria-busy="true"` on the container while loading, `role="status"` for live regions, and ensure skeleton elements are hidden from assistive technology with `aria-hidden="true"`. **Important caveat**: Roselli notes that few screen readers actually honor `aria-busy` at the time of writing — test with actual assistive technology.
- **E-Commerce Application**: When implementing skeleton screens on product grids, search results, or checkout loading states: (1) wrap the loading region in `aria-busy="true"`, (2) announce loading completion with `aria-live="polite"`, (3) hide decorative skeleton shapes from screen readers. This is implementation guidance, not a conversion optimization — but failing to do it creates legal exposure (see accessibility lawsuit trends).
- **Replication Status**: Expert guidance consistent with WCAG best practices. No empirical study on the conversion impact of accessible vs inaccessible skeleton implementations.
- **Boundary Conditions**: Screen reader support for `aria-busy` varies. Test with VoiceOver (iOS/macOS), NVDA (Windows), and TalkBack (Android) before shipping.
- **Evidence Tier**: Bronze

---

## Key Sources

1. Google/Deloitte -- "Milliseconds Make Millions" (2020)
2. Viget -- "A Bone to Pick with Skeleton Screens" (2017)
3. Bill Chung -- Skeleton screen research (2020)
4. NNGroup -- "Progress Indicators" 
5. NNGroup -- "Response Times: 3 Important Limits"
6. Rakuten 24 case study
7. Akamai -- Mobile load time and abandonment
8. Unbounce -- Page Speed Report
9. Simon Hearne -- Optimistic UI Patterns (2021)
10. web.dev -- Fetch Priority API
11. NNGroup -- Animation Duration
12. Cloud Four -- Stop Lazy Loading Product Images
13. web.dev -- Business impact of Core Web Vitals
14. Smashing Magazine -- "True Lies of Optimistic UI" (2016)
15. Wang et al. -- "Website Loading Animation and Perceived Waiting Time" (2025)
16. Harrison, Yeo & Hudson -- "Faster Progress Bars: Manipulating Perceived Duration" (2010)
17. Bill Chung -- "What you should know about skeleton screens" (2017)
18. Erwin Hofman -- "Skeleton Loading and Perceived Performance" (practitioner)
19. Yin et al. -- "Design Strategies for Mobile Click-and-Load Waiting Scenarios" (2025)
20. Tim Kadlec -- "Effective Skeleton Screens" (2020)
21. NNGroup -- "Skeleton Screens 101" (2023)
22. Adrian Roselli -- "More Accessible Skeletons" (2020)
23. HTTP Archive -- "Web Almanac 2024 — Performance" (2024)

---

### Finding 17: Controlled A/B Evidence: 31% LCP Improvement Produced 8% More Sales (Vodafone)
- **Source**: Google web.dev, "Vodafone: A 31% improvement in LCP increased sales by 8%," https://web.dev/case-studies/vodafone. Published March 2021.
- **Methodology**: Controlled A/B test: Vodafone Italy tested two versions of their site — optimized (31% better LCP) vs. control (existing performance). Traffic split 50/50 across paid media channels. Sample: ~100,000 clicks, 34,000 visits/day. Duration sufficient for statistical significance. Measured using PerformanceObserver API for LCP.
- **Key Finding**: 31% LCP improvement → 8% more online sales (+15% lead-to-visit rate, +11% cart-to-visit rate). This is a controlled A/B test — not a before/after comparison, meaning confounders are controlled. The causal chain (better LCP → more sales) is confirmed. This is the single most credible performance-to-business-outcome study available, complementing the observational data in Findings 1 and 5. Note: Finding 5 (Rakuten 24) showed a 33% conversion increase from CWV improvements; Vodafone's 8% from a single metric (LCP) is a more conservative and isolated estimate.
- **E-Commerce Application**: Use this study for stakeholder buy-in: "A controlled test at Vodafone showed 31% LCP improvement = 8% sales increase. Our LCP is currently [Xs]. Improving it to [Ys] could deliver approximately [Z]% sales uplift." The methodology (A/B test on paid media) is replicable for validating your own LCP improvements.
- **Replication Status**: Published by Google/web.dev — corroborated by Rakuten (Finding 5), Swappie, and other web.dev case studies with similar directional results. The specific 31%/8% ratio is Vodafone-specific; it provides a conservative real-world baseline.
- **Boundary Conditions**: Vodafone Italy — specific to their market, product catalog, and traffic mix. Use as directional evidence, not as a precise predictor for a different site. Results this significant suggest the baseline LCP was relatively poor before optimization.
- **Evidence Tier**: Silver (web.dev / Google Developers blog is Silver-listed in evidence-tiers.md publisher list; harmonized with core-web-vitals.md F5 which cites the same source at Silver)
- **Quality Flag**: This is an A/B controlled case study with disclosed methodology and ~100,000 clicks — it sits at the high end of Silver. The tier is Silver because web.dev is Silver-listed; the methodology justifies prioritizing this finding over typical Silver-tier case studies when building stakeholder cases.

---

### Finding 18: Every 100ms of Latency Has Measurable Business Impact (Akamai + Deloitte Convergence)
- **Source**: Akamai Technologies, "State of Online Retail Performance" (2017). Deloitte/Google, "Milliseconds Make Millions" (2020), https://www.deloitte.com/ie/en/services/consulting/research/milliseconds-make-millions.html. eBay Engineering blog on latency and "Add to Cart" interactions.
- **Methodology**: Akamai (2017): analysis of 10 billion page views across retail sites, correlating load time with conversion rate. Deloitte/Google (2020): study of 37 major brands across multiple verticals, 30M+ user sessions, measuring funnel progression with 0.1s speed improvements. eBay: internal analysis of cart interaction latency.
- **Key Finding**: Akamai (2017): 100ms delay → up to 7% conversion decrease. Deloitte/Google (2020): 0.1s improvement in mobile site speed → 8.4% higher retail conversion rate, 9.2% higher average order value (consistent with Finding 1). eBay: 100ms faster loading → 0.5% more "Add to Cart" interactions. Multiple independent sources consistently confirm that sub-second latency improvements produce measurable conversion changes. This provides a per-millisecond conversion impact estimate for business case calculations.
- **E-Commerce Application**: Performance improvements compound. A 0.5s LCP improvement on a product page with $1M annual revenue could realistically generate $42,000+ in additional revenue (using Deloitte's 8.4%/0.1s ratio). Use this math to build internal business cases for performance engineering investment. The eBay finding shows that even specific interaction latency (add-to-cart) is affected by millisecond-level improvements — this extends the principle from page load to micro-interactions.
- **Replication Status**: Akamai (2017) and Deloitte/Google (2020) are independent studies with large datasets, confirming the direction. The specific percentages vary by study and vertical — treat as directional benchmarks, not exact predictions.
- **Boundary Conditions**: The studies measure correlations between speed and conversion, not pure causal experiments. Confounders (traffic quality, device distribution, competitive landscape) affect results. The Deloitte study was Google-commissioned — independent methodology but sponsor has financial interest in demonstrating speed importance.
- **Evidence Tier**: Silver (Akamai: large-scale industry analysis, vendor-published but methodologically transparent; Deloitte: named researchers, 37 brands, 30M+ sessions)

---

### Finding 19: Speed-to-Trust Relationship — Slow Pages Are Perceived as Untrustworthy Businesses
- **Source**: Multiple: Unbounce Page Speed Report https://unbounce.com/; Queue-it ecommerce speed statistics https://queue-it.com/; Stanford Web Credibility Project (Fogg, 2002) on credibility cues https://credibility.stanford.edu/. Cross-referenced with Finding 7 in this file.
- **Methodology**: Consumer surveys and behavioral analysis across ecommerce sites. Stanford credibility research: survey of 4,500+ participants.
- **Key Finding**: 70% of consumers say page speed impacts their willingness to buy from an online retailer. 78% of consumers report negative emotions from slow/unreliable websites. Beyond conversion impact, page speed functions as a **brand trust signal**: Stanford's credibility research found users form credibility judgments within seconds based on site performance and visual quality. A slow checkout page specifically undermines trust at the critical conversion moment. Sites loading in 1 second convert 3× more than those loading in 5 seconds, and 5× more than those loading in 10 seconds (consistent with Finding 7).
- **E-Commerce Application**: Frame speed optimization internally as a brand trust investment, not just a technical metric. The speed-trust connection means performance regressions can harm brand perception beyond the immediate conversion loss — customers associate slow sites with unreliable or low-quality businesses. Checkout pages deserve the most aggressive performance treatment because that's where speed-trust anxiety peaks.
- **Replication Status**: Consistent across multiple surveys and studies. The directional finding is robust. Stanford credibility research is foundational and widely replicated.
- **Boundary Conditions**: Brand strength can buffer speed penalties. Amazon or Apple can get away with slightly more than an unknown brand. But even strong brands see measurable conversion drops from speed regressions. The speed-trust connection may be weaker for brands where other trust signals (physical presence, word of mouth) dominate.
- **Evidence Tier**: Silver (survey-based consumer data; mechanism corroborated by Stanford credibility research)

---

### Finding 20: Mobile Abandonment Threshold — The "3-Second Rule" Context and Current Validity
- **Source**: Google/SOASTA, 2016-2017 mobile session analysis. https://www.thinkwithgoogle.com/ Akamai, 2010-2016. https://www.akamai.com/ Baymard Institute cart abandonment meta-analysis. https://baymard.com/lists/cart-abandonment-rate
- **Methodology**: Google/SOASTA analyzed mobile sessions for abandonment timing. Akamai tracked abandonment across CDN-served sites. Baymard: meta-analysis of 50 published cart abandonment studies.
- **Key Finding**: Google found 53% of mobile visits abandoned if page took >3 seconds. Akamai's peak conversion rate of 4.75% occurred at 3.3 seconds load time; one additional second dropped conversion to 3.52% (a 26% drop). The 3-second threshold remains a useful engineering target, but expectations are tightening — aim for under 2 seconds on mobile. The trend shows users becoming less patient over time, not more (Akamai 2010 vs. 2016 data shows threshold shifted downward). This provides the psychological framing for why LCP targets matter: users don't consciously measure load time, they experience frustration and leave. [DATED 2016 — same Akamai/Google/SOASTA dataset as Finding 6; Akamai primary URL returns 403/redirects. Directional finding robust; specific percentages should not be cited as current benchmarks.]
- **E-Commerce Application**: Use the 3-second rule as a minimum floor target, not a pass/fail ceiling. The 53% mobile abandonment stat is from 2016-era data — current expectations are higher. Target under 2 seconds on mobile as the practical engineering goal. Frame A/B tests and optimization prioritization around "how many users are we losing to abandonment in seconds 2-4?" rather than abstract performance metrics.
- **Replication Status**: Widely cited but the original Google/SOASTA data is from 2016. The directional finding (slower = more abandonment) is robust; the exact 53% figure is dated. Consistent with Baymard's finding that 48% of cart abandonment is due to cost-related friction — speed is a parallel friction category.
- **Boundary Conditions**: Varies by context. Users will wait longer for complex tasks (booking flights) than simple ones (browsing products). Wi-Fi vs. cellular also matters. Desktop thresholds are more forgiving. User expectations vary by market — users in high-speed markets (South Korea, Japan) may be less tolerant.
- **Evidence Tier**: Silver (Dated: Google/SOASTA data from 2016; directional finding robust but specific percentages should not be cited as current)

---

### Finding 21: CLS — Cumulative Layout Shift Causes Misclicks and Erodes Trust
- **Source**: Google web.dev, "Optimize CLS," https://web.dev/articles/optimize-cls. Swappie case study: LCP -55%, CLS -91% → 42% mobile revenue increase. https://web.dev/case-studies/swappie.
- **Methodology**: Google official documentation on CLS measurement and causes. Swappie: before/after comparison (not a pure A/B test). LCP reduced 55%, CLS reduced 91%, FID reduced 90%. Time periods: pre-optimization vs. post-optimization metrics.
- **Key Finding**: CLS (Cumulative Layout Shift) — page layout reflowing as content loads — causes two distinct user experience problems: (1) **Misclicks**: user taps a button that shifts position during load, triggering unintended actions; (2) **Trust erosion**: visible page jumps during loading create a perception of an unstable, untrustworthy site. Swappie's 91% CLS reduction contributed to a 42% mobile revenue increase, suggesting CLS was a major contributor to their mobile conversion problem. CLS is the most underrated Core Web Vitals metric and the most commonly caused by fixable implementation issues (images without dimensions, dynamic content injection).
- **E-Commerce Application**: CLS is often caused by simple fixable issues: (1) images without `width` and `height` attributes — browser reserves no space until image loads; (2) dynamically-loaded variant selectors or price elements that appear after page render; (3) promotional banners injected above the fold after page load; (4) late-loading web fonts causing FOUT; (5) deferred third-party widgets (review widgets, live chat). Fix: always specify `width` and `height` on all `<img>` elements; reserve space for dynamic content with explicit CSS min-height.
- **Replication Status**: Swappie case study is a named company with disclosed metrics (not a pure A/B test, so causality is less certain than Vodafone). Direction (CLS improvement = revenue improvement) is consistent with all web.dev performance case studies.
- **Boundary Conditions**: CLS from user interactions (e.g., the user clicking to expand content) does not contribute to the CLS score — only unexpected shifts count. CLS impact is proportionally larger for mobile than desktop because mobile screens have less real estate for absorbing layout shifts.
- **Evidence Tier**: Gold (web.dev case study with named company and disclosed methodology; Google official documentation on CLS measurement)

---

### Finding 22: Current-Era CWV Pass Rates at Population Scale (Web Almanac 2024)

- **Source**: HTTP Archive, "Web Almanac 2024 — Performance" chapter, https://almanac.httparchive.org/en/2024/performance. Published 2024. WebFetch-confirmed 2026-04-22: 43% mobile / 54% desktop pass all three CWV at 75th percentile.
- **Methodology**: HTTP Archive crawls millions of websites monthly using real browsers with a Lighthouse-compatible pipeline, collecting CrUX-aligned performance data. The Web Almanac is an annual report authored and peer-reviewed by named performance engineers and researchers. Data reflects real-user measurements at the 75th percentile, matching the CWV assessment threshold.
- **Key Finding**: In 2024, **43% of origins pass all three Core Web Vitals on mobile** and **54% on desktop** at the 75th percentile. The 11-percentage-point mobile/desktop gap reflects ongoing performance inequality between high-end and low-end devices. Year-over-year improvement is documented, meaning the competitive advantage of being fast is still available — the majority of the web still fails mobile CWV. This finding provides the current-era baseline to contextualize the dated Google/SOASTA 53% mobile abandonment stat (Findings 6 and 20, 2016-era data).
- **E-Commerce Application**: Pair this with Findings 6 and 20 when building internal performance investment cases: the 2016 abandonment threshold data establishes why speed matters directionally; the Web Almanac 2024 establishes where the competitive opportunity lives today. If 43% of origins pass on mobile and your store is in that group, you're at the population median. Frame continued CWV investment as "move from median to top quartile" rather than "hit a threshold and stop." If your store is in the 57% that fail on mobile, framing is: "the majority of competitors are also failing — first-mover advantage available."
- **Replication Status**: HTTP Archive is a long-running, well-documented, Google-backed but methodologically independent project tracking real-browser performance across the web. The Web Almanac is peer-reviewed by chapter authors and updated annually, providing consistent year-over-year comparability.
- **Boundary Conditions**: Web Almanac measures the open web, not ecommerce specifically. Retail subsets may perform differently from the population mean. Consult the ecommerce-specific subsection of the performance chapter when available. The 43%/54% figures reflect the 75th-percentile CWV threshold — the same threshold Google uses for the "Good" designation in Search Console.
- **Evidence Tier**: Silver
