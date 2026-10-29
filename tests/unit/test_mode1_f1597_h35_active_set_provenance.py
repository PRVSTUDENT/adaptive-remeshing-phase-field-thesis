# -*- coding: utf-8 -*-
"""
tests/unit/test_mode1_f1597_h35_active_set_provenance.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Independent unit test suite verifying Hypothesis H35:
Active-Set Provenance and History-Transfer Audit.
"""

from __future__ import print_function, division
import os
import sys
import json
import unittest
from pathlib import Path


class TestMode1F1597H35ActiveSetProvenance(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parent.parent.parent
        cls.audit_path = cls.repo_root / "results/validation/h35_active_set_provenance_audit.json"
        cls.p113_json = cls.repo_root / "models/pandey_kumar_mode1/113_c1_2_second_forward_continuation/c4_c1_2_inc79_continuation_summary.json"
        cls.p115_json = cls.repo_root / "models/pandey_kumar_mode1/115_c4_inc79_direct_transfer/c4_inc79_direct_transfer_summary.json"

        self_assertTrue = cls.audit_path.exists()
        if not self_assertTrue:
            raise RuntimeError("Audit artifact missing: %s" % cls.audit_path)

        with open(cls.audit_path, "r") as f:
            cls.data = json.load(f)

    def test_01_schema_and_task_id(self):
        """Verify schema, task id, and audit name."""
        self.assertEqual(self.data.get("schema"), 1)
        self.assertEqual(self.data.get("task_id"), "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertIn("H35", self.data.get("audit_name", ""))
        self.assertTrue(self.data.get("verification_passed", False))

    def test_02_classification_and_finding(self):
        """Verify classification H35_ACTIVE_SET_PHYSICALLY_JUSTIFIED and finding length."""
        self.assertEqual(self.data.get("classification"), "H35_ACTIVE_SET_PHYSICALLY_JUSTIFIED")
        finding = self.data.get("finding", "")
        self.assertGreaterEqual(len(finding), 20)
        self.assertIn("H35_ACTIVE_SET_PHYSICALLY_JUSTIFIED", finding)
        self.assertFalse(self.data.get("transfer_defect_detected", True))
        self.assertTrue(self.data.get("path_dependence_proven", False))

    def test_03_mesh_and_slit_metrics(self):
        """Verify C4 mesh metrics: 4,588 nodes, 4,422 elements, 32 slit coordinate pairs."""
        mesh = self.data.get("mesh_metrics", {})
        self.assertEqual(mesh.get("total_nodes"), 4588)
        self.assertEqual(mesh.get("total_quad_elements"), 4422)
        self.assertEqual(mesh.get("slit_seam_coordinate_pairs"), 32)
        self.assertEqual(mesh.get("slit_nodes_count"), 64)
        tip = mesh.get("crack_tip_coords_mm", [])
        self.assertAlmostEqual(tip[0], 0.040, places=3)
        self.assertAlmostEqual(tip[1], 0.050, places=3)

    def test_04_package_113_active_set_and_kkt(self):
        """Verify Package 113 has 1,640 clamped nodes, zero healing, and passes KKT conditions."""
        p113 = self.data.get("package_113_sequential_continuation", {})
        self.assertEqual(p113.get("free_nodes"), 2948)
        self.assertEqual(p113.get("clamped_nodes"), 1640)
        self.assertEqual(p113.get("healing_violations"), 0)
        self.assertAlmostEqual(p113.get("free_nodes_pct"), 64.25, places=2)
        self.assertAlmostEqual(p113.get("clamped_nodes_pct"), 35.75, places=2)
        self.assertTrue(p113.get("kkt_optimality_satisfied"))
        self.assertGreaterEqual(p113.get("min_lambda_kN_mm"), -1.0e-9)
        self.assertLessEqual(p113.get("free_res_max_kN_mm"), 1.0e-6)

    def test_05_package_115_active_set(self):
        """Verify Package 115 has 110 clamped nodes and 4,478 free nodes."""
        p115 = self.data.get("package_115_direct_transfer", {})
        self.assertEqual(p115.get("free_nodes"), 4478)
        self.assertEqual(p115.get("clamped_nodes"), 110)
        self.assertEqual(p115.get("healing_violations"), 0)
        self.assertAlmostEqual(p115.get("free_nodes_pct"), 97.60, places=1)
        self.assertAlmostEqual(p115.get("clamped_nodes_pct"), 2.40, places=1)
        self.assertTrue(p115.get("kkt_optimality_satisfied"))

    def test_06_active_set_disparity_and_compensation(self):
        """Verify active-set difference is 1,530 nodes and disparity comparison matches H34."""
        disp = self.data.get("disparity_comparison", {})
        self.assertEqual(disp.get("clamped_nodes_diff"), 1530)
        self.assertEqual(disp.get("free_nodes_diff"), -1530)
        self.assertAlmostEqual(disp.get("e_elas_diff_uJ"), 1.458, places=2)
        self.assertAlmostEqual(disp.get("e_frac_diff_uJ"), -1.504, places=2)
        self.assertAlmostEqual(disp.get("e_tot_diff_nJ"), -46.27, places=1)

    def test_07_history_and_bounds_provenance(self):
        """Verify history non-negativity and bounds continuity."""
        hb = self.data.get("history_and_bounds_audit", {})
        self.assertTrue(hb.get("history_non_negative"))
        p113_d0 = hb.get("p113_initial_d0_range", [])
        p115_d0 = hb.get("p115_initial_d0_range", [])
        self.assertAlmostEqual(p113_d0[1], 0.4906, places=3)
        self.assertAlmostEqual(p115_d0[1], 0.3884, places=3)
        self.assertGreater(hb.get("nodes_where_p113_d0_higher"), 3000)

    def test_08_governing_gates_and_sources(self):
        """Verify governing gate retention and evidence sources hashes."""
        gates = self.data.get("governing_gates_retained", {})
        self.assertTrue(gates.get("STAGE_C1_2_STEP2_ENERGY_GATE_FAILED"))
        self.assertTrue(gates.get("P113_GATE_VALID_FAILURE"))
        self.assertTrue(gates.get("H24_REFERENCE_AUDIT_PENDING"))
        self.assertTrue(gates.get("hpc_submission_withheld"))

        sources = self.data.get("evidence_sources", {})
        self.assertGreaterEqual(len(sources), 5)
        for path_str, h in sources.items():
            self.assertEqual(len(h), 64)
            full_path = self.repo_root / path_str
            self.assertTrue(full_path.exists(), "Source file missing: %s" % path_str)


if __name__ == "__main__":
    unittest.main()
