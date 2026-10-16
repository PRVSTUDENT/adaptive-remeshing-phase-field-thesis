import hashlib
import json
import os
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestMode1F1508IsolateReleaseAndHoldDamageGrowth(unittest.TestCase):
    """
    Unit test suite for Task F1508:
    Isolating whether crack-tip damage jump (d_max = 0.0904 -> 0.3256) is driven by
    mesh refinement / singularity resolution or by an algorithmic defect, and verifying
    the same-mesh self-transfer release-and-hold diagnostic model.
    """

    def setUp(self):
        self.p40_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "40_method_b_corrected_propagation_14k"
        self.p49_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer"
        self.evidence_1412465 = self.p40_dir / "evidence_1412465"
        self.fine_state_json = self.evidence_1412465 / "fine_baseline_14k_u0050_state.json"
        self.samemesh_inp = self.p49_dir / "M1_MC_STAGE_C1_1_SAMEMESH_RELHOLD.inp"
        self.samemesh_pbs = self.p49_dir / "submit_M1_MC_STAGE_C1_1_SAMEMESH_RELHOLD.pbs"
        self.samemesh_auth = self.p49_dir / "METHOD_C_STAGE_C1_1_SAMEMESH_AUTHORIZATION.json"
        self.hpc_ledger = REPO_ROOT / "project_coordination" / "HPC_JOB_LEDGER.csv"
        self.batch_receipts = REPO_ROOT / "project_coordination" / "MODE1_BATCH_SUBMISSIONS.json"

    def test_01_fine_baseline_state_extraction_and_damage_ground_truth(self):
        """Test 1: Verify continuous fine baseline state at u = 0.0050 mm has d_max = 0.3181, NOT 0.092."""
        self.assertTrue(self.fine_state_json.exists(), f"Missing fine baseline state: {self.fine_state_json}")
        with open(self.fine_state_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["mesh_elements"], 14483)
        self.assertEqual(data["frame_id"], 2000)
        self.assertAlmostEqual(data["step_time"], 1.0, places=4)

        # Ground truth: continuous fine baseline peak damage at u = 0.0050 mm is already ~0.3181!
        d_max = data["max_damage"]
        self.assertGreater(d_max, 0.30)
        self.assertLess(d_max, 0.33)
        self.assertAlmostEqual(d_max, 0.31814, places=3)
        self.assertEqual(data["max_damage_element"], 661)

        # Peak history
        h_max = data["max_history"]
        self.assertGreater(h_max, 0.70)
        self.assertLess(h_max, 0.85)

    def test_02_reaction_force_discrepancy_reconciliation(self):
        """Test 2: Reconcile 653.089 N (coarse donor) vs 661.725 N (continuous fine baseline) discrepancy."""
        ld_csv = self.evidence_1412465 / "corrected_method_b_load_displacement.csv"
        self.assertTrue(ld_csv.exists(), f"Missing load-displacement CSV: {ld_csv}")

        # Check line 2000 (0-indexed: line 0 is header, line 2000 is Step 1 end at u = 0.0050 mm)
        lines = ld_csv.read_text(encoding="utf-8").splitlines()
        header = lines[0].split(",")
        self.assertIn("u_mm", header[1].lower())
        self.assertIn("f_kn", header[2].lower())

        row_2000 = [x.strip() for x in lines[2000].split(",")]
        u_val = float(row_2000[1])
        rf_kn = float(row_2000[2])
        rf_n = rf_kn * 1000.0

        self.assertAlmostEqual(u_val, 0.0050, places=4)
        self.assertAlmostEqual(rf_n, 661.725, places=1)

        # Proves intrinsic compliance gap between coarse (653.089 N) and fine (661.725 N) is +8.636 N (+1.322%)
        delta_rf = rf_n - 653.0886
        self.assertGreater(delta_rf, 8.5)
        self.assertLess(delta_rf, 8.8)

    def test_03_samemesh_relhold_deck_structure_and_hashes(self):
        """Test 3: Verify same-mesh self-transfer release-and-hold input deck structure and SHA-256."""
        self.assertTrue(self.samemesh_inp.exists(), f"Missing input deck: {self.samemesh_inp}")
        deck_sha = hashlib.sha256(self.samemesh_inp.read_bytes()).hexdigest().lower()
        self.assertEqual(deck_sha, "83a1a7bc2b4014f14787b3c6d1fa56c069d9562f3bda27834847d6fcc78e66e8")

        # Check key sections
        content = self.samemesh_inp.read_text(encoding="utf-8", errors="ignore")
        self.assertIn("*USER ELEMENT, TYPE=U1", content)
        self.assertIn("*USER ELEMENT, TYPE=U3", content)
        self.assertIn("*INITIAL CONDITIONS, TYPE=SOLUTION", content)
        self.assertIn("*STEP, NAME=Step-1-Equilibrate", content)
        self.assertIn("*STEP, NAME=Step-2-ReleaseHold", content)
        self.assertIn("*BOUNDARY, OP=NEW", content)
        self.assertIn("N_RP, 2, 2, 5.0000000000e-03", content)

    def test_04_pbs_script_and_notification_contract(self):
        """Test 4: Verify PBS script syntax, resources, and notification integration."""
        self.assertTrue(self.samemesh_pbs.exists(), f"Missing PBS script: {self.samemesh_pbs}")
        pbs_sha = hashlib.sha256(self.samemesh_pbs.read_bytes()).hexdigest().lower()
        self.assertEqual(pbs_sha, "cb54c6622722f13d59547df0c71d409ede072ad27e8d86017164ecf41308b60c")

        content = self.samemesh_pbs.read_text(encoding="utf-8")
        self.assertIn("#PBS -N M1_MC_C1_1_SM", content)
        self.assertIn("#PBS -l select=1:ncpus=1:mem=8gb", content)
        self.assertIn("#PBS -l walltime=01:00:00", content)
        self.assertIn("#PBS -q entry_imfdfkmq", content)
        self.assertIn("#PBS -m abe", content)
        self.assertIn("notification_load_config", content)
        self.assertIn("notification_install_terminal_trap", content)

    def test_05_batch_authorization_and_job_ledger_receipt(self):
        """Test 5: Verify batch authorization manifest and HPC submission ledger receipt for Job 1414558."""
        self.assertTrue(self.samemesh_auth.exists(), f"Missing auth manifest: {self.samemesh_auth}")
        with open(self.samemesh_auth, "r", encoding="utf-8") as f:
            auth = json.load(f)

        self.assertEqual(auth["batch_name"], "MODE1_METHOD_C_STAGE_C1_1")
        self.assertEqual(auth["max_submissions"], 1)
        self.assertEqual(len(auth["jobs"]), 1)
        self.assertEqual(auth["jobs"][0]["id"], "samemesh_relhold_diagnostic")
        self.assertEqual(auth["jobs"][0]["input"], "M1_MC_STAGE_C1_1_SAMEMESH_RELHOLD.inp")

        # Verify HPC job ledger has 1414558 recorded
        self.assertTrue(self.hpc_ledger.exists())
        ledger_text = self.hpc_ledger.read_text(encoding="utf-8")
        self.assertIn("1414558.mmaster02", ledger_text)
        self.assertIn("M1_MC_STAGE_C1_1_SAMEMESH_RELHOLD", ledger_text)

    def test_06_physical_singularity_sharpening_resolution(self):
        """Test 6: Verify scientific proof that damage relaxation in Job 1414550 matches fine baseline continuum."""
        relhold_eval_file = self.p49_dir / "evidence" / "1414550.mmaster02" / "STAGE_C1_1_RELHOLD_EVALUATION_1414550.json"
        self.assertTrue(relhold_eval_file.exists())
        with open(relhold_eval_file, "r", encoding="utf-8") as f:
            ev = json.load(f)

        d_relaxed_1414550 = ev["step2_release_inc10_terminal"]["sdv14_max"]  # 0.325563
        e_frac_relaxed_1414550 = ev["step2_release_inc10_terminal"]["e_frac_mJ"]  # 0.036947

        with open(self.fine_state_json, "r", encoding="utf-8") as f:
            fine_baseline = json.load(f)

        d_fine_baseline = fine_baseline["max_damage"]  # 0.318142

        # Relative difference between relaxed damage and authentic fine baseline is only 2.33%!
        rel_diff_pct = abs(d_relaxed_1414550 - d_fine_baseline) / d_fine_baseline * 100.0
        self.assertLess(rel_diff_pct, 3.0)

        # Fracture energy difference vs continuous fine baseline (0.036786 mJ) is only 0.438%!
        e_frac_baseline = 0.036786
        e_frac_diff_pct = abs(e_frac_relaxed_1414550 - e_frac_baseline) / e_frac_baseline * 100.0
        self.assertLess(e_frac_diff_pct, 0.50)


if __name__ == "__main__":
    unittest.main()
