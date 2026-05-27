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


class AutoPromotionError(PermissionError):
    """Raised when automated/--auto execution tries to mark a report client-ready."""


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


def set_client_verified(
    meta_path: str | Path,
    *,
    auto: bool = False,
    now: str | None = None,
) -> dict[str, Any]:
    """Promote a report to ``client-verified`` — the §6 manual verification pass.

    Args:
        meta_path: path to the engagement's ``meta.json``.
        auto: True when running under ``--auto`` / any automated chain. When
            True this raises ``AutoPromotionError`` — automated execution can
            never mark a report client-ready (product.md §6).
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
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["report_state"] = REPORT_STATE_CLIENT_VERIFIED
    meta["updated"] = now or _utc_now()
    atomic_write_json(meta_path, meta)
    return meta


__all__ = [
    "AutoPromotionError",
    "REPORT_STATE_CLIENT_VERIFIED",
    "REPORT_STATE_DRAFT",
    "VALID_REPORT_STATES",
    "read_report_state",
    "set_client_verified",
]
