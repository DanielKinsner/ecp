#!/usr/bin/env python3
"""Lead-side prep helpers for v2 audit pipeline.

Two operations the lead runs at well-defined phase boundaries to close
gaps that surfaced during 2026-05-02 (engagement 9cd2a2ac) post-mortem:

1. ``normalize-scrolly`` — runs AFTER acquisition, BEFORE specialist
   dispatch. Acquirers sometimes report STATUS: COMPLETE but leave
   ``baton.{screenshots,sections}[].scrollY`` empty. The renderer's
   ``_slide_for_y`` then collapses every element to slide 0 because
   every slide reports ``scrollY=0``. This step recovers the real
   per-section scroll position from ``elements-{?mobile-}sN.json``'s
   ``scroll_y_at_capture`` field (which the acquirer DOES populate
   correctly via the JS eval) and writes it back into the baton.

2. ``build-canonical-frefs`` — runs AFTER all specialists complete and
   BEFORE the synthesizer dispatch. The ``contracts/synthesizer-v2.md``
   prompt expects ``{{canonical_f_refs_manifest}}`` to be inlined
   verbatim so the synthesizer cites cluster-local 1-based indices
   matching the renderer's display order. Skipping this step lets the
   synthesizer mint its own numbering (``visual-cta F-77`` etc) which
   diverges from priority_path's ``visual-cta F-01..F-06``, and the
   render-time filter (``v2_loader.load_v2_priority_path``, line ~691)
   drops every Priority Path story for falling below the 2-actionable-
   ref threshold. Writes ``canonical-f-refs-manifest.json`` and a
   markdown ``canonical-f-refs-manifest.md`` for prompt inlining.

Usage::

    python scripts/lead_prep.py normalize-scrolly --engagement docs/ecp/<id>
    python scripts/lead_prep.py build-canonical-frefs --engagement docs/ecp/<id>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable


def _read_elements(path: Path) -> list[dict]:
    """Tolerant element-file reader. Some acquirer paths double-encode
    the JSON (write a string that itself parses to a list); handle both.
    Returns ``[]`` on any read/parse error rather than raising."""
    if not path.exists():
        return []
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return []
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            return []
    if isinstance(data, list):
        return [e for e in data if isinstance(e, dict)]
    if isinstance(data, dict):
        elems = data.get("elements", [])
        if isinstance(elems, list):
            return [e for e in elems if isinstance(e, dict)]
    return []


def _scrolly_for_section(elements: list[dict]) -> int | None:
    """Pick the dominant ``scroll_y_at_capture`` value. Acquirer sets
    the same value on every element captured at one scroll position;
    fall back to the first non-zero value if the file is mixed."""
    if not elements:
        return None
    seen: dict[int, int] = {}
    for e in elements:
        sy = e.get("scroll_y_at_capture")
        if sy is None:
            continue
        try:
            sy_int = int(sy)
        except (TypeError, ValueError):
            continue
        seen[sy_int] = seen.get(sy_int, 0) + 1
    if not seen:
        return None
    # Most common value wins; ties broken by smaller scrollY (earliest).
    return sorted(seen.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def normalize_scrolly(engagement: Path) -> int:
    """Populate baton.{screenshots,sections}[].scrollY from element files.

    Runs idempotently — re-running on a baton that already has correct
    scrollY values changes nothing. Returns process exit code (0 ok)."""
    fixed = 0
    for baton_name, suffix in (("baton.json", ""), ("baton-mobile.json", "-mobile")):
        baton_path = engagement / baton_name
        if not baton_path.exists():
            print(f"[skip] {baton_name}: not present")
            continue
        try:
            baton = json.loads(baton_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"[error] {baton_name}: invalid JSON ({e})", file=sys.stderr)
            return 2

        screenshots = baton.get("screenshots", []) or []
        sections = baton.get("sections", []) or []
        n_sections = max(len(screenshots), len(sections))
        # The acquirer captures element coords per scroll position into
        # elements-{suffix}-sN.json (1-indexed). Walk those to recover
        # scrollY.
        recovered: list[int | None] = []
        for i in range(1, n_sections + 1):
            elem_path = engagement / f"elements{suffix}-s{i}.json"
            elements = _read_elements(elem_path)
            recovered.append(_scrolly_for_section(elements))

        changed = False
        for i, sy in enumerate(recovered):
            if sy is None:
                continue
            if i < len(screenshots):
                ss = screenshots[i]
                if isinstance(ss, dict) and (ss.get("scrollY") in (None, 0) or ss.get("scrollY") != sy):
                    if ss.get("scrollY") != sy:
                        ss["scrollY"] = sy
                        changed = True
            if i < len(sections):
                sec = sections[i]
                if isinstance(sec, dict) and sec.get("scrollY") != sy:
                    sec["scrollY"] = sy
                    changed = True

        if changed:
            baton_path.write_text(json.dumps(baton, indent=2), encoding="utf-8")
            fixed += 1
            print(f"[fixed] {baton_name}: scrollY = {recovered}")
        else:
            print(f"[ok]    {baton_name}: scrollY already populated")

    print(f"\nnormalize-scrolly: fixed {fixed} baton file(s)")
    return 0


def _cluster_emissions(engagement: Path) -> Iterable[tuple[Path, dict]]:
    for path in sorted(engagement.glob("cluster-*-*.json")):
        # Skip cluster-context-* files — those are the DOM slices, not emissions.
        if path.name.startswith("cluster-context-"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and data.get("findings"):
            yield path, data


def build_canonical_frefs(engagement: Path) -> int:
    """Compute canonical f_refs from cluster emissions using the SAME
    algorithm the renderer uses (``scripts/assembly/pipeline.py:
    FinalizedFindings.build``). Display indices are content-hash-derived
    (sha256(surface|baton_index|verdict)[:6] mod 99 + 1) per Phase L
    (2026-04-29), NOT cluster-local 1-based.

    Why content-hashed instead of 1-based: positional 1-based indexing
    means the same finding gets a different F-NN on every re-run as the
    specialist's emission order shifts. Hash-derived F-NN keeps the same
    conceptual finding pinned to the same identifier across runs (drift
    target ref TARr ≈ 0). The synthesizer MUST cite these specific
    integers because the renderer re-derives them at parse time and
    rejects mismatched refs as out-of-allowlist.

    Writes two files:
    - ``canonical-f-refs-manifest.json`` — structured for tooling
    - ``canonical-f-refs-manifest.md`` — for inlining into the
      synthesizer prompt under the ``{{canonical_f_refs_manifest}}``
      placeholder. Paste verbatim — the integers are non-negotiable.

    Returns process exit code (0 ok).
    """
    # Lazy import — same pattern as v2_loader._build_canonical_view, so
    # the algorithm stays a single source of truth.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from assembly.json_parser import parse_emission_file
        from assembly.pipeline import FinalizedFindings
    except ImportError as e:
        print(f"[error] couldn't import assembly module: {e}", file=sys.stderr)
        return 3

    findings_assembly: list = []
    clusters_used: list[str] = []
    devices_by_local: dict[tuple, list[str]] = {}

    # Phase 4a hardening (2026-05-18) — load anchor-candidates sidecars
    # per device so parse_emission_file can resolve candidate_id references
    # in visual_evidence.observed_anchor into canonical baton_index. Pre-fix,
    # build-canonical-frefs called parse_emission_file(path) without the
    # sidecar and silently rejected candidate_id-only emissions because the
    # element.baton_index was empty. Closes Codex 2026-05-18 review item 2
    # on ffeb1a6. Mirrors the same wiring in
    # scripts/build_canonical_f_refs.py and scripts/report/v2_loader.py.
    #
    # Phase 4b hardening 2 (2026-05-18) — use the strict shared loader.
    # Missing file → None (legacy skip). Present-but-broken → raise and
    # propagate to a non-zero exit. Codex 2026-05-18 review of 64ce7f2.
    from assembly.anchor_candidates import (
        SidecarLoadError, load_anchor_candidates_sidecar_strict,
    )
    sidecar_by_device: dict[str, dict | None] = {}
    try:
        for dev in ("desktop", "mobile", "laptop"):
            sidecar_by_device[dev] = load_anchor_candidates_sidecar_strict(
                engagement / f"anchor-candidates-{dev}.json"
            )
    except SidecarLoadError as e:
        print(f"[error] {e}", file=sys.stderr)
        return 1
    if any(sidecar_by_device.values()):
        loaded = [d for d, s in sidecar_by_device.items() if s is not None]
        print(f"[info] loaded anchor-candidates sidecars for: {', '.join(loaded)}")

    for path, data in _cluster_emissions(engagement):
        cluster = data.get("cluster", "unknown")
        device = data.get("device", "unknown")
        if cluster not in clusters_used:
            clusters_used.append(cluster)
        sidecar = sidecar_by_device.get(device)
        try:
            res = parse_emission_file(path, anchor_candidates_sidecar=sidecar)
        except Exception as e:
            print(f"[warn] couldn't parse {path.name}: {e}", file=sys.stderr)
            continue
        findings_assembly.extend(res.findings)
        # Track devices_present for cross-device merge reporting (the
        # renderer's Layer-2.5 cross-device-title-merge handles canonical
        # ref consolidation; we just surface visibility here).
        for f in res.findings:
            key = (cluster, (f.title or "").strip().lower())
            devices_by_local.setdefault(key, []).append(device)

    if not findings_assembly:
        print("[error] no cluster emissions found", file=sys.stderr)
        return 3

    finalized = FinalizedFindings.build(findings_assembly, clusters_used)
    manifest_entries: list[dict] = []
    for f in finalized.findings:
        key = (f.cluster, (f.title or "").strip().lower())
        devs = sorted(set(devices_by_local.get(key, [f.device or "unknown"])))
        manifest_entries.append({
            "f_ref": f"{f.cluster} F-{f.display_index:02d}",
            "cluster": f.cluster,
            "display_index": f.display_index,
            "title": f.title or "",
            "severity": f.priority or "MEDIUM",
            "devices_present": devs,
            "device": f.device or "unknown",
        })

    by_cluster: dict[str, list] = {}
    for entry in manifest_entries:
        by_cluster.setdefault(entry["cluster"], []).append(entry)

    # Write the structured JSON manifest
    json_path = engagement / "canonical-f-refs-manifest.json"
    json_path.write_text(
        json.dumps({"engagement": str(engagement), "entries": manifest_entries}, indent=2),
        encoding="utf-8",
    )

    # Write the markdown form for synthesizer prompt inlining
    md_lines = [
        "# Canonical f_refs manifest",
        "",
        "USE ONLY THESE f_refs in priority_path[].f_refs, scope_page_synchronized_refs,",
        "quick_wins_manifest, severity_manifest, humanized_findings[].f_ref, and as the",
        "heading suffix on each finding subsection in audit-{device}.md.",
        "",
        "Format: `{cluster} F-{NN}` (zero-padded). The NN integer is",
        "**content-hash-derived** (sha256(surface|baton_index|verdict)[:6] mod 99 + 1)",
        "per `scripts/assembly/pipeline.py:assign_display_indices`. The renderer",
        "re-derives the same hash at parse time and rejects mismatched refs as",
        "out-of-allowlist — paste these integers verbatim, do NOT renumber.",
        "",
        "| f_ref | severity | devices_present | title |",
        "|---|---|---|---|",
    ]
    for entry in manifest_entries:
        devices = ",".join(sorted(entry["devices_present"]))
        title = entry["title"].replace("|", "\\|")[:80]
        md_lines.append(f"| `{entry['f_ref']}` | {entry['severity']} | {devices} | {title} |")
    md_lines.append("")
    md_lines.append(f"_Total: {len(manifest_entries)} canonical f_refs across {len(by_cluster)} cluster(s)._")

    md_path = engagement / "canonical-f-refs-manifest.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"[ok] wrote {json_path.name} and {md_path.name}")
    print(f"     {len(manifest_entries)} canonical f_refs across {len(by_cluster)} cluster(s)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_norm = sub.add_parser("normalize-scrolly", help="Populate baton scrollY from element files")
    p_norm.add_argument("--engagement", required=True, type=Path)

    p_man = sub.add_parser("build-canonical-frefs", help="Compute canonical f_refs manifest from cluster emissions")
    p_man.add_argument("--engagement", required=True, type=Path)

    args = parser.parse_args()
    if not args.engagement.exists():
        print(f"[error] engagement dir not found: {args.engagement}", file=sys.stderr)
        return 1

    if args.cmd == "normalize-scrolly":
        return normalize_scrolly(args.engagement)
    if args.cmd == "build-canonical-frefs":
        return build_canonical_frefs(args.engagement)
    return 1


if __name__ == "__main__":
    sys.exit(main())
