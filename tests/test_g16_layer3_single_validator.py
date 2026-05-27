"""G16 Layer 3 regression: single shared validator instance.

Pre-Layer-3, ``scripts/test-specialist.py`` and
``scripts/assembly/json_parser.py`` each built their own
Draft202012Validator from the same schema files. The code was
byte-equivalent — but two copies meant a future edit to one and not
the other could re-introduce the silent-drift class G16 Layer 1+2
made loud. Layer 3 consolidates: both paths now use the same
``assembly.json_parser.get_validator()`` instance.

This regression locks the invariant: if anyone re-introduces a duplicate
validator (or otherwise breaks the shared-instance contract), this
test catches it.

unittest-style for ``python -m unittest discover`` runner compatibility.

Run:
    python -m unittest tests.test_g16_layer3_single_validator
"""
from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))


class TestSingleValidatorInstance(unittest.TestCase):
    def test_test_specialist_load_schemas_returns_shared_validator(self):
        """``test-specialist.py:_load_schemas()`` must return the SAME
        validator instance as ``assembly.json_parser.get_validator()``,
        not a fresh copy built from the same schema files. ``is`` check
        catches the case where someone re-introduces a `_build_validator()`
        in test-specialist that happens to produce an equivalent
        Draft202012Validator — equivalent isn't enough; same instance
        is the contract."""
        # test-specialist.py has a dash in its name so it can't be
        # imported as a normal module. Import via importlib.util.
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "test_specialist_cli", _REPO / "scripts" / "test-specialist.py",
        )
        assert spec is not None and spec.loader is not None
        test_specialist = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_specialist)

        from assembly.json_parser import get_validator

        validator_from_test_specialist, _finding_schema = test_specialist._load_schemas()
        validator_from_json_parser = get_validator()

        self.assertIs(
            validator_from_test_specialist,
            validator_from_json_parser,
            "G16 Layer 3 invariant violated: test-specialist.py's "
            "_load_schemas must return the same validator instance as "
            "assembly.json_parser.get_validator. Both code paths must "
            "share one validator so a future schema-handling edit can't "
            "drift one validator's behavior away from the other.",
        )

    def test_validate_emission_payload_uses_shared_validator(self):
        """``assembly.json_parser.validate_emission_payload`` uses
        ``_VALIDATOR`` directly. Confirm ``get_validator()`` returns the
        same instance so external callers see the same validator
        ``validate_emission_payload`` does internally."""
        from assembly.json_parser import _VALIDATOR, get_validator
        self.assertIs(get_validator(), _VALIDATOR)


if __name__ == "__main__":
    unittest.main()
