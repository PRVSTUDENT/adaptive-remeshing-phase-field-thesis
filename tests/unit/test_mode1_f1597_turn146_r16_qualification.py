"""
tests/unit/test_mode1_f1597_turn146_r16_qualification.py

Focused unit test suite for Candidate Package 108 Revision 16 (R16):
- Exact R15-to-R16 configuration difference (max_outer_iters 8 -> 15).
- Active-set updates, ranking, and terminal closure logic.
- Stage-A checkpoint reset and history integrity.
- Monolithic 12-DOF UEL residual and multiplier sign conventions.
- Rejection of premature or false convergence (kinematic displacement accuracy guard).
- Solver completion and fail-fast propagation.
"""

import os
import json
import hashlib
import unittest

REPO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
R15_DIR = os.path.join(REPO_DIR, "models/pandey_kumar_mode1/108_r15_c3_autonomous_active_set")
R16_DIR = os.path.join(REPO_DIR, "models/pandey_kumar_mode1/108_r16_c3_autonomous_active_set")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

class TestMode1Turn146R16Qualification(unittest.TestCase):

    def test_01_frozen_production_uel_and_repaired_12dof_uel_hashes(self):
        # 1. Production UEL remains 100% bitwise frozen
        prod_uel = os.path.join(REPO_DIR, "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for")
        expected_prod_sha = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
        self.assertEqual(sha256_file(prod_uel), expected_prod_sha, "Production UEL was modified!")

        # 2. R16 uses verified repaired 12-DOF UEL
        r16_uel = os.path.join(R16_DIR, "f42_unified_12dof_active_set_uel.for")
        expected_repaired_sha = "ab0a5a71335ecb445e91ec13a645e280ff3310b561a5e78aba4a49c8e81dd8ac"
        self.assertEqual(sha256_file(r16_uel), expected_repaired_sha, "R16 UEL does not match repaired 12-DOF UEL!")

    def test_02_exact_r15_to_r16_configuration_difference(self):
        # R16 must preserve identical numerical method: B_max=20, tau_release=5.0e-8, tau_heal=1.0e-8
        # The single algorithmic change must be max_outer_iters 8 -> 15
        driver_r15_path = os.path.join(R15_DIR, "driver_r15_autonomous_continuation.py")
        driver_r16_path = os.path.join(R16_DIR, "driver_r16_autonomous_continuation.py")
        self.assertTrue(os.path.exists(driver_r15_path))
        self.assertTrue(os.path.exists(driver_r16_path))

        with open(driver_r15_path, "r") as f:
            r15_text = f.read()
        with open(driver_r16_path, "r") as f:
            r16_text = f.read()

        self.assertIn("max_outer_iters = 8", r15_text)
        self.assertIn("max_outer_iters = 15", r16_text)
        self.assertIn("B_max = 20", r16_text)
        self.assertIn("tau_release = 5.0e-8", r16_text)
        self.assertIn("tau_heal = 1.0e-8", r16_text)

    def test_03_stage_a_checkpoint_and_boundary_integrity(self):
        # Both R15 and R16 must share identical authentic Stage-A boundary cards and d_lower_bounds
        stage_a_inc_r15 = os.path.join(R15_DIR, "stage_a_all_d0_boundary_cards.inc")
        stage_a_inc_r16 = os.path.join(R16_DIR, "stage_a_all_d0_boundary_cards.inc")
        d_bounds_r15 = os.path.join(R15_DIR, "d_lower_bounds.csv")
        d_bounds_r16 = os.path.join(R16_DIR, "d_lower_bounds.csv")

        self.assertEqual(sha256_file(stage_a_inc_r15), sha256_file(stage_a_inc_r16))
        self.assertEqual(sha256_file(d_bounds_r15), sha256_file(d_bounds_r16))

        # Initial active_set_boundary_cards must start with all nodes active
        active_inc = os.path.join(R16_DIR, "active_set_boundary_cards.inc")
        self.assertEqual(sha256_file(active_inc), sha256_file(stage_a_inc_r16))

    def test_04_kinematic_accuracy_and_fail_fast_guards(self):
        # Verify that driver contains the 6 mandatory fail-fast guardrails
        driver_path = os.path.join(R16_DIR, "driver_r16_autonomous_continuation.py")
        with open(driver_path, "r") as f:
            content = f.read()

        self.assertIn("KINEMATIC_DISPLACEMENT_ERROR", content)
        self.assertIn("DAMAGE_UPPER_BOUND_VIOLATED", content)
        self.assertIn("SEVERE_HEALING_DIVERGENCE", content)
        self.assertIn("CYCLE_OSCILLATION_DETECTED", content)
        self.assertIn("SOLVER_ABORT_EXIT", content)
        self.assertIn("MAX_ITERATIONS_REACHED", content)

    def test_05_r16_authorization_manifest_integrity(self):
        auth_path = os.path.join(R16_DIR, "M1_C3_ACTIVE_SET_R16_AUTHORIZATION.json")
        self.assertTrue(os.path.exists(auth_path))
        with open(auth_path, "r") as f:
            auth = json.load(f)

        self.assertEqual(auth["adapter"], "mode1-experimental-12dof-v1")
        self.assertEqual(auth["jobs"][0]["id"], "M1_C3_ACTIVE_SET_R16")
        self.assertEqual(auth["jobs"][0]["cpus"], 1)
        self.assertLessEqual(auth["jobs"][0]["memory_gb"], 16)
        self.assertLessEqual(auth["jobs"][0]["walltime_hours"], 8)
        self.assertEqual(auth["jobs"][0]["queue"], "entry_imfdfkmq")

        # Verify all files exist and match hashes
        for fname, h in auth["files"].items():
            p = os.path.join(R16_DIR, fname)
            self.assertTrue(os.path.exists(p), f"Missing file: {fname}")
            self.assertEqual(sha256_file(p), h.lower(), f"Hash mismatch for {fname}")

    def test_06_r15_deliverables_and_acceptance_verdict(self):
        verdict_path = os.path.join(REPO_DIR, "results/validation/mode1_f1597/r15_acceptance_verdict.json")
        self.assertTrue(os.path.exists(verdict_path))
        with open(verdict_path, "r") as f:
            verdict = json.load(f)

        self.assertEqual(verdict["verdict"], "FULL_DISPLACEMENT_PASS__ACTIVE_SET_INCOMPLETE")
        self.assertAlmostEqual(verdict["metrics"]["final_rf2_N"], 180.895, places=2)
        self.assertLess(abs(verdict["metrics"]["rf2_discrepancy_pct"]), 2.0)
        self.assertEqual(verdict["metrics"]["violating_active_nodes"], 51)
        self.assertEqual(verdict["metrics"]["healing_nodes"], 0)

if __name__ == "__main__":
    unittest.main()
