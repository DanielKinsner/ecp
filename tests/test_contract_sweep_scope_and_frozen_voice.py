"""Lane B contract-sweep grep guards (product.md v1.2 §2.3/§2.4/§5/§7).

Pins the conformance state established by the v1.2 contract-reword sweep
across four prompt contracts the audit lead reads at runtime:

  - contracts/cluster-routing.md
  - contracts/flags.md
  - contracts/device-semantics.md
  - contracts/meta-schema.md

These guards are deliberately textual — they catch regressions where a
future edit reintroduces stale live-voiced instructions for frozen modes
(product.md §5) or restores the retired pre-v1.2 reduced-scope default
(product.md §2.3 §10 row, ruling A3).

Each test reads the contract file once and asserts both a positive
(required substring) AND a negative (forbidden substring/regex) so that a
file-wide rewrite that drops the load-bearing sentence fails loudly even
if it also drops the forbidden text.

Run:
    python -m pytest tests/test_contract_sweep_scope_and_frozen_voice.py -q
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parent.parent
_CONTRACTS = _REPO / "contracts"


def _read(name: str) -> str:
    path = _CONTRACTS / name
    assert path.is_file(), f"{name} missing — sweep cannot guard a contract that has been deleted."
    return path.read_text(encoding="utf-8")


# --- PART 1: A3 tier collapse (product.md §2.3 v1.2, §10 row) -----------------


def test_cluster_routing_retires_3_to_4_default_tier():
    """The legacy 3-4-cluster default tier is retired (ruling A3).

    Asserts the routing file no longer carries a 'standard defaults' or
    'recommended for most audits' section advertising the 3-4 cluster set
    as a live default. The phrase 'highest-impact 3-4 clusters' was the
    load-bearing description of the retired tier; if it returns we've
    regressed.
    """
    body = _read("cluster-routing.md")

    # Positive: standard is now the canonical default and the page-type-relevant set.
    assert "Standard defaults" in body, (
        "cluster-routing.md must keep a 'Standard defaults' section as the "
        "canonical v1.2 audit scope (all clusters relevant to the detected "
        "page type)."
    )
    assert "all clusters relevant to the detected page type" in body.lower() or (
        "every cluster relevant to the detected page type" in body.lower()
    ), (
        "cluster-routing.md must describe the standard scope as the "
        "page-type-relevant set per product.md §2.3 v1.2."
    )
    assert "retired" in body.lower(), (
        "cluster-routing.md must explicitly mark the legacy 3-4-cluster "
        "default tier as retired (ruling A3 / §10 v1.2)."
    )

    # Negative: no surviving live-voice copy of the retired tier's tagline.
    forbidden = [
        r"highest[- ]impact 3[- ]4 clusters",  # the retired tagline
        r"3[- ]4 highest[- ]impact clusters",
        r"standard set selects the 3[- ]4",
    ]
    for pat in forbidden:
        assert not re.search(pat, body, flags=re.IGNORECASE), (
            f"cluster-routing.md still describes the retired 3-4-cluster "
            f"default tier as live ({pat!r}). Ruling A3 retired it; only a "
            f"frozen / legacy back-compat mention is allowed."
        )


def test_cluster_routing_fixes_dead_skill_anchors():
    """The dead <cluster_selection> / <domain_cluster_routing> SKILL.md
    anchor references must not survive as live cross-skill instructions.

    Those anchors do not exist in skills/audit/SKILL.md; quoting them as
    live cross-references mis-routes any reader trying to follow them.
    """
    body = _read("cluster-routing.md")
    # The current SKILL.md does not define these anchors — see Lane B handoff.
    assert "<cluster_selection>" not in body, (
        "cluster-routing.md references a SKILL.md anchor <cluster_selection> "
        "that does not exist; drop the reference or point to a real anchor."
    )
    assert "<domain_cluster_routing>" not in body, (
        "cluster-routing.md references a SKILL.md anchor <domain_cluster_routing> "
        "that does not exist; drop the reference or point to a real anchor."
    )


def test_flags_auto_default_names_all_relevant_standard():
    """--auto's scope default in flags.md must name the v1.2 standard set
    (every cluster relevant to the detected page type), not the retired tier.
    """
    body = _read("flags.md")

    # The --auto section must describe scope as the page-type-relevant set.
    auto_anchor = body.find("## `--auto`")
    deep_anchor = body.find("## `--deep`")
    assert auto_anchor != -1 and deep_anchor != -1 and deep_anchor > auto_anchor, (
        "flags.md must keep the --auto and --deep sections in order."
    )
    auto_block = body[auto_anchor:deep_anchor]
    assert "standard" in auto_block.lower(), (
        "flags.md --auto block must name the standard scope as the default."
    )
    assert (
        "relevant to the detected page type" in auto_block.lower()
        or "every cluster relevant" in auto_block.lower()
    ), (
        "flags.md --auto block must describe standard as the "
        "page-type-relevant set per product.md §2.3 v1.2."
    )
    assert "2.3" in auto_block, (
        "flags.md --auto block must cite product.md §2.3 as the v1.2 spec "
        "authority for the standard scope default."
    )

    # --auto must NOT still describe scope as '3-4 clusters' as a live default.
    assert not re.search(r'standard["\)]?\s*\(3[- ]4 clusters', auto_block, flags=re.IGNORECASE), (
        "flags.md --auto block still describes standard as '3-4 clusters' — "
        "that was the retired pre-v1.2 default (ruling A3)."
    )

    # The precedence table must NOT route --auto --deep to a separate
    # 'comprehensive' default — that was the pre-v1.2 split.
    precedence_anchor = body.find("Scope and flag precedence")
    assert precedence_anchor != -1, "flags.md must keep the scope-precedence section."
    precedence_block = body[precedence_anchor:]
    assert not re.search(
        r"--auto --deep[^\n]*Defaults scope to `?comprehensive`?",
        precedence_block,
    ), (
        "flags.md precedence table still splits --auto --deep into a separate "
        "comprehensive default; the v1.2 collapse means --deep no longer "
        "changes scope."
    )


# --- PART 2: frozen-voice sweep (product.md §5 / §7, ruling A4) ---------------


def _block_for_flag(body: str, flag: str) -> str:
    """Return the body of the `## `--flag`` section up to the next `## `."""
    anchor = f"## `{flag}`"
    start = body.find(anchor)
    assert start != -1, f"flags.md missing the {flag!r} section."
    rest = body[start + len(anchor):]
    next_anchor = rest.find("\n## ")
    end = (start + len(anchor) + next_anchor) if next_anchor != -1 else len(body)
    return body[start:end]


def test_flags_ab_scaffold_is_frozen_voice():
    """--ab-scaffold (and --ab-tool) must be frozen-voiced.

    The canonical v1.2 audit stops at the §2.4 deliverables and never
    produces A/B test scaffolding (§3 #1: 'does not run A/B tests').
    The earlier live-voiced 'generate an A/B test scaffold file ... after
    the plan phase completes' addressed the live lead as if scaffolding
    were a canonical-audit deliverable — that's the §5 / §7 violation
    ruling A4 forbids.
    """
    body = _read("flags.md")
    block = _block_for_flag(body, "--ab-scaffold")

    assert "frozen" in block.lower(), (
        "--ab-scaffold section must declare frozen status (ruling A4); "
        "audit stops at §2.4 and never produces A/B scaffolding."
    )
    # Must not instruct the live lead to generate scaffolding.
    forbidden_live = [
        r"After the plan phase completes, generate an A/B test scaffold",
        r"generate an A/B test scaffold file for the top recommendations",
    ]
    for pat in forbidden_live:
        assert not re.search(pat, block), (
            f"--ab-scaffold section still carries live-voice generation "
            f"instructions ({pat!r}); reword to frozen per ruling A4."
        )

    # And the paired --ab-tool flag.
    tool_block = _block_for_flag(body, "--ab-tool")
    assert "frozen" in tool_block.lower(), (
        "--ab-tool section must also be frozen-voiced (paired with --ab-scaffold)."
    )


def test_device_semantics_non_url_modes_are_frozen():
    """File / pasted-code / description / screenshot source modes must be
    presented as frozen per product.md §2.2 (URL is the only canonical input)
    and §5; live-voiced 'description mode is quick-scan and build only'
    addresses a live lead as if those modes were invokable.
    """
    body = _read("device-semantics.md")
    assert "frozen" in body.lower(), (
        "device-semantics.md must mark the non-URL source modes as frozen "
        "(product.md §5)."
    )
    # The pre-sweep live-voiced section heading must be gone.
    forbidden_live = [
        r"^## File mode and description mode: device selection is skipped",
        # The pre-sweep live phrase that addressed quick-scan / build as live modes.
        r"description mode[^\n]*quick[- ]scan and build only",
    ]
    for pat in forbidden_live:
        assert not re.search(pat, body, flags=re.IGNORECASE | re.MULTILINE), (
            f"device-semantics.md still carries live-voice non-URL "
            f"source-mode copy ({pat!r}); reword to frozen per ruling A4."
        )
    # URL-as-only-canonical-input must be reasserted somewhere in the file.
    assert "URL is the only canonical input" in body or "url is the only canonical input" in body.lower(), (
        "device-semantics.md must reassert product.md §2.2 (URL-only) when "
        "documenting the frozen non-URL source modes."
    )


def test_meta_schema_marks_frozen_engagement_types_and_source_modes():
    """meta.json `type` enum values build/quick-scan/compare and
    `source_mode` values file/pasted-code/screenshot/description stay in
    the schema (ruling A4 — frozen INTERFACE ROWS stay) but their
    descriptions must mark them frozen / legacy-read-only.
    """
    body = _read("meta-schema.md")

    # The `type` row must explicitly call out the frozen status of build /
    # quick-scan / compare.
    type_row_match = re.search(
        r"\|\s*`type`\s*\|[^\n]*\|[^\n]*", body
    )
    assert type_row_match, "meta-schema.md must keep the required `type` row."
    type_row = type_row_match.group(0)
    assert (
        "frozen" in type_row.lower() or "legacy" in type_row.lower()
    ), (
        "meta-schema.md `type` row must mark `build`, `quick-scan`, `compare` "
        "as frozen / legacy interface contracts (ruling A4 — they stay in the "
        "enum but never get written by a new v1.2 engagement)."
    )
    assert "audit" in type_row, "the `type` row must still allow `audit`."

    # The source_mode section must mark file / pasted-code / screenshot /
    # description as frozen.
    sm_anchor = body.find("### Valid `source_mode` values")
    assert sm_anchor != -1, "meta-schema.md must keep the source_mode enum section."
    sm_section = body[sm_anchor:sm_anchor + 4000]
    for frozen_value in ("file", "pasted-code", "screenshot", "description"):
        # Each value's row should mention frozen or legacy.
        # Look for the value in a row context.
        row_pattern = re.compile(
            r"\|\s*`" + re.escape(frozen_value) + r"`\s*\|[^|]*\|[^\n]*",
            re.IGNORECASE,
        )
        match = row_pattern.search(sm_section)
        assert match, (
            f"meta-schema.md source_mode enum missing `{frozen_value}` row — "
            f"the frozen INTERFACE row must stay (ruling A4)."
        )
        row = match.group(0)
        assert (
            "frozen" in row.lower() or "legacy" in row.lower()
        ), (
            f"meta-schema.md source_mode `{frozen_value}` row must mark the "
            f"value frozen / legacy — a new v1.2 audit never writes it."
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
