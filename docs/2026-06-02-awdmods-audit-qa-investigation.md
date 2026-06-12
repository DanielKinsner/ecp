# QA Investigation: ECP Audit of awdmods.com (2026-06-02-3c7ddb73)

> **📜 HISTORICAL — banner added 2026-06-12.** Point-in-time QA investigation (2026-06-02). The hotspot/accuracy failure classes it documents drove the hotspot-accuracy program and were resolved or re-triaged via the consolidated 2026-06-09/10 roadmap ([reviews/2026-06-10-consolidated-findings-and-plan.md](reviews/2026-06-10-consolidated-findings-and-plan.md), EXECUTED) and its post-roadmap fix plan ([reviews/2026-06-10-post-roadmap-review-and-fix-plan.md](reviews/2026-06-10-post-roadmap-review-and-fix-plan.md)). Re-triage anything that still looks undone against the current chain — CLAUDE.md §"Start here" is the live pointer.

## 1. Executive Summary

The audit is **largely accurate at the claim level but materially weak at the hotspot level**. Across 37 findings verified, **3 contain materially false or contradicted claims** (1 critical false-absence, 2 false-absence framings about already-implemented patterns) and **~8 carry minor framing imprecision**. Of **52 hotspot markers verified (32 desktop + 20 mobile)**, **18 are WRONG_LOCATION (~35%)**, dominated by two systemic placement bugs: a slide-projection error that mis-maps elements near slide boundaries, and a canned "section-bottom-overlay" default at y=77.5% (desktop) / y=77.7% (mobile) that mislocates hero-band ghosts. The single biggest problem class is **false-absence claims where the recommended pattern already exists in the page** (cart-drawer shipping bar, logo alt text, newsletter aria-label) — these would generate no-op or actively wrong recommendations if a client implemented them.

**Headline:** 3 of ~37 findings materially false; 18 of 52 hotspots misplaced; 1 critical defect (logo alt) must be pulled before shipping.

---

## 2. False / Contradicted Claims

### CRITICAL — `trust-credibility F5` (mobile): "Logo Image Has No Alt Text"
- **Claim:** "The AWDMods logo image (e47) has no alt text / empty accessible name" and "Screen-reader users hear an unlabeled graphic."
- **Actually true:** `dom-mobile.html` line 672: `<img ... alt="AWDMods" ...>`. The baton selector `'img[alt]:not([alt=""])'` **by construction** only matches images with non-empty alt — so e47 cannot have an empty alt. The auditor confused baton's empty `text_content` field (always empty for `<img>`) with the alt attribute.
- **Severity:** CRITICAL. The recommendation ("Set the logo image's alt attribute to AWDMods home") is a no-op at best, a regression at worst. This finding must be pulled before client delivery.
- **Cross-confirmed by ground-truth check #8:** CONTRADICTED — `dom.html` line 671 also carries `alt="AWDMods"`.

### MAJOR — `pricing F-3` (desktop) and `pricing F-3` (mobile): "Free-Shipping Banner Lacks Progress Framing / No Dynamic Cart Calculation"
- **Claim (mobile F-3):** "Threshold is communicated only at the page top — not at the price element or in cart." Recommends "add a dynamic progress bar in the cart drawer."
- **Claim (desktop F-3):** "The page never tells the close-to-threshold visitor 'add $26 more to qualify'."
- **Actually true:** `dom.html` line 112 / `dom-mobile.html` lines 112-115 already contain a working cart-drawer progress component: `<div class="drawer__shipping-bar"><div class="caption">YOU'RE <strong>$75.00</strong> AWAY FROM <strong>FREE SHIPPING</strong>!</div><div class="free-shipping-bar" style="--shipping-bar-width: 0.0%; ..."></div></div>`. The CSS-variable-driven width bar is fully implemented.
- **Severity:** MAJOR. The recommendation is partly redundant. The real lift (mirror this existing component up to the announcement bar / add a per-price-element "Add $X for free shipping" line) is hidden behind a false-absence framing. Should be reframed as a "propagate existing component" job — like the desktop pricing F-4 Borla MSRP finding correctly does.

### MAJOR — `performance-ux F-4` (desktop): "Fitment Finder Forces Four Sequential Dropdowns"
- **Claim:** "With a four-step funnel as the only homepage path to product, you measure conversion against every visitor who balks at clicking 'Select Make' first."
- **Actually true:** `section-1.jpg` shows: (1) top nav with "Shop All / Shop by Category / Shop by Vehicle" (all 1-click), (2) **five category cards** each with a `SHOP <CATEGORY>` button at `/collections/performance` etc. (`dom.html` line 1159), (3) Featured Collection grid below. The funnel is not the only path; it is one of at least three above-the-fold paths to product.
- **Severity:** MAJOR. The funnel critique still holds (4 sequential dropdowns is friction), but the "only path" framing misrepresents the page and inflates conversion impact estimates.

### MAJOR — `performance-ux F-1` (desktop): "LCP Forced to Logo or Off-Screen Image"
- **Claim:** "LCP metric is forced to either the tiny logo (e62, 80x45) or the first off-screen product image."
- **Actually true:** `dom.html` line 1135 shows the Performance category card uses an actual `<img width=3200 height=3200 fetchpriority="high">` at y=544 — **above fold and already prioritized**. Rendered at ~273x302 (~82,446 px²), it dwarfs the 80x45 logo (3,600 px²) and is the most likely LCP candidate.
- **Severity:** MAJOR. The hero-band-is-empty observation is correct, but the LCP-forced-to-logo claim misreads the page. Reframe as "hero band lacks LCP-eligible content; the actual LCP candidate is a category card image well below the headline-eligible zone."

### MAJOR — `performance-ux F1` (mobile): "Entire Navigation System Disappears After Hero Scrolls Off"
- **Claim:** "Once a shopper scrolls past the hero, the entire navigation system disappears — the hamburger, search, account, and cart icons all sit in the top header and scroll away."
- **Actually true:** `dom-mobile.html` line 517 has class `shopify-section-header-sticky scrolling-down scrolled-past-header` and a `<sticky-header>` custom element wraps the header. `section-2-mobile.jpg` and `section-3-mobile.jpg` both visibly show hamburger, logo, account, cart, and search bar pinned to the TOP during scroll. The header IS sticky.
- **Severity:** MAJOR. The valid critique (thumb-zone reachability — top-corner icons are awkward) survives, but the auditor framed a thumb-zone problem as a missing-header problem. The "no sticky bottom CTA" headline of the finding is correct; the supporting claim that the top header scrolls away is wrong.

### MAJOR — `performance-ux F4` (mobile): "Newsletter Submit Button Has No Accessible Name / WCAG 4.1.2 Failure"
- **Claim:** "The button's accessible-name string is the CSS class list 'newsletter-form__button field__button font-bold'... creates an automated WCAG 2.1 Name/Role/Value (4.1.2) failure."
- **Actually true:** `dom-mobile.html` line 2515: `<button ... aria-label="Subscribe">`. aria-label resolves the AccName to "Subscribe", and screen readers announce "Subscribe button." 4.1.2 is satisfied. The baton's `accessible_name` field captured the class attribute in error; the auditor propagated that mistake.
- **Severity:** MAJOR for accuracy (the WCAG hook is wrong), MEDIUM for the underlying finding (visible-label parity / icon-only conversion clarity IS still a real concern — but should hook to WCAG 1.3.1 / 3.3.2, not 4.1.2).
- **Cross-confirmed by ground-truth check #9:** PARTIAL — visible arrow-only is real, but aria-label="Subscribe" is present.

### CONTRADICTED — `pricing F-2` (desktop): "Four Tiles at or Above $400"
- **Claim:** "Featured Collection contains four tiles at or above $400 (Borla $1,649.99, Magnaflow $1,766.00, Injen $437.91, Lloyd Mats $135.99)."
- **Actually true:** $135.99 is not ≥ $400. Three tiles are above $400, not four. Self-contradicting bullet.
- **Severity:** MINOR. The core BNPL-absence finding is correct; only the evidence-anchor count is wrong.

### MISLEADING — `trust-credibility F1` (mobile): "Lead Featured Product Has Only 2 Reviews"
- **Claim:** "The Revo Designs SKU is the lead/featured product in the Featured Collection."
- **Actually true:** `dom-mobile.html` line 1387 shows Lloyd Mats VelourTex mats as Slide 1; Revo Designs is Slide 2. The actual lead card carries NO rating widget at all.
- **Severity:** MINOR. The core thin-review-volume concern (2, 3, 3 across featured SKUs) is correct; only the "lead" framing is wrong.

### MISLEADING — `ethics F-2`: "Visible Review Count" Wording
- **Claim:** "(N) N total reviews" rendered as "explicit visible count."
- **Actually true:** Only the `(N)` numeral is visible; "N total reviews" is in a `visually-hidden` span (screen-reader-only).
- **Severity:** MINOR. The PASS verdict still holds (a real backing count IS shown), but the evidence wording overstates what's on screen.

### MISLEADING — `visual-cta F-1` (mobile): Title Dash Character
- **Claim:** Title is "AWDMods — AWDMods" (EM-dash).
- **Actually true:** Title uses EN-dash: "AWDMods – AWDMods" (U+2013).
- **Severity:** TRIVIAL. The duplication observation is correct; only the dash character is misquoted.

---

## 3. Unverifiable / Weak Claims

| f_ref | Claim | Why unverifiable | What would settle it |
|---|---|---|---|
| `trust-credibility F-5` desktop | "Will this look right on my car" is the dominant buyer question | Qualitative buyer-intent assertion | Category-specific user research or session-replay data |
| `trust-credibility F-6` desktop | "PayPal Seal Attracts Most Visual Attention (67% Notice Rate)" | External Silver-tier citation, not page evidence | Properly tier-tagged — fine as Silver |
| `pricing F-3` desktop | "Baymard's 39% extra-cost abandonment" | External stat outside captured artifacts | Cite directly from `free-shipping.md` reference file |
| `pricing F-2` mobile | "Shop Pay Installments could be enabled with one toggle" | Depends on merchant region/volume eligibility, not in page DOM | Merchant account audit / Shopify admin check |
| `performance-ux F-2` mobile | "Each dropdown opens a separate full-screen wheel picker" | DOM shows custom `.nice-select` widgets (JS-driven, suppress native picker); behavior depends on runtime | Live mobile device test |
| `performance-ux F-3` mobile | "No progressive feedback as fields are filled" | Static capture cannot prove interactive behavior | Live form interaction recording |
| `performance-ux F-1` mobile | "Bottom navigation has been shown to lift engagement 25–50%" + "Airbnb's redesign drove 38% more feature engagement" | External stats not validated against source | Pull from `mobile-conversion.md` reference |
| `performance-ux F4` mobile | "95.9% of homepages fail WCAG (WebAIM Million)" | External citation | Reference passthrough |
| `ethics F-1` | "ADJACENT not BLOCK because staging URL presumably redirects to awdmods.com" | Captures did not probe the staging host | Live HTTP probe of `https://e1520g-k3.myshopify.com/policies/privacy-policy` |
| `visual-cta F-5` mobile | "Grid mixes Focus RS/ST and Subaru WRX/STI parts" | Only two cards visible in captured sections | Capture additional scroll depth or read full DOM grid |
| `visual-cta F-6` mobile | Search bar is sticky | Inferred from sticky-header class + visual confirmation in sections 2/3 | Baton already records `is_sticky=false` at capture (scroll_y=0) — known baton quirk, not an audit error |

---

## 4. Hotspot Problems

### Desktop — 9 of 16 unique findings WRONG_LOCATION

**Pattern A — Slide-clamp on e50 "Featured Collection" h2** (4 findings, 8 markers):
- `performance-ux F-17`, `trust-credibility F-48`, `visual-cta F-10`, `visual-cta F-41`
- e50's source-y=906 falls inside slide-1 (y=0..930), not slide-2 (y=931..1814). When the renderer projects to slide-2, y_pct=(906-931)/1080=-2.3% gets clamped to 0%, placing the marker on the sticky AWDMods navigation header instead of the actual "Featured Collection" h2 (visible at bottom of `section-1.jpg` around y_pct=84%).
- `visual-cta F-41` is **doubly wrong**: it also snapped to the wrong element (the h2 instead of the five "SHOP X" category buttons it describes).

**Pattern B — Canned 77.5% section-ghost on slide-1** (5 findings, 10 markers):
- `performance-ux F-37` (hero LCP), `performance-ux F-69` (fitment finder), `pricing F-58` (free-shipping bar — **mislocated by 75 percentage points; the bar is at the TOP of slide-1, not the bottom**), `visual-cta F-11` (hero headline), `visual-cta F-37` (primary CTA), `visual-cta F-38` (trust signal)
- All default to `(50%, 77.5%)`, landing in the white gap between category cards and "Featured Collection" h2 — well BELOW the actual hero band (source y~120-540, image y_pct~11-50%). Hero ghosts should sit in the dark hero region.

**ACCEPTABLE_PROXY (desktop):** `ethics F-01` (slide right, x=50% misses left-column Privacy Policy link), `performance-ux F-20` (head prefetch — no visible target so any slide-1 placement is fine), `trust-credibility F-05` (sits on e60 instead of after it, but right card/slide), `trust-credibility F-84` (bottom-of-slide-2 is a reasonable "after Featured Collection" ghost).

### Mobile — 9 of 20 unique findings WRONG_LOCATION

**Pattern C — Slide-3 vertical projection bug** (3 findings):
- `performance-ux F-01` (e43 "Information" accordion), `performance-ux F-94` (e50 newsletter button), `trust-credibility F-81` (e63 Apple Pay)
- All three snapped element indices are CORRECT, but the CSS-y → slide-y conversion drops them 20-40 percentage points TOO LOW, landing in the empty black band below the copyright. Likely cause: slide_y is being mapped against `scroll_y_top=1461 / bottom=2305` (an 844-px CSS viewport coordinate space) while baton element rects live in the 0-8622 full-page coordinate space — the renderer is using one space for the slide and another for the element.

**Pattern D — Canned 77.7% section-bottom-overlay on slide-1** (mobile equivalent of Pattern B):
- `pricing F-57` (FREE SHIPPING bar — actually at ~2.5% of slide 1, marker at 77.7% misses by ~75 percentage points), `visual-cta F-12` (headline insertion proposed between search and dropdowns at ~22-26% — marker at 77.7% is in the wrong half)
- Works as a section-bottom-overlay convention for whole-hero-band findings (F-47, F-70, F-36, F-39 — ACCEPTABLE_PROXY), but fails for findings whose subject is at the top or middle.

**Other mobile misplacements:**
- `trust-credibility F-27` ("guarantee below FIND PARTS"): marker at y=22.4% lands on the search bar, well above the CTA at ~58%.
- `ethics F-01` (mobile): marker at slide-3 y=90% lands in the empty black band below the copyright; the Privacy Policy link is not even rendered in the visible `section-3-mobile.jpg` capture — effectively unresolvable for the operator.

### Proxy-overload pattern assessment
The audit relies heavily on section-ghost / viewport-ghost markers for absence findings. **The pattern itself is reasonable** — a "missing trust signal" finding genuinely has no DOM element to pin against. The problem is the **renderer's canned defaults** (77.5% / 77.7%) treat all section-ghosts identically regardless of whether the subject is at the top, middle, or bottom of the section. A correctly-built section-ghost system would take the finding's `proposed_anchor` semantics ("before-element X", "after-element Y", "viewport-top", "viewport-bottom") into account when placing the marker.

---

## 5. Ground-Truth Notes

**Live cross-check:** WebFetch on `https://www.awdmods.com/` succeeded and corroborated captured DOM. No capture-vs-live drift detected on any verified claim.

**CONFIRMED outright (7/11):**
1. Hero is bare 4-dropdown selector with no H1/CTA/trust/LCP image
2. Title is duplicate "AWDMods – AWDMods" (EN-dash)
3. Only Borla SKU shows strikethrough MSRP
4. Three tiles show 5.0/5.0 on 2-3 reviews
5. JSON-LD is only OnlineStore + WebSite (no Product/AggregateRating/ItemList)
6. `<head>` prefetches 76 Shopify checkout chunks (audit said "70+" — exact)
7. Catalog is Subaru WRX/STI + Ford Focus RS/ST only

**PARTIAL (3/11):**
- **Privacy Policy staging-host leak (claim #7):** The footer Privacy Policy link IS https://e1520g-k3.myshopify.com/... (real). But the four My Account / Order History / Wish List / Track My Order links visibly point at `https://account.awdmods.com/...` — the staging host only appears **embedded inside the JWT `buyer_flags` query param** (JWT issuer claim `iss: e1520g-k3.myshopify.com`). The leak is real but the audit should specify "JWT payload" vs "visible href."
- **Newsletter button (claim #9):** Visually arrow-only confirmed. But `aria-label="Subscribe"` IS present (`dom.html` line 2546 / `dom-mobile.html` line 2515).
- **Shop Pay Installments (claim #10):** Payment row Visa/MC/PayPal/Shop Pay confirmed. But **no Shop Pay Installments badge or banner exists anywhere on the page or in WebFetch**. The only "installment" string in DOM is the prefetched checkout JS chunk `helpers-installmentsNotSupportedForAddress.BOCZuYce.js` — an internal helper, not a user-visible offering.

**CONTRADICTED (1/11):**
- **Header logo alt text (claim #8):** `dom.html` line 671 carries `alt="AWDMods"`. Logo is correctly labeled.

---

## 6. What Held Up

**Claim accuracy (the good news):**
- All 6 findings in `cluster-visual-cta-desktop.json` verified accurate. Every absence claim (no H1, no CTA, no trust signal, no AggregateRating schema) confirmed as genuine absence in baton + DOM + screenshots. Every cited element (e17, e50, e94) matches text_content/role/y-position exactly.
- All 6 findings in `cluster-trust-credibility-desktop.json` factually well-grounded. Element anchors (e61, e50, e60, e94) match baton ground truth exactly.
- `pricing F-1` (Borla unique MSRP), `pricing F-4` (Borla as working template), `performance-ux F-2` (checkout prefetch — 56 scripts + 20 styles = 76 exact match), `performance-ux F-3` (Featured Collection generic heading), `performance-ux F-5` (category card praise) — all clean.
- All 6 `ethics-findings.json` checks pass factually, including the high-stakes `ethics F-1` Privacy Policy staging-host claim (every element of the JWT decode verifies).
- Mobile `pricing F-4` charm-pricing PASS — accurate.
- Mobile `trust-credibility F2/F3/F6` (no reviews section, no returns/fitment hero copy, no UGC) — clean absence claims, DOM-grep-verified.

**Hotspot placement (the good news):**
- **Desktop CORRECT (3 unique findings):** `pricing F-41` (e60 price block — exact match), `trust-credibility F-38` (e61 rating widget on Revo Designs card — within ~1% of element center), `pricing F-96` (BNPL ghost correctly placed 50px below the $135.99 price).
- **Mobile CORRECT (7 unique findings):** `performance-ux F-18` (viewport-bottom-sticky ghost — conventional placement), `pricing F-16` (e45 price block direct hit), `pricing F-97` (BNPL ghost below price), `trust-credibility F-28` (e47 logo — pixel-perfect), `trust-credibility F-33` & `F-75` (UGC/reviews ghosts below Featured Collection — reasonable), `visual-cta F-10` (e42 h2 direct hit), `visual-cta F-67` (sticky-bottom-bar viewport ghost).

---

## 7. Root Causes

1. **False-absence from baton-field misreading (CRITICAL):** Two findings (`trust-credibility F5` mobile logo alt, `performance-ux F4` mobile newsletter aria-label) trusted baton's `accessible_name` / `text_content` fields without cross-checking the actual DOM `alt` / `aria-label` attributes. The baton selector `'img[alt]:not([alt=""])'` by construction guarantees a non-empty alt — yet the finding claimed the alt was empty. **Specialists need to verify absence claims against `dom.html` not just baton fields.**

2. **False-absence from incomplete page exploration:** Three findings (`pricing F-3` desktop free-shipping, `pricing F-3` mobile free-shipping, `pricing F-1` mobile MSRP) recommend adding patterns that already exist elsewhere on the page (cart-drawer shipping bar at `dom.html` line 112; Borla strikethrough MSRP on a sibling card in the same rail). **The specialist routing only saw a subset of the relevant cards/zones.** Synthesizer should cross-check recommendations against existing DOM patterns before publishing.

3. **Hotspot slide-projection bug (HIGH PRIORITY):** Element rects near slide boundaries get clamped to 0%/100% instead of being routed to the correct adjacent slide. Affects all e50-based markers on desktop (Pattern A: 4 findings, 8 markers) and 3 of 4 slide-3 element markers on mobile (Pattern C). Likely fix: when projected y_pct < 0% or > 100%, re-route the marker to the adjacent slide rather than clamping.

4. **Hotspot section-ghost default placement bug (HIGH PRIORITY):** All section-absence ghosts on slide-1 default to `(50%, 77.5%)` (desktop) / `(50%, 77.7%)` (mobile), placing 5+ hero-band findings in a white gap that is nowhere near the hero. Fix: use the finding's `proposed_anchor` semantics (`viewport-top` / `before-element` / `after-element`) to compute placement rather than a constant.

5. **Overstated framing on real findings:** Several findings have a correct core observation wrapped in overstated framing (`performance-ux F-1` desktop "LCP forced to logo" when category card images are actually LCP-eligible above-fold; `performance-ux F-4` desktop "only homepage path to product" when 3+ paths exist; `performance-ux F1` mobile "entire navigation system disappears" when header is sticky). The core observations would be defensible if reframed; the overstatement creates credibility risk.

6. **Mathematical / categorical imprecision:** `pricing F-2` desktop lists $135.99 under "at or above $400"; `visual-cta F-5` desktop says "35x price range" when actual is ~88x; `trust-credibility F-1` desktop says "three other featured products" carry 5.0/(3) when only two do. Low-stakes but reads sloppy in a polished deliverable.

7. **External stats not load-bearing-verified:** Bronze/Silver-tier citations (NNGroup 25-50%, Airbnb 38%, WebAIM 95.9%, Baymard 39%) carry through findings without inline verification. Tier-tagging is fine for ranking, but high-trust citations should be passthrough-verified at synthesis time.

---

## 8. Recommendations

### Pre-Ship Fixes (this audit, before client delivery)

1. **PULL `trust-credibility F5` mobile (logo alt text)** — the recommendation is a no-op/regression. Remove from deliverable.
2. **REWRITE `performance-ux F4` mobile (newsletter button)** — drop the WCAG 4.1.2 hook, drop the "accessible-name is class list" claim. Reframe as "visible-label parity / icon-only conversion clarity" with WCAG 1.3.1 / 3.3.2 hooks.
3. **REWRITE both `pricing F-3` findings (free-shipping)** — acknowledge the existing cart-drawer progress bar. Reframe as "propagate the existing cart-drawer pattern up to the announcement bar" + "add per-price-element 'Add $X for free shipping' line." Mirror the framing of desktop `pricing F-4` (Borla MSRP).
4. **REWRITE `pricing F-1` mobile (MSRP)** — acknowledge the Borla sibling card already implements the pattern. Reframe as "extend the existing strikethrough pattern from Borla to remaining 8 tiles" — a data-feed/Shopify product-data job, not a new component.
5. **REWRITE `performance-ux F-4` desktop (fitment finder)** — drop "only homepage path to product." Keep the 4-step funnel critique but acknowledge the 5 category buttons and top nav as alternative paths.
6. **REWRITE `performance-ux F1` mobile (sticky CTA)** — keep the "no sticky bottom CTA" headline. Drop "entire navigation disappears" supporting claim. Reframe as "top-corner placement vs thumb-easy bottom zone."
7. **REWRITE `performance-ux F-1` desktop (LCP)** — keep "hero band lacks LCP-eligible content." Drop "LCP forced to logo." Add: "Most likely LCP candidate is a category card image at y=544, well below where a hero headline should sit."
8. **TIGHTEN `ethics F-1` claim wording** — specify that staging-host leak in My Account/Order History/etc. is in the **JWT `buyer_flags` payload**, not the visible `href`.
9. **DROP "Shop Pay Installments available" framing** from any pricing finding — there is no installments badge anywhere on the page. The Shop Pay logo in the wallet strip does not imply Installments is configured.
10. **FIX trivial imprecision:** `pricing F-2` desktop ($135.99 not ≥$400); `visual-cta F-5` desktop (35x → 88x or rephrase); `trust-credibility F-1` mobile ("lead" → "second card"); `trust-credibility F-1` desktop ("three other" → "two other"); title dash character on `visual-cta F-1` mobile.
11. **FIX hotspot placements** for the 18 WRONG_LOCATION markers before they render in the client deliverable — at minimum, manually re-pin the Pattern A (e50 clamp) and the worst Pattern B/D offenders (`pricing F-58` / `pricing F-57` FREE SHIPPING ghost at the page top, not 77.5%/77.7% down).

### Pipeline Fixes (compound on future audits)

**Claim-verification layer:**
- Add a "false-absence guard": for every absence finding, run a DOM grep for the recommended pattern (alt-text, aria-label, shipping-bar, MSRP) **before** publishing. If the pattern is found elsewhere in the DOM, demote to "extend existing pattern" framing.
- Stop trusting baton's `accessible_name` / `text_content` for accessibility findings. Use raw DOM attributes (`alt`, `aria-label`, `aria-labelledby`) as the source of truth.
- Cross-check `<head>` schema-type counts (currently only OnlineStore + WebSite) into a structured negative-evidence cache so the synthesizer never recommends adding what already exists.

**Hotspot renderer:**
- **Fix slide-projection clamp:** when source-y crosses a slide boundary (within ~5% of boundary), route the marker to the adjacent slide rather than clamping to 0%/100%. This alone would fix 11 of 18 WRONG_LOCATION markers (Pattern A + Pattern C).
- **Replace canned 77.5%/77.7% section-ghost default** with placement-aware logic: when `proposed_anchor.placement` is `viewport-top`, render at y=5%; `viewport-bottom` at y=92%; `before-element X` at `element_y - 5%`; `after-element X` at `element_y + element_height + 2%`. Default to slide-center only when no semantic anchor is given.
- **Investigate mobile slide-3 coordinate-space bug:** the audit notes slide_y is being mapped against `scroll_y_top=1461 / bottom=2305` (an 844-px CSS viewport coordinate space) while baton element rects live in the 0-8622 full-page coordinate space. Pick one space and stick to it.

**Reference-citation layer:**
- Auto-passthrough-verify Gold-tier stats (Baymard, Spiegel, SearchPilot) by extracting the cited number from the reference file at synthesis time, not at specialist time, so synth can flag drift.

**Quality gate before client delivery:**
- Run a "patterns-already-implemented" sweep: grep DOM for every component the audit recommends adding. Any hit triggers manual review.
- Render every hotspot and have a human verify position-on-image for at least the top-5-priority findings before shipping.

---

## 9. Independent Live Re-Capture Corroboration (lead-added)

After the ad-hoc `agent-browser --session qa` call wedged, live verification was NOT abandoned — the page was re-captured live via the proven `scripts/acquire_url.py` (the same agent-browser wrapper that captured the original audit, timeout-bounded with daemon close/restart) into engagement `2026-06-02-ab12cd34`. The fresh capture is byte-near-identical to the original (`dom.html` 228,760 vs 228,788 B — no meaningful drift) and independently confirms the workflow's headline verdicts:

| Audit claim | Independent live re-capture | Verdict |
|---|---|---|
| Logo image has NO alt text (`trust-credibility F5` mobile) | `alt="AWDMods"` present | **FALSE — confirmed contradicted** |
| Newsletter submit has no accessible name / WCAG 4.1.2 fail (`performance-ux F4` mobile) | `aria-label="Subscribe"` present | **FALSE — confirmed contradicted** |
| No free-shipping progress component (`pricing F-3` both devices) | `drawer__shipping-bar` + `free-shipping-bar` present | **FALSE-ABSENCE — component already exists** |
| Shop Pay Installments available (lead report framing) | 0 user-facing Installments references | **UNSUPPORTED — no Installments offering on page** |
| Only OnlineStore + WebSite JSON-LD; no Product/AggregateRating | live `@type`s = OnlineStore, WebSite, SearchAction | **TRUE — schema-absence confirmed** |
| Staging host in account/policy links | `e1520g-k3.myshopify.com` present | **TRUE — staging-host leak confirmed** |
| 70+ prefetch assets in head | 81 `rel=preload/prefetch/dns-prefetch/preconnect` | **TRUE (ballpark) — confirmed** |
| Duplicate title "AWDMods – AWDMods" | live title = "AWDMods – AWDMods" (EN-dash) | **TRUE — confirmed** |

**Method note:** this used `acquire_url.py` (agent-browser, wrapped + 180s/device budget) — the same tool via the reliable path, not the wedged ad-hoc session. The workflow's ground-truth phase independently reached identical conclusions via WebFetch. Two independent live fetches + the captured artifacts all agree.

_QA investigation run on Opus 4.8 (13 workflow agents: 9 claim verifiers, 2 hotspot verifiers, 1 ground-truth, 1 synthesizer) + independent live re-capture._
