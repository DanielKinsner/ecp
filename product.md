# product.md — ECP Canonical Product Specification

**Spec version:** 1.0
**Baseline date:** 2026-05-26
**Status:** Authoritative. This file is the single source of truth for what ECP is and is not.

> Prior version language elsewhere in the codebase ("v5.0", "Round N", plugin
> `1.1.0`, etc.) is **historical and non-authoritative**. Where any code, README,
> CHANGELOG, skill, contract, or marketing claim disagrees with this file, **that
> artifact is wrong**, not this file. See §9 Governance.

---

## 0. Governing Principle

**Untrustworthy = unusable — even for an audience of one.**

ECP is a personal operator tool whose output is delivered to clients with the
operator's professional name attached. It is therefore held to a commercial-grade
trust bar despite having a single operator. The bar is not "never wrong" — it is
**"never untraceable, never silently misleading."** Every claim must be checkable;
every limitation must be visible. A polished output that quietly lies is a product
failure. A plain output that shows its work is the product working.

---

## 1. Identity

ECP is an **ecommerce conversion-psychology audit engine**: it analyzes a single
ecommerce page against an evidence-tiered research library and produces cited,
page-anchored findings, a prioritized action ranking, and an editable annotated
visual report.

- **Operator (who runs it):** Dan, via Claude Code.
- **Deliverable audience (who reads the report):** clients.
- **Canonical runtime:** Claude Code. (Codex is optional — see §8.)

The **audit** is the product. Everything else in the repo is either support for the
audit, frozen scope (§5), or a frozen contract (§7).

---

## 2. What ECP IS

### 2.1 The canonical capability — the audit

A single-page conversion-psychology audit driven from a **URL**.

### 2.2 Input

- **URL — the only canonical input.** A real audit reasons about the **rendered,
  visible page** (computed styles / what is actually painted), not raw markup.
- Screenshot-only and codebase inputs are **frozen** (§5).

### 2.3 Domain breadth (the moat)

The audit spans the **full cross-domain cluster set**. Breadth is the differentiator
and is canonical:

`visual-cta` · `trust-credibility` · `pricing` · `checkout-flows` ·
`performance-ux` · `product-media` · `category-navigation` · `content-seo` ·
`post-purchase` · `audience`

backed by the full evidence-tiered reference library (Gold / Silver / Bronze
credibility tiers). The trust invariants in §4 apply **uniformly** to every cluster;
no cluster is exempt.

### 2.4 Deliverable boundary

The canonical audit produces exactly three things and **stops**:

1. **Findings** — each cited (tiered) and anchored to a page element.
2. **Priority Path** — the prioritized ranking of findings.
3. **Visual report** — the annotated, self-contained HTML report, including the
   **hotspot edit tool** (§4.2).

The audit **stops before** generating an action plan, review, or code. `plan` →
`review` → `build` are the frozen build family (§5).

---

## 3. What ECP IS NOT

1. **NOT a measurement or testing tool.** It never sees real traffic or conversion
   rate, does not run A/B tests, and does not promise lift. Output is
   research-backed *hypotheses*, not measured outcomes.

2. **NOT an exhaustive technical auditor.** It is not a replacement for Lighthouse,
   axe, or an SEO crawler. It surfaces **obvious, high-signal, conversion-relevant**
   technical issues (e.g., JPEG where WebP belongs) — but does not produce full
   technical breakdowns unless an issue is obvious.

3. **NOT legal or compliance advice.** Ethics/legal citations are **informational**,
   hedged when borderline ("adjacent", §4.1), and are **never** a compliance
   certification or legal opinion. Legal rigor is held as high as possible, and legal
   findings are human-verified before client delivery (§6).

4. **NOT a crawler or autonomous fixer.** One URL per engagement (no site-wide
   crawl). It never edits the operator's or client's code (build is frozen, §5) and
   never acts without operator review.

---

## 4. Trust Invariants

Trust is enforced in two independent layers. A failure in either layer is a **spec
violation** regardless of how good the other layer looks.

### 4.1 Content layer — is the *finding* valid?

A finding is valid **if and only if** it carries a **tiered citation**, a concrete
**ELEMENT anchor** locating it on the page, and a **falsifiable claim**. Trust here
means *verifiable*, not *infallible*: a wrong-but-checkable finding is in-spec; an
untraceable finding is not.

**Spec violations (must not ship):**
- **Fabrication** — a finding about an element that does not exist on the page.
- **DOM-not-displayed** — a visibility-dependent claim that reflects raw markup
  rather than what is actually rendered. (Retired by the rendered-state rule, §2.2.)
- **Misquoted / over-applied law** — *highest bar.* Legal claims must be exact, or
  explicitly hedged. Citing a law as hard fact when it is not is a violation.
- **Hallucinated reference** — any finding or Priority Path entry pointing to a
  source/ref that does not resolve. (This is the `(not found)` Priority Path bug; it
  is a violation, not cosmetic.)

**Tolerated (in-spec):**
- **Slight overlap / overclaim** across granular findings — "almost healthy";
  bounded by dedup, not eliminated.

**Feature (must be preserved, never "fixed" away):**
- **Adjacent ethics findings** — borderline ethics cases are intentionally surfaced
  so the operator knows, **but** must be labeled `Adjacent`, and any law cited within
  them must be hedged as borderline ("may implicate [law] — verify").

### 4.2 Presentation layer — does the *report* point at the right thing?

Optimize for **precision over recall**: a *wrong* hotspot costs more than a *missing*
one. A false hotspot is net-negative; a blank is neutral.

- **Auto-place a hotspot only at ~99.9% confidence.** Below threshold → **leave it
  blank** for manual placement. Never auto-place a guess.
- **Wrong / wrong-page placement is the worst outcome** — a hard violation, worse
  than a blank.
- **Absence findings** (recommending an element that does not exist, e.g. "no sticky
  CTA") → **always blank**; the operator places or declines them manually.
- **The hotspot edit tool is a first-class part of the product.** The report is not
  finished when generated; it is finished when placement is finalized. The edit
  workflow must make creating, placing, and erasing hotspots **easy**. Manual
  placement is a designed step, not a defect.

---

## 5. Frozen Scope & Reserved Seams

Frozen items exist in the codebase/archive but are **out of the canonical product**
until explicitly unfrozen via a Spec Change Log entry (§9). They may not be invoked,
marketed, or relied upon as canonical. When unfrozen, they must re-prove conformance
to this spec and to the frozen contracts (§7).

**Frozen modes:** `quick-scan`, `compare`, `build`, `resume`.
**Frozen inputs:** screenshot-only, codebase.

**Reserved seams** (named so their later addition is deliberate, not a surprise):
- Codebase-mode audit.
- Audit → build-on-the-same-repo handoff.

---

## 6. Draft → Client-Ready Verification Gate

A generated report is a **DRAFT**. Promotion to **CLIENT-READY** requires a manual
verification pass by the operator:

1. Re-check the live site.
2. Follow **every** legal/ethics citation link and confirm relevancy.
3. Finalize hotspot placement (§4.2).

The report's state is tracked (e.g., `meta.json`: `draft | client-verified`).
**Automated/`--auto` execution can never mark a report `client-ready`.**

---

## 7. Frozen Contracts

These shared contracts are **frozen now** so that every present and future mode
conforms to one stable interface. Changing any of them requires a Spec Change Log
entry (§9). They are the reason deferring the frozen modes costs zero rework: the
modes are downstream consumers of these contracts.

- Finding schema (tiered citation + ELEMENT anchor + severity + falsifiable claim).
- Engagement artifact layout (`docs/ecp/<engagement-id>/`).
- `meta.json` schema (including the `draft | client-verified` state, §6).
- Plan / review / build-log formats (frozen alongside the build family).
- Flag matrix.
- Cluster routing + page-type defaults.
- Ethics gate (guardrail + detector, §4.1 / §8-adjacent).
- Reference-library format + Gold/Silver/Bronze tiering.
- Input contract (URL; rendered-state requirement, §2.2).

---

## 8. Runtime

- **Claude Code is the only runtime in this repo.** The audit is the `ecp` plugin,
  invoked as `/ecp:audit`. For live development the plugin loads straight from the
  repo with `claude --plugin-dir <repo>` — no cache copy, no stale-version step.
- **Codex (and Cursor) are archived, not shipped.** Both alternate runtimes were
  archived with the old repo and are reserved seams (§5): re-portable from the
  archive if ever wanted, but not part of the canonical product. Codex historically
  rendered the report with good precision — that edge is a target for the Claude
  renderer, not a reason to maintain a second runtime.

The **ethics gate is permanent and dual-role**: an **absolute guardrail** on ECP's
own output (it must never recommend fake urgency, hidden fees, deceptive defaults,
review manipulation, or any dark pattern — even if instructed to), and a **detector**
on the audited page (per §4.1).

---

## 9. Governance

**Authority direction.** `product.md` wins. Code, README, CHANGELOG, skills, and
contracts must conform to it. Where they disagree, they are bugs against the spec.

**Change rule.** Changes are deliberate and logged: every change requires a dated,
rationale'd entry in the Spec Change Log (§10). **Frozen scope (§5) unfreezes ONLY
via such an entry — never implicitly by someone writing code.** This is what lets the
product "bob and weave" when new problems arise without drifting: agility is allowed,
silent drift is not.

**Delivery vehicle.** This spec is the **constitution of a clean, pruned repo**, not
a patch on the existing one. The clean repo is a **prune-and-re-root, not a rewrite**:
working audit-path code and the full reference library are **moved, not
reimplemented**. (If "clean repo" ever turns into "rebuild the working pipeline" —
stop; that is the move failing.) Carry over only what serves the canonical audit,
trace the full audit dependency closure before migrating, and write a fresh README
and CHANGELOG (reusing the old where beneficial).

**Archive / quarry.** The existing repo becomes a **read-only archive** — never
deleted. It is the quarry from which frozen modes (§5) are mined back when unfrozen.
Git history, the build/compare code, and the postmortem CHANGELOG are shelved, not
lost.

**Baseline.** This is Spec v1.0. All prior version language is historical.

---

## 10. Spec Change Log

| Date | Version | Change | Rationale |
|------|---------|--------|-----------|
| 2026-05-26 | 1.0 | Initial canonical spec. Audit-only product; URL-only input; full cluster breadth; two-layer trust model; build/compare/quick-scan/resume + screenshot/codebase inputs frozen; draft→client-ready gate; Claude canonical / Codex optional; clean prune-and-re-root repo with this file as constitution. | Stop the documented drift between docs, code, and marketing; pin scope so future sessions stay "inside the lines." |
| 2026-06-01 | 1.1 | B0 / path-resolution contract: dispatch-contract.md now mandates the lead expand `${CLAUDE_PLUGIN_ROOT}` to absolute paths before dispatch; `scripts/test-specialist.py` `render_prompt`/`render_synthesizer_prompt` substitute it at render time. | Claude Code does not expand `${CLAUDE_PLUGIN_ROOT}` inside spawned-teammate prompts (Cursor did), so post-migration specialists received literal paths and failed their reference reads -> retries. |
| 2026-06-01 | 1.1 | P1 dispatch-contract restoration: re-added the multi-planner/relay dispatch structure (per-role + counter table rows, multi-planner subsection + dispatch row, SendMessage-row contradiction fix) and restored `contracts/relay-loop-protocol.md` + `contracts/multi-planner-protocol.md`. | The migration trim left line-69 self-contradictory and the multi-planner peer-negotiation contract absent, leaving v2 multi-planner dispatch unspecified. |
| 2026-06-01 | 1.1 | Screenshot naming contract (#26): per-section screenshots are `section-N.jpg` (desktop/laptop) / `section-N-mobile.jpg` (mobile) in both single- and multi-device runs; `acquire_url.py` no longer emits `{device}-section-N.jpg`. | acquire emitted device-prefixed names in multi-device runs that the validator regex and the v1->v2 converter rejected. |
| 2026-06-01 | 1.1 | Specialists off Agent Teams: cluster specialists migrated from Agent-Teams teammates to GA parallel one-shot subagents — the last teammate role removed from the audit path. `dispatch-contract.md` (per-role + how-to-dispatch rows drop `team_name`/`name`; rationale section retitled "Why specialists are one-shot subagents"; canonical counter `subagent_spawned_specialists`); `specialist-prompt-v2.md` / `ethics-subagent-v2.md` / `synthesizer-v2.md` (dispatch lines drop `team_name`/`name`, add `prompt=`); `skills/audit/SKILL.md` (team-create step deleted + Phase Order renumbered; full-parallel default + `--max-concurrent` fallback; fresh-re-dispatch recovery); `audit-reconciliation.md` (Steps 0/0b/0c recovery → fresh re-dispatch); `flags.md` (`--max-concurrent`); `trace-assertion-canary.md` + `scripts/assembly/canary_checks.py` + `determinism_gate.py` (canonical counter accepted at runtime; `team_spawned_specialists`/`team_spawned_auditors` retained as aliases); `team-lifecycle.md` (annotated dead-for-audit, retained for multi-planner). | Retire the last Agent-Teams (experimental) teammate role in the audit path per handoff §5b. File-presence collection (glob `cluster-{cluster}-{device}.json`) is transport-independent, so the lead loop is unchanged; only recovery delivery (SendMessage-bounce → fresh one-shot re-dispatch with the validation error embedded) and concurrency (waves-of-≤5 → full-parallel, `--max-concurrent N` rate-limit fallback) change. Aliases kept indefinitely so archived v1/v2 traces still validate. Follow-ups (out of scope): live `/ecp:audit` smoke + fixture regeneration; broad cosmetic `Task`→`Agent` rename of other roles. |
