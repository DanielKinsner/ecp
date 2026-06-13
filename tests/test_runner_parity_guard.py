"""Runner-parity guard: catch mass-collection regressions that hide
pytest-only tests from ``python -m unittest discover -s tests``.

Background
----------
``python -m unittest discover -s tests`` only picks up
``unittest.TestCase`` subclasses; it silently skips bare ``def test_*``
functions (~91 of the §4.1/§4.2 trust guards live in that shape today —
visual evidence, synthesizer fref contract, determinism canaries,
ethics preservation, final-report render, review-state contract...).

Nothing else in the suite enforces both runners (CLAUDE.md prose only;
no CI). This guard is the cheap insurance:

  * It is itself a ``unittest.TestCase`` — so ``unittest discover``
    *does* see it.
  * It shells out ``python -m pytest tests/ --collect-only -q`` and
    asserts the collected count stays above ``EXPECTED_MIN_COLLECTED``.
  * If the pytest collector ever stops seeing the bare-function tests
    (wrong runner, bad ``conftest``, missing ``__init__.py`` shadowing,
    a refactor that broke discovery) the count nose-dives and this
    guard turns the silent regression into a loud one.

Why ``--collect-only``
----------------------
Collection is ~2-3 s; we never want this guard to recurse into running
the full suite (which would deadlock pytest inside itself).

Floor update rule
-----------------
``EXPECTED_MIN_COLLECTED`` is set ~30 below the actual collected count
at the time of writing (1352 collected -> floor 1322). If the suite
*legitimately* shrinks below the floor (real test removal, not a
collection bug), bump the floor down to ``new_count - 30`` in the SAME
commit that removes the tests. Never raise the floor casually — a high
floor turns small refactors into red builds. The inverse also rots:
when a wave ADDS tests, re-floor to ``new_count - 30`` in that wave,
or the guard's slack silently grows past what it was designed to catch
(found at 195 tests of slack on 2026-06-10).
"""
from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

# Set ~30 below the actual collected count (1386 on 2026-06-12, after the
# post-roadmap backlog guards grew the suite from 1366).
# See "Floor update rule" in the module docstring before changing.
EXPECTED_MIN_COLLECTED = 1356

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = REPO_ROOT / "tests"

# Pytest prints e.g. "1187 tests collected in 16.43s" or "1 test collected".
_COLLECTED_RE = re.compile(r"(\d+)\s+tests?\s+collected", re.IGNORECASE)


def _pytest_available() -> bool:
    """True when ``pytest`` is importable in the current interpreter."""
    return importlib.util.find_spec("pytest") is not None


class TestRunnerParityGuard(unittest.TestCase):
    """Guard against silent pytest-collection regressions.

    Lives as a ``unittest.TestCase`` so ``unittest discover`` sees it
    even though the thing it protects is pytest-only collection.
    """

    @unittest.skipUnless(
        _pytest_available(),
        "pytest not installed; runner-parity guard cannot collect "
        "(install pytest>=9,<10 per CLAUDE.md to enable this trust guard)",
    )
    def test_pytest_collects_at_least_floor_tests(self) -> None:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        # Collection-only — never recurse into running the suite.
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", str(TESTS_DIR), "--collect-only", "-q"],
            cwd=str(REPO_ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
        self.assertEqual(
            proc.returncode,
            0,
            msg=(
                "pytest --collect-only failed (rc="
                f"{proc.returncode}). This usually means a syntax / import "
                "error in a test module is breaking collection — fix that "
                "first.\n--- stdout ---\n"
                f"{proc.stdout}\n--- stderr ---\n{proc.stderr}"
            ),
        )
        match = _COLLECTED_RE.search(combined)
        self.assertIsNotNone(
            match,
            msg=(
                "Could not find a 'N tests collected' line in pytest "
                "--collect-only output. Did the pytest output format "
                "change?\n--- output ---\n" + combined[-2000:]
            ),
        )
        collected = int(match.group(1))
        self.assertGreaterEqual(
            collected,
            EXPECTED_MIN_COLLECTED,
            msg=(
                f"pytest collected only {collected} tests, below floor "
                f"{EXPECTED_MIN_COLLECTED}. Likely cause: a recent change "
                "broke pytest discovery (wrong runner used, conftest "
                "error, accidental __init__.py shadowing, mass rename). "
                "If the drop is legitimate (real test removal), lower "
                "EXPECTED_MIN_COLLECTED to (new_count - 30) in the SAME "
                "commit that removed the tests."
            ),
        )


if __name__ == "__main__":
    unittest.main()
