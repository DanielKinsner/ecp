<!-- RESEARCH_DATE: 2026-03-17 -->
# Cookie Consent Banners: UX, Compliance, and Conversion Impact

**Research Date:** 2026-03-17
**Domain:** Cookie consent banner design, GDPR/ePrivacy compliance, consent rate optimization, and mobile consent UX
**Total Findings:** 12 cited findings with specific data points (9 original + 3 added 2026-04-22)

## Executive Summary

Cookie consent is the strongest evidence base in the mobile CRO expansion — multiple large-N peer-reviewed field experiments exist, including one conducted on a real ecommerce website. The research converges on several actionable conclusions:

### Top 3 Most Impactful Findings

1. **Banner design swings consent rates by 17-23 percentage points.** Choice architecture (what options are shown, how they're presented) has massive, experimentally-verified effects on consent rates. Utz et al. (2019) demonstrated this across 82,000+ users on a real ecommerce site.
2. **Only 12-15% of cookie banners are compliant.** Two independent studies (Nouwens 2020, CHI 2025) found the vast majority of consent implementations fail basic legal requirements. 38% of "compliant" banners still use dark patterns.
3. **Cookie consent is a cognitive load event before shopping begins.** Every visitor must make a decision about an unfamiliar legal concept before they can engage with your products. Minimizing this friction is a conversion imperative, not just a compliance exercise.

### Key Context

- **No ecommerce-specific conversion RCT exists** measuring the causal effect of specific banner layouts on purchase conversion (add-to-cart, checkout completion). All evidence measures consent rates, interaction rates, or bounce — not downstream purchase behavior.
- **Geographic scope matters.** GDPR/ePrivacy requirements (EU/UK) differ from US markets. Findings 3, 5, and 6 are EU/UK-specific. US-only sites face different (weaker) consent requirements.
- **Utz et al. (2019) is the single most directly applicable study** — conducted on a real German ecommerce website with 82,000+ users. This is undersold in most literature reviews.

### 2025–2026 Enforcement Landscape

The regulatory enforcement environment for cookie consent has materially escalated since 2024:

- **CNIL v. Google — €325M (September 1, 2025)**: The largest single CNIL cookie fine to date. Google was fined for (a) placing advertising cookies when users created a Google account without valid consent, and (b) inserting advertisements between Gmail users' emails without consent. Split: €200M (Google LLC) + €125M (Google Ireland). CNIL cited recidivism — prior fines of €100M (2020) and €150M (2021) — as an aggravating factor. This makes recidivism a formal sanctioning criterion for repeat violations. Source: https://www.cnil.fr/en/cookies-and-advertisements-inserted-between-emails-google-fined-325-million-euros-cnil
- **CNIL v. Shein — €150M (September 2025)**: The first nine-figure CNIL cookie fine against a pure-play ecommerce operator. Directly precedential for DTC/Shopify stores. See Finding 10 below for full treatment.
- **Washington MHMDA** (RCW 19.373, effective March 31, 2024): Health data inference is now subject to consent-before-processing in Washington state. See Finding 9 boundary conditions.
- **2026 state privacy laws** (Indiana, Kentucky, Rhode Island): Additional US states have enacted comprehensive privacy laws effective 2026, adding to the CCPA/CPRA + Virginia + Colorado + Connecticut landscape. US-only stores are not exempt from consent requirements — California CCPA/CPRA currently applies to large enough US operators.

**Practitioner posture**: Cookie non-compliance is no longer a theoretical risk. The Shein €150M fine establishes the realistic exposure floor for ecommerce operators with systemic cookie violations — it is not a ceiling. Cross-reference: ethics-gate.md Parts 7.2 and 7.6.

---

## Findings

### Finding 1: Banner Choice Architecture Swings Consent Rates by 17-23 Percentage Points

- **Source**: (a) Utz et al., 2019, ACM CCS (N=82,000+) https://dl.acm.org/; (b) Nouwens et al., 2020, ACM CHI (N=680 scraped + N=40 experiment) https://dl.acm.org/; (c) Bauer et al., 2021, Computers in Human Behavior (N=1,493) https://www.sciencedirect.com/journal/computers-in-human-behavior
- **Methodology**: (a) Three field experiments on a German ecommerce website, 82,000+ real users. Binary-choice notices on mobile achieved 55% interaction rate. Nudging effects were large. (b) Scraped 680 UK websites for compliance + controlled experiment with 40 participants testing option manipulation. (c) Field trial on a real website, N=1,493, manipulating banner design elements.
- **Key Finding**: Banner design choices have massive, experimentally-verified effects on consent. (b) Nouwens: removing the opt-out button increased consent by **+22-23 percentage points**; adding granular controls decreased consent by **-8-20pp**. (c) Bauer: banner manipulations increased consent by **17pp**. (a) Utz: nudging had large effects across all conditions. The magnitude of these effects (17-23pp) is among the largest experimentally-demonstrated UX effects in the entire CRO literature.
- **E-Commerce Application**: The options you present and how you present them determine consent rates more than any other factor. For compliant banners: present Accept and Reject as equal options (required by law in EU/UK), but use clear visual design to make the choice easy and fast. Minimize the cognitive burden of the decision.
- **Replication Status**: Three independent peer-reviewed studies converge (2019 ACM CCS, 2020 ACM CHI, 2021 CHB). Utz 2019 is the strongest — conducted on a real ecommerce site with 82,000+ users. This is one of the most well-replicated findings in the entire CRO domain.
- **Boundary Conditions**: All studies are EU/GDPR context. US markets have different (weaker) consent requirements — the magnitude of design effects may differ where "accept or leave" is the only option. Utz's ecommerce site was German — cultural attitudes toward privacy may moderate effects.
- **Evidence Tier**: Gold
- **Quality Flag**: Primary source (ACM CCS) is a top-tier peer-reviewed computer science venue; evidence quality substantially exceeds Bronze norm

### Finding 2: Banner Placement — Bottom Bars Are the Only Viable Mobile Format

- **Source**: (a) Utz et al., 2019, ACM CCS (N=14,135 for placement comparison) https://dl.acm.org/; (b) Habib et al., 2022, ACM CHI (N=1,109) https://dl.acm.org/; (c) Cookie-Script, 2024, vendor benchmark https://cookie-script.com/
- **Methodology**: (a) Utz: field experiment comparing banner positions. (b) Habib: controlled experiment examining user interaction with cookie preference interfaces. (c) Cookie-Script: platform analytics across deployed banners.
- **Key Finding**: Placement dramatically affects interaction rates. Utz: **top bar: 1.8% acceptance** vs **bottom-left corner: 18.4%** — a **10x difference**. Habib: **ZERO out of 1,109 participants interacted** with a small corner cookie preferences button. Cookie-Script vendor data: bottom bars achieve **76.26% acceptance**, full-screen overlays **70.8%**, bottom-right corner on mobile **3.4%**. **Important distinction**: Utz measures interaction (which includes rejections); Cookie-Script measures acceptance rate. These are different outcomes — higher "interaction" does not guarantee higher tracking consent.
- **E-Commerce Application**: Bottom bars are the only viable format for mobile cookie consent. Corner popups are functionally invisible on mobile. Full-screen overlays force engagement but may increase bounce. Do not use small corner buttons for cookie preferences — they will be ignored entirely.
- **Replication Status**: Utz and Habib are peer-reviewed at top venues (ACM CCS, ACM CHI). Cookie-Script is vendor data. The directional finding (bottom > corner) is robust across all sources.
- **Boundary Conditions**: Cookie-Script acceptance rates reflect their specific client base. Full-screen overlays force a decision (lower bounce, higher rejection rates) — the optimal format depends on whether you prioritize consent rate or user experience.
- **Evidence Tier**: Gold
- **Quality Flag**: Primary source (ACM CCS, N=14,135) is top-tier peer-reviewed; evidence quality substantially exceeds Bronze norm

### Finding 3: Regulatory Landscape — Reject Must Equal Accept (EU/UK Only)

- **Source**: (a) EDPB Cookie Banner Taskforce Report, 2023 https://www.edpb.europa.eu/; (b) UK ICO, 2023 https://ico.org.uk/; (c) CNIL, 2020-2022 enforcement records https://www.cnil.fr/en
- **Methodology**: (a) EDPB: regulatory guidance from the "vast majority" of EU data protection authorities. (b) ICO: UK regulator guidance + enforcement letters to 53 of top 100 UK websites. (c) CNIL: enforcement actions with published decisions.
- **Key Finding**: EU and UK regulators require the reject option to be **equally prominent and accessible** as the accept option. Consent is not "freely given" if rejecting requires more clicks, smaller text, or is visually de-emphasized. CNIL imposed **8 sanctions totaling €421 million** for cookie violations between 2020-2022. EDPB's taskforce report states the "vast majority" of authorities consider an absent reject button an infringement. **2025 update**: CNIL imposed an additional **€325 million** fine on Google (September 1, 2025) for placing advertising cookies during account creation without valid consent and inserting ads in Gmail without consent (split: €200M Google LLC + €125M Google Ireland). This brings the CNIL's total cookie enforcement to well over €746 million since 2020.
- **E-Commerce Application**: For sites serving EU/UK users: Accept and Reject buttons must be the same size, same visual weight, same number of clicks to reach. Do not hide Reject behind "Manage preferences." Do not use color to make Accept more prominent than Reject. The regulatory risk is real and actively enforced. For US-only sites: these requirements do not apply, but providing clear consent options builds trust regardless of jurisdiction.
- **Replication Status**: Regulatory/legal documents — factual, not experimental. EU/UK-specific jurisdiction. Enforcement is documented and ongoing.
- **Boundary Conditions**: This is EU/UK law, not universal. US markets (except California CCPA/CPRA) have minimal cookie consent requirements. The legal landscape is evolving — regulations may tighten in additional jurisdictions.
- **Evidence Tier**: Silver (primary regulator documents — EDPB taskforce report, CNIL published decisions, ICO guidance — clear the Silver bar; "not experimental" does not mean Bronze when primary regulators are the source)

### Finding 4: Expect ~25% Full Consent — Design Consent as a Micro-Conversion

- **Source**: (a) Advance Metrics, 2023 (N=1,200,000+) https://advmetrics.co/; (b) etracker, 2022-2024 https://www.etracker.com/en/; (c) Ignite.video/Consentmo, 2025, meta-analysis of 26 studies https://ignite.video/
- **Methodology**: (a) Advance Metrics: platform analytics across 1.2M+ users, measuring consent banner behavior. (b) etracker: German analytics platform tracking consent rates. (c) Ignite/Consentmo: meta-analysis aggregating 26 studies and 1.2M user interactions.
- **Key Finding**: With fully compliant banners (equal Accept/Reject), approximately **25.4% accept all cookies** (Advance Metrics), **33.6% ignore the banner entirely**, and **50-70% reject when Reject All is on equal footing** (Ignite). etracker estimates **~60% of visit data is lost** with compliant consent designs. When rejecting takes multiple clicks but accepting takes one, **up to 90% accept** — but this is a dark pattern. Approximately **37% always accept regardless, 26% always reject regardless**, and **~1/3 switch based on design** — this switchable third is where consent UX optimization has impact.
- **E-Commerce Application**: Design consent as a micro-conversion funnel. You cannot ethically manipulate consent, but you can reduce friction: (1) use clear, simple language, (2) minimize the number of categories/choices, (3) load the banner after a brief delay (not blocking first paint), (4) ensure the banner doesn't obscure product content on mobile. Accept that ~60-75% of analytics data will be incomplete in GDPR markets. Plan measurement strategy accordingly.
- **Replication Status**: Multiple vendor platforms converge on similar ranges. All are vendor-sourced (Advance Metrics, etracker, Ignite/Consentmo). The directional finding (~25% full consent, ~60% data loss) is consistent. Specific percentages vary by market and banner design.
- **Boundary Conditions**: All data is from EU/GDPR markets. US consent rates are higher because fewer sites offer equal reject options. The "switchable 1/3" insight suggests UX optimization has real but bounded impact — you cannot move the 37% who always accept or the 26% who always reject.
- **Evidence Tier**: Bronze

### Finding 5: Only 12-15% of Cookie Banners Meet Minimum GDPR Compliance

- **Source**: (a) Nouwens et al., 2020, ACM CHI (N=680 UK websites) https://dl.acm.org/; (b) CHI 2025, "A Cross-Country Analysis of GDPR Cookie Banners" (254,148 websites, 31 countries), peer-reviewed https://dl.acm.org/
- **Methodology**: (a) Nouwens: scraped and analyzed 680 UK websites for minimal GDPR compliance. (b) CHI 2025: massive cross-country audit of 254,148 websites across 31 countries using automated analysis of consent interfaces.
- **Key Finding**: (a) Nouwens found only **11.8% of UK websites met minimal EU law requirements**. (b) CHI 2025 found only **15% of 254,148 websites across 31 countries were compliant**. Additionally: **50%+ set cookies before consent was given**, and **38% of consent interfaces used dark patterns** (making accept the visual focal point even on "compliant" banners). 67% of consent interfaces use Consent Management Platforms (CMPs), but CMP use does not guarantee compliance.
- **E-Commerce Application**: Most competitors are non-compliant — this is simultaneously a risk (regulators are enforcing) and an opportunity (compliant consent UX builds trust). Use this as a competitive differentiator: a well-designed, compliant consent banner signals professionalism. Audit your own banner against EDPB requirements: equal Accept/Reject, no pre-checked categories, no cookies before consent, clear withdrawal mechanism.
- **Replication Status**: Two independent large-scale audits (Nouwens 2020 N=680, CHI 2025 N=254,148) converge on the same finding. CHI 2025 is peer-reviewed at the top HCI venue with a massive dataset. This is among the strongest evidence in the entire CRO expansion.
- **Boundary Conditions**: Both studies are EU/GDPR-focused. Compliance rates in non-GDPR markets may differ. Automated compliance checking detects structural issues but may miss contextual violations.
- **Evidence Tier**: Gold

### Finding 6: "Bright Patterns" — Highlighting the Decline Option Improves Decision Quality

- **Source**: Bielova et al., 2024, USENIX Security (N=3,947 French participants) https://www.usenix.org/conference/usenixsecurity24
- **Methodology**: Large-scale experiment testing the effect of "bright patterns" (design choices that highlight the privacy-protective option) on consent decisions, decision quality, and user satisfaction. Top-tier security venue.
- **Key Finding**: Highlighting the decline/reject option through bright pattern design (making it visually prominent rather than hidden) **substantially improved decision quality and user satisfaction** without destroying consent rates. Users made more deliberate choices and reported higher satisfaction with their decisions. This is the opposite of dark patterns — instead of manipulating toward consent, bright patterns help users make the choice that matches their actual preferences.
- **E-Commerce Application**: Consider bright pattern design as a trust-building strategy. Making the reject option genuinely easy to find and use — rather than legally compliant but practically hidden — signals transparency. For repeat-purchase businesses, the trust benefit of transparent consent may outweigh the analytics data lost from slightly lower consent rates. Satisfaction with the consent experience influences overall site perception.
- **Replication Status**: Single study at a top-tier venue (USENIX Security) with large N=3,947. No direct replication yet. French-only sample limits geographic generalizability.
- **Boundary Conditions**: French-only sample — consent attitudes vary by country. The study measures decision quality and satisfaction, not downstream purchase conversion. The trust benefit is theoretical (plausible but unmeasured in ecommerce context).
- **Evidence Tier**: Gold
- **Quality Flag**: Primary source (USENIX Security, N=3,947) is a top-tier peer-reviewed security venue; evidence quality substantially exceeds Bronze norm

### Finding 7: Initial Options Matter More Than Placement on Mobile

- **Source**: Bouma-Sims et al., 2023, ACM CHI (N=1,359, US-UK) https://dl.acm.org/
- **Methodology**: Tested 14 cookie consent interface variants examining three factors: banner prominence, location of cookie category definitions, and initial cookie options. N=1,359 participants from US and UK.
- **Key Finding**: The **initial cookie options presented** (what categories are shown, what's pre-selected) had the **largest effect on user decisions** — larger than banner placement or visual prominence. This means the content of the consent interface matters more than its position or styling. The study directly challenges the common CRO focus on banner position optimization.
- **E-Commerce Application**: Focus consent UX optimization on what options you present, not just where you put the banner. Show clear, simple categories (e.g., "Essential," "Analytics," "Marketing") rather than technical jargon. Do not pre-check non-essential categories. The fewer categories requiring decisions, the faster users move through consent and into shopping.
- **Replication Status**: Peer-reviewed at ACM CHI (top HCI venue). N=1,359 across US and UK — good geographic breadth. Single study, no direct replication.
- **Boundary Conditions**: US-UK sample may not generalize to markets with different privacy attitudes (e.g., Germany, where privacy sensitivity is higher). The study tested interface variants, not the downstream effect on shopping behavior.
- **Evidence Tier**: Gold

### Finding 8: Consent Fatigue is Increasing — Mobile Acceptance 3-10% Lower Than Desktop

- **Source**: (a) Secure Privacy, 2024, CMP platform benchmark https://secureprivacy.ai/; (b) Ignite.video/Consentmo, 2025, meta-analysis https://ignite.video/
- **Methodology**: (a) Secure Privacy: consent management platform data showing acceptance rates by device type and industry. (b) Ignite/Consentmo: meta-analysis of 26 studies across 1.2M+ interactions tracking consent behavior trends.
- **Key Finding**: Mobile cookie acceptance rates are **3-10% lower than desktop** (Secure Privacy). Consent fatigue is increasing over time — **46% of users report clicking "Accept All" less frequently than 3 years ago** (Ignite/Consentmo). The ecommerce consent rate benchmark is **45-70% acceptance** (wide range depending on banner design and market). The consent market itself has grown to **$470M** (Secure Privacy 2024), reflecting the scale of the compliance challenge.
- **E-Commerce Application**: Mobile banner design needs MORE optimization than desktop, not less — yet it typically gets less attention. The 3-10% acceptance gap means more lost tracking data on the channel with the most traffic. Optimize the mobile consent experience specifically: ensure the banner doesn't cover product content, use large touch targets for Accept/Reject, minimize the number of taps required. As consent fatigue increases, banner design quality becomes more important each year.
- **Replication Status**: Secure Privacy is a vendor (sells CMP tools). Ignite/Consentmo is also vendor-adjacent. The 46% fatigue figure could not be independently verified. The mobile-desktop gap is directionally supported by multiple platform observations.
- **Boundary Conditions**: Both sources are vendor-sourced. The specific "3-10%" range is wide enough to be credible but narrow enough to be useful. The 46% fatigue claim needs independent verification. Consent behavior is highly market-dependent — EU vs US vs other jurisdictions show very different patterns.
- **Evidence Tier**: Bronze

### Finding 9: Cookie Consent as Cognitive Load — A Decision Before Shopping Begins

- **Source**: Synthesis of cognitive load principles (Hick's Law, choice overload) applied to consent UX. Draws on Nouwens 2020, Utz 2019, and Bouma-Sims 2023. https://dl.acm.org/
- **Methodology**: Framework application — not a primary study. Applies established cognitive load research (documented in cognitive-load-management.md) to the specific context of cookie consent banners.
- **Key Finding**: A cookie consent banner is a **cognitive load event that occurs before the user has any engagement with your products**. It introduces a decision about an unfamiliar legal concept (data processing categories) at the moment of lowest user investment. Per Hick's Law, each additional option increases decision time. Per choice overload research, complex consent interfaces with many categories may cause decision paralysis. The user hasn't decided to shop yet — and the first thing they must do is make a legal decision. Every second spent on consent is a second not spent discovering products.
- **E-Commerce Application**: Minimize consent cognitive load: (1) use a maximum of 3 clear categories (Essential, Analytics, Marketing), (2) use plain language (not legal jargon), (3) delay the banner by 1-2 seconds so the page renders first (user sees products before the banner), (4) on mobile, ensure the banner consumes no more than 30-40% of viewport, (5) provide a one-tap Accept All and one-tap Reject All as the primary options, with "Customize" as a secondary action for engaged users.
- **Replication Status**: This is a framework application, not a primary finding. The underlying cognitive load principles are well-established (Hick's Law, choice overload). The specific application to consent UX is logical but not experimentally validated.
- **Boundary Conditions**: The "delay the banner" recommendation may conflict with strict GDPR interpretation (some regulators argue consent must be obtained before any processing, including page analytics). Test compliance with your legal team. The cognitive load framework assumes users process consent rationally — many users click Accept reflexively without reading. **WA MHMDA note**: Washington's My Health MY Data Act (RCW 19.373, effective March 31, 2024 for most entities; June 30, 2024 for small businesses) applies to any health-related data inference including any script reading on a health-adjacent page before consent. Stores with health, wellness, or fitness products serving Washington residents must obtain consent *before* any analytics or tracking fires — the "delay the banner by 1-2 seconds" approach is non-compliant for WA MHMDA-covered contexts. Cross-reference: ethics-gate.md Part 7.7.
- **Evidence Tier**: Bronze

---

### Finding 10: CNIL September 2025 Ecommerce Precedent — Shein €150M + Google €325M

- **Source**: (a) CNIL press release on Google €325M (Sep 1, 2025) — https://www.cnil.fr/en/cookies-and-advertisements-inserted-between-emails-google-fined-325-million-euros-cnil — VERIFIED against CNIL website. (b) CNIL enforcement cycle, Shein €150M (Sep 2025) — CNIL enforcement announcement; primary URL marked below pending final slug verification.
- **Methodology**: Primary regulator press release and enforcement record.
- **Key Finding**: On September 1, 2025, CNIL fined Google **€325 million** (€200M Google LLC + €125M Google Ireland) for: (a) placing advertising cookies on Google account creation pages without valid consent, and (b) displaying advertisements between Gmail users' emails without consent. CNIL explicitly cited recidivism (prior 2020 and 2021 fines) as an aggravating factor. In the same enforcement cycle, CNIL fined Shein **€150 million** — the first nine-figure CNIL cookie penalty against a pure-play ecommerce operator. Aggravating factors for recidivists, first-of-kind fines for pure-play ecommerce: these two fines together reset the baseline for what "material compliance exposure" means for EU-facing merchants.
- **E-Commerce Application**: For any EU-facing DTC store, treat Shein €150M as the realistic floor of regulatory exposure for systemic cookie non-compliance — not the ceiling. Audit the full cookie layer, not just the banner: (i) Do any marketing/analytics cookies drop before Accept? (ii) Is Reject the same number of clicks as Accept? (iii) Is consent re-collected after material banner design changes? (iv) Is per-user consent record auditable on request? Non-compliance with any of (i)–(iv) is the specific pattern CNIL has penalized in 2025.
- **Replication Status**: Primary regulator decision. Independently verifiable via CNIL.fr for the Google fine. Shein URL pending final verification (see Deferred).
- **Boundary Conditions**: EU/GDPR jurisdiction only. US-only stores are not directly exposed to CNIL enforcement (though CCPA/state privacy law exposure remains separate). The recidivism-as-aggravator principle applies across all CNIL enforcement — any prior finding or warning is now a formal factor in penalty calculation.
- **Evidence Tier**: Gold (primary CNIL press release for Google €325M; conditional on Shein URL verification for Shein €150M)
- **Cross-reference**: ethics-gate.md Parts 7.2 and 7.6

---

### Finding 11: TCF v2.2 and the Legitimate-Interest Dark-Pattern Crackdown

- **Source**: (a) Belgian DPA (APD/GBA) decision, February 2, 2022, on IAB Europe TCF, https://www.dataprotectionauthority.be/citizen/iab-europe-held-responsible-for-a-mechanism-that-infringes-the-gdpr; (b) IAB Europe Transparency and Consent Framework v2.2 launch/specification materials (May 2023), https://iabeurope.eu/tcf-2-2-launches-all-you-need-to-know/; (c) CNIL 2024 cookie-banner enforcement guidance, https://www.cnil.fr/fr/bannieres-cookies-trompeuses-la-cnil-met-en-demeure-des-editeurs-de-sites-web.
- **Methodology**: Primary DPA decision + industry framework specification + national regulator guidance.
- **Key Finding**: The Belgian DPA ruled in February 2022 that IAB Europe's TCF itself violated GDPR — the TC String was held to be personal data processed without valid legal basis. TCF v2.2 (released May 2023) responded by restricting "legitimate interest" as a legal basis for advertising cookies; consent is now the only viable legal basis for ad-targeting purposes under the framework. **Practical consequence**: Ecommerce operators running any IAB-TCF-based Consent Management Platform (OneTrust, Didomi, Cookiebot, Osano, Usercentrics, etc.) must verify: (a) the deployed CMP is on TCF v2.2, not v1.1 or v2.1; (b) the default purpose-table state presents "Legitimate Interest" ad-targeting purposes as opt-in rather than opt-out; (c) no ad-targeting purpose defaults to "on" under legitimate interest.
- **E-Commerce Application**: During your next consent audit: (1) Confirm your CMP vendor version — ask your CMP provider which TCF version they are registered for (check IAB Europe's CMP list at https://iabeurope.eu/cmp-list/); (2) Review your purpose table defaults; (3) If any purpose defaults to "on" under Legitimate Interest for advertising or measurement, reconfigure to "off" (opt-in) before the next regulator sweep; (4) For stores running third-party advertising (Meta Pixel, Google Ads, etc.), confirm the ad platform is receiving only consented signals — verify via platform consent-mode audit tools.
- **Replication Status**: Primary DPA decision (Belgian APD) + industry framework (IAB Europe TCF v2.2). Both primary sources.
- **Boundary Conditions**: TCF v2.2 requirement applies to all operators using IAB-TCF-compliant CMPs. Non-IAB CMPs are not directly subject to TCF, but must still meet GDPR consent requirements. The Belgian DPA ruling applies directly to IAB Europe; its implications for CMP operators are via regulatory risk, not direct liability (unless the CMP is passing TC Strings as personal data on the operator's behalf).
- **Evidence Tier**: Silver (primary DPA decision + industry framework; practitioner implementation guidance layer)

---

### Finding 12: ePrivacy Directive Art 5(3) — Statutory Scope Covers Any Client-Side Storage

- **Source**: Directive 2002/58/EC as amended by 2009/136/EC, Article 5(3). eur-lex CELEX 32002L0058 — https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32002L0058 — VERIFIED against eur-lex live text.
- **Methodology**: EU primary law — verbatim statutory text.
- **Key Finding**: The verbatim statutory trigger in Art 5(3) is: *"the storing of information, or the gaining of access to information already stored, in the terminal equipment of a subscriber or user."* This means Art 5(3) applies to **any** client-side storage or read — not only HTTP cookies. Covered: localStorage, sessionStorage, IndexedDB, browser fingerprinting, pixel reads, SDK identifiers, canvas fingerprinting, WebGL fingerprinting, AudioContext fingerprinting, font enumeration. **This is a widespread compliance gap**: many ecommerce CMP implementations gate HTTP cookies but leave localStorage writes and fingerprinting scripts running pre-consent. The statutory text does not limit the trigger to cookies — the phrase "storing of information" covers all client-side writes; "gaining of access to information already stored" covers all client-side reads including fingerprinting (which reads device characteristics without writing persistent storage).
- **E-Commerce Application**: When auditing the pre-consent state, open browser devtools → Application → Storage. Inspect: (a) **Local Storage** — any third-party key present before Accept is an Art 5(3) trigger; (b) **Session Storage** — same; (c) **Cookie jar** — well-known, but check; (d) **Network tab** — filter for any third-party domain making a request before consent fires; any response that sets a device identifier is an Art 5(3) trigger. Baseline audit scope must include all client-side storage and any script making identifier-grade reads. Ask your analytics and advertising vendors for their pre-consent behavior documentation — most have this; if they cannot provide it, assume they are writing before consent.
- **Replication Status**: EU primary statutory text — not experimental. Independently verifiable at eur-lex.europa.eu. Regulatory enforcement aligns with this interpretation (CNIL's post-consent-click audit process checks localStorage and fingerprinting, not only cookies).
- **Boundary Conditions**: EU/EEA and UK (UK PECR) jurisdiction. US has no equivalent federal statute (California CCPA does not have an equivalent client-side-storage consent trigger). The statutory text is clear; national transposition and supervisory authority interpretation are what create variation — CNIL, ICO, and EDPB all align on the broad reading.
- **Evidence Tier**: Gold (EU primary statutory text, eur-lex verified)
- **Cross-reference**: ethics-gate.md Part 7.2

---

## Research Gaps

All sources and all 4 verification audits independently identify the same gaps:
1. **No study directly measures causal effect of specific banner layouts on mobile ecommerce conversion** (add-to-cart, checkout completion) — only consent rates and interaction rates
2. **Mobile-specific banner format comparisons** are almost absent from academic literature
3. **Long-term effects of consent fatigue** on brand trust and repeat purchase are unstudied
4. **Whether cookie-rejecting users have inherently different purchase intent** is unknown — if rejectors are lower-intent regardless, the analytics data loss may overstate the business impact
5. **Post-rejection cookie behavior**: 43% of websites may still set tracking cookies after users click Reject (Ignite.video technical audit, 2025) — compliance extends beyond banner design to actual cookie behavior

---

## Key Sources

1. Utz et al. (2019). "(Un)informed Consent." ACM CCS. N=82,000+.
2. Nouwens et al. (2020). "Dark Patterns after the GDPR." ACM CHI.
3. Bauer et al. (2021). "Are you sure, you want a cookie?" Computers in Human Behavior. N=1,493.
4. Habib et al. (2022). "Okay, whatever." ACM CHI. N=1,109.
5. Bouma-Sims et al. (2023). "A US-UK Usability Evaluation of Consent Management Platform Cookie Consent Interface Design." ACM CHI. N=1,359.
6. Bielova et al. (2024). "The Effect of Design Patterns on Cookie Consent Decisions." USENIX Security. N=3,947.
7. CHI 2025. "A Cross-Country Analysis of GDPR Cookie Banners." 254,148 websites, 31 countries.
8. EDPB Cookie Banner Taskforce Report (2023).
9. UK ICO Cookie Banner Guidance (2023).
10. CNIL Enforcement Records (2020-2025). Including CNIL v. Google €325M (Sep 1, 2025): https://www.cnil.fr/en/cookies-and-advertisements-inserted-between-emails-google-fined-325-million-euros-cnil
11. CNIL v. Shein €150M (Sep 2025). https://www.cnil.fr/en/cookie-regulation-cnil-continuing-action-plan-initiated-2019-and-has-imposed-two-fines-shein-and (verified 2026-04-22)
12. Belgian DPA (APD/GBA) decision on IAB Europe TCF (February 2, 2022).
13. IAB Europe Transparency and Consent Framework v2.2 (May 2023). https://iabeurope.eu/cmp-list/
14. ePrivacy Directive 2002/58/EC Art 5(3). https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32002L0058
15. Washington My Health MY Data Act, RCW 19.373 (effective March 31, 2024).
16. Advance Metrics (2023). Cookie Behaviour Study. N=1,200,000+.
17. Secure Privacy (2024). Consent Conversion Rate Optimization Guide.
