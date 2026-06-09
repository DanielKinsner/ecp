"""ECP Audit Assembly — cluster file reconciliation package.

This package mixes the live v2 JSON pipeline (canary_checks, synth_input,
review_state, reflection_state/report_state state machines, emission_autofix,
…) with the LEGACY v1 markdown reconciliation pipeline below. The v1 pipeline
runs only for archived v1 markdown engagements; a v2 run reconciles via the
synthesizer + canonical f_refs, not load_all_cluster_files().

v1 (legacy markdown) pipeline:
  CLI args -> load_all_cluster_files() -> deduplicate()
  -> score_groups() -> write_audit_md() + write_sidecars()
"""
from .parser import load_all_cluster_files
from .dedup import deduplicate
from .scoring import score_groups
from .writer import write_audit_md, write_sidecars

__all__ = [
    "load_all_cluster_files",
    "deduplicate",
    "score_groups",
    "write_audit_md",
    "write_sidecars",
]
