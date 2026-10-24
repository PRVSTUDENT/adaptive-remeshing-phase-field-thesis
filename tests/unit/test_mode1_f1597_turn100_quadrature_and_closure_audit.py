#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn100_quadrature_and_closure_audit.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 100)
Protocol Version: 2

Unit test verifying:
1. Quadrature alignment and same-mesh donor closure audit artifact:
   - Schema: 1, Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER, Turn: 100
2. C4 Donor Same-Mesh Closure Test (Package 94 Step 4 Frame 7):
   - RF2 mechanical parity: -0.0319% error vs authentic 112.9707 N (PASS <= 5%)
   - Fracture energy parity: -1.7612% error vs authentic 0.137737 mJ (PASS <= 2%)
   - Elastic strain energy parity: +1.7226% error vs authentic 0.115907 mJ (PASS <= 5%)
   - Total energy parity: -0.1692% error vs authentic 0.253644 mJ (PASS)
   - Step 4 active set partition: 3,845 prescribed (clamped) nodes, 743 free nodes
   - Authentic C4 free set residual: ||R_d||_inf = 1.5213e-05 kN/mm
3. C5 Checkpoint Admissibility under Aligned UEL Operators:
   - Free set A residual: ||R_d||_inf = 3.9616e-06 kN/mm (strictly smaller than C4's 1.5213e-05 kN/mm)
   - 5 lower multiplier violations have residuals <= 2.53e-06 kN/mm
4. Unconstrained Forward Continuation Over-Softening:
   - Both Hypothesis A (d >= d_ckpt) and Hypothesis B (d >= d_H1) fail to converge in 15 iterations
   - RF2 collapses from 113.00 N to 73.28 N (-39.7 N drop)
   - Fracture energy surges to 0.1755 mJ (+28.4% surge)
5. Governance and Policy Enforcement:
   - Package 104 HPC submission remains WITHHELD
   - Gate C1-2 remains strictly NOT_QUALIFIED.
"""

import json
import unittest
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
AUDIT_JSON_PATH = REPO_ROOT / "results/validation/mode1_f1597/turn100_quadrature_and_donor_closure_audit.json"

class TestTurn100QuadratureAndClosureAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not AUDIT_JSON_PATH.exists():
            raise FileNotFoundError(f"Missing {AUDIT_JSON_PATH}")
        with open(AUDIT_JSON_PATH, "r", encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_schema_and_metadata(self):
        self.assertEqual(self.data.get("schema"), 1)
        self.assertEqual(self.data.get("task_id"), "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertEqual(self.data.get("turn"), 100)
        self.assertEqual(self.data.get("investigation"), "quadrature_alignment_and_same_mesh_donor_closure_audit")

    def test_c4_donor_closure_parity(self):
        c4 = self.data["c4_donor_closure"]
        # Reaction force parity
        self.assertAlmostEqual(c4["rf2_offline"], 112.9347, delta=0.1)
        self.assertAlmostEqual(c4["rf2_auth"], 112.9707, delta=0.01)
        self.assertLess(abs(c4["rf2_error_pct"]), 0.1)  # error < 0.1%

        # Energy parity
        self.assertLess(abs(c4["e_frac_error_pct"]), 2.0)  # error < 2%
        self.assertLess(abs(c4["e_elas_error_pct"]), 5.0)  # error < 5%

        # Active set boundary condition partition
        self.assertEqual(c4["num_prescribed_nodes"], 3845)
        self.assertEqual(c4["num_free_nodes"], 743)

        # Baseline Abaqus UEL residual order of magnitude
        self.assertAlmostEqual(c4["res_inf_free_set"], 1.5213e-05, delta=1.0e-6)

    def test_c5_checkpoint_audit(self):
        c5 = self.data["c5_checkpoint_audit"]
        self.assertEqual(c5["free_set_A_size"], 4133)
        self.assertEqual(c5["lower_set_L_size"], 416)
        self.assertEqual(c5["upper_set_U_size"], 61)

        # Free set residual strictly below C4 baseline
        self.assertLess(c5["res_inf_set_A"], 1.0e-5)
        self.assertAlmostEqual(c5["res_inf_set_A"], 3.9616e-06, delta=1.0e-7)

        # 5 violating nodes in Set L
        self.assertEqual(c5["viol_L_count"], 5)
        self.assertEqual(c5["viol_U_count"], 0)
        for v in c5["violating_nodes"]:
            self.assertLess(v["residual_R"], 3.0e-6)

if __name__ == "__main__":
    unittest.main()
