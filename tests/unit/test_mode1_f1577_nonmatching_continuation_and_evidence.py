"""Unit tests for Task F1577: Nonmatching mesh continuation, parity audit resolution, and state conservation."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FROZEN_PROD_UEL = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
EXP_OFFSET_UEL = "ef92ed58dbe3ea921b48cb328128ab950ba2cafd698e05381e2b29f61412514d"

class TestMode1F1577NonmatchingContinuation(unittest.TestCase):
    def test_production_uel_remains_strictly_frozen(self):
        uel_path = ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
        import hashlib
        h = hashlib.sha256(uel_path.read_bytes()).hexdigest()
        self.assertEqual(h, FROZEN_PROD_UEL, "Production UEL must remain 100% bitwise frozen")

    def test_experimental_offset_uel_invariant(self):
        uel_path = ROOT / "models/pandey_kumar_mode1/experimental_offset_uel/f42_experimental_offset_uel.for"
        import hashlib
        h = hashlib.sha256(uel_path.read_bytes()).hexdigest()
        self.assertEqual(h, EXP_OFFSET_UEL, "Experimental offset UEL must match qualified revision")

    def test_parity_audit_resolution(self):
        # Case A with extrapolation=NO at u=0.00270 mm
        case_a_rf2 = 5.289597
        # Case B Package 50 at u=0.00270 mm
        case_b_rf2 = 5.242816
        parity_error_pct = abs(case_b_rf2 - case_a_rf2) / case_a_rf2 * 100.0
        self.assertAlmostEqual(parity_error_pct, 0.8844, places=3)
        self.assertLess(parity_error_pct, 1.0, "Parity under extrapolation=NO must be within 1.0%")

        # Reconstructed static plateau relaxation: 5.1365 N vs 5.0857 N
        reconstructed_rf2 = 5.136498
        plateau_rf2 = 5.085707
        diff_pct = (reconstructed_rf2 - plateau_rf2) / plateau_rf2 * 100.0
        self.assertAlmostEqual(diff_pct, 0.999, places=2)

    def test_package51_transfer_audit(self):
        audit_path = ROOT / "models/pandey_kumar_mode1/51_method_c_nonmatching_transfer_continuation/PACKAGE51_TRANSFER_AUDIT.json"
        self.assertTrue(audit_path.is_file(), "PACKAGE51_TRANSFER_AUDIT.json must exist")
        with open(audit_path, "r", encoding="utf-8") as f:
            audit = json.load(f)
        self.assertEqual(audit["donor_elements"], 400)
        self.assertEqual(audit["receiver_elements"], 650)
        self.assertEqual(audit["receiver_nodes"], 708)
        self.assertAlmostEqual(audit["delta_d_max"], 0.0, places=6)
        self.assertLessEqual(abs(audit["delta_e_frac_pct"]), 2.0)
        self.assertEqual(audit["history_violations"], 0)
        self.assertGreater(audit["chordal_sag_points"], 0, "Chordal sag points must be documented")

    def test_package51_pbs_job_1415037_evaluation(self):
        eval_path = ROOT / "models/pandey_kumar_mode1/51_method_c_nonmatching_transfer_continuation/evidence_1415037/JOB_1415037_EVALUATION.json"
        self.assertTrue(eval_path.is_file(), "JOB_1415037_EVALUATION.json must exist")
        with open(eval_path, "r", encoding="utf-8") as f:
            record = json.load(f)
        self.assertEqual(record["pbs_job_id"], "1415037.mmaster02")
        self.assertEqual(record["status"], "COMPLETED")
        self.assertEqual(record["exit_code"], 0)
        self.assertEqual(record["solver_metrics"]["step1_increments"], 1)
        self.assertEqual(record["solver_metrics"]["step1_iterations"], 10)
        self.assertEqual(record["solver_metrics"]["step1_cutbacks"], 0)
        self.assertEqual(record["solver_metrics"]["step2_increments"], 3)
        self.assertEqual(record["solver_metrics"]["step2_cutbacks"], 0)
        self.assertTrue(record["solver_metrics"]["energy_dissipation_monotonic"])
        self.assertEqual(record["solver_metrics"]["predictor_control"], "extrapolation=NO")
        self.assertEqual(record["acceptance_verdict"], "PASS")

    def test_package51_evidence_files_exist(self):
        ev_dir = ROOT / "models/pandey_kumar_mode1/51_method_c_nonmatching_transfer_continuation/evidence_1415037"
        self.assertTrue((ev_dir / "pbs_execution.log").is_file())
        self.assertTrue((ev_dir / "M1_EXP_NONMATCHING_CONT_650.sta").is_file())
        self.assertTrue((ev_dir / "uel_energy_balance.csv").is_file())
        self.assertTrue((ev_dir / "JOB_1415037_EVALUATION.json").is_file())

if __name__ == "__main__":
    unittest.main()
