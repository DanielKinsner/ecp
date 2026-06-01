# Team-Based Q&A Protocol (formerly "Relay Loop Protocol")

Defines how reviewer and builder teammates communicate questions and answers with the user via the team lead.

**v5.0 update (Phase 4 — April 2026):** This protocol replaces the previous nonce-based "relay loop" pattern. The old protocol used regex-parsed `QUESTION__{nonce}:` lines in subagent stdout, with the coordinator re-dispatching the entire subagent on every Q&A round. The new protocol uses Claude Code's native Agent Teams `SendMessage` mechanism: teammates stay running, send questions to the lead via SendMessage, the lead presents to the user, and the lead SendMessages the answer back. No regex parsing, no nonces, no re-dispatch, no context bloat.

The reviewer and builder teammates inherit this protocol from `${CLAUDE_PLUGIN_ROOT}/skills/audit/SKILL.md` `<phase_review>` and `<phase_build>`. The single source of truth for the spawn templates and lead-side handling is in those skill sections; this file documents the protocol itself for reference and onboarding.

---

## When teammates ask questions

Reviewer and builder teammates ask blocking questions when they encounter ambiguity that materially affects their output. They do NOT ask non-blocking clarifications or stylistic preferences — only questions whose answers change the outcome.

### Reviewer question types

- **VAGUE** — A plan step is too ambiguous to evaluate ("Step 3 says 'improve CTA' — improve which dimension: contrast, copy, size, all three?")
- **CONTRADICTION** — Two plan steps conflict with each other ("Step 5 says hide the popup; Step 12 adds a popup-triggered upsell flow")
- **ETHICS** — Potential ethics violation that needs a judgment call ("Plan recommends a countdown timer — is the underlying scarcity real or fabricated?")
- **WCAG** — Accessibility concern that needs a decision ("Plan says 'use icon-only mute button' — should I require an aria-label?")

### Builder question types

- **STUCK** — Cannot implement a step due to a technical or environmental blocker ("Plan says 'add Apple Pay' but the theme doesn't have a payment-method snippet — should I create one or use the Shopify dynamic checkout block?")
- **ETHICS** — Plan asks for something that violates ethics-gate.md ("Plan says 'add `setTimeout` to fade out the price after 3s' — this is a hidden-pricing dark pattern, refusing to implement, suggest alternative")
- **AMBIGUITY** — Multiple valid implementations of a single plan step ("Plan says 'wire BNPL near the price' — Klarna SDK, Affirm SDK, or a static link to Shop Pay Installments?")

---

## Question format (teammate → lead via SendMessage)

```
SendMessage to "team-lead":
"REVIEWER QUESTION 1 of N: {short summary}

  Type: {VAGUE | CONTRADICTION | ETHICS | WCAG}
  Context: {2-3 sentence framing — what you're looking at, why it matters}
  Question: {the actual question}

  Options:
    A) {option label} — {one-line consequence}
    B) {option label} — {one-line consequence}
    C) Skip this question (best-effort verdict)

  Reply with: A, B, or C (and optional commentary)."
```

For builder questions, use `BUILDER QUESTION` instead of `REVIEWER QUESTION` and use the builder question types.

The lead presents this to the user verbatim (or wraps it in a friendlier checkpoint message), collects the answer, and SendMessages the teammate back.

---

## Answer format (lead → teammate via SendMessage)

```
SendMessage to "reviewer":
"Answer to QUESTION 1: B (and any user commentary)"
```

The teammate receives this as its next conversation turn. It applies the answer to its reasoning and either continues to its next question or proceeds to the final output.

---

## Round-trip cap

**Maximum 5 question/answer round-trips per teammate session.** This is up from the legacy 3-iteration cap because each "iteration" of the old nonce protocol was actually a Q&A round bundled into a re-dispatch — the new protocol can naturally handle 5 questions in a single teammate run without re-spawning anything.

If a teammate hits 5 round-trips:
- Stop asking questions
- Make best-effort decisions for any remaining ambiguity
- Document the unresolved items in the output file (review.md or build-log.md)
- SendMessage the lead a summary noting the cap was hit

---

## Auto mode

When `--auto` is active:
- The lead's spawn prompt sets `auto_mode_flag: true`
- Teammates do NOT use SendMessage for questions — they make best-effort decisions and document them
- Reviewers produce best-effort verdicts using the simpler/safer interpretation for vague steps
- Builders mark unclear steps as `Adapted` (best interpretation) or `Stuck` (with reason)
- BLOCK verdicts still halt the pipeline unless `--force` is also set

---

## Comparison: old vs new

| Aspect | Old (nonce relay loop) | New (team SendMessage) |
|--------|------------------------|-------------------------|
| Communication channel | Regex-parsed stdout lines | Native team mailbox |
| Identity verification | 8-character hex nonce | Team membership (built into Agent Teams) |
| Question marker | `QUESTION__{nonce}: {json}` | `SendMessage` plain text |
| Verdict marker | `VERDICT__{nonce}: APPROVE` | Final `SendMessage` to lead with verdict line |
| Context preservation between Q&A rounds | Coordinator re-dispatches the agent with previous Q&A pairs as input | Teammate stays running, keeps full context |
| Token cost per Q&A round | Full re-dispatch (entire prompt + all previous Q&A) | Single message round-trip |
| Maximum rounds | 3 (initial + 2 re-dispatches) | 5 (raised because each round is now cheap) |
| Failure mode | Malformed JSON in QUESTION line → skipped silently | SendMessage → delivered, processed natively |
| Subagent vs team | Required isolated subagents | Requires Agent Teams (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) |

The old protocol existed because subagents couldn't communicate with the coordinator at runtime — the only channel was their final stdout output. With Agent Teams, that constraint is gone.

---

## Status reporting (still uses TaskUpdate, not SendMessage)

When a teammate finishes its work, it does TWO things:

1. **TaskUpdate** with `status=completed` (and a status note if PARTIAL or FAILED) — this updates the team task list and is the canonical state change
2. **SendMessage** to team-lead with a one-line summary — this notifies the lead that work is done, in human-readable form

The TaskUpdate is what the lead uses to know the teammate is done. The SendMessage is for the human-readable summary that the lead may surface in the checkpoint.

Valid status values:
- `completed` (with optional status note: "PARTIAL — {reason}", "FAILED — {reason}", or empty for full completion)

The lead reads the task status to determine completion, NOT the SendMessage content. SendMessage is for narrative; TaskUpdate is for state.
