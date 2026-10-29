# -*- coding: utf-8 -*-
"""
test_mode1_f1597_h37_refined_donor_transfer.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Independent unit tests verifying the H37 refined-donor transfer audit,
donor availability assessment, and predeclared acceptance criteria.
"""

from __future__ import print_function, division
import os
import sys
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

class TestMode1F1597H37RefinedDonorTransfer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.audit_path = REPO_ROOT / "results/validation/h37_refined_donor_transfer_audit.json"
        if not cls.audit_path.is_file():
            raise unittest.SkipTest("H37 audit artifact does not exist: %s" % cls.audit_path)
        with open(cls.audit_path, "r") as f:
            cls.audit_data = json.load(f)

    def test_01_schema_and_turn_metadata(self):
        self.assertEqual(self.audit_data.get("schema"), 1)
        self.assertEqual(self.audit_data.get("turn"), 302)
        self.assertEqual(self.audit_data.get("task_id"), "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertEqual(self.audit_data.get("hypothesis"), "H37")

    def test_02_c3_int_donor_availability_verdict(self):
        availability = self.audit_data.get("availability_audit", {})
        self.assertTrue(availability.get("p116_r1_dir_exists"))
        self.assertTrue(availability.get("summary_exists"))
        self.assertFalse(availability.get("has_authentic_frame77_checkpoint"))
        self.assertIn("AUTHENTIC_FRAME77_CHECKPOINT_ABSENT", availability.get("authenticity_verdict", ""))
        self.assertAlmostEqual(availability.get("inp_applied_displacement_mm"), 0.00184250, places=6)
        self.assertAlmostEqual(availability.get("required_frame77_displacement_mm"), 0.00180031, places=5)

    def test_03_classification(self):
        self.assertEqual(self.audit_data.get("classification"), "H37_BLOCKED_AUTHENTIC_STATE")

    def test_04_mesh_progression_and_mismatch_reduction(self):
        h37_spec = self.audit_data.get("h37_specification", {})
        progression = h37_spec.get("mesh_progression", {})
        source = progression.get("source_mesh", {})
        target = progression.get("target_mesh", {})
        coarse = progression.get("reference_coarse_mesh", {})
        reduction = progression.get("resolution_mismatch_reduction", {})

        self.assertEqual(source.get("elements"), 2484)
        self.assertEqual(source.get("nodes"), 2610)
        self.assertAlmostEqual(source.get("h_over_ell0"), 0.16000000, places=6)

        self.assertEqual(target.get("elements"), 4422)
        self.assertEqual(target.get("nodes"), 4588)
        self.assertAlmostEqual(target.get("h_over_ell0"), 0.08080000, places=6)

        self.assertEqual(coarse.get("elements"), 1600)
        self.assertEqual(coarse.get("nodes"), 1681)
        self.assertAlmostEqual(coarse.get("h_over_ell0"), 0.33333333, places=6)

        # Mismatch reduction ratio
        self.assertAlmostEqual(reduction.get("original_ratio_c3_to_c4"), 4.12541254, places=4)
        self.assertAlmostEqual(reduction.get("intermediate_ratio_c3int_to_c4"), 1.98019802, places=4)
        self.assertAlmostEqual(reduction.get("mismatch_reduction_factor"), 2.08333333, places=4)

    def test_05_predeclared_acceptance_thresholds(self):
        thresholds = self.audit_data.get("h37_specification", {}).get("predeclared_acceptance_thresholds", {})
        
        # Initial mapping
        mapping = thresholds.get("initial_mapping_fidelity", {})
        self.assertEqual(mapping.get("max_damage_attenuation_pct"), 0.25)
        self.assertEqual(mapping.get("committed_history_loss_pct"), 0.00)
        self.assertEqual(mapping.get("slit_flank_cross_contamination"), 0)

        # Gate C1-1
        c1_1 = thresholds.get("stage_c1_1_re_equilibration", {})
        self.assertEqual(c1_1.get("reaction_force_continuity_pct"), 5.0)
        self.assertEqual(c1_1.get("total_energy_continuity_pct"), 2.0)
        self.assertEqual(c1_1.get("damage_healing_violations"), 0)

        # Gate C1-2 Step 2
        c1_2_step2 = thresholds.get("stage_c1_2_step2_forward_continuation", {})
        self.assertEqual(c1_2_step2.get("reaction_force_continuity_pct"), 5.0)
        self.assertEqual(c1_2_step2.get("total_energy_discrepancy_pct"), 2.00000000)
        self.assertEqual(c1_2_step2.get("damage_healing_violations"), 0)
        self.assertEqual(c1_2_step2.get("kkt_min_dual_multiplier_kN_mm"), -1.0e-9)
        self.assertEqual(c1_2_step2.get("kkt_max_free_residual_kN_mm"), 1.0e-6)

    def test_06_governing_gate_invariants(self):
        gates = self.audit_data.get("governing_gate_status", {})
        self.assertIn("RETAINED_INVARIANT", gates.get("stage_c1_2_step2_energy_gate_failed", ""))
        self.assertIn("RETAINED_INVARIANT", gates.get("p113_gate_valid_failure", ""))
        self.assertIn("RETAINED_INVARIANT", gates.get("h24_reference_audit_pending", ""))

if __name__ == "__main__":
    unittest.main()
