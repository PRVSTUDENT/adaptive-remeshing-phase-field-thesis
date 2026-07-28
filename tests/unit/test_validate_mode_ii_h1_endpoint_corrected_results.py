#!/usr/bin/env python3
"""Unit tests for Stage-F Mode-II H1 endpoint-corrected result validator."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validation.validate_mode_ii_h1_endpoint_corrected_results import validate_results


class TestValidateModeIIH1Results(unittest.TestCase):
    def test_validate_mocked_h1_evidence_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            ev_dir = Path(tmp_dir)
            ext_dir = ev_dir / "extracted"
            ext_dir.mkdir(parents=True)

            rf1_u1 = ext_dir / "rf1_u1_curve.csv"
            rf1_u1.write_text("step,frame,time,rp_u1,rp_rf1,max_sdv15\n1,100,0.2,0.010,0.450,0.992\n", encoding="utf-8")

            energy = ext_dir / "energy_history.csv"
            energy.write_text("step,frame,time,ALLSE,ALLPD\n1,100,0.2,0.001,0.002\n", encoding="utf-8")

            phase_json = ext_dir / "phase_bounds_summary.json"
            phase_json.write_text(json.dumps({"maximum_phase": 0.992, "minimum_phase": 0.0}), encoding="utf-8")

            crack_csv = ext_dir / "crack_path_sdv15_ge_0p5.csv"
            crack_csv.write_text("x,y,sdv15\n0.5,0.0,0.992\n0.6,0.1,0.85\n", encoding="utf-8")

            res = validate_results(ev_dir, abaqus_return_code=0, extractor_return_code=0)
            self.assertTrue(res["passed"])
            self.assertEqual(res["classification"], "stage_f_mode_ii_h1_endpoint_corrected_serial_baseline_pass")
            self.assertAlmostEqual(res["final_u1_mm"], 0.010, places=4)


if __name__ == "__main__":
    unittest.main()
