# Handoff — Cross-OS hardening + CLAUDE.md (the dynamic-workflows feature is still TODO)

> **📜 HISTORICAL — banner added 2026-06-12.** Point-in-time handoff (2026-06-01); the title's "still TODO" no longer reflects the queue. Superseded as a work pointer by the consolidated 2026-06-09/10 roadmap ([reviews/2026-06-10-consolidated-findings-and-plan.md](reviews/2026-06-10-consolidated-findings-and-plan.md), EXECUTED) and its post-roadmap fix plan ([reviews/2026-06-10-post-roadmap-review-and-fix-plan.md](reviews/2026-06-10-post-roadmap-review-and-fix-plan.md)). Re-triage anything that still looks undone against the current chain — CLAUDE.md §"Start here" is the live pointer.

**Date:** 2026-06-01
**Status:** Done and **on `main`** (commits `e089366`, `c1ba55c`, `49c5962`, + this doc). Test suite green.
**Author:** Claude (Opus 4.8), on the macOS porting box (~5–10% machine; Dan is Windows-primary).
**Audience:** the next agent (likely on Windows) + Dan.

---

## 0. Read this first — what this session was NOT
This session did **not** touch the headline goal: **adding dynamic workflows to the ECP plugin.**
The original ask ("use dynamic workflows to fix everything") turned into *using* the Workflow tool to
run a **cross-OS hardening pass** + write an environment doc. Useful, but orthogonal to the feature.

**The dynamic-workflows work is still entirely open. The plan for it already exists:**
`docs/2026-05-31-dynamic-workflows-determinism-plan.md` — **start there** (see §3).

---

## 1. What landed on `main` this session
| Commit | What |
|---|---|
| `e089366` `fix(tooling)` | **Cross-platform Python resolution** at the Node→Python boundary. New `scripts/lib/python-cmd.cjs` (`ECP_PYTHON` → `.venv` → `python3` → `python` → `py -3`); `package.json check:python`, `serve-editor.cjs`, `editor-smoke.mjs` route through it. `requirements-dev.txt` declares `pytest`. Editor-server smoke hardened to not pass vacuously. |
| `c1ba55c` `docs(contracts)` | Finished the **teammate→subagent terminology cleanup** in `dispatch-contract.md` + `audit-reconciliation.md` (the `§6` residuals from the specialists-off-Agent-Teams migration). Guard module still 18/18. |
| `49c5962` `docs` | New **`CLAUDE.md`** (auto-loaded env/workflow guide) + README Windows-setup parity (dev deps, chromium, the `agent-browser` global). |

**Root cause that motivated commit 1:** the tooling hardcoded `python`, which doesn't exist on
macOS/Linux (only `python3`). It was never broken on Windows — so on Dan's primary OS this is
**neutral-to-positive, but validated only on macOS.** See §4.

## 2. Verify on pickup
```
python -m pytest tests/             # ~923 passed on macOS w/o optional deps; ~989 with pillow + sentence-transformers
python -m unittest discover -s tests   # cross-check (unittest-only hides pytest-style tests)
npm test                            # check:editor + check:python + chromium editor smoke
```
Load the plugin: `claude --plugin-dir <repo>` (NOT a marketplace install). **Before the first
`/ecp:audit` on Windows, run the stale-plugin check in `CLAUDE.md` §"stale-plugin check"** — the
archived `ecp@ecommerce-conversion-psychology` v1.4.1 was only uninstalled on the Mac.

---

## 3. THE HEADLINE WORK (still TODO): dynamic workflows for the plugin
Per `docs/2026-05-31-dynamic-workflows-determinism-plan.md`, in priority order:

1. **Build the determinism-gate workflow FIRST.** `scripts/run-determinism-gate.py`'s loop
   (`for N: prep → fan out ~20 specialists → barrier → ethics → build-frefs → synthesizer →
   validate → aggregate`) is a dynamic workflow currently *run by hand* over 5–12 hours. Converting
   it to a saved `.claude/workflows/` script removes lead-orchestration drift from the measurement.
   The plan calls this "exactly the audit-the-plugin-with-a-workflow idea — build this first."
2. **(Later) the `/ecp:audit` production spine as a saved workflow** — makes validation + the
   drop-check *mandatory stages* instead of per-run discipline. Hardening, not a determinism cure.
3. **(§7 addendum) agentic report-QA workflow** — automates `product.md` §6's draft→client-ready
   gate (verify hotspots/citations/claims, loop until clean). A PoC already exists as the
   `ecp-report-qa` skill and reportedly caught a materially false finding + a mis-cited claim.

**Plugin-mechanics reality (confirmed in the plan §3.4):** a Claude Code *plugin* cannot ship or
auto-run a workflow — `workflows/` is not a plugin component. The viable shape is a **saved script
in `.claude/workflows/`** in this repo (project-scoped, version-controlled), invoked opt-in.

> Note: the plan also concludes dynamic workflows do **not** fix the run-to-run non-determinism
> (that's live-page drift + LLM word-choice + a few concrete bugs). Don't sell workflows as a
> determinism cure. See the plan's §2.

---

## 4. Deferred cross-OS fixes — kept SEPARATE on purpose (Dan's call)
These were found this session but **intentionally not bundled**, so whoever implements them (on
Windows, where they can validate + troubleshoot in the moment) owns each one:

| # | Item | Location | Action |
|---|---|---|---|
| 4 | README "Known limitations" Windows acquisition bug looks **already fixed** in code (base64 `-b`) | `README.md:83-87` vs `scripts/acquire_url.py:399-411` | Verify all eval sites route through `_eval_args`, then reword/remove the limitation |
| 5 | `_run`/`_run_ab` use `text=True` with no `encoding=` → **cp1252 mojibake on Windows** | `scripts/acquire_url.py:300,316` | Add `encoding="utf-8", errors="replace"` to match `_run_capture` |
| 6 | `report-export.md` python resolver is `python`-first (ignores `py -3` / `ECP_PYTHON` / `.venv`) | `contracts/report-export.md:17-18` | Align with `resolvePython()` or prefer `node serve-editor.cjs` |
| 7 | Operator snippets hardcode bare `python` (break on stock Mac) | `skills/audit/SKILL.md:127,131,137,145,151,156,163`; `contracts/meta-schema.md:96,107` | Use `python3`/activated venv on Mac |

Benign (spent scaffolding, no action): `tests/fixtures/2026-05-02-9cd2a2ac/build_baton.py:3` +
`_build_baton_mobile.py:4` hardcode a `C:\Users\Daniel Kinsner\OneDrive\...\ecommerce-conversion-psychology\...`
path into the *other* repo; their output is committed and nothing re-runs them.

---

## 5. Still-open runtime proof (separate from everything above)
The **live `/ecp:audit` smoke run** (`handoff-2026-06-01-specialists-off-agent-teams-complete.md` §5.1)
remains the one thing the green test suite cannot prove: that specialists dispatch as one-shot
subagents at runtime with **zero team creation**. Run a real audit on Windows and watch for: no
team create/delete, one full-parallel specialist batch, non-zero `subagent_spawned_specialists`,
file-presence collection, completion canary passes.

## 6. Cross-machine setup is now documented
`CLAUDE.md` (repo root, auto-loaded) carries the Windows-primary reality, the `--plugin-dir` launch
command + stale-plugin check, the global-deps install (python.org not Store; Python 3.12;
`agent-browser` global; `ECP_PYTHON` to pin the interpreter), the both-runner test rule, and the
shared-checkout / cp1252 / acquisition-eval gotchas. New agents should read it before acting.
