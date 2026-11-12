#!/usr/bin/env python3
"""Unit tests for Task F1722: Bounded Causal-Isolation Diagnostic Pilot Execution Results and Forensics.

Verifies:
1. Existence and integrity of primary solver receipts (.sta, .msg, .dat, pbs_execution.log).
2. Solver termination with Exit Code 0, 157 increments, and exactly 0 cutbacks.
3. Telemetry extraction JSON and CSV data integrity.
4. Static equilibrium balance: |RF_RP + sum(RF_bottom)| <= 1e-6 kN across all frames.
5. Elastic stiffness K0 ~ 175.79 kN/mm and peak load F_peak ~ 0.940 kN.
6. Localized damage nucleation and hierarchy: Ligament 3 (0.5425) > Ligament 2 > Ligament 4 > Ligament 1.
7. Falsification verdict CONDITIONAL_PASS for Picard operator-split hypothesis F1721-H1-R1.
8. Generation and existence of publication figures.
"""

import json
from pathlib import Path
import unittest
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / 'results/validation'
RECEIPTS_DIR = RESULTS_DIR / 'f1722_solver_receipts'
TELEMETRY_JSON = RESULTS_DIR / 'f1722_causal_pilot_telemetry.json'
CURVES_CSV = RESULTS_DIR / 'f1722_causal_pilot_curves.csv'
FIG_DIR = ROOT / 'figures/pandey_kumar_fig22_25_reproduction'
THESIS_DIR = ROOT / 'MA_AdaptiveRemeshing_Report_2026'


class TestF1722CausalPilotResults(unittest.TestCase):

    def test_01_primary_solver_receipts_existence(self):
        receipt_files = [
            RECEIPTS_DIR / 'M1_PK_F1722_CAUSAL_PILOT.sta',
            RECEIPTS_DIR / 'M1_PK_F1722_CAUSAL_PILOT.msg',
            RECEIPTS_DIR / 'M1_PK_F1722_CAUSAL_PILOT.dat',
            RECEIPTS_DIR / 'pbs_execution.log',
            RECEIPTS_DIR / 'f1720_call_order.txt'
        ]
        for f in receipt_files:
            self.assertTrue(f.is_file(), f"Missing receipt file: {f}")
            self.assertGreater(f.stat().st_size, 0, f"Receipt file {f} is empty")

    def test_02_solver_exit_code_and_cutbacks(self):
        log_text = (RECEIPTS_DIR / 'pbs_execution.log').read_text(encoding='utf-8', errors='replace')
        self.assertIn("Abaqus JOB M1_PK_F1722_CAUSAL_PILOT COMPLETED", log_text)
        self.assertIn("=== Abaqus Finished with Exit Code: 0 ===", log_text)

        msg_text = (RECEIPTS_DIR / 'M1_PK_F1722_CAUSAL_PILOT.msg').read_text(encoding='utf-8', errors='replace')
        self.assertIn("TOTAL OF        157  INCREMENTS", msg_text)
        self.assertIn("0  CUTBACKS IN AUTOMATIC INCREMENTATION", msg_text)
        self.assertIn("0  ERROR MESSAGES", msg_text)

        sta_text = (RECEIPTS_DIR / 'M1_PK_F1722_CAUSAL_PILOT.sta').read_text(encoding='utf-8', errors='replace')
        self.assertIn("THE ANALYSIS HAS COMPLETED SUCCESSFULLY", sta_text)

    def test_03_telemetry_schema_and_falsification_verdict(self):
        self.assertTrue(TELEMETRY_JSON.is_file(), f"Missing telemetry: {TELEMETRY_JSON}")
        with open(TELEMETRY_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)

        fals = data['falsification_evaluation']
        self.assertEqual(fals['verdict'], 'CONDITIONAL_PASS')
        self.assertEqual(fals['hypothesis'], 'F1721-H1-R1 (Picard Staggered Operator-Split Decoupling via Committed State)')
        self.assertAlmostEqual(fals['f1720_stall_threshold_mm'], 0.0056644953, places=6)
        self.assertAlmostEqual(fals['f1722_target_displacement_mm'], 0.0058, places=4)

        solv = data['solver_execution']
        self.assertEqual(solv['exit_code'], 0)
        self.assertEqual(solv['total_cutbacks'], 0)
        self.assertEqual(solv['pbs_job_id'], '1422895.mmaster02')

    def test_04_mechanical_properties_and_stiffness(self):
        with open(TELEMETRY_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)

        phys = data['physical_results']
        k0 = phys['initial_elastic_stiffness_kN_per_mm']
        self.assertGreater(k0, 174.0)
        self.assertLess(k0, 177.0)

        f_peak = phys['peak_force_kN']
        self.assertGreater(f_peak, 0.93)
        self.assertLess(f_peak, 1.05)

        u_term = phys['terminal_displacement_mm']
        self.assertGreaterEqual(u_term, 0.00580)

    def test_05_static_equilibrium_force_balance(self):
        self.assertTrue(CURVES_CSV.is_file(), f"Missing curves CSV: {CURVES_CSV}")
        df = pd.read_csv(CURVES_CSV)
        self.assertGreater(len(df), 150)

        # Check equilibrium: rf_rp_kN vs rf_bottom_kN
        # Note: frame 0 is unloaded initial state
        diff = (df['rf_rp_kN'] - df['rf_bottom_kN']).abs()
        max_diff = diff.max()
        self.assertLess(max_diff, 1e-6, f"Static force balance violation: max diff = {max_diff} kN")

    def test_06_ligament_damage_hierarchy(self):
        with open(TELEMETRY_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)

        phys = data['physical_results']
        d_lig3 = phys['terminal_damage_lig3']
        d_lig2 = phys['terminal_damage_lig2']
        d_lig1 = phys['terminal_damage_lig1']
        d_lig4 = phys['terminal_damage_lig4']

        # Critical Ligament 3 (h3 <-> h4) dominates with d > 0.50
        self.assertGreater(d_lig3, 0.50)
        # Damage hierarchy: Lig 3 > Lig 2 > Lig 4 > Lig 1
        self.assertGreater(d_lig3, d_lig2)
        self.assertGreater(d_lig2, d_lig4)
        self.assertGreater(d_lig4, d_lig1)

        # Max damage element is in Ligament 3
        coords = phys['terminal_max_damage_coords']
        self.assertGreaterEqual(coords[0], 0.63)
        self.assertLessEqual(coords[0], 0.70)
        self.assertGreaterEqual(coords[1], 0.48)
        self.assertLessEqual(coords[1], 0.56)

    def test_07_publication_figures_exist(self):
        figs = [
            RESULTS_DIR / 'f1722_causal_pilot_validation.png',
            RESULTS_DIR / 'f1722_ligament_damage_evolution.png',
            FIG_DIR / 'f1722_causal_pilot_validation.png',
            FIG_DIR / 'f1722_causal_pilot_validation.pdf',
            FIG_DIR / 'f1722_ligament_damage_evolution.pdf',
            THESIS_DIR / 'f1722_causal_pilot_validation.pdf',
            THESIS_DIR / 'f1722_ligament_damage_evolution.pdf'
        ]
        for fig in figs:
            self.assertTrue(fig.is_file(), f"Missing publication figure: {fig}")
            self.assertGreater(fig.stat().st_size, 0, f"Empty figure file: {fig}")


if __name__ == '__main__':
    unittest.main()
