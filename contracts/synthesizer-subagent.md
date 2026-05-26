# Priority Path Synthesizer — Subagent Prompt

The lead dispatches ONE synthesizer subagent per device after dedup + F-N assignment. The subagent reads the post-dedup candidates + finalized findings, produces 3–5 "stories" in fenced JSON, and returns. The lead captures the response text to a file and re-runs `assemble-audit.py` with `--priority-path PATH` pointing at the file. Python-side parsing + validation lives in `scripts/assembly/synthesizer_parser.py`.

## Dispatch contract

| Field | Value |
|---|---|
| Tool | `Task` (Claude Code subagent dispatch) |
| `subagent_type` | `general-purpose` |
| Prompt model requested | Opus (the prompt body explicitly asks for it — see §Prompt body) |
| Input payload | candidates JSON + finalized findings + F-N allowlist, inlined in the prompt |
| Output contract | one fenced JSON code block containing `{"stories": [...]}` and nothing else |

**Why Opus specifically:** Sonnet reads more robotic for copy work. Operator preference. A v1.1 cost tradeoff could revisit.

## Inputs the lead interpolates

- `{{device}}` — `"desktop"`, `"laptop"`, `"mobile"`, or `"tablet"`.
- `{{engagement_id}}` — for logging.
- `{{valid_refs}}` — a newline-separated list of every `"{cluster} F-{NN}"` the lead will accept. Built from `pipeline.FinalizedFindings.valid_refs()`. This is the allowlist the synthesizer must cite from. Forbid invention.
- `{{candidates_json}}` — the contents of `priority-path-candidates-{device}.json` (the scoring output).
- `{{findings_digest}}` — a compact newline-delimited summary of the finalized findings: one line per finding in the format `{cluster} F-{NN} [{severity}] {section} — {one-sentence observation}`. Keep under ~8K tokens; truncate longer observations at ~140 chars. This gives the synthesizer context without re-inlining full finding bodies.

## Prompt body

```
You are joining the audit-{{engagement_id}} team as synthesizer-{{device}}.
Your job is to produce the Priority Path for this audit: 3–5 stories that
tell the operator what to fix FIRST, and why.

Please use Opus-tier reasoning. Copy quality matters more than speed on
this dispatch — you are writing the first thing a prospect reads when
they open the report.

## Inputs

### Valid F-N allowlist (you MUST cite only from this list — do not invent)
{{valid_refs}}

### Candidates (from scoring.py, already ranked)
```
{{candidates_json}}
```

### Findings digest (for context)
```
{{findings_digest}}
```

## Constraints (hard — validated in Python after you return)

1. Produce **3 to 5 stories**. Not 2. Not 6. If the scoring output has fewer
   than 3 candidates worth promoting, pick the highest-severity ungrouped
   findings and bundle thematically.
2. Each story cites **2 to 4** `f_refs`, drawn from the allowlist above.
   Never invent an F-N. Never cite an F-N not in the list.
3. Severity per story is one of: CRITICAL, HIGH, MEDIUM, LOW. Pick the
   highest severity present in the story's `f_refs`.
4. Every story has:
   - `title` — short, client-readable label (no jargon). 4-8 words.
   - `narrative_md` — 2-4 sentences of markdown explaining the issue as
     a specific consumer would experience it on the actual page. No
     generic CRO cliches ("best practice suggests", "typical stores
     benefit from"). Describe what the shopper sees and feels.
   - `action_md` — 1-2 sentences in imperative voice naming the specific
     change to make. Reference the actual element, not abstractions.
   - `f_refs` — the underlying findings.
5. **F-N format is cluster-slug + space + `F-` + two-digit zero-padded number**
   (e.g., `pricing F-03`, `trust-credibility F-12`). The allowlist above is
   the source of truth. Every cluster starts at F-01 regardless of where
   its findings sit in the audit document. If you are tempted to cite
   `pricing F-10` or `pricing F-41`, verify the literal string against the
   allowlist first — under cluster-local numbering, a cluster with 7
   findings stops at F-07.
6. **Titles are written from the underlying findings, not from slugs.**
   Do NOT mechanically title-case a SYNTHESIS_HINT slug
   (`hero-cta-trust-overlap` → "Fix: Hero Cta Trust Overlap" is a
   banned pattern). The title describes the specific action a store
   operator would take on their specific page — verb-first, human voice.
7. **Do NOT fabricate element selectors or DOM references in
   `narrative_md` / `action_md`.** Quote the elements the underlying
   findings actually name. If F-01 says `ELEMENT: #button-cart`, your
   narrative can reference "the Add to Cart button" but should not
   invent `.hero-wrapper > form > #submit-btn` selectors the finding
   doesn't claim.
8. **One Priority Path per device — do not mix devices.** The dispatch
   is per-device and the allowlist is per-device. Do not cite refs
   from a different device's allowlist. Do not tag refs with
   `(desktop)` / `(mobile)` annotations — those break the downstream
   parser at `scripts/report/parser.py:240`.

## Voice target

Senior strategist memo to the store operator. Measured, analytical,
zero jargon. Short sentences. Name what is on the page; name what to
change. No "consider adding", no "best practice suggests", no
"typical stores benefit from" — these phrases get the response
rejected at Python validation.

## Output — exactly this shape, nothing else

Return a single fenced JSON code block. No prose before or after the
fence. No markdown outside the fence. The Python parser extracts the
first fenced JSON block and discards anything else.

```json
{
  "stories": [
    {
      "title": "...",
      "severity": "HIGH",
      "narrative_md": "...",
      "action_md": "...",
      "f_refs": ["pricing F-03", "trust-credibility F-01"]
    }
  ]
}
```

Go idle when done. The lead will pick up the response, run it through
`synthesizer_parser.parse_response` + `validate_stories`, and either
feed it to the writer or dispatch you again with a correction
instruction if validation fails.
```

## Retry protocol

If `validate_stories` returns `(False, reason)`, the lead dispatches the subagent ONE more time with a correction turn:

```
Your previous response failed validation: {reason}.
Regenerate using ONLY these f_refs: {valid_refs}.
Produce exactly 3-5 stories with 2-4 f_refs each.
Do not explain; return the corrected JSON block.
```

If the retry also fails, the lead stops, writes whatever it got to `audit-trace.log` for diagnosis, and calls `assemble-audit.py` WITHOUT `--priority-path`. The writer renders an ERROR block so the operator sees the failure visibly rather than as a silent placeholder. No third attempt — graceful degradation is sufficient; elaborate correction loops defend a hypothetical we haven't observed.

## Anti-patterns (subagent-side)

These patterns fail the Python validator and/or produce misleading output that ships to clients. The lead rejects responses exhibiting any of them:

- **Hallucinated F-Ns** — using `f_refs` not present in the allowlist (e.g., "pricing F-99" when F-99 doesn't exist; "pricing F-10" when the allowlist stops at F-07). Hard-rejected by `synthesizer_parser.validate_stories`.
- **Global-numbering F-Ns** — refs like "F-10" or "F-41" that only make sense under a global sequential index (F-01 through F-NN across all clusters). The allowlist uses **cluster-local** numbering: every cluster starts at F-01. If the allowlist's pricing refs go F-01 through F-07, citing "pricing F-41" is invention — even though it might "look right" based on a misread of some other numbering scheme seen elsewhere in the engagement.
- **Slug-derived titles** — mechanically converting a SYNTHESIS_HINT slug into a title (`hero-cta-trust-overlap` → "Fix: Hero Cta Trust Overlap"). Slugs are internal routing tags, not client-facing copy. Titles are verb-first and written from what the findings actually say. Concrete failure: 2026-04-16-a20ca3d1 shipped with four slug-derived titles across its two device reports.
- **Fabricated selectors in narrative/action** — inventing CSS selectors, DOM paths, or element IDs that the underlying findings don't claim. Quote what the findings name; don't improvise.
- **Cross-device refs** — citing F-Ns from a different device's allowlist, or tagging refs with `(desktop)` / `(mobile)` device markers. One Priority Path per device. Concrete failure: the mobile Priority Path in 2026-04-15-36bf19a6 shipped with cross-device tags and `parser.py` collided duplicate F-Ns across devices, producing 14 "(not found)" refs in the rendered HTML.
- **Prose or headers outside the fenced JSON block.** The parser extracts the first fenced block and ignores surrounding text, but stray prose indicates the subagent misunderstood the output contract.
- **Generic CRO framings in `narrative_md` / `action_md`** — avoid "consider adding", "best practice suggests", "typical stores benefit from", "industry standard is", "users often expect", "research shows that". These ship to the client in the rendered report and make it read generic. No Python lint for these yet, but they make v1.0.1 test coverage.
