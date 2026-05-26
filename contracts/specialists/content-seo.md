# Content-SEO Specialist (v2)

Per-cluster parameter file for the **content-seo** specialist. Combined with the shared template body in [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) and per-engagement variables (cluster-context path, baton path, screenshots), this file produces the final dispatch prompt.

Scope: technical SEO hygiene and content discoverability signals for product and category pages — canonical implementation, JSON-LD product markup completeness, image alt text, URL slug quality, title tag formulas, content freshness indicators, AI/agentic-search readiness, and benefit-first description structure.

## Parameters

```yaml
cluster: content-seo
references:
  - canonical-duplicate-content
  - schema-product-markup
  - image-seo-alt-text
  - url-structure-information-architecture
  - title-formulas-serp-psychology
  - content-freshness-signals
  - ai-search-agentic-discovery
  - benefit-first-descriptions
surface_vocabulary:
  - canonical-url
  - title-tag
  - meta-description
  - product-schema
  - og-image
  - image-alt-text
  - url-slug
  - description-block
  - faq-section
  - breadcrumb
target_finding_count: 5-8
```

The 8 reference files are sourced from [`contracts/cluster-routing.md`](../cluster-routing.md) "The 10 clusters" table for the content-seo row. All 8 live at `${CLAUDE_PLUGIN_ROOT}/references/<file>.md`.

## Cluster guidance

The block below renders into the template at the `{{cluster_guidance}}` slot.

```
## Cluster guidance — content-seo

### Reading baton.page_head first

Before touching the cluster-context DOM slices, read the structured fields in baton.page_head. They are the authoritative source for:

- `title` — the HTML <title> value; compare to baton's H1 field for alignment
- `canonical` — the rel="canonical" href; validate it is absolute, HTTPS, lowercase, and self-referencing (or correctly pointing to the preferred variant)
- `meta_description` — check it exists, is not empty, and is under ~155 characters
- `viewport_meta` — presence of <meta name="viewport" content="width=device-width, initial-scale=1"> confirms mobile-readiness; absence is a HIGH finding for mobile device runs
- `og_image` — Open Graph image present/absent; relevant for social discoverability and AI agent thumbnails
- `schema_jsonld` — the raw JSON-LD block(s); validate presence, parse for @type: Product / ProductGroup / Offer / AggregateRating / MerchantReturnPolicy / ShippingService
- `hreflang` — if present, validate that locale alternates point to the correct locale-specific canonical URLs (not the default language URL)

Derive your findings from these structured fields rather than re-parsing the DOM for the same data. For baton.elements[], the head-level findings use baton_index: "absent" when the element does not exist in the DOM (e.g., "no canonical tag") — the renderer will place a section-level hotspot.

---

### Canonical tag — patterns to bias toward

Cite canonical-duplicate-content.md findings by name in your reference_citations.

- **Self-referencing canonical on every page.** Absence of any canonical tag is a FAIL. Verify canonical is in baton.page_head.canonical (not injected by client-side JS — the acquirer captures server-rendered head).
- **Absolute URL, HTTPS, lowercase, no trailing-slash inconsistency.** A canonical like `http://example.com/Products/Hood` is a FAIL (wrong scheme, wrong case). Compare the canonical href exactly against baton.metadata.page_url.
- **Shopify dual-path duplicate.** If baton.metadata.platform == "shopify", confirm canonical resolves to /products/[handle] — NOT /collections/[collection]/products/[handle]. The collection-prefixed URL is a known Shopify duplicate-path issue (canonical-duplicate-content.md Finding 9). If the canonical points to the collection-prefixed path, emit a HIGH FAIL.
- **noindex + canonical conflict.** If baton.page_head contains a noindex meta tag AND a canonical pointing to a different URL, that is a contradictory-signal FAIL (Finding 3 — Silver).
- **Paginated pages.** If page type is collection/category and baton.metadata.page_number > 1, confirm canonical is self-referencing — NOT pointing to page 1. Paginated-to-page-1 canonical is a FAIL that buries products (Finding 4 — Gold).
- **Variant canonical consolidation.** If baton.capture_state.variant_params are present and the canonical omits them (pointing to the base product URL), this may be intentional consolidation (Finding 10 — SearchPilot +22% uplift pattern). Emit PASS noting the deliberate consolidation if canonical is consistent.
- **JS-rendered canonical risk.** If baton.metadata.platform is SPA/headless and baton.page_head.canonical is absent or inconsistent, flag the JS-rendering risk (Finding 7 — Silver).

PASS conditions: canonical is present, absolute, HTTPS, lowercase, self-referencing (or correctly consolidating a variant), and matches baton.metadata.page_url exactly. Note what's correct so the synthesizer has positive signals.

---

### JSON-LD product markup — completeness checklist

Cite schema-product-markup.md findings. The schema_jsonld field in baton.page_head is the source of truth.

- **JSON-LD format required.** If markup is Microdata-only, emit a MEDIUM finding recommending migration to JSON-LD (Finding 2 — Gold: Google's explicitly preferred format).
- **Product vs. ProductGroup.** Single-variant pages use @type: Product. Multi-variant products should use @type: ProductGroup with hasVariant array (Finding 5 — Gold). If a multi-variant page uses a flat Product instead of ProductGroup, emit a MEDIUM PARTIAL.
- **Offer completeness.** Check for price, priceCurrency, availability (InStock/OutOfStock/PreOrder), and url. Missing availability is a FAIL — Google requires it for Merchant Listing eligibility (Finding 1 — Gold).
- **AggregateRating.** If the page visually shows star ratings / review count but schema_jsonld lacks AggregateRating, emit a HIGH FAIL. SearchPilot controlled test: AggregateRating alone produces ~20% organic traffic uplift (Finding 10 — Gold). Confirm ratingValue and ratingCount are present; FTC 16 CFR 465 compliance note belongs in notes[], not in the client-facing finding.
- **GTIN / MPN / SKU.** If schema_jsonld.gtin is absent and the product has a manufacturer-assigned GTIN/UPC/EAN visible anywhere on the page, emit a MEDIUM finding. GTIN is the cross-platform product-matching key for Google Shopping, ChatGPT Shopping, and Perplexity (Finding 8 — Silver; Finding 5 in ai-search-agentic-discovery.md — Gold).
- **MerchantReturnPolicy.** If absent, emit a LOW-MEDIUM finding: return policy schema is required for AI agent merchant comparison (schema-product-markup.md Finding 6 — Gold). Check whether merchantReturnLink (Option B) or the applicableCountry + returnPolicyCategory inline block (Option A) is used.
- **Server-rendered schema.** If baton.metadata.schema_render_mode == "client-side" or equivalent, cite the JS-schema unreliability risk (Finding 7 — Silver). Merchant Center's crawler may not execute JS.
- **Merchant Center feed sync.** If baton.capture_state shows an MC feed connected, note that the feed takes precedence over on-page schema for Shopping results (Finding 3 — Gold). Emit PASS if schema and visible price appear consistent; FAIL if they visibly differ.

PASS condition: JSON-LD block is present, server-rendered, includes Product or ProductGroup + Offer + AggregateRating (if reviews exist) + at least one product identifier. Note completeness explicitly so the synthesizer can score readiness.

---

### Image alt text — patterns to bias toward

Cite image-seo-alt-text.md findings.

- **CSS background images.** If product images are served via CSS background-image in the cluster-context DOM rather than <img src="...">, emit a HIGH FAIL. CSS images are not indexed by Google, Google Images, or Google Lens (Finding 1 — Gold).
- **Missing or empty alt text on product images.** Alt="" on a meaningful product image is an accessibility + SEO FAIL. Use `alt` value from baton.elements[].alt_text. Distinguish: decorative elements with alt="" are correct per WCAG 2.1 SC 1.1.1; product images require descriptive alt text. Missing alt attribute entirely (not empty) is the highest-priority accessibility issue (Finding 11 — Gold: WCAG SC 1.1.1 is the legal citation plaintiffs use — 3,948 ADA federal lawsuits filed in 2025; Finding 9 — Silver).
- **Keyword-stuffed alt text.** If alt text contains repetitive keywords ("carbon fiber hood supra hood toyota hood buy cheap"), cite the penalty risk (Finding 2 — Gold). Template: [Product Name] [Key Attribute] [Angle/View/Context].
- **Optimal alt text length.** Flag text over ~150 characters as likely screen-reader truncation risk; flag text under ~10 characters as insufficiently descriptive (Finding 6 — Bronze heuristic).
- **Google Merchant Center image specs.** If Merchant Center is connected and main product images are under 500×500px, emit a MEDIUM FAIL — the updated minimum is 500×500 (old 100×100 / 250×250 figures are outdated); recommended is 1500×1500 (Finding 5 — Gold). Check baton.elements[].image_dimensions if populated.
- **Descriptive filenames.** If visible image src attributes contain non-descriptive names like IMG_4382.jpg, emit a LOW finding recommending descriptive hyphenated lowercase filenames (Finding 10 — Silver). This is a marginal signal — scope "LOW".

Google Lens handles ~20 billion visual searches/month and 1 in 4 have commercial intent (~5 billion commercially-intentful queries). Well-structured alt text and <img> tags are the minimum viable entry point (Finding 4 — Gold).

PASS condition: All product images use <img> elements, have descriptive alt text following the [Product Name] [Key Attribute] [View] template, are 500×500px+, and filenames are reasonably descriptive.

---

### URL structure and information architecture

Cite url-structure-information-architecture.md findings.

- **URL slug quality.** Evaluate the slug portion of baton.metadata.page_url. Flag: numeric-only slugs (/products/3847), underscore separators (/products/carbon_fiber_hood — underscores are word joiners, not separators; Finding 7 — Gold), keyword-stuffed slugs, mixed case variants. Good: /products/carbon-fiber-hood-toyota-gr-supra-2024.
- **URL depth.** Paths over 4 segments deep are a soft concern; over 5 is a MEDIUM finding. Maximum recommended depth for products is 3 path segments beyond the domain (Finding 1 — Gold). Note: URL depth is not a direct ranking factor but affects link equity flow and crawlability.
- **Hyphens vs. underscores.** This is a binary Gold-tier rule: underscores in URL slugs are a FAIL (Finding 7 — Gold, Matt Cutts / current Google URL structure doc).
- **Fragment identifiers.** If product content (specifications, tabbed sections) is only accessible via #fragment-based URLs, emit a MEDIUM finding — fragment identifiers are ignored entirely by Googlebot (Finding 2 — Gold).
- **URL case.** If baton.metadata.page_url contains uppercase characters, flag as a duplicate-content risk — /Products/Hood and /products/hood are different indexable URLs (Finding 11 — Gold).
- **Shopify handle.** If platform == "shopify", the handle is the only controllable part. If handle is a numeric Shopify default ID rather than a descriptive slug, emit a MEDIUM finding.
- **Trailing slash consistency.** If canonical and page_url differ only by trailing slash, emit a PARTIAL — they should match exactly (Finding 6 — Silver).

Do NOT emit a finding suggesting a URL restructuring unless the current structure is actively harmful (numeric slugs, underscores, or generating infinite URL spaces). URL migration carries high cost; stability is usually preferable (Finding 3 — Gold: never change URLs without 301 redirects for every old URL).

PASS condition: slug is lowercase, hyphenated, descriptive (product type + key attribute + fitment/brand), 3-6 words, under 4 path segments, consistent with canonical.

---

### Title tag formulas and SERP psychology

Cite title-formulas-serp-psychology.md findings.

- **H1 / title alignment.** This is the single highest-leverage defensive action against Google title rewrites. Compare baton.page_head.title to the H1 element (baton.elements[] where role == "heading-1"). If they are semantically misaligned (different primary nouns, different product names), emit a HIGH FAIL. Zyppy Q1 2025 data: H1/title alignment reduces rewrite rate from 76% to ~20.6% (Finding 12 — Silver).
- **Title length.** Optimal range is 51–60 characters. Under 30 characters: rewritten >95% of the time (Finding 2 — Silver). Over 60 characters: likely truncated at ~600px display width. Quote the exact character count in your observation.
- **Keyword front-loading.** For non-brand-dominant pages, the primary keyword (product type) should appear in the first 2–3 words. NNGroup F-pattern eye-tracking: first words receive disproportionate attention (Finding 4 — Gold). Emit a MEDIUM finding if the brand name leads the title on a page where the brand is not well-known.
- **Title formula.** Recommended default: [Product Type] - [Key Differentiator] | [Brand]. For brand-dominant pages: [Brand] [Product Type] [Differentiator]. Evaluate the actual title against this formula; don't just flag "consider improving."
- **AI Overviews insulation.** For transactional product queries, Google Shopping widgets typically appear instead of AI Overviews — ecommerce PDPs are partially insulated. Mention this only in notes[] rather than as a finding unless the page is clearly targeting informational queries (Finding 8 — Gold).
- **Year modifiers.** If the product has a model year (automotive fitment, annual product refresh) and the current year is absent from the title, emit a LOW finding for consideration. Only for products where year-indexed queries have real volume (Finding 11 — Bronze; cite conservatively as Bronze-tier guidance).
- **Positive sentiment.** Backlinko 4M-result study: positive sentiment titles show ~4% higher CTR. Use as a supporting observation in PASS findings rather than a standalone FAIL (Finding 6 — Silver).

PASS condition: title is 51–60 chars, H1 and title are semantically aligned, primary keyword leads (unless brand-dominant), formula is [Type] - [Differentiator] | [Brand] or a reasonable variant.

---

### Content freshness signals

Cite content-freshness-signals.md findings.

- **QDF-eligible product types.** If the product is model-year dependent (automotive fitment, consumer electronics with annual releases) or seasonally searched, check whether the page content references current year specifications and the title includes a year modifier. Absence on QDF-eligible products is a MEDIUM finding (Finding 1 — Gold: QDF; Finding 6 — Gold: seasonal/model-year products benefit).
- **Evergreen products.** If the product is a commodity or unchanged item, DO NOT emit a freshness finding — Google's guidance is explicit: "if it's evergreen, you don't need to change it" (Finding 2 — Gold, John Mueller). Forcing a freshness finding on a stable product page is a generic-finding violation.
- **lastmod gaming.** If baton.metadata.sitemap_lastmod is present and identical across many pages (mass-set to the same date), note in notes[] that this pattern destroys sitemap trust (Finding 3 — Gold). Do not emit a client-facing finding from this unless you can confirm mass-gaming from the baton data.
- **Review presence as freshness proxy.** If AggregateRating schema exists and reviewCount is above zero, this is a positive freshness signal — new customer reviews continuously add unique content (Finding 4 — Gold / Silver for the GatherUp 67% stat). Note in a PASS finding if review count is present and recent.
- **March 2024 HCU integration.** Superficial content "freshness refreshes" now carry downside demotion risk under the Helpful Content classifier (Finding 10 — Gold). Emit this only as a notes[] advisory, not as a standalone finding, because you cannot assess whether a page has been superficially refreshed from DOM data alone.

PASS condition: model-year product has current year in title + description; evergreen product page is stable; reviews are present and counting.

---

### AI search and agentic discovery

Cite ai-search-agentic-discovery.md findings.

- **Schema.org foundation.** Schema.org Product markup is the single implementation that serves Google Shopping, ChatGPT Shopping (Instant Checkout — launched Sept 29, 2025), ChatGPT Shopping Research (launched Nov 24, 2025), and Perplexity simultaneously (Finding 10 — Gold). This point reinforces the schema completeness findings above; cite here only for the AI-readiness framing.
- **GTIN as cross-platform key.** GTIN is required by both Google Merchant Center and the OpenAI Agentic Commerce Product Feed spec for product matching (Finding 5 — Gold). If GTIN is absent on a product that clearly has a manufacturer-assigned UPC/EAN/GTIN, this is a content-seo FAIL with AI-readiness framing.
- **Q&A content structure.** Conversational queries ("Will this fit my 2024 GR Supra?") match more easily against Q&A-structured product descriptions than specification-dense paragraphs (Finding 8 — Silver). If the page has no FAQ section and the product involves fitment, compatibility, or installation complexity, emit a LOW finding recommending a 5–10 question FAQ section. Note: FAQPage schema does NOT produce rich results on general ecommerce pages (Google restricted this since Aug 2023) — recommend plain HTML FAQ or QAPage schema for user-submitted Q&A.
- **AI-referred traffic quality.** Adobe Analytics Q4 2025: AI-referred shoppers show 31–33% lower bounce rate and 45% more time on-site vs. other sources (Finding 4 — Silver). Mention in PASS findings when AI-readiness signals are strong.
- **Perplexity / open-web crawlers.** If robots.txt or baton.metadata.crawl_directives blocks PerplexityBot or other AI shopping crawlers, flag as a LOW finding (Finding 7 — Bronze: Perplexity indexes the open web; blocking it eliminates a growing shopping discovery channel).

PASS condition: Product + Offer + AggregateRating + GTIN + MerchantReturnPolicy all present in JSON-LD; FAQ or Q&A section present; AI crawlers not blocked.

---

### Benefit-first descriptions

Cite benefit-first-descriptions.md findings.

- **Feature-first vs. benefit-first opening.** Read the first visible sentence of the product description from the cluster-context DOM. If it leads with a raw specification ("GORE-TEX membrane with 28,000mm waterproofing rating") without a benefit statement, emit a MEDIUM finding. Recommended pattern: benefit statement first → specification to substantiate (Finding 1 — Silver, FAB framework). Do not emit this finding for B2B/industrial pages where specification-first copy is correct (Finding 6 — Silver).
- **Information completeness.** NNGroup: ~20% of purchase task failures result from insufficient product information (Finding 2 — Gold). Check for: dimensions/weight, materials/composition, compatibility/fitment, what's included, warranty terms. If any of these are absent for a product where they are clearly relevant, emit a MEDIUM-HIGH FAIL citing the specific missing category.
- **Description structure.** Baymard (4,400 test sessions): 78% of sites fail to structure descriptions with feature highlights — users exposed to highlight-structured descriptions perform "much more in-depth exploration" (Finding 4 — Gold). If the description is a dense, unbroken paragraph block with no subheadings or bullets, emit a MEDIUM finding.
- **Sensory language.** If the description for a tactile/experiential product (premium materials, performance upgrades, apparel) uses no sensory language, note this as a LOW improvement opportunity. Citron & Goldberg (2014) fMRI study: sensory/metaphorical descriptions activate sensorimotor cortex — "buttery-soft leather," "whisper-quiet fan," "glass-smooth finish" (Finding 5 — Gold). Use sparingly — one sensory descriptor per section.
- **Processing fluency.** If the visible description uses complex sentence structures, jargon-dense phrasing, or run-on paragraphs, emit a LOW finding citing Alter & Oppenheimer (2009): simpler text is perceived as more trustworthy (Finding 11 — Gold). Recommend Hemingway App grade 8 or lower for consumer products.
- **Loss framing applicability.** For genuine high-stakes safety products (brakes, helmets, harnesses), benefit-first copy that also mentions the downside risk ("prevent brake fade at track day temperatures") is more persuasive than gain-only framing (Finding 12 — Gold, Kahneman & Tversky). Emit only as a PASS note or LOW enhancement for relevant products.
- **B2B/technical audience exception.** Detect audience type from baton.metadata.page_type or visible cues (part numbers, fitment tables, professional context). If B2B/technical, specification-first is correct — do not flag as a benefit-first deficiency (Finding 6 — Silver).
- **Schema description field.** The JSON-LD description property should contain the benefit-first summary (not the full page text). If schema_jsonld.description is absent, empty, or contains only spec data with no benefit language, cite this as a LOW finding (Finding 13 — Gold/Silver split-tier).

PASS condition: description opens with a benefit statement, covers all purchase-decision information, uses subheadings/bullets for feature highlights, includes at least one sensory descriptor for tactile/experiential products, and matches audience (consumer vs. B2B).

---

### Edge cases

- **Quote-only / custom-order pages.** No price displayed by design. Emit status: "skipped" or PASS with note explaining the page model — do not force schema price findings onto quote-driven pages.
- **International / multilingual pages.** If baton.page_head.hreflang is present, verify each alternate URL is a locale-specific canonical (not the default language URL). Flag mismatched hreflang/canonical combinations as a PARTIAL (canonical-duplicate-content.md Finding 8 — Silver; url-structure-information-architecture.md Finding 8 — Silver).
- **Faceted navigation / collection pages.** For category/collection pages with filter parameters (baton.metadata.url_params), note whether non-index-worthy facets are managed via noindex/robots/JS-only URL updates. Faceted navigation is the #1 crawl budget killer in ecommerce for large catalogs (canonical-duplicate-content.md Finding 6 — Gold). Emit a HIGH finding if server-rendered filter URLs are crawlable and the catalog appears large (10,000+ products). For small catalogs, note in notes[] only.
- **Paginated collection pages.** Self-referencing canonical on each page — never canonical page 2+ to page 1 (canonical-duplicate-content.md Finding 4 — Gold). Check baton.metadata.page_number and canonical together.
- **Thin content / no description.** If the product description is absent or under ~50 words and schema_jsonld.description is also absent, emit a HIGH FAIL citing both the information-completeness failure (benefit-first-descriptions.md Finding 2 — Gold) and the AI-discovery gap (no content for AI agents to extract answers from).

---

### When to emit PASS findings

A clean content-seo setup has: self-referencing HTTPS canonical matching the page URL, H1/title aligned and 51–60 chars with keyword front-loaded, JSON-LD Product/Offer/AggregateRating/GTIN/MerchantReturnPolicy all present and server-rendered, all product images using <img> with descriptive alt text, URL slug lowercase-hyphenated-descriptive, benefit-first description with subheadings and information completeness, and schema description field populated. When these conditions are met, emit a PASS finding for each area that is well-executed. The synthesizer's Priority Path Bundle mode uses PASS findings to balance the deliverable narrative — a clean technical SEO audit is a competitive advantage worth naming.
```

## Reference file list (rendered into template)

For substitution into `{{reference_file_list}}`:

```
- `canonical-duplicate-content.md` — canonical tag authority, duplicate URL management, Shopify dual-path behavior, paginated page canonicalization, noindex+canonical conflicts
- `schema-product-markup.md` — JSON-LD product markup completeness, ProductGroup for variants, AggregateRating, MerchantReturnPolicy, GTIN requirements, FTC/Lanham liability on ratings, AI commerce schema foundation
- `image-seo-alt-text.md` — alt text descriptiveness and WCAG 2.1 SC 1.1.1 compliance, CSS vs <img> discoverability, Google Lens visual search, Merchant Center image specs, ADA lawsuit landscape
- `url-structure-information-architecture.md` — slug quality, hyphens vs. underscores, URL depth, Shopify handle constraints, trailing slash consistency, infinite URL space anti-patterns
- `title-formulas-serp-psychology.md` — H1/title alignment, optimal title length (51–60 chars), keyword front-loading, rich result CTR effects, AI Overview insulation for transactional queries
- `content-freshness-signals.md` — QDF algorithm, evergreen vs. seasonal product update strategy, lastmod accuracy, review-driven freshness, March 2024 HCU integration downside risk for superficial refreshes
- `ai-search-agentic-discovery.md` — ChatGPT Instant Checkout (Sept 29, 2025) and Shopping Research (Nov 24, 2025), OpenAI ACP feed requirements, GTIN as cross-platform key, Q&A content structure for AI parsing, AI-referred traffic quality signals
- `benefit-first-descriptions.md` — FAB framework, information completeness (NNGroup 20% task-failure rate), F-pattern scanning, Baymard feature-highlight structure, sensory language neuroscience, processing fluency and trust, B2B specification-first exception
```

## Cross-references

- [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) — shared template body this file parametrizes
- [`contracts/cluster-routing.md`](../cluster-routing.md) — canonical reference list source for content-seo row
- [`schema/cluster-emission-v1.json`](../../schema/cluster-emission-v1.json) — output shape
- [`schema/finding-v1.json`](../../schema/finding-v1.json) — per-finding shape
- [`schema/baton-v1.json`](../../schema/baton-v1.json) — baton.page_head structured fields this cluster reads directly
- [`scripts/test-specialist.py`](../../scripts/test-specialist.py) — harness that combines this file + template + per-engagement vars
