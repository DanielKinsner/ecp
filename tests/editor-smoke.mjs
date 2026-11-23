// Smoke test for the simplified ECP hotspot editor (tools/editor, rebuilt 2026-07-20).
//
// Covers the full operator loop the editor exists for:
//   report "Queue edit" pick -> editor opens on that finding -> place a hotspot ->
//   glow / spotlight styles -> color swatch -> blur region -> retype callout ->
//   Done (approve) -> the saved review state validates and renders via the
//   canonical Python renderer (--validate-review-state / --from-review).
//
// Run: node tests/editor-smoke.mjs [fixture] [device]
import { execFile } from "node:child_process";
import { mkdtemp, rm, cp, access, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { promisify } from "node:util";
import { chromium } from "playwright";

const require = createRequire(import.meta.url);
const { resolvePython } = require("../scripts/lib/python-cmd.cjs");
const py = resolvePython();

const execFileAsync = promisify(execFile);
const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const fixtureArg = process.argv[2] || "tests/fixtures/2026-05-02-9cd2a2ac";
const device = process.argv[3] || "desktop";
const sourceEngagement = path.resolve(repoRoot, fixtureArg);

async function exists(file) {
  try {
    await access(file);
    return true;
  } catch {
    return false;
  }
}

async function run(cmd, args, options = {}) {
  return execFileAsync(cmd, args, {
    cwd: repoRoot,
    timeout: options.timeout || 120000,
    maxBuffer: 30 * 1024 * 1024,
  });
}

function fileUrl(file) {
  return pathToFileURL(file).href;
}

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function cssEscape(value) {
  if (globalThis.CSS?.escape) return CSS.escape(value);
  return String(value).replace(/["\\]/g, "\\$&");
}

async function editorState(page) {
  return page.evaluate(dev => {
    const key = Object.keys(localStorage).find(
      k => k.startsWith("ecp-review-state:") && k.endsWith(`:${dev}`),
    );
    return key ? JSON.parse(localStorage.getItem(key)) : null;
  }, device);
}

async function main() {
  assert(await exists(sourceEngagement), `Missing smoke fixture: ${sourceEngagement}`);

  const tmpRoot = await mkdtemp(path.join(tmpdir(), "ecp-editor-smoke-"));
  const tmpEngagement = path.join(tmpRoot, path.basename(sourceEngagement));
  let browser;
  try {
    await cp(sourceEngagement, tmpEngagement, { recursive: true });

    await run(py.command, [...py.baseArgs, "scripts/generate-editor.py", "--engagement", tmpEngagement, "--plugin-root", repoRoot]);
    await run(py.command, [
      ...py.baseArgs,
      "scripts/generate-report.py",
      "--engagement", tmpEngagement,
      "--device", device,
      "--plugin-root", repoRoot,
      "--v2",
      "--skip-editor",
    ]);

    const reportPath = path.join(tmpEngagement, `visual-report-${device}-v2.html`);
    const editorPath = path.join(tmpEngagement, "editor.html");
    assert(await exists(reportPath), `Generated report missing: ${reportPath}`);
    assert(await exists(editorPath), `Generated editor missing: ${editorPath}`);

    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({ viewport: { width: 1500, height: 950 } });
    const pageErrors = [];
    page.on("pageerror", error => pageErrors.push(String(error)));
    // Mirrors editor.js `markerBox`: a marker counts as PLACED if any geometry
    // family resolves, not just a rect. The generator emits real point markers
    // (cx_pct/cy_pct) for proposed-anchor placements, so a rect-only check
    // reports placed findings as unplaced.
    const hasPlacement = (state, finding) => {
      const marker = (state.markers || []).find(m => m.marker_id === finding.marker_id);
      if (!marker || marker.hidden === true) return false;
      const num = v => Number.isFinite(Number(v));
      const shape = String(marker.shape || "").toLowerCase();
      if (shape === "polygon" || shape === "freeform") {
        return Array.isArray(marker.points) && marker.points.length > 0;
      }
      if (shape === "ellipse") {
        return num(marker.cx_pct ?? marker.cx) && num(marker.rx_pct ?? marker.rx);
      }
      if (shape === "point") {
        return num(marker.cx_pct ?? marker.cx) && num(marker.cy_pct ?? marker.cy);
      }
      return num(marker.x_pct) && Number(marker.w_pct) > 0 && Number(marker.h_pct) > 0;
    };
    // The preset/bulk-approve/revert flows use prompt() and confirm().
    // Playwright dismisses dialogs by default, which would silently no-op them.
    let dialogResponse = "Smoke Look";
    page.on("dialog", async dialog => { await dialog.accept(dialogResponse); });

    // ---- report side: the pick queue the editor consumes is unchanged ----
    await page.goto(fileUrl(reportPath));
    assert(await page.locator("button", { hasText: "Open Editor" }).count() >= 1, "Report header lacks Open Editor");
    assert(await page.locator(".detail-btn-editor-queue").count() > 0, "Report lacks Queue edit buttons");

    await page.locator(".panel-scroll:not([hidden]) .finding-row[data-fid], .panel-scroll:not([hidden]) .priority-ref-row[data-fid]").first().click();
    const fid = await page.locator(".detail-card.visible").getAttribute("data-fid");
    assert(fid, "No active finding detail was selected");
    await page.locator(`.detail-btn-editor-queue[data-fid="${cssEscape(fid)}"]`).click();
    const queued = await page.evaluate(() => {
      const entry = Object.entries(localStorage).find(([key]) => key.startsWith("ecp-editor-picks:"));
      return entry ? JSON.parse(entry[1]) : [];
    });
    assert(Array.isArray(queued) && queued.includes(fid), "Queue edit did not persist the selected finding");

    // ---- editor: pick routing ----
    await page.goto(`${fileUrl(editorPath)}#pick=${encodeURIComponent(fid)}&device=${encodeURIComponent(device)}`);
    await page.waitForSelector("#stage .stage-hud", { timeout: 15000 });
    await page.waitForTimeout(300);

    assert(await page.locator("#doneFinding").count() === 1, "Editor lacks Done button");
    assert(await page.locator("#exportFinal").count() === 1, "Editor lacks Render Final Report");
    assert(await page.locator(".finding-card.is-active").count() === 1, "Editor did not activate a finding card");
    const pickedState = await editorState(page);
    const picked = pickedState.findings.find(f => f.review_selected === true);
    assert(picked, "#pick did not mark the finding as review_selected");

    const activeRef = await page.evaluate(() => document.querySelector(".finding-card.is-active .card-ref")?.textContent);
    assert(activeRef, "Active card has no ref label");

    // ---- clear placement, then hand-place a hotspot ----
    await page.keyboard.press("Delete");
    await page.waitForTimeout(150);
    assert(await page.locator(".place-banner").count() === 1, "Clearing the hotspot did not surface the place banner");
    assert(await page.locator(".hotspot").count() === 0, "Cleared hotspot still renders");

    // Long screenshots extend past the viewport; drag inside the VISIBLE part
    // of the image (pointer events dispatched off-viewport never hit the stage).
    const img = await page.locator("#slideImage").boundingBox();
    assert(img, "Slide image has no bounding box");
    const viewport = page.viewportSize();
    const vis = {
      x: Math.max(img.x, 0),
      y: Math.max(img.y, 0),
      right: Math.min(img.x + img.width, viewport.width),
      bottom: Math.min(img.y + img.height, viewport.height),
    };
    vis.w = vis.right - vis.x;
    vis.h = vis.bottom - vis.y;
    assert(vis.w > 40 && vis.h > 40, `Slide image is not visibly on screen (${JSON.stringify(vis)})`);
    await page.mouse.move(vis.x + vis.w * 0.30, vis.y + vis.h * 0.30);
    await page.mouse.down();
    await page.mouse.move(vis.x + vis.w * 0.55, vis.y + vis.h * 0.55, { steps: 4 });
    await page.mouse.up();
    await page.waitForTimeout(150);
    assert(await page.locator(".hotspot").count() === 1, "Hand-drawn hotspot did not render");
    assert(await page.locator(".place-banner").count() === 0, "Place banner did not clear after placement");
    assert(await page.locator(".callout").count() === 1, "Placed finding has no callout");

    // ---- styles: glow then spotlight, each with an intensity slider ----
    await page.locator('.style-btn[data-style="glow"]').click();
    await page.waitForTimeout(100);
    assert(await page.locator(".hotspot.style-glow").count() === 1, "Glow style did not apply");
    assert(await page.locator("#styleIntensityWrap:not([hidden])").count() === 1, "Glow did not surface the intensity slider");
    await page.locator("#styleIntensity").fill("90");
    await page.locator("#styleIntensity").dispatchEvent("change");
    await page.waitForTimeout(100);
    const glowState = await editorState(page);
    assert(glowState.markers.some(m => Math.abs((m.glow_opacity ?? 0) - 0.9) < 0.01), "Glow intensity slider did not set glow_opacity");

    await page.locator('.style-btn[data-style="spotlight"]').click();
    await page.waitForTimeout(100);
    assert(await page.locator(".spotlight-dim").count() === 1, "Spotlight style did not dim the surroundings");
    await page.locator("#styleIntensity").fill("70");
    await page.locator("#styleIntensity").dispatchEvent("change");
    await page.waitForTimeout(100);
    // Scope to the picked finding — fixture states may already carry rectless
    // dim effects belonging to other findings.
    const spotState = await editorState(page);
    const activeFRef = spotState.findings.find(f => f.review_selected === true)?.f_ref;
    assert(activeFRef, "Could not resolve the picked finding's f_ref");
    const spotDim = spotState.slide_edits.flatMap(se => se.effects)
      .find(e => e.type === "dim" && !e.rect && e.f_ref === activeFRef);
    assert(spotDim && Math.abs(spotDim.opacity - 0.7) < 0.01, "Spotlight intensity slider did not set the dim opacity");

    // ---- Blur surroundings: auto-selects around the hotspot and follows it ----
    await page.locator("#blurAround").click();
    await page.waitForTimeout(150);
    assert(await page.locator(".blur-around-piece").count() === 4, "Blur surroundings did not render four around-pieces");
    assert(await page.locator("#blurStrengthWrap:not([hidden])").count() === 1, "Blur surroundings did not surface the strength slider");
    const findAround = s => s.slide_edits.flatMap(se => se.effects)
      .find(e => e.type === "blur" && e.mode === "outside" && e.f_ref === activeFRef);
    let around = findAround(await editorState(page));
    assert(around && around.rect, "Blur surroundings effect was not persisted with mode outside + rect");
    const aroundXBefore = around.rect.x_pct;
    await page.keyboard.press("Shift+ArrowRight");
    await page.waitForTimeout(150);
    around = findAround(await editorState(page));
    assert(Math.abs(around.rect.x_pct - aroundXBefore - 0.5) < 0.05, "Blur surroundings rect did not follow the nudged hotspot");

    // ---- ArrowDown/ArrowUp step through findings ----
    // Arrow nav cycles within the visible filter; the pick queue may hold just
    // one finding, so switch to All where there is something to step to.
    await page.locator("#filterTabs button", { hasText: "All" }).click();
    await page.waitForTimeout(100);
    const navRefBefore = await page.locator(".finding-card.is-active .card-ref").textContent();
    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(150);
    const navRefNext = await page.locator(".finding-card.is-active .card-ref").textContent();
    assert(navRefNext !== navRefBefore, "ArrowDown did not advance to the next finding");
    await page.keyboard.press("ArrowUp");
    await page.waitForTimeout(150);
    const navRefBack = await page.locator(".finding-card.is-active .card-ref").textContent();
    assert(navRefBack === navRefBefore, "ArrowUp did not return to the previous finding");

    // ---- color swatch updates marker stroke + callout accent ----
    await page.locator('.swatch[data-color="#EF4444"]').click();
    await page.waitForTimeout(100);
    const colorState = await editorState(page);
    const coloredMarker = colorState.markers.find(m => m.stroke === "#EF4444");
    assert(coloredMarker, "Color swatch did not set marker stroke");
    const coloredFinding = colorState.findings.find(f => f.callout_color === "#EF4444");
    assert(coloredFinding, "Color swatch did not set callout_color");
    const calloutBorder = await page.locator(".callout").first().evaluate(el => getComputedStyle(el).borderColor);
    assert(/239,\s*68,\s*68/.test(calloutBorder), `Callout border did not take the new color (${calloutBorder})`);

    // ---- blur region ----
    await page.locator('.tool[data-tool="blur"]').click();
    await page.mouse.move(vis.x + vis.w * 0.62, vis.y + vis.h * 0.10);
    await page.mouse.down();
    await page.mouse.move(vis.x + vis.w * 0.85, vis.y + vis.h * 0.24, { steps: 4 });
    await page.mouse.up();
    await page.waitForTimeout(150);
    assert(await page.locator(".blur-region").count() === 1, "Blur tool did not create a blur region");
    assert(await page.locator("#deleteRegion:not([hidden])").count() === 1, "Selected blur region did not surface Remove region");
    assert(await page.locator("#blurStrengthWrap:not([hidden])").count() === 1, "Selected blur region did not surface the strength slider");
    const blurState = await editorState(page);
    const blurEffect = blurState.slide_edits.flatMap(se => se.effects).find(e => e.type === "blur");
    assert(blurEffect && blurEffect.rect && blurEffect.f_ref, "Blur effect was not persisted with rect + f_ref");

    // ---- retype the callout ----
    await page.locator(".callout .callout-title").click();
    await page.keyboard.press("Control+a");
    await page.keyboard.type("Smoke-edited callout title");
    await page.keyboard.press("Enter");
    await page.waitForTimeout(150);
    const textState = await editorState(page);
    assert(
      textState.findings.some(f => f.callout_title_override === "Smoke-edited callout title"),
      "Callout retype did not persist callout_title_override",
    );

    // ---- undo reverts the retype ----
    await page.keyboard.press("Control+z");
    await page.waitForTimeout(100);
    const undoneState = await editorState(page);
    assert(
      !undoneState.findings.some(f => f.callout_title_override === "Smoke-edited callout title"),
      "Undo did not revert the callout retype",
    );
    await page.keyboard.press("Control+y");
    await page.waitForTimeout(100);

    // ---- text panel: rewrite what the CLIENT reads, not just the callout ----
    // The renderer has always honored *_override on the finding body; until
    // 2026-07-24 nothing in the editor could write them.
    const textPanelRef = await page.evaluate(() =>
      document.querySelector(".finding-card.is-active .card-ref")?.textContent?.trim());
    assert(textPanelRef, "No active finding to edit text on");

    await page.keyboard.press("t");
    await page.waitForTimeout(150);
    assert(await page.locator("#inspector:not([hidden])").count() === 1, "T did not open the text panel");
    assert(
      await page.locator('.field[data-override="recommendation_override"] textarea').count() === 1,
      "Text panel lacks a Recommendation field",
    );

    const recBox = page.locator('.field[data-override="recommendation_override"] textarea');
    await recBox.click();
    await page.keyboard.press("Control+a");
    await page.keyboard.type("Smoke-rewritten recommendation");
    await recBox.blur();
    await page.waitForTimeout(200);
    let panelState = await editorState(page);
    assert(
      panelState.findings.some(f => f.recommendation_override === "Smoke-rewritten recommendation"),
      "Text panel did not persist recommendation_override",
    );

    // Per-field revert puts the AI's words back and clears the override.
    await page.locator('.field[data-override="recommendation_override"] [data-role="revert"]').click();
    await page.waitForTimeout(150);
    panelState = await editorState(page);
    assert(
      !panelState.findings.some(f => f.recommendation_override),
      "Per-field Revert did not clear recommendation_override",
    );

    // ---- severity: must reach the review state, not just recolour a stroke ----
    await page.locator('.field select[data-role="severity"]').selectOption("critical");
    await page.waitForTimeout(200);
    const sevState = await editorState(page);
    const sevFinding = sevState.findings.find(f => f.severity_override === "critical");
    assert(sevFinding, "Severity control did not write severity_override");
    const sevMarker = sevState.markers.find(m => m.marker_id === sevFinding.marker_id);
    assert(
      sevMarker && String(sevMarker.severity).toLowerCase() === "critical",
      "Severity change did not follow through to the marker",
    );

    // ---- callout hide is a real, persisted decision ----
    await page.locator("#calloutVisible").uncheck();
    await page.waitForTimeout(150);
    const hiddenCalloutState = await editorState(page);
    assert(
      hiddenCalloutState.findings.some(f => f.callout_visible === false),
      "Unticking Callout did not persist callout_visible:false",
    );
    await page.locator("#calloutVisible").check();
    await page.waitForTimeout(150);

    // ---- look presets apply to the finding you are on ----
    await page.locator('.style-btn[data-style="glow"]').click();
    await page.waitForTimeout(150);
    dialogResponse = "Smoke Look";
    await page.locator("#savePreset").click();
    await page.waitForTimeout(200);
    assert(
      await page.locator('#presetSelect option[value="Smoke Look"]').count() === 1,
      "Save look did not add a preset option",
    );
    // Change the look away from the preset, then apply it back.
    await page.locator('.style-btn[data-style="outline"]').click();
    await page.waitForTimeout(150);
    await page.locator("#presetSelect").selectOption("Smoke Look");
    await page.waitForTimeout(250);
    const presetState = await editorState(page);
    const presetMarker = presetState.markers.find(m => m.marker_id === sevFinding.marker_id);
    assert(
      presetMarker && presetMarker.highlight_style === "glow",
      `Applying a preset did not restore its style (got ${presetMarker && presetMarker.highlight_style})`,
    );

    // ---- search narrows the list and Escape restores it ----
    const listedBefore = await page.locator(".finding-card").count();
    await page.locator("#findingSearch").fill("zzz-no-such-finding-zzz");
    await page.waitForTimeout(150);
    assert(await page.locator(".finding-card").count() === 0, "Search did not filter the finding list");
    assert(await page.locator(".empty-note").count() === 1, "Empty search shows no explanation");
    await page.locator("#findingSearch").press("Escape");
    await page.waitForTimeout(150);
    assert(
      await page.locator(".finding-card").count() === listedBefore,
      "Escape in the search box did not restore the full list",
    );

    // ---- [hidden] controls are actually INVISIBLE, not just attributed ----
    // `.control-group label {display:flex}` (0,1,1) outranks the UA `[hidden]`
    // rule (0,1,0), so these sliders rendered for styles that have no
    // intensity/blur at all. Attribute-only assertions miss this entirely.
    await page.locator('.style-btn[data-style="outline"]').click();
    await page.waitForTimeout(200);
    assert(
      !(await page.locator("#styleIntensityWrap").isVisible()),
      "Intensity slider is still VISIBLE on the Outline style ([hidden] lost to a display rule)",
    );
    assert(
      !(await page.locator("#blurStrengthWrap").isVisible())
      || await page.locator("#blurAround.is-active").count() === 1,
      "Blur strength slider is VISIBLE with no blur to adjust ([hidden] lost to a display rule)",
    );
    await page.locator('.style-btn[data-style="glow"]').click();
    await page.waitForTimeout(200);
    assert(
      await page.locator("#styleIntensityWrap").isVisible(),
      "Intensity slider did not appear for the Glow style",
    );

    // ---- the Render button warns that the HTML on disk is behind ----
    assert(
      await page.locator("#exportFinal.has-unrendered").count() === 1,
      "Render button does not flag unrendered edits after editing",
    );

    // ---- approve ----
    await page.locator("#doneFinding").click();
    await page.waitForTimeout(150);
    let approvedState = await editorState(page);
    assert(
      approvedState.findings.some(f => f.status === "approved"),
      "Done did not approve the finding",
    );

    // ---- revert restores the AI original for one finding ----
    await page.locator(".finding-card").first().click();
    await page.waitForTimeout(150);
    await page.keyboard.press("t");
    await page.waitForTimeout(100);
    if (await page.locator("#inspector[hidden]").count() === 1) {
      await page.keyboard.press("t");
      await page.waitForTimeout(100);
    }
    const beforeRevert = await editorState(page);
    const revertRef = await page.evaluate(() =>
      document.querySelector(".finding-card.is-active .card-ref")?.textContent?.trim());
    await page.locator(".inspector-danger").click();
    await page.waitForTimeout(250);
    const revertedState = await editorState(page);
    const revertedFinding = revertedState.findings.find(f => String(f.f_ref).endsWith(revertRef));
    assert(revertedFinding, `Reverted finding ${revertRef} vanished from the state`);
    assert(
      !revertedFinding.severity_override
      && !revertedFinding.recommendation_override
      && !revertedFinding.callout_title_override
      && revertedFinding.callout_visible !== false,
      "Revert to AI original left operator overrides behind",
    );
    assert(
      !(revertedState.slide_edits || []).some(se =>
        (se.effects || []).some(e => e && e.f_ref === revertedFinding.f_ref)),
      "Revert to AI original left this finding's blur/dim effects behind",
    );
    assert(beforeRevert.findings.length === revertedState.findings.length, "Revert dropped findings");

    // ---- bulk approve skips anything still unplaced ----
    await page.locator('#filterTabs button:has-text("All")').click();
    await page.waitForTimeout(150);
    const unplacedBefore = await page.evaluate(() =>
      document.querySelectorAll(".finding-card .card-status.place").length);
    await page.locator("#approveAll").click();
    await page.waitForTimeout(300);
    approvedState = await editorState(page);
    const stillUnplaced = approvedState.findings.filter(f =>
      f.status === "approved" && !hasPlacement(approvedState, f));
    assert(
      stillUnplaced.length === 0,
      `Approve all shown approved ${stillUnplaced.length} unplaced finding(s) — those render blank for the client`,
    );
    if (unplacedBefore > 0) {
      assert(
        approvedState.findings.some(f => f.status !== "approved"),
        "Approve all shown swept up unplaced findings instead of skipping them",
      );
    }

    // ---- file:// render help modal + help overlay ----
    await page.locator("#exportFinal").click();
    await page.waitForTimeout(300);
    assert(await page.locator("#renderModal:not([hidden])").count() === 1, "Render on file:// did not open the how-to modal");
    const serveCmd = await page.locator("#cmdServe").textContent();
    assert(serveCmd.includes("serve-editor.cjs") && serveCmd.includes("--engagement"), "Render modal lacks a usable serve command");
    await page.locator("#closeRenderModal").click();
    await page.keyboard.press("?");
    assert(await page.locator("#helpModal:not([hidden])").count() === 1, "? did not open the help overlay");
    await page.keyboard.press("Escape");
    await page.waitForTimeout(100);
    assert(await page.locator("#helpModal:not([hidden])").count() === 0, "Escape did not close the help overlay");

    assert(pageErrors.length === 0, `Editor threw page errors: ${pageErrors.join(" | ")}`);

    // ---- the edited state passes the canonical validator and renders ----
    const editedPath = path.join(tmpEngagement, `review-state-${device}-smoke.json`);
    await writeFile(editedPath, JSON.stringify(approvedState, null, 2) + "\n");
    await run(py.command, [
      ...py.baseArgs,
      "scripts/generate-report.py",
      "--engagement", tmpEngagement,
      "--device", device,
      "--plugin-root", repoRoot,
      "--validate-review-state", `review-state-${device}-smoke.json`,
    ]);
    await run(py.command, [
      ...py.baseArgs,
      "scripts/generate-report.py",
      "--engagement", tmpEngagement,
      "--device", device,
      "--plugin-root", repoRoot,
      "--from-review", `review-state-${device}-smoke.json`,
      "--output", `visual-report-${device}-smoke-final.html`,
    ]);
    assert(
      await exists(path.join(tmpEngagement, `visual-report-${device}-smoke-final.html`)),
      "Edited review state did not render a final report",
    );

    console.log(JSON.stringify({ ok: true, fixture: fixtureArg, device, fid, activeRef }, null, 2));
  } finally {
    if (browser) await browser.close();
    await rm(tmpRoot, { recursive: true, force: true });
  }
}

main().catch(error => {
  console.error(error.stack || error.message || String(error));
  process.exit(1);
});
