"""acquire_url section-screenshot naming contract (#26 / migration fix).

acquire_url.py historically emitted ``{device}-section-N.jpg`` in multi-device
runs (e.g. ``desktop-section-1.jpg``), which the validator regex
(``assembly.business_rules._SCREENSHOT_PATTERN``) and the v1->v2 converter
reject. The canonical contract is ``section-N.jpg`` (desktop/laptop) and
``section-N-mobile.jpg`` (mobile) — mobile-vs-not is the ONLY naming axis, and
it must not vary with single- vs multi-device runs.

These tests assert acquire's helper against the REAL validator pattern (imported,
not hardcoded) so they stay coupled to the authoritative contract.
"""
import importlib.util
import re
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.business_rules import _SCREENSHOT_PATTERN  # noqa: E402


def _load_acquire_url():
    spec = importlib.util.spec_from_file_location(
        "acquire_url", _REPO / "scripts" / "acquire_url.py"
    )
    mod = importlib.util.module_from_spec(spec)
    # Register before exec so @dataclass can resolve cls.__module__ via
    # sys.modules (otherwise dataclasses._is_type hits None.__dict__).
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


acquire_url = _load_acquire_url()
_PATTERN = re.compile(_SCREENSHOT_PATTERN)


@pytest.mark.parametrize("device", ["desktop", "laptop"])
def test_non_mobile_has_no_suffix_or_prefix(device):
    assert acquire_url.section_screenshot_name(1, device) == "section-1.jpg"


def test_mobile_gets_mobile_suffix():
    assert acquire_url.section_screenshot_name(3, "mobile") == "section-3-mobile.jpg"


@pytest.mark.parametrize("device", ["desktop", "laptop", "mobile"])
@pytest.mark.parametrize("index", [1, 5, 12])
def test_matches_authoritative_validator_regex(device, index):
    name = acquire_url.section_screenshot_name(index, device)
    assert _PATTERN.match(name), f"{name!r} fails {_SCREENSHOT_PATTERN}"


def test_name_is_independent_of_single_vs_multi_device():
    # The number of devices in a run must not change the section filename;
    # only mobile-vs-non-mobile does. (Regression guard for the {device}- prefix.)
    assert acquire_url.section_screenshot_name(2, "desktop") == "section-2.jpg"
    assert acquire_url.section_screenshot_name(2, "mobile") == "section-2-mobile.jpg"
    assert "desktop-" not in acquire_url.section_screenshot_name(2, "desktop")
