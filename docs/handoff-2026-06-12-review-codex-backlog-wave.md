# Handoff — review Codex's post-roadmap backlog wave (written 2026-06-12, work box)

**For:** a fresh Claude Code instance on Dan's home machine (`C:\Users\Daniel Kinsner\OneDrive\Documents\GitHub\ecp`).
**Job:** review the wave of commits Codex is producing against the backlog prompt summarized below, then report ship/no-ship per item. Dan wants explicit recommendations whenever you ask him questions.

## Where the truth lives (do not trust this doc over these)

- `CLAUDE.md` §"Start here" — the live pointer (updated this session: V1–V3 fixed, live gate is the current task).
- `docs/reviews/2026-06-10-post-roadmap-review-and-fix-plan.md` — the backlog's source of truth. Its banner records V1–V3 FIXED 2026-06-12. Codex was instructed to true-up each item's entry as it lands and to append a "U-item verdicts" section.
- `git log` — everything is on `main`. Today's waves, in order:
  - `a5e5e95..671e245` — Codex's V1–V3 fixes (8 commits, already review-verified, done).
  - `73ad205..f263fbf` — Claude follow-ups: e2e `--from-review` guard + point-fallback 0%-coord fix (done).
  - `bb43034..dd46c3d` — doc-hygiene sweep: banner true-ups + 📜 HISTORICAL banners on all stale docs (done).
  - **Everything after `dd46c3d` is the wave under review** (Codex was told to use branch `fix/post-roadmap-backlog`, ff-merged to main).

## What Codex was asked to do (compliance checklist)

Scope: **V4, V5, S1(min), S2, S3, U1–U7, O2** from the fix-plan doc. Key rules it must have followed:

1. Tiny per-behavior commits, guard-test-FIRST (failing test + fix in the same commit), suite green at every commit, conventional messages carrying the item ID.
2. **U1–U7 were VERIFY-FIRST:** for each, Codex had to confirm the claim with a probe/repro, then either (a) fix if small+contained, (b) record CONFIRMED-but-deferred, or (c) record REFUTED with evidence — verdicts appended to the fix-plan doc. **Audit the verdicts, not just the fixes** — verdict quality is the main risk of the unsupervised run.
3. **U2 trap:** corrupt-review-state-weaker-than-no-file is pinned DELIBERATE by `tests/test_g8*:279-294`. Codex was told not to reverse the pinned ruling. Check it didn't.
4. **S3 could not invent behavior:** pin tests only where behavior exists; otherwise a dated DEFERRED note in the fix-plan doc. Check no new product behavior was added to satisfy a test.
5. **S1 was minimum-fix only:** flip `is_offscreen: True` on the reveal placeholder (`scripts/baton_v1_to_v2.py:235`) + rewrite contract text (`workflows/acquire.md:243-268`) to the presence-in-list convention. The full reveal-scoping rework (`acquire_url.py:825-833`) was OUT of scope — flag any drift.
6. Out of scope entirely: V1–V3, O1/O3 (live session — operator-only), product.md, schema changes, live acquisition. Final commits: parity-guard re-floor (~30 below collected) + one CLAUDE.md suite-count true-up.
7. Required done-report: a table item → FIXED <hash> / PINNED <hash> / DEFERRED / REFUTED, all commit hashes, both runners' counts.

## Review protocol that worked on the V1–V3 wave (reuse it)

1. `git log --oneline dd46c3d..HEAD` → map commits to items; read diffs per item, not as one blob.
2. **Prove guard tests pin the bug:** check out the pre-fix source file(s) only (`git checkout <pre-commit> -- <files>`), run the new tests (expect failures), restore (`git checkout main -- <files>`). Green-by-construction tests are the #1 failure mode to catch.
3. **Read the consumer, not just the diff** — e.g. the V2 ellipse fix was only verifiable by reading `scripts/report/templates/components.py` (renderer expects bounding-box + border-radius). Same discipline for V4 (who reads `dpr_requested` downstream?) and V5 (what consumes `variant_source`?).
4. Run BOTH runners and compare to the done-report's claimed counts. Baseline before the wave: 1355 pytest passed / 11 skipped, 895 unittest, parity floor 1336.
5. `$env:PYTHONIOENCODING='utf-8'` before any script that prints non-ASCII (cp1252 console).
6. Shared-checkout rule: `git branch` before any commit; stage explicit paths only.

## Machine notes (home box)

- Home box is ✅ clean of the stale v1.4.1 plugin (per CLAUDE.md). The WORK box remains ⚠️ unverified — irrelevant at home.
- After this review, the next milestone is the **live `--plugin-dir` `/ecp:audit` gate** (LV1–LV4 + O1 on the work box + O2 verification cross-machine — O2's ROOT de-hardcoding is part of the wave under review; verify it actually works from the home checkout path, that's the cross-machine test O2 exists for).

## Suggested skills

- `superpowers:receiving-code-review` mindset in reverse — you are the reviewer; verify claims against code, don't accept the done-report at face value.
- `superpowers:verification-before-completion` — before telling Dan "wave is good", have both runners' output in hand.
- `superpowers:systematic-debugging` / `diagnose` — if a wave commit looks wrong, reproduce before judging.
- `/code-review` — optionally run it over `dd46c3d..HEAD` as a second pair of eyes.

## Context that lives only in the old conversation (already captured above, listed for completeness)

- The exact Codex prompt text (its rules are summarized in the compliance checklist; the fix-plan doc carries the per-item technical detail).
- Dan is in a GitHub-contribution contest (friend at 118, Dan ~98 + this wave) — tiny commits are a feature; never suggest squashing. All commits must be real work, no padding.
