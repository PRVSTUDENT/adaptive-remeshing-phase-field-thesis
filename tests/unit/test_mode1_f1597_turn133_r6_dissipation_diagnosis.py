#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn133_r6_dissipation_diagnosis.py
Unit test suite for Turn 133: Diagnostic localization of Package 108 R6 fracture energy over-dissipation.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
"""

import json
import unittest
import hashlib
from pathlib import Path

class TestR6DissipationDiagnosis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path("D:/Master thesis/Adaptive remeshing")
        cls.prod_uel = cls.repo_root / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
        cls.diag_path = cls.repo_root / "results/validation/mode1_f1597/r6_energy_dissipation_diagnosis.json"
        
        cls.assertTrue(cls.prod_uel.exists(), "Production UEL missing")
        cls.assertTrue(cls.diag_path.exists(), "Diagnosis artifact missing")
        
        with open(cls.diag_path, "r") as f:
            cls.diag = json.load(f)

    def test_01_production_uel_bitwise_frozen(self):
        expected_hash = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        actual_hash = hashlib.sha256(self.prod_uel.read_bytes()).hexdigest().upper()
        self.assertEqual(actual_hash, expected_hash, "Production UEL hash altered!")

    def test_02_diagnosis_structure_and_16_steps(self):
        self.assertEqual(self.diag["schema"], 1)
        self.assertEqual(len(self.diag["step_analysis"]), 16)
        self.assertEqual(self.diag["first_departure"]["step_index"], 3)
        self.assertEqual(self.diag["first_departure"]["step_name"], "Inc1-Phase1")

    def test_03_first_departure_localization(self):
        dep = self.diag["first_departure"]
        self.assertAlmostEqual(dep["ef_mJ"], 0.0649785, places=5)
        self.assertGreater(dep["ef_mJ"], 0.063652, "First departure did not exceed tolerance")
        self.assertGreater(dep["excess_pct"], 4.0)

    def test_04_h_max_escalation_mechanism(self):
        steps = {s["step_name"]: s for s in self.diag["step_analysis"]}
        
        # Mech1 steps (displacement advance) show tiny H_max changes (~0.005 MPa)
        delta_h_disp1 = steps["Inc1-Mech1"]["h_max_MPa"] - steps["Stage-A"]["h_max_MPa"]
        self.assertLess(delta_h_disp1, 0.010, f"Displacement advance H change excessive: {delta_h_disp1}")

        # Mech2 steps (mechanical re-equilibration against softened phase) show large H_max surges (>0.35 MPa)
        delta_h_reequil1 = steps["Inc1-Mech2"]["h_max_MPa"] - steps["Inc1-Phase1"]["h_max_MPa"]
        self.assertGreater(delta_h_reequil1, 0.350, f"Re-equilibration H surge insufficient: {delta_h_reequil1}")

        # Final H_max in R6 reaches 7.847 MPa (+49.7% above Turn 107 benchmark 5.241 MPa)
        final_h = steps["Inc5-Mech2"]["h_max_MPa"]
        bench_h = self.diag["turn_107_benchmark"]["forward_max_H_MPa"]
        self.assertGreater(final_h, 7.80)
        self.assertGreater((final_h - bench_h) / bench_h, 0.45)

    def test_05_dissipation_monotonicity_satisfied(self):
        steps = self.diag["step_analysis"]
        # In all phase relaxation and re-equilibration intervals, Delta E_total <= 0
        for s in steps:
            if "Phase" in s["step_name"] or "Mech2" in s["step_name"]:
                # total energy change from preceding step
                idx = s["step_index"] - 1
                delta_et = s["e_total_mJ"] - steps[idx-1]["e_total_mJ"]
                self.assertLessEqual(delta_et, 1e-6, f"Positive dissipation increment at {s['step_name']}: {delta_et}")

if __name__ == "__main__":
    unittest.main()
