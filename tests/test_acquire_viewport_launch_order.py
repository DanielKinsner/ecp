"""Regression guard: acquire_url.py must set the viewport with the launch
ordering that agent-browser 0.32.x actually honors, for BOTH devices.

Root cause (2026-07-21, agent-browser 0.21 -> 0.32.3 upgrade). The 0.32.x
persistent daemon changed emulation semantics, and `_run_one_device`'s
launch/goto block hit three separate bugs that all produced a silently WRONG
capture (both desktop and mobile captured at the browser window's default
1258x566 @1x instead of 1920x1080 / 390x844@3x):

  1. `set viewport` / `set device` issued before any browser was launched: the
     first `set` launches the browser at the OS window's default size and the
     override is lost. Fix: a bare `open` (about:blank) launches the context
     FIRST, then `set viewport` sticks.
  2. `goto` exits non-zero under emulation even when navigation succeeds. The
     script hard-failed (check=True) on that exit code. Fix: `goto` with
     check=False + an authoritative post-nav `location.href` check (a genuine
     failure leaves href empty / about:blank).
  3. `set device "iPhone 14"` either raced the following `goto` (captured
     1258x566) or wedged the daemon >10 min when preceded by a bare `open`.
     Fix: `set device` is gone; mobile uses the retina viewport form
     `set viewport 390 844 3` (3rd arg = deviceScaleFactor).

These tests drive `_run_one_device` with subprocess helpers stubbed, forcing an
early return right after the launch+goto sequence (the stubbed
`_eval_json_object` returns an empty landed-URL, which the new about:blank guard
treats as a genuine nav failure). They then assert the recorded agent-browser
command ordering. Belt-and-suspenders source checks pin the invariants against a
rename/refactor.

Run:
    python -m pytest tests/test_acquire_viewport_launch_order.py -v
"""
import types
from pathlib import Path
import sys

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

import acquire_url  # noqa: E402


def _drive(monkeypatch, device):
    """Run _run_one_device far enough to record the launch/goto command
    sequence, then bail via the about:blank guard. Returns (calls, rc)."""
    calls = []

    def _fake_run(cmd, **kwargs):
        calls.append(("_run", list(cmd)))
        return 0

    def _fake_run_ab(agent_browser, sub, **kwargs):
        calls.append(("_run_ab", list(sub), dict(kwargs)))
        return 0

    monkeypatch.setattr(acquire_url, "_run", _fake_run)
    monkeypatch.setattr(acquire_url, "_run_ab", _fake_run_ab)
    # Empty landed-URL -> the new authoritative post-nav guard returns (1, None)
    # right after launch+goto, before any screenshot/DOM work.
    monkeypatch.setattr(acquire_url, "_eval_json_object", lambda *a, **k: {})
    monkeypatch.setattr(acquire_url.time, "sleep", lambda *a, **k: None)

    ecp_dom = types.SimpleNamespace(preprocess_acquisition_dom=lambda *a, **k: "")
    rc, info = acquire_url._run_one_device(
        device=device,
        file_prefix="",
        url="https://example.com/product",
        engagement_id="test-engagement",
        eng_dir=Path("."),
        agent_browser="agent-browser",
        ecp_dom=ecp_dom,
        ecp_ov=None,
        sec_hints=None,
        ecp_cfg=None,
        max_screenshots=1,
        settle_seconds=0.0,
        post_scroll_wait=0.0,
        goto_timeout=5.0,
    )
    return calls, rc


def _contains_subseq(argv, subseq):
    """True if `subseq` appears as a contiguous run inside argv."""
    n = len(subseq)
    return any(argv[i : i + n] == subseq for i in range(len(argv) - n + 1))


def _index_of_run_ab_open(calls):
    for i, c in enumerate(calls):
        if c[0] == "_run_ab" and c[1] == ["open"]:
            return i
    return -1


def _index_of_set_viewport(calls):
    for i, c in enumerate(calls):
        if c[0] == "_run" and _contains_subseq(c[1], ["set", "viewport"]):
            return i
    return -1


def _no_set_device(calls):
    return not any(
        c[0] == "_run" and _contains_subseq(c[1], ["set", "device"]) for c in calls
    )


def test_desktop_bare_open_before_set_viewport(monkeypatch):
    calls, _ = _drive(monkeypatch, "desktop")
    open_i = _index_of_run_ab_open(calls)
    vp_i = _index_of_set_viewport(calls)
    assert open_i >= 0, "desktop path must issue a bare `open` to launch the browser"
    assert vp_i >= 0, "desktop path must issue `set viewport`"
    assert open_i < vp_i, (
        "bare `open` must come BEFORE `set viewport` (0.32.x loses the viewport "
        "override when `set` launches the browser)"
    )


def test_desktop_sets_1920x1080_and_never_set_device(monkeypatch):
    calls, _ = _drive(monkeypatch, "desktop")
    assert any(
        c[0] == "_run" and _contains_subseq(c[1], ["set", "viewport", "1920", "1080"])
        for c in calls
    ), "desktop must set viewport 1920x1080"
    assert _no_set_device(calls), "desktop must not use `set device`"


def test_mobile_uses_retina_viewport_not_set_device(monkeypatch):
    calls, _ = _drive(monkeypatch, "mobile")
    assert any(
        c[0] == "_run"
        and _contains_subseq(c[1], ["set", "viewport", "390", "844", "3"])
        for c in calls
    ), (
        "mobile must set viewport 390x844 with deviceScaleFactor 3 (retina viewport "
        "form), NOT `set device \"iPhone 14\"`"
    )
    assert _no_set_device(calls), (
        "mobile must not use `set device` (it races goto -> 1258x566, or wedges the "
        "daemon when preceded by a bare open)"
    )
    open_i = _index_of_run_ab_open(calls)
    vp_i = _index_of_set_viewport(calls)
    assert 0 <= open_i < vp_i, "mobile also launches with a bare `open` before set viewport"


def test_goto_is_tolerant_of_nonzero_exit(monkeypatch):
    """goto must be dispatched with check=False so a benign non-zero exit under
    emulation does not abort a capture that actually navigated."""
    calls, rc = _drive(monkeypatch, "desktop")
    goto_calls = [c for c in calls if c[0] == "_run_ab" and c[1][:1] == ["goto"]]
    assert goto_calls, "a goto must be dispatched"
    assert goto_calls[0][2].get("check") is False, (
        "goto must be dispatched with check=False (agent-browser 0.32.x exits "
        "non-zero under emulation even on a successful navigation)"
    )
    # With an empty landed-URL, the authoritative post-nav guard treats it as a
    # genuine failure and returns rc=1 (not a crash, not a silent success).
    assert rc == 1, "empty landed-URL must be caught by the post-nav about:blank guard"


def test_source_pins_the_fix_invariants():
    """Belt-and-suspenders: a rename/refactor that drops any invariant still
    trips this guard."""
    src = (_REPO / "scripts" / "acquire_url.py").read_text(encoding="utf-8")
    # goto is tolerant of the emulation-quirk exit code.
    assert '["goto", url], session=session, check=False' in src, (
        "goto must be dispatched with check=False"
    )
    # The authoritative post-nav guard is present.
    assert "about:blank" in src, "post-nav about:blank failure guard must be present"
    # `set device` is no longer used to launch/emulate the mobile viewport.
    assert '"set", "device"' not in src and "'set', 'device'" not in src, (
        "the `set device` launch path must be gone (replaced by retina set viewport)"
    )
    # The retina scale arg is appended for high-DPR devices.
    assert "vp_args.append(str(_scale))" in src, (
        "high-DPR devices must append the deviceScaleFactor to `set viewport`"
    )


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-v"]))
