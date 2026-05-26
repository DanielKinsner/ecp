# Page detection

Algorithms for detecting page type from URL patterns (pre-acquisition) and page patterns from DOM signals (post-acquisition).

**Why this file exists:** Page type and pattern detection are reusable across any skill that needs to classify an e-commerce page before dispatching auditors (audit, compare, quick-scan). Extracting them from the audit skill makes them a single canonical source for URL-based classification heuristics and DOM-based configurator detection.

**Read this file when:** you are any `/ecp:*` skill coordinator that needs to classify a page before cluster routing.

---

## Page type detection (pre-acquisition)

Detect page type from URL patterns. DOM is not yet available at this point in the flow.

| URL pattern | Page type |
|---|---|
| `/products/` or `/product/` | product |
| `/cart` | cart |
| `/checkout` | checkout |
| `/collections/` or `/category/` | category |
| Root path `/` with no product/collection path | homepage |
| `/pages/` with pricing keywords | landing or pricing |
| Ambiguous from URL alone | Ask the user: "What type of page is this? (product, category, homepage, cart, checkout, landing, pricing)" |

Set `page.type` in meta.json. This determines cluster routing via the domain_cluster_routing table.

### Post-acquisition refinement

After acquisition completes, if the pre-acquisition classification was based on user input or a weak URL match, verify against DOM signals in the baton:
- `form[action*='cart']` -> product
- `[class*='checkout']` -> checkout

Update `page.type` in meta.json if the DOM contradicts the initial classification. This refinement runs alongside page pattern detection (below).

---

## Page pattern detection (post-acquisition)

After acquisition completes and baton is validated, check for configurator patterns in the DOM:

1. Look for: multiple required `<select>` elements with empty/placeholder defaults, a disabled CTA button (`disabled` attribute, class containing `disabled`), dynamic price elements, validation messages requiring selections before purchase
2. Also check for: `[class*='fitment']`, `[class*='compatibility']`, `[class*='configurator']`, `[class*='vehicle']`, `[class*='year-make-model']`
3. If 2+ required selects exist above the primary CTA AND the CTA is disabled in default state, classify as `page_pattern: 'configurator'`

### If configurator detected

- Set `page_pattern: "configurator"` in meta.json
- Include `page_pattern: "configurator"` in every auditor dispatch (the auditor workflow has instructions for how to adjust evaluation -- see `workflows/audit.md` "Configurator Page Context")
- This changes how auditors evaluate CTA visibility and price placement -- they assess configurator UX quality rather than flagging gated CTAs as missing

### If not detected

Omit `page_pattern` from meta.json. Auditors will evaluate normally.
