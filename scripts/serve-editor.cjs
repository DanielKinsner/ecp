#!/usr/bin/env node
const http = require("node:http");
const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

function argValue(name, fallback = null) {
  const idx = process.argv.indexOf(name);
  if (idx >= 0 && process.argv[idx + 1]) return process.argv[idx + 1];
  return fallback;
}

const repoRoot = path.resolve(__dirname, "..");
const engagementArg = argValue("--engagement");
if (!engagementArg) {
  console.error("Usage: node scripts/serve-editor.cjs --engagement <engagement-dir> [--port 8787]");
  process.exit(2);
}

const engagementDir = path.resolve(repoRoot, engagementArg);
const port = Number(argValue("--port", "8787"));
const maxImportBytes = 5 * 1024 * 1024;

function within(base, target) {
  const rel = path.relative(base, target);
  return rel && !rel.startsWith("..") && !path.isAbsolute(rel);
}

function send(res, status, body, headers = {}) {
  res.writeHead(status, headers);
  res.end(body);
}

function sendJson(res, status, value) {
  send(res, status, JSON.stringify(value), {
    "content-type": "application/json; charset=utf-8",
    "cache-control": "no-store",
  });
}

function contentType(file) {
  const ext = path.extname(file).toLowerCase();
  return {
    ".html": "text/html; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
  }[ext] || "application/octet-stream";
}

function safeFilename(name) {
  return String(name || "imported-image")
    .replace(/[^a-zA-Z0-9._-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    || "imported-image";
}

function extensionForMime(mime) {
  if (mime === "image/jpeg") return ".jpg";
  if (mime === "image/png") return ".png";
  if (mime === "image/webp") return ".webp";
  if (mime === "image/gif") return ".gif";
  return ".img";
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = "";
    req.setEncoding("utf8");
    req.on("data", chunk => {
      body += chunk;
      if (body.length > 20 * 1024 * 1024) {
        reject(new Error("request body too large"));
        req.destroy();
      }
    });
    req.on("end", () => resolve(body));
    req.on("error", reject);
  });
}

function renderReview(state) {
  const device = state.device || "desktop";
  if (!["desktop", "mobile", "laptop"].includes(device)) {
    throw new Error(`invalid review-state device: ${device}`);
  }
  const reviewName = `review-state-${device}.json`;
  const finalName = `visual-report-${device}-final.html`;
  const reviewPath = path.join(engagementDir, reviewName);
  fs.writeFileSync(reviewPath, JSON.stringify(state, null, 2) + "\n", "utf8");

  const result = spawnSync(
    "python",
    [
      "scripts/generate-report.py",
      "--engagement",
      engagementDir,
      "--device",
      device,
      "--plugin-root",
      repoRoot,
      "--from-review",
      reviewName,
      "--output",
      finalName,
    ],
    { cwd: repoRoot, encoding: "utf8" },
  );
  if (result.status !== 0) {
    throw new Error(`${result.stderr || result.stdout || "render failed"}`.trim());
  }
  return {
    ok: true,
    device,
    review_state: reviewName,
    final_report: finalName,
    url: `/${finalName}`,
    message: result.stdout.trim(),
  };
}

function saveImportedAsset(payload) {
  const assetId = safeFilename(payload?.asset_id || `import-${Date.now()}`);
  const match = /^data:(image\/[a-zA-Z0-9.+-]+);base64,([a-zA-Z0-9+/=\r\n]+)$/.exec(String(payload?.data_url || ""));
  if (!match) throw new Error("invalid image data URL");
  const mime = payload.mime_type || match[1];
  if (!String(mime).startsWith("image/")) throw new Error("import must be an image");
  const raw = Buffer.from(match[2].replace(/\s+/g, ""), "base64");
  if (raw.length > maxImportBytes) throw new Error("imported image exceeds 5MB");
  let filename = safeFilename(payload.filename || assetId);
  if (!path.extname(filename)) filename += extensionForMime(mime);
  const source = `user-imports/${assetId}-${filename}`;
  const outPath = path.resolve(engagementDir, source);
  if (!within(engagementDir, outPath)) throw new Error("invalid import path");
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, raw);
  return {
    ok: true,
    asset: {
      asset_id: assetId,
      source,
      mime_type: mime,
      bytes: raw.length,
    },
  };
}

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://localhost:${port}`);
    if (req.method === "POST" && url.pathname === "/api/import-asset") {
      const body = await readBody(req);
      const payload = JSON.parse(body || "{}");
      return sendJson(res, 200, saveImportedAsset(payload));
    }

    if (req.method === "POST" && url.pathname === "/api/render-review") {
      const body = await readBody(req);
      const payload = JSON.parse(body || "{}");
      if (!payload || typeof payload !== "object" || !payload.state) {
        return sendJson(res, 400, { ok: false, error: "missing review state" });
      }
      return sendJson(res, 200, renderReview(payload.state));
    }

    if (req.method !== "GET" && req.method !== "HEAD") {
      return send(res, 405, "Method not allowed");
    }

    const pathname = decodeURIComponent(url.pathname === "/" ? "/editor.html" : url.pathname);
    const filePath = path.resolve(engagementDir, `.${pathname}`);
    if (!within(engagementDir, filePath) && filePath !== engagementDir) {
      return send(res, 403, "Forbidden");
    }
    if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
      return send(res, 404, "Not found");
    }
    const headers = {
      "content-type": contentType(filePath),
      "cache-control": "no-store",
    };
    res.writeHead(200, headers);
    if (req.method === "HEAD") return res.end();
    fs.createReadStream(filePath).pipe(res);
  } catch (error) {
    sendJson(res, 500, { ok: false, error: error.message || String(error) });
  }
});

server.listen(port, "127.0.0.1", () => {
  console.log(`ECP editor server running: http://127.0.0.1:${port}/editor.html`);
  console.log(`Engagement: ${engagementDir}`);
});
