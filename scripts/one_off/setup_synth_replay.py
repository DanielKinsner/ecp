"""Set up 3 synth-replay engagement dirs cloned from r01.

Each replay dir gets:
- All r01 inputs verbatim (cluster JSONs, ethics, batons, baton-trimmed,
  canonical-f-refs, screenshots, meta.json, dom files)
- engagement_id rewritten everywhere from r01's id to the replay id
  (so outputs don't collide and the synth's emission is tagged uniquely)
- A freshly-rendered synth prompt pointed at the replay dir

NOT copied:
- audit-desktop.md / audit-mobile.md / synthesizer-emission-v1.json
  (those are r01's synth outputs; each replay should produce its own)
- phase-k-validate-report.json (per-run artifact)
- .prompts/synth.md (will be re-rendered for the new engagement_id)
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
R01_DIR = REPO / "docs" / "ecp" / "2026-04-29-ee4d6cc6"
R01_ENGAGEMENT_ID = "2026-04-29-ee4d6cc6"

REPLAYS = [
    ("2026-04-29-aaaaaaa1", "synth-replay against r01 inputs, attempt A"),
    ("2026-04-29-aaaaaaa2", "synth-replay against r01 inputs, attempt B"),
    ("2026-04-29-aaaaaaa3", "synth-replay against r01 inputs, attempt C"),
]

# Files to skip when copying — these are r01's outputs, not inputs
SKIP_FILES = {
    "audit-desktop.md",
    "audit-mobile.md",
    "synthesizer-emission-v1.json",
    "phase-k-validate-report.json",
    ".prompts/synth.md",
}

PAGE_SUMMARY = (
    "SlingMods product detail page for Can-Am Spyder F3-RT Handlebar End Weights "
    "— accessory aftermarket part with PayPal Pay Later widget, fitment guide, "
    "customer reviews. Niche enthusiast audience."
)


def copy_inputs(src: Path, dst: Path) -> None:
    """Recursively copy src → dst, skipping output files."""
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        rel_posix = rel.as_posix()
        if any(rel_posix == s or rel_posix.endswith("/" + s) for s in SKIP_FILES):
            continue
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def rewrite_engagement_id(directory: Path, old: str, new: str) -> None:
    """Replace `old` engagement_id with `new` in every JSON/MD/log/txt file."""
    extensions = {".json", ".md", ".log", ".txt"}
    for item in directory.rglob("*"):
        if not item.is_file():
            continue
        if item.suffix.lower() not in extensions:
            continue
        try:
            text = item.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # Binary or non-utf8 file, skip
        if old not in text:
            continue
        new_text = text.replace(old, new)
        item.write_text(new_text, encoding="utf-8")


def render_synth_prompt(replay_dir: Path, engagement_id: str) -> None:
    """Render a fresh synth prompt for the replay dir."""
    cluster_emissions = sorted(
        p for p in replay_dir.glob("cluster-*.json")
        if not p.name.startswith("cluster-context-")
    )
    desktop_screenshots = sorted(p for p in replay_dir.glob("section-*.jpg") if "mobile" not in p.name)
    mobile_screenshots = sorted(p for p in replay_dir.glob("section-*-mobile.jpg"))

    args = [
        sys.executable, str(REPO / "scripts" / "test-specialist.py"), "prepare-synthesizer",
        "--engagement-id", engagement_id,
        "--ethics-findings-path", str(replay_dir / "ethics-findings.json"),
        "--desktop-baton-path", str(replay_dir / "baton-desktop-trimmed.json"),
        "--mobile-baton-path", str(replay_dir / "baton-mobile-trimmed.json"),
        "--desktop-viewport", "1920x1080",
        "--mobile-viewport", "390x844",
        "--page-type", "product",
        "--platform", "unknown",
        "--page-summary", PAGE_SUMMARY,
        "--canonical-f-refs-path", str(replay_dir / "canonical-f-refs.json"),
        "--out", str(replay_dir / ".prompts" / "synth.md"),
    ]
    for p in cluster_emissions:
        args.extend(["--cluster-emission", str(p)])
    for p in desktop_screenshots:
        args.extend(["--desktop-screenshot", str(p)])
    for p in mobile_screenshots:
        args.extend(["--mobile-screenshot", str(p)])

    (replay_dir / ".prompts").mkdir(parents=True, exist_ok=True)
    result = subprocess.run(args, cwd=REPO, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"FAILED to render synth prompt for {engagement_id}: {result.stderr}")
        sys.exit(1)
    print(f"  rendered: {replay_dir / '.prompts' / 'synth.md'}")


def main() -> None:
    for replay_id, description in REPLAYS:
        replay_dir = REPO / "docs" / "ecp" / replay_id
        print(f"=== {replay_id} ({description}) ===")
        if replay_dir.exists():
            print(f"  removing existing {replay_dir}")
            shutil.rmtree(replay_dir)
        print(f"  copying inputs from {R01_DIR}")
        copy_inputs(R01_DIR, replay_dir)
        print(f"  rewriting engagement_id {R01_ENGAGEMENT_ID} -> {replay_id}")
        rewrite_engagement_id(replay_dir, R01_ENGAGEMENT_ID, replay_id)
        render_synth_prompt(replay_dir, replay_id)
        print()


if __name__ == "__main__":
    main()
