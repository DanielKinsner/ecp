# Checkout-Flows Specialist (v2)

Per-cluster parameter file for the **checkout-flows** specialist. Combined with the shared template body in [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) and per-engagement variables (cluster-context path, baton path, screenshots), this file produces the final dispatch prompt.

Cluster scope: cart and checkout friction, express-checkout button presence, abandoned-cart recovery mechanisms visible on-page, and cookie-consent banner UX — all signals that affect whether a shopper completes or abandons the transaction.

## Parameters

```yaml
cluster: checkout-flows
references:
  - checkout-optimization
  - biometric-and-express-checkout
  - abandoned-cart-psychology
  - cookie-consent-and-compliance
surface_vocabulary:
  - cart-summary
  - checkout-form
  - payment-options-block
  - express-checkout-button
  - shipping-and-delivery-block
  - coupon-field
  - trust-signals-block
  - progress-indicator
  - cookie-consent-banner
  - exit-intent-overlay
target_finding_count: 4-7
```

The 4 reference files are sourced from [`contracts/cluster-routing.md`](../cluster-routing.md) "The 10 clusters" table for the checkout-flows row. All 4 live at `${CLAUDE_PLUGIN_ROOT}/references/<file>.md`.

## Cluster guidance

The block below renders into the template at the `{{cluster_guidance}}` slot. It surfaces patterns the specialist should bias toward and edge cases the template body does not cover.

```
## Cluster guidance — checkout-flows

This cluster owns checkout friction, express-checkout button presence and placement, in-session
abandoned-cart recovery mechanisms (exit-intent triggers, cart-drawer state), and cookie-consent
banner UX. Bias toward findings where the evidence base is specific and measurable. The references
contain Gold-tier Baymard data and peer-reviewed field experiments — citation is never the
bottleneck here.

### page-type routing rule

**True checkout page** (URL contains /checkout, /cart, payment form present): full coverage
applies — audit all patterns listed below.

**PDP, homepage, or category page**: your scope narrows to (a) express-checkout buttons (Apple
Pay / Google Pay / Shop Pay) visible in the buy-box or product form; (b) cart-drawer / mini-cart
signals (presence, item count badge, subtotal display, express-checkout within drawer); (c)
shipping threshold framing visible on the page (free-shipping progress bar, "X away from free
shipping" copy). Do not force checkout-specific findings (form field count, progress indicators)
onto non-checkout pages.

### patterns to bias toward

**Extra costs revealed late — the #1 abandonment driver**
Baymard (Gold): 39-48% of actionable cart abandonment cites extra costs appearing late. Look for:
- Shipping cost displayed at the price block or in-cart summary vs. hidden until checkout
- Tax estimate visible in cart vs. absent (surprise tax = abandonment trigger)
- "Free shipping over $X" threshold framing: is the threshold shown on the PDP and cart, or only
  at checkout?
- On a cart page: is the running order total (subtotal + estimated shipping + estimated tax) visible
  before the user clicks "Checkout"?

**Guest checkout vs. forced account creation**
Baymard (Gold): 19% of shoppers abandon when account creation is required. Look for:
- Is a guest checkout option present and clearly labeled at the checkout entry point?
- Is the guest path the default, or is account creation the first option shown?
- Is post-purchase account creation offered ("Save your info for next time?") instead of pre-checkout
  registration?
- On mobile, does the login/account modal appear before payment options are shown?

**Express-checkout button presence and placement**
Stripe A/B (Silver): express checkout placed at the top of the flow converts at ~2x vs. placement
at the end. Shopify: Shop Pay delivers average 9% lift; Apple Pay +22.3% conversion (Stripe). Look
for:
- Are Apple Pay / Google Pay / Shop Pay buttons visible on the cart or checkout page?
- On a PDP or cart-drawer: are express-checkout buttons present in the buy-box or drawer?
- Are the buttons positioned above the email / shipping form, or buried below the standard form?
- On mobile: are the buttons visible without scrolling (above-fold at mobile viewport)?
- If buttons are absent entirely, emit a finding with `baton_index: "absent"` at the payment-options
  surface.

**Form field count**
Baymard (Gold): average US checkout has 11.3 fields; ideal is 7-8. Look for:
- Count the visible form fields in the checkout: name (first + last = 2), email (1), address line 1
  (1), city (1), state (1), ZIP (1), country (1), payment card (1) = 9 is the minimum viable set.
- Fields to flag as unnecessary unless operationally required: "Company name," "Address line 2,"
  "Phone number" (when not carrier-required), "Title / Salutation."
- Each unnecessary required field is a friction point; emit PARTIAL if the form exceeds 12 fields
  with optional fields not clearly marked.

**Address autocomplete**
Google A/B (Silver): autocomplete improves conversion by 1.5-2% and reduces address errors by 20%.
Look for:
- Does the address field offer autocomplete / lookup (dropdown appears as user types)?
- On mobile, is the address field triggering native autocomplete (autocomplete attributes present)?
- Absent autocomplete on mobile is a higher-severity finding than on desktop.

**Inline validation vs. post-submission errors**
Baymard (Silver): inline validation produces 22% higher form completion; 70% of users abandon after
bulk error messages. Look for:
- Does the form show per-field errors immediately on blur, or only after the user clicks submit?
- Are error messages specific ("Enter a valid 5-digit ZIP code") or generic ("Invalid input")?
- Are validation errors visually associated with their fields, or displayed in a summary block at
  the top?

**Progress indicators**
Silver (endowed-progress effect, academic; 30% completion lift is a single case study): Look for:
- Is a step indicator present on multi-step checkout (shipping → payment → review)?
- Does it show no more than 4 steps with meaningful labels?
- Is the first step presented as already partially complete (endowed progress)?
- Single-page checkout: progress indicator optional, but absence on multi-step is a finding.

**Cart summary visibility**
Baymard / UX consensus (Bronze): persistent order summary reduces abandonment by preventing
surprise totals. Look for:
- Desktop: is there a sidebar order summary showing line items, quantities, discounts, shipping,
  tax, and total?
- Mobile: is there a collapsible summary with the order total always visible (not hidden until
  expanded)?
- If the total is only visible after the user scrolls to the order-review step, emit PARTIAL.

**Coupon / discount code field treatment**
Baymard / Zuko (Bronze): a prominent, empty coupon field causes 27% of shoppers to leave to search
for a code; 46% abandon when they can't find one. Look for:
- Is the coupon/promo code field a visible empty text input, or collapsed behind a "Have a promo
  code?" link?
- Auto-applied promotions (banner or URL-based) are best practice; look for their presence.
- If a prominent empty coupon field is visible and no promotion is in effect, emit PARTIAL.

**Trust signals near payment**
Baymard (Gold): 19% abandon over credit-card trust concerns. Look for:
- SSL / security badges near the payment field
- Accepted card logos (Visa, MC, Amex) visible at the payment section
- Clear privacy / security language near card input
- HTTPS indicator (URL bar) — note but do not emit a finding, as this is site-level not page-level

**Delivery date / speed framing**
Baymard (Gold): 21% abandon because delivery is too slow. Look for:
- Are estimated delivery dates shown as calendar dates ("Arrives by May 3") or vague ranges
  ("5-7 business days")?
- Is expedited shipping offered with its own delivery date?
- Absent delivery date on a checkout page is a PARTIAL-worthy finding for high-AOV stores.

**Subscription checkout compliance (ROSCA / AB-2863)**
Baymard / statutory (Gold): subscriptions require clear pre-billing disclosure and a separate
affirmative consent checkbox. If the page contains subscription, recurring charge, or
free-trial-to-paid elements, look for:
- All subscription terms (price, frequency, next charge date) displayed immediately before the
  "Place Order" button
- A separate affirmative consent checkbox for the subscription, distinct from payment authorization
- Cancellation mechanism described or linked
  Describe what is present or absent in your observation neutrally — the ethics subagent handles
  the ROSCA compliance verdict; you own the UX framing.

### abandoned-cart recovery mechanisms (in-session)

These are page-level signals the specialist evaluates when the page_type includes a cart or
checkout surface.

**Exit-intent triggers**
Abandoned-cart-psychology (finding 12 / authentic urgency framing): Look for:
- Is there an exit-intent overlay or popup visible or referenced in the DOM?
- If present: does it use authentic urgency (real inventory low, real deadline) or fabricated
  countdowns / "37 people viewing" copy?
- Note the presence/absence; do not evaluate ethics framing — that belongs to the ethics subagent.

**Cart-expiry messaging**
Look for: "Your cart expires in X hours" — is the message present on the cart page?
If absent for carts with time-sensitive inventory, emit a finding.

**Push / browser notification prompt**
If a web-push consent prompt fires during the checkout session (visible in the DOM or screenshots),
note it as an observation — late-funnel notification requests increase abandonment. Do not emit an
ethics finding; describe the friction in checkout-flows framing.

### cookie-consent banner UX

The cookie-consent-and-compliance reference covers this surface. Evaluate the banner as a
checkout-adjacent friction event, not as a compliance audit.

**Banner placement — mobile**
Utz et al. (Gold, N=82,000+ on a real ecommerce site): top-bar banners achieve 1.8% interaction
vs. bottom-bar 18.4%. Corner popup achieves near-zero interaction (Habib 2022, N=1,109, zero
interactions). Look for:
- Is the banner a bottom bar, full-screen overlay, or corner widget?
- On mobile: does the banner cover product content (buy button, price block)?
- A corner widget on mobile is a finding (functionally invisible = unresolved consent state).

**Accept/Reject visual parity (EU/UK sites)**
EDPB / CNIL (Silver): reject must equal accept in prominence. Only flag this when the engagement's
platform/market signals EU/UK audience (hreflang EU, .co.uk domain, €/£ currency, language). Look
for:
- Are Accept and Reject the same size, color weight, and tap-target size?
- Is Reject hidden behind "Manage preferences" requiring more clicks?
- If the site is EU/UK-facing and Reject requires more steps than Accept, emit PARTIAL.

**Pre-consent cookie writes**
CHI 2025 (Gold, 254,148 websites): 50%+ set cookies before consent is given. This is a compliance
and trust signal. Look for:
- In the screenshots, does a consent banner appear on first load before any interaction?
- If the baton's `capture_state` includes a pre-consent network log showing third-party writes,
  note it in your observation.
- Do not attempt to evaluate Art 5(3) scope (localStorage, fingerprinting) from screenshots alone;
  note what is visible and flag for deeper audit.

**Cognitive load — banner complexity**
Bouma-Sims et al. (Gold, N=1,359): initial options matter more than placement. Look for:
- Does the banner present more than 3 categories requiring separate decisions?
- Is the language plain ("Analytics," "Marketing") or technical (IAB purpose IDs, legal jargon)?
- A banner with 5+ toggles on first display is a finding.

### when to emit PASS findings

Emit a PASS (not silence) when:
- Guest checkout is clearly the default path with express-checkout buttons above the form
- Form field count is at or below 9 required fields with optional fields clearly labeled
- Shipping costs and estimated delivery date are displayed before the user enters checkout
- Cookie banner is a bottom bar with equal Accept/Reject and fewer than 4 consent categories
- Address autocomplete is present and triggering on the address field

PASS findings anchor the synthesizer's Priority Path Bundle narrative. A store that has done the
express-checkout, guest-checkout, and transparent-cost work correctly deserves credit for it.

### edge cases

**One-page vs. multi-step checkout**
Bronze evidence: one-page checkout converts 7.5-21.8% higher for AOV <$150; multi-step may
outperform above $150. Note the checkout structure (one-page or multi-step) in your observation
and flag if the pattern appears mismatched to apparent AOV signals. Do not emit a FAIL without
a more specific friction indicator — structure preference alone is too context-dependent.

**Payment method variety**
Baymard (Gold): 10% abandon over insufficient payment methods. If fewer than 4 payment methods
are visible at checkout (cards, PayPal, Apple Pay, Google Pay as minimum), flag as PARTIAL.
Regional payment methods (iDEAL, Bancontact, Alipay) are in scope if market signals suggest
non-US audience.

**Generational divide — biometrics**
PYMNTS/AWS (Bronze, N=3,278): 75% of Gen Z/Millennials have used biometric auth; only 16% of
Boomers have. If the store's apparent audience is older (health, home, gardening, auto parts for
classic cars), ensure traditional auth and payment forms are the primary path — don't emit a
finding about missing express-checkout without noting the demographic context.

**EU ePrivacy / cart recovery audience constraint**
If the page is EU/UK-facing and the DOM shows an email-capture form on a cart page (the typical
abandoned-cart recovery trigger), note that the EU ePrivacy Directive Art 5(3) limits the
recoverable audience to visitors with both tracking consent AND email marketing consent. Describe
this as a scope constraint on cart recovery effectiveness in your notes[], not as an ethics
finding.

**BNPL at checkout**
If BNPL (Klarna, Afterpay, Affirm, Shop Pay Installments) is absent on a cart or checkout page
for a store with AOV >$100, emit a finding citing checkout-optimization.md Finding 13 (10%
abandon from insufficient payment methods). AOV signal comes from product prices visible in the
cart summary; if not visible, note uncertainty.
```

## Reference file list (rendered into template)

For substitution into `{{reference_file_list}}`:

```
- `checkout-optimization.md` — checkout friction, form field count, guest checkout, progress indicators, cart abandonment reason breakdown (Baymard Gold)
- `biometric-and-express-checkout.md` — Apple Pay / Google Pay / Shop Pay conversion lifts, passkey auth, express button placement, biometric trust signals
- `abandoned-cart-psychology.md` — in-session exit-intent, authentic vs. fabricated urgency, cart-expiry messaging, multi-channel recovery cascade overview
- `cookie-consent-and-compliance.md` — banner placement (Utz et al. Gold), Accept/Reject parity, pre-consent cookie writes, cognitive load of consent UX, CNIL enforcement precedents
```

## Cross-references

- [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) — shared template body this file parametrizes
- [`contracts/cluster-routing.md`](../cluster-routing.md) — canonical reference list source
- [`schema/cluster-emission-v1.json`](../../schema/cluster-emission-v1.json) — output shape
- [`schema/finding-v1.json`](../../schema/finding-v1.json) — per-finding shape
- [`scripts/test-specialist.py`](../../scripts/test-specialist.py) — harness that combines this file + template + per-engagement vars
