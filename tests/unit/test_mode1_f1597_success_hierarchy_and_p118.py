"""
Unit test for Method C Success-Criteria Hierarchy and Package 118 Validation.
Verifies:
1. Definitive 6-level success-criteria decision matrix structure and verdicts.
2. Exact retention of Level 3 gate failure (C1_2_STEP2_ENERGY_GATE_FAILED).
3. Non-promotion of Level 5 (NOT_YET_DEMONSTRATED).
4. Pointwise unrounded agreement between Package 115 and Package 118 on Candidate C4.
5. Exact cross-mesh energy attribution decomposition.
"""

import os
import json
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

class TestMethodCSuccessHierarchyAndP118(unittest.TestCase):

    def setUp(self):
        self.matrix_path = os.path.join(REPO_ROOT, "results/validation/method_c_success_hierarchy_matrix.json")
        self.p115_p118_path = os.path.join(REPO_ROOT, "results/validation/p115_vs_p118_comparative_audit.json")
        self.attribution_path = os.path.join(REPO_ROOT, "results/validation/cross_mesh_energy_attribution_audit.json")

        self.assertTrue(os.path.isfile(self.matrix_path), "Success hierarchy matrix must exist")
        self.assertTrue(os.path.isfile(self.p115_p118_path), "P115 vs P118 audit must exist")
        self.assertTrue(os.path.isfile(self.attribution_path), "Cross-mesh attribution audit must exist")

        with open(self.matrix_path, "r", encoding="utf-8") as f:
            self.matrix = json.load(f)
        with open(self.p115_p118_path, "r", encoding="utf-8") as f:
            self.p115_p118 = json.load(f)
        with open(self.attribution_path, "r", encoding="utf-8") as f:
            self.attribution = json.load(f)

    def test_hierarchy_matrix_structure(self):
        self.assertEqual(self.matrix["schema"], 1)
        levels = self.matrix["levels"]
        self.assertEqual(len(levels), 6, "Must define exactly 6 levels (Level 0 through 5)")

        expected_verdicts = {
            0: "PASS",
            1: "PASS",
            2: "PASS",
            3: "FAIL",
            4: "PASS",
            5: "NOT_YET_DEMONSTRATED"
        }
        for lvl in levels:
            lvl_num = lvl["level"]
            self.assertIn(lvl_num, expected_verdicts)
            self.assertEqual(lvl["level_verdict"], expected_verdicts[lvl_num],
                             f"Level {lvl_num} verdict mismatch")

    def test_level_3_gate_retention(self):
        lvl3 = self.matrix["levels"][3]
        self.assertEqual(lvl3["binding_verdict"], "C1_2_STEP2_ENERGY_GATE_FAILED")
        self.assertIn("BLOCKED", lvl3["progression_permitted"])
        pkg113_crit = [c for c in lvl3["criteria"] if "Package 113" in c["metric"]][0]
        self.assertEqual(pkg113_crit["status"], "FAIL")
        self.assertIn("+2.0080315%", pkg113_crit["measured_result"])

    def test_level_5_not_demonstrated(self):
        lvl5 = self.matrix["levels"][5]
        self.assertEqual(lvl5["level_verdict"], "NOT_YET_DEMONSTRATED")
        for crit in lvl5["criteria"]:
            self.assertEqual(crit["status"], "NOT_YET_DEMONSTRATED")

    def test_p115_vs_p118_field_agreement(self):
        norms = self.p115_p118["pointwise_field_norms"]
        # Damage L_infinity < 0.001, relative L2 < 0.05%
        self.assertLess(norms["damage_nodal"]["l_infinity"], 1.0e-3)
        self.assertLess(norms["damage_nodal"]["relative_l_2_pct"], 0.05)

        # Displacement L_infinity < 1.0e-6 mm (1 nm)
        self.assertLess(norms["displacement_nodal_mm"]["l_infinity"], 1.0e-6)
        self.assertLess(norms["displacement_nodal_mm"]["relative_l_2_pct"], 0.01)

        # Scalar total energy and RF2 diffs
        metrics = self.p115_p118["terminal_metrics_comparison"]
        self.assertLess(abs(metrics["energies"]["e_tot_mJ"]["rel_diff_pct"]), 0.001)
        self.assertLess(abs(metrics["reaction_force"]["rel_diff_pct"]), 0.01)

    def test_cross_mesh_energy_attribution(self):
        attr = self.attribution["energy_shift_attribution"]
        # Quadrature error on fixed transferred field should be < 0.5%
        self.assertLess(abs(attr["stage_1_discretization_quadrature_pct"]), 0.5)

        # Re-equilibration sharpening should drive the elevation (> 5%)
        self.assertGreater(attr["stage_2_reequilibration_crack_sharpening_pct"], 5.0)

        # Check total net offset is ~ +2.03%
        self.assertAlmostEqual(attr["total_energy_continuity_offset_pct"], 2.026, places=1)

if __name__ == "__main__":
    unittest.main()
