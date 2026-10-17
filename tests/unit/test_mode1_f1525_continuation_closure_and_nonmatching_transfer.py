#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_mode1_f1525_continuation_closure_and_nonmatching_transfer.py
================================================================
Unit tests for Task F1525:
1. Stage C1-0B same-mesh continuation quantitative closure across all 200 increments
2. Separation of physical mesh discretization gap (~8.64 N) from state transfer mapping error
3. Stage C1-1 nonmatching mesh state transfer monotonic relaxation and physical continuity criteria
4. Package 54/54B input deck structure, boundary conditions, and companion UMAT constants
5. Cryptographic integrity of harvested HPC solver evidence (Jobs 1414761 and 1414764)
"""

import os
import sys
import json
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class TestMode1F1525ContinuationClosureAndNonmatchingTransfer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.c1_0b_summary_path = os.path.join(
            REPO_ROOT, "results", "validation", "stage_c1_0b_continuation_summary.json"
        )
        cls.c1_1_summary_path = os.path.join(
            REPO_ROOT, "results", "validation", "stage_c1_1_nm_summary.json"
        )
        cls.pkg54b_inp_path = os.path.join(
            REPO_ROOT, "models", "pandey_kumar_mode1", "54b_method_c_stage_c1_1_nonmatching_transfer",
            "M1_MC_STAGE_C1_1_NM_CORRECTED_V2.inp"
        )
        cls.pkg54b_manifest_path = os.path.join(
            REPO_ROOT, "models", "pandey_kumar_mode1", "54b_method_c_stage_c1_1_nonmatching_transfer",
            "METHOD_C_STAGE_C1_1_NM_CORRECTED_V2_AUTHORIZATION.json"
        )

        with open(cls.c1_0b_summary_path, "r") as f:
            cls.c1_0b_summary = json.load(f)

        with open(cls.c1_1_summary_path, "r") as f:
            cls.c1_1_summary = json.load(f)

        with open(cls.pkg54b_manifest_path, "r") as f:
            cls.pkg54b_manifest = json.load(f)

    def test_01_stage_c1_0b_same_mesh_continuation_closure(self):
        """Verify complete quantitative closure of Stage C1-0B same-mesh continuation."""
        summary = self.c1_0b_summary
        eval_6c = summary["gate_6c_evaluation"]
        self.assertEqual(eval_6c["same_mesh_continuation_verdict"], "STAGE_C1_0B_SAME_MESH_CONTINUATION_PASS")

        # Step 1 re-equilibration parity
        s1 = summary["handoff_step1"]
        self.assertLess(s1["delta_rf_N"], 5.0, "Step 1 RF error must be <= 5.0 N")
        self.assertAlmostEqual(s1["delta_rf_N"], 0.00015, delta=0.0001)
        self.assertLess(s1["e_tot_err_pct"], 0.10, "Step 1 total energy error must be <= 0.10%")
        self.assertLess(s1["delta_d_max"], 0.020, "Step 1 d_max difference must be <= 0.020")

        # Step 2 terminal continuation parity (inc 200, u = 0.0052 mm)
        s2_term = summary["step2_continuation"]["terminal_inc_200"]
        self.assertEqual(s2_term["rf_cont_N"], 685.45427)
        self.assertEqual(s2_term["rf_base_N"], 685.45427)
        self.assertEqual(s2_term["delta_rf_N"], 0.0, "Step 2 inc 200 RF must match to all recorded digits")
        self.assertEqual(s2_term["d_max_cont"], 0.3611296)
        self.assertEqual(s2_term["d_max_base"], 0.3611296)
        self.assertEqual(s2_term["delta_d_max"], 0.0, "Step 2 inc 200 d_max must match to all recorded digits")

        # Step 2 max energy errors across 200 increments
        s2 = summary["step2_continuation"]
        self.assertLess(s2["max_e_elas_err_pct"], 0.50)
        self.assertLess(s2["max_e_frac_err_pct"], 0.50)
        self.assertLess(s2["max_e_tot_err_pct"], 0.10)

    def test_02_physical_discretization_vs_transfer_error_separation(self):
        """Verify rigorous separation of physical discretization error from transfer error."""
        c1_1 = self.c1_1_summary
        donor = c1_1["coarse_donor"]
        base = c1_1["fine_baseline"]
        gap = c1_1["discretization_gap"]

        self.assertEqual(donor["elements"], 2906)
        self.assertEqual(base["elements"], 14483)

        # Inherent discretization difference: fine mesh is stiffer and higher energy
        expected_rf_gap = base["rf_N"] - donor["rf_N"]
        self.assertAlmostEqual(gap["delta_rf_N"], expected_rf_gap, delta=0.01)
        self.assertGreater(gap["delta_rf_N"], 8.0, "Physical mesh difference must be > 8 N")

        # Transfer mapping error itself is minuscule
        t_map = c1_1["transfer_mapping"]
        self.assertLess(t_map["u_L2_error_pct"], 0.05, "L2 displacement mapping error must be < 0.05%")
        self.assertLess(t_map["integrated_damage_error_pct"], 0.05, "Integrated damage error must be < 0.05%")
        self.assertGreaterEqual(t_map["min_H_kN_per_mm2"], 0.0, "Internal history must be non-negative everywhere")

    def test_03_stage_c1_1_nonmatching_transfer_relaxation_and_continuity(self):
        """Verify Stage C1-1 monotonic relaxation and physical continuity criteria."""
        c1_1 = self.c1_1_summary
        self.assertEqual(c1_1["overall_verdict"], "STAGE_C1_1_NONMATCHING_TRANSFER_PASS")
        self.assertEqual(c1_1["job_id"], "1414764.mmaster02")

        # Step 2 monotonic relaxation
        curve = c1_1["step2_release_and_hold"]["rf_relaxation_curve_N"]
        self.assertEqual(len(curve), 10, "Step 2 must have exactly 10 release-and-hold increments")
        for i in range(len(curve) - 1):
            self.assertGreater(curve[i], curve[i + 1], f"RF must relax monotonically at increment {i + 1}")

        # Terminal physical continuity checks
        eval_crit = c1_1["acceptance_evaluation"]
        self.assertEqual(eval_crit["force_continuity"]["verdict"], "PASS")
        self.assertLess(eval_crit["force_continuity"]["value_N"], 5.0)

        self.assertEqual(eval_crit["total_energy_continuity"]["verdict"], "PASS")
        self.assertLess(eval_crit["total_energy_continuity"]["value_pct"], 0.10)

        self.assertEqual(eval_crit["peak_damage_continuity"]["verdict"], "PASS")
        self.assertLess(eval_crit["peak_damage_continuity"]["value"], 0.0200)

        self.assertEqual(eval_crit["history_monotonicity"]["verdict"], "PASS")

    def test_04_package54b_deck_structure_and_boundary_conditions(self):
        """Verify Package 54B deck structure, boundary conditions, and companion UMAT constants."""
        self.assertTrue(os.path.isfile(self.pkg54b_inp_path), "Package 54B deck must exist")

        with open(self.pkg54b_inp_path, "r") as f:
            lines = f.readlines()

        content = "".join(lines)

        # Correct boundary conditions
        self.assertIn("N_TOP, 1, 1, 0.0", content)
        self.assertIn("N_PIN, 1, 1, 0.0", content)
        self.assertIn("*STEP, NAME=Step-1-Equilibrate", content)
        self.assertIn("*STEP, NAME=Step-2-ReleaseHold", content)
        self.assertNotIn("NLGEOM=YES", content)

        # Companion UMAT constants with NPHYS=14483
        self.assertIn("*USER MATERIAL, CONSTANTS=3", content)
        self.assertIn("210.0, 0.3, 14483.0", content)

    def test_05_harvested_evidence_files_exist(self):
        """Verify harvested solver evidence exists locally with non-zero size."""
        evidence_dir_1414761 = os.path.join(
            REPO_ROOT, "runs", "hpc", "mode1_stage_c1_0b_samemesh_continuation", "evidence_1414761"
        )
        evidence_dir_1414764 = os.path.join(
            REPO_ROOT, "runs", "hpc", "mode1_stage_c1_1_nonmatching_transfer_corrected_v2", "evidence_1414764"
        )

        for fname in ["M1_MC_STAGE_C1_0B_SAMEMESH_CONT.sta", "uel_energy_balance.csv"]:
            p = os.path.join(evidence_dir_1414761, fname)
            self.assertTrue(os.path.isfile(p), f"Missing {p}")
            self.assertGreater(os.path.getsize(p), 0)

        for fname in ["M1_MC_STAGE_C1_1_NM_CORRECTED_V2.sta", "M1_MC_STAGE_C1_1_NM_CORRECTED_V2.dat", "uel_energy_balance.csv"]:
            p = os.path.join(evidence_dir_1414764, fname)
            self.assertTrue(os.path.isfile(p), f"Missing {p}")
            self.assertGreater(os.path.getsize(p), 0)

if __name__ == "__main__":
    unittest.main()
