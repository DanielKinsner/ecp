"""Finding and source parsing functions."""

import re


def parse_findings(audit_path):
    """Parse audit.md to extract FAIL and PARTIAL findings.

    Supports two formats:
    1. Fenced: findings wrapped in triple-backtick code blocks
    2. Unfenced: FINDING: line followed by field lines, terminated by blank
       line, next heading (** or #), or EOF

    Also detects cluster membership from ### cluster headings.
    """
    with open(audit_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Build cluster map: list of (char_offset, cluster_slug) from ### headings
    cluster_map = []
    for m in re.finditer(r"^### ([\w-]+) cluster", content, re.MULTILINE):
        cluster_map.append((m.start(), m.group(1)))

    def cluster_at(pos):
        """Return cluster slug for a character position in content."""
        result = None
        for offset, slug in cluster_map:
            if offset <= pos:
                result = slug
            else:
                break
        return result

    findings = []

    # Strategy 1: fenced blocks  ```\nFINDING: FAIL\n...\n```
    fenced = list(re.finditer(
        r"```\s*\nFINDING:\s*(FAIL|PARTIAL)\s*\n(.*?)```",
        content,
        re.DOTALL,
    ))

    # Strategy 2: unfenced blocks
    if not fenced:
        fenced = list(re.finditer(
            r"^FINDING:\s*(FAIL|PARTIAL)\s*\n(.*?)(?=\n\n\*\*\d|^FINDING:|^## |^### |^# |\Z)",
            content,
            re.DOTALL | re.MULTILINE,
        ))

    for idx, m in enumerate(fenced, 1):
        verdict = m.group(1)
        block = m.group(2)
        finding = {"index": idx, "verdict": verdict}

        # Assign cluster from position in document
        cluster = cluster_at(m.start())
        if cluster:
            finding["cluster"] = cluster

        for field in ["TITLE", "SECTION", "ELEMENT", "SYNTHESIS_HINT", "SOURCE", "PRIORITY", "OBSERVATION", "RECOMMENDATION", "REFERENCE", "ETHICS_STATE", "SOURCE_URL"]:
            match = re.search(rf"^{field}:\s*(.+)$", block, re.MULTILINE)
            if match:
                finding[field.lower()] = match.group(1).strip()

        why_match = re.search(r"\*\*Why this matters:\*\*\s*(.+?)(?=\n↳|\Z)", block, re.DOTALL)
        if why_match:
            finding["why_matters"] = why_match.group(1).strip()

        cite_match = re.search(r"↳\s*(.+?)(?:\[(\w+)\])?\s*$", block, re.MULTILINE)
        if cite_match:
            finding["citation"] = cite_match.group(1).strip()
            finding["tier"] = cite_match.group(2) if cite_match.group(2) else "Bronze"

        findings.append(finding)

    return findings


def parse_sources(plugin_path):
    """Parse citations/sources.md into a lookup dict.

    Returns dict keyed by "filename:finding_number" -> first URL found.
    Example: "checkout-optimization.md:1" -> "https://baymard.com/..."
    """
    from pathlib import Path
    sources_path = Path(plugin_path) / "citations" / "sources.md"
    if not sources_path.exists():
        return {}

    lookup = {}
    current_file = None
    with open(sources_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Detect section headers like "## checkout-optimization.md" or "## checkout-optimization.md (v2.1 additions)"
            if line.startswith("## ") and ".md" in line:
                # Extract the .md filename, ignoring any suffix like "(v2.1 additions)"
                header_match = re.match(r'## ([\w\-]+\.md)', line)
                if header_match:
                    current_file = header_match.group(1)
                continue
            # Parse table rows: | Finding | Description | Source | URL |
            if current_file and line.startswith("|") and "http" in line:
                cols = [c.strip() for c in line.split("|")]
                # cols[0] is empty (before first |), cols[1]=finding, ..., last non-empty has URL
                if len(cols) >= 5:
                    finding_num_raw = cols[1].strip()
                    url = cols[-2].strip()  # URL is second-to-last (last is empty after trailing |)
                    # Strip "Sources " or "Finding " prefix if present
                    finding_num = re.sub(r'^(?:Sources?|Findings?)\s*', '', finding_num_raw).strip()
                    if finding_num.isdigit() and url.startswith("http"):
                        key = f"{current_file}:{finding_num}"
                        if key not in lookup:  # keep first URL per finding
                            lookup[key] = url

    return lookup


def parse_pass_findings(audit_path):
    """Parse the What's Working Well section for PASS findings."""
    with open(audit_path, "r", encoding="utf-8") as f:
        content = f.read()

    passes = []
    well_match = re.search(r"## What's Working Well\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if well_match:
        section = well_match.group(1)
        for line in section.strip().split("\n"):
            line = line.strip()
            if line.startswith("- "):
                passes.append(line[2:])

    return passes


def parse_priority_path(audit_path):
    """Parse the ## Priority Path section into a list of action stories.

    Each story has the structure documented in audit/SKILL.md
    <priority_path_synthesis>:

      ### {N}. {Title} ({SEVERITY})
      **Fixes {X} findings across {Y} clusters** ({cluster1, cluster2, ...})

      {description paragraph}

      **Do this:** {action sentence}

      **Underlying findings:** {cluster} F-{NN}, {cluster} F-{NN}, ...

    Returns a list of dicts:
      [
        {
          "number": "1",
          "title": "Fix the newsletter popup",
          "severity": "CRITICAL",
          "fixes_count": 4,
          "spans_clusters": ["trust-credibility", "visual-cta", "performance-ux"],
          "description": "...",
          "action": "...",
          "underlying": [
            {"cluster": "trust-credibility", "index": 2, "label": "trust-credibility F-02"},
            ...
          ]
        },
        ...
      ]

    Returns [] if the section is missing or unparseable.
    """
    with open(audit_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Locate the ## Priority Path section
    section_match = re.search(
        r"^## Priority Path\s*\n(.*?)(?=\n## |\Z)",
        content,
        re.DOTALL | re.MULTILINE,
    )
    if not section_match:
        return []

    section = section_match.group(1)

    # Each action story starts with `### N. Title (SEVERITY)` and ends at
    # the next `### ` heading or `## ` heading or end of section.
    story_pattern = re.compile(
        r"^### (\d+)\.\s+(.+?)\s*\(([A-Z]+)\)\s*\n(.*?)(?=\n### \d+\.|\n## |\n> \*\*The remaining|\Z)",
        re.DOTALL | re.MULTILINE,
    )

    stories = []
    for m in story_pattern.finditer(section):
        number = m.group(1)
        title = m.group(2).strip()
        severity = m.group(3).strip()
        body = m.group(4).strip()

        # Parse "Fixes N findings across M clusters (cluster1, cluster2, ...)"
        leverage_match = re.search(
            r"\*\*Fixes (\d+) findings? across (\d+) clusters?\*\*\s*\(([^)]+)\)",
            body,
        )
        fixes_count = int(leverage_match.group(1)) if leverage_match else 0
        spans_clusters = []
        if leverage_match:
            spans_clusters = [c.strip() for c in leverage_match.group(3).split(",") if c.strip()]

        # Parse description: paragraph(s) between the leverage line and "Do this:"
        description = ""
        desc_match = re.search(
            r"\*\*Fixes [^*]+\*\*[^\n]*\n+(.*?)(?=\n\*\*Do this:\*\*|\Z)",
            body,
            re.DOTALL,
        )
        if desc_match:
            description = desc_match.group(1).strip()

        # Parse "Do this:" action line
        action = ""
        action_match = re.search(
            r"\*\*Do this:\*\*\s*(.*?)(?=\n\*\*Underlying findings:\*\*|\Z)",
            body,
            re.DOTALL,
        )
        if action_match:
            action = action_match.group(1).strip()

        # Parse underlying findings list
        underlying = []
        under_match = re.search(
            r"\*\*Underlying findings:\*\*\s*(.*?)(?=\n\n|\Z)",
            body,
            re.DOTALL,
        )
        if under_match:
            refs_str = under_match.group(1).strip()
            # Format: "trust-credibility F-02, visual-cta F-04, ..."
            for ref in re.finditer(r"([\w-]+)\s+F-?(\d+)", refs_str):
                cluster = ref.group(1)
                idx = int(ref.group(2))
                underlying.append({
                    "cluster": cluster,
                    "index": idx,
                    "label": f"{cluster} F-{idx:02d}",
                })

        stories.append({
            "number": number,
            "title": title,
            "severity": severity,
            "fixes_count": fixes_count,
            "spans_clusters": spans_clusters,
            "description": description,
            "action": action,
            "underlying": underlying,
        })

    return stories


def build_cluster_finding_map(findings):
    """Build a map: {cluster: [global_idx_1, global_idx_2, ...]}.

    The list position is the cluster's local F-N index (1-based):
    cluster_map[cluster][N-1] = the global finding index for `cluster F-N`.
    """
    cluster_map = {}
    for f in findings:
        cluster = f.get("cluster", "unknown")
        if cluster not in cluster_map:
            cluster_map[cluster] = []
        cluster_map[cluster].append(f["index"])
    return cluster_map


def cluster_finding_to_global_id(cluster_map, cluster, local_index):
    """Resolve `cluster F-N` to the global finding-{idx} anchor ID for linking."""
    if cluster not in cluster_map:
        return None
    if local_index < 1 or local_index > len(cluster_map[cluster]):
        return None
    global_idx = cluster_map[cluster][local_index - 1]
    return f"finding-{global_idx}"
