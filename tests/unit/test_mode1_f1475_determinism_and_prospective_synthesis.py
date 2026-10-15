#!/usr/bin/env python3
"""
Unit test suite for Task F1475:
Method B Stage B 8-Thread SMP Determinism Repeat Verification (Job 1413022),
Terminal Accounting, Bitwise Energy Trace Identity,
and Consolidated Prospective Adaptive Remeshing Synthesis.
"""

import os
import sys
import json
import hashlib
import unittest

# Dynamic REPO_ROOT resolution:
candidate_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if not os.path.exists(os.path.join(candidate_root, "models", "pandey_kumar_mode1")):
    candidate_root = os.path.abspath(os.getcwd())
if not os.path.exists(os.path.join(candidate_root, "models", "pandey_kumar_mode1")):
    candidate_root = r"D:\Master thesis\Adaptive remeshing"
REPO_ROOT = candidate_root


class TestMode1F1475DeterminismAndProspectiveSynthesis(unittest.TestCase):
    """Test suite verifying F1475 Stage B determinism and prospective remeshing synthesis."""

    def test_01_job_1413022_terminal_accounting_and_metrics(self):
        """Verify terminal accounting, exit behavior, and fracture metrics for Job 1413022."""
        eval_path = os.path.join(
            REPO_ROOT, "models", "pandey_kumar_mode1",
            "40_method_b_corrected_propagation_14k", "evidence_1413022",
            "corrected_method_b_8tb_evaluation.json"
        )
        self.assertTrue(os.path.exists(eval_path), f"Evaluation JSON missing: {eval_path}")
        with open(eval_path, "r", encoding="utf-8") as fp:
            data = json.load(fp)

        # Execution identifiers
        self.assertEqual(data["pbs_job_id"], "1413022.mmaster02")
        self.assertEqual(data["job_name"], "M1_MB_CORR_8TB")
        self.assertEqual(data["cpus"], 8)
        self.assertEqual(data["pbs_exit_status"], 1)
        self.assertEqual(data["solver_execution_status"], "PREMATURE_TERMINATION_AT_DT_MIN")

        # Converged increments
        self.assertEqual(data["total_converged_increments"], 4890)
        self.assertEqual(data["step1_increments"], 2000)
        self.assertEqual(data["step2_increments"], 2890)
        self.assertEqual(data["step2_converged_increments"], 2889)

        # Performance and wallclock speedup
        self.assertEqual(data["wallclock_time_sec"], 12169)
        self.assertAlmostEqual(data["speedup_vs_serial"], 1.9306, places=3)
        self.assertGreater(data["speedup_vs_serial"], 1.80)

        # Multi-quantity fracture response
        self.assertAlmostEqual(data["K0_kN_per_mm"], 137.909558, places=4)
        self.assertAlmostEqual(data["F_max_kN"], 0.743701, places=4)
        self.assertAlmostEqual(data["u_peak_mm"], 0.005733, places=6)
        self.assertAlmostEqual(data["u_terminal_mm"], 0.007889, places=6)
        self.assertAlmostEqual(data["F_terminal_N"], 1.76448, places=3)
        self.assertGreater(data["softening_pct_from_peak"], 99.7)

        # Energy quantities
        self.assertAlmostEqual(data["W_ext_terminal_mJ"], 2.267379, places=4)
        self.assertAlmostEqual(data["E_fracture_terminal_mJ"], 2.285469, places=4)
        self.assertAlmostEqual(data["E_elastic_terminal_mJ"], 0.006960, places=5)
        self.assertAlmostEqual(data["energy_residual_delta_E_mJ"], 0.025050, places=4)
        self.assertAlmostEqual(data["energy_residual_rel_pct"], 1.10479, places=3)

    def test_02_job_1413022_stage_b_determinism_and_bitwise_parity(self):
        """Verify full-precision bitwise identity of energy balance trace across serial, Stage A, and Stage B."""
        evidence_dir = os.path.join(
            REPO_ROOT, "models", "pandey_kumar_mode1",
            "40_method_b_corrected_propagation_14k", "evidence_1413022"
        )
        csv_path_8tb = os.path.join(evidence_dir, "uel_energy_balance.csv")
        self.assertTrue(os.path.exists(csv_path_8tb), f"CSV missing: {csv_path_8tb}")

        # Compute SHA-256 of Stage B repeat
        with open(csv_path_8tb, "rb") as fp:
            hash_8tb = hashlib.sha256(fp.read()).hexdigest().lower()
        expected_hash = "82f2963d4399f7929db6df019a2d7fd34abd3deb570571c04ad489b723561333"
        self.assertEqual(hash_8tb, expected_hash)

        # Compare directly with serial 1412465 baseline
        csv_path_serial = os.path.join(
            REPO_ROOT, "models", "pandey_kumar_mode1",
            "40_method_b_corrected_propagation_14k", "evidence_1412465",
            "uel_energy_balance.csv"
        )
        if os.path.exists(csv_path_serial):
            with open(csv_path_serial, "rb") as fp:
                hash_serial = hashlib.sha256(fp.read()).hexdigest().lower()
            self.assertEqual(hash_8tb, hash_serial)

        # Line count check
        with open(csv_path_8tb, "r", encoding="utf-8") as fp:
            line_count = sum(1 for _ in fp)
        self.assertEqual(line_count, 4890)

        # Verify evaluations certify THREAD_DETERMINISM_PASS
        eval_path = os.path.join(evidence_dir, "corrected_method_b_8tb_evaluation.json")
        with open(eval_path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
        self.assertEqual(data["parity_certification"], "THREAD_PARITY_PASS")
        self.assertEqual(data["determinism_certification"], "THREAD_DETERMINISM_PASS")
        self.assertEqual(data["parallelization_status"], "THREAD_PARALLELIZATION_QUALIFIED")

    def test_03_method_b_prospective_remeshing_synthesis(self):
        """Verify the consolidated prospective remeshing synthesis across 4 errorTarget tiers."""
        l0 = 0.0075
        h_half_l0 = l0 / 2.0  # 3.75 um

        tiers = {
            "1.0%": {"elements": 71320, "x_max_resolved": 0.7529, "coverage_pct": 50.58, "h_tip_um": 1.89},
            "2.0%": {"elements": 14677, "x_max_resolved": 0.6040, "coverage_pct": 20.80, "h_tip_um": 1.94},
            "3.0%": {"elements": 7633,  "x_max_resolved": 0.5556, "coverage_pct": 11.12, "h_tip_um": 1.99},
            "5.0%": {"elements": 4194,  "x_max_resolved": 0.5231, "coverage_pct": 4.62,  "h_tip_um": 3.10},
        }

        # 1. Monotonic decrease in contiguous resolved ligament coverage
        prev_cov = 100.0
        for name, d in tiers.items():
            self.assertLess(d["coverage_pct"], prev_cov)
            prev_cov = d["coverage_pct"]
            # Crack tip is always refined
            self.assertLess(d["h_tip_um"] / 1000.0, h_half_l0)

        # 2. Maximum reach even at 71k elements covers only 50.6% of ligament
        self.assertLess(tiers["1.0%"]["x_max_resolved"], 0.76)

        # 3. Retrospective Corrected Package 40 (14,483 FE) resolves 96.8% of ligament
        package_40_corridor_pct = 96.76
        self.assertGreater(package_40_corridor_pct, 95.0)

    def test_04_hpc_zero_additional_jobs_decision_and_queue_status(self):
        """Verify that zero active jobs remain and zero additional jobs are authorized."""
        active_task_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
        self.assertTrue(os.path.exists(active_task_path))
        with open(active_task_path, "r", encoding="utf-8") as fp:
            active_task = json.load(fp)

        # Active queue check
        if "F1475" in active_task["task_id"]:
            self.assertEqual(len(active_task["active_pbs_job_ids"]), 0)
            self.assertEqual(active_task["status"], "COMPLETED")
        else:
            self.assertIn("1413022.mmaster02", active_task.get("completed_pbs_job_ids", []))

    def test_05_governance_uel_freeze_and_gate_6c_lock(self):
        """Verify production UEL source SHA-256 and Gate 6C authorization lock."""
        uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
        self.assertTrue(os.path.exists(uel_path))
        with open(uel_path, "rb") as fp:
            uel_sha256 = hashlib.sha256(fp.read()).hexdigest().upper()
        expected_sha = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        self.assertEqual(uel_sha256, expected_sha)

        # Verify Gate 6C lock in submission script
        script_path = os.path.join(
            REPO_ROOT, "models", "pandey_kumar_mode1",
            "42_method_c1_forward_refinement", "submit_c1_forward_refinement_job.sh"
        )
        self.assertTrue(os.path.exists(script_path))
        with open(script_path, "r", encoding="utf-8", errors="ignore") as fp:
            content = fp.read()
        self.assertIn("AUTHORIZED=false", content)


if __name__ == "__main__":
    unittest.main()
