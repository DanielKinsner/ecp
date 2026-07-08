"""Guard: a co-placed "loser" finding must carry an UNPLACED hotspot_confidence.

Regression for adversarial review 2026-07-08 #16. When two findings auto-place
on the same baton element, coplaced_blanks keeps the highest-severity box and
blanks the rest (§4.2 precision-over-recall). review_state correctly built a
blank/hidden MARKER for the loser, but derived the finding's hotspot_confidence
from the stale match_method ('e_index_lookup' -> 'exact-selector'). So the §6/A9
client-verified promotion gate — which refuses promotion while any hotspot is
still queued — counted the loser's blank hotspot as PLACED, letting a report
promote to client-ready with an unplaced hotspot the operator never positioned.

The committed fixture 2026-05-02-9cd2a2ac/desktop produces exactly one such
loser (category-navigation F-96), which pins the fix deterministically.

Run:
    python -m pytest tests/test_review_state_coplaced_confidence.py
    python -m unittest tests.test_review_state_coplaced_confidence
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.review_state import build_initial_review_state  # noqa: E402

_FIXTURE = _REPO / "tests" / "fixtures" / "2026-05-02-9cd2a2ac"


@unittest.skipUnless(_FIXTURE.exists(), f"committed fixture missing: {_FIXTURE}")
class CoplacedLoserConfidence(unittest.TestCase):
    def test_known_coplaced_loser_labeled_needs_manual(self):
        state = build_initial_review_state(_FIXTURE, "desktop", plugin_root=_REPO)
        by_ref = {f["f_ref"]: f for f in state["findings"]}
        loser = by_ref.get("category-navigation F-96")
        self.assertIsNotNone(loser, "expected the coplaced-loser fixture finding to be present")
        self.assertEqual(
            loser["hotspot_confidence"], "needs-manual-marker",
            "A co-placed loser renders blank; its hotspot_confidence must read "
            "unplaced so the client-verified gate counts it as needing manual "
            "placement (review 2026-07-08 #16).",
        )
        markers = [m for m in state["markers"] if m.get("f_ref") == "category-navigation F-96"]
        self.assertTrue(
            markers and all(m.get("hidden") for m in markers),
            "the coplaced loser's markers must be hidden/blank",
        )

    def test_no_hidden_marker_claims_exact_confidence(self):
        # General invariant the bug violated: a finding whose marker is blank
        # (hidden) must never advertise a confident 'exact-selector' placement.
        for dev in ("desktop", "mobile"):
            state = build_initial_review_state(_FIXTURE, dev, plugin_root=_REPO)
            markers_by_ref: dict = {}
            for m in state["markers"]:
                markers_by_ref.setdefault(m.get("f_ref"), []).append(m)
            for f in state["findings"]:
                ms = markers_by_ref.get(f["f_ref"], [])
                if ms and all(m.get("hidden") for m in ms):
                    self.assertNotEqual(
                        f["hotspot_confidence"], "exact-selector",
                        f"{f['f_ref']} ({dev}) has an all-blank marker but claims "
                        f"exact-selector confidence — the §6 gate would treat it as placed.",
                    )


if __name__ == "__main__":
    unittest.main()
