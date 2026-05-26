<!-- RESEARCH_DATE: 2026-04-14 -->
# WooCommerce Platform Reference

Platform-specific patterns for the ECP builder when generating WooCommerce code. Loaded only during the builder phase when `platform: "woocommerce"` is detected or forced.

## Detection

WooCommerce is auto-detected by the heuristics in `${CLAUDE_PLUGIN_ROOT}/contracts/platform-detection.md`. Detection requires **at least two signals, one of which must be commerce-specific** — bare `wp-content/` is insufficient (would false-positive on every WordPress blog). The highest-confidence markers are:

- **WC-specific body classes:** `woocommerce`, `woocommerce-page`, `woocommerce-cart`, `woocommerce-checkout`, `woocommerce-account`, `single-product`, `archive-product`
- **WC-specific CSS classes on elements:** `wc-block-*` (block-editor era, WC 8.3+), `woocommerce-Price-amount`, `woocommerce-product-gallery`, `woocommerce-ordering`
- **WC-specific scripts:** `wc_cart_fragments`, `woocommerce-js`, `wc-add-to-cart`, `wc-blocks-*`
- **Generator meta:** `<meta name="generator" content="WooCommerce X.Y.Z">` (may be stripped by security plugins)
- **URL patterns:** `/shop/`, `/cart/`, `/checkout/`, `/my-account/`, `/product/{slug}/`, `/product-category/{slug}/` (WP's default pretty-permalink convention for WC)
- **Cookies:** `woocommerce_cart_hash`, `wp_woocommerce_session_*`

**Versions supported:**
- WooCommerce 9.x (current, default) — block cart/checkout by default on new installs, HPOS (High-Performance Order Storage) on by default, full site editing supported
- WooCommerce 8.3–8.x — transitional; cart/checkout blocks available but classic shortcodes still default on many existing stores
- WooCommerce ≤ 8.2 — classic shortcodes only; block cart/checkout not yet available

Assume **WC 9.x on WordPress 6.5+** unless detection reports a specific older version. When version detection fails, check for `wp-block-*` classes on cart/checkout surfaces — presence means block era, absence means classic.

---

## Theme hierarchy

WooCommerce templates live in `wp-content/plugins/woocommerce/templates/`. Themes override them by copying into `wp-content/themes/{theme}/woocommerce/` (lowercase preferred). The theme copy always wins over the plugin copy. Never edit plugin files directly — they are wiped on update.

```
wp-content/
├── plugins/
│   └── woocommerce/
│       └── templates/                              # NEVER edit these
│           ├── single-product.php
│           ├── single-product/
│           │   ├── add-to-cart/
│           │   │   ├── simple.php
│           │   │   └── variable.php
│           │   ├── price.php
│           │   ├── meta.php
│           │   └── title.php
│           ├── cart/
│           │   ├── cart.php
│           │   ├── cart-totals.php
│           │   └── cross-sells.php
│           ├── checkout/
│           │   ├── form-checkout.php
│           │   ├── form-billing.php
│           │   ├── review-order.php
│           │   └── thankyou.php
│           ├── archive-product.php
│           ├── content-product.php
│           └── global/
│               ├── breadcrumb.php
│               └── quantity-input.php
│
└── themes/
    └── {theme}/
        ├── woocommerce/                            # Classic-theme overrides (copy from plugin then edit)
        │   ├── single-product.php
        │   ├── archive-product.php
        │   └── ... (mirror plugin structure)
        ├── templates/                              # Block-theme templates (HTML, not PHP)
        │   ├── single-product.html
        │   ├── archive-product.html
        │   ├── page-cart.html
        │   ├── page-checkout.html
        │   └── order-confirmation.html
        ├── parts/                                  # Block-theme reusable parts
        │   ├── mini-cart.html
        │   └── checkout-header.html
        └── functions.php                           # Hook registration, the main customization surface
```

**Classic themes vs block themes:** `wp_is_block_theme()` returns true when the active theme has a `templates/index.html`. Block themes use `/templates/*.html` and `/parts/*.html` with block markup; classic themes use PHP files in `/woocommerce/`. A theme can be one or the other — not both for the same surface. Detect via body class `wp-theme-{slug}` + presence of `wp-block-*` wrappers.

---

## Modification patterns

WooCommerce offers three customization paths. The builder must pick the right one per change:

### 1. Hook registration in a child theme (recommended default)

WordPress coding convention. Changes live in `wp-content/themes/{child-theme}/functions.php` (or a mu-plugin) and attach to WC's action/filter hooks. Survives core + parent-theme updates.

```php
<?php
// Inject trust badges beside the Add-to-Cart button on single product pages.
add_action( 'woocommerce_before_add_to_cart_button', 'myplugin_render_trust_badges' );

function myplugin_render_trust_badges() {
    if ( ! is_product() ) {
        return;
    }
    $product = wc_get_product( get_the_ID() );
    if ( ! $product || ! $product->is_purchasable() ) {
        return;
    }
    ?>
    <ul class="myplugin-trust-badges" aria-label="<?php esc_attr_e( 'Purchase guarantees', 'myplugin' ); ?>">
        <li><?php esc_html_e( 'Free shipping over $75', 'myplugin' ); ?></li>
        <li><?php esc_html_e( '30-day returns', 'myplugin' ); ?></li>
        <li><?php esc_html_e( 'Secure SSL checkout', 'myplugin' ); ?></li>
    </ul>
    <?php
}
```

WooCommerce coding standards follow WordPress: snake_case function names, plugin prefix (`myplugin_`), 4-space indent, escape on output (`esc_html`, `esc_attr`, `wp_kses_post`), `wc_*` helpers over `get_post_meta` when available. Text domain on all user-visible strings for i18n.

### 2. Template override via child theme (when a hook is not available)

Copy the target plugin template into `wp-content/themes/{child-theme}/woocommerce/` and edit. Best for changes that a hook cannot reach — e.g., restructuring the product summary block order, changing the cart line-item markup.

**Override priority:** child theme `/woocommerce/{path}` > child theme `/templates/{path}` > parent theme > plugin default. After copying, the override file can diverge from the plugin version; add a header comment noting the plugin version it was forked from so the builder can compare after a WC update.

### 3. Block render filter (WC 8.3+ cart/checkout surfaces)

The classic cart and checkout action hooks (`woocommerce_review_order_before_payment`, `woocommerce_checkout_before_order_review`, etc.) **DO NOT FIRE inside the Cart and Checkout Blocks.** Injecting via classic hooks on a block-checkout store is the #1 "my trust badge disappeared" cause. On block cart/checkout, use one of:

1. **`render_block_{namespace}/{block}` filter** — wrap or prepend/append HTML to a specific inner block:
   ```php
   add_filter( 'render_block_woocommerce/checkout-actions-block', function( $html ) {
       return '<p class="reassure">' . esc_html__( 'Secure SSL checkout. 30-day money-back guarantee.', 'myplugin' ) . '</p>' . $html;
   }, 10, 1 );
   ```
2. **Checkout Block Integration API** — `woocommerce_blocks_loaded` → register an `IntegrationInterface` with a frontend JS bundle that uses `<ExperimentalOrderMeta>` / `<ExperimentalDiscountsMeta>` slot fills. Heavier; required for UI that needs to react to cart state changes.
3. **Store API extension** — `woocommerce_store_api_register_endpoint_data()` to surface custom data to the block frontend. Use when the block needs new fields from the server.

**Decision rule for the builder:** if the audit finding targets cart or checkout, always check whether the store is block-era first (`wp_is_block_theme()` + presence of `wc-block-*` wrappers). If block, reach for `render_block_*`. If classic, reach for `woocommerce_*` action hooks.

---

## CRO-relevant hook reference

Single product and archive surfaces (classic, and partially fires on block Single Product too):

- `woocommerce_before_single_product` / `_after_single_product` — wrap the whole PDP
- `woocommerce_before_add_to_cart_button` / `_after_add_to_cart_button` — trust badges beside CTA
- `woocommerce_before_add_to_cart_form` / `_after_add_to_cart_form` — wider CTA wrapper
- `woocommerce_product_meta_start` / `_end` — SKU / category row
- `woocommerce_single_product_summary` (priority 5/10/20/30/40/50 = title / price / excerpt / cart / meta / sharing) — reorder via `remove_action` + `add_action` with new priority
- `woocommerce_after_shop_loop_item_title` — under each product card title in archive
- `woocommerce_after_shop_loop_item` — bottom of each archive card

Cart and checkout (classic shortcode era — see Block render filter section above for block era):

- `woocommerce_before_cart` / `_after_cart`
- `woocommerce_cart_collaterals` — between cart table and totals (cross-sells default here)
- `woocommerce_before_checkout_form` — banner above the checkout form
- `woocommerce_review_order_before_payment` / `_after_payment` — around the gateway list
- `woocommerce_review_order_before_submit` / `_after_submit` — around the Place Order button
- `woocommerce_thankyou` — order-received page (good for post-purchase upsell)

Filters worth knowing:

- `woocommerce_product_tabs` — add, remove, reorder tabs on the product page
- `woocommerce_sale_flash` — customize the "Sale!" badge
- `woocommerce_get_price_html` — override price markup globally
- `woocommerce_structured_data_product` — extend Product JSON-LD
- `woocommerce_available_payment_gateways` — reorder or hide methods contextually
- `woocommerce_gateway_description` — inject HTML under a specific payment method

---

## Schema and structured data

WooCommerce emits Product JSON-LD automatically on single-product pages via `WC_Structured_Data`. Out of the box it includes `name`, `image`, `description`, `sku`, `offers` (price / currency / availability / url), and `aggregateRating` + `review` ONLY when reviews exist and are enabled in Settings → Products → General.

**Common gaps** flagged by ECP's content-seo cluster audits:

- Missing `brand` (required by Google Merchant Center, 2023+)
- Missing `gtin13` / `mpn` (product identification)
- Missing `shippingDetails` / `hasMerchantReturnPolicy` (required by Google Merchant Center since 2023 for Shopping listings)

Extension pattern:

```php
add_filter( 'woocommerce_structured_data_product', function( $markup, $product ) {
    $markup['brand']  = array( '@type' => 'Brand', 'name' => 'Acme' );
    $markup['gtin13'] = get_post_meta( $product->get_id(), '_gtin', true );
    return $markup;
}, 10, 2 );
```

Other structured-data filters: `woocommerce_structured_data_review`, `woocommerce_structured_data_order`, `woocommerce_structured_data_breadcrumblist`.

---

## CRO pattern placement map

| Element | Classic hook / template | Block-era approach |
|---|---|---|
| Trust badges next to ATC | `woocommerce_before_add_to_cart_button` | `render_block_woocommerce/product-button` filter |
| Free-shipping banner (site-wide) | `wp_body_open` or `woocommerce_before_main_content` | Template part "Header" in the Site Editor |
| Review stars on listing | Default — `woocommerce_after_shop_loop_item_title` priority 5 emits rating | `woocommerce/product-rating` block inside Product Template |
| Urgency / low stock | `woocommerce_get_stock_html` filter + summary priority ~25 | `woocommerce/product-stock-indicator` block |
| Product-page upsells | `woocommerce_after_single_product_summary` priority 15 (default) | Upsells block inside `single-product.html` |
| Cart cross-sells | `woocommerce_cart_collaterals` → `cart/cross-sells.php` | `woocommerce/cart-cross-sells-block` (inside Cart Items section) |
| Checkout reassurance | `woocommerce_review_order_before_submit` | `render_block_woocommerce/checkout-actions-block` filter |
| Thank-you upsell | `woocommerce_thankyou` action (takes order ID argument) | Order Confirmation block template |
| Payment-method trust copy | `woocommerce_gateway_description` filter, per-gateway | Payments API `registerPaymentMethod({content})` |

---

## Known gotchas

- **`the_content` filter does NOT run on single-product pages.** Product description is output by `woocommerce_template_single_excerpt()` and the `[product_description]` shortcode inside blocks. Injecting via `the_content` silently does nothing on `/product/*`. Flag as a common "my banner disappeared" cause.
- **Classic checkout hooks are silent no-ops on block checkout.** `woocommerce_review_order_before_payment`, `woocommerce_checkout_before_order_review`, etc., do not fire when Cart/Checkout Blocks are active. Always check block vs classic before writing checkout customization.
- **Shortcodes inside block templates run through the Shortcode block**, not the legacy `do_shortcode()` path. Nested-shortcode and `wpautop` behavior differ. Prefer blocks when customizing a block theme.
- **CSS specificity**: WC block stylesheets load with fairly high specificity (`.wc-block-components-*`). Use `:where()` selectors or `theme.json` custom-property overrides — not `!important` bombs, which create maintenance debt.
- **`wp_is_block_theme()` early-call warning:** don't call it before `after_setup_theme`. Gate via `did_action( 'after_setup_theme' )` when running from plugin bootstrap.
- **HPOS (High-Performance Order Storage)** is default on new WC 9.x installs. Direct SQL queries against `wp_posts` for orders break; use `wc_get_orders()` / `$order->get_meta()` exclusively. Flag any recommendation that mentions `wp_posts` for order data as obsolete.
- **Child theme is the idiomatic customization seat.** Putting hook registrations in the parent theme's `functions.php` means edits get wiped on theme updates. Always recommend creating / using a child theme for any store without one.
- **Caching plugins (WP Rocket, W3 Total Cache, Autoptimize)** aggressively cache page output. A template change can appear to "not take effect" until page + object + CDN caches are purged. Include a cache-purge step in any builder instruction touching template output.

---

## Platform-specific finding translations

When cluster auditors emit findings on a WooCommerce store, the builder's implementation patterns translate as follows:

| Finding type | WooCommerce implementation target |
|---|---|
| Hero headline / CTA copy | Homepage: template part "Header" (block theme) or `header.php` + custom homepage template (classic). PDP hero: `woocommerce_single_product_summary` priority 5/10 hooks |
| Price display / anchoring | `woocommerce_get_price_html` filter (global) or `woocommerce_single_product_summary` priority 10 hook (per-page) |
| Trust badges / social proof | `woocommerce_before_add_to_cart_button` (classic) or `render_block_woocommerce/product-button` (block) |
| Review display | Default enabled; ensure Settings → Products → General → Enable product reviews. Customize layout via `single-product/review.php` override. Review form hooks: `comment_form_before`, `comment_form_after` |
| Search / filter UX | `pre_get_posts` filter for query modification; theme template `archive-product.php` / `templates/archive-product.html`; `woocommerce_catalog_orderby` filter for sort options |
| Checkout step collapse | Block era: Cart and Checkout blocks are already single-page. Classic era: enable WC's built-in "Enable guest checkout" in Settings; consider a single-page checkout plugin if the store is multi-step |
| Product schema markup | `woocommerce_structured_data_product` filter to add brand / GTIN / shipping / return-policy fields |
| Mobile performance / srcset | Theme image template tags — `wp_get_attachment_image()` emits srcset automatically when image has multiple sizes registered in `add_image_size()` |
| Cart abandonment (email capture) | Not achievable via template edits alone. Requires a plugin (CartFlows, Retainful, WooCommerce Cart Abandonment Recovery, Klaviyo) or a custom cron + `wc_get_orders( status => 'checkout-draft' )` |
| Free-shipping progress bar | `woocommerce_cart_collaterals` hook (classic) or Cart block's Shipping element + custom CSS (block); use `WC()->cart->get_cart_contents_total()` to compute remaining-to-threshold |

---

## Cross-references

- **`${CLAUDE_PLUGIN_ROOT}/contracts/platform-detection.md`** — detection heuristics that flag `platform: "woocommerce"`. Requires ≥2 signals with at least one commerce-specific marker; bare `wp-content/` alone detects as `generic`.
- **`${CLAUDE_PLUGIN_ROOT}/contracts/cluster-routing.md`** — cluster routing does not change based on platform; WC stores use the same 10-cluster system as any other.
- **`${CLAUDE_PLUGIN_ROOT}/workflows/build.md`** — the builder teammate reads this platform guide only when `platform: "woocommerce"` is set in the engagement context.

When editing this file, keep the "classic hooks vs block render filters" decision framework prominent — it is the single biggest call the builder has to make on cart/checkout recommendations, and getting it wrong produces customizations that silently vanish on block-enabled stores.
