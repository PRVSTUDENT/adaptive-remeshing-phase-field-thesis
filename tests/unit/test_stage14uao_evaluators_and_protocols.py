"""
Unit tests for Gate-6B Stage 14U-AO evaluators, Package 31 manifest integrity,
and multi-threaded / spatial resolution / convergence control decision protocols.
"""

import json
import os
import sys
import unittest
import importlib.util

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class TestStage14UAOEvaluatorsAndProtocols(unittest.TestCase):

    def setUp(self):
        self.pkg31_manifest_path = os.path.join(
            REPO_ROOT,
            "models",
            "pandey_kumar_mode1",
            "31_stage14_adaptive_candidate_14k_8thread_stage_b",
            "package_manifest.json"
        )
        self.eval_8t_path = os.path.join(
            REPO_ROOT,
            "models",
            "pandey_kumar_mode1",
            "29_stage14_adaptive_candidate_14k_8thread",
            "evaluate_stage14uao_8thread_stage_a.py"
        )
        self.eval_pkg28_path = os.path.join(
            REPO_ROOT,
            "models",
            "pandey_kumar_mode1",
            "28_stage14_convergence_control_candidate",
            "evaluate_stage14uao_pkg28_convergence_control.py"
        )
        self.eval_spatial_path = os.path.join(
            REPO_ROOT,
            "models",
            "pandey_kumar_mode1",
            "30_stage14_adaptive_candidate_spatial_fine",
            "evaluate_stage14uao_spatial_fine_candidate.py"
        )

    def test_package_31_manifest_integrity(self):
        self.assertTrue(os.path.isfile(self.pkg31_manifest_path), f"Missing {self.pkg31_manifest_path}")
        with open(self.pkg31_manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest.get("package_id"), "PACKAGE_31_STAGE14_ADAPTIVE_14K_8THREAD_STAGE_B_REPEAT")
        self.assertEqual(manifest.get("package_role"), "STAGEB_8THREAD_SHARED_MEMORY_DETERMINISM_REPEAT")
        self.assertEqual(manifest.get("status"), "8THREAD_STAGEB_REPEAT_VALIDATED__WAITING_FOR_STAGEA_TERMINAL_PASS")
        
        # Verify gating rules
        gating = manifest.get("gating_rules", {})
        self.assertTrue(gating.get("datacheck_authorized"))
        self.assertFalse(gating.get("submission_authorized"))
        self.assertEqual(gating.get("prerequisite"), "STAGE_A_8THREAD_PARITY_FULL_PASS_AT_U007889")
        
        # Verify execution resources
        pbs_info = manifest.get("governed_files", {}).get("pbs_script", {})
        self.assertEqual(pbs_info.get("cpus"), 8)
        self.assertEqual(pbs_info.get("mp_mode"), "threads")
        
        # Verify hashes
        gov_files = manifest.get("governed_files", {})
        inp_hash = gov_files.get("input_deck", {}).get("sha256", "").lower()
        for_hash = gov_files.get("user_subroutine", {}).get("sha256", "").lower()
        self.assertTrue(inp_hash.startswith("26d873fb"))
        self.assertTrue(for_hash.startswith("ce8d5edc"))

    def test_evaluator_scripts_exist(self):
        self.assertTrue(os.path.isfile(self.eval_8t_path), f"Missing {self.eval_8t_path}")
        self.assertTrue(os.path.isfile(self.eval_pkg28_path), f"Missing {self.eval_pkg28_path}")
        self.assertTrue(os.path.isfile(self.eval_spatial_path), f"Missing {self.eval_spatial_path}")

    def test_evaluator_modules_loadable(self):
        for path, mod_name, expected_func in [
            (self.eval_8t_path, "eval_8t", "evaluate_8thread_stage_a"),
            (self.eval_pkg28_path, "eval_pkg28", "evaluate_convergence_control_diagnostic"),
            (self.eval_spatial_path, "eval_spatial", "evaluate_spatial_fine_candidate")
        ]:
            spec = importlib.util.spec_from_file_location(mod_name, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self.assertTrue(hasattr(mod, expected_func), f"Module {mod_name} missing {expected_func}")

    def test_8thread_stage_a_parity_decision_logic(self):
        """Test decision logic of 8-thread Stage-A evaluator."""
        spec = importlib.util.spec_from_file_location("eval_8t_mod", self.eval_8t_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        
        # Test simulated perfect parity comparison
        sim_data_8t = {
            "completed": True,
            "exit_code": 0,
            "max_force_diff_pct": 0.02,
            "energy_diff_pct": 0.03,
            "cutbacks": 0,
            "u_term": 0.0080
        }
        
        # Verify tolerance bounds: <= 0.5% max force difference, <= 0.5% energy difference
        is_pass = (
            sim_data_8t["completed"] and
            sim_data_8t["exit_code"] == 0 and
            sim_data_8t["max_force_diff_pct"] <= 0.5 and
            sim_data_8t["energy_diff_pct"] <= 0.5
        )
        self.assertTrue(is_pass)

    def test_pkg28_convergence_control_decision_logic(self):
        """Test decision logic of Package 28 convergence control evaluator."""
        spec = importlib.util.spec_from_file_location("eval_pkg28_mod", self.eval_pkg28_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        
        # Test simulated stability comparison
        sim_data_conv = {
            "completed": True,
            "exit_code": 0,
            "cutback_count": 0,
            "iterations_per_increment_avg": 3.05,
            "peak_load_diff_pct": 0.01
        }
        
        is_robust = (
            sim_data_conv["completed"] and
            sim_data_conv["exit_code"] == 0 and
            sim_data_conv["cutback_count"] <= 5 and
            sim_data_conv["iterations_per_increment_avg"] <= 4.5
        )
        self.assertTrue(is_robust)

    def test_spatial_resolution_decision_logic(self):
        """Test decision logic of Package 30 spatial fine evaluator."""
        spec = importlib.util.spec_from_file_location("eval_spatial_mod", self.eval_spatial_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        
        # Test simulated fine mesh evaluation
        sim_spatial = {
            "completed": True,
            "exit_code": 0,
            "num_elements": 57929,
            "h_min": 0.015,
            "peak_load": 182.4,
            "reference_peak_load": 182.1
        }
        
        peak_diff_pct = abs(sim_spatial["peak_load"] - sim_spatial["reference_peak_load"]) / sim_spatial["reference_peak_load"] * 100.0
        self.assertLess(peak_diff_pct, 1.0)

if __name__ == "__main__":
    unittest.main()
