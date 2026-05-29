# Handoff — 2026-05-28 Cursor-migration completion batch

**Audience:** Dan (picking this up on a *different* work computer) + the next Claude. Anything not in the committed repo is captured inline. `docs/ecp/` is gitignored.

**Previous handoff:** [docs/handoff-2026-05-28-observability-batch.md](handoff-2026-05-28-observability-batch.md) (G21–G24 + the `e4050c0e` engagement forensics). Read it second if cold-starting; the one before it is [docs/handoff-2026-05-27-conformance-batch.md](handoff-2026-05-27-conformance-batch.md). **This doc is the delta on top of the observability batch.**

**Session window:** 2026-05-28 afternoon (single session), originating machine `C:\Users\Daniel Kinsner\OneDrive\Documents\GitHub\ecp`. This session did NOT run an audit — it finished the prune-and-re-root migration off the archived Cursor/Codex repo.

---

## 0. ⚠️ READ THIS FIRST IF YOU'RE ON THE WORK COMPUTER (Dan: this is the one that bites)

The biggest fix this session was **not in the repo** — it was uninstalling a stale plugin. **That uninstall happened only on the home machine's `~/.claude`.** The work computer very likely still has the old plugin installed, and if so your "first thing" audit will run the WRONG, pre-fix code.

**Before running `/ecp:audit` on the work machine, verify which `ecp` is active:**

```
claude plugin list | Select-String -Context 0,2 ecp      # PowerShell
# or: claude plugin list   (look for any ecp@ecommerce-conversion-psychology entry)
```

- **If you see `ecp@ecommerce-conversion-psychology` (v1.4.1 or any version):** that's the archived-repo plugin. It shadows the clean repo on the `ecp:` namespace and is the source of all the `*-cursor` skills + `ecp-*` agents. Remove it (it may be installed at user AND project scope):
  ```
  claude plugin uninstall ecp@ecommerce-conversion-psychology --scope user
  claude plugin uninstall ecp@ecommerce-conversion-psychology --scope project   # ok if this says "not installed"
  claude plugin marketplace remove ecommerce-conversion-psychology
  ```
  Then **restart Claude** (uninstalled skills stay loaded in the running session until restart).

- **Load the clean plugin** per `product.md` §8 — it is NOT a marketplace install:
  ```
  claude --plugin-dir <path-to-cloned-ecp-repo>
  ```
  The repo is `https://github.com/Dannytownkins/ecp` (clone it on the work box if needed). `/ecp:audit` then resolves to the clean, fully-patched plugin.

Sanity check you're on the clean one: `/ecp:audit` should be the **only** ecp audit command (no `audit-cursor`, no `build`/`compare`/`quick-scan`/`resume`, no `ecp-orchestrator` agent in the type list). If you still see those, you're on the old plugin.

See the updated memory `project_ecp_plugin_marketplace.md` for the full rationale.

---

## 1. Where `main` is

```
c3de949  Rename canonical acquirer cursor_bootstrap_url.py -> acquire_url.py
5a16c5d  Clean stale migration residue: package.json identity + Cursor-framed docstrings
a0e6aba  Move frozen Cursor agents out of Claude Code discovery scope (G21)
4380817  Add handoff doc for the 2026-05-28 observability batch   <- prior handoff tip
```
(This handoff doc will be the commit on top of `c3de949`.)

**Both runners green on `c3de949`:**
- `pytest tests/` → **779 passed, 13 skipped, 47 subtests passed**
- `python -m unittest discover -s tests` → **514 ran, 1 skipped**

> **Doc-discrepancy note for the next agent:** the *observability* handoff recorded `690 passed` for its tip. Actual on a fresh checkout was `777` (then `779` after this session's +2 tests). The `690` was a recording error in that doc — both runners were always clean. Don't chase it.

Commit-level detail: [CHANGELOG.md](../CHANGELOG.md) "session 7" entry (G21) covers the agent relocation; the rename + package.json cleanup are in their commit bodies. Roadmap: [docs/conformance-gaps.md](conformance-gaps.md) — G21 entry under "Observability".

## 2. What closed this session (in commit order)

All three are fully described in their commit messages + CHANGELOG/conformance-gaps; **not duplicated here**. One-line each:

1. **`a0e6aba` — G21.** Five `ecp-*` Cursor agent prompts `git mv`'d `agents/` → `archive/cursor-agents/` (out of Claude Code's `agents/*.md` auto-discovery). Added `archive/cursor-agents/README.md` (freeze rationale + un-freeze recipe), a non-existence regression guard [tests/test_g21_cursor_agents_not_discoverable.py](../tests/test_g21_cursor_agents_not_discoverable.py) (mirrors G17's `test_old_constant_is_gone`), conformance-gaps + CHANGELOG entries.
2. **`5a16c5d` — stale identity.** `package.json` was still `name: "ecommerce-conversion-psychology"` with old-repo git/bugs/homepage URLs, a shields.io badge blob (incl. a "Codex skill" badge) as its description, ISC license (vs MIT in `plugin.json`). Realigned to the canonical `ecp` identity. Reworded 3 `scripts/ecp_{acquire_dom,configurator,section_hints}.py` docstrings that called themselves "Cursor" helpers.
3. **`c3de949` — rename.** `scripts/cursor_bootstrap_url.py` → `scripts/acquire_url.py` (history preserved). Updated every **live** reference: SKILL "Dispatch Shape", `workflows/acquire.md` (3), README, `docs/conformance-gaps.md`, and 5 tests (the module is only imported by tests + invoked as a subprocess from markdown — no production import, so the suite is the safety net).

## 3. The migration finding (the "why" behind the plugin uninstall)

G21 fixed the in-repo agent surface, but the agents/skills *kept showing in discovery* because the **archived-repo plugin `ecp@ecommerce-conversion-psychology` v1.4.1 was still installed (user + project scope)** and shares the `ecp:` plugin name → namespace collision. It carried its own copies of the agents + all the Cursor/frozen-mode skills (`audit-cursor`, `build-cursor`, `compare-cursor`, `quick-scan-cursor`, `resume-cursor`, the `ecp-cursor` router, and the frozen `build`/`compare`/`quick-scan`/`resume` modes). Uninstalled this session **on the home machine only** (see §0 for the work machine). The clean repo is meant to load ephemerally via `claude --plugin-dir` per `product.md` §8 — it is not, and should not become, a marketplace install.

## 4. Deliberately NOT changed (decisions, not misses)

- **`"cursor"` in `references/{cta-design-and-placement,grid-layout,pagination-patterns}.md`** → the *mouse* cursor (Fitts's law, touch-target precision, cursor-based pagination APIs). Domain content. Leave.
- **`Codex Qn` / `Closes Codex review` comments** across ~40 files in `scripts/`, `contracts/`, `schema/` → legitimate design-rationale provenance (Codex was a review pass during development). NOT dead pointers like the G10 `docs/plans/` scrub. A blind sweep would destroy real "why this exists" context. The `product.md` §8 Codex/Cursor references are the spec's runtime history — also keep.
- **CHANGELOG ledger, the two dated `docs/handoff-*` snapshots, frozen `archive/cursor-agents/*.md` agent prompts** → still contain `cursor_bootstrap_url.py` by design. Dated/frozen records; rewriting history is worse than the stale name. `docs/conformance-gaps.md` historical entries got `(then cursor_bootstrap_url.py)` breadcrumbs instead.
- **`tests/fixtures/2026-05-02-9cd2a2ac/{build_baton,_build_baton_mobile}.py`** still reference the old repo name in path/comment → frozen test fixtures, low value, left.

## 5. What your "first thing" live `/ecp:audit` will exercise (delta from prior handoff)

Everything in the observability handoff §6 still applies (the **6th canary `trace_counters_reconcile_with_artifacts`**, `meta.json` `reflection_state: draft|complete`, the `--mark-reflection-complete` verb at SKILL step 15). New/affected this session:

| Watch for | Where |
|---|---|
| **Acquirer runs as `scripts/acquire_url.py`** (not `cursor_bootstrap_url.py`) | The acquirer subagent invocation per `workflows/acquire.md` / SKILL "Dispatch Shape". If anything still calls the old name, the acquire phase fails — that's the one thing the rename could surface live (tests cover the import path; a live subprocess invocation is the last mile). |
| **No Cursor skills/agents in discovery** | After the §0 work + restart: `/ecp:audit` is the only ecp command; no `ecp-orchestrator` delegation option offered at the dispatch checkpoint. |
| **`reflection_state` ends at `complete`** | `meta.json` at audit end — `draft` means the lead skipped the `--mark-reflection-complete` attestation (discipline gap worth noting). |
| **`audit-trace.log` counters reconcile** | 6th canary line `acquirers=N/N, specialists=N/N, ethics=N/N, synthesizer=N/N`. The `e4050c0e` run had all-zero counters; this should now FAIL loudly if the lead under-counts. |

**Per the prior handoffs' hard-won lesson: evidence first.** Every confident pre-data hypothesis got corrected by the next data point (the `e4050c0e` "synth didn't run" that turned out to be a stale lead-reflection is the cleanest example). Let the run surface what it surfaces.

## 6. What's open (carried + this session)

| # | Item | Status |
|---|---|---|
| Opus-by-default specialists | §10 Spec Change Log decision — cost ~+75%/audit, reduces sonnet-drift autofixes. **Draft on request.** | Not started; flagged in observability handoff §4 |
| v2 specialists: Task subagent vs Agent teammate by default | §10 decision. Amazon `0669899d` proved Task works for v2 (which opts out of the mailbox anyway). **Draft on request.** | Not started; observability handoff §4 |
| Lead-reflection-stale canary | When `phase: complete` but `reflection_state: draft`, flag it. G23 built the state machine; this is the consumer-side check. | One-line add to `run_all_canaries` if wanted |
| `specialist-content-seo-desktop` wrote the lead's `lead-reflection.md` | Scope violation independent of G23 (a specialist shouldn't write the lead's file). G23 closed the *trust* surface; the *ownership* surface is open. | Possible file-ownership check in `atomic_write` or a `specialist-prompt-v2.md` prohibition |
| Backlog #3 — teammate dispatch reliability | Can't fix in-repo (Claude Code Agent-tool level). | Unchanged |
| Backlog #6 — `visual_quality` all-zeros on v2 emissions | Needs a clean v2 review-state fixture from a live run. | Unchanged |
| G3 / G9 (P3) | DOM-present-not-displayed canary; ISN'T-list copy spot-check. | Optional |

## 7. Suggested skills for the next session

| Skill | When |
|---|---|
| `verify` | After the first `/ecp:audit`, before claiming the migration/canaries hold — inspect the engagement dir for: `acquire_url.py` actually ran the acquire, `meta.json` `reflection_state`, the 6th `trace_counters_reconcile` canary line, `canonical-frefs-dropped.json`, autofix repairs log. |
| `verification-before-completion` | Before pushing any post-handoff commit — run `pytest tests/` + `python -m unittest discover -s tests` and confirm both green (this repo's invariant: verify BOTH runners; unittest alone hides pytest-style breakage). |
| `code-review` | If a follow-up touches >~200 lines or the canary suite. |
| `brainstorming` | Before drafting either §10 Spec Change Log entry (opus-default, Task-vs-teammate) — the fix shape isn't obvious and these are deliberate spec changes. |

NOT suggested: `tdd` (surgical fixes don't need it), design skills (out of scope).

## 8. Conventions a fresh agent should know (delta — rest in prior handoffs §10)

- **Commit cadence:** branch from `main` per commit set → push branch → `git merge --ff-only` to main → push main → delete the merged branch (local + remote). Commit-and-push-to-main without asking is authorized for ECP roadmap/cleanup work (memory `project_ecp_commit_cadence`).
- **Commit trailer this session:** `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>` (harness-specified; prior sessions used 4.7).
- **`product.md` is the constitution.** §5 frozen scope unfreezes ONLY via a §10 Spec Change Log entry. To freeze something *operationally*, delete the discoverable surface — don't just mark it out-of-scope in prose (G16/G17/G21/G22+G24 are all instances of this same lesson).
- **`docs/ecp/` is gitignored** — engagement evidence is working-tree only; summarize inline in docs to carry it across machines.

## 9. Working-tree state (originating machine, at time of writing)

Clean. `git status` shows nothing uncommitted after the handoff commit. No per-engagement scratch files this session (no audit was run). The home machine's `~/.claude` plugin state was modified (old plugin uninstalled) — that's local config, not repo.

---

_End of handoff. Dan: the §0 work-machine plugin check is the one thing that'll silently ruin your first audit if skipped — do it before `/ecp:audit`. Everything else is committed and pushed. Cheers._
