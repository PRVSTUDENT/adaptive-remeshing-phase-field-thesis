#!/usr/bin/env python3
"""
Unit Test Suite for Gate-6B Mode-I Stage 14U-Y:
Adaptive Spatial-Field and Energy Sensitivity Closure Audit
"""

import unittest
import os
import json

class TestStage14UYAdaptiveSpatialSensitivity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.repo_root = r"D:\Master thesis\Adaptive remeshing"
        cls.report_json_path = os.path.join(
            cls.repo_root,
            "models",
            "pandey_kumar_mode1",
            "25_stage14_adaptive_candidate_14k",
            "MODE1_STAGE14UY_ADAPTIVE_SPATIAL_SENSITIVITY_REPORT.json"
        )
        cls.report_md_path = os.path.join(
            cls.repo_root,
            "models",
            "pandey_kumar_mode1",
            "25_stage14_adaptive_candidate_14k",
            "MODE1_STAGE14UY_ADAPTIVE_SPATIAL_SENSITIVITY_REPORT.md"
        )
        cls.fig_energy_pdf = os.path.join(
            cls.repo_root,
            "results",
            "figures",
            "mode1_gate6b",
            "fig_mode1_stage14uy_adaptive_energy_comparison.pdf"
        )
        cls.fig_fu_pdf = os.path.join(
            cls.repo_root,
            "results",
            "figures",
            "mode1_gate6b",
            "fig_mode1_stage14uy_adaptive_fu_comparison.pdf"
        )
        
        self = cls
        self.assertTrue(os.path.exists(cls.report_json_path), f"Missing report JSON: {cls.report_json_path}")
        with open(cls.report_json_path, 'r') as f:
            cls.data = json.load(f)

    def test_01_report_structure_and_task_id(self):
        """Verify report metadata and task ID alignment."""
        self.assertEqual(self.data["task_id"], "F1208-GATE6B-STAGE14UY-ADAPTIVE-SPATIAL-ENERGY-SENSITIVITY-AUDIT-20261004")
        self.assertEqual(self.data["agent"], "gemini-antigravity")
        self.assertIn("mesh_provenance", self.data)
        self.assertIn("matched_comparison_table", self.data)
        self.assertIn("scientific_synthesis", self.data)

    def test_02_mesh_provenance_and_corridor_density(self):
        """Verify exact mesh provenance and corridor element density metrics."""
        prov = self.data["mesh_provenance"]
        
        # Package 24
        p24 = prov["package_24"]
        self.assertEqual(p24["total_base_elements"], 13897)
        self.assertEqual(p24["corridor_elements"], 1696)
        self.assertAlmostEqual(p24["corridor_share_pct"], 12.203, places=2)
        self.assertAlmostEqual(p24["h_min_um"], 0.868, places=3)
        self.assertAlmostEqual(p24["h_median_corridor_um"], 2.586, places=3)
        
        # Stage 14
        p25 = prov["stage_14"]
        self.assertEqual(p25["total_base_elements"], 14483)
        self.assertEqual(p25["corridor_elements"], 8326)
        self.assertAlmostEqual(p25["corridor_share_pct"], 57.488, places=2)
        self.assertAlmostEqual(p25["h_min_um"], 0.760, places=3)
        self.assertAlmostEqual(p25["h_median_corridor_um"], 2.058, places=3)

        # Concentration ratio
        conc_ratio = p25["corridor_elements"] / p24["corridor_elements"]
        self.assertAlmostEqual(conc_ratio, 4.909, places=2)

    def test_03_pre_peak_mechanical_and_energy_parity(self):
        """Verify exact mechanical stiffness, peak force, and pre-peak energy parity."""
        table = self.data["matched_comparison_table"]
        
        # u = 1.0 um
        st_1um = next(s for s in table if abs(s["u_target_mm"] - 0.0010) < 1e-5)
        self.assertAlmostEqual(st_1um["package_24"]["e_frac_mJ"], 0.000056, places=5)
        self.assertAlmostEqual(st_1um["stage_14"]["e_frac_mJ"], 0.000056, places=5)
        self.assertAlmostEqual(st_1um["package_24"]["e_elas_mJ"], 0.068934, places=4)
        self.assertAlmostEqual(st_1um["stage_14"]["e_elas_mJ"], 0.068944, places=4)
        
        # u = 3.0 um
        st_3um = next(s for s in table if abs(s["u_target_mm"] - 0.0030) < 1e-5)
        self.assertAlmostEqual(st_3um["package_24"]["e_frac_mJ"], 0.004541, places=5)
        self.assertAlmostEqual(st_3um["stage_14"]["e_frac_mJ"], 0.004543, places=5)

        # u = 5.0 um
        st_5um = next(s for s in table if abs(s["u_target_mm"] - 0.0050) < 1e-5)
        self.assertAlmostEqual(st_5um["package_24"]["e_frac_mJ"], 0.036780, places=5)
        self.assertAlmostEqual(st_5um["stage_14"]["e_frac_mJ"], 0.036786, places=5)

        # Peak force parity (< 0.25% difference)
        prov = self.data["mesh_provenance"]
        fmax_p24 = prov["package_24"]["F_max_kN"]
        fmax_p25 = prov["stage_14"]["F_max_kN"]
        delta_fmax_pct = (fmax_p25 - fmax_p24) / fmax_p25 * 100.0
        self.assertLess(abs(delta_fmax_pct), 0.25)

    def test_04_u_0065_energy_discrepancy_resolution(self):
        """Verify exact diagnosis of u = 0.0065 mm energy discrepancy."""
        table = self.data["matched_comparison_table"]
        st_65 = next(s for s in table if abs(s["u_target_mm"] - 0.0065) < 1e-5)
        
        # Package 24: Total energy = 2.6874 mJ, but split into 1.9033 mJ elas + 0.7842 mJ frac
        p24 = st_65["package_24"]
        self.assertAlmostEqual(p24["e_total_mJ"], 2.687448, places=4)
        self.assertAlmostEqual(p24["e_elas_mJ"], 1.903275, places=4)
        self.assertAlmostEqual(p24["e_frac_mJ"], 0.784172, places=4)

        # Stage 14: Total energy = 2.2902 mJ, with 0.0067 mJ elas + 2.2835 mJ frac
        p25 = st_65["stage_14"]
        self.assertAlmostEqual(p25["e_total_mJ"], 2.290170, places=4)
        self.assertAlmostEqual(p25["e_elas_mJ"], 0.006703, places=4)
        self.assertAlmostEqual(p25["e_frac_mJ"], 2.283468, places=4)

        # Proves Stage 14 is fully severed while Package 24 retains high elastic strain
        self.assertLess(p25["e_elas_mJ"], 0.010)
        self.assertGreater(p24["e_elas_mJ"], 1.50)

    def test_05_governed_verdicts_and_classification(self):
        """Verify governed verdicts and methodological classifications."""
        synth = self.data["scientific_synthesis"]
        self.assertEqual(
            synth["methodological_classification"]["classification"],
            "ADAPTIVE_SPATIAL_COMPARISON_NOT_A_CONVERGENCE_PAIR"
        )
        self.assertEqual(
            synth["governing_verdict"],
            "ADAPTIVE_MACRO_RESPONSE_STABLE__PHASE_FIELD_MESH_SENSITIVE"
        )
        self.assertEqual(
            synth["overall_spatial_verdict"],
            "SPATIAL_CONVERGENCE_EVIDENCE_ALREADY_SUFFICIENT"
        )

    def test_06_artifacts_and_figures_exist(self):
        """Verify that all report and figure artifacts exist on disk."""
        self.assertTrue(os.path.exists(self.report_md_path))
        self.assertTrue(os.path.exists(self.fig_energy_pdf))
        self.assertTrue(os.path.exists(self.fig_fu_pdf))


if __name__ == "__main__":
    unittest.main()
