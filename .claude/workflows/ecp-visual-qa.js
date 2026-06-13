export const meta = {
  name: 'ecp-visual-qa',
  description: 'Visual hotspot-placement QA for an ECP report: Tier-0 deterministic placement-confidence triage -> crop the suspect markers onto their screenshots -> a vision agent looks at each crop and judges whether the hotspot box lands on the element its finding describes -> aggregate. Tiered: free (Tier-0 only) / standard (1 verifier on flagged) / deep (3-verifier majority on flagged).',
  whenToUse: 'After an ECP audit produces review-state-{device}.json, to verify hotspots land on the right elements before the product.md §6 human client-ready pass. Verifies against the frozen engagement screenshots (no live re-fetch).',
  phases: [
    { title: 'Triage', detail: 'Tier-0 placement_audit (free, deterministic) + crop suspect markers' },
    { title: 'Verify', detail: 'vision agent per crop: on-target / off-target / wrong-element / empty-region' },
    { title: 'Repair', detail: 'auto re-anchor misplaced findings, re-verify the re-anchors with vision, flag the rest' },
    { title: 'Aggregate', detail: 'summarize verdicts + flag misplacements for repair' },
  ],
}

// ---- Inputs (override via Workflow args) ----
// Workflow scripts run in a sandboxed JS context with NO Node API: `process`
// is not defined (a bare reference dies with ReferenceError before any agent
// spawns). Default to '.' — paths resolve against the session cwd, which is
// the repo root in the canonical --plugin-dir session; pass args.root to run
// against another checkout.
const ROOT = (args && args.root) || '.'
const ENG = (args && args.engagement) || `${ROOT}/docs/ecp/2026-06-01-749a3c3d`
const DEVICE = (args && args.device) || 'desktop'
const TIER = (args && args.tier) || 'standard' // 'free' | 'standard' | 'deep'
const MIX = (args && args.mix) || (TIER === 'deep' ? 40 : 8)
const VOTES = TIER === 'deep' ? 3 : 1
const REPAIR = (args && args.repair) !== false // auto-repair misplaced findings (default on)

const MANIFEST_SCHEMA = {
  type: 'object',
  required: ['summary', 'crops'],
  properties: {
    summary: { type: 'string', description: 'the Tier-0 audit summary text' },
    total_weak: { type: 'integer', description: 'total WEAK placements the audit reported (the Y in "X strong, Y weak")' },
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

const CROPS_SCHEMA = { type: 'object', required: ['crops'], properties: { crops: MANIFEST_SCHEMA.properties.crops } }

const REPAIR_SCHEMA = {
  type: 'object',
  required: ['re_anchored', 'flagged', 'repaired_path'],
  properties: {
    re_anchored: { type: 'array', items: { type: 'object', required: ['f_ref'], properties: { f_ref: { type: 'string' } } } },
    flagged: { type: 'array', items: { type: 'object', required: ['f_ref'], properties: { f_ref: { type: 'string' }, reason: { type: 'string' } } } },
    repaired_path: { type: 'string', description: 'absolute path to review-state-{device}.repaired.json' },
  },
}

// ---- Phase 1: Tier-0 triage + crops (deterministic Python, run by one agent) ----
phase('Triage')
const triage = await agent(
  `From the directory ${ROOT}, run these two commands with the project Python (python / py -3), then return the result.

1. python scripts/report/placement_audit.py audit --engagement ${ENG} --device ${DEVICE}
2. ${TIER === 'free' ? '(skip — free tier)' : `python scripts/report/placement_audit.py crops --engagement ${ENG} --device ${DEVICE} --out ${ENG}/.visual-qa-crops/triage --mix ${MIX}
   then read ${ENG}/.visual-qa-crops/triage/crops-manifest.json`}

Return the audit summary text in "summary" and total_weak = the WEAK count from the "[device] N markers -> X strong, Y weak" line. ${TIER === 'free'
    ? 'Return an empty "crops" array.'
    : 'Return the manifest\'s "crops" array verbatim (the manifest png paths are already absolute).'}`,
  { schema: MANIFEST_SCHEMA, label: `triage:${DEVICE}`, phase: 'Triage' },
)

if (!triage || !Array.isArray(triage.crops)) {
  return { engagement: ENG, device: DEVICE, tier: TIER, error: 'triage returned no usable result', verified: [] }
}

log(`Tier-0 triage complete (${DEVICE}, tier=${TIER}): ${triage.crops.length} crops to verify`)

if (TIER === 'free' || triage.crops.length === 0) {
  return { engagement: ENG, device: DEVICE, tier: TIER, summary: triage.summary, total_weak: triage.total_weak ?? null, verified: [] }
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
      const status = onTarget > VOTES / 2 ? 'on-target' : 'misplaced' // vs configured VOTES, not survivors
      return { ...c, status, on_target_votes: onTarget, votes: v }
    }),
)

const results = verified.filter(Boolean)
const misplaced = results.filter((r) => r.status === 'misplaced')
log(`Visual QA: ${results.length} verified -> ${results.length - misplaced.length} on-target, ${misplaced.length} misplaced`)

// ---- Phase 3: repair (deterministic re-anchor + flag) then re-verify the re-anchors ----
let repair = null
if (REPAIR && misplaced.length > 0) {
  phase('Repair')
  const misplacedRefs = misplaced.map((r) => r.f_ref).join(',')
  const rep = await agent(
    `From ${ROOT}, run with the project Python (python / py -3):
  python scripts/report/placement_repair.py repair --engagement ${ENG} --device ${DEVICE} --misplaced "${misplacedRefs}" --plugin-root ${ROOT}
Then read ${ENG}/placement-repair-log.json and return: re_anchored (array of {f_ref} from log entries with action "re-anchored"), flagged (array of {f_ref, reason} from entries with action "flagged"), and repaired_path = the absolute path to ${ENG}/review-state-${DEVICE}.repaired.json.`,
    { schema: REPAIR_SCHEMA, label: 'repair', phase: 'Repair' },
  )

  // Re-verify each re-anchor (it trusts the finding's anchor text, so confirm with vision).
  let reverified = []
  if (rep.re_anchored.length > 0) {
    const reRefs = rep.re_anchored.map((r) => r.f_ref).join(',')
    const recrop = await agent(
      `From ${ROOT}, run with the project Python:
  python scripts/report/placement_audit.py crops --engagement ${ENG} --device ${DEVICE} --review-state "${rep.repaired_path}" --out ${ENG}/.visual-qa-crops/recrop --f-refs "${reRefs}"
Then read ${ENG}/.visual-qa-crops/recrop/crops-manifest.json and return its "crops" array (png paths are already absolute).`,
      { schema: CROPS_SCHEMA, label: 'repair:recrop', phase: 'Repair' },
    )
    reverified = (await parallel(
      recrop.crops.map((c) => () =>
        agent(verifyPrompt(c), { label: `reverify:${c.f_ref}`, phase: 'Repair', schema: VERDICT_SCHEMA })
          .then((v) => ({ f_ref: c.f_ref, kept: v.verdict === 'on-target', verdict: v.verdict, evidence: v.inside_box })),
      ),
    )).filter(Boolean)
  }
  const confirmed = reverified.filter((r) => r.kept).map((r) => r.f_ref)
  const reverted = reverified.filter((r) => !r.kept)
  // Reconcile: a re-anchor that got NO verdict (e.g. screenshot missing) must fail
  // safe to manual — never adopted by omission.
  const gotVerdict = new Set(reverified.map((r) => r.f_ref))
  const noVerdict = rep.re_anchored.map((r) => r.f_ref).filter((fr) => !gotVerdict.has(fr))
  const toManual = reverted.map((r) => r.f_ref).concat(noVerdict)

  // Persist the verdicts into .repaired.json: confirmed -> confident, everything
  // else -> needs-manual-marker. (repair() already left re-anchors at the safe
  // "section-match" default, so even if this step is skipped nothing reads "Likely OK".)
  await agent(
    `From ${ROOT}, run with the project Python and report the one-line result:
  python scripts/report/placement_repair.py finalize --engagement ${ENG} --device ${DEVICE} --confirmed "${confirmed.join(',')}" --reverted "${toManual.join(',')}"`,
    { label: 'repair:finalize', phase: 'Repair' },
  )

  log(`Repair: ${confirmed.length} verified, ${reverted.length} reverted, ${noVerdict.length} no-verdict -> manual, ${rep.flagged.length} flagged`)
  repair = {
    repaired_path: rep.repaired_path,
    re_anchored_verified: confirmed,
    re_anchored_reverted: reverted.map((r) => ({ f_ref: r.f_ref, verdict: r.verdict, evidence: r.evidence })),
    no_verdict_forced_manual: noVerdict,
    flagged_for_manual: rep.flagged,
  }
}

phase('Aggregate')
// Coverage honesty: the MIX sample caps how many weak markers get verified. Surface
// the gap so "verified" can't be misread as "the whole page was QA'd".
const weakVerified = triage.crops.filter((c) => c.classification === 'weak').length
const weakNotVerified = Math.max(0, (triage.total_weak ?? weakVerified) - weakVerified)
if (weakNotVerified > 0) {
  log(`Coverage gap: ${weakNotVerified} weak placements NOT verified (MIX cap ${MIX}) — raise --mix or use tier=deep`)
}
return {
  engagement: ENG,
  device: DEVICE,
  tier: TIER,
  summary: triage.summary,
  coverage: { weak_total: triage.total_weak ?? null, weak_verified: weakVerified, weak_not_verified: weakNotVerified, mix_cap: MIX },
  totals: { verified: results.length, on_target: results.length - misplaced.length, misplaced: misplaced.length },
  misplaced: misplaced.map((r) => ({
    f_ref: r.f_ref, severity: r.severity, finding_title: r.finding_title,
    tier0_reasons: r.reasons, votes: `${r.on_target_votes}/${VOTES} on-target`,
    evidence: (r.votes[0] && r.votes[0].inside_box) || '',
  })),
  on_target: results.filter((r) => r.status === 'on-target').map((r) => r.f_ref),
  repair,
}
