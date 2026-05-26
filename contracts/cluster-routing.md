# Domain cluster routing

Canonical routing table for ECP's 10-cluster architecture. All skills reference this file for page-type defaults, `--focus` flag mapping, and override rules.

**Why this file exists:** Prior to Round 11, cluster routing lived inside `skills/audit/SKILL.md` and build/compare deferred to it via "See `/ecp:audit` `<domain_cluster_routing>`". Addendum Finding 3 flagged audit as the hidden shared authority for cross-skill concepts. This file resolves the coupling by making cluster routing a first-class canonical reference that no skill owns.

---

## The 10 clusters (v5.0+)

Each cluster owns a specific set of reference files. Cluster auditor teammates load ONLY their cluster's reference files (plus the always-loaded ethics gate + evidence tiers files) — not the full reference library.

| Cluster | Reference files |
|---------|-----------------|
| `visual-cta` | cta-design-and-placement, color-psychology, eye-tracking-and-scan-patterns, hero-section-psychology, headline-copywriting, page-length-strategy |
| `trust-credibility` | trust-and-credibility, social-proof-patterns, eeat-product-pages, review-collection, ugc-integration, ugc-reviews-seo, accessibility |
| `pricing` | pricing-psychology, charm-pricing, price-anchoring, bundle-pricing, discount-framing, free-shipping, tiered-pricing, bnpl-payment, price-transparency, scarcity-urgency, competitive-positioning |
| `checkout-flows` | checkout-optimization, biometric-and-express-checkout, abandoned-cart-psychology, cookie-consent-and-compliance |
| `performance-ux` | mobile-conversion, cognitive-load-management, page-performance-psychology, core-web-vitals, media-performance-optimization |
| `product-media` | gallery-ux, image-quantity-types, thumbnail-design, video-integration, video-optimization, video-schema, ar-3d-visualization, color-accuracy |
| `category-navigation` | search-and-filter-ux, filtering-ux, grid-layout, merchandising-psychology, pagination-patterns, product-cards, sorting-psychology, zero-results, breadcrumbs, collection-page-architecture |
| `content-seo` | canonical-duplicate-content, schema-product-markup, image-seo-alt-text, url-structure-information-architecture, title-formulas-serp-psychology, content-freshness-signals, ai-search-agentic-discovery, benefit-first-descriptions |
| `post-purchase` | post-purchase-psychology, order-confirmation, buyers-remorse, loyalty-programs, referral-programs |
| `audience` | personalization-psychology, cross-cultural-considerations, social-commerce-psychology |

Every file listed above lives in `${CLAUDE_PLUGIN_ROOT}/references/` with the `.md` extension.

**Note on `performance-ux` (v1.1 rename from `mobile-performance`):** This cluster covers **all viewports**, not just mobile — four of its five reference files (`cognitive-load-management`, `page-performance-psychology`, `core-web-vitals`, `media-performance-optimization`) are device-agnostic. The prior name led desktop audit users to expect the cluster to be skipped on desktop; it was not, and it should not be. `mobile-conversion.md` remains in the cluster to carry mobile-specific guidance when the auditor runs against mobile viewports. The legacy slug `mobile-performance` is accepted on resume and maps to `performance-ux` — see `contracts/cluster-migration.md`.

---

## Page type → default cluster routing

Each page type has two cluster sets: **comprehensive** (all relevant clusters — used by scope option `c` and `--auto --deep`) and **standard** (highest-impact 3-4 clusters — used by scope option `b` and `--auto`). The scope selector in `skills/audit/SKILL.md` `<cluster_selection>` determines which table is used. The `--focus` flag overrides both tables.

### Comprehensive defaults (scope option c)

| Page Type | Comprehensive Clusters |
|-----------|------------------------|
| Product page | `visual-cta`, `trust-credibility`, `pricing`, `product-media`, `content-seo`, `performance-ux` |
| Cart | `checkout-flows`, `trust-credibility`, `pricing` |
| Checkout | `checkout-flows`, `trust-credibility`, `performance-ux` |
| Homepage | `visual-cta`, `trust-credibility`, `content-seo`, `performance-ux`, `pricing`, `category-navigation` |
| Category / Collection | `category-navigation`, `visual-cta`, `performance-ux`, `content-seo` |
| Landing page | `visual-cta`, `trust-credibility`, `pricing`, `performance-ux` |
| Pricing / Plans | `pricing`, `trust-credibility`, `visual-cta` |
| Post-purchase / Confirmation | `post-purchase`, `audience` |

### Standard defaults (scope option b) — recommended for most audits

The standard set selects the 3-4 highest-impact clusters per page type. These produce the majority of actionable findings while using significantly fewer tokens than comprehensive mode.

| Page Type | Standard Clusters |
|-----------|-------------------|
| Product page | `visual-cta`, `trust-credibility`, `pricing`, `content-seo` |
| Cart | `checkout-flows`, `trust-credibility`, `pricing` |
| Checkout | `checkout-flows`, `trust-credibility`, `performance-ux` |
| Homepage | `visual-cta`, `trust-credibility`, `performance-ux`, `content-seo` |
| Category / Collection | `category-navigation`, `visual-cta`, `content-seo` |
| Landing page | `visual-cta`, `trust-credibility`, `pricing` |
| Pricing / Plans | `pricing`, `trust-credibility`, `visual-cta` |
| Post-purchase / Confirmation | `post-purchase`, `audience` |

**Note:** Cart, Checkout, Pricing/Plans, and Post-purchase already have 3 or fewer clusters in comprehensive mode, so their standard and comprehensive sets are identical.

(Single-cluster scan modes that pick exactly one cluster and skip override rules are out of scope in this build — see `product.md`.)

---

## `--focus` flag value mapping

`--focus` accepts cluster slugs directly OR high-level domain values that map to one or more clusters.

| `--focus` value | Resolves to clusters |
|-----------------|-----------------------|
| (no flag) | Page-type defaults from the table above |
| `all` | All 10 clusters |
| `cro` | visual-cta, trust-credibility, pricing, checkout-flows, performance-ux, post-purchase, audience |
| `seo` | content-seo |
| `pricing` | pricing |
| `trust` | trust-credibility |
| `visual` | visual-cta, product-media |
| `mobile` | performance-ux |
| `content` | content-seo, visual-cta |
| `checkout` | checkout-flows |
| Direct cluster slug (e.g., `pricing`, `category-navigation`) | That single cluster |
| Comma-separated list (e.g., `pricing,trust,visual`) | All listed clusters/domains, deduplicated |

**Aliases:** `--cluster` and `--clusters` are silent backwards-compat aliases for `--focus`. Every skill that supports `--focus` also accepts these aliases.

---

## Quick-scan single-cluster restriction

Quick-scan picks exactly ONE cluster — it's the fast option. `--focus` in quick-scan accepts:

1. **Direct cluster slugs** (any of the 10): used as-is.
2. **Single-cluster domain aliases:** `seo` → `content-seo`, `pricing` → `pricing`, `trust` → `trust-credibility`, `mobile` → `performance-ux`, `checkout` → `checkout-flows`.
3. **Multi-cluster domain aliases (`cro`, `visual`, `content`, `all`):** print a warning and fall back to the first cluster in that domain's mapping. For multi-cluster coverage, use `/ecp:audit` instead.

The quick-scan page-type defaults (when `--focus` is not set) are:

| Page Type | Default Cluster (quick-scan only) |
|-----------|----------------------------------|
| Product page | `visual-cta` |
| Cart | `checkout-flows` |
| Checkout | `checkout-flows` |
| Homepage | `visual-cta` |
| Category / Collection | `category-navigation` |
| Landing page | `visual-cta` |
| Pricing / Plans | `pricing` |
| Post-purchase | `post-purchase` |

---

## Override rules (applied AFTER `--focus` resolution)

These rules can ADD clusters to the resolved set but never REMOVE them. They're applied after the page-type defaults or `--focus` resolution, during the cluster selection phase in `skills/audit/SKILL.md` `<cluster_selection>`.

- **Non-Western market detected** → add `audience` cluster. Detection signals: non-English primary content, non-Latin script, currency/locale markers (₹, ¥, ₩, R$, etc.), or an explicit `locale` meta tag pointing outside `en-*`, `de-*`, `fr-*`, `es-*`, `it-*`, `nl-*`, `pt-*`, `sv-*`, `no-*`, `da-*`, `fi-*`.
- **Significant price display detected** → ensure `pricing` cluster is included. Detection signals: more than 3 distinct price markers in the hero/above-fold area, explicit discount framing (strikethrough, "X% off", "was/now"), bundle offers, or payment plan markers (Klarna, Affirm, Afterpay, etc.).
- **Mobile in device set** → ensure `performance-ux` cluster is included. Triggered when the device set includes `mobile` (single or paired). The cluster hosts `mobile-conversion.md` alongside its device-agnostic page-performance references, so a mobile audit without this cluster would miss thumb-zone, touch-target, sticky-CTA, and mobile-drawer coverage.

**Quick-scan does NOT apply override rules.** Quick-scan selects exactly one cluster based on the page-type default or explicit `--focus` value, period. No additions, no expansions.

---

## Legacy v4.x cluster name handling on resume

When resuming an engagement created in v4.x, the loader silently maps old cluster names to v5.0 equivalents at load time. The on-disk `meta.json` is NOT rewritten — the translation applies only to the in-memory representation of the resumed engagement.

The full translation table and apply-at-load-time rules live in `${CLAUDE_PLUGIN_ROOT}/contracts/cluster-migration.md` — read that file as the canonical source.

Resumed v4.x engagements get the closest semantic mapping and do NOT retroactively gain coverage from new clusters that didn't exist when they were created. If an engagement needs coverage from a new v5.0 cluster, re-run the audit as a new engagement (do not resume).

---

## Resolution algorithm (for coordinator implementation)

The coordinator in each skill resolves clusters in this exact order. Implementations must not skip steps or apply them out of order:

1. **If `--focus` (or `--cluster` / `--clusters`) is set:** parse the value(s) using the `--focus` flag value mapping table above. The user explicitly named what they want — use it exactly.
2. **Otherwise:** use the page-type default cluster set from the routing table above.
3. **Apply override rules** (non-Western market, significant price display, mobile-first device list) — these can ADD clusters but never REMOVE them. Skipped in quick-scan.
4. **Deduplicate** the resolved set.
5. **Set `clusters_used` in `meta.json`** to the final deduplicated list. This is the canonical record of what was actually dispatched, used on resume and for aggregation queries.

After resolution, the coordinator presents an informational confirmation (NOT a blocking question):

> "Auditing {page_type} with **{N} clusters**: {cluster list}.
> {If --focus was used: 'You set --focus={value}.'}
> {If override rules added clusters: 'Added {cluster} because {reason}.'}"

This is informational only — the user doesn't answer it. If the user wants to change the cluster selection, they re-invoke with `--focus`.

---

## Cross-skill references

Skills that use this file:

- **`skills/audit/SKILL.md`** — `<domain_cluster_routing>` defers here. `<cluster_selection>` references the resolution algorithm above.

When editing this file, grep `skills/audit/` for any stale inline cluster documentation that may have been missed and convert to references.
