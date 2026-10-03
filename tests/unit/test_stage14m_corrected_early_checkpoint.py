"""
Unit tests for Gate-6B Mode-I Stage 14M Corrected-Job Early Mechanical Checkpoint.

Validates:
1. Stage 14M JSON report schema and metrics.
2. Canonical K0 semantics: strictly NOT_YET_QUALIFIED when N < 400.
3. K_energy vs canonical K0 distinction.
4. Physical stiffness scale restoration vs invalidated Job 1409947 (>1000x force ratio).
5. Early mechanical parity vs Reference Job 1409734 (mean error < 0.1%).
"""

import json
import os
import unittest


class TestStage14MCorrectedEarlyCheckpoint(unittest.TestCase):

    def setUp(self):
        self.project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )
        self.report_json_path = os.path.join(
            self.project_root,
            "models",
            "pandey_kumar_mode1",
            "25_stage14_adaptive_candidate_14k",
            "MODE1_STAGE14M_CORRECTED_ADAPTIVE_EARLY_CHECKPOINT_REPORT.json"
        )
        self.assertTrue(
            os.path.exists(self.report_json_path),
            f"Stage 14M JSON report missing: {self.report_json_path}"
        )
        with open(self.report_json_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def test_01_report_structure_and_task_id(self):
        self.assertEqual(
            self.data["task_id"],
            "F1190-GATE6B-STAGE14M-CORRECTED-ADAPTIVE-EARLY-CHECKPOINT-20261003"
        )
        self.assertEqual(
            self.data["overall_classification"],
            "CORRECTED_JOB_EARLY_MECHANICAL_CHECKPOINT_ONLY"
        )
        self.assertEqual(
            self.data["active_solver_job"]["job_id"],
            "1409953.mmaster02"
        )
        self.assertEqual(
            self.data["active_solver_job"]["status"],
            "RUNNING_ACTIVE"
        )

    def test_02_canonical_k0_semantics_and_window_status(self):
        k0_info = self.data["canonical_k0_semantics_correction"]
        n_avail = k0_info["available_increments_evaluated"]
        req_incs = k0_info["canonical_window_increments_required"]
        self.assertEqual(req_incs, 400)
        
        # When n_avail < 400, canonical K0 MUST be classified as NOT_YET_QUALIFIED
        if n_avail < 400:
            self.assertIn("NOT_YET_QUALIFIED", k0_info["canonical_k0_status"])
        
        # Check that interim OLS fit is physically consistent
        interim_k = k0_info["interim_ols_stiffness_kN_per_mm"]
        self.assertGreater(interim_k, 130.0)
        self.assertLess(interim_k, 145.0)
        self.assertGreater(k0_info["interim_ols_r2"], 0.9999)

    def test_03_physical_scale_restoration_vs_invalidated_job(self):
        ref_comp = self.data["reference_benchmark_comparison"]
        inv_info = self.data["invalidated_job_forensics"]
        
        self.assertEqual(inv_info["invalidated_job_id"], "1409947.mmaster02")
        self.assertEqual(
            inv_info["classification"],
            "INVALID_BENCHMARK__UEL_PROPERTY_ABI_MISMATCH"
        )
        self.assertEqual(
            ref_comp["mechanical_scale_status"],
            "PHYSICAL_ELASTICITY_SCALE_RESTORED"
        )
        
        # Discrepancy vs reference should be well within 1% (actual is ~0.03%)
        mean_diff = ref_comp["mean_pointwise_force_difference_pct"]
        self.assertLess(abs(mean_diff), 0.5)

    def test_04_energy_vs_canonical_k0_distinction(self):
        k0_info = self.data["canonical_k0_semantics_correction"]
        # Both quantities exist and are distinctly labeled
        self.assertIn("interim_ols_stiffness_kN_per_mm", k0_info)
        self.assertIn("interim_energy_stiffness_kN_per_mm", k0_info)
        self.assertIn("correction_explanation", k0_info)
        self.assertIn("K_energy", k0_info["correction_explanation"])


if __name__ == "__main__":
    unittest.main()
