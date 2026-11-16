# -*- coding: utf-8 -*-
"""
tests/unit/test_f1820_minmax_sizing_framework.py
=================================================
Unit tests for Task F1820: Minimum-Maximum Sizing Framework Enhancement.
Verifies:
1. Production UEL remains bitwise frozen at CE8D5EDC...
2. Shared framework updated to support sizingMethod=MINIMUM_MAXIMUM and UNIFORM_ERROR.
3. AdaptiveConfig correctly parses sizing_method, max_solution_error_target, min_solution_error_target, and mesh_bias.
4. Default behavior remains bitwise compatible with UNIFORM_ERROR when sizing_method is omitted.
5. AbaqusNativeRemeshingEngine.build_rule_kwargs generates correct keyword arguments for both sizing methods.
6. Allowed operations in bridge_research_policy.json includes minmax_sizing_evaluation.
7. Governance invariants: 0 new PBS jobs, cumulative 35 preserved, MASTER_GOAL_STATUS = OPEN.
"""

import os
import json
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FRAMEWORK_F1820_SHA256 = "0578156E5551173307892B8881E4BA772F099187BCF332672F39AC825023E80D"


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


class TestF1820MinMaxSizingFramework(unittest.TestCase):

    def test_01_frozen_uel_and_framework(self):
        """Production UEL must be bitwise frozen; framework must match F1820 SHA."""
        uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
        self.assertTrue(os.path.isfile(uel_path), "UEL file missing")
        self.assertEqual(_sha256(uel_path), FROZEN_UEL_SHA256)

        fw_path = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
        self.assertTrue(os.path.isfile(fw_path), "Framework file missing")
        self.assertEqual(_sha256(fw_path), FRAMEWORK_F1820_SHA256)

    def test_02_adaptive_config_defaults_uniform_error(self):
        """AdaptiveConfig defaults to UNIFORM_ERROR when sizing_method is omitted."""
        import sys
        fw_dir = os.path.join(REPO_ROOT, "scripts", "remeshing")
        if fw_dir not in sys.path:
            sys.path.insert(0, fw_dir)
        from reusable_2d_adaptive_framework import AdaptiveConfig

        raw_cfg = {
            "case_id": "case_1",
            "benchmark_name": "Test Case 1",
            "geometry": {"plate_width": 1.0, "plate_height": 1.0, "notch_length": 0.5},
            "remeshing_rule": {
                "error_target": 4.5,
                "min_element_size_mm": 0.001,
                "max_element_size_mm": 0.020
            }
        }
        cfg = AdaptiveConfig(raw_cfg)
        self.assertEqual(cfg.sizing_method, "UNIFORM_ERROR")
        self.assertEqual(cfg.error_target, 4.5)
        self.assertEqual(cfg.max_solution_error_target, 4.5)
        self.assertAlmostEqual(cfg.min_solution_error_target, 0.9, places=3)
        self.assertEqual(cfg.mesh_bias, 1)

    def test_03_adaptive_config_minmax_parsing(self):
        """AdaptiveConfig correctly parses MINIMUM_MAXIMUM parameters."""
        import sys
        fw_dir = os.path.join(REPO_ROOT, "scripts", "remeshing")
        if fw_dir not in sys.path:
            sys.path.insert(0, fw_dir)
        from reusable_2d_adaptive_framework import AdaptiveConfig

        raw_cfg = {
            "case_id": "case_2",
            "benchmark_name": "Test Case 2",
            "geometry": {"plate_width": 1.0, "plate_height": 1.0},
            "remeshing_rule": {
                "sizing_method": "MINIMUM_MAXIMUM",
                "max_solution_error_target": 1.0,
                "min_solution_error_target": 5.0,
                "mesh_bias": 7,
                "min_element_size_mm": 0.0015,
                "max_element_size_mm": 0.020,
                "refinement_factor": 10
            }
        }
        cfg = AdaptiveConfig(raw_cfg)
        self.assertEqual(cfg.sizing_method, "MINIMUM_MAXIMUM")
        self.assertEqual(cfg.max_solution_error_target, 1.0)
        self.assertEqual(cfg.min_solution_error_target, 5.0)
        self.assertEqual(cfg.mesh_bias, 7)

    def test_04_build_rule_kwargs_uniform_error(self):
        """build_rule_kwargs constructs valid UNIFORM_ERROR arguments."""
        import sys
        fw_dir = os.path.join(REPO_ROOT, "scripts", "remeshing")
        if fw_dir not in sys.path:
            sys.path.insert(0, fw_dir)
        from reusable_2d_adaptive_framework import AdaptiveConfig, AbaqusNativeRemeshingEngine

        raw_cfg = {
            "case_id": "case_1",
            "benchmark_name": "Test Case 1",
            "geometry": {"plate_width": 1.0, "plate_height": 1.0, "notch_length": 0.5},
            "remeshing_rule": {
                "error_target": 3.0,
                "min_element_size_mm": 0.001,
                "max_element_size_mm": 0.020,
                "sizing_method": "UNIFORM_ERROR"
            }
        }
        cfg = AdaptiveConfig(raw_cfg)
        kwargs = AbaqusNativeRemeshingEngine.build_rule_kwargs(cfg, "Rule_Test", "Step-1")
        self.assertEqual(kwargs['name'], "Rule_Test")
        self.assertEqual(kwargs['stepName'], "Step-1")
        self.assertEqual(kwargs['sizingMethod'], "UNIFORM_ERROR")
        self.assertEqual(kwargs['errorTarget'], 3.0)
        self.assertNotIn('maxSolutionErrorTarget', kwargs)
        self.assertNotIn('minSolutionErrorTarget', kwargs)
        self.assertNotIn('meshBias', kwargs)
        self.assertTrue(kwargs['specifyMinSize'])
        self.assertEqual(kwargs['minElementSize'], 0.001)
        self.assertTrue(kwargs['specifyMaxSize'])
        self.assertEqual(kwargs['maxElementSize'], 0.020)

    def test_05_build_rule_kwargs_minmax(self):
        """build_rule_kwargs constructs valid MINIMUM_MAXIMUM arguments."""
        import sys
        fw_dir = os.path.join(REPO_ROOT, "scripts", "remeshing")
        if fw_dir not in sys.path:
            sys.path.insert(0, fw_dir)
        from reusable_2d_adaptive_framework import AdaptiveConfig, AbaqusNativeRemeshingEngine

        raw_cfg = {
            "case_id": "case_3",
            "benchmark_name": "Test Case 3",
            "geometry": {"plate_width": 65.0, "plate_height": 120.0},
            "remeshing_rule": {
                "sizing_method": "MINIMUM_MAXIMUM",
                "max_solution_error_target": 2.0,
                "min_solution_error_target": 6.0,
                "mesh_bias": 5,
                "min_element_size_mm": 0.05,
                "max_element_size_mm": 2.0
            }
        }
        cfg = AdaptiveConfig(raw_cfg)
        kwargs = AbaqusNativeRemeshingEngine.build_rule_kwargs(cfg, "Rule_MinMax_Test", "RECOVERY_STEP")
        self.assertEqual(kwargs['name'], "Rule_MinMax_Test")
        self.assertEqual(kwargs['stepName'], "RECOVERY_STEP")
        self.assertEqual(kwargs['sizingMethod'], "MINIMUM_MAXIMUM")
        self.assertEqual(kwargs['maxSolutionErrorTarget'], 2.0)
        self.assertEqual(kwargs['minSolutionErrorTarget'], 6.0)
        self.assertEqual(kwargs['meshBias'], 5)
        self.assertNotIn('errorTarget', kwargs)
        self.assertTrue(kwargs['specifyMinSize'])
        self.assertEqual(kwargs['minElementSize'], 0.05)
        self.assertTrue(kwargs['specifyMaxSize'])
        self.assertEqual(kwargs['maxElementSize'], 2.0)

    def test_06_bridge_research_policy_includes_operation(self):
        """bridge_research_policy.json must include minmax_sizing_evaluation in allowed_operations."""
        policy_path = os.path.join(REPO_ROOT, ".agents", "scripts", "bridge_research_policy.json")
        self.assertTrue(os.path.isfile(policy_path))
        with open(policy_path, "r", encoding="utf-8-sig") as f:
            policy = json.load(f)
        allowed = policy.get("allowed_operations", [])
        self.assertIn("minmax_sizing_evaluation", allowed)
        self.assertIn("shared_framework_improvement", allowed)

    def test_07_governance_invariants(self):
        """Active task must maintain cumulative PBS at 35, 0 new PBS jobs, and goal OPEN."""
        task_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
        self.assertTrue(os.path.isfile(task_path))
        with open(task_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("master_goal_status"), "OPEN")
        self.assertEqual(data.get("cumulative_pbs_submissions"), 35)
        self.assertEqual(data.get("max_new_pbs_submissions"), 0)
        self.assertEqual(data.get("submissions_consumed"), 0)
        self.assertIn(data.get("task_id"), [
            "F1820-MINIMUM-MAXIMUM-SIZING-FRAMEWORK-ENHANCEMENT-AND-EVALUATION",
            "F1821-GENUINE-MINIMUM-MAXIMUM-EXECUTION-AND-F1820-CORRECTION"
        ])

    def test_08_f1820_receipt_and_summary_exist(self):
        """F1820 receipt and summary JSON files must exist with verified hashes."""
        receipt_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "264_f1820_minmax_sizing", "PK_F1820_MINMAX_SIZING_RECEIPT.json")
        self.assertTrue(os.path.isfile(receipt_path))
        self.assertEqual(_sha256(receipt_path), "D93446727278A84ADA6172B47FDE3B65ED20CAA7B683854E9E505244CE87A910")

        summary_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "264_f1820_minmax_sizing", "minmax_sizing_summary.json")
        self.assertTrue(os.path.isfile(summary_path))
        self.assertEqual(_sha256(summary_path), "DA5F67891F03BF4515EAA1F653B0B442BE2CE63C67747A6E1D6355488829C6B7")

    def test_09_f1820_four_case_mesh_files_and_hashes(self):
        """All four physical adapted meshes must exist and match verified hashes."""
        mesh_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "264_f1820_minmax_sizing")
        expected_meshes = {
            "case_1": ("PK_F1820_MINMAX_CASE_1_ADAPT_PHYS.inp", "ABAA325BC6EE7EEBDE5553F1E9498639545895AC43B3EF61279B189A5554ABF5", 63210),
            "case_2": ("PK_F1820_MINMAX_CASE_2_ADAPT_PHYS.inp", "AD6D83A99E41B5AD5643AAE4E92BF53CC40AC94997488761F01E3A4D7045C7B7", 56300),
            "case_3": ("PK_F1820_MINMAX_CASE_3_ADAPT_PHYS.inp", "84B1241DE4F910FD6605F01CE824C54DDEC25148CB08CB5687D7038F4A1C9A89", 87786),
            "case_5": ("PK_F1820_MINMAX_CASE_5_ADAPT_PHYS.inp", "33CCC72D7E35676C4D09E62C09E1CD857FF5E8D0330AC5462CC4CA4BD62F4A9C", 51598),
        }
        for cid, (fname, exp_sha, exp_el) in expected_meshes.items():
            p = os.path.join(mesh_dir, fname)
            self.assertTrue(os.path.isfile(p), "Missing mesh: %s" % p)
            self.assertEqual(_sha256(p), exp_sha, "Hash mismatch for %s" % fname)

    def test_10_f1820_rejection_and_pareto_optimum_confirmed(self):
        """F1820 receipt must record REJECTED and total elements = 258,894."""
        receipt_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "264_f1820_minmax_sizing", "PK_F1820_MINMAX_SIZING_RECEIPT.json")
        with open(receipt_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["adoption_decision"]["verdict"], "REJECTED")
        self.assertEqual(data["four_benchmark_totals"]["total_physical_elements"], 258894)
        self.assertEqual(data["four_benchmark_totals"]["zero_or_negative_jacobians"], 0)
        self.assertAlmostEqual(data["four_benchmark_totals"]["comparison_vs_f1812_baseline"]["percent_change"], 61.66, places=1)


if __name__ == "__main__":
    unittest.main()
