"""Render the r03 synth prompt with r01's exact em-dash page_summary string.

Wraps scripts/test-specialist.py prepare-synthesizer to avoid shell escaping
issues with the em-dash (U+2014) character in --page-summary.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ENG_ID = "2026-04-29-bd952a50"
ENG_DIR = REPO / "docs" / "ecp" / ENG_ID

# r01's exact page_summary — em-dash (U+2014) preserved
PAGE_SUMMARY = (
    "SlingMods product detail page for Can-Am Spyder F3-RT Handlebar End Weights "
    "— accessory aftermarket part with PayPal Pay Later widget, fitment guide, "
    "customer reviews. Niche enthusiast audience."
)


def main() -> None:
    cluster_emissions = sorted(
        p for p in ENG_DIR.glob("cluster-*.json")
        if not p.name.startswith("cluster-context-")
    )
    desktop_screenshots = sorted(p for p in ENG_DIR.glob("section-*.jpg") if "mobile" not in p.name)
    mobile_screenshots = sorted(p for p in ENG_DIR.glob("section-*-mobile.jpg"))

    args = [
        sys.executable, str(REPO / "scripts" / "test-specialist.py"), "prepare-synthesizer",
        "--engagement-id", ENG_ID,
        "--ethics-findings-path", str(ENG_DIR / "ethics-findings.json"),
        "--desktop-baton-path", str(ENG_DIR / "baton-desktop-trimmed.json"),
        "--mobile-baton-path", str(ENG_DIR / "baton-mobile-trimmed.json"),
        "--desktop-viewport", "1920x1080",
        "--mobile-viewport", "390x844",
        "--page-type", "product",
        "--platform", "unknown",
        "--page-summary", PAGE_SUMMARY,
        "--canonical-f-refs-path", str(ENG_DIR / "canonical-f-refs.json"),
        "--out", str(ENG_DIR / ".prompts" / "synth.md"),
    ]
    for p in cluster_emissions:
        args.extend(["--cluster-emission", str(p)])
    for p in desktop_screenshots:
        args.extend(["--desktop-screenshot", str(p)])
    for p in mobile_screenshots:
        args.extend(["--mobile-screenshot", str(p)])

    print(f"cluster_emissions: {len(cluster_emissions)}")
    print(f"desktop_screenshots: {len(desktop_screenshots)}")
    print(f"mobile_screenshots: {len(mobile_screenshots)}")
    result = subprocess.run(args, cwd=REPO, capture_output=True, text=True, encoding="utf-8")
    print("STDOUT:", result.stdout[-500:] if result.stdout else "(empty)")
    if result.stderr:
        print("STDERR:", result.stderr[-1000:])
    print(f"Exit code: {result.returncode}")


if __name__ == "__main__":
    main()
