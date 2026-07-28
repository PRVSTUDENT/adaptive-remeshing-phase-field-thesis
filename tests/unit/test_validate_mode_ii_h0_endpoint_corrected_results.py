#!/usr/bin/env python3
"""Unit tests for Mode-II H0 endpoint-corrected result validator."""

import csv
import json
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

    def _create_synthetic_result(
        self,
        u1: float = 0.010,
        crack_rows: int = 10,
        max_sdv15: float = 0.8,
        history_violations: int = 0,
    ) -> None:
        rf1_csv = self.ext_dir / "rf1_u1_curve.csv"
        with rf1_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["step", "frame", "rp_u1", "rp_rf1", "max_sdv15"])
            writer.writerow([1, 1, 0.005, 0.2, 0.1])
            writer.writerow([2, 20, u1, 0.3, max_sdv15])

        energy_csv = self.ext_dir / "energy_history.csv"
        with energy_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["step", "step_time", "variable", "value"])
            writer.writerow(["Step-1", 0.0, "ALLAE", 0.0])
            writer.writerow(["Step-2", 0.2, "ALLAE", 0.01])

        phase_json = self.ext_dir / "phase_bounds_summary.json"
        phase_json.write_text(
            json.dumps({"maximum_phase": max_sdv15, "minimum_phase": 0.0, "values_checked": 100}),
            encoding="utf-8",
        )

        irrev_json = self.ext_dir / "irreversibility_summary.json"
        irrev_json.write_text(
            json.dumps({"history_decrease_violation_count": history_violations}),
            encoding="utf-8",
        )

        crack_csv = self.ext_dir / "crack_path_sdv15_ge_0p5.csv"
        with crack_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["element", "phase_variable", "phase_value", "threshold", "step", "frame"])
            if crack_rows > 0:
                for i in range(crack_rows):
                    sdv15 = max_sdv15 if i == 0 else 0.5
                    writer.writerow([1000 + i, "SDV15", sdv15, 0.5, "Step-2", 20])

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
        self.assertTrue(any("crack-path" in f or "maximum damage" in f for f in res["failures"]))


if __name__ == "__main__":
    unittest.main()
