# Repository Conventions

This repository keeps product runtime, research evidence, tests, generated reports, and planning history close together. That is useful, but it also means new material needs an explicit source boundary before agents or humans treat it as active product state.

## Source Categories

### Runtime Instructions

Runtime instructions tell an agent or script what to do during a current audit, report build, validation run, or package workflow.

Examples:

- `skills/**/SKILL.md`
- `workflows/**`
- Codex or plugin runtime entrypoints
- Active runbooks used by current automation

Default handling:

- Keep runtime files short, current, and operational.
- Put only instructions that should affect present behavior in these files.
- Move history, rationale, and migration notes into nearby `.notes.md` files when they are useful but not needed on every run.
- Use explicit priority language only when the runtime consequence is clear.

### Contracts And Schemas

Contracts and schemas define required data shape, validation expectations, or cross-step compatibility.

Examples:

- JSON schemas
- validator contracts
- report artifact contracts
- evidence, finding, cluster, or review-state shape documentation

Default handling:

- Treat these files as product correctness surfaces.
- Keep examples minimal and aligned with current code.
- When a contract changes, update the readers, writers, validators, and tests that rely on it in the same work slice.

### References

References are retrieved selectively for audit reasoning, research support, legal/ethics guidance, evidence standards, or domain interpretation.

Examples:

- `references/**`
- evidence tier guidance
- ethics and legal review material
- domain-specific research notes

Default handling:

- References may be longer and more contextual than runtime files because they are not always-on instructions.
- Preserve evidence fidelity and source wording where accuracy matters.
- Do not weaken legal, ethics, citation, or evidence requirements for prompt-size cleanup.

### Tests And Fixtures

Tests and fixtures prove behavior without requiring full historical engagement archives.

Examples:

- `tests/**`
- `tests/fixtures/**`
- focused HTML, JSON, screenshot, or state samples used by tests

Default handling:

- Prefer the smallest fixture that proves the regression or contract.
- Document what each fixture protects.
- Do not point tests at full `docs/ecp/<id>` engagement folders unless the test explicitly needs full-report shape and explains why.

### Generated Engagements

Generated engagements are audit outputs, screenshots, DOM captures, reports, logs, and intermediate artifacts produced by a run.

Examples:

- `docs/ecp/<date-id>/**`
- generated `visual-report*.html`
- captured DOM, baton, screenshot, and review-state artifacts
- audit logs tied to a specific generated engagement

Default handling:

- New `docs/ecp/<id>` engagements are local and untracked by default.
- Promote only the smallest useful subset when a generated engagement becomes fixture or reference material.
- Audit logs are evidence only when the engagement itself is intentionally tracked or otherwise preserved as an approved reference.
- Large generated artifacts should not be added to normal Git unless they are explicitly promoted as fixtures or reference material.

### Archives And Historical Plans

Archives and historical plans explain prior decisions, completed handoffs, deferred ideas, or superseded work.

Examples:

- old handoff documents
- completed plans
- deferred architecture proposals
- historical audit reports kept for context

Default handling:

- Historical material should not masquerade as current runtime instruction.
- Mark superseded or deferred documents clearly when they remain in the repo.
- Full archived reports belong outside the normal source flow unless they are explicitly promoted as reference engagements.

## Promotion Rules

Before adding generated or historical material to normal Git, decide which category it belongs to.

Use this default path:

1. Keep new generated engagement output local and untracked.
2. If tests need it, extract a minimal fixture under `tests/fixtures/`.
3. If humans need it as a durable example, promote only the relevant reference subset.
4. If the whole engagement must be preserved, record that decision in the plan or handoff that promotes it.

Promotion should name the reason the artifact belongs in source control: regression coverage, reference evidence, contract example, or active runtime behavior.

## Agent Handling Rules

Agents should read runtime files for current execution, contracts for required shape, references for selective support, fixtures for test evidence, and plans for coordination. Do not infer that a file is active runtime just because it is large, recent, or detailed.

When source boundaries are unclear, pause before broad rewrites and classify the material first.
