# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn209_energy_gate_audit.py
=============================================
Unit test suite verifying high-precision energy continuity evaluation,
strict gate classification (C1_2_STEP2_ENERGY_GATE_FAILED), and
Package 95 MISESERI load-state correspondence audit for Turn 209.

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 209)
"""
import os
import json
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class TestTurn209EnergyGateAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        audit_path = os.path.join(REPO_ROOT, "results", "validation", "turn209_energy_and_miseseri_audit.json")
        with open(audit_path, "r") as f:
            cls.audit = json.load(f)

    def test_01_donor_and_c4_energy_values(self):
        """Verify authentic donor Increment 79 and Candidate C4 Cycle 4 energies."""
        donor_e = self.audit["donor_increment_79"]["e_tot_mJ"]
        c4_e = self.audit["candidate_c4_increment_79"]["e_tot_mJ"]
        self.assertAlmostEqual(donor_e, 0.21244805, places=7)
        self.assertAlmostEqual(c4_e, 0.21671407, places=7)

    def test_02_strict_energy_gate_classification(self):
        """Verify unrounded energy diff exceeds 2.0% and verdict is strictly C1_2_STEP2_ENERGY_GATE_FAILED."""
        eval_data = self.audit["energy_continuity_evaluation"]
        diff_pct = eval_data["total_energy_diff_pct_unrounded"]
        self.assertGreater(diff_pct, 2.000000)
        self.assertAlmostEqual(diff_pct, 2.0080315, places=5)
        self.assertFalse(eval_data["gate_passed"])
        self.assertEqual(eval_data["verdict"], "C1_2_STEP2_ENERGY_GATE_FAILED")

    def test_03_energy_component_breakdown(self):
        """Verify component breakdown: elastic matches within 0.7%, fracture is +7.48% higher."""
        eval_data = self.audit["energy_continuity_evaluation"]
        elas_diff = eval_data["elastic_energy_diff_pct"]
        frac_diff = eval_data["fracture_energy_diff_pct"]
        self.assertAlmostEqual(elas_diff, 0.69737, places=3)
        self.assertAlmostEqual(frac_diff, 7.48145, places=3)
        # Verify physical mechanism description is present
        self.assertIn("606 nm", eval_data["physical_mechanism"])
        self.assertIn("C1_2_STEP2_ENERGY_GATE_FAILED", eval_data["physical_mechanism"])

    def test_04_miseseri_displacement_load_state_audit(self):
        """Verify Package 95 MISESERI was solved at u=0.002052 mm vs Inc 79 at u=0.0018425 mm."""
        miseseri = self.audit["miseseri_audit"]
        self.assertAlmostEqual(miseseri["pkg95_prescribed_u2_mm"], 0.002052, places=6)
        self.assertAlmostEqual(miseseri["pkg113_inc79_u2_mm"], 0.0018425, places=6)
        self.assertAlmostEqual(miseseri["displacement_discrepancy_pct"], 11.3704, places=2)
        self.assertEqual(miseseri["spatial_indicator_validity"], "TOPOLOGICALLY_CONSISTENT_NOTCH_TIP_LOCALIZATION")
        self.assertEqual(miseseri["quantitative_load_correspondence"], "LOAD_STATE_MISMATCH_POST_PEAK_VS_PRE_PEAK")

    def test_05_c5_adaptation_prerequisite(self):
        """Verify scientific finding that a new companion solve at Increment 79 is required before C5."""
        miseseri = self.audit["miseseri_audit"]
        self.assertEqual(
            miseseri["c5_remeshing_recommendation"],
            "DEDICATED_COMPANION_SOLVE_REQUIRED_AT_INC79_LOAD_BEFORE_C5_FINALIZATION"
        )

    def test_06_audit_artifact_integrity(self):
        """Verify audit artifact contains all required evidence source hashes."""
        hashes = self.audit["evidence_hashes"]
        self.assertEqual(len(hashes), 4)
        for rel_path, sha in hashes.items():
            full_path = os.path.join(REPO_ROOT, rel_path)
            self.assertTrue(os.path.exists(full_path))
            self.assertEqual(len(sha), 64)

if __name__ == "__main__":
    unittest.main()
