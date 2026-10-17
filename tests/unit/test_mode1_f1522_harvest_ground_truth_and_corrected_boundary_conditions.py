import hashlib
import json
import math
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestMode1F1522HarvestGroundTruthAndCorrectedBoundaryConditions(unittest.TestCase):
    """
    Unit test suite for Task F1522:
    - Harvesting continuous baseline enriched ground truth (Job 1414571)
    - Verifying pointwise displacement comparison proving lateral boundary condition defect
    - Verifying corrected boundary condition same-mesh diagnostic (Job 1414758)
    - Confirming restoration of reaction force and machine-precision energy preservation
    - Validating state transfer engine updates with N_PIN, N_TOP lateral constraint, and NLGEOM=NO.
    """

    def setUp(self):
        self.p50_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "50_method_b_fine_baseline_enriched"
        self.p51_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "51_method_c_stage_c1_1_samemesh_corrected_bc"
        self.evidence_1414758_dir = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_1_samemesh_corrected_bc" / "evidence_1414758"
        self.engine_file = REPO_ROOT / "scripts" / "state_transfer" / "mode1_state_transfer_engine.py"
        self.disp_summary = REPO_ROOT / "results" / "validation" / "displacement_comparison_summary.json"
        self.ground_truth_json = self.p50_dir / "fine_baseline_ground_truth_u0050.json"
        self.ground_truth_energy = self.p50_dir / "uel_energy_balance.csv"

    def test_01_enriched_baseline_ground_truth_harvested_and_verified(self):
        """Test 1: Verify enriched continuous baseline ground truth harvested and energetic identity confirmed."""
        self.assertTrue(self.ground_truth_json.exists(), "Ground truth JSON must exist locally")
        self.assertTrue(self.ground_truth_energy.exists(), "Ground truth energy CSV must exist locally")

        with open(self.ground_truth_json, "r", encoding="utf-8") as f:
            gt_data = json.load(f)

        self.assertIn("nodal_state", gt_data)
        self.assertIn("elem_sdv", gt_data)
        self.assertEqual(len(gt_data["nodal_state"]), 14457)  # 14456 mesh nodes + RP 999999
        self.assertEqual(len(gt_data["elem_sdv"]), 14483)

        # Verify ground truth energetic values at u = 0.0050 mm
        with open(self.ground_truth_energy, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        last_line = lines[-1].split(",")
        self.assertEqual(int(last_line[0]), 1)  # Step 1
        self.assertEqual(int(last_line[1]), 2000)  # Inc 2000
        e_elas = float(last_line[4]) * 1000.0  # mJ
        e_frac = float(last_line[5]) * 1000.0  # mJ
        e_tot = float(last_line[6]) * 1000.0   # mJ

        self.assertAlmostEqual(e_elas, 1.6543134, places=6)
        self.assertAlmostEqual(e_frac, 0.0367858, places=6)
        self.assertAlmostEqual(e_tot, 1.6910993, places=6)

    def test_02_pointwise_displacement_comparison_proved_lateral_contraction_defect(self):
        """Test 2: Verify pointwise displacement comparison proved the missing lateral constraint caused the compliance deficit."""
        self.assertTrue(self.disp_summary.exists(), "Displacement comparison summary must exist")

        with open(self.disp_summary, "r", encoding="utf-8") as f:
            disp_data = json.load(f)

        self.assertIn("rel_l2_displacement_error_pct", disp_data)
        rel_l2_pct = disp_data["rel_l2_displacement_error_pct"]
        self.assertAlmostEqual(rel_l2_pct, 34.19, places=1)
        self.assertGreater(disp_data["max_displacement_diff_mm"], 0.0013)
        self.assertEqual(disp_data["max_displacement_diff_node"], 70)

    def test_03_corrected_samemesh_experiment_job_1414758_restores_reaction_force(self):
        """Test 3: Verify Job 1414758 restores reaction force from 644.56 N back to 661.73 N matching ground truth to 0.00016 N."""
        results_file = self.evidence_1414758_dir / "corrected_samemesh_results.json"
        self.assertTrue(results_file.exists(), "Job 1414758 results JSON must exist")

        with open(results_file, "r", encoding="utf-8") as f:
            res = json.load(f)

        step1_frames = res["Step-1-Equilibrate"]
        self.assertEqual(len(step1_frames), 2)  # Frame 0 and Frame 1
        term_step1 = step1_frames[1]

        # rf_bot_y is in kN (negative in compression on bottom reacting upward tension)
        rf_step1_N = abs(term_step1["rf_bot_y"]) * 1000.0
        rf_target_N = 661.72540

        # Verify restoration of the entire -17.17 N deficit
        self.assertGreater(rf_step1_N, 660.0, "Reaction force must be restored above 660 N")
        rf_diff_N = abs(rf_step1_N - rf_target_N)
        self.assertLess(rf_diff_N, 0.01, f"Reaction force difference {rf_diff_N} N must be < 0.01 N")
        self.assertAlmostEqual(rf_step1_N, 661.72524, places=4)

        # Damage maximum fidelity
        self.assertAlmostEqual(term_step1["d_max"], 0.3181415, places=5)

    def test_04_release_and_hold_stability_and_energy_conservation(self):
        """Test 4: Verify Step 2 release-and-hold stability and machine-precision energy conservation."""
        results_file = self.evidence_1414758_dir / "corrected_samemesh_results.json"
        energy_csv = self.evidence_1414758_dir / "uel_energy_balance.csv"
        self.assertTrue(energy_csv.exists(), "Job 1414758 energy CSV must exist")

        with open(results_file, "r", encoding="utf-8") as f:
            res = json.load(f)

        step2_frames = res["Step-2-ReleaseHold"]
        self.assertEqual(len(step2_frames), 11)  # Frame 0 to Frame 10

        rf_init = abs(step2_frames[0]["rf_bot_y"]) * 1000.0
        rf_final = abs(step2_frames[10]["rf_bot_y"]) * 1000.0
        delta_rf = abs(rf_final - rf_init)
        self.assertLess(delta_rf, 0.01, "Release-and-hold force drift must be < 0.01 N (well below 5.0 N threshold)")

        dmax_init = step2_frames[0]["d_max"]
        dmax_final = step2_frames[10]["d_max"]
        delta_dmax = abs(dmax_final - dmax_init)
        self.assertLess(delta_dmax, 0.001, "Release-and-hold damage drift must be < 0.001 (well below 0.02 threshold)")

        # Verify energy conservation from CSV
        with open(energy_csv, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("Step")]

        # Step 1 Inc 1 (line 0)
        p1 = lines[0].split(",")
        e_tot_step1 = float(p1[6]) * 1000.0  # mJ
        # Continuous baseline is 1.6910993 mJ
        err_pct = abs(e_tot_step1 - 1.6910993) / 1.6910993 * 100.0
        self.assertLess(err_pct, 0.01, f"Step 1 total energy error {err_pct}% must be < 0.01%")

        # Step 2 Inc 10 (line 10)
        p10 = lines[10].split(",")
        e_tot_step2_term = float(p10[6]) * 1000.0  # mJ
        self.assertAlmostEqual(e_tot_step2_term, 1.6910993, places=6)

    def test_05_state_transfer_engine_boundary_conditions_and_linear_kinematics(self):
        """Test 5: Verify mode1_state_transfer_engine.py is updated with N_PIN, N_TOP lateral constraint, and NLGEOM=NO."""
        self.assertTrue(self.engine_file.exists())
        text = self.engine_file.read_text(encoding="utf-8")

        # N_PIN node set generation
        self.assertIn("lines.append(\"*NSET, NSET=N_PIN\")", text)
        self.assertIn("lines.append(\"N_PIN, 1, 1, 0.0\")", text)

        # N_TOP lateral constraint ux=0
        self.assertIn("lines.append(\"N_TOP, 1, 1, 0.0\")", text)

        # NLGEOM=NO across continuation steps
        self.assertIn("NAME=Step-1-Equilibrate, NLGEOM=NO", text)
        self.assertIn("NAME=Step-2-Continue, NLGEOM=NO", text)
        self.assertNotIn("NAME=Step-1-Equilibrate, NLGEOM=YES", text)
        self.assertNotIn("NAME=Step-2-Continue, NLGEOM=YES", text)


if __name__ == "__main__":
    unittest.main()
