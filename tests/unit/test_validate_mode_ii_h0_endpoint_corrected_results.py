#!/usr/bin/env python3
"""Unit tests for Mode-II H0 endpoint-corrected result validator."""

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.validation.validate_mode_ii_h0_endpoint_corrected_results import (
    FAIL_CLASSIFICATION,
    PASS_CLASSIFICATION,
    validate_results,
)


class TestValidateModeIIH0EndpointCorrectedResults(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.ev_dir = Path(self.tmp_dir.name)
        self.ext_dir = self.ev_dir / "extracted"
        self.ext_dir.mkdir()

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def _create_synthetic_result(self, u1: float = 0.010, crack_rows: int = 10, max_sdv15: float = 0.8) -> None:
        energy_csv = self.ext_dir / "energy_history.csv"
        with energy_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["step", "frame", "rp_u1", "rp_rf1", "ALLSE"])
            writer.writerow([1, 1, 0.005, 0.2, 0.01])
            writer.writerow([2, 20, u1, 0.3, 0.05])

        crack_csv = self.ext_dir / "sdv14_sdv15_sdv16_contours.csv"
        with crack_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["x", "y", "sdv14", "sdv15", "sdv16"])
            if crack_rows > 0:
                for i in range(crack_rows):
                    sdv15 = max_sdv15 if i == 0 else 0.1
                    writer.writerow([0.5 + i * 0.01, 0.5, 0.0, sdv15, 0.0])

    def test_result_validator_accepts_valid_synthetic_result(self) -> None:
        self._create_synthetic_result(u1=0.010, crack_rows=10, max_sdv15=0.8)
        res = validate_results(self.ev_dir, abaqus_return_code=0, extractor_return_code=0)
        self.assertTrue(res["passed"])
        self.assertEqual(res["classification"], PASS_CLASSIFICATION)

    def test_result_validator_rejects_u1_0p007(self) -> None:
        self._create_synthetic_result(u1=0.007, crack_rows=10, max_sdv15=0.8)
        res = validate_results(self.ev_dir, abaqus_return_code=0, extractor_return_code=0)
        self.assertFalse(res["passed"])
        self.assertEqual(res["classification"], FAIL_CLASSIFICATION)
        self.assertTrue(any("0.007" in f for f in res["failures"]))

    def test_result_validator_rejects_empty_crack_path(self) -> None:
        self._create_synthetic_result(u1=0.010, crack_rows=0, max_sdv15=0.0)
        res = validate_results(self.ev_dir, abaqus_return_code=0, extractor_return_code=0)
        self.assertFalse(res["passed"])
        self.assertEqual(res["classification"], FAIL_CLASSIFICATION)
        self.assertTrue(any("crack-path" in f for f in res["failures"]))


if __name__ == "__main__":
    unittest.main()
