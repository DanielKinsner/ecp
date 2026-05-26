<!-- RESEARCH_DATE: 2026-04-14 -->
# Platform Detection

Heuristics for detecting the ecommerce platform of a page being audited. Used to load platform-specific reference files for enhanced recommendations.

## Detection Priority

1. **User explicitly states platform** — via intake conversation or `--platform` flag. Always trust the user.
2. **File detection** (when source code is available):
   - `.liquid` files AND (`shopify` in package.json OR `config/settings_schema.json` exists) → **Shopify**
   - `.liquid` files WITHOUT Shopify indicators → **Ask user** (could be Jekyll, Bridgetown, 11ty)
   - `next.config.*` or package.json with `"next"` dependency → **Next.js**
   - `gatsby-config.*` or package.json with `"gatsby"` dependency → **Gatsby** (use generic, no platform file)
   - `wp-content/plugins/woocommerce/` directory OR `class-woocommerce.php` OR `uploads/woocommerce_uploads/` → **WooCommerce**
   - `wp-content/` directory or `functions.php` WITHOUT WooCommerce markers → **WordPress** (use generic)
   - `catalog/view/` directory OR `system/engine/` directory OR `admin/controller/` directory → **OpenCart**
3. **DOM/HTML detection** (when preprocessed DOM is available):
   - DOM contains `catalog/view/` paths, `route=product/product` URL patterns, or `opencart` in meta generator → **OpenCart**
   - DOM contains `Shopify.theme` or `cdn.shopify.com` → **Shopify**
   - DOM contains `__NEXT_DATA__` or `_next/static` → **Next.js**
   - WooCommerce: **require ≥2 signals, at least one commerce-specific** (see WooCommerce Signal Scoring below).
4. **URL patterns** (when only URL is available):
   - `*.myshopify.com` → **Shopify**
   - `*.vercel.app` → likely **Next.js** (ask to confirm)
   - `*.netlify.app` → could be anything (ask)
   - URL contains `route=product/product` or `index.php?route=` → **OpenCart**
   - URL contains `/product/{slug}/` or `/product-category/{slug}/` or `/cart/` or `/checkout/` AND response headers / body carry another WC marker (see below) → **WooCommerce**
5. **Ask the user:** "What platform is this built on? (Shopify, Next.js, OpenCart, WooCommerce, or other)"

## WooCommerce Signal Scoring (≥2 signals required, one commerce-specific)

Bare `wp-content/` alone is **insufficient** — it fires on every WordPress site, including blogs, marketing sites, and membership sites that have no ecommerce. Require at least two signals from the list below AND at least one from the **commerce-specific** group.

**Commerce-specific signals** (any one alone, combined with any generic signal, confirms WooCommerce):

- Body class `woocommerce`, `woocommerce-page`, `woocommerce-cart`, `woocommerce-checkout`, `single-product`, `archive-product`
- Any element with a class matching `wc-block-*` (block-editor era, WC 8.3+)
- Class `woocommerce-Price-amount` on a price element
- Script handle or URL containing `wc_cart_fragments`, `wc-add-to-cart`, `wc-blocks-*`
- `<meta name="generator" content="WooCommerce ...">` in document head
- URL path `/cart/` or `/checkout/` returning a page whose body contains any of the above markers
- Cookie `woocommerce_cart_hash` or `wp_woocommerce_session_*` in response headers

**Generic signals** (two or more together are **not** sufficient to confirm WC — each one must pair with a commerce-specific signal):

- `wp-content/` in any asset URL
- `wp-json/` API endpoint present
- `generator` meta reading `WordPress ...`
- `stylesheet-uri` referencing `/wp-content/themes/`

If detection yields <2 signals or only generic signals, classify as **generic** (not `woocommerce`) and do NOT load the WooCommerce platform file. The builder stays generic. Avoiding false positives matters more than catching an edge case — a WC knowledge file loaded onto a non-commerce WordPress site would produce recommendations that cannot be implemented.

## Platform File Loading

| Platform | File | When Loaded |
|----------|------|-------------|
| Shopify | `${CLAUDE_PLUGIN_ROOT}/platforms/shopify.md` | Builder phase only |
| Next.js | `${CLAUDE_PLUGIN_ROOT}/platforms/nextjs.md` | Builder phase only |
| OpenCart | `${CLAUDE_PLUGIN_ROOT}/platforms/opencart.md` | Builder phase only |
| WooCommerce | `${CLAUDE_PLUGIN_ROOT}/platforms/woocommerce.md` | Builder phase only |
| Generic | No additional file | Default for all other platforms, including WordPress without WC markers |

Platform files enhance the builder's output with platform-specific patterns, anti-patterns, and code examples. They do NOT change audit or review behavior — those remain platform-agnostic.

## Disambiguation: .liquid Files

IMPORTANT: `.liquid` is used by multiple frameworks:
- **Shopify** — most common in ecommerce context
- **Jekyll** — static site generator
- **Bridgetown** — Ruby static site framework
- **11ty** — JavaScript static site generator

Never assume Shopify from `.liquid` alone. Require a second signal:
- `shopify` in package.json
- `config/settings_schema.json` exists
- `*.myshopify.com` URL
- User confirms Shopify

If only `.liquid` files with no second signal: ask "I see Liquid templates. Is this a Shopify theme, or another framework?"

## Future Platforms

When adding a new platform:
1. Create `platforms/{platform}.md` following the existing format
2. Add detection heuristics to this file
3. Add to the Platform File Loading table above
4. No changes needed to SKILL.md files — they load platform files dynamically
