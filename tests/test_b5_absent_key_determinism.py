"""GUARD B5: absent-finding grouping key is content-derived and deterministic.

The cross-cluster structural dedup layer cannot collapse findings whose
``baton_index == 'absent'`` (two absent findings usually describe different
missing things -- no JSON-LD vs no OG image -- so collapsing on baton_index
would erase distinct content). Each absent finding must therefore survive as
its own group.

The pre-fix code keyed those groups on ``id(f)``, which is process-dependent:
two equivalent builds of the same engagement produced *different* group keys,
breaking the byte-identical-determinism invariant Phase E guarantees. The fix
(scripts/assembly/dedup._absent_content_key) derives the key purely from
finding content -- ``(cluster, device, local_index, surface, title, verdict,
observation)`` -- so the key is:

  1. byte-identical across two in-process builds of the same input, even when
     the underlying objects have different ``id()``;
  2. unique per distinct finding (distinct content -> distinct key);
  3. preserved as its own group inside the structural layer -- absent findings
     are never merged away, regardless of count.

This test imports the real ``Finding`` model and the real authoritative
functions (``_absent_content_key`` and ``_v2_layer_cross_cluster_structural``)
rather than hardcoding the key format, so it stays coupled to the source of
truth. Hermetic: no fixtures, no I/O, no network.

Run:
    python -m pytest tests/test_b5_absent_key_determinism.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# The repo puts scripts/ on sys.path; modules import as 'from assembly.X import ...'.
_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.dedup import (  # noqa: E402
    _absent_content_key,
    _v2_layer_cross_cluster_structural,
)
from assembly.models import Finding  # noqa: E402


# ---------------------------------------------------------------------------
# Builders -- each call constructs a FRESH Finding so id() differs between the
# two "builds" even when every content field is identical.
# ---------------------------------------------------------------------------


def _absent_finding(**overrides) -> Finding:
    """Construct an 'absent' baton_index Finding with sane defaults.

    Every call allocates a new object -> different id(). The fixed key must
    ignore identity entirely and depend only on content.
    """
    base = dict(
        cluster="seo",
        device="desktop",
        local_index=1,
        verdict="FAIL",
        section="head",
        element="meta[og:image]",
        element_normalized="meta[og:image]",
        source="CODE",
        priority="HIGH",
        priority_rank=1,
        observation="No Open Graph image present in the document head.",
        recommendation="Add an og:image meta tag.",
        reference="r1",
        title="Missing og:image",
        tier="Silver",
        baton_index="absent",
        surface="head-metadata",
        scope="device",
    )
    base.update(overrides)
    return Finding(**base)


def _distinct_absent_set() -> list[Finding]:
    """A set of DISTINCT absent findings (different missing things)."""
    return [
        _absent_finding(
            cluster="seo",
            device="desktop",
            local_index=1,
            title="Missing og:image",
            surface="head-metadata",
            observation="No Open Graph image present in the document head.",
        ),
        _absent_finding(
            cluster="seo",
            device="desktop",
            local_index=2,
            title="Missing JSON-LD",
            surface="structured-data",
            observation="No JSON-LD structured data block present.",
        ),
        _absent_finding(
            cluster="trust",
            device="mobile",
            local_index=1,
            title="No security badges",
            surface="checkout-trust",
            observation="No trust or security badges near the purchase CTA.",
        ),
        # Same cluster/device/surface/title as the first, but a different
        # local_index AND observation -> still a distinct finding.
        _absent_finding(
            cluster="seo",
            device="desktop",
            local_index=3,
            title="Missing og:image",
            surface="head-metadata",
            observation="og:image absent on the mobile-shared head template.",
        ),
    ]


# ---------------------------------------------------------------------------
# Property 1: byte-identical key across two in-process builds (different id())
# ---------------------------------------------------------------------------


def test_absent_key_byte_identical_across_builds():
    """Two equivalent builds yield byte-identical keys despite differing id()."""
    build_a = _distinct_absent_set()
    build_b = _distinct_absent_set()

    # Sanity: these really are different objects (identity differs).
    for fa, fb in zip(build_a, build_b):
        assert fa is not fb
        assert id(fa) != id(fb)

    keys_a = [_absent_content_key(f) for f in build_a]
    keys_b = [_absent_content_key(f) for f in build_b]

    assert keys_a == keys_b, (
        "Absent-finding keys must be byte-identical across in-process builds "
        "of the same content; got divergent keys (id()-dependent grouping?)."
    )

    # Each key is an exact str -> compare as bytes to make 'byte-identical'
    # literal rather than merely value-equal.
    for ka, kb in zip(keys_a, keys_b):
        assert ka.encode("utf-8") == kb.encode("utf-8")


def test_absent_key_stable_under_repeated_calls():
    """The key is a pure function of content -- repeated calls never drift."""
    f = _absent_finding()
    first = _absent_content_key(f)
    for _ in range(5):
        assert _absent_content_key(f) == first


# ---------------------------------------------------------------------------
# Property 2: unique per distinct finding
# ---------------------------------------------------------------------------


def test_absent_keys_unique_per_distinct_finding():
    """Distinct findings produce distinct keys (no collisions)."""
    findings = _distinct_absent_set()
    keys = [_absent_content_key(f) for f in findings]
    assert len(set(keys)) == len(keys), (
        "Distinct absent findings collided on the content key: "
        f"{len(keys)} findings -> {len(set(keys))} unique keys."
    )


def test_absent_key_discriminates_each_content_field():
    """Changing any identity-bearing field changes the key."""
    base = _absent_finding()
    base_key = _absent_content_key(base)

    from dataclasses import replace

    variants = {
        "cluster": replace(base, cluster="trust"),
        "device": replace(base, device="mobile"),
        "local_index": replace(base, local_index=99),
        "surface": replace(base, surface="other-surface"),
        "title": replace(base, title="Different title"),
        "verdict": replace(base, verdict="PARTIAL"),
        "observation": replace(base, observation="A wholly different observation."),
    }
    for field_name, variant in variants.items():
        assert _absent_content_key(variant) != base_key, (
            f"Changing '{field_name}' must change the absent content key."
        )


# ---------------------------------------------------------------------------
# Property 3: every absent finding preserved as its own group by the real layer
# ---------------------------------------------------------------------------


def test_structural_layer_preserves_every_absent_finding():
    """_v2_layer_cross_cluster_structural keeps every absent finding, merges none."""
    findings = _distinct_absent_set()
    kept, merged = _v2_layer_cross_cluster_structural(findings)

    # No absent finding may be merged away.
    assert merged == [], "Absent findings must never be merged in the structural layer."
    assert len(kept) == len(findings), (
        f"Expected all {len(findings)} absent findings preserved, got {len(kept)}."
    )

    # The kept set is exactly the input set (by content key).
    in_keys = sorted(_absent_content_key(f) for f in findings)
    out_keys = sorted(_absent_content_key(f) for f in kept)
    assert in_keys == out_keys


def test_structural_layer_output_byte_identical_across_builds():
    """Two builds through the real layer yield byte-identical kept-key ordering."""
    kept_a, _ = _v2_layer_cross_cluster_structural(_distinct_absent_set())
    kept_b, _ = _v2_layer_cross_cluster_structural(_distinct_absent_set())

    keys_a = [_absent_content_key(f) for f in kept_a]
    keys_b = [_absent_content_key(f) for f in kept_b]

    # The layer sorts groups by key, so order must be identical too -- this is
    # the determinism guarantee that the old id()-based key violated.
    assert keys_a == keys_b
    assert [k.encode("utf-8") for k in keys_a] == [k.encode("utf-8") for k in keys_b]


def test_identical_content_distinct_objects_share_key():
    """Two distinct objects with identical content map to the SAME group key.

    This is the crux of the fix: id() differs, key does not. (The set builder
    deliberately gives every finding a unique local_index, so to exercise the
    identity-vs-content distinction we duplicate one finding's content here.)
    """
    f1 = _absent_finding()
    f2 = _absent_finding()  # fresh object, identical content
    assert f1 is not f2
    assert _absent_content_key(f1) == _absent_content_key(f2)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
