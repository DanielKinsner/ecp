"""Draft -> Client-Ready report-state gate (product.md §6).

A generated report is always a DRAFT. Promotion to CLIENT-VERIFIED is a
deliberate manual attestation by the operator, who must:

  1. Re-check the live site.
  2. Follow every legal/ethics citation link and confirm relevancy.
  3. Finalize hotspot placement (§4.2).

The state lives in ``meta.json`` as ``report_state: "draft" | "client-verified"``.
Missing/blank is treated as ``draft`` (back-compat with engagements created
before this field existed).

The load-bearing invariant: **automated / ``--auto`` execution can NEVER mark a
report client-ready.** Rendering a report does not promote it either — promotion
is a separate, explicit operator action (see ``generate-report.py
--mark-client-verified``). ``set_client_verified`` refuses when ``auto=True`` so
the invariant is enforced in code, not just documented.

Phase-0 ruling A9 (2026-06-10) — the gate grows teeth. The §6 manual steps that
were previously docstring text are now mechanically enforced: before promoting,
``set_client_verified`` reads the engagement's ``review-state-{device}.json``
file(s) and counts findings whose hotspot is still queued for manual placement
(``hotspot_confidence == "needs-manual-marker"`` — Strategy-4 "unplaced",
off-slide e_index fallthroughs, hero-stack distributed markers). If any device
has unplaced markers, promotion refuses with ``UnplacedMarkerError`` unless the
operator passes ``force=True``. An engagement with no review-state files at all
likewise refuses (placement was never finalized) — ``force=True`` bypasses.

On successful promotion the writer stamps an attestation block on meta.json
(``report_state_attestation``: promoted_at, per-device unplaced counts at
promotion, forced bool) so the audit trail records *what* the operator attested
to and whether they used the escape hatch.

The review-state JSON is small and well-known; rather than importing
``assembly.review_state`` (which transitively pulls v2 renderer code), we read
the files directly here — the only field consulted is
``findings[].hotspot_confidence``.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .atomic_write import atomic_write_json

REPORT_STATE_DRAFT = "draft"
REPORT_STATE_CLIENT_VERIFIED = "client-verified"
VALID_REPORT_STATES = (REPORT_STATE_DRAFT, REPORT_STATE_CLIENT_VERIFIED)

# Devices the v2 review-state builder writes per
# ``assembly.review_state.REVIEW_STATE_FILENAMES``. Duplicated here (rather than
# imported) to keep ``report_state`` free of the v2 renderer's transitive import
# graph — the only review-state field this module reads is the well-known
# ``findings[].hotspot_confidence`` enum.
_REVIEW_STATE_FILENAMES = {
    "desktop": "review-state-desktop.json",
    "mobile": "review-state-mobile.json",
    "laptop": "review-state-laptop.json",
}

# The hotspot_confidence label written by the review-state builder for any
# finding that the operator must place by hand (Strategy-4 "unplaced",
# off-slide e_index, hero-stack distributed). Single source of truth lives in
# ``schema/review-state-v1.json`` (hotspot_confidence enum) and in
# ``assembly.review_state._hotspot_confidence``.
_NEEDS_MANUAL_MARKER = "needs-manual-marker"

# Statuses that represent an explicit operator decision on the finding —
# "hidden" is the editor's decline path, "approved" an explicit keep.
# product.md §4.2: the operator "places or declines" markers manually; either
# decision satisfies the §6 placement gate even with no marker placed (a
# deliberate blank is neutral; only an UNREVIEWED blank blocks promotion).
_OPERATOR_RESOLVED_STATUSES = ("hidden", "approved")


class AutoPromotionError(PermissionError):
    """Raised when automated/--auto execution tries to mark a report client-ready."""


class UnplacedMarkerError(PermissionError):
    """Raised when promotion is refused because hotspots still need manual placement.

    Mirrors ``AutoPromotionError``: a ``PermissionError`` subclass so a generic
    permission-denied handler still catches both, but distinct so a caller can
    distinguish "you tried under --auto" from "your placement queue isn't empty
    yet". Carries the per-device unplaced counts on ``.unplaced_counts`` so the
    CLI doesn't have to re-derive them from the message.
    """

    def __init__(self, message: str, *, unplaced_counts: dict[str, int]):
        super().__init__(message)
        self.unplaced_counts = unplaced_counts


def read_report_state(meta: dict[str, Any]) -> str:
    """Return the report_state, defaulting to ``draft`` (product.md §6).

    Missing, null, blank, or any unrecognized value reads as ``draft`` — a
    report is never client-ready unless something explicitly and validly set
    it so.
    """
    value = meta.get("report_state")
    return value if value in VALID_REPORT_STATES else REPORT_STATE_DRAFT


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _count_unplaced_per_device(engagement_dir: Path) -> dict[str, int]:
    """Return per-device unplaced-marker counts from review-state-{device}.json.

    Returns a dict keyed by device name with one entry per review-state file
    present on disk. Empty dict means no review-state file exists for any
    device — placement was never finalized for this engagement. Missing or
    malformed individual files are skipped (no entry in the dict for that
    device) so a single broken file can't block promotion of a real engagement.
    Each entry counts findings whose ``hotspot_confidence`` equals
    ``"needs-manual-marker"`` and whose status is not an explicit operator
    resolution (hidden = declined, approved = deliberate keep).
    """
    counts: dict[str, int] = {}
    for device, filename in _REVIEW_STATE_FILENAMES.items():
        path = engagement_dir / filename
        if not path.exists():
            continue
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        findings = state.get("findings")
        if not isinstance(findings, list):
            continue
        count = 0
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            if finding.get("status") in _OPERATOR_RESOLVED_STATUSES:
                continue
            if finding.get("hotspot_confidence") == _NEEDS_MANUAL_MARKER:
                count += 1
        counts[device] = count
    return counts


def set_client_verified(
    meta_path: str | Path,
    *,
    auto: bool = False,
    force: bool = False,
    now: str | None = None,
) -> dict[str, Any]:
    """Promote a report to ``client-verified`` — the §6 manual verification pass.

    Args:
        meta_path: path to the engagement's ``meta.json``.
        auto: True when running under ``--auto`` / any automated chain. When
            True this raises ``AutoPromotionError`` — automated execution can
            never mark a report client-ready (product.md §6). ``force`` does
            NOT bypass this guard; the auto-refusal is absolute.
        force: Operator escape hatch for the §4.2 placement gate. When False
            (default), promotion refuses with ``UnplacedMarkerError`` if any
            ``review-state-{device}.json`` reports hotspots still queued for
            manual placement, or if no review-state file exists at all
            (placement was never finalized). When True, the operator is
            attesting that they have placement intentionally
            unfinished/handled out-of-band — the attestation block records
            ``forced=True`` so the audit trail captures the escape.
        now: ISO 8601 timestamp for the ``updated`` field; defaults to now.

    Returns the updated meta dict. Writes back atomically (atomic_write_json,
    the mandated meta.json writer).
    """
    if auto:
        raise AutoPromotionError(
            "Refusing to mark report client-verified under --auto: client-ready "
            "promotion requires a manual verification pass (product.md §6). "
            "Automated execution can never mark a report client-ready."
        )

    meta_path = Path(meta_path)
    engagement_dir = meta_path.parent
    unplaced_counts = _count_unplaced_per_device(engagement_dir)

    if not force:
        if not unplaced_counts:
            raise UnplacedMarkerError(
                "Refusing to mark report client-verified: no review-state-{device}.json "
                "files found in the engagement directory — hotspot placement was never "
                "finalized (product.md §6 step 3). Run the v2 render to produce review "
                "state, finalize placement, then retry. Pass --force to override.",
                unplaced_counts={},
            )
        total = sum(unplaced_counts.values())
        if total > 0:
            per_device = ", ".join(
                f"{device}={count}" for device, count in sorted(unplaced_counts.items())
            )
            raise UnplacedMarkerError(
                "Refusing to mark report client-verified: "
                f"{total} hotspot(s) still queued for manual placement "
                f"({per_device}). Finalize placement in the editor "
                "(product.md §4.2/§6 step 3), then retry. Pass --force to override.",
                unplaced_counts=dict(unplaced_counts),
            )

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    promoted_at = now or _utc_now()
    meta["report_state"] = REPORT_STATE_CLIENT_VERIFIED
    meta["updated"] = promoted_at
    meta["report_state_attestation"] = {
        "promoted_at": promoted_at,
        "unplaced_counts": dict(unplaced_counts),
        "forced": bool(force),
    }
    atomic_write_json(meta_path, meta)
    return meta


__all__ = [
    "AutoPromotionError",
    "REPORT_STATE_CLIENT_VERIFIED",
    "REPORT_STATE_DRAFT",
    "UnplacedMarkerError",
    "VALID_REPORT_STATES",
    "read_report_state",
    "set_client_verified",
]
