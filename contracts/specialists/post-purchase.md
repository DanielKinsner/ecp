# Post-Purchase Specialist (v2)

Per-cluster parameter file for the **post-purchase** specialist. Combined with the shared template body in [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) and per-engagement variables (cluster-context path, baton path, screenshots), this file produces the final dispatch prompt.

The post-purchase cluster audits the order confirmation page and any surface on non-confirmation pages that carries post-purchase signals: loyalty-program teasers, referral CTAs, account-creation prompts, points-earned displays, and buyer's-remorse mitigation elements.

## Parameters

```yaml
cluster: post-purchase
references:
  - post-purchase-psychology
  - order-confirmation
  - buyers-remorse
  - loyalty-programs
  - referral-programs
surface_vocabulary:
  - order-confirmation-block
  - delivery-date-display
  - tracking-info-block
  - support-contact-block
  - return-policy-snippet
  - upsell-cta
  - referral-cta
  - account-creation-prompt
  - loyalty-points-display
  - post-purchase-content-block
target_finding_count: 2-5
```

The 5 reference files are sourced from [`contracts/cluster-routing.md`](../cluster-routing.md) "The 10 clusters" table for the post-purchase row. All 5 live at `${CLAUDE_PLUGIN_ROOT}/references/<file>.md`.

## Cluster guidance

The block below renders into the template at the `{{cluster_guidance}}` slot. It surfaces patterns the specialist should bias toward and edge cases the template body does not cover.

```
## Cluster guidance — post-purchase

Post-purchase findings are strongest when they name specific page elements and observable patterns against the frameworks below. Bias toward these:

### order confirmation page — reassurance hierarchy

The primary surface for this cluster. The research-backed priority order for confirmation page content (order-confirmation.md F9, Silver) is:

1. Large "Order Confirmed" visual indicator + order number
2. Specific delivery date — not a date range; "Arrives Tuesday, April 8" (not "3-5 business days")
3. Tracking mechanism — tracking link or opt-in for shipping notifications
4. Support access — visible phone, chat, or email contact
5. One reassurance element — return policy snippet, social proof ("47,000+ customers"), or decision affirmation
6. Single secondary CTA — exactly one of: upsell, referral, or account creation (not all three)
7. Continue shopping link

Audit the confirmation page in this order. If upsell or referral CTAs appear above the tracking mechanism or support contact, that is a hierarchy violation — emit a finding at HIGH severity. If three competing secondary CTAs (upsell + referral + account creation simultaneously) are all present, emit a PARTIAL or FAIL for decision-paralysis, citing order-confirmation.md F7 (priority-rule) and F9.

### confirmation page upsells

Post-checkout upsell benchmarks (order-confirmation.md F3, Silver): 3-8% acceptance across implementations; 5-15% for well-implemented, highly relevant single offers with one-click functionality. Key patterns to check:

- Single offer or multiple? Multiple competing upsells invoke choice paralysis. A single contextually relevant offer is the finding-supported pattern.
- One-click add-to-order? If the upsell requires re-entering payment information or navigating to a new checkout, that is a critical implementation failure — emit HIGH severity (order-confirmation.md F3).
- Offer priced at < 50% of original order value? Upsells exceeding that threshold may amplify buyer's remorse rather than reduce it.
- Offer relevance: is the upsell complementary to the purchased item (accessories, protection plans, consumables)? A generic bestseller upsell that has no relationship to the purchased SKU is a finding.

Note: a 7.01% single-merchant case (Laumiere Gourmet Fruits, order-confirmation.md F8, Bronze) is the best available benchmark for thank-you page cross-sells — frame as indicative, not universal.

### buyer's remorse mitigation

66% of online shoppers feel anxious after clicking "buy" (Narvar 2025, buyers-remorse.md F1 and order-confirmation.md F1, Bronze). The confirmation page is the first anxiety-reduction touchpoint. Patterns to check:

- Delivery date specificity: a date range ("3-5 business days") is anxiety-generating relative to a specific date. Flag vague ranges as MEDIUM severity.
- Return policy visibility: the return policy framing should be reassuring, not buried ("Easy 60-day returns, no questions asked" vs. a footer footnote). Generous return windows reduce return rates through the endowment effect (buyers-remorse.md F4 / Wang 2009, Bronze; Janakiraman et al. 2016, Journal of Retailing, indirectly Gold-tier).
- Support contact visibility: a phone number or chat link on the confirmation page provides reassurance even if never used — its presence reduces anxiety (buyers-remorse.md F10, Bronze). Absence on the page with the highest post-purchase anxiety is a finding.
- Social proof on the confirmation: "You're in good company — here's what other [Product] owners say:" with specific review snippets bolsters post-purchase rationalization (buyers-remorse.md F3, Gold; Elliot & Devine 1994 peer-reviewed). Absence is findable when the page has a known anxiety surface (high-AOV, first-time buyer segment signals, or zero reassurance elements present).
- Content-as-reassurance: a "Post-Purchase Hug" content block during the shipping window — how-to guide, styling inspiration, anticipation content — reduces cognitive dissonance (buyers-remorse.md F6, Silver; Kumar et al. 2014 Psychological Science). If the confirmation page has zero content-as-reassurance elements and the product category is high-consideration (electronics, apparel, home goods), that is a findable gap.

### loyalty program display on the confirmation page

If the page carries a loyalty program (Smile.io, LoyaltyLion, Yotpo, etc.), check the points display:

- Points earned from the current order should be shown immediately on the confirmation page — this creates positive reinforcement and reduces buyer's remorse (order-confirmation.md F11, Bronze).
- Framing should use progress toward next reward: "You've earned 150 points! Only 350 more to your $10 reward." The goal gradient effect (Kivetz et al. 2006, Journal of Marketing Research, Gold — loyalty-programs.md F2) means progress-toward framing outperforms total-balance framing. Absence of a progress bar or progress framing when points are displayed is a LOW-severity finding.
- Endowed progress check: does enrollment use a welcome-bonus head-start ("You've earned 100 welcome points!") rather than starting at zero? Starting at zero leaves the endowed progress effect (Nunes & Drèze 2006, Journal of Consumer Research, Gold — loyalty-programs.md F1) unused.
- Enrollment rate benchmarks: the confirmation page produces 12-25% enrollment rate for new customers — highest of any trigger location (loyalty-programs.md F9, Bronze). If a loyalty program exists site-wide but the confirmation page shows no enrollment prompt for guest-checkout customers, emit a MEDIUM finding.

### referral program placement and copy

The 72-hour post-purchase window is when referral participation peaks (referral-programs.md F3, Bronze; Talkable data, audit-verified). Check:

- Is a referral CTA present on the confirmation page? For registered/repeat customers with no complementary upsell available, a referral prompt is the highest-leverage secondary CTA.
- Copy framing: "Give your friend $15 off. You get $15 too." (give-first framing) outperforms "Earn $15 when your friend buys" (get-first) per referral-programs.md F4 (Silver; Cialdini reciprocity mechanism). If the referral CTA uses get-first framing, emit a LOW-severity copy finding.
- Double-sided vs. single-sided: double-sided incentives show 52% vs 29% completion rate (Mention Me via GrowSurf, referral-programs.md F1, Bronze). If the program is single-sided, note it as a LOW-severity finding with the benchmark.
- Share mechanism: one-click native share sheet (navigator.share) or copy-link is the pattern; requiring manual link extraction or multi-step social auth is HIGH friction — findable at MEDIUM severity.
- Priority rule: the confirmation page should present only ONE secondary CTA (referral-programs.md / order-confirmation.md F7). If a referral CTA competes with an upsell and an account-creation prompt on the same page without clear visual priority, emit a hierarchy finding.

### guest-to-registered account creation

Guest checkout customers arriving at the confirmation page are the prime window for account creation (Baymard, order-confirmation.md F5, Silver):

- Is an account creation prompt visible for guest-checkout sessions? If absent entirely, emit MEDIUM severity — enrollment rate for new customers is 12-25% on the confirmation page (loyalty-programs.md F9).
- Friction check: does the prompt require only a password (email already captured) or ask for additional fields? Minimum-friction account creation is the pattern.
- Value framing: "Track this order and future orders in one place — save your info for faster checkout" is concrete immediate value vs. abstract "join our community" framing.
- Position: account creation should be the secondary CTA for guest-checkout customers, below the reassurance elements, not above tracking information.

### CAN-SPAM and transactional email compliance signal

When the page is an email rendering (embedded template or email screenshot) rather than a browser confirmation page, check the primary-purpose balance (order-confirmation.md F13, Gold; FTC CAN-SPAM):

- Transactional content (order summary, delivery date, tracking link) must visually dominate above the fold.
- Marketing content (upsells, referral CTAs, promotional blocks) must be clearly secondary and below the transactional content. If promotional content dominates above the transactional section, emit a compliance finding at HIGH severity citing the CAN-SPAM primary-purpose rule.

### post-purchase signals on non-confirmation pages

The cluster's primary surface is the order confirmation page, but loyalty and referral signals appear on other page types. When the page being audited is a PDP, category page, cart page, or homepage:

- Loyalty program teasers in the product area ("Earn 75 points on this purchase — join free") — findable if absent on a PDP from a brand that has an active loyalty program signaled elsewhere in the baton.
- Referral CTAs in the footer or account area — if present, audit for give-first copy framing and one-click share mechanism.
- Account-creation prompts on non-checkout pages — if present, check value framing clarity.
- "Join rewards" or "loyalty" nav items — presence is a PASS observation if well-labeled; absence when a loyalty program is active (signaled by baton metadata) is a LOW-severity finding.

If the page being audited is a non-confirmation page that has none of these signals (no loyalty teaser, no referral CTA, no account-creation prompt, and no page-type context that would warrant them — e.g., a bare PDP with no loyalty integration in the baton), emit status: skipped with skip_reason explaining which signals were absent and why the cluster has nothing to evaluate on this surface.

### PASS findings

Emit a PASS finding when the confirmation page:
- Shows a specific delivery date (not a range)
- Places tracking information above any secondary CTA
- Displays a return policy snippet in reassuring framing
- Has visible support contact (phone, chat, or email)
- Contains exactly one secondary CTA appropriate to the customer segment

A well-implemented loyalty points display (with progress framing and a progress bar) and a give-first referral CTA with one-click share are both PASS-worthy individually. The synthesizer uses PASS findings to balance the audit narrative — note what the page does correctly so the deliverable isn't uniformly critical.
```

## Reference file list (rendered into template)

For substitution into `{{reference_file_list}}`:

```
- `post-purchase-psychology.md` — overarching post-purchase anxiety, upsell timing, email sequence mechanics, 72-hour referral window
- `order-confirmation.md` — confirmation page element hierarchy, upsell benchmarks, account creation, tracking prominence, CAN-SPAM primary-purpose rule
- `buyers-remorse.md` — cognitive dissonance triggers, reassurance content frameworks, shipping black hole, return policy psychology
- `loyalty-programs.md` — endowed progress effect, goal gradient, points vs. cashback, tier loss aversion, redemption friction, enrollment placement
- `referral-programs.md` — double-sided incentives, 72-hour window, give-first copy framing, share mechanism friction, FTC disclosure requirements
```

## Cross-references

- [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) — shared template body this file parametrizes
- [`contracts/cluster-routing.md`](../cluster-routing.md) — canonical reference list source
- [`schema/cluster-emission-v1.json`](../../schema/cluster-emission-v1.json) — output shape
- [`schema/finding-v1.json`](../../schema/finding-v1.json) — per-finding shape
- [`scripts/test-specialist.py`](../../scripts/test-specialist.py) — harness that combines this file + template + per-engagement vars
