"""ECP Visual Report Generator — modular package.

v2 render path (CANONICAL — what live audits use):
  load_v2_engagement() -> auto_map_markers_v2() -> compute_marker_positions_v2()
  -> validate_v2_hotspot_geometry() -> v2_html_builder.generate_v2_report()

v1 render path (LEGACY markdown renderer, retained for archived v1 engagements):
  CLI args -> _load_inputs() -> parse_findings() -> _resolve_citations()
  -> auto_map_markers() -> _process_screenshots() -> _compute_metrics()
  -> _build_html_fragments() -> assemble_html() -> _write_output()
"""

from .html_builder import generate_report

__all__ = ["generate_report"]
