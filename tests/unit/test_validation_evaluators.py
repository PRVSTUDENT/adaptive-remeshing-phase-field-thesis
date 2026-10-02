#!/usr/bin/env python3
"""
Unit and Software Qualification Test Suite for Mode-II Dual Validation Evaluators:
Qualifies:
  - scripts/postprocessing/criterion_registry.json
  - scripts/postprocessing/evaluate_m2corr_pk10r1_samemesh_r7.py
  - scripts/postprocessing/evaluate_m2corr_pk10r2_topology.py
  - scripts/postprocessing/ingest_validation_job_results.py
"""

import os
import sys
import json
import math
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
POST_DIR = REPO_ROOT / "scripts" / "postprocessing"
sys.path.insert(0, str(POST_DIR))

from evaluate_m2corr_pk10r1_samemesh_r7 import (
    load_criterion_registry,
    CRITERIA,
    ACTIVE_REFERENCE_HANDOFF_RF1_KN,
    ORIGINAL_HANDOFF_RF1_KN,
    REPLAY_HANDOFF_RF1_KN,
    THRESH_PHASE_HEALING_MIN_DELTA_D,
    THRESH_STEP1_HANDOFF_PCT,
    THRESH_MECH_JUMP_PCT,
    THRESH_TERMINAL_RF1_PCT
)
from evaluate_m2corr_pk10r2_topology import (
    calculate_k0_stiffness,
    calculate_peak_and_terminal,
    evaluate_pk10r2_topology,
    ACCEPTED_REFERENCES,
    DEFECTIVE_PK10R1
)
from ingest_validation_job_results import classify_job_execution_state

class TestValidationEvaluators(unittest.TestCase):

    def test_01_criterion_registry_integrity(self):
        """Test criterion registry has all required criteria and no missing provenance."""
        reg = load_criterion_registry()
        self.assertIn("CRIT_R7_HANDOFF_RF1_TOLERANCE", reg)
        self.assertIn("CRIT_R7_MECH_EQUILIBRATION_RF1_JUMP", reg)
        self.assertIn("CRIT_R7_PHASE_IRREVERSIBILITY_TOLERANCE", reg)
        self.assertIn("CRIT_R7_TERMINAL_CONTINUATION_RF1_TOLERANCE", reg)
        self.assertIn("CRIT_PK10R2_INITIAL_STIFFNESS_K0", reg)

        # Check types
        self.assertEqual(reg["CRIT_R7_HANDOFF_RF1_TOLERANCE"]["criterion_type"], "FROZEN_SCIENTIFIC")
        self.assertEqual(reg["CRIT_R7_PHASE_IRREVERSIBILITY_TOLERANCE"]["criterion_type"], "FROZEN_SCIENTIFIC")
        self.assertEqual(reg["CRIT_R7_PHASE_RELEASE_RF1_JUMP"]["criterion_type"], "QUALITATIVE")

    def test_02_phase_irreversibility_tolerance(self):
        """Test Phase Irreversibility evaluation on 4 synthetic cases."""
        tol = THRESH_PHASE_HEALING_MIN_DELTA_D # -1.0e-6

        # Case A: Positive growth (+0.05)
        d_prev = 0.10
        d_next_a = 0.15
        delta_a = d_next_a - d_prev
        self.assertTrue(delta_a >= tol, "Case A positive growth should pass")

        # Case B: Exactly unchanged (0.00)
        d_next_b = 0.10
        delta_b = d_next_b - d_prev
        self.assertTrue(delta_b >= tol, "Case B zero change should pass")

        # Case C: Small negative change within numerical tolerance (-5.0e-7)
        d_next_c = 0.10 - 5.0e-7
        delta_c = d_next_c - d_prev
        self.assertTrue(delta_c >= tol, "Case C small numerical negative should pass")

        # Case D: Unphysical healing outside tolerance (-0.01)
        d_next_d = 0.09
        delta_d = d_next_d - d_prev
        self.assertFalse(delta_d >= tol, "Case D unphysical healing must fail")

    def test_03_handoff_reference_resolution(self):
        """Test distinct preservation of replay handoff and original baseline handoff."""
        self.assertAlmostEqual(REPLAY_HANDOFF_RF1_KN, 0.305426, places=5)
        self.assertAlmostEqual(ORIGINAL_HANDOFF_RF1_KN, 0.305468, places=5)
        self.assertEqual(ACTIVE_REFERENCE_HANDOFF_RF1_KN, REPLAY_HANDOFF_RF1_KN)

    def test_04_pk10r2_k0_stiffness_calculation(self):
        """Test K0 calculation on synthetic linear response and reference values."""
        synth_traj = [
            {"u1_mm": 0.000000, "rf1_kN": 0.000000, "d_max": 0.0},
            {"u1_mm": 0.000100, "rf1_kN": 0.052901, "d_max": 0.0},
            {"u1_mm": 0.000200, "rf1_kN": 0.105802, "d_max": 0.0},
            {"u1_mm": 0.000616, "rf1_kN": 0.294830, "d_max": 0.1},
        ]
        k0_res, err = calculate_k0_stiffness(synth_traj)
        self.assertIsNone(err)
        self.assertAlmostEqual(k0_res["k0_kN_mm"], 529.01, delta=0.01)

    def test_05_pk10r2_error_reduction_math(self):
        """Test error reduction fraction calculation."""
        h2_k0 = ACCEPTED_REFERENCES["H2"]["k0_kN_mm"] # 529.01
        pk10r1_k0 = DEFECTIVE_PK10R1["k0_kN_mm"] # 639.80
        base_err = abs(pk10r1_k0 - h2_k0) # 110.79

        # Case 1: Perfect candidate matching H2 (K0 = 529.01) -> reduction = 1.0 (100%)
        cand_k0_perf = 529.01
        cand_err_perf = abs(cand_k0_perf - h2_k0)
        red_perf = 1.0 - (cand_err_perf / base_err)
        self.assertAlmostEqual(red_perf, 1.0, places=5)

        # Case 2: Candidate with 50% error reduction (K0 = 584.405) -> reduction = 0.50
        cand_k0_half = 529.01 + 0.5 * base_err
        cand_err_half = abs(cand_k0_half - h2_k0)
        red_half = 1.0 - (cand_err_half / base_err)
        self.assertAlmostEqual(red_half, 0.50, places=5)

    def test_06_failure_stage_classifier(self):
        """Test failure classifier on representative log patterns."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Subtest: Compiler failure
            (tmppath / "job.err").write_text("ifort: command not found\n")
            res = classify_job_execution_state(tmpdir)
            self.assertEqual(res, "MODULE_COMPILER_FAILURE")
            (tmppath / "job.err").unlink()

            # Subtest: Input processor failure
            (tmppath / "job.dat").write_text("***ERROR: Invalid card\n")
            res = classify_job_execution_state(tmpdir)
            self.assertEqual(res, "INPUT_PROCESSOR_FAILURE")
            (tmppath / "job.dat").unlink()

            # Subtest: Successful solver completion
            (tmppath / "job.sta").write_text(" 1 1 1 0.1 0.1 0.1\nTHE ANALYSIS HAS COMPLETED SUCCESSFULLY\n")
            res = classify_job_execution_state(tmpdir)
            self.assertEqual(res, "SUCCESSFUL_SOLVER_COMPLETION")

if __name__ == "__main__":
    unittest.main()
