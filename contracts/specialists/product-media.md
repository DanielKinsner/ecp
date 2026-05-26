# Product Media Specialist (v2)

Per-cluster parameter file for the **product-media** specialist. Combined with the shared template body in [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) and per-engagement variables (cluster-context path, baton path, screenshots), this file produces the final dispatch prompt.

Covers the full visual media surface of a product page: gallery navigation mechanics, image quantity and type requirements, thumbnail design and category-grid UX, video presence and optimization, video schema markup, AR/3D visualization, and color accuracy — all eight reference files that feed the product-media cluster.

## Parameters

```yaml
cluster: product-media
references:
  - gallery-ux
  - image-quantity-types
  - thumbnail-design
  - video-integration
  - video-optimization
  - video-schema
  - ar-3d-visualization
  - color-accuracy
surface_vocabulary:
  - gallery
  - thumbnail-strip
  - hero-image
  - zoom-viewer
  - image-count-indicator
  - video-player
  - video-thumbnail
  - ar-viewer
  - swatch-selector
  - product-card-grid
target_finding_count: 4-7
```

The 8 reference files are sourced from [`contracts/cluster-routing.md`](../cluster-routing.md) "The 10 clusters" table for the product-media row. All 8 live at `${CLAUDE_PLUGIN_ROOT}/references/<file>.md`.

## Cluster guidance

The block below renders into the template at the `{{cluster_guidance}}` slot. It surfaces patterns the specialist should bias toward and edge cases the template body does not cover.

```
## Cluster guidance — product-media

Product-media findings are strongest when they name specific elements (gallery container,
thumbnail strip, video thumbnail, AR button, swatch selector) and cite measured signals
(image count, scroll position, file size, aspect ratio). Bias toward the following patterns.

### Gallery navigation mechanics (gallery-ux.md)

- **Dot vs. thumbnail navigation**: 50% of desktop users miss additional images when only
  dot indicators are shown (Baymard — Gold). Always flag dot-only navigation on desktop as
  a FAIL. On mobile, dots with a counter ("1 of 8") are a PARTIAL; a thumbnail strip is the
  full fix.
- **Mobile swipe support**: Swipe gesture is the baseline expectation on mobile. Confirm the
  gallery uses CSS scroll-snap (hardware-accelerated), not JavaScript scroll interception.
  Missing or broken swipe on a mobile PDP gallery is a HIGH-severity FAIL.
- **Image count signal**: Without a thumbnail strip or "N of N" counter, 50–80% of users
  overlook truncated images. Flag absence of any count signal as a FAIL when the gallery has
  4+ images.
- **Desktop zoom modalities**: Users expect both inline hover-zoom (2–3× magnifier following
  mouse) and click-to-fullscreen lightbox. Absence of either on a visual product is a
  MEDIUM FAIL. Zoom source images must be ≥2000px on shortest side — low-resolution sources
  with zoom enabled create a worse experience than no zoom.
- **LCP / first image loading**: The hero (position-1) gallery image is typically the LCP
  element. Flag `loading="lazy"` or missing `fetchpriority="high"` on the first gallery
  image as a MEDIUM performance finding. All position-2+ images should be lazy-loaded.
- **Keyboard accessibility**: Gallery thumbnails reachable by Tab, Arrow keys navigating
  between images, Escape closing lightbox — absence of any of these is a FAIL per WCAG 2.1
  SC 2.1.1. Include `role="region" aria-label="Product images"` and `aria-live="polite"`.
  Scope this finding with `scope: "page"` (device-independent accessibility requirement).
- **Quick View modals**: If a Quick View modal is present, evaluate whether it clearly
  distinguishes itself from the PDP (partial-screen, visible backdrop) and includes a
  "View Full Details" link. Full-viewport Quick Views that mimic the PDP are a MEDIUM FAIL
  due to back-button disorientation.

### Image quantity and types (image-quantity-types.md)

- **Category-specific minimums**: Apparel requires 8–15 images (5 minimum); electronics
  5–8; commodity 3–5; furniture 6–10 (Baymard — Gold, with paywall note). Audit actual
  image count from the baton's gallery element list or DOM slice. A product below minimum
  for its category is a HIGH FAIL.
- **Four universal image types**: Every product needs (1) hero/packshot, (2) lifestyle/
  context, (3) scale reference (hand, ruler, on-model height callout), (4) detail/close-up.
  Flag whichever types are missing. Scale reference absence is the most common gap —
  28% of major sites lack in-scale images (Baymard — Gold).
- **Color variant completeness**: Each visually distinct color variant requires its own
  photo set. Digitally colorized variants (single base photo recolored) are detectable by
  users and trigger distrust, particularly for textured materials. Flag colorized-only
  variants as a MEDIUM FAIL (cite image-quantity-types.md F7, color-accuracy.md F3).
- **Resolution floor**: Display images must be ≥1000px shortest side; zoom sources ≥2000px.
  If the DOM slice or screenshot shows pixelated or low-detail images, emit a FAIL citing
  image-quantity-types.md F8 (Baymard / Google — Gold).
- **fetchpriority on hero**: Per Google (Gold), apply `fetchpriority="high"` to exactly one
  hero image per page. If multiple images carry this attribute, dilution is the finding.

### Thumbnail design on category/collection pages (thumbnail-design.md)

- **Minimum 3 accessible thumbnails per listing**: On category/collection pages, each
  product card should expose at least 3 images via hover (desktop) or swipe (mobile).
  Single-image-only cards force unnecessary PDP navigation; flag as MEDIUM FAIL (Baymard —
  Gold).
- **Hover swap — packshot to lifestyle**: The packshot-to-lifestyle hover swap is the
  highest-ROI desktop interaction on category pages. Absence on a lifestyle-oriented
  category (apparel, home decor) is a MEDIUM finding. Ensure hover swap uses a CSS opacity
  transition (150–200ms) and that the hover image is preloaded to prevent visible flash
  on mouseenter.
- **Unified hit area**: The entire product card must be a single clickable region. Split hit
  areas (image links to PDP, title is plain text) are a FAIL — 76% of sites get this wrong
  (Baymard — Gold).
- **Consistent aspect ratio across grid**: Mixed aspect ratios break visual rhythm and
  increase scanning time by ~0.8s/row. Flag inconsistent ratios as a MEDIUM FAIL (Jenkins
  UsabilityHub n=150 + Baymard — Silver).
- **Badge quantity**: Maximum 2 badges per card. More than 2 creates visual noise that
  neutralizes each badge's effectiveness. If counting badges from the DOM, 3+ is a MEDIUM
  finding.
- **Mobile swipe in product cards**: Touch swipe in category-card image carousels must
  use CSS `scroll-snap`. JavaScript scroll interception on mobile cards is a HIGH FAIL.
- **Swatch display**: Up to 5 swatches shown in the listing; 6+ should show 4 + "+N more".
  Active swatch selection state must meet WCAG 1.4.11 Non-Text Contrast (≥3:1 contrast
  ring/border). Solid color fill swatches on textured products are a MEDIUM finding
  (cite thumbnail-design.md F11, color-accuracy.md F6).

### Video presence and integration (video-integration.md, video-optimization.md)

- **Gallery placement — position 2–3**: Video embedded in the product gallery at position
  2 or 3 receives 41% viewer rates; video buried in a separate tab or below the fold is
  missed by most visitors (35% of sites get placement wrong — Baymard 2019 — Gold). Flag
  absent-from-gallery video as a MEDIUM FAIL.
- **Video type match**: Usage/tutorial videos outperform appearance/beauty videos for
  purchase intention (Cheng et al. 2022 — Gold). For electronics, tools, fitness equipment:
  if only a brand/lifestyle video is present, note the mismatch. For apparel, lifestyle
  is appropriate.
- **Optimal length**: 30–60 seconds for PDP demo videos; 90 seconds is the outer limit
  before significant completion-rate degradation. Videos under 30 seconds that omit key
  features are PARTIAL. Videos over 90 seconds near the Add to Cart zone are a MEDIUM
  finding.
- **Autoplay**: Never with sound. Muted autoplay acceptable for loops ≤5 seconds with
  `autoplay muted loop playsinline`. Autoplay with audio is a HIGH FAIL — browsers block
  it, and NNGroup finds it universally negative (Gold).
- **Thumbnail / play button**: Video thumbnails should show a compelling still (not black
  screen or first-frame logo) plus a visible play button overlay. Missing play button is
  a LOW–MEDIUM finding. Duration indicator ("2:34") is recommended.
- **Captions**: All product videos with spoken content require WebVTT captions (`<track
  kind="captions">`) per WCAG 2.2 SC 1.2.2 Level A (Gold). EU EAA (effective 28 June
  2025) makes this a legal requirement for EU-facing merchants. Emit a HIGH FAIL if captions
  are absent on a narrated video.
- **Audio description**: Videos with significant visual-only action require an audio
  description track per WCAG 2.2 SC 1.2.5 Level AA. Flag absence for EU-facing merchants
  as a MEDIUM FAIL.
- **Performance — facade pattern**: Video embeds should use a facade (static poster image)
  that loads the player only on click. Eagerly loaded third-party video players (especially
  YouTube full embed) are a primary source of CLS and LCP degradation — SearchPilot found
  +4.1% organic traffic lift from removing video carousels with heavy CWV impact (Gold).
  Flag non-facade video embeds as MEDIUM on performance grounds.
- **Mobile video**: iOS requires `playsinline` to prevent forced fullscreen. File size
  target <5MB for PDP embedded video. Flag missing `playsinline` as a MEDIUM technical
  FAIL on a mobile viewport.
- **AI-generated video**: If any product video appears AI-generated (synthetic spokesperson,
  text-to-video output), it requires consumer-facing disclosure under FTC §5 / EU AI Act
  Article 50 (enforcement Aug 2, 2026). Describe the video content and flag absence of
  disclosure as a MEDIUM finding. Do not invoke ethics terms — describe neutrally as a
  disclosure gap; the ethics subagent handles the regulatory framing.

### Video schema (video-schema.md)

- **VideoObject schema presence**: Product pages with hosted video should have VideoObject
  JSON-LD. Required fields: `name`, `thumbnailUrl`, `uploadDate`. Recommended fields:
  `description`, `duration` (ISO 8601: `PT1M30S`), `contentUrl` or `embedUrl`. Missing
  VideoObject schema on a page with video is a MEDIUM SEO FAIL (Google Developers — Gold).
- **YouTube vs. self-hosted**: YouTube embeds show competitor ads after playback and send
  users off-site. For primary PDP video: self-hosted or dedicated CDN (Mux, Cloudflare
  Stream, Vimeo Pro) is the recommendation. YouTube-only for PDP primary is a MEDIUM
  finding. Tutorial/supplemental video on YouTube is acceptable.
- **CWV impact of video embeds**: Heavy third-party embeds (YouTube full player) cause
  CLS on page load. Flag non-facade YouTube embeds as a MEDIUM on CWV grounds, citing
  video-schema.md F6 (SearchPilot Gold).

### AR and 3D visualization (ar-3d-visualization.md)

- **Category fit for AR**: AR has strongest ROI for furniture, large home goods, eyewear,
  accessories, and products with specific size-fit uncertainty. For these categories on
  PDPs, absence of AR or 3D viewer is a LOW finding (note it; don't over-weight if other
  media gaps are present). For simple commodity products, absence of AR is not a finding.
- **Progressive enhancement**: AR button must only appear on AR-capable devices. If the
  DOM shows an AR button rendering on a desktop viewport, that is a MEDIUM finding —
  desktop users cannot use mobile AR, and a non-functional button creates confusion.
  3D model viewer (Google model-viewer) is the desktop equivalent.
- **3D model quality**: If a 3D viewer is present, evaluate visible quality signals in the
  screenshot: polygon artifacts, texture stretching, scale inaccuracy (product much larger/
  smaller than real object in AR context). Poor-quality 3D is a MEDIUM FAIL — low-quality
  models reduce conversion below good static images (Baymard extrapolation — Silver).
- **360 spin viewers**: For products where all-angle evaluation matters (shoes, bags, power
  tools), absence of a 360 viewer on an otherwise minimal gallery is a LOW finding. Note
  as an enhancement opportunity rather than a FAIL unless the gallery has fewer than 5 images.

### Color accuracy (color-accuracy.md)

- **Color variant photography completeness**: Cross-cluster with image-quantity-types.md F7
  — emit on this cluster. Flag digitally colorized variants as MEDIUM FAIL. Textured
  materials (fabric, leather, knitwear) cannot be represented via digital colorization.
- **Swatch type**: Solid color fill swatches misrepresent textured materials. Flag solid-
  fill swatches on fabric/upholstery products as a MEDIUM finding (color-accuracy.md F6 —
  Gold; Baymard).
- **Over-editing signals**: If the product screenshot shows unusually saturated colors,
  HDR-style contrast, or color grading that reads more like a lifestyle filter than an
  accurate product representation — flag as a MEDIUM finding, citing the arm's-length
  editing rule (color-accuracy.md F7 — Silver). Observation should describe the specific
  visual characteristic: "The product images show heavy saturation and warm color grading
  that may not match the physical item's color."
- **FTC materiality**: Color misrepresentation that makes a product appear materially
  different from what the customer will receive is within FTC §5 scope. Do not invoke
  ethics terms — emit the finding as a photography-accuracy issue describing the visual
  gap. The ethics subagent will surface the regulatory dimension separately.
- **AI image enhancement**: If product images appear AI-generated or AI-enhanced to a
  degree that changes apparent material properties (smooth texture where product is rough,
  color significantly different from the product name/label), flag it neutrally as a
  photography-accuracy gap. Do not invoke ethics terms.

### Edge cases

- **Pages without a product gallery** (homepage, category page, checkout): If no gallery
  surface exists in the cluster context, emit `status: "skipped"` with
  `skip_reason: "No product gallery surface routed to product-media cluster for this page
  type."` Do not force findings on a page that does not have the media surface this cluster
  audits.
- **Category/collection pages**: Your cluster scope includes thumbnail UX on collection
  pages (thumbnail-design.md). If the cluster context contains collection-page sections,
  audit hover states, card hit areas, badge counts, and swatch design — do not skip.
- **Homepage hero — no gallery present**: If a homepage hero has NO image at all (text-only
  or background-color-only hero where product imagery would be expected), emit a FAIL
  noting the absent media surface with `baton_index: "absent"`. A homepage for a product
  store with no hero imagery is a HIGH finding.
- **Video present but no gallery**: If the page has an embedded video but no product image
  gallery (video-only product page), audit video placement, type, length, thumbnail,
  captions, and schema. Emit `status: "complete"` with appropriate findings.
- **Variant-driven gallery**: Evaluate the default-state gallery (first-load image set).
  If the baton's `configured_state` or DOM slice includes a variant-selected state, note
  whether the image set changes appropriately when a color/size variant is selected — if
  variant selection does not update the gallery, that is a MEDIUM FAIL.

### When emitting PASS findings

A clean product-media setup has: 6+ images on a visual PDP (8+ for apparel), all four
universal image types present, thumbnail navigation with count signal, mobile swipe
functional, desktop zoom available, video at gallery position 2–3 with muted autoplay or
click-to-play and a compelling thumbnail, captions on narrated video, VideoObject schema
present, swatch photography (not solid fills) for textured variants, and consistent
photography style across the category grid. Note what is working — the synthesizer uses
PASS findings to balance the deliverable narrative.
```

## Reference file list (rendered into template)

For substitution into `{{reference_file_list}}`:

```
- `gallery-ux.md` — gallery navigation mechanics: thumbnail vs. dot navigation, swipe support, image count signals, zoom modalities, LCP/first-image performance, keyboard accessibility, Quick View UX
- `image-quantity-types.md` — image count requirements by category (apparel 8–15, electronics 5–8, commodity 3–5), the four universal image types, color variant completeness, resolution standards, fetchpriority
- `thumbnail-design.md` — category-page thumbnail UX: accessible image counts per listing, hover swap, unified card hit areas, aspect ratio consistency, badge limits, mobile swipe in cards, swatch display and WCAG contrast
- `video-integration.md` — video type effectiveness (usage vs. beauty), gallery placement (position 2–3), optimal length (30–60s), autoplay rules, thumbnail design, AI-generated video legal exposure (FTC §5 / EU AI Act)
- `video-optimization.md` — autoplay behavior, PDP video length, video type matching, mobile delivery (playsinline, <5MB), captions (WCAG 1.2.2 Level A), audio description (WCAG 1.2.5 Level AA), codec selection (AV1/H.264), AI-generated video technical disclosure
- `video-schema.md` — VideoObject required/recommended fields, YouTube vs. self-hosted for conversion, CWV impact of video embeds (SearchPilot +4.1% from removal), UGC video, video ROI by product type
- `ar-3d-visualization.md` — AR/3D conversion data (Shopify 94% — vendor-flagged), category fit, WebAR vs. native AR, progressive enhancement hierarchy (static → 360 → 3D → AR), 3D model quality thresholds, ROI framework
- `color-accuracy.md` — return rate impact (22–30% of apparel returns from color mismatch), variant photography requirements, photo editing limits (ΔE₀₀ <3 target), swatch photography standards, multi-condition photography, FTC §5 color misrepresentation, AI image enhancement regulatory obligations
```

## Cross-references

- [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) — shared template body this file parametrizes
- [`contracts/cluster-routing.md`](../cluster-routing.md) — canonical reference list source for product-media row
- [`schema/cluster-emission-v1.json`](../../schema/cluster-emission-v1.json) — output shape
- [`schema/finding-v1.json`](../../schema/finding-v1.json) — per-finding shape
- [`scripts/test-specialist.py`](../../scripts/test-specialist.py) — harness that combines this file + template + per-engagement vars
- [`references/evidence-tiers.md`](../../references/evidence-tiers.md) — Gold/Silver/Bronze definitions required for `evidence_tier` and `reference_citations[].tier`
