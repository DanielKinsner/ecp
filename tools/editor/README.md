# ECP Review Editor

The editor is a human-in-the-loop review surface for visual audit reports.

The pipeline generates `review-state-{device}.json` from AI draft artifacts, then builds a self-contained `editor.html` with inline CSS, JavaScript, review states, and screenshot data URLs. The editor writes operator changes into review state; it does not mutate raw evidence artifacts.

## Source Of Truth

- Raw evidence: `baton*.json`, `cluster-*.json`, `synthesizer-emission-v1.json`, screenshots, and AI draft `visual-report-*.html`.
- Human-approved presentation: `review-state-{device}.json`.
- Client deliverable: `visual-report-{device}-final.html`, rendered from review state.

## MVP Editor Features

- Desktop/mobile tabs from one `editor.html`.
- Slide filmstrip for fast section jumps.
- All Findings is the default finding list, matching report order; mark cards with Edit to build a focused Edit Set.
- Generated visual reports expose Queue edit and Open editor actions so the operator can manually choose screenshot + finding + callout corrections from the report itself. The editor consumes those picks as the Edit Set; AI confidence no longer controls what opens for review.
- Done Finding approves the active finding, removes it from the Edit Set, and advances to the next queued correction.
- AI Draft View / Corrected View toggles between the original generated placement and the current human-edited version.
- Preview Finding opens a focused single-finding preview.
- Export Bundle downloads the active screenshot frame plus hotspot, connector, callout, and manifest layers for manual editing outside the browser.
- Photoshop-style canvas workspace with a right-side properties and layers dock.
- The canvas hides non-queue and hidden markers by default so the screen is not covered by already-credible hotspots.
- Numeric geometry controls for markers and callouts, plus direct callout resize handles.
- Severity-matched color swatches and report-ready highlight styles: outline, glow, fill, spotlight, underline, with opacity controls for fill and glow.
- Simple default tools for the intended report workflow: draw/move the highlight box, move/edit the callout, and blur only the active finding's surrounding context.
- Dim Region draws a finding-scoped dim rectangle. Spotlight still dims everything outside the hotspot when that is the desired treatment.
- Right-click canvas/object menu for shape conversion, fill color, severity matching, expand/shrink, reset crop, clear active-finding effects, and delete/hide actions.
- Delete / Backspace clears only the active hotspot placement so the finding stays editable; `H` or `Shift+Delete` hides the entire finding.
- Visible crop and blur regions with draggable resize handles.
- Finding-scoped dim/spotlight amount, blur amount percentage, and blur rolloff sliders.
- Selectable layer rows for marker, callout, effects, individual effects, crop, and evidence image.
- Fit button and `F` hotkey reset pan/zoom and keep large screenshots inside the workspace.
- Export Frame downloads the active screenshot frame for manual editing.
- Export Callout Layer downloads the active callout as a transparent, full-frame SVG layer for manual image-editor placement.
- Move Callout Here explicitly pins a finding's callout to the current screenshot when the callout should live on a different screenshot than the hotspot.
- Report Set panel for the manual edit set, all findings, review status, and hidden findings.
- Finding metadata panel for severity, cluster, source section, match method, review notes, and raw evidence.
- Findings are grouped by placement verdict but sorted in report order, so AI confidence no longer drives the main workflow.
- Approve, edit, hide, and tag-for-AI-pass status controls.
- Editable finding/callout prose.
- Point, rectangle, and ellipse marker placement on the slide.
- Off-image callout positioning and blur/dim effect persistence.
- Multi-step undo/redo for editor actions.
- Save review state as a downloaded JSON file.
- Export the current review state for the canonical Python final renderer.

## Hotkeys

- `Ctrl/Cmd+Z`: undo
- `Ctrl/Cmd+Shift+Z` or `Ctrl/Cmd+Y`: redo
- `Ctrl/Cmd+S`: download current review state
- `Left` / `Right`: previous or next slide
- `J` / `K`: next or previous finding
- `F`: fit active screenshot to the workspace
- `+` / `-`: scale active slide canvas
- `Shift` + arrow keys: nudge active marker
- `Alt` + arrow keys: resize active marker
- `C`: show or hide active callout
- `G`: cycle highlight style
- `M`: match active marker color to finding severity
- `0`: recenter active callout
- `1` point, `2` rect, `3` ellipse, `4` pan, `5` crop, `6` blur, `7` dim region
- `A`: approve active finding
- `Delete` or `Backspace`: delete active hotspot only
- `H` or `Shift+Delete`: hide active finding
- `Escape`: cancel current draw/drag and return to point tool

## Canonical Export

When the editor is opened through `scripts/serve-editor.cjs`, `Render Final Report` writes the current `review-state-{device}.json` and invokes the canonical Python renderer. When the editor is opened as a standalone file, save the review state and run the same renderer manually.

Run this after saving review state:

```powershell
python scripts\generate-report.py --engagement docs\ecp\<engagement-id> --device desktop --plugin-root . --from-review review-state-desktop.json
```

Use `--device mobile --from-review review-state-mobile.json` for the mobile deliverable.

Validate a saved review state without rendering:

```powershell
python scripts\generate-report.py --engagement docs\ecp\<engagement-id> --device desktop --plugin-root . --validate-review-state review-state-desktop.json
```

Audit imported assets referenced by a review state:

```powershell
python scripts\generate-report.py --engagement docs\ecp\<engagement-id> --device desktop --plugin-root . --list-imports review-state-desktop.json
```

## Mobile DPR Display

Mobile screenshots may be 1170px wide because acquisition uses a 390px CSS viewport at 3x DPR. The editor displays them at CSS viewport width by default, then lets the operator scale and pan the slide canvas intentionally. Do not treat the raw image pixel width as the editor display width.
