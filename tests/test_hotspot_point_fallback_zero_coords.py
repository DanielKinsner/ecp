"""Point-fallback hotspots must honor legitimate 0% coordinates.

``build_hotspot_overlays_html``'s point branch used ``m.get("x_pct") or 92``
(and ``or 10`` for y), so a marker placed at an exact screen edge — x or y of
0.0, falsy in Python — teleported to the (92,10) "no data" default. Latent
while only auto-mapped markers flowed through; load-bearing once V2 routed
operator cx_pct/cy_pct point placements into this branch (an operator CAN pin
a point at the very top/left edge). The default must apply only when the
coordinate is absent, not when it is zero.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.templates.components import build_hotspot_overlays_html  # noqa: E402


def _finding(index: int = 1) -> dict:
    return {"index": index, "fid": "hero/F-01", "cluster_index": index}


def _point_marker(**coords) -> dict:
    marker = {
        "number": 1,
        "finding_index": 1,
        "severity": "high",
        "shape": "point",
    }
    marker.update(coords)
    return marker


def test_zero_coords_render_at_zero_not_default():
    html = build_hotspot_overlays_html(
        [_finding()], {0: [_point_marker(x_pct=0.0, y_pct=0.0)]}
    )
    assert "left:calc(0.00% - 16px)" in html, html
    assert "top:calc(0.00% - 16px)" in html, html


def test_missing_coords_keep_92_10_default():
    html = build_hotspot_overlays_html([_finding()], {0: [_point_marker()]})
    assert "left:calc(92.00% - 16px)" in html, html
    assert "top:calc(10.00% - 16px)" in html, html
