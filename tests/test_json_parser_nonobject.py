"""Negative test: json_parser candidate-id resolution must not crash on a
non-object payload (adversarial-review finding 12).

parse_emission_file resolved candidate_ids on the raw payload BEFORE schema
validation. A non-object JSON (list/scalar) with a sidecar present crashed the
resolver with AttributeError instead of surfacing a clean EmissionValidationError.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO / "scripts"))

from assembly.json_parser import parse_emission_file, EmissionValidationError  # noqa: E402


class TestNonObjectPayloadWithSidecar(unittest.TestCase):
    def _emission(self, text: str) -> Path:
        tmp = tempfile.mkdtemp(prefix="ecp-jp-")
        p = Path(tmp) / "cluster-visual-cta-desktop.json"
        p.write_text(text, encoding="utf-8")
        return p

    def test_json_array_payload_raises_validation_error(self):
        p = self._emission("[]")
        with self.assertRaises(EmissionValidationError):
            parse_emission_file(p, anchor_candidates_sidecar={"candidate_to_e_index": {"c1": "e1"}})

    def test_json_scalar_payload_raises_validation_error(self):
        p = self._emission("42")
        with self.assertRaises(EmissionValidationError):
            parse_emission_file(p, anchor_candidates_sidecar={"candidate_to_e_index": {"c1": "e1"}})


if __name__ == "__main__":
    unittest.main()
