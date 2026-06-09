# Hotspot / finding diagnosis protocol — hold each stage accountable

> **Read this first thing.** This is the method for figuring out *which stage* is
> producing the bad hotspots and false findings, so you can tune the right knob
> instead of guessing. It works on any completed engagement, offline, in seconds.

## The one idea

Every visible defect is born at one of five stages, and the same symptom can come
from any of them:

```
ACQUISITION  ->  BATON  ->  SPECIALIST  ->  SYNTHESIZER  ->  PLACEMENT/RENDER
capture the      extract    write the       humanize +      map findings to
real page        elements   findings        de-dupe         screenshot pixels
```

- If the **hero captured black** (acquisition), a specialist's "empty hero"
  finding is garbage-in — no placement tuning will ever fix it.
- If a specialist anchored **"items over $1,000" to a $135 part** (specialist),
  that's a prompt problem, not geometry.
- If a region finding rendered as a **stacked point-circle** (placement), that's
  the renderer.

You can't tune the right stage until you know which one to blame. The tool below
attributes every defect to its owning stage.

## Run it (one command)

```powershell
python scripts/diagnose_engagement.py --engagement docs/ecp/<engagement-id>
# add --device desktop|mobile to scope; --no-crops to skip images
```

Needs `pillow` for the crops (`pip install pillow`). It writes, under
`docs/ecp/<id>/_diagnosis/`:

| file | what |
|---|---|
| `report-<device>.md` | the verdict, capture signals, and the per-finding accountability table |
| `crops/<device>-<f_ref>.png` | **each hotspot cropped from its screenshot with the marker drawn** — look at these |
| `diagnosis.json` | machine-readable, for an agent to act on |

## Read it (top to bottom)

1. **Verdict.** `DO NOT SHIP` means the above-fold likely didn't render (flat/void
   screenshot + scroll-trigger/lazy elements in the DOM). Re-capture before you
   trust *any* above-fold finding. This is the gate that should have pulled the
   2026-06-08 awdmods run.
2. **Stage-attribution table.** Counts per defect class, each mapped to the
   **owning stage** and a one-line "tune this" pointer. This is the accountability:
   a number next to ACQUISITION / SPECIALIST / PLACEMENT.
3. **Per-finding table + crops.** For every non-`OK` row, open its crop and confirm
   with your eyes. This is the visual assessment the pipeline can't do
   deterministically — the crop shows you exactly where ECP put the hotspot and on
   what.

### The defect classes (and who owns them)

| attribution | meaning | owning stage | tune |
|---|---|---|---|
| `CAPTURE_SUSPECT` | finding claims an empty/blank region while the above-fold actually captured flat/void | **ACQUISITION** | `scripts/acquire_url.py` reveal/settle (scroll-trigger + lazy media). Re-capture; confirm the screenshot now shows real content. |
| `PREDICATE_MISMATCH` | finding says "over/under $X" but is anchored to an element whose price violates it | **SPECIALIST** | `contracts/specialist-prompt-v2.md` — a numeric-predicate finding must anchor to an element that satisfies it (or to the section), not an arbitrary one. |
| `WEAK_ANCHOR` | no concrete on-page element backs the marker (absence / proposed-zone) | **SPECIALIST** + PLACEMENT | specialist should cite the closest real element or the section; placement should give absence findings a deterministic lane (not pile them on the logo). |
| `POINT_FOR_REGION` | a banner/section/"whole-area" finding rendered as a single point, not a box | **PLACEMENT** | `scripts/report/v2_markers.py` — region findings should render as a box over the section. |
| `STACKED` | 2+ markers within 6% on a slide (overlapping circles) | **PLACEMENT** | `_distribute_stacked_section_markers` in `v2_markers.py` — generalize de-stacking to `proposed_anchor_element` + `e_index_lookup`. |
| `DUPLICATE` | another marker shares the exact position (incl. the base/`-ai` pair) | **PLACEMENT** | drop the `-ai` suggestion copy from the render set; collapse identical-position markers. |
| `LOW_CONF_PLACEMENT` | placed via a proxy/low-confidence anchor | **PLACEMENT** | confirm the crop; tighten the proxy fallback. |
| `OK` | exact element anchor, high confidence, not stacked | — | no action |

## The accountability loop (this is the whole point)

1. Run the tool on the latest engagement.
2. Pick the stage with the highest defect count.
3. Make ONE change to that stage (use the "tune" pointer).
4. **Re-run the audit, re-run the tool, and watch that stage's count.** A stage is
   "fixed" when its attributed count goes to ~0 and stays there across a couple of
   different sites. If the count doesn't move, the change didn't work — revert and
   try a different lever. No more guessing whether a fix helped.

Track it like a scoreboard across runs (awdmods, then a second site, then a third):

```
            CAPTURE_SUSPECT  PREDICATE  WEAK_ANCHOR  POINT_FOR_REGION  STACKED  DUPLICATE
awdmods 06-08      6            1           6              0              7         3      <- baseline
<next run>        ...          ...         ...            ...            ...       ...
```

If those numbers don't trend to zero after focused tuning, *that* is the signal to
shelve — you'll have hard evidence of which stage is unfixable, not a vibe.

## Two things the tool deliberately does NOT do

- **It won't tell you a finding is true or false.** That needs your eyes (the
  crops) or a vision model. The tool tells you *where to look* and *who's
  accountable*. For an automated visual pass, escalate to the `ecp-visual-qa`
  Workflow (it crops each marker and has a vision agent judge on-target /
  off-target) — run it per device after a clean capture.
- **It won't gate on pixels alone.** A pure "blank screenshot" detector
  false-positives on dark-themed sites (measured — the hero is "selector floating
  in black", not a pure void). `CAPTURE_SUSPECT` requires BOTH a flat above-fold
  AND scroll-trigger/lazy/video elements in the DOM, and the finding text claiming
  emptiness — three signals, not one.

## Tunables (top of `scripts/diagnose_engagement.py`)

- `ABOVE_FOLD_VOID_FLAG` (0.35) — void-row fraction that, with DOM render-risk,
  trips `CAPTURE_SUSPECT`.
- `STACK_RADIUS_PCT` (6.0) / `STACK_MIN` (2) — what counts as a stack.
- `VOID_ROW_FRAC` (0.90) / `VOID_TOL` (16) — what counts as a flat/void row.

Tune these against a couple of *known-good* engagements so OK findings stay OK.

## Worked example (committed)

`docs/ecp/2026-06-08-8e46b1c8/_diagnosis/` is the awdmods run this tool was built
against — the report + crops are committed so you can see expected output before
running anything. Desktop verdict: **DO NOT SHIP** (56% void above-fold + 19
scroll-trigger / 19 lazy in the DOM), 24/25 findings defect-attributed. That's the
run that "should have been pulled" — now it would be, automatically.
