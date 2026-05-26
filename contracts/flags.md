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
**Supported by:** `/ecp:audit`, `/ecp:build`, `/ecp:compare`, `/ecp:quick-scan`.

Skip all checkpoint pauses. Runs the full deterministic phase chain end-to-end without prompting:
- `/ecp:audit`: audit → plan → review → build.
- `/ecp:build`: plan → review → build.
- `/ecp:compare`: paired audit → comparison.
- `/ecp:quick-scan`: single-cluster scan + optional aggregate (no phase chain).

Abort with error if any interactive input would otherwise be required (e.g., ambiguous URL/file detection, missing required intake field).

Halts on a `BLOCK` verdict unless `--force` is also set. `--force` is only supported by audit and build; compare and quick-scan have no BLOCK verdict to force past.

In `--auto` mode, device selection defaults (where no `--device` flag is passed):
- `/ecp:audit`: defaults to `"mobile,laptop"` (dual-device, no prompt).
- `/ecp:compare`: defaults to `"laptop"` (single device, no prompt).
- `/ecp:quick-scan`: defaults to `"laptop"` (single device, no prompt).

In `--auto` mode, scope selection defaults (where no `--focus` flag is passed):
- `/ecp:audit`: defaults to `"standard"` (3-4 clusters, no prompt).
- `/ecp:audit` with `--deep`: defaults to `"comprehensive"` (all clusters, no prompt).
- Other skills: scope selector does not apply (compare uses its own routing, quick-scan is always 1 cluster, build has no acquisition).

**Quick-scan `--auto` note:** `--auto` still DOES NOT skip the URL fetch confirmation prompt (the "About to fetch {domain} — proceed?" check). That's a network-call consent check, not a workflow checkpoint — consent is always required before making an outbound network request unless the user has explicitly authorized the domain upstream.

---

## `--force`

**Type:** boolean (no value).
**Default:** false.
**Supported by:** `/ecp:audit`, `/ecp:build`.

Override BLOCK verdicts in `--auto` mode. No effect without `--auto`.

Use sparingly — BLOCK verdicts exist for a reason (ethics gate failures, structural assertion failures in the trace canary). Forcing past a BLOCK in `--auto` mode silences the safety rail.

---

## `--device`

**Type:** string (single device) or comma-pair (two devices, max 2).
**Values:** `mobile`, `laptop`, `desktop`.
**Default:** prompt user (URL mode only); `laptop` in `--auto` mode for compare + quick-scan; `mobile,laptop` in `--auto` mode for audit.
**Supported by:** `/ecp:audit`, `/ecp:compare`, `/ecp:quick-scan`.

Target device viewport(s) for acquisition and audit. The full device semantics (viewport dimensions, DPR, dual-device file naming, session isolation for parallel acquisition) live in `${CLAUDE_PLUGIN_ROOT}/contracts/device-semantics.md` — read that file for the canonical details.

Quick summary:
- `mobile`: 390×844, 3× DPR (via `agent-browser close` + `agent-browser set device "iPhone 14"`).
- `laptop`: 1440×900, 1× DPR.
- `desktop`: 1920×1080, 1× DPR.

Accepts a comma-pair (e.g., `--device mobile,desktop`) for dual-device mode. Max 2 devices per run. Dual-device mode produces separate per-device audit files (`audit.md` + `audit-{second_device}.md`) and separate per-device baton files (`baton.json` + `baton-{second_device}.json`).

For file path and description modes: device selection is skipped entirely (no viewport rendering).

---

## `--focus`

**Type:** cluster slug, domain alias, or comma-separated list (audit/build/compare). Single value only in quick-scan.
**Default:** page-type defaults from the routing table in `${CLAUDE_PLUGIN_ROOT}/contracts/cluster-routing.md`.
**Supported by:** `/ecp:audit`, `/ecp:build`, `/ecp:compare`, `/ecp:quick-scan`.

Override auto-selected clusters. The full routing table, page-type defaults, domain alias mapping, override rules, and legacy v4.x translation live in `${CLAUDE_PLUGIN_ROOT}/contracts/cluster-routing.md` — read that file for the canonical mapping.

**Accepted values:**
- **Direct cluster slugs (v5.0):** `visual-cta`, `trust-credibility`, `pricing`, `checkout-flows`, `performance-ux`, `product-media`, `category-navigation`, `content-seo`, `post-purchase`, `audience`.
- **Domain aliases (expanded to cluster sets):** `cro`, `seo`, `pricing`, `trust`, `visual`, `mobile`, `content`, `checkout`, `all`.
- **Legacy v4.x names:** `trust-conversion`, `context-platform`, `audience-journey` — silently translated to v5.0 equivalents on resume per `${CLAUDE_PLUGIN_ROOT}/contracts/cluster-migration.md`.

**Quick-scan restriction:** Quick-scan picks ONE cluster (it's the fast option), so `--focus` accepts only a single cluster slug or a single-cluster domain alias. Multi-cluster domains (`cro`, `visual`, `content`, `all`) print a warning and fall back to the first cluster in that domain's mapping. For multi-cluster coverage, use `/ecp:audit`.

**Aliases:** `--cluster` and `--clusters` accepted for backwards compatibility in every skill that supports `--focus`.

---

## `--deep`

**Type:** boolean (no value).
**Default:** false.
**Supported by:** `/ecp:audit`, `/ecp:build`, `/ecp:compare`, `/ecp:quick-scan`.

Route cluster auditors and builder to `opus` instead of the default `sonnet`. Use when:
- Comparing heavily-designed client-facing sites where extra reasoning depth is worth the cost.
- Auditing complex pages (configurators, multi-step checkout, heavily-designed landing pages).
- Producing client-facing output where the strongest possible quality signal matters more than speed.

**Default behavior (no `--deep`):** cluster auditors and builder run on `sonnet`. Faster, cheaper, good enough for most pages.

**Roles that stay on `opus` regardless of `--deep`:**
- Lead (coordinator)
- Planner
- Reviewer
- Multi-planner peers

These are the synthesis brain and quality gate — downgrading them would degrade audit quality. See `contracts/dispatch-contract.md` for the full per-role model assignment table.

**Quick-scan note:** `--deep` is rarely needed for quick-scan (the value prop is speed), but available for client-facing quick-scan runs.

---

## `--min-priority`

**Type:** string.
**Values:** `critical`, `high`, `medium`, `low`.
**Default:** — (show all findings) for audit/build; `high` for quick-scan.
**Supported by:** `/ecp:audit`, `/ecp:build`, `/ecp:quick-scan`.

Filter findings by minimum severity. Scale: `critical` > `high` > `medium` > `low`.

CRITICAL findings are always included regardless of filter setting (they cannot be hidden). A `--min-priority high` setting shows HIGH + CRITICAL; a `--min-priority medium` setting shows MEDIUM + HIGH + CRITICAL; and so on.

Quick-scan defaults to `high` (only HIGH and CRITICAL) because the value prop is 3-5 highest-impact findings, not exhaustive coverage.

---

## `--platform`

**Type:** string.
**Values:** `shopify`, `nextjs`, `opencart`, `woocommerce`, `generic`.
**Default:** auto-detect via `${CLAUDE_PLUGIN_ROOT}/contracts/platform-detection.md`.
**Supported by:** `/ecp:audit`, `/ecp:build`, `/ecp:quick-scan`.

Skip platform auto-detection and force a specific platform. Use when:
- Auto-detection is returning the wrong platform (e.g., a custom Next.js storefront misdetected as generic).
- You want to force `generic` mode for a platform you don't want to treat as first-class.
- Platform markers aren't visible in the DOM sample (some SPAs hydrate late).

If auto-detection produces a platform you don't want, `--platform generic` is always a safe fallback.

---

## `--visual` / `--no-visual`

**Type:** boolean (mutually exclusive).
**Default:** prompt the user at the end of the phase.
**Supported by:** `/ecp:audit`, `/ecp:build`, `/ecp:compare`, `/ecp:quick-scan`.

Control whether a visual report (annotated HTML with screenshot markers, dark-mode theme, scroll-sync) is generated after the phase completes.

- `--visual`: auto-generate the visual report without prompting.
- `--no-visual`: skip the prompt, markdown-only output. `meta.json` is still created silently.
- Neither flag: prompt the user after the phase completes. In `--auto` mode, skip the prompt (no visual report unless `--visual` is explicitly set).

---

## `--ab-scaffold`

**Type:** boolean (no value).
**Default:** false.
**Supported by:** `/ecp:audit`, `/ecp:build`.

After the plan phase completes, generate an A/B test scaffold file for the top recommendations. Pair with `--ab-tool` to target a specific existing testing tool.

Scaffold format depends on `--ab-tool` (if provided) or defaults to a generic test-harness YAML if no tool is specified.

---

## `--ab-tool`

**Type:** string.
**Values:** tool-specific (e.g., `optimizely`, `vwo`, `growthbook`, `convert`, `ab-tasty`). Value is passed through to the scaffold generator.
**Default:** — (generic scaffold).
**Supported by:** `/ecp:audit`, `/ecp:build`. No effect without `--ab-scaffold`.

Specify the A/B testing tool to target when generating the scaffold. The scaffold generator formats the output for the specified tool's experiment definition file format.

---

## `--engagement-id`

**Type:** string (engagement directory name, e.g., `2026-04-06-a3f7b1c2`).
**Default:** — (create new engagement).
**Supported by:** `/ecp:audit`, `/ecp:build`, `/ecp:compare`, `/ecp:resume`.

Target a specific past engagement instead of creating a new one. Used to:
- Resume an engagement from its last checkpoint (combined with `/ecp:resume`).
- Re-run a specific phase of an existing engagement (e.g., re-audit after editing a reference file).
- Continue a multi-PRD build where only some plans have shipped.

If the engagement directory doesn't exist, the skill aborts with an error.

**Schema version check:** engagements with `schema_version` > 2 are skipped with a warning (forward compatibility). See `${CLAUDE_PLUGIN_ROOT}/contracts/meta-schema.md` for the canonical schema.

---

## `--aggregate`

**Type:** boolean (no value).
**Default:** false.
**Supported by:** `/ecp:quick-scan` only.

Explicitly trigger the quick-scan multi-scan aggregate view when 2+ previous quick-scans exist for the same URL AND same device. Without this flag, the aggregate view is offered via an interactive prompt after the scan completes.

The aggregate view compares findings across historical scans of the same URL + device:
- **Consistent findings** (appeared in ≥ 2 scans) are labeled high confidence.
- **One-off findings** (appeared in exactly 1 scan) are labeled low confidence and may be noise.
- Aggregate only compares desktop-to-desktop or mobile-to-mobile — never cross-device. The device used is shown in the aggregate header.

Use cases:
- Running quick-scan on a page you've scanned before and want the aggregate view without answering the prompt.
- Automating multi-scan checks in `--auto` mode (where interactive prompts are skipped).

In `--auto` mode, the aggregate prompt is silently skipped unless `--aggregate` is explicitly set.

---

## `--ephemeral` (deprecated)

**Type:** boolean (no value).
**Default:** false.
**Supported by:** `/ecp:quick-scan` only (deprecated).
**Replacement:** `--no-visual`.

Historical flag. Currently behaves identically to `--no-visual`. When passed, prints a deprecation warning: `"--ephemeral is deprecated, use --no-visual"`.

Will be removed in a future version. Do not use in new work.

---

## Scope and flag precedence for `/ecp:audit`

When multiple flags affect cluster selection, this precedence order applies (highest wins):

| Priority | Mechanism | Effect |
|---|---|---|
| 1 (highest) | `--focus <clusters>` | Absolute override. Skips scope prompt entirely. Uses the specified clusters directly. |
| 2 | `--auto --deep` | Defaults scope to `comprehensive` (all page-type clusters). No prompt. |
| 3 | `--auto` (without `--deep`) | Defaults scope to `standard` (3-4 clusters). No prompt. |
| 4 (lowest) | Interactive scope prompt | Shown when no flags override. User picks a/b/c/d. |

**`--focus` always wins.** If `--focus pricing,trust` is set alongside `--auto --deep`, the audit runs only pricing and trust — not all clusters. Focus is the power-user escape hatch that bypasses all scope logic.

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
