<!-- RESEARCH_DATE: 2026-04-02 -->
<!-- NOTE: Key findings from this file have been merged into page-performance-psychology.md (performance psychology findings about user perception and abandonment thresholds). This file remains as supplementary reference with additional depth on technical image optimization implementation: LCP image attributes, lazy loading strategy, modern image formats (AVIF/WebP), responsive srcset, CLS prevention with explicit dimensions, and CDN delivery. -->
# Media Performance Optimization: Research Findings

**Research Date**: April 2, 2026
**Domain**: Product Media — Image and Video Loading Performance
**Total Findings**: 12
**Methodology Note**: Performance research has the strongest evidence base in this domain — Google/Deloitte's "Milliseconds Make Millions" study and Google's Core Web Vitals are anchored in production data analysis across millions of sessions. The ECP's page-performance-psychology.md contains the full performance psychology evidence base (16 findings). This file focuses on the technical implementation details specific to media (images and video) that complement the psychology findings — avoiding duplication of the performance psychology research covered there.

---

## Cross-Reference Notice

**ECP Reference Overlap** — These findings are COVERED in page-performance-psychology.md and NOT duplicated here:
- Finding 1 (0.1s improvement = 8.4% retail conversion lift) — page-performance-psychology.md Finding 1
- Finding 3 (Progress indicators allow 3× longer wait) — page-performance-psychology.md Finding 3
- Finding 4 (0.1s/1s/10s response thresholds) — page-performance-psychology.md Finding 4
- LCP/FID/CLS Core Web Vitals business impact — page-performance-psychology.md Findings 5, 6, 7

This file covers: LCP image-specific optimization, lazy loading strategy, modern image formats, responsive images, file size targets, CDN delivery, and CLS prevention — the technical implementation layer for media specifically.

---

## Summary

### Top 3 Most Impactful Findings

1. **Finding 1 (Hero Image Is the LCP Element — fetchpriority="high" Required)**: The product hero image is the Largest Contentful Paint element on most PDPs. A single missing `fetchpriority="high"` attribute causes the browser to deprioritize it — turning a solvable performance problem into a persistent ranking and conversion drag.
2. **Finding 3 (WebP/AVIF Reduce File Size 30–50% vs. JPEG)**: Switching to modern image formats is the highest-leverage single technical change for image performance, with near-universal browser support for WebP (~96.4%) and strong support for AVIF (~94.9%). AVIF-first is now acceptable for most markets. Typical catalog-level savings: 30–50% total image weight reduction.
3. **Finding 5 (Never Lazy Load Above-Fold Images — Including Hero)**: Applying `loading="lazy"` to the hero product image is one of the most common and damaging performance mistakes — it tells the browser to deprioritize the very element that needs to load first. This is a zero-cost fix with guaranteed LCP improvement.

---

## Findings

### Finding 1: Product Hero Image Is the LCP Element — Requires fetchpriority="high" and Preload

- **Source**: Google Web Vitals. "Optimize Largest Contentful Paint." https://web.dev/articles/optimize-lcp. Updated 2024. Cross-referenced with Deloitte/Google "Milliseconds Make Millions" study (2020).
- **Methodology**: Google Web Vitals technical analysis of LCP element distribution across top websites, Chrome User Experience Report (CrUX) data. Deloitte study: 37 brands, 30M+ sessions monitored over 30 days.
- **Key Finding**: On product detail pages, the hero/main product image is the LCP element in the majority of cases (estimated >80% of PDPs based on real-world CrUX analysis). LCP thresholds: ≤2.5s Good; 2.5–4.0s Needs Improvement; >4.0s Poor. Every 0.1s improvement in load time on mobile produces 8.4% conversion lift in retail (Deloitte/Google). The three most impactful attributes for hero image LCP: (1) `fetchpriority="high"` — tells browser to prioritize this resource over others in the same network tier; (2) `<link rel="preload" as="image">` in `<head>` — begins fetching before HTML parser reaches the img tag; (3) Explicit `width` and `height` attributes — prevents layout shift during load.
- **E-Commerce Application**: For every PDP: (1) Identify the hero product image; (2) Add `fetchpriority="high"` to the `<img>` element; (3) Add `<link rel="preload" as="image" href="product-hero.webp" fetchpriority="high">` in `<head>`; (4) Add explicit `width` and `height` attributes matching the image's rendered dimensions; (5) Do NOT add `loading="lazy"` to this image. For Shopify: use `{{ product.featured_image | image_url: width: 800 }}` and add the fetchpriority attribute via theme customization. Test using Lighthouse or WebPageTest: LCP element should be identified and load within 2.5s on simulated 4G mobile.
- **Replication Status**: Google Web Vitals technical standard confirmed by Chrome DevTools analysis and CrUX real-world data. Deloitte conversion correlation is based on production session analysis across 37 brands.
- **Boundary Conditions**: fetchpriority is supported by Chrome 102+ (2022), Safari 17.2+ (2023), Firefox 132+ (2024) — Baseline-supported, ship without fallback guards (see Finding 12). Fallback gracefully for older browsers — the attribute is ignored if not understood. Preload only the above-fold hero image; preloading multiple images creates competition and may worsen LCP.
- **Evidence Tier**: Gold

---

### Finding 2: Lazy Load All Images Below the Fold — Never Lazy Load Above-Fold or LCP Images

- **Source**: Google Web Vitals. "Best Practices for Images." https://web.dev/uses-responsive-images/. Google Developers documentation on lazy loading. https://web.dev/articles/browser-level-image-lazy-loading Updated 2024.
- **Methodology**: Technical analysis of browser image loading priority queuing. Confirmed by Lighthouse audits and real-world performance measurements.
- **Key Finding**: Native browser lazy loading (`loading="lazy"`) instructs the browser to defer fetching images until they're near the viewport. Applied to the hero/main product image, this causes the LCP element to be deprioritized — directly worsening the metric most correlated with conversion. Applied to all gallery images below position 1–2, lazy loading reduces total page weight loaded on initial render by 40–70% for image-heavy PDPs. `loading="lazy"` has 92%+ global browser support (Chrome 76+, Firefox 75+, Safari 15.4+) — no JavaScript polyfill required for modern browsers.
- **E-Commerce Application**: Implementation rule: (1) Hero/main product image (LCP element): `fetchpriority="high"` — NO `loading="lazy"`; (2) First 2 gallery images (visible above fold on most viewports): no lazy loading; (3) Gallery images 3+: `loading="lazy"`; (4) Thumbnails in thumbnail strip: `loading="lazy"`; (5) UGC photos in reviews section: `loading="lazy"`; (6) Related products grid: `loading="lazy"`; (7) Footer images: `loading="lazy"`. Test with Chrome DevTools Network panel: on page load, only the first 2–3 images should load immediately; others should load as user scrolls.
- **Replication Status**: Technical standard confirmed by browser documentation and Lighthouse audits.
- **Boundary Conditions**: `loading="lazy"` can cause layout shift if image dimensions aren't specified (image loads at 0×0 then reflows to actual size). Always pair lazy loading with explicit `width` and `height` attributes or `aspect-ratio` CSS. For static site generators (Next.js, Nuxt, Gatsby), framework image components handle lazy loading automatically and correctly.
- **Evidence Tier**: Gold (technical standard)

---

### Finding 3: WebP Reduces File Size ~30%; AVIF Reduces ~50% vs. JPEG — With 97%+ and 85%+ Browser Support

- **Source**: HTTP Archive. "Web Almanac 2024 — Media." https://httparchive.org/reports/media. Google Web Vitals image format guidance. https://web.dev/uses-webp-images/
- **Methodology**: HTTP Archive crawls millions of URLs monthly, analyzing image format usage and file size patterns. Google web.dev format guidance is based on technical analysis of codec performance.
- **Key Finding**: WebP images are on average 25–34% smaller than JPEG at equivalent visual quality. AVIF images are on average 45–55% smaller than JPEG. Browser support as of 2026-04-21 (caniuse.com verified): WebP ~96.4%; AVIF ~94.9% (Chrome 85+, Firefox 93+, Safari 16+). With AVIF near-parity with WebP in browser support, AVIF-first is acceptable for most markets. The standard implementation serves AVIF to supporting browsers, WebP as fallback, JPEG as final fallback using `<picture>` element with `<source>` type negotiation.
- **E-Commerce Application**: Modern format implementation: use `<picture>` element for format negotiation: `<picture><source srcset="product.avif" type="image/avif"><source srcset="product.webp" type="image/webp"><img src="product.jpg" alt="..." loading="lazy"></picture>`. For CDN/Shopify: automatic format negotiation is supported — `Accept: image/avif,image/webp` header triggers automatic format selection on Cloudflare Images, Cloudinary, Shopify CDN, and Imgix. Quality settings: AVIF 70–75 quality (more efficient codec; lower quality number still looks good); WebP 80–85 quality; JPEG 80–85 quality. Target: hero image <100KB, gallery images <150KB each, thumbnails <25KB.
- **Replication Status**: Codec performance comparisons are technically validated by independent analysis (Cloudinary, Squoosh). Browser support data is from Can I Use (caniuse.com) which tracks actual browser version adoption.
- **Boundary Conditions**: AVIF encoding is computationally expensive — encode AVIF in advance (build time, not runtime). AVIF animated images are not well-supported. For stores serving significant traffic in China or Indonesia where older browsers persist, WebP-first is safer than AVIF-first. Some AVIF implementations in Safari (16.0–16.3) had rendering issues — test specifically.
- **Evidence Tier**: Gold (technical standard confirmed by large-scale measurement)

---

### Finding 4: Responsive Images via srcset Prevent Serving Oversized Images to Mobile — 50%+ File Size Savings

- **Source**: Google Web Vitals. "Serve images in modern formats." https://web.dev/uses-responsive-images/. W3C HTML specification for srcset. https://html.spec.whatwg.org/ Cross-referenced with WebPageTest real-world analysis. https://www.webpagetest.org/
- **Methodology**: Technical specification analysis. WebPageTest measurements of responsive vs. non-responsive image serving on real mobile devices.
- **Key Finding**: Serving a 1600px wide image to a 375px mobile screen delivers ~18× more pixels than the device can display — wasting bandwidth proportionally to the pixel ratio mismatch. `srcset` attribute allows browsers to select the optimal image size for their viewport and pixel density. A well-implemented srcset can reduce mobile image data transfer by 50–80% compared to single-size serving. `sizes` attribute tells the browser how large the image will appear in CSS layout, enabling accurate image selection before layout is known.
- **E-Commerce Application**: Hero image srcset implementation:
```html
<img
  src="product-800.webp"
  srcset="product-400.webp 400w, product-800.webp 800w, product-1200.webp 1200w, product-1600.webp 1600w"
  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 800px"
  fetchpriority="high"
  width="800"
  height="800"
  alt="Product Name — Front View"
>
```
For Shopify: `{{ image | image_url: width: 800 }}` with Liquid `image_tag` helper handles srcset automatically. For gallery images: 400w, 800w, 1200w breakpoints. For thumbnails: 100w, 200w. For zoom images: 1200w, 1600w, 2400w (zoom requires high resolution source).
- **Replication Status**: Technical specification standard. File size savings are empirically measurable.
- **Boundary Conditions**: srcset requires image variants to be generated and stored at multiple sizes — increases storage ~3×. Image CDNs (Cloudflare Images, Imgix, Cloudinary) generate variants on-demand from a single master, eliminating manual variant management. The `sizes` attribute must accurately reflect the CSS layout — incorrect sizes cause wrong image selection and negate the benefit.
- **Evidence Tier**: Gold (technical standard)

---

### Finding 5: Explicit Width and Height Attributes Prevent Cumulative Layout Shift (CLS)

- **Source**: Google Web Vitals. "Prevent layout shifts with CSS aspect-ratio." https://web.dev/cls/. Updated 2023. W3C HTML specification. https://html.spec.whatwg.org/
- **Methodology**: Chrome team analysis of CLS sources across top websites. Technical analysis of browser rendering behavior with and without explicit dimensions.
- **Key Finding**: Images without explicit `width` and `height` attributes cause Cumulative Layout Shift — the page layout reflowing as images load and claim their space. CLS thresholds: ≤0.1 Good; 0.1–0.25 Needs Improvement; >0.25 Poor. Google Core Web Vitals uses CLS as a ranking signal (since 2021). The fix is simple and has been a browser behavior since the 1990s: always specify `width` and `height` attributes matching the image's intrinsic dimensions (or the rendered CSS dimensions). Modern browsers use these to reserve space before the image loads.
- **E-Commerce Application**: Every `<img>` element should have `width` and `height` attributes. The values should match the image's natural dimensions or the rendered size (either works for space reservation). For aspect-ratio-constrained responsive images, also add CSS: `img { max-width: 100%; height: auto; }` — this allows the image to scale while maintaining the declared aspect ratio. For lazy-loaded images especially: space reservation prevents the page from "jumping" as offscreen images load into view. Audit using Chrome DevTools Performance panel: CLS contributions show as pink bars on the timeline.
- **Replication Status**: Technical standard confirmed by Chrome DevTools measurement and CrUX real-world data.
- **Boundary Conditions**: The width and height attributes must be accurate — specifying wrong dimensions causes incorrect aspect ratio reservation, which itself causes CLS when the image loads with correct dimensions. For dynamically sized images (container changes width based on viewport), use CSS `aspect-ratio` property instead of HTML attributes.
- **Evidence Tier**: Gold (technical standard)

---

### Finding 6: CDN with Edge Caching Reduces Latency for Distant Users

- **Source**: Cloudflare. "What is a CDN?" https://www.cloudflare.com/learning/cdn/what-is-a-cdn/. Cross-referenced with Google Web Vitals TTFB (Time to First Byte) guidance. https://web.dev/articles/ttfb Technical performance benchmarks from WebPageTest. https://www.webpagetest.org/
- **Methodology**: Technical analysis of network request latency with and without CDN edge caching. WebPageTest measurements from multiple global test locations.
- **Key Finding**: Serving images from a single origin server (typical for small ecommerce) results in full round-trip latency for each request — 100–300ms added to image load time for users geographically distant from the server. CDN edge nodes serve cached images from the closest geographic point of presence, reducing round-trip time by 40–60% for distant users. All major ecommerce platforms include CDN (Shopify CDN via Fastly, BigCommerce via Cloudflare, WooCommerce requires separate CDN setup). Correct cache headers: `Cache-Control: public, max-age=31536000, immutable` for versioned asset URLs.
- **E-Commerce Application**: Verify CDN is active by inspecting image URLs in browser DevTools Network panel — response headers should show `cf-ray` (Cloudflare), `x-served-by` (Fastly), or equivalent CDN headers. For Shopify: images served from `cdn.shopify.com` are automatically CDN-cached. For WooCommerce/custom: implement Cloudflare Images ($5/month), Cloudinary (free tier for <25K images), or Imgix ($25/month) — all provide CDN delivery + on-the-fly resizing + format conversion. Cache strategy: use content-addressed URLs (filename includes hash of content) to allow `immutable` cache headers — images never need revalidation for the same URL.
- **Replication Status**: Network latency physics is measurable and reproducible. CDN performance improvement is well-established.
- **Boundary Conditions**: CDN primarily helps global performance. If your customers are geographically concentrated (same city as your server), CDN impact is lower. Video content requires different CDN configuration (streaming CDN vs. standard object CDN for images). Large video files should use a video-specific CDN (Cloudflare Stream, Mux) rather than being served from a standard image CDN.
- **Evidence Tier**: Silver (mechanism is unimpeachable physics; the specific "40–60%" band is vendor-published by Cloudflare — the seller of the product — rather than from an independent peer-reviewed measurement; Silver is the honest tier for a vendor-cited percentage range)

---

### Finding 7: Image File Size Targets — Hero <100KB, Gallery <150KB, Thumbnails <25KB

- **Source**: Google Web Vitals "Optimize Images" guidance. https://web.dev/articles/optimize-lcp HTTP Archive Web Almanac 2024 image weight analysis. https://httparchive.org/reports/media Portent "Site Speed and Business Metrics" study (2023). https://portent.com/blog/analytics/research-site-speed-hurting-everyones-revenue.htm
- **Methodology**: Google technical guidance on image optimization targets. HTTP Archive measurement of real-world image sizes across top e-commerce sites. Portent analysis of 33,000+ pages correlating image weight with conversion rate.
- **Key Finding**: Target file sizes (WebP, optimized): Hero/LCP image: <100KB (200KB acceptable max); Gallery images: <150KB each (300KB acceptable max); Thumbnail strip: <25KB each (50KB acceptable max); Zoom-source images: <500KB (1MB absolute max). Total page image weight target: <1MB for PDPs (1.5MB acceptable; >2MB is poor practice). Portent found 4.42% conversion decrease per additional second of page load — excessive image weight is one of the primary causes of slow PDP load times.
- **E-Commerce Application**: Audit current image file sizes by downloading your product page and inspecting Network tab in DevTools. Filter by "Img" type. Sort by size (descending). Address any images >300KB immediately. Optimization tools: Squoosh (manual, high quality), Sharp (Node.js programmatic), ImageMagick (CLI), Shopify CDN (automatic format optimization, add `&quality=85` parameter). Compression command: `sharp input.jpg --quality 82 --webp --resize 800 -o output.webp`. After optimization: run WebPageTest to verify total image weight impact on LCP and total page size.
- **Replication Status**: Technical targets are informed by Google's guidance (authoritative). Portent conversion correlation is based on real-site analysis (n=33,000+; not a controlled experiment).
- **Boundary Conditions**: File size targets are for product display images. Zoom-source images (loaded only on explicit zoom request) can be larger since they're not loaded on page render. Animated WebP or GIF files are exempt — they're inherently larger.
- **Evidence Tier**: Silver

---

### Finding 8: Skeleton Screens vs. Spinners vs. Progressive Loading for Gallery Images

- **Source**: Nielsen Norman Group. "Skeleton Screens 101." https://www.nngroup.com/articles/skeleton-screens/. Published June 2023. Cross-referenced with Viget (2017) and Bill Chung (2020) — see page-performance-psychology.md Finding 2 for full analysis.
- **Methodology**: Multiple studies with contradictory results. NNGroup 2023 synthesis resolves the contradiction by use case.
- **Key Finding**: For product image gallery initial load: use background color placeholder matching approximate product photo tones (prevents white flash), paired with aspect-ratio-maintained container (prevents CLS). For gallery lazy-load below fold: CSS transition from placeholder to loaded image (opacity: 0 → 1, 200ms) provides smooth loading experience. Skeleton screens for gallery images (gray boxes with shimmer) are appropriate when load time is 1–3 seconds; for faster loads, plain placeholder color is sufficient and less distracting. For very slow connections (>3s gallery load): skeleton with shimmer animation.
- **E-Commerce Application**: Gallery loading implementation: (1) Set `background-color: #f5f5f5` (or brand-neutral) on all image containers before image loads; (2) Set `aspect-ratio: 1/1` (or appropriate ratio) on container to reserve space; (3) Add CSS transition on `img`: `opacity: 0; transition: opacity 200ms ease;`; (4) On image load event: `img.style.opacity = 1;`; (5) For skeleton shimmer effect (for slower loads): use CSS `@keyframes` gradient animation. This approach prevents both CLS (from space reservation) and the jarring "pop" of instant image appearance.
- **Replication Status**: NNGroup 2023 synthesis. Viget and Chung studies are contradictory — see page-performance-psychology.md for full analysis.
- **Boundary Conditions**: Skeleton benefit is implementation-quality dependent. A skeleton that doesn't match final content dimensions causes its own CLS when content loads. The debate between skeleton vs. spinner vs. blank is secondary to the core requirement of preventing CLS.
- **Evidence Tier**: Silver

---

### Finding 9: Third-Party Image Tools (Cloudflare Images, Cloudinary, Imgix) Automate Optimization at Scale

- **Source**: Technical comparison of image CDN services. Cloudflare Images documentation. https://developers.cloudflare.com/images/ Cloudinary feature documentation. https://cloudinary.com/documentation/image_transformations Imgix technical documentation. https://docs.imgix.com/
- **Methodology**: Technical feature comparison and pricing analysis. Industry practitioner benchmarks.
- **Key Finding**: Image CDNs provide: automatic format negotiation (AVIF/WebP/JPEG based on Accept header), on-the-fly resizing (eliminates manual srcset variant management), CDN edge delivery, and transformation APIs. Pricing comparison (2024 approximate): Cloudflare Images: $5/month for 100K images stored, unlimited delivery; Cloudinary: free tier (25K transformations/month), $89/month for medium volume; Imgix: $25/month for 10GB bandwidth. Shopify stores: Shopify CDN already handles format negotiation and CDN delivery — additional image CDN is usually not needed. WooCommerce/custom platforms: significant benefit from adding an image CDN.
- **E-Commerce Application**: Decision framework: (1) Shopify → use Shopify CDN + Liquid image helpers, no additional image CDN needed; (2) BigCommerce → built-in CDN handles most requirements; (3) WooCommerce with <500 products → Cloudflare Images or free Cloudinary tier; (4) Custom platform or large WooCommerce (500+ products) → Cloudinary or Imgix for transformation pipeline; (5) High-traffic stores (>1M pageviews/month) → Cloudflare Images for consistent performance at scale. For any platform: test actual image delivery performance using WebPageTest from multiple global locations.
- **Replication Status**: Technical feature documentation from authoritative service providers. Pricing is current as of April 2026 (verify current pricing before budget decisions).
- **Boundary Conditions**: Adding an image CDN in front of Shopify or other platforms that already have CDN creates potential conflicts — test carefully for cache invalidation behavior. Image transformation quality can vary by provider for edge cases (image with transparency, unusual aspect ratios).
- **Evidence Tier**: Silver (technical comparison)

---

### Finding 10: Video Poster Frames Are Required to Prevent LCP and Layout Issues

- **Source**: Google Web Vitals. Video and LCP guidance. https://web.dev/articles/lcp#what-elements-are-considered Cross-referenced with Baymard Institute product page video research. https://baymard.com/research/product-page
- **Methodology**: Technical analysis of video element rendering behavior and its interaction with LCP metrics. Chrome DevTools LCP element identification.
- **Key Finding**: `<video>` elements without a `poster` attribute render as a black box until video metadata loads. If a video is above the fold (e.g., in a gallery position 1–2), the black box becomes the LCP element — and video LCP is measured at poster frame load time. Without a poster, the browser must wait for video metadata before rendering any placeholder — increasing LCP. Additionally, a black box above the fold during page load creates a poor first impression that drives immediate scroll-past behavior.
- **E-Commerce Application**: All `<video>` elements must have a `poster` attribute: `<video poster="product-video-thumb.jpg" controls playsinline preload="metadata">`. The poster image should: (1) Show the most compelling frame from the video (not the first frame, which is often a blank or transition); (2) Be optimized to <50KB (it's loaded eagerly like any above-fold image); (3) Match the video's aspect ratio exactly; (4) Include an accessible play button visual cue overlaid via CSS (not embedded in poster image). For video in gallery position 2+: treat the poster like any gallery image — lazy load the video but eager-load the poster.
- **Replication Status**: Technical standard from Google Web Vitals documentation.
- **Boundary Conditions**: `preload="metadata"` loads only duration and dimensions (not the video body) — acceptable for performance. `preload="none"` requires an explicit user interaction before loading begins — appropriate for bandwidth-sensitive contexts. `preload="auto"` begins loading video body immediately — avoid for non-critical PDPs.
- **Evidence Tier**: Gold (technical standard)

---

### Finding 11: `sizes` Attribute Accuracy Is Load-Bearing for srcset to Work Correctly

- **Source**: HTML Living Standard, `sizes` attribute specification. web.dev, "Serve responsive images," https://web.dev/articles/serve-responsive-images. Verified 2026-04-21: web.dev confirms `sizes` drives browser srcset candidate selection; HTML spec is authoritative.
- **Methodology**: Technical specification analysis. Common pitfall identified across real-world implementations where blanket `sizes="100vw"` causes browsers to fetch larger images than necessary.
- **Key Finding**: The `srcset` attribute alone does not tell the browser how large an image will appear in CSS layout. The `sizes` attribute completes the picture — it defines the image's rendered width at each breakpoint, enabling the browser to select the correct srcset candidate before layout is computed. **The most common mistake** is using `sizes="100vw"` for all images — this tells the browser the image spans the full viewport width, causing it to fetch the largest srcset candidate on wide screens even when the image is in a 33%-width column. Incorrect `sizes` negates the bandwidth savings of srcset entirely.
- **E-Commerce Application**: Every `srcset` implementation must have an accurate `sizes` attribute. For a full-width hero image: `sizes="100vw"` is correct. For a product card in a 3-column grid: `sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"`. For a thumbnail strip: `sizes="(max-width: 600px) 25vw, 100px"`. Test using Chrome DevTools Network panel: the image variant selected should match the rendered CSS width of the element.
- **Replication Status**: Technical specification standard. The pitfall (blanket 100vw) is real and common in production implementations.
- **Boundary Conditions**: Image CDNs (Cloudinary, Cloudflare Images, Imgix) generate srcset variants on-demand and some provide responsive image helpers that compute `sizes` automatically. Verify the computed `sizes` values are accurate, not just defaulting to 100vw.
- **Evidence Tier**: Gold (HTML Living Standard; web.dev verified)

---

### Finding 12: `fetchpriority` Is Baseline-Supported — Ship Without Fallback Guards

- **Source**: web.dev, "Optimizing resource loading with the Fetch Priority API," https://web.dev/articles/fetch-priority. Verified 2026-04-21: Chrome 102+, Edge 102+, Firefox 132+, Safari 17.2+ confirmed.
- **Methodology**: Browser compatibility documentation confirmed against web.dev/articles/fetch-priority and Baseline browser support data (2026-04-21).
- **Key Finding**: `fetchpriority="high"` is now Baseline-supported across all major browsers: Chrome 102+ (May 2022), Edge 102+, Firefox 132+ (October 2024), Safari 17.2+ (December 2023). This means the attribute is safe to ship in production without JavaScript fallback guards or feature-detection wrappers. When `fetchpriority="high"` is present on an unsupported browser, the attribute is silently ignored — no errors, no fallback needed. The attribute has been the recommended implementation for hero/LCP images since Finding 1 in this file, and is now fully safe to deploy universally.
- **E-Commerce Application**: Remove any JavaScript-based fallback detection you may have added when `fetchpriority` was experimental. The implementation is now a clean HTML attribute: `<img src="hero.webp" fetchpriority="high" width="800" height="800" alt="...">`. If you previously used `<link rel="preload" fetchpriority="high">` as a polyfill pattern, it remains valid and complementary — but the `img` attribute alone is sufficient on modern browsers.
- **Replication Status**: Browser support is factual (tracked by Can I Use and MDN browser compat data).
- **Boundary Conditions**: Chrome 102+ means Chrome 101 and earlier do not support the attribute. Chrome 101 was released April 2022 and accounts for negligible traffic share in 2026. Safari 17.2 is the Safari floor — Safari 16.x does not support `fetchpriority`. Safari 16.x traffic has declined substantially but may be non-negligible on older iOS devices. For stores with significant iOS 15 traffic, the attribute is still worth using (it's ignored, not broken), but the graceful degradation means older Safari users get the default browser priority queue.
- **Evidence Tier**: Gold (browser specification standard; verified 2026-04-21)

---

## Methodological Notes

- Performance research has a stronger evidence base than most ecommerce UX research because it relies on measured technical metrics (LCP, CLS, bytes transferred) rather than self-reported behavior. Google's CrUX database and Lighthouse are reproducible measurement tools.
- The Deloitte/Google "Milliseconds Make Millions" study (2020) is the most cited production performance study and remains the benchmark — see page-performance-psychology.md Finding 1 for the full citation.
- Image CDN pricing and feature comparisons require verification at time of implementation — this is a rapidly evolving market.
- AVIF support has expanded significantly since 2022 — verify current Can I Use data (caniuse.com/avif) before implementation decisions.

---

## Sources Consulted

1. Google Web Vitals. "Optimize Largest Contentful Paint." https://web.dev/articles/optimize-lcp
2. Google Web Vitals. "Optimize Images." https://web.dev/uses-responsive-images/
3. Google Web Vitals. "Prevent layout shifts." https://web.dev/cls/
4. Google/Deloitte. "Milliseconds Make Millions." https://web.dev/case-studies/milliseconds-make-millions (also: https://www.deloitte.com/ie/en/services/consulting/research/milliseconds-make-millions.html)
5. HTTP Archive. "Web Almanac 2024 — Media." https://almanac.httparchive.org/en/2024/media
6. Portent. "Site Speed and Business Metrics." https://www.portent.com/blog/analytics/research-site-speed-hurting-everyones-revenue.htm
7. Cloudflare Images. https://www.cloudflare.com/developer-platform/cloudflare-images/
8. Cloudinary. https://cloudinary.com/
9. Imgix. https://imgix.com/
10. Can I Use. AVIF support. https://caniuse.com/avif
11. Can I Use. WebP support. https://caniuse.com/webp
12. web.dev. "Serve responsive images." https://web.dev/articles/serve-responsive-images
13. web.dev. "Optimizing resource loading with the Fetch Priority API." https://web.dev/articles/fetch-priority
