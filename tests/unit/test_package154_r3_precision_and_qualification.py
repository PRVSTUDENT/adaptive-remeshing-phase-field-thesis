#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package154_r3_precision_and_qualification.py
Unit tests verifying the double-precision ODB mechanism, Package 154 (C1-2 Revision 3)
technical qualification, datacheck evidence, and UEL integrity.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2
"""
import unittest
import json
import os
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

class TestPackage154R3Qualification(unittest.TestCase):

    def test_01_frozen_uel_integrity(self):
        """Confirm bitwise match of frozen UEL subroutine."""
        uel_path = REPO_ROOT / "models/pandey_kumar_mode1/154_c4_package150_c1_2_continuation_r3/f42_mixed_uel.for"
        self.assertTrue(uel_path.is_file())
        h = hashlib.sha256(uel_path.read_bytes()).hexdigest().upper()
        self.assertEqual(h, FROZEN_UEL_HASH)

    def test_02_package_manifest_integrity(self):
        """Verify Package 154 manifest parameters."""
        man_path = REPO_ROOT / "models/pandey_kumar_mode1/154_c4_package150_c1_2_continuation_r3/PACKAGE_MANIFEST.json"
        self.assertTrue(man_path.is_file())
        with open(man_path) as f:
            data = json.load(f)
        self.assertEqual(data["package_id"], "PACKAGE_154_C1_2_CONTINUATION_R3")
        self.assertEqual(data["max_outer"], 100)
        self.assertEqual(data["discretization"]["elements"], 7056)
        self.assertEqual(data["discretization"]["physical_nodes"], 7265)
        self.assertEqual(len(data["loading_schedule"]["steps"]), 4)

    def test_03_execution_manifest_command(self):
        """Verify Execution manifest command and target job ID."""
        exec_path = REPO_ROOT / "models/pandey_kumar_mode1/154_c4_package150_c1_2_continuation_r3/EXECUTION_MANIFEST.json"
        self.assertTrue(exec_path.is_file())
        with open(exec_path) as f:
            data = json.load(f)
        self.assertEqual(data["batch_name"], "MODE1_PACKAGE154_STAGE_C1_2_CONTINUATION_R3")
        self.assertEqual(data["technical_stage"], "C1-2")
        self.assertEqual(data["jobs"][0]["id"], "M1_C4_P150_C1_2_R3")
        self.assertEqual(data["jobs"][0]["cpus"], 1)
        self.assertEqual(data["jobs"][0]["memory_gb"], 16)
        self.assertEqual(data["jobs"][0]["walltime_hours"], 8)

    def test_04_driver_output_precision_full(self):
        """Verify that continuation driver passes output_precision=full to Abaqus."""
        driver_path = REPO_ROOT / "scripts/state_transfer/driver_package150_c1_2_continuation.py"
        text = driver_path.read_text()
        self.assertIn('"output_precision=full"', text)
        self.assertIn("live_iteration_telemetry.json", text)

    def test_05_extractor_supports_double_and_single(self):
        """Verify that endpoint_double.json and endpoint_single_test.json were extracted with correct precision."""
        double_ep = REPO_ROOT / "tests/scratch/test_full_precision/endpoint_double.json"
        single_ep = REPO_ROOT / "tests/scratch/test_full_precision/endpoint_single_test.json"
        self.assertTrue(double_ep.is_file())
        self.assertTrue(single_ep.is_file())
        
        with open(double_ep) as f:
            d_data = json.load(f)
        with open(single_ep) as f:
            s_data = json.load(f)
            
        self.assertEqual(d_data["precision"], "DOUBLE_PRECISION")
        self.assertEqual(s_data["precision"], "SINGLE_PRECISION")
        # Verify 16 digits retained on Node 2 in double
        self.assertEqual(d_data["nodes"][1][2], 0.0013516490580514073)

    def test_06_datacheck_proof(self):
        """Verify authentic cluster datacheck proof recorded."""
        proof_path = REPO_ROOT / "results/validation/package154_r3_datachecks.json"
        self.assertTrue(proof_path.is_file())
        with open(proof_path) as f:
            proof = json.load(f)
        self.assertEqual(proof["status"], "PASS")
        self.assertIn("P150_MECHANICAL_DC.dat", proof["datachecks"])
        self.assertIn("P150_PHASE_DC.dat", proof["datachecks"])

if __name__ == "__main__":
    unittest.main()
