<!-- RESEARCH_DATE: 2026-04-21 -->
<!-- RECONCILED: 2026-04-22 by opus-4.7-reconciler -->
# Product Image Gallery UX: Research Findings

**Research Date**: April 21, 2026 (reconciled from April 2, 2026 research; Run A + Run B audits 2026-04-21)
**Domain**: Product Media — Gallery & Image Navigation
**Total Findings**: 13
**Methodology Note**: Findings draw primarily from Baymard Institute usability testing (gold standard for ecommerce UX), supplemented by eye-tracking research. See also eye-tracking-and-scan-patterns.md (ECP) for visual attention findings that directly affect gallery design.

---

## Cross-Reference Notice

**ECP Reference Overlap**: The following findings in ECP's `eye-tracking-and-scan-patterns.md` directly cover gallery UX topics:
- **Finding 1** (56% image-first behavior on product pages) — do not duplicate here
- **Finding 9** (25% of sites fail image zoom quality; 40% lack mobile pinch-to-zoom) — do not duplicate
- **Finding 10** (42% of users try to judge size from images; 28% of sites provide no in-scale image) — do not duplicate
- **Finding 25** (video placement in gallery; 35% get it wrong) — covered in video-optimization.md

**Hero image LCP optimization** (Finding 7 below — never lazy-load first gallery image) covers the same technical guidance as `core-web-vitals.md` Finding 6 and `hero-section-psychology.md` Finding 12. Do not cite multiple files for the same `fetchpriority="high"` recommendation.

This file covers: thumbnail type, swipe mechanics, image count signaling, hover states, and quickview — topics NOT covered in the CRO scan-patterns file.

---

## Summary

### Top 3 Most Impactful Findings

1. **Finding 1 (Thumbnails vs. Dots)**: 50% of desktop users miss additional images when only dot indicators are shown — dot navigation fails at the fundamental task of revealing the gallery exists. Thumbnails are always superior.
2. **Finding 3 (Mobile Gallery Abandonment)**: Swipe gesture support is the baseline expectation for mobile image galleries; failure creates instant distrust signals regardless of product quality.
3. **Finding 7 (Quick View Disorientation)**: Quick View modals regularly cause users to believe they've navigated to the product page; when they hit back, they're confused. The pattern has narrow viability conditions.

---

## Findings

### Finding 1: Dot Navigation Causes 50% of Desktop Users to Miss Additional Images

- **Source**: Baymard Institute. "Always Use Thumbnails to Represent Additional Product Images (76% of Mobile Sites Don't)." https://baymard.com/blog/always-use-thumbnails-additional-images. Published October 2020, drawn from ongoing benchmark research.
- **Methodology**: Qualitative usability testing (think-aloud + eye-tracking with Tobii) across 19+ major e-commerce sites, 4,400+ cumulative test sessions. 76% of mobile sites observed to use dots rather than thumbnails.
- **Key Finding**: 50% of desktop test subjects missed the existence of additional product images when dot indicators were the only navigation mechanism. Dots provide no preview of what images exist, have tiny tap targets (~8px radius), and provide no content differentiation cues. Thumbnails provide all three functions: visual preview, direct access, and evidence that more images exist.
- **E-Commerce Application**: Always use thumbnail strips on desktop. On mobile, thumbnails are preferred; if dots are used due to space constraints, ensure minimum 44px touch targets and supplement with an image counter ("1 of 8"). Never rely on dots alone on desktop.
- **Replication Status**: Consistent across multiple Baymard benchmark rounds (2014–2024). The finding is among the most stable in Baymard's product page research.
- **Boundary Conditions**: Dot navigation may be acceptable for single-purpose galleries with ≤3 images where the content type is obvious. On very small mobile screens (320px width), thumbnail strips can create layout problems — a counter + large dots (44px+) is an acceptable fallback.
- **Evidence Tier**: Gold

---

### Finding 2: Mobile Gallery Requires Native Swipe Support as Baseline Expectation

- **Source**: Baymard Institute. "Mobile E-Commerce Usability." https://baymard.com/research/mcommerce-usability. Ongoing research through 2024 covering mobile image gallery interaction patterns.
- **Methodology**: Large-scale mobile usability testing. Qualitative observation of user interactions with image galleries across 20+ major mobile e-commerce sites.
- **Key Finding**: Mobile users universally expect and use swipe gesture to navigate image galleries. This behavior is instinctive — users attempt swipe even before looking for navigation controls. Sites that intercept native scroll in ways that conflict with swipe cause immediate abandonment signals (frustration, visible hesitation, repeated failed attempts). There is no tolerance for broken swipe behavior on mobile galleries.
- **E-Commerce Application**: Use CSS `scroll-snap` for hardware-accelerated native swipe behavior. Never intercept scroll events to implement custom swipe — this breaks browser default scroll and leads to the exact failure mode observed. Ensure smooth, responsive animation on swipe. Provide loop behavior or clear end-of-gallery indication to prevent the "dead end swipe" confusion pattern.
- **Replication Status**: Replicated consistently across Baymard mobile testing rounds.
- **Boundary Conditions**: Applies to touch devices. Desktop hover galleries have different mechanics. This applies specifically to swipe gesture support — not to the specific navigation UI pattern above the swipe layer.
- **Evidence Tier**: Gold

---

### Finding 3: Without Image Count Indication, Users Swipe Repeatedly Past the Last Image

- **Source**: Baymard Institute. "Truncating Additional Images in the Gallery Causes 50-80% of Users to Overlook Them (30% Get it Wrong)." https://baymard.com/blog/truncating-product-gallery-thumbnails. 2019 research update.
- **Methodology**: Qualitative usability testing with observation of swipe behavior at gallery end states. Identified across multiple rounds of mobile and desktop testing.
- **Key Finding**: 50–80% of users overlook truncated or hidden product images when truncation indicators are absent or inadequate; 30% of e-commerce sites truncate gallery thumbnails without sufficiently clear truncation indication. Manual vertical carousels performed worst: 83% of test subjects had significant trouble finding (or never found) truncated thumbnails. Users use image count as a mental model for evaluation completeness; without it, they either over-swipe (wasting time) or under-explore (missing key images). A thumbnail strip showing all images with the current active state highlighted is optimal; a "3 of 8" counter is the minimum viable solution.
- **E-Commerce Application**: Implement one of these solutions (in priority order): (1) Full thumbnail strip showing all images with current active state highlighted; (2) Partial thumbnail peek showing the edge of adjacent thumbnails to signal more exist; (3) Image counter in format "N of N" that updates as images are swiped; (4) Large gradient-fade edge indicator. Never leave a gallery without one of these signals.
- **Replication Status**: Consistent across Baymard benchmark rounds. The "dead-end bounce" pattern is reliably observed.
- **Boundary Conditions**: Galleries with ≤3 images have low risk from missing count indicators. Risk increases linearly with gallery depth. Mobile context shows higher abandonment than desktop for this issue.
- **Evidence Tier**: Gold

---

### Finding 4: 76% of Sites Use No Synchronized Hover Effects or Unified Hit Areas

- **Source**: Baymard Institute. "Hover UX: Use Synchronized Hover Effects & Unified Hit-Areas (76% Don't)." https://baymard.com/blog/list-items-hover-and-hit-area. Published 2020, based on benchmark of **50 major US e-commerce sites**.
- **Methodology**: Benchmark of 50 major US e-commerce sites. Observation of hover interaction quality across product listing pages. (Note: Baymard's broader benchmark covers 327 sites across all UX topics; the hover-specific 76% figure is from the focused 50-site study.)
- **Key Finding**: 76% of product list pages do not implement synchronized hover effects with unified hit areas. Users expect the entire product card to be clickable (unified hit area), and expect all visual changes — image swap, overlay appearance, quick action visibility — to occur simultaneously on hover. Split hit areas (only image clickable, title in different link zone) cause confusion and misclicks. Delayed or desynchronized hover effects feel broken.
- **E-Commerce Application**: Make the entire product card a single clickable region. All hover state changes (secondary image, overlay, quick actions) must trigger simultaneously from the same event. Show 2–4 of the following on hover: secondary product image (lifestyle vs. packshot), available color swatches, quick-add button, wishlist button, and star rating summary. Use CSS transitions (opacity: 0 → 1, 150–200ms) rather than JavaScript-triggered class changes for performance.
- **Replication Status**: Benchmark finding, consistent across Baymard's ongoing benchmarking.
- **Boundary Conditions**: Hover states are desktop-only; mobile requires explicit touch targets. This finding is less relevant for sites with predominantly mobile traffic (>80% mobile share).
- **Evidence Tier**: Gold

---

### Finding 5: Quick View Modals Cause Disorientation — Users Believe They've Navigated to a New Page

- **Source**: Baymard Institute. "Avoid 'Quick Views' for Spec-Driven Product Types (21% Don't)." https://baymard.com/blog/ecommerce-quick-views. Research from multiple usability testing rounds 2014–2022.
- **Methodology**: Qualitative usability testing with think-aloud protocol. Multiple rounds of testing across sites with and without Quick View modals.
- **Key Finding**: Quick View modals regularly cause users to believe they have navigated to the product detail page. When they press the browser back button and find themselves on the category page rather than a page in their history, they are confused and frequently abandon. This confusion occurs because modals often fill a large portion of the viewport and contain product-page-like content. The pattern shows a "small conversion increase" on sites with insufficient information in list view — because any additional info helps — but the back-button disorientation is a consistent negative side effect. Baymard reports 21% of spec-driven sites use Quick View despite its downsides.
- **E-Commerce Application**: If implementing Quick View: (1) Make modal styling clearly different from the product page (partial-screen overlay with visible backdrop); (2) Include a prominent "View Full Details →" link; (3) Ensure ESC, click-outside, and visible X button all close the modal; (4) Test whether the increase in product page views (a vanity metric) translates to actual conversion. Better alternatives: improved hover states with key info (desktop), expanded inline cards, or bottom-sheet drawers (mobile).
- **Replication Status**: Replicated across multiple Baymard testing rounds. The confusion pattern is stable.
- **Boundary Conditions**: Quick View may be appropriate for product comparison contexts where users are deliberately evaluating multiple items. The pattern works better for simple products (single variant, clear pricing) than for complex products requiring configuration.
- **Evidence Tier**: Gold

---

### Finding 6: Lightbox Zoom — Desktop Users Expect Both Inline Hover Zoom and Fullscreen Option

- **Source**: Baymard Institute. "Ensure Sufficient Image Resolution and Zoom." https://baymard.com/blog/ensure-sufficient-image-resolution-and-zoom. Published 2018, updated 2022.
- **Methodology**: Qualitative usability testing with eye-tracking. Baymard reports 25% of e-commerce sites provide insufficient resolution or zoom (14% low-resolution + 11% insufficient zoom); 93% of sites allow some form of zoom but only 75% at adequate quality.
- **Key Finding**: Desktop users expect two zoom modalities: (1) Hover-triggered inline magnification (mouse-lens zoom) for quick detail inspection without leaving the gallery context; (2) Click-triggered lightbox or fullscreen mode for deep inspection and zooming into specific areas. Sites offering only one mode leave users frustrated. Mobile zoom via pinch-to-zoom is covered in eye-tracking-and-scan-patterns.md (Finding 9) — 40% of stores still lack mobile pinch-to-zoom support.
- **E-Commerce Application**: On desktop, implement both hover zoom (follows mouse, 2–3x magnification in an inset panel or inline expansion) and click-to-fullscreen lightbox. Zoom source images must be ≥2000px on shortest side for acceptable zoom quality. Include a zoom indicator icon (magnifying glass) on images to signal the capability exists. In the lightbox, include navigation arrows and thumbnail strip for continuity.
- **Replication Status**: Consistent across Baymard benchmark rounds.
- **Boundary Conditions**: Hover zoom can be omitted for very simple products (cables, basic commodities) where detail inspection is low-value. Hover zoom quality depends entirely on source image resolution — implementing hover zoom with low-resolution sources (≤1000px) creates a worse experience than no zoom.
- **Evidence Tier**: Gold

---

### Finding 7: Gallery Carousel Performance — First Image Requires Special Treatment

- **Source**: Google Web Vitals / web.dev. "Optimize Largest Contentful Paint." https://web.dev/articles/optimize-lcp. Last updated March 2025. Cross-referenced with Baymard Institute product image positioning research.
- **Methodology**: Web performance research combining Google CrUX data across millions of real-world user sessions with Core Web Vitals measurement methodology. Rakuten 24 case study: A/B test on high-traffic landing page (N = millions of sessions).
- **Key Finding**: The primary product image in a gallery carousel is typically the Largest Contentful Paint (LCP) element on product pages. Treating it as just another carousel image (lazy-loaded, low priority) directly degrades LCP scores. The image should be treated as a priority resource: not lazy-loaded, given `fetchpriority="high"` (Google recommends this attribute for likely LCP elements), and preloaded via `<link rel="preload">`. All subsequent gallery images (position 2+) should be lazy-loaded. Rakuten 24 saw 33% conversion increase and 53% revenue-per-visitor increase from CWV improvements; LCP was a primary driver. LCP thresholds: ≤2.5s Good; 2.5–4.0s Needs Improvement; >4.0s Poor.
- **E-Commerce Application**: Implement two-tier gallery loading: hero image (position 1) as high-priority non-lazy-loaded asset with preload header; images 2–N as lazy-loaded assets. Use `scroll-snap` CSS for smooth carousel behavior without JavaScript overhead. Reserve explicit width/height on all gallery image containers to prevent Cumulative Layout Shift during load.
- **Replication Status**: See page-performance-psychology.md (ECP) Finding 5 (Rakuten 24 case study) and Finding 12 (Vodafone LCP-to-sales pipeline) for corroboration.
- **Boundary Conditions**: Performance impact is greatest on mobile and slower connections. High-bandwidth desktop users may see minimal difference. The preload approach can backfire if applied to below-fold images (wastes bandwidth on images that may never be viewed).
- **Evidence Tier**: Gold (Google CrUX data + production A/B testing)

---

### Finding 8: Video Integration in Gallery — Position 2 or 3 is Optimal

- **Source**: Baymard Institute. "UX Research on Product Page Videos: Where and How to Embed Them (35% Get it Wrong)." https://baymard.com/blog/embedding-product-page-videos. 2019. Cross-referenced with eye-tracking-and-scan-patterns.md Finding 25.
- **Methodology**: Usability testing and benchmark analysis across major e-commerce sites with product videos.
- **Key Finding**: Product videos embedded in the main image gallery at position 2 or 3 receive the highest view rates — 41% of users watch product videos when placed well. Videos placed in separate tabs, below the fold, or accessible only via text link are missed by the majority of users. 35% of major e-commerce sites fail to get these placement details right — the video effectively does not exist for most users. Baymard guidance: place video "at the top of the product page, mixed with or next to the product image gallery." A clear play button overlay on the thumbnail is required — users do not discover video content without a recognizable play icon.
- **E-Commerce Application**: Embed video as a gallery item at position 2–3 (after the hero packshot). Use a video-specific thumbnail with a visible play button overlay (minimum 48px icon). For autoplay behavior, use muted autoplay only for short loops (≤5 seconds); all narrated or instructional video must be click-to-play. See video-optimization.md for complete video guidance.
- **Replication Status**: Cross-referenced with Finding 16 in eye-tracking-and-scan-patterns.md (27% of users overlook tabbed content entirely), which provides the mechanism explaining why non-gallery video placement fails.
- **Boundary Conditions**: The position 2–3 recommendation assumes a standard gallery layout. For products where video IS the primary media (e.g., motion-dependent products like fans, waterfalls, kinetic art), video in position 1 is appropriate.
- **Evidence Tier**: Gold

---

### Finding 9: Keyboard Accessibility — Gallery Navigation Fails WCAG 2.1 AA at Most Sites

- **Source**: Baymard Institute. "E-Commerce Accessibility" (collection of 8 articles, 2021–2025). https://baymard.com/blog/collections/accessibility. Featured finding: "94% of the Largest E-Commerce Sites Are Not Accessibility Compliant." W3C WAI, WCAG 2.1 Success Criterion 2.1.1 (Keyboard). https://www.w3.org/WAI/WCAG21/quickref/. Cross-reference: ECP `references/accessibility.md` for the dedicated accessibility reference.
- **Methodology**: Baymard accessibility UX research across the top 50 largest US e-commerce sites; WCAG conformance auditing methodology.
- **Key Finding**: 94% of the largest e-commerce sites are not compliant with basic WCAG 2.1 AA criteria (Baymard 2024 featured finding). Product galleries are a recurring failure point. Common failures: (1) thumbnail buttons not reachable via Tab; (2) arrow key navigation not implemented; (3) lightbox/zoom modal traps focus and cannot be escaped via keyboard; (4) no visible focus indicator on gallery controls. This affects not only screen reader users but the 10–15% of desktop users who rely primarily on keyboard navigation.
- **E-Commerce Application**: Implement the full keyboard pattern: Tab to enter the gallery, Arrow keys to navigate thumbnails, Enter/Space to select, Escape to close lightbox. Use `role="region" aria-label="Product images"` on gallery container. Use `role="tablist"` and `role="tab"` on thumbnail navigation. Use `aria-live="polite"` to announce image changes. Ensure all interactive elements have visible focus indicators (outline: 2px solid, outline-offset: 2px minimum).
- **Replication Status**: WCAG requirements are W3C standards. The 94% non-compliance figure is Baymard's current benchmark. See accessibility.md for the full accessibility reference. Alt-text on gallery images is covered in image-seo-alt-text.md (content-seo cluster) — ADJACENT per ethics-gate.md PART 7.3.
- **Boundary Conditions**: ADA/accessibility lawsuit risk varies by jurisdiction and company size. Compliance requirements are higher in the US, EU (European Accessibility Act effective 28 June 2025), and UK. Small stores face lower regulatory risk but identical ethical obligation.
- **Evidence Tier**: Gold (WCAG is a W3C standard; Baymard benchmark confirms industry non-compliance)
- **Audit Note (2026-04-22)**: Prior version cited `baymard.com/blog/accessibility` (non-resolving). Updated to the live Baymard accessibility collection URL. 94% non-compliance figure added from Baymard's featured article in that collection.

---

### Finding 10: Partial Thumbnail Peek Signals Gallery Depth on Mobile

- **Source**: Baymard Institute. "Mobile E-Commerce Usability." https://baymard.com/research/mcommerce-usability. Ongoing research through 2024.
- **Methodology**: Mobile usability testing, observation of user behavior with thumbnail strips of varying implementations.
- **Key Finding**: On mobile, showing a partial peek of the next thumbnail (cutting off the rightmost thumbnail at ~50% visibility) is an effective signaling pattern that communicates "more images exist" without requiring a counter or full thumbnail strip. This pattern is borrowed from horizontal scroll containers and is intuitively understood. It outperforms full-bleed single images with dot indicators for gallery depth communication.
- **E-Commerce Application**: In mobile gallery implementations, design the thumbnail strip so the rightmost visible thumbnail is partially cut off (~30–50% visible). Use `overflow-x: scroll` with the container width calculated to show 3.5 thumbnails (for example), never a whole number. This creates the "peek" effect. Pair with CSS `scroll-snap` for smooth behavior.
- **Replication Status**: Consistent with Baymard's horizontal navigation research and general "signifier of scrollability" research (NNGroup).
- **Boundary Conditions**: Requires deliberate implementation — default thumbnail strip layouts often show whole thumbnails and must be manually configured to show partial. Less impactful when gallery has ≤3 images (all thumbnails visible).
- **Evidence Tier**: Gold

---

### Finding 11: 360-Degree Spin Viewers — User-Controlled Rotation Supports Angle-Level Evaluation

<!-- RECONCILER NOTE: The prior claim that BrandXR reports "360 spin outperforms video loops" is not supported by the BrandXR 2025 report, which does not make that comparison. Rewritten per Run B finding and reconciler brief (Known Issue). Tier downgraded Silver → Bronze. -->

- **Source**: BrandXR. "2025 Augmented Reality in Retail & E-Commerce Research Report." https://www.brandxr.io/2025-augmented-reality-in-retail-e-commerce-research-report (general 3D/AR engagement context; does not directly compare 360-spin to video-loop formats). General UX principle: user-controlled interaction produces better information gathering than passive presentation.
- **Methodology**: BrandXR 2025 industry report synthesizing AR/3D adoption and satisfaction data across retail brands. Not a controlled study; no direct 360-spin-vs-video-loop comparison in the source.
- **Key Finding**: Interactive 360-degree spin viewers (drag-to-rotate image sequences of 24–72 frames) give users control over rotation speed and direction. User-controlled interaction with product rotation supports angle-level evaluation — users can stop at the specific orientation they care about, which passive video loops do not allow. Implementation quality matters: image sequences must be smooth (≥24 frames for non-jerky rotation), file sizes must be optimized (2–5MB total). The BrandXR 2025 report indicates 98% of AR-users found AR helpful for purchase decisions and 92% of Gen Z want AR for shopping — providing general engagement context, not a direct format comparison.
- **E-Commerce Application**: For products where viewing multiple angles is important but full AR is cost-prohibitive (electronics, shoes, bags, equipment), implement image-sequence 360 viewers as an intermediate step. Use 24–36 frames minimum; 72 frames for premium products. Total compressed weight target: <5MB. See ar-3d-visualization.md for full AR/3D reference including Shopify's 94% conversion lift and Macy's 40% return reduction.
- **Replication Status**: No controlled study directly compares 360-spin to video-loop format. The recommendation is grounded in general interaction design principle (user-control > passive consumption) and should be treated as directional.
- **Boundary Conditions**: 360 viewers have higher production cost (requires turntable photography session). ROI is product-category dependent. Simple products where all sides are nearly identical (e.g., rectangular books) gain little from 360.
- **Evidence Tier**: Bronze (general interaction principle; no direct comparative study; vendor report does not support the specific format comparison)

---

### Finding 12: Gallery Consistency — Mixed Background Styles Within a Grid Harm Visual Scanning Speed

- **Source**: Hugo Jenkins / UsabilityHub (now Lyssna). "Size and Layout of E-Commerce Product Grids: A User Research Case Study." Medium / Insights & Observations. November 2020. https://medium.com/insights-observations/size-and-layout-of-e-commerce-product-grids-a-user-research-case-study-8a8307cbd087
- **Citation Status**: Medium article may require Medium account/membership for anonymous access (403 returned on some fetches). Content confirmed via Run B fetch (scan-time data verified).
- **Methodology**: UsabilityHub click-testing platform. 6 test variations × 25 participants = N=150 total. Measured average scanning time per row across conditions.
- **Key Finding**: Visual inconsistency within a product grid — mixed background styles (some products on white, some on lifestyle backgrounds), mixed aspect ratios, or varied image quality levels — significantly increases scanning time per row and creates a perception of low quality. Jenkins' test 5 (scaled-up, consistent grid) reduced average scanning time from 4.45s (original 3-column) to 3.61s per row — nearly one full second off the average scanning time. Consistent photography style across a category page allows users to develop a scanning pattern for each card, reducing cognitive load.
- **E-Commerce Application**: Enforce consistent photography standards at the category level, not just the brand level. Within any category page, all primary images should share: same background treatment (white or consistent lifestyle), same aspect ratio, same approximate product size-to-frame ratio, and similar lighting quality. If some products in a category have professional images and others have supplier-provided images of lower quality, address this before other gallery optimizations.
- **Replication Status**: Practitioner research (N=150, UsabilityHub). Not peer-reviewed. Consistent with general cognitive load research on visual search efficiency.
- **Boundary Conditions**: Some category pages intentionally mix photography styles for editorial/storytelling reasons (e.g., curated lookbooks). The consistency requirement is most important for standard browse/category pages, not editorial pages. Small catalogs with wide visual variety may require editorial photography decisions over pure consistency.
- **Evidence Tier**: Silver

---

### Finding 13: 52% of Sites Fail to Make Decorative / Functional Images Accessible

<!-- RECONCILER ADDITION: Run B. Baymard accessibility collection, August 2021. Tightly scoped to gallery mechanics; alt-text semantics owned by content-seo cluster. -->

- **Source**: Baymard Institute. "How To Make 'Decorative' and 'Functional' Images Accessible to All Users (52% of Sites Don't)." https://baymard.com/blog/collections/accessibility. Published August 2021.
- **Methodology**: Baymard accessibility benchmark of major US e-commerce sites, evaluated against WCAG 2.1 roles and naming guidelines.
- **Key Finding**: 52% of e-commerce sites fail to properly distinguish decorative images (empty alt or `role="presentation"`) from functional images (buttons/links with accessible names) in their markup. On product galleries, functional thumbnails that lack accessible names leave screen-reader users unable to navigate between gallery positions. Decorative product images that carry long alt text flood screen readers with noise.
- **E-Commerce Application**: For gallery thumbnails that act as buttons (selecting a gallery position): use `<button aria-label="View image 2 of 8">` pattern or ensure the thumbnail's accessible name describes the function. For purely decorative repeats (e.g., a duplicated pattern frame): use `alt=""` or `role="presentation"`. For content-bearing gallery images: short, specific alt text is required — see image-seo-alt-text.md (content-seo cluster) for full alt-text guidance.
- **Replication Status**: Baymard benchmark finding. Complements Finding 9's keyboard-navigation gaps with a distinct failure mode (image role attribution, not keyboard patterns).
- **Boundary Conditions**: Legal ADA/EAA exposure applies. This file covers gallery-level mechanics; alt-text semantics (content and SEO value) are owned by the content-seo cluster per ethics-gate.md PART 7.3.
- **Evidence Tier**: Gold

---

## Methodological Notes

1. **Baymard Institute dominance**: Gallery UX research is dominated by Baymard Institute, which runs the only large-scale continuous usability testing program focused specifically on e-commerce UX. Their methodology (4,400+ cumulative test sessions, expert benchmarking across 50–327 sites depending on study scope) is the gold standard. Findings have not been independently replicated by academic researchers but are internally consistent across multiple research rounds.

2. **ECP overlap**: Critical gallery-adjacent findings (image-first visual attention, zoom quality, in-scale images, video placement) are covered in ECP's `eye-tracking-and-scan-patterns.md`. This file deliberately excludes those findings to avoid duplication.

3. **Performance intersection**: Gallery UX and page performance intersect at the LCP element. Finding 7 covers the performance-critical aspects of gallery implementation. Full performance guidance is in `media-performance-optimization.md`.

4. **Mobile vs. desktop divergence**: Several findings (1, 2, 3, 10) apply primarily or exclusively to mobile. The mobile-first majority of e-commerce traffic (typically 60–70% mobile) makes mobile gallery UX the higher-priority implementation concern.

5. **Reconciliation revisions (2026-04-22)**: Finding 4 clarified to "50 major US e-commerce sites" benchmark scope. Finding 7 URL canonicalized to `web.dev/articles/optimize-lcp`. Finding 9 URL updated to Baymard accessibility collection; 94% non-compliance figure added. Finding 11 rewritten to remove unsupported spin-vs-video-loop comparison (BrandXR source confirmed not to contain it); downgraded Silver → Bronze. Finding 12 Citation Status annotation added; scan-time data added (4.45s → 3.61s). Finding 13 added (Baymard, 52% image role attribution failure).

---

## Sources Consulted

1. Baymard Institute. "Always Use Thumbnails to Represent Additional Product Images (76% of Mobile Sites Don't)." https://baymard.com/blog/always-use-thumbnails-additional-images
2. Baymard Institute. "Mobile E-Commerce Usability." https://baymard.com/research/mcommerce-usability
3. Baymard Institute. "Truncating Additional Images in the Gallery Causes 50-80% of Users to Overlook Them (30% Get it Wrong)." https://baymard.com/blog/truncating-product-gallery-thumbnails
4. Baymard Institute. "Hover UX: Use Synchronized Hover Effects & Unified Hit-Areas (76% Don't)." https://baymard.com/blog/list-items-hover-and-hit-area
5. Baymard Institute. "Avoid 'Quick Views' for Spec-Driven Product Types (21% Don't)." https://baymard.com/blog/ecommerce-quick-views
6. Baymard Institute. "Ensure Sufficient Image Resolution and Zoom." https://baymard.com/blog/ensure-sufficient-image-resolution-and-zoom
7. Baymard Institute. "UX Research on Product Page Videos: Where and How to Embed Them (35% Get it Wrong)." https://baymard.com/blog/embedding-product-page-videos
8. Baymard Institute. "E-Commerce Accessibility" (collection). https://baymard.com/blog/collections/accessibility
9. Google web.dev. "Optimize Largest Contentful Paint." https://web.dev/articles/optimize-lcp
10. Hugo Jenkins / UsabilityHub. "Size and Layout of E-Commerce Product Grids." https://medium.com/insights-observations/size-and-layout-of-e-commerce-product-grids-a-user-research-case-study-8a8307cbd087
11. BrandXR. "2025 Augmented Reality in Retail & E-Commerce Research Report." https://www.brandxr.io/2025-augmented-reality-in-retail-e-commerce-research-report
12. W3C WAI. WCAG 2.1. https://www.w3.org/WAI/WCAG21/quickref/
13. **ECP cross-reference**: references/eye-tracking-and-scan-patterns.md (Findings 1, 9, 10, 25)
14. **Performance cross-reference**: references/page-performance-psychology.md (Findings 5, 12)
15. **Accessibility cross-reference**: references/accessibility.md
16. **Legal-adjacent cross-reference**: references/ethics-gate.md PART 7.3 (accessibility ADJACENT flagging)
