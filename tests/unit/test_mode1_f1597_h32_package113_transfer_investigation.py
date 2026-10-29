# -*- coding: utf-8 -*-
"""
test_mode1_f1597_h32_package113_transfer_investigation.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Independent unit test qualification of Turn 297 H32 Package 113 cross-mesh
energy transfer investigation and mathematical hypothesis evaluation.
"""

import json
import os
import unittest


class TestMode1F1597H32Package113TransferInvestigation(unittest.TestCase):
    """Independent unit test suite verifying H32 Package 113 investigation."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cls.audit_path = os.path.join(
            cls.repo_root, "results", "validation", "h32_package113_transfer_investigation.json"
        )
        with open(cls.audit_path, "r") as f:
            cls.audit = json.load(f)

    def test_01_original_energy_discrepancy_reconstruction(self):
        """Verify exact unrounded Package 113 energy discrepancy reconstruction."""
        gate = self.audit["binding_energy_gate"]
        # Exact discrepancy is +2.00803158%
        self.assertAlmostEqual(gate["pct_diff_tot_unrounded"], 2.00803158, places=6)
        self.assertEqual(gate["predeclared_tolerance_pct"], 2.0)
        self.assertAlmostEqual(gate["exceedance_pct_points"], 0.00803158, places=6)
        self.assertAlmostEqual(gate["exceedance_ppm"], 80.3158, places=2)
        # Exceedance energy is ~17.06 nJ
        self.assertAlmostEqual(gate["excess_energy_nJ"], 17.0629, places=1)

    def test_02_component_energy_deconstruction(self):
        """Verify that AT2 fracture energy drives 71.98% of the excess energy."""
        gate = self.audit["binding_energy_gate"]
        self.assertTrue(gate["reproducibility_of_71_98_share"])
        self.assertAlmostEqual(gate["share_of_excess_frac_pct"], 71.9806, places=2)
        self.assertAlmostEqual(gate["share_of_excess_elas_pct"], 28.0194, places=2)

        # Donor and receiver absolute component values
        self.assertAlmostEqual(gate["donor_elas_mJ"], 0.17140369, places=8)
        self.assertAlmostEqual(gate["donor_frac_mJ"], 0.041044352, places=8)
        self.assertAlmostEqual(gate["donor_tot_mJ"], 0.21244805, places=8)
        self.assertAlmostEqual(gate["receiver_elas_mJ"], 0.17259901, places=6)
        self.assertAlmostEqual(gate["receiver_frac_mJ"], 0.04411506, places=6)
        self.assertAlmostEqual(gate["receiver_tot_mJ"], 0.21671407, places=6)

    def test_03_independent_experiment_consistency(self):
        """Verify cross-check across independent transfer and control experiments."""
        matrix = self.audit["independent_transfer_matrix"]
        # Package 113 sequential continuation (+2.008%)
        self.assertAlmostEqual(matrix["package113_sequential_continuation"]["pct_diff_tot"], 2.00803, places=3)
        # Package 115 direct transfer (+2.030%)
        self.assertAlmostEqual(matrix["package115_direct_transfer"]["pct_diff_tot"], 2.02983, places=3)
        # Package 117 same-mesh control (+0.00305%)
        self.assertAlmostEqual(matrix["package117_same_mesh_control"]["pct_diff_tot"], 0.003056, places=4)
        # Package 118 transfer from P117 (+2.030%)
        self.assertAlmostEqual(matrix["package118_transfer_from_p117"]["pct_diff_tot"], 2.02983, places=3)

    def test_04_h32_hypothesis_verdict(self):
        """Verify that Hypothesis H32 is quantitatively rejected."""
        self.assertEqual(self.audit["classification"], "H32_HYPOTHESIS_REJECTED")
        h32 = self.audit["h32_hypothesis_evaluation"]
        self.assertEqual(h32["hypothesis_verdict"], "H32_HYPOTHESIS_REJECTED")
        bounds = h32["mathematical_bound_analysis"]
        self.assertFalse(bounds["projection_energy_reduction_possible"])

    def test_05_governing_gate_retention(self):
        """Verify that STAGE_C1_2_STEP2_ENERGY_GATE_FAILED remains strictly retained."""
        self.assertEqual(self.audit["governing_gate_retained"], "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED")
        self.assertEqual(self.audit["p113_gate_valid_failure_retained"], "+2.00803158%")
        self.assertTrue(self.audit["h24_reference_audit_pending_retained"])

    def test_06_finding_clarity_and_length(self):
        """Verify finding description meets controller standards."""
        finding = self.audit["finding"]
        self.assertGreaterEqual(len(finding), 50)
        self.assertIn("H32", finding)
        self.assertIn("WITHHELD", finding)


if __name__ == "__main__":
    unittest.main()
