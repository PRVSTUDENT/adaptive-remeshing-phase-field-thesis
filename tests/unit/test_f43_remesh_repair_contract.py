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

    def test_env_var_path_resolution_with_empirical_cae_argv(self):
        import sys, tempfile, importlib.util
        driver_path = os.path.join(PACKAGE_DIR, "run_f43_native_remesh_driver.py")
        spec = importlib.util.spec_from_file_location("f43_driver", driver_path)
        f43_driver = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(f43_driver)

        with tempfile.NamedTemporaryFile("wb", delete=False) as tmp_odb:
            dummy_content = b"DUMMY_ODB_CONTENT_FOR_3a201a6d"
            tmp_odb.write(dummy_content)
            tmp_odb_path = tmp_odb.name

        actual_hash = hashlib.sha256(dummy_content).hexdigest()
        config_path = os.path.join(PACKAGE_DIR, "f43_remeshing_rule_config.json")
        output_inp_path = os.path.join(REPO_ROOT, "F43REFINED_standard.inp")

        old_argv = sys.argv
        sys.argv = ['-cae', 'f43_remeshing_rule_config.json', 'evidence/1384674.mmaster02/F43PRE1.odb', 'F43REFINED_standard.inp']

        old_env = dict(os.environ)
        try:
            os.environ["F43REM1_CONFIG_PATH"] = config_path
            os.environ["F43REM1_ODB_PATH"] = tmp_odb_path
            os.environ["F43REM1_OUTPUT_INP"] = output_inp_path
            os.environ["F43REM1_EXPECTED_ODB_SHA256"] = actual_hash

            env_res = f43_driver.resolve_runtime_environment()
            self.assertEqual(env_res["config_path"], os.path.abspath(config_path))
            self.assertEqual(env_res["odb_path"], os.path.abspath(tmp_odb_path))
            self.assertEqual(env_res["out_path"], os.path.abspath(output_inp_path))
        finally:
            sys.argv = old_argv
            os.environ.clear()
            os.environ.update(old_env)
            if os.path.exists(tmp_odb_path):
                os.remove(tmp_odb_path)

    def test_missing_env_vars_fail(self):
        import importlib.util
        driver_path = os.path.join(PACKAGE_DIR, "run_f43_native_remesh_driver.py")
        spec = importlib.util.spec_from_file_location("f43_driver", driver_path)
        f43_driver = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(f43_driver)

        required_vars = [
            "F43REM1_CONFIG_PATH",
            "F43REM1_ODB_PATH",
            "F43REM1_OUTPUT_INP",
            "F43REM1_EXPECTED_ODB_SHA256"
        ]
        for missing_var in required_vars:
            old_env = dict(os.environ)
            try:
                os.environ["F43REM1_CONFIG_PATH"] = "dummy_cfg"
                os.environ["F43REM1_ODB_PATH"] = "dummy_odb"
                os.environ["F43REM1_OUTPUT_INP"] = "dummy_out"
                os.environ["F43REM1_EXPECTED_ODB_SHA256"] = "dummy_hash"
                del os.environ[missing_var]

                with self.assertRaises(RuntimeError) as ctx:
                    f43_driver.resolve_runtime_environment()
                self.assertIn("Missing required environment variable", str(ctx.exception))
            finally:
                os.environ.clear()
                os.environ.update(old_env)

    def test_odb_hash_validation_and_legacy_rejection(self):
        import tempfile, importlib.util
        driver_path = os.path.join(PACKAGE_DIR, "run_f43_native_remesh_driver.py")
        spec = importlib.util.spec_from_file_location("f43_driver", driver_path)
        f43_driver = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(f43_driver)

        with tempfile.NamedTemporaryFile("wb", delete=False) as tmp_odb:
            tmp_odb.write(b"LEGACY_ODB_1379579")
            tmp_odb_path = tmp_odb.name

        config_path = os.path.join(PACKAGE_DIR, "f43_remeshing_rule_config.json")
        output_inp_path = os.path.join(REPO_ROOT, "F43REFINED_standard.inp")

        old_env = dict(os.environ)
        try:
            os.environ["F43REM1_CONFIG_PATH"] = config_path
            os.environ["F43REM1_ODB_PATH"] = tmp_odb_path
            os.environ["F43REM1_OUTPUT_INP"] = output_inp_path
            os.environ["F43REM1_EXPECTED_ODB_SHA256"] = "3a201a6d405b92f4588e3d7e68177797706fd80ca9fa541e36ed0b10fdfb0534"

            with self.assertRaises(RuntimeError) as ctx:
                f43_driver.resolve_runtime_environment()
            self.assertIn("Source ODB SHA256 mismatch", str(ctx.exception))
        finally:
            os.environ.clear()
            os.environ.update(old_env)
            if os.path.exists(tmp_odb_path):
                os.remove(tmp_odb_path)

    def test_missing_cae_path_driver_fails_gate_1(self):
        import tempfile, importlib.util
        driver_path = os.path.join(PACKAGE_DIR, "run_f43_native_remesh_driver.py")
        spec = importlib.util.spec_from_file_location("f43_driver", driver_path)
        f43_driver = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(f43_driver)

        config_path = os.path.join(PACKAGE_DIR, "f43_remeshing_rule_config.json")
        env = {
            "config_path": config_path,
            "odb_path": config_path,
            "out_path": "dummy_out.inp",
            "cae_path": None,
            "cae_sha256": None,
            "model_name": None,
            "part_name": None,
            "step_name": "Step-1"
        }

        # Mocking abaqus module presence in dry-run to trigger Gate 1 check
        import sys
        class MockMdb:
            models = {}
        class MockSession:
            pass
        mock_abaqus = type(sys)('abaqus')
        mock_abaqus.mdb = MockMdb()
        mock_abaqus.session = MockSession()
        
        mock_constants = type(sys)('abaqusConstants')
        mock_constants.STANDARD = 1
        mock_constants.ALLOW_COARSENING = 2

        old_modules = dict(sys.modules)
        sys.modules['abaqus'] = mock_abaqus
        sys.modules['abaqusConstants'] = mock_constants
        try:
            with self.assertRaises(RuntimeError) as ctx:
                f43_driver.run_f43_native_remesh_driver(env)
            self.assertIn("FAIL_GATE_1", str(ctx.exception))
        finally:
            sys.modules.clear()
            sys.modules.update(old_modules)

    def test_runtime_validator_rejects_missing_success_marker(self):
        import tempfile, importlib.util
        validator_path = os.path.join(PACKAGE_DIR, "validate_f43rem1_runtime.py")
        spec = importlib.util.spec_from_file_location("f43_validator", validator_path)
        f43_validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(f43_validator)

        with tempfile.TemporaryDirectory() as tmp_dir:
            exec_log = os.path.join(tmp_dir, "execution.log")
            refined_deck = os.path.join(tmp_dir, "F43REFINED_standard.inp")
            with open(exec_log, "w") as f:
                f.write("Log without success marker\n")
            with open(refined_deck, "w") as f:
                f.write("*Element, type=CPE4\n1, 1, 2, 3, 4\n" * 10)

            passed = f43_validator.validate_f43rem1_runtime(tmp_dir)
            self.assertFalse(passed, "Validator must fail when F43REM1_RUNTIME_SUCCESS=true is missing!")

    def test_runtime_validator_passes_on_valid_marker_and_deck(self):
        import tempfile, importlib.util
        validator_path = os.path.join(PACKAGE_DIR, "validate_f43rem1_runtime.py")
        spec = importlib.util.spec_from_file_location("f43_validator", validator_path)
        f43_validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(f43_validator)

        with tempfile.TemporaryDirectory() as tmp_dir:
            exec_log = os.path.join(tmp_dir, "execution.log")
            refined_deck = os.path.join(tmp_dir, "F43REFINED_standard.inp")
            with open(exec_log, "w") as f:
                f.write("Log line\nF43REM1_RUNTIME_SUCCESS=true\nLog line\n")
            with open(refined_deck, "w") as f:
                f.write("*Element, type=CPE4\n1, 1, 2, 3, 4\n" * 10)

            passed = f43_validator.validate_f43rem1_runtime(tmp_dir)
            self.assertTrue(passed, "Validator must pass when success marker and valid deck are present!")

if __name__ == "__main__":
    unittest.main()

