# -*- coding: utf-8 -*-
"""
tests/unit/test_mode1_f1597_h36_path_consistent_transfer.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Independent unit test suite verifying Hypothesis H36:
Path-Consistent Nonmatching Transfer Validation.
"""

from __future__ import print_function, division
import os
import sys
import json
import unittest
from pathlib import Path


class TestMode1F1597H36PathConsistentTransfer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parent.parent.parent
        cls.audit_path = cls.repo_root / "results/validation/h36_path_consistent_transfer_audit.json"

        if not cls.audit_path.exists():
            raise RuntimeError("Audit artifact missing: %s" % cls.audit_path)

        with open(cls.audit_path, "r", encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_01_schema_and_task_id(self):
        """Verify schema, task id, and audit name."""
        self.assertEqual(self.data.get("schema"), 1)
        self.assertEqual(self.data.get("task_id"), "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertIn("H36", self.data.get("audit_name", ""))
        self.assertTrue(self.data.get("verification_passed", False))

    def test_02_classification_and_finding(self):
        """Verify classification H36_PATH_MATCHED_TRANSFER_OFFLINE_VALIDATED and finding length."""
        self.assertEqual(self.data.get("classification"), "H36_PATH_MATCHED_TRANSFER_OFFLINE_VALIDATED")
        finding = self.data.get("finding", "")
        self.assertGreaterEqual(len(finding), 20)
        self.assertIn("H36_PATH_MATCHED_TRANSFER_OFFLINE_VALIDATED", finding)
        self.assertFalse(self.data.get("transfer_defect_identified", True))
        self.assertTrue(self.data.get("irreversibility_preserved", False))
        self.assertTrue(self.data.get("kkt_consistency_verified", False))
        self.assertTrue(self.data.get("mechanical_continuity_satisfied", False))

    def test_03_remesh_event_frame77_metrics(self):
        """Verify Frame 77 remesh event: 1600 quads to 4422 quads, minimal attenuation."""
        remesh = self.data.get("remesh_event_frame77", {})
        donor = remesh.get("donor_mesh", {})
        receiver = remesh.get("receiver_mesh", {})
        self.assertEqual(donor.get("quad_elements"), 1600)
        self.assertEqual(receiver.get("quad_elements"), 4422)
        self.assertEqual(receiver.get("nodes"), 4588)

        # Attenuation of peak nodal damage is within 0.50%
        mapped = remesh.get("receiver_initial_mapped_state", {})
        self.assertLessEqual(mapped.get("peak_attenuation_pct"), 0.50)
        self.assertEqual(mapped.get("slit_seam_coordinate_pairs"), 32)
        self.assertFalse(mapped.get("cross_slit_contamination"))

        # History is non-negative and max history conserved
        gp_hist = remesh.get("donor_gp_history", {})
        self.assertTrue(gp_hist.get("non_negative"))
        self.assertAlmostEqual(gp_hist.get("h_max_MPa"), 680.612564, places=2)

    def test_04_continuation_trajectory(self):
        """Verify Gate C1-1 passed, Gate C1-2 Step 1 passed, and Step 2 failed by 80 ppm."""
        traj = self.data.get("continuation_trajectory", {})
        p111 = traj.get("stage_c1_1_frame77_p111_r2", {})
        p112 = traj.get("stage_c1_2_step1_inc78_p112", {})
        p113 = traj.get("stage_c1_2_step2_inc79_p113", {})

        self.assertEqual(p111.get("gate_status"), "GATE_C1_1_PASSED")
        self.assertEqual(p112.get("gate_status"), "GATE_C1_2_STEP1_PASSED")
        self.assertEqual(p113.get("gate_status"), "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED")

        # Check mechanical continuity (RF2 error <= 5%)
        self.assertLessEqual(abs(p111.get("rf2_diff_pct")), 5.0)
        self.assertLessEqual(abs(p112.get("rf2_diff_pct")), 5.0)
        self.assertLessEqual(abs(p113.get("rf2_diff_pct")), 5.0)

        # Check zero healing
        self.assertEqual(p113.get("healing_violations"), 0)

        # Check energy excess is ~17 nJ (80.32 ppm)
        self.assertAlmostEqual(p113.get("energy_diff_pct"), 2.00803158, places=4)
        self.assertAlmostEqual(p113.get("energy_gate_exceedance_nJ"), 17.0629, places=1)

    def test_05_path_dependence_synthesis(self):
        """Verify fine-mesh continuum plateau and delta total energy."""
        syn = self.data.get("path_dependence_synthesis", {})
        self.assertAlmostEqual(syn.get("sequential_p113_e_tot_mJ"), 0.216714, places=4)
        self.assertAlmostEqual(syn.get("direct_p115_e_tot_mJ"), 0.216760, places=4)
        self.assertAlmostEqual(syn.get("delta_tot_energy_nJ"), -46.27, places=1)

    def test_06_governing_gates_and_evidence_hashes(self):
        """Verify governing gate retention and evidence sources integrity."""
        gates = self.data.get("governing_gates_retained", {})
        self.assertTrue(gates.get("STAGE_C1_2_STEP2_ENERGY_GATE_FAILED"))
        self.assertTrue(gates.get("P113_GATE_VALID_FAILURE"))
        self.assertTrue(gates.get("H24_REFERENCE_AUDIT_PENDING"))
        self.assertTrue(gates.get("hpc_submission_withheld"))

        sources = self.data.get("evidence_sources", {})
        self.assertGreaterEqual(len(sources), 7)
        for rel_path, h in sources.items():
            self.assertEqual(len(h), 64)
            full_path = self.repo_root / rel_path
            self.assertTrue(full_path.exists(), "Source file missing: %s" % rel_path)


if __name__ == "__main__":
    unittest.main()
