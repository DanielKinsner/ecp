# Audience Specialist (v2)

Per-cluster parameter file for the **audience** specialist. Combined with the shared template body in [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) and per-engagement variables (cluster-context path, baton path, screenshots), this file produces the final dispatch prompt.

The audience cluster audits personalization signals, cross-cultural and locale-aware presentation, and social commerce surface elements. It is one of the lower-density clusters on most pages — findings here are often PASS or `status: skipped`, and the absence of personalization on a logged-out PDP is typically not a defect.

## Parameters

```yaml
cluster: audience
references:
  - personalization-psychology
  - cross-cultural-considerations
  - social-commerce-psychology
surface_vocabulary:
  - personalization-widget
  - recently-viewed-rail
  - recommendation-block
  - locale-selector
  - currency-display
  - payment-method-badges
  - cultural-imagery
  - social-commerce-embed
  - ugc-gallery
  - live-commerce-block
target_finding_count: 1-3
```

The 3 reference files are sourced from [`contracts/cluster-routing.md`](../cluster-routing.md) "The 10 clusters" table for the audience row. All 3 live at `${CLAUDE_PLUGIN_ROOT}/references/<file>.md`. Read them all before auditing.

## Cluster guidance

The block below renders into the template at the `{{cluster_guidance}}` slot. It surfaces patterns the specialist should bias toward and edge cases the template body does not cover.

```
## Cluster guidance — audience

Audience findings are strongest when the page surfaces specific signals your three reference files cover. Bias toward these:

**Personalization signals (personalization-psychology.md)**

- "Recommended for you" / "Because you viewed" / "Your recently viewed" widgets — evaluate whether framing is social-proof-style ("Popular with customers who viewed this") vs. algorithmic-style ("Our algorithm thinks you'll like this"). Algorithmic framing carries reactance risk (Finding 10). Social-proof framing converts better and avoids the personalization paradox.
- Recently-viewed rail or persistent cart state — presence on a PDP or category page for a logged-in user is a baseline expectation; absence for a logged-in returning user is a finding (McKinsey: 76% get frustrated when personalization is absent, Finding 6).
- Personalized pricing or individualized discount codes — flag any signals that a price or discount is tailored to this visitor specifically. Personalized pricing reduces fairness perception regardless of whether the consumer benefits (Finding 7). Note it as a finding within your cluster's frame; ethics subagent surfaces the regulatory layer separately.
- Algorithmic transparency labels ("personalized by AI," "tailored for you") — these have mixed effects (Finding 12). Benefit-focused language ("Based on your recent searches") is safer than mechanism-focused language ("Our AI analyzed your behavior"). If a transparency label is present, evaluate its framing, not just its presence.
- First-party vs. surveillance signals — if a recommendation widget appears to surface browsing data the user didn't knowingly provide (cross-site retargeting, recently-viewed items from a prior anonymous session), note the data-source risk (Findings 1, 8).
- Trust seals or preference-center links adjacent to personalization elements — their presence offsets the covert-data vulnerability effect; their absence alongside heavy personalization is a finding.

**Cross-cultural signals (cross-cultural-considerations.md)**

- Currency and locale — if `page_head.hreflang[]`, visible currency markers (₹, ¥, ₩, R$, €, £, etc.), or baton metadata indicate a non-default locale, evaluate whether prices render in local currency with correct formatting. Incorrect decimal separator, missing local currency symbol, or US-style formatting on a non-US page erodes trust (Finding 10). Tax-inclusive pricing is expected in EU/Australia/Japan; tax-exclusive display in those markets feels deceptive.
- Payment method localization — if checkout or product page surfaces payment badges, check that locally dominant methods are present for the apparent market (iDEAL for Netherlands; Boleto/PIX for Brazil; Alipay/WeChat Pay for China; UPI for India; Konbini for Japan). Missing the dominant local payment method for a targeted market is a HIGH severity finding (Finding 6, directional).
- Language and RTL — if the page is in a non-Latin script or an RTL language (Arabic, Hebrew), evaluate whether full layout mirroring is present, not just text direction (Finding 9). Navigation, progress bars, and icon placement must mirror. If RTL text is detected but layout is LTR, flag as a finding.
- Trust signal conventions — for German-market pages (.de domain, DSGVO badge, Impressum present), evaluate institutional trust markers (Trusted Shops / TÜV seals) (Finding 7). For East Asian markets, evaluate whether social proof quantity (view/purchase counts) is prominently displayed (Findings 4, 8). For collectivist-market pages, review volume of community validation signals vs. individualist personalization emphasis.
- Cultural color and imagery — if the baton metadata or screenshots suggest a specific target market, flag color palette mismatches where evidence is concrete (e.g., white-dominant funeral-imagery associations in East Asian product photography, red CTA absence on a Chinese-market page where red carries positive cultural resonance) (Finding 1). Only flag this when the evidence is specific — general color observations without a market signal are not findings.
- Information density — for confirmed East Asian market pages, a sparse Western-minimalist layout is not automatically better; what East Asian shoppers want is trust and verification signals (clear return policies, security certifications, transparent pricing) within potentially dense layout (Finding 4). Do not penalize information density on East Asian pages as a UX defect unless the density prevents access to trust signals.

**Social commerce signals (social-commerce-psychology.md)**

- Instagram Shopping / TikTok Shop integration — if the page or baton metadata shows a social commerce entry point (Instagram Shopping tag, TikTok Shop badge, Pinterest buyable pin, Facebook Shop link), evaluate whether the checkout path is appropriate for the apparent target demographic. In-app checkout is optimal for Gen Z / sub-$50 impulse products; redirect to .com is better for mixed demographics or high-AOV considered purchases (Finding 6).
- Creator / influencer content embeds — if UGC galleries, creator video embeds, or influencer testimonials are present, evaluate FTC disclosure compliance: material connections must be clearly disclosed at the start of the content, not buried in hashtag clouds. A visible "#ad" or "Gifted" disclosure meets the standard; absence is a MEDIUM finding (social-commerce-psychology.md Finding 8). Note this finding in your cluster's frame; ethics subagent surfaces the regulatory layer separately.
- Social proof quantity signals — real-time purchase notifications ("X people bought this in the last 24 hours"), live view counts, or "trending now" indicators. Evaluate whether these appear to be real-data driven or fabricated. Fabricated counters that reset are an ethics-adjacent signal; describe the urgency framing neutrally and note your observation; the ethics subagent will surface the fabrication issue.
- Shop-the-look / UGC galleries — product-tagged photo galleries or shoppable video embeds are a social commerce surface. Evaluate whether social proof quality signals (authentic user-generated content, real engagement counts) are present or absent. Absence of any UGC on a fashion/beauty/hedonic product page where competitors commonly use it is a LOW finding (Finding 4).
- Live commerce elements — if a livestream embed, countdown to live event, or "watch replay" block is present, evaluate herd-effect signals: real-time viewer counts, live purchase activity, and urgency framing (Finding 5). For Western-market pages, note that live commerce herd-effect strength is uncertain — applicability is directional.
- Social-capture flows (DM for link, comment to enter) — if a page or embedded widget invites social actions that trigger a marketing list enrollment, note compliance risk: DM/comment engagement does not constitute SMS consent under TCPA (Finding 10). Flag as a MEDIUM finding if the flow exists without an explicit consent checkpoint.

Edge cases:

- **Logged-out PDP with no personalization.** The absence of personalization on a logged-out product detail page is a deliberate stance, not a defect. 90-98% of e-commerce traffic is anonymous (personalization-psychology.md Finding 9). Only flag absent personalization on a logged-out page if the brand context strongly suggests personalization should be present (e.g., a page that is part of a logged-in account flow per the baton's `capture_state.auth_state` field, or a brand whose core value proposition is personalization and the page has zero signals of it even at the segment level).
- **Returning logged-in visitor with no recognition signals.** If the baton's `capture_state.auth_state` is "logged-in" and the page shows no recognition signal at all (no greeting, no recently-viewed, no personalized recommendations), that is a MEDIUM finding (McKinsey 61% of consumers feel treated as a number, Finding 11).
- **Single-market domestic page with no locale signals.** If the page is a domestic US page with no visible international signals, the cross-cultural reference file contributes little. Do not force findings for absent localization on a page that is not serving international traffic. Emit a PASS noting the page's domestic scope if sections were routed to you.
- **Social commerce embeds on a page not targeting social-native audiences.** A B2B industrial parts page with no social commerce signals is not missing anything. Don't emit a finding for absent TikTok Shop integration on a product that has no social commerce fit.
- **Personalization signals present but light.** Category-level personalization ("More in this category") is a lower-risk, lower-benefit form than item-level. Note it as observed-as-deliberate (consistent with Finding 3's timing decay argument) rather than penalizing it as insufficient.

When emitting PASS findings: a clean audience setup on a page with full localization, appropriate social-proof framing (not algorithmic framing), correctly formatted local currency, and no reactance-risk personalization elements is worth documenting explicitly. The synthesizer's Priority Path Bundle mode uses PASS findings to balance the deliverable narrative. A typical domestic logged-out PDP may emit a PASS finding noting that the page correctly uses segment-level or social-proof-framed recommendations without exposing covert tracking signals.
```

## Reference file list (rendered into template)

For substitution into `{{reference_file_list}}`:

```
- `personalization-psychology.md` — personalization paradox, creepiness threshold, first-party vs. third-party data, recommendation framing, timing decay, regulatory constraints (CCPA ADMT, GDPR Art. 22, EU AI Act)
- `cross-cultural-considerations.md` — Hofstede dimensions, color symbolism, RTL layout, local currency formatting, payment method localization, trust signal conventions by market, GDPR/LGPD/PIPL/APPI legal constraints
- `social-commerce-psychology.md` — trust transfer mechanics, impulse buying drivers, TikTok Shop / Instagram Shopping dynamics, creator partnership FTC disclosure, herd-effect live commerce, social-capture consent flows (CAN-SPAM, TCPA)
```

## Cross-references

- [`contracts/specialist-prompt-v2.md`](../specialist-prompt-v2.md) — shared template body this file parametrizes
- [`contracts/cluster-routing.md`](../cluster-routing.md) — canonical reference list source
- [`schema/cluster-emission-v1.json`](../../schema/cluster-emission-v1.json) — output shape
- [`schema/finding-v1.json`](../../schema/finding-v1.json) — per-finding shape
- [`scripts/test-specialist.py`](../../scripts/test-specialist.py) — harness that combines this file + template + per-engagement vars
