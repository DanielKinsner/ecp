# Consolidated Review Findings & Execution Plan — 2026-06-10

**This is the single working roadmap.** It consolidates the three review-era commits
(`a45d196` Codex adversarial audit, `5c645d7` Claude spec-conformance audit, `25c072f`
GRAPHIFY) plus the still-open items from the 2026-06-08 handoff into one deduped
inventory and one sequenced plan. Full finding texts stay in the source docs — this doc
maps and sequences; it does not restate.

**Sources (provenance):**

| Commit | Doc | Author | What it is |
|---|---|---|---|
| `a45d196` | [docs/2026-06-09-product-v1-adversarial-audit.md](../2026-06-09-product-v1-adversarial-audit.md) | Codex session | 5 findings (2×P0, 2×P1, 1×P2) vs product.md v1.0 |
| `5c645d7` | [docs/reviews/2026-06-10-spec-audit.md](2026-06-10-spec-audit.md) | Claude session (117-agent) | 216-entry conformance matrix + 31 ranked findings (C1–C18, H1–H4, M1–M5, L1–L4) |
| `25c072f` | `graphify-out/GRAPH_REPORT.md` | Codex session | **Not a review** — code-graph navigation artifact (5050 nodes / 316 communities). No findings to merge; useful as a map while executing this plan. |
| (prior) | [docs/2026-06-08-handoff-bloat-prune-and-runreview-fixes.md](../2026-06-08-handoff-bloat-prune-and-runreview-fixes.md) | Claude session | Deferred/pending items that this plan absorbs |

**⚠️ ID disambiguation.** Three ID spaces collide. In this doc: `C1–C18 / H / M / L`
**always** mean the spec-audit findings; handoff run-review items are prefixed
`hc-` (`hc-C3` true-height probe, `hc-C4` normalizations canary, `hc-C6` ghost-zone);
Codex audit findings are `P0-1, P0-2, P1-1, P1-2, P2-1`. The two C-spaces share **no**
semantic overlap (e.g. `C3` = off-slide markers; `hc-C3` = scroll-height probe).

---

## 1. Dedupe map (Codex ↔ spec-audit)

Every Codex finding accounted for. Verification of the two Codex-unique findings was
re-run against the working tree on 2026-06-09 (5-agent pass) — both confirmed.

| Codex finding | Spec-audit counterpart | Disposition |
|---|---|---|
| **P0-2** absence findings auto-placed | **C2** (identical: schema requires `proposed_anchor`, autofix injects, Strategies 2/3 place) | **Full dup.** Track as C2. Both audits independently converged — highest-confidence finding in the set. |
| **P0-1** SKILL load order imports frozen/v1 runbooks | **H1** (broader: frozen-family marketing across runtime-loaded contracts) | **Partial dup.** H1 is the canonical item, **but** P0-1's per-file evidence index is primary material H1 only cites secondhand: `team-lifecycle.md:53-58`, `workflows/audit.md:16,142,740`, `synthesizer-subagent.md:3`, `priority-path-synthesis.md:12,14`, `audit-assembly.md`, `audit-reconciliation.md:56`, `progress-comparison.md`, `flags.md:42`, `lead-discipline.md:17,26`, `SKILL.md:15,41,54,56,58,59,123,168`. The Phase-5 sweep scope = union of H1 + P0-1 + handoff Category B (14 files). |
| **P1-1** default cluster routing undercuts full-breadth moat | **None — spec-audit missed it** (matrix s2.1 marked conforms) | **NEW → H5** (below). Verified true 2026-06-09. |
| **P1-2** frozen inputs/modes remain valid active contract states | **H1 + Decline List** — and the audits **disagree** | **Adjudication A4.** Convergent half (live-voiced `--ab-scaffold`, consent chain) is in H1. Contested half: `meta-schema.md:26,115-121` accepting `build`/`quick-scan`/`compare` + frozen source modes — Codex says fix, spec-audit declined as deliberate §7/G7 shared-contract surface. Unexamined half: `contracts/device-semantics.md:141-147` presents file/description/screenshot as **active** source modes — cited by neither H1 nor the Decline List (grep-verified); fold into the Phase-5 sweep regardless of A4's outcome. |
| **P2-1** product.md version inconsistency | **None — spec-audit missed it** (its own header even says "v1.0 … amendments through 2026-06-01" without noticing the tension) | **NEW → M6** (below). Verified true 2026-06-09. |

## 2. New findings from consolidation

### H5 — Default `--auto` audit ships 3–4 clusters while the spec calls all-10 breadth canonical (ex-Codex P1-1)

product.md:57-58 declares the full 10-cluster set canonical ("breadth is the
differentiator"). But `contracts/flags.md:56-58,298-299` defaults `--auto` to `standard`
(3–4 clusters); `--auto --deep` only reaches `comprehensive` (5–7, still a page-type
subset); all-10 requires explicit `everything`/`--focus all` (`meta-schema.md:81-85`).
Override rules (`cluster-routing.md:116-122`) can ADD on specific signals but never
restore full breadth, and **no label/banner marks a reduced-scope report** — "degraded"
(`audit-state-machine.md:32`) is reserved for acquisition failures. Net: the default
automated run silently sells subset coverage under a full-breadth claim.
**Severity** High (spec divergence). **Effort** S–M depending on adjudication **A3**:
make all-10 the canonical default, or amend the spec via §10 to bless page-type subsets,
or keep subsets but label reduced scope in meta + rendered report.
**Verification:** test pinning the default scope resolution to whichever rule A3 picks;
if labeling is chosen, a render test asserting the subset banner.

### M6 — product.md header says Spec v1.0 while §10 contains four v1.1 amendment rows (ex-Codex P2-1)

`product.md:3` ("Spec version: 1.0") + `product.md:244` ("Baseline. This is Spec v1.0")
vs four v1.1 rows dated 2026-06-01 at `product.md:253-256`. No supersession rule exists;
the header's "prior version language is historical" caveat covers only *other* artifacts.
Both this consolidation's prompt and both audits had to guess which version they were
auditing. **Severity** Medium (governance ambiguity in the constitution itself).
**Effort** S — adjudication **A5** picks: bump header to 1.1, or relabel the rows as
contract addenda that don't bump the spec version. Either way one §10-consistent edit.

## 3. Consolidated inventory (33 ranked findings + carried items)

Canonical IDs = spec-audit IDs + H5/M6. Full texts in
[2026-06-10-spec-audit.md](2026-06-10-spec-audit.md) (Ranked Findings section).

| Tier | IDs | Theme |
|---|---|---|
| Critical | C1, C2*, C3 | §4.2 placement: no confidence gate; absence auto-place (*= Codex P0-2*); off-slide wrong-screenshot |
| Critical | C4, C5, C6, C7, C8, C9 | Reference/dedup chain: `(not found)` device-suffix; other-device mislabel; unvalidated v1 fallback; merge data loss; no dedup trail; local_id keying |
| Critical | C10–C16 | Acquisition truth: invisible elements; unrecorded DOM mutation; blind Subscribe-click; variant pinning; one-shot `occluded`; silent 1× DPR; per-selector truncation |
| Critical | C17, C18 | v1 "projected lift"; ethics voice contract anti-hedging |
| High | H1*, H2, H3, H4, **H5** | Frozen-family marketing/load order (*= Codex P0-1*); source_url enforcement; §8 guardrail absent; honor-system §6 gate; **cluster-scope default** |
| Medium | M1–M5, **M6** | Runner blind spot; 21 untested clauses; CRITICAL-severity schema gap; missing frozen formats; hypotheses-voice; **spec version** |
| Low | L1–L4 | AGENTS.md; stale README limitation; conformance-gaps names; Sweep-3 premise |
| Watch (appendix) | W1–W3 | `placement_repair.finalize` provenance; loader regex hardening; tall-page tiling docstring/test |
| Handoff carry | hc-C3, hc-C4, hc-C6, region-as-point, predicate-anchor, factory-dedup, CONVENTIONS-note | True-height probe; normalizations canary; ghost-zone stacking (recommend **decline**, see A8); region/banner findings rendering as a point not a box (handoff Addendum B — distinct from stacking, judged by LV3); specialist predicate-anchor tightening (PR-97 class); `reflection_state`/`report_state` dedup; `reference_*` family note |
| Handoff pending (live) | LV1–LV4 | LV1 acquirer merge/auto-convert audit; LV2 hero-capture re-audit (awdmods); LV3 `ecp-visual-qa` vision gate on the re-capture; LV4 editor active-marker-only render check |

## 4. Adjudication queue — owner decisions (nothing below Phase 1 starts until these are ruled)

One sitting, ~30 minutes. Each ruling is recorded as a §10 Spec Change Log entry when it
amends the spec, or as a one-line verdict in this doc when it confirms code must move.

| # | Decision | Options (pick one) | Blocks |
|---|---|---|---|
| **A1** | **C2 absence placement** — spec "always blank" vs deliberate, schema-enforced `proposed_anchor` design | (a) code conforms: schema+contract+autofix+markers+tests change together (effort L) · (b) §10 entry blesses typed proposed-anchor placement for absences (effort S) | Phase 2 |
| **A2** | **C1 confidence gate** — operationalize "~99.9%" | (a) numeric gate over the strategy ladder + QA taxonomy alignment · (b) §10 entry redefining the threshold as the strategy ladder's exact-tier only | Phase 2 |
| **A3** | **H5 cluster default** | (a) default all-10 · (b) §10 entry: page-type subsets are canonical · (c) keep subsets, label reduced scope in meta + report | Phase 5 (labels) or standalone |
| **A4** | **P1-2 contested half** — meta-schema frozen engagement types/source modes, flag-matrix frozen columns | (a) Codex: split active vs archived schema / mark legacy-read-only · (b) spec-audit: working-as-designed §7 shared contract; reword only live-voiced text | Phase 5 scope |
| **A5** | **M6 spec version** | (a) bump header to 1.1 · (b) relabel rows as addenda | Phase 1 (trivial edit once ruled) |
| **A6** | **L1 AGENTS.md** | (a) delete · (b) commit a §8-conformant version ("this is a Claude Code plugin; Codex archived") | Phase 1 |
| **A7** | **hc-C4 normalizations canary** — ~150–250 additive lines making the shipped C5-normalize sanction enforceable | (a) greenlight (recommended — it's the enforcement that makes the sanction safe) · (b) keep deferred | Phase 7 |
| **A8** | **hc-C6 ghost-zone placement** | **Recommend decline/park**: validation showed it won't silence the `proxy_overload` warn it targeted; high-risk geometry. Re-open only if LV3 vision-QA shows stacked-marker **or region-as-point** placement (two distinct failure classes from the awdmods addendum) is still hurting reports | — |
| **A9** | **H4 gate strictness** — should `--mark-client-verified` mechanically refuse while `needs-manual-marker` markers remain (escape hatch `--force`)? | (a) yes (recommended) · (b) keep honor-system per spec's "manual pass stays manual" | Phase 2 |

## 5. Execution plan

Sequenced for correctness-per-risk; every commit is small, on a short-lived branch
ff-merged to `main`, with its regression test (repo convention). Phases 3/4/6/7 need no
spec ruling; Phase 1 is adjudication-free except items 12a/12b (trivial edits gated on
A5/A6); Phases 2 and 5 consume the larger adjudications.

### Phase 0 — Adjudication sitting (owner, no code)
Rule A1–A9 above. Output: §10 entries where the spec moves; verdict lines here otherwise.

### Phase 1 — Quick-wins batch (~13 S-effort, no-adjudication code true-ups)
From the spec-audit's greenlightable batch, plus the trivial ruled items:
1. **C4** v1 `finding-groups` device suffix (kills a literal `(not found)` source)
2. **C6** loud ERROR on sidecar-fallback parse (contract already specifies it)
3. **C8** serialize the v2 dedup-review sidecar (data already in memory)
4. **C9** key loader extras by `local_id`
5. **C3** blank the `e_index_lookup_offslide` path instead of rendering
6. **C10** visibility filter in element extraction (the contract's own check)
7. **C14** per-scroll occlusion probe
8. **C15** record `dpr_requested`/`dpr_actual`/`dpr_fallback`
9. **M3** schema allOf: CRITICAL ⇒ ethics only
10. **L2 + L3** doc true-ups (README known-limitations; conformance-gaps test names)
11. **Sweep-3 hygiene**: delete orphaned v1.4.1 plugin cache; update CLAUDE.md:45-55 stale-plugin note for this box
12. (a) **M6** spec-version edit (gated on A5) · (b) **L1** AGENTS.md (gated on A6)
13. **CONVENTIONS-note**: `reference_*` family = operator maintenance, off the audit path

### Phase 2 — §4.2 placement ruling implementation (consumes A1/A2/A9)
C1 + C2 + H4 land together as one focused branch — schema, specialist contract,
autofix, `v2_markers`, QA taxonomy (`visual_evidence` medium vs `v2_html_builder`
strong mismatch), and tests move in the same direction the ruling picks. Don't start
before the ruling; C2 touches a schema-**required** field.

### Phase 3 — Reference-chain integrity
**C5** (other-device membership check + `synthesizer-v2.md:256` contract alignment) and
**C7** (union loser citations/anchors on merge — pattern at `pipeline.py:409-420`; fix or
delete the dead `devices_present` loop). Quick wins C4/C6/C8/C9 will already have closed
the rest of the silent-loss paths.

### Phase 4 — Acquisition truth batch + ONE live audit session
Code: **C11** (record overlay removal/reveal into `overlays_detected` + scope the
reveal), **C12** (text/aria-constrained dismissal — no more blind Subscribe clicks),
**C13** (URL variant pinning + `variant_source`), **C16** (capture-then-cap per
contract), **C17** (remove v1 projected-lift), **hc-C3** (true-height probe — both
halves or neither, per the handoff plan).
Then **one live `--plugin-dir` session** clears the entire pending-live queue at once:
**LV1** (acquirer merge/auto-convert — confirm verbatim per the handoff caveat: (a) the
lead pre-creates the engagement dir and the acquirer accepts it with `--allow-existing`
without wiping `meta.json`; (b) `baton{,-mobile}.json` are v2-shape on disk after
acquisition with `baton*.v1raw.json` backups present), **LV2** (awdmods hero re-audit —
confirm the `293d0ed` reveal fix kills the VC-08/VC-24 false-finding cascade), **LV3**
(`ecp-visual-qa` on the re-capture — its verdicts also rule the A8 re-open question),
**LV4** (editor active-marker check), plus smoke for this phase's acquisition changes. Run `scripts/diagnose_engagement.py` on the result
as the stage-attribution scorecard.

### Phase 5 — The contract-reword sweep (H1 ∪ P0-1 ∪ handoff Category B; consumes A3/A4)
The big deferred item, now precisely scoped three ways. One workflow: one agent per
contract file → reads the stale file + canonical v2 source + how SKILL loads it →
proposes exact diff + confidence → human reviews → apply high-confidence → tests +
grep-guards so it can't regress. File list (union):
`workflows/audit.md` · `contracts/synthesizer-subagent.md` · `audit-reconciliation.md` ·
`audit-assembly.md` · `progress-comparison.md` · `priority-path-synthesis.md` ·
`dispatch-contract.md` (v1 teammate template ~129-269) · `team-lifecycle.md` ·
`flags.md` (incl. `--ab-scaffold`/`--ab-tool` per H1) · `device-semantics.md` (per A4 —
uncovered by the spec-audit; verify + reword) · `meta-schema.md` (per A4) ·
`lead-discipline.md` (consent chain) · `cluster-routing.md` (dead SKILL anchors; H5
labels per A3) · `skills/audit/SKILL.md` (load table itself: stop loading what's dead) ·
`SKILL.notes.md` routing rows. Keep the §7 carve-out: frozen *interface rows* stay;
live-voiced *behavioral instructions* go. Fold in C18's contract half (ADJACENT hedge
carve-out in `ethics-subagent-v2.md:184-188`) and C5's doc half. End with grep-guard
tests + a G21-style frozen-mode non-invokability guard (from M2's list).

### Phase 6 — Ethics/legal enforcement
**C18** canary half (hedge-lint on ADJACENT prose), **H2** (Source-Registry allowlist +
vacated-rules blocklist in the citations canary), **H3** (deterministic dark-pattern
lint over recommendation/Priority-Path text reusing the BLOCK detector vocabulary,
wired into `run_all_canaries`). One canary-design session.

### Phase 7 — Coverage backfill + parked items
**M1 first** (runner-blind-spot guard — protects everything after it; + add
`smoke:editor-server` to `npm test`), then **M2** pins opportunistically alongside
whichever fix touches the same surface, **M4**, **M5**, **W2/W3** cheap hardening if
touching those files anyway, **hc-C4** (if A7 greenlights), factory-dedup (optional,
focused refactor), specialist-prompt predicate-anchor tightening (with any further
placement work, after LV3 data).

### Standing constraint
`docs/ecp/` is gitignored — summarize live-audit results inline in the handoff/PR text.
Run both test runners on every phase (`pytest` + `unittest discover`); M1's guard makes
this self-enforcing once landed.

## 6. What was checked so nothing was lost

- Every Codex finding mapped (table §1); the two with no spec-audit counterpart were
  re-verified against the tree by independent agents before inclusion (H5, M6).
- The spec-audit's Decline List was honored — declined items stay declined except where
  Codex disagrees (that's A4, surfaced as a decision, not silently re-opened).
- All 11 handoff deferred/pending items are placed: hc-C3 → Phase 4; hc-C4 → A7/Phase 7;
  hc-C6 → A8 (recommend decline); Category B → Phase 5; factory-dedup + CONVENTIONS-note
  → Phases 7/1; LV1–LV4 → Phase 4's live session; predicate-anchor tightening → Phase 7.
- GRAPH_REPORT.md carries no findings (navigation artifact only).
- Spec-audit appendix item 4 is intentionally untracked: it is the audit's own
  self-correction note (an agent error about `citations/sources.md`, already corrected
  in the matrix), not a finding.
- This draft was itself adversarially checked against all three sources by an
  independent agent; 5 gaps it found (region-as-point coverage, A5/A6 gating, LV1
  acceptance criteria, P0-1 cite completeness, appendix-item-4 note) were fixed before
  commit.
