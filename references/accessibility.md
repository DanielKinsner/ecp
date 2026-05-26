<!-- RESEARCH_DATE: 2026-04-02 -->
<!-- AUDIT NOTE 2026-04-22: Reconciled from Run A and Run B audits. Key changes: F1 alt-text figure updated 54.5%→53.1% (WebAIM Million 2026); n corrected 1,527→1,539 (WebAIM Survey #10). F3 WCAG 2.2 date corrected from "October 2023" to "W3C Recommendation, 12 December 2024" (both runs). F4 ADA lawsuit count updated 4,000+→3,117 federal website lawsuits in 2025 (Seyfarth 2025 tracker); EAA effective date added (2025-06-28); ADA.gov fact sheet date corrected. F6 screen-reader percentages corrected to match WebAIM #10 (both commonly-used and primary breakdowns added); n corrected. F9 added Birch 2012 + Deeb & Motulsky 2005 for 0.5% female prevalence citation gap. F10 Forrester 4.8×/4.5× multipliers flagged as unverifiable (URL 404); ADA litigation cost data retained. New F11 added: WCAG 2.2 vs 2.1 deltas (9 new SCs). WCAG 2.1→2.2 cross-file coordination with ethics-gate resolved 2026-04-22 (ethics-gate Part 7.3 updated to WCAG 2.2 AA as current W3C Recommendation). -->
# Image Accessibility in E-Commerce: Research Findings

**Research Date**: April 2, 2026; audited and reconciled April 22, 2026
**Domain**: Product Media — Accessibility for Images, Video, and Interactive Media
**Total Findings**: 11
**Methodology Note**: WCAG 2.2 (W3C Recommendation, 12 December 2024) is a normative technical standard from W3C — not a research finding but a compliance requirement. ADA Title III case law establishes legal obligation for ecommerce accessibility. Baymard Institute's image accessibility research provides UX context for best practices beyond minimum compliance. Market penetration data for assistive technology use comes from WebAIM Screen Reader User Survey.


---

## Cross-Reference Notice

**ECP Reference Overlap**: No direct ECP overlap on accessibility specifically.

**Cross-reference**: See `ethics-gate.md` PART 7 for EAA (European Accessibility Act) effective 2025-06-28 and DOJ Title III Final Rule (April 2024) policy surfaces.

This file covers: alt text requirements and formulas, video accessibility (captioning, transcripts), ARIA patterns for galleries, touch target sizing, color contrast requirements, and the business case for accessibility.

---

## Summary

### Top 3 Most Impactful Findings

1. **Finding 1 (53% of Web Pages Have Inadequate Alt Text)**: More than half of top web pages fail at the most basic image accessibility requirement. This affects both screen reader users and SEO — a rare case where the fix is low-effort and benefits multiple goals simultaneously.
2. **Finding 4 (WCAG 2.2 Level AA Is the Legal Standard)**: WCAG 2.2 Level AA is the de facto legal requirement for ecommerce sites operating in the US (under ADA Title III court precedent), EU (EAA, effective 2025-06-28), and increasingly other jurisdictions. Non-compliance carries litigation risk that significantly exceeds the cost of remediation.
3. **Finding 7 (Touch Target 44×44pt Minimum)**: Inadequate touch target size is the most common mobile accessibility failure in ecommerce, affecting both disabled users and general users equally — making it one of the highest-ROI accessibility fixes.

---

## Findings

### Finding 1: 53% of Web Pages Have Inadequate Alt Text for Product Images

- **Source**: WebAIM "Million Report" (2026 edition) — https://webaim.org/projects/million/ — annual automated accessibility analysis of 1,000,000 home pages. Cross-referenced with Baymard Institute "Informational Image Accessibility" (https://baymard.com/research/product-page) and WebAIM "Screen Reader User Survey #10" (https://webaim.org/projects/screenreadersurvey10/).
- **Methodology**: WebAIM Million: automated accessibility analysis of top 1M home pages annually. Baymard: UX benchmarking of major ecommerce sites against accessibility guidelines. WebAIM Screen Reader Survey #10: n=1,539 screen reader users (December 2023–January 2024).
- **Key Finding**: 53.1% of home pages have missing alt text for images (WebAIM Million 2026, analysis conducted February 2026). Additionally, 10.8% of images with alt text have "questionable or repetitive" alt text. More than one in four images on popular home pages has missing, questionable, or repetitive alternative text. Trend is declining from 58% in 2020 → 54.5% in 2024 → 53.1% in 2026. Without alt text, screen readers announce the file name or URL — e.g., "productimage_1234_v2_FINAL.jpg" — which provides zero product information. Baymard testing found screen reader users frequently abandon product pages where images lack descriptions, as images are the primary evaluation mechanism.
- **E-Commerce Application**: Audit all product images for alt text using automated tools (Axe, WAVE) as a starting point, then manual review for quality. Priority: hero images and first gallery image for every product. The formula for product image alt text: `[Product Name] — [View/Angle] — [Key Feature or Context]`. Examples: "Sony WH-1000XM5 Headphones — Side View — Premium Leather Earcups" (good); "product-img-1.jpg" (bad); "headphones" (too vague); "Sony WH-1000XM5 Wireless Bluetooth Premium Noise Canceling Over Ear Headphones Black..." (keyword stuffing, bad).
- **Replication Status**: WebAIM Million Report is replicated annually with consistent findings. The percentage of alt-text failures has declined slowly but remains >50% across the web.
- **Boundary Conditions**: Automated alt text detection flags missing alt attributes; it cannot evaluate alt text quality. A file with `alt="headphone"` passes automated checks but fails usability standards. Manual review is required for quality assessment. Dynamic product images loaded via JavaScript may require additional testing with screen readers.
- **Evidence Tier**: Gold

---

### Finding 2: Alt Text Formula for Product Images — By Image Type

- **Source**: W3C WAI. "An alt Decision Tree." https://www.w3.org/WAI/tutorials/images/decision-tree/. Cross-referenced with Baymard Institute image accessibility guidelines and Google Search Central image SEO documentation.
- **Methodology**: W3C normative guidance. Google documentation on image alt text for SEO. Baymard UX research on screen reader interaction with product pages.
- **Key Finding**: Different image types require different alt text approaches. Hero/packshot: `[Product Name] — Front View` or `[Product Name] — Main Product Image`. Lifestyle/context: describe what's shown in the environment — `[Product Name] [in/on/with] [context description]`. Scale reference: `[Product Name] Size Comparison — [reference object used]` (e.g., "held in hand to show scale"). Detail/close-up: `[Product Name] Detail — [what is shown]` (e.g., "Leather Stitching Detail"). Purely decorative images: `alt=""` (empty, not missing) tells screen readers to skip. Color variant thumbnails: `[Product Name] in [Color Name]`.
- **E-Commerce Application**: Create alt text template by image type for each product category. For large catalogs, implement programmatic alt text generation as a minimum acceptable baseline: `{{product.title}} — {{image.position}} of {{product.images.size}} — {{product.vendor}}`. Manually review and enhance alt text for bestselling products. Never keyword-stuff alt text — Google's guidelines explicitly flag this as spam.
- **Replication Status**: Technical guidance from authoritative sources (W3C, Google). Not a research finding requiring replication.
- **Boundary Conditions**: Programmatic alt text generation produces acceptable but not excellent alt text — it does not describe what's in the image. For major product launches and high-traffic PDPs, manual alt text writing produces meaningfully better accessibility outcomes.
- **Evidence Tier**: Gold (normative guidance)

---

### Finding 3: Videos with Spoken Audio Require Captions — WCAG 2.2 Level A Requirement

- **Source**: W3C. WCAG 2.2 Success Criterion 1.2.2 (Captions — Pre-recorded). https://www.w3.org/TR/WCAG22/#captions-prerecorded. **W3C Recommendation published 12 December 2024** (prior citation of "October 2023" was a Candidate Recommendation milestone, not the final W3C Recommendation — corrected per audit). Cross-referenced with ADA.gov web accessibility guidance (2024).
- **Methodology**: Normative technical standard. ADA.gov guidance (March 2024 rule for state/local government) references WCAG 2.1 Level AA; private-sector standards are determined by court interpretation which widely adopts WCAG 2.1 AA (and increasingly WCAG 2.2 AA).
- **Key Finding**: WCAG 2.2 SC 1.2.2 (Level A — minimum compliance) requires captions for all prerecorded video content that has audio. This applies to product demonstration videos, how-to videos, and any other video with spoken content on ecommerce sites. Level AA (the de facto legal standard under ADA and EU EAA) additionally requires audio descriptions for prerecorded video (SC 1.2.5) and live captions for live video. The penalty for non-compliance is ADA litigation — 3,117 federal-court website accessibility lawsuits were filed in 2025 per the Seyfarth Shaw tracker (36% of 8,667 total Title III filings).
- **E-Commerce Application**: Add WebVTT caption files to all product videos with spoken content: `<track kind="captions" src="video-captions.vtt" srclang="en" label="English" default>`. Caption quality requirements: accurate transcription (not auto-generated without human review), speaker identification where multiple speakers, sound effects noted when relevant. Tools: Rev.com ($1.50/minute, human-reviewed), Otter.ai (AI, requires review), YouTube auto-captions exported and reviewed. For new video production: budget caption creation at $1–3/minute of video as a line item.
- **Replication Status**: Normative technical standard.
- **Boundary Conditions**: Videos that are purely visual (product spin, silent lifestyle loop) without audio content are exempt from caption requirements. Auto-captions from YouTube or Whisper AI are acceptable only after human review — auto-captions have significant error rates for technical product names and specialized vocabulary.
- **Evidence Tier**: Gold (normative legal standard)

---

### Finding 4: WCAG 2.2 Level AA Is the De Facto Legal Standard for US Ecommerce (ADA Title III)

- **Source**: ADA.gov. "Guidance on Web Accessibility and the ADA." https://www.ada.gov/resources/web-guidance/. 2024. ADA.gov. "Fact Sheet: New Rule on the Accessibility of Web Content and Mobile Apps" (April 2024) — https://www.ada.gov/resources/2024-03-08-web-rule/. W3C WCAG 2.2 (W3C Recommendation, 12 December 2024) — https://www.w3.org/TR/WCAG22/. Seyfarth Shaw ADA Title III tracker — https://www.adatitleiii.com/2026/02/ada-title-iii-federal-lawsuit-filings-fall-slightly-to-8667-in-2025/.
- **Methodology**: Legal guidance from ADA.gov, confirmed by April 2024 rule (for state/local governments). Private sector Title III interpretation through court precedent. **2025 federal lawsuit count: 3,117 website accessibility lawsuits (36% of all 8,667 ADA Title III filings; up 27% from 2024; pro se filings up 40% YoY)** per Seyfarth Shaw tracker published February 2026 (prior citation of "4,000+ lawsuits/year as of 2023" updated to current 2025 Seyfarth figure).
- **Key Finding**: WCAG 2.2 Level AA is the technical standard increasingly referenced in ADA litigation against private ecommerce sites. The EU European Accessibility Act (EAA, Directive 2019/882) requires WCAG 2.1 AA compliance for ecommerce sites operating in EU markets, **effective 28 June 2025**. Australia, Canada, and UK have similar requirements. The practical minimum for US ecommerce: WCAG 2.1 Level AA (now superseded by WCAG 2.2 as W3C Recommendation, December 2024; courts are beginning to reference 2.2). WCAG 2.2 adds 9 new criteria vs 2.1; most relevant for ecommerce: SC 2.5.8 (Target Size Minimum — 24×24 CSS px minimum for interactive elements). Cross-reference: ethics-gate.md PART 7 for EAA and DOJ Final Rule (April 2024, applies to state/local government — not private ecommerce) policy surfaces.
- **E-Commerce Application**: Conduct a WCAG 2.2 Level AA audit using: automated tools (Axe DevTools, WAVE) for ~30% of issues; manual keyboard navigation testing; screen reader testing (NVDA+Chrome for Windows, VoiceOver+Safari for Mac/iOS). Key ecommerce-specific checks: product image alt text, video captions, color contrast on all text overlays, touch target sizes on mobile, form input labels (checkout, filter forms), skip navigation links, focus management in modal dialogs (quick view, cart drawer).
- **Replication Status**: Legal standard — not a research finding requiring replication.
- **Boundary Conditions**: The April 2024 ADA.gov rule formally applies to state and local government; Title III (private sector) compliance standards are determined by court interpretation. Courts have widely adopted WCAG 2.1 AA as the standard. WCAG 2.2 supersedes 2.1 and is backward-compatible — compliance with 2.2 AA implies compliance with 2.1 AA. Private ecommerce legal risk is real regardless of formal rulemaking.
- **Evidence Tier**: Gold (legal standard)

---

### Finding 5: Color Contrast Ratio Must Be 4.5:1 for Body Text, 3:1 for Large Text (18pt+)

- **Source**: W3C WCAG 2.2. Success Criteria 1.4.3 (Contrast — Minimum, Level AA). https://www.w3.org/TR/WCAG22/#contrast-minimum.
- **Methodology**: Technical standard based on contrast sensitivity research for users with low vision and color vision deficiencies.
- **Key Finding**: Text on backgrounds must meet minimum contrast ratios: 4.5:1 for normal text (<18pt / <14pt bold); 3:1 for large text (≥18pt / ≥14pt bold). Color alone cannot be the only means of conveying information (SC 1.4.1). Ecommerce violations: light gray price text on white background (common), sale price red-only indication without text label, star ratings shown only in yellow-on-white without text equivalent.
- **E-Commerce Application**: Common ecommerce contrast failures to fix: (1) Sale/original price markup — ensure strikethrough price has 4.5:1 contrast even when colored; (2) Form placeholder text — WCAG exempts placeholder text from contrast requirements but practical guidance is to meet it anyway; (3) Badge text on colored backgrounds — test "Sale" on red, "New" on green; (4) Star ratings — ensure review count text meets contrast; (5) "Out of stock" dimmed product cards — dimmed images are exempt but any text overlay must still meet contrast. Tool: WebAIM Contrast Checker — https://webaim.org/resources/contrastchecker/. WCAG 2.2 adds SC 1.4.11 (Non-text Contrast, Level AA): UI components and graphical objects must meet 3:1 contrast — covers icon-only buttons, interactive element borders, filter controls, gallery navigation.
- **Replication Status**: Technical standard. Vision research supporting the 4.5:1 ratio is from Arditi & Faye (2002) and ANSI/HFS 100 standards.
- **Boundary Conditions**: SC 1.4.11 (Non-text Contrast) covers UI components and graphical objects against adjacent colors — relevant for filter controls and gallery navigation.
- **Evidence Tier**: Gold (normative standard)

---

### Finding 6: Screen Reader Users Represent ~7.5M US Users — Not a Negligible Market Segment

- **Source**: WebAIM. "Screen Reader User Survey #10." https://webaim.org/projects/screenreadersurvey10/. Conducted December 2023–January 2024. **n=1,539 screen reader users** (prior citation of "n=1,527" was incorrect — WebAIM site shows 1,539 valid responses). Cross-referenced with CDC disability statistics (2022) at https://www.cdc.gov/ncbddd/disabilityandhealth/ (current CDC canonical path; prior /infographic-disability-impacts-all.html URL has drifted).
- **Methodology**: WebAIM survey of screen reader users (self-selected sample). CDC national disability statistics from NHIS survey data.
- **Key Finding**: An estimated 7.4% of US adults have a vision disability (CDC 2022), representing ~19M people. **WebAIM Survey #10 (December 2023–January 2024, n=1,539) shows two breakdowns: (1) Commonly used screen readers — NVDA 65.6%, JAWS 60.5%, VoiceOver 43.9% (respondents often use multiple); (2) Primary screen reader — JAWS 40.5%, NVDA 37.7%, VoiceOver 9.7%** (prior figures of "NVDA 53%, JAWS 40%, VoiceOver 39%" matched neither breakdown in WebAIM #10 — corrected per audit). 80%+ of screen reader users access the web daily. For ecommerce with $100K+ annual revenue, the accessibility market represents both legal risk management and a real revenue segment.
- **E-Commerce Application**: Screen reader testing should include: (1) Navigate product page with keyboard only; (2) Use NVDA+Chrome to confirm product images are announced with alt text; (3) Confirm gallery navigation is keyboard accessible (arrow keys or tab); (4) Verify cart and checkout process is fully keyboard operable; (5) Confirm filter controls have proper labels and state announcements (checked/unchecked). VoiceOver+Safari is the primary tool for iOS mobile testing. Testing takes 2–4 hours for a full product page audit.
- **Replication Status**: WebAIM survey is self-selected, limiting generalizability. CDC statistics are nationally representative.
- **Boundary Conditions**: Screen reader user behavior and preferences shift with technology updates. The survey is a cross-sectional snapshot. Not all people with vision disabilities use screen readers.
- **Evidence Tier**: Silver

---

### Finding 7: Touch Target Minimum Is 44×44pt (Apple HIG) / 48×48dp (Material Design) / 24×24 CSS px (WCAG 2.2)

- **Source**: Apple Human Interface Guidelines "Layout" — https://developer.apple.com/design/human-interface-guidelines/layout; Material Design 3 "Accessibility" (Google) — https://m3.material.io/foundations/accessibility/overview; W3C WCAG 2.2 SC 2.5.8 (Target Size Minimum, Level AA) — https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.
- **Methodology**: Platform design guidelines informed by ergonomics research. WCAG 2.5.8 based on Fitts's Law studies on touch target performance.
- **Key Finding**: Touch targets below 44×44pt (Apple HIG) or 48×48dp (Material Design 3) cause measurable increases in tap error rates — affecting motor-impaired users most severely but also affecting general users. WCAG 2.2 SC 2.5.8 (Level AA) sets 24×24 CSS px as the minimum with five defined exceptions (spacing, equivalent, inline, user agent control, essential). Common ecommerce failures: gallery thumbnail navigation arrows (often 24px tap targets), color swatches (<30px), wishlist icons, filter checkboxes in sidebar. Note: WCAG 2.5.8 minimum (24×24 CSS px) is a lower bar than Apple/Google platform standards (44/48pt) — aim for 44px.
- **E-Commerce Application**: Minimum touch target audit: measure all interactive elements on mobile using browser DevTools device simulation. Fix sequence: (1) Gallery navigation arrows → 44px minimum; (2) Color swatches → 44px with 4px margin; (3) Wishlist heart icon → 44×44px tap area even if icon is smaller; (4) Filter checkboxes → 44px row height in filter panel; (5) Cart icon in header → already typically 44px+; (6) Thumbnail strip images in gallery → 44px minimum height. Use CSS padding to extend tap areas without changing visual size.
- **Replication Status**: Platform standards confirmed by ergonomics research. WCAG 2.5.8 is normative.
- **Boundary Conditions**: WCAG 2.5.8 has exceptions for inline text links (exempt from minimum size) and when target size is essential to the feature. The 24×24 CSS px WCAG minimum is a lower bar than Apple/Google's 44/48 recommendations — aim for 44px.
- **Evidence Tier**: Gold (normative standard + ergonomics research)

---

### Finding 8: Product Gallery Requires ARIA Patterns for Screen Reader Navigation

- **Source**: W3C WAI-ARIA Authoring Practices Guide — https://www.w3.org/WAI/ARIA/apg/ — specifically the ARIA Carousel Pattern at https://www.w3.org/WAI/ARIA/apg/patterns/carousel/. Cross-referenced with Baymard Institute gallery UX research.
- **Methodology**: W3C normative ARIA pattern guidance. Extrapolation from Baymard gallery UX research to accessibility context.
- **Key Finding**: Standard product image galleries (carousels) require specific ARIA markup to be navigable by screen reader users: `role="region"` with descriptive `aria-label` ("Product Images"); individual slides must have `aria-roledescription="slide"`; current slide position announced with `aria-label="Slide 1 of 8"` or equivalent; navigation controls (previous/next) with descriptive `aria-label` ("Previous product image"); live region for slide changes (`aria-live="polite"` or `aria-atomic="true"`). Without this markup, carousel navigation is opaque to screen readers.
- **E-Commerce Application**: Gallery accessibility implementation checklist: (1) Wrap gallery in `<nav aria-label="Product images">` or `<section aria-label="Product image gallery">`; (2) Each thumbnail: `<button aria-label="Product name - view 3 of 8: leather detail close-up">`; (3) Main image: `<img alt="..." aria-current="true">` for active image; (4) Keyboard navigation: left/right arrow keys cycle images; (5) Autoplay galleries (rare): provide pause control; (6) Touch-only swipe: ensure keyboard alternative exists. Most third-party gallery components (Swiper.js, Splide, Slick) have optional ARIA modes — enable them.
- **Replication Status**: ARIA patterns are normative W3C guidance. Screen reader behavior with specific ARIA implementations is confirmed through user testing.
- **Boundary Conditions**: ARIA implementation must be tested with actual screen readers — ARIA declarations that look correct in code may not produce expected behavior in NVDA/JAWS/VoiceOver. Screen reader support for ARIA patterns varies; test across NVDA+Chrome, JAWS+Chrome, and VoiceOver+Safari.
- **Evidence Tier**: Gold (normative standard)

---

### Finding 9: Provide Text Alternatives for Color-Only Product Variants — Color Blindness Affects ~8% of Males

- **Source**: National Eye Institute. "Color Blindness." https://www.nei.nih.gov/learn-about-eye-health/eye-conditions-and-diseases/color-blindness ("About 1 in 12 men have color vision deficiency"). Female prevalence ~0.5% from Deeb, S.S. & Motulsky, A.G. (2005). "Genetics of Color Vision." In *GeneReviews*, NCBI Bookshelf — https://www.ncbi.nlm.nih.gov/books/; and Birch, J. (2012). "Worldwide prevalence of red-green color deficiency." *Journal of the Optical Society of America A*, 29(3), 313–320. Cross-referenced with W3C WCAG 2.2 SC 1.4.1 (Use of Color, Level A) — https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.
- **Methodology**: NEI epidemiological communication. Peer-reviewed epidemiological data for female prevalence (Birch 2012 / Deeb & Motulsky 2005). WCAG normative standard on color-only information conveyance.
- **Key Finding**: Red-green color blindness affects approximately 8% of males ("about 1 in 12 men" per NEI) and approximately 0.5% of females (figures vary by ethnicity; Northern European descent data per Birch 2012 review). For a product with 10 color variants, ~8% of male shoppers cannot reliably distinguish red from green swatches. WCAG SC 1.4.1 (Level A) prohibits conveying information using color as the only visual means — color swatches must include text labels (color names) accessible to screen readers and visible in color-deficient view.
- **E-Commerce Application**: Color swatch accessibility: (1) Each swatch must have an `aria-label` with color name: `<button aria-label="Select Navy Blue" ...>`; (2) Currently selected color must be announced: `aria-pressed="true"` or `aria-checked="true"` on selected swatch; (3) Color name should be visible as text near swatches, not only encoded in swatch appearance; (4) For checked/selected state: use shape change (ring, checkmark) in addition to color change — not color-only selected indicator; (5) Red and green swatches should differ in size or have pattern in addition to color for users who cannot distinguish them.
- **Replication Status**: Color blindness prevalence data is epidemiologically well-established across multiple studies. WCAG standard is normative.
- **Boundary Conditions**: Color blindness accessibility is most critical for red/green pairs (protanopia/deuteranopia, the most common types). Blue color blindness (tritanopia) is rare (<0.01%). Full color blindness (achromatopsia) is extremely rare. The fix (adding text labels and non-color shape differentiation) is low-effort with high-coverage benefit.
- **Evidence Tier**: Gold (epidemiological data + normative standard)

---

### Finding 10: The Business Case — Accessibility ROI Exceeds Remediation Cost for Ecommerce at Scale

- **Source**: Deque Systems practitioner data on remediation costs — https://www.deque.com; Seyfarth Shaw ADA Title III lawsuit tracker — https://www.adatitleiii.com/2026/02/ada-title-iii-federal-lawsuit-filings-fall-slightly-to-8667-in-2025/ (8,667 total 2025 filings); Forrester Research (commissioned by Microsoft), "The Business Value of Accessible Technology," 2023 — note: the cited Microsoft URL (microsoft.com/en-us/accessibility/business-case) was returning errors as of this audit; Forrester multipliers (4.8× profit growth, 4.5× customer retention) are unverifiable at the primary URL and should be treated with caution until a live Forrester primary source is confirmed. American Institutes for Research disability economy estimate ($490B+ annual discretionary spending).
- **Methodology**: Deque Systems cost benchmarks from accessibility remediation projects (practitioner data). ADA lawsuit data from Seyfarth Shaw court-record tracker. Forrester multipliers are from commissioned research with limited public methodology disclosure; primary URL unverifiable as of audit.
- **Key Finding**: Proactive accessibility implementation costs ~3× less than reactive remediation after product launch (Deque Systems benchmark). The cost of a single ADA Title III lawsuit settlement ranges from $50,000 to $150,000+ including legal fees. Note: the Forrester 4.8× profit growth / 4.5× customer retention multipliers are from a Microsoft-commissioned study whose primary URL was returning errors during this audit — these specific multipliers should not be cited without direct source verification; they are retained here as directional but flagged as unverifiable pending URL resolution. The accessible market (people with disabilities + their networks) controls over $490 billion in annual discretionary spending (US, AIR estimate).
- **E-Commerce Application**: Frame accessibility investment to stakeholders as: (1) Legal risk management — compliance is cheaper than litigation by 10–100×; (2) Market expansion — 26% of US adults have some disability, representing real purchasing power; (3) SEO improvement — alt text, semantic HTML, and page structure improve crawlability; (4) General UX improvement — touch target sizing, contrast, and keyboard navigation benefit all users, not only disabled users. The "curb cut effect" is well-documented: accessibility improvements benefit populations beyond the originally intended target.
- **Replication Status**: ADA lawsuit statistics are verifiable from court records (Seyfarth Shaw tracker). Forrester multipliers are from vendor-commissioned research with unverifiable primary URL as of this audit — treat as directional only. Deque cost benchmarks are practitioner estimates.
- **Boundary Conditions**: The $490B figure represents total disability community spending power, not ecommerce share. Business value claims from technology vendor-commissioned research should be treated skeptically — especially when primary sources are not accessible.
- **Evidence Tier**: Silver (mixed sources; ADA litigation data is strong; Forrester ROI multipliers unverifiable at primary URL)

---

### Finding 11: WCAG 2.2 vs 2.1 — 9 New Success Criteria (What Changed for Ecommerce)

- **Source**: W3C. "What's New in WCAG 2.2." https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/. W3C WCAG 2.2 — https://www.w3.org/TR/WCAG22/. W3C Recommendation, 12 December 2024. All 9 new SCs are at Level AA or Level AAA; ecommerce-relevant SCs are Level AA (mandatory for legal compliance).
- **Methodology**: Normative W3C specification. The 9 new SCs are verifiable by direct comparison of WCAG 2.1 and WCAG 2.2 specifications.
- **Key Finding**: WCAG 2.2 adds 9 success criteria not present in WCAG 2.1. Ecommerce-relevant SCs (all Level AA unless noted): **(1) SC 2.4.11 Focus Not Obscured (Minimum, AA)** — focused component must not be entirely hidden by sticky headers/overlays; **(2) SC 2.4.12 Focus Not Obscured (Enhanced, AAA)** — full visibility required; **(3) SC 2.4.13 Focus Appearance (AAA)** — visible focus indicator sizing; **(4) SC 2.5.7 Dragging Movements (AA)** — all drag interactions must have pointer/click alternative (e.g., gallery swipe must also work with click/tap); **(5) SC 2.5.8 Target Size Minimum (AA)** — 24×24 CSS px minimum for interactive elements (see Finding 7); **(6) SC 3.2.6 Consistent Help (AA)** — help mechanisms (chat, phone number) must appear in same location across pages; **(7) SC 3.3.7 Redundant Entry (AA)** — avoid requiring users to re-enter information provided earlier in same process (e.g., address re-entry in checkout); **(8) SC 3.3.8 Accessible Authentication (Minimum, AA)** — cognitive function tests (CAPTCHA) must have an alternative; **(9) SC 3.3.9 Accessible Authentication (Enhanced, AAA)** — no cognitive function test at all. Removed from WCAG 2.2 vs. 2.1: SC 4.1.1 Parsing (deprecated; modern browsers handle parsing consistently).
- **E-Commerce Application**: If already at WCAG 2.1 AA compliance, the mandatory new work for WCAG 2.2 AA is: (a) SC 2.4.11 — audit sticky header behavior when users tab through checkout form fields; (b) SC 2.5.7 — ensure all swipe/drag gallery interactions have click alternatives; (c) SC 2.5.8 — touch target audit (see Finding 7); (d) SC 3.2.6 — ensure help widget (chat, phone) appears consistently; (e) SC 3.3.7 — audit checkout for address re-entry friction; (f) SC 3.3.8 — ensure CAPTCHA alternatives exist. These are mechanical implementation tasks, not UX redesigns.
- **Replication Status**: Normative W3C specification — not a research finding requiring replication.
- **Boundary Conditions**: SCs 2.4.12, 2.4.13, and 3.3.9 are Level AAA — not required for standard WCAG 2.2 AA compliance but represent best practice. SC 3.3.7 (Redundant Entry) has an exception for when re-entry is needed for security reasons.
- **Evidence Tier**: Gold (normative W3C specification)

---

## Methodological Notes

- WCAG 2.2 (W3C Recommendation, 12 December 2024) is the primary authoritative source for accessibility requirements. It supersedes WCAG 2.1 and is backward-compatible (meeting 2.2 AA satisfies 2.1 AA). Courts are still in the process of updating references from 2.1 to 2.2.
- WebAIM Million Report provides the largest annual dataset on web accessibility failures and is the best benchmark for industry prevalence.
- Screen reader testing is essential — automated tools catch ~30% of accessibility issues. Manual testing with real assistive technology is required for the remaining 70%.
- ADA Title III interpretation through US court precedent is the operative legal standard for private ecommerce — consult legal counsel for jurisdiction-specific guidance.

---

## Sources Consulted

1. W3C. WCAG 2.2 (W3C Recommendation 12 December 2024). https://www.w3.org/TR/WCAG22/
2. W3C WAI. "What's New in WCAG 2.2." https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/
3. W3C WAI. "An alt Decision Tree." https://www.w3.org/WAI/tutorials/images/decision-tree/
4. W3C WAI-ARIA Authoring Practices Guide. https://www.w3.org/WAI/ARIA/apg/
5. ADA.gov. "Guidance on Web Accessibility and the ADA." https://www.ada.gov/resources/web-guidance/
6. ADA.gov. "Fact Sheet: New Rule on Accessibility" (April 2024). https://www.ada.gov/resources/2024-03-08-web-rule/
7. WebAIM. Screen Reader User Survey #10 (December 2023–January 2024, n=1,539). https://webaim.org/projects/screenreadersurvey10/
8. WebAIM. Million Report 2026 (53.1% home pages missing alt text). https://webaim.org/projects/million/
9. Baymard Institute. Image Accessibility Research. https://baymard.com/research/product-page
10. Apple Human Interface Guidelines. https://developer.apple.com/design/human-interface-guidelines/
11. Material Design 3 Accessibility. https://m3.material.io/foundations/accessibility/overview
12. National Eye Institute. Color Blindness. https://www.nei.nih.gov/learn-about-eye-health/eye-conditions-and-diseases/color-blindness
13. Birch, J. (2012). "Worldwide prevalence of red-green color deficiency." *Journal of the Optical Society of America A*, 29(3), 313–320.
14. Deeb, S.S. & Motulsky, A.G. (2005). "Genetics of Color Vision." *GeneReviews*, NCBI Bookshelf. https://www.ncbi.nlm.nih.gov/books/
15. Seyfarth Shaw. ADA Title III Lawsuit Tracker (2025). https://www.adatitleiii.com/2026/02/ada-title-iii-federal-lawsuit-filings-fall-slightly-to-8667-in-2025/
16. Deque Systems. Accessibility Remediation Cost Benchmarks. https://www.deque.com
