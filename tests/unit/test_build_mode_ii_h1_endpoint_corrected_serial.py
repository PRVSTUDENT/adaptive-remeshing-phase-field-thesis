#!/usr/bin/env python3
"""Unit tests for Mode-II H1 endpoint-corrected serial technical package builder."""

import tempfile
import unittest
from pathlib import Path

from scripts.model_generation.build_mode_ii_h1_endpoint_corrected_serial import (
    EXPECTED_LAYERED,
    EXPECTED_NODES,
    EXPECTED_N_ELEM,
    EXPECTED_PHYSICAL,
    build_package,
)

ROOT = Path(__file__).resolve().parents[2]


class TestBuildModeIIH1(unittest.TestCase):
    def test_build_package_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "h1_pkg"
            manifest = build_package(out_dir)

            self.assertEqual(manifest["classification"], "stage_f_mode_ii_h1_endpoint_corrected_package_prepared")
            self.assertTrue(manifest["source_byte_identical"])
            self.assertEqual(manifest["physical_element_count"], EXPECTED_PHYSICAL)
            self.assertEqual(manifest["layered_element_count"], EXPECTED_LAYERED)
            self.assertEqual(manifest["node_count"], EXPECTED_NODES)
            self.assertEqual(manifest["n_elem_fortran"], EXPECTED_N_ELEM)

            deck_path = out_dir / "ModeII_H1_endpoint_corrected_serial.inp"
            for_path = out_dir / "ModeII_H1_endpoint_corrected_serial.for"
            manifest_path = out_dir / "PACKAGE_MANIFEST.json"

            self.assertTrue(deck_path.is_file())
            self.assertTrue(for_path.is_file())
            self.assertTrue(manifest_path.is_file())

            deck_text = deck_path.read_text(encoding="utf-8")
            self.assertIn("*Amplitude, name=Amp-2\n0., 0.005, 0.2, 0.01", deck_text)
            self.assertIn("RP, 1, 1, 1.", deck_text)
            self.assertIn("bottom, 1, 2", deck_text)


if __name__ == "__main__":
    unittest.main()
