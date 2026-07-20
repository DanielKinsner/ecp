// Behavioral smoke test for the acquirer element-capture JS (RC#1, 2026-06-02
// hotspot diagnosis + 2026-06-03 adversarial review §1 P0-1).
//
// The locking unit test (tests/test_acquire_element_selectors.py) only asserts
// selector STRINGS appear in the JS source — it never runs the JS, so it could
// not catch that a zero-sized native <select> was allowlisted and then dropped
// by the per-element `r.width===0 || r.height===0` guard. This test runs the
// CANONICAL extraction JS (pulled from scripts/acquire_url.py — no duplication)
// in real chromium against a synthetic DOM where the native <select> is
// 0x0/opacity:0 inside a sized wrapper, and asserts the control reaches the
// captured rows anchored to its ancestor rect.

import { execFile } from "node:child_process";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { chromium } from "playwright";

const require = createRequire(import.meta.url);
const { resolvePython } = require("../scripts/lib/python-cmd.cjs");
const py = resolvePython();
const execFileAsync = promisify(execFile);
const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

// Pull the exact extraction JS the acquirer evaluates. expected_hostname="" so
// the contamination guard matches about:blank (location.hostname === "").
async function canonicalElementsJs() {
  const code =
    "import sys; sys.path.insert(0, 'scripts'); " +
    "from acquire_url import _build_elements_js; " +
    "sys.stdout.write(_build_elements_js(''))";
  const { stdout } = await execFileAsync(
    py.command,
    [...py.baseArgs, "-c", code],
    { cwd: repoRoot, timeout: 60000, maxBuffer: 8 * 1024 * 1024 },
  );
  assert(stdout.includes("querySelectorAll"), "Did not get the extraction JS from python");
  return stdout;
}

const FIXTURE_HTML = `<!doctype html><html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0">
  <div id="ymm-wrap" style="width:300px;height:60px;position:relative">
    <!-- native control hidden behind the enhanced widget (the RC#1 shape):
         display:none yields a guaranteed 0x0 getBoundingClientRect. -->
    <select id="ymm-year" style="display:none">
      <option>Year</option><option>2024</option>
    </select>
    <!-- JS-enhanced visible widget overlaying the native select -->
    <div class="custom-dropdown" style="width:300px;height:40px">Select Year</div>
  </div>
  <!-- These controls have no visible local proxy and must remain excluded. -->
  <select id="unrepresented-hidden" style="display:none"><option>Ghost</option></select>
  <div style="display:none;width:300px;height:60px">
    <select id="hidden-with-hidden-wrapper"><option>Ghost wrapper</option></select>
  </div>
  <button id="find-parts" style="width:140px;height:44px">Find parts</button>
  <div style="height:2200px"></div>
</body></html>`;

async function main() {
  const js = await canonicalElementsJs();
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
    await page.setContent(FIXTURE_HTML, { waitUntil: "load" });
    const rows = await page.evaluate(js);
    assert(Array.isArray(rows), "Extraction JS did not return an array of rows");

    const selects = rows.filter(r => r && r.tag === "select");
    assert(
      selects.length === 1,
      "RC#1 regression: a zero-sized native <select> inside a sized wrapper was " +
      "not captured exactly once, or an unrepresented hidden control leaked into the baton.",
    );
    const s = selects[0];
    // The native select is 0x0 (display:none); it can only have been captured by
    // inheriting the nearest sized ancestor rect (#ymm-wrap, 300x60). A non-zero
    // rect matching the wrapper proves the form-control ancestor-resolution path
    // ran — not that chromium happened to give the control a min-size.
    assert(
      s.width === 300 && s.height === 60,
      `Captured <select> must inherit the sized ancestor rect (300x60), got ${s.width}x${s.height}`,
    );

    // sanity: an ordinary visible button is still captured
    assert(rows.some(r => r && r.tag === "button"), "Visible <button> was not captured");

    console.log(JSON.stringify({ ok: true, rows: rows.length, selects: selects.length, selectRect: [s.width, s.height] }));
  } finally {
    await browser.close();
  }
}

main().catch(err => {
  console.error(err.stack || err.message || String(err));
  process.exit(1);
});
