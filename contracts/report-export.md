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

- Mobile: `visual-report-mobile.html`
- Laptop: `visual-report.html`
- Desktop: `visual-report-desktop.html`

**Two-device mode:** Generate both reports by running the Python script twice sequentially (2-5 seconds each).
