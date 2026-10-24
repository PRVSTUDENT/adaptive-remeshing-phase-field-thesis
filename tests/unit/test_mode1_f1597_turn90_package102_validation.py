#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn90_package102_validation.py
Comprehensive regression tests for Package 102 simulation outputs and diagnostic audits.
"""
import unittest
import json
import csv
import hashlib
from pathlib import Path
import numpy as np

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG102_DIR = REPO_ROOT / "models/pandey_kumar_mode1/102_c5_coupled_staggered_reequilibration"

class TestPackage102CoupledState(unittest.TestCase):
    def setUp(self):
        self.uel_path = PKG102_DIR / "f42_mixed_uel.for"
        self.report_path = PKG102_DIR / "pdas_trial_evaluation.json"
        self.kkt_path = REPO_ROOT / "results/validation/mode1_f1597/turn90_pkg102_kkt_stationarity.json"
        self.energy_csv = PKG102_DIR / "uel_energy_balance.csv"
        self.extracted_csv = PKG102_DIR / "M1_C5_PACKAGE102_STAGGERED_REEQUIL_extracted.csv"
        self.state_table = PKG102_DIR / "candidate_c5_frame7_mapped_state_table.csv"
        self.d_opt_npy = PKG102_DIR / "turn89_c5_staggered_d_opt.npy"

    def test_01_frozen_uel_integrity(self):
        """Verify 100% bitwise frozen UEL hash."""
        expected_hash = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        actual_hash = hashlib.sha256(self.uel_path.read_bytes()).hexdigest().upper()
        self.assertEqual(actual_hash, expected_hash)

    def test_02_strict_zero_healing_and_overshoot(self):
        """Verify strict zero damage healing and zero overshoot in Abaqus execution."""
        with open(self.report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["healing_nodes_count"], 0)
        self.assertEqual(data["overshoot_nodes_count"], 0)
        self.assertTrue(data["zero_healing_passed"])
        self.assertTrue(data["zero_overshoot_passed"])
        self.assertGreaterEqual(data["min_delta_d"], -1e-6)
        self.assertLessEqual(data["max_d"], 1.0 + 1e-6)

    def test_03_reaction_force_continuity_evaluation(self):
        """Evaluate reaction force continuity against 5% gate."""
        with open(self.report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        rf2_N = data["rf2_N"]
        donor_rf2_N = data["donor_rf2_N"]
        rf_error_pct = data["rf_error_pct"]

        self.assertAlmostEqual(donor_rf2_N, 112.97, places=2)
        self.assertAlmostEqual(rf2_N, 98.7915, places=2)
        # Error is -12.55%, exceeding the 5.0% threshold
        self.assertFalse(data["force_continuity_passed"])
        self.assertGreater(abs(rf_error_pct), 5.0)

    def test_04_fracture_energy_continuity_evaluation(self):
        """Evaluate Bourdin AT2 fracture energy continuity against 2% gate."""
        with open(self.report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        e_frac_mj = data["e_frac_mJ"]
        donor_e_frac_mj = data["donor_e_frac_mJ"]
        e_frac_error_pct = data["e_frac_error_pct"]

        self.assertAlmostEqual(donor_e_frac_mj, 0.137737, places=4)
        self.assertAlmostEqual(e_frac_mj, 0.149309, places=4)
        # Error is +8.40%, exceeding the 2.0% threshold
        self.assertFalse(data["fracture_energy_passed"])
        self.assertGreater(abs(e_frac_error_pct), 2.0)

    def test_05_kkt_stationarity_audit(self):
        """Verify KKT complementarity and free-set residual."""
        with open(self.kkt_path, "r", encoding="utf-8") as f:
            kkt = json.load(f)
        self.assertEqual(kkt["n_nodes"], 4610)
        self.assertEqual(kkt["set_U_count"], 60)
        self.assertEqual(kkt["set_L_count"], 1327)
        self.assertEqual(kkt["set_A_count"], 3223)
        self.assertEqual(kkt["set_U_count"] + kkt["set_L_count"] + kkt["set_A_count"], 4610)

        # Lower-bound multiplier validity
        self.assertLessEqual(kkt["max_kkt_viol_L"], 1e-6)
        # Upper-bound multiplier validity
        self.assertLessEqual(kkt["max_kkt_viol_U"], 1e-6)
        # Free-set residual
        self.assertAlmostEqual(kkt["norm_R_A_kN_mm"], 1.8267e-06, places=8)

    def test_06_governed_gate_c1_2_maintained_not_qualified(self):
        """Verify Gate C1-2 is strictly maintained as NOT_QUALIFIED."""
        with open(self.report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["governed_gate_c1_2"], "NOT_QUALIFIED")
        self.assertFalse(data["verification_passed"])

if __name__ == "__main__":
    unittest.main()
