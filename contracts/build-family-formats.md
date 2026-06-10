# Build-family formats (frozen pointer)

`product.md` §7 freezes the **plan / review / build-log formats** alongside the
frozen build family (§5). This file exists so the freeze has something to point
at — a future unfreeze has a concrete artifact to re-prove conformance against
instead of an empty bullet.

## Status

- **Frozen.** Out of the canonical product per `product.md` §5 alongside the
  `build` / `review` modes themselves.
- **Defining sources are not in this repo.** Per
  [`contracts/dispatch-contract.md`](dispatch-contract.md) (the "Single-planner
  / reviewer / builder note"), the workflow prompt sources
  `workflows/plan.md` · `workflows/review.md` · `workflows/build.md` and the
  `/ecp:build` · `/ecp:compare` · `/ecp:quick-scan` sibling skills were left
  with the archived repo on the 2026-05-26 prune-and-re-root.
- **The archive is the quarry.** Per `README.md` and `product.md` §9, the
  archived predecessor repo `ecommerce-conversion-psychology` is the read-only
  source the formats are mined back from when unfrozen.

## What each format is (one line)

- **Plan doc** (`plan-{cluster-slug}.md` per `contracts/multi-planner-protocol.md`)
  — a planner teammate's focused, cross-cluster-negotiated action plan over the
  audit's findings.
- **Review doc** — the reviewer role's pass over a candidate change-set,
  emitted as one document per review cycle.
- **Build log** — the builder role's append-only record of attempted edits,
  outcomes, and rollbacks for one engagement.

The shape of each is fixed by its archived workflow source above; this file
deliberately does not re-derive them — re-derivation without the source would
be a silent un-freeze.

## Unfreeze rule

Lifting the freeze on any one of these formats requires:

1. A dated, rationaled `product.md` §10 Spec Change Log entry per §9.
2. Re-proving the format conforms to the trust invariants in §4 and to the
   finding-schema / engagement-layout / meta-schema contracts in §7.
3. Restoring the defining workflow source from the archive (or authoring a
   replacement in this repo) before any code references the format as live.

Code, skills, or contracts that begin referencing these formats as live
without that §10 entry are bugs against the spec.
