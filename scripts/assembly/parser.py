"""Cluster file parser for the ECP Audit Assembly package."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from .models import Finding, PassFinding, PRIORITY_ORDER

# Fields that mark the start of a new FINDING field (used for multi-line extraction)
_FIELD_NAMES = (
    "FINDING",
    "TITLE",
    "SECTION",
    "ELEMENT",
    "SYNTHESIS_HINT",
    "SOURCE",
    "OBSERVATION",
    "RECOMMENDATION",
    "REFERENCE",
    "PRIORITY",
    "ETHICS_STATE",
    "SOURCE_URL",
)

# Regex to split on any known field label at the start of a line
_NEXT_FIELD_RE = re.compile(
    r"^(?:" + "|".join(_FIELD_NAMES) + r"):",
    re.MULTILINE,
)

# Regex to extract a single-value field (everything after "FIELD: " on one line)
_SINGLE_LINE_RE = re.compile(r"^{field}:\s*(.+)$", re.MULTILINE)

# Code-fenced block: ```\n...\n```
_CODE_BLOCK_RE = re.compile(r"```\s*\n(.*?)```", re.DOTALL)

# Why this matters line
_WHY_RE = re.compile(r"\*\*Why this matters:\*\*\s*(.+?)(?=\n↳|\Z)", re.DOTALL)

# Citation line: ↳ ... [Gold|Silver|Bronze]
_CITATION_RE = re.compile(r"↳\s*(.+?)(?:\s*\[(Gold|Silver|Bronze)\])?\s*$", re.MULTILINE)


def _extract_single(block: str, field: str) -> str:
    """Extract a single-line field value from a FINDING block."""
    pattern = re.compile(r"^" + re.escape(field) + r":\s*(.+)$", re.MULTILINE)
    m = pattern.search(block)
    return m.group(1).strip() if m else ""


def _extract_multiline(block: str, field: str, next_fields: tuple[str, ...]) -> str:
    """Extract a potentially multi-line field value.

    Starts at 'FIELD: ' and continues until the next known field label or end of block.
    """
    # Build a pattern that finds FIELD: ... up to the next field boundary
    next_boundary = "|".join(re.escape(f) + r":" for f in next_fields)
    pattern = re.compile(
        r"^" + re.escape(field) + r":\s*(.*?)(?=^(?:" + next_boundary + r")|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(block)
    if not m:
        return ""
    return m.group(1).strip()


def _parse_finding_block(
    block: str,
    cluster: str,
    device: str,
    local_index: int,
) -> Optional[Finding]:
    """Parse a single code-fenced block into a Finding object.

    Returns None if the block is not a FINDING: FAIL or FINDING: PARTIAL block.
    """
    # Check verdict
    verdict_m = re.match(r"^\s*FINDING:\s*(FAIL|PARTIAL|PASS)\s*$", block, re.MULTILINE)
    if not verdict_m:
        return None
    verdict = verdict_m.group(1)
    if verdict == "PASS":
        return None  # PASS blocks are handled separately

    # Single-line fields
    title = _extract_single(block, "TITLE")
    section = _extract_single(block, "SECTION")
    element = _extract_single(block, "ELEMENT")
    source = _extract_single(block, "SOURCE")
    reference = _extract_single(block, "REFERENCE")
    priority_raw = _extract_single(block, "PRIORITY")
    synthesis_hint = _extract_single(block, "SYNTHESIS_HINT")
    ethics_state = _extract_single(block, "ETHICS_STATE")
    source_url = _extract_single(block, "SOURCE_URL")

    # Normalize priority
    priority = priority_raw.upper() if priority_raw else "MEDIUM"
    priority_rank = PRIORITY_ORDER.get(priority, 2)

    # Multi-line fields: OBSERVATION runs to RECOMMENDATION, REFERENCE, PRIORITY, or end
    observation = _extract_multiline(
        block,
        "OBSERVATION",
        ("RECOMMENDATION", "REFERENCE", "PRIORITY", "ETHICS_STATE", "SOURCE_URL"),
    )
    recommendation = _extract_multiline(
        block,
        "RECOMMENDATION",
        ("REFERENCE", "PRIORITY", "ETHICS_STATE", "SOURCE_URL"),
    )

    # Why this matters (may span multiple lines up to ↳)
    why_m = _WHY_RE.search(block)
    why_matters = why_m.group(1).strip() if why_m else ""

    # Citation line
    citation_m = _CITATION_RE.search(block)
    citation = citation_m.group(1).strip() if citation_m else ""
    tier = citation_m.group(2) if citation_m and citation_m.group(2) else ""

    return Finding(
        cluster=cluster,
        device=device,
        local_index=local_index,
        verdict=verdict,
        title=title,
        section=section,
        element=element,
        element_normalized=Finding.normalize_element(element),
        source=source,
        priority=priority,
        priority_rank=priority_rank,
        observation=observation,
        recommendation=recommendation,
        reference=reference,
        why_matters=why_matters,
        citation=citation,
        tier=tier,
        synthesis_hint=synthesis_hint,
        ethics_state=ethics_state,
        source_url=source_url,
        raw_block=block.strip(),
    )


def _parse_pass_block(block: str, cluster: str) -> Optional[PassFinding]:
    """Parse a code-fenced FINDING: PASS block into a PassFinding."""
    if not re.match(r"^\s*FINDING:\s*PASS\s*$", block, re.MULTILINE):
        return None
    # Use SECTION as identifier; fall back to ELEMENT or full text
    section = _extract_single(block, "SECTION")
    observation = _extract_multiline(block, "OBSERVATION", ("RECOMMENDATION", "REFERENCE", "PRIORITY"))
    label = section or observation[:80] or block.strip()[:80]
    return PassFinding(cluster=cluster, text=label)


def _extract_section(content: str, header: str) -> str:
    """Extract content under a ## level-2 section header.

    Stops at the next ## level-2 header (not ### subsections) or end of file.
    Uses '## [^#]' lookahead to avoid matching ### headers.
    """
    # Match the header line (consumes it) then capture until next ## or EOF
    pattern = re.compile(
        r"## " + re.escape(header) + r"[^\n]*\n(.*?)(?=\n## [^#]|\Z)",
        re.DOTALL,
    )
    m = pattern.search(content)
    return m.group(1) if m else ""


def _detect_ethics_status(content: str) -> str:
    """Return 'BLOCK', 'ADJACENT', or 'CLEAR' from structured ETHICS_STATE markers only.

    Prose-inference fallbacks (FINDING: FAIL inside ## Ethics Gate, bare
    ETHICS: X tokens) were removed in v1.0.0: they produced C3 split-brain
    where _detect_ethics_status said BLOCK via prose while the structured
    ethics_findings list was empty, leading to "VIOLATIONS FOUND + 0 BLOCK
    findings" contradictions in rendered reports.

    Only structured ETHICS_STATE: BLOCK / ETHICS_STATE: ADJACENT are recognised.
    Anything else (including prose-only ethics concerns that never made it
    into a structured finding block) returns CLEAR. Auditors that intend to
    flag an ethics concern MUST emit a structured FINDING block with
    ETHICS_STATE and SOURCE_URL — see contracts/dispatch-contract.md and
    workflows/audit.md.
    """
    if re.search(r"ETHICS_STATE:\s*BLOCK", content, re.IGNORECASE):
        return "BLOCK"
    if re.search(r"ETHICS_STATE:\s*ADJACENT", content, re.IGNORECASE):
        return "ADJACENT"
    return "CLEAR"


def parse_cluster_file(
    filepath: Path,
    cluster: str,
    device: str,
) -> tuple[list[Finding], list[PassFinding], str]:
    """Parse a single cluster file.

    Returns (findings, pass_findings, ethics_status).
    """
    content = filepath.read_text(encoding="utf-8")

    # Detect ethics status
    ethics_status = _detect_ethics_status(content)

    # Isolate the ## Findings section to avoid parsing blocks in other sections
    findings_section = _extract_section(content, "Findings") or content

    # Parse all code-fenced blocks within ## Findings
    findings: list[Finding] = []
    local_index = 1
    for block_m in _CODE_BLOCK_RE.finditer(findings_section):
        block = block_m.group(1)
        finding = _parse_finding_block(block, cluster, device, local_index)
        if finding is not None:
            findings.append(finding)
            local_index += 1

    # Parse pass findings from two sources:
    # 1. code-fenced FINDING: PASS blocks in ## What's Working Well
    # 2. bullet-point lines in ## What's Working Well

    pass_findings: list[PassFinding] = []

    # Find the ## What's Working Well section (handles both curly and straight apostrophes)
    ww_text = _extract_section(content, "What\u2019s Working Well") or _extract_section(
        content, "What's Working Well"
    )

    # Parse code-fenced FINDING: PASS blocks and bullet-point lines
    if ww_text:
        # Code-fenced PASS blocks
        for block_m in _CODE_BLOCK_RE.finditer(ww_text):
            block = block_m.group(1)
            pf = _parse_pass_block(block, cluster)
            if pf is not None:
                pass_findings.append(pf)

        # Bullet-point lines (- **section**: description)
        for line in ww_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("- "):
                text = stripped[2:].strip()
                if text:
                    pass_findings.append(PassFinding(cluster=cluster, text=text))

    return findings, pass_findings, ethics_status


def load_all_cluster_files(
    engagement_dir: Path,
    device: str,
    clusters: list[str],
) -> tuple[list[Finding], list[PassFinding], str]:
    """Load all cluster files for a given device and aggregate results.

    Overall ethics: BLOCK if any cluster has BLOCK, else ADJACENT if any has ADJACENT,
    else CLEAR.
    """
    all_findings: list[Finding] = []
    all_pass_findings: list[PassFinding] = []
    ethics_votes: list[str] = []
    missing: list[str] = []

    for cluster in clusters:
        filename = f"cluster-{cluster}-{device}.md"
        filepath = engagement_dir / filename

        if not filepath.exists():
            # Collect and report at end — silent skip was a bug (Codex
            # Phase 1 HIGH). A missing cluster file for a cluster in
            # meta.json's clusters_used array means either the auditor
            # failed or the lead didn't prune the cluster from the list.
            # Either way, shipping a partial audit is worse than failing
            # loud with a resolution path.
            missing.append(filename)
            continue

        findings, pass_findings, ethics_status = parse_cluster_file(filepath, cluster, device)
        all_findings.extend(findings)
        all_pass_findings.extend(pass_findings)
        ethics_votes.append(ethics_status)

        print(f"  {filename}: {len(findings)} findings, {len(pass_findings)} passes, ethics={ethics_status}")

    if missing:
        raise FileNotFoundError(
            f"Missing {len(missing)} cluster file(s) for device={device}: "
            f"{', '.join(missing)}. "
            "Resolution: (1) retry the failed auditor(s) to produce the "
            "missing file(s), OR (2) remove the cluster slug(s) from "
            "meta.json's 'clusters_used' array if the cluster was "
            "intentionally skipped (empty-slice pruning or persistent "
            "auditor failure). Partial audits MUST NOT ship — the "
            "silent-skip behavior was a bug (Codex Phase 1 HIGH)."
        )

    # Aggregate ethics
    if "BLOCK" in ethics_votes:
        overall_ethics = "BLOCK"
    elif "ADJACENT" in ethics_votes:
        overall_ethics = "ADJACENT"
    else:
        overall_ethics = "CLEAR"

    return all_findings, all_pass_findings, overall_ethics
