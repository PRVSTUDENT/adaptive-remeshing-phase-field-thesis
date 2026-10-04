#!/usr/bin/env python3
"""
Unit test suite for Gate-6B Mode-I Stage 14U-T:
Spatial-Convergence Evidence Audit and Controlled Candidate-Definition Preflight.

Validates:
1. Integrity and structure of the spatial convergence inventory report.
2. Bitwise source identity of f42_mixed_uel.for (SHA-256 CE8D5EDC...).
3. Mathematical formulation and parameter ABI invariance across spatial cases.
4. Crack corridor mesh statistics consistency and concentration (57.57% in Stage 14).
5. Elastic structural stiffness K0 stability (|Delta K0| <= 0.10%, STABLE).
6. Peak reaction force Fmax monotonic trend and adaptive placement (MESH_SENSITIVE).
7. Post-fracture crack surface functional Efrac stability (spread < 4%, STABLE).
8. Formal verdict governance consistency (SPATIAL_CONVERGENCE_EVIDENCE_ALREADY_SUFFICIENT).
"""

import unittest
import json
import os
import hashlib

class TestStage14UTSpatialConvergenceAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cls.report_path = os.path.join(
            cls.repo_root,
            "models",
            "pandey_kumar_mode1",
            "25_stage14_adaptive_candidate_14k",
            "MODE1_STAGE14UT_SPATIAL_CONVERGENCE_AUDIT_REPORT.json"
        )
        self_assertTrue = os.path.isfile(cls.report_path)
        if not self_assertTrue:
            # Fallback to model directory
            cls.report_path = os.path.join(
                cls.repo_root,
                "models",
                "pandey_kumar_mode1",
                "MODE1_STAGE14UT_SPATIAL_CONVERGENCE_AUDIT_REPORT.json"
            )
        
        with open(cls.report_path, "r", encoding="utf-8") as f:
            cls.report = json.load(f)

    def test_01_report_structure_and_protocol(self):
        """Verify report structure, protocol version 2, and required fields."""
        self.assertEqual(self.report["protocol_version"], 2)
        self.assertEqual(
            self.report["task_id"],
            "F1203-GATE6B-STAGE14UT-SPATIAL-CONVERGENCE-AUDIT-AND-PREFLIGHT-20261004"
        )
        self.assertEqual(self.report["phase"], "MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION")
        self.assertEqual(
            self.report["spatial_convergence_verdict"],
            "SPATIAL_CONVERGENCE_EVIDENCE_ALREADY_SUFFICIENT"
        )
        self.assertTrue(self.report["running_solver_discipline"]["solver_discipline_maintained"])
        self.assertEqual(self.report["running_solver_discipline"]["unauthorized_submissions"], 0)

    def test_02_subroutine_source_identity(self):
        """Verify production Fortran subroutine SHA-256 is CE8D5EDC... across comparable cases."""
        expected_sha = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        cases = self.report["inventory_and_equivalence_matrix"]
        self.assertGreaterEqual(len(cases), 7)
        for c in cases:
            sha = c["physics_and_invariance"]["subroutine_sha256"]
            self.assertEqual(
                sha, expected_sha,
                f"Case {c['case_id']} subroutine hash {sha} != {expected_sha}"
            )

    def test_03_formulation_and_property_invariance(self):
        """Verify material properties (E, nu, Gc, l0, k) and boundary conditions are invariant."""
        cases = self.report["inventory_and_equivalence_matrix"]
        for c in cases:
            phys = c["physics_and_invariance"]
            self.assertEqual(phys["E_GPa"], 210.0)
            self.assertEqual(phys["nu"], 0.3)
            self.assertEqual(phys["Gc_kN_mm"], 0.0027)
            self.assertEqual(phys["l0_mm"], 0.0075)
            self.assertEqual(phys["k_residual"], 1.0e-7)
            self.assertIn("Zero-gap", phys["crack_type"])
            self.assertIn("Bottom roller", phys["bc_type"])

    def test_04_corridor_mesh_statistics(self):
        """Verify crack corridor mesh concentration and sizing statistics."""
        cases_dict = {c["case_id"]: c for c in self.report["inventory_and_equivalence_matrix"]}
        
        # S1 Reference
        s1 = cases_dict["S1_REF_15K"]["mesh"]
        self.assertEqual(s1["num_base_elements"], 15192)
        self.assertAlmostEqual(s1["h_corridor_mm"], 0.0030, places=4)
        self.assertAlmostEqual(s1["h_corridor_over_l0"], 0.400, places=3)
        
        # Stage 14 Adaptive Candidate
        st14 = cases_dict["STAGE14_ADAPT_14K"]["mesh"]
        self.assertEqual(st14["num_base_elements"], 14483)
        self.assertEqual(st14["quad_elements"], 14082)
        self.assertEqual(st14["tri_elements"], 401)
        self.assertGreater(st14["corridor_element_share_pct"], 50.0) # 57.57%
        self.assertLess(st14["h_min_over_l0"], 0.15)

    def test_05_k0_stability_across_all_meshes(self):
        """Verify structural stiffness K0 varies by less than 0.10% domain-wide (STABLE)."""
        cases = self.report["inventory_and_equivalence_matrix"]
        k0_ref = cases[0]["mechanical_and_energetic_metrics"]["K0_kN_mm"]
        self.assertAlmostEqual(k0_ref, 137.945520, places=5)
        
        for c in cases:
            k0 = c["mechanical_and_energetic_metrics"]["K0_kN_mm"]
            self.assertIsNotNone(k0)
            rel_diff_pct = abs(k0 - k0_ref) / k0_ref * 100.0
            self.assertLess(
                rel_diff_pct, 0.10,
                f"Case {c['case_id']} K0 discrepancy {rel_diff_pct:.4f}% exceeds 0.10%"
            )
            
        summary = self.report["multi_quantity_spatial_convergence_summary"]["K0_structural_stiffness"]
        self.assertEqual(summary["classification"], "STABLE")

    def test_06_fmax_and_upeak_monotonic_trend(self):
        """Verify Fmax and upeak decrease smoothly with mesh refinement (MESH_SENSITIVE)."""
        cases_dict = {c["case_id"]: c for c in self.report["inventory_and_equivalence_matrix"]}
        
        fmax_s1 = cases_dict["S1_REF_15K"]["mechanical_and_energetic_metrics"]["Fmax_kN"]
        fmax_s2 = cases_dict["S2_FIX_32K"]["mechanical_and_energetic_metrics"]["Fmax_kN"]
        fmax_s3 = cases_dict["S3_FIX_42K"]["mechanical_and_energetic_metrics"]["Fmax_kN"]
        fmax_s4 = cases_dict["S4_FIX_51K"]["mechanical_and_energetic_metrics"]["Fmax_kN"]
        fmax_s5 = cases_dict["S5_FIX_69K"]["mechanical_and_energetic_metrics"]["Fmax_kN"]
        
        # Verify strict monotonicity on fixed sequence S1 -> S2 -> S3 -> S4 -> S5
        self.assertGreater(fmax_s1, fmax_s2)
        self.assertGreater(fmax_s2, fmax_s3)
        self.assertGreater(fmax_s3, fmax_s4)
        self.assertGreater(fmax_s4, fmax_s5)
        
        # Verify Stage 14 Adaptive candidate falls within S1-S2 transition
        fmax_st14 = cases_dict["STAGE14_ADAPT_14K"]["mechanical_and_energetic_metrics"]["Fmax_kN"]
        self.assertLess(fmax_st14, fmax_s1)
        self.assertGreater(fmax_st14, fmax_s3)
        
        summary = self.report["multi_quantity_spatial_convergence_summary"]["Fmax_peak_reaction_force"]
        self.assertEqual(summary["classification"], "MESH_SENSITIVE")

    def test_07_efrac_fracture_functional_stability(self):
        """Verify post-fracture crack surface functional Efrac remains tightly bounded (STABLE)."""
        cases = self.report["inventory_and_equivalence_matrix"]
        efrac_values = [
            c["mechanical_and_energetic_metrics"]["Efrac_mJ"]
            for c in cases
            if c["mechanical_and_energetic_metrics"]["Efrac_mJ"] is not None
        ]
        self.assertGreaterEqual(len(efrac_values), 7)
        min_e = min(efrac_values)
        max_e = max(efrac_values)
        self.assertGreaterEqual(min_e, 2.25)
        self.assertLessEqual(max_e, 2.40)
        
        spread_pct = (max_e - min_e) / min_e * 100.0
        self.assertLess(spread_pct, 4.0)
        
        summary = self.report["multi_quantity_spatial_convergence_summary"]["Efrac_fracture_surface_functional"]
        self.assertEqual(summary["classification"], "STABLE")

    def test_08_methodological_distinction_and_verdict(self):
        """Verify clear separation between parity and spatial convergence, and valid verdict."""
        dist = self.report["methodological_distinction"]
        self.assertIn("parity", dist["reference_vs_adaptive_parity"].lower())
        self.assertIn("spatial", dist["true_spatial_convergence"].lower())
        
        decision = self.report["conclusions_and_decision"]
        self.assertTrue(decision["spatial_evidence_sufficient"])
        self.assertFalse(decision["additional_hpc_jobs_required"])
        self.assertTrue(decision["thesis_convergence_coverage_complete"])

if __name__ == "__main__":
    unittest.main()
