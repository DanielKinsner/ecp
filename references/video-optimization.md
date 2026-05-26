<!-- RESEARCH_DATE: 2026-04-21 -->
<!-- RECONCILED: 2026-04-21 — Run-A + Run-B. F2 Wyzowl URL/numbers updated (A). F5 Baymard blog URL added (both). F8 EAA + UK Equality Act added (B). F10 VideoObject required-vs-recommended fields corrected (B; confirmed per Known). F11 WCAG 1.2.5 audio description added (B). F12 VP9/AV1 codec added (B). F13 AI-generated video legal cross-ref added (B). Total findings: 13. -->
# Product Video Optimization: Research Findings

**Research Date**: April 21, 2026 (audit update of April 2, 2026 research)
**Domain**: Product Media — Video on Product Detail Pages
**Total Findings**: 13
**Methodology Note**: Video conversion statistics in ecommerce frequently originate from vendors (Invideo, Wyzowl, Invodo) with commercial interest in promoting video adoption. These figures are noted where applicable. Baymard and NNGroup findings on autoplay and placement represent the stronger evidence base. The ECP's eye-tracking-and-scan-patterns.md (Finding 25) addresses video placement within gallery — this file focuses on video conversion impact, format, length, and delivery optimization.

---

## Cross-Reference Notice

**ECP Reference Overlap**:
- page-performance-psychology.md covers the performance impact of video loading on Core Web Vitals — see that file for LCP/speed findings
- eye-tracking-and-scan-patterns.md Finding 25 covers video position within gallery
- video-integration.md Findings 2, 6, 7, 8, 11 closely parallel findings here; this file emphasizes PDP-specific optimization (encoding, hosting, accessibility, CWV), video-integration.md emphasizes integration patterns (gallery, landing page, thumbnail design)
- video-integration.md Finding 15 covers AI-generated video legal exposure (primary location); Finding 13 here covers technical disclosure implementation
- accessibility.md is the canonical ECP accessibility reference; WCAG captions requirement (Finding 8 here) is cross-referenced there

This file covers: video conversion impact, autoplay behavior, optimal length, video types, mobile delivery, format/encoding, accessibility, and AI-generated video technical disclosure implementation.

---

## Summary

### Top 3 Most Impactful Findings

1. **Finding 1 (37% Add-to-Cart Lift)**: Product pages with video see 37% more add-to-cart conversions than pages without — making video among the highest single-element conversion levers available to ecommerce teams, particularly for complex or high-consideration products.
2. **Finding 3 (Autoplay with Sound Causes Abandonment)**: Autoplay with audio is the most universally negatively-received media behavior in ecommerce. It overrides user agency, burns mobile data, and has near-zero tolerance among users. Muted autoplay for short clips (<5s) is the only acceptable autoplay form.
3. **Finding 4 (PDP Video Length: 30–90 Seconds)**: Attention drop-off on product detail page videos is severe. Videos longer than 90 seconds have dramatically reduced completion rates. If product story requires more than 90 seconds, split into multiple focused clips rather than extending a single video.

---

## Findings

### Finding 1: Product Pages with Video See 37% More Add-to-Cart Conversions

- **Source**: Invesp. "E-Commerce Product Videos: How Videos on Product Pages Can Increase Conversion Rate." https://www.invespcro.com/blog/e-commerce-product-videos/. Published April 2018. Cross-referenced with Wyzowl "State of Video Marketing" annual reports.
- **Methodology**: Industry compilation from Invodo (vendor) and Invesp analysis. The 37% add-to-cart figure is widely cited; original Invodo data is from merchant client aggregate. Wyzowl annual surveys: 2024 n=967 online video consumers and marketing professionals.
- **Key Finding**: Product pages with embedded video see 37% more add-to-cart conversions compared to pages without video (Invesp/Invodo). 52% of consumers say watching product videos makes them more confident in purchase decisions (Wyzowl 2024). Visitors who view product videos are 85% more likely to purchase (Wyzowl 2022). 73% of consumers are more likely to purchase after watching a product explainer video (Wyzowl 2023).
- **E-Commerce Application**: Prioritize video production for: (1) complex products requiring demonstration (assembly, features, use-case), (2) high-consideration purchases ($100+) where confidence is the key conversion lever, (3) products with tactile qualities difficult to convey in stills (fabric drape, material weight, mechanical action). Video ROI is lowest for simple commodity products where visual complexity is low.
- **Replication Status**: The 37% figure is from a single vendor-aggregated dataset. Directionally consistent with broader Wyzowl survey data, but neither study is a controlled experiment. Treat as directional with high plausibility rather than precise.
- **Boundary Conditions**: Effect size likely depends heavily on product complexity and purchase consideration level. A high-end technical product with a clear demo video will see much larger lift than a simple consumable with a lifestyle video. These statistics are average across diverse merchant types.
- **Evidence Tier**: Bronze (vendor-origin data; directional plausibility is strong)

---

### Finding 2: Survey-Reported Video Confidence Effects (Wyzowl) — Treat as Directional

- **Source**: Wyzowl. "Video Marketing Statistics." https://wyzowl.com/video-marketing-statistics/ (current State of Video report; prior editions at archived URLs). 2024/2025 editions.
- **Methodology**: Annual survey of online video consumers and marketing professionals. 2025 edition (most recent): 266 respondents in late 2025. Prior editions reported larger samples (~1,000 respondents). Self-reported behavior data.
- **Key Finding**: Wyzowl's annual surveys consistently report that a majority of consumers say videos affect their purchase confidence and that most viewers watch through more than half of product videos. 2024 edition reported 52% of consumers more confident after video and 65% watching more than half; 2025 edition reports 85% convinced to buy by video and 96% having watched an explainer video. The specific numbers shift year to year with sample composition. First 5 seconds are critical — completion rate drops dramatically after initial engagement is lost.
- **E-Commerce Application**: Front-load the most important product information in the first 5–10 seconds. Do not use slow intro sequences or brand animations before showing the product. Structure: product in use within first 3 seconds → key benefit demonstration → CTA at end. Videos with front-loaded product demos retain more viewers and drive higher completion rates.
- **Replication Status**: Annual survey with consistent directional findings year-over-year. Self-reported behavior systematically overstates actual engagement — treat percentages as indicative rather than precise.
- **Boundary Conditions**: Survey methodology (self-reported behavior) inflates engagement figures. Actual video completion rates from analytics typically run 20–40% lower than self-reported. Mobile users have significantly lower completion rates than desktop viewers.
- **Evidence Tier**: Bronze (self-reported survey data)
- **Audit Note (2026-04-21)**: Prior version cited specific percentages (52/65/73) against `wyzowl.com/state-of-video-marketing/`; that URL now redirects to Wyzowl's corporate services page, and current `wyzowl.com/video-marketing-statistics/` reports different headline figures (sample size smaller in 2025). Wording updated to explain the year-to-year variance; specific numbers annotated with their edition.

---

### Finding 3: Autoplay with Audio Causes Immediate Abandonment — Muted Autoplay Acceptable for Clips ≤5 Seconds

- **Source**: Nielsen Norman Group. "Video Usability." https://www.nngroup.com/articles/video-usability/. Cross-referenced with NN/g "Five User Requirements for Online Ads" (https://www.nngroup.com/articles/user-requirements-online-ads/) on autoplay disruption, Baymard Institute product page research, and browser vendor autoplay policy documentation (Chrome, Safari — https://webkit.org/blog/6784/new-video-policies-for-ios/, Firefox).
- **Methodology**: NNGroup usability research on autoplay media behavior; Baymard qualitative testing of PDP media interactions; technical review of browser autoplay policies.
- **Key Finding**: Autoplay video with audio is among the most universally negatively received behaviors on web pages — users experience it as intrusive, disruptive to their browsing context, and as a trust signal violation (exploitative or desperate). Modern browsers (Chrome since 2018, Safari since 2017, Firefox since 2018) block audio autoplay by default, making audio autoplay technically non-functional in most browsers anyway. Muted autoplay is acceptable and effective specifically for: product spin/rotation loops ≤5 seconds, silent lifestyle atmosphere clips ≤5 seconds.
- **E-Commerce Application**: Never autoplay video with audio. For demo/explainer/how-to videos: always click-to-play with a compelling thumbnail poster frame. For short silent loops (product 360, ambient lifestyle): muted autoplay is acceptable with `autoplay muted loop playsinline` attributes. Provide a visible play/pause control even for muted autoloop. For all click-to-play videos: show a custom thumbnail (not black frame) with a large, accessible play button overlay.
- **Replication Status**: Consistently replicated across NNGroup and Baymard research. Browser vendor policies (Chrome, Safari, Firefox) codify this finding into technical constraints, making it non-negotiable regardless of UX preference.
- **Boundary Conditions**: Muted autoplay for very short loops (≤5s) is generally well-tolerated, especially when it shows product motion (fabric movement, product rotation). Autoplay of longer clips (>5s) is poorly received even when muted — users feel they're being shown something without consent.
- **Evidence Tier**: Gold

---

### Finding 4: Optimal PDP Video Length Is 30–90 Seconds; Segment Longer Content Into Clips

- **Source**: Wyzowl "State of Video Marketing" (2023/2024). https://www.wyzowl.com/ HubSpot "Video Marketing Statistics" (2023). https://www.hubspot.com/ Baymard Institute product page video research. https://baymard.com/research/product-page
- **Methodology**: Wyzowl annual survey data on optimal video length by context. HubSpot analytics across customer video libraries. Baymard usability observation of video engagement on product pages.
- **Key Finding**: For product detail page demo videos: 30–60 seconds is optimal; 90 seconds is the outer limit before significant completion rate degradation. How-to/tutorial content can extend to 1–3 minutes because users seek instructional completeness. Lifestyle/brand content: 15–30 seconds. Attention drops significantly after the first 30 seconds for product demos specifically, as users either have the information they need or have decided it's not what they wanted.
- **E-Commerce Application**: For PDPs: target 30–60 second product demos. If full product story requires more than 90 seconds, create a primary 60-second overview video + supplementary clips (tutorial, unboxing, comparison). Label each clip clearly so users can select the type they need. Place demo video first; tutorials in a "How it Works" section further down page.
- **Replication Status**: Industry surveys are consistent on length-engagement relationship. The specific thresholds are estimates, not experimentally validated — actual optimal length is product-specific.
- **Boundary Conditions**: B2B products with complex technical demonstrations may justify longer videos (3–5 minutes) for professional buyers in research mode. High-consideration luxury products may benefit from longer storytelling. Mobile context shifts toward shorter (≤30s) due to attention constraints and data costs.
- **Evidence Tier**: Silver

---

### Finding 5: Video Placement in Gallery (Position 2–4) Outperforms Dedicated Section or Hero Position

- **Source**: Baymard Institute. Product page gallery video placement research. https://baymard.com/blog/embedding-product-page-videos. Eye-tracking-and-scan-patterns.md (ECP) Finding 25. Cross-referenced with Baymard gallery UX research. See also video-integration.md Finding 8 which phrases this as "position 2–3."
- **Methodology**: Usability testing examining user discovery and engagement with video placed in different positions on product pages.
- **Key Finding**: Video integrated into the product image gallery (typically in position 2, 3, or 4, after the hero packshot) achieves higher user discovery and engagement than video placed in a dedicated separate section below the fold. Users expect the gallery to contain all visual media for the product. A thumbnail with a visible play icon signals video presence naturally within the gallery browsing flow.
- **E-Commerce Application**: Integrate demo video as a gallery item (typically position 2 for hero video, position 3–4 for supporting content). Use a video poster thumbnail with a centered play button overlay for the gallery thumbnail. When the video thumbnail is clicked, play inline within the gallery frame (not redirect to external player). For tutorials and how-to content that exceeds gallery context: use a dedicated section with appropriate heading; link from gallery "See full tutorial" if relevant.
- **Replication Status**: Consistent across Baymard research rounds. Note this overlaps with gallery-ux.md findings — the gallery UX file covers the mechanics; this file covers video-specific placement rationale.
- **Boundary Conditions**: For products where video is the primary differentiator (interactive/software products, musical instruments), hero position video (first gallery item) may be appropriate. YouTube-hosted video embeds work for tutorial sections but should not be used in the primary gallery due to loading performance impact.
- **Evidence Tier**: Gold

---

### Finding 6: Mobile Video Must Use playsinline and preload="metadata"; File Size <5MB for PDPs

- **Source**: Google Web Vitals. "Optimize Largest Contentful Paint." https://web.dev/articles/optimize-lcp. Cross-referenced with Baymard mobile product page research and Apple WebKit documentation — https://webkit.org/blog/6784/new-video-policies-for-ios/.
- **Methodology**: Technical analysis of mobile video loading behavior, combined with Baymard mobile usability testing of product page video interactions.
- **Key Finding**: iOS Safari without the `playsinline` attribute forces video into fullscreen mode on play — which is disorienting on a product page and prevents users from seeing other page content. `preload="metadata"` (not `preload="auto"`) fetches video duration and dimensions without downloading the video body, enabling poster frame display without bandwidth cost. Mobile product page videos must be <5MB to load acceptably on 4G connections; <2MB targets 3G-acceptable performance.
- **E-Commerce Application**: All mobile-targeted videos: `<video poster="thumb.jpg" controls playsinline preload="metadata">`. For mobile, use H.264 MP4 as primary (universal iOS/Android support). Target bitrate: 1.5–2.5 Mbps for 720p mobile video. Offer 720p as primary mobile resolution (1080p is wasteful on phone screens). Consider adaptive streaming (HLS/DASH via a CDN like Cloudflare Stream, Mux, or Vimeo) for videos >5MB.
- **Replication Status**: Technical requirements; confirmed by platform documentation (Apple WebKit, Android Chrome).
- **Boundary Conditions**: Self-hosting video is adequate for small catalogs (<100 SKUs with video). Larger catalogs benefit from a video CDN for adaptive bitrate streaming, geographic distribution, and transcoding. YouTube embeds are not recommended for PDP primary video due to loading overhead and cross-origin latency.
- **Evidence Tier**: Gold (technical standard)

---

### Finding 7: Video Type Should Match Product Complexity and Purchase Decision Type

- **Source**: Baymard Institute. Product page content type research. https://baymard.com/research/product-page Wyzowl "Types of Video Marketing" (2023). https://www.wyzowl.com/
- **Methodology**: Usability testing observing user video engagement patterns by product category and purchase intent type.
- **Key Finding**: Video type effectiveness is highly product-dependent. Demo videos (product in action, features shown): most effective for electronics, tools, appliances — anything where "how does this work?" is the key question. Lifestyle videos (product in aspirational context): most effective for apparel, home decor, fitness gear — where "how will this fit my life?" drives purchase. How-to videos: most effective for complex products requiring assembly/setup (furniture, tools, electronics). 360/spin videos: effective for shoes, bags, jewelry — products with complex geometry. Lifestyle-only videos on technical products and demo-only videos on emotional/lifestyle products both underperform.
- **E-Commerce Application**: Map video type to product category: Electronics → Demo primary, How-to secondary. Apparel → Lifestyle primary, fabric-in-motion secondary. Furniture → Lifestyle (in-room) primary, assembly secondary. Tools → Demo + How-to combined. Jewelry → 360/spin primary, on-body lifestyle secondary. Beauty → Application/tutorial primary, before/after secondary (with care for substantiation requirements).
- **Replication Status**: Directionally consistent across Wyzowl survey data and Baymard usability observations. Not isolated by controlled experiment.
- **Boundary Conditions**: Video type effectiveness also depends on production quality — a poorly produced demo may underperform a well-produced lifestyle video in any category. Some products (outdoor gear, sporting equipment) benefit from multiple types simultaneously.
- **Evidence Tier**: Silver

---

### Finding 8: Video Captions Are Required for Accessibility — WCAG 1.2.2 Level A

- **Source**: W3C Web Content Accessibility Guidelines 2.2. https://www.w3.org/TR/WCAG22/ (Success Criterion 1.2.2: Captions — Pre-recorded, **Level A**). Cross-referenced with European Accessibility Act (Directive (EU) 2019/882), effective 28 June 2025 for ecommerce services in EU member states; UK Equality Act 2010. Facebook/Meta video analytics data on captioned vs. uncaptioned video engagement.
- **Methodology**: WCAG is a normative technical standard (W3C, October 2023). EAA transposed into EU member-state national law. Facebook video analytics data (published in DigiDay) showed captioned videos had 12% higher view time.
- **Key Finding**: WCAG 2.2 Success Criterion 1.2.2 (Level A) requires captions for all pre-recorded video with audio content. WCAG verbatim: "Captions are provided for all prerecorded audio content in synchronized media." This is a legal requirement in jurisdictions enforcing WCAG for ecommerce (US ADA Title III interpretation; EU EAA since 28 June 2025; UK Equality Act). Beyond compliance: 85% of Facebook video is watched without sound (Facebook internal data, 2016); captions serve muted-autoplay and sound-off contexts, improving engagement for the substantial portion of users who watch video muted.
- **E-Commerce Application**: Add WebVTT captions (`.vtt`) to all product videos with spoken content: `<track kind="captions" src="captions.vtt" srclang="en" label="English" default>`. For how-to content: also provide a text transcript below the video (accessibility + SEO benefit). For muted autoplay short clips: captions less critical but still recommended. Tools: Rev.com, Otter.ai, or YouTube auto-captions as a starting point (always review for accuracy). EU-facing merchants: EAA compliance required since 28 June 2025.
- **Replication Status**: WCAG 2.2 and EAA are normative standards. The 85% muted-watching figure is widely reported from Facebook's 2016 data; current muted rates on product pages are not separately studied.
- **Boundary Conditions**: Caption requirement applies when video has meaningful audio content. A muted product spin with no audio is exempt. US ADA Title III private ecommerce requirements are determined by court interpretation — consult legal counsel for specific compliance questions.
- **Evidence Tier**: Gold (normative standard)

---

### Finding 9: Self-Hosted vs. YouTube — Choose Based on Control, Not Just Bandwidth Cost

- **Source**: Technical analysis. Google Search Console documentation on video indexing. https://support.google.com/webmasters/answer/9495631?hl=en Baymard Institute performance research. https://baymard.com/research/product-page
- **Methodology**: Technical comparison of hosting options with reference to page performance impact and SEO indexation patterns.
- **Key Finding**: YouTube hosting offers free bandwidth, automatic transcoding, and YouTube search visibility. But YouTube embeds add ~200ms+ loading overhead from cross-origin requests, display YouTube branding, and can recommend competitor videos after playback. Self-hosted video provides full control, no competitive recommendations, and faster loading when served from a proper CDN, but requires transcoding infrastructure and storage cost. For PDPs: self-hosted (or dedicated video CDN like Mux, Cloudflare Stream, Vimeo Pro) outperforms YouTube embeds for page performance. For tutorial content intended for wider discovery: YouTube is appropriate as a primary distribution channel with embed on site as secondary.
- **E-Commerce Application**: For product page primary video: use self-hosted or dedicated video CDN. For tutorial/educational content: dual-publish (YouTube for discovery + self-hosted embed on site). Add VideoObject schema markup to all self-hosted product videos for Google indexation (see Finding 10).
- **Replication Status**: Technical finding confirmed by Google documentation and performance measurement tools.
- **Boundary Conditions**: Small stores with limited SKU video content may find YouTube's free tier sufficient. Stores with significant international traffic need a CDN regardless of hosting choice. Vimeo Pro and Mux are good middle-ground options: better control than YouTube, less infrastructure than full self-hosting.
- **Evidence Tier**: Silver

---

### Finding 10: Video Schema Markup Enables Google Rich Results and Increases Click-Through Rate

<!-- CORRECTED 2026-04-21 (Run-B): Google Developers docs (updated 2026-02-13) classify description/duration/contentUrl/embedUrl as RECOMMENDED, not required. Only name, thumbnailUrl, uploadDate are required. Prior version listed all six fields as required — corrected below. -->

- **Source**: Google Developers. "Video (VideoObject, Clip, BroadcastEvent) structured data." https://developers.google.com/search/docs/appearance/structured-data/video. Last updated 2026-02-13. Cross-referenced with Baymard SEO research and Search Console case studies from Merkle and Ahrefs.
- **Methodology**: Google documentation for VideoObject schema requirements. SEO case studies from Merkle and Ahrefs on video rich result impact.
- **Key Finding**: VideoObject schema markup enables video carousels and video preview thumbnails in Google search results. Pages with valid VideoObject schema receive video-enriched SERP listings with ~25–40% higher click-through rates vs. standard listings (Ahrefs case study analysis; directional).
  - **Required fields**: `name`, `thumbnailUrl`, `uploadDate`.
  - **Recommended fields** (strongly advised for rich result eligibility): `description`, `duration`, `contentUrl` or `embedUrl`, `expires`, `hasPart`, `interactionStatistic`, `publication`, `regionsAllowed`.
  - Optional but valuable: `transcript`.
- **E-Commerce Application**: Add VideoObject JSON-LD to all product pages with hosted video. Duration format: ISO 8601 (`PT1M30S` = 1 minute 30 seconds). Thumbnail must be ≥160px wide. ContentUrl must be a direct link to the video file (not a page URL). For YouTube-hosted video, use `embedUrl` with YouTube embed URL. Test with Google's Rich Results Test before deploying at scale.
- **Replication Status**: Technical standard confirmed by Google documentation. CTR lift estimates vary by study; directional improvement is well-established.
- **Boundary Conditions**: Google must be able to crawl and index the video thumbnail and content URL. Paywalled or login-gated videos may not be indexed. Schema errors (invalid duration format, missing required fields) prevent rich result eligibility.
- **Evidence Tier**: Gold (technical standard + consistent practitioner evidence)

---

### Finding 11: Audio Description for Pre-Recorded Video — WCAG 1.2.5 Level AA

<!-- Run-B Addition: Complements Finding 8 (WCAG 1.2.2 Level A captions) with the Level AA audio description requirement. -->

- **Source**: W3C WCAG 2.2 Success Criterion 1.2.5 Audio Description (Prerecorded), Level AA. https://www.w3.org/WAI/WCAG22/Understanding/audio-description-prerecorded. Cross-referenced with WCAG SC 1.2.3 (Level A baseline).
- **Methodology**: W3C normative standard.
- **Key Finding**: SC 1.2.5 (Level AA) requires audio description for all pre-recorded video content in synchronized media, except when the media is a media alternative for text and is clearly labeled as such. Captions (1.2.2, Level A) ensure deaf/hard-of-hearing users can access audio; audio description ensures blind/low-vision users can access visual-only content — e.g., a product demo where narration says "press this button" without describing what or where the button is. SC 1.2.3 (Level A) allows a full text alternative as a substitute; 1.2.5 (Level AA) requires audio description specifically.
- **E-Commerce Application**: For product demos with significant visual-only content (unnarrated action, on-screen text, UI demonstrations): add an audio description track. Two approaches: (a) a narrated version of the video with extended description baked in; (b) a WebVTT `kind="descriptions"` track synced to gaps in the primary audio. For videos where the narration already fully describes what is shown ("here I'm pressing the red power button on the left side"), primary audio itself serves as description — no separate track required. EU EAA (effective 28 June 2025) makes WCAG 2.1 AA the de facto baseline for EU-facing ecommerce, including this requirement.
- **Replication Status**: Normative W3C standard.
- **Boundary Conditions**: Muted autoplay loops with no spoken content are exempt. Live video is covered by different criteria (WCAG SC 1.2.4).
- **Evidence Tier**: Gold (normative standard)

---

### Finding 12: VP9 and AV1 Codecs — Modern Compression Alternatives to H.264

<!-- Run-B Addition: Technical complement to Finding 6. VP9 and AV1 produce 30–50% smaller files at same perceptual quality. -->

- **Source**: Google Media documentation (web.dev). MDN Web Docs video codec guide. https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Video_codecs. Alliance for Open Media (AV1 spec).
- **Methodology**: Technical codec specifications and bitrate comparison benchmarks published by browser vendors and the Alliance for Open Media.
- **Key Finding**: Modern codecs outperform H.264 on file size at equivalent perceptual quality. VP9 (widespread support since 2016): ~30% smaller than H.264 at same quality. AV1 (royalty-free, near-universal decode support as of 2025): ~50% smaller than H.264 / ~30% smaller than VP9 at same quality. Trade-off: AV1 encoding is CPU-intensive server-side; decoding is well-supported on desktop and modern mobile. H.264 remains the safest universal baseline for older devices.
- **E-Commerce Application**: Modern video workflow: encode each product video in AV1 (primary) + H.264 (fallback). Serve via `<source>` elements in priority order: `<video><source src="video.av1.mp4" type='video/mp4; codecs="av01"'><source src="video.h264.mp4" type='video/mp4; codecs="avc1"'></video>`. Use a video hosting service (Mux, Cloudflare Stream) for automatic codec negotiation. For non-critical loops (hero atmosphere): AV1 alone with graceful degradation on legacy clients.
- **Replication Status**: Codec specs are standardized. Bitrate savings vary by content type (motion-heavy content sees larger relative savings).
- **Boundary Conditions**: AV1 server-side encoding is slow without hardware acceleration. Legacy browser/device support (pre-2020 iOS/Android): fallback to H.264 required.
- **Evidence Tier**: Silver

---

### Finding 13: AI-Generated Product Video — Technical Disclosure Implementation

<!-- Run-B Addition: Technical-implementation angle for the legal finding in video-integration.md Finding 15. -->

- **Source**: US FTC Operation AI Comply (Sep 2024) — https://www.ftc.gov/business-guidance/blog/2024/09/operation-ai-comply-continuing-crackdown-overpromises-ai-related-lies. EU AI Act Article 50 — https://artificialintelligenceact.eu/article/50/. C2PA (Coalition for Content Provenance and Authenticity) technical standard v1.3 — https://c2pa.org/. Cross-reference: video-integration.md Finding 15 (primary legal analysis).
- **Methodology**: Primary regulatory sources (FTC, EU AI Act) + C2PA technical specification for cryptographic content provenance.
- **Key Finding**: When product video is AI-generated, merchants need both consumer-facing disclosure (satisfies FTC Section 5 reasonable-consumer standard; satisfies EU AI Act Article 50 deployer obligation) and machine-readable labeling (satisfies EU AI Act Article 50 provider obligation for synthetic content, enforcement begins August 2, 2026). Technical implementation options: (1) C2PA content credentials — cryptographically signed metadata attached to the video file describing AI generation, supported by Adobe, Microsoft, OpenAI, and Google starting 2024–2025; (2) visible on-screen disclosure — text overlay or badge on video player ("AI-generated content"); (3) page-level disclosure — prominent text adjacent to the video thumbnail ("This video was created using AI"); (4) schema.org machine-readable disclosure in structured data.
- **E-Commerce Application**: For any AI-generated product video: (a) apply C2PA provenance metadata at export time — most current AI video generation tools support this natively; (b) add visible on-screen disclosure in the first 2 seconds or as a persistent corner badge; (c) add page-level text disclosure adjacent to the video player; (d) if serving EU customers, verify C2PA metadata survives CDN re-encoding — some re-encoders strip metadata, requiring a CDN that preserves C2PA. See video-integration.md Finding 15 for the full legal framework and color-accuracy.md Finding 13 for parallel AI image-enhancement exposure.
- **Replication Status**: Primary regulatory documents + C2PA v1.3 technical specification.
- **Boundary Conditions**: FTC Section 5 applies to US commerce. EU AI Act Article 50 enforcement begins August 2, 2026. C2PA is the leading but not the only provenance standard.
- **Evidence Tier**: Gold (primary regulatory + technical standard)

---

## Methodological Notes

- Video marketing statistics are among the most vendor-polluted data in ecommerce. Invodo, Wyzowl, and Invesp all have commercial interest in promoting video adoption. Treat conversion lift figures as directionally plausible but not precise.
- Baymard and NNGroup findings on autoplay and placement are the strongest evidence in this file, backed by controlled usability testing with observable user behavior.
- WCAG 2.2 (October 2023) represents the current normative accessibility standard. US ADA Title III private ecommerce requirements are determined by court interpretation — consult legal counsel for specific compliance questions. EU EAA (effective 28 June 2025) makes WCAG 2.1 AA the de facto baseline for EU-facing ecommerce services.
- Browser autoplay policies (Google Chrome Autoplay Policy, Apple WebKit Autoplay) provide technical constraints that make audio autoplay a non-issue in modern browsers regardless of UX preference.
- AI-generated video legal landscape: FTC Operation AI Comply is ongoing (US); EU AI Act Article 50 enforcement begins August 2, 2026.

---

## Sources Consulted

1. Invesp. "E-Commerce Product Videos." https://www.invespcro.com/blog/e-commerce-product-videos/
2. Wyzowl. "Video Marketing Statistics." https://wyzowl.com/video-marketing-statistics/
3. Nielsen Norman Group. "Video Usability." https://www.nngroup.com/articles/video-usability/
4. Baymard Institute. "UX Research on Product Page Videos." https://baymard.com/blog/embedding-product-page-videos
5. Google. "Optimize Largest Contentful Paint." https://web.dev/articles/optimize-lcp
6. W3C. WCAG 2.2. https://www.w3.org/TR/WCAG22/ (1.2.2 Level A Captions; 1.2.5 Level AA Audio Description)
7. Google Developers. "Video structured data." https://developers.google.com/search/docs/appearance/structured-data/video (updated 2026-02-13)
8. Apple WebKit. "New Video Policies for iOS." https://webkit.org/blog/6784/new-video-policies-for-ios/
9. European Accessibility Act (Directive 2019/882). https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019L0882
10. US FTC. "Operation AI Comply." https://www.ftc.gov/business-guidance/blog/2024/09/operation-ai-comply-continuing-crackdown-overpromises-ai-related-lies
11. EU AI Act Article 50. https://artificialintelligenceact.eu/article/50/
12. C2PA (Coalition for Content Provenance and Authenticity). https://c2pa.org/
13. MDN Web Docs. Video codec guide. https://developer.mozilla.org/en-US/docs/Web/Media/Formats/Video_codecs
