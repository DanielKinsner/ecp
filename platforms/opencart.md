<!-- RESEARCH_DATE: 2026-04-08 -->
# OpenCart Platform Reference

Platform-specific patterns for the ECP builder when generating OpenCart code. Loaded only during the builder phase when `platform: "opencart"` is detected or forced.

## Detection

OpenCart is auto-detected by the heuristics in `${CLAUDE_PLUGIN_ROOT}/contracts/platform-detection.md`. The highest-confidence markers are:

- **URL patterns:** `index.php?route=product/product`, `index.php?route=common/home`, `index.php?route=checkout/checkout`, `route=account/login`
- **Directory structure:** `catalog/view/theme/{theme-name}/` is the OpenCart theme root
- **Meta generator:** `<meta name="generator" content="OpenCart X.Y.Z.Z">` (present in default templates, may be stripped in customized themes)
- **Journal3 marker:** `/catalog/view/theme/journal3/` — Journal3 is the dominant commercial theme for OpenCart 3.x/4.x and is worth detecting separately because its layout system differs from vanilla OpenCart
- **Session cookie:** `OCSESSID=` in `Set-Cookie` headers

**Versions supported:**
- OpenCart 2.x — legacy, still widely deployed on older stores. Template extension: `.tpl`
- OpenCart 3.x — current mainstream. Template extension: `.twig`
- OpenCart 4.x — newest, not widely adopted. Template extension: `.twig`
- Journal3 theme (3.x+) — commercial theme with its own layout builder; treat as a sub-platform

If version detection fails, assume 3.x (the most common current deployment).

---

## Theme directory structure

```
catalog/
├── view/
│   ├── theme/
│   │   ├── default/                       # Vanilla OpenCart default theme
│   │   │   ├── template/
│   │   │   │   ├── common/
│   │   │   │   │   ├── home.twig          # Homepage template
│   │   │   │   │   ├── header.twig        # Site header + nav
│   │   │   │   │   └── footer.twig        # Footer
│   │   │   │   ├── product/
│   │   │   │   │   ├── product.twig       # Product detail page
│   │   │   │   │   ├── category.twig      # Category / collection page
│   │   │   │   │   └── search.twig        # Search results
│   │   │   │   ├── checkout/
│   │   │   │   │   ├── cart.twig          # Cart page
│   │   │   │   │   └── checkout.twig      # Checkout wrapper
│   │   │   │   └── account/
│   │   │   ├── stylesheet/
│   │   │   │   └── stylesheet.css         # Main theme CSS
│   │   │   ├── javascript/
│   │   │   │   └── jquery/                # jQuery-based — OpenCart is jQuery-native
│   │   │   └── image/
│   │   └── journal3/                      # Journal3 commercial theme (if installed)
│   │       ├── template/
│   │       ├── stylesheet/
│   │       └── javascript/
│   └── javascript/
│       └── common.js                      # Global JS (cart update, search, etc.)
system/
└── storage/
    └── modification/                      # OCMOD modifications applied here
        └── catalog/
            └── view/
                └── theme/
                    └── ...                # OCMOD-patched copies of theme files
```

**Critical rule:** if OCMOD modifications are present in `system/storage/modification/catalog/view/theme/`, OpenCart reads the modified copy at runtime, NOT the original `catalog/view/theme/` file. Editing the original and leaving the modification cache stale causes confusing "my change doesn't show up" bugs. Always either (a) refresh the modification cache after direct edits, or (b) apply changes via OCMOD XML.

---

## Modification patterns

OpenCart has THREE distinct ways to customize a theme. The builder must pick the right one based on the change:

### 1. Direct theme file edits (fastest, least portable)

Edit `.twig` files in `catalog/view/theme/{theme-name}/template/` directly. Best for:

- One-off customizations on a store the user maintains themselves
- Text changes, CTA copy tweaks, section reordering, CSS adjustments
- Changes that don't need to survive a theme update

**After direct edits, clear the modification cache AND the theme cache:**
```
Admin → Dashboard → Clear cache (twice: once for "Modification", once for "Theme")
OR via CLI: rm -rf system/storage/cache/*
```

Without the cache clear, the changes won't show up on the live site even though the file was saved.

### 2. OCMOD (OpenCart Modification) XML — portable, installable

OCMOD is OpenCart's official modification system. You write an `install.xml` that describes file patches, and OpenCart applies them at install time into the `system/storage/modification/` virtual overlay. Best for:

- Packageable customizations that ship as a ZIP installable via admin
- Changes that should survive theme updates
- Any modification you want to distribute to multiple stores

**Basic OCMOD structure:**
```xml
<?xml version="1.0" encoding="utf-8"?>
<modification>
    <name>ECP — Add trust badges to product page</name>
    <code>ecp-trust-badges</code>
    <version>1.0</version>
    <author>ECP Builder</author>

    <file path="catalog/view/theme/*/template/product/product.twig">
        <operation>
            <search><![CDATA[{{ price }}]]></search>
            <add position="after"><![CDATA[
                <div class="ecp-trust-badges">
                    <img src="/image/trust/free-shipping.svg" alt="Free shipping over $75">
                    <img src="/image/trust/secure-checkout.svg" alt="Secure checkout">
                    <img src="/image/trust/30-day-returns.svg" alt="30-day returns">
                </div>
            ]]></add>
        </operation>
    </file>
</modification>
```

The `path="catalog/view/theme/*/template/..."` wildcard applies the patch to every installed theme, which is crucial for multi-theme stores.

### 3. vQmod — legacy, OpenCart 1.5 / some 2.x stores

vQmod predates OCMOD and used an XML format in `vqmod/xml/`. Some older themes still rely on it. Detection: presence of `vqmod/` directory at repo root. If vQmod is active, the builder should treat it the same as OCMOD — patch via XML file rather than direct edits — but target the `vqmod/xml/` directory instead.

**Rule of thumb:** Use OCMOD for OpenCart 2.x/3.x/4.x. Only touch vQmod if the store is on OpenCart 1.5 or the theme explicitly uses it.

---

## Journal3 theme specifics

Journal3 is the dominant commercial theme for OpenCart 3.x+ and has its own layout system that sits on top of OpenCart's theme engine. If you detect Journal3, the rules change:

- **Theme files live in:** `catalog/view/theme/journal3/template/` (standard) AND `system/storage/modification/catalog/view/theme/journal3/` (modified overlay).
- **Layout builder:** Journal3 has a GUI layout builder in the admin (Journal → Modules → Page Layouts) that stores its configuration in the database, not in template files. Many "where is this element defined?" questions for Journal3 stores are answered in the database, not in `.twig` files. Builder teammates should note this in their plan — "edit via admin Layout Builder" is a legitimate implementation step.
- **Module system:** Journal3 uses its own "modules" (custom blocks, banners, tabs, testimonials) that are configured in admin → Journal → Modules → [Module Type]. These modules inject HTML into the page at render time.
- **Journal3 JS bundles** can be heavy and may delay hydration. Acquisition agents should wait at least 5 seconds after DOMContentLoaded on Journal3 stores before capturing the DOM, because some Journal3 components (product carousels, tab content, lazy-loaded testimonials) don't render until after hydration completes.
- **Journal3 CSS customization:** `catalog/view/theme/journal3/stylesheet/custom.css` is the conventional safe place for custom CSS that survives theme updates.

If the detection heuristics flag Journal3, treat the cluster routing's `platform-detection.md` output as `"opencart"` but note `journal3: true` in the context hint passed to the builder.

---

## Common implementation patterns for ECP recommendations

### CTA text / button copy changes

- **Product page CTAs** — `catalog/view/theme/{theme}/template/product/product.twig`, look for the Add to Cart button (often `<button id="button-cart">` or `<button data-button="cart">`).
- **Cart page CTAs** — `catalog/view/theme/{theme}/template/checkout/cart.twig`
- **Checkout flow CTAs** — `catalog/view/theme/{theme}/template/checkout/checkout.twig` (wrapper) plus individual step templates in the same directory

### Price display changes (pricing psychology, anchoring)

- **Main price element:** `{{ price }}` in the Twig template is the current price. For MSRP/strikethrough, OpenCart has a `{{ special }}` field (the discount price) and `{{ price }}` as the original — the default theme doesn't always render the strikethrough; you may need to add it.
- **Adding a "Save $X" badge:** wrap the price + special price in a div and add a computed savings block. Example patch:
```twig
{% if special %}
  <div class="price-container">
    <span class="price-original" style="text-decoration:line-through">{{ price }}</span>
    <span class="price-special">{{ special }}</span>
    <span class="price-savings">Save {{ (price | striptags | replace({'$':''}) - special | striptags | replace({'$':''})) | number_format(2) }}</span>
  </div>
{% endif %}
```

### Checkout step collapse / guest checkout

OpenCart's default checkout is already a single-page checkout on 3.x+, but many themes override it into a multi-step flow. If the plan calls for single-page checkout, check:

- `catalog/view/theme/{theme}/template/checkout/checkout.twig` — the main wrapper. If it has multiple `<div class="panel panel-default" id="collapse-*">` blocks wrapped in Bootstrap accordions, it's running multi-step.
- **Guest checkout toggle** lives in `admin → System → Settings → [store] → Option tab → Checkout Guest: Yes`. If set to No, the store requires account creation before purchase — flag this as a CRITICAL checkout-flows finding if the audit catches it.

### Section reordering / layout changes

- **Vanilla OpenCart:** edit the relevant template file directly (e.g., move the `{{ review_block }}` include before the `{{ description_block }}` include in `product.twig`).
- **Journal3:** use the admin Layout Builder (Journal → Modules → Page Layouts → [Product page]) to drag-and-drop sections. This is faster than editing templates but requires admin access.

### Adding a new element (trust badges, social proof, etc.)

- **Direct:** patch the template file with the new HTML.
- **OCMOD:** write an `install.xml` with a `<search>` + `<add position="before|after">` operation.
- **Journal3:** use the admin "Custom Block" module and place it via the Layout Builder.

---

## Known gotchas

- **Cache layers stack.** OpenCart has a theme cache, a modification cache, and (if enabled) a page cache. Clearing one doesn't clear the others. After any theme edit, clear ALL three in admin (Dashboard → Clear cache) or delete `system/storage/cache/*` from the filesystem.
- **SEO URLs conflict with progress memory.** OpenCart uses two URL formats: query-string (`index.php?route=product/product&product_id=42`) and SEO URL (`product-handle.html`). Both resolve to the same page. ECP's progress memory normalization in `skills/audit/SKILL.md <progress_memory>` should treat these as equivalent — if the audit runs against one URL format and resumes against the other, the `url_normalized` field must match.
- **Journal3 JS hydration delay.** Journal3's testimonial carousels, product tabs, and lazy-loaded blocks may not exist in the DOM at DOMContentLoaded. Acquisition should wait at least 5 seconds after settle before capturing. If the audit flags missing elements that a human can see, the settle time was too short.
- **OCMOD silent failures.** If an OCMOD `<search>` string doesn't match anything in the target file (e.g., because the theme was updated and the search text changed), the modification is silently dropped with a log entry in `system/storage/logs/ocmod.log`. Always tail the log after applying OCMOD changes to verify nothing was dropped.
- **Theme file encoding.** Some OpenCart themes store template files as UTF-8 with BOM. If the builder's patch introduces byte-order-mark issues, the theme may render with a visible `` at the top of the page. Write template edits as UTF-8 WITHOUT BOM.
- **`catalog/` vs `admin/` templates.** OpenCart separates the storefront (`catalog/view/theme/`) from the admin interface (`admin/view/template/`). ECP only cares about `catalog/` — do NOT touch `admin/` files in the builder phase.

---

## Platform-specific finding translations

When cluster auditors emit findings on an OpenCart store, the builder's implementation patterns translate them as follows:

| Finding type | OpenCart implementation target |
|---|---|
| Hero headline / CTA copy | `catalog/view/theme/{theme}/template/common/home.twig` (homepage) or `product.twig` (PDP) |
| Price display / anchoring | `catalog/view/theme/{theme}/template/product/product.twig` — `{{ price }}` / `{{ special }}` block |
| Trust badges / social proof | Template patch or (Journal3) admin Custom Block module |
| Review display | `catalog/view/theme/{theme}/template/product/review.twig` — may need `{{ review_status }}` activation in admin |
| Search / filter UX | `catalog/view/theme/{theme}/template/product/category.twig` (category filters) + `search.twig` (search results) |
| Checkout step collapse | `catalog/view/theme/{theme}/template/checkout/checkout.twig` — look for multi-panel accordion |
| Product schema markup | Add via OCMOD injecting `<script type="application/ld+json">` into `common/header.twig` |
| Mobile performance / srcset | Template `<img>` tags in product.twig need `srcset` + `sizes` attributes added |
| Cart abandonment (email capture) | Admin → Marketing → Mail → Recurring Orders OR a 3rd-party extension; note this is often NOT achievable via template edits alone |

---

## Cross-references

- **`${CLAUDE_PLUGIN_ROOT}/contracts/platform-detection.md`** — detection heuristics that flag `platform: "opencart"` and (optionally) `journal3: true`.
- **`${CLAUDE_PLUGIN_ROOT}/contracts/cluster-routing.md`** — cluster routing doesn't change based on platform; OpenCart stores use the same 10-cluster system as any other platform.
- **`${CLAUDE_PLUGIN_ROOT}/workflows/build.md`** — the builder teammate reads this platform guide only when `platform: "opencart"` is set in the engagement context.

When editing this file, keep the "direct edit vs OCMOD vs Journal3 admin" decision framework prominent — it's the single biggest choice the builder has to make for every OpenCart recommendation, and getting it wrong produces changes that don't persist through theme updates.
