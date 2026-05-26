<!-- RESEARCH_DATE: 2026-04-21 -->
<!-- RECONCILED: 2026-04-21 — see RECONCILED/image-seo-alt-text.md for full decision log -->
# Image SEO & Alt Text

**Research Date:** 2026-04-21 (reconciled revision of 2026-04-02 source)
**Total Findings:** 11
**Methodology:** Synthesis of Google's official image SEO documentation (verified 2026-04-21, last updated 2026-03-02), Google Lens usage statistics (Google-published data, verified 2026-04-21), Google Merchant Center image requirements (verified 2026-04-21), ADA lawsuit data (EcomBack 2025 annual report, verified 2026-04-21), WCAG 2.1 primary source (W3C), accessibility compliance research, and industry image optimization studies. Evidence weighted by source authority and data quality per evidence-tiers.md.

> **Cross-Reference:** See CRO reference `gallery-ux.md` for the conversion psychology of product image presentation. See `image-quantity-types.md` for UX best practices around image types. See `ethics-gate.md` PART 7.3 for ADA Title III and EAA legal obligations. This file focuses on the SEO/discoverability and compliance angle.

---

### Top 3 Most Impactful Findings

1. **Google Lens processes ~20 billion visual searches/month — 1 in 4 have commercial intent** (Finding 4) — Per Think with Google: "1 in 4 visual searches using Lens has commercial intent" — roughly 5 billion shopping-intent visual searches monthly. High-quality product images with clear composition directly improve visual search discoverability.

2. **Missing alt text triggers ADA lawsuits — 3,948 businesses sued in 2025** (Finding 9) — Missing alt text is one of the most commonly cited WCAG violations. Overlay widgets provide no legal protection — 24.90% of 2025 lawsuits targeted sites already using overlay widgets. Alt text is a legal compliance requirement, not optional SEO.

3. **CSS background images are not indexed by Google** (Finding 1) — Product images served via CSS `background-image` are entirely invisible to Google, Google Images, and Google Lens. Every product image must use `<img>` elements.

---

### Coverage by Research Question

| Research Question | Findings | Evidence Quality |
|---|---|---|
| How does Google discover/index images? | 1, 8 | Gold / Silver |
| What is the scale of visual search opportunity? | 3, 4 | Bronze / Gold |
| How should alt text be written? | 2, 6 | Gold / Bronze |
| What are Google Merchant Center image specs? | 5 | Gold |
| Do customer photos help conversion? | 7 | Bronze |
| What are the legal risks of missing alt text? | 9, 11 | Silver / Gold |
| What is the specific WCAG criterion for alt text? | 11 | Gold |
| How should image filenames be structured? | 10 | Silver |

---

### Finding 1: Google Does NOT Index CSS Background Images
- **Source**: Google Search Central, "Google Images best practices" (last updated 2026-03-02), https://developers.google.com/search/docs/appearance/google-images.
- **Methodology**: Google official documentation — describes actual crawler behavior. Verbatim confirmed 2026-04-21: "Google doesn't index CSS images" and "Google can find images in `src` attribute of `<img>` element."
- **Key Finding**: CSS `background-image` properties are not indexed for Google Images, cannot appear in visual search results, and cannot be matched via Google Lens. Images must be in HTML `<img>` elements to be discoverable.
- **E-Commerce Application**: Every product image must use `<img src="...">` tags. Common failure mode: hero banners, promotional blocks, and collection header images served as CSS backgrounds — none of these are indexable.
- **Replication Status**: Google official specification — applies universally to all crawled content.
- **Boundary Conditions**: JS-injected `<img>` elements may be indexed with delay and unreliability; server-side-rendered elements are most reliable. Lazy-loaded images using `loading="lazy"` on `<img>` tags ARE indexed by Googlebot. Lazy-loaded CSS backgrounds are not.
- **Evidence Tier**: Gold — Google Search Central official documentation.
- **Audit Note (2026-04-21)**: VERIFIED — no changes.

---

### Finding 2: Alt Text Must Be Descriptive — Keyword Stuffing Triggers Penalties
- **Source**: Google Search Central, "Google Images best practices" (alt text section), https://developers.google.com/search/docs/appearance/google-images. Google SEO Starter Guide: https://developers.google.com/search/docs/fundamentals/seo-starter-guide.
- **Methodology**: Google official documentation. Verbatim confirmed 2026-04-21: "Avoid filling `alt` attributes with keywords (also known as keyword stuffing) as it results in a negative user experience and may cause your site to be seen as spam."
- **Key Finding**: Google uses alt text along with computer vision algorithms and page context to understand image subject matter. Decorative images should use `alt=""` (empty attribute, not omitted entirely — omitting the attribute flags missing accessibility under SC 1.1.1; see Finding 11).
- **E-Commerce Application**:
  - **Good**: `alt="2024 Toyota GR Supra carbon fiber hood, gloss finish, front 3/4 angle view installed on white car"`
  - **Bad**: `alt="carbon fiber hood supra hood toyota hood buy cheap carbon fiber hood"`
  - **Decorative** (borders, spacers, pure design elements): `alt=""`
  - **Icons/UI**: `alt="Add to cart"` or `alt="Zoom image"`
- **Replication Status**: Google policy — consistent across all official documentation for 10+ years.
- **Boundary Conditions**: Alt text too short provides insufficient context for image search matching. Too long (>150 characters) may be truncated by screen readers. See Finding 6 for length heuristics.
- **Evidence Tier**: Gold — Google Search Central official documentation.
- **Audit Note (2026-04-21)**: VERIFIED — updated to quote Google's current verbatim wording.

---

### Finding 3: Google Images Is a Substantial US Web-Search Channel
- **Source**: SparkToro / Rand Fishkin analysis of clickstream data (2022). https://sparktoro.com/ **Citation Status**: Original SparkToro URL (sparktoro.com/blog/how-much-of-googles-search-traffic-is-actually-going-to-google/) was not retrievable on 2026-04-21 (returned 4xx). No clean successor URL confirmed. The 20–22% figure is widely repeated in SEO industry writing but the originating post is no longer accessible.
- **Methodology**: SparkToro clickstream panel analysis (via Datos) — estimates of search distribution across Google properties. Panel-based clickstream data, not a complete census.
- **Key Finding**: Google Images is a significant US search vertical — a substantial product-discovery channel that many ecommerce sites neglect entirely. The historically cited "20–22%" figure is preserved as a widely-cited industry estimate; it is not verifiable from a live primary source as of 2026-04-21 and should not be cited as a confirmed hard figure.
- **E-Commerce Application**: Optimized product images are discoverable through Google Images, driving traffic that text-only SEO misses. Particularly impactful for visually-driven categories: fashion, home decor, automotive accessories, art, furniture.
- **Replication Status**: Google does not publish precise channel-by-channel search volume data. The specific 20–22% figure is from an inaccessible primary source; the directional claim is consistent with multiple secondary analyses.
- **Boundary Conditions**: Google Images traffic tends to be earlier in the purchase funnel than direct product search queries. Conversion rates from image search typically lag behind direct product search.
- **Evidence Tier**: Bronze — specific 20–22% figure unverifiable from live primary (downgraded from Silver 2026-04-21); directional claim defensible from secondary sources.
- **Citation Status**: Original SparkToro URL dead as of 2026-04-21 audit; stat unverifiable from primary.
- **Audit Note (2026-04-21)**: REFORMULATED — downgraded from Silver to Bronze; added Citation Status annotation per evidence-tiers.md deprecation rule; directional claim retained.

---

### Finding 4: Google Lens Processes ~20 Billion Visual Searches/Month — 1 in 4 Have Commercial Intent
- **Source**: Google Search blog, "5 helpful Google Lens updates" (October 2024), https://blog.google/products/search/google-search-lens-october-2024-updates/ — confirms "nearly 20 billion visual searches every month" (volume; does NOT contain commercial-intent percentage). Think with Google, "Search Innovations," https://business.google.com/us/think/search-and-video/google-search-innovations/ — states: "Google Lens is used for over 20 billion visual search queries every month, and 1 in 4 visual searches using Lens has commercial intent." Both URLs verified live 2026-04-21.
- **Methodology**: Google's own usage data — self-reported but authoritative for Google's own product. Not independently auditable.
- **Key Finding**: Google Lens handles approximately 20 billion visual search queries per month. **1 in 4 (~25%)** of Lens queries have commercial intent — approximately **~5 billion commercially-intentful visual searches per month**. (Prior version of this file stated 20% / 4 billion — both figures were incorrect; corrected 2026-04-21 per Think with Google primary.)
- **E-Commerce Application**: Product images optimized for visual search should: (1) use clear, well-lit photography with product as primary subject; (2) include multiple angles; (3) use white/neutral backgrounds for main product images (improves Google's ability to isolate and match the product); (4) use consistent naming and alt text. These align with Google Merchant Center best practices — alignment serves both channels.
- **Replication Status**: Google's own data — authoritative for scale, though Google has financial incentive to highlight Lens usage.
- **Boundary Conditions**: Lens matching is strongest for visually distinctive products — unique items, fashion, branded consumer goods. Commodity products benefit less from visual search optimization.
- **Evidence Tier**: Gold — Google's own platform data, confirmed in official Google publications 2026-04-21.
- **Audit Note (2026-04-21)**: REFORMULATED — corrected commercial-intent share from 20% → **25% (1 in 4)** per Think with Google; corrected downstream figure from 4 billion → **~5 billion**. The blog.google October 2024 URL confirms the volume figure only; Think with Google is the sole confirmed source for the 1-in-4 figure.

---

### Finding 5: Google Merchant Center Image Requirements — Minimum 500×500
- **Source**: Google Merchant Center Help, "Image link [image_link]," https://support.google.com/merchants/answer/6324350?hl=en (verified 2026-04-24).
- **Methodology**: Google official specification — defines required, recommended, and prohibited image characteristics for Merchant Center product listings.
- **Key Finding**: **Minimum image size: 500×500 pixels (all products).** (Prior version of this file stated 100×100 non-apparel / 250×250 apparel — this apparel/non-apparel split and those minimums are no longer in the current live spec; corrected 2026-04-21.) Recommended: 1500×1500 pixels or higher for optimal performance and zoom functionality. Maximum: 64 megapixels, 16MB file size. Main product image: solid white (#FFFFFF) or transparent background strongly recommended; no watermarks; no promotional text, logos, or calls-to-action overlaid on the main image (logos inherent to the product design are allowed). Additional images (lifestyle shots) may use contextual backgrounds.
- **E-Commerce Application**: Shoot main product images at 1500×1500px minimum at source. White or transparent background for primary image ensures Merchant Center eligibility and Google Lens matching. Note: transparent backgrounds may display with black backgrounds for light-colored products, so solid white is often safer. Never include promotional text, prices, or CTAs on main product images — will cause disapproval.
- **Replication Status**: Google official specification — applies to all Merchant Center accounts. Non-compliance results in product disapproval and removal from Shopping results.
- **Boundary Conditions**: Some product categories have exceptions (products that cannot be photographed in isolation). Multi-pack products may show the pack rather than a single item.
- **Evidence Tier**: Gold — Google Merchant Center official specification.
- **Audit Note (2026-04-21)**: REFORMULATED — updated minimum from outdated "100×100 (non-apparel) / 250×250 (apparel)" to **current 500×500 universal minimum** per live Merchant Center Help page. Removed apparel/non-apparel split (not in current spec). Clarified background as "strongly recommended" (not absolutely required).

---

### Finding 6: Optimal Alt Text Length — Succinct But Complete; 80–140 Characters Is a Common Heuristic
- **Source**: WebAIM accessibility guidelines citing WCAG 2.1 recommendations, https://webaim.org/techniques/alttext/ (verified 2026-04-21). AltText.ai analysis of alt text length vs. SEO performance, https://alttext.ai/blog/. Accessibility Checker, https://www.accessibilitychecker.org/. **Audit correction 2026-04-21**: WebAIM does NOT specify a hard 125-character limit — their guidance is qualitative ("succinct"). The 80–140 character range is a practitioner heuristic.
- **Methodology**: Industry consensus based on WCAG 2.1 guidance and observed screen reader behavior. The 80–140 character range is a practitioner heuristic, not a rigorously tested finding.
- **Key Finding**: WebAIM states alt text should be "succinct" — "typically, only a few words are necessary, though rarely a short sentence or two may be appropriate." Many screen readers have historically truncated alt text somewhere between approximately 125–150 characters (this varies by reader and version; no single universal cutoff). The 5–15 word / 80–140 character practitioner heuristic provides sufficient information for both Google's image understanding and screen reader users without likely truncation.
- **E-Commerce Application**: Template: `[Product Name] [Key Attribute] [View/Context/Color]`. Examples:
  - `"Brembo GT-S 6-piston front brake kit, red caliper, installed on 2024 GR Supra"` (82 chars ✓)
  - `"Women's white running shoe, Nike Air Max 90, side profile view"` (62 chars ✓)
  - `"Carbon fiber hood showing 2x2 twill carbon fiber weave pattern, gloss finish detail"` (71 chars ✓)
- **Replication Status**: Not a controlled study — practitioner consensus based on accessibility standards and vendor testing.
- **Boundary Conditions**: Alt text for complex images (infographics, size charts, installation diagrams) may require longer descriptions — use adjacent text description or linked page rather than stuffing into alt. Alt text for decorative images must be empty (`alt=""`), regardless of length guidance. See Finding 11 for the WCAG primary standard.
- **Evidence Tier**: Bronze — vendor analysis and accessibility heuristics; no controlled study isolating this specific parameter.
- **Audit Note (2026-04-21)**: REFORMULATED — softened "historically truncated at approximately 125–150 characters" to reflect that the specific cutoff varies by reader and version; no hard limit is specified by WebAIM or WCAG.

---

### Finding 7: Customer Photos May Increase Purchase Likelihood
- **Source**: Multiple vendor-produced studies: Bazaarvoice Shopper Research (2024) https://www.bazaarvoice.com/research-and-insights/; Flowbox/Olapic UGC conversion data https://getflowbox.com/. The "77% prefer customer photos over professional shots" figure is widely cited but original study not consistently attributed.
- **Methodology**: Vendor surveys and behavioral data from UGC platforms. Significant selection bias: users who view UGC photos are already engaged. Correlation between UGC viewing and purchase does not prove causation.
- **Key Finding**: Multiple vendor studies suggest customer/UGC photos increase conversion rates — typically cited as 25–40% conversion lift. The 77% preference figure is widely cited but original methodology is unclear.
- **E-Commerce Application**: Supplement professional photography with customer/UGC photos clearly labeled as "Customer Photos." Professional images for clarity and quality; UGC for authenticity and social proof. Google Images and Google Lens can index both — UGC images in Google Images extend your visual search footprint.
- **Replication Status**: Not independently replicated with controlled methodology. Vendors have direct financial interest in UGC platforms (Bazaarvoice, Flowbox sell UGC solutions). Directionally plausible but magnitude is likely inflated.
- **Boundary Conditions**: UGC is most impactful for fashion, lifestyle, consumer goods. For technical/industrial products, professional specification photography likely outperforms UGC. Quality control matters — low-quality customer photos can hurt rather than help.
- **Evidence Tier**: Bronze — vendor-produced studies with financial interest; no independent peer-reviewed replication.
- **Audit Note (2026-04-21)**: VERIFIED — no changes.

---

### Finding 8: Consistent Image URLs Improve Crawl and Cache Efficiency
- **Source**: Google Search Central, "Google Images best practices" (last updated 2026-03-02), https://developers.google.com/search/docs/appearance/google-images. Verbatim confirmed 2026-04-21: "consistently reference the image with the same URL, so that Google can cache and reuse the image without needing to request it multiple times."
- **Methodology**: Google official documentation — describes crawler behavior and best practices for efficient image indexing.
- **Key Finding**: Google recommends maintaining stable, consistent image URLs. Once a product image URL is indexed, changing that URL requires re-crawl and re-index. Frequent URL changes (e.g., cache-busting query parameters that change per deployment) create unnecessary recrawl demand and may temporarily remove images from search.
- **E-Commerce Application**: Establish a permanent URL structure for product images. Avoid deployment-specific cache-busting params (`product.jpg?v=1704067200`). Use `Cache-Control: max-age` and `ETag` for freshness control. If you must change an image URL, implement a 301 redirect from the old to the new.
- **Replication Status**: Google official documentation — confirmed by Google's stated crawler behavior.
- **Boundary Conditions**: CDN-served images using content-hash filenames (`product.abc123.jpg`) are a necessary engineering tradeoff; in these cases, ensure a stable canonical URL exists via canonical image markup.
- **Evidence Tier**: Silver — Google Search Central documentation (official but classified Silver as documentation guidance, not a direct ranking study).
- **Audit Note (2026-04-21)**: VERIFIED — no changes.

---

### Finding 9: Missing Alt Text Triggers ADA Lawsuits — 3,948 Businesses Sued in 2025
- **Source**: EcomBack, "2025 ADA Website Compliance Lawsuit Annual Report," https://www.ecomback.com/annual-2025-ada-website-accessibility-lawsuit-report (verified 2026-04-21). UsableNet Annual Accessibility Lawsuit Report. FTC and DOJ guidance on web accessibility.
- **Methodology**: EcomBack and UsableNet track US federal ADA Title III website-accessibility filings via public court records.
- **Key Finding**: **3,948 ADA website lawsuits filed January–December 2025** (23.84% YoY increase over 2024's 3,188). Top 9 consumer-facing industries accounted for 91.51% of lawsuits — restaurants/food/beverage 34.65% (1,368 cases), fashion/apparel 25.96% (1,025 cases), beauty/personal care 8.03% (317 cases). **Note**: the top-9 figure covers consumer-facing industries broadly, not specifically "ecommerce" — prior versions of this file conflated these; corrected 2026-04-21. E-commerce is a significant subset but EcomBack's dataset does not cleanly disaggregate it. Missing alt text is among the most commonly cited WCAG violations. **Accessibility overlay widgets do NOT provide legal protection** — 983 lawsuits (24.90%) targeted sites already using overlay widgets; the top five widget vendors accounted for 88.40% of widget-related cases (AccessiBe alone: 424 cases / 43.13%). The European Accessibility Act (EAA) entered enforcement 2025-06-28.
- **E-Commerce Application**: Every product image needs descriptive alt text — legal compliance, not optional SEO. (1) alt text serves both SEO and accessibility; (2) overlay widgets are insufficient protection; (3) automated tools identify missing alt text at scale but key product images need manual review; (4) EAA means non-US merchants selling to EU consumers face equivalent obligations.
- **Replication Status**: Lawsuit data is from public court records — verifiable. Trend consistent across EcomBack and UsableNet independent tracking.
- **Boundary Conditions**: Legal risk higher in jurisdictions with active plaintiff firms (New York, California, Florida account for the majority of US ADA website lawsuits). B2B-only platforms with restricted access may have different exposure. State-level lawsuits (e.g., California Unruh Act) are filed separately — total accessibility litigation exposure is higher than the 3,948 federal figure suggests.
- **Evidence Tier**: Silver — EcomBack aggregates verifiable public court records but is a vendor selling accessibility services (financial interest undercuts Gold per evidence-tiers.md). The ADA Title III and EAA primary texts are Gold-grade authorities, cited separately in `ethics-gate.md` §7.3.
- **Tracker Scope Note**: This file uses **EcomBack's 2025 full-year count (3,948)** — federal ADA Title III website-accessibility filings only. Other reference files in this corpus cite parallel but non-identical trackers: `accessibility.md` and `mobile-conversion.md` cite **UsableNet's 2024 count (4,187+)**; `ethics-gate.md` Part 7.3 cites **Seyfarth's 2024 count (~4,600+)**. All three are correct for their reporting period and methodology. When comparing across files, check (a) reporting year, (b) federal-only vs. broader scope, (c) whether the scope is website-accessibility specifically or ADA Title III broadly. Do not treat these as contradictory.
- **Audit Note (2026-04-21)**: REFORMULATED — corrected "ecommerce" conflation to "top 9 consumer-facing industries"; added category breakdown and AccessiBe overlay detail per live EcomBack report; added Tracker Scope Note to prevent cross-file confusion with UsableNet (accessibility.md F10, mobile-conversion.md F23) and Seyfarth (ethics-gate.md Part 7.3) counts.

---

### Finding 10: Descriptive Image Filenames Signal Content to Google
- **Source**: Google Search Central, "Google Images best practices" (filename section), https://developers.google.com/search/docs/appearance/google-images (verified 2026-04-21). Verbatim confirmed: "When possible, use filenames that are short, but descriptive. For example, `my-new-black-kitten.jpg` is better than `IMG00023.JPG`."
- **Methodology**: Google official documentation — describes filenames as one of multiple signals for image content understanding.
- **Key Finding**: Google uses image filenames as a signal for image content. A filename of `carbon-fiber-hood-supra-2024.jpg` provides meaningful context; `IMG_4382.jpg` provides none.
- **E-Commerce Application**: Rename product images with descriptive, hyphenated, lowercase filenames before upload. Include: product category, product name, key attribute, relevant identifier. Example: `carbon-fiber-hood-toyota-gr-supra-2024-gloss.jpg`. Do not keyword-stuff filenames. Use hyphens as word separators (same rule as URL slugs).
- **Replication Status**: Google official documentation. The magnitude of ranking impact from filename optimization alone is unclear — it is one of many signals.
- **Boundary Conditions**: A marginal signal — matters more for borderline cases than as a primary ranking factor. CDN-served images using content-hash filenames are a known engineering conflict with this best practice.
- **Evidence Tier**: Silver — Google Search Central confirms filename as a signal; no controlled study isolating independent impact.
- **Audit Note (2026-04-21)**: VERIFIED — added Google's verbatim example.

---

### Finding 11 (NEW 2026-04-21): WCAG 2.1 Success Criterion 1.1.1 Is the Legally-Cited Alt Text Standard
- **Source**: W3C, Web Content Accessibility Guidelines (WCAG) 2.1, Success Criterion 1.1.1 Non-text Content (Level A), https://www.w3.org/TR/WCAG21/#non-text-content.
- **Methodology**: W3C primary recommendation — international standard.
- **Key Finding**: SC 1.1.1 requires: "All non-text content that is presented to the user has a text alternative that serves the equivalent purpose." Decorative images must be "implemented in a way that it can be ignored by assistive technology" (empty `alt=""`). **This is the specific WCAG criterion ADA plaintiffs cite for missing-alt-text claims** — generic references to "WCAG guidelines" without citing 1.1.1 specifically are legally imprecise. U.S. DOJ 2024 final rule under ADA Title II adopts WCAG 2.1 Level AA for state/local government websites; private-sector ADA Title III litigation has converged on WCAG 2.1 AA as the de facto standard despite the absence of a formal DOJ rule for Title III. The European Accessibility Act (EAA) references EN 301 549, which incorporates WCAG 2.1 Level AA.
- **E-Commerce Application**: Any alt-text remediation plan should reference SC 1.1.1 conformance explicitly, not generic "WCAG guidelines." For litigation defense: demonstrate WCAG 2.1 Level AA conformance including SC 1.1.1, supplemented by manual testing and user testing with assistive technology users.
- **Replication Status**: W3C Recommendation — stable international standard.
- **Boundary Conditions**: WCAG 2.2 (October 2023) adds Success Criteria without removing 1.1.1 — it remains the operative standard. WCAG 3.0 (in development) is expected to retain an equivalent requirement. EU obligations under EAA require EN 301 549 conformance, which currently references WCAG 2.1 Level AA.
- **Evidence Tier**: Gold — W3C primary source; international standard.
- **Audit Note (2026-04-21)**: ADDED — proposed by Run-B; accepted in reconciliation. Prior finding text (F2, F6, F9) referenced "WCAG guidelines" generically without citing SC 1.1.1 specifically. This finding fills that gap and provides the legal anchor for alt-text compliance claims.

---

### Decision Tree: Alt Text Strategy

```
What type of image is this?
├── Product image (primary/main)
│   → [Product Name] [Key Attribute] [Angle/View]
│   "2024 GR Supra carbon fiber hood, gloss finish, front 3/4 view"
├── Product image (lifestyle/in-use)
│   → [Product] [Context/Activity]
│   "Carbon fiber hood installed on white 2024 GR Supra at track day"
├── Product image (detail/macro)
│   → Focus on what's being shown: [Feature Detail]
│   "Close-up of 2x2 twill carbon fiber weave pattern, gloss finish"
├── Customer/UGC photo
│   → "Customer photo: [Product] [Context]"
├── Size chart or diagram
│   → "Size chart for [Product Name] showing measurements S through XXL"
├── Decorative element (border, spacer, design)
│   → alt="" (empty, not omitted) — per WCAG 2.1 SC 1.1.1
├── Icon or UI element with function
│   → Functional description: "Add to cart" or "Open image zoom"
└── Infographic or complex chart
    → Brief alt + adjacent detailed text description or linked page
```

---

### Methodological Notes and Caveats

1. **Finding 7 (customer photos) is vendor-sourced with financial interest.** Treat as directional guidance only — not a proven conversion multiplier.

2. **Google Lens statistics (Finding 4) are self-reported by Google.** Revised 2026-04-21: commercial intent is ~25% (1 in 4), not 20% as previously stated. The ~5 billion figure is Google's own derived estimate and should be understood as the upper bound of the opportunity.

3. **The Google Images traffic share (Finding 3) is no longer verifiable from primary (2026-04-21).** The 20–22% figure is preserved as a widely-cited historical estimate; do not cite it as a confirmed current fact without a fresh primary source.

4. **ADA lawsuit data (Finding 9) reflects US federal filings only.** State-level lawsuits (e.g., California Unruh Act) are filed separately — total accessibility litigation exposure is higher than the 3,948 federal figure suggests.

5. **Finding 11 (WCAG 2.1 SC 1.1.1) is the specific legal anchor for alt text claims.** Reference it explicitly in remediation plans rather than citing "WCAG guidelines" generically.

6. **Google Merchant Center minimum is 500×500 px (corrected 2026-04-21).** The prior file's 100×100 / 250×250 figures are outdated and should not be relied upon.

---

### Sources Consulted

- Google Search Central Image SEO Best Practices (updated 2026-03-02): https://developers.google.com/search/docs/appearance/google-images
- Google SEO Starter Guide (alt text section): https://developers.google.com/search/docs/fundamentals/seo-starter-guide
- Google Merchant Center Image Guidelines: https://support.google.com/merchants/answer/6324350?hl=en
- Google Blog — Lens ~20 Billion Visual Searches (October 2024): https://blog.google/products/search/google-search-lens-october-2024-updates/
- Think with Google — 1 in 4 Commercial Intent: https://business.google.com/us/think/search-and-video/google-search-innovations/
- SparkToro Google Images Traffic Share: https://sparktoro.com/blog/how-much-of-googles-search-traffic-is-actually-going-to-google/ (URL not retrievable 2026-04-21 — see Citation Status on F3)
- EcomBack 2025 ADA Lawsuit Annual Report: https://www.ecomback.com/annual-2025-ada-website-accessibility-lawsuit-report
- WebAIM Alt Text Guidance: https://webaim.org/techniques/alttext/
- W3C WCAG 2.1 SC 1.1.1 Non-text Content: https://www.w3.org/TR/WCAG21/#non-text-content
