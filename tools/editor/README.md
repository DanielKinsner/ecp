# ECP Hotspot Editor

The editor is the human-in-the-loop surface for fixing visual audit reports when
the AI could not place (or misplaced) a hotspot. It was rebuilt 2026-07-20 as a
deliberately small tool: place the box, style it, blur distractions, fix the
callout text, done.

The pipeline generates `review-state-{device}.json` from AI draft artifacts, then
builds a self-contained `editor.html` with inline CSS, JavaScript, review states,
and screenshot data URLs. The editor writes operator changes into review state;
it does not mutate raw evidence artifacts.

## Source Of Truth

- Raw evidence: `baton*.json`, `cluster-*.json`, `synthesizer-emission-v1.json`, screenshots, and AI draft `visual-report-*.html`.
- Human-approved presentation: `review-state-{device}.json`.
- Client deliverable: `visual-report-{device}-final.html`, rendered from review state by the canonical Python renderer.

## The workflow

1. In the generated visual report, click **Queue edit** on any finding that needs
   a manual fix, then **Open editor** (or open `editor.html` directly).
2. The editor opens on the queued finding. The left rail lists findings —
   **Queue** (picked + unplaced), **All**, **Done**, **Hidden**.
3. Fix the finding on the canvas, hit **Done ✓**, and the editor advances to the
   next queued finding.
4. **Render Final Report** writes the review state and re-renders the client
   deliverable through `generate-report.py --from-review` (requires the editor
   server, below).

## Features (all of them)

### Placing and styling the hotspot

- **Highlight box** — drag on the screenshot to draw the hotspot; drag the box to
  move it, corner/edge handles to resize. Unplaced findings show a "not placed"
  banner and just need one drag.
- **Style** — Outline, Glow, or Spotlight (dims everything outside the box).
  Glow and Spotlight get an **Intensity** slider.
- **Color** — five swatches + a custom picker; sets the box stroke and the
  callout accent together.
- **Blur surroundings** — one click blurs everything outside the highlight box
  and follows the box when it moves; the strength slider adjusts it.
- **Blur regions** — the Blur tool also drags freehand regions over anything
  distracting; regions are per-finding, selectable, resizable, and deletable.
- **Look presets** — save the current finding's style + color + intensity + blur
  as a named look, then apply it to any other finding in one click. Presets live
  in the browser, so a house style carries across engagements. They always apply
  to the finding you are on — there is no bulk restyle.

### Rewriting what the client reads (`T`)

The **Text panel** on the right edits the finding itself, not just its callout:

- **Finding title, Observation, Recommendation, Why it matters, Element** — these
  are the words in the report body. Each field shows the AI's original in a
  collapsible *AI original* block and has its own **Revert**.
- **Severity** — changes how the report *files* the finding: its priority chip,
  severity color, ordering and metric counts. Changing severity re-colors the
  hotspot only if you had not already picked a color by hand.
- **Callout title / Callout body** — the overlay text (also editable in place on
  the canvas).
- **Callout width** — how wide the callout card sits on the screenshot.
- **Revert finding to AI original** — one button that throws away every edit to
  this finding: text, severity, color, style, blur regions and hotspot geometry,
  restored from the untouched AI twin marker the pipeline stores alongside each
  marker.

Leaving a field identical to the AI's wording stores `null`, so the review state
only ever records what a human actually changed.

### Working through a report

- **Search** (`/`) — filter the finding list by ref, title, body, cluster,
  severity, element or section. Tab counts always show the whole bucket, so a
  stale search can never make findings look like they vanished.
- **Done / Hide** — approve and advance, or drop the finding from the report.
- **Approve all shown** — bulk-approves everything listed in the current tab,
  and **skips anything still unplaced** (an unplaced finding has no hotspot, so
  approving it would ship a blank frame). It tells you how many it skipped.
- **Undo/redo**, autosave to browser storage, **Save JSON** download, and
  **Render Final Report** (opened without the server, the button shows a
  copy-paste how-to with the exact commands for this engagement).
- **Unrendered-changes dot** — a yellow dot on *Render Final Report* means the
  HTML on disk is older than what is in front of you.
- A "Done x/y" progress counter, Ctrl+scroll zoom, and a `?` help overlay.
- The finding filter, active tool, ghost-hotspot toggle and text-panel state are
  remembered between sessions.

Legacy review states (ellipse/polygon markers, dim regions, fill/underline
styles) still load and render; redrawing a legacy marker converts it to a plain
rectangle.

## Hotkeys

- `Ctrl/Cmd+Z` / `Ctrl/Cmd+Y`: undo / redo
- `Ctrl/Cmd+S`: download the review state JSON
- `Down` / `Up` (or `J` / `K`): next / previous finding
- `Left` / `Right`: previous / next screenshot
- `Shift`+arrows: nudge the highlight box; `Alt`+arrows: resize it
- `V` / `B`: Highlight tool / Blur tool
- `T`: show / hide the text panel
- `/`: jump to the finding search box (`Esc` clears it, `Enter` opens the top hit)
- `F`: fit screenshot to window; `Ctrl`+scroll: zoom
- `A`: Done (approve + advance)
- `H`: hide / unhide the finding
- `Delete`: remove the selected blur region, otherwise clear the hotspot placement
- `Escape`: close modal / cancel drag / deselect
- `?`: hotkey and workflow help

## Canonical Export

When the editor is opened through `scripts/serve-editor.cjs`, **Render Final
Report** writes the current `review-state-{device}.json` and invokes the
canonical Python renderer:

```powershell
node scripts\serve-editor.cjs --engagement docs\ecp\<engagement-id>
# then open http://127.0.0.1:8787/editor.html
```

When the editor is opened as a standalone file, **Save JSON** downloads the
review state; run the renderer manually:

```powershell
python scripts\generate-report.py --engagement docs\ecp\<engagement-id> --device desktop --plugin-root . --from-review review-state-desktop.json
```

Validate a saved review state without rendering:

```powershell
python scripts\generate-report.py --engagement docs\ecp\<engagement-id> --device desktop --plugin-root . --validate-review-state review-state-desktop.json
```

## Data contract

The editor reads and writes `review-state-v1` (schema:
`schema/review-state-v1.json`). Fields the renderer honors from the editor:

- markers: rect geometry (`x_pct`/`y_pct`/`w_pct`/`h_pct`), `stroke`
  (`#RRGGBB`), `highlight_style` (`outline`/`glow`/`spotlight`),
  `spotlight_visible`, `glow_opacity`, `severity`, `hidden`.
- findings — report body: `finding_title_override`, `observation_override`,
  `recommendation_override`, `why_this_matters_override`, `element_override`,
  `severity_override`.
- findings — overlay: `callout_title_override`, `callout_body_override`,
  `callout_color`, `callout_position`, `callout_visible` (false suppresses the
  callout entirely), `status` (`approved`/`edited`/`hidden`).
- slide_edits: `effects` of `{type: "blur"|"dim", f_ref, rect, radius_px,
  opacity, mode}` — blur/dim regions scoped to one finding. `mode:"outside"`
  is Blur surroundings; a rectless `dim` is the Spotlight mask.

An override set to `null` means "use the AI's original". A finding the operator
never touched keeps `status: needs_review` and no overrides, and the renderer
leaves its auto-mapped marker alone — the review state only overrides what a
human actually changed.

Both renderer paths (`scripts/report/html_builder.py` for v1 and
`scripts/report/v2_html_builder.py` for v2) carry this logic. A field added to
one and not the other silently works on some engagements and not others;
`tests/test_review_state_editor_contract.py` pins them in agreement.

## Mobile DPR Display

Mobile screenshots may be 1170px wide because acquisition uses a 390px CSS
viewport at 3x DPR. All editor geometry is percentage-based, so placement is
DPR-safe; the default zoom fits the image to the window.
