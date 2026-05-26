# Device semantics

Canonical documentation for ECP device handling — viewport dimensions, DPR (device pixel ratio), `--device` flag syntax, dual-device file naming conventions, session isolation for parallel acquisition, and the coordinator prompt template.

**Why this file exists:** Prior to Round 11, device handling was duplicated across multiple skills. This file consolidates the rules so no skill drifts from the canonical device behavior.

---

## Supported devices

ECP supports exactly 3 device profiles. No custom viewports are supported — adding more would explode the dual-device file-naming matrix and the cluster-routing override rules. If you need a custom viewport, use agent-browser directly and pipe the DOM as a file-mode input.

| Device | Viewport | DPR | Acquisition command |
|---|---|---|---|
| `mobile` | 390×844 | 3× | `agent-browser close` + `agent-browser set device "iPhone 14"` |
| `laptop` | 1440×900 | 1× | `agent-browser set viewport 1440 900` |
| `desktop` | 1920×1080 | 1× | `agent-browser set viewport 1920 1080` |

**Why iPhone 14 for mobile:** iPhone 14 hits 3× DPR with a modern viewport and is the closest stock agent-browser preset to the median iOS device at time of writing. Using `set device "iPhone 14"` gives the acquirer touch simulation and correct viewport meta handling in one call. Manual viewport resets (`set viewport 390 844`) do NOT replicate DPR correctly and should not be used for mobile acquisition.

**Why 1440×900 for laptop:** It's the median 13" MacBook Pro / 14" Windows laptop viewport after chrome subtraction. Using 1366×768 (the literal web-stats median) misrepresents modern retina laptops; 1440×900 is the closest "modern but not 4K" baseline.

**Why 1920×1080 for desktop:** Full HD is still the dominant desktop monitor resolution per web analytics. 2560×1440 and 4K introduce layout differences on responsive sites that would fire non-representative findings.

---

## `--device` flag syntax

Full flag documentation lives in `${CLAUDE_PLUGIN_ROOT}/contracts/flags.md`. Quick recap:

**Single device:**
```
--device mobile
--device laptop
--device desktop
```

**Dual device (comma-pair, max 2):**
```
--device mobile,laptop
--device mobile,desktop
--device laptop,desktop
```

Order matters for dual-device file naming — see "Dual-device file naming" below.

**Interactive prompt format (when `--device` not set and not in `--auto` mode):**

Every skill that supports `--device` shows a prompt like this when no flag is passed:

```
Which device should I scan?
1. **Desktop** (1920×1080) — default
2. **Mobile** (390×844)
3. **Laptop** (1440×900)

Select a single device, or two for dual-device mode (e.g., `1,2` for desktop + mobile).
```

User response:
- A single digit (`1`, `2`, `3`) → single device.
- A comma-pair (`1,2`, `1,3`, `2,3`) → dual device.
- Empty input / Enter → uses the default (Desktop).
- Any other input → re-prompt with the same options.

---

## `--auto` mode device defaults

When `--device` is not set AND `--auto` mode is active, each skill has a deterministic default:

| Skill | Default device(s) in --auto mode |
|---|---|
| `/ecp:audit` | `mobile,laptop` (dual-device) |
| `/ecp:compare` | `laptop` (single device) |
| `/ecp:quick-scan` | `laptop` (single device) |

**Rationale:**
- **Audit defaults to dual-device** because audit is the thorough mode — two devices give the planner the full picture for responsive layout issues.
- **Compare defaults to single laptop** because dual-device compare runs 4 acquisitions (2 pages × 2 devices) and is expensive. Opt-in via explicit `--device` for dual.
- **Quick-scan defaults to single laptop** because quick-scan is the fast mode — the value prop is speed, not comprehensive coverage.

**Build does not accept `--device`** — there are no viewports to render (the page is being built from scratch). Build infers "mobile-first" signal from intake for cluster routing override rules per `${CLAUDE_PLUGIN_ROOT}/contracts/cluster-routing.md`.

---

## Dual-device file naming conventions

When a skill runs with a dual-device comma-pair (e.g., `--device mobile,desktop`), it captures and writes separate files for each device. The **first** device in the pair uses the bare filename; the **second** device uses the `-{device}` suffix.

| File type | First device (e.g., mobile) | Second device (e.g., desktop) |
|---|---|---|
| Baton file | `baton.json` | `baton-desktop.json` |
| Preprocessed DOM | `dom.html` | `dom-desktop.html` |
| Sectioned screenshots | `section-1.jpg`, `section-2.jpg`, ... | `section-desktop-1.jpg`, `section-desktop-2.jpg`, ... |
| Per-cluster audit file | `cluster-{cluster}-mobile.md` | `cluster-{cluster}-desktop.md` |
| Final audit report | `audit.md` | `audit-desktop.md` |
| Visual report | `visual-report.html` | `visual-report-desktop.html` |

**Rationale for this naming convention:**
- The first device is the "default" — if a consumer reads just `audit.md` they get a coherent single-device report.
- The second device is the "addendum" — explicitly suffixed so the pair is greppable and the directory listing is sortable.
- Per-cluster files ALWAYS use the device suffix (including for the first device, e.g., `cluster-pricing-mobile.md`) so cluster auditors can write deterministically without needing to know which device is "first".

**Compare-specific variant:** compare adds a `-competitor` suffix on top of the device convention:
- `baton.json` (your page, first device)
- `baton-competitor.json` (competitor, first device)
- `baton-mobile.json` (your page, second device if different from first)
- `baton-competitor-mobile.json` (competitor, second device)

This file covers the device half of the naming only.

---

## Session isolation for parallel dual-device acquisition

When a skill spawns dual-device acquisition teammates in parallel (audit mode default), the acquirers use **named agent-browser sessions** to prevent the two browser instances from clobbering each other's state.

**Session naming:** `--session {device}` passed to all `agent-browser` commands. Examples:
```
agent-browser --session mobile set device "iPhone 14"
agent-browser --session mobile open "https://example.com"
agent-browser --session mobile screenshot --full section-1.jpg
agent-browser --session desktop set viewport 1920 1080
agent-browser --session desktop open "https://example.com"
agent-browser --session desktop screenshot --full section-desktop-1.jpg
```

Without named sessions, two parallel agent-browser processes would race for the single default session and produce corrupted DOM/screenshots.

**Teammate naming convention for dual-device:** spawn two acquirer teammates with device-suffixed names:
```
name="acquirer-mobile"
name="acquirer-desktop"
```

The audit team relay layer uses these names to route acquisition results to the correct baton file on disk. See `${CLAUDE_PLUGIN_ROOT}/workflows/acquire.md` for the acquisition workflow details.

---

## File mode and description mode: device selection is skipped

When the input is a file path or a description (not a URL), device selection is skipped entirely — there's no viewport rendering happening. Specifically:

- **File mode** (`source_mode: "file"` or `"pasted-code"`): the skill reads the file directly; no agent-browser, no screenshots. Device selection prompt is never shown. `devices_requested` in meta.json is set to an empty array `[]` or the single value `"file"` depending on the skill.
- **Description mode** (`source_mode: "description"`, quick-scan and build only): the skill evaluates against principles without page code. Device selection prompt is never shown.
- **Screenshot mode** (`source_mode: "screenshot"`, quick-scan only): the device context is INFERRED from the screenshot itself (image dimensions < 500px width → mobile) or the user's description. No viewport rendering happens, but `device_context` is still set for downstream processing. Device selection prompt is not shown.

In all three cases, the coordinator does NOT call agent-browser at all — the device semantics above apply only to URL mode.

---

## Cost warnings for high-cost device combinations

Some skill × device combinations are expensive enough to warrant an interactive warning:

**Compare dual-device warning** (shown when `/ecp:compare` is invoked with `--device mobile,desktop` or a comma-pair):
> "Scanning 2 URLs × 2 devices = 4 acquisitions. This will take longer. Proceed?"

In `--auto` mode: show the warning but proceed without prompt (don't block deterministic runs on it).

**Audit dual-device in `--auto` mode:** no warning — dual-device is the audit default in `--auto`, so it's expected behavior.

---

## Cross-skill references

Skills that use this file:

- **`skills/audit/SKILL.md`** — `<device_selection>` defers here. Supports both single and dual-device modes.
- **`workflows/acquire.md`** — uses the session naming convention for parallel dual-device acquisition.

When editing this file, grep all 4 skill files for any stale inline device documentation that may have been missed and convert to references.
