<!-- RESEARCH_DATE: 2026-04-22 -->
# AI Media Disclosure Framework

**Research Date:** 2026-04-22
**Total Findings:** 4
**Methodology:** Synthesis of primary regulatory sources (US FTC enforcement actions, EU AI Act text), technical standards (C2PA Content Credentials), and cross-reference consolidation from color-accuracy.md F13, video-integration.md F15, and video-optimization.md F12. This file is the canonical reference for AI-generated media disclosure obligations across image, video, and emerging modalities.

> **Cross-Reference:** This file consolidates AI-media-disclosure content previously duplicated across `color-accuracy.md` (F13 — AI image enhancement), `video-integration.md` (F15 — AI video legal exposure), and `video-optimization.md` (F12 — AI video technical implementation). Those findings remain in their source files with distinct application framing; this file provides the unified regulatory and technical framework. See also `ethics-gate.md` PART 5.3 (AI disclosure doctrine).

---

## Summary

### Top 3 Most Impactful Findings

1. **FTC Operation AI Comply established AI-assisted misrepresentation as an active enforcement priority** (Finding 1) — September 2024 sweep targeted five operators using AI to generate deceptive content. AI enhancement is not a safe harbor for product misrepresentation under Section 5.

2. **EU AI Act Article 50 requires machine-readable labeling of synthetic media by August 2, 2026** (Finding 2) — Deployers (merchants) must disclose AI-generated content to end users; providers must ensure outputs are machine-detectable. Dual obligation creates both technical and UX requirements.

3. **C2PA Content Credentials provide the leading technical standard for provenance metadata** (Finding 3) — Cryptographically signed metadata attached to media files describing AI generation. Supported by Adobe, Microsoft, OpenAI, and Google. Practical implementation path for EU AI Act Article 50 compliance.

---

## Findings

### Finding 1: FTC Operation AI Comply — AI-Assisted Misrepresentation Is an Active Enforcement Priority
- **Source**: US Federal Trade Commission. "FTC Announces Crackdown on Deceptive AI Claims and Schemes" (September 25, 2024). https://www.ftc.gov/news-events/news/press-releases/2024/09/ftc-announces-crackdown-deceptive-ai-claims-schemes. FTC Business Blog. "Operation AI Comply: continuing the crackdown on overpromises and AI-related lies." https://www.ftc.gov/business-guidance/blog/2024/09/operation-ai-comply-continuing-crackdown-overpromises-ai-related-lies.
- **Methodology**: Primary regulatory enforcement source — FTC press release and blog post documenting enforcement actions.
- **Key Finding**: FTC filed 5 enforcement actions in September 2024 against operations using AI to generate deceptive content. Section 5 prohibits "unfair or deceptive acts or practices" under the reasonable-consumer standard. AI enhancement that materially misrepresents a product's appearance, function, or capabilities is squarely within scope. The enforcement sweep established that AI-assisted misrepresentation is not a safe harbor — the medium of deception (AI vs. manual) does not affect liability.
- **E-Commerce Application**: Any AI enhancement applied to product media (images or video) that changes the product's appearance beyond what the physical product delivers creates FTC Section 5 exposure. Key thresholds: (1) AI background removal — generally acceptable (does not alter product appearance); (2) AI color correction — apply ΔE₀₀ ≤ 3 gate (see `color-accuracy.md` F12); (3) AI upscaling — acceptable if not introducing false texture detail; (4) AI generative fill, virtual photography, or AI-generated demonstration video — treat as AI-generated content requiring disclosure.
- **Replication Status**: Primary regulatory document. FTC Operation AI Comply press release dated September 25, 2024.
- **Boundary Conditions**: FTC Section 5 applies to US commerce. The materiality test requires the representation to affect purchasing decisions — minor technical correction within color-accuracy ΔE bounds is not materially deceptive. Decorative imagery (backgrounds, lifestyle scenes) that does not represent the product itself is likely outside scope (see `ethics-gate.md` PART 5.3 for the decorative/product distinction).
- **Evidence Tier**: Gold (primary FTC enforcement press release)

---

### Finding 2: EU AI Act Article 50 — Synthetic Media Labeling Obligation (Effective August 2, 2026)
- **Source**: EU AI Act, Article 50: Transparency Obligations for Providers and Deployers of Certain AI Systems. https://artificialintelligenceact.eu/article/50/. Regulation (EU) 2024/1689.
- **Methodology**: Primary regulatory source — final text of EU regulation.
- **Key Finding**: Article 50 creates dual obligations: (1) **Providers** of AI systems that generate synthetic media must ensure outputs are marked in a machine-readable format and detectable as AI-generated. (2) **Deployers** (merchants using AI-generated media) must disclose deepfakes and synthetic content to end users. For ecommerce: merchants marketing into the EU with AI-generated product images or video will need both technical labeling (machine-readable metadata) and consumer-facing disclosure (visible text/badge). Enforcement begins August 2, 2026.
- **E-Commerce Application**: For EU-facing merchants using AI-generated product media: (1) Implement consumer-facing disclosure — text overlay, badge, or adjacent disclosure ("This image/video includes AI-generated content"). (2) Implement machine-readable labeling — C2PA content credentials (see Finding 3) or equivalent provenance metadata. (3) Verify that CDN re-encoding preserves provenance metadata — some re-encoders strip C2PA data. (4) Audit your media pipeline to identify which assets are AI-generated or AI-modified.
- **Replication Status**: Primary regulatory text. EU AI Act is final (Regulation 2024/1689).
- **Boundary Conditions**: Applies to EU-facing providers and deployers. Non-EU US merchants with no EU customer base are primarily under FTC scope (Finding 1). Penalties for Article 50 breaches can reach €15M or 3% of global annual turnover. The "synthetic media" scope covers AI-generated images, video, and audio — not traditional photo editing (cropping, exposure correction, white balance).
- **Evidence Tier**: Gold (primary EU regulation text)

---

### Finding 3: C2PA Content Credentials — Technical Standard for AI Provenance Metadata
- **Source**: Coalition for Content Provenance and Authenticity (C2PA). Technical Specification v1.3. https://c2pa.org/specifications/. C2PA membership includes Adobe, Microsoft, OpenAI, Google, BBC, Intel, and others.
- **Methodology**: Industry technical standard — open specification for cryptographic content provenance.
- **Key Finding**: C2PA provides cryptographically signed metadata attached to media files that describes: (1) whether the content was AI-generated, AI-modified, or captured by a device; (2) the provenance chain (what tools created or modified the content); (3) tamper-evident signatures that detect post-hoc modification. C2PA is the leading (but not the only) technical path to satisfying EU AI Act Article 50's machine-readable labeling requirement. Major AI generation tools (Adobe Firefly, OpenAI DALL-E, Google Imagen) support C2PA output natively as of 2024–2025.
- **E-Commerce Application**: (1) When using AI to generate or modify product images/video, export with C2PA provenance metadata enabled. (2) Verify your CDN and image optimization pipeline preserves C2PA data — test with the Content Authenticity Initiative's Verify tool (https://contentauthenticity.org/verify). (3) For video: confirm that transcoding/re-encoding preserves C2PA manifests. (4) C2PA is not yet required by US law but is the clearest technical path to EU AI Act compliance and proactive FTC good faith.
- **Replication Status**: C2PA v1.3 is the current published specification. Adoption is growing but not yet universal across all media tools.
- **Boundary Conditions**: C2PA metadata can be stripped by tools that don't support it. Not all social media platforms or CDNs preserve C2PA data. The standard covers provenance, not content moderation — it proves what created the content but does not judge whether the content is deceptive.
- **Evidence Tier**: Gold (published technical standard from major industry coalition)

---

### Finding 4: Disclosure Best Practices — Consumer-Facing Implementation
- **Source**: Synthesis of FTC disclosure guidance (FTC Endorsement Guides, 16 CFR Part 255, revised November 2023) https://www.ftc.gov/business-guidance/resources/ftcs-endorsement-guides-what-people-are-asking, EU AI Act Article 50 deployer obligations https://artificialintelligenceact.eu/article/50/, and C2PA implementation guidance https://c2pa.org/. Cross-reference: `ethics-gate.md` PART 5.3.
- **Methodology**: Regulatory guidance synthesis + practitioner consensus on AI disclosure UX.
- **Key Finding**: Effective AI-media disclosure requires three layers: (1) **Machine-readable**: C2PA or equivalent metadata (satisfies EU AI Act Article 50 provider obligation). (2) **Visible on-content**: Text overlay, corner badge, or watermark on the media itself (e.g., "AI-generated content") — survives screenshot/share. (3) **Page-level contextual**: Text adjacent to the media element on the product page explaining AI involvement. The FTC's general disclosure standard (must be "clear and conspicuous") applies — buried disclosures in footnotes or terms pages do not satisfy the reasonable-consumer test.
- **E-Commerce Application**: Recommended implementation: (a) Apply C2PA provenance metadata at media export. (b) Add a persistent corner badge or text overlay on AI-generated media ("AI-generated" or "AI-enhanced"). (c) Add page-level disclosure text adjacent to the media player/image ("This [image/video] was created using AI"). (d) Do NOT hide disclosure behind click-to-expand, tooltips, or separate pages. (e) For product images with AI color correction within ΔE₀₀ ≤ 3: disclosure is not required (not materially deceptive) but C2PA metadata is recommended as a proactive measure.
- **Replication Status**: Regulatory guidance — not empirical finding. FTC disclosure standards are well-established across endorsement, advertising, and native advertising contexts.
- **Boundary Conditions**: Disclosure requirements will evolve as regulators issue specific AI-media guidance. The current framework is synthesized from existing FTC disclosure principles and EU AI Act text — specific AI-media disclosure regulations may impose additional requirements post-2026.
- **Evidence Tier**: Gold for regulatory sources (FTC, EU AI Act); Silver for implementation best practices (practitioner consensus, no controlled study on optimal disclosure format for AI media)

---

## Methodological Notes

1. This file consolidates AI-media-disclosure content that was independently developed in three reference files during Sprint 3. The source files retain their findings with application-specific framing (color-accuracy for images, video-integration/video-optimization for video). This file provides the unified regulatory and technical framework.

2. The regulatory landscape is actively evolving. EU AI Act Article 50 enforcement begins August 2, 2026; additional FTC rulemaking on AI is expected. This file should be reviewed quarterly.

3. FTC Operation AI Comply (Finding 1) targeted deceptive AI capability claims and fake reviews — zero cases involved decorative imagery. The materiality threshold matters: not all AI-modified media requires disclosure.

---

## Sources Consulted

- US FTC. "FTC Announces Crackdown on Deceptive AI Claims and Schemes." September 25, 2024. https://www.ftc.gov/news-events/news/press-releases/2024/09/ftc-announces-crackdown-deceptive-ai-claims-schemes
- US FTC Business Blog. "Operation AI Comply." https://www.ftc.gov/business-guidance/blog/2024/09/operation-ai-comply-continuing-crackdown-overpromises-ai-related-lies
- EU AI Act, Article 50. https://artificialintelligenceact.eu/article/50/
- EU AI Act full text (Regulation 2024/1689). https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689
- C2PA Technical Specification v1.3. https://c2pa.org/specifications/
- Content Authenticity Initiative — Verify Tool. https://contentauthenticity.org/verify
- FTC Endorsement Guides (16 CFR Part 255, revised November 2023)
- Cross-references: color-accuracy.md F13, video-integration.md F15, video-optimization.md F12, ethics-gate.md PART 5.3
