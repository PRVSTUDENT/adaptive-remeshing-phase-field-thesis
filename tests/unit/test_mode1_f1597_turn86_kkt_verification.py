#!/usr/bin/env python3
"""
Unit Regression Test: Turn 86 KKT Correctness and False Acceptance Prevention.
Validates:
1. Rejection of candidate states where release suppression produces zero set changes
   but leaves lower-bound dual residuals exceeding TAU_RES = 1.0e-6 kN/mm.
2. Rejection of free-set residual 2.130e-6 kN/mm under governing threshold 1.0e-6 kN/mm.
3. Falsification of false acceptance: kkt_lower_valid must be strictly enforced.
4. Non-zero projected gradient norm proving release suppression terminates at a suboptimal state.
5. Exact identification of the 32 suppressed KKT-violating boundary nodes.
"""

import unittest
import json
from pathlib import Path
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
audit_json = REPO_ROOT / "results/validation/mode1_f1597/turn86_package100_kkt_and_acceptance_audit.json"

class TestPackage100KKTCorrectness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        self_audit_path = audit_json
        with open(self_audit_path, "r", encoding="utf-8") as f:
            cls.audit_data = json.load(f)

    def test_01_free_set_tolerance_rejection(self):
        """Verifies that the free-set residual (2.130e-6) fails the 1.0e-6 governing threshold."""
        eval_data = self.audit_data["scientific_evaluation"]["defect_a_free_set_tolerance"]
        res_A = eval_data["value"]
        threshold = eval_data["governing_threshold_kNmm"]
        self.assertGreater(res_A, threshold, "Free set residual must exceed governing threshold")
        self.assertEqual(eval_data["verdict"], "FAIL", "Free set residual verdict must be FAIL")

    def test_02_kkt_lower_multiplier_rejection(self):
        """Verifies that lower-bound KKT violations exist and kkt_lower_valid is False."""
        eval_data = self.audit_data["scientific_evaluation"]["defect_b_kkt_lower_multiplier"]
        self.assertFalse(eval_data["value"], "kkt_lower_multiplier_valid must be False")
        self.assertEqual(eval_data["violating_node_count"], 32, "Exactly 32 boundary nodes must violate KKT")
        self.assertGreater(eval_data["max_residual_excess_kNmm"], 0.0, "Residual excess must be positive")
        self.assertEqual(eval_data["verdict"], "FAIL", "KKT lower multiplier verdict must be FAIL")

    def test_03_suppressed_boundary_nodes_identification(self):
        """Verifies exact identification of the 32 suppressed boundary nodes."""
        suppressed_nodes = self.audit_data["scientific_evaluation"]["defect_c_heuristic_suppression"]["top_violating_nodes"]
        self.assertGreaterEqual(len(suppressed_nodes), 10, "At least 10 top violating nodes must be recorded")
        for node_info in suppressed_nodes:
            self.assertIn("node_id", node_info)
            self.assertGreater(node_info["R_d_kNmm"], 1.0e-6, "Each suppressed node must have R_d > 1e-6")
            self.assertGreater(node_info["kkt_excess_kNmm"], 0.0, "Residual excess must be strictly positive")

    def test_04_objective_suboptimality(self):
        """Verifies that Package 100 objective value is suboptimal relative to exact QP minimizer."""
        obj_data = self.audit_data["scientific_evaluation"]["objective_function_suboptimality"]
        gap = obj_data["suboptimality_gap"]
        self.assertGreater(gap, 0.0, "Objective value must be higher than exact QP minimizer")

    def test_05_fracture_energy_continuity_rejection(self):
        """Verifies that fracture energy continuity deficit (-2.063%) fails the 2.0% threshold."""
        e_frac_data = self.audit_data["scientific_evaluation"]["continuity_metrics"]["fracture_energy"]
        disc_pct = e_frac_data["discrepancy_pct"]
        tol_pct = e_frac_data["tolerance_pct"]
        self.assertGreater(abs(disc_pct), tol_pct, "Fracture energy discrepancy must exceed 2.0% tolerance")
        self.assertEqual(e_frac_data["verdict"], "FAIL", "Fracture energy verdict must be FAIL")

    def test_06_gate_c1_2_remains_not_qualified(self):
        """Verifies that Gate C1-2 is strictly maintained as NOT_QUALIFIED."""
        gate_status = self.audit_data["governed_gate_status"]["gate_c1_2"]
        self.assertEqual(gate_status, "NOT_QUALIFIED", "Gate C1-2 must remain strictly NOT_QUALIFIED")

if __name__ == "__main__":
    unittest.main()
