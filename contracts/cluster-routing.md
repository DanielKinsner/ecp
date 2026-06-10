# Domain cluster routing

Canonical routing table for ECP's 10-cluster architecture. `/ecp:audit` references this file for page-type defaults, `--focus` flag mapping, and override rules. Spec authority: `product.md` §2.3 v1.2 (the canonical audit dispatches every cluster relevant to the detected page type).

**Why this file exists:** cluster routing used to live inline in `skills/audit/SKILL.md`, with build/compare deferring to it across a hidden cross-skill coupling. This file is the first-class canonical reference that no skill owns — `/ecp:audit` defers here, and the §5-frozen modes' interface contracts live here too.

---

## The 10 clusters (v5.0+)

Each cluster owns a specific set of reference files. Cluster specialists load ONLY their cluster's reference files (plus the always-loaded ethics gate + evidence tiers files) — not the full reference library.

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

**Note on `performance-ux` (v1.1 rename from `mobile-performance`):** This cluster covers **all viewports**, not just mobile — four of its five reference files (`cognitive-load-management`, `page-performance-psychology`, `core-web-vitals`, `media-performance-optimization`) are device-agnostic. The prior name led desktop audit users to expect the cluster to be skipped on desktop; it was not, and it should not be. `mobile-conversion.md` remains in the cluster to carry mobile-specific guidance when the specialist runs against mobile viewports. The legacy slug `mobile-performance` is accepted on resume and maps to `performance-ux` — see `contracts/cluster-migration.md`.

---

## Page type → default cluster routing (v1.2)

Spec authority: `product.md` §2.3 (v1.2). A canonical audit dispatches **every cluster relevant to the detected page type** — the `standard` set below. This is the default for every `/ecp:audit` invocation; no other scope is offered automatically. `everything` (all 10 clusters) and `custom` (operator-picked) stay available on explicit operator request via `--focus` or the scope prompt.

### Standard defaults — the canonical audit scope

The standard set is every cluster relevant to the detected page type. Resolved from the page-type column below.

| Page Type | Standard Clusters (all relevant for this page type) |
|-----------|------------------------------------------------------|
| Product page | `visual-cta`, `trust-credibility`, `pricing`, `product-media`, `content-seo`, `performance-ux` |
| Cart | `checkout-flows`, `trust-credibility`, `pricing` |
| Checkout | `checkout-flows`, `trust-credibility`, `performance-ux` |
| Homepage | `visual-cta`, `trust-credibility`, `content-seo`, `performance-ux`, `pricing`, `category-navigation` |
| Category / Collection | `category-navigation`, `visual-cta`, `performance-ux`, `content-seo` |
| Landing page | `visual-cta`, `trust-credibility`, `pricing`, `performance-ux` |
| Pricing / Plans | `pricing`, `trust-credibility`, `visual-cta` |
| Post-purchase / Confirmation | `post-purchase`, `audience` |

**Back-compat note (pre-v1.2 name):** this is the set previously called `comprehensive` (and is still written as `comprehensive` in `meta.json` `scope` on engagements created before v1.2). New v1.2 engagements write `scope: "standard"` for the same set. See `contracts/meta-schema.md` "Valid `scope` values".

### Explicit-opt-in scopes

These remain available on explicit operator request — they are NOT the default and are NOT offered as defaults by `--auto`.

| Scope | How it's invoked | Clusters dispatched |
|-------|------------------|---------------------|
| `everything` | `--focus all` (or interactive scope prompt option e) | All 10 clusters, regardless of detected page type |
| `custom` | Comma-separated `--focus <slug1>,<slug2>,...` (or interactive scope prompt option d) | Exactly the operator's listed cluster set |
| `focused` | Single `--focus <slug>` (or interactive scope prompt option a) | Exactly one cluster |

The legacy 3–4-cluster default tier (called `standard` before v1.2) is **retired** — the canonical audit no longer offers a reduced-scope default. Operators who want to limit scope must do so explicitly via `--focus` or `custom`.

(Single-cluster scan modes that pick exactly one cluster and skip override rules are out of scope in this build — see `product.md`.)

---

## `--focus` flag value mapping

`--focus` accepts cluster slugs directly OR high-level domain values that map to one or more clusters.

| `--focus` value | Resolves to clusters |
|-----------------|-----------------------|
| (no flag) | Page-type standard defaults from the table above (all clusters relevant to the detected page type, per `product.md` §2.3 v1.2). |
| `all` | All 10 clusters (the `everything` scope). |
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

## Quick-scan single-cluster restriction (frozen mode)

Quick-scan is a `product.md` §5 frozen mode — not invokable from the canonical v1.2 audit pipeline. The rules below are retained as a §7 frozen contract so that if/when quick-scan is unfrozen via §10 it conforms to one stable cluster-routing interface.

Quick-scan picks exactly ONE cluster — it's the fast option. `--focus` in quick-scan accepts:

1. **Direct cluster slugs** (any of the 10): used as-is.
2. **Single-cluster domain aliases:** `seo` → `content-seo`, `pricing` → `pricing`, `trust` → `trust-credibility`, `mobile` → `performance-ux`, `checkout` → `checkout-flows`.
3. **Multi-cluster domain aliases (`cro`, `visual`, `content`, `all`):** would print a warning and fall back to the first cluster in that domain's mapping. For multi-cluster coverage, use `/ecp:audit` instead.

The quick-scan page-type defaults (when `--focus` is not set) are:

| Page Type | Default Cluster (quick-scan only, frozen) |
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

These rules can ADD clusters to the resolved set but never REMOVE them. They're applied after the standard page-type defaults or `--focus` resolution, during cluster selection in `/ecp:audit`.

- **Non-Western market detected** → add `audience` cluster. Detection signals: non-English primary content, non-Latin script, currency/locale markers (₹, ¥, ₩, R$, etc.), or an explicit `locale` meta tag pointing outside `en-*`, `de-*`, `fr-*`, `es-*`, `it-*`, `nl-*`, `pt-*`, `sv-*`, `no-*`, `da-*`, `fi-*`.
- **Significant price display detected** → ensure `pricing` cluster is included. Detection signals: more than 3 distinct price markers in the hero/above-fold area, explicit discount framing (strikethrough, "X% off", "was/now"), bundle offers, or payment plan markers (Klarna, Affirm, Afterpay, etc.).
- **Mobile in device set** → ensure `performance-ux` cluster is included. Triggered when the device set includes `mobile` (single or paired). The cluster hosts `mobile-conversion.md` alongside its device-agnostic page-performance references, so a mobile audit without this cluster would miss thumb-zone, touch-target, sticky-CTA, and mobile-drawer coverage.

Override rules apply to **`standard`, `custom`, and `everything`** alike: they never silently remove a cluster, only add. Quick-scan (frozen) does NOT apply override rules — it selects exactly one cluster, period.

---

## Legacy v4.x cluster name handling on resume

When resuming an engagement created in v4.x, the loader silently maps old cluster names to v5.0 equivalents at load time. The on-disk `meta.json` is NOT rewritten — the translation applies only to the in-memory representation of the resumed engagement.

The full translation table and apply-at-load-time rules live in `${CLAUDE_PLUGIN_ROOT}/contracts/cluster-migration.md` — read that file as the canonical source.

Resumed v4.x engagements get the closest semantic mapping and do NOT retroactively gain coverage from new clusters that didn't exist when they were created. If an engagement needs coverage from a new v5.0 cluster, re-run the audit as a new engagement (do not resume).

---

## Resolution algorithm (for coordinator implementation)

The coordinator in each skill resolves clusters in this exact order. Implementations must not skip steps or apply them out of order:

1. **If `--focus` (or `--cluster` / `--clusters`) is set:** parse the value(s) using the `--focus` flag value mapping table above. The operator explicitly named what they want — use it exactly.
2. **Otherwise:** use the **standard** page-type default cluster set from the routing table above (all clusters relevant to the detected page type, per `product.md` §2.3 v1.2). This is the canonical audit scope; there is no reduced-scope default.
3. **Apply override rules** (non-Western market, significant price display, mobile-first device list) — these can ADD clusters but never REMOVE them. Skipped in the frozen quick-scan mode.
4. **Deduplicate** the resolved set.
5. **Set `clusters_used` in `meta.json`** to the final deduplicated list, and set `scope` to `"standard"`, `"everything"`, `"custom"`, or `"focused"` according to which branch was taken. This is the canonical record of what was actually dispatched, used on resume and for aggregation queries.

After resolution, the coordinator presents an informational confirmation (NOT a blocking question):

> "Auditing {page_type} with **{N} clusters**: {cluster list}.
> {If --focus was used: 'You set --focus={value}.'}
> {If override rules added clusters: 'Added {cluster} because {reason}.'}"

This is informational only — the operator doesn't answer it. If the operator wants to change the cluster selection, they re-invoke with `--focus`.

---

## Cross-skill references

This file is the canonical cluster-routing reference for `/ecp:audit`. `skills/audit/SKILL.md` defers all page-type defaults, `--focus` resolution, and override rules here (Load Order: "Input and setup"). When editing this file, grep `skills/audit/` for any stale inline cluster documentation that may have been missed and convert to references.
