# Report export

Procedure for generating the visual report (annotated screenshots + findings as a self-contained HTML file) using the Python report generator.

**Why this file exists:** The report export procedure is shared across `/ecp:audit`, `/ecp:build`, `/ecp:compare`, and `/ecp:quick-scan`. Prior to extraction, the audit skill owned the procedure and sibling skills referenced it via "Same as /ecp:audit". This file is the single canonical source.

**Read this file when:** you are any `/ecp:*` skill coordinator and the user requests a visual report at a checkpoint.

---

## Visual report (annotated screenshots + findings)

**Preferred: Python script.** Before attempting LLM-based assembly, try the Python report generator:

**Prerequisites (run once per environment):**
```bash
# Detect the working Python command (Windows uses `python`, Linux/macOS use `python3`)
python --version 2>/dev/null && PYTHON_CMD=python || PYTHON_CMD=python3
```

1. Run the script WITHOUT `--markers` to use automatic fuzzy matching (recommended). The script matches each finding's ELEMENT CSS selector against baton element entries using a cascade of strategies (exact selector match -> class keyword match -> fuzzy text match). This produces better marker placement than manual mapping with fewer null matches.

   ```bash
   $PYTHON_CMD ${CLAUDE_PLUGIN_ROOT}/scripts/generate-report.py \
     --engagement docs/ecp/{engagement-id} \
     --device {device} \
     --audit {audit-filename} \
     --baton {baton-filename} \
     --plugin-root ${CLAUDE_PLUGIN_ROOT}
   ```

   **Manual override:** To override auto-matching, create a `markers.json` and pass `--markers docs/ecp/{engagement-id}/markers.json`. Format:
   ```json
   [
     {"finding_index": 1, "baton_element_index": 3, "slide": 0, "severity": "critical"},
     {"finding_index": 2, "baton_element_index": null, "slide": 1, "severity": "high"}
   ]
   ```

2. The script handles: font injection (no context window consumption), hotspot mapping (with fuzzy element matching + coordinate normalization), base64 encoding, template population, click target generations, and writes a self-contained HTML file.

**If Python is unavailable:** instruct the user to install it (`apt install python3` / `brew install python` / https://python.org). As of Round 10.5 there is no LLM-assembly fallback — the Python generator is the single canonical render path across all ECP skills.

## Output naming

The **v2 renderer** (the canonical path — `--v2`, auto-detected from `synthesizer-emission-v1.json`) appends a `-v2` suffix so a v1 and a v2 report can coexist in one engagement dir. The legacy v1 renderer writes the un-suffixed names:

| Device | v2 (canonical, hardcoded by `report/v2_html_builder.py`) | v1 (legacy) |
| --- | --- | --- |
| Mobile | `visual-report-mobile-v2.html` | `visual-report-mobile.html` |
| Laptop | `visual-report-v2.html` | `visual-report.html` |
| Desktop | `visual-report-desktop-v2.html` | `visual-report-desktop.html` |

(`--from-review` final renders use `visual-report-{device}-final.html`.)

**Two-device mode:** Generate both reports by running the Python script twice sequentially (2-5 seconds each).

---

## Post-render placement QA (Tier-0 automatic + visual-QA gate escalation)

A hotspot can be *placed* (it got a coordinate) yet *wrong* (the coordinate isn't on the element the finding describes). `generate-report.py --v2` therefore prints a deterministic, zero-token **Placement QA** line in its own render summary — no separate tool run, no remembered manual step:

```
Match methods: e_index=N operator=N unplaced=N other=N
Placement QA: weak_placements=N stacks=M
  WARNING: stack of K findings on slide S @ (x, y): <f_refs>   ← stderr, one per stack
```

- **`weak_placements`** — findings placed via any match method outside the exact tier (`e_index_lookup` / `operator_override`). Since the v1.2 exact-tier-or-blank rule the live renderer no longer emits non-exact placements, so a non-zero count almost always means a stale persisted review-state still carrying a pre-v1.2 method (`proposed_anchor_*`, `section_centroid`, `section_stacked_manual`, `banner`) — treat it as a re-render/re-place signal.
- **`stacks`** — `≥ STACK_MIN` (3) distinct findings resolving to the same rendered pixel (the section-bottom-overlay collapse class). Each stack is a stderr WARNING.

The lead surfaces a non-zero `weak_placements`/`stacks` count at the audit checkpoint so the operator knows which hotspots to spot-check during the draft → client-verified pass (`product.md` §6). This is the **`free` tier** — it always runs, costs nothing, and is the CI-friendly regression signal.

> **Promotion gate (Phase-0 A9):** `--mark-client-verified` mechanically refuses promotion while any review-state finding still carries `hotspot_confidence: "needs-manual-marker"` (or no review-state file exists). The operator must either finalize placement in the editor or pass `--force` to bypass (the attestation block records `forced: true`). See `contracts/meta-schema.md` `report_state` / `report_state_attestation`.

### Escalating to the visual-QA gate (vision verification)

When the operator wants vision to confirm placement (not just the deterministic triage), escalate to the **`ecp-visual-qa`** Workflow (`.claude/workflows/ecp-visual-qa.js`). It re-runs Tier-0, crops the suspect markers onto their frozen screenshots, has a vision agent judge each crop (on-target / off-target / wrong-element / empty-region), optionally auto-re-anchors, and aggregates. It reads `review-state-{device}.json` and verifies against the captured screenshots (no live re-fetch). Invoke it via the `Workflow` tool, **once per device**:

```
Workflow(name="ecp-visual-qa", args={ engagement: "docs/ecp/{engagement-id}", device: "{device}", tier: "{tier}" })
```

**Tier is mapped from the audit flags** (see `${CLAUDE_PLUGIN_ROOT}/contracts/flags.md` `--visual`):

| Condition | Tier | What runs | Cost |
| --- | --- | --- | --- |
| no `--visual` (or `--no-visual`) | `free` | Tier-0 only — already emitted by the render summary above | $0 |
| `--visual` | `standard` | + 1 vision verifier on flagged crops (MIX cap 8) | low |
| `--visual --deep` | `deep` | + 3-verifier majority on flagged crops (MIX cap 40) | higher |

The vision tiers spend tokens, so they are an **operator opt-in** — the audit never auto-escalates past `free` on its own, and `--auto` never runs a paid tier. Run `deep` for a client-facing verification pass; `free` is the default zero-cost signal already baked into every render.
