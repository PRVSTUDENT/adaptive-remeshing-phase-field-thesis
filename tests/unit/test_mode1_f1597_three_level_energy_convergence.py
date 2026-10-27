"""
Unit regression test for Turn 218 Three-Level AT2 Energy-Convergence Audit.
Verifies:
1. Constitutive property consistency (k = 1.0e-07 across all decks).
2. Convergence metrics of Package 116 R1 (Job 1417818).
3. Monotonic convergence of reaction force and fracture energy across Levels 1, 2, 3.
4. Plateau ratio between Level 2 and Level 3 (< 0.1% change in E_frac).
"""

import os
import json
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

class TestThreeLevelConvergence(unittest.TestCase):

    def setUp(self):
        self.audit_path = os.path.join(REPO_ROOT, "results/validation/three_level_at2_energy_convergence_audit.json")
        self.assertTrue(os.path.exists(self.audit_path), "Audit artifact must exist")
        with open(self.audit_path, "r") as f:
            self.data = json.load(f)

    def test_constitutive_consistency(self):
        ca = self.data["constitutive_consistency_audit"]
        self.assertEqual(ca["mismatch_finding"][:11], "NO_MISMATCH")
        for deck_key, deck_info in ca["verified_decks"].items():
            self.assertTrue(deck_info["match"], f"Deck {deck_key} must match canonical properties")
            self.assertEqual(deck_info["k_residual"], 1.0e-07)

    def test_package_116_r1_convergence(self):
        p116 = self.data["package_116_r1_evaluation"]
        self.assertEqual(p116["classification"], "INTERMEDIATE_MESH_CONVERGED")
        self.assertEqual(p116["driver_status"], "CONVERGED_STATIONARY_STATE")
        self.assertEqual(p116["exit_status"], 0)
        self.assertEqual(p116["cycles_to_convergence"], 7)
        for crit_name, crit_data in p116["acceptance_criteria"].items():
            self.assertTrue(crit_data["pass"], f"Criterion {crit_name} must pass")

    def test_monotonic_convergence(self):
        h = self.data["three_level_mesh_hierarchy"]
        rf2_1 = h["level_1_c3_donor"]["rf2_N"]
        rf2_2 = h["level_2_c3_int_r1"]["rf2_N"]
        rf2_3 = h["level_3_c4_receiver"]["rf2_N"]

        # Reaction force decreases monotonically
        self.assertGreater(rf2_1, rf2_2)
        self.assertGreater(rf2_2, rf2_3)

        e_frac_1 = h["level_1_c3_donor"]["e_frac_mJ"]
        e_frac_2 = h["level_2_c3_int_r1"]["e_frac_mJ"]
        e_frac_3 = h["level_3_c4_receiver"]["e_frac_mJ"]

        # Fracture energy increases monotonically
        self.assertLess(e_frac_1, e_frac_2)
        self.assertLess(e_frac_2, e_frac_3)

    def test_plateau_ratio(self):
        c = self.data["consecutive_step_changes"]
        p = c["convergence_plateau_analysis"]
        self.assertGreater(p["pct_of_shift_in_first_refinement"], 99.0)
        self.assertLess(p["pct_of_shift_in_second_refinement"], 1.0)
        self.assertLess(c["level_2_to_level_3"]["delta_e_frac_pct"], 0.1)

    def test_governance_retained(self):
        g = self.data["governance_verdict"]
        self.assertEqual(g["gate_status"], "C1_2_STEP2_ENERGY_GATE_FAILED_RETAINED")
        self.assertFalse(g["threshold_relaxation_authorized"])

if __name__ == "__main__":
    unittest.main()
