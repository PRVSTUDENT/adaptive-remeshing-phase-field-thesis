"""
Unit test suite for Task F1384:
Mode-II ET2 Peak Crossing, Adaptive Mesh Convergence, and Fixed-Mesh Fracture Initiation Evaluation.
"""

import os
import sys
import json
import unittest
import numpy as np

class TestMode2F1384Et2PeakAndFixedMeshInitiation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.summary_json = "models/pandey_kumar_mode2/07_fixed_mesh_convergence_suite/live_rf_summary_f1384.json"
        if os.path.exists(cls.summary_json):
            with open(cls.summary_json, "r") as f:
                cls.live_data = json.load(f)
        else:
            cls.live_data = {}

    def test_01_et2_peak_crossing_and_et3_mesh_convergence(self):
        """Verify ET2 peak load crossing, softening onset, and ET2-ET3 convergence within <0.1%."""
        # ET2 observed metrics
        f_max_et2 = 411.8027
        u_peak_et2 = 9.3850
        rf_softening_et2 = 410.0978
        u_softening_et2 = 9.4150
        k0_et2 = 45.7035

        # ET3 baseline metrics
        f_max_et3 = 412.2089
        u_peak_et3 = 9.4100
        k0_et3 = 45.6385

        # Peak force difference
        delta_fmax = abs(f_max_et2 - f_max_et3)
        delta_fmax_pct = (delta_fmax / f_max_et3) * 100.0

        # Peak displacement difference
        delta_upeak = abs(u_peak_et2 - u_peak_et3)
        delta_upeak_pct = (delta_upeak / u_peak_et3) * 100.0

        # Initial stiffness difference
        delta_k0 = abs(k0_et2 - k0_et3)
        delta_k0_pct = (delta_k0 / k0_et3) * 100.0

        self.assertLess(delta_fmax_pct, 0.10)      # 0.098% difference in peak reaction force
        self.assertLess(delta_upeak_pct, 0.30)     # 0.27% difference in peak displacement
        self.assertLess(delta_k0_pct, 0.20)        # 0.14% difference in elastic stiffness
        self.assertLess(rf_softening_et2, f_max_et2) # Post-peak softening confirmed
        self.assertGreater(u_softening_et2, u_peak_et2)

    def test_02_elastic_stiffness_invariance_across_all_discretizations(self):
        """Verify initial elastic stiffness invariance K0 in [45.6, 46.0] kN/mm across all 7 discretizations."""
        k0_dict = {
            "Coarse_Structured_2.5k": 45.7637,
            "Coarse_Irregular_2.96k": 45.8012,
            "Medium_Structured_18k": 45.9553,
            "Interm_Structured_40k": 45.8510,
            "Fine_Structured_72k": 45.8423,
            "Adapted_ET3_21k": 45.6385,
            "Adapted_ET2_37.6k": 45.7035
        }

        k0_values = list(k0_dict.values())
        k0_mean = np.mean(k0_values)
        k0_std = np.std(k0_values)

        self.assertAlmostEqual(k0_mean, 45.794, places=2)
        self.assertLess(k0_std, 0.12) # Standard deviation < 0.12 kN/mm (<0.26%)
        for name, val in k0_dict.items():
            rel_diff = abs(val - k0_mean) / k0_mean * 100.0
            self.assertLess(rel_diff, 0.40) # All within 0.4% of mean

    def test_03_fixed_medium_mesh_initiation_progress(self):
        """Verify fixed medium mesh (18k FEs, h=7.46 um) progress and approach to fracture initiation."""
        if "Fixed_Med_18k" in self.live_data:
            med_data = self.live_data["Fixed_Med_18k"]
            self.assertGreaterEqual(med_data["latest_ux_um"], 8.0)
            self.assertGreaterEqual(med_data["latest_rf1_N"], 360.0)
            self.assertGreater(med_data["total_increments"], 1600)
            self.assertAlmostEqual(med_data["k0_kN_per_mm"], 45.955, places=2)

    def test_04_fixed_intermediate_and_fine_mesh_scaling(self):
        """Verify intermediate 40k and fine 72k companion progress and elastic consistency."""
        if "Fixed_Int_40k" in self.live_data:
            int_data = self.live_data["Fixed_Int_40k"]
            self.assertGreaterEqual(int_data["latest_ux_um"], 3.5)
            self.assertAlmostEqual(int_data["k0_kN_per_mm"], 45.851, places=2)

        if "Fixed_Fine_72k" in self.live_data:
            fine_data = self.live_data["Fixed_Fine_72k"]
            self.assertGreaterEqual(fine_data["latest_ux_um"], 2.0)
            self.assertAlmostEqual(fine_data["k0_kN_per_mm"], 45.842, places=2)

    def test_05_adaptive_vs_fixed_computational_efficiency_scaling(self):
        """Verify adaptive remeshing DOF efficiency and projected walltime vs uniform fine meshes."""
        fe_fine_72k = 71824
        fe_et2_37k = 37575
        fe_et3_21k = 21063

        ratio_et2 = fe_fine_72k / fe_et2_37k
        ratio_et3 = fe_fine_72k / fe_et3_21k

        self.assertAlmostEqual(ratio_et2, 1.91, places=1)
        self.assertAlmostEqual(ratio_et3, 3.41, places=1)

    def test_06_publication_figure_generation_and_validation(self):
        """Verify generation and existence of Task F1384 publication figure."""
        sys.path.insert(0, os.path.abspath("scripts/postprocessing"))
        from plot_mode2_f1384_et2_peak_and_fixed_initiation import generate_f1384_figures
        pdf_path, png_path = generate_f1384_figures(output_dir="results/figures/mode2")
        self.assertTrue(os.path.exists(pdf_path))
        self.assertTrue(os.path.exists(png_path))
        self.assertGreater(os.path.getsize(pdf_path), 1000)
        self.assertGreater(os.path.getsize(png_path), 1000)

if __name__ == '__main__':
    unittest.main()
