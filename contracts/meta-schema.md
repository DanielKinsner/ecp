# meta.json validation schema

Canonical schema for `docs/ecp/{engagement-id}/meta.json`. Every skill that creates or consumes an engagement directory (`/ecp:audit`, `/ecp:build`, `/ecp:compare`, `/ecp:quick-scan`, `/ecp:resume`) validates against this document.

Prior to ECP v5.0 the same schema was duplicated verbatim across four skill files. That duplication caused subtle drift (`build/SKILL.md` accepted `[shopify, nextjs, generic]` while the other three already accepted `opencart`, and so on). This reference file is the single source of truth — update it here and the reference in each skill picks up the change.

## When to validate

**Do NOT re-read and validate `meta.json` immediately after writing it.** The coordinator just wrote it, so it will always pass. Validation is only needed when **resuming an engagement** (via `/ecp:resume` or `--engagement-id`) where the coordinator is reading a `meta.json` it did not write in this session.

On resume:

1. Re-read `meta.json`.
2. Verify every required field against the rules below.
3. If ANY field is missing, null, or fails its pattern/enum check: **fix it immediately** before proceeding, and log which field was corrected.
4. Apply legacy cluster name translation per `contracts/cluster-migration.md` before comparing `clusters_used` against the v5.0 enum.

Always update the `updated` field to the current ISO 8601 timestamp on every phase transition (regardless of validation context).

## Required fields

| Field | Type | Constraint |
|---|---|---|
| `id` | string | MUST match `^\d{4}-\d{2}-\d{2}-[0-9a-f]{8}$` (e.g., `2026-04-08-a3f7b1c2`) |
| `created` | string | Valid ISO 8601 (e.g., `2026-04-08T14:30:00.000Z`) |
| `type` | string | Enum: `audit` (the canonical v1.2 engagement type — the only value written by a new engagement). The values `build`, `quick-scan`, `compare` are retained as a `product.md` §7 frozen-interface contract for the §5-frozen modes — accepted on resume from archived engagements, never written by a new v1.2 engagement. |
| `phase` | string | LEGACY (v1/v2 schema_version): One of `pending`, `audit`, `plan`, `review`, `build`, `complete`, `blocked`. v2-architecture engagements (schema_version=3) use `engagement_status` instead — see below. |
| `engagement_status` | string | **v2-architecture only (schema_version=3).** One of the values listed in [`contracts/audit-state-machine.md`](audit-state-machine.md). v1-schema engagements omit this field. |
| `platform` | string | One of: `shopify`, `nextjs`, `opencart`, `woocommerce`, `generic` |
| `page.type` | string | One of: `product`, `cart`, `checkout`, `homepage`, `category`, `landing`, `pricing`, `post-purchase` |
| `clusters_used` | string[] | Each entry MUST be a v5.0 cluster slug (see below). Legacy v4.x names are silently translated per `contracts/cluster-migration.md`. |

### Valid `clusters_used` values (v5.0+)

`visual-cta`, `trust-credibility`, `pricing`, `checkout-flows`, `performance-ux`, `product-media`, `category-navigation`, `content-seo`, `post-purchase`, `audience`

Legacy v4.x cluster names (`trust-conversion`, `context-platform`, `audience-journey`) are accepted on resume and silently mapped to v5.0 equivalents. See `contracts/cluster-migration.md` for the full translation table.

### Note on `phase: blocked` (legacy v1/v2-schema)

For v1-schema engagements (`schema_version: 1` or `2`), the `blocked` phase value is written by the Phase 4 **forensic assertion canary** (see `${CLAUDE_PLUGIN_ROOT}/contracts/trace-assertion-canary.md`) when structural assertions fail at audit completion — for example, when `team_spawned_auditors: 0` means the lead skipped all cluster auditor teammates. A blocked engagement is structurally invalid and needs investigation, not a normal recovery path.

For v2-architecture engagements (`schema_version: 3`), this state is replaced by `engagement_status: failed_<phase>` — the `<phase>` suffix names exactly which layer's assertion failed (e.g., `failed_specialists`, `failed_synthesis`, `failed_render`). See [`contracts/audit-state-machine.md`](audit-state-machine.md) for the full state graph.

The `phase: blocked` value is distinct from the `blocked: true` **boolean optional field** (below), which is set by the reviewer teammate when it issues a BLOCK verdict on a plan. That's a plan-level block ("revise before proceeding"); this is a run-level block ("the audit itself is broken"). The boolean is preserved across schema versions.

On resume:
- v1-schema: a blocked engagement should show the `assertion_failures` field (also written by the canary) to the user and offer retry options
- v2-schema: a `failed_<phase>` engagement cannot be resumed automatically; operator inspects, fixes input, creates a new engagement (per audit state machine contract)
- A `blocked: true` plan engagement should offer revise-plan / re-review / abort (regardless of schema version)

## Optional fields

Valid if present, ignored if absent:

| Field | Type | Notes |
|---|---|---|
| `schema_version` | number | `1` (legacy v4.x), `2` (v5.x v1-architecture), or `3` (v2-architecture: specialist JSON emission, single-Opus synthesizer, baton element-index hotspots, audit state machine). Missing → treat as `1`. Sticky once set: v2 cannot retro-touch a v1 engagement; v1 cannot resume a v2 engagement. |
| `updated` | string | ISO 8601; rewritten on every phase transition |
| `blocked` | boolean | Set by reviewer on BLOCK verdict |
| `quick_scan` | boolean | `true` for quick-scan engagements only |
| `compare_target` | object | Compare mode only — `{ url: string, file_path: string \| null }` |
| `page.url` | string \| null | Source URL when `source_mode = "url-dual"` |
| `page.url_normalized` | string \| null | Normalized URL for progress memory matching |
| `page.file_path` | string \| null | Source path when `source_mode = "file"` |
| `min_priority` | string \| null | `critical`, `high`, `medium`, `low`, or null |
| `source_mode` | string \| null | See enum below |
| `devices_requested` | string[] | User-requested devices (e.g., `["mobile", "desktop"]`) |
| `devices_scanned` | string[] | Devices actually scanned (may differ on partial failure) |
| `plans_queue` | array | Multi-planner mode only — per-cluster plan queue |
| `reconciled` | boolean | `true` after finding reconciliation step |
| `screenshot_input` | object \| null | Set when `source_mode = "screenshot"` |
| `scope` | string \| null | Audit scope selected by user. See enum below. Missing on legacy engagements → treat as `"comprehensive"` on resume. |
| `report_state` | string \| null | `draft` or `client-verified` (product.md §6). Missing/null → treat as `draft`. See below. |
| `report_state_attestation` | object \| null | Written by `set_client_verified` on successful promotion (Phase-0 A9, 2026-06-10). Records `promoted_at` (ISO 8601), `unplaced_counts` (per-device map of `needs-manual-marker` finding counts at promotion time), and `forced` (boolean — true when the operator bypassed the placement gate with `--force`). Absent on engagements that have not been promoted; readers MUST NOT infer state from its absence — `report_state` is the source of truth. See below. |
| `reflection_state` | string \| null | `draft` or `complete` (G23, 2026-05-28). Missing/null → treat as `draft`. The lead's attestation that `lead-reflection.md` matches the pipeline's actual end-state. See below. |

### Valid `scope` values

| Value | Meaning |
|---|---|
| `focused` | Single cluster selected (interactive scope prompt option a). |
| `standard` | **Canonical v1.2 audit scope (default; interactive scope prompt option b).** Every cluster relevant to the detected page type, per `product.md` §2.3 v1.2 and `contracts/cluster-routing.md`. New v1.2 engagements write this value for the page-type-relevant set. |
| `custom` | Operator-selected cluster set (interactive scope prompt option d). |
| `everything` | Every cluster regardless of page type — all 10 clusters dispatched (interactive scope prompt option e, equivalent to `--focus all`). |
| `comprehensive` | **Legacy alias (pre-v1.2).** Pre-v1.2 engagements wrote `"comprehensive"` for what is now called `"standard"` (page-type-relevant set). Accepted on resume from those engagements; new v1.2 engagements never write it. The pre-v1.2 reduced-scope 3-4-cluster default tier (also called `"standard"` before v1.2) is retired — neither a new engagement nor an unfreezing change can introduce it without a §10 Spec Change Log entry. |

On resume: if `scope` is missing (legacy v5.0 engagement created before the scope selector existed), treat as `"standard"` (page-type-relevant set) for backward compatibility — that matches what legacy runs actually dispatched.

### Valid `report_state` values (product.md §6 draft → client-ready gate)

| Value | Meaning |
|---|---|
| `draft` | Default. Every generated report is a DRAFT. **All `--auto` / automated runs MUST leave `report_state` at `draft`.** Rendering a report never promotes it. |
| `client-verified` | Set **only** by the operator's manual verification pass: re-check the live site, follow every legal/ethics citation link and confirm relevancy, and finalize hotspot placement (§4.2). |

**The load-bearing invariant: automated / `--auto` execution can NEVER mark a report `client-verified`.** Promotion is a deliberate, explicit operator action — run `python ${CLAUDE_PLUGIN_ROOT}/scripts/generate-report.py --engagement <dir> --mark-client-verified`. That verb refuses (`AutoPromotionError`, non-zero exit) when invoked with `--auto`; the same guard lives in `scripts/assembly/report_state.py:set_client_verified(auto=...)`.

**Placement gate (Phase-0 A9, 2026-06-10):** `set_client_verified` also refuses (`UnplacedMarkerError`, distinct non-zero exit) when the engagement's `review-state-{device}.json` file(s) report any finding with `hotspot_confidence == "needs-manual-marker"`, or when no review-state file exists at all (placement was never finalized — product.md §6 step 3 / §4.2). The CLI exposes `--force` as the operator escape hatch; the resulting attestation block records `forced: true` so the audit trail captures the bypass. `--force` does NOT bypass the `--auto` refusal — that guard is absolute.

On successful promotion, `set_client_verified` stamps `report_state_attestation` on `meta.json`: `{ promoted_at, unplaced_counts: {device: count}, forced: bool }`. The block is informational (the source of truth for state is `report_state` itself) but the unplaced counts let a reader see exactly *what* the operator attested to at promotion time.

On resume / when missing: treat absent, null, or blank `report_state` as `draft` (back-compat with engagements created before §6 tracking existed). `read_report_state()` in `report_state.py` is the canonical reader.

### Valid `reflection_state` values (G23, 2026-05-28)

| Value | Meaning |
|---|---|
| `draft` | Default. `lead-reflection.md` may have been written but has NOT been explicitly attested as matching the pipeline's actual end-state. Premature writes (e.g. an agent writing reflection mid-pipeline before all specialists finish) leave the state at `draft`. **All `--auto` / automated runs MUST leave `reflection_state` at `draft`.** |
| `complete` | Set **only** by the lead's explicit completion attestation at audit end — after canaries pass and the reflection narrative has been written/refreshed against the actually-completed on-disk state. |

**The load-bearing invariant: automated / `--auto` execution can NEVER mark a reflection `complete`.** Engagement `docs/ecp/2026-05-28-e4050c0e` proved why — a rogue early write produced a narrative that said "synth did not run" against a deliverable where synth actually had run and produced a clean priority path. The G8-style draft-by-default state machine prevents the next premature write from being trusted: the operator (or any downstream tooling) reading `meta.json` sees `reflection_state: draft` and knows the narrative isn't finalized. Completion is a deliberate, explicit verb — run `python ${CLAUDE_PLUGIN_ROOT}/scripts/generate-report.py --engagement <dir> --mark-reflection-complete`. That verb refuses (`AutoCompletionError`, non-zero exit) when invoked with `--auto`; the same guard lives in `scripts/assembly/reflection_state.py:set_reflection_complete(auto=...)`.

On resume / when missing: treat absent, null, or blank `reflection_state` as `draft`. `read_reflection_state()` in `reflection_state.py` is the canonical reader.

### Valid `source_mode` values

URL is the only canonical input (`product.md` §2.2). The file / pasted-code / screenshot / description values are retained as `product.md` §7 frozen-interface contracts for the §5-frozen non-URL input modes — accepted on resume from archived engagements, never written by a new v1.2 audit.

| Value | Status | Meaning |
|---|---|---|
| `url-dual` | live | Page scanned via URL with agent-browser (dual capture: DOM + screenshots). |
| `manual` | live | Acquisition agent failed; coordinator captured screenshots + DOM directly from a URL. |
| `webfetch` | live | agent-browser unavailable; page content fetched via WebFetch from a URL. |
| `file` | **frozen / legacy** | Local file path provided. §7 contract only — a new v1.2 audit never writes this. |
| `pasted-code` | **frozen / legacy** | Code pasted directly. §7 contract only — a new v1.2 audit never writes this. |
| `screenshot` | **frozen / legacy** | Operator-provided screenshot image (no URL, no DOM). §7 contract only — a new v1.2 audit never writes this. |
| `description` | **frozen / legacy** | Text description only (from-scratch mode). §7 contract only — a new v1.2 audit never writes this. |

### `screenshot_input` object shape

Only present when `source_mode = "screenshot"`. Otherwise `null` or absent.

```json
{
  "filename": "original filename or null",
  "description": "user's description of what the screenshot shows",
  "device_context": "desktop"
}
```

`device_context` is one of `desktop`, `mobile`, or `unknown`.

## Example

```json
{
  "schema_version": 3,
  "id": "2026-04-08-a3f7b1c2",
  "created": "2026-04-08T14:30:00.000Z",
  "updated": "2026-04-08T14:45:00.000Z",
  "type": "audit",
  "page": {
    "url": "https://example.com/products/widget",
    "url_normalized": "example.com/products/widget",
    "file_path": null,
    "type": "product"
  },
  "platform": "shopify",
  "source_mode": "url-dual",
  "devices_requested": ["mobile", "laptop"],
  "devices_scanned": [],
  "scope": "standard",
  "clusters_used": ["visual-cta", "trust-credibility", "pricing", "product-media", "content-seo", "performance-ux"],
  "min_priority": null,
  "compare_target": null,
  "quick_scan": false,
  "blocked": false,
  "plans_queue": [],
  "reconciled": false,
  "screenshot_input": null,
  "report_state": "draft",
  "reflection_state": "draft"
}
```

## Related references

- `contracts/cluster-migration.md` — v4.x → v5.0 cluster name translation rules
- `contracts/team-lifecycle.md` — Agent Teams lifecycle contract (teams use `meta.json` to track phase transitions)
- `templates/meta.json.template` — reference example with field comments (not copied at runtime — skills write meta.json programmatically using this schema)
