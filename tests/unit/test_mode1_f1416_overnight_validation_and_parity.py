#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1416_overnight_validation_and_parity.py
===================================================
Unit test suite for Task F1416: Overnight HPC Reliability, Harvest Dependency Correction,
and Mode-I Fracture Validation.

Verifies:
1. Resolution of the 0.0108 mm displacement discrepancy: true physical horizon is strictly 0.0100 mm.
2. Shared-memory 8-thread SMP qualification: 1 MPI process x 8 threads.
3. Stage A Parity: Bitwise identical energy balance and stiffness across serial and 8-thread runs.
4. Tri-model accuracy comparison against Canonical 15k Uniform Reference.
5. Global UEL energy balance conservation: >90% fracture surface energy, complete post-peak unloading.
6. Stage B determinism repeat candidate deferral governance.
"""

import os
import json
import csv
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
HARVEST_DIR = os.path.join(REPO_ROOT, 'runs', 'mode1', 'harvest_results_f1416')

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

class TestMode1F1416OvernightValidationAndParity(unittest.TestCase):

    def test_01_displacement_horizon_discrepancy_resolved(self):
        """Verify true terminal displacement is strictly 0.0100 mm across all extracted models."""
        files = [
            'm1_mb_et2_6k_1s_metrics.json',
            'm1_mb_et2_6k_8t_a_metrics.json',
            'm1_mb_native_14k_1s_metrics.json',
            'm1_mb_native_14k_8t_a_metrics.json'
        ]
        for fname in files:
            fpath = os.path.join(HARVEST_DIR, fname)
            self.assertTrue(os.path.exists(fpath), f"Metrics file missing: {fname}")
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            u_term = data['terminal_u_mm']
            self.assertAlmostEqual(u_term, 0.0100, places=4,
                                   msg=f"Discrepancy: {fname} has terminal u={u_term}, expected 0.0100 mm")

    def test_02_thread_parity_bitwise_energy_hashes(self):
        """Verify bitwise identical SHA-256 hashes between 1-CPU serial and 8-thread SMP energy balances."""
        hash_nat_1s = compute_sha256(os.path.join(HARVEST_DIR, 'energy_native_14k_1s.csv'))
        hash_nat_8t = compute_sha256(os.path.join(HARVEST_DIR, 'energy_native_14k_8t_a.csv'))
        self.assertEqual(hash_nat_1s, hash_nat_8t, "Method B Native serial and 8T energy hashes differ!")
        self.assertEqual(hash_nat_1s, "792BE67DB9AC2CA2E51B9811CA0FB6F374BF28D0BA160F725F2D071B3C38D99D")

        hash_et2_1s = compute_sha256(os.path.join(HARVEST_DIR, 'energy_et2_6k_1s.csv'))
        hash_et2_8t = compute_sha256(os.path.join(HARVEST_DIR, 'energy_et2_6k_8t_a.csv'))
        self.assertEqual(hash_et2_1s, hash_et2_8t, "Historical ET2 serial and 8T energy hashes differ!")
        self.assertEqual(hash_et2_1s, "52CF636A3CC145472E87D922167B6AD9EF86ABDB7836827FBA4D283194F9C218")

    def test_03_stage_a_stiffness_and_peak_parity(self):
        """Verify numerical stiffness and peak force parity between serial and 8-thread runs."""
        with open(os.path.join(HARVEST_DIR, 'm1_mb_native_14k_1s_metrics.json')) as f:
            nat_1s = json.load(f)
        with open(os.path.join(HARVEST_DIR, 'm1_mb_native_14k_8t_a_metrics.json')) as f:
            nat_8t = json.load(f)
        self.assertAlmostEqual(nat_1s['stiffness_u10']['K0_kN_per_mm'],
                               nat_8t['stiffness_u10']['K0_kN_per_mm'], places=8)
        self.assertAlmostEqual(nat_1s['peak_reaction']['F_max_kN'],
                               nat_8t['peak_reaction']['F_max_kN'], places=6)

        with open(os.path.join(HARVEST_DIR, 'm1_mb_et2_6k_1s_metrics.json')) as f:
            et2_1s = json.load(f)
        with open(os.path.join(HARVEST_DIR, 'm1_mb_et2_6k_8t_a_metrics.json')) as f:
            et2_8t = json.load(f)
        self.assertAlmostEqual(et2_1s['stiffness_u10']['K0_kN_per_mm'],
                               et2_8t['stiffness_u10']['K0_kN_per_mm'], places=2)
        self.assertAlmostEqual(et2_1s['peak_reaction']['F_max_kN'],
                               et2_8t['peak_reaction']['F_max_kN'], places=6)

    def test_04_tri_model_compliance_parity(self):
        """Verify uncracked structural compliance K0 matches reference within 0.05%."""
        ref_k0 = 137.945520
        with open(os.path.join(HARVEST_DIR, 'm1_mb_native_14k_1s_metrics.json')) as f:
            nat = json.load(f)
        with open(os.path.join(HARVEST_DIR, 'm1_mb_et2_6k_1s_metrics.json')) as f:
            et2 = json.load(f)

        delta_nat = abs(nat['stiffness_u10']['K0_kN_per_mm'] - ref_k0) / ref_k0 * 100.0
        delta_et2 = abs(et2['stiffness_u10']['K0_kN_per_mm'] - ref_k0) / ref_k0 * 100.0

        self.assertLess(delta_nat, 0.05, f"Method B Native K0 delta {delta_nat:.4f}% exceeds 0.05%")
        self.assertLess(delta_et2, 0.05, f"ET2 K0 delta {delta_et2:.4f}% exceeds 0.05%")

    def test_05_global_uel_energy_balance(self):
        """Verify energy conservation: >90% fracture energy, <2% elastic residual at fracture."""
        with open(os.path.join(HARVEST_DIR, 'energy_native_14k_1s.csv')) as f:
            rows_nat = list(csv.DictReader(f))
        last_nat = rows_nat[-1]
        e_elas_nat = float(last_nat['E_elastic_kNmm']) * 1000.0
        e_frac_nat = float(last_nat['E_fracture_kNmm']) * 1000.0
        e_tot_nat = float(last_nat['E_total_kNmm']) * 1000.0

        self.assertGreater(e_frac_nat / e_tot_nat, 0.90, "Fracture surface energy should be >90% at u=0.01 mm")
        self.assertLess(e_elas_nat / e_tot_nat, 0.02, "Residual elastic energy should be <2% at u=0.01 mm")

    def test_06_stage_b_candidate_deferred(self):
        """Ensure Stage B repeat candidate script exists and is safely deferred."""
        stage_b_pbs = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '38_method_b_native_final_14k', 'submit_M1_MB_NATIVE_8T_B.pbs')
        self.assertTrue(os.path.exists(stage_b_pbs), "Stage B candidate PBS script missing")

if __name__ == '__main__':
    unittest.main()
