# Review State Migrations

The editor loads `review_state_schema_version` from inline review-state JSON.

- Same version: load directly.
- Older version with a migration: upgrade in memory and preserve the original state for download before saving.
- Older version without a migration: stop with a clear maintainer-facing error.
- Newer version: stop and ask the operator to upgrade the editor.

Migrations should be pure functions that accept a state object and return a new state object. They must not mutate raw ECP artifacts such as `baton.json`, cluster emissions, synthesizer emissions, or AI draft visual reports.
