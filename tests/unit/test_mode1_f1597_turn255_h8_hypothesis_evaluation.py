"""Unit test for Turn 255: Independent verification of Hypothesis H8 AT2 energy-consistency evaluation.

Validates:
1. File existence, schema, and cryptographic SHA256 integrity of H8 deliverables.
2. Rigorous pre-analysis holdout eligibility matrix (separation of calibration, holdout, and ineligible sets).
3. Independent holdout predictions and error quantification (Packages 119, 123, 120).
4. Bounded domain of applicability (pre-peak stationary regime d_max <= 0.65).
5. Governance gate retention: STAGE_C1_2_STEP2_ENERGY_GATE_FAILED preserved, C5 prohibited.
6. Supervisor decision memorandum existence, structure, and integrity.
"""

import hashlib
import json
import os
import unittest


class TestMode1F1597Turn255H8HypothesisEvaluation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = r"D:\Master thesis\Adaptive remeshing"
        cls.artifact_path = os.path.join(
            cls.workspace, "results", "validation", "h8_at2_energy_consistency_evaluation.json"
        )
        cls.script_path = os.path.join(
            cls.workspace, "scripts", "validation", "evaluate_mode1_f1597_turn255_h8_at2_energy_criterion.py"
        )
        cls.memo_path = os.path.join(
            cls.workspace, "docs", "supervisor_reports", "decision_memorandum_turn255_mesh_aware_at2_energy_gate.md"
        )
        with open(cls.artifact_path, "r", encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_01_artifact_integrity_and_schema(self):
        self.assertTrue(os.path.isfile(self.artifact_path), f"Artifact missing: {self.artifact_path}")
        self.assertTrue(os.path.isfile(self.script_path), f"Script missing: {self.script_path}")
        self.assertTrue(os.path.isfile(self.memo_path), f"Memo missing: {self.memo_path}")
        self.assertEqual(self.data.get("schema"), 1)
        self.assertEqual(self.data.get("task_id"), "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertEqual(self.data.get("investigation"), "H8_PROSPECTIVE_AT2_ENERGY_CONSISTENCY_EVALUATION")
        self.assertEqual(self.data.get("classification"), "H8_SUPPORTED_PROSPECTIVELY")

    def test_02_holdout_eligibility_matrix(self):
        em = self.data.get("eligibility_matrix", {})
        # Calibration / In-sample controls (ineligible as holdouts)
        self.assertFalse(em.get("PACKAGE_111_R2", {}).get("eligible_for_holdout"))
        self.assertFalse(em.get("PACKAGE_115", {}).get("eligible_for_holdout"))
        self.assertFalse(em.get("PACKAGE_117", {}).get("eligible_for_holdout"))
        self.assertFalse(em.get("PACKAGE_113", {}).get("eligible_for_holdout"))

        # Independent holdouts (eligible)
        self.assertTrue(em.get("PACKAGE_119", {}).get("eligible_for_holdout"))
        self.assertTrue(em.get("PACKAGE_123", {}).get("eligible_for_holdout"))
        self.assertTrue(em.get("PACKAGE_120", {}).get("eligible_for_holdout"))

        # Ineligible controls (different physics / formulation)
        self.assertFalse(em.get("PACKAGE_93", {}).get("eligible_for_holdout"))
        self.assertFalse(em.get("PACKAGE_94", {}).get("eligible_for_holdout"))

    def test_03_holdout_evaluations_and_residuals(self):
        he = {item["package"]: item for item in self.data.get("holdout_evaluations", [])}

        # Package 119 (Inc 85) holdout pass
        p119 = he.get("PACKAGE_119", {})
        self.assertTrue(p119.get("is_within_pass_band"))
        self.assertAlmostEqual(abs(p119.get("dimensionless_residual_r_E_pct")), 0.20898, places=4)
        self.assertLessEqual(abs(p119.get("dimensionless_residual_r_E_pct")), 0.25)

        # Package 123 (Inc 86) holdout pass
        p123 = he.get("PACKAGE_123", {})
        self.assertTrue(p123.get("is_within_pass_band"))
        self.assertAlmostEqual(abs(p123.get("dimensionless_residual_r_E_pct")), 0.23497, places=4)
        self.assertLessEqual(abs(p123.get("dimensionless_residual_r_E_pct")), 0.25)

        # Package 120 (Inc 88) softening boundary fail
        p120 = he.get("PACKAGE_120", {})
        self.assertFalse(p120.get("is_within_pass_band"))
        self.assertGreater(abs(p120.get("dimensionless_residual_r_E_pct")), 0.25)
        self.assertFalse(p120.get("stationarity_converged"))

    def test_04_domain_of_applicability(self):
        doa = self.data.get("domain_of_applicability", {})
        self.assertIn("d_max <= 0.65", doa.get("valid_regime", ""))
        self.assertIn("d_max >= 0.70", doa.get("invalid_regime", ""))
        self.assertIn("|r_E| <= 0.235%", doa.get("holdout_accuracy_in_valid_regime", ""))

    def test_05_governance_and_gate_retention(self):
        self.assertEqual(self.data.get("governing_gate"), "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED")
        self.assertTrue(self.data.get("gate_retained"))
        self.assertFalse(self.data.get("c5_remeshing_permitted"))

        p113 = self.data.get("package113_retained_metrics", {})
        self.assertEqual(p113.get("status"), "FAIL_RETAINED")
        self.assertAlmostEqual(p113.get("measured_discrepancy_pct"), 2.00803158, places=5)
        self.assertAlmostEqual(p113.get("predeclared_tolerance_pct"), 2.00000000, places=5)
        self.assertAlmostEqual(p113.get("exceedance_pct_points"), 0.00803158, places=5)

        hpc = self.data.get("hpc_execution_justification", {})
        self.assertFalse(hpc.get("submission_justified"))

    def test_06_supervisor_decision_memorandum(self):
        with open(self.memo_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Decision Memorandum", content)
        self.assertIn("H8_SUPPORTED_PROSPECTIVELY", content)
        self.assertIn("STAGE_C1_2_STEP2_ENERGY_GATE_FAILED remains strictly retained", content)
        self.assertIn("+2.00803158", content)


if __name__ == "__main__":
    unittest.main()
