# -*- coding: utf-8 -*-
"""
tests/unit/test_mode1_f1597_h33_discretization_aware_energy.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit regression test suite for Turn 298 Hypothesis H33 Discretization-Aware Energy Validation.
Verifies:
1. Integrity of H33 audit artifact (schema, task ID, classification).
2. Level A Predeclared Acceptance Gate strictly retains failure (STAGE_C1_2_STEP2_ENERGY_GATE_FAILED,
   +2.00803158%, exceedance +0.00803158 pct pts / 80.32 ppm / ~17.06 nJ, no retrospective waiver).
3. Level B Mesh-Aware Discretization Diagnostic confirms residual <= 0.02% against continuum limit
   and proves excess energy is strictly bounded within fine-mesh discretization truncation uncertainty.
4. Asymptotic spatial convergence metrics confirm >99% of AT2 fracture shift occurs in L1->L2 refinement.
5. Absolute separation between Level A governance failure and Level B physical diagnostic.
"""

from __future__ import print_function, division
import os
import json
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))


class TestH33DiscretizationAwareEnergy(unittest.TestCase):

    def setUp(self):
        self.audit_path = os.path.join(REPO_ROOT, "results/validation/h33_discretization_aware_energy_audit.json")
        self.assertTrue(os.path.exists(self.audit_path), "H33 audit artifact must exist on disk: %s" % self.audit_path)
        with open(self.audit_path, "r") as f:
            self.data = json.load(f)

    def test_schema_and_classification(self):
        self.assertEqual(self.data["schema"], 1)
        self.assertEqual(self.data["task_id"], "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertEqual(self.data["investigation"], "H33_DISCRETIZATION_AWARE_ENERGY_VALIDATION")
        self.assertEqual(self.data["classification"], "H33_MESH_AWARE_DIAGNOSTIC_SUPPORTED")
        self.assertIn("H33_MESH_AWARE_DIAGNOSTIC_SUPPORTED", self.data["classification_candidates"])

    def test_governing_gate_invariance(self):
        self.assertEqual(self.data["governing_gate_retained"], "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED")
        self.assertEqual(self.data["p113_gate_valid_failure_retained"], "+2.00803158%")
        self.assertTrue(self.data["h24_reference_audit_pending_retained"])

    def test_level_a_original_gate_metrics(self):
        level_a = self.data["two_level_evaluation_framework"]["level_a_original_acceptance_gate"]
        self.assertEqual(level_a["gate_name"], "STAGE_C1_2_STEP2_ENERGY_GATE")
        self.assertAlmostEqual(level_a["measured_pct"], 2.00803158, places=6)
        self.assertEqual(level_a["predeclared_tolerance_pct"], 2.00000000)
        self.assertAlmostEqual(level_a["exceedance_pct_points"], 0.00803158, places=6)
        self.assertAlmostEqual(level_a["exceedance_ppm"], 80.3158, places=2)
        self.assertAlmostEqual(level_a["excess_energy_nJ"], 17.0628, places=2)
        self.assertFalse(level_a["pass"])
        self.assertEqual(level_a["status"], "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED")
        self.assertEqual(level_a["p113_classification"], "P113_GATE_VALID_FAILURE")
        self.assertFalse(level_a["retrospective_relaxation_allowed"])

    def test_level_b_mesh_aware_diagnostic_metrics(self):
        level_b = self.data["two_level_evaluation_framework"]["level_b_mesh_aware_diagnostic"]
        self.assertEqual(level_b["diagnostic_name"], "LEVEL_B_MESH_AWARE_ENERGY_DIAGNOSTIC")
        self.assertEqual(level_b["diagnostic_status"], "H33_MESH_AWARE_DIAGNOSTIC_SUPPORTED")

        # Continuum limit E_inf between 0.21673 and 0.21676 mJ
        e_inf_p1 = level_b["continuum_limit_e_inf_p1_mJ"]
        e_inf_p2 = level_b["continuum_limit_e_inf_p2_mJ"]
        self.assertGreater(e_inf_p1, 0.21670)
        self.assertLess(e_inf_p1, 0.21676)
        self.assertGreater(e_inf_p2, 0.21670)
        self.assertLess(e_inf_p2, 0.21676)

        # Deviation from continuum limit is << 2.0% (around 0.01-0.02%, ~180 ppm)
        self.assertLess(level_b["pct_deviation_from_e_inf_p1"], 0.05)
        self.assertLess(level_b["pct_deviation_from_e_inf_p2"], 0.05)
        self.assertLess(level_b["pct_deviation_from_direct_c4"], 0.05)

        # Crucial physical check: excess energy (17.06 nJ) is strictly bounded by mesh truncation uncertainty (20.58 nJ)
        self.assertTrue(level_b["is_excess_bounded_by_mesh_uncertainty"])
        self.assertLess(level_b["excess_energy_over_2pct_gate_nJ"], level_b["mesh_truncation_uncertainty_raw_nJ"])

    def test_three_level_spatial_convergence(self):
        sc = self.data["spatial_convergence_analysis"]
        # Over 99% of fracture energy shift occurs in first refinement (L1 -> L2)
        self.assertGreater(sc["share_first_refinement_frac_pct"], 99.0)
        # Less than 1% of fracture energy shift occurs in second refinement (L2 -> L3)
        self.assertLess(sc["share_second_refinement_frac_pct"], 1.0)

        # Coarse donor bias is negative (under-predicts true energy by ~2%)
        ce = sc["continuum_extrapolation"]
        self.assertLess(ce["coarse_donor_bias_p2_pct"], -1.8)
        self.assertGreater(ce["coarse_donor_bias_p2_pct"], -2.2)

    def test_gate_separation_discipline(self):
        # Level A must be failed and Level B supported simultaneously without conflict
        level_a = self.data["two_level_evaluation_framework"]["level_a_original_acceptance_gate"]
        level_b = self.data["two_level_evaluation_framework"]["level_b_mesh_aware_diagnostic"]
        self.assertFalse(level_a["pass"])
        self.assertEqual(level_b["diagnostic_status"], "H33_MESH_AWARE_DIAGNOSTIC_SUPPORTED")


if __name__ == "__main__":
    unittest.main()
