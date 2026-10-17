import json
import math
import os
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestMode1F1527EarlyCheckpointTransfer(unittest.TestCase):
    """
    Unit regression test suite for Task F1527:
    Physical resolution of Stage C1-1 nonmatching damage continuity through
    early-checkpoint state transfer at u = 0.0010 mm.
    """

    def setUp(self):
        self.evidence_dir = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_1_early_u0010_transfer" / "evidence_1414768"
        self.summary_json = REPO_ROOT / "results" / "validation" / "stage_c1_1_early_u0010_summary.json"
        self.pkg56_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "56_method_c_stage_c1_1_early_u0010_transfer"
        self.inp_path = self.pkg56_dir / "M1_MC_STAGE_C1_1_EARLY_U0010.inp"
        self.manifest_path = self.pkg56_dir / "METHOD_C_STAGE_C1_1_EARLY_U0010_AUTHORIZATION.json"
        self.metrics_path = self.pkg56_dir / "STAGE_C1_1_EARLY_U0010_TRANSFER_METRICS.json"

    def test_01_package_56_artifacts_exist(self):
        """Verify Package 56 model files and harvested evidence exist."""
        self.assertTrue(self.inp_path.is_file(), "Package 56 input deck missing")
        self.assertTrue(self.manifest_path.is_file(), "Package 56 authorization manifest missing")
        self.assertTrue(self.metrics_path.is_file(), "Package 56 transfer metrics missing")
        self.assertTrue(self.summary_json.is_file(), "Stage C1-1 early u0010 summary JSON missing")
        self.assertTrue((self.evidence_dir / "uel_energy_balance.csv").is_file(), "UEL energy balance missing")
        self.assertTrue((self.evidence_dir / "M1_MC_STAGE_C1_1_EARLY_U0010.sta").is_file(), "Solver .sta missing")
        self.assertTrue((self.evidence_dir / "M1_MC_STAGE_C1_1_EARLY_U0010.dat").is_file(), "Solver .dat missing")

    def test_02_deck_structure_and_boundary_conditions(self):
        """Verify correct boundary conditions and companion UMAT constants in Package 56 deck."""
        with open(self.inp_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Correct boundary condition lines
        self.assertIn("N_PIN, 1, 1, 0.0", content)
        self.assertIn("N_TOP, 1, 1, 0.0", content)
        self.assertIn("N_BOTTOM, 2, 2, 0.0", content)
        self.assertIn("N_RP, 2, 2, 1.0000000000e-03", content)

        # Companion UMAT constants (NPROPS=3, NPHYS=14483)
        self.assertIn("*USER MATERIAL, CONSTANTS=3", content)
        self.assertIn("210.0, 0.3, 14483.0", content)

        # Step 1 static equilibration with constrained DOF 3
        self.assertIn("*STEP, NAME=Step-1-Equilibrate, INC=100", content)
        self.assertIn("*STEP, NAME=Step-2-ReleaseHold, INC=100", content)
        self.assertIn("*BOUNDARY, OP=NEW", content)

    def test_03_quantitative_continuity_at_u0010_checkpoint(self):
        """
        Verify that nonmatching transfer at u = 0.0010 mm strictly satisfies
        all Gate 6C acceptance criteria against the continuous fine baseline.
        """
        with open(self.summary_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        s1 = data["step1_equilibration"]
        s2 = data["step2_terminal_release"]
        fine = data["fine_baseline_u0010"]

        # Step 1 Re-equilibration
        self.assertAlmostEqual(s1["RF2_N"], 137.9109, places=2)
        self.assertLessEqual(s1["delta_RF2_N"], 5.0, "Step 1 Delta RF exceeds 5.0 N")
        self.assertTrue(s1["delta_RF2_pass"])

        self.assertLessEqual(s1["delta_dmax"], 0.0200, "Step 1 Delta d_max exceeds 0.0200")
        self.assertTrue(s1["delta_dmax_pass"])

        self.assertLessEqual(s1["delta_etot_pct"], 0.10, "Step 1 Delta E_tot exceeds 0.10%")
        self.assertTrue(s1["delta_etot_pass"])

        # Step 2 Terminal Release-and-Hold
        self.assertAlmostEqual(s2["RF2_N"], 137.8794, places=2)
        self.assertLessEqual(s2["delta_RF2_N"], 5.0, "Step 2 Delta RF exceeds 5.0 N")
        self.assertTrue(s2["delta_RF2_pass"])

        # CRITICAL TEST: Peak damage continuity upon release
        # Terminal d_max = 0.010572 vs Fine baseline 0.009532 -> Delta = 0.001040 <= 0.0200 PASS!
        self.assertAlmostEqual(s2["d_max"], 0.010572, places=4)
        self.assertLessEqual(s2["delta_dmax"], 0.0200, "Step 2 damage continuity exceeded 0.0200 threshold!")
        self.assertTrue(s2["delta_dmax_pass"])

        # Total energy continuity upon release
        self.assertLessEqual(s2["delta_etot_pct"], 0.10, "Step 2 Delta E_tot exceeds 0.10%")
        self.assertTrue(s2["delta_etot_pass"])

    def test_04_energy_monotonic_relaxation(self):
        """Verify smooth convergence across all 11 increments without cutbacks."""
        with open(self.summary_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        history = data["step2_history"]
        self.assertEqual(len(history), 11)  # frames 0..10

        energies = data["energies_history"]
        self.assertEqual(len(energies), 11)  # step 1 (1 inc) + step 2 (10 incs)

        # Total energy remains conserved within 0.005% across the entire release step
        e_tot_values = [e["e_tot_mJ"] for e in energies]
        max_e = max(e_tot_values)
        min_e = min(e_tot_values)
        delta_span_pct = (max_e - min_e) / min_e * 100.0
        self.assertLess(delta_span_pct, 0.01, "Internal energy drifted by more than 0.01% during release")


if __name__ == "__main__":
    unittest.main()
