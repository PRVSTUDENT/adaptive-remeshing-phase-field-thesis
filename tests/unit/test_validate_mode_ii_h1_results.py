#!/usr/bin/env python3
"""Unit tests for Stage F Mode-II H1 result validator."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validation.validate_mode_ii_h1_results import validate_results


class TestModeIIH1Validator(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.evidence_dir = Path(self.temp_dir.name)
        extracted = self.evidence_dir / "extracted"
        extracted.mkdir(parents=True, exist_ok=True)

        # Minimal valid rf1_u1_curve.csv
        curve_csv = extracted / "rf1_u1_curve.csv"
        curve_csv.write_text(
            "rp_u1,rp_rf1,max_sdv15\n"
            "0.001,0.0128,0.05\n"
            "0.012,0.1398,0.50\n"
            "0.020,0.0812,0.99\n",
            encoding="utf-8",
        )

        # Minimal energy CSV
        energy_csv = extracted / "energy_history.csv"
        energy_csv.write_text(
            "step,u1,energy\n"
            "1,0.001,1e-5\n"
            "2,0.020,5e-4\n",
            encoding="utf-8",
        )

        # Minimal crack path CSV
        crack_csv = extracted / "crack_path_sdv15_ge_0p5.csv"
        crack_csv.write_text(
            "elem_id,x,y,sdv15\n"
            "101,0.0,0.0,0.85\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_phase_summary(self, max_phase: float, min_phase: float = 0.0):
        phase_json = self.evidence_dir / "extracted" / "phase_bounds_summary.json"
        phase_json.write_text(
            json.dumps({"maximum_phase": max_phase, "minimum_phase": min_phase}),
            encoding="utf-8",
        )

    def test_damage_normal_pass_d_1p0(self):
        self._write_phase_summary(1.0, 0.0)
        res = validate_results(self.evidence_dir, abaqus_return_code=0, extractor_return_code=0)
        self.assertTrue(res["technical_pass"])
        self.assertEqual(res["validator_return_code"], 0)
        self.assertEqual(res["warnings"], [])
        self.assertEqual(res["classification"], "stage_f_mode_ii_h1_postpeak")
        self.assertAlmostEqual(res["max_sdv15"], 1.0)

    def test_damage_small_overshoot_d_1p0005(self):
        self._write_phase_summary(1.0005, 0.0)
        res = validate_results(self.evidence_dir, abaqus_return_code=0, extractor_return_code=0)
        self.assertTrue(res["technical_pass"])
        self.assertEqual(res["validator_return_code"], 0)
        self.assertIn("damage_upper_bound_small_overshoot", res["warnings"])
        self.assertEqual(res["classification"], "stage_f_mode_ii_h1_postpeak")
        self.assertAlmostEqual(res["max_sdv15"], 1.0005)

    def test_damage_small_overshoot_d_1p00498(self):
        self._write_phase_summary(1.00498, 0.0)
        res = validate_results(self.evidence_dir, abaqus_return_code=0, extractor_return_code=0)
        self.assertTrue(res["technical_pass"])
        self.assertEqual(res["validator_return_code"], 0)
        self.assertIn("damage_upper_bound_small_overshoot", res["warnings"])
        self.assertEqual(res["classification"], "stage_f_mode_ii_h1_postpeak")
        self.assertAlmostEqual(res["max_sdv15"], 1.00498)

    def test_damage_small_overshoot_d_1p01(self):
        self._write_phase_summary(1.01, 0.0)
        res = validate_results(self.evidence_dir, abaqus_return_code=0, extractor_return_code=0)
        self.assertTrue(res["technical_pass"])
        self.assertEqual(res["validator_return_code"], 0)
        self.assertIn("damage_upper_bound_small_overshoot", res["warnings"])
        self.assertEqual(res["classification"], "stage_f_mode_ii_h1_postpeak")
        self.assertAlmostEqual(res["max_sdv15"], 1.01)

    def test_damage_excessive_overshoot_d_gt_1p01(self):
        self._write_phase_summary(1.02, 0.0)
        res = validate_results(self.evidence_dir, abaqus_return_code=0, extractor_return_code=0)
        self.assertFalse(res["technical_pass"])
        self.assertEqual(res["validator_return_code"], 1)
        self.assertTrue(any("exceeds upper bound tolerance" in f for f in res["failures"]))
        self.assertEqual(res["classification"], "stage_f_mode_ii_h1_technical_fail")

    def test_negative_damage_beyond_tolerance(self):
        self._write_phase_summary(0.95, -0.05)
        res = validate_results(self.evidence_dir, abaqus_return_code=0, extractor_return_code=0)
        self.assertFalse(res["technical_pass"])
        self.assertEqual(res["validator_return_code"], 1)
        self.assertTrue(any("below lower bound tolerance" in f for f in res["failures"]))

    def test_non_finite_damage_nan(self):
        self._write_phase_summary(float("nan"), 0.0)
        res = validate_results(self.evidence_dir, abaqus_return_code=0, extractor_return_code=0)
        self.assertFalse(res["technical_pass"])
        self.assertEqual(res["validator_return_code"], 1)
        self.assertTrue(any("non-finite" in f for f in res["failures"]))


if __name__ == "__main__":
    unittest.main()
