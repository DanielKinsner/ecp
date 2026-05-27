# ECP Review Editor Changelog

## v1.0.3 - 2026-05-26 (Manual-placement ergonomics — conformance G5, §4.2)

- Fixed the core manual-placement gap: hand-drawing a hotspot (`setMarker`) now promotes a finding off `needs-manual-marker`/risky confidence to `exact-selector`, mirroring `snapToNearestBaton`. Before this, a finding the operator just placed by hand stayed flagged "Place manually" forever and the queue never drained. This completes the conformance-G4 flow, which routes every unplaced/absence finding into the manual-placement queue with no marker.
- Added a **Place** queue to the finding-list switch: one click surfaces every finding still awaiting a hotspot (unplaced marker or `needs-manual-marker` confidence), with an empty-state note when nothing is left to place.
- Added a stage placement hint: when the active finding has no hotspot yet, the stage shows "draw a {tool} to place {finding}" so the next action is obvious.
- Smoke test (`tests/editor-smoke.mjs`) now covers the round-trip: clear a hotspot → "Place manually" → hand-draw a box → state clears and the marker registers.

## v1.0.2 - 2026-05-03 (Manual report-to-editor correction workflow)

- Added visual-report buttons to Queue edit or Open editor for the selected finding, so the operator chooses what needs correction from the report instead of relying on AI confidence.
- Added editor queue ingestion from `localStorage`/hash route, marking report-picked findings as the focused Edit Set and opening directly on the chosen device/finding.
- Added Done Finding, AI Draft View / Corrected View, Preview Finding, and Export Bundle workflow actions.
- Added focused inspector panels for hotspot, callout, effects, and crop, with full controls moved behind an expandable section.
- Added one-click visual presets for problem highlight, soft blur, premium callout, dim background, and clean yellow.
- Added shaped Dim Region drawing, independent hotspot-only delete via Delete/Backspace, stronger panel-contained scrolling, and actual blur edge masking for the rolloff slider.
- Kept frame/callout/Photopea exports and added a per-finding bundle with frame, hotspot, connector, callout, and manifest layers.
- Removed disconnected polygon/lasso buttons from the default visible UI while keeping the simpler highlight-box and blur-region workflow primary.

## v1.0.1 - 2026-05-02 (Editor bug-fix triple — text edit, hotspot clear, picker toggle)

- Fixed text-edit P0: per-keystroke `rememberUndo()` filled the 50-entry undo cap in seconds, per-keystroke `renderFindings()`+`renderStage()` blew away textarea focus mid-typing, and status flipped to `"edited"` only for `*_override` fields so callout-body / review-notes / AI-pass-note edits silently failed to mark the finding as touched. Now: live model update on every keystroke (no re-render), one undo entry per editing burst (snapshot at first keystroke), debounced localStorage save (600ms), full re-render on blur. Status flip covers all editable content fields.
- Fixed marker delete P1: added "Clear placement (keep finding)" right-click action and a trash button on the Marker layer row. Strips the marker's coords, sets `hotspot_confidence: "needs-manual-marker"`, and surfaces the finding in the "Place manually" queue — without hiding the finding itself. Existing "Hide finding (delete)" still does what it did.
- Fixed Picked-toggle P1: clicking "Picked" on a finding flagged `needs_manual_edit:true` no longer appears dead. `isPickedForEdit` now treats explicit user input (`review_selected: true|false`) as authoritative, falling back to `needs_manual_edit` only when the operator hasn't expressed a preference yet.

## v1 - 2026-05-01

- Added canonical `review-state-v1.json` contract.
- Added self-contained per-engagement `editor.html` generation.
- Added desktop/mobile tabs, editable findings, marker tools, off-image callout placement, crop/blur/dim state, localStorage autosave, and multi-step undo/redo.
- Added slide filmstrip, review progress, status counts, active-finding context, stage HUD, and keyboard finding navigation.
- Reshaped the editor into a Photoshop-style canvas app with a checkerboard workspace, docked properties panel, and layer stack.
- Added report-specific QA: preflight buckets, finding flags, severity/source metadata, review notes, and raw evidence context.
- Added direct visual-edit controls for marker geometry, callout position/width, callout visibility, crop/effect reset, and marker nudge/resize hotkeys.
- Added severity-matched color swatches and report-ready highlight styles that persist into final HTML rendering.
- Added object-like editing: right-click menu, selectable layer rows, crop/blur resize handles, dim amount slider, blur radius slider, and blur rolloff slider.
- Added a default Fix Queue so exact-selector findings are hidden from the main work list and canvas until explicitly requested.
- Added placement verdict labels, fit-to-workspace behavior, and real hide/delete behavior so hidden hotspots disappear from the canvas.
- Simplified the default tool surface around the actual report workflow: highlight box, blur area, callout editing, save/export.
- Changed blur and dim effects from slide-global behavior to active-finding scoped behavior, with blur amount shown as a percentage slider.
- Changed Photopea handoff to send the active finding as layered screenshot/hotspot/connector/callout files instead of only opening the screenshot.
- Added manual exports for the active screenshot frame and the active callout as a transparent full-frame SVG layer.
- Changed the main finding workflow from AI-confidence queueing to a manual All Findings -> Edit Set picker.
- Added right-click marker shape conversion plus fill/glow opacity controls and a stronger glow renderer.
- Canonical final export is the Python `generate-report.py --from-review` path to avoid browser/CLI renderer drift.
- Added review-state validation and imported-asset listing via `generate-report.py`.
- Mobile screenshots render at CSS viewport scale by default even when captured at 3x DPR.
