<!-- CLASSIFICATION_DATE: 2026-04-14 -->
# Evidence Tier Classification

**Purpose:** Define the credibility tiers for all citations used in CRO findings. Every citation in the plugin's reference files is assigned a tier based on the publisher's reputation and research rigor. Tiers are locked to the publisher — never upgraded or downgraded per individual citation.

**Version:** 1.1.0
**Created:** 2026-03-19
**Revised:** 2026-04-14 (finding-level tier rule)

---

## Tier application — finding-level, not citation-level

The tier attached to a rendered finding reflects **both** the source credibility AND the strength of the finding's page anchor. A finding that cites a Gold-tier publisher (Baymard, NNGroup, peer-reviewed journal) but lacks a concrete page anchor — a DOM selector, screenshot region, or verbatim quoted copy from the audited page — is **downgraded to Bronze** regardless of citation quality. Page-specificity is a precondition for Gold.

- **Gold finding** = Gold-tier citation AND concrete page anchor AND measured value (e.g., observed contrast ratio, counted elements, quoted price).
- **Silver finding** = Silver-tier citation AND page anchor (DOM selector OR quoted copy), evidence described but not numerically measured.
- **Bronze finding** = any lower combination, including findings with strong citations but no page anchor (the citation is sound; the finding has not shown how it applies to this page).

This rule is enforced at the reconciliation layer by the evidence-anchor gate (`${CLAUDE_PLUGIN_ROOT}/contracts/audit-reconciliation.md` Step 0c). Findings without any page anchor are rejected entirely — they do not reach the Bronze tier, they are bounced back to the auditor for rewrite or dropped after two rewrite attempts.

---

## Tier Definitions

### Gold — Highest Credibility
Primary research institutions, peer-reviewed journals, and industry-standard measurement bodies. Gold sources conduct original research with documented methodology, large sample sizes, and peer review.

**Publishers:**
- Baymard Institute
- Nielsen Norman Group (NNGroup)
- Spiegel Research Center
- Laws of UX
- Google CrUX (Chrome User Experience Report)
- **Peer-reviewed journals:**
  - PMC / NIH (PubMed Central)
  - SAGE Journals
  - Oxford Journal of Consumer Research (JCR)
  - Springer
  - ScienceDirect (Elsevier)
  - ACM CHI (Conference on Human Factors in Computing Systems)
  - ACM CCS (Conference on Computer and Communications Security)
  - ACM conferences and journals (general — top-tier peer-reviewed CS venues)
  - USENIX Security Symposium
  - Taylor & Francis (Psychology & Marketing, Journal of Consumer Behaviour)
  - Wiley (Journal of Consumer Psychology)
  - APA (American Psychological Association journals)
  - INFORMS (Marketing Science, Management Science)
  - MDPI peer-reviewed journals (when N>500 or with ACM CHI secondary citations)

**Criteria:** Original research, documented methodology, sample sizes typically N>500, peer-reviewed or industry-standard measurement.

### Silver — Strong Credibility
Established industry practitioners, enterprise research divisions, standards bodies, and analyst firms with documented methodology. Silver sources produce original insights but may lack formal peer review.

**Publishers:**
- CXL Institute (CXL)
- Stripe (engineering blog, research reports)
- W3C (Web Content Accessibility Guidelines, specifications)
- Shopify enterprise blog (Shopify Plus, UX research posts)
- Forrester Research
- McKinsey & Company
- Gartner
- Google Developers blog
- Google/Alphabet research papers
- Adobe Digital Insights
- Salesforce Research
- Deloitte Digital
- Accenture Interactive

**Criteria:** Original research or analysis with methodology described, enterprise-scale data, industry authority in their domain.

### Bronze — Baseline Credibility
Marketing blogs, content marketing platforms, SaaS vendor blogs, and industry commentators. Bronze sources often aggregate or repackage research from Gold/Silver sources. Data may be proprietary without disclosed methodology.

**Publishers:**
- VWO Blog
- Campaign Monitor
- HubSpot (blog, reports)
- Neil Patel / NP Digital
- GrowthSuite
- Yieldify
- TargetBay
- Optimizely Blog
- Unbounce Blog
- ConversionXL Blog (non-Institute content)
- WordStream
- Kissmetrics
- Crazy Egg
- Sumo
- Any "(2026)" blog post repackaging older statistics without new data
- Any source not listed in Gold or Silver tiers

**Criteria:** Industry commentary, aggregated statistics, proprietary data without full methodology, vendor-produced content.

**Default rule:** Any source not explicitly listed in Gold or Silver defaults to Bronze at runtime.

---

## Do Not Cite

**When to apply:** A citation URL is dead (returns 404, domain expired, content removed) and no alternative URL for the same research can be found.

**Handling rules:**

1. **If other citations support the same finding:** Drop the dead citation. Keep the finding and its stat supported by the remaining live citations.

2. **If the dead URL is the ONLY citation for a specific statistic:** Do NOT rewrite the finding or remove the stat. Instead, add a deprecation annotation:
   ```
   - **Citation Status**: Original source URL dead; stat unverifiable
   ```
   This preserves backward compatibility — existing audit.md files that reference this stat remain valid.

3. **If the dead URL is the only citation AND no other evidence supports the recommendation:** Flag the finding for manual review. Add:
   ```
   - **Citation Status**: Original source URL dead; finding requires re-verification
   ```

**Rationale:** Destructive edits to reference files break existing audit.md references. A finding that says "232% increase (trust-and-credibility.md, Finding 14)" would become a dangling reference if Finding 14 no longer contains that number.

---

## Multi-Source Findings

When a finding cites multiple sources from different tiers:

**Rule:** Assign the tier of the **primary (first-listed) source**.

**Examples:**
- "CXL Institute (Silver), HubSpot Blog (Bronze)" → **Silver**
- "Baymard Institute (Gold), NNGroup (Gold)" → **Gold**
- "Neil Patel (Bronze), Forrester (Silver)" → **Bronze** (Neil Patel is listed first)

**Rationale:** The first-listed source is typically the primary basis for the finding's claim. Subsequent sources provide corroboration.

---

## Quality Flags

**Purpose:** Optional per-citation annotation for outliers where evidence quality diverges significantly from the tier norm.

**When to use:** Only for genuine outliers. Most citations need NO quality flag (~90%+ will not have one).

**Format:**
```markdown
- **Quality Flag**: [brief note]
```

**Examples of when to flag:**
- Bronze citation with unusually strong methodology: `"Quality Flag: methodology note — N=50,000 across 12 sites (HubSpot 2024 report)"`
- Gold source with an editorial claim (no data): `"Quality Flag: editorial; no sample data for this specific claim"`
- Silver source citing a single case study: `"Quality Flag: single case study; N=1 site"`

**Examples of when NOT to flag:**
- A Gold source with normal Gold-quality methodology (expected)
- A Bronze source with typical Bronze-quality methodology (expected)
- Disagreement with the finding's conclusion (tiers measure source credibility, not agreement)

---

## Adding New Sources

When a new source is encountered during a future audit:

1. Check if the publisher is listed in Gold, Silver, or Bronze above
2. If listed, use that tier
3. If NOT listed, default to Bronze
4. To permanently add a new publisher to a tier:
   - Edit this file (`references/evidence-tiers.md`)
   - Add the publisher name to the appropriate tier's publisher list
   - Commit with message: `chore: add [Publisher] to [Tier] evidence tier`

**Criteria for tier promotion:**
- Bronze → Silver: Publisher demonstrates consistent original research with documented methodology
- Silver → Gold: Publisher's research is peer-reviewed or achieves industry-standard measurement status

---

## Field Format in Reference Files

Each finding in the domain reference files (`references/*.md`) should have these fields added after `Boundary Conditions`:

```markdown
- **Evidence Tier**: [Gold|Silver|Bronze]
- **Quality Flag**: [optional string — omit line entirely if no flag needed]
```

If Citation Status annotation is needed (dead URL):
```markdown
- **Evidence Tier**: [Gold|Silver|Bronze]
- **Citation Status**: Original source URL dead; stat unverifiable
```
