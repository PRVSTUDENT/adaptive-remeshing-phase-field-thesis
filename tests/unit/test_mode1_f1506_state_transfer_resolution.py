import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG49 = ROOT / "models/pandey_kumar_mode1/49_method_c_stage_c1_1_nonmatching_transfer"
EVIDENCE = PKG49 / "evidence/1414550.mmaster02"


class TestMode1F1506StateTransferResolution(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PKG49.is_dir(), "Package 49 directory missing")
        self.assertTrue(EVIDENCE.is_dir(), "Evidence directory 1414550 missing")

    def test_01_evidence_files_exist_and_hash(self):
        eval_file = EVIDENCE / "STAGE_C1_1_RELHOLD_EVALUATION_1414550.json"
        self.assertTrue(eval_file.is_file(), "Evaluation JSON missing")
        data = json.loads(eval_file.read_text(encoding="utf-8"))
        self.assertEqual(data["pbs_job_id"], "1414550.mmaster02")
        self.assertEqual(data["terminal_exit_status"], 0)
        self.assertEqual(data["total_cutbacks"], 0)
        self.assertEqual(data["step1_increments"], 1)
        self.assertEqual(data["step2_increments"], 10)

    def test_02_step1_constrained_equil_rf_and_damage(self):
        eval_file = EVIDENCE / "STAGE_C1_1_RELHOLD_EVALUATION_1414550.json"
        data = json.loads(eval_file.read_text(encoding="utf-8"))
        s1 = data["step1_equil"]
        # RF must be within 5.0 N of donor 653.0886 N
        self.assertAlmostEqual(s1["rf2_N"], 648.5472, places=3)
        self.assertLessEqual(s1["delta_rf_vs_donor_N"], 5.00)
        # Damage peak retained near 0.092105
        self.assertAlmostEqual(s1["sdv14_max"], 0.090403, places=4)

    def test_03_step2_internal_energy_conservation(self):
        eval_file = EVIDENCE / "STAGE_C1_1_RELHOLD_EVALUATION_1414550.json"
        data = json.loads(eval_file.read_text(encoding="utf-8"))
        s2 = data["step2_release_inc10_terminal"]
        # Internal energy strictly conserved during release-and-hold (Delta E_tot < 0.10%)
        self.assertLess(s2["internal_energy_conservation_in_step2_pct"], 0.10)
        self.assertAlmostEqual(s2["internal_energy_conservation_in_step2_pct"], 0.0682, places=2)

    def test_04_step2_fracture_energy_fine_baseline_agreement(self):
        eval_file = EVIDENCE / "STAGE_C1_1_RELHOLD_EVALUATION_1414550.json"
        data = json.loads(eval_file.read_text(encoding="utf-8"))
        base = data["continuous_fine_baseline_comparison"]
        # RelHold terminal fracture energy (0.03695 mJ) matches continuous fine baseline (0.03679 mJ) within 0.50%
        self.assertAlmostEqual(base["relhold_terminal_e_frac_mJ"], 0.036947, places=4)
        self.assertLess(base["e_frac_match_pct"], 0.50)
        self.assertAlmostEqual(base["e_frac_match_pct"], 0.438, places=2)

    def test_05_hpc_ledger_and_batch_submissions(self):
        ledger = (ROOT / "project_coordination/HPC_JOB_LEDGER.csv").read_text(encoding="utf-8")
        self.assertIn("1414550.mmaster02", ledger)
        self.assertIn("F,0,COMPLETED_49S_STEP1_EQUIL_RF_4P54N_PASS_STEP2_RELEASE_HOLD_CONVERGED_10_INCS_0_CUTBACKS", ledger)

        batch = json.loads((ROOT / "project_coordination/MODE1_BATCH_SUBMISSIONS.json").read_text(encoding="utf-8"))
        # Must have record for relhold_diagnostic
        found = False
        for bkey, bval in batch.items():
            if "relhold_diagnostic" in bval and bval["relhold_diagnostic"]["pbs_job_id"] == "1414550.mmaster02":
                found = True
                break
        self.assertTrue(found, "Job 1414550 missing from MODE1_BATCH_SUBMISSIONS.json")

    def test_06_active_task_forward_continuation_blocked(self):
        task = json.loads((ROOT / "project_coordination/ACTIVE_TASK.json").read_text(encoding="utf-8"))
        self.assertEqual(task["task_id"], "F1506-RESOLVE-METHOD-C-STATE-TRANSFER")
        self.assertIn("1414550.mmaster02", task["completed_pbs_job_ids"])
        self.assertIn("gate 6c", task["phase"].lower())
        self.assertIn("forward continuation remains strictly held", task["phase"].lower())


if __name__ == "__main__":
    unittest.main()
