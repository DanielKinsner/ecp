"""ECP Audit Assembly — cluster file reconciliation package.

Pipeline:
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
