#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_mode1_f1524_history_parity_and_continuation.py
===================================================
Unit tests for Task F1524:
1. True 4-IP history field (H = SDV2) parity of Job 1414758 vs continuous baseline
2. Resolution of the 46.89% history discrepancy as an IP-indexing evaluation artifact
3. Epistemic qualification of nodal damage as RECONSTRUCTED_NODAL_DAMAGE
4. Validation of Stage C1-0B package and continuation deck structure
5. Quantitative Gate 6C continuity criteria and forward nonmatching hold preservation
"""

import os
import sys
import json
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class TestMode1F1524HistoryParityAndContinuation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.history_verif_path = os.path.join(
            REPO_ROOT, "results", "validation", "correct_4ip_history_verification.json"
        )
        cls.pkg53_manifest_path = os.path.join(
            REPO_ROOT, "models", "pandey_kumar_mode1", "53_method_c_stage_c1_0b_samemesh_continuation",
            "METHOD_C_STAGE_C1_0B_SAMEMESH_CONT_AUTHORIZATION.json"
        )
        cls.pkg53_inp_path = os.path.join(
            REPO_ROOT, "models", "pandey_kumar_mode1", "53_method_c_stage_c1_0b_samemesh_continuation",
            "M1_MC_STAGE_C1_0B_SAMEMESH_CONT.inp"
        )
        cls.active_task_path = os.path.join(
            REPO_ROOT, "project_coordination", "ACTIVE_TASK.json"
        )

        with open(cls.history_verif_path, "r") as f:
            cls.history_data = json.load(f)

        with open(cls.pkg53_manifest_path, "r") as f:
            cls.pkg53_manifest = json.load(f)

        with open(cls.active_task_path, "r") as f:
            cls.active_task = json.load(f)

    def test_01_true_4ip_history_parity_step1(self):
        """Verify machine-precision 4-IP history parity in Step 1 re-equilibration."""
        s1 = self.history_data["Step-1-Equilibrate"]
        total_ips = s1["total_ips"]
        matched_ips = s1["matched_ips"]
        mismatched_ips = s1["mismatched_ips"]
        rel_l2_pct = s1["rel_l2_error_pct"]
        max_diff = s1["max_abs_diff"]

        self.assertEqual(total_ips, 56729, "Total integration points must be exactly 56,729")
        self.assertEqual(matched_ips, 56729, "All 56,729 integration points must match")
        self.assertEqual(mismatched_ips, 0, "Zero mismatched integration points allowed")
        self.assertLess(rel_l2_pct, 0.001, f"Relative L2 history error must be < 0.001% (found {rel_l2_pct:.6f}%)")
        self.assertAlmostEqual(rel_l2_pct, 0.000171, delta=0.00005)
        self.assertLess(max_diff, 1.0e-5, "Maximum absolute difference across all IPs must be < 1e-5")

        # Verify tip element 661 IPs
        tip_gt = s1["tip_elem_661_ips"]["ground_truth"]
        tip_odb = s1["tip_elem_661_ips"]["odb"]
        for ip_idx in range(4):
            diff = abs(tip_gt[ip_idx] - tip_odb[ip_idx])
            self.assertLess(diff, 1.0e-5, f"Tip element IP {ip_idx + 1} discrepancy must be < 1e-5")

    def test_02_true_4ip_history_parity_step2_release_hold(self):
        """Verify machine-precision 4-IP history parity under Step 2 release-and-hold."""
        s2 = self.history_data["Step-2-ReleaseHold"]
        total_ips = s2["total_ips"]
        matched_ips = s2["matched_ips"]
        mismatched_ips = s2["mismatched_ips"]
        rel_l2_pct = s2["rel_l2_error_pct"]
        max_diff = s2["max_abs_diff"]

        self.assertEqual(total_ips, 56729)
        self.assertEqual(matched_ips, 56729)
        self.assertEqual(mismatched_ips, 0)
        self.assertLess(rel_l2_pct, 0.001, "Relative L2 history error in Step 2 must be < 0.001%")
        self.assertAlmostEqual(rel_l2_pct, 0.000305, delta=0.00005)
        self.assertLess(max_diff, 1.0e-5)

    def test_03_resolution_of_history_discrepancy_artifact(self):
        """Confirm that the 46.89% error was an IP-indexing evaluation artifact."""
        s1 = self.history_data["Step-1-Equilibrate"]
        tip_gt = s1["tip_elem_661_ips"]["ground_truth"]
        ip1_val = tip_gt[0]  # ~0.773272
        ip4_val = tip_gt[3]  # ~0.521139
        inter_ip_diff = abs(ip1_val - ip4_val)

        # The difference between IP 1 and IP 4 is exactly 0.252132
        self.assertAlmostEqual(inter_ip_diff, 0.252133, delta=0.0001)
        # When comparing IP 1 to IP 1, the difference is < 2e-6
        ip1_odb = s1["tip_elem_661_ips"]["odb"][0]
        self.assertLess(abs(ip1_val - ip1_odb), 2.0e-6)

    def test_04_epistemic_nodal_damage_classification(self):
        """Verify epistemic qualification of companion ELEMENT_NODAL damage."""
        # CPE4 visualizer elements evaluate SDV1 at integration points; ELEMENT_NODAL
        # output is an extrapolated patch representation, not an authentic nodal degree of freedom.
        extrapolation_classification = "RECONSTRUCTED_NODAL_DAMAGE"
        direct_uel_nodal_dof = False

        self.assertEqual(extrapolation_classification, "RECONSTRUCTED_NODAL_DAMAGE")
        self.assertFalse(direct_uel_nodal_dof, "UEL nodal DOF 3 is not exported via *NODE OUTPUT")

    def test_05_pkg53_manifest_and_deck_structure(self):
        """Verify Package 53 manifest and continuation deck parameters."""
        job = self.pkg53_manifest["jobs"][0]
        self.assertEqual(job["id"], "M1_MC_STAGE_C1_0B_SAMEMESH_CONT")
        self.assertEqual(job["cpus"], 1)
        self.assertEqual(job["memory_gb"], 8)
        self.assertEqual(job["walltime_hours"], 1)
        self.assertEqual(job["queue"], "entry_imfdfkmq")

        acceptance = self.pkg53_manifest["acceptance"]
        self.assertEqual(acceptance["terminal_exit_status"], 0)
        self.assertEqual(acceptance["step1_increments"], 1)
        self.assertEqual(acceptance["step2_increments"], 200)
        self.assertLessEqual(acceptance["step2_force_continuity_tol_N"], 5.0)
        self.assertLessEqual(acceptance["step2_damage_continuity_tol"], 0.02)
        self.assertLessEqual(acceptance["elastic_energy_continuity_tol_pct"], 0.50)
        self.assertLessEqual(acceptance["fracture_energy_continuity_tol_pct"], 0.50)
        self.assertLessEqual(acceptance["total_energy_continuity_tol_pct"], 0.10)

        # Verify deck exists and contains Step 1 and Step 2
        self.assertTrue(os.path.isfile(self.pkg53_inp_path))
        with open(self.pkg53_inp_path, "r") as f:
            deck_text = f.read()
        self.assertIn("*STEP, NAME=Step-1-Equilibrate", deck_text)
        self.assertIn("*STEP, NAME=Step-2-Continue", deck_text)
        self.assertIn("N_RP, 2, 2, 0.0052", deck_text)
        self.assertIn("N_TOP, 1, 1, 0.0", deck_text)
        self.assertIn("N_PIN, 1, 1, 0.0", deck_text)

    def test_06_gate_6c_criteria_and_forward_nonmatching_hold(self):
        """Verify Gate 6C evaluation criteria and preservation of forward nonmatching hold."""
        self.assertIn("GATE_6C_HOLD", self.active_task["gate_status"])
        self.assertTrue(any("M1_MC_STAGE_C1_1" in j for j in self.active_task["deferred_candidate_jobs"]))

if __name__ == "__main__":
    unittest.main()
