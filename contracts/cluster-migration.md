# Cluster migration — legacy slug translation

ECP has renamed cluster slugs twice — once in v5.0 (4 clusters → 10) and once in v1.1 (`mobile-performance` → `performance-ux`). Resumed engagements must translate stored cluster slugs to the current names so they remain resumable against the live pipeline. This reference is the single source of truth for both translation tables.

Prior to ECP v5.0.x the v4.x translation table was duplicated across 5 skill files (`audit`, `build`, `compare`, `quick-scan`, `resume`). Inconsistent updates would cause silent resume failures on old engagements, which is the highest-risk kind of drift — the user doesn't notice until they try to resume a week-old audit and get a schema validation error.

## Translation table — v5.0 (4-cluster → 10-cluster)

| Old name (v4.x) | Intermediate (v5.0) | Notes |
|---|---|---|
| `visual-cta` | `visual-cta` | Unchanged (semantic match) |
| `trust-conversion` | `trust-credibility` | Renamed |
| `context-platform` | `performance-ux` | Renamed — closest semantic match. Both cover mobile UX, performance, and cognitive load. (Originally mapped to `mobile-performance` in v5.0; that slug itself was renamed to `performance-ux` in v1.1 — the translation layer collapses both steps for v4.x engagements.) |
| `audience-journey` | `audience` | Renamed |

## Translation table — v1.1 (`mobile-performance` → `performance-ux`)

| Old name (v5.0 through v1.0) | New name (v1.1+) | Notes |
|---|---|---|
| `mobile-performance` | `performance-ux` | Renamed. The cluster contains four device-agnostic reference files (`core-web-vitals`, `cognitive-load-management`, `page-performance-psychology`, `media-performance-optimization`) plus `mobile-conversion.md`. The original name led users to expect it to be skipped on desktop audits; it was not, and it should not be. The new name reflects the cluster's actual scope. The reference files inside the cluster did not change; only the cluster slug did. |

The v4.x routing concentrated multiple domains into 4 clusters. v5.0+ engagements get the full 10-cluster routing (`visual-cta`, `trust-credibility`, `pricing`, `checkout-flows`, `performance-ux`, `product-media`, `category-navigation`, `content-seo`, `post-purchase`, `audience`). Resumed v4.x engagements get the closest semantic mapping — **they do NOT retroactively gain coverage from new clusters that didn't exist when they were created**.

## When to apply

**Load-time translation only.** The on-disk `meta.json` is NEVER rewritten. The translation is a fixup applied when the resume coordinator reads any engagement whose stored slugs don't match the current canonical set:

1. Read `meta.json` from disk
2. Apply BOTH tables above to every entry in `clusters_used`. The v4.x → v5.0 mapping runs first, then the v5.0 → v1.1 mapping. Both are idempotent — applying v1.1 to an already-current slug is a no-op.
3. Apply the same translation to every `plans_queue` entry's `cluster` field AND to any cluster slugs embedded in its `file` field (e.g., `plan-trust-conversion.md`, `plan-mobile-performance.md`)
4. Apply the same translation to any cluster slug that appears in baton.json or audit.md headers when the resume coordinator presents the engagement to the user
5. **Do NOT rename files on disk** — legacy file names like `plan-trust-conversion.md` and `plan-mobile-performance.md` stay as-is and are accessed by their original filenames. The mapping is a translation layer, not a migration.
6. Log the translation once per resumed engagement. Only log the slugs that actually needed translation — don't spam the log with no-ops:
   > `Translated legacy cluster names: trust-conversion → trust-credibility, context-platform → performance-ux, mobile-performance → performance-ux, audience-journey → audience.`

After step 2 completes, the in-memory `clusters_used` array is ready to validate against the current cluster enum in `contracts/meta-schema.md`.

## Why not migrate on disk?

Two reasons:

1. **Old engagements are immutable history.** Rewriting their `meta.json` would erase the record of what the v4.x engagement actually ran. A user looking at an old trace needs to see the original cluster names to understand what was actually produced.
2. **v4.x files on disk still have legacy names.** `plan-trust-conversion.md` is a real file that the resume coordinator has to read. Renaming the meta.json slug without renaming the file on disk would break the file lookup. Renaming the file on disk would change git history for an artifact that was correct at the time of creation. Neither is worth it — the translation layer handles both concerns by keeping the disk intact and translating on read.

## What's out of scope here

- **v5.0 → future migrations**: this file is v4.x-specific. When v6 introduces new clusters, add a new table, don't modify this one.
- **Non-cluster schema changes**: `contracts/meta-schema.md` owns the current schema. This file is only about the cluster name translation.
- **Team lifecycle changes on resume**: v4.x engagements have no team state on disk. Team recreation is handled by `skills/resume/SKILL.md` and documented in `contracts/team-lifecycle.md`.
