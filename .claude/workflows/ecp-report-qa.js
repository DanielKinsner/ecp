export const meta = {
  name: 'ecp-report-qa',
  description: 'Agentic QA pass over an ECP report: verify a sample of findings against the frozen engagement evidence across anchor / citation / claim dimensions, then summarize. Prototype for the product.md §6 draft->client-ready gate.',
  whenToUse: 'After an ECP audit produces findings, to verify hotspots resolve, citations support their claims, and observations hold against the captured page — before the human client-ready pass.',
  phases: [
    { title: 'Sample', detail: 'extract a sample of FAIL/PARTIAL findings from the engagement' },
    { title: 'Verify', detail: 'per finding, fan out anchor + citation + claim verifiers in parallel' },
    { title: 'Report', detail: 'aggregate verdicts into a QA summary' },
  ],
}

// Forward slashes work on Windows; override via args for another machine/engagement.
const ROOT = (args && args.root) || 'C:/Users/Daniel Kinsner/OneDrive/Documents/GitHub/ecp'
const ENG = (args && args.engagement) || `${ROOT}/fixtures/slingmods-pdp`
const SAMPLE = (args && args.sample) || 6

const FINDINGS_SCHEMA = {
  type: 'object',
  required: ['findings'],
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['cluster', 'local_id', 'verdict', 'title', 'baton_index'],
        properties: {
          cluster: { type: 'string' },
          local_id: { type: 'integer' },
          verdict: { type: 'string' },
          title: { type: 'string' },
          surface: { type: 'string' },
          baton_index: { type: 'string' },
          element_role: { type: 'string' },
          observation: { type: 'string' },
          citations: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                source: { type: 'string' },
                section: { type: 'string' },
                tier: { type: 'string' },
              },
            },
          },
        },
      },
    },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['status', 'detail'],
  properties: {
    status: { type: 'string', description: 'one of the allowed status tokens for this dimension' },
    detail: { type: 'string', description: 'one sentence of concrete evidence for the verdict' },
  },
}

phase('Sample')
const sampled = await agent(
  `You are sampling findings from an ECP audit engagement for a QA pass. Read these cluster-emission JSON files (absolute paths):
- ${ENG}/cluster-visual-cta-desktop.json
- ${ENG}/cluster-pricing-desktop.json
- ${ENG}/cluster-trust-credibility-desktop.json
Across them, select the first ${SAMPLE} findings whose verdict is FAIL or PARTIAL. Prefer variety across clusters, and INCLUDE at least one finding whose element.baton_index is "absent" if present. For each selected finding return: cluster, local_id, verdict, title, surface, baton_index (element.baton_index), element_role (element.role), observation (first ~400 chars), and citations (each reference_citations entry's source, section, tier). Return ONLY the structured object.`,
  { schema: FINDINGS_SCHEMA, label: 'sample-findings', phase: 'Sample' },
)

const findings = (sampled && sampled.findings) || []
log(`sampled ${findings.length} finding(s) for QA`)

const ref = (f) => `${f.cluster} F-${String(f.local_id).padStart(2, '0')}`

phase('Verify')
const verified = await pipeline(
  findings,
  (f) =>
    parallel([
      // 1) ANCHOR — does the hotspot target resolve, and is it the right kind of element?
      () =>
        agent(
          `Verify the page-anchor integrity of one ECP finding against the captured baton.
Read ${ENG}/baton.json — it has an "elements" array where each entry has an "e_index" (like "e4"), "tag", "role", "text_content", and "rect".
Finding ${ref(f)}: title="${f.title}", element.baton_index="${f.baton_index}", expected role="${f.element_role || '(unknown)'}".
- If baton_index is "absent": this is a legitimate absence finding (recommending something NOT on the page). status="absent_ok" UNLESS the title implies a concrete on-page element it should have anchored to.
- Else: confirm an element with e_index exactly "${f.baton_index}" exists in baton.elements, and that its tag/role is consistent with the finding's subject and expected role.
Return status ∈ {valid, role_mismatch, not_found, absent_ok} and a one-sentence detail naming the element you found (tag/role/text).`,
          { schema: VERDICT_SCHEMA, label: `anchor ${ref(f)}`, phase: 'Verify' },
        ),
      // 2) CITATION — does the cited reference exist and actually support the claim?
      () =>
        agent(
          `Verify the citation of one ECP finding resolves and supports its claim.
Finding ${ref(f)}: title="${f.title}", claim="${(f.observation || '').slice(0, 300)}".
Citations: ${JSON.stringify(f.citations || [])}.
For the FIRST citation, read the file ${ROOT}/references/<source> where <source> is its "source" field (e.g. "hero-section-psychology.md"). Confirm the file exists; if a "section" is given, confirm a heading matching it is present; then judge whether the source actually supports the finding's claim (not just topically adjacent).
Return status ∈ {supported, file_missing, section_missing, weak_support} and a one-sentence detail quoting or naming what you found.`,
          { schema: VERDICT_SCHEMA, label: `cite ${ref(f)}`, phase: 'Verify' },
        ),
      // 3) CLAIM — adversarially test the observation against the captured page.
      () =>
        agent(
          `Adversarially verify one ECP finding against the captured page evidence. Try to REFUTE it; default to "uncertain" if you cannot confirm.
Finding ${ref(f)}: surface="${f.surface}", claim="${(f.observation || '').slice(0, 400)}".
Evidence: ${ENG}/dom.html (captured DOM — use Grep to find the relevant element/text, do NOT read the whole file) and ${ENG}/baton.json.
Decide whether the captured evidence SUPPORTS the claim, CONTRADICTS it, or is INSUFFICIENT.
Return status ∈ {holds, refuted, uncertain} and a one-sentence detail citing the specific text/element you found (or failed to find).`,
          { schema: VERDICT_SCHEMA, label: `claim ${ref(f)}`, phase: 'Verify' },
        ),
    ]).then((v) => ({
      ref: ref(f),
      title: f.title,
      baton_index: f.baton_index,
      anchor: v[0],
      citation: v[1],
      claim: v[2],
    })),
)

const rows = verified.filter(Boolean)

phase('Report')
const summary = await agent(
  `You are writing the QA summary for an ECP report-verification run. Here are the per-finding verdicts (anchor / citation / claim), as JSON:

${JSON.stringify(rows, null, 2)}

Write a TERSE markdown section (no preamble) with:
1. A table: | Finding | Anchor | Citation | Claim | (use the status tokens; add ✓ for clean, ⚠ for a problem).
2. Counts per dimension (how many clean vs flagged).
3. The 3 most important concrete problems found (quote the detail), if any.
4. One-line verdict: did this agentic QA pass surface real, actionable issues a human reviewer would want before client-ready? Be honest if it mostly passed.
Keep it under ~250 words.`,
  { label: 'qa-summary', phase: 'Report' },
)

return summary
