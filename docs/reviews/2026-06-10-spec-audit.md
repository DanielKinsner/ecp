# ECP Spec-Conformance Audit — 2026-06-10

**Spec:** `product.md` v1.0 (baseline 2026-05-26, amendments through 2026-06-01)
**Audited commit:** `a45d196` on `main` (working tree, Windows home checkout)
**Mode:** audit-only. One pre-authorized fix was in scope (Sweep 3); it was **not applied** because the diagnosis it rested on is contradicted by the machine state — see Sweep 3 and finding L4.
**Method:** three sweeps. Sweep 1 ran a 117-agent adversarial conformance pass: ten section-mappers covering 100% of `product.md` (216 requirement entries), five targeted hunters on wrong-audit-result paths, and adversarial verifiers on every non-conforming claim (each hunt finding judged by two independent verifiers; claims that failed verification were dropped or moved to the appendix). Sweep 2 ran both test runners and mapped spec clauses to tests. Sweep 3 inspected the live plugin configuration directly.

> **Concurrent-session note (read first).** While this audit ran, a separate Codex session was active on this same checkout. Evidence: (a) untracked `AGENTS.md` appeared at 2026-06-09 18:36:47 (a copy of `CLAUDE.md` with "Claude" string-replaced by "Codex"); (b) commit `a45d196` ("docs: add product v1 adversarial audit findings", trailer `Co-Authored-By: Codex Opus 4.8`) landed at 18:48:23, adding [docs/2026-06-09-product-v1-adversarial-audit.md](../2026-06-09-product-v1-adversarial-audit.md). I verified via the workflow transcripts that none of my agents wrote either artifact. The two audits were independent and **converge on the same two top findings** (absence-finding auto-placement; frozen/v1 contract text in the live load order), which strengthens both. This document is the broader of the two (full matrix + test truthfulness + acquisition/dedup/reference-chain hunts + tooling). Note: pushing this document to origin necessarily also pushes `a45d196`, which was sitting unpushed on local `main`.

## Executive summary

The repo is in much better shape than a cold read of this findings list suggests — **178 of 216 spec requirements conform**, all 29 §10 change-log amendments are in force and test-pinned, and the §6 `--auto` gate, the G4 blank-fallback, the G16 drop-surfacing, and the citation/anchor schema are real, code-enforced trust machinery. Both test suites are green.

But the audit's job was adversarial, and three clusters of real problems survived two-verifier scrutiny:

1. **§4.2 presentation trust is the largest divergence.** There is no confidence gate anywhere in the placement code — placement is categorical (strategy ladder), absence findings are systematically auto-placed (schema *requires* the anchor that triggers auto-placement; the autofix *injects* one when missing), off-slide elements render on the wrong screenshot, and the placement-QA summary undercounts weak placements. The spec's own words make wrong placement "the worst outcome — a hard violation."
2. **The reference/dedup chain can silently lose or misattribute data.** A v1 device-suffix bug produces the literal `(not found)` Priority Path string the spec names as a violation; the v2 loader can mislabel a hallucinated ref as "applies on the other device"; dedup merges drop loser citations with no audit trail; a local_id/position keying mismatch can silently strip citations and severity.
3. **Acquisition can capture a page state no user ever saw, unsignalled.** No visibility filtering (the spec's named DOM-not-displayed class), unrecorded DOM mutation (overlay force-removal + animation force-reveal), blind first-button overlay clicks, no variant pinning, a single-shot `occluded` flag, silent 1× DPR fallback, and per-selector element truncation.

Separately: the **legal/ethics hedging mandate is not just unenforced — the voice contract actively contradicts it** (F-C18), the §8 guardrail role has no implementation surface at all (F-H3), and the unittest runner silently misses ~91 declared tests including the highest-stakes §4.2/§4.1 guards (F-M1).

Per the standing constraint, no finding below decides whether spec or code is right; both sides are quoted and the owner adjudicates. The biggest single adjudication is **absence-finding placement** (F-C2): the `proposed_anchor` design is deliberate, schema-enforced, and test-pinned — and the spec verbatim forbids it. One of the two must move via a §10 entry or a code change.

---

# Sweep 1 — Spec Conformance Matrix

Every requirement in `product.md` is enumerated below — 216 entries across ten section groups. Status values: `conforms`, **DIVERGENT**, **MISSING**, `untestable` (principle/aspirational/conditional-on-future-action). Entries marked `conforms †` were initially flagged divergent by a mapper and **refuted on adversarial verification** (details in the Decline List). Every DIVERGENT/MISSING entry maps to a ranked finding or the Decline List.

| Section group | Entries | Conforms | Divergent | Missing | Untestable |
|---|---|---|---|---|---|
| §0 + §1 + §2.1–2.2 | 18 | 18 | 0 | 0 | 0 |
| §2.3 + §2.4 | 20 | 17† | 3 | 0 | 0 |
| §3 | 15 | 10 | 4 | 0 | 1 |
| §4.1 | 13 | 10 | 3 | 0 | 0 |
| §4.2 | 9 | 6 | 3 | 0 | 0 |
| §5 | 14 | 6 | 6 | 0 | 2 |
| §6 | 14 | 10† | 1 | 3 | 0 |
| §7 | 61 | 55† | 2 | 2 | 2 |
| §8 + §9 | 23 | 19 | 1 | 1 | 2 |
| §10 (v1.1 amendments) | 29 | 29 | 0 | 0 | 0 |
| **Total** | **216** | **180** | **24** | **6** | **7** |

† includes entries refuted back to conforms on verification.

## A. §0 Governing Principle + §1 Identity + §2.1–2.2 Input contract

| # | Requirement | Status | Where (primary evidence) |
|---|---|---|---|
| s0.1 | Governing principle: ECP is held to a commercial-grade trust bar despite being a personal operator tool, because output is delivered to clie… | conforms | .claude-plugin/plugin.json:5-7; scripts/report/templates/html_structure.py:258 |
| s0.2 | Trust bar definition: not 'never wrong' but 'never untraceable, never silently misleading'. | conforms | schema/finding-v1.json:8-25; schema/finding-v1.json:425-459 |
| s0.3 | Every claim must be checkable. | conforms | schema/finding-v1.json:255-322; schema/finding-v1.json:425-459 |
| s0.4 | Every limitation must be visible. | conforms | scripts/report/templates/html_structure.py:258; tests/test_report_disclaimer.py:18-26 |
| s0.5 | A polished output that quietly lies is a product failure; a plain output that shows its work is the product working. | conforms | scripts/assembly/report_state.py:14-18; scripts/assembly/report_state.py:53-76 |
| s0.6 | ECP is an ecommerce conversion-psychology audit engine. | conforms | .claude-plugin/plugin.json:4; skills/audit/SKILL.md:1-11 |
| s0.7 | Analyzes a single ecommerce page against an evidence-tiered research library. | conforms | schema/finding-v1.json:291-322; schema/finding-v1.json:341-345 |
| s0.8 | Produces cited, page-anchored findings. | conforms | schema/finding-v1.json:77-113; schema/finding-v1.json:255-322 |
| s0.9 | Produces a prioritized action ranking (Priority Path). | conforms | contracts/priority-path-synthesis.md:32-43; skills/audit/SKILL.md:34 (P0-09) |
| s0.10 | Produces an editable annotated visual report. | conforms | tools/editor/index.html; tools/editor/editor.js |
| s0.11 | Operator: Dan, via Claude Code. | conforms | .claude-plugin/plugin.json:5-7 |
| s0.12 | Deliverable audience: clients. | conforms | scripts/report/templates/html_structure.py:258; contracts/humanizer-subagent.md:76-79 |
| s0.13 | Canonical runtime: Claude Code; Codex is optional. | conforms | .claude-plugin/plugin.json:2-4; .claude-plugin/marketplace.json |
| s0.14 | The audit IS the product; everything else is support, frozen scope (§5), or a frozen contract (§7). | conforms | skills/audit/SKILL.md:15; docs/CONVENTIONS.md |
| s0.15 | The canonical capability is a single-page conversion-psychology audit driven from a URL. | conforms | skills/audit/SKILL.md:64-68; contracts/lead-discipline.md:54 |
| s0.16 | URL is the only canonical input. | conforms | skills/audit/SKILL.md:10; skills/audit/SKILL.md:64-68 |
| s0.17 | A real audit reasons about the rendered, visible page — computed styles / what is actually painted — not raw markup. | conforms | scripts/acquire_url.py:107-166; scripts/acquire_url.py:262-297 |
| s0.18 | Screenshot-only and codebase inputs are frozen (§5). | conforms | skills/audit/SKILL.md:68; docs/conformance-gaps.md:147-157 |

## B. §2.3 Domain breadth + §2.4 Deliverable boundary

| # | Requirement | Status | Where (primary evidence) |
|---|---|---|---|
| s2.1 | The audit must span the full cross-domain cluster set; breadth is the differentiator and is canonical. | conforms | product.md:57-58; contracts/cluster-routing.md:9 |
| s2.2 | Cluster 'visual-cta' exists in cluster routing. | conforms | contracts/cluster-routing.md:15; contracts/specialists/visual-cta.md |
| s2.3 | Cluster 'trust-credibility' exists in cluster routing. | conforms | contracts/cluster-routing.md:16; contracts/specialists/trust-credibility.md |
| s2.4 | Cluster 'pricing' exists in cluster routing. | conforms | contracts/cluster-routing.md:17; contracts/specialists/pricing.md |
| s2.5 | Cluster 'checkout-flows' exists in cluster routing. | conforms | contracts/cluster-routing.md:18; contracts/specialists/checkout-flows.md |
| s2.6 | Cluster 'performance-ux' exists in cluster routing. | conforms | contracts/cluster-routing.md:19; contracts/cluster-routing.md:28 |
| s2.7 | Cluster 'product-media' exists in cluster routing. | conforms | contracts/cluster-routing.md:20; contracts/specialists/product-media.md |
| s2.8 | Cluster 'category-navigation' exists in cluster routing. | conforms | contracts/cluster-routing.md:21; contracts/specialists/category-navigation.md |
| s2.9 | Cluster 'content-seo' exists in cluster routing. | conforms | contracts/cluster-routing.md:22; contracts/specialists/content-seo.md |
| s2.10 | Cluster 'post-purchase' exists in cluster routing. | conforms | contracts/cluster-routing.md:23; contracts/specialists/post-purchase.md |
| s2.11 | Cluster 'audience' exists in cluster routing. | conforms | contracts/cluster-routing.md:24; contracts/specialists/audience.md |
| s2.12 | The audit must be backed by the full evidence-tiered reference library (Gold/Silver/Bronze credibility tiers). | conforms | references/evidence-tiers.md:24-96; references/cta-design-and-placement.md:32 |
| s2.13 | Cluster auditors load only their cluster reference files plus the always-loaded ethics + evidence-tier files (operationalizes 'backed by the… | conforms | contracts/cluster-routing.md:11; contracts/specialist-prompt-v2.md:74-78 |
| s2.14 | The trust invariants in section 4 apply uniformly to every cluster; no cluster is exempt. | conforms † | schema/finding-v1.json:7-25; contracts/specialist-prompt-v2.md:154 |
| s2.15 | The canonical audit produces exactly three things and stops. | **DIVERGENT** | product.md:70-78; skills/audit/SKILL.md:15 |
| s2.16 | Deliverable 1: Findings — each cited (tiered) and anchored to a page element. | conforms | schema/finding-v1.json:8-25; schema/finding-v1.json:55-58 |
| s2.17 | Deliverable 2: Priority Path — the prioritized ranking of findings. | conforms | contracts/priority-path-synthesis.md:30-43; contracts/synthesizer-v2.md:65-73 |
| s2.18 | Deliverable 3: Visual report — the annotated, self-contained HTML report, including the hotspot edit tool (§4.2). | conforms | contracts/report-export.md:11-42; scripts/generate-report.py |
| s2.19 | The audit stops before generating an action plan, review, or code. | **DIVERGENT** | skills/audit/SKILL.md:15; contracts/audit-state-machine.md:18-66 |
| s2.20 | plan -> review -> build are the frozen build family (§5) — not invokable from the canonical audit. | **DIVERGENT** | product.md:155; skills/ |

## C. §3 What ECP IS NOT

| # | Requirement | Status | Where (primary evidence) |
|---|---|---|---|
| s3.1 | Never sees real traffic or conversion rate. | conforms | scripts/acquire_url.py:1315; scripts/acquire_url.py:1314 |
| s3.2 | Does not run A/B tests. | **DIVERGENT** | contracts/flags.md:25-26; contracts/flags.md:217-236 |
| s3.3 | Does not promise lift. | **DIVERGENT** | scripts/report/html_builder.py:609-648; scripts/report/html_builder.py:1004 |
| s3.4 | Output is research-backed hypotheses, not measured outcomes. | **DIVERGENT** | scripts/report/templates/html_structure.py:258; tests/test_report_disclaimer.py:19-23 |
| s3.5 | Not a replacement for Lighthouse, axe, or an SEO crawler. | conforms | README.md:16-17; scripts/report/templates/html_structure.py:258 |
| s3.6 | Surfaces obvious, high-signal, conversion-relevant technical issues. | conforms | contracts/specialist-prompt-v2.md:137; contracts/specialists/performance-ux.md:40 |
| s3.7 | Does not produce full technical breakdowns unless an issue is obvious. | untestable | contracts/specialist-prompt-v2.md:137; contracts/specialists/performance-ux.md:40-62 |
| s3.8 | Ethics/legal citations are informational. | conforms | scripts/report/templates/html_structure.py:258; tests/test_report_disclaimer.py:19-23 |
| s3.9 | Borderline ethics hedged as 'adjacent' per §4.1. | conforms | contracts/ethics-subagent-v2.md:27; contracts/ethics-subagent-v2.md:142-149 |
| s3.10 | Never a compliance certification or legal opinion. | conforms | scripts/report/templates/html_structure.py:258; tests/test_report_disclaimer.py:19-23 |
| s3.11 | Legal rigor held as high as possible. | conforms | contracts/ethics-subagent-v2.md:36-38; contracts/ethics-subagent-v2.md:202 |
| s3.12 | Legal findings human-verified before client delivery (§6). | conforms | scripts/assembly/report_state.py:53-83; scripts/generate-report.py:77-94 |
| s3.13 | One URL per engagement (no site-wide crawl). | conforms | scripts/acquire_url.py:1314-1315; skills/audit/SKILL.md:10 |
| s3.14 | Never edits the operator's or client's code (build is frozen, §5). | **DIVERGENT** | contracts/flags.md:13-29; contracts/flags.md:42-43 |
| s3.15 | Never acts without operator review. | conforms | scripts/assembly/report_state.py:71-76; scripts/assembly/reflection_state.py |

## D. §4.1 Content-layer trust invariants

| # | Requirement | Status | Where (primary evidence) |
|---|---|---|---|
| s4.1 | A finding is valid IFF it carries a tiered citation, a concrete ELEMENT anchor, and a falsifiable claim. | conforms | schema/finding-v1.json:8-25 (required: cluster, device, element, evidence_anchors, reference_citations, observation, rec… |
| s4.2 | Tiered citation: every FAIL/PARTIAL finding has >=1 reference_citations entry with a Gold/Silver/Bronze tier. | conforms | schema/finding-v1.json:291-321 (reference_citations array; tier enum Gold/Silver/Bronze; source must end in .md); schema… |
| s4.3 | Concrete ELEMENT anchor: every finding carries an element.baton_index (e<int> or 'absent') resolving to a captured baton element, with role/… | conforms | schema/finding-v1.json:77-113 (element.baton_index REQUIRED; pattern ^e[0-9]+$ OR const 'absent'); schema/finding-v1.jso… |
| s4.4 | Falsifiable claim: every FAIL/PARTIAL finding has >=1 evidence_anchor (DOM/visual/both) and substantive observation/recommendation (>=20 cha… | conforms | schema/finding-v1.json:255-289 (evidence_anchors items; type in {dom,visual,both}; reference required); schema/finding-v… |
| s4.5 | Trust invariants apply uniformly to every cluster; no cluster is exempt. | conforms | schema/finding-v1.json:27-43 (cluster enum: visual-cta, trust-credibility, pricing, checkout-flows, performance-ux, prod… |
| s4.6 | Spec violation: Fabrication — a finding about an element that does not exist on the page must not ship. | conforms | scripts/assembly/business_rules.py:477-512 (_check_baton_index: baton_index must resolve to baton.elements[].e_index — e… |
| s4.7 | Spec violation: DOM-not-displayed — a visibility-dependent claim that reflects raw markup rather than what is actually rendered. (Retired by… | conforms | workflows/acquire.md:554-563 (isOffscreen() checks computed display:none, visibility:hidden, aria-hidden=true at capture… |
| s4.8 | Spec violation: Misquoted / over-applied law — highest bar. Legal claims must be exact, or explicitly hedged. Citing a law as hard fact when… | **DIVERGENT** | references/ethics-gate.md:132-144 (Applicability Self-Check — prompt-level three-question gate, no code enforcement); re… |
| s4.9 | Legal claims that are not exact must be 'explicitly hedged' — i.e., ADJACENT findings must hedge law text as borderline ('may implicate [law… | **DIVERGENT** | workflows/audit.md:197 (RECOMMENDATION framing rule — prompt-level); references/ethics-gate.md:100-120 (ADJACENT finding… |
| s4.10 | Spec violation: Hallucinated reference — any finding or Priority Path entry pointing to a source/ref that does not resolve. (The '(not found… | conforms | scripts/assembly/synthesizer_parser.py:98-158 (v1 validate_stories: every f_ref must be in JSON-derived valid_refs allow… |
| s4.11 | Tolerated (in-spec): Slight overlap / overclaim across granular findings — 'almost healthy'; bounded by dedup, not eliminated. | conforms | scripts/assembly/dedup.py:345-420 (deduplicate_v2: SCOPE-aware dedup across devices; merges duplicates rather than dropp… |
| s4.12 | Feature (must be preserved, never 'fixed' away): Adjacent ethics findings — borderline ethics cases must be intentionally surfaced, labeled … | conforms | schema/finding-v1.json:346-356 (ethics_state enum includes ADJACENT; source_url required when state is BLOCK or ADJACENT… |
| s4.13 | Adjacent ethics findings: any law cited within them must be hedged as borderline ('may implicate [law] — verify'). | **DIVERGENT** | workflows/audit.md:197 (prompt rule for recommendation framing); references/ethics-gate.md:100-120 (ADJACENT format spec… |

## E. §4.2 Presentation-layer trust invariants

| # | Requirement | Status | Where (primary evidence) |
|---|---|---|---|
| s5.1 | Section header naming the trust invariant — presentation layer asks whether the report points at the right thing. | conforms | scripts/report/v2_markers.py:1-61; scripts/assembly/review_state.py:1-6 |
| s5.2 | Optimize for precision over recall: a wrong hotspot costs more than a missing one — a false hotspot is net-negative; a blank is neutral. | conforms | scripts/report/v2_markers.py:36-47; scripts/report/v2_markers.py:773-793 |
| s5.3 | Auto-place a hotspot ONLY at ~99.9% confidence. Below threshold → leave it blank for manual placement. Never auto-place a guess. | **DIVERGENT** | scripts/report/v2_markers.py:37-47; scripts/report/v2_markers.py:672-794 |
| s5.4 | Wrong / wrong-page placement is the worst outcome — a hard violation, worse than a blank. | **DIVERGENT** | scripts/report/geometry_validator.py:121; scripts/report/geometry_validator.py:200-245 |
| s5.5 | Absence findings (recommending an element that does not exist, e.g. 'no sticky CTA') → always blank; the operator places or declines them ma… | **DIVERGENT** | scripts/report/v2_markers.py:452-538; scripts/report/v2_markers.py:751-794 |
| s5.6 | The hotspot edit tool is a first-class part of the product. | conforms | tools/editor/index.html:1-79; tools/editor/editor.js:1-200 |
| s5.7 | The report is not finished when generated; it is finished when placement is finalized. | conforms | scripts/assembly/report_state.py:29-83; contracts/meta-schema.md:89-98 |
| s5.8 | The edit workflow must make creating, placing, and erasing hotspots easy. | conforms | tools/editor/index.html:20-37; tools/editor/editor.js:24-36 |
| s5.9 | Manual placement is a designed step, not a defect. | conforms | scripts/report/v2_markers.py:36-47; scripts/assembly/review_state.py:84-89 |

## F. §5 Frozen scope & reserved seams

| # | Requirement | Status | Where (primary evidence) |
|---|---|---|---|
| s6.1 | Frozen items exist in the codebase/archive but are out of the canonical product until explicitly unfrozen via a Spec Change Log entry (§9). | conforms | README.md:19-20; CHANGELOG.md:396-399 |
| s6.2 | Frozen items may NOT be invoked. | conforms | skills/ (directory listing: only `audit/` and `ecp/` subdirectories exist — no build/, compare/, quick-scan/, resume/ sk… |
| s6.3 | Frozen items may NOT be marketed. | **DIVERGENT** | contracts/flags.md:13-29; contracts/flags.md:39 |
| s6.4 | Frozen items may NOT be relied upon as canonical. | **DIVERGENT** | templates/meta.json.template:22; templates/meta.json.template:23 |
| s6.5 | When unfrozen, frozen items must re-prove conformance to this spec and to the frozen contracts (§7). | untestable | product.md:248-256 (Spec Change Log — no unfreeze entries to date) |
| s6.6 | Frozen mode `quick-scan` is frozen. | **DIVERGENT** | skills/ (no quick-scan skill directory); .claude-plugin/plugin.json:4 (only /ecp:audit registered) |
| s6.7 | Frozen mode `compare` is frozen. | **DIVERGENT** | skills/ (no compare skill directory); .claude-plugin/plugin.json:4 (only /ecp:audit registered) |
| s6.8 | Frozen mode `build` is frozen. | **DIVERGENT** | skills/ (no build skill directory); workflows/ (no plan.md/review.md/build.md — confirmed by directory listing) |
| s6.9 | Frozen mode `resume` is frozen. | **DIVERGENT** | skills/ (no resume skill directory); .claude-plugin/plugin.json:4 (only /ecp:audit registered) |
| s6.10 | Frozen input `screenshot-only` is frozen. | conforms | skills/audit/SKILL.md:64-68; skills/ecp/SKILL.md:22 |
| s6.11 | Frozen input `codebase` is frozen. | conforms | skills/audit/SKILL.md:64-68; skills/ecp/SKILL.md:22 |
| s6.12 | Reserved seam 'Codebase-mode audit' is named-only (its later addition is deliberate, not a surprise). | conforms | product.md:164 (the seam is named only in the spec); skills/audit/SKILL.md:68 (URL-only input enforced) |
| s6.13 | Reserved seam 'Audit → build-on-the-same-repo handoff' is named-only. | conforms | product.md:165 (the seam is named only in the spec); CHANGELOG.md:400-402 |
| s6.14 | Frozen items must conform to the frozen contracts of §7 when unfrozen (cross-reference within §5). | untestable | product.md:183-198 (§7 lists the frozen contracts: finding schema, engagement artifact layout, meta.json schema, plan/re… |

## G. §6 Draft → Client-Ready verification gate

| # | Requirement | Status | Where (primary evidence) |
|---|---|---|---|
| s7.1 | A generated report is a DRAFT (default state). | conforms | templates/meta.json.template:28; scripts/assembly/report_state.py:29 |
| s7.2 | Promotion to CLIENT-READY requires a manual verification pass by the operator. | conforms † | scripts/assembly/report_state.py:30; scripts/assembly/report_state.py:53-83 |
| s7.3 | Manual verification step 1: Re-check the live site. | **MISSING** | scripts/assembly/report_state.py:5; scripts/assembly/report_state.py:53-83 |
| s7.4 | Manual verification step 2: Follow EVERY legal/ethics citation and confirm relevancy. | **MISSING** | scripts/assembly/report_state.py:6; scripts/assembly/report_state.py:53-83 |
| s7.5 | Manual verification step 3: Finalize hotspot placement (per §4.2). | **MISSING** | scripts/assembly/report_state.py:7; scripts/assembly/report_state.py:53-83 |
| s7.6 | The report's state is tracked in meta.json with values `draft` | `client-verified`. | conforms | templates/meta.json.template:28; templates/meta.json.template:101-110 |
| s7.7 | Automated / --auto execution can NEVER mark a report client-ready. | conforms | scripts/assembly/report_state.py:34-36; scripts/assembly/report_state.py:71-76 |
| s7.8 | Rendering a report never promotes it (every generated report starts as draft; the audit flow must not set client-verified). | conforms | scripts/generate-report.py:280-325; scripts/assembly/report_state.py:80 |
| s7.9 | Missing/blank report_state must be treated as draft (back-compat with pre-§6 engagements). | conforms | scripts/assembly/report_state.py:38-46; tests/test_g8_client_verified_gate.py:53-65 |
| s7.10 | Promotion must be a deliberate, explicit operator action (a named CLI verb), not a side-effect. | conforms | scripts/generate-report.py:77-84; scripts/generate-report.py:157-170 |
| s7.11 | Promotion atomically updates `updated` ISO timestamp on flip. | conforms | scripts/assembly/report_state.py:49-51; scripts/assembly/report_state.py:80-82 |
| s7.12 | Spec uses both 'client-ready' (heading/body) and 'client-verified' (meta.json value); code state value MUST be `client-verified`. | **DIVERGENT** | scripts/assembly/report_state.py:29-31; scripts/generate-report.py:77 |
| s7.13 | The verification gate is page-/audit-scope independent: applies to every generated report regardless of cluster set, device, or run mode. | conforms | templates/meta.json.template:28; scripts/assembly/report_state.py:38-46 |
| s7.14 | Validator must flag invalid report_state enum values (anything other than draft|client-verified). | conforms | scripts/assembly/meta_validator.py:131-137; tests/test_g8_client_verified_gate.py:94-101 |

## H. §7 Frozen contracts

| # | Requirement | Status | Where (primary evidence) |
|---|---|---|---|
| s8.1 | Frozen contracts are the stable shared interface that every present and future mode conforms to. | conforms | contracts/lead-discipline.md:120-128; schema/finding-v1.json:1-25 |
| s8.2 | Changing any frozen contract requires a Spec Change Log entry (§9). | conforms | product.md:248-256 |
| s8.3 | Frozen contracts are the reason deferring frozen modes costs zero rework: the modes are downstream consumers of these contracts. | untestable | product.md:155 (frozen modes) |
| s8.4 | Finding schema exists and is a single canonical contract. | conforms | schema/finding-v1.json:1-784 |
| s8.5 | Finding carries a tiered citation (reference_citations[].tier in {Gold, Silver, Bronze}). | conforms | schema/finding-v1.json:291-321 (reference_citations); schema/finding-v1.json:315-320 (tier enum Gold|Silver|Bronze) |
| s8.6 | Finding carries an ELEMENT anchor (element.baton_index keyed against the baton). | conforms | schema/finding-v1.json:77-113 (element + baton_index); schema/finding-v1.json:82-96 (baton_index 'e<int>' OR 'absent') |
| s8.7 | Finding carries a severity (CRITICAL|HIGH|MEDIUM|LOW). | conforms | schema/finding-v1.json:221-225 (severity enum) |
| s8.8 | Finding carries a falsifiable claim (observation + recommendation + why_this_matters required prose). | conforms | schema/finding-v1.json:323-340 (observation, recommendation, why_this_matters); schema/finding-v1.json:460-479 (FAIL/PAR… |
| s8.9 | Engagement artifact layout is docs/ecp/<engagement-id>/. | conforms | contracts/meta-schema.md:3; contracts/lead-discipline.md:290 |
| s8.10 | Engagement directory contains the canonical set of v2 artifacts (meta.json, baton{,-mobile}.json, cluster-{cluster}-{device}.json, ethics-fi… | **DIVERGENT** | contracts/lead-discipline.md:120-128 |
| s8.11 | Concurrent audits share the docs/ecp/ root but isolate by engagement subdirectory; lead does not write outside its engagement directory. | conforms | contracts/lead-discipline.md:290-292 |
| s8.12 | meta.json schema exists. | conforms | contracts/meta-schema.md:1-174; templates/meta.json.template:1-30 |
| s8.13 | meta.json includes the report_state = 'draft' | 'client-verified' field per product.md §6. | conforms | contracts/meta-schema.md:74 (report_state row); contracts/meta-schema.md:89-98 (valid report_state values) |
| s8.14 | Automated/--auto execution can NEVER mark a report client-verified. | conforms | scripts/assembly/report_state.py:53-76 (set_client_verified raises AutoPromotionError when auto=True); contracts/meta-sc… |
| s8.15 | Missing/blank report_state reads as 'draft' (back-compat). | conforms | scripts/assembly/report_state.py:38-46 (read_report_state defaults to draft); contracts/meta-schema.md:98 |
| s8.16 | meta.json carries v2 schema_version=3 and the engagement_status enum per audit-state-machine.md. | conforms | contracts/meta-schema.md:28 (engagement_status required for v2); contracts/audit-state-machine.md:18-93 (full enum + leg… |
| s8.17 | Plan, review, and build-log output formats are frozen alongside the build family. | **MISSING** | contracts/dispatch-contract.md:118 |
| s8.18 | Each format must have a frozen on-disk shape (so an unfrozen mode could write to it). | **MISSING** | — |
| s8.19 | plans_queue field in meta.json supports multi-planner mode (deferred shape for build family). | conforms | contracts/meta-schema.md:70 (plans_queue row); contracts/multi-planner-protocol.md:141,172 (per-PRD plan/review/build-lo… |
| s8.20 | Flag matrix exists as a single canonical reference. | conforms | contracts/flags.md:1-319 |
| s8.21 | Flag matrix is the single source of truth — skills defer here instead of re-documenting flags inline. | conforms | contracts/flags.md:5-8 (single-source-of-truth claim); contracts/flags.md:308-318 ('Adding a new flag' procedure) |
| s8.22 | Flag matrix table lists every CLI flag with type, default, supported-by columns. | conforms | contracts/flags.md:12-30 (Flag summary table) |
| s8.23 | Flag matrix lists flags for currently-frozen modes (build/compare/quick-scan/resume). | conforms † | contracts/flags.md:12-30 |
| s8.24 | Cluster routing is a single canonical contract. | conforms | contracts/cluster-routing.md:1-164 |
| s8.25 | All 10 v5.0 clusters are enumerated. | conforms | contracts/cluster-routing.md:14-24 (10-cluster table); schema/finding-v1.json:30-42 (cluster enum) |
| s8.26 | Page-type defaults table (comprehensive + standard) exists for every documented page type. | conforms | contracts/cluster-routing.md:38-47 (comprehensive defaults); contracts/cluster-routing.md:49-62 (standard defaults) |
| s8.27 | Page-type detection algorithm (URL pattern + DOM signals) is documented. | conforms | contracts/page-detection.md:1-54 |
| s8.28 | Override rules (non-Western market, significant price, mobile device set) ADD clusters but never REMOVE them. | conforms | contracts/cluster-routing.md:116-124 |
| s8.29 | Resolution algorithm (focus → defaults → overrides → dedup → meta.json) is documented in deterministic order. | conforms | contracts/cluster-routing.md:138-154 |
| s8.30 | Legacy v4.x cluster name translation is preserved on resume. | conforms | contracts/cluster-routing.md:126-134; contracts/cluster-migration.md (referenced) |
| s8.31 | Ethics gate exists as canonical ruleset (guardrail on ECP output + detector on audited page). | conforms | references/ethics-gate.md:1-200+; product.md:213-216 (dual-role spec) |
| s8.32 | Ethics-detector implementation: a dedicated ethics subagent runs once per audit on union of devices. | conforms | contracts/ethics-subagent-v2.md:1-372; contracts/ethics-subagent-v2.md:3-5 (only agent running ethics rules) |
| s8.33 | Ethics findings carry ethics_state ∈ {BLOCK, ADJACENT, CLEAR}. | conforms | schema/finding-v1.json:346-350 (ethics_state enum); references/ethics-gate.md:90-122 (three-state output model) |
| s8.34 | Adjacent ethics findings preserved (must not be 'fixed away'); legal claims hedged. | conforms | references/ethics-gate.md:95-104 (ADJACENT semantics); contracts/ethics-subagent-v2.md:149 (ADJACENT) |
| s8.35 | BLOCK/ADJACENT findings require source_url from Source Registry. | conforms | schema/finding-v1.json:481-496 (allOf rule source_url required when BLOCK/ADJACENT); schema/finding-v1.json:351-356 (sou… |
| s8.36 | Source Registry with canonical URLs for every cited regulation exists. | conforms | references/ethics-gate.md:27-86 (Source Registry tables) |
| s8.37 | Vacated / rescinded rules tracker exists; vacated rules must not be cited as live authority. | conforms | references/ethics-gate.md:11-19 (Vacated/Rescinded Rules Tracker); contracts/ethics-subagent-v2.md:42-46 (vacated rules … |
| s8.38 | Cluster specialists do not emit ethics findings (ethics is property of ethics subagent's output only). | conforms | schema/finding-v1.json:498-512 (allOf rule: non-ethics cluster must NOT carry ethics_state); contracts/ethics-subagent-v… |
| s8.39 | Ethics gate acts as absolute guardrail on ECP's own output — ECP must never recommend dark patterns. | conforms | references/ethics-gate.md:1-9 (Check FIRST. Override ALL. No Exceptions.); contracts/ethics-subagent-v2.md:1-5 |
| s8.40 | Applicability self-check before firing BLOCK (3-question rubric). | conforms | references/ethics-gate.md:132-146 (Applicability Self-Check — Mandatory Before Firing BLOCK) |
| s8.41 | Multi-tier standards severity mapping (legal minimum vs. AAA/platform recommendations). | conforms | references/ethics-gate.md:148-183 |
| s8.42 | CRITICAL severity is reserved for ethics; cluster specialists cannot emit CRITICAL. | **DIVERGENT** | schema/finding-v1.json:221-225; contracts/ethics-subagent-v2.md:154-156 |
| s8.43 | Reference library exists in references/ with per-domain markdown files. | conforms | references/cta-design-and-placement.md:1-60+ (24 findings); references/pricing-psychology.md:1-30+ (43 findings) |
| s8.44 | Reference library file format: per-finding fields include Evidence Tier line. | conforms | references/evidence-tiers.md:179-186 (Field Format in Reference Files); references/cta-design-and-placement.md:32,45,57 … |
| s8.45 | Gold / Silver / Bronze tier definitions exist with publisher lists. | conforms | references/evidence-tiers.md:25-94 (Gold/Silver/Bronze definitions + publishers) |
| s8.46 | Default rule: any source not explicitly listed in Gold or Silver defaults to Bronze. | conforms | references/evidence-tiers.md:96 |
| s8.47 | Finding-level tier rule: a Gold-citation finding without a concrete page anchor is downgraded to Bronze. | conforms | references/evidence-tiers.md:12-20 |
| s8.48 | evidence_tier on findings equals max(citation tiers). | conforms | schema/finding-v1.json:514-583 (allOf promotion rules: Gold forces Gold; Silver-and-no-Gold forces Silver); schema/findi… |
| s8.49 | Citations cite reference files relative to references/ ending in .md, with optional line or section. | conforms | schema/finding-v1.json:298-320 (reference_citations item shape with source.pattern '^[a-z][a-z0-9-]*\\.md$') |
| s8.50 | Reference library covers full cross-domain cluster set (10 clusters). | conforms | contracts/cluster-routing.md:14-24 (each cluster's reference files); references/ directory (~70 .md files) |
| s8.51 | Citations file (citations/sources.md) bundles per-finding source URLs. | untestable | — |
| s8.52 | Input contract: URL is the only canonical input. | conforms | skills/audit/SKILL.md:64-68 (URL is sole supported audit input); contracts/url-validation.md:1-63 |
| s8.53 | URL validation: only http://, https:// schemes accepted; reject private/internal IPs. | conforms | contracts/url-validation.md:8-32 (scheme + host validation); contracts/url-validation.md:34-39 (encoding bypass preventi… |
| s8.54 | DNS rebinding protection (validate resolved IP). | conforms | contracts/url-validation.md:41-46 |
| s8.55 | User confirmation required on first fetch per domain per session. | conforms | contracts/url-validation.md:48-52; contracts/flags.md:60-61 ('quick-scan --auto note': consent still required) |
| s8.56 | Rendered-state requirement: audit reasons about the rendered, visible page (computed styles / what is actually painted), not raw markup. | conforms | workflows/acquire.md:678-688 (Step 5: Extract Style Metadata from rendered page); schema/baton-v1.json:72-79 (capture_st… |
| s8.57 | DOM-not-displayed findings (visibility-dependent claims reflecting raw markup) are a spec violation. | conforms | schema/finding-v1.json:602-632 (visual-position-finding rule: above-fold/below-fold/sticky claims require visual anchor … |
| s8.58 | Screenshot-only and codebase inputs are frozen — not accepted as canonical input. | conforms | skills/audit/SKILL.md:64-68; product.md:160-162 (Frozen inputs) |
| s8.59 | Acquirer output (baton) validates against schema/baton-v1.json with engagement_id format YYYY-MM-DD-<8hex>. | conforms | schema/baton-v1.json:1-50; schema/baton-v1.json:26-30 (engagement_id pattern) |
| s8.60 | Acquirer enforces hard wall-clock timeout (180s per device) and aborts to STATUS: TIMEOUT. | conforms | workflows/acquire.md:16 (Hard wall-clock timeout: 180s per acquirer call); contracts/audit-state-machine.md:30-33 (acqui… |
| s8.61 | Baton captures viewport, capture_state, elements with e_index, sections, page_head. | conforms | schema/baton-v1.json:8-19 (required fields); schema/baton-v1.json:46-79 (viewport + capture_state) |

## I. §8 Runtime + §9 Governance

| # | Requirement | Status | Where (primary evidence) |
|---|---|---|---|
| s9.1 | Claude Code is the only runtime in this repo | conforms | .claude-plugin/plugin.json:1-21; .claude-plugin/marketplace.json:1-15 |
| s9.2 | The audit is the `ecp` plugin | conforms | .claude-plugin/plugin.json:2; .claude-plugin/plugin.json:4 |
| s9.3 | Audit invoked as `/ecp:audit` | conforms | skills/audit/SKILL.md:2; .claude-plugin/plugin.json:4 |
| s9.4 | Live development loads the plugin straight from the repo with `claude --plugin-dir <repo>` — no cache copy, no stale-version step | conforms | README.md:55-59; CLAUDE.md:37-43 |
| s9.5 | Codex (and Cursor) are archived, not shipped — both alternate runtimes were archived with the old repo | **DIVERGENT** | AGENTS.md:38-55; AGENTS.md:100-104 |
| s9.6 | Frozen Codex/Cursor are re-portable from the archive if ever wanted, but not part of the canonical product | conforms | archive/cursor-agents/ecp-acquisition.md; archive/cursor-agents/ecp-cluster-auditor.md |
| s9.7 | Codex historically rendered the report with good precision — that edge is a target for the Claude renderer, not a reason to maintain a secon… | conforms | scripts/report/; scripts/generate-report.py |
| s9.8 | Ethics gate is permanent and dual-role | conforms | contracts/ethics-subagent-v2.md:1-371; references/ethics-gate.md:1-765 |
| s9.9 | Ethics gate role 1: absolute guardrail on ECP's own output — must never recommend fake urgency, hidden fees, deceptive defaults, review mani… | **MISSING** | product.md:213-216; references/ethics-gate.md:88-122 (three-state output model — detector framing only) |
| s9.10 | Ethics gate role 2: detector on the audited page (per §4.1) | conforms | contracts/ethics-subagent-v2.md:1-371; references/ethics-gate.md:88-122 |
| s9.11 | Authority direction: product.md wins. Code, README, CHANGELOG, skills, and contracts must conform to it. Where they disagree, they are bugs … | conforms | product.md:7-10; README.md:8-10 |
| s9.12 | Change rule: every change requires a dated, rationale'd entry in the Spec Change Log (§10) | conforms | product.md:248-256 (Spec Change Log table with Date | Version | Change | Rationale columns; 5 entries from 2026-05-26 th… |
| s9.13 | Frozen scope (§5) unfreezes ONLY via such an entry — never implicitly by someone writing code | conforms | product.md:154-158; product.md:226-227 |
| s9.14 | This is what lets the product bob and weave when new problems arise without drifting: agility is allowed, silent drift is not. | untestable | product.md:227-229 |
| s9.15 | Delivery vehicle: this spec is the constitution of a clean, pruned repo, not a patch on the existing one | conforms | CHANGELOG.md:3 ('This repo begins at **1.0.0** as a clean prune-and-re-root.'); CHANGELOG.md:391-405 ('1.0.0 — 2026-05-2… |
| s9.16 | The clean repo is a prune-and-re-root, not a rewrite: working audit-path code and the full reference library are moved, not reimplemented | conforms | CHANGELOG.md:391-405; references/ (full reference library moved) |
| s9.17 | (If 'clean repo' ever turns into 'rebuild the working pipeline' — stop; that is the move failing.) | untestable | product.md:234-235 |
| s9.18 | Carry over only what serves the canonical audit, trace the full audit dependency closure before migrating | conforms | CHANGELOG.md:395-405 ('Removed (archived in the old repo): the build, compare, quick-scan, and resume modes; the Codex a… |
| s9.19 | Write a fresh README and CHANGELOG (reusing the old where beneficial) | conforms | README.md:1-102; CHANGELOG.md:1-425 |
| s9.20 | Archive / quarry: the existing repo becomes a read-only archive — never deleted | conforms | README.md:99-101 ('This repo is a clean prune-and-re-root of `ecommerce-conversion-psychology` (2026-05-26). The full pr… |
| s9.21 | Archive is the quarry from which frozen modes (§5) are mined back when unfrozen | conforms | archive/cursor-agents/README.md:34-40 (un-freeze recipe explicitly: 'Add a dated Spec Change Log entry... Re-prove confo… |
| s9.22 | Git history, the build/compare code, and the postmortem CHANGELOG are shelved, not lost | conforms | README.md:99-101 ('the archived modes/runtimes, and prior CHANGELOG eras live in that archived repo'); CHANGELOG.md:5 |
| s9.23 | Baseline: this is Spec v1.0. All prior version language is historical. | conforms | product.md:3 (Spec version: 1.0); product.md:7-10 (prior version language is historical clause) |

## J. §10 Spec Change Log (v1.1 amendments as binding requirements)

| # | Requirement | Status | Where (primary evidence) |
|---|---|---|---|
| s10.1 | Spec Change Log table exists with headers Date|Version|Change|Rationale | conforms | product.md:250-251 |
| s10.2 | v1.0 baseline row dated 2026-05-26 present as the initial canonical-spec entry | conforms | product.md:252 |
| s10.3 | v1.1 B0: contracts/dispatch-contract.md mandates the lead expand ${CLAUDE_PLUGIN_ROOT} to absolute paths before dispatch | conforms | contracts/dispatch-contract.md:26-28 |
| s10.4 | v1.1 B0: scripts/test-specialist.py render_prompt() substitutes ${CLAUDE_PLUGIN_ROOT} at render time | conforms | scripts/test-specialist.py:302-359; scripts/test-specialist.py:330-333 |
| s10.5 | v1.1 B0: scripts/test-specialist.py render_synthesizer_prompt() substitutes ${CLAUDE_PLUGIN_ROOT} at render time | conforms | scripts/test-specialist.py:418-489; scripts/test-specialist.py:466-469 |
| s10.6 | v1.1 P1: dispatch-contract.md restored the multi-planner/relay dispatch structure (per-role + counter table rows, multi-planner subsection +… | conforms | contracts/dispatch-contract.md:44; contracts/dispatch-contract.md:102-104 |
| s10.7 | v1.1 P1: contracts/relay-loop-protocol.md restored as a file | conforms | contracts/relay-loop-protocol.md:1-7 |
| s10.8 | v1.1 P1: contracts/multi-planner-protocol.md restored as a file | conforms | contracts/multi-planner-protocol.md:1-13 |
| s10.9 | v1.1 #26: per-section screenshots are section-N.jpg for desktop/laptop | conforms | scripts/acquire_url.py:376-393; scripts/acquire_url.py:381 |
| s10.10 | v1.1 #26: per-section screenshots are section-N-mobile.jpg for mobile | conforms | scripts/acquire_url.py:382; scripts/acquire_url.py:392-393 |
| s10.11 | v1.1 #26: naming uniform in BOTH single- and multi-device runs (no device prefix in multi-device) | conforms | scripts/acquire_url.py:376-393; tests/test_acquire_screenshot_naming.py:58-63 |
| s10.12 | v1.1 #26: the validator regex enforces the section-N(-mobile)?.jpg shape (i.e., rejects {device}-section-N.jpg) | conforms | scripts/assembly/business_rules.py:57; scripts/assembly/business_rules.py:788-798 |
| s10.13 | v1.1 #26: the v1->v2 converter (baton_v1_to_v2.py) emits canonical names matching section-N(-mobile)?.jpg | conforms | scripts/baton_v1_to_v2.py:164-166; scripts/baton_v1_to_v2.py:314-316 |
| s10.14 | v1.1 #26: tests/test_acquire_screenshot_naming.py asserts the contract | conforms | tests/test_acquire_screenshot_naming.py:1-63 |
| s10.15 | v1.1: cluster specialists migrated from Agent-Teams teammates to GA parallel one-shot subagents (last teammate role removed from the audit p… | conforms | contracts/dispatch-contract.md:37; contracts/dispatch-contract.md:81 |
| s10.16 | v1.1: dispatch-contract.md per-role + how-to-dispatch rows drop team_name/name for specialists | conforms | contracts/dispatch-contract.md:37; contracts/dispatch-contract.md:111 |
| s10.17 | v1.1: dispatch-contract.md rationale section retitled 'Why specialists are one-shot subagents' | conforms | contracts/dispatch-contract.md:94 |
| s10.18 | v1.1: contracts/specialist-prompt-v2.md (and ethics-subagent-v2.md / synthesizer-v2.md) dispatch lines drop team_name/name and add prompt= a… | conforms | contracts/specialist-prompt-v2.md:19; contracts/ethics-subagent-v2.md:16 |
| s10.19 | v1.1: canonical counter subagent_spawned_specialists is the v2 default in the canary contract | conforms | contracts/dispatch-contract.md:289; contracts/trace-assertion-canary.md:27 |
| s10.20 | v1.1: team_spawned_specialists / team_spawned_auditors retained as aliases at runtime (scripts/assembly/canary_checks.py + determinism_gate.… | conforms | scripts/assembly/canary_checks.py:758-767; scripts/assembly/canary_checks.py:794-799 |
| s10.21 | v1.1: skills/audit/SKILL.md has the team-create step deleted (no TeamCreate call in audit v2) | conforms | skills/audit/SKILL.md:72-89; skills/audit/SKILL.md:89 |
| s10.22 | v1.1: skills/audit/SKILL.md states full-parallel default + --max-concurrent fallback | conforms | skills/audit/SKILL.md:83 |
| s10.23 | v1.1: skills/audit/SKILL.md uses fresh re-dispatch for recovery (not SendMessage bounce) | conforms | skills/audit/SKILL.md:125-133 |
| s10.24 | v1.1: contracts/audit-reconciliation.md Steps 0/0b/0c recovery is fresh re-dispatch | conforms | contracts/audit-reconciliation.md:19; contracts/audit-reconciliation.md:26 |
| s10.25 | v1.1: contracts/flags.md documents --max-concurrent | conforms | contracts/flags.md:20; contracts/flags.md:143-158 |
| s10.26 | v1.1: contracts/trace-assertion-canary.md updated for canonical counter + aliases at runtime | conforms | contracts/trace-assertion-canary.md:27; contracts/trace-assertion-canary.md:43-46 |
| s10.27 | v1.1: contracts/team-lifecycle.md annotated dead-for-audit (retained for multi-planner) | conforms | contracts/team-lifecycle.md:9-22 |
| s10.28 | v1.1 rationale text recorded in §10 for every 2026-06-01 amendment (per §9 Governance which mandates a 'dated, rationale'd entry') | conforms | product.md:253; product.md:254 |
| s10.29 | v1.1: §10 'Specialists off Agent Teams' entry records follow-ups as out-of-scope (live audit smoke + fixture regen + broad Task→Agent rename… | conforms | product.md:256; contracts/dispatch-contract.md:116 |


---

# Sweep 2 — Test Truthfulness

## What each runner reports

Run at repo root on this machine (Python via global interpreter, `PYTHONIOENCODING=utf-8`):

```
python -m pytest tests/ -q
  → 1124 passed, 12 skipped, 54 subtests passed in 54.77s

python -m unittest discover
  → Ran 736 tests ... OK
```

Both green. Both lying by omission in different ways.

## The real combined picture

- **The unittest runner silently misses 91 declared tests** (plus their parametrize expansions — the runtime delta is 388 reported tests): 56 module-level pytest functions across 14 pure-pytest files, 21 methods in pytest-style classes in `test_visual_evidence.py`, and 14 module-level functions in the one **mixed** file, [tests/test_specialist_subagent_dispatch.py](../../tests/test_specialist_subagent_dispatch.py) — where unittest sees only the 4 counter-alias methods and is blind to the 14 functions guarding the entire §10 "specialists off Agent Teams" migration.
- **The pytest-only blind spot is concentrated exactly where the spec's trust invariants live.** Pure-pytest (invisible to unittest): `test_visual_evidence.py` (§4.2 placement taxonomy + hotspot CSS classes), `test_synthesizer_fref_contract.py` (the §4.1 hallucinated-reference guard), `test_determinism_canaries.py` + `test_b4/b5_*` (build determinism), `test_ethics_ref_agreement.py` + `test_dedup_consumer_parity.py` (the §4.1 adjacent-ethics-preservation guard), `test_final_report_render.py` (incl. the path-traversal guard on the self-contained report), `test_review_state_schema.py` / `test_review_state_migration.py` (§6/§7 review-state contract), `test_acquire_screenshot_naming.py` (§10 amendment c), `test_prompt_template_completeness.py` (§10 amendment a), `test_fixture_schema_evolution.py`, `test_no_mojibake_in_fixtures.py`.
- **A third runner exists and is also incomplete:** the three `.mjs` smokes are invisible to both Python runners. `npm test` ([package.json:17](../../package.json)) chains only 2 of 3 — `tests/editor-server-render-smoke.mjs` (`smoke:editor-server`, package.json:14) runs **only when invoked by name**.
- **Fixture-dependent triple-invisibility:** `test_review_state_schema.py` and 2 of 3 tests in `test_final_report_render.py` skip when `docs/ecp/2026-05-01-d5ebb62c` is absent — and `docs/ecp/` is gitignored, so on a fresh checkout those §4.2/§6 guards are unittest-invisible AND pytest-skipped. The 12 pytest skips this run include these.
- **Nothing enforces running both runners.** The rule lives in CLAUDE.md prose only; there is no CI config in the repo at all (verified: no `.github/workflows/`).

This is finding **F-M1**.

## Spec requirements with no test coverage at all

Consolidated from the coverage sweep (each verified against the actual test bodies — name-matching tests asserting something weaker were counted as partial, not covered). This is finding **F-M2**; the full list:

| Spec clause | Coverage |
|---|---|
| §2.2 "URL is the **only** canonical input" (rejection of non-URL inputs at the boundary) | none — prompt text only |
| §2.2 rendered-state allOf branch (`finding-v1.json:602-631`: above-fold/sticky claims need visual anchor + `scroll_y`) | schema exists, **no test exercises the branch** |
| §2.3 the exact ten-cluster set pinned against the spec list | none (enum exists in `cluster-emission-v1.json:33-45` + `dom_preprocess.py:60-69`; no test compares to spec) |
| §2.3 trust invariants uniform across all ten clusters (parametrized) | none — cluster tests default to `pricing` |
| §2.4 "the audit **stops** before plan/review/code" (no plan/review/build artifact produced) | none — prose-only |
| §3.2 not an exhaustive technical auditor | none |
| §3.4 one URL per engagement / never edits code / never acts without review | none |
| §4.1 misquoted/over-applied law ("highest bar") — exactness, hedging, jurisdiction match | none — prompt text only |
| §4.1 ADJACENT hedge phrasing ("may implicate [law] — verify") in finding prose | none — the literal phrase exists nowhere but product.md:133 |
| §4.1 fabrication with no baton present (`test_no_baton_skips_check` confirms the rule silently passes) | unguarded |
| §4.2 absence findings always blank | none (G4 test pins only the no-signal path) |
| §4.2 "~99.9%" threshold (any numeric confidence gate) | none — no such gate exists in code |
| §4.2 wrong placement as a hard ship-blocker | none — detection canaries exist, no blocking gate |
| §5 frozen modes not invokable (a G21-style non-existence guard for `/ecp:build` etc.) | none |
| §5 frozen inputs (screenshot-only, codebase) rejected at the boundary | none |
| §6 manual-pass steps 1 and 2 (re-check live site; follow every legal/ethics citation) | none — honor-system |
| §7 contract 4 (plan/review/build-log formats) | no artifact to test (see F-M4) |
| §7 contract 5 (flag matrix completeness/congruence) | only `--max-concurrent` pinned |
| §7 contract 6 (cluster routing + page-type defaults) | none — `cluster-routing.md`/`page-detection.md` untested |
| §7 contract 9 (input contract URL + rendered-state) | none |
| §8 guardrail on ECP's own output (incl. "even if instructed to") | none — see F-H3 |

A green suite that does not cover these is a finding, not a comfort — but note the inverse too: the §10 amendments, the §6 `--auto` gate, screenshot naming, counter aliases, B0 path resolution, G4/G6/G8/G15/G16/G21/G23/G24 are all genuinely and well test-pinned.

---

# Sweep 3 — Tooling Integrity

**The brief's diagnosis is contradicted by the machine state, so per the brief's own instruction the pre-authorized fix was NOT applied and this is recorded as a finding (L4).**

The brief said: *"The `/ecp:audit` plugin points at the deleted pre-prune directory"* and runs stale code; locate the stale pointer and fix it. What the machine actually shows:

1. **No `ecp` plugin is registered anywhere.** `claude plugin list` shows only compound-engineering, frontend-design, github. `%USERPROFILE%\.claude\plugins\installed_plugins.json` (current) has no ecp entry; `known_marketplaces.json` (current) has no `ecommerce-conversion-psychology` marketplace; `enabledPlugins` in `~/.claude/settings.json` has none.
2. **The stale plugin existed and was already removed.** The removal left backups: `installed_plugins.json.bak-20260503-143433` (had `ecp@ecommerce-conversion-psychology` v1.4.0 entries) and `known_marketplaces.json.bak-20260430-204450` (had the marketplace). So the cleanup CLAUDE.md:53 predicts is still pending on "the Windows boxes" already happened on this one.
3. **One orphan remains:** `%USERPROFILE%\.claude\plugins\cache\ecommerce-conversion-psychology\ecp\1.4.1\` — the full v1.4.1 payload (with `.in_use` marker) still on disk, but **nothing references it**; it cannot load.
4. **No stale pointer exists anywhere findable:** PowerShell profiles (none exist with `plugin-dir`), desktop shortcuts (none), Windows Terminal profiles (no matches), `~/.claude.json` (only a dead project-history entry for the deleted `ecommerce-conversion-psychology` directory and skill-usage counters — neither is a pointer).
5. **The plugin loads correctly from this repo.** Verified live: `claude --plugin-dir "<this repo>" plugin list` → `ecp@inline · Version 1.0.0 · Path: C:\...\GitHub\ecp · Status: √ loaded`.

So the true failure mode on this machine is the opposite of the brief: a session started **without** `--plugin-dir` doesn't run stale code — it has **no** `/ecp:audit` at all. The repo-side plugin manifests ([.claude-plugin/plugin.json](../../.claude-plugin/plugin.json) v1.0.0, [marketplace.json](../../.claude-plugin/marketplace.json) `source: "./"`) are correct. Caveats: the work box (`C:\Users\SM - Dan\...`) was not reachable from here and may still hold the v1.4.1 install; and if the owner observed stale behavior recently, it most plausibly happened there or via the Codex-side session.

No fix was committed. Recommended hygiene (owner greenlight, S-effort): delete the orphaned cache directory and update the stale CLAUDE.md:45-55 guidance for this machine.

---

# Ranked Findings

Severity scale per brief: **Critical** = could produce a wrong audit result · **High** = spec divergence · **Medium** = coverage gap · **Low** = hygiene. Every Critical/High claim below survived two independent adversarial verifiers (or, for L4/L2/L3, was verified directly by the auditing session). Spec/code conflicts record both sides; the owner adjudicates.

## Critical

### C1 — No confidence gate exists anywhere in hotspot auto-placement; the §4.2 "~99.9% or blank" rule is unimplemented

**Issue.** Placement is decided by a categorical strategy ladder — if *any* anchor signal resolves, a marker is placed; only the no-signal-at-all case is left blank. There is no numeric confidence comparison anywhere in the placement path, and the two quality gates that do exist are advisory and inconsistent with each other.
**Evidence.** Spec: *"**Auto-place a hotspot only at ~99.9% confidence.** Below threshold → **leave it blank** for manual placement. Never auto-place a guess."* (product.md:140-141). Code: [scripts/report/v2_markers.py:609-793](../../scripts/report/v2_markers.py) (`auto_map_markers_v2`, Strategies 1→4 with zero confidence comparison; grep for `0.999|99.9` across `scripts/` returns nothing). Compounding: [visual_evidence.py:98-99](../../scripts/report/visual_evidence.py) types `proposed_anchor_element` as (`proxy_element`, **medium**) while [v2_html_builder.py:37-39,51-56](../../scripts/report/v2_html_builder.py) counts the same marker as **strong** in the operator-facing placement summary; [visual_quality.py:62,219-225](../../scripts/assembly/visual_quality.py) tolerates 40% non-exact markers and is consulted by nothing in the render path (grep `visual_quality|proxy_overload` in `v2_html_builder.py` → no matches).
**Severity.** Critical — sub-threshold markers ship in the draft report, and the summary that should warn the operator undercounts them.
**User impact.** A client receives an annotated report whose markers include medium/low-confidence guesses rendered as if placed, while the operator's placement-QA summary reads cleaner than reality.
**Effort.** M (decide the operationalization of "~99.9%", gate Strategies 2/3 and the QA classification on it).
**Verification.** New test: a finding whose only signal is a low-confidence anchor type must produce `fallback_position=None` + `needs-manual-marker` (extends [tests/test_g4_blank_below_confidence.py](../../tests/test_g4_blank_below_confidence.py)); a test pinning `_STRONG_PLACEMENT_METHODS` to the `visual_evidence` confidence taxonomy. Spec clause §4.2 (product.md:140-141).

### C2 — Absence findings are systematically auto-placed; spec says "always blank" (owner adjudication required)

**Issue.** Every layer of the pipeline is built to place absence findings: the schema *requires* a `proposed_anchor` on absent findings, the specialist contract instructs emitting one, the autofix injects a default (`section_index=0`, bottom overlay) when missing, and Strategies 2/3 then render a real marker. Only an absent finding with no anchor and no surface is left blank. This is a deliberate, test-pinned design (fix B, 2026-04-30 — predating the spec) that the spec verbatim forbids.
**Evidence.** Spec: *"**Absence findings** (recommending an element that does not exist, e.g. 'no sticky CTA') → **always blank**; the operator places or declines them manually."* (product.md:144-145). Code: [v2_markers.py:726-771](../../scripts/report/v2_markers.py) (Strategy 2 `proposed_anchor` → real `fallback_position`; Strategy 3 section centroid → `absent_in_section`); [schema/finding-v1.json:586-600](../../schema/finding-v1.json) (proposed_anchor REQUIRED when `baton_index='absent'`); [contracts/specialist-prompt-v2.md:254](../../contracts/specialist-prompt-v2.md) (*"The renderer will place a section-level hotspot at the centroid of the section"*); [scripts/assembly/emission_autofix.py:292-331](../../scripts/assembly/emission_autofix.py) (injects the default anchor pre-validation); [tests/test_visual_evidence.py:111-167](../../tests/test_visual_evidence.py) (locks the auto-placement in). The G4 test covers only the no-signal path.
**Severity.** Critical — a marker drawn for an element that does not exist necessarily lands **on some other element**; §4.2 calls wrong placement "the worst outcome — a hard violation."
**User impact.** A client sees a hotspot box on a real element while the finding text describes a missing one — the report points at the wrong thing.
**Effort.** L if code conforms to spec (schema + contract + autofix + markers + tests all change); S if the owner instead amends the spec via a §10 entry to bless typed proposed-anchor placement for absences.
**Verification.** If code moves: test that every `baton_index='absent'` finding yields `fallback_position=None` + manual queue, per product.md:144-145. If spec moves: §10 Spec Change Log entry; retitle the G4 test scope. (Both sides quoted; not adjudicating.)

### C3 — Off-slide elements render markers on the wrong screenshot; only the label downgrades

**Issue.** When an element's geometry doesn't fall inside any captured screenshot, the resolver *knows* it (`degenerate=True`) but still emits a mapping with the nearest slide and full element geometry; the renderer then clamps the rect onto that wrong slide.
**Evidence.** [v2_markers.py:704-723](../../scripts/report/v2_markers.py) (`e_index_lookup_offslide` keeps `baton_element_index` + nearest `slide`); v2_markers.py:1032-1123 (renderer falls through to the element-rect block and clamps `cx/cy` into the slide); [review_state.py:1121-1135](../../scripts/assembly/review_state.py) maps it to `fallback-absence` — a label only. Verifier reproduced a wrong-slide marker empirically. Spec: *"**Wrong / wrong-page placement is the worst outcome** — a hard violation, worse than a blank"* (product.md:142-143).
**Severity.** Critical — this is the literal wrong-page placement class, produced knowingly.
**User impact.** A finding about (say) a footer element renders its box on whatever screenshot is nearest, on top of unrelated content.
**Effort.** S — treat `degenerate=True` like Strategy 4 (no position, manual queue).
**Verification.** Test: an element whose `y` lies between captured viewports yields no rendered marker + `needs-manual-marker`. Spec clause §4.2 (product.md:142-145).

### C4 — v1 renderer reads `finding-groups.json` without the device suffix the writer adds → literal `(not found)` Priority Path entries on non-laptop v1 renders

**Issue.** The writer emits `finding-groups-{device}.json` for every device except laptop; the v1 renderer hard-codes the bare name. On `--device desktop|mobile` v1 renders the file is never found, display indices stay positional, and Priority Path refs degrade to the exact `(not found)` string the spec names as a violation.
**Evidence.** [scripts/assembly/writer.py:25-26,541](../../scripts/assembly/writer.py) vs [scripts/report/html_builder.py:141](../../scripts/report/html_builder.py) (`fg_path = engagement_path / "finding-groups.json"`; contrast line 108-109 where the same file's priority-path loader DOES apply the suffix). Spec: *"**Hallucinated reference** — any finding or Priority Path entry pointing to a source/ref that does not resolve. (This is the `(not found)` Priority Path bug; it is a violation, not cosmetic.)"* (product.md:122-124). Two verifiers confirmed the chain end-to-end.
**Severity.** Critical — produces the spec's named violation string in client-facing output. (Reachability: v1 path runs when `synthesizer-emission-v1.json` is absent or `--legacy-v1` is passed.)
**User impact.** Priority Path entries in a v1-rendered report show "(not found)" instead of resolving to findings.
**Effort.** S — thread `device` into `_attach_display_indices` like its sibling loader.
**Verification.** Test: v1 render with `--device desktop` against a fixture with `finding-groups-desktop.json` asserts no `(not found)` in output and display indices attach. Spec clause §4.1 (product.md:122-124).

### C5 — v2 loader labels any unresolvable Priority Path ref "applies on the other device" without checking the other device; contract text claims refs are "dropped"

**Issue.** A canonical ref absent from the current device's findings is unconditionally labeled `applies_on_other_device=True` — the loader never checks the canonical view or the other device, so a hallucinated ref that escapes the prompt-level validation renders as a confident cross-device claim. The synthesizer contract meanwhile documents the opposite behavior ("drops f_refs that don't resolve"), so a maintainer reading the contract believes an allowlist exists at render time.
**Evidence.** [scripts/report/v2_loader.py:1022-1026,1153](../../scripts/report/v2_loader.py) (`actionable_refs` = current-device findings only; no canonical-view membership check); [components.py:350-356](../../scripts/report/templates/components.py) (renders the "applies on the other device — see that device's report" chip); vs [contracts/synthesizer-v2.md:256](../../contracts/synthesizer-v2.md): *"The render-time filter … drops f_refs that don't resolve to a heading on the current device."* Spec: §4.1 hallucinated-reference violation (product.md:122-124).
**Severity.** Critical — a nonexistent ref renders with an affirmative, wrong explanation instead of being blocked.
**User impact.** A client following the chip to "that device's report" finds nothing; the report asserted a cross-device fact that was never true.
**Effort.** S/M — check membership in the canonical view (both devices) before labeling; align synthesizer-v2.md:256 with whichever behavior the owner picks.
**Verification.** Test: a Priority Path story citing a ref absent from BOTH devices renders as blocked/flagged, not as "applies on the other device." Spec clause §4.1 (product.md:122-124).

### C6 — v1 markdown fallback parses Priority Path refs from prose with no allowlist

**Issue.** When the priority-path sidecar is absent or unreadable (the `except` swallows malformed JSON), the renderer falls back to regex-scraping `{cluster} F-NN` tokens out of `audit.md` with zero validation — re-opening the exact hole the sidecar+validator design closed.
**Evidence.** [html_builder.py:117-122](../../scripts/report/html_builder.py) (`except (OSError, IOError, json.JSONDecodeError): pass` → `parse_priority_path(...)`); [parser.py:230-247](../../scripts/report/parser.py) (regex `([\w-]+)\s+F-?(\d+)`, no allowlist); [components.py:358-365](../../scripts/report/templates/components.py) emits `(not found)` for misses. Spec: §4.1 (product.md:122-124); also [contracts/priority-path-synthesis.md:15](../../contracts/priority-path-synthesis.md) requires validation failures to render a visible ERROR block instead.
**Severity.** Critical — silent degradation to an unvalidated parse path in client-facing output.
**User impact.** On a legacy/corrupted engagement, hand-edited or hallucinated refs flow into the rendered Priority Path unchecked.
**Effort.** S — surface the fallback loudly (ERROR block per the contract) and/or validate parsed refs against the findings set.
**Verification.** Test: malformed sidecar produces a visible error marker, not a silent markdown parse. Spec clauses §4.1 + priority-path-synthesis.md:15.

### C7 — v2 dedup merges silently discard loser findings' citations/anchors, and the cross-device attribution code is dead (key-shape mismatch)

**Issue.** Two defects in one merge helper. (a) `_absorb_losers` forwards only `merged_from`/`ethics_state`/`source_url`/`synthesis_hint` — the losers' `evidence_anchors`, `reference_citations`, `proposed_anchor`, `visual_evidence`, `confidence`, `tier` vanish without record. (b) The canonical view's `devices_present` augmentation reads `merge_record["winner"]/["loser"]` but the producer emits `{"reason","kept","merged_from"}` — every iteration `continue`s, so a finding merged across devices is reported as single-device in the manifest the synthesizer cites.
**Evidence.** [scripts/assembly/dedup.py:285-337](../../scripts/assembly/dedup.py) (the `replace()` call lists every carried field); [v2_loader.py:520-534](../../scripts/report/v2_loader.py) (reads keys that never exist — verifier reproduced live: a desktop+mobile page-scope merge yields `devices_present` missing the mobile leg). Spec: §0 *"never untraceable, never silently misleading"* (product.md:20-21); §4.1 findings must carry citations/anchors.
**Severity.** Critical — cross-device misattribution flows into `audit-{device}.md` headings and Priority Path; citation evidence silently narrows.
**User impact.** A finding that fired on both devices is presented as one-device; merged findings may show weaker sourcing than was actually collected.
**Effort.** M — fix the key shape (or delete the dead loop and derive `devices_present` from `merged_from`), and union loser anchors/citations on merge (pattern already exists at [pipeline.py:409-420](../../scripts/assembly/pipeline.py)).
**Verification.** Test: page-scope merge of a desktop Gold-cited + mobile Silver-cited finding yields `devices_present={desktop,mobile}` and the union of citations. Spec clauses §0 + §4.1.

### C8 — v2 pipeline writes no dedup audit trail (v1 wrote `dedup-review.json`; v2 writes nothing)

**Issue.** The v1 path persisted `{auto_merged, fuzzy_candidates}` per device so the operator could audit what collapsed and why; the v2 path computes the same data and discards it.
**Evidence.** [writer.py:530-535](../../scripts/assembly/writer.py) (v1 sidecar) vs [lead_prep.py:217-355](../../scripts/lead_prep.py) + [v2_loader.py:460-546](../../scripts/report/v2_loader.py) (v2 writes canonical-f-refs + manifest + dropped, never `auto_merged`/`fuzzy_candidates`). Spec: §0 traceability (product.md:20-22).
**Severity.** Critical (by the brief's rule: it removes the operator's ability to detect C7-class data loss; on its own it is a §0 traceability violation).
**User impact.** An operator cannot reconstruct raw-emission→canonical-F-NN without rerunning dedup; merge mistakes are invisible.
**Effort.** S — serialize the existing in-memory data alongside `canonical-frefs-dropped.json`.
**Verification.** Test: `lead_prep build-canonical-frefs` on a fixture with merges writes a dedup-review artifact listing them. Spec clause §0.

### C9 — Loader extras keyed by array position while findings carry `local_id` → silent citation/severity loss on mismatch

**Issue.** `raw_extras_by_local` is keyed by `enumerate(start=1)` array position, but looked up by the specialist-emitted `local_id` (schema constrains it only to 1..99 — no uniqueness, no sequence). Any emission whose `local_id`s don't equal array positions silently loses `reference_citations`/`proposed_anchor`/`change_type` and defaults `severity` to MEDIUM.
**Evidence.** [v2_loader.py:401-418 vs 474,491,496-497](../../scripts/report/v2_loader.py); [json_parser.py:388](../../scripts/assembly/json_parser.py); [schema/finding-v1.json:49-54](../../schema/finding-v1.json). Spec: §4.1 (every finding cited); §0.
**Severity.** Critical — a Gold-cited HIGH finding can render uncited at MEDIUM, distorting Priority Path ranking.
**User impact.** Citations vanish and severity understates with no warning, on an input the schema accepts as valid.
**Effort.** S — key the extras map by `local_id` (or validate `local_id == position` at parse and reject otherwise).
**Verification.** Test: an emission with `local_id`s `[2,1]` keeps each finding's citations and severity. Spec clause §4.1.

### C10 — Acquirer captures invisible elements: no `display`/`visibility`/`opacity`/`aria-hidden` filtering (the spec's named DOM-not-displayed class)

**Issue.** Element extraction filters only zero-size rects and out-of-viewport y; an element with `visibility:hidden`, `opacity:0`, or `aria-hidden=true` enters the baton as visible evidence. The acquirer workflow contract itself mandates the missing check.
**Evidence.** [scripts/acquire_url.py:130-152](../../scripts/acquire_url.py) (no computed-style consult) vs [workflows/acquire.md:558-563](../../workflows/acquire.md) (mandates `getComputedStyle` display/visibility + aria-hidden). Spec: *"**DOM-not-displayed** — a visibility-dependent claim that reflects raw markup rather than what is actually rendered"* is a named spec violation (product.md:118-120); rendered-state rule (product.md:51-53).
**Severity.** Critical — specialists can anchor findings to elements no user sees.
**User impact.** A finding (and its hotspot) about a hidden flyout/drawer/animation start-state presents as if it were on the visible page.
**Effort.** S — add the contract's own filter to `_build_elements_js`.
**Verification.** Test: fixture page with an `opacity:0` element → element absent from baton (or flagged `is_offscreen`). Spec clauses §2.2 + §4.1 DOM-not-displayed.

### C11 — Acquirer mutates the page before capture with no record: overlay force-removal logs nothing and `overlays_detected` is hard-coded empty; the animation force-reveal is similarly unsignalled and over-broad

**Issue.** `force_remove_blocking_overlays` removes/hides any element covering >10% of the viewport (twice, unconditionally) and returns only a count; the v1→v2 converter then writes `overlays_detected: []` always — so the "DOM was edited during capture" caveat the contract requires can never fire. The pre-capture reveal force-paints every `.scroll-trigger`/`[class*="animate--"]`/`[data-cascade]` element with `!important` overrides, which can render genuinely-hidden UI as visible, also unrecorded.
**Evidence.** [acquire_url.py:943-946](../../scripts/acquire_url.py) + [ecp_acquire_overlays.py:74-92](../../scripts/ecp_acquire_overlays.py) (returns `{removed: count}` only); [baton_v1_to_v2.py:248-253](../../scripts/baton_v1_to_v2.py) (`'overlays_detected': []` always); [acquire_url.py:674-700](../../scripts/acquire_url.py) (reveal + global `<style>` injection) — vs [workflows/acquire.md:253-268](../../workflows/acquire.md) (mandates per-overlay records with `dom_state_modified: true` so renderers can surface the caveat). Spec: rendered-state rule (product.md:51-53) + §0.
**Severity.** Critical — the captured evidence can differ from any real user's view with zero signal downstream.
**User impact.** Findings reason about a page state (overlay-free, all animations completed) the user never saw, presented as a normal capture.
**Effort.** M — log removed/revealed elements into `capture_state.overlays_detected` (the schema field already exists) and scope the reveal.
**Verification.** Test: a capture that fires force-removal yields non-empty `overlays_detected` with `dom_state_modified: true`. Spec clauses §2.2 + §0; contract acquire.md:253-268.

### C12 — Overlay dismissal blind-clicks the first button in dialogs — including newsletter "Subscribe"

**Issue.** `_DISMISS_ROUND` clicks the first matching button for selectors like `[class*="omnisend"] button`, `[role="dialog"] button`, `.modal button` with no aria/text semantics — in typical newsletter popups the first button is Subscribe. The text-constrained fallback runs only after the blind per-selector loop.
**Evidence.** [ecp_acquire_overlays.py:42-72](../../scripts/ecp_acquire_overlays.py) vs [workflows/acquire.md:222-228](../../workflows/acquire.md) (requires aria-label/text-semantic targeting). Spec: rendered-state rule (product.md:51-52).
**Severity.** Critical — the capture can put the page into a state (subscribed/consented) the user never reached, and hides the popup the audit should have flagged.
**User impact.** Findings about overlay UX vanish (the popup was "dismissed" by subscribing); side effects hit the client's live systems (a subscription signup from the audit).
**Effort.** S/M — apply the contract's text/aria constraints to every round.
**Verification.** Test (DOM fixture): a dialog whose first button is "Subscribe" and second is "✕" results in the close button being clicked. Spec clause §2.2; contract acquire.md:222-228.

### C13 — Configured-state capture ignores URL variant pinning — the cross-device different-SKU bug the contract was written to close is still open in code

**Issue.** `ecp_configurator` selects the first non-disabled option per select, ignoring `variant=`/`sku=` URL parameters, and records no `variant_id`/`variant_source` — so desktop and mobile can capture different SKUs (different price, different CTA), which is precisely the documented awdmods 2026-05-18 failure the acquire contract's Step 1d mandates preventing.
**Evidence.** [scripts/ecp_configurator.py:36-52,107-112](../../scripts/ecp_configurator.py) vs [workflows/acquire.md:311-323](../../workflows/acquire.md) (MUST select the URL-pinned variant on every device; record `variant_source`/`variant_id`; names the awdmods bug verbatim). Spec: single-page audit integrity (§2.1-2.2); §0.
**Severity.** Critical — cross-device pricing findings can compare different products silently.
**User impact.** "Desktop shows $399.50 but mobile shows $420.75" findings that are actually two SKUs, shipped to a client as a conversion problem.
**Effort.** M.
**Verification.** Test: given `?variant=123`, `_APPLY_JS` selects variant 123 on both devices and `configured_state.variant_source == "url-pinned"`. Contract acquire.md:311-323; spec §2.2.

### C14 — `occluded` flag is computed once at scroll-y=0 and copied to every section

**Issue.** Viewport occlusion is probed a single time before the scroll loop; every section row gets the same boolean. A banner blocking only the first frame falsely marks all later sections occluded (wireframe-rendering real screenshots); a late-appearing overlay falsely marks them clean.
**Evidence.** [acquire_url.py:947-951,1153](../../scripts/acquire_url.py) (single `read_viewport_state` call — grep confirms one call site) vs [workflows/acquire.md:363](../../workflows/acquire.md) (per-section >30% occlusion check). Spec: §2.2 rendered-state; the flag drives the renderer's screenshot-vs-wireframe switch.
**Severity.** Critical — either direction corrupts the visual evidence presentation.
**User impact.** Clean screenshots hidden behind wireframes, or occluded screenshots presented as clean evidence.
**Effort.** S — re-probe per scroll position.
**Verification.** Test: section rows carry per-position occlusion values when the probe sequence differs. Contract acquire.md:363; spec §2.2.

### C15 — Mobile DPR fallback is silently 1×: `dpr_fallback`/`dpr_requested`/`dpr_actual` never written despite schema requiring them

**Issue.** When only `chromium_headless_shell` is available, mobile captures land at 1× DPR; the acquirer records only the single observed `dpr` and never the required `dpr_requested`/`dpr_actual` split or `dpr_fallback: true` — downstream geometry assuming nominal 3× puts every mobile hotspot at ⅓ of its true position with no signal.
**Evidence.** [acquire_url.py:972,1240-1270](../../scripts/acquire_url.py) vs [workflows/acquire.md:88,117-119](../../workflows/acquire.md) and [schema/baton-v1.json:46-70](../../schema/baton-v1.json) (`dpr_requested` AND `dpr_actual` required); [baton_v1_to_v2.py:240-247](../../scripts/baton_v1_to_v2.py) reads a `dpr_fallback` key that is never written. Spec: §4.2 placement precision; §2.2.
**Severity.** Critical — systematic, silent 3× geometry error on affected machines.
**User impact.** Every mobile hotspot lands in the wrong place on an entire engagement, with nothing flagging why.
**Effort.** S — record requested vs actual DPR and the fallback flag.
**Verification.** Test: baton emitted under a 1×-actual capture carries `dpr_requested=3, dpr_actual=1, dpr_fallback=true` and validates against baton-v1.json. Schema baton-v1.json:46-70; spec §4.2.

### C16 — Per-selector `slice(0, 10)` truncates evidence; the contract specifies a global 200-element cap with always-include preservation

**Issue.** Element capture keeps only the first 10 matches per selector, so densely repeated UI (36 product cards) is mostly invisible to specialists — making "missing below the fold" claims unfalsifiable from the on-disk evidence — while the contract specifies a 200-element global cap applied after capture with always-include selectors preserved.
**Evidence.** [acquire_url.py:129](../../scripts/acquire_url.py) vs [workflows/acquire.md:638](../../workflows/acquire.md). Spec: §4.1 falsifiable-claim requirement; §2.2.
**Severity.** Critical (lower confidence than C10-C15 on real-world frequency, but the truncation is code-enforced and unsignalled).
**User impact.** Findings about lower-page repetitions of an element can be neither supported nor checked against the baton.
**Effort.** S — capture-then-cap per the contract.
**Verification.** Test: a section with 30 matching elements retains them up to the global cap with always-include preserved. Contract acquire.md:638; spec §4.1.

### C17 — v1 renderer computes and exposes "projected lift" (§3.1: ECP "does not promise lift")

**Issue.** `_compute_metrics` computes `projected_lift` from severity counts (capped at 35) and spreads it into the render context; the committed v1 baseline HTMLs display "Projected Lift". The active v2 templates don't consume it, but the v1 path remains reachable (missing emission / `--legacy-v1`), and the metric exists nowhere in the spec.
**Evidence.** [html_builder.py:609-648,1004,1028](../../scripts/report/html_builder.py); `tests/baseline/*-desktop.html:1404` ("Projected Lift"). Spec: *"It never sees real traffic or conversion rate, does not run A/B tests, and **does not promise lift**. Output is research-backed *hypotheses*, not measured outcomes."* (product.md:84-86).
**Severity.** Critical on the v1 path (a fabricated quantitative promise in client-facing output); the v2 path is currently clean.
**User impact.** A v1-rendered report shows a percentage lift "projection" ECP has no basis to make.
**Effort.** S — remove the metric (or fence it off the render context).
**Verification.** Test: rendered v1 output contains no lift figure; grep-guard on templates. Spec clause §3.1 (product.md:84-86).

### C18 — The ethics voice contract instructs *against* the hedging the spec mandates for ADJACENT legal claims; the canonical hedge phrase exists nowhere but the spec

**Issue.** §4.1 requires any law cited in an Adjacent finding to be hedged ("may implicate [law] — verify") and calls misquoted/over-applied law the highest-bar violation. The ethics-subagent voice contract instructs the opposite — *"be direct about regulatory exposure. Avoid hedging ('may potentially be considered' → 'is')"* — without carving out ADJACENT findings; no code, schema, regex, or test checks hedge phrasing anywhere; the literal phrase "may implicate" appears in zero files other than product.md:133; and a committed test fixture already contains an ADJACENT finding with unhedged law text.
**Evidence.** Spec: product.md:120-121 + 131-133 (verbatim above). Contract: [contracts/ethics-subagent-v2.md:184-188](../../contracts/ethics-subagent-v2.md). Repo-wide grep: `may implicate` → 1 match (product.md:133). Fixture: `tests/fixtures/v2_engagement_with_adjacent_ethics/ethics-findings.json:48-50`. Renderer prints prose verbatim ([components.py:415-468](../../scripts/report/templates/components.py) preserves only the label pill).
**Severity.** Critical — the pipeline is steered toward shipping a hard-fact legal accusation in the spec's own highest-bar violation class.
**User impact.** A client reads "this violates [law]" on a borderline case the spec required to be hedged — with the operator's professional name attached.
**Effort.** S for the contract fix (add the ADJACENT carve-out + canonical hedge template); M to add a hedge-lint canary on ADJACENT prose.
**Verification.** Contract grep-guard test (ADJACENT sections of ethics-subagent-v2.md contain the hedge rule); canary: ADJACENT finding whose prose cites a law without hedge phrasing fails. Spec clauses §4.1 (product.md:120-121, 131-133).

## High

### H1 — Frozen build family (plan/review/build, quick-scan, compare, resume) is still marketed as canonical across the runtime-loaded contracts

**Issue.** §5 freezes the four modes and says they "may not be invoked, marketed, or relied upon as canonical." Invocation conforms (no skills/commands exist). But the contracts the audit lead loads at every invocation still present them as live siblings: full flag-matrix columns and per-flag "Supported by: /ecp:build …" sections, the lead-discipline consent chain "`/ecp:audit` → … → plan → … → review → … → build", team-naming tables, device defaults, and `--ab-scaffold`/`--ab-tool` flags that describe generating an A/B test scaffold from `/ecp:audit` (offending §3.1 separately). The meta.json template every audit writes carries `compare_target`/`quick_scan`/`plans_queue`/`screenshot_input`. The concurrent Codex audit's P0-1 found the same drift class and adds that the SKILL's runtime load order still imports v1/Agent-Teams-era files (`team-lifecycle.md`, `audit-assembly.md`, `audit-reconciliation.md`, `synthesizer-subagent.md`, `progress-comparison.md`).
**Evidence.** Spec: product.md:70-78 (audit "stops"; plan→review→build frozen), 155-161 ("may not be invoked, marketed, or relied upon as canonical"). Code/contracts: [contracts/lead-discipline.md:17-20](../../contracts/lead-discipline.md); [contracts/flags.md:13-29,39-46,217-236,244-287](../../contracts/flags.md); [contracts/meta-schema.md:3](../../contracts/meta-schema.md); [templates/meta.json.template:22-27](../../templates/meta.json.template); loaded at runtime per [skills/audit/SKILL.md:41-59](../../skills/audit/SKILL.md). **Counterpoint the owner must weigh:** §7 (product.md:183-198) freezes the flag matrix and the meta.json schema *as shared contracts precisely so frozen modes stay downstream consumers* — one verifier refuted the flag-matrix-columns claim on exactly that basis. The divergence that survives regardless: lead-discipline's plan→build consent chain and the `--ab-scaffold` description are *behavioral instructions to the live lead*, not dormant interface rows.
**Severity.** High — spec divergence in runtime-loaded prompt contracts; it has not been shown to produce a wrong audit result (the SKILL's own "stops" instruction currently wins), but it is exactly the "lead pulled onto mutually exclusive paths" hazard.
**User impact.** Worst case: an audit lead, mid-run, offers or attempts a frozen mode/post-audit phase; best case: none, today.
**Effort.** M — this is the **already-deferred v1/Agent-Teams contract-reword sweep** from the 2026-06-08 handoff; this finding scopes it precisely.
**Verification.** Grep-guard tests: lead-discipline/flags contain no live-voiced plan→review→build chain for `/ecp:audit`; a G21-style non-existence guard for frozen-mode invocation surfaces. Spec clauses §2.4, §5, §3.1.

### H2 — Legal citation integrity is enforcement-free: `source_url` accepts any well-formed URI; the vacated-rules tracker is documentation-only

**Issue.** The contract says the ethics subagent must copy `source_url` verbatim from the Source Registry; in code the schema checks only `format: uri, maxLength: 512`, the canary fails only on *missing* URL or self-cite filler, and nothing prevents citing the three vacated rules the reference library itself tracks as "do not cite as live authority."
**Evidence.** [schema/finding-v1.json:351-356,480-495](../../schema/finding-v1.json); [canary_checks.py:215](../../scripts/assembly/canary_checks.py); [contracts/ethics-subagent-v2.md:36-46](../../contracts/ethics-subagent-v2.md); [references/ethics-gate.md:11-19](../../references/ethics-gate.md). Spec: §4.1 highest-bar law class (product.md:120-121); §7 ethics gate frozen contract.
**Severity.** High — requires a model error to fire (vs C18 where the contract steers toward the error), but when it fires it ships the highest-bar violation class.
**User impact.** A BLOCK/ADJACENT finding can cite an invented URL or a vacated rule as live authority and pass every gate.
**Effort.** M — registry allowlist check + vacated-URL blocklist in the citations canary.
**Verification.** Canary test: ethics finding with a non-registry `source_url` (or a tracker-listed vacated URL) fails `run_all_canaries`. Spec clause §4.1; contract ethics-subagent-v2.md:36.

### H3 — §8's "absolute guardrail" on ECP's own output has no implementation surface at all

**Issue.** The ethics gate's guardrail role — ECP must never *recommend* fake urgency, hidden fees, deceptive defaults, review manipulation, or any dark pattern, **even if instructed to** — exists only as the spec sentence. `ethics-gate.md` is structured entirely as a page-detector ruleset; no contract clause, schema rule, scan, or test addresses ECP's own recommendation text; cluster specialists are explicitly told not to read the ethics gate at all.
**Evidence.** Spec: product.md:213-216. [references/ethics-gate.md:88-122,720-735](../../references/ethics-gate.md) (detector framing; the OVERRIDE RULE is generic guidance, not a guardrail); [contracts/specialist-prompt-v2.md:80](../../contracts/specialist-prompt-v2.md) ("Do not read the full ethics-gate"). Coverage sweep: zero tests (see F-M2).
**Severity.** High — missing spec-mandated control; firing requires model misbehavior, but the spec's word is "absolute" and "even if instructed to" implies prompt-injection resilience that nothing provides.
**User impact.** A drifted prompt or adversarial page content could put a dark-pattern recommendation into a client deliverable with no net underneath.
**Effort.** M — a deterministic dark-pattern lint over `recommendation`/Priority Path text (the BLOCK detector vocabulary in ethics-gate.md is reusable) wired into `run_all_canaries`.
**Verification.** Canary test: an emission whose recommendation says "add a countdown timer that resets per visit" fails. Spec clause §8 (product.md:213-216).

### H4 — §6 manual verification steps are honor-system: promotion runs unconditionally for any non-`--auto` caller

**Issue.** The gate's hard half is real (`AutoPromotionError` under `--auto`, test-pinned). But steps 1-3 (re-check live site; follow **every** legal/ethics citation; finalize placement) are docstring text: `set_client_verified` takes no attestation, reads no review-state, consults no placement QA — `--mark-client-verified` promotes regardless.
**Evidence.** [scripts/assembly/report_state.py:53-83](../../scripts/assembly/report_state.py); [generate-report.py:157-170](../../scripts/generate-report.py); [contracts/report-export.md:60-73](../../contracts/report-export.md) (weak-placement count is surfaced informationally only). Spec: product.md:171-179.
**Severity.** High — spec divergence. (The spec arguably *intends* a manual pass to stay manual; whether promotion should mechanically consume the placement-QA/citation signals is an owner call. Both sides noted.)
**User impact.** A rushed operator can promote a report with unplaced hotspots and unverified legal citations; nothing resists.
**Effort.** S/M — e.g. refuse promotion while `needs-manual-marker` markers remain unless `--force`, and record an attestation blob.
**Verification.** Test: promotion with a non-empty manual-placement queue fails without an explicit override. Spec clauses §6 steps 1-3 (product.md:174-176) + §4.2.

## Medium

### M1 — The two-runner blind spot: `unittest discover` silently misses 91 declared tests, including the highest-stakes §4.1/§4.2 guards; nothing enforces running both

**Issue/Evidence/Impact.** Full data in Sweep 2 above (runner outputs, per-file classification, the mixed-file case, the npm-chain gap, the fixture-skip triple-invisibility, no CI).
**Severity.** Medium — coverage/process gap (the canonical pytest runner does run everything).
**User impact.** A developer (or agent) who runs only `unittest discover` ships changes with the placement-taxonomy, fref-contract, determinism, and ethics-preservation guards unexecuted — exactly how the post-migration drops documented in `docs/conformance-gaps.md` happened.
**Effort.** S — a pre-flight guard test in the unittest-visible set that asserts pytest collection count ≥ a floor (or a `conftest.py`/CI note); adding `smoke:editor-server` to `npm test`.
**Verification.** Run `python -m unittest discover` after introducing a deliberately broken pytest-only test: the guard must fail. Spec clause: §0 (process integrity); CLAUDE.md "run BOTH runners".

### M2 — Twenty-one spec clauses have no test coverage at all

**Issue/Evidence.** The consolidated table in Sweep 2 (each row carries the spec clause verbatim or by line). The standouts: §4.2 absence-always-blank (untested because code does the opposite — see C2), the §4.1 law-exactness/hedging class (untested, see C18/H2), §5 frozen-mode non-invokability (no G21-style guard), §2.3 cluster-set pin, the `finding-v1.json:602-631` rendered-state allOf branch (schema exists, never exercised), and fabrication-with-no-baton (rule self-skips).
**Severity.** Medium — coverage gaps.
**User impact.** Regressions in these clauses ship without a red test.
**Effort.** M cumulative; each individual pin is S.
**Verification.** Each new test maps 1:1 to the clause listed in its row.

### M3 — "CRITICAL severity is reserved for ethics" is contract prose; the schema accepts CRITICAL on any cluster

**Issue.** Three contract files state cluster specialists never emit CRITICAL; `finding-v1.json` has no allOf restricting it, so a specialist emitting CRITICAL on `pricing` passes validation and inflates Priority Path weighting.
**Evidence.** [contracts/ethics-subagent-v2.md:32,154-156](../../contracts/ethics-subagent-v2.md); [contracts/specialist-prompt-v2.md:150](../../contracts/specialist-prompt-v2.md); [schema/finding-v1.json:221-225](../../schema/finding-v1.json) (plain enum).
**Severity.** Medium — enforcement gap on a contract-internal rule (the spec itself doesn't state it).
**User impact.** Severity inflation can distort ranking if a specialist drifts.
**Effort.** S — schema allOf: `severity=CRITICAL` ⇒ `cluster=ethics`.
**Verification.** Schema test: non-ethics CRITICAL emission fails validation. Contract ethics-subagent-v2.md:155; spec §7 (finding schema frozen contract).

### M4 — §7 freezes "Plan / review / build-log formats" but no such artifact exists in the repo

**Issue.** The frozen-contracts list names formats whose defining artifact is absent (dispatch-contract.md explicitly says the workflow sources are "not part of this repo"); a future unfreeze has nothing to conform to. Whether the formats should live here or in the archive (§9 quarry) is the owner's call — both sides quoted.
**Evidence.** Spec: product.md:193. [contracts/dispatch-contract.md:118](../../contracts/dispatch-contract.md); Glob across schema/, contracts/, workflows/ confirms absence; `schema/review-state-v1.json` is the hotspot editor's state, not the build-family review format.
**Severity.** Medium.
**User impact.** None today; rework risk at unfreeze time (the exact "zero rework" §7 promises).
**Effort.** S (pointer doc to the archived formats) or M (copy formats into contracts/).
**Verification.** §7 list resolves 9/9 to on-disk artifacts. Spec clause product.md:193.

### M5 — "Hypotheses, not measured outcomes" framing exists only in the footer disclaimer; the synthesizer voice contract pushes the other way

**Issue.** §3.1 frames output as research-backed *hypotheses*. The word appears in no contract or prompt; the synthesizer contract instructs rewriting specialist hedges into direct action verbs ("could/may want to/consider" → strongest defensible verb). The test-locked footer disclaimer carries the qualification, but body prose is steered confident.
**Evidence.** Spec: product.md:84-86. [contracts/synthesizer-v2.md:42,48,83](../../contracts/synthesizer-v2.md); [html_structure.py:258](../../scripts/report/templates/html_structure.py) + [tests/test_report_disclaimer.py](../../tests/test_report_disclaimer.py).
**Severity.** Medium (verifier confidence medium; the disclaimer is real mitigation).
**User impact.** Clients may read directive certainty the evidence tier doesn't support.
**Effort.** S — one synthesizer-contract clause distinguishing action-voice from outcome-claims.
**Verification.** Contract grep-guard; spot-check fixture renders. Spec clause §3.1 (product.md:85-86).

## Low

### L1 — Untracked `AGENTS.md` (Codex-voiced operator doc) appeared in the working tree mid-audit

**Issue.** A byte-level copy of CLAUDE.md with "Claude"→"Codex" substitutions ("This repo is a Codex plugin"; "`Codex --plugin-dir …`"; "restart Codex") was created at 2026-06-09 18:36:47, untracked. As operator guidance it contradicts §8 ("Claude Code is the only runtime in this repo") and its commands don't exist. Provenance: the concurrent Codex session (see header note); verified not written by this audit's agents.
**Evidence.** `git status` → `?? AGENTS.md`; file timestamps; AGENTS.md:38-41,51-55 vs product.md:204-209.
**Severity.** Low — untracked, so the committed repo conforms; flagged because (a) something is writing into the working tree during audits, and (b) if ever committed it becomes an H-class divergence.
**User impact.** An operator following it would run nonexistent commands.
**Effort.** S — owner decides: delete, or keep-and-fix (an AGENTS.md that says "this is a Claude Code plugin; Codex is archived per §8" would be conformant).
**Verification.** `git status` clean of it, or a committed version consistent with §8. Spec clause §8 (product.md:204-209).

### L2 — README "Known limitations" still flags the Windows eval-mangling bug as the current top fix target

**Issue.** README says `acquire_url.py` "can fail to acquire large pages because `agent-browser eval` mangles long inline JS args on Windows. This is the current top fix target" — but the base64 eval guard (G12/G27) landed, is test-pinned, and CLAUDE.md already suspects the README note is stale.
**Evidence.** [README.md:91-93](../../README.md) vs `_eval_args`/`-b` base64 path in [acquire_url.py](../../scripts/acquire_url.py), [tests/test_eval_encoding.py](../../tests/test_eval_encoding.py), [tests/test_acquire_eval_guard.py](../../tests/test_acquire_eval_guard.py).
**Severity.** Low — §9 requires README conform to reality; this is doc drift.
**User impact.** Misleading triage signal for the next session.
**Effort.** S.
**Verification.** README reflects the guard; spec clause §9 authority direction.

### L3 — `docs/conformance-gaps.md` G16 entry cites regression files by the wrong names

**Issue.** The G16 entry references `tests/test_g19_canonical_view_surfaces_drops.py` and `tests/test_g19_clusters_represented_canary.py`; the actual files are `test_g16_*`.
**Evidence.** docs/conformance-gaps.md:652-656 vs the tests/ directory listing.
**Severity.** Low.
**User impact.** A reader hunting the regression tests greps the wrong names.
**Effort.** S.
**Verification.** Names match on disk.

### L4 — Sweep 3's diagnosed defect does not exist on this machine (premise contradicted; fix withheld)

**Issue.** As detailed in Sweep 3: no stale `/ecp:audit` pointer exists; the archived plugin was already uninstalled here (only an orphaned, unreferenced v1.4.1 cache payload remains); the plugin loads current code from this repo via `--plugin-dir`. The brief's instruction for this case — record, don't fix — was followed.
**Evidence.** Sweep 3 items 1-5 (config file contents, backup filenames, live `claude --plugin-dir … plugin list` output).
**Severity.** Low — remaining items are hygiene (orphaned cache dir; stale CLAUDE.md:45-55 guidance for this box).
**User impact.** None on this machine; the work box may still need the documented uninstall.
**Effort.** S (cache delete + CLAUDE.md note), pending owner greenlight since it's outside this session's authorization.
**Verification.** Cache dir absent; `claude plugin list` unchanged; `--plugin-dir` load still v1.0.0. Spec clause §8 (plugin loads straight from the repo).

---

# Appendix — Unverified hunches / refuted-on-materiality

Items that are algorithmically real but failed adversarial verification on reachability or materiality. Not ranked; recorded so silence is informative.

1. **`placement_repair.finalize()` promotes `--confirmed` refs to `exact-selector` with no stored proof.** Real code behavior ([placement_repair.py:228-233](../../scripts/report/placement_repair.py)), but refuted on materiality: the intended caller is the vision-vote workflow (`.claude/workflows/ecp-visual-qa.js:117-157`) which supplies the provenance, and the editor's own operator promotion has identical semantics. Watch item: nothing *prevents* a hand-rolled CSV call.
2. **`load_v2_priority_path` silently discards refs that fail its regex** ([v2_loader.py:1002-1010](../../scripts/report/v2_loader.py) — no `missing_refs` entry, no counter). Split verdict: unreachable under conforming inputs because `schema/synthesizer-emission-v1.json:145` is strictly tighter than the loader regex; reachable only via alias-map corruption or a skipped validate step. Cheap hardening if touched anyway.
3. **Screenshot tiling leaves uncaptured bands on very tall pages** (`_plan_scroll_ys` caps at 6/12 shots; spacing then exceeds viewport height — math verified at [acquire_url.py:748-773](../../scripts/acquire_url.py); the docstring's "contiguous" claim is wrong past the cap and `tests/test_acquire_scroll_tiling.py` never exercises the cap-binding regime). Refuted as a *spec* divergence; recorded as a docstring bug + test-coverage gap.
4. **Corrected agent error (excluded from matrix counts as flagged):** one §7 mapper claimed `citations/sources.md` does not exist; it does — verified directly. The §7 row stands as conforms.

---

# Recommendation Layer

## Quick Wins — one greenlightable batch (all S-effort, low-risk, code-true-up; no spec adjudication needed)

1. **C4** v1 `finding-groups` device suffix (one-line threading fix) — kills a literal `(not found)` source.
2. **C6** loud ERROR on sidecar-fallback parse (the contract already specifies it).
3. **C8** serialize the v2 dedup-review sidecar (data already in memory).
4. **C9** key loader extras by `local_id`.
5. **C3** blank the `e_index_lookup_offslide` path instead of rendering.
6. **C10** add the contract's own visibility filter to element extraction.
7. **C14** per-scroll occlusion probe.
8. **C15** record `dpr_requested`/`dpr_actual`/`dpr_fallback`.
9. **M3** schema allOf restricting CRITICAL to ethics.
10. **L2 + L3** doc true-ups (README known-limitations; conformance-gaps test names).
11. **Sweep-3 hygiene** (orphaned v1.4.1 cache delete + CLAUDE.md stale-plugin note) — outside this session's authorization, included here for greenlight.

Each lands as its own tiny commit on `main` with its regression test, per repo convention.

## Recommended Fix Sequence

1. **Quick-wins batch above** — highest correctness-per-risk; every item is a code-vs-its-own-contract true-up, so no spec question blocks it.
2. **Adjudicate C2 (absence placement) + C1 (confidence gate) + H4 (gate strictness) in one sitting.** These are the §4.2/§6 design rulings everything else hangs off: either the spec's "always blank"/"~99.9%" stands (then schema, specialist contract, autofix, markers, and tests change together — plan as one focused branch) or the spec gets a §10 entry blessing typed proposed-anchor placement and defining the operational threshold. Don't start the code work before the ruling; C2 touches a schema-required field.
3. **Reference-chain integrity: C5, C7** (after the quick wins land C4/C6/C8/C9, these two close the remaining silent-loss paths; C7's union-merge has an in-repo pattern to copy).
4. **Acquisition truth batch: C11, C12, C13, C16, C17** — pairs naturally with the handoff's already-planned acquirer work (true-height probe C3, normalizations canary C4 from the 2026-06-08 handoff); one live `--plugin-dir` audit afterward per the handoff's standing instruction.
5. **H1 contract-reword sweep** — this is the deferred v1/Agent-Teams sweep, now precisely scoped by file:line; do it with grep-guard tests so it can't regress. Fold the synthesizer-v2.md:256 contract fix (C5's documentation half) in here.
6. **Ethics/legal enforcement: C18 (contract fix is S — do it early, with the sweep), then H2 + H3** (registry allowlist, vacated blocklist, dark-pattern lint — one canary-design session).
7. **Coverage backfill: M1 runner guard first** (it protects everything after it), then M2's pins opportunistically alongside whichever fix touches the same surface; M4, M5 last.

The owner reviews findings before any fix lands.

## Decline List — examined and judged fine (or not worth fixing)

- **§10 v1.1 amendments (all four)** — fully in force and test-pinned (29/29 conform: B0 path resolution, P1 dispatch restoration, screenshot naming, specialists-off-Agent-Teams + counter aliases).
- **§0/§1/§2.1-2.2 core identity and input contract** — 18/18 conform; URL-only mode selection (G7) held.
- **Ethics header pill** — hunt claim that it renders PASS despite ADJACENT findings was **refuted**: the pill is driven by `ethics_state` counting at `html_builder.py:778-781` + `html_structure.py:118-128`, verified by live regeneration.
- **Acquirer baton "missing v2 fields"** — refuted: `_upgrade_batons_to_v2` (acquire_url.py:1611-1613 → baton_v1_to_v2.py) emits the full v2 shape on disk.
- **"client-ready" vs "client-verified" naming** — internal to the spec's own §6 wording; code implements line 178's mandated value; behavior conforms.
- **Flag matrix carrying frozen-mode columns** — defensible as the §7 frozen shared contract working as designed; subsumed into H1's adjudication rather than standing alone.
- **§4.1 uniformity across clusters** — mapper's divergence claim refuted; the schema's required fields bind every cluster identically; ethics-only fields are spec-scoped to ethics.
- **`meta.json` frozen-mode fields (`compare_target` etc.) as a standalone finding** — deliberate shared-contract surface per the G7 decision and §7; the *narrower* live-voice issues are inside H1.
- **Engagement layout spread across contracts rather than one document** (s8-R3b) — works as-is; consolidation is optional tidiness, declined.
- **`tests/__init__.py` empty file** — load-bearing (enables `unittest discover` from root); leave it.
- **`citations/sources.md`** — exists and serves the citation URL resolver; a mapper's contrary claim was an agent error (appendix item 4).
- **Editor manual-placement ergonomics (§4.2 first-class tool)** — G5 fixes verified present (Place queue, smoke-tested round-trip); conforms.
- **`docs/2026-06-09-product-v1-adversarial-audit.md` (the concurrent Codex audit)** — reviewed; its two P0s correspond to C2 and H1 here; no contradictions with this document found; no action needed on it beyond the owner reading both.
