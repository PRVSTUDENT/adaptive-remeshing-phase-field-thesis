#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for Task F1530:
Resolve Cycle 1 Fracture Energy Discrepancy & Execute Native-Mesh Uninterrupted Control.
"""

import os
import sys
import json
import hashlib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestMode1F1530UninterruptedControl(unittest.TestCase):

    def test_01_active_task_and_ledgers_integrity(self):
        active_task_path = REPO_ROOT / "project_coordination" / "ACTIVE_TASK.json"
        self.assertTrue(active_task_path.is_file())
        with open(active_task_path, "r", encoding="utf-8") as f:
            task = json.load(f)
        self.assertTrue(task["task_id"] in [
            "F1530-RESOLVE-CYCLE1-FRACTURE-ENERGY-DISCREPANCY-AND-UNINTERRUPTED-CONTROL",
            "F1531-EXECUTE-METHOD-C-CYCLE2-CONTINUATION",
            "F1531-INTEGRATE-PUBLISHED-STATE-TRANSFER-METHODS"
        ] or task["task_id"].startswith("F153"))

        # Check HPC Job Ledger
        job_ledger_path = REPO_ROOT / "project_coordination" / "HPC_JOB_LEDGER.csv"
        with open(job_ledger_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("1414784.mmaster02,M1_MC_STAGE_C1_2_UNINTERRUPTED_CONTROL", content)

    def test_02_package58_manifest_and_evidence_integrity(self):
        pkg_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "58_method_c_stage_c1_2_cycle1_uninterrupted_control"
        manifest_path = pkg_dir / "METHOD_C_STAGE_C1_2_UNINTERRUPTED_AUTHORIZATION.json"
        self.assertTrue(manifest_path.is_file())

        with open(manifest_path, "r", encoding="utf-8") as f:
            m = json.load(f)

        self.assertEqual(m["adapter"], "mode1-qualified-batch-v2")
        self.assertEqual(m["batch_name"], "MODE1_METHOD_C_STAGE_C1_2_UNINTERRUPTED_CONTROL")
        self.assertEqual(m["remote_run_dir"], "/scratch9/pr21vyci/runs/mode1_stage_c1_2_cycle1_uninterrupted_control")

        # Verify frozen UEL hash
        uel_hash = m["files"]["f42_mixed_uel.for"]
        self.assertEqual(uel_hash.lower(), "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6")

        # Verify on-disk deck hash matches manifest
        deck_path = pkg_dir / "M1_MC_STAGE_C1_2_UNINTERRUPTED_CONTROL.inp"
        self.assertTrue(deck_path.is_file())
        actual_deck_sha = hashlib.sha256(deck_path.read_bytes()).hexdigest().lower()
        self.assertEqual(m["files"]["M1_MC_STAGE_C1_2_UNINTERRUPTED_CONTROL.inp"].lower(), actual_deck_sha)

        # Verify evidence files exist
        ev_dir = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle1_uninterrupted_control" / "evidence_1414784"
        self.assertTrue(ev_dir.is_dir())
        for fname in ["stage_c1_2_control_extracted_results.json", "uel_energy_balance.csv", "pbs_execution.log",
                      "M1_MC_STAGE_C1_2_UNINTERRUPTED_CONTROL.sta", "three_way_trajectory_evaluation.json"]:
            fpath = ev_dir / fname
            self.assertTrue(fpath.is_file(), f"Missing evidence file: {fname}")
            self.assertGreater(fpath.stat().st_size, 0, f"Empty file: {fname}")

    def test_03_package58_input_deck_structure(self):
        pkg_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "58_method_c_stage_c1_2_cycle1_uninterrupted_control"
        deck_path = pkg_dir / "M1_MC_STAGE_C1_2_UNINTERRUPTED_CONTROL.inp"

        with open(deck_path, "r", encoding="utf-8") as f:
            deck_text = f.read()

        # Pristine initial state: no initial condition cards
        self.assertNotIn("*INITIAL CONDITIONS", deck_text.upper())

        # Correct 3-layer formulation
        self.assertIn("TYPE=U1", deck_text)
        self.assertIn("TYPE=U2", deck_text)
        self.assertIn("TYPE=U3", deck_text)
        self.assertIn("TYPE=U4", deck_text)
        self.assertIn("TYPE=CPE4", deck_text)
        self.assertIn("TYPE=CPE3", deck_text)

        # 2 Steps: Step 1 (u=0 -> 0.0010 mm) and Step 2 (u=0.0010 -> 0.0012 mm)
        self.assertIn("*STEP, NAME=Step-1-To-u0010", deck_text)
        self.assertIn("*STEP, NAME=Step-2-To-u0012", deck_text)

    def test_04_three_way_trajectory_metrics_and_gate6c_verification(self):
        eval_path = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle1_uninterrupted_control" / "evidence_1414784" / "three_way_trajectory_evaluation.json"
        self.assertTrue(eval_path.is_file())
        with open(eval_path, "r", encoding="utf-8") as f:
            res = json.load(f)

        s1 = {r["name"]: r for r in res["step1_checkpoint_u0010"]}
        s2 = {r["name"]: r for r in res["step2_terminal_u0012"]}

        # Step 1: Force continuity |Delta RF| <= 5.0 N
        self.assertLess(abs(s1["Reaction Force RF2"]["diff_B_vs_C"]), 5.0)
        # Step 1: Damage continuity |Delta d_max| <= 0.020
        self.assertLess(abs(s1["Maximum Damage d_max"]["diff_B_vs_C"]), 0.020)
        # Step 1: Total energy error <= 0.10%
        self.assertLess(abs(s1["Total Energy E_tot"]["pct_B_vs_C"]), 0.10)

        # Step 2 Terminal: Force continuity |Delta RF| <= 5.0 N (observed: 0.0036 N)
        self.assertLess(abs(s2["Reaction Force RF2"]["diff_B_vs_C"]), 5.0)
        self.assertLess(abs(s2["Reaction Force RF2"]["diff_B_vs_C"]), 0.01)

        # Step 2 Terminal: Damage continuity |Delta d_max| <= 0.020 (observed: 0.00082)
        self.assertLess(abs(s2["Maximum Damage d_max"]["diff_B_vs_C"]), 0.020)
        self.assertLess(abs(s2["Maximum Damage d_max"]["diff_B_vs_C"]), 0.001)

        # Step 2 Terminal: Elastic energy error <= 0.50% (observed: 0.002%)
        self.assertLess(abs(s2["Elastic Strain Energy E_elas"]["pct_B_vs_C"]), 0.50)

        # Step 2 Terminal: Total energy error <= 0.10% (observed: 0.0004%)
        self.assertLess(abs(s2["Total Energy E_tot"]["pct_B_vs_C"]), 0.10)

        # Resolution of history discrepancy:
        # A vs B has +21.25% elevation, proving it is mesh resolution
        # B vs C is only +0.17%, proving transfer conservation
        h_ab_pct = s2["Maximum History H_max"]["pct_A_vs_B"]
        h_bc_pct = s2["Maximum History H_max"]["pct_B_vs_C"]
        self.assertGreater(h_ab_pct, 20.0)
        self.assertLess(abs(h_bc_pct), 0.50)

    def test_05_fracture_energy_physical_scale_and_dissipation_monotonicity(self):
        eval_path = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle1_uninterrupted_control" / "evidence_1414784" / "three_way_trajectory_evaluation.json"
        with open(eval_path, "r", encoding="utf-8") as f:
            res = json.load(f)

        s2 = {r["name"]: r for r in res["step2_terminal_u0012"]}
        diff_efrac_mJ = abs(s2["Fracture Dissipation E_frac"]["diff_B_vs_C"])
        e_tot_mJ = s2["Total Energy E_tot"]["val_B"]

        # Absolute difference in fracture dissipation is on the order of picojoules (2.53e-6 mJ)
        self.assertLess(diff_efrac_mJ, 5.0e-6)  # < 5.0 pJ

        # Discrepancy as fraction of total energy is negligible (< 0.01%)
        frac_of_tot = (diff_efrac_mJ / e_tot_mJ) * 100.0
        self.assertLess(frac_of_tot, 0.01)


if __name__ == "__main__":
    unittest.main()
