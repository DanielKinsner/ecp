# Handoff 2026-06-02 — ECP audit claim-accuracy + hotspot-render: open problem & hunches

**Status:** NOT fixed. This is a problem statement + hypotheses for the next instance, written deliberately to leave room for independent research. Do your own investigation before acting on anything here — treat every claim below as a hunch to verify, not a finding to trust.

**Context artifacts**
- Committed QA report (on main, authoritative read first): `docs/2026-06-02-awdmods-audit-qa-investigation.md`
- Engagement (working-tree-only; `docs/ecp/` is gitignored, so a fresh clone won't have it — re-run or re-capture if you need it): `docs/ecp/2026-06-02-3c7ddb73/`, with a `pre-correction/` snapshot of the originals for before/after diffing.

---

## What happened (so you don't have to reconstruct it)

1. Ran a full `/ecp:audit` of `https://www.awdmods.com/` (dual-device, comprehensive landing clusters: visual-cta, trust-credibility, pricing, performance-ux + ethics). It shipped a DRAFT audit + two annotated visual reports.
2. Ran an Opus-4.8 adversarial QA investigation (the committed report above). It found, against captured DOM + screenshots + a live re-capture: **3 materially-false findings** (1 critical), **~6 overstated framings**, and **18 of 52 hotspots misplaced (~35%)**.
3. Did an **engagement-local correction pass** (operator asked to prove the theory before any pipeline code change): re-dispatched the 5 affected specialists with a "verify every absence/accessibility claim against the full `dom.html`, not the baton's derived fields" guard. The false claims **self-corrected** (provable before/after — see QA report §9 and the `pre-correction/` snapshot). Re-synth + re-render produced corrected audit docs + reports.
4. **Operator's read: "that second pass didn't change anything from what I can tell."** That observation is the seed of this doc.

---

## The problem on hand (my framing — challenge it)

There are two layers, and they behave very differently:

### Layer A — claims (text). Fixed, but ~invisible.
The claim corrections genuinely landed in the rendered HTML (verified by grep: `4.1.2` → 0, "forced to logo" → 0, "propagate/drawer" now present, both HTMLs grew ~7KB). So the content changed. **But it's text inside finding panels** — not what the eye lands on. So at a glance the report looks identical. My hunch: the operator's "nothing changed" is real *perceptually* and correct *about the salient layer*, even though the underlying claims did change.

### Layer B — hotspots (geometry). The actual unresolved problem, and the reason it "looks the same."
The annotated screenshots + marker positions are byte-identical between passes because the claim pass cannot touch them — **the renderer recomputes marker positions from the emission + baton on every render.** ~35% of those markers are wrong. The QA report isolates 3 patterns (these are my hunches with supporting math, not proven root cause in code):
- **Slide-projection boundary clamp** — an element whose source-y sits just across a slide boundary (e.g. the "Featured Collection" h2 at y≈906 vs slide-1 range 0–930) projects to a negative %, gets clamped to 0%/100%, and lands on the wrong slide/element. Suspected ~11 of the 18.
- **Canned section-ghost default** — absence findings default to a constant `(50%, 77.5%)` desktop / `(50%, 77.7%)` mobile, dumping hero-band ghosts into a gap far from where the missing thing belongs (the "FREE SHIPPING bar" ghost lands ~75 percentage points off).
- **Mobile coordinate-space mismatch** — slide-y appears to be computed in 844px CSS-viewport space while element rects live in full-page (0–8622) space, dropping mobile slide-3 markers into the black band below the footer.

**If you fix one thing to make the report visibly better, it is almost certainly Layer B.** That is the layer the operator is looking at.

### Upstream root causes I *suspect* feed Layer A (verify, don't trust)
- **Baton converter derives `accessible_name` from CSS className, not `alt`/`aria-label`** (`scripts/baton_v1_to_v2.py`, look around the element-build / `accessible_name` logic). For `<img>` the real `alt` never reaches the specialist, so "image has no alt text" / "icon button has no accessible name" findings are false-positives by construction. This is the highest-confidence upstream hunch; the rendered DOM had `alt="AWDMods"` and `aria-label="Subscribe"` the whole time.
- **Specialists only receive a sliced `cluster-context-*.json`, not the full DOM** — so they "can't see" existing components (the cart-drawer free-shipping bar, the Borla sibling MSRP) and write false-absence findings. The engagement-local fix (hand them `dom.html` + a verify-absence guard) worked, which is *evidence* this is the mechanism — but whether the right durable fix is "give specialists the full DOM," "add a synthesizer cross-check," or "a deterministic false-absence grep gate" is an open design question. I have a lean (below) but no strong proof.

---

## My assumptions / hunches (confidence-tagged — all need independent verification)

- **[high]** The capture is sound. `dom.html`/`baton.v1raw.json`/screenshots contain the truth for every contested claim; nothing here requires re-auditing the page. (Live re-capture via `acquire_url.py` was byte-near-identical: 228,760 vs 228,788 B.)
- **[high]** The `accessible_name = className` converter behavior is real and is the root of the accessibility false-positives.
- **[med]** The 3 hotspot patterns are distinct bugs, not one bug with three symptoms. The slide-clamp and the coordinate-space mismatch *might* be the same underlying "which coordinate space / which slide" confusion — I didn't confirm in code.
- **[med]** The section-ghost default is a placement-policy gap, not a math bug: the renderer probably ignores `proposed_anchor.placement` semantics (`viewport-top` / `before-element` / `after-element`) and falls back to a constant. Worth confirming in `scripts/report/v2_markers.py` (and `v2_loader.py`).
- **[low/uncertain]** "Nothing changed" might *also* be hiding a real regression I didn't catch — e.g., the renderer pulling some panel content from a stale source, or the visual report not surfacing the corrected priority-path prose as prominently as I assume. I only grep-verified a handful of phrases. **Please don't take my "corrections landed" as fully settled** — diff the rendered HTML panels against `pre-correction/` before concluding.
- **[caution]** The QA verifiers themselves are fallible. In an earlier (discarded 4.7) run a verifier confabulated a non-existent "slingmods $59.95 PDP," primed by the specialist template's "Polaris Slingshot accessory PDP" one-shot example that lives in every rendered `.prompts/*.txt`. If you re-verify, give each verifier a ground-truth tripwire (echo the real finding titles + the audited URL before judging) and cross-check verdicts against the actual emission files.

---

## Soft recommendation (a lean, with my reasoning — not a directive)

If it were me, I'd sequence it: **(1) renderer hotspot geometry → (2) baton converter `alt`/`aria-label` → (3) specialist false-absence guard.**

Why this order — and why it's soft:
- **Renderer first** because it is (a) the only layer the operator actually *sees* change, (b) backed by the most concrete evidence already (deterministic projection math in the QA report, no LLM judgment needed), and (c) compounding across every future audit. It's also the most contained: pure Python geometry in `generate-report.py` / `scripts/report/`, easy to unit-test against the awdmods baton as a fixture.
- **Converter second** because it's a tiny, high-certainty change (`accessible_name` should prefer `alt`→`aria-label`→text) that kills a whole class of false-positives at the source.
- **Specialist guard last** because it's the least-bounded design decision (full-DOM-to-specialist has token/cost and routing implications; a deterministic grep gate might be safer) and deserves the most of *your* research rather than my guess.

I could easily be wrong about the order. Reasonable alternative: do the converter first (smallest, safest, unblocks accurate accessibility findings immediately) and treat the renderer as a larger, separately-tested effort. Pick after you've read the renderer code — I'm leaning on visibility/leverage, you may weigh risk/effort differently.

---

## What I deliberately did NOT do (your room to work)

- Did **not** change any plugin code (operator deferred "implementation"). The engagement-local pass only re-dispatched specialists + re-ran synth/render within the one engagement.
- Did **not** re-pin hotspots — the static visual report recomputes positions each render, so re-pinning would be a throwaway per-engagement workaround, not a fix.
- Left the `pre-correction/` snapshot intact for before/after evidence.

Open questions I'd want answered before committing to a fix (non-exhaustive — find your own):
- Is the slide-projection clamp in marker placement (`v2_markers.py`) or in the slide/section model (`v2_loader.py`)? Are slide ranges and element rects ever in different coordinate spaces, and where is the conversion?
- Does the renderer read `proposed_anchor.{kind,placement,element_baton_index}` at all when placing ghosts, or does it only use `surface`/section centroid?
- What's the cleanest regression fixture — can the awdmods baton + emission be frozen as a golden so a renderer change is provably better, not just different?
- Is "give the specialist the full DOM" actually desirable, or does it reintroduce the cross-device drift / cost the cluster-context slicing was built to prevent? (See `contracts/dom-preprocessor.md` rationale.)
- Did the claim corrections fully and faithfully propagate into BOTH device reports' panels, or only partially? (I spot-checked; you should diff.)

## Pointers
- QA report: `docs/2026-06-02-awdmods-audit-qa-investigation.md`
- Engagement + snapshot (gitignored, this box only): `docs/ecp/2026-06-02-3c7ddb73/`, `docs/ecp/2026-06-02-3c7ddb73/pre-correction/`
- Renderer: `scripts/generate-report.py`, `scripts/report/v2_markers.py`, `scripts/report/v2_loader.py`
- Converter: `scripts/baton_v1_to_v2.py`
- Specialist routing / DOM slicing: `scripts/dom_preprocess.py`, `contracts/dom-preprocessor.md`, `contracts/specialist-prompt-v2.md`

_Authored after an engagement-local correction pass on 2026-06-02. Everything above is a starting point, not a conclusion — research first._
