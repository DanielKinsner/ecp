<!-- RESEARCH_DATE: 2026-03-11 -->
# Shopify Platform Reference

Platform-specific patterns for the CRO builder when generating Shopify/Liquid code. Loaded only during the builder phase.

## OS 2.0 Theme Architecture

### Key Concepts
- **JSON templates** (`templates/*.json`): Define which sections appear on a page. Merchants rearrange in theme editor.
- **Sections** (`sections/*.liquid`): Self-contained blocks with their own schema, styles, and JS. Rendered via `{% section %}`.
- **Blocks** (inside sections): Granular content units merchants can add/remove/reorder within a section.
- **Snippets** (`snippets/*.liquid`): Reusable partials rendered via `{% render 'snippet-name' %}`. No schema — pure code.
- **Assets** (`assets/`): CSS, JS, images. Reference via `{{ 'file.css' | asset_url }}`.

### Template vs Section
```
templates/product.json     → declares section order
sections/product-main.liquid → renders product UI + schema
sections/product-reviews.liquid → renders reviews + schema
```
Merchants can reorder sections in the theme editor. CRO builder should create NEW sections, not modify existing ones, to avoid breaking merchant customizations.

## Liquid Patterns for CRO Elements

### Trust Badges
```liquid
{%- comment -%} snippets/trust-badges.liquid {%- endcomment -%}
<div class="trust-badges" role="list" aria-label="Trust signals">
  {%- for block in section.blocks -%}
    {%- case block.type -%}
      {%- when 'payment_icons' -%}
        <div role="listitem">
          {%- for type in shop.enabled_payment_types -%}
            {{ type | payment_type_svg_tag }}
          {%- endfor -%}
        </div>
      {%- when 'guarantee' -%}
        <div role="listitem">
          {% render 'icon-shield' %}
          <span>{{ block.settings.guarantee_text }}</span>
        </div>
      {%- when 'secure_checkout' -%}
        <div role="listitem">
          {% render 'icon-lock' %}
          <span>Secure checkout</span>
        </div>
    {%- endcase -%}
  {%- endfor -%}
</div>
```

### CTA Buttons — Add to Cart Variants
```liquid
{%- comment -%} Standard add-to-cart with dynamic checkout {%- endcomment -%}
<div class="product-form__buttons">
  <button
    type="submit"
    name="add"
    class="product-form__submit button button--primary"
    {% unless current_variant.available %}disabled{% endunless %}
  >
    {%- if current_variant.available -%}
      {{ 'products.product.add_to_cart' | t }}
    {%- else -%}
      {{ 'products.product.sold_out' | t }}
    {%- endif -%}
  </button>

  {%- if section.settings.show_dynamic_checkout -%}
    {{ form | payment_button }}
  {%- endif -%}
</div>
```

### Urgency/Scarcity (with Ethics Boundaries)
```liquid
{%- comment -%} ONLY display real inventory data. Never fake scarcity. {%- endcomment -%}
{%- if current_variant.inventory_management == 'shopify'
    and current_variant.inventory_policy == 'deny'
    and current_variant.inventory_quantity > 0
    and current_variant.inventory_quantity <= section.settings.low_stock_threshold -%}
  <p class="product__inventory" role="status">
    {{ 'products.product.low_stock' | t: count: current_variant.inventory_quantity }}
  </p>
{%- endif -%}
```
NEVER generate fake countdown timers or artificial scarcity. Only use real `inventory_quantity` data with `inventory_management == 'shopify'`.

### Social Proof — Reviews Integration
```liquid
{%- comment -%} Works with Shopify Product Reviews app or Judge.me {%- endcomment -%}
{%- if product.metafields.reviews.rating.value != blank -%}
  {%- assign rating = product.metafields.reviews.rating.value -%}
  <div class="product__rating" role="img" aria-label="{{ rating }} out of {{ rating.scale_max }} stars">
    {%- render 'star-rating', rating_value: rating.rating, scale_max: rating.scale_max -%}
    <span class="product__rating-count">
      ({{ product.metafields.reviews.rating_count.value }})
    </span>
  </div>
{%- endif -%}
```

### Price Display — Compare-at Pricing
```liquid
<div class="price" data-price>
  {%- if current_variant.compare_at_price > current_variant.price -%}
    <span class="price__sale" aria-label="Sale price">
      {{ current_variant.price | money }}
    </span>
    <s class="price__compare" aria-label="Original price">
      {{ current_variant.compare_at_price | money }}
    </s>
    <span class="price__badge badge--sale">
      {{ 'products.product.on_sale' | t }}
    </span>
  {%- else -%}
    <span class="price__regular">{{ current_variant.price | money }}</span>
  {%- endif -%}
</div>
```

### Multi-Currency (Shopify Markets)
```liquid
{%- comment -%} Prices auto-convert when using money filters with Markets enabled {%- endcomment -%}
{{ current_variant.price | money }}
{%- comment -%} Do NOT hardcode currency symbols. Use money filters which respect
    the buyer's market/currency automatically. {%- endcomment -%}
```

## Section Schema Patterns

### Merchant-Configurable CRO Settings
```json
{
  "name": "Product CRO",
  "settings": [
    {
      "type": "checkbox",
      "id": "show_trust_badges",
      "label": "Show trust badges",
      "default": true
    },
    {
      "type": "range",
      "id": "low_stock_threshold",
      "label": "Low stock warning threshold",
      "min": 0,
      "max": 20,
      "step": 1,
      "default": 5,
      "info": "Show 'Only X left' when inventory is at or below this number. Set to 0 to disable."
    },
    {
      "type": "checkbox",
      "id": "show_dynamic_checkout",
      "label": "Show dynamic checkout button (Shop Pay, Apple Pay, etc.)",
      "default": true,
      "info": "Accelerated checkout converts 1.72x higher on average."
    },
    {
      "type": "select",
      "id": "social_proof_style",
      "label": "Social proof display",
      "options": [
        { "value": "stars", "label": "Star rating" },
        { "value": "count", "label": "Review count only" },
        { "value": "both", "label": "Stars + count" },
        { "value": "none", "label": "Hidden" }
      ],
      "default": "both"
    }
  ],
  "blocks": [
    {
      "type": "payment_icons",
      "name": "Payment icons",
      "limit": 1
    },
    {
      "type": "guarantee",
      "name": "Guarantee badge",
      "settings": [
        {
          "type": "text",
          "id": "guarantee_text",
          "label": "Guarantee text",
          "default": "30-day money-back guarantee"
        }
      ]
    }
  ]
}
```

## Shop Pay & Accelerated Checkout

- Shop Pay converts 1.72x higher than standard checkout (Shopify data)
- Always enable `{{ form | payment_button }}` on product pages
- Dynamic checkout buttons auto-show the buyer's preferred wallet (Shop Pay, Apple Pay, Google Pay)
- Do NOT hide or de-emphasize dynamic checkout — it is the highest-impact CRO lever on Shopify
- For Shopify Plus: Shop Pay Installments further reduces cart abandonment

## Checkout UI Extensions (Post checkout.liquid)

`checkout.liquid` is deprecated. Use Checkout UI Extensions instead:
```
shopify app generate extension --type checkout_ui
```

### Extension Points for CRO
- `purchase.checkout.block.render` — Add trust badges, upsells, custom messaging
- `purchase.checkout.delivery-address.render-before` — Shipping assurance messaging
- `purchase.checkout.payment-method-list.render-after` — Payment trust signals
- `purchase.thank-you.block.render` — Post-purchase survey, referral prompt

Extensions run in a sandbox with limited UI components (Checkout UI primitives). They cannot access the full DOM.

## Metafield Patterns for Personalization

```liquid
{%- comment -%} Product-level CRO metafields {%- endcomment -%}
{%- assign urgency_message = product.metafields.cro.urgency_message.value -%}
{%- assign social_proof_override = product.metafields.cro.social_proof.value -%}
{%- assign guarantee_type = product.metafields.cro.guarantee.value -%}

{%- if urgency_message != blank -%}
  <p class="product__urgency">{{ urgency_message }}</p>
{%- endif -%}
```

Define metafields in `config/settings_schema.json` or via Admin API. Use namespace `cro` for all conversion-related metafields.

## Performance

### Shopify CDN & Image Optimization
```liquid
{%- comment -%} Always use image_url filter for CDN-optimized images {%- endcomment -%}
{{ product.featured_image | image_url: width: 800 | image_tag:
   loading: 'lazy',
   widths: '200,400,600,800',
   sizes: '(max-width: 768px) 100vw, 50vw'
}}

{%- comment -%} Hero/above-fold: eager load, fetchpriority high {%- endcomment -%}
{{ product.featured_image | image_url: width: 1200 | image_tag:
   loading: 'eager',
   fetchpriority: 'high',
   widths: '400,600,800,1200',
   sizes: '(max-width: 768px) 100vw, 50vw'
}}
```

### Section Rendering API
For dynamic updates without full page reload:
```javascript
fetch(`${window.location.pathname}?sections=product-main`)
  .then(r => r.json())
  .then(data => {
    document.querySelector('#product-main').innerHTML = data['product-main'];
  });
```
Use for variant switching, cart updates, and real-time inventory checks.

### Critical CSS Inlining
```liquid
{%- comment -%} Inline critical CSS for above-fold content {%- endcomment -%}
<style>
  {{ 'critical.css' | asset_url | stylesheet_tag | split: '<link' | first }}
</style>
{%- comment -%} Defer non-critical CSS {%- endcomment -%}
<link rel="stylesheet" href="{{ 'theme.css' | asset_url }}" media="print" onload="this.media='all'">
```

## 12 Shopify CRO Anti-Patterns

| # | Anti-Pattern | Fix |
|---|-------------|-----|
| 1 | Hiding dynamic checkout button | Always show `{{ form \| payment_button }}` — it is your highest-converting element |
| 2 | Fake scarcity timers | Only use real `inventory_quantity` data; fake urgency erodes trust |
| 3 | Hardcoded currency symbols | Use `\| money` filter — respects Shopify Markets multi-currency |
| 4 | Missing `alt` on product images | Use `{{ image.alt \| escape }}` or product title as fallback |
| 5 | No compare-at pricing display | If `compare_at_price` exists, show it — anchoring drives conversions |
| 6 | Eager-loading all images | Only `loading='eager'` for above-fold hero; `lazy` for everything else |
| 7 | Inline scripts blocking render | Move JS to deferred `<script>` tags or use `{% javascript %}` tag |
| 8 | Not using Section Rendering API | Full page reloads for variant changes kill UX; use section rendering |
| 9 | Modifying Dawn core sections directly | Create new sections — core edits break on theme updates |
| 10 | Missing schema settings for CRO elements | Every CRO element should be merchant-toggleable via section schema |
| 11 | No mobile-specific CTA sizing | Touch targets must be 44x44px minimum; test on real devices |
| 12 | Ignoring Shopify analytics events | Fire `shopify:section:load` and standard cart events for proper tracking |

## Detection Heuristics

How to confirm a site is Shopify:
- URL contains `*.myshopify.com`
- Source contains `Shopify.theme` or `shopify-section` classes
- `config/settings_schema.json` exists in source
- `shopify` in package.json dependencies
- HTML meta tags reference `shopify`
- `/cdn/shop/` in image URLs
