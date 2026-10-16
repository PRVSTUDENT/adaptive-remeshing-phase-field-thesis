import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG49 = ROOT / "models/pandey_kumar_mode1/49_method_c_stage_c1_1_nonmatching_transfer"
EVIDENCE = PKG49 / "evidence/1414550.mmaster02"


class TestMode1F1507EvaluateReleaseAndHoldExperiment(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PKG49.is_dir(), "Package 49 directory missing")
        self.assertTrue(EVIDENCE.is_dir(), "Evidence directory 1414550 missing")

    def test_01_job_1414550_terminal_accounting_and_files(self):
        """Verify Job 1414550 completed Exit 0 with all evidence files present."""
        sta_file = EVIDENCE / "M1_MC_STAGE_C1_1_RELHOLD.sta"
        msg_file = EVIDENCE / "M1_MC_STAGE_C1_1_RELHOLD.msg"
        dat_file = EVIDENCE / "M1_MC_STAGE_C1_1_RELHOLD.dat"
        log_file = EVIDENCE / "pbs_execution_relhold.log"
        csv_file = EVIDENCE / "uel_energy_balance.csv"
        json_file = EVIDENCE / "STAGE_C1_1_RELHOLD_EVALUATION_1414550.json"

        for f in [sta_file, msg_file, dat_file, log_file, csv_file, json_file]:
            self.assertTrue(f.is_file(), f"Missing required evidence file: {f.name}")

        # Check exit 0 and zero cutbacks in .sta
        sta_text = sta_file.read_text(encoding="utf-8")
        self.assertIn("THE ANALYSIS HAS COMPLETED SUCCESSFULLY", sta_text)
        self.assertIn("2    10   1     0     3     3", sta_text)

        # Check PBS log exit code
        log_text = log_file.read_text(encoding="utf-8")
        self.assertIn("Abaqus Finished with Exit Code: 0", log_text)

    def test_02_dof3_release_contract_and_equation_count(self):
        """Verify DOF 3 was genuinely released, equations increased from 28k to 43k."""
        msg_text = (EVIDENCE / "M1_MC_STAGE_C1_1_RELHOLD.msg").read_text(encoding="utf-8")
        self.assertIn("NUMBER OF EQUATIONS:     43317", msg_text)
        self.assertIn("TOTAL OF         11  INCREMENTS", msg_text)
        self.assertIn("0  CUTBACKS IN AUTOMATIC INCREMENTATION", msg_text)

        # Check input deck boundary definitions
        inp_text = (PKG49 / "M1_MC_STAGE_C1_1_RELHOLD.inp").read_text(encoding="utf-8")
        self.assertIn("*STEP, NAME=Step-1-Equilibrate", inp_text)
        self.assertIn("*STEP, NAME=Step-2-ReleaseHold", inp_text)
        self.assertIn("*BOUNDARY, OP=NEW", inp_text)

    def test_03_quantitative_measurements_step1_vs_step2(self):
        """Verify exact quantitative measurements across Step 1 and Step 2."""
        data = json.loads((EVIDENCE / "STAGE_C1_1_RELHOLD_EVALUATION_1414550.json").read_text(encoding="utf-8"))
        s1 = data["step1_equil"]
        s2 = data["step2_release_inc10_terminal"]

        # Step 1: Constrained equilibrium
        self.assertAlmostEqual(s1["rf2_N"], 648.5472, places=3)
        self.assertAlmostEqual(s1["delta_rf_vs_donor_N"], 4.5414, places=3)
        self.assertAlmostEqual(s1["e_elas_mJ"], 1.621368, places=5)
        self.assertAlmostEqual(s1["e_frac_mJ"], 0.029148, places=5)
        self.assertAlmostEqual(s1["e_tot_mJ"], 1.650516, places=5)
        self.assertAlmostEqual(s1["sdv14_max"], 0.090403, places=4)

        # Step 2: Unconstrained release and hold
        self.assertAlmostEqual(s2["rf2_N"], 644.9771, places=3)
        self.assertAlmostEqual(s2["e_elas_mJ"], 1.612442, places=5)
        self.assertAlmostEqual(s2["e_frac_mJ"], 0.036947, places=5)
        self.assertAlmostEqual(s2["e_tot_mJ"], 1.649390, places=5)
        self.assertAlmostEqual(s2["sdv14_max"], 0.325563, places=4)
        self.assertAlmostEqual(s2["sdv14_domain_avg"], 0.019758, places=5)

    def test_04_energy_conservation_and_fine_baseline_recovery(self):
        """Verify internal energy conservation and spontaneous fracture energy convergence."""
        data = json.loads((EVIDENCE / "STAGE_C1_1_RELHOLD_EVALUATION_1414550.json").read_text(encoding="utf-8"))
        s2 = data["step2_release_inc10_terminal"]
        base = data["continuous_fine_baseline_comparison"]

        # Total energy conserved during hold to within 0.0682%
        self.assertAlmostEqual(s2["internal_energy_conservation_in_step2_pct"], 0.0682, places=2)

        # Fracture energy matches continuous fine baseline within 0.438%
        self.assertAlmostEqual(base["relhold_terminal_e_frac_mJ"], 0.036947, places=4)
        self.assertAlmostEqual(base["baseline_e_frac_mJ"], 0.036786, places=4)
        self.assertAlmostEqual(base["e_frac_match_pct"], 0.438, places=2)

    def test_05_scientific_verdict_and_governance_hold(self):
        """Verify strict Gate 6C evaluation: Unstable release -> Gate 6C FAIL -> Forward HELD."""
        data = json.loads((EVIDENCE / "STAGE_C1_1_RELHOLD_EVALUATION_1414550.json").read_text(encoding="utf-8"))
        s1 = data["step1_equil"]
        s2 = data["step2_release_inc10_terminal"]

        # Against strict predeclared continuity thresholds vs coarse donor (RF <= 5 N, d_max <= 0.020, E_tot <= 0.10%):
        step1_rf_pass = s1["delta_rf_vs_donor_N"] <= 5.0  # PASS (4.54 N)
        step1_d_pass = abs(s1["sdv14_max"] - 0.092105) <= 0.020  # PASS (0.0017)
        step1_energy_pass = abs(s1["e_tot_mJ"] - 1.663384) / 1.663384 <= 0.0010  # FAIL (0.774%)

        step2_rf_pass = s2["delta_rf_vs_donor_N"] <= 5.0  # FAIL (8.11 N)
        step2_d_pass = abs(s2["sdv14_max"] - 0.092105) <= 0.020  # FAIL (0.2335)
        step2_energy_pass = abs(s2["e_tot_mJ"] - 1.663384) / 1.663384 <= 0.0010  # FAIL (0.841%)

        self.assertTrue(step1_rf_pass)
        self.assertTrue(step1_d_pass)
        self.assertFalse(step1_energy_pass)
        self.assertFalse(step2_rf_pass)
        self.assertFalse(step2_d_pass)
        self.assertFalse(step2_energy_pass)

        # Confirm task ledger records forward held
        ledger = (ROOT / "project_coordination/TASK_LEDGER.csv").read_text(encoding="utf-8")
        self.assertIn("JOB_1414550_EXIT0_RELHOLD_CONVERGED_10_INCS_0_CUTBACKS__EFRAC_RELAXATION_MATCHES_FINE_BASELINE_0P438PCT__FORWARD_REMAINS_HELD_GATE_6C", ledger)


if __name__ == "__main__":
    unittest.main()
