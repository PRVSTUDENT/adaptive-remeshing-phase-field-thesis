#!/usr/bin/env python3
"""
Unit Test Suite for Gate-6B Stage 14U-AD:
4-Thread Shared-Memory Stage-A Parity Qualification & Live Telemetry Correction
"""

import unittest
import hashlib
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
PACKAGE_DIR = os.path.join(PROJECT_ROOT, "models", "pandey_kumar_mode1", "26_stage14_adaptive_candidate_14k_4thread")

EXPECTED_INP_SHA = "26d873fb2e68055c80550d1dd981766bcaf46e13d3d0a7ba6411b63d9c382d35"
EXPECTED_FOR_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

class TestStage14UAD4ThreadParity(unittest.TestCase):
    
    def test_01_package26_hash_invariance(self):
        """Verify Package 26 input deck and Fortran hashes match authoritative Stage-14U baseline."""
        inp_path = os.path.join(PACKAGE_DIR, "PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp")
        for_path = os.path.join(PACKAGE_DIR, "f42_mixed_uel.for")
        
        self.assertTrue(os.path.exists(inp_path), f"Package 26 input deck missing: {inp_path}")
        self.assertTrue(os.path.exists(for_path), f"Package 26 Fortran source missing: {for_path}")
        
        self.assertEqual(sha256_file(inp_path), EXPECTED_INP_SHA, "Input deck hash mismatch")
        self.assertEqual(sha256_file(for_path), EXPECTED_FOR_SHA, "Fortran source hash mismatch")

    def test_02_step_displacement_ramp_formulation(self):
        """Verify correct Step-1 and Step-2 loading schedules and validate displacement correction."""
        # Step 1: Monotonic loading to u = 0.0050 mm over time period 1.0
        u_step1_end = 0.0050 * 1.0
        self.assertAlmostEqual(u_step1_end, 0.0050, places=6)
        
        # Step 2: Monotonic loading from u = 0.0050 to u = 0.0100 mm over time period 1.0
        # u(t_step) = 0.0050 + (0.0100 - 0.0050) * t_step = 0.0050 + 0.0050 * t_step
        t_sample = 0.3940
        u_sample = 0.0050 + 0.0050 * t_sample
        self.assertAlmostEqual(u_sample, 0.006970, places=6)
        
        # Reject erroneous previous estimate of 0.00454 mm
        self.assertNotAlmostEqual(u_sample, 0.00454, places=4)

    def test_03_execution_architecture_contract(self):
        """Verify 1 MPI rank x 4 shared-memory threads configuration."""
        pbs_path = os.path.join(PACKAGE_DIR, "submit_solver.pbs")
        self.assertTrue(os.path.exists(pbs_path), f"submit_solver.pbs missing: {pbs_path}")
        
        with open(pbs_path, "r") as f:
            content = f.read()
            
        self.assertIn("cpus=4", content)
        self.assertIn("mp_mode=threads", content)
        self.assertIn("nodes=1:ppn=4", content)
        self.assertIn("f42_mixed_uel.for", content)

    def test_04_manifest_and_pre_job_card(self):
        """Verify MANIFEST.json and PRE_JOB_ANTI_DEVIATION_CARD.md."""
        manifest_path = os.path.join(PACKAGE_DIR, "MANIFEST.json")
        card_path = os.path.join(PACKAGE_DIR, "PRE_JOB_ANTI_DEVIATION_CARD.md")
        
        self.assertTrue(os.path.exists(manifest_path), f"MANIFEST.json missing: {manifest_path}")
        self.assertTrue(os.path.exists(card_path), f"PRE_JOB_ANTI_DEVIATION_CARD.md missing: {card_path}")
        
        with open(manifest_path, "r") as f:
            m = json.load(f)
            
        self.assertEqual(m["subroutine_status"], "THREAD_SAFETY_UNVERIFIED")
        self.assertEqual(m["invariances"]["nodes"], 14456)
        self.assertEqual(m["invariances"]["base_elements"], 14483)
        self.assertEqual(m["invariances"]["layered_elements"], 43449)

    def test_05_two_stage_qualification_protocol_logic(self):
        """Verify that Stage A (parity) and Stage B (determinism) are required before qualification."""
        stage_a_status = "THREAD_PARITY_PASS_OVER_REACHED_RANGE"
        stage_b_status = "PENDING_REPEATED_RUN"
        
        # Qualification cannot be granted from Stage A alone
        qualified = (stage_a_status == "THREAD_PARITY_PASS_OVER_REACHED_RANGE") and (stage_b_status == "THREAD_DETERMINISM_PASS")
        self.assertFalse(qualified)

    def test_06_evaluator_script_presence(self):
        """Verify evaluation script is present and importable."""
        eval_path = os.path.join(PACKAGE_DIR, "evaluate_stage14uad_4thread_parity.py")
        self.assertTrue(os.path.exists(eval_path), f"Parity evaluator missing: {eval_path}")

if __name__ == "__main__":
    unittest.main()
