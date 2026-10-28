"""Unit test for Turn 255: Independent verification of Package 113 forensic energy audit.

Validates:
1. File existence and cryptographic SHA256 hash integrity
2. Schema structure, task identification, and forensic classification
3. Mathematical precision of energy deconstruction and component excess share
4. Physical and numerical uncertainty bounds vs floating-point and truncation noise
5. Method C governance matrix status and binding gate retention
6. Strict HPC non-submission justification and C5 prohibition
"""

import hashlib
import json
import os
import unittest


class TestMode1F1597Turn255Package113EnergyGateAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = r"D:\Master thesis\Adaptive remeshing"
        cls.audit_path = os.path.join(
            cls.workspace,
            "results",
            "validation",
            "package113_energy_gate_forensic_audit.json",
        )
        cls.expected_sha256 = (
            "e2587da5fdf47347280c3c2fd893714f85dbcbd45a0149504db7da8395b70af8"
        )
        with open(cls.audit_path, "r", encoding="utf-8") as f:
            cls.data = json.load(f)

    def test_01_file_integrity_and_schema(self):
        self.assertTrue(os.path.isfile(self.audit_path), f"Audit file missing: {self.audit_path}")
        with open(self.audit_path, "rb") as f:
            content = f.read()
        calculated_sha = hashlib.sha256(content).hexdigest().lower()
        self.assertEqual(
            calculated_sha,
            self.expected_sha256,
            "Package 113 forensic audit SHA256 mismatch",
        )
        self.assertEqual(self.data.get("schema"), 1)
        self.assertEqual(self.data.get("task_id"), "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertEqual(
            self.data.get("investigation"),
            "FORENSIC_PACKAGE113_ENERGY_GATE_AUDIT_AND_METHOD_C_EVIDENCE_SYNTHESIS",
        )

    def test_02_classification_and_binding_gate(self):
        self.assertEqual(self.data.get("classification"), "P113_DISCRETIZATION_BIAS_SUPPORTED")
        self.assertEqual(self.data.get("governing_gate"), "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED")
        self.assertIn("P113_DISCRETIZATION_BIAS_SUPPORTED", self.data.get("classification_candidates", []))
        self.assertIn("STAGE_C1_2_STEP2_ENERGY_GATE_FAILED", self.data.get("finding", ""))

    def test_03_energy_deconstruction_mathematics(self):
        ed = self.data.get("energy_deconstruction", {})
        donor_tot = ed.get("donor_elas_mJ") + ed.get("donor_frac_mJ")
        receiver_tot = ed.get("receiver_elas_mJ") + ed.get("receiver_frac_mJ")

        self.assertAlmostEqual(donor_tot, ed.get("donor_tot_csv_mJ"), places=6)
        self.assertAlmostEqual(receiver_tot, ed.get("receiver_tot_mJ"), places=6)

        pct_diff_tot = ((receiver_tot - donor_tot) / donor_tot) * 100.0
        self.assertAlmostEqual(pct_diff_tot, ed.get("pct_diff_tot"), places=5)
        self.assertAlmostEqual(pct_diff_tot, 2.00803158, places=5)

        exceedance = pct_diff_tot - ed.get("predeclared_tolerance_pct")
        self.assertAlmostEqual(exceedance, ed.get("exceedance_pct_points"), places=5)
        self.assertGreater(exceedance, 0.0)

        # Fracture energy accounts for majority of excess (> 70%)
        self.assertGreater(ed.get("share_of_excess_frac_pct"), 70.0)
        self.assertAlmostEqual(ed.get("share_of_excess_frac_pct"), 71.9806, places=3)

        # Elastic energy continuity passes under 2% threshold
        self.assertLess(ed.get("pct_diff_elas"), 2.0)
        self.assertAlmostEqual(ed.get("pct_diff_elas"), 0.69737, places=3)

    def test_04_uncertainty_and_numerical_significance(self):
        ua = self.data.get("uncertainty_analysis", {})
        self.assertEqual(ua.get("verdict"), "EXCEEDANCE_STATISTICALLY_AND_NUMERICALLY_SIGNIFICANT")
        self.assertFalse(ua.get("is_exceedance_explained_by_float_precision"))
        self.assertFalse(ua.get("is_exceedance_explained_by_summary_truncation"))
        self.assertGreater(ua.get("exceedance_to_truncation_ratio"), 330.0)

    def test_05_method_c_governance_matrix(self):
        mc = self.data.get("method_c_matrix", {})
        # Stage C1-0 and C1-1 passed
        self.assertEqual(mc.get("STAGE_C1_0_SAME_MESH_CONTINUATION", {}).get("status"), "PASS")
        self.assertEqual(mc.get("STAGE_C1_1_NONMATCHING_TRANSFER_TO_C4", {}).get("status"), "PASS")
        self.assertEqual(mc.get("STAGE_C1_2_STEP1_FIRST_FORWARD_PHYSICAL_CONTINUATION", {}).get("status"), "PASS")

        # Stage C1-2 Step 2 failed
        c12_step2 = mc.get("STAGE_C1_2_STEP2_SECOND_FORWARD_PHYSICAL_CONTINUATION", {})
        self.assertEqual(c12_step2.get("status"), "FAILED")
        self.assertFalse(c12_step2.get("governing_gate_cleared"))
        self.assertEqual(c12_step2.get("binding_gate"), "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED")

        # Stage C2 (C5 refinement) strictly blocked
        c2 = mc.get("STAGE_C2_ADAPTIVE_CYCLE_C5_REFINEMENT", {})
        self.assertEqual(c2.get("status"), "BLOCKED")
        self.assertFalse(c2.get("governing_gate_cleared"))

    def test_06_hpc_governance_and_recommendations(self):
        hpc = self.data.get("hpc_execution_justification", {})
        self.assertFalse(hpc.get("submission_justified"))
        recs = self.data.get("post_overnight_recommendations", [])
        self.assertEqual(len(recs), 3)
        self.assertEqual(recs[0].get("rank"), 1)
        self.assertFalse(recs[0].get("requires_hpc"))


if __name__ == "__main__":
    unittest.main()
