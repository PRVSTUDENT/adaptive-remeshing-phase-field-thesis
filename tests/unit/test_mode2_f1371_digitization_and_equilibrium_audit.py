import unittest
import os
import numpy as np
import pandas as pd
import re

class TestMode2F1371DigitizationAndEquilibriumAudit(unittest.TestCase):
    """
    Unit test suite for Task F1371: Mode-II Digitization Audit,
    Global Equilibrium Verification, and ET2-ET3 Scientific Preparation.
    """

    def setUp(self):
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.lit_csv = os.path.join(self.repo_root, "references", "derived", "pandey_kumar_2025_fig13a_authoritative_redigitized.csv")
        self.et3_inp = os.path.join(self.repo_root, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "m2_corrected_remesh", "M2_CORRECTED_JOB2_ET3PCT_STABILIZED.inp")
        self.et3_rf_csv = os.path.join(self.repo_root, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "m2_corrected_remesh", "job2_rf_active_history.csv")
        self.coarse_rf_csv = os.path.join(self.repo_root, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "mode2_j1_coarse_retest_rf_history.csv")
        self.damage_sum_csv = os.path.join(self.repo_root, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "m2_corrected_remesh", "mode2_damage_evolution_summary.csv")
        self.fig_pdf = os.path.join(self.repo_root, "results", "figures", "mode2", "fig_mode2_f1371_digitization_audit_and_work_integration.pdf")

    def test_digitization_authoritative_dataset_and_work_integration(self):
        """Verify authoritative Fig. 13(a) dataset, peak force, and work integration."""
        self.assertTrue(os.path.exists(self.lit_csv), f"Literature CSV must exist at {self.lit_csv}")
        df = pd.read_csv(self.lit_csv)
        self.assertEqual(len(df), 801, "Authoritative curve must have exactly 801 data points")
        
        u_mm = df['displacement_mm'].values
        u_um = df['displacement_um'].values
        rf_adapt = df['proposed_pfm_N'].values
        
        # Peak force check
        idx_peak = np.argmax(rf_adapt)
        self.assertAlmostEqual(rf_adapt[idx_peak], 365.74, places=1)
        self.assertAlmostEqual(u_um[idx_peak], 8.30, places=1)
        
        # External work over [0, 16.0] um
        W_16 = np.trapezoid(rf_adapt, u_mm)
        self.assertAlmostEqual(W_16, 3.516651, places=3)
        
        # Historical partial integration check at 15.28 um
        mask_1528 = u_um <= 15.28
        W_1528 = np.trapezoid(rf_adapt[mask_1528], u_mm[mask_1528])
        self.assertAlmostEqual(W_1528, 3.378, delta=0.01)

    def test_global_equilibrium_and_deck_boundary_mechanics(self):
        """Verify boundary value problem constraints, thickness, and equation coupling."""
        self.assertTrue(os.path.exists(self.et3_inp), f"ET3 INP deck must exist at {self.et3_inp}")
        with open(self.et3_inp, 'r') as f:
            text = f.read()
            
        # Section thickness
        self.assertIn("*Solid Section, elset=All_elem, material=UMAT_MAT\n1.0", text)
        
        # UEL properties (l0=0.015, Gc=0.0027, E=210.0, nu=0.3, k=1e-7, NPHYS=21063)
        self.assertIn("210.0, 0.3, 0.0027, 0.015, 1.0E-7, 21063.", text)
        
        # Boundary conditions
        self.assertIn("N_BOTTOM, 1, 2, 0.0", text)
        self.assertIn("N_TOP, 2, 2, 0.0", text)
        self.assertIn("N_RP, 1, 1, 0.0100", text)
        self.assertIn("N_RP, 1, 1, 0.0200", text)
        
        # Exactly 97 top surface nodes coupled to RP 999999
        eq_matches = re.findall(r"\*Equation\s*\n\s*2\s*\n\s*(\d+),\s*1,\s*1\.0,\s*999999,\s*1,\s*-1\.0", text)
        self.assertEqual(len(eq_matches), 97, "Exactly 97 top surface nodes must be coupled to RP 999999")

    def test_postpeak_reloading_and_crack_deceleration_physics(self):
        """Verify damage progression, crack velocity deceleration, and intact ligament."""
        self.assertTrue(os.path.exists(self.damage_sum_csv), f"Damage summary must exist at {self.damage_sum_csv}")
        df = pd.read_csv(self.damage_sum_csv).drop_duplicates(subset=['ux_prescribed_um'])
        
        u = df['ux_prescribed_um'].values
        h_lig_um = df['ligament_height_mm'].values * 1000.0
        a_crack = (0.500 - df['ligament_height_mm'].values) * 1000.0 / np.sin(np.radians(58.04))
        da_du = np.gradient(a_crack, u)
        
        # Rapid propagation in softening
        max_da_du = np.max(da_du)
        self.assertGreater(max_da_du, 100.0, "Rapid crack speed must exceed 100 mm/mm")
        
        # Deceleration near base boundary
        terminal_da_du = da_du[-1]
        self.assertLess(terminal_da_du, 20.0, "Terminal crack speed must drop below 20 mm/mm")
        
        # Terminal ligament
        self.assertAlmostEqual(h_lig_um[-1], 56.32, delta=0.5)

    def test_multiscale_gap_closure_and_work_reconciliation(self):
        """Verify coarse vs adapted gap closure and figure generation."""
        self.assertTrue(os.path.exists(self.et3_rf_csv), "ET3 RF CSV must exist")
        self.assertTrue(os.path.exists(self.coarse_rf_csv), "Coarse RF CSV must exist")
        self.assertTrue(os.path.exists(self.fig_pdf), "Publication figure PDF must exist")
        
        df_et3 = pd.read_csv(self.et3_rf_csv)
        df_coarse = pd.read_csv(self.coarse_rf_csv)
        
        F_max_et3 = np.max(df_et3['rf_N'].values)
        F_max_coarse = np.max(df_coarse['rf1_kN'].values) * 1000.0
        F_max_lit = 365.74
        
        gap_initial = F_max_coarse - F_max_lit
        gap_adapted = F_max_et3 - F_max_lit
        gap_closure = (1.0 - gap_adapted / gap_initial) * 100.0
        
        self.assertAlmostEqual(F_max_et3, 412.21, delta=0.5)
        self.assertAlmostEqual(F_max_coarse, 514.51, delta=0.5)
        self.assertAlmostEqual(gap_closure, 68.76, delta=0.5)

if __name__ == '__main__':
    unittest.main()
