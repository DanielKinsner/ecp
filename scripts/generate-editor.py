#!/usr/bin/env python3
"""Generate ECP review-state JSON and a self-contained editor.html."""
from __future__ import annotations

import argparse
from pathlib import Path

from assembly.review_state import generate_editor_artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate ECP review editor artifacts")
    parser.add_argument("--engagement", required=True, help="Path to engagement directory")
    parser.add_argument("--plugin-root", required=True, help="Path to plugin root")
    parser.add_argument(
        "--device",
        action="append",
        choices=["desktop", "mobile", "laptop"],
        help="Device to include. Repeat for multiple devices. Defaults to available engagement devices.",
    )
    parser.add_argument(
        "--overwrite-review-state",
        action="store_true",
        help="Regenerate review-state files even if they already exist. Use carefully; this can replace human edits.",
    )
    args = parser.parse_args()
    outputs = generate_editor_artifacts(
        Path(args.engagement),
        Path(args.plugin_root),
        devices=args.device,
        overwrite_review_state=args.overwrite_review_state,
    )
    for label, path in outputs.items():
        print(f"{label}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
