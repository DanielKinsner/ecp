"""Trim r03 batons (desktop + mobile) to referenced elements per Phase F.3.

Loads all cluster-*.json + ethics-findings.json, gathers findings per-device,
calls synth_input.trim_baton_file. Outputs baton-{device}-trimmed.json.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from assembly.json_parser import parse_emission_file
from assembly.synth_input import trim_baton_file

ENG_DIR = REPO / "docs" / "ecp" / "2026-04-29-bd952a50"


def gather_findings(device: str):
    findings = []
    for path in sorted(ENG_DIR.glob("cluster-*.json")):
        if "cluster-context-" in path.name:
            continue
        result = parse_emission_file(path)
        for f in result.findings:
            if f.device == device or f.device == "page":
                findings.append(f)
    eth_path = ENG_DIR / "ethics-findings.json"
    if eth_path.exists():
        eth = parse_emission_file(eth_path)
        for f in eth.findings:
            if f.device == device or f.device == "page":
                findings.append(f)
    return findings


def main() -> None:
    desktop_findings = gather_findings("desktop")
    mobile_findings = gather_findings("mobile")
    print(f"Desktop findings: {len(desktop_findings)}")
    print(f"Mobile findings: {len(mobile_findings)}")

    desktop_summary = trim_baton_file(
        ENG_DIR / "baton.json",
        desktop_findings,
        ENG_DIR / "baton-desktop-trimmed.json",
    )
    mobile_summary = trim_baton_file(
        ENG_DIR / "baton-mobile.json",
        mobile_findings,
        ENG_DIR / "baton-mobile-trimmed.json",
    )
    print(f"Desktop baton: {desktop_summary['input_count']} -> {desktop_summary['output_count']} elements")
    print(f"Mobile  baton: {mobile_summary['input_count']} -> {mobile_summary['output_count']} elements")


if __name__ == "__main__":
    main()
