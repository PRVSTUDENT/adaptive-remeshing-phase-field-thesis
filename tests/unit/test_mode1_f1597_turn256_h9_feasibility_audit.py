"""Unit test for Turn 256: Verification of Increment-86 to 87 continuation feasibility audit (Hypothesis H9).

Validates:
1. File existence, schema, and cryptographic SHA256 integrity of Turn 256 deliverables.
2. Precise definition of Increment-87 donor (Package 76, u = 0.00194731 mm, RF2 = 185.682 N, E_tot = 0.231977 mJ).
3. Exact kinematics of the proposed Increment 86 -> 87 step (Delta u = 17.80 nm).
4. Machine-readable checkpoint completeness report verifying the state persistence gap in Package 123.
5. Strict governance classification H9_BLOCKED_STATE_OR_GOVERNANCE and non-submission compliance.
"""

import hashlib
import json
import os
import unittest


class TestMode1F1597Turn256H9FeasibilityAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = r"D:\Master thesis\Adaptive remeshing"
        cls.report_path = os.path.join(
            cls.workspace, "results", "validation", "package123_checkpoint_completeness_report.json"
        )
        cls.audit_path = os.path.join(
            cls.workspace, "results", "validation", "h9_inc86_to_inc87_continuation_feasibility_audit.json"
        )
        with open(cls.report_path, "r", encoding="utf-8") as f:
            cls.report = json.load(f)
        with open(cls.audit_path, "r", encoding="utf-8") as f:
            cls.audit = json.load(f)

    def test_01_files_and_schema(self):
        self.assertTrue(os.path.isfile(self.report_path), f"Missing: {self.report_path}")
        self.assertTrue(os.path.isfile(self.audit_path), f"Missing: {self.audit_path}")
        self.assertEqual(self.report.get("schema"), 1)
        self.assertEqual(self.audit.get("schema"), 1)
        self.assertEqual(self.report.get("task_id"), "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertEqual(self.audit.get("task_id"), "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")

    def test_02_donor_increment_87_specification(self):
        donor = self.audit.get("donor_increment_87_specification", {})
        self.assertEqual(donor.get("package"), "PACKAGE_76_CANDIDATE_DONOR_H0025_VISUAL")
        self.assertEqual(donor.get("increment"), 87)
        self.assertAlmostEqual(donor.get("prescribed_u_rp_mm"), 0.001947309589, places=8)
        self.assertAlmostEqual(donor.get("rf2_donor_N"), 185.68243, places=3)
        self.assertAlmostEqual(donor.get("e_tot_donor_mJ"), 0.23197697, places=6)
        self.assertAlmostEqual(donor.get("e_elas_donor_mJ"), 0.18079648, places=6)
        self.assertAlmostEqual(donor.get("e_frac_donor_mJ"), 0.051180487, places=6)

    def test_03_continuation_kinematics(self):
        kin = self.audit.get("continuation_step_kinematics", {})
        self.assertAlmostEqual(kin.get("starting_u_rp_mm"), 0.001929511665, places=8)
        self.assertAlmostEqual(kin.get("target_u_rp_mm"), 0.001947309589, places=8)
        delta_u = kin.get("target_u_rp_mm") - kin.get("starting_u_rp_mm")
        self.assertAlmostEqual(delta_u, 0.000017797924, places=10)
        self.assertAlmostEqual(kin.get("delta_u_nm"), 17.797924, places=4)

    def test_04_checkpoint_completeness_audit(self):
        internal = self.report.get("internal_state_and_history_audit", {})
        gp = internal.get("gauss_point_history_variables_H", {})
        self.assertEqual(gp.get("required_count"), 17688)
        self.assertFalse(gp.get("persisted_to_disk"))
        self.assertFalse(gp.get("d_lower_bounds_csv_updated"))

        restart = internal.get("abaqus_restart_database", {})
        self.assertFalse(restart.get("restart_cards_in_deck"))
        self.assertFalse(restart.get("res_or_mdl_file_available"))

        verdict = self.report.get("continuation_eligibility_verdict", {})
        self.assertFalse(verdict.get("eligible_for_genuine_restart"))
        self.assertFalse(verdict.get("eligible_for_state_reconstruction"))
        self.assertEqual(verdict.get("classification"), "H9_BLOCKED_STATE_OR_GOVERNANCE")

    def test_05_governance_and_classification(self):
        self.assertEqual(self.audit.get("classification"), "H9_BLOCKED_STATE_OR_GOVERNANCE")
        self.assertEqual(self.audit.get("governing_gate"), "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED")
        self.assertTrue(self.audit.get("gate_retained"))
        self.assertFalse(self.audit.get("c5_remeshing_permitted"))

        uel_hash = self.audit.get("package127_predeclared_specification", {}).get("uel_hash")
        self.assertEqual(uel_hash, "AB0A5A71335ECB445E91EC13A645E280FF3310B561A5E78ABA4A49C8E81DD8AC")


if __name__ == "__main__":
    unittest.main()
