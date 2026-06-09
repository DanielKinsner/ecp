# Hotspot-Accuracy Troubleshooting Methodology (2026-06-09)

**Purpose:** how to *catch* the hotspot/finding accuracy failures — not how to fix them. A review playbook for a fresh-eyed pass, plus a paste-ready prompt at the end.

**Who this is for:** the reviewer (human or agent) doing the morning review pass. Read the framing, then run the prompt.

---

## 0. The one principle everything hangs on

**The instruments lie. Trust the rendered picture, never the pipeline's self-report.**

The pipeline says `25/25 placed, 0 unplaced`, 1,118 tests green, 9-agent QA passes — and the product is ~20% accurate. That gap exists because **every check in the system validates against the DOM (does a coordinate map to a node), and none validates against the VISUAL truth (is the marker on the right thing, the right shape, and does this finding even deserve a marker).**

So the review must be **visual-first and outside-in**: start from the rendered audit a human sees, judge it cold, and only *then* trace causes. Do not open a green test and conclude "fine." A green test here means "the wrong thing passed."

---

## 1. The two root causes (the lenses to sort everything into)

Every failure observed so far collapses into these two. When you catch something, name which one it is.

**RC-A — The capture is broken (garbage in).**
The acquirer screenshots the page before it finishes loading (hero/lazy media not rendered). Agents then *faithfully* describe an "empty black hero" — they aren't hallucinating, they're auditing a broken photo. This cascades: one bad capture → multiple false findings → markers placed on nothing. *Upstream of everything.*

**RC-B — There is no visual ground truth for placement (only DOM coordinates).**
Markers "map correctly to the DOM" yet land visually wrong, because nothing looks at the pixels. Two failure shapes fall out:
- **Wrong area / wrong size:** a banner finding gets a dot, not a box over the banner.
- **Phantom markers on absence findings:** a finding about something *missing* ("no trust block", "no pricing anchor") has no element to attach to, so the DOM logic drops a circle *somewhere arbitrary*. That's the "weird circles on bad areas."

> Fixes live elsewhere; this doc is only about reliably *catching* RC-A and RC-B at scale.

---

## 2. The per-finding screen (run in this order — stop early when it fails)

For each clickable finding in an audit, look at the **rendered page + the placed marker** and ask, in order:

1. **Is the capture real?** Is the page in this screenshot actually loaded — hero present, lazy content in, no blank/black regions that are really just un-rendered? **If no → tag `RC-A:capture` and STOP.** Every finding on this page is suspect; don't grade the marker, the input is broken.
2. **Is the finding TRUE?** Does the claimed problem actually exist on a *properly loaded* page? ("Blank hero" — really blank, or just didn't load?) **If false → tag `false-finding`** (note whether it's RC-A fallout or a genuine analysis error).
3. **Is the marker VISUALLY correct?** Only for true findings:
   - **3a. Right area?** Is it on the element/region the finding is about? (trust-block finding → is it where the trust block is/should be, not floating on the product grid?)
   - **3b. Right shape/size?** Banner/section → a **box over the area**, not a point. Small control → a tight marker. Tag `wrong-geometry` if the shape is wrong even when the location is roughly right.
   - **3c. Should it even have a marker?** Absence/"missing X" findings should be **no marker or a labeled zone**, never a confident dot on a random pixel. Tag `phantom-marker` if a no-anchor finding got a placed dot.

A finding can collect multiple tags. The tags ARE the data.

---

## 3. The failure-mode taxonomy (step back — bucket, don't fix)

Don't fix markers one at a time. Tally every finding into these buckets per audit; the distribution tells you where the systemic fix lives.

| Tag | What it is | Root cause | Points the fix at |
|---|---|---|---|
| `RC-A:capture` | page/media not loaded in the shot | RC-A | acquisition wait-for-load |
| `false-finding` | the claim isn't true on a loaded page | RC-A or analysis | capture, or the auditor prompt |
| `wrong-area` | marker on the wrong element/region | RC-B | a visual placement pass |
| `wrong-geometry` | dot where a box belongs (or vice-versa) | RC-B | marker-shape model |
| `phantom-marker` | absence finding got a placed dot | RC-B | "should this be placed at all" gate |
| `duplicate` | same finding/marker repeated | dedup | reconciliation dedup |
| `accurate` | capture real, finding true, marker right | — | (this is the only "pass") |

**The real accuracy number** = `accurate / total`, reported per-category so you see *which* failure is eating the score. ("20%" is useless; "55% wrong-area, 20% phantom, 15% capture, 10% true-pass" is a work order.)

---

## 4. The detection mechanism (how to catch it without eyeballing 30 findings by hand every time)

The eyeball pass above is the gold standard but doesn't scale. **Operationalize it as a visual-review pass:** for each finding, hand a **vision model** the rendered page (or a crop around the marker) + the finding text + the marker box, and have it answer the §2 questions and emit the §3 tags. That vision judgment is *exactly* the accuracy metric the pipeline is missing — and once it exists, it becomes both the **scoreboard** (track accuracy per build) and, later, the **placer** (let vision decide where/whether to mark).

This review pass is the first domino. It changes nothing in the product yet — it just makes the failure *visible and counted* so the fixes can be aimed instead of guessed.

---

## 5. What this review must NOT do

- Do **not** fix code, move markers, or edit findings. Catch and categorize only.
- Do **not** trust `placed`/`unplaced`/test-green as evidence of correctness — judge the picture.
- Do **not** average into one "accuracy %." Report the per-category breakdown + the worst offenders with their screenshots.
- Do **not** grade a marker on a page that failed the capture check — flag the page, move on.

---

## 6. Paste-ready review-pass prompt (run fresh tomorrow)

> You are doing a **visual accuracy review** of the most recent ECP audit. You are an eagle-eyed senior reviewer stepping back, not a coder — your only job is to **catch and categorize** what's wrong, NOT to fix anything.
>
> **Setup:** Find the most recent engagement under `docs/ecp/<engagement-id>/`. Load its rendered audit + the page screenshots + the placed hotspots/markers (the visual report, not just `audit.md`).
>
> **Ignore all internal success signals** — `0 unplaced`, green tests, QA pass. They validate DOM mapping, not visual correctness. Judge only what's rendered.
>
> **For every clickable finding, look at the rendered page + its marker and screen it in order (stop early on failure):**
> 1. **Capture real?** Is the page actually loaded in this shot (hero/lazy media present, no un-rendered blank/black areas)? If not → tag `RC-A:capture`, stop grading this page's markers.
> 2. **Finding true?** Does the claimed problem exist on a properly loaded page? If not → tag `false-finding` (note if it's capture fallout vs analysis error).
> 3. **Marker visually correct?** (true findings only) `wrong-area` (off the element it's about) · `wrong-geometry` (dot where a box belongs / wrong size) · `phantom-marker` (an absence/"missing X" finding that got a confident dot instead of no-marker or a labeled zone).
>
> **Output a markdown report:**
> - A table: finding → tags → 1-line why, with the screenshot region cited.
> - A **per-category tally** and the **real accuracy = accurate/total**, broken down by failure mode (e.g. "55% wrong-area, 20% phantom, 15% capture, 10% pass").
> - The **3–5 worst offenders** with their screenshots and exactly what's wrong.
> - One closing section: **which systemic fix each category points to** (capture → acquisition wait-for-load; wrong-area/geometry/phantom → a visual placement+gating pass; duplicate → reconciliation dedup). Do not implement them.
>
> Think like a human looking at the page for the first time. If a marker would confuse a paying client, it fails — regardless of what the DOM says.

---

*Method, not fixes. The whole point: make the failures visible and counted (visual-first), so the two root causes — broken capture, no visual ground truth — can be aimed at instead of guessed at.*
