export const meta = {
  name: 'ecp-visual-qa',
  description: 'Visual hotspot-placement QA for an ECP report: Tier-0 deterministic placement-confidence triage -> crop the suspect markers onto their screenshots -> a vision agent looks at each crop and judges whether the hotspot box lands on the element its finding describes -> aggregate. Tiered: free (Tier-0 only) / standard (1 verifier on flagged) / deep (3-verifier majority on flagged).',
  whenToUse: 'After an ECP audit produces review-state-{device}.json, to verify hotspots land on the right elements before the product.md §6 human client-ready pass. Verifies against the frozen engagement screenshots (no live re-fetch).',
  phases: [
    { title: 'Triage', detail: 'Tier-0 placement_audit (free, deterministic) + crop suspect markers' },
    { title: 'Verify', detail: 'vision agent per crop: on-target / off-target / wrong-element / empty-region' },
    { title: 'Aggregate', detail: 'summarize verdicts + flag misplacements for repair' },
  ],
}

// ---- Inputs (override via Workflow args) ----
const ROOT = (args && args.root) || 'C:/Users/SM - Dan/Documents/GitHub/ecp'
const ENG = (args && args.engagement) || `${ROOT}/docs/ecp/2026-06-01-749a3c3d`
const DEVICE = (args && args.device) || 'desktop'
const TIER = (args && args.tier) || 'standard' // 'free' | 'standard' | 'deep'
const MIX = (args && args.mix) || (TIER === 'deep' ? 40 : 8)
const VOTES = TIER === 'deep' ? 3 : 1

const MANIFEST_SCHEMA = {
  type: 'object',
  required: ['summary', 'crops'],
  properties: {
    summary: { type: 'string', description: 'the Tier-0 audit summary text' },
    crops: {
      type: 'array',
      items: {
        type: 'object',
        required: ['f_ref', 'png', 'finding_title', 'classification'],
        properties: {
          f_ref: { type: 'string' },
          png: { type: 'string', description: 'absolute path to the crop PNG' },
          finding_title: { type: 'string' },
          observation: { type: 'string' },
          element_hint: { type: 'string' },
          classification: { type: 'string' },
          reasons: { type: 'array', items: { type: 'string' } },
          severity: { type: 'string' },
        },
      },
    },
  },
}

const VERDICT_SCHEMA = {
  type: 'object',
  required: ['verdict', 'inside_box', 'why'],
  properties: {
    verdict: { type: 'string', description: 'on-target | off-target | wrong-element | empty-region | too-large-ambiguous' },
    inside_box: { type: 'string', description: 'one sentence: what is actually inside the orange rectangle' },
    why: { type: 'string', description: 'one sentence: does that match the finding subject' },
  },
}

// ---- Phase 1: Tier-0 triage + crops (deterministic Python, run by one agent) ----
phase('Triage')
const triage = await agent(
  `From the directory ${ROOT}, run these two commands with the project Python (python / py -3), then return the result.

1. python scripts/report/placement_audit.py audit --engagement ${ENG} --device ${DEVICE}
2. ${TIER === 'free' ? '(skip — free tier)' : `Make a fresh empty temp dir (e.g. under the system temp), then run:
   python scripts/report/placement_audit.py crops --engagement ${ENG} --device ${DEVICE} --out <that_tmp_dir> --mix ${MIX}
   then read <that_tmp_dir>/crops-manifest.json`}

Return the audit summary text in "summary". ${TIER === 'free'
    ? 'Return an empty "crops" array.'
    : 'Return the manifest\'s "crops" array verbatim, but ensure each crop\'s "png" is an ABSOLUTE path.'}`,
  { schema: MANIFEST_SCHEMA, label: `triage:${DEVICE}`, phase: 'Triage' },
)

log(`Tier-0 triage complete (${DEVICE}, tier=${TIER}): ${triage.crops.length} crops to verify`)

if (TIER === 'free' || triage.crops.length === 0) {
  return { engagement: ENG, device: DEVICE, tier: TIER, summary: triage.summary, verified: [] }
}

// ---- Phase 2: vision verification (1 verifier, or 3-of majority for deep) ----
function verifyPrompt(c) {
  return `Read the image at: ${c.png}

It is a crop of an ecommerce page screenshot with an ORANGE RECTANGLE drawn on it — the hotspot an audit tool placed for this finding:
- Title: "${c.finding_title}"
- About: ${c.observation || c.finding_title}
- Intended element: ${c.element_hint || '(the subject described above)'}

Look at what is actually INSIDE the orange rectangle. Does the box land on the element/subject this finding is about?
Reply via the schema: verdict (on-target | off-target | wrong-element | empty-region | too-large-ambiguous), inside_box (what is actually in the box), why (does it match). Read-only visual check; do nothing else.`
}

const verified = await pipeline(
  triage.crops,
  (c) =>
    parallel(
      Array.from({ length: VOTES }, (_, i) => () =>
        agent(verifyPrompt(c), { label: `verify:${c.f_ref}#${i + 1}`, phase: 'Verify', schema: VERDICT_SCHEMA }),
      ),
    ).then((votes) => {
      const v = votes.filter(Boolean)
      const onTarget = v.filter((x) => x.verdict === 'on-target').length
      // majority must affirm on-target, else it's a placement problem
      const status = v.length && onTarget > v.length / 2 ? 'on-target' : 'misplaced'
      return { ...c, status, on_target_votes: onTarget, votes: v }
    }),
)

phase('Aggregate')
const results = verified.filter(Boolean)
const misplaced = results.filter((r) => r.status === 'misplaced')
log(`Visual QA: ${results.length} verified -> ${results.length - misplaced.length} on-target, ${misplaced.length} misplaced`)

return {
  engagement: ENG,
  device: DEVICE,
  tier: TIER,
  summary: triage.summary,
  totals: { verified: results.length, on_target: results.length - misplaced.length, misplaced: misplaced.length },
  misplaced: misplaced.map((r) => ({
    f_ref: r.f_ref, severity: r.severity, finding_title: r.finding_title,
    tier0_reasons: r.reasons, votes: `${r.on_target_votes}/${VOTES} on-target`,
    evidence: (r.votes[0] && r.votes[0].inside_box) || '',
  })),
  on_target: results.filter((r) => r.status === 'on-target').map((r) => r.f_ref),
}
