<!-- RESEARCH_DATE: 2026-04-02 -->
<!-- NOTE: Key findings from this file have been merged into page-performance-psychology.md (performance psychology findings). This file remains as supplementary reference with additional depth on SEO/ranking aspects of Core Web Vitals, INP technical optimization, Speculation Rules API, CrUX field data methodology, and third-party script auditing. -->
# Core Web Vitals for Ecommerce

**Research Date:** 2026-04-02
**Total Findings:** 13
**Methodology:** Synthesis of Google CWV documentation and official thresholds, web.dev case studies (Vodafone, Swappie, Ray-Ban — all independently published on Google's developer platform), Deloitte/Google mobile speed study ("Milliseconds Make Millions"), Akamai performance research, SpeedCurve third-party script analysis, and Google Chrome User Experience Report (CrUX) data. Evidence weighted by methodology rigor and independence.

> **Cross-Reference:** See CRO reference `page-performance-psychology.md` for the conversion psychology of page speed — this file focuses on the SEO/ranking angle. See `media-performance-optimization.md` for image/video delivery technical implementation. The business cases in both are complementary — CWV improves both rankings AND conversion rates simultaneously.
>
> **Specific finding overlaps with `page-performance-psychology.md`** — do not cite both for the same recommendation:
> - Finding 4 (Deloitte 0.1s latency) overlaps with `page-performance-psychology.md` Finding 18
> - Finding 5 (Vodafone 31% LCP → 8% sales) overlaps with `page-performance-psychology.md` Finding 17
> - Finding 10 (Swappie CLS/LCP → 42% mobile revenue) overlaps with `page-performance-psychology.md` Finding 21

---

## Summary

### Top 3 Most Impactful Findings

1. **Vodafone: 31% LCP improvement → 8% more online sales** (Finding 5) — A/B tested with 100K+ clicks on paid media channels. This is the single strongest performance-to-revenue correlation in publicly available controlled data. Use it to justify CWV investment to stakeholders.

2. **Never lazy-load the hero product image** (Finding 6) — Martin Splitt (Google): lazy-loading the hero image is "almost guaranteed to have an impact on your LCP." The LCP element on most PDPs is the hero product image. One `loading="eager"` and `fetchpriority="high"` attribute change can significantly improve LCP.

3. **Third-party scripts average +34ms per script — one site went from 1s to 26.82s LCP with all third parties** (Finding 8) — SpeedCurve testing showed catastrophic third-party script impact. Ruthless script auditing is required. Each script that doesn't contribute to revenue should be removed.

---

## Coverage by Research Question

| Research Question | Findings | Evidence Quality |
|---|---|---|
| What are the CWV thresholds? | 1 | Gold |
| What is INP and why did FID matter more? | 2 | Gold |
| Is CWV a ranking factor? | 3 | Gold |
| Does page speed affect conversion? | 4 | Gold |
| What is the strongest business case for CWV? | 5 | Gold |
| What causes LCP failures on product pages? | 6, 7 | Gold |
| How much do third-party scripts cost? | 8 | Gold |
| Does Google use lab or field data for ranking? | 9 | Gold |
| What is the best CWV-to-revenue case study? | 10 | Gold |
| How to implement Speculation Rules API? | 11 | Gold |
| What causes CLS on ecommerce pages? | 12 | Gold |
| What is the CWV priority order for ecommerce? | 13 | Gold |
| Does poor INP correlate with ranking drops? | — | DEFERRED (no verifiable primary source; see removed F14 comment) |

---

## Findings

### Finding 1: Core Web Vitals Thresholds — LCP, INP, CLS
- **Source**: Google Search Central, "Core Web Vitals," https://developers.google.com/search/docs/appearance/core-web-vitals. Google's official CWV threshold documentation (updated March 2024 when INP replaced FID).
- **Methodology**: Google official specification — defines the three CWV metrics and their threshold values.
- **Key Finding**: All three metrics are measured at the 75th percentile of page loads using Chrome User Experience Report (CrUX) field data:
  - **LCP (Largest Contentful Paint)**: Good ≤2.5s | Needs Improvement 2.5–4.0s | Poor >4.0s
  - **INP (Interaction to Next Paint)**: Good ≤200ms | Needs Improvement 200–500ms | Poor >500ms
  - **CLS (Cumulative Layout Shift)**: Good ≤0.1 | Needs Improvement 0.1–0.25 | Poor >0.25
  All three metrics must be "Good" to achieve the Page Experience ranking benefit. Failing on any one metric means no Page Experience bonus.
- **E-Commerce Application**: Prioritize the metric where you're in "Needs Improvement" or "Poor" territory. For most ecommerce PDPs: LCP is the most commonly failing (hero product image). INP is the second most challenging (variant selectors, add-to-cart interactions). CLS is most often caused by image dimension omission or dynamic content injection.
- **Replication Status**: Google official specification — definitive thresholds.
- **Boundary Conditions**: These are the 75th-percentile thresholds — 25% of your page loads can exceed "Good" while still scoring "Good" overall. The 75th percentile uses real user data from Chrome browsers (excluding Chrome iOS, which doesn't contribute to CrUX).
- **Evidence Tier**: Gold — Google Search Central official documentation.

---

### Finding 2: INP Replaced FID in March 2024 — More Demanding Interactivity Metric
- **Source**: Google Search Central, "Interaction to Next Paint (INP)," https://developers.google.com/search/docs/appearance/core-web-vitals#inp. Google announcement: "INP becomes a Core Web Vital" (March 12, 2024). web.dev INP documentation: https://web.dev/articles/inp.
- **Methodology**: Google official announcement and specification.
- **Key Finding**: INP (Interaction to Next Paint) replaced FID (First Input Delay) as the responsiveness CWV on March 12, 2024 (see web.dev/blog/inp-cwv-launch). Key difference: FID measured only the first interaction on a page; INP measures the worst (or close to worst) interaction across the entire user session. Implication: loading-time tricks that reduced FID (deferring work until after first interaction) don't help INP. INP is a harder, more demanding target than FID was — affecting more pages, especially on mobile.
- **Citation Status**: The specific "35.5% worse than FID" figure and "median ecommerce INP ~280ms" were not found in the linked Google documentation during 2026-04-21 audit. These figures have been removed. The authoritative launch announcement is web.dev/blog/inp-cwv-launch (2024-03-12).
- **E-Commerce Application**: Focus INP optimization on high-frequency interactions: variant selector (color/size selection), add-to-cart button, image gallery navigation, filter/sort controls on collection pages. These are the interactions users perform most — and they're now measured and ranked against. Optimization approach: yield to main thread between tasks (`requestAnimationFrame`, `setTimeout(0)`), use `isInputPending()` to prioritize input events, minimize main thread work during interactions.
- **Replication Status**: Google official announcement — applies universally from March 12, 2024.
- **Boundary Conditions**: INP measures the 98th percentile interaction latency — nearly the worst interaction during the session. Even one slow interaction on a page can cause a failing INP score. Long JavaScript tasks blocking the main thread are the primary cause.
- **Evidence Tier**: Gold — Google Search Central official documentation.

---

### Finding 3: CWV Is a Confirmed Ranking Signal — Described as a "Tiebreaker"
- **Source**: Google Search Central, "Page experience ranking," https://developers.google.com/search/docs/appearance/page-experience. Google official announcement of Page Experience update (2021). John Mueller multiple statements on CWV as tiebreaker.
- **Methodology**: Google official announcement + spokesperson statements.
- **Key Finding**: CWV are confirmed ranking signals within the Page Experience system (since August 2021). Google's current language: "Core Web Vitals are used by our ranking systems" — content relevance and quality dominate ranking, but CWV influences outcomes between similarly-relevant pages. Critical implication: excellent CWV does not rescue poor content; poor CWV does not tank excellent content. CWV optimization earns the Page Experience benefit most meaningfully in competitive keyword landscapes.
- **Citation Status**: The terms "tiebreaker" and "10–15% weight" have been removed. "Tiebreaker" was Google's informal historical characterization but is no longer in their current page-experience documentation as of 2026-04-21 audit. The 10–15% weight figure is an analyst estimate with no primary source — Google does not publish signal weights.
- **E-Commerce Application**: CWV optimization should be a continuous practice, not a one-time fix. Prioritize: (1) get all three metrics to "Good" as baseline; (2) then optimize further for conversion benefit (which is separate from the ranking benefit). The ranking benefit is real but not transformational — the bigger justification is the direct conversion impact (Finding 4, 5).
- **Replication Status**: Google official confirmation — the ranking signal status is definitive. The tiebreaker characterization is from multiple Mueller statements, consistent.
- **Boundary Conditions**: The Page Experience ranking signal specifically requires HTTPS, no intrusive interstitials, and mobile-friendliness in addition to CWV. All components must be met. The ranking benefit is measured at the URL level using CrUX data — pages must have sufficient real user traffic to have CrUX data (low-traffic pages may be evaluated with origin-level data instead).
- **Evidence Tier**: Gold — Google Search Central official documentation + Google spokesperson statements.

---

### Finding 4: Every 100ms of Latency Has Measurable Business Impact
- **Source**: Akamai Technologies, "State of Online Retail Performance" (2017, https://www.akamai.com/resources/reference-architecture/state-of-online-retail-performance). Deloitte/Google, "Milliseconds Make Millions" (2020), https://www.deloitte.com/ie/en/services/consulting/research/milliseconds-make-millions.html. eBay Engineering blog on latency and "Add to Cart" interactions.
- **Methodology**: Akamai (2017): analysis of 10 billion page views across retail sites, correlating load time with conversion rate. Deloitte/Google (2020): study of 37 major brands across multiple verticals, 30M+ user sessions, measuring funnel progression with 0.1s speed improvements — commissioned by Google, conducted by Deloitte. eBay: internal analysis of cart interaction latency.
- **Key Finding**: Akamai (2017): 100ms delay → up to 7% conversion decrease. Deloitte/Google (2020): 0.1s improvement in mobile site speed → 8.4% higher retail conversion rate, 9.2% higher average order value. eBay: 100ms faster loading → 0.5% more "Add to Cart" interactions. Multiple independent sources consistently confirm that sub-second latency improvements produce measurable conversion changes.
- **E-Commerce Application**: Performance improvements compound. A 0.5s LCP improvement on a product page with $1M annual revenue could realistically generate $42,000+ in additional revenue (using Deloitte's 8.4%/0.1s ratio). Use this math to build internal business cases for performance engineering investment.
- **Replication Status**: Akamai (2017) and Deloitte/Google (2020) are independent studies with large datasets. Both show consistent directional results. The specific percentages vary by study and vertical — treat as directional benchmarks, not exact predictions.
- **Boundary Conditions**: The studies measure correlations between speed and conversion, not pure causal experiments. Confounders (traffic quality, device distribution, competitive landscape) affect results. The Deloitte study was Google-commissioned — Google has financial interest in demonstrating speed importance, but Deloitte's methodology is independent.
- **Evidence Tier**: Silver — Akamai is a CDN vendor (large-scale industry analysis, methodologically transparent but vendor-published); Silver — Deloitte/Google "Milliseconds Make Millions" (named researchers, 37 brands, 30M+ sessions, published methodology). Deloitte is Silver per publisher list.

---

### Finding 5: Vodafone — 31% LCP Improvement Produced 8% More Sales
- **Source**: Google web.dev, "Vodafone: A 31% improvement in LCP increased sales by 8%," https://web.dev/case-studies/vodafone. Published March 2021. A/B test methodology.
- **Methodology**: Controlled A/B test: Vodafone Italy tested two versions of their site — optimized (31% better LCP) vs. control (existing performance). Traffic split 50/50 across paid media channels. Measured using PerformanceObserver API for LCP. Sample: ~100,000 clicks, 34,000 visits/day. Duration sufficient for statistical significance.
- **Key Finding**: 31% LCP improvement → 8% more online sales (+15% lead-to-visit rate, +11% cart-to-visit rate). This is a controlled A/B test — not a before/after comparison, meaning confounders (seasonality, external factors) are controlled. The causal chain (better LCP → more sales) is confirmed.
- **E-Commerce Application**: This is the single most credible performance-to-business-outcome case study available. Use it for stakeholder buy-in: "A controlled test at Vodafone showed 31% LCP improvement = 8% sales increase. Our LCP is currently [Xs]. Improving it to [Ys] could deliver [Z]% sales uplift." The methodology (A/B test on paid media) is replicable.
- **Replication Status**: Published by Google/web.dev — the Vodafone case study is one of many web.dev performance case studies with similar directional results. The specific 31%/8% ratio is Vodafone-specific but directionally consistent with other case studies.
- **Boundary Conditions**: Vodafone Italy — specific to their market, product catalog, and traffic mix. The specific percentage shouldn't be applied as a universal conversion formula. Use as directional evidence, not as a precise predictor for a different site.
- **Evidence Tier**: Silver (web.dev case studies are published on Google Developers blog, which is Silver-listed; quality flag: A/B tested with 100K+ clicks)

---

### Finding 6: Never Lazy-Load the LCP Hero Image
- **Source**: Martin Splitt (Google DevRel), multiple recorded talks and interviews (2022–2024): "Lazy-loading the hero image is almost guaranteed going to have an impact on your LCP." Google web.dev, "Optimize LCP," https://web.dev/articles/optimize-lcp. Chrome DevTools performance analysis documentation.
- **Methodology**: Google developer advocate statement + Google's own LCP optimization guidance. The mechanism is documented: lazy-loading delays image fetch until the element enters the viewport — but if the element IS the first viewport content, it delays LCP itself.
- **Key Finding**: The hero product image is the LCP element on most PDPs. Adding `loading="lazy"` to the hero image defers its fetch, causing LCP to be measured as the image load completes after a deliberate delay. Google's official guidance: hero/LCP image should use `loading="eager"` (or omit the loading attribute entirely) + `fetchpriority="high"`. Below-fold gallery images: `loading="lazy"`. Thumbnail images: `loading="lazy"` + `fetchpriority="low"`.
- **E-Commerce Application**: Implementation:
```html
<!-- LCP/hero image — fetchpriority="high"; do NOT add loading="lazy" -->
<picture>
  <source srcset="hero.avif" type="image/avif">
  <source srcset="hero.webp" type="image/webp">
  <img src="hero.jpg" 
       alt="2024 GR Supra Carbon Fiber Hood, gloss finish"
       fetchpriority="high"
       width="800" height="800">
</picture>

<!-- Gallery thumbnails — lazy load -->
<img src="thumb-2.jpg" loading="lazy" fetchpriority="low" width="200" height="200">
```
- **Replication Status**: Martin Splitt's statement is consistent with Google's documented LCP measurement behavior. Widely confirmed by performance engineers. The fix is simple and unambiguous.
- **Boundary Conditions**: If your LCP element is NOT the hero image (e.g., a large heading or a video thumbnail), this rule applies to that element instead. Identify your actual LCP element using Chrome DevTools → Performance → Core Web Vitals.
- **Evidence Tier**: Gold — Google Developer Advocate statement; documented in Google's official LCP optimization guide.

---

### Finding 7: Image Format Priority — AVIF → WebP → JPEG
- **Source**: Can I Use browser support data (https://caniuse.com/avif, https://caniuse.com/webp). Google web.dev image optimization documentation (https://web.dev/articles/serve-images-with-correct-dimensions). Compression benchmark studies (Cloudinary, Squoosh comparison data).
- **Methodology**: Browser support data: documented by Can I Use (tracking browser capability flags across versions). Compression ratios: comparative compression tests across image formats with equivalent visual quality (measured via SSIM or DSSIM similarity scores).
- **Key Finding**: AVIF (AV1 Image Format): 50% smaller than JPEG, 20–30% smaller than WebP at equivalent quality, ~94.9% global browser support (caniuse.com, verified 2026-04-21). WebP: ~96.4% global browser support (caniuse.com, verified 2026-04-21). Use `<picture>` element for progressive format negotiation — offers AVIF first, WebP second, JPEG as fallback. A 1500×1500px product image as JPEG (~500KB) can become ~100KB as AVIF — reducing LCP by several hundred milliseconds for mid-speed connections. With AVIF now near-parity with WebP in browser support, AVIF-first is acceptable for most markets.
- **E-Commerce Application**: Use `<picture>` with `<source>` elements for all product images (see Finding 6 example). For CDN-served images (Cloudinary, Imgix, Shopify's CDN): append format parameters to auto-select AVIF/WebP. Shopify's CDN automatically serves WebP to supporting browsers. For maximum performance: configure CDN to serve AVIF to supporting browsers.
- **Replication Status**: Browser support percentages are tracked in real-time (Can I Use, Stat Counter). Format compression advantages are documented in multiple independent benchmarks. Well-established.
- **Boundary Conditions**: AVIF encoding is computationally expensive — it's not suitable for client-side on-the-fly encoding of high volumes of images. Use CDN-level transcoding. Some specialized image types (simple icons, simple graphics) may be better served as SVG. Transparent images need PNG fallback (AVIF and WebP both support transparency).
- **Evidence Tier**: Gold — browser support data is public and verifiable; compression ratios from multiple independent benchmarks.

---

### Finding 8: Third-Party Scripts Are the Primary CWV Killer — 35 Scripts = +1.19s LCP
- **Source**: SpeedCurve, "How third-party scripts impact performance" (https://www.speedcurve.com/blog/3rd-party-scripts-webpagetest/). SpeedCurve testing: LCP measured with all third-party scripts enabled vs. disabled. Backlinko web performance analysis (large-scale crawl): each third-party script adds approximately 34ms to page load.
- **Methodology**: SpeedCurve: WebPageTest-based A/B performance measurement with third-party scripts enabled vs. blocked. The 26.82s LCP example comes from SpeedCurve's published test results on a specific ecommerce site. Backlinko: correlation analysis across large crawl dataset.
- **Key Finding**: SpeedCurve testing: a real ecommerce site had LCP <1s with third-party scripts blocked; LCP jumped to 26.82s with all third-party scripts enabled. Average website: 35+ third-party scripts. Backlinko analysis: each third-party script contributes approximately 34ms of additional delay. 35 scripts × 34ms = 1.19s additional LCP from third-party scripts alone — before any first-party performance issues.
- **E-Commerce Application**: Conduct a third-party script audit: (1) List all third-party scripts loading on product pages; (2) Categorize: tracking/analytics, social widgets, chat, marketing automation, A/B testing tools, recommendation engines; (3) Ask for each: "Is this directly attributable to revenue?" (4) Remove scripts that fail the revenue test; (5) For remaining scripts: implement async/defer loading and conditional loading (e.g., load chat widget only when user scrolls toward it). Use Chrome DevTools → Performance → third-party summary to identify the worst offenders. **Consent-timing boundary (EU):** ePrivacy Directive Art. 5(3) requires prior informed consent before firing non-essential tracking or marketing scripts. Under CNIL v. Google (€325M, 1 September 2025), pre-consent firing of analytics or advertising scripts is a confirmed enforcement target. "Ruthless script auditing" must align with consent-gate timing — scripts in the analytics/marketing/personalization category must fire only post-consent. See ethics-gate.md Part 7.2 for the canonical compliance rule.
- **Replication Status**: SpeedCurve's testing is reproducible (WebPageTest is open methodology). The 34ms per script average from Backlinko is a large-sample correlation. Both are directionally consistent with multiple other third-party performance analyses.
- **Boundary Conditions**: Third-party script impact varies enormously by script. A lightweight analytics tag may add <5ms; a full-featured recommendation engine may add 500ms+. The 34ms average masks huge variance. Tag managers that load synchronously before their contents are particularly harmful.
- **Citation Status**: SpeedCurve primary article URL (speedcurve.com/blog/3rd-party-scripts-webpagetest/) redirects to blog root as of 2026-04-21 audit; the 26.82s LCP figure in the finding comes from the SpeedCurve published test results cited in the original analysis and carries forward from that provenance — not re-verifiable at the current canonical URL. CNIL v. Google €325M (1 September 2025) accepted as cited; flag for confirmation against CNIL press release primary source at ethics-gate reconciliation pass.
- **Evidence Tier**: Silver — SpeedCurve is a performance monitoring vendor with transparent methodology (not in Gold publisher list); Bronze — Backlinko is a vendor blog per tier rules. Combined finding: Silver.

---

### Finding 9: Google Uses CrUX Field Data for Rankings — NOT Lighthouse Lab Data
- **Source**: Google Search Central, "Core Web Vitals and page experience," https://developers.google.com/search/docs/appearance/core-web-vitals. Google Chrome User Experience Report (CrUX) documentation: https://developer.chrome.com/docs/crux/. CrUX methodology: 28-day rolling window of Chrome user data.
- **Methodology**: Google official documentation describing the data source for CWV ranking signals.
- **Key Finding**: Google uses real user field data from the Chrome User Experience Report (CrUX) — NOT Lighthouse/PageSpeed Insights lab data — for CWV ranking signals. CrUX collects: LCP, INP, CLS from opted-in Chrome users on desktop and Android Chrome. Chrome on iOS does NOT contribute to CrUX (WebKit rendering engine, not Blink). 28-day rolling window. If a URL doesn't have enough CrUX data, Google uses origin-level data (the whole domain's CrUX profile).
- **E-Commerce Application**: (1) Don't optimize for Lighthouse 100 — optimize for real user experience; (2) Monitor your actual CrUX data via: PageSpeed Insights (scroll to "Discover what your real users are experiencing"), Google Search Console CWV report; (3) Low-traffic pages may not have URL-level CrUX data — check origin-level in CrUX dashboard; (4) Chrome iOS users' experiences are NOT captured in CrUX.
- **Replication Status**: Google official documentation — definitive data source description.
- **Boundary Conditions**: Pages with insufficient real user data (new pages, low-traffic pages) fall back to origin-level data — meaning your entire domain's average performance affects these pages. A poorly-performing blog page can hurt a new product page's CrUX profile.
- **Evidence Tier**: Gold — Google Search Central official documentation.

---

### Finding 10: Swappie — LCP -55%, CLS -91% → 42% Mobile Revenue Increase
- **Source**: Google web.dev, "How Swappie increased mobile revenue by 42% by focusing on Core Web Vitals," https://web.dev/case-studies/swappie. Published September 2021.
- **Methodology**: Before/after comparison (not a pure A/B test — the same site measured before and after optimization). Time periods: pre-optimization vs. post-optimization metrics. The lack of a simultaneous control is a limitation; seasonality and other factors could influence the result. However, the metrics changes (LCP -55%, CLS -91%) are substantial and directly attributable to the optimization work.
- **Key Finding**: Swappie (Finnish refurbished phone ecommerce): LCP reduced by 55%, CLS reduced by 91%, FID reduced by 90%, load time reduced by 23%. Result: 42% increase in mobile revenue and 10 percentage point increase in relative mobile conversion rate.
- **E-Commerce Application**: CLS impact is often underestimated. CLS causes visible page jumps during loading — buttons moving, content shifting. Users who experience CLS lose confidence in the page and may abandon. The 91% CLS reduction and 42% revenue increase suggests CLS was a major contributor to Swappie's mobile revenue problem.
- **Replication Status**: Published web.dev case study — Swappie is a named company with disclosed metrics. Not an A/B test, so causality is less certain than Vodafone. The direction (CWV improvement = revenue improvement) is consistent with all web.dev case studies.
- **Boundary Conditions**: Swappie sells refurbished smartphones — a product requiring significant trust and a high-consideration purchase. CWV impact may be proportionally larger for higher-consideration purchases where site quality signals matter more.
- **Evidence Tier**: Gold — web.dev case study with named company and disclosed methodology (acknowledging the before/after limitation vs. A/B test).

---

### Finding 11: Ray-Ban Speculation Rules API → +101% Mobile PDP Conversion
- **Source**: Google web.dev, "How Ray-Ban doubled conversion rate and reduced exit rate by 13% through prerendering," https://web.dev/case-studies/rayban-speculation-rules.
- **Methodology**: A/B test with Speculation Rules API prerendering enabled (variant) vs. not (control) on Ray-Ban's product pages. Mobile PDP conversion measured as primary metric. Disclosed A/B methodology.
- **Key Finding**: Ray-Ban implemented the Speculation Rules API to prerender product detail pages from collection pages (predicting which product a user would navigate to next). Mobile PDP conversion: +101.47%. Desktop PDP conversion: +156.16%. Exit rate reduction: -13%. The mechanism: prerendered pages appear to load instantly when navigated to, because the browser has already fetched and rendered them in the background.
- **E-Commerce Application**: Speculation Rules API (Chrome 108+, ~65%+ global desktop browser support): implement on collection pages to prerender likely next PDPs:
```html
<script type="speculationrules">
{
  "prerender": [{
    "urls": ["/products/carbon-fiber-hood", "/products/borla-catback"]
  }]
}
</script>
```
Or use dynamic rules that prerender on hover:
```html
<script type="speculationrules">
{
  "prerender": [{
    "where": {"href_matches": "/products/*"},
    "eagerness": "eager"
  }]
}
</script>
```
- **Replication Status**: A/B tested case study — controlled methodology. Chrome-only (not available on Firefox/Safari). The +101% lift is very large and should be treated as an upper bound for the specific Ray-Ban context.
- **Boundary Conditions**: Speculation Rules API is Chrome-only as of April 2026 (~65% desktop market share). The prerendering consumes bandwidth and CPU — expensive on mobile connections. Use eagerness controls to limit prerendering to high-probability navigations. Not suitable for pages with heavy server-side personalization (prerendered content may not match the user's actual state).
- **Evidence Tier**: Silver (web.dev case study; Google Developers blog is Silver-listed)

---

### Finding 12: CLS — Reserve Space for All Dynamic Elements
- **Source**: Google web.dev, "Optimize CLS," https://web.dev/articles/optimize-cls. Google Search Central CLS documentation: https://web.dev/articles/cls.
- **Methodology**: Google official documentation describing CLS causes and fixes.
- **Key Finding**: CLS (Cumulative Layout Shift) is caused by content that loads late and pushes existing content around. Common ecommerce causes: (1) images without `width` and `height` attributes — browser reserves no space until image loads; (2) dynamically-loaded variant selectors or price elements; (3) promotional banners injected above the fold after page load; (4) late-loading web fonts causing FOUT (Flash of Unstyled Text) that changes layout; (5) deferred third-party widgets (review widgets, live chat) that appear after initial render.
- **E-Commerce Application**: (1) Always specify `width` and `height` attributes on all `<img>` elements (or use CSS `aspect-ratio`); (2) Reserve space for price/variant selectors with explicit min-height in CSS; (3) Never inject content above the user's current scroll position; (4) Use `font-display: swap` with size-adjusted fallback fonts to minimize font swap shift; (5) Pre-size review widget containers with explicit dimensions.
- **Replication Status**: Google official documentation — definitive cause/fix descriptions for CLS.
- **Boundary Conditions**: Some CLS is unavoidable (dynamic content inherently changes layout). The goal is to minimize layout shifts caused by resources loading late. CLS from user interactions (e.g., the user clicking to expand content) does not contribute to the CLS score — only unexpected shifts count.
- **Evidence Tier**: Silver (web.dev case study; Google Developers blog is Silver-listed)

---

### Finding 13: CWV Optimization Priority for Ecommerce PDPs
- **Source**: Synthesis of Google CWV documentation https://web.dev/articles/vitals, web.dev case studies https://web.dev/case-studies/, and practitioner analysis of most common ecommerce CWV failure patterns (Cloudflare Web Analytics https://www.cloudflare.com/web-analytics/, HTTP Archive CrUX data https://httparchive.org/).
- **Methodology**: Synthesis of Google documentation and observational analysis of CrUX failure patterns across ecommerce sites. Not a single study.
- **Key Finding**: For most ecommerce product pages, the priority order is: (1) LCP — failing most often, biggest revenue impact (Vodafone case study); (2) INP — often failing on ecommerce due to JavaScript-heavy variant selectors, dynamic price calculations, complex add-to-cart flows; (3) CLS — often caused by images without dimensions or dynamic promotional elements. LCP optimization for hero product images typically provides the fastest time-to-impact for rankings and conversion.
- **E-Commerce Application**: Optimization priority order for typical ecommerce PDP:
  1. Fix lazy-loading on hero image (`loading="eager"`, `fetchpriority="high"`)
  2. Convert hero image to AVIF/WebP (`<picture>` element)
  3. Add `width` and `height` to all product images (CLS fix)
  4. Audit and remove unnecessary third-party scripts
  5. Address INP in variant selectors and add-to-cart interactions
  6. Implement Speculation Rules API on collection pages (highest upside, Chrome-only)
- **Replication Status**: Synthesis of multiple documented findings — not a single study.
- **Boundary Conditions**: Priority order may differ for sites with unusual CWV patterns. Always diagnose with real CrUX data before assuming the standard priority applies.
- **Evidence Tier**: Silver (synthesis finding derived from multiple sources; no single primary Gold-tier source)

---

<!-- FINDING 14 REMOVED 2026-04-22 (Vera reconciled audit): ALM Corp INP ranking-drop analysis had no anchored URL and was a single non-peer-reviewed analysis with limited methodology transparency. Run B recommended REMOVE; reconciler concurred. The research question "Does poor INP correlate with ranking drops?" is DEFERRED — no verifiable primary source. Google has confirmed only the general Page Experience signal (Finding 3). Optimize INP for UX/conversion value regardless of the unverifiable SEO-specific claim. If a primary ALM Corp URL surfaces in future audit passes, the INP-ranking-drop question can be re-added with real provenance. -->

---

## Methodological Notes and Caveats

1. **CrUX data represents Chrome users only.** Chrome has ~65% browser market share. Safari/Firefox users' experiences are not captured. For Safari-heavy audiences (Apple users, design/creative industries), CrUX data may not fully represent their experience.

2. **The Vodafone case study (Finding 5) is the gold standard.** It's an A/B test with disclosed sample size. Other case studies (Swappie, Ray-Ban) are before/after or A/B with less disclosed methodology — directionally valid but less causally certain.

3. **Lighthouse lab scores are useful for diagnosis — not for ranking evaluation.** Use Lighthouse/PageSpeed Insights to identify issues; use CrUX/Search Console to understand ranking impact.

4. **CWV thresholds will likely change over time.** Google periodically updates CWV metrics and thresholds. Finding 2 (INP replacing FID) shows this is an ongoing evolution. Check current thresholds at web.dev/vitals before implementation decisions.

---

## Sources Consulted

- Google Search Central Core Web Vitals: https://developers.google.com/search/docs/appearance/core-web-vitals
- web.dev INP launch announcement (2024-03-12): https://web.dev/blog/inp-cwv-launch
- Google web.dev Optimize LCP: https://web.dev/articles/optimize-lcp
- Google web.dev Optimize INP: https://web.dev/articles/optimize-inp
- Google web.dev Optimize CLS: https://web.dev/articles/optimize-cls
- Vodafone Case Study (+8% sales): https://web.dev/case-studies/vodafone
- Swappie Case Study (+42% mobile revenue): https://web.dev/case-studies/swappie
- Ray-Ban Speculation Rules (+101% mobile conversion): https://web.dev/case-studies/rayban-speculation-rules
- Deloitte Milliseconds Make Millions: https://www.deloitte.com/ie/en/services/consulting/research/milliseconds-make-millions.html
- web.dev Milliseconds Make Millions (case study summary): https://web.dev/case-studies/milliseconds-make-millions
- SpeedCurve Third-Party Scripts: https://www.speedcurve.com/blog/3rd-party-scripts-webpagetest/
- Chrome User Experience Report (CrUX): https://developer.chrome.com/docs/crux/
- Speculation Rules API Implementation Guide: https://developer.chrome.com/docs/web-platform/implementing-speculation-rules
