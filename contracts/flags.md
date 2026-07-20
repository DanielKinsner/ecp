# CLI flag reference

Canonical documentation for every ECP CLI flag. Skills reference this file instead of documenting flags inline.

**Why this file exists:** Prior to Round 11, flags were duplicated across 4+ skill files and drifted. `--deep` was added to audit + build in Round 5 but missed in compare + quick-scan until Round 9. `--export-report` was documented but never implemented and shipped in two skill files until Round 9. This reference file is the single source of truth — every skill defers here.

**If you are adding a new flag or changing flag behavior:** update THIS file first. Update each skill's `<flags>` section to list only which flags the skill accepts (no inline re-documentation).

---

## Flag summary table

| Flag | Type | Default | audit | build | compare | quick-scan | resume |
|---|---|---|:-:|:-:|:-:|:-:|:-:|
| `--auto` | boolean | false | ✓ | ✓ | ✓ | ✓ | — |
| `--force` | boolean | false | ✓ | ✓ | — | — | — |
| `--device` | string / comma-pair | prompt | ✓ | — | ✓ | ✓ | — |
| `--focus` | cluster-slug / domain / comma-list | page-type default | ✓ | ✓ | ✓ | ✓ (single) | — |
| `--deep` | boolean | false | ✓ | ✓ | ✓ | ✓ | — |
| `--max-concurrent` | integer | all (unlimited) | ✓ | ✓ | — | — | — |
| `--min-priority` | `critical` / `high` / `medium` / `low` | — (audit/build) / `high` (quick-scan) | ✓ | ✓ | — | ✓ | — |
| `--platform` | `shopify` / `nextjs` / `opencart` / `woocommerce` / `generic` | auto-detect | ✓ | ✓ | — | ✓ | — |
| `--visual` | boolean | prompt | ✓ | ✓ | ✓ | ✓ | — |
| `--no-visual` | boolean | false | ✓ | ✓ | ✓ | ✓ | — |
| `--ab-scaffold` | boolean | false | ✓ | ✓ | — | — | — |
| `--ab-tool` | string | — | ✓ | ✓ | — | — | — |
| `--engagement-id` | string | — | ✓ | ✓ | ✓ | — | ✓ |
| `--aggregate` | boolean | false | — | — | — | ✓ | — |
| `--ephemeral` | boolean (deprecated) | false | — | — | — | ✓ (warns) | — |

Aliases: `--cluster` and `--clusters` are accepted as backwards-compatible aliases for `--focus` in every skill that supports `--focus`.

---

## `--auto`

**Type:** boolean (no value).
**Default:** false.
**Supported by:** `/ecp:audit` (live). The matrix row for `/ecp:build`, `/ecp:compare`, `/ecp:quick-scan` is a `product.md` §7 frozen interface contract — those modes are frozen per `product.md` §5.

Skip all checkpoint pauses. Runs the canonical audit end-to-end without prompting:
- `/ecp:audit`: audit only. The audit produces the three §2.4 deliverables (findings, Priority Path, visual report) and **stops** — it never chains into `plan` → `review` → `build` (those are frozen per `product.md` §5).
- `/ecp:build`, `/ecp:compare`, `/ecp:quick-scan`: frozen / reserved per `product.md` §5; the row exists as a §7 interface contract so an eventual unfreezing has one stable behavior to conform to. Not invokable from the canonical v1.2 audit pipeline.

Abort with error if any interactive input would otherwise be required (e.g., ambiguous URL/file detection, missing required intake field).

Halts on a `BLOCK` verdict unless `--force` is also set.

**Promotion gate:** `--auto` runs always leave `meta.json` `report_state` at `"draft"` and `reflection_state` at `"draft"`. Automated execution can **never** mark a report `client-verified` or a reflection `complete` — that's the operator's manual verification pass per `product.md` §6.

In `--auto` mode, device selection defaults (where no `--device` flag is passed):
- `/ecp:audit`: defaults to `"mobile,laptop"` (dual-device, no prompt).
- `/ecp:compare`, `/ecp:quick-scan`: frozen rows retained as `product.md` §7 contracts; the documented `"laptop"` default applies only if/when those modes are unfrozen via §10.

In `--auto` mode, scope selection defaults (where no `--focus` flag is passed):
- `/ecp:audit`: defaults to `"standard"` — every cluster relevant to the detected page type (per `product.md` §2.3 v1.2 and the standard table in `${CLAUDE_PLUGIN_ROOT}/contracts/cluster-routing.md`). No prompt. The legacy reduced-scope 3-4-cluster default tier is retired.
- `/ecp:audit` with `--deep`: scope is unchanged — `--deep` no longer changes scope (it stays at `"standard"`). `--deep` affects model selection and the visual-QA tier only (see the `--deep` section below). `"everything"` (all 10 clusters) is reached via `--focus all`, not via `--deep`.
- Other skills: scope selector does not apply (compare and quick-scan are `product.md` §5 frozen modes; build has no acquisition).

**Quick-scan `--auto` note (frozen):** retained as a §7 interface contract for the frozen quick-scan mode — when/if quick-scan is unfrozen, `--auto` must NOT skip the URL fetch confirmation prompt (the "About to fetch {domain} — proceed?" check). That's a network-call consent check, not a workflow checkpoint — consent is always required before making an outbound network request unless the operator has explicitly authorized the domain upstream.

---

## `--force`

**Type:** boolean (no value).
**Default:** false.
**Supported by:** `/ecp:audit` (live). The `/ecp:build` row is a `product.md` §7 frozen interface contract.

Override BLOCK verdicts in `--auto` mode. No effect without `--auto`.

Use sparingly — BLOCK verdicts exist for a reason (ethics gate failures, structural assertion failures in the trace canary). Forcing past a BLOCK in `--auto` mode silences the safety rail. `--force` does NOT bypass the `--auto` refusal in `set_client_verified` — the §6 promotion gate is absolute. See `${CLAUDE_PLUGIN_ROOT}/contracts/meta-schema.md` `report_state` for the full rule.

---

## `--device`

**Type:** string (single device) or comma-pair (two devices, max 2).
**Values:** `mobile`, `laptop`, `desktop`.
**Default:** prompt the operator (URL mode only); `mobile,laptop` in `--auto` mode for `/ecp:audit`. The `laptop` default for compare + quick-scan is retained as a §7 frozen-interface contract for those §5-frozen modes.
**Supported by:** `/ecp:audit` (live). The matrix row for `/ecp:compare`, `/ecp:quick-scan` is a §7 frozen interface contract.

Target device viewport(s) for acquisition and audit. The full device semantics (viewport dimensions, DPR, dual-device file naming, session isolation for parallel acquisition) live in `${CLAUDE_PLUGIN_ROOT}/contracts/device-semantics.md` — read that file for the canonical details.

Quick summary:
- `mobile`: 390×844, 3× DPR (via `agent-browser close` + `agent-browser set device "iPhone 14"`).
- `laptop`: 1440×900, 1× DPR.
- `desktop`: 1920×1080, 1× DPR.

Accepts a comma-pair (e.g., `--device mobile,desktop`) for dual-device mode. Max 2 devices per run. Dual-device mode produces separate per-device audit files (`audit.md` + `audit-{second_device}.md`) and separate per-device baton files (`baton.json` + `baton-{second_device}.json`).

URL is the only canonical input (`product.md` §2.2); file-path / description / screenshot source modes are frozen per `product.md` §5 — when those frozen modes appear elsewhere in this matrix, device selection is documented as skipped, but those rows are §7 frozen-interface contracts only.

---

## `--focus`

**Type:** cluster slug, domain alias, or comma-separated list.
**Default:** standard page-type defaults from the routing table in `${CLAUDE_PLUGIN_ROOT}/contracts/cluster-routing.md` (all clusters relevant to the detected page type, per `product.md` §2.3 v1.2).
**Supported by:** `/ecp:audit` (live). The matrix row for `/ecp:build`, `/ecp:compare`, `/ecp:quick-scan` is a §7 frozen-interface contract.

Override the standard auto-selected clusters. The full routing table, page-type defaults, domain alias mapping, override rules, and legacy v4.x translation live in `${CLAUDE_PLUGIN_ROOT}/contracts/cluster-routing.md` — read that file for the canonical mapping.

**Accepted values:**
- **Direct cluster slugs (v5.0):** `visual-cta`, `trust-credibility`, `pricing`, `checkout-flows`, `performance-ux`, `product-media`, `category-navigation`, `content-seo`, `post-purchase`, `audience`.
- **Domain aliases (expanded to cluster sets):** `cro`, `seo`, `pricing`, `trust`, `visual`, `mobile`, `content`, `checkout`, `all`.
- **Legacy v4.x names:** `trust-conversion`, `context-platform`, `audience-journey` — silently translated to v5.0 equivalents on resume per `${CLAUDE_PLUGIN_ROOT}/contracts/cluster-migration.md`.

**Quick-scan restriction (frozen):** retained as a §7 interface contract — quick-scan would pick ONE cluster, so `--focus` would accept only a single cluster slug or a single-cluster domain alias; multi-cluster domains (`cro`, `visual`, `content`, `all`) would print a warning and fall back to the first cluster in that domain's mapping.

**Aliases:** `--cluster` and `--clusters` accepted for backwards compatibility in every skill that supports `--focus`.

---

## `--deep`

**Type:** boolean (no value).
**Default:** false.
**Supported by:** `/ecp:audit` (live). The matrix row for `/ecp:build`, `/ecp:compare`, `/ecp:quick-scan` is a §7 frozen-interface row — those modes are frozen per `product.md` §5; the row exists so an unfreezing change set has one place to conform to.

**`--deep` has two effects in v1.2 — both orthogonal to scope:**

1. **Model selection.** Route the **cluster specialists, ethics subagent, and builder** to `opus` instead of their default `sonnet` (Sonnet 5).
2. **Visual-QA tier.** Escalate `ecp-visual-qa` from `standard` (1 vision verifier on flagged crops) to `deep` (3-verifier majority on flagged crops) when paired with `--visual`. See the `--visual` / `--no-visual` section below.

**`--deep` does NOT change cluster scope.** The canonical `--auto` scope is `"standard"` (every cluster relevant to the detected page type, per `product.md` §2.3 v1.2) — `--deep` leaves that unchanged. Operators who want all 10 clusters dispatched regardless of page type pass `--focus all` (the `everything` scope), not `--deep`.

Use `--deep` when:
- Producing client-facing output where the strongest possible reasoning signal on ethics + builder is worth the cost.
- Pairing with `--visual` and wanting the 3-verifier majority placement-QA gate.

**Default behavior (no `--deep`):** the cluster specialists, ethics subagent, and builder run on `sonnet` (Sonnet 5); the visual-QA tier with `--visual` is `standard` (1 verifier).

**Roles that stay on `opus` regardless of `--deep`:**
- Lead (coordinator)
- Synthesizer
- Planner
- Reviewer
- Multi-planner peers

These are the audit's reasoning roles — downgrading them would degrade audit quality. See `contracts/dispatch-contract.md` for the full per-role model assignment table.

---

## `--max-concurrent`

**Type:** integer.
**Default:** all (unlimited; dispatch all requested clusters in one wave).
**Supported by:** `/ecp:audit` (live). The `/ecp:build` row is a §7 frozen-interface contract.

Batch specialist subagent dispatch into concurrent waves of up to N agents. Use when:
- Resource-constrained environments (e.g., rate-limited API, shared compute quota, avoiding fork-bomb spike load).
- Network conditions favor fewer parallel streams over many.
- Observability/debugging requires serialization (though wave batching is orthogonal to that; use `--auto` for automated runs).

**Default behavior (no `--max-concurrent`):** Dispatch all cluster auditors and builder in one wave (full parallelism). Fastest wall-clock time.

**Example:** `--max-concurrent 5` for audit of 12 clusters (6 clusters × 2 devices) will dispatch in three waves: (1) auditors 1-5, (2) auditors 6-10, (3) auditor 11-12, then builder. Wave boundaries are transparent to the user — the lead waits for the entire batch to complete before the next phase.

**Fallback for throttling:** This flag is the lead's escape hatch when token/rate limits, fork-bomb concerns, or queue saturation would otherwise cause failures. Before adding hardcoded wave-batching logic, the lead tries `--max-concurrent` first.

---

## `--min-priority`

**Type:** string.
**Values:** `critical`, `high`, `medium`, `low`.
**Default:** — (show all findings) for `/ecp:audit`. The `high` default for quick-scan is retained as a §7 frozen-interface contract.
**Supported by:** `/ecp:audit` (live). The matrix row for `/ecp:build`, `/ecp:quick-scan` is a §7 frozen-interface contract.

Filter findings by minimum severity. Scale: `critical` > `high` > `medium` > `low`.

CRITICAL findings are always included regardless of filter setting (they cannot be hidden). A `--min-priority high` setting shows HIGH + CRITICAL; a `--min-priority medium` setting shows MEDIUM + HIGH + CRITICAL; and so on.

The quick-scan default of `high` (only HIGH and CRITICAL) is a frozen interface row — its rationale (3-5 highest-impact findings, not exhaustive coverage) applies only if/when quick-scan is unfrozen.

---

## `--platform`

**Type:** string.
**Values:** `shopify`, `nextjs`, `opencart`, `woocommerce`, `generic`.
**Default:** auto-detect via `${CLAUDE_PLUGIN_ROOT}/contracts/platform-detection.md`.
**Supported by:** `/ecp:audit` (live). The matrix row for `/ecp:build`, `/ecp:quick-scan` is a §7 frozen-interface contract.

Skip platform auto-detection and force a specific platform. Use when:
- Auto-detection is returning the wrong platform (e.g., a custom Next.js storefront misdetected as generic).
- You want to force `generic` mode for a platform you don't want to treat as first-class.
- Platform markers aren't visible in the DOM sample (some SPAs hydrate late).

If auto-detection produces a platform you don't want, `--platform generic` is always a safe fallback.

---

## `--visual` / `--no-visual`

**Type:** boolean (mutually exclusive).
**Default:** prompt the operator at the end of the audit.
**Supported by:** `/ecp:audit` (live). The matrix row for `/ecp:build`, `/ecp:compare`, `/ecp:quick-scan` is a §7 frozen-interface contract.

Control whether the annotated visual report (the third §2.4 deliverable — annotated HTML with screenshot markers, dark-mode theme, scroll-sync, and the hotspot edit tool) is generated after the audit completes.

- `--visual`: auto-generate the visual report without prompting.
- `--no-visual`: skip the prompt, markdown-only output. `meta.json` is still created silently.
- Neither flag: prompt the operator after the audit completes. In `--auto` mode, skip the prompt (no visual report unless `--visual` is explicitly set).

**Placement-QA tier mapping.** Every `--v2` render emits a deterministic, zero-cost Tier-0 Placement QA summary (`weak_placements` + `≥3-on-a-pixel` stacks) — this is the `free` tier and always runs. `--visual` additionally escalates the `ecp-visual-qa` vision gate (`.claude/workflows/ecp-visual-qa.js`) per device:

| Flags | Visual-QA tier |
|---|---|
| (none) / `--no-visual` | `free` (Tier-0 only, already in the render summary) |
| `--visual` | `standard` (1 vision verifier on flagged crops) |
| `--visual --deep` | `deep` (3-verifier majority on flagged crops) |

The vision tiers cost tokens and are an operator opt-in. **`--auto` never runs a paid tier** (it stays `free`), consistent with the draft → client-verified gate (`product.md` §6). See `${CLAUDE_PLUGIN_ROOT}/contracts/report-export.md` "Post-render placement QA" for the full procedure.

---

## `--ab-scaffold`

**Type:** boolean (no value).
**Default:** false.
**Supported by:** matrix row retained as a `product.md` §7 frozen interface contract. **NOT produced by the canonical `/ecp:audit`.**

**Status: frozen / reserved.** The canonical v1.2 audit produces exactly the three deliverables in `product.md` §2.4 — findings, Priority Path, visual report — and **stops**. It does not generate A/B test scaffolding (A/B tests are out of scope per `product.md` §3 #1: "It never sees real traffic or conversion rate, does not run A/B tests, and does not promise lift."). This flag is reserved for the frozen build family (`plan` → `review` → `build`, `product.md` §5) and will only become live if that family is unfrozen via a §10 Spec Change Log entry. Until then the flag is documented here so that an eventual unfreezing has one stable interface to conform to; passing it to `/ecp:audit` has no effect.

---

## `--ab-tool`

**Type:** string.
**Values:** tool-specific (e.g., `optimizely`, `vwo`, `growthbook`, `convert`, `ab-tasty`). Value is passed through to the scaffold generator referenced by the frozen `--ab-scaffold` flag above.
**Default:** — (generic scaffold).
**Supported by:** matrix row retained as a `product.md` §7 frozen interface contract. **NOT produced by the canonical `/ecp:audit`.**

**Status: frozen / reserved** (paired with `--ab-scaffold` above). No effect without `--ab-scaffold`, which is itself frozen — the canonical audit never produces A/B scaffolding. Documented only as a §7 interface row so the frozen build family has one stable shape to conform to if unfrozen.

---

## `--engagement-id`

**Type:** string (engagement directory name, e.g., `2026-04-06-a3f7b1c2`).
**Default:** — (create new engagement).
**Supported by:** `/ecp:audit` (live). The matrix row for `/ecp:build`, `/ecp:compare`, `/ecp:resume` is a §7 frozen-interface contract.

Target a specific past engagement instead of creating a new one. In the canonical `/ecp:audit` flow this is used to re-run a specific phase of an existing engagement (e.g., re-audit after editing a reference file). Resume into the frozen build family (`plan` → `review` → `build`) and multi-PRD continuation are frozen per `product.md` §5; if the engagement directory doesn't exist, the audit aborts with an error.

**Schema version check:** engagements with `schema_version` > 2 are skipped with a warning (forward compatibility). See `${CLAUDE_PLUGIN_ROOT}/contracts/meta-schema.md` for the canonical schema.

---

## `--aggregate`

**Type:** boolean (no value).
**Default:** false.
**Supported by:** matrix row retained as a `product.md` §7 frozen-interface contract for the §5-frozen `/ecp:quick-scan` mode. Not invokable from the canonical v1.2 audit.

The frozen behavior is preserved here as the §7 interface contract: when/if quick-scan is unfrozen, `--aggregate` would explicitly trigger a multi-scan aggregate view when 2+ previous quick-scans exist for the same URL AND same device; without it, the aggregate view would be offered via an interactive prompt after the scan. Aggregates compare same-device runs only (desktop-to-desktop or mobile-to-mobile, never cross-device), label findings that appear in ≥ 2 scans as high-confidence and one-off findings as low-confidence noise, and are skipped in `--auto` unless explicitly set.

---

## `--ephemeral` (deprecated, frozen)

**Type:** boolean (no value).
**Default:** false.
**Supported by:** matrix row retained as a `product.md` §7 frozen-interface contract for the §5-frozen `/ecp:quick-scan` mode. Not invokable from the canonical v1.2 audit.
**Replacement:** `--no-visual`.

Historical flag. Behaved identically to `--no-visual` and emitted a deprecation warning (`"--ephemeral is deprecated, use --no-visual"`) when passed. Retained as a §7 interface row only; will be removed if/when quick-scan is unfrozen and rebuilt against the v1.2 spec.

---

## Scope and flag precedence for `/ecp:audit`

When multiple flags affect cluster selection, this precedence order applies (highest wins):

| Priority | Mechanism | Effect |
|---|---|---|
| 1 (highest) | `--focus <clusters>` | Absolute override. Skips scope prompt entirely. Uses the specified clusters directly. `--focus all` resolves to the `everything` scope (all 10 clusters). |
| 2 | `--auto` (with or without `--deep`) | Defaults scope to `"standard"` — every cluster relevant to the detected page type (per `product.md` §2.3 v1.2 and `${CLAUDE_PLUGIN_ROOT}/contracts/cluster-routing.md`). No prompt. `--deep` does NOT change scope — it only changes model selection and the visual-QA tier. |
| 3 (lowest) | Interactive scope prompt | Shown when no flags override. Operator picks: a=`focused` (one cluster), b=`standard` (page-type-relevant, the canonical default), d=`custom` (operator-listed), e=`everything` (all 10). The pre-v1.2 reduced-scope tier (also previously called `standard`) is retired. |

**`--focus` always wins.** If `--focus pricing,trust` is set alongside `--auto --deep`, the audit runs only pricing and trust — not all clusters. Focus is the operator escape hatch that bypasses all scope logic.

**Override rules still apply after scope resolution.** Non-Western market, significant price display, and mobile-first device list overrides can ADD clusters to the resolved set but never REMOVE them, regardless of which scope was selected.

---

## Adding a new flag

When adding a new flag to one or more skills:

1. **Add the flag to this file first.** Include: name, type, default, supported-by list, behavior description, edge cases.
2. **Update the flag summary table at the top of this file.** Add a row with checkmarks for each supporting skill.
3. **Add the flag to each supporting skill's `argument-hint`** in the frontmatter. This is what Claude Code shows in autocomplete.
4. **In each skill's `<flags>` section, add the flag name to the "This skill accepts" list.** Do NOT re-document the behavior inline — point to this file instead.
5. **Run the drift grep** (`${CLAUDE_PLUGIN_ROOT}` — plan doc cheat sheet check #9) to verify no skill has re-documented the flag inline.

**Rationale:** Inline flag documentation drifts. A single canonical source prevents the Round 5 → Round 9 propagation gap from ever happening again.
