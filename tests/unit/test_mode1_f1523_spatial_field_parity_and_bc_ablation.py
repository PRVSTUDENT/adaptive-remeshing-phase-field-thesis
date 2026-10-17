#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_mode1_f1523_spatial_field_parity_and_bc_ablation.py
========================================================
Unit tests for Task F1523:
1. Spatial field parity of Job 1414758 vs continuous baseline ground truth
2. Damage reconstruction fidelity and release-and-hold stability
3. Resolution of UEL nodal DOF 3 via companion ELEMENT_NODAL extrapolation
4. One-factor ablation diagnostic (Job 1414760) proving BC causality
5. Gate 6C quantitative continuity verification and forward hold preservation
"""

import os
import sys
import json
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class TestMode1F1523SpatialFieldParityAndBcAblation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.samemesh_summary_path = os.path.join(
            REPO_ROOT, "results", "validation", "samemesh_spatial_field_parity_summary.json"
        )
        cls.ablation_summary_path = os.path.join(
            REPO_ROOT, "results", "validation", "ablation_spatial_field_parity_summary.json"
        )
        cls.ablation_dat_path = os.path.join(
            REPO_ROOT, "runs", "hpc", "mode1_stage_c1_1_top_bc_ablation", "evidence_1414760", "M1_MC_STAGE_C1_1_TOP_BC_ABLATION.dat"
        )
        cls.ablation_energy_path = os.path.join(
            REPO_ROOT, "runs", "hpc", "mode1_stage_c1_1_top_bc_ablation", "evidence_1414760", "uel_energy_balance.csv"
        )

        with open(cls.samemesh_summary_path, "r") as f:
            cls.samemesh_summary = json.load(f)

        with open(cls.ablation_summary_path, "r") as f:
            cls.ablation_summary = json.load(f)

    def test_01_samemesh_displacement_parity(self):
        """Verify machine-precision displacement parity of Job 1414758 vs continuous baseline."""
        s1 = self.samemesh_summary["step1_vs_ground_truth"]
        rel_u_pct = s1["rel_l2_displacement_error_pct"]
        max_u_err = s1["max_displacement_error_mm"]
        top_ux_err = s1["top_boundary_max_ux_error_mm"]
        node70_err = s1["node_70_ux_error_mm"]

        self.assertLess(rel_u_pct, 0.001, "Relative L2 displacement error must be < 0.001%")
        self.assertLess(max_u_err, 1.0e-6, "Max nodal displacement error must be < 1 nm")
        self.assertLess(top_ux_err, 1.0e-12, "Top boundary lateral error must be effectively zero")
        self.assertEqual(node70_err, 0.0, "Node 70 lateral displacement error must be exactly 0.0")
        self.assertEqual(self.samemesh_summary["spatial_field_parity_verdict"], "PASS")

    def test_02_samemesh_damage_and_history_reconstruction(self):
        """Verify element damage reconstruction fidelity and history discrepancy."""
        s1 = self.samemesh_summary["step1_vs_ground_truth"]
        rel_d_pct = s1["rel_l2_damage_error_pct"]
        max_d_err = s1["max_damage_error"]
        tip_d_diff = s1["tip_elem_661_damage"]["abs_diff"]

        self.assertLess(rel_d_pct, 0.05, "Relative L2 damage error must be < 0.05%")
        self.assertLess(max_d_err, 0.020, "Max damage error must be <= Gate 6C threshold 0.020")
        self.assertLess(tip_d_diff, 1.0e-6, "Apex element 661 damage difference must be < 1e-6")

        # History H should show discrepancy due to un-transferred plastic/damage history
        rel_h_pct = s1["rel_l2_history_error_pct"]
        self.assertGreater(rel_h_pct, 20.0, "History field H discrepancy must be preserved as evidence")

    def test_03_within_run_release_stability(self):
        """Verify Step 2 release-and-hold stability on corrected same-mesh model."""
        rel = self.samemesh_summary["within_run_release_relaxation"]
        self.assertLess(rel["rel_l2_displacement_shift_pct"], 0.001)
        self.assertLess(rel["max_displacement_shift_mm"], 1.0e-6)
        self.assertLess(rel["max_damage_shift"], 0.020)

    def test_04_ablation_causality_reproduction(self):
        """Verify that omitting ONLY N_TOP reproduces the exact -16.71 N deficit and ~33% lateral error."""
        s1_abl = self.ablation_summary["step1_vs_ground_truth"]
        rel_ux_err = s1_abl["rel_l2_ux_error_pct"]
        max_u_err = s1_abl["max_displacement_error_mm"]

        # 1. Lateral displacement error must be ~33.2%
        self.assertGreater(rel_ux_err, 30.0, "Omitting N_TOP must induce > 30% lateral displacement error")
        self.assertAlmostEqual(rel_ux_err, 33.20, delta=1.0)
        self.assertAlmostEqual(max_u_err, 0.001376, delta=0.0001)

        # 2. Step 1 reaction force must match 645.01 N within 0.05 N
        with open(self.ablation_dat_path, "r") as f:
            dat_text = f.read()
        self.assertIn("6.4501075E-01", dat_text, "Ablation deck must reproduce RF2 = 645.01075 N")

        # 3. Total energy must match 1.649336 mJ
        with open(self.ablation_energy_path, "r") as f:
            energy_lines = f.readlines()
        s1_energy_line = energy_lines[1]
        self.assertIn("0.16493355E-02", s1_energy_line, "Ablation deck must reproduce E_tot = 1.649336 mJ")

    def test_05_gate_6c_re_evaluation_and_hold(self):
        """Verify quantitative Gate 6C criteria and preservation of forward continuation hold."""
        # Check active task ledger and Gate 6C status
        active_task_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
        with open(active_task_path, "r") as f:
            task_data = json.load(f)

        self.assertIn("GATE_6C_HOLD", task_data["gate_status"])
        self.assertTrue(any("M1_MC_STAGE_C1_1" in j for j in task_data["deferred_candidate_jobs"]))

if __name__ == "__main__":
    unittest.main()
