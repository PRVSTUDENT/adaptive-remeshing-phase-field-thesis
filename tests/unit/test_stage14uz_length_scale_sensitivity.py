"""
test_stage14uz_length_scale_sensitivity.py

Unit test suite verifying Gate-6B Stage 14U-Z: Phase-Field Regularization
Length-Scale Sensitivity Provenance, Matched-State Energy Partitioning,
and Claim-Discipline Audit.
"""

import os
import json
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CANDIDATE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k")
REPORT_JSON = os.path.join(CANDIDATE_DIR, "MODE1_STAGE14UZ_LENGTH_SCALE_SENSITIVITY_REPORT.json")
REPORT_MD = os.path.join(CANDIDATE_DIR, "MODE1_STAGE14UZ_LENGTH_SCALE_SENSITIVITY_REPORT.md")


def get_sha256(file_path):
    if not os.path.exists(file_path):
        return None
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class TestStage14uzLengthScaleSensitivity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.assertTrue(os.path.exists(REPORT_JSON), f"Missing JSON report: {REPORT_JSON}")
        cls.assertTrue(os.path.exists(REPORT_MD), f"Missing MD report: {REPORT_MD}")
        with open(REPORT_JSON, "r") as f:
            cls.report = json.load(f)

    def test_01_report_structure_and_verdict(self):
        """Verify report metadata, task ID, and governing verdict."""
        self.assertEqual(self.report["task_id"], "F1209-GATE6B-STAGE14UZ-PHASE-FIELD-LENGTH-SCALE-SENSITIVITY-AUDIT-20261004")
        self.assertEqual(self.report["governing_verdict"], "LENGTH_SCALE_SENSITIVITY_SUFFICIENTLY_CHARACTERIZED")
        self.assertEqual(self.report["phase"], "MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION")

    def test_02_provenance_and_fortran_identity(self):
        """Verify 17-field provenance across length-scale family and Fortran SHA-256 identity."""
        expected_for_sha = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
        prov = self.report["provenance_17_fields"]
        
        for case_id in ["S1_ref", "L1_S3", "L2_intermediate", "L3_coarse"]:
            self.assertIn(case_id, prov)
            case_data = prov[case_id]
            self.assertEqual(case_data["comparability_classification"], "LENGTH_SCALE_COMPARABLE")
            self.assertEqual(case_data["for_sha256"].lower(), expected_for_sha.lower())
            self.assertIn("PK_MODE1_", case_data["inp_file"])
            self.assertIsNotNone(case_data["inp_sha256"])

    def test_03_uel_property_abi_and_l0_values(self):
        """Verify UEL property ABI card parameter ordering and length scale values."""
        prov = self.report["provenance_17_fields"]
        self.assertAlmostEqual(prov["S1_ref"]["material_params"]["l0_mm"], 0.00750, places=5)
        self.assertAlmostEqual(prov["L1_S3"]["material_params"]["l0_mm"], 0.00750, places=5)
        self.assertAlmostEqual(prov["L2_intermediate"]["material_params"]["l0_mm"], 0.01125, places=5)
        self.assertAlmostEqual(prov["L3_coarse"]["material_params"]["l0_mm"], 0.01500, places=5)

    def test_04_mesh_resolution_constraint_compliance(self):
        """Verify that all tested length-scale cases satisfy h_min / l0 <= 0.20."""
        ratios = self.report["scientific_nature_of_l0"]["resolution_ratios_achieved"]
        for cid, data in ratios.items():
            h_l0 = data["h_over_l0"]
            self.assertLessEqual(h_l0, 0.20, f"Case {cid} violates resolution constraint: h/l0 = {h_l0}")

    def test_05_initial_stiffness_invariance(self):
        """Verify that canonical initial stiffness K0 is STABLE across 2x l0 variation (spread <= 0.20%)."""
        prov = self.report["provenance_17_fields"]
        k0_vals = [prov[cid]["elastic_stiffness"]["K0_kN_per_mm"] for cid in ["L1_S3", "L2_intermediate", "L3_coarse"]]
        spread_pct = ((max(k0_vals) - min(k0_vals)) / min(k0_vals)) * 100.0
        self.assertLessEqual(spread_pct, 0.20, f"K0 spread too high: {spread_pct}%")
        self.assertEqual(self.report["quantity_classifications"]["initial_structural_stiffness_K0"]["classification"], 
                         "STABLE_OVER_TESTED_LENGTH_SCALE_RANGE")

    def test_06_monotonic_peak_load_degradation(self):
        """Verify that peak load decreases monotonically with increasing length scale."""
        prov = self.report["provenance_17_fields"]
        f1 = prov["L1_S3"]["peak_response"]["f_max_kN"]
        f2 = prov["L2_intermediate"]["peak_response"]["f_max_kN"]
        f3 = prov["L3_coarse"]["peak_response"]["f_max_kN"]
        
        self.assertGreater(f1, f2, f"Peak force should decrease: L1 ({f1}) <= L2 ({f2})")
        self.assertGreater(f2, f3, f"Peak force should decrease: L2 ({f2}) <= L3 ({f3})")
        self.assertEqual(self.report["quantity_classifications"]["peak_reaction_force_Fmax"]["classification"], 
                         "LENGTH_SCALE_SENSITIVE")

    def test_07_broken_state_fracture_functional_stability(self):
        """Verify that broken-state crack-surface functional E_frac is STABLE (spread <= 3.0%)."""
        matched = self.report["matched_states_table"]
        # Look at state 0.005839 (severed state for all 42k meshes)
        state_severed = None
        for s in matched:
            if abs(s["u_nominal_mm"] - 0.005839) < 1e-6:
                state_severed = s
                break
        self.assertIsNotNone(state_severed)
        e_frac_vals = [state_severed[k]["E_frac_mJ"] for k in ["L1_S3", "L2_inter", "L3_coarse"]]
        spread_pct = ((max(e_frac_vals) - min(e_frac_vals)) / min(e_frac_vals)) * 100.0
        self.assertLessEqual(spread_pct, 3.0, f"Broken state E_frac spread too high: {spread_pct}%")
        self.assertEqual(self.report["quantity_classifications"]["broken_state_fracture_functional_Efrac"]["classification"], 
                         "STABLE_OVER_TESTED_LENGTH_SCALE_RANGE")


if __name__ == "__main__":
    unittest.main()
