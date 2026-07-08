"""De-stack co-placed findings (§4.2 precision-over-recall).

When two or more findings auto-place on the SAME baton element their marker
rects land pixel-for-pixel on top of each other: the operator sees one blob
and diagnose_engagement.py flags STACKED / DUPLICATE. §4.2 optimizes for
precision over recall — a wrong/redundant hotspot costs more than a blank —
so the placement policy keeps the single highest-severity box on the element
and blanks the rest into the manual-placement queue.

``coplaced_blanks`` is the pure decision: given the (f_ref, slide, element,
severity) of every finding that DID auto-place, return the set of f_refs to
blank. It is deterministic — severity ties resolve to the first finding in
input order.
"""
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from report.placement import coplaced_blanks  # noqa: E402


class CoplacedBlanksTest(unittest.TestCase):
    def test_lower_severity_blanks_when_sharing_an_element(self):
        losers = coplaced_blanks([
            ("hero/F-01", "slide-1", 15, "HIGH"),
            ("hero/F-02", "slide-1", 15, "MEDIUM"),
        ])
        self.assertEqual(losers, {"hero/F-02"})

    def test_single_finding_on_an_element_is_never_blanked(self):
        self.assertEqual(
            coplaced_blanks([("hero/F-01", "slide-1", 15, "HIGH")]),
            set(),
        )

    def test_distinct_elements_do_not_collide(self):
        self.assertEqual(
            coplaced_blanks([
                ("a/F-01", "slide-1", 15, "HIGH"),
                ("b/F-02", "slide-1", 16, "LOW"),
            ]),
            set(),
        )

    def test_same_element_index_on_different_slides_does_not_collide(self):
        self.assertEqual(
            coplaced_blanks([
                ("a/F-01", "slide-1", 15, "HIGH"),
                ("b/F-02", "slide-2", 15, "LOW"),
            ]),
            set(),
        )

    def test_severity_tie_keeps_the_first_in_input_order(self):
        losers = coplaced_blanks([
            ("hero/F-01", "slide-1", 15, "HIGH"),
            ("hero/F-02", "slide-1", 15, "HIGH"),
        ])
        self.assertEqual(losers, {"hero/F-02"})

    def test_three_on_one_element_keeps_only_the_top_severity(self):
        losers = coplaced_blanks([
            ("hero/F-01", "slide-1", 15, "HIGH"),
            ("hero/F-02", "slide-1", 15, "CRITICAL"),
            ("hero/F-03", "slide-1", 15, "LOW"),
        ])
        self.assertEqual(losers, {"hero/F-01", "hero/F-03"})

    def test_a_none_element_index_never_collides(self):
        self.assertEqual(
            coplaced_blanks([
                ("a/F-01", "slide-1", None, "HIGH"),
                ("b/F-02", "slide-1", None, "LOW"),
            ]),
            set(),
        )


if __name__ == "__main__":
    unittest.main()
