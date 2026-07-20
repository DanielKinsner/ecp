"""Regression guard: acquire_url.py must not leak its stdout pipe to the
agent-browser daemon.

Root cause (2026-07-20, agent-browser 0.21 -> 0.32 upgrade): agent-browser 0.26+
runs a *persistent daemon*. The first `open`/`goto` spawns it, and it inherits
the stdout/stderr of the spawning subprocess. If that subprocess inherited the
Python process's real stdout (a pipe), the daemon holds the pipe's write-end
open after acquire_url.py exits, so any caller reading our stdout — the acquirer
subagent, or a shell `... | tail` — hangs long after the capture already
finished. Symptom: capture artifacts are all on disk, but the command never
returns (observed as a 3-minute wedge -> SIGTERM).

Fix: the two fire-and-forget agent-browser invocation helpers (`_run`,
`_run_ab`) pass ``stdout=DEVNULL, stderr=DEVNULL`` so the daemon inherits
DEVNULL, never the caller's pipe. Output the script actually parses goes through
`_run_capture` (unaffected). This test fails if that redirect is ever removed.

Run:
    python -m pytest tests/test_acquire_daemon_pipe.py -v
"""
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

import acquire_url  # noqa: E402


class _FakeCompleted:
    returncode = 0
    stdout = ""
    stderr = ""


def _record_run(monkeypatch):
    """Patch subprocess.run inside acquire_url to record call kwargs."""
    calls = []

    def _fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, "kwargs": kwargs})
        return _FakeCompleted()

    monkeypatch.setattr(acquire_url.subprocess, "run", _fake_run)
    return calls


def test_run_redirects_child_streams_to_devnull(monkeypatch):
    """`_run` must send child stdout+stderr to DEVNULL so a spawned daemon
    cannot inherit and hold this process's stdout pipe."""
    calls = _record_run(monkeypatch)
    acquire_url._run(["agent-browser", "close"], check=False)
    assert calls, "_run must invoke subprocess.run"
    kw = calls[0]["kwargs"]
    assert kw.get("stdout") is subprocess.DEVNULL, "_run must set stdout=DEVNULL"
    assert kw.get("stderr") is subprocess.DEVNULL, "_run must set stderr=DEVNULL"


def test_run_ab_redirects_child_streams_to_devnull(monkeypatch):
    """`_run_ab` (the goto/open/screenshot/eval dispatcher) must redirect child
    stdout+stderr to DEVNULL — this is the call that spawns the daemon."""
    calls = _record_run(monkeypatch)
    acquire_url._run_ab(
        "agent-browser",
        ["goto", "https://example.com"],
        session="ecp-test",
        check=False,
        timeout=5,
    )
    assert calls, "_run_ab must invoke subprocess.run"
    kw = calls[0]["kwargs"]
    assert kw.get("stdout") is subprocess.DEVNULL, "_run_ab must set stdout=DEVNULL"
    assert kw.get("stderr") is subprocess.DEVNULL, "_run_ab must set stderr=DEVNULL"


def test_devnull_redirect_literals_present_in_source():
    """Belt-and-suspenders: the DEVNULL redirect is present in both helpers'
    source, so a refactor that renames the helpers still trips this guard."""
    src = (_REPO / "scripts" / "acquire_url.py").read_text(encoding="utf-8")
    assert src.count("stdout=subprocess.DEVNULL") >= 2, (
        "both _run and _run_ab must redirect stdout to DEVNULL (daemon-pipe guard)"
    )
    assert src.count("stderr=subprocess.DEVNULL") >= 2, (
        "both _run and _run_ab must redirect stderr to DEVNULL (daemon-pipe guard)"
    )


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-v"]))
