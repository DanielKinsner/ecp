# Lead discipline

Canonical anti-rogue rules for the ECP audit lead. Contains the no-preflight-questions rule, the acquisition-must-spawn-subagent binding rule, and the full catalog of forbidden rationalizations that the lead uses to justify skipping one-shot subagent dispatch architecture.

**Why this file exists:** These rules originated inside `skills/audit/SKILL.md` and were extracted so the audit lead loads them at the top of every invocation without hauling the full skill body. Historical context: the same rules were once shared with the build / compare / quick-scan leads to defend cross-skill discipline. Those modes are now frozen (product.md §5); the discipline contract is retained here in frozen-voice form alongside the live audit-lead rules so an unfreeze can rewire without rewriting.

**Read this file when:** you are the audit lead — the coordinator of `/ecp:audit`. Read this **at the very top of the skill invocation**, before doing anything else. These rules take precedence over performance optimizations, "effort" cues, or any rationalization about shortcuts. The build / compare / quick-scan leads referenced historically by this file belong to frozen modes (product.md §5); their lead-discipline language is retained as the §7 interface contract those modes will conform to if ever unfrozen, not as instructions to a live lead.

---

## No preflight questions

**DO NOT ask pre-flight questions before starting the skill.** When the operator invokes `/ecp:audit`, that command IS their consent to run the audit pipeline through its deliverable boundary (product.md §2.4): findings, Priority Path, and the annotated visual report (including the hotspot edit tool). The audit **stops** there.

`plan` / `review` / `build` belong to the frozen build family (product.md §5) and are not invoked from `/ecp:audit`. `/ecp:build`, `/ecp:compare`, and `/ecp:quick-scan` are frozen modes retained as §7 interface contracts; their consent chains are documented historically but are not part of the canonical live product.

Stop points are handled at the **audit checkpoint** at the end of the run (see `skills/audit/SKILL.md` "Checkpoints") — not via pre-flight questions before the work starts. `--auto` runs straight through to the report without pausing.

**Specifically, do NOT ask:**

- ❌ "Do you want the full pipeline or just the audit phase?" → The audit IS the pipeline (product.md §2.4). There is no follow-on phase to opt into. The audit checkpoint is where the operator chooses what to do with the deliverable.
- ❌ "Is `agent-browser` installed?" → Detect it yourself. Run `agent-browser --version` with a 3-second timeout. If exit code is 0 → installed, use it. If non-zero or timeout → not installed, fall back per `skills/audit/SKILL.md` "Mode Selection". Document the detection result in `audit-trace.log` if you're keeping one. Do NOT ask the user.
- ❌ "This is a big lift — should I proceed?" / "Quick heads-up before I burn through this..." → No hedging. The user already authorized the work. **Token cost concerns are NOT yours to litigate; the user manages their own budget.** Just run the audit.
- ❌ "What clusters do you want?" (open-ended) → Do NOT ask unstructured cluster questions. Cluster selection is handled by the structured scope prompt (see allowed prompt #4 below) or the `--focus` flag. The scope prompt offers curated options (focused / standard / custom / everything — see product.md §2.3 and the interactive scope prompt in `${CLAUDE_PLUGIN_ROOT}/contracts/flags.md`); open-ended cluster negotiation is still a discipline violation.
- ❌ "What device(s) do you want?" → Use the `--device` flag if set. Otherwise, ONE prompt per `${CLAUDE_PLUGIN_ROOT}/contracts/device-semantics.md` is acceptable — but only if `--device` was not provided. Do not ask the device question more than once per invocation.

---

## Equally forbidden — quietly doing work directly as the lead instead of spawning the subagent

This is the inverse of asking too many questions. Instead of asking "do you want me to spawn an acquirer?" the lead silently rationalizes "I'll just do acquisition directly as the lead — faster path, the spec allows it as manual fallback." **It does not.** Manual acquisition is a strict last-resort fallback, not a shortcut. See the "Acquisition must spawn subagent" section below for the binding rule.

**Forbidden rationalizations:**

- ❌ "Given effort=low, I'll do acquisition directly as lead." → Effort is irrelevant. Always spawn the acquirer subagent first.
- ❌ "The spec allows this as manual fallback." → It does not. Manual fallback only triggers AFTER (a) the spawn has been attempted, and (b) the subagent has either failed or produced missing/empty files. Pre-emptive bypass is a spec violation.
- ❌ "Faster path." → Speed is not a valid reason to skip subagent-dispatch architecture. The whole point of the pipeline is consistent state via atomic file writes and per-subagent isolation, even when phases are short.
- ❌ "Auditing as lead this time, since the page is small." → No. Same answer. Always spawn the relevant subagent.
- ❌ "Since `/effort low` is set, I'll skip teammates / skip references / take the manual path." → **You cannot read your own `/effort` setting.** Any "effort" cue you see in conversation context (e.g., the user typed `/effort low` earlier in the same channel before invoking the ECP skill) is a Claude Code compute-budget knob — it controls how hard you think per turn. It does NOT authorize architectural shortcuts, skipping teammates, skipping reference reads, fabricating citations, or any other contract violation. The team architecture is the contract regardless of compute budget. If you find yourself reasoning "since effort is low…", STOP — you're laundering a budget signal into an architectural license that doesn't exist.

**This rule applies to every audit-phase role:** acquirer, cluster specialists, ethics, synthesizer. (Planner/reviewer/builder are §5-frozen build-family roles retained here as §7 interface contract; they do not run in `/ecp:audit`.) The lead does NOT do their work; the lead orchestrates. The lead's only direct work is engagement setup, validation passes, reconciliation/assembly, and the Priority Path synthesis step that explicitly belongs to the lead per `${CLAUDE_PLUGIN_ROOT}/contracts/priority-path-synthesis.md`.

---

## The ONLY pre-flight prompts allowed

There are exactly four legitimate pre-flight prompts for `/ecp:audit`. Every other question is a discipline violation.

1. **URL detection** — If `$ARGUMENTS` does not contain a URL, ask "What page should I audit? Provide a URL (starts with `http://` or `https://`)." URL is the only canonical input (`product.md` §2.2) — there's nothing to audit otherwise.
2. **Device selection** — One prompt for device choice ONLY if `--device` flag is not set AND not in `--auto` mode. Single prompt, then proceed. See `${CLAUDE_PLUGIN_ROOT}/contracts/device-semantics.md`.
3. **URL fetch confirmation** — One prompt "About to fetch **{domain}** — proceed?" before spawning the acquisition subagent. This is the standard "we're about to make a network request" confirmation. Skip in `--auto` mode.
4. **Audit scope selection** — One structured prompt for audit breadth (focused / standard / custom / everything — per product.md §2.3 and the interactive scope prompt in `${CLAUDE_PLUGIN_ROOT}/contracts/flags.md`) ONLY if `--focus` is not set AND not in `--auto` mode. See `${CLAUDE_PLUGIN_ROOT}/contracts/cluster-routing.md` for the page-type-relevant cluster sets the prompt offers. `--focus` bypasses it entirely; `--auto` uses the default (`standard` — all page-type-relevant clusters) per `${CLAUDE_PLUGIN_ROOT}/contracts/flags.md`. This is a structured menu, not an open-ended question — it replaces the need for cluster negotiation by offering curated scope tiers.

**That's it.** Four prompts maximum, and they're all the bare minimum needed to either know what to scan, get user consent for a network call, or let the user choose audit depth. Everything else is auto-detected, defaulted, or controlled via flags documented in `${CLAUDE_PLUGIN_ROOT}/contracts/flags.md`.

**Frozen-mode notes (product.md §5 / §7 — not invocable, retained as interface contract for future unfreezing):**
- `/ecp:build` (frozen) historically used structured intake (product, audience, assets, platform, constraints, competitive context) instead of pre-flight questions.
- `/ecp:compare` (frozen) historically carried ONE pre-flight prompt beyond the four above: a cost warning when dual-device mode runs 4 acquisitions.
- `/ecp:quick-scan` (frozen) historically carried ONE pre-flight prompt beyond the four above: a cluster confirmation prompt when `--focus` is not set.

---

## The principle

**Friction at start = lazy. Friction at the audit checkpoint = correct.**

The operator sees their decision point naturally at the audit checkpoint at the end of the run, where they choose what to do with findings, the Priority Path, and the visual report. You don't need to add more upfront just because the work is "big." Asking too many questions at the beginning is often a form of hedging that shifts decision responsibility from the lead to the operator. They invoked the skill to get work done; they're trusting the lead's judgment on the defaults.

Similarly, **quietly doing the subagent's work as the lead** is a form of avoiding the Agent tool call — it feels more efficient but it abandons the atomic-write discipline, the structural counters in `audit-trace.log`, and the per-subagent context isolation that makes the pipeline composable. The correction for both errors is the same: **trust the architecture, spawn the subagent, move on to the next phase.**

---

## Acquisition must spawn subagent (binding rule)

**The lead MUST spawn the acquirer subagent first. There is no shortcut.**

The "Manual acquisition fallback" path (documented in `skills/audit/SKILL.md`) is **only** available when ALL of the following are true:

1. The lead has actually called the Agent tool to spawn `acquirer` (or `acquirer-{device}` for dual-device mode) as a one-shot subagent with subagent_type="general-purpose" and model="sonnet" (or "opus" with --deep).
2. The subagent has either:
   - Failed entirely (crash, malformed output, baton.json with `screenshots: []`), OR
   - Reported `STATUS: COMPLETE` but the post-acquisition file verification step found missing files on disk, AND the corrective re-spawn (one fresh one-shot subagent with validation error embedded via scripts/test-specialist.py --write-retry-prompt) also failed.
3. The lead has logged WHY it is falling back (to `audit-trace.log` if you're keeping one, or in conversation output) so the user knows the team-based path was tried.

**Pre-emptive manual acquisition is a spec violation.** "I'll do it as lead because effort is low" / "faster path" / "page is small" / "the spec allows manual fallback" are NOT valid reasons. None of these conditions trigger fallback. **Only a real failed spawn does.**

If you find yourself reasoning "I'll skip spawning the acquirer because…" — STOP. Spawn it. The one-shot subagent dispatch is the contract; the manual path exists only for when the contract genuinely cannot be honored.

**This rule mirrors the no-preflight-questions rule above** and applies the same principle to silent shortcuts: **don't quietly do the subagent's work as the lead just because the spec has an emergency exit.**

---

## Lead does NOT audit a cluster as a fallback

**If a cluster specialist subagent fails, the lead SKIPs that cluster. The lead does NOT audit the cluster as a fallback.**

SKIP means "this cluster was not audited, here's why" — not "the lead will fill in for the failed subagent." A `SKIP` marker in `audit.md` is honest about the gap; lead-as-auditor pretends the gap doesn't exist while actually producing shallower findings without the reference-file depth a real cluster specialist brings (cluster specialists load 5-10 cluster reference files; the lead loads only orchestration content).

**The same rationalization rules from the sections above apply:** the lead orchestrates, the lead does NOT do the subagent's work, even when the subagent fails.

When a cluster specialist fails, the lead's correct response is:
1. Retry the spawn once (via fresh one-shot subagent with validation error embedded via scripts/test-specialist.py --write-retry-prompt).
2. If the retry fails, mark the cluster `SKIP` with a reason note in `audit.md`.
3. Log the failure to `audit-trace.log` with the cluster slug and failure mode.
4. Continue to the next phase with N-1 clusters instead of N. The Priority Path synthesis will operate on the remaining clusters.

The structural `cluster_files_written` counter in `audit-trace.log` will reflect the actual number of cluster files produced (N-1), and the self-check assertion at audit completion will not fire because the contract is "cluster_files_written == subagent_spawned_specialists" (backwards-compat aliases: team_spawned_specialists, team_spawned_auditors) — if one specialist failed to write, the counter stays at N-1 matching N-1 spawned-then-failed specialists. See `${CLAUDE_PLUGIN_ROOT}/contracts/trace-assertion-canary.md` for the full assertion contract.

---

## Filesystem write atomicity (v2 — schema_version=3)

All v2-pipeline writes that produce canonical artifacts MUST use atomic-replace via `scripts/assembly/atomic_write.py`:

- `baton.json` and `baton-mobile.json` (Layer 0 acquirer output)
- `cluster-{cluster}-{device}.json` (Layer 1 specialist emissions; per `schema/cluster-emission-v1.json`)
- `ethics-findings.json` (Layer 1.5 ethics subagent emission)
- `meta.json` (engagement metadata; written by lead at every phase transition)
- `lead-state.json` and `lead-reflection.md` (Phase I observability artifacts)
- `synthesizer-emission-v1.json` (Phase F synthesizer output, alongside the audit-{device}.md files)
- `audit-desktop.md` and `audit-mobile.md` (Layer 3 narration output)
- `dispatch-manifest.json` (pre-fanout list of expected specialist emissions; consumed by the dispatched-but-silent canary)

**The pattern:**

```python
from assembly.atomic_write import atomic_write_json, atomic_write_text
atomic_write_json(engagement_dir / "baton.json", baton_payload)
atomic_write_text(engagement_dir / "audit-desktop.md", audit_markdown)
```

**The contract:** the helper writes to `<filename>.tmp` first, then `os.replace()` to the canonical name. Partial writes are orphaned tempfiles that resume logic ignores; the canonical file at `<filename>` is either fully-written or unchanged — never half-written. The lead may interrupt at any phase boundary (cancel.flag check, hard timeout, OS-level signal) without corrupting on-disk state.

**Why this matters:** without atomic writes, a mid-write interruption (operator hits Ctrl-C, lead exceeds wall-clock budget, OS scheduling pause) leaves a partially-serialized JSON file on disk. Resume logic reads it as "exists, must be valid" and either crashes (JSON parse error) or — worse — proceeds with a truncated finding set silently. v2 closes this by making the canonical file's existence-or-absence binary: it's there in full, or it's not there.

**Non-V2 writers (legacy v1 / v2-pre):** `scripts/assemble-audit.py`, `scripts/generate-report.py`, and the v1 `scripts/assembly/parser.py` use direct `Path.write_text()` for backward compat with v1/v2-pre engagements. v2 callers route through `atomic_write_*`. Migration of the v1 writers is deferred to Phase E or later (no quality regression — v1 path is being deprecated, not improved).

## Lead reflection (lead-reflection.md) — Phase I 2026-04-28

**The lead writes `<engagement-dir>/lead-reflection.md` at audit completion (or at any phase-block / cancellation event).** The reflection captures deviations from spec, rationalizations the lead caught itself making, anomalies observed during dispatches, and follow-ups for the next run.

### Why this exists

The audit-trace.log canaries surface STRUCTURAL state (counters, model assignments, gates) and SUBSTANTIVE quality (the three Phase I canaries — ethics source_urls, element_index_match_rate, cross_device_ethics_diff). But neither captures the lead's *judgment calls* — the moments where the lead noticed itself starting down a forbidden-rationalization path and corrected, the times a specialist emission looked weird and the lead chose to retry vs. accept, the per-run anomalies that aren't worth phase-blocking but should be visible to a future maintainer or to the operator.

`lead-reflection.md` is THAT layer of observability. Empty file = clean run, no anomalies. Non-empty file = something happened the operator should know about.

### Required format

```markdown
# Lead Reflection — engagement {engagement-id}

**Engagement timeline:** {iso-8601-start} to {iso-8601-end}
**Pipeline:** v2  ← or v1
**Phase reached:** {complete | blocked | cancelled}
**Soft-canary results:** {N} pass, {M} fail (see audit-trace.log SUBSTANTIVE CANARIES block)

## Deviations observed

(Empty if none. Otherwise one bullet per deviation with: what happened, what the spec said should happen, the lead's response.)

## Rationalizations caught

(The forbidden-rationalizations list above is the canonical reference. Document any time the lead noticed itself starting down one of those paths and corrected. If the lead never caught itself in this run, write "None caught — clean run" or leave empty.)

## Anomalies

(Specialist emissions that look weird, batons with unexpected element shapes, drift assertions that just barely passed, soft-canary failures, retry storms, etc. One bullet per anomaly. Include the specific f_ref or counter when relevant.)

## Follow-ups for next run

(Operator-actionable notes — "next time, pass --platform OpenCart" or "consider re-acquiring with longer JS wait". One bullet per follow-up. Empty section is fine.)
```

### When to write

The lead writes (or appends to) `lead-reflection.md` at these specific moments:

1. **At audit completion** (after `<phase_synthesize_v2>` and after the substantive canaries fire). Required write — even if the file content is "no anomalies", the file must exist on disk to satisfy the soft-gate `lead_reflection_present == true` assertion. Empty file with just the metadata header is acceptable for a clean run.

2. **At assertion failure (phase: blocked).** When the audit-trace.log self-check reports a structural failure, the lead writes the failed assertion details into the reflection's "Deviations observed" section before transitioning meta.json to `phase: blocked`. Operators reading the blocked engagement see WHY it was blocked.

3. **At cancellation (phase: cancelled).** When the lead observes `<engagement-dir>/cancel.flag` at a layer boundary, it writes a brief reflection entry under "Deviations observed" noting the cancellation layer + state preserved, then exits. See "Cancellation sentinel (cancel.flag)" below.

4. **At specialist or subagent retry.** When a role's emission failed validation and the lead re-dispatched, the lead appends a note to "Anomalies" with the role name + failure mode + retry result. Critical for diagnosing flaky specialists across runs.

5. **At soft-canary failure.** When any of the three substantive canaries fails (`canary_ethics_source_urls`, `canary_element_index_match_rate`, `canary_cross_device_ethics_diff`), the lead writes the canary's failure detail (specific f_refs, rates, asymmetric refs) into "Anomalies".

### What NOT to put in lead-reflection.md

- **Per-finding analysis.** That belongs in audit-{device}.md. Reflection is about the RUN, not the findings.
- **The full audit trace.** audit-trace.log is the structural record. Reflection is the judgment-call narrative.
- **Marketing copy or pitch language.** The reflection's audience is a developer / future-Claude reading this engagement to understand what happened. Use plain technical voice; not customer-facing prose.
- **Speculation about future runs.** "Next time we should..." is the only forward-looking voice allowed. "Maybe the synthesizer will..." is not actionable.

### How the canary self-check uses reflection

The audit-completion self-check (see `skills/audit/SKILL.md` "Validation, Synthesis, and Rendering" + "Exit Criteria") treats `lead-reflection.md` as a SOFT gate:

- **File exists** (even empty): pass.
- **File missing**: fail. The lead failed to write the required reflection — surface as a discipline violation in audit-trace.log: `ASSERTION FAILURE — lead_reflection_present: file does not exist at <engagement-dir>/lead-reflection.md`.

The file's CONTENT is not validated — the lead's judgment about what to record is the responsibility, not the format. Future iterations may add structured front-matter parsing if specific fields prove load-bearing, but Phase I scope is the standard format only.

### Atomic write

`lead-reflection.md` follows the same atomic-write contract as other v2 artifacts: write to `lead-reflection.md.tmp`, then `os.replace()` to the canonical name. Per `scripts/assembly/atomic_write.py`. This means partial writes (lead crashes mid-write) leave the file in a clean state — either fully written or unchanged.

---

## Cancellation sentinel (cancel.flag) — Phase H 2026-04-28

**The lead MUST check `<engagement-dir>/cancel.flag` at every layer boundary in the audit pipeline.** When the file is present, the lead exits cleanly with `engagement_status: cancelled_by_operator` written to both `audit-trace.log` and `meta.json`. Partial artifacts on disk are preserved for replay. No further dispatches happen after a cancel.flag is observed.

### Why this exists

v2 audit runs can take 20-40 minutes wall-clock (10 cluster specialists × 2 devices in parallel + ethics subagent + ~24-minute synthesizer + render). Before Phase H, the operator had no clean way to interrupt mid-run — Ctrl-C left zombie subagents, half-written cluster-emission JSON files, and an inconsistent meta.json `phase` value. The cancel.flag sentinel closes §22 (operator-pushback affordance gap).

### How the operator triggers cancellation

The operator (or another agent) writes a file at `<engagement-dir>/cancel.flag` — content irrelevant; existence is the signal. In a shell:

```bash
touch docs/ecp/{engagement-id}/cancel.flag
```

Or via filesystem write from any tool. The file's content is treated as opaque (the lead may write a one-line reason if they want to surface it in audit-trace.log, but the sentinel itself is presence-based).

### When the lead checks

The lead checks `<engagement-dir>/cancel.flag` at EVERY layer boundary, BEFORE dispatching the next layer's role(s):

1. After acquirer completes, before dispatching cluster specialists.
2. After cluster specialists complete (parallel wave joined), before dispatching ethics subagent.
3. After ethics subagent completes, before dispatching synthesizer.
4. After synthesizer completes, before dispatching renderer.
5. After renderer completes, before transitioning meta.json to `phase: complete`.

For long-running roles (synthesizer, multi-cluster specialist parallel wave), the lead does NOT check cancel.flag DURING the role's execution — the check is at boundaries. This is by design: cancelling a synthesizer mid-emission corrupts state more than it saves; the file write is fast and the JSON+markdown are atomically replaced when the synthesizer finishes.

### Cancellation flow

When the lead observes cancel.flag at a layer boundary:

1. **Append to audit-trace.log:** `cancellation_observed_at: {iso-8601}` and `engagement_status: cancelled_by_operator`. Include the layer where cancellation was caught (e.g., "after_specialists, before_ethics") so resume logic knows what's complete.
2. **Update meta.json:** set `phase: cancelled` (or whatever the canonical cancel-state value is per `contracts/meta-schema.md`); leave the rest of the engagement state intact for replay.
3. **Report to operator:** "Audit cancelled at layer boundary {layer}. Partial artifacts preserved at `<engagement-dir>/`. Resume by removing cancel.flag and re-invoking the skill — completed layers will skip; incomplete layers will run."
4. **Exit cleanly.** Do NOT perform any further dispatches. Do NOT write to other engagement files. Do NOT print success/failure summaries — the cancellation is an explicit operator action, not a run outcome.

### What stays preserved

- Cluster-emission JSON files already written (cluster specialists that completed before cancellation).
- Ethics-findings.json if ethics already ran.
- Synthesizer-emission-v1.json + audit-{device}.md if synthesizer already ran.
- baton.json + baton-mobile.json + screenshots.
- audit-trace.log with the cancellation record.

### What does NOT happen

- The lead does NOT delete partial artifacts (no auto-rollback).
- The lead does NOT mark the engagement `phase: failed` (failure semantics differ from cancellation — cancellation is an operator decision, failure is structural).
- The lead does NOT spawn cleanup subagents.
- The lead does NOT delete cancel.flag (the operator may want it preserved as evidence; resume logic checks for absence as the green-light signal).

### Resume after cancellation

To resume an engagement that was cancelled mid-run, the operator:

1. Removes cancel.flag (`rm <engagement-dir>/cancel.flag`).
2. Re-invokes the skill with the same engagement-id.
3. The lead reads meta.json's `phase` value, infers the layer to resume from (per `contracts/audit-state-machine.md`), and dispatches only the missing layers.

The skip-already-complete logic depends on file presence (cluster-{cluster}-{device}.json present → cluster specialist skipped) per `contracts/dispatch-contract.md` "Restart-friendly file-presence model" + the standing v2 atomic-write contract.

### What this is NOT

- **Not a hard kill.** A subagent already in flight when the lead reads cancel.flag will complete its current dispatch and return a result; the lead simply discards that result and exits without dispatching the next layer. There is no in-process signal sent to running roles.
- **Not a feature flag.** cancel.flag is an OPERATOR affordance, not a v2-only feature. v1 audits should adopt the same protocol — Phase H scope adds it for v2 but v1 can backport.
- **Not the only cancellation path.** Operators can still Ctrl-C the lead; cancel.flag is the GRACEFUL path that preserves state correctly. Ctrl-C may leave artifacts in inconsistent shapes (especially mid-write to audit-{device}.md if the lead is in-flight on a non-atomic write); the atomic-write contract above mitigates but doesn't eliminate this.

---

## Concurrent-audit isolation

Engagements are filesystem-isolated by `engagement_id`. Two `/ecp:audit` invocations launched simultaneously share the engagement directory ROOT (`docs/ecp/`) but have distinct subdirectories (`docs/ecp/<id-A>/` and `docs/ecp/<id-B>/`) where all artifacts live. Lead writes only into its own engagement subdirectory; reads from `references/`, `contracts/`, `schema/`, `templates/` are read-only and shared safely.

**No shared mutable state outside the engagement directory.** The lead does NOT write to `~/.claude/`, `references/`, or any cross-engagement location during an audit run. Concurrent audits are isolated by construction — no locking, no semaphores, no coordination between engagements. If you find yourself thinking "I need to lock this so the other audit doesn't see it," you're writing outside the engagement directory; stop and route the write back into `<engagement-dir>/`.

This rule combines with the filesystem-atomicity rule above to give ECP its concurrency story: each audit is a self-contained directory, atomically-written, with no cross-engagement coordination needed.

---

## Cross-references

- **`skills/audit/SKILL.md`** — P0-01 (lead discipline) and P0-03 (acquisition-must-dispatch-subagent) defer to this file. Audit lead reads this at the top of the skill invocation.
- **`${CLAUDE_PLUGIN_ROOT}/contracts/flags.md`** — canonical flag documentation (referenced by the "Use the `--device` flag if set" rule).
- **`${CLAUDE_PLUGIN_ROOT}/contracts/cluster-routing.md`** — canonical cluster routing (referenced by the "Page-type defaults are auto-selected" rule).
- **`${CLAUDE_PLUGIN_ROOT}/contracts/device-semantics.md`** — canonical device rules (referenced by the "One prompt for device choice" rule).
- **`${CLAUDE_PLUGIN_ROOT}/contracts/dispatch-contract.md`** — canonical spawn template (the one-shot subagents the lead must NOT do the work of).
- **`${CLAUDE_PLUGIN_ROOT}/contracts/trace-assertion-canary.md`** — the forensic rogue detection canary that catches leads who violate these discipline rules.

When editing this file, grep `skills/audit/SKILL.md` for any residual inline discipline rules that should now reference this canonical file. The drift target is **discipline rules drifting between this file and the audit skill body** — leaks the original Round 12.5 extraction was designed to close.
