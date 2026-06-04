"""Capture-coverage report: did the acquirer grab the hero controls?

Summarizes a baton's ``elements[]`` into control-type coverage, so a before/after
audit verifies the acquirer element-capture fix (Root Cause #1 of the 2026-06-02
hotspot diagnosis) worked *at the source* — the selector allowlist used to drop
<select>/dropdowns, submit inputs, gallery thumbnails, and promo bars.

Usage:
    python scripts/report/capture_coverage.py report  --engagement <dir>
    python scripts/report/capture_coverage.py compare --before <dir> --after <dir>
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from cli_io import force_utf8_io  # noqa: E402

_BUCKETS = ("dropdown", "submit_input", "gallery", "promo", "aria_named", "button", "input")


def classify(el: dict) -> set[str]:
    """Which control buckets a captured element falls into (may be several)."""
    tag = (el.get("tag") or "").lower()
    sel = (el.get("selector") or "").lower()
    cls = (el.get("class") or "").lower()
    out: set[str] = set()
    if tag == "select" or any(k in sel for k in ("combobox", "listbox", "dropdown")) or "dropdown" in cls:
        out.add("dropdown")
    if tag == "input" and ("submit" in sel or "button" in sel):
        out.add("submit_input")
    if tag == "input":
        out.add("input")
    if tag == "button" or "btn" in sel or sel == "button" or sel == '[role="button"]':
        out.add("button")
    if any(k in sel for k in ("gallery", "thumb")) or any(k in cls for k in ("gallery", "thumb")):
        out.add("gallery")
    if any(k in sel for k in ("announce", "promo", "shipping")) or any(k in cls for k in ("announce", "promo")):
        out.add("promo")
    if "aria-label" in sel:
        out.add("aria_named")
    return out


def coverage(engagement: Path, baton_file: str) -> dict | None:
    p = engagement / baton_file
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    els = [e for e in (data.get("elements") or []) if isinstance(e, dict)]
    buckets: Counter = Counter()
    for e in els:
        for b in classify(e):
            buckets[b] += 1
    return {
        "baton": baton_file,
        # Prefer the baton's self-declared device; fall back to filename
        # inference so a delta is never mislabeled by list position.
        "device": data.get("device") or _device_for_baton(baton_file),
        "total": len(els),
        "tags": dict(Counter((e.get("tag") or "?") for e in els)),
        "controls": {b: buckets.get(b, 0) for b in _BUCKETS},
    }


def _device_for_baton(baton_file: str) -> str:
    """Infer the device from a baton filename when the baton omits ``device``.

    ``baton.json`` is the primary (non-mobile) capture; ``baton-mobile.json``
    is mobile; ``baton-laptop.json`` / ``baton-desktop.json`` name themselves.
    """
    name = baton_file.lower()
    if "mobile" in name:
        return "mobile"
    if "laptop" in name:
        return "laptop"
    return "desktop"


def compare_coverage(before: Path, after: Path) -> dict:
    """Per-device before/after control-coverage delta.

    Pairs batons by their real ``device`` (never by list index), so BOTH
    desktop and mobile are surfaced and a present-on-one-side-only device is
    flagged rather than silently mislabeled. Closes the desktop-blind +
    mislabel bugs (adversarial review 2026-06-03, §1 P0-2).
    """
    b_rep, a_rep = report(before), report(after)
    b_by_dev = {c["device"]: c for c in b_rep["batons"]}
    a_by_dev = {c["device"]: c for c in a_rep["batons"]}

    def _present(maps: dict, dev: str) -> bool:
        # laptop satisfies the non-mobile ("desktop") slot.
        if dev == "desktop":
            return "desktop" in maps or "laptop" in maps
        return dev in maps

    warnings: list[str] = []
    for dev in ("desktop", "mobile"):
        label = "desktop/laptop" if dev == "desktop" else dev
        in_b, in_a = _present(b_by_dev, dev), _present(a_by_dev, dev)
        if not in_b and not in_a:
            warnings.append(
                f"{label} baton absent in both engagements — this delta does not "
                f"cover {label}"
            )
        elif in_a != in_b:
            side, other = ("after", "before") if in_a else ("before", "after")
            warnings.append(f"{label} baton present in '{side}' but absent in '{other}'")

    devices: list[dict] = []
    for dev in sorted(set(b_by_dev) | set(a_by_dev)):
        b_ctl = b_by_dev.get(dev, {}).get("controls", {})
        a_ctl = a_by_dev.get(dev, {}).get("controls", {})
        devices.append({
            "device": dev,
            "baton": (a_by_dev.get(dev) or b_by_dev.get(dev) or {}).get("baton"),
            "delta": {k: (b_ctl.get(k, 0), a_ctl.get(k, 0)) for k in _BUCKETS},
        })
    return {
        "before": before.name,
        "after": after.name,
        "devices": devices,
        "warnings": warnings,
    }


def report(engagement: Path) -> dict:
    out = {"engagement": engagement.name, "batons": []}
    for bf in ("baton.json", "baton-mobile.json"):
        cov = coverage(engagement, bf)
        if cov is not None:
            out["batons"].append(cov)
    return out


def _print_report(rep: dict) -> None:
    print(f"== Capture coverage: {rep['engagement']} ==")
    for c in rep["batons"]:
        ctl = c["controls"]
        print(f"\n[{c['baton']}] {c['total']} elements")
        print("  controls: " + "  ".join(f"{k}={ctl[k]}" for k in _BUCKETS))


def main(argv: list[str] | None = None) -> int:
    force_utf8_io()
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report", help="control-coverage of one engagement's batons")
    r.add_argument("--engagement", required=True, type=Path)
    r.add_argument("--json", type=Path, default=None)
    c = sub.add_parser("compare", help="before/after control-coverage delta")
    c.add_argument("--before", required=True, type=Path)
    c.add_argument("--after", required=True, type=Path)

    args = p.parse_args(argv)
    if args.cmd == "report":
        rep = report(args.engagement)
        if not rep["batons"]:
            print(f"No baton*.json under {args.engagement}", file=sys.stderr)
            return 2
        _print_report(rep)
        if args.json:
            args.json.write_text(json.dumps(rep, indent=2), encoding="utf-8")
        return 0
    if args.cmd == "compare":
        cmp = compare_coverage(args.before, args.after)
        if not cmp["devices"]:
            print(f"No baton*.json under {args.before} or {args.after}", file=sys.stderr)
            return 2
        print(f"== Capture-coverage delta: {cmp['before']} -> {cmp['after']} ==")
        for w in cmp["warnings"]:
            print(f"  WARNING: {w}", file=sys.stderr)
        for d in cmp["devices"]:
            print(f"\n[{d['device']}] ({d['baton']})")
            for k in _BUCKETS:
                bv, av = d["delta"][k]
                arrow = "↑" if av > bv else ("↓" if av < bv else "=")
                print(f"  {k:14s} {bv:3d} -> {av:3d}  {arrow}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
