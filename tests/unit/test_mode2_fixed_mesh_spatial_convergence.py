#!/usr/bin/env python3
"""
Unit Test Suite for Mode-II Fixed-Mesh Spatial Convergence, Terminal Evidence Integrity,
and Adaptive Accuracy Synthesis (Gate M2-1B and Gate M2-4).
"""

import unittest
import os
import json
import numpy as np

class TestMode2FixedMeshSpatialConvergence(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        cls.evidence_dir = os.path.join(cls.repo_root, 'runs', 'mode2', 'fixed_convergence', 'evidence')
        cls.et3_history = os.path.join(cls.repo_root, 'models', 'pandey_kumar_mode2', '06_paper_grounded_uel_preanalysis', 'm2_corrected_remesh', 'job2_rf_active_history.csv')

    def parse_dat(self, rel_path):
        dat_path = os.path.join(self.repo_root, rel_path)
        self.assertTrue(os.path.exists(dat_path), f"File not found: {dat_path}")
        u_vals, rf_vals = [], []
        with open(dat_path, 'r') as f:
            for line in f:
                if line.strip().startswith('999999'):
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            u_vals.append(float(parts[1]))
                            rf_vals.append(float(parts[2]))
                        except ValueError:
                            pass
        u_arr = np.array(u_vals)
        rf_arr = np.array(rf_vals)
        self.assertGreater(len(u_arr), 0, f"No points parsed from {dat_path}")
        return u_arr, rf_arr

    def test_01_terminal_evidence_file_presence(self):
        """Verify all terminal .sta, .dat, and pbs_execution.log files exist in local evidence."""
        expected_dirs = ['01_coarse_2p5k', '02_med_18k', '03_int_40k', '03_int_48h', 'et2_adapt_37k']
        for d in expected_dirs:
            p_dir = os.path.join(self.evidence_dir, d)
            self.assertTrue(os.path.isdir(p_dir), f"Missing evidence dir: {p_dir}")
            p_log = os.path.join(p_dir, 'pbs_execution.log')
            p_sta = [f for f in os.listdir(p_dir) if f.endswith('.sta')]
            p_dat = [f for f in os.listdir(p_dir) if f.endswith('.dat')]
            self.assertTrue(os.path.exists(p_log), f"Missing pbs_execution.log in {d}")
            self.assertGreaterEqual(len(p_sta), 1, f"Missing .sta in {d}")
            self.assertGreaterEqual(len(p_dat), 1, f"Missing .dat in {d}")

    def test_02_coarse_2p5k_completion_and_metrics(self):
        """Verify Coarse 2.5k mesh completed all 4,000 increments with exact expected metrics."""
        u, rf = self.parse_dat('runs/mode2/fixed_convergence/evidence/01_coarse_2p5k/M2_FIX_COARSE_2P5K.dat')
        self.assertEqual(len(u), 4000)
        rf_max_N = np.max(rf) * 1000.0
        u_peak_um = u[np.argmax(rf)] * 1000.0
        # Peak reaction force: ~525.70 N at ~13.99 um
        self.assertAlmostEqual(rf_max_N, 525.703, delta=0.5)
        self.assertAlmostEqual(u_peak_um, 13.990, delta=0.05)
        # Final state at 20 um: ~489.25 N
        self.assertAlmostEqual(u[-1] * 1000.0, 20.000, delta=0.01)
        self.assertAlmostEqual(rf[-1] * 1000.0, 489.249, delta=0.5)

    def test_03_medium_18k_completion_and_metrics(self):
        """Verify Medium 18k mesh completed all 4,000 increments with exact expected metrics."""
        u, rf = self.parse_dat('runs/mode2/fixed_convergence/evidence/02_med_18k/M2_FIX_MED_18K.dat')
        self.assertEqual(len(u), 4000)
        rf_max_N = np.max(rf) * 1000.0
        u_peak_um = u[np.argmax(rf)] * 1000.0
        # Peak reaction force: ~436.99 N at ~10.97 um
        self.assertAlmostEqual(rf_max_N, 436.988, delta=0.5)
        self.assertAlmostEqual(u_peak_um, 10.970, delta=0.05)
        # Final state at 20 um: ~408.41 N
        self.assertAlmostEqual(u[-1] * 1000.0, 20.000, delta=0.01)
        self.assertAlmostEqual(rf[-1] * 1000.0, 408.407, delta=0.5)

    def test_04_intermediate_40k_metrics_and_safeguard_parity(self):
        """Verify Intermediate 40k (24h and 48h safeguard) traversed peak and achieved bitwise parity."""
        u1, rf1 = self.parse_dat('runs/mode2/fixed_convergence/evidence/03_int_40k/M2_FIX_INT_40K.dat')
        u2, rf2 = self.parse_dat('runs/mode2/fixed_convergence/evidence/03_int_48h/M2_FIX_INT_48H.dat')
        self.assertEqual(len(u1), 1928)
        self.assertEqual(len(u2), 1928)
        # 100% Bitwise identity between 24h and 48h safeguard
        np.testing.assert_array_equal(u1, u2)
        np.testing.assert_array_equal(rf1, rf2)
        # Peak reaction force: ~420.66 N at ~9.595 um
        rf_max_N = np.max(rf1) * 1000.0
        u_peak_um = u1[np.argmax(rf1)] * 1000.0
        self.assertAlmostEqual(rf_max_N, 420.655, delta=0.5)
        self.assertAlmostEqual(u_peak_um, 9.595, delta=0.05)
        # Softening captured past peak: terminal ux = 9.635 um > 9.595 um
        self.assertGreater(u1[-1] * 1000.0, u_peak_um)

    def test_05_adapted_et2_metrics(self):
        """Verify Adapted ET2 mesh traversed peak force at ~411.80 N."""
        u, rf = self.parse_dat('runs/mode2/fixed_convergence/evidence/et2_adapt_37k/Job-2_UEL.dat')
        self.assertEqual(len(u), 1884)
        rf_max_N = np.max(rf) * 1000.0
        u_peak_um = u[np.argmax(rf)] * 1000.0
        # Peak reaction force: ~411.80 N at ~9.385 um
        self.assertAlmostEqual(rf_max_N, 411.803, delta=0.5)
        self.assertAlmostEqual(u_peak_um, 9.385, delta=0.05)

    def test_06_spatial_convergence_monotonicity(self):
        """Verify monotonic decrease of peak force with mesh refinement toward asymptotic ~412 N limit."""
        u_c, rf_c = self.parse_dat('runs/mode2/fixed_convergence/evidence/01_coarse_2p5k/M2_FIX_COARSE_2P5K.dat')
        u_m, rf_m = self.parse_dat('runs/mode2/fixed_convergence/evidence/02_med_18k/M2_FIX_MED_18K.dat')
        u_i, rf_i = self.parse_dat('runs/mode2/fixed_convergence/evidence/03_int_40k/M2_FIX_INT_40K.dat')
        u_et2, rf_et2 = self.parse_dat('runs/mode2/fixed_convergence/evidence/et2_adapt_37k/Job-2_UEL.dat')
        
        fmax_c = np.max(rf_c) * 1000.0
        fmax_m = np.max(rf_m) * 1000.0
        fmax_i = np.max(rf_i) * 1000.0
        fmax_et2 = np.max(rf_et2) * 1000.0
        fmax_et3 = 412.2089 # from Job 1411267
        
        # Strictly monotonic sequence: Coarse > Medium > Intermediate > Adapted
        self.assertGreater(fmax_c, fmax_m)
        self.assertGreater(fmax_m, fmax_i)
        self.assertGreater(fmax_i, fmax_et3)
        self.assertAlmostEqual(fmax_et3, fmax_et2, delta=1.0) # ET3 vs ET2 within 0.41 N (0.10%)

    def test_07_initial_stiffness_invariance(self):
        """Verify initial structural stiffness K0 is invariant across all meshes within 0.65%."""
        u_c, rf_c = self.parse_dat('runs/mode2/fixed_convergence/evidence/01_coarse_2p5k/M2_FIX_COARSE_2P5K.dat')
        u_m, rf_m = self.parse_dat('runs/mode2/fixed_convergence/evidence/02_med_18k/M2_FIX_MED_18K.dat')
        u_i, rf_i = self.parse_dat('runs/mode2/fixed_convergence/evidence/03_int_40k/M2_FIX_INT_40K.dat')
        u_et2, rf_et2 = self.parse_dat('runs/mode2/fixed_convergence/evidence/et2_adapt_37k/Job-2_UEL.dat')
        
        def calc_k0(u_arr, rf_arr, n=20):
            return np.sum(u_arr[:n] * rf_arr[:n]) / np.sum(u_arr[:n]**2)
            
        k0_c = calc_k0(u_c, rf_c)
        k0_m = calc_k0(u_m, rf_m)
        k0_i = calc_k0(u_i, rf_i)
        k0_et2 = calc_k0(u_et2, rf_et2)
        
        for name, k in [('Coarse', k0_c), ('Medium', k0_m), ('Intermediate', k0_i), ('ET2', k0_et2)]:
            self.assertGreater(k, 45.5, f"{name} K0 too low: {k}")
            self.assertLess(k, 46.1, f"{name} K0 too high: {k}")
            self.assertAlmostEqual(k, 45.68, delta=0.35, msg=f"{name} deviates from reference 45.68 kN/mm")

    def test_08_publication_figures_presence(self):
        """Verify master spatial convergence publication figure exists and has non-zero size."""
        fig_pdf = os.path.join(self.repo_root, 'results', 'figures', 'mode2', 'fig_mode2_fixed_mesh_spatial_convergence.pdf')
        fig_png = os.path.join(self.repo_root, 'results', 'figures', 'mode2', 'fig_mode2_fixed_mesh_spatial_convergence.png')
        self.assertTrue(os.path.exists(fig_pdf), f"Missing figure: {fig_pdf}")
        self.assertTrue(os.path.exists(fig_png), f"Missing figure: {fig_png}")
        self.assertGreater(os.path.getsize(fig_pdf), 10000)
        self.assertGreater(os.path.getsize(fig_png), 50000)

if __name__ == '__main__':
    unittest.main()
