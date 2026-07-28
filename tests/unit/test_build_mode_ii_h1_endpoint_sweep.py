#!/usr/bin/env python3
"""Unit tests for Stage-F Mode-II H1 endpoint sweep builder, static validator, and PBS extractor interface."""

import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.model_generation.build_mode_ii_h1_endpoint_sweep import build_all_packages, VARIANTS
from scripts.validation.validate_mode_ii_h1_sweep_static import validate_all_sweep_packages
from scripts.validation.validate_mode_ii_h1_results import validate_results


class TestModeIIH1EndpointSweep(unittest.TestCase):

    def test_package_generation_and_static_validation(self):
        sweep_dir = ROOT / "models/generated/mode_ii/h1_endpoint_sweep"
        manifests = build_all_packages(sweep_dir)

        self.assertEqual(set(manifests.keys()), set(VARIANTS.keys()))

        for vkey, m in manifests.items():
            self.assertEqual(m["physical_element_count"], 12064)
            self.assertEqual(m["layered_element_count"], 36192)
            self.assertEqual(m["node_count"], 12382)
            self.assertEqual(m["n_elem_fortran"], 12064)
            self.assertTrue((sweep_dir / vkey / f"{m['job_name']}.inp").is_file())
            self.assertTrue((sweep_dir / vkey / f"{m['job_name']}.for").is_file())

        summary = validate_all_sweep_packages(sweep_dir)
        self.assertTrue(summary["all_passed"], f"Static validation failed: {summary}")

    def test_pbs_script_extractor_cli(self):
        pbs_path = ROOT / "scripts/hpc/stage_f/mode_ii_h1_endpoint_sweep/mode_ii_h1_endpoint_sweep.pbs"
        self.assertTrue(pbs_path.is_file())

        text = pbs_path.read_text(encoding="utf-8")

        # Must use supported flags
        self.assertIn("--odb", text)
        self.assertIn("--sta", text)
        self.assertIn("--dat", text)
        self.assertIn("--msg", text)
        self.assertIn("--output-dir", text)
        self.assertIn("--displacement-component 1", text)
        self.assertIn("--reaction-component 1", text)

        # Must NOT use unsupported --config or positional ODB
        self.assertNotIn("--config", text)

    def test_result_validator_classifications(self):
        # Test result validator logic for physical state classifications
        # Pre-peak case
        res_prepeak = validate_results(
            evidence_dir=ROOT / "runs/hpc/stage_f/mode_ii_h1/evidence/1379433.mmaster02",
            abaqus_return_code=0,
            extractor_return_code=0,
            expected_u1_target=0.010,
        )
        self.assertTrue(res_prepeak["technical_pass"])
        self.assertEqual(res_prepeak["classification"], "stage_f_mode_ii_h1_prepeak")


if __name__ == "__main__":
    unittest.main()
