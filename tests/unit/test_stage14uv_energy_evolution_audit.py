import os
import json
import unittest

class TestStage14UVEnergyEvolutionAudit(unittest.TestCase):
    """
    Unit test suite for Gate-6B Mode-I Stage 14U-V: Energy Evolution and Partitioning Dynamics Audit.
    Verifies multi-quantity energy conservation, elastic-to-fracture partitioning, peak elastic monotonicity,
    and broken-state functional convergence across spatial, temporal, and adaptive discretization families.
    """

    @classmethod
    def setUpClass(cls):
        # Robust repository path discovery
        base_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(base_dir, "..", ".."))
        
        cls.json_path = os.path.join(
            repo_root,
            "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k",
            "MODE1_STAGE14UV_ENERGY_EVOLUTION_AUDIT_REPORT.json"
        )
        cls.md_path = os.path.join(
            repo_root,
            "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k",
            "MODE1_STAGE14UV_ENERGY_EVOLUTION_AUDIT_REPORT.md"
        )
        
        if os.path.exists(cls.json_path):
            with open(cls.json_path, "r", encoding="utf-8") as f:
                cls.report_data = json.load(f)
        else:
            cls.report_data = None

    def test_01_reports_exist_and_non_empty(self):
        """Verify that the Stage 14U-V JSON and Markdown audit reports exist and are non-empty."""
        self.assertTrue(os.path.exists(self.json_path), f"Missing JSON report at {self.json_path}")
        self.assertTrue(os.path.exists(self.md_path), f"Missing MD report at {self.md_path}")
        self.assertGreater(os.path.getsize(self.json_path), 500)
        self.assertGreater(os.path.getsize(self.md_path), 500)
        self.assertIsNotNone(self.report_data)

    def test_02_governing_verdicts_and_metadata(self):
        """Verify protocol metadata, governing directive, and formal verdicts."""
        data = self.report_data
        self.assertEqual(data.get("protocol_version"), 2)
        self.assertEqual(data.get("audit_id"), "F1205-GATE6B-STAGE14UV-ENERGY-EVOLUTION-AND-PARTITIONING-AUDIT-20261004")
        self.assertEqual(
            data.get("governing_directive"),
            "We need to have understood everything related to the first model before we increase complexity."
        )
        
        verdicts = data.get("governing_verdicts", {})
        self.assertEqual(
            verdicts.get("energy_conservation_and_partitioning"),
            "THERMODYNAMICALLY_CONSISTENT_AND_QUALIFIED"
        )
        self.assertEqual(
            verdicts.get("spatial_convergence_evidence"),
            "SPATIAL_CONVERGENCE_EVIDENCE_ALREADY_SUFFICIENT"
        )

    def test_03_initial_elastic_linearity_1um(self):
        """Verify that stored energy at u = 1.0 um is > 99.80% elastic across all discretizations (>99.91% for physical l0=0.0075mm)."""
        cases = self.report_data.get("cases", [])
        self.assertGreaterEqual(len(cases), 7)
        
        for c in cases:
            state = c["initial_elastic_state_1um"]
            self.assertAlmostEqual(state["u_mm"], 0.0010, delta=1e-5)
            self.assertGreaterEqual(state["fraction_elastic_pct"], 99.80, f"Failed for {c['case_id']}")
            self.assertLessEqual(state["fraction_fracture_pct"], 0.20, f"Failed for {c['case_id']}")
            self.assertGreaterEqual(state["e_elas_mJ"], 0.0688, f"Failed for {c['case_id']}")
            self.assertLessEqual(state["e_elas_mJ"], 0.0690, f"Failed for {c['case_id']}")
            
            # For physical l0=0.0075mm meshes, elastic share is >= 99.91%
            if c["family"] in ["spatial_and_reference", "spatial", "temporal", "adaptive"]:
                self.assertGreaterEqual(state["fraction_elastic_pct"], 99.91, f"Failed for physical l0 case {c['case_id']}")

    def test_04_pre_peak_partitioning_5um(self):
        """Verify energy partitioning at u = 5.0 um (end of Step 1) across spatial and adaptive cases."""
        case_map = {c["case_id"]: c for c in self.report_data.get("cases", [])}
        
        s1 = case_map["S1_ref_15k"]["step1_terminal_state_5um"]
        s2 = case_map["S2_fix_32k"]["step1_terminal_state_5um"]
        s3 = case_map["S3_fix_42k"]["step1_terminal_state_5um"]
        stage14 = case_map["Stage14_953"]["step1_terminal_state_5um"]
        
        # Verify elastic energy ordering at 5 um
        self.assertAlmostEqual(s1["e_elas_mJ"], 1.655130, delta=1e-4)
        self.assertAlmostEqual(stage14["e_elas_mJ"], 1.654313, delta=1e-4)
        self.assertAlmostEqual(s2["e_elas_mJ"], 1.654067, delta=1e-4)
        self.assertAlmostEqual(s3["e_elas_mJ"], 1.653385, delta=1e-4)
        
        # Stage 14 candidate lies between S1 and S2
        self.assertLess(stage14["e_elas_mJ"], s1["e_elas_mJ"])
        self.assertGreater(stage14["e_elas_mJ"], s2["e_elas_mJ"])

    def test_05_peak_elastic_monotonicity(self):
        """Verify that peak elastic strain energy decreases monotonically with spatial refinement."""
        case_map = {c["case_id"]: c for c in self.report_data.get("cases", [])}
        
        s1_peak = case_map["S1_ref_15k"]["peak_elastic_state"]["e_elas_peak_mJ"]
        s2_peak = case_map["S2_fix_32k"]["peak_elastic_state"]["e_elas_peak_mJ"]
        s3_peak = case_map["S3_fix_42k"]["peak_elastic_state"]["e_elas_peak_mJ"]
        stage14_peak = case_map["Stage14_953"]["peak_elastic_state"]["e_elas_peak_mJ"]
        
        # Monotonic decrease in fixed mesh sequence
        self.assertGreater(s1_peak, s2_peak)
        self.assertGreater(s2_peak, s3_peak)
        
        # Stage 14 candidate lies squarely in the S1 -> S2 transition band
        self.assertLess(stage14_peak, s1_peak)
        self.assertGreater(stage14_peak, s2_peak)
        self.assertAlmostEqual(stage14_peak, 2.132779, delta=1e-4)

    def test_06_broken_state_dissipation_bounds(self):
        """Verify broken-state fracture functional converges in [2.285, 2.375] mJ across physical spatial meshes."""
        case_map = {c["case_id"]: c for c in self.report_data.get("cases", [])}
        
        e_frac_s1 = case_map["S1_ref_15k"]["broken_terminal_state"]["e_frac_terminal_mJ"]
        e_frac_s2 = case_map["S2_fix_32k"]["broken_terminal_state"]["e_frac_terminal_mJ"]
        e_frac_s3 = case_map["S3_fix_42k"]["broken_terminal_state"]["e_frac_terminal_mJ"]
        e_frac_stage14 = case_map["Stage14_953"]["broken_terminal_state"]["e_frac_terminal_mJ"]
        
        for val in [e_frac_s1, e_frac_s2, e_frac_s3, e_frac_stage14]:
            self.assertGreaterEqual(val, 2.280, f"Value {val} below lower bound")
            self.assertLessEqual(val, 2.380, f"Value {val} above upper bound")
            
        spread_pct = ((max(e_frac_s1, e_frac_s2, e_frac_s3, e_frac_stage14) - 
                       min(e_frac_s1, e_frac_s2, e_frac_s3, e_frac_stage14)) / e_frac_s1) * 100.0
        self.assertLess(spread_pct, 3.9, f"Spread {spread_pct}% exceeds 3.9% limit")

    def test_07_stage14_reference_energy_parity(self):
        """Verify Stage 14 adaptive candidate matches S1 reference broken-state E_frac within -2.34%."""
        case_map = {c["case_id"]: c for c in self.report_data.get("cases", [])}
        
        e_frac_s1 = case_map["S1_ref_15k"]["broken_terminal_state"]["e_frac_terminal_mJ"]
        e_frac_stage14 = case_map["Stage14_953"]["broken_terminal_state"]["e_frac_terminal_mJ"]
        
        diff_pct = ((e_frac_stage14 - e_frac_s1) / e_frac_s1) * 100.0
        self.assertAlmostEqual(diff_pct, -2.3396, delta=0.01)

    def test_08_energy_unit_consistency(self):
        """Verify all energy quantities are strictly scaled in mJ (order of magnitude 0.069 to 2.400 mJ)."""
        cases = self.report_data.get("cases", [])
        for c in cases:
            # Check 1um elastic energy is ~0.069 mJ
            self.assertGreater(c["initial_elastic_state_1um"]["e_elas_mJ"], 0.05)
            self.assertLess(c["initial_elastic_state_1um"]["e_elas_mJ"], 0.10)
            
            # Check terminal fracture energy is in mJ range (~2.2 - 3.4 mJ)
            self.assertGreater(c["broken_terminal_state"]["e_frac_terminal_mJ"], 2.0)
            self.assertLess(c["broken_terminal_state"]["e_frac_terminal_mJ"], 4.0)

if __name__ == "__main__":
    unittest.main()
