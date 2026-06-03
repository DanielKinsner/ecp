# ECP — environment & workflow (agent quick-start)

**`product.md` is the constitution — it wins over this file.** This doc is only *how to set
ECP up and not break it across machines*. If anything here disagrees with `product.md`, `product.md` is right.

## ▶ Start here (current work state)
**Rolling handoff: [`docs/2026-06-03-handoff-hotspot-accuracy.md`](docs/2026-06-03-handoff-hotspot-accuracy.md)** —
read it before picking up hotspot-accuracy work. Current state (2026-06-03): all four
hotspot-placement fixes are in code (acquirer element-capture, mobile tiling, hero-stack
distribute+flag) and pushed to `main`; the one remaining step is a single live verification
audit — **which requires the `--plugin-dir` launch below, or it tests stale code.**

## Platform reality
- **Primary dev/run environment is Windows** (PowerShell). The majority of work and every real
  `/ecp:audit` happens there.
- **This macOS checkout is ~5–10% use — cross-OS porting/verification only.** Do not treat Mac
  state as representative: an empty `docs/ecp/` here just means "not run on the Mac lately," and the
  local `.venv` exists only because Homebrew Python blocks global `pip` (PEP 668).
- Recorded checkout paths (verify on your box):
  - Windows (home): `C:\Users\Daniel Kinsner\OneDrive\Documents\GitHub\ecp`
  - Windows (work): `C:\Users\SM - Dan\Documents\GitHub\ecp`
  - macOS: `/Users/danielkinsner/Projects/ecp`

## Running the plugin (live, no cache)
This repo is a Claude Code plugin named `ecp`. Load it straight from the working tree —
**never as a marketplace install** (`product.md` §8: no cache copy, no stale-version step):
- **Windows (PowerShell):** `claude --plugin-dir "C:\Users\Daniel Kinsner\OneDrive\Documents\GitHub\ecp"`
- **macOS:** `claude --plugin-dir /Users/danielkinsner/Projects/ecp`

Then inside the session: `/ecp:audit https://your-product-page --visual` (flags: `contracts/flags.md`).

### ⚠️ BEFORE the first `/ecp:audit` on any machine — stale-plugin check
An archived plugin **also named `ecp`** (`ecp@ecommerce-conversion-psychology`, **v1.4.1**, pre-migration
Agent-Teams code + `*-cursor` skills + `ecp-*` agents) collides on the `/ecp:` namespace. A session
started **without** `--plugin-dir` loads *that* one and runs the wrong, old code.
- `--plugin-dir` makes this repo (**v1.0.0**) win for the session (empirically: it collapses the
  double `/ecp:audit` down to the single 1.0.0 command).
- **Verify:** `claude plugin list` → **v1.0.0 = this repo ✅ · v1.4.x = archived ❌.** Backup tell: on
  the clean repo, `/ecp:audit` is the ONLY ecp command — no `*-cursor` skills, no `ecp-*` agents.
- The archived plugin was uninstalled **only on the Mac**; the **Windows boxes likely still have it.**
  Remove with: `claude plugin uninstall ecp@ecommerce-conversion-psychology` (user **and** project
  scope) + `claude plugin marketplace remove ecommerce-conversion-psychology`, then **restart Claude**.

## One-time setup — GLOBAL deps (no per-repo venv), Windows
Install **Python from python.org — NOT the Microsoft Store** (its App-Execution-Alias breaks the
resolver's shell-less probe). Check "Add python.exe to PATH" + "py launcher". **Use Python 3.12**
(3.11–3.13 fine; avoid 3.14 — torch wheels lag; do not mirror the Mac `.venv`'s 3.14.5).

```powershell
pip install "jsonschema>=4.26,<5" "pytest>=9,<10" pillow
#   jsonschema = the ONLY hard runtime dep (pulls `referencing` itself — don't pin it)
#   pytest     = test runner (suite mixes unittest classes + bare pytest funcs)
#   pillow     = undeclared but recommended — true screenshot geometry + un-skips PIL tests
npm install ; npx playwright install chromium          # hotspot-editor smoke tests
npm install -g agent-browser ; agent-browser install   # REQUIRED for a real /ecp:audit (live URL/DOM
                                                       # capture) — NOT the same as playwright
setx ECP_PYTHON "C:\Path\To\python.exe"                # pins the global interpreter deterministically
```
- The Node→Python boundary resolves the interpreter via `scripts/lib/python-cmd.cjs`
  (`ECP_PYTHON` → repo `.venv` → `python3` → `python` → `py -3`). With global installs and **no
  `.venv`**, it lands on `python`/`py -3`; **`ECP_PYTHON` makes it deterministic.**
- ⚠️ It probes `./.venv` **first** — a stale `.venv` in the checkout shadows your global interpreter.
  Delete it, or set `ECP_PYTHON`.
- `sentence-transformers`/`torch` (~500 MB) is **optional + lazy** — only for the Phase J
  finding-stability metric. Skipping it only skips a few tests.

## Tests (run BOTH runners)
```
python -m pytest tests/                # canonical — collects unittest classes AND bare pytest funcs
python -m unittest discover -s tests   # cross-check; unittest-only HIDES pytest-style breakage
```
- Green is **~989 passed** with the optional deps (pillow/sentence-transformers); **~923 passed,
  more skipped** without them — same health, fewer optional tests.
- **Missing `jsonschema` makes the determinism / canonical-frefs canaries *cascade-fail*** (false
  "logic" failures). Install deps first before trusting a red suite.

## Windows gotchas (carried, real)
- **Console encoding:** `set $env:PYTHONIOENCODING='utf-8'` before canary/diagnostic scripts —
  cp1252 console + a non-ASCII `print()` = `UnicodeEncodeError`.
- **Acquisition is the OS-sensitive surface:** `agent-browser eval` on Windows historically mangled
  long / `//`-commented inline JS; `scripts/acquire_url.py` mitigates via base64 (`-b`) encoding.
  (README §Known-limitations still flags this as open — likely stale; verify on Windows.)
- A few operator command snippets in `skills/audit/SKILL.md` / contracts hardcode bare `python` —
  fine on Windows, breaks on a stock Mac (use `python3` / the activated venv there).

## Workflow rules
- **Shared checkout / concurrent Claude windows:** two windows share one `.git`. **Run `git branch`
  immediately before any add/commit/push; stage explicit paths, never `git add -A`** — a sibling
  window moving HEAD can silently land commits on the wrong branch (this has happened).
- **Commit cadence:** branch from `main` → push branch → `git merge --ff-only` to `main` → push →
  delete branch. Trailer: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.
- `docs/ecp/` is **gitignored** (engagement output is working-tree-only) — summarize results inline
  to carry them across machines.
- Source taxonomy (runtime vs contracts vs references vs fixtures vs generated vs archives):
  `docs/CONVENTIONS.md`. Don't assume a file is active runtime just because it's large or recent.
