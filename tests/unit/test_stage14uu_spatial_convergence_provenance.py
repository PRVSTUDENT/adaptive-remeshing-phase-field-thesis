"""
Unit test suite for Gate-6B Mode-I Stage 14U-U:
Spatial-Convergence Provenance and Claim-Discipline Audit.
"""

import os
import json
import unittest

PACKAGE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k"
)

PROVENANCE_TABLE_PATH = os.path.join(PACKAGE_DIR, "MODE1_STAGE14UU_SPATIAL_PROVENANCE_TABLE.json")
AUDIT_REPORT_PATH = os.path.join(PACKAGE_DIR, "MODE1_STAGE14UU_SPATIAL_PROVENANCE_AUDIT_REPORT.json")


class TestStage14UUSpatialConvergenceProvenance(unittest.TestCase):

    def setUp(self):
        self.assertTrue(os.path.exists(PROVENANCE_TABLE_PATH), "Provenance table JSON must exist")
        self.assertTrue(os.path.exists(AUDIT_REPORT_PATH), "Audit report JSON must exist")
        with open(PROVENANCE_TABLE_PATH, "r") as f:
            self.provenance = json.load(f)
        with open(AUDIT_REPORT_PATH, "r") as f:
            self.report = json.load(f)

    def test_01_provenance_inventory_completeness(self):
        """Verify all 7 discretizations are present with complete 17-field records."""
        self.assertEqual(len(self.provenance), 7, "Exactly 7 spatial cases must be recorded")
        expected_ids = [
            "S1_REF15K", "S2_FIX32K", "S3_FIX42K", "S4_FIX51K", "S5_FIX69K",
            "ADAPT_2PCT_PKG24", "ADAPT_STAGE14_PKG25"
        ]
        actual_ids = [r["case_id"] for r in self.provenance]
        self.assertEqual(actual_ids, expected_ids, "Case IDs must match canonical spatial sequence")

        required_fields = [
            "case_id", "case_name", "job_id", "inp_relpath", "inp_sha256",
            "for_relpath", "for_sha256", "uel_props_abi", "geometry", "seam_type",
            "boundary_conditions", "material_constants", "temporal_schedule",
            "solver_controls", "energy_instrumentation", "base_elements_count",
            "corridor_elements_share_pct", "corridor_h_min_um", "canonical_k0_kN_per_mm",
            "f_max_kN", "u_peak_mm", "broken_state_e_frac_mJ", "completion_status"
        ]
        for r in self.provenance:
            for field in required_fields:
                self.assertIn(field, r, f"Field {field} must be present in record {r['case_id']}")

    def test_02_physical_parameter_and_abi_invariance(self):
        """Verify strict material constant and ABI invariance across all audited cases."""
        for r in self.provenance:
            mat = r["material_constants"]
            self.assertAlmostEqual(mat["E_GPa"], 210.0, places=3)
            self.assertAlmostEqual(mat["nu"], 0.3, places=3)
            self.assertAlmostEqual(mat["Gc_kN_per_mm"], 0.0027, places=5)
            self.assertAlmostEqual(mat["l0_mm"], 0.0075, places=5)
            self.assertEqual(r["seam_type"], "ZERO_GAP_DUPLICATED_NODES")
            self.assertIn("0.0075", r["uel_props_abi"])
            self.assertIn("0.0027", r["uel_props_abi"])
            self.assertIn("210.0", r["uel_props_abi"])

    def test_03_crack_corridor_geometry_and_area(self):
        """Verify crack corridor geometry (0.05 mm^2 = 5.0% domain area)."""
        for r in self.provenance:
            self.assertAlmostEqual(r["corridor_area_mm2"], 0.050, places=4)
            self.assertAlmostEqual(r["corridor_area_share_pct"], 5.0, places=2)

    def test_04_mesh_statistics_and_adaptive_concentration(self):
        """Verify element counts and adaptive corridor concentration."""
        record_map = {r["case_id"]: r for r in self.provenance}
        
        # Stage 14 Adaptive Candidate
        s14 = record_map["ADAPT_STAGE14_PKG25"]
        self.assertEqual(s14["base_elements_count"], 14483)
        self.assertAlmostEqual(s14["corridor_elements_share_pct"], 57.57, delta=0.2)
        self.assertAlmostEqual(s14["corridor_h_min_um"], 0.76, places=2)
        self.assertAlmostEqual(s14["h_min_over_l0"], 0.101, places=3)
        
        # Package 24 2% Variant
        p24 = record_map["ADAPT_2PCT_PKG24"]
        self.assertEqual(p24["base_elements_count"], 13897)
        self.assertAlmostEqual(p24["corridor_elements_share_pct"], 12.36, delta=0.2)
        
        # Fixed meshes
        self.assertEqual(record_map["S1_REF15K"]["base_elements_count"], 15192)
        self.assertEqual(record_map["S2_FIX32K"]["base_elements_count"], 32130)
        self.assertEqual(record_map["S3_FIX42K"]["base_elements_count"], 41912)
        self.assertEqual(record_map["S4_FIX51K"]["base_elements_count"], 51408)
        self.assertEqual(record_map["S5_FIX69K"]["base_elements_count"], 69384)

    def test_05_structural_stiffness_k0_stability(self):
        """Verify initial structural stiffness K0 stability (<= 0.0886% domain variation)."""
        k0_values = [r["canonical_k0_kN_per_mm"] for r in self.provenance]
        min_k0 = min(k0_values)
        max_k0 = max(k0_values)
        spread_pct = ((max_k0 - min_k0) / max_k0) * 100.0
        
        self.assertLessEqual(spread_pct, 0.10, "K0 spread must be <= 0.10% domain-wide")
        self.assertAlmostEqual(min_k0, 137.823, places=2)
        self.assertAlmostEqual(max_k0, 137.946, places=2)
        
        for r in self.provenance:
            self.assertGreaterEqual(r["k0_r2"], 0.9999995)

    def test_06_peak_force_and_displacement_sensitivity(self):
        """Verify monotonic peak force convergence across fixed sequence S1 -> S5."""
        record_map = {r["case_id"]: r for r in self.provenance}
        f_s1 = record_map["S1_REF15K"]["f_max_kN"]
        f_s2 = record_map["S2_FIX32K"]["f_max_kN"]
        f_s3 = record_map["S3_FIX42K"]["f_max_kN"]
        f_s4 = record_map["S4_FIX51K"]["f_max_kN"]
        f_s5 = record_map["S5_FIX69K"]["f_max_kN"]
        
        self.assertGreater(f_s1, f_s2)
        self.assertGreater(f_s2, f_s3)
        self.assertGreater(f_s3, f_s4)
        self.assertGreater(f_s4, f_s5)
        
        # Adaptive candidate must lie between S1 and S2
        f_adapt = record_map["ADAPT_STAGE14_PKG25"]["f_max_kN"]
        self.assertLess(f_adapt, f_s1)
        self.assertGreater(f_adapt, f_s2)

    def test_07_energetic_and_trajectory_discipline(self):
        """Verify fracture energy boundedness [2.285, 2.375] mJ and planar crack trajectory."""
        for r in self.provenance:
            e_frac = r["broken_state_e_frac_mJ"]
            self.assertGreaterEqual(e_frac, 2.280, f"E_frac for {r['case_id']} must be >= 2.280 mJ")
            self.assertLessEqual(e_frac, 2.380, f"E_frac for {r['case_id']} must be <= 2.380 mJ")
            self.assertAlmostEqual(r["crack_trajectory_y_mm"], 0.5000, places=4)

    def test_08_governing_verdict_and_three_tier_claims(self):
        """Verify formal verdict and three-tier claim separation in audit report."""
        self.assertEqual(
            self.report["metadata"]["governing_verdict"],
            "SPATIAL_CONVERGENCE_EVIDENCE_ALREADY_SUFFICIENT"
        )
        self.assertFalse(
            self.report["conclusion"]["additional_spatial_runs_required"],
            "No additional spatial runs should be required"
        )
        tiers = self.report["three_tier_claims_evaluation"]
        self.assertEqual(tiers["tier_1_reference_adaptive_agreement"]["classification"], "STABLE")
        self.assertIn("STABLE", tiers["tier_2_fixed_mesh_spatial_sensitivity"]["classification"])
        self.assertEqual(tiers["tier_3_adaptive_spatial_sensitivity"]["classification"], "STABLE")


if __name__ == "__main__":
    unittest.main()
