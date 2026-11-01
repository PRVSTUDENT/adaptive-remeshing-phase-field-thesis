#!/usr/bin/env python3
"""
test_authentic_fracture_energy_audit.py

Unit tests verifying authentic fracture-energy provenance and state-transfer consistency
for Method C (Turn 434).
"""

import unittest
import json
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
AUDIT_JSON = REPO_ROOT / "results/validation/authentic_fracture_energy_audit.json"

class TestAuthenticFractureEnergyAudit(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.assertTrue(cls, AUDIT_JSON.exists(), f"Audit JSON not found at {AUDIT_JSON}")
        with open(AUDIT_JSON, "r", encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_provenance_and_schema(self):
        self.assertEqual(self.data.get("schema"), 1)
        self.assertEqual(self.data.get("investigation"), "AUTHENTIC_FRACTURE_ENERGY_AND_STATE_TRANSFER_AUDIT")
        self.assertEqual(self.data.get("status"), "AUTHENTIC_ENERGY_RECONCILED")
        self.assertTrue(self.data.get("verification_passed"))
        self.assertGreaterEqual(len(self.data.get("finding", "")), 20)

    def test_quadrature_machine_precision_match(self):
        quad = self.data["provenance_reconciliation"]["quadrature_reconciliation"]
        self.assertTrue(quad["machine_precision_match_verified"])
        self.assertLess(quad["quadrature_relative_difference_percent"], 1e-10)
        self.assertLess(quad["quadrature_absolute_difference_kNmm"], 1e-15)
        # Scaled donor should match Abaqus reported value
        scaled = quad["scaled_donor_fracture_energy_kNmm"]
        abaqus = quad["abaqus_reported_fracture_energy_kNmm"]
        self.assertAlmostEqual(scaled, abaqus, places=12)

    def test_energy_conservation_gates(self):
        discrepancies = self.data["energy_decomposition"]["donor_to_receiver_discrepancies"]
        self.assertLessEqual(discrepancies["fracture_energy_difference_percent"], 2.0)
        self.assertLessEqual(discrepancies["elastic_energy_difference_percent"], 2.0)
        self.assertLessEqual(discrepancies["total_energy_difference_percent"], 2.0)
        self.assertTrue(discrepancies["fracture_gate_pass"])
        self.assertTrue(discrepancies["elastic_gate_pass"])
        self.assertTrue(discrepancies["total_raw_gate_pass"])

    def test_receiver_vs_abaqus_continuity(self):
        rx_abaqus = self.data["energy_decomposition"]["receiver_to_abaqus_discrepancies"]
        self.assertLessEqual(rx_abaqus["fracture_energy_difference_percent"], 2.0)
        self.assertLessEqual(rx_abaqus["elastic_energy_difference_percent"], 2.0)
        self.assertLessEqual(rx_abaqus["total_energy_difference_percent"], 2.0)

    def test_damage_peak_attenuation(self):
        d_audit = self.data["damage_peak_audit"]
        self.assertEqual(d_audit["mechanism"], "CONVEX_BILINEAR_INTERPOLATION_DISCRETIZATION_SMOOTHING")
        self.assertTrue(d_audit["physical_monotonicity_satisfied"])
        self.assertTrue(d_audit["bounds_satisfied"])
        self.assertAlmostEqual(d_audit["max_damage_donor"], 0.60525, places=4)
        self.assertAlmostEqual(d_audit["max_damage_receiver"], 0.60337, places=4)
        self.assertLess(d_audit["relative_reduction_percent"], 1.0)
        self.assertGreater(d_audit["relative_reduction_percent"], 0.0)

    def test_package158_canonical_identity(self):
        p158 = self.data["package158_identity_resolution"]
        self.assertEqual(p158["canonical_operation_id"], "execute_mode1_package158_c2_0_r5_re_equilibration")
        self.assertEqual(p158["manifest_batch_name"], "MODE1_PACKAGE158_M1_P158_C2_0_R5")
        self.assertEqual(p158["manifest_job_id"], "M1_P158_C2_0_R5")


if __name__ == "__main__":
    unittest.main()
