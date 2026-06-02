"use strict";

// Shared, dependency-free resolver for "which Python interpreter do we spawn?".
//
// Why this exists: the Python tree is already portable (every shebang is
// `#!/usr/bin/env python3`), but the Node tooling used to hardcode the
// interpreter name "python", which does not exist on a stock macOS/Linux box
// (only "python3" does). Worse, the report/editor generators import jsonschema,
// so we must not fall through to a bare system python3 that lacks it when a
// project-local virtualenv (with jsonschema installed) is sitting right there.
//
// Resolution order (first that works wins):
//   a. process.env.ECP_PYTHON  — explicit override, used verbatim.
//   b. <repoRoot>/.venv        — the project virtualenv, if present. This is
//      preferred over a bare python3 precisely because it carries jsonschema.
//   c. A system interpreter that answers `--version` with exit 0:
//      python3, then python, then the Windows `py` launcher (`py -3`).
//
// Only Node builtins are used (path, fs, child_process) so this can be required
// from any tooling context without a dependency install.

const path = require("node:path");
const fs = require("node:fs");
const { spawnSync } = require("node:child_process");

// This file lives at <repoRoot>/scripts/lib/python-cmd.cjs, so the repo root is
// two directories up from __dirname.
const repoRoot = path.resolve(__dirname, "..", "..");

// Probe a candidate interpreter by running `<command> <baseArgs...> --version`.
// Output is suppressed; we only care whether it exits 0. Any spawn failure
// (ENOENT, etc.) surfaces as a non-zero/null status and is treated as "no".
function probe(command, baseArgs) {
  try {
    const result = spawnSync(command, [...baseArgs, "--version"], {
      stdio: "ignore",
      // Bound the probe so a pathological PATH entry that hangs on --version
      // (e.g. the Windows Store python3.exe App Execution Alias, or a shim that
      // waits on stdin) is skipped instead of wedging resolution. A timeout
      // yields status null + result.error, which the status===0 gate rejects.
      timeout: 5000,
    });
    return result.status === 0;
  } catch {
    return false;
  }
}

function venvPython() {
  return process.platform === "win32"
    ? path.join(repoRoot, ".venv", "Scripts", "python.exe")
    : path.join(repoRoot, ".venv", "bin", "python");
}

function resolvePython() {
  // a. Explicit override — trust the caller completely.
  const override = process.env.ECP_PYTHON;
  if (override && override.trim()) {
    return { command: override.trim(), baseArgs: [] };
  }

  // b. Project-local virtualenv — preferred because it carries jsonschema.
  //    Verify it actually runs (not just that the file exists): a partial or
  //    orphaned venv whose base interpreter was uninstalled must fall through
  //    to a working system python3 rather than ENOENT every downstream spawn.
  const venv = venvPython();
  if (fs.existsSync(venv) && probe(venv, [])) {
    return { command: venv, baseArgs: [] };
  }

  // c. First system interpreter that actually runs.
  const candidates = [
    { command: "python3", baseArgs: [] },
    { command: "python", baseArgs: [] },
    { command: "py", baseArgs: ["-3"] },
  ];
  for (const candidate of candidates) {
    if (probe(candidate.command, candidate.baseArgs)) {
      return candidate;
    }
  }

  throw new Error(
    "ECP could not find a Python interpreter. Create the project virtualenv " +
      "(`python3 -m venv .venv && . .venv/bin/activate && pip install -r " +
      "requirements.txt -r requirements-dev.txt`), install Python 3 so that " +
      "`python3` is on PATH, or set ECP_PYTHON to the interpreter to use.",
  );
}

module.exports = { resolvePython };
