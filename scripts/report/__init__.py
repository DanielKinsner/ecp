"""ECP Visual Report Generator — modular package.

Pipeline:
  CLI args -> _load_inputs() -> parse_findings() -> _resolve_citations()
  -> auto_map_markers() -> _process_screenshots() -> _compute_metrics()
  -> _build_html_fragments() -> assemble_html() -> _write_output()
"""

from .html_builder import generate_report

__all__ = ["generate_report"]
