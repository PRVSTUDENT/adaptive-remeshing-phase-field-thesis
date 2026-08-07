#!/usr/bin/env python3
"""
Unit tests for F43REM1-R1 current-predecessor repair and remote submission contract.
"""
import unittest
import os
import json
import hashlib

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PACKAGE_DIR = os.path.join(REPO_ROOT, "models", "generated", "mode_ii", "f43_stage_c_bridge")

class TestF43RemeshRepairContract(unittest.TestCase):

    def test_legacy_1379579_reference_absent_in_executable_package(self):
        stale_term = "1379579"
        executable_files = [
            "F43REM1.pbs",
            "submit_f43rem1.sh",
            "run_f43_native_remesh_driver.py",
            "f43_remeshing_rule_config.json",
            "validate_f43rem1_runtime.py",
            "collect_f43rem1_evidence.sh",
            "F43REM1_SOURCE_MANIFEST.json",
            "F43REM1_PACKAGE_MANIFEST.json"
        ]
        for filename in executable_files:
            path = os.path.join(PACKAGE_DIR, filename)
            self.assertTrue(os.path.exists(path), f"Missing package file: {filename}")
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertNotIn(stale_term, content, f"Stale legacy reference '{stale_term}' found in {filename}")

    def test_source_manifest_predecessor_and_sha(self):
        manifest_path = os.path.join(PACKAGE_DIR, "F43REM1_SOURCE_MANIFEST.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["predecessor_job"], "1384674.mmaster02")
        self.assertIn("1384674.mmaster02", data["odb_path"])
        self.assertNotIn("1379579", data["odb_path"])
        self.assertEqual(data["odb_sha256"], "3a201a6d405b92f4588e3d7e68177797706fd80ca9fa541e36ed0b10fdfb0534")
        self.assertEqual(data["input_sha256"], "a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2")
        self.assertEqual(data["configured_min_h_mm"], 0.0075)
        self.assertEqual(data["configured_max_h_mm"], 0.03)
        self.assertEqual(data["phase_field_length_scale_l_mm"], 0.015)
        self.assertEqual(data["configured_h_over_l"], 0.50)

    def test_submit_wrapper_fail_closed_without_qsub(self):
        submit_path = os.path.join(PACKAGE_DIR, "submit_f43rem1.sh")
        with open(submit_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("command -v qsub", content)
        self.assertIn("qsub command not found", content)
        self.assertIn("F43REM1_EXECUTION_AUTHORIZED", content)
        self.assertIn("3a201a6d405b92f4588e3d7e68177797706fd80ca9fa541e36ed0b10fdfb0534", content)

    def test_package_manifest_completeness(self):
        manifest_path = os.path.join(PACKAGE_DIR, "F43REM1_PACKAGE_MANIFEST.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        expected_keys = [
            "F43REM1.pbs",
            "submit_f43rem1.sh",
            "run_f43_native_remesh_driver.py",
            "f43_remeshing_rule_config.json",
            "validate_f43rem1_runtime.py",
            "collect_f43rem1_evidence.sh",
            "F43REM1_SOURCE_MANIFEST.json"
        ]
        for key in expected_keys:
            self.assertIn(key, data)
            self.assertEqual(len(data[key]), 64)

if __name__ == "__main__":
    unittest.main()
