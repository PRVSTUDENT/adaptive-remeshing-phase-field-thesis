#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn135_r7_strain_ratcheting.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 135)
Protocol Version: 2

Regression unit test suite verifying:
1. Bitwise preservation of production UEL (CE8D5EDC...).
2. Bitwise preservation of experimental UEL (E72E00D3...).
3. Stage-A discrete coupled equilibrium audit pass.
4. Package 108 Revision 7 execution and 18-step completion.
5. Mathematical and physical proof of constitutive strain localization ratcheting
   under fixed-displacement alternating minimization with iterative history updating.
"""

import unittest
import hashlib
import json
import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestTurn135R7StrainRatcheting(unittest.TestCase):

    def test_01_production_uel_bitwise_frozen(self):
        prod_uel = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
        self.assertTrue(prod_uel.exists(), "Production UEL not found")
        h = hashlib.sha256(prod_uel.read_bytes()).hexdigest().upper()
        self.assertEqual(h, "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6")

    def test_02_experimental_uel_bitwise_frozen(self):
        exp_uel = REPO_ROOT / "models/pandey_kumar_mode1/108_r7_c3_fixed_disp_am_cycles/f42_experimental_irreversible_uel.for"
        self.assertTrue(exp_uel.exists(), "Experimental UEL in R7 package not found")
        h = hashlib.sha256(exp_uel.read_bytes()).hexdigest().upper()
        self.assertEqual(h, "E72E00D338E355B370FC5EBABFE6679F49BC07458D333B642B593C6710B16DAD")

    def test_03_stage_a_stationarity_audit(self):
        audit_file = REPO_ROOT / "results/validation/mode1_f1597/stage_a_stationarity_audit.json"
        self.assertTrue(audit_file.exists(), "Stage-A stationarity audit artifact missing")
        with open(audit_file, "r") as fp:
            data = json.load(fp)
        telemetry = data["stage_a_telemetry"]
        self.assertTrue(telemetry["is_coupled_stationary"])
        self.assertTrue(telemetry["mech_residual_pass"])
        self.assertTrue(telemetry["free_phase_residual_pass"])
        self.assertTrue(telemetry["kkt_pass"])
        self.assertTrue(telemetry["healing_pass"])
        self.assertLessEqual(telemetry["max_mech_residual_kN"], 1e-4)
        self.assertLessEqual(telemetry["free_phase_residual_kN_mm"], 1e-6)

    def test_04_r7_metrics_and_ratcheting_proof(self):
        metrics_file = REPO_ROOT / "models/pandey_kumar_mode1/108_r7_c3_fixed_disp_am_cycles/r7_metrics.json"
        self.assertTrue(metrics_file.exists(), "R7 metrics file missing")
        with open(metrics_file, "r") as fp:
            data = json.load(fp)
        
        steps = data["steps"]
        self.assertEqual(len(steps), 18, "Expected 18 steps in R7 execution")
        
        # Verify H_max monotonically ratchets across mechanical steps
        h_vals = [
            steps["Inc1-Mech1"]["h_max_MPa"],
            steps["Cyc1-Mech"]["h_max_MPa"],
            steps["Cyc2-Mech"]["h_max_MPa"],
            steps["Cyc3-Mech"]["h_max_MPa"],
            steps["Cyc4-Mech"]["h_max_MPa"],
            steps["Cyc5-Mech"]["h_max_MPa"],
            steps["Cyc6-Mech"]["h_max_MPa"],
            steps["Cyc7-Mech"]["h_max_MPa"],
            steps["Cyc8-Mech"]["h_max_MPa"]
        ]
        for i in range(len(h_vals) - 1):
            self.assertGreater(h_vals[i+1], h_vals[i], f"H_max did not increase strictly at cycle {i+1}")
        
        self.assertAlmostEqual(h_vals[0], 5.2147, places=2)
        self.assertAlmostEqual(h_vals[-1], 10.2310, places=2)

    def test_05_r7_energy_balance_monotonic_decrease(self):
        csv_file = REPO_ROOT / "models/pandey_kumar_mode1/108_r7_c3_fixed_disp_am_cycles/uel_energy_balance.csv"
        self.assertTrue(csv_file.exists(), "R7 energy balance CSV missing")
        
        # Extract end-of-step energies
        step_end_energies = {}
        with open(csv_file, "r") as fp:
            reader = csv.reader(fp)
            header = next(reader)
            for row in reader:
                if not row or len(row) < 7:
                    continue
                step = int(row[0].strip())
                e_frac = float(row[5].strip())
                e_tot = float(row[6].strip())
                # Update with the latest increment of that step
                step_end_energies[step] = (e_frac, e_tot)
                    
        # Total energy must strictly decrease across steps 2 to 18 (Lyapunov property of alternating minimization)
        for s in range(2, 18):
            e_tot_curr = step_end_energies[s][1]
            e_tot_next = step_end_energies[s+1][1]
            self.assertLess(e_tot_next, e_tot_curr,
                            f"Total energy did not strictly decrease between step {s} ({e_tot_curr}) and {s+1} ({e_tot_next})")
            
        # Fracture energy must increase monotonically across cycles
        for s in range(2, 18):
            e_frac_curr = step_end_energies[s][0]
            e_frac_next = step_end_energies[s+1][0]
            self.assertGreaterEqual(e_frac_next, e_frac_curr - 1e-9,
                                    f"Fracture energy decreased between step {s} and {s+1}")


if __name__ == "__main__":
    unittest.main()
