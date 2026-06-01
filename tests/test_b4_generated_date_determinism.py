"""GUARD B4: the report's "generated {date}" surface must be deterministic.

scripts/report/html_builder._load_metadata() builds the metadata dict that the
HTML footer renders, including ``generated_date``. A prior regression derived
that value from the wall clock (``datetime.now()``), which made byte-identical
engagement inputs produce different report output on different days.

This guard pins the fixed behaviour by exercising the REAL _load_metadata:

  1. generated_date is inputs-bound: it is derived from the engagement meta's
     acquisition timestamp (``created`` / ``created_at`` / ``updated_at``),
     mirroring how the visible ``date_str`` is sourced.
  2. Determinism: two calls on identical inputs yield identical generated_date.
  3. No-timestamp fallback: when meta carries no timestamp, generated_date is
     the literal "Unknown" and is NOT today's datetime.now() date.

The test imports the authoritative function rather than re-implementing it, and
also inspects its source to assert it never reaches for datetime.now()/today().
"""

import datetime
import inspect
import re
import sys
from pathlib import Path

# The repo puts scripts/ on sys.path; report.* resolves from there.
sys.path.insert(0, str(Path("scripts").resolve()))

from report.html_builder import _load_metadata  # noqa: E402


# _load_metadata(engagement_path, baton, meta, device, plugin_path)
DEVICE = "desktop"
BATON = {"viewport": {"width": 1440, "height": 900}}


def _call(meta, tmp_path):
    """Invoke the real _load_metadata with minimal, hermetic inputs.

    engagement_path/plugin_path point at a tmp dir with no font-embed.css, so
    the font branch is skipped cleanly and nothing touches the real repo tree.
    """
    engagement_path = tmp_path / "some-engagement"
    plugin_path = tmp_path  # no templates/font-embed.css here -> font_css == ""
    return _load_metadata(engagement_path, BATON, meta, DEVICE, plugin_path)


def test_generated_date_is_inputs_bound_to_created(tmp_path):
    """generated_date is derived from the meta timestamp, not the wall clock."""
    meta = {"created": "2026-04-14T08:30:00Z", "engagement_id": "slingmods-pdp"}
    result = _call(meta, tmp_path)

    # Bound to the date portion of the supplied timestamp.
    assert result["generated_date"] == "2026-04-14"
    # And consistent with the visible date_str, which is sourced the same way.
    assert result["date_str"] == "2026-04-14"


def test_generated_date_accepts_created_at_and_updated_at_fallbacks(tmp_path):
    """Live meta.json writers emit created_at/updated_at; both are honoured."""
    by_created_at = _call({"created_at": "2026-05-02T12:00:00Z"}, tmp_path)
    assert by_created_at["generated_date"] == "2026-05-02"

    by_updated_at = _call({"updated_at": "2026-05-03T23:59:59Z"}, tmp_path)
    assert by_updated_at["generated_date"] == "2026-05-03"


def test_generated_date_is_deterministic_across_calls(tmp_path):
    """Two calls on identical inputs yield an identical generated_date."""
    meta = {"created": "2026-04-14T08:30:00Z"}
    first = _call(meta, tmp_path)
    second = _call(meta, tmp_path)
    assert first["generated_date"] == second["generated_date"]
    # Whole metadata dict is stable too, not just this one field.
    assert first == second


def test_generated_date_unknown_when_no_timestamp_not_wall_clock(tmp_path):
    """No timestamp -> literal 'Unknown', never today's datetime.now() date."""
    meta = {"engagement_id": "no-timestamp-engagement"}
    result = _call(meta, tmp_path)

    assert result["generated_date"] == "Unknown"

    today = datetime.datetime.now().date().isoformat()
    assert result["generated_date"] != today
    # Defensive: it must not be ANY parseable YYYY-MM-DD date string.
    assert not re.fullmatch(r"\d{4}-\d{2}-\d{2}", result["generated_date"])


def _executable_source(func):
    """Return func's source with comments and string literals stripped.

    The fixed _load_metadata legitimately *mentions* datetime.now() in a comment
    explaining why it does NOT use it. We tokenize and drop COMMENT/STRING tokens
    so the scan only sees executable code, not prose, keeping the guard coupled
    to behaviour rather than to wording.
    """
    import io
    import tokenize

    src = inspect.getsource(func)
    kept = []
    readline = io.StringIO(src).readline
    for tok in tokenize.generate_tokens(readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        kept.append(tok.string)
    return " ".join(kept)


def test_load_metadata_code_does_not_touch_wall_clock():
    """Couple to the source: _load_metadata's CODE must not read the clock."""
    code = _executable_source(_load_metadata)
    assert "datetime.now" not in code
    assert "datetime.today" not in code
    assert ".now(" not in code
    assert ".today(" not in code
