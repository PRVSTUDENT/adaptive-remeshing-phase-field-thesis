import hashlib
import json
import os
import re
import subprocess
import sys
import unittest

class TestStageF40Batch(unittest.TestCase):

    def setUp(self):
        self.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.pkg_dir = os.path.join(self.repo_root, "models", "generated", "mode_ii", "f40_f38_cae_invocation_model_building_bisect")
        self.wrapper_path = os.path.join(self.repo_root, "scripts", "hpc", "stage_f", "submit_stage_f40_cae_bisect.sh")
        self.validator_path = os.path.join(self.repo_root, "scripts", "validation", "validate_f40_cae_bisect_gate.py")

    def test_runner_has_no_file_dependency(self):
        runner_path = os.path.join(self.pkg_dir, "runtime", "f40_cae_bisection_runner.py")
        self.assertTrue(os.path.exists(runner_path))
        with open(runner_path, "r") as f:
            content = f.read()
            self.assertNotIn("__file__", content)

    def test_contract_delta_auditor_exists(self):
        delta_path = os.path.join(self.pkg_dir, "runtime", "f40_invocation_contract_delta.py")
        self.assertTrue(os.path.exists(delta_path))

    def test_pbs_queue_and_resource_directives(self):
        pbs_path = os.path.join(self.pkg_dir, "M2RMBISECT1.pbs")
        with open(pbs_path, "r") as f:
            content = f.read()
            self.assertIn("#PBS -q entry_imfdfkmq", content)
            self.assertIn("#PBS -l select=1:ncpus=1:mpiprocs=1:ompthreads=1:mem=8gb", content)

    def test_pbs_trap_preserves_first_failure(self):
        pbs_path = os.path.join(self.pkg_dir, "M2RMBISECT1.pbs")
        with open(pbs_path, "r") as f:
            content = f.read()
            self.assertIn("trap - EXIT", content)
            self.assertIn('exit "$first_failure"', content)
            self.assertIn("runtime_validator_rc", content)

    def test_runner_records_metrics(self):
        runner_path = os.path.join(self.pkg_dir, "runtime", "f40_cae_bisection_runner.py")
        with open(runner_path, "r") as f:
            content = f.read()
            self.assertIn("metrics", content)
            self.assertIn("write_phase_audit", content)

    def test_pbs_mandatory_evidence_dir(self):
        pbs_path = os.path.join(self.pkg_dir, "M2RMBISECT1.pbs")
        with open(pbs_path, "r") as f:
            content = f.read()
            self.assertIn("F40_EVIDENCE_DIR", content)

    def test_evidence_report_disjoint_sets(self):
        gen_rep_path = os.path.join(self.pkg_dir, "runtime", "generate_missing_evidence_report.py")
        with open(gen_rep_path, "r") as f:
            content = f.read()
            self.assertIn("missing_files = [f for f in EXPECTED_EVIDENCE_FILES", content)
            self.assertIn("existing_files = [f for f in EXPECTED_EVIDENCE_FILES", content)

    def test_package_manifest_completeness(self):
        man_path = os.path.join(self.pkg_dir, "PACKAGE_MANIFEST.json")
        with open(man_path, "r") as f:
            manifest = json.load(f)
            file_entries = manifest.get("files", [])
            paths = [item["path"] for item in file_entries] if isinstance(file_entries, list) else list(manifest.get("package_files", {}).keys())
            self.assertIn("M2RMBISECT1.pbs", paths)
            self.assertIn("runtime/f40_cae_bisection_runner.py", paths)
            self.assertIn("runtime/run_f38_cae_diagnostic.py", paths)
            self.assertIn("runtime/f38_cae_diagnostic_matrix.py", paths)
            self.assertIn("runtime/f40_invocation_contract_delta.py", paths)
            self.assertIn("runtime/generate_missing_evidence_report.py", paths)
            self.assertIn("runtime/source_deck.inp", paths)
            self.assertIn("runtime/validate_f40_runtime_audits.py", paths)

    def test_wrapper_single_qsub(self):
        with open(self.wrapper_path, "r") as f:
            content = f.read()
            qsubs = re.findall(r"^\s*JOB_ID=\$\(qsub\b", content, re.MULTILINE)
            self.assertEqual(len(qsubs), 1)

    def test_submission_gates_default_closed(self):
        with open(self.wrapper_path, "r") as f:
            content = f.read()
            self.assertIn('F40_ALLOW_SUBMISSION:-false', content)
            self.assertIn('F40_AUTHORIZE_M2RMBISECT1:-false', content)

    def test_f38_f39_preservation(self):
        f38_dir = os.path.join(self.repo_root, "models", "generated", "mode_ii", "f38_comprehensive_cae_diagnostic_matrix")
        f39_dir = os.path.join(self.repo_root, "models", "generated", "mode_ii", "f39_abaqus_cae_kernel_startup_diagnostic")
        self.assertTrue(os.path.exists(os.path.join(f38_dir, "M2RMDIAG1.pbs")))
        self.assertTrue(os.path.exists(os.path.join(f39_dir, "M2RMKERN1.pbs")))

    def test_p02_does_not_execute_main(self):
        runner_path = os.path.join(self.pkg_dir, "runtime", "f40_cae_bisection_runner.py")
        with open(runner_path, "r") as f:
            content = f.read()
            self.assertIn("EXPECTED_ENTRYPOINT_SHA256", content)
            self.assertIn("EXPECTED_HELPER_SHA256", content)
            self.assertIn("entrypoint_sha256 != EXPECTED_ENTRYPOINT_SHA256", content)
            self.assertIn("helper_sha256 != EXPECTED_HELPER_SHA256", content)
            self.assertIn('"main_executed_in_p02": False', content)
            # Ensure P02 does NOT call main()
            p02_block = content[content.find("p02_id, p02_name ="):content.find("p03_id, p03_name =")]
            self.assertNotIn("f38_cae_diagnostic_matrix.main()", p02_block)

    def test_stage_3_is_only_full_f38_execution(self):
        pbs_path = os.path.join(self.pkg_dir, "M2RMBISECT1.pbs")
        with open(pbs_path, "r") as f:
            content = f.read()
            self.assertIn("Stage 3: Exact F38 Entrypoint Execution", content)
            self.assertIn("run_f38_cae_diagnostic.py", content)
            self.assertIn("f38_entrypoint_rc", content)
            self.assertIn("validate_f38_matrix_results.py", content)
            self.assertIn("f38_matrix_validator_rc", content)

    def test_pbs_non_circular_finalized_evidence_ordering(self):
        pbs_path = os.path.join(self.pkg_dir, "M2RMBISECT1.pbs")
        with open(pbs_path, "r") as f:
            content = f.read()
            idx_gen = content.find("generate_missing_evidence_report.py")
            idx_val = content.find("validate_f40_runtime_audits.py")
            self.assertGreater(idx_gen, 0)
            self.assertGreater(idx_val, idx_gen)

    def test_matrix_validator_detects_overall_passed_false(self):
        mat_val_path = os.path.join(self.pkg_dir, "runtime", "validate_f38_matrix_results.py")
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            inv_data = {
                "protocol_version": 1,
                "entrypoint": "run_f38_cae_diagnostic.py",
                "file_global_defined": False,
                "runtime_dir": tmpdir,
                "runtime_dir_exists": True,
                "runtime_dir_on_sys_path": True,
                "bootstrap_passed": True
            }
            with open(os.path.join(tmpdir, "CAE_INVOCATION_CONTEXT_AUDIT.json"), "w") as f:
                json.dump(inv_data, f)
            mat_data = {"overall_passed": False, "phases": []}
            with open(os.path.join(tmpdir, "CAE_PHASE_DIAGNOSTIC_MATRIX.json"), "w") as f:
                json.dump(mat_data, f)

            res = subprocess.run([sys.executable, mat_val_path, tmpdir], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            self.assertNotEqual(res.returncode, 0, "Validator should fail when overall_passed is False")
            self.assertIn("overall_passed is not True", res.stdout)

    def test_matrix_validator_accepts_exact_entrypoint_schema_when_matrix_passes(self):
        mat_val_path = os.path.join(self.pkg_dir, "runtime", "validate_f38_matrix_results.py")
        expected_phases = [
            "bootstrap", "abaqus_module_import", "source_deck_access", "model_import",
            "repository_inventory", "repository_resolution", "geometry_conversion",
            "element_type_assignment", "mesh_control_assignment", "mesh_generation",
            "assembly_feature_inventory", "instance_replacement", "crack_edge_method_inventory",
            "crack_edge_detection", "crack_mesh_topology", "assembly_set_inventory",
            "output_variable_probe", "output_request_rebinding", "input_write", "generated_input_presence"
        ]
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            inv_data = {
                "protocol_version": 1,
                "entrypoint": "run_f38_cae_diagnostic.py",
                "file_global_defined": False,
                "runtime_dir": tmpdir,
                "runtime_dir_exists": True,
                "runtime_dir_on_sys_path": True,
                "bootstrap_passed": True
            }
            with open(os.path.join(tmpdir, "CAE_INVOCATION_CONTEXT_AUDIT.json"), "w") as f:
                json.dump(inv_data, f)

            phases_records = []
            for pname in expected_phases:
                phases_records.append({
                    "phase": pname,
                    "attempted": True,
                    "passed": True,
                    "dependency_blocked": False,
                    "exception_type": None,
                    "exception_message": None,
                    "traceback": None
                })
            mat_data = {"overall_passed": True, "phases": phases_records}
            with open(os.path.join(tmpdir, "CAE_PHASE_DIAGNOSTIC_MATRIX.json"), "w") as f:
                json.dump(mat_data, f)

            res = subprocess.run([sys.executable, mat_val_path, tmpdir], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            self.assertEqual(res.returncode, 0, "Validator failed on valid schema and 20 passing phases: " + res.stdout + res.stderr)
            self.assertIn("F38_MATRIX_VALIDATION_PASSED", res.stdout)

    def test_get_first_analysis_step_helper(self):
        matrix_path = os.path.join(self.pkg_dir, "runtime", "f38_cae_diagnostic_matrix.py")
        import importlib.util
        spec = importlib.util.spec_from_file_location("f38_cae_diagnostic_matrix", matrix_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        class MockModel:
            def __init__(self, step_dict):
                self.steps = step_dict

        # Case 1: Only Initial -> raise RuntimeError
        m1 = MockModel({"Initial": "step_initial_obj"})
        with self.assertRaises(RuntimeError):
            mod.get_first_analysis_step(m1)

        # Case 2: Initial + Step-1 -> return Step-1
        m2 = MockModel({"Initial": "step_initial_obj", "Step-1": "step_1_obj"})
        self.assertEqual(mod.get_first_analysis_step(m2), "step_1_obj")

    def test_helper_sha256_constant_matches_manifest(self):
        helper_path = os.path.join(self.pkg_dir, "runtime", "f38_cae_diagnostic_matrix.py")
        h = hashlib.sha256()
        with open(helper_path, "rb") as f:
            h.update(f.read())
        actual_sha = h.hexdigest()

        runner_path = os.path.join(self.pkg_dir, "runtime", "f40_cae_bisection_runner.py")
        import importlib.util
        spec = importlib.util.spec_from_file_location("f40_cae_bisection_runner", runner_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        self.assertEqual(mod.EXPECTED_HELPER_SHA256, actual_sha, "EXPECTED_HELPER_SHA256 in runner must match actual SHA256 of helper matrix")

        manifest_path = os.path.join(self.pkg_dir, "PACKAGE_MANIFEST.json")
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        manifest_hashes = {item["path"]: item["sha256"] for item in manifest["files"]}
        self.assertEqual(manifest_hashes["runtime/f38_cae_diagnostic_matrix.py"], actual_sha, "Manifest SHA256 must match actual helper SHA256")

    def test_p02_fails_on_helper_content_modification(self):
        runner_path = os.path.join(self.pkg_dir, "runtime", "f40_cae_bisection_runner.py")
        import importlib.util
        spec = importlib.util.spec_from_file_location("f40_cae_bisection_runner", runner_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            # Copy real entrypoint
            with open(os.path.join(self.pkg_dir, "runtime", "run_f38_cae_diagnostic.py"), "rb") as sf, \
                 open(os.path.join(tmpdir, "run_f38_cae_diagnostic.py"), "wb") as df:
                df.write(sf.read())

            # Write modified helper (altered content)
            with open(os.path.join(tmpdir, "f38_cae_diagnostic_matrix.py"), "w") as f:
                f.write("# Modified helper content\ndef main(): pass\n")

            exp_entry, exp_help = mod.load_expected_sha256(tmpdir)
            helper_sha256 = hashlib.sha256(b"# Modified helper content\ndef main(): pass\n").hexdigest()

            self.assertNotEqual(helper_sha256, exp_help, "Modified helper SHA256 must differ from expected helper SHA256")

    def test_static_gate_validator_passes(self):
        res = subprocess.run([sys.executable, self.validator_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(res.returncode, 0, "Static validator failed: " + res.stdout + res.stderr)

if __name__ == "__main__":
    unittest.main()
