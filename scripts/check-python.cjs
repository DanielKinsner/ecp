#!/usr/bin/env node
"use strict";

// Thin cross-platform wrapper around `python -m py_compile <files>`, invoked by
// the `check:python` npm script. It exists only to resolve a real interpreter
// (see scripts/lib/python-cmd.cjs) instead of hardcoding "python", which is
// absent on stock macOS/Linux. The set of files compiled is unchanged.

const { spawnSync } = require("node:child_process");
const { resolvePython } = require("./lib/python-cmd.cjs");

// The exact six files the previous inline `check:python` script compiled.
const FILES = [
  "scripts/report/templates/js.py",
  "scripts/report/templates/html_structure.py",
  "scripts/report/templates/components.py",
  "scripts/report/templates/css.py",
  "scripts/report/html_builder.py",
  "scripts/report/v2_html_builder.py",
];

const py = resolvePython();
const result = spawnSync(py.command, [...py.baseArgs, "-m", "py_compile", ...FILES], {
  stdio: "inherit",
});

process.exit(result.status === null ? 1 : result.status);
