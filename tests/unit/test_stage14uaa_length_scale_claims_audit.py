import unittest
import os
import json
import re

class TestStage14UaaLengthScaleClaimsAudit(unittest.TestCase):
    """
    Unit test suite for Gate-6B Stage 14U-AA:
    Length-Scale Claim Correction, Exact Matched-State Boundary Audit,
    and Resolution-Adequacy Qualification.
    """

    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cls.report_json_path = os.path.join(
            cls.repo_root,
            "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k",
            "MODE1_STAGE14UAA_LENGTH_SCALE_REPORT.json"
        )
        cls.report_md_path = os.path.join(
            cls.repo_root,
            "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k",
            "MODE1_STAGE14UAA_LENGTH_SCALE_REPORT.md"
        )
        cls.assertTrue(os.path.exists(cls.report_json_path), f"Missing JSON report: {cls.report_json_path}")
        cls.assertTrue(os.path.exists(cls.report_md_path), f"Missing MD report: {cls.report_md_path}")

        with open(cls.report_json_path, "r", encoding="utf-8") as f:
            cls.report_data = json.load(f)
        with open(cls.report_md_path, "r", encoding="utf-8") as f:
            cls.report_md = f.read()

    def test_01_l2_exact_boundary_and_not_reached_state(self):
        """Verify L2 exact terminal displacement is 0.0058390107 mm and u=0.005840 mm is marked NOT_REACHED."""
        prov = self.report_data["provenance_17_fields"]["L2_intermediate"]
        self.assertAlmostEqual(prov["terminal_u_mm"], 0.0058390107, places=6)
        self.assertLess(prov["terminal_u_mm"], 0.005840)

        # Check matched states table at u = 0.005840 mm
        matched_table = self.report_data["matched_states_table"]
        state_5840 = next((s for s in matched_table if abs(s["u_nominal_mm"] - 0.005840) < 1e-6), None)
        self.assertIsNotNone(state_5840, "Matched state at u=0.005840 mm must exist in table")
        self.assertEqual(state_5840["L2_inter"]["status"], "NOT_REACHED")
        self.assertIsNone(state_5840["L2_inter"]["F_kN"])
        self.assertIsNone(state_5840["L2_inter"]["E_frac_mJ"])
        self.assertIsNone(state_5840["L2_inter"]["E_elas_mJ"])

    def test_02_energy_nomenclature_purged_of_dissipation(self):
        """Verify all occurrences of 'dissipation' for E_frac are purged and replaced with governed terminology."""
        # Check JSON keys and classifications
        classifications = self.report_data["quantity_classifications"]
        self.assertNotIn("broken_state_fracture_dissipation", classifications)
        self.assertNotIn("pre_peak_micro_damage_dissipation", classifications)
        self.assertIn("post_fracture_crack_surface_functional_Efrac", classifications)

        classification_val = classifications["post_fracture_crack_surface_functional_Efrac"]["classification"]
        self.assertEqual(classification_val, "POST_FRACTURE_EFRAC_STABLE_OVER_TESTED_LENGTH_SCALE_RANGE")

        # Check Markdown content for prohibited phrases
        prohibited_patterns = [
            r"micro-damage dissipation",
            r"fracture dissipation",
            r"dissipated fracture energy"
        ]
        for pat in prohibited_patterns:
            matches = re.findall(pat, self.report_md, re.IGNORECASE)
            self.assertEqual(len(matches), 0, f"Found prohibited phrase '{pat}' in report MD: {matches}")

    def test_03_resolution_ratio_descriptive_reporting(self):
        """Verify mesh resolution ratios are reported descriptively without undeclared hard threshold cutoffs."""
        res_info = self.report_data["scientific_nature_of_l0"]["mesh_resolution_reporting"]
        self.assertEqual(
            res_info["qualification_classification"],
            "DESCRIPTIVELY_REPORTED__RESOLUTION_ADEQUACY_NOT_INDEPENDENTLY_QUALIFIED"
        )
        ratios = res_info["actual_project_ratios"]
        self.assertAlmostEqual(ratios["L1_baseline_l0_0075"]["h_over_l0"], 0.2000, places=4)
        self.assertAlmostEqual(ratios["L2_intermediate_l0_01125"]["h_over_l0"], 0.1333, places=4)
        self.assertAlmostEqual(ratios["L3_coarse_l0_01500"]["h_over_l0"], 0.1000, places=4)
        self.assertAlmostEqual(ratios["S1_reference_l0_0075"]["h_over_l0"], 0.4000, places=4)

    def test_04_idealized_1d_at2_scaling_qualification(self):
        """Verify 1D AT2 critical stress formula is qualified as idealized theoretical background."""
        theo_info = self.report_data["scientific_nature_of_l0"]["theoretical_1d_at2_background"]
        self.assertEqual(theo_info["status"], "IDEALIZED_1D_THEORETICAL_BACKGROUND")
        self.assertIn("sigma_c = sqrt(9 * E * Gc / (16 * l0))", theo_info["formula"])

    def test_05_multi_quantity_invariance_and_sensitivity_bounds(self):
        """Verify K0 invariance (<0.11%), monotonic peak load reduction (-4.96%), and broken-state Efrac stability."""
        classifications = self.report_data["quantity_classifications"]
        
        # K0 stability
        k0_class = classifications["initial_structural_stiffness_K0"]
        self.assertEqual(k0_class["classification"], "STABLE_OVER_TESTED_LENGTH_SCALE_RANGE")
        self.assertLess(k0_class["variation_pct"], 0.11)

        # Fmax sensitivity
        fmax_class = classifications["peak_reaction_force_Fmax"]
        self.assertEqual(fmax_class["classification"], "LENGTH_SCALE_SENSITIVE")
        self.assertAlmostEqual(fmax_class["variation_pct"], 4.9556, places=2)

        # Terminal broken-state E_frac spread < 2.33%
        efrac_class = classifications["post_fracture_crack_surface_functional_Efrac"]
        self.assertLess(efrac_class["variation_pct"], 2.33)
        self.assertGreaterEqual(efrac_class["spread_mJ"][0], 2.30)
        self.assertLessEqual(efrac_class["spread_mJ"][1], 2.36)

    def test_06_governing_verdict_selection(self):
        """Verify the exact required governing verdict is assigned."""
        expected_verdict = "LENGTH_SCALE_SENSITIVITY_CHARACTERIZED__RESOLUTION_ADEQUACY_NOT_INDEPENDENTLY_QUALIFIED"
        self.assertEqual(self.report_data["governing_verdict"], expected_verdict)


if __name__ == "__main__":
    unittest.main()
