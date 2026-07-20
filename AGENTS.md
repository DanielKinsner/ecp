# AGENTS.md — non-Claude agent quick-start (Codex, etc.)

This repo is a **Claude Code plugin** (`ecp`, v1.0.0). Per `product.md` §8, Claude Code
is the only runtime in this repo; the Codex/Cursor runtimes are archived. If you are a
non-Claude agent (e.g. a Codex session) working in this checkout:

- **Read [`CLAUDE.md`](CLAUDE.md)** — environment, setup, tests, and workflow rules all
  apply to you too (same checkout, same git discipline, same two test runners).
- **`product.md` is the constitution** — it wins over every other doc, including this one.
- **Current work state / roadmap:**
  [`docs/reviews/2026-06-10-consolidated-findings-and-plan.md`](docs/reviews/2026-06-10-consolidated-findings-and-plan.md).
- Do **not** attempt `/ecp:audit`, `claude plugin …`, or other Claude-Code-specific
  commands from your harness — the plugin runs only inside Claude Code (installed as
  `ecp@ecp`, or loaded live via `claude --plugin-dir <this repo>`).
- **Shared-checkout rule (critical):** concurrent agent sessions share this `.git`. Run
  `git branch` immediately before any add/commit/push; stage explicit paths, never
  `git add -A`.
